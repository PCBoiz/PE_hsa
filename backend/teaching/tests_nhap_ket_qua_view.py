"""Nhập kết quả thi thử từ PDF — hai tuyến `…/ket-qua-thi/doc` và `…/ket-qua-thi/ghi`.

Chạy trên DB thật trong giao dịch được CUỘN LẠI (xem `conftest.py`), gọi qua URL
thật để đi đúng bộ định tuyến và cổng phân quyền.

KHÔNG có tệp PDF trong phép kiểm: phần đọc PDF có bộ kiểm riêng
(`tests_nhap_ket_qua_thi.py`), và tờ báo cáo thật mang tên một học sinh có thật.
Ở đây thay hàm đọc tệp bằng một hàm giả — nhưng PHIẾU thì luôn lấy từ tuyến
`doc` thật chứ không tự ký, để lượt ghi đi đúng đường màn hình đi.

Canh:
  1. Đọc và xem trước KHÔNG ghi gì — kể cả nhật ký.
  2. Ghi thật thì đúng một dòng, đúng em, đúng số; và chỉ khi `ghi` là `true` thật.
  3. Nhập LẠI cùng tờ ấy thì GHI ĐÈ, không đẻ thêm lượt thi ma.
  4. Tên không có trong lớp, hoặc trùng tên, thì KHÔNG đoán; chọn tay thì ghi đúng em đã chọn.
  5. Hai tờ rơi vào một em cho cùng kỳ thi → không ghi tờ nào.
  6. Phiếu giả, bị sửa, quá hạn, của lớp khác, của người khác → từ chối, không ghi gì.
  7. Chọn tay một học viên NGOÀI lớp → từ chối CẢ lượt.
  8. Trợ giảng không chạm được; giảng viên lớp khác nhận 404 chứ không phải 403.
  9. Một tờ hỏng không làm hỏng cả lượt đọc.
"""
from datetime import date, timedelta

import pytest
from django.core import signing
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q1, x
from common.permissions import ROLE_ADMIN, ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER
from teaching import nhap_ket_qua_view as V
from teaching.nhap_ket_qua_thi import LoiDocBaoCao

pytestmark = pytest.mark.django_db

DOC = '/api/teach/classes/%s/ket-qua-thi/doc'
GHI = '/api/teach/classes/%s/ket-qua-thi/ghi'


def _to(ho_ten, tong=105, ngay=None, dot='Online 2308'):
    """Dữ liệu một tờ báo cáo đã đọc xong — hình dạng `nhap_ket_qua_thi.doc_tep` trả về."""
    return {
        'hoTen': ho_ten, 'maHocSinh': 'ONL000000', 'ngayThi': ngay or date(2026, 8, 23),
        'hinhThuc': 'Offline', 'diaDiem': 'THPT Thử Nghiệm', 'dot': dot,
        'tongDiem': tong, 'tongToiDa': 150,
        'diemPhan': [{'phan': 1, 'ten': 'Định lượng và Xử lí số liệu', 'diem': 27, 'toiDa': 50},
                     {'phan': 2, 'ten': 'Định tính', 'diem': 38, 'toiDa': 50},
                     {'phan': 3, 'ten': 'Tiếng Anh', 'diem': 40, 'toiDa': 50}],
        'donVi': [{'phan': 1, 'phanTen': 'Định lượng và Xử lí số liệu',
                   'ten': 'Nguyên hàm, tích phân và ứng dụng', 'pct': 0},
                  {'phan': 1, 'phanTen': 'Định lượng và Xử lí số liệu',
                   'ten': 'Hình học Oxyz', 'pct': 50},
                  {'phan': 3, 'phanTen': 'Tổ hợp', 'ten': 'Antonyms', 'pct': 100}],
        'canhBao': [],
    }


def _gia_lap(monkeypatch, theo_ten_tep):
    """Thay hàm đọc PDF: tên tệp → dữ liệu (hoặc `LoiDocBaoCao` nếu giá trị là lỗi)."""
    goi = {'n': 0}

    def doc_tep(_du_lieu):
        ten = list(theo_ten_tep)[goi['n']]
        goi['n'] += 1
        gia = theo_ten_tep[ten]
        if isinstance(gia, Exception):
            raise gia
        return gia

    monkeypatch.setattr(V, 'doc_tep', doc_tep)
    return [(ten, b'%PDF-gia') for ten in theo_ten_tep]


def _nguoi(ten, vai, email=None):
    row = q1('INSERT INTO users (name, email, phone, password, role, streak) '
             "VALUES (%s,%s,NULL,'x',%s,0) RETURNING id", (ten, email, vai))
    return User.objects.get(id=row['id'])


def _lop(ten, gv):
    return q1("INSERT INTO classes (name, course_id, teacher_id, status) "
              "VALUES (%s,'hsa_quantitative',%s,'active') RETURNING id", (ten, gv.id))['id']


def _vao_lop(class_id, u):
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s)',
      (class_id, u.id, local_now() - timedelta(days=10)))


def _dem_nk(ai):
    """Nhật ký do CHÍNH tài khoản này ghi — `admin_audit` là bảng dùng chung, đếm
    tổng sẽ đỏ oan khi có người thao tác song song."""
    return q1('SELECT COUNT(*) AS n FROM admin_audit WHERE actor_id=%s', (ai.id,))['n']


def _json(v):
    """Cột `jsonb` đọc qua con trỏ thô có thể là chuỗi hoặc đã là list — nhận cả hai."""
    import json
    return json.loads(v) if isinstance(v, str) else v


def _dem_kq(uid):
    return q1('SELECT COUNT(*) AS n FROM ket_qua_thi_ngoai WHERE user_id=%s', (uid,))['n']


@pytest.fixture
def lop(db):
    gv = _nguoi('GV Nhap KQ', ROLE_TEACHER, 'gv_nkq@example.com')
    em = _nguoi('Nguyễn Văn An', ROLE_STUDENT, 'an_nkq@example.com')
    lop_id = _lop('Lop nhap KQ', gv)
    _vao_lop(lop_id, em)
    return {'gv': gv, 'em': em, 'id': lop_id}


class _Tep:
    """Tệp tải lên tối thiểu — nội dung không quan trọng vì hàm đọc đã bị thay."""

    def __init__(self, ten, than):
        import io
        self.f = io.BytesIO(than)
        self.name = ten

    def read(self, *a):
        return self.f.read(*a)

    def __iter__(self):
        return iter([self.f.getvalue()])


def _client(ai):
    c = APIClient()
    c.force_authenticate(ai)
    return c


def _doc(ai, lop_id, tep):
    return _client(ai).post(DOC % lop_id, {'files': [_Tep(ten, than) for ten, than in tep]},
                            format='multipart')


def _phieu(ai, lop_id, monkeypatch, theo_ten_tep):
    """Đọc qua tuyến `doc` THẬT → danh sách phiếu, đúng thứ tự tệp."""
    r = _doc(ai, lop_id, _gia_lap(monkeypatch, theo_ten_tep))
    assert r.status_code == 200, r.data
    return [t['phieu'] for t in r.data['tep']]


def _ghi(ai, lop_id, phieu, chon=None, ghi=False):
    body = {'phieu': phieu}
    if chon is not None:
        body['chon'] = chon
    if ghi:
        body['ghi'] = True
    return _client(ai).post(GHI % lop_id, body, format='json')


# ── Đọc ────────────────────────────────────────────────────────────────────

def test_doc_chi_phat_phieu_KHONG_ghi_gi(lop, monkeypatch):
    truoc = _dem_nk(lop['gv'])
    r = _doc(lop['gv'], lop['id'], _gia_lap(monkeypatch, {'an.pdf': _to('Nguyễn Văn An')}))
    assert r.status_code == 200, r.data
    assert r.data['tep'][0]['tep'] == 'an.pdf' and r.data['tep'][0]['phieu']
    assert _dem_kq(lop['em'].id) == 0 and _dem_nk(lop['gv']) == truoc


def test_mot_to_hong_khong_lam_hong_ca_luot_doc(lop, monkeypatch):
    tep = _gia_lap(monkeypatch, {
        'hong.pdf': LoiDocBaoCao('Tệp PDF này gần như không có chữ.'),
        'an.pdf': _to('Nguyễn Văn An'),
    })
    r = _doc(lop['gv'], lop['id'], tep)
    assert r.status_code == 200
    hong, an = r.data['tep']
    assert 'không có chữ' in hong['loi'] and 'phieu' not in hong
    assert an['phieu'], 'tờ đọc được vẫn phải có phiếu'


def test_doc_qua_nhieu_tep_mot_luot_bi_chan(lop, monkeypatch):
    """Màn hình gửi từng tệp. Một request tự dựng gửi cả xấp là thứ chạm trần 60
    giây của gunicorn — chặn TRƯỚC khi đọc tờ nào."""
    ds = {'t%d.pdf' % i: _to('Nguyễn Văn An') for i in range(V.MAX_TEP_MOT_LUOT + 1)}
    r = _doc(lop['gv'], lop['id'], _gia_lap(monkeypatch, ds))
    assert r.status_code == 400 and str(V.MAX_TEP_MOT_LUOT) in r.data['error']


def test_khong_chon_tep_thi_bao_ro(lop):
    r = _client(lop['gv']).post(DOC % lop['id'], {}, format='multipart')
    assert r.status_code == 400 and 'PDF' in r.data['error']


# ── Xem trước & ghi ───────────────────────────────────────────────────────

def test_xem_truoc_KHONG_ghi_gi(lop, monkeypatch):
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})
    truoc = _dem_nk(lop['gv'])
    r = _ghi(lop['gv'], lop['id'], phieu)
    assert r.status_code == 200, r.data
    assert r.data['daGhi'] == 0
    assert r.data['tomTat'] == {'tong': 1, 'sanSang': 1, 'chuaKhop': 0,
                                'boQua': 0, 'trung': 0, 'seGhiDe': 0}
    assert r.data['dong'][0]['userId'] == lop['em'].id
    assert _dem_kq(lop['em'].id) == 0, 'xem trước mà ghi là hỏng đúng thứ nó sinh ra để chặn'
    assert _dem_nk(lop['gv']) == truoc, 'xem trước không được ghi cả nhật ký'


def test_ghi_that_dung_mot_dong_dung_so(lop, monkeypatch):
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})
    truoc = _dem_nk(lop['gv'])
    r = _ghi(lop['gv'], lop['id'], phieu, ghi=True)
    assert r.status_code == 200 and r.data['daGhi'] == 1
    row = q1('SELECT * FROM ket_qua_thi_ngoai WHERE user_id=%s', (lop['em'].id,))
    assert row['tong_diem'] == 105 and row['tong_toi_da'] == 150
    assert row['dot'] == 'Online 2308' and row['ngay_thi'] == date(2026, 8, 23)
    # Con trỏ SQL thô trả cột `jsonb` dưới dạng CHUỖI, nên phải đọc lại trước khi
    # đếm — `len()` trên chuỗi đếm ký tự và ra 264, một con số trông như dữ liệu.
    assert len(_json(row['don_vi'])) == 3 and len(_json(row['diem_phan'])) == 3
    assert row['ten_tren_to'] == 'Nguyễn Văn An', 'giữ tên IN TRÊN TỜ để đối chiếu về sau'
    assert row['nhap_boi'] == lop['gv'].id
    assert _dem_nk(lop['gv']) == truoc + 1, 'một dòng nhật ký cho cả lượt'


def test_ghi_la_CHUOI_true_thi_KHONG_ghi(lop, monkeypatch):
    """Ghi là việc phải nói RÕ: `"true"` hay `1` không phải `true`."""
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})
    for gia in ('true', 1, '1'):
        r = _client(lop['gv']).post(GHI % lop['id'], {'phieu': phieu, 'ghi': gia}, format='json')
        assert r.status_code == 200 and r.data['daGhi'] == 0, gia
    assert _dem_kq(lop['em'].id) == 0


def test_nhap_lai_thi_GHI_DE_khong_de_them_luot_ma(lop, monkeypatch):
    p1 = _phieu(lop['gv'], lop['id'], monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})
    _ghi(lop['gv'], lop['id'], p1, ghi=True)
    p2 = _phieu(lop['gv'], lop['id'], monkeypatch, {'an.pdf': _to('Nguyễn Văn An', tong=118)})
    xem = _ghi(lop['gv'], lop['id'], p2)
    assert xem.data['tomTat']['seGhiDe'] == 1, 'phải báo TRƯỚC là sẽ ghi đè'
    _ghi(lop['gv'], lop['id'], p2, ghi=True)
    assert _dem_kq(lop['em'].id) == 1, 'vẫn đúng một lượt'
    assert q1('SELECT tong_diem FROM ket_qua_thi_ngoai WHERE user_id=%s',
              (lop['em'].id,))['tong_diem'] == 118


def test_ten_khong_co_trong_lop_thi_khong_doan(lop, monkeypatch):
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {'x.pdf': _to('Trần Thị Người Lạ')})
    r = _ghi(lop['gv'], lop['id'], phieu, ghi=True)
    assert r.data['tomTat']['chuaKhop'] == 1 and r.data['daGhi'] == 0
    assert 'Không có em nào' in r.data['dong'][0]['ghiChu']
    assert _dem_kq(lop['em'].id) == 0


def test_thieu_dau_van_khop_nhung_phai_bao(lop, monkeypatch):
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {'an.pdf': _to('Nguyen Van An')})
    d = _ghi(lop['gv'], lop['id'], phieu).data['dong'][0]
    assert d['userId'] == lop['em'].id
    assert 'bỏ dấu' in d['ghiChu'], 'khớp nới thì phải nói ra để người nhập kiểm lại'


# ── Chọn tay ──────────────────────────────────────────────────────────────

def test_trung_ten_thi_khong_doan_nhung_CHON_TAY_thi_ghi_dung_em(lop, monkeypatch):
    em2 = _nguoi('Nguyễn Văn An', ROLE_STUDENT, 'an2_nkq@example.com')
    _vao_lop(lop['id'], em2)
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})

    r = _ghi(lop['gv'], lop['id'], phieu, ghi=True)
    assert r.data['dong'][0]['trangThai'] == 'chua-khop' and 'cùng tên' in r.data['dong'][0]['ghiChu']
    assert _dem_kq(lop['em'].id) == 0 and _dem_kq(em2.id) == 0

    r = _ghi(lop['gv'], lop['id'], phieu, chon={'0': em2.id}, ghi=True)
    assert r.status_code == 200 and r.data['daGhi'] == 1
    assert r.data['dong'][0]['chonTay'] is True and r.data['dong'][0]['khopTuDong'] is None
    assert _dem_kq(em2.id) == 1 and _dem_kq(lop['em'].id) == 0, 'đúng em ĐÃ CHỌN, không phải em kia'


def test_chon_tay_ten_khac_ho_so_thi_bao_kiem_lai(lop, monkeypatch):
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {'x.pdf': _to('Trần Thị Người Lạ')})
    d = _ghi(lop['gv'], lop['id'], phieu, chon={'0': lop['em'].id}).data['dong'][0]
    assert d['trangThai'] == 'san-sang' and 'khác tên' in d['ghiChu']


def test_bo_qua_mot_to_thi_khong_ghi_to_do(lop, monkeypatch):
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})
    r = _ghi(lop['gv'], lop['id'], phieu, chon={'0': 0}, ghi=True)
    assert r.data['dong'][0]['trangThai'] == 'bo-qua' and r.data['tomTat']['boQua'] == 1
    assert r.data['daGhi'] == 0 and _dem_kq(lop['em'].id) == 0


def test_chon_tay_hoc_vien_NGOAI_lop_bi_tu_choi_ca_luot(lop, monkeypatch):
    """Bỏ qua lặng lẽ thì tờ kia VẪN được ghi, và người bấm tưởng cả hai đã vào."""
    ngoai = _nguoi('Em Lop Khac', ROLE_STUDENT, 'ngoai_nkq@example.com')
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {
        'an.pdf': _to('Nguyễn Văn An'), 'la.pdf': _to('Trần Thị Người Lạ', tong=90)})
    r = _ghi(lop['gv'], lop['id'], phieu, chon={'1': ngoai.id}, ghi=True)
    assert r.status_code == 400 and 'không thuộc lớp' in r.data['error']
    assert _dem_kq(lop['em'].id) == 0 and _dem_kq(ngoai.id) == 0


def test_em_DA_ROI_LOP_khong_gay_trung_ten_va_khong_chon_duoc(lop, monkeypatch):
    """Danh sách khớp là học viên ĐANG học (`left_at IS NULL`), như mọi đường ghi
    khác của khu giảng dạy (điểm danh, chấm bài). Bản đầu lấy cả em đã rời lớp:
    một em cùng tên đã chuyển đi làm tờ của em đang học thành "trùng tên", và ô
    "Ghi cho" mời ghi điểm vào hồ sơ một em không còn ở lớp."""
    cu = _nguoi('Nguyễn Văn An', ROLE_STUDENT, 'an_cu_nkq@example.com')
    x('INSERT INTO class_members (class_id, user_id, joined_at, left_at) VALUES (%s,%s,%s,%s)',
      (lop['id'], cu.id, local_now() - timedelta(days=60), local_now() - timedelta(days=30)))
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})

    r = _ghi(lop['gv'], lop['id'], phieu)
    assert r.data['dong'][0]['userId'] == lop['em'].id, r.data['dong'][0]['ghiChu']
    assert cu.id not in [e['id'] for e in r.data['hocVienTrongLop']]

    r = _ghi(lop['gv'], lop['id'], phieu, chon={'0': cu.id}, ghi=True)
    assert r.status_code == 400 and 'không thuộc lớp' in r.data['error']
    assert _dem_kq(cu.id) == 0 and _dem_kq(lop['em'].id) == 0


def test_chon_tay_gia_tri_la_true_bi_tu_choi(lop, monkeypatch):
    """Giá trị chọn tay không phải số nguyên → 400, không ghi.

    Riêng `true`: phép kiểm này KHÔNG canh được dòng chặn `bool` — đột biến 16/09
    gỡ dòng ấy mà nó vẫn xanh (`true` → #1 → "không thuộc lớp" → vẫn 400). Dòng
    ấy do `test_doc_chon_true_KHONG_thanh_hoc_vien_so_1` canh.
    """
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})
    for gia in (True, '7', 1.5, None):
        r = _ghi(lop['gv'], lop['id'], phieu, chon={'0': gia}, ghi=True)
        assert r.status_code == 400, gia
    assert _ghi(lop['gv'], lop['id'], phieu, chon={'5': 0}).status_code == 400, 'không có tờ thứ 6'
    assert _dem_kq(lop['em'].id) == 0


def test_doc_chon_true_KHONG_thanh_hoc_vien_so_1():
    """Đi thẳng vào `_doc_chon`, không qua URL.

    Qua URL thì `true` → #1 → "không thuộc lớp" → vẫn 400, vì học viên #1 không
    nằm trong lớp dựng cho phép kiểm. Tức phép kiểm ở trên XANH cả khi thiếu
    dòng chặn `bool`. Ở đây lớp CÓ học viên #1, nên chỉ dòng chặn ấy cứu được.
    """
    with pytest.raises(ValueError):
        V._doc_chon({'0': True}, {1}, 1)
    assert V._doc_chon({'0': 1}, {1}, 1) == {0: 1}, 'số 1 thật thì vẫn nhận'


def test_hai_to_roi_vao_mot_em_cung_ky_thi_KHONG_ghi_to_nao(lop, monkeypatch):
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {
        'an.pdf': _to('Nguyễn Văn An'), 'la.pdf': _to('Trần Thị Người Lạ', tong=90)})
    r = _ghi(lop['gv'], lop['id'], phieu, chon={'1': lop['em'].id}, ghi=True)
    assert [d['trangThai'] for d in r.data['dong']] == ['trung', 'trung']
    assert r.data['daGhi'] == 0 and _dem_kq(lop['em'].id) == 0, \
        'ghi cả hai là tờ sau đè tờ trước, im lặng'


def test_cung_em_KHAC_ky_thi_thi_ghi_ca_hai(lop, monkeypatch):
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {
        't8.pdf': _to('Nguyễn Văn An'),
        't9.pdf': _to('Nguyễn Văn An', tong=112, ngay=date(2026, 9, 13), dot='Online 1309')})
    r = _ghi(lop['gv'], lop['id'], phieu, ghi=True)
    assert r.data['daGhi'] == 2 and _dem_kq(lop['em'].id) == 2


# ── Phiếu ─────────────────────────────────────────────────────────────────

def test_phieu_gia_hoac_bi_sua_thi_tu_choi(lop, monkeypatch):
    that = _phieu(lop['gv'], lop['id'], monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})[0]
    to = _to('Nguyễn Văn An', tong=150)
    gia = signing.dumps({'c': lop['id'], 'u': lop['gv'].id, 'tep': 'an.pdf',
                         'd': {**to, 'ngayThi': to['ngayThi'].isoformat()}},
                        salt=V._MUOI_PHIEU, key='khong-phai-SECRET_KEY-that', compress=True)
    giua = len(that) // 3
    sua = that[:giua] + ('A' if that[giua] != 'A' else 'B') + that[giua + 1:]
    for p in (gia, sua, 12345):
        r = _ghi(lop['gv'], lop['id'], [p], ghi=True)
        assert r.status_code == 400 and 'Phiếu' in r.data['error'], p
    assert _dem_kq(lop['em'].id) == 0


def test_phieu_qua_han_bi_tu_choi(lop, monkeypatch):
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})
    monkeypatch.setattr(V, 'TUOI_PHIEU', -1)
    r = _ghi(lop['gv'], lop['id'], phieu, ghi=True)
    assert r.status_code == 400 and 'quá' in r.data['error']
    assert _dem_kq(lop['em'].id) == 0


def test_phieu_cua_LOP_KHAC_bi_tu_choi(lop, monkeypatch):
    """Cùng giảng viên, cùng em, nhưng phiếu đọc ở lớp kia — chữ ký thật mà sai chỗ."""
    lop2 = _lop('Lop nhap KQ 2', lop['gv'])
    _vao_lop(lop2, lop['em'])
    phieu = _phieu(lop['gv'], lop2, monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})
    r = _ghi(lop['gv'], lop['id'], phieu, ghi=True)
    assert r.status_code == 400 and 'không thuộc lớp này' in r.data['error']
    assert _dem_kq(lop['em'].id) == 0


def test_phieu_cua_NGUOI_KHAC_bi_tu_choi(lop, monkeypatch):
    qtv = _nguoi('QTV Nhap KQ', ROLE_ADMIN, 'qtv_nkq@example.com')
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})
    r = _ghi(qtv, lop['id'], phieu, ghi=True)
    assert r.status_code == 400 and 'không do bạn đọc' in r.data['error']
    assert _dem_kq(lop['em'].id) == 0


def test_ghi_khong_co_phieu_thi_bao_ro(lop):
    c = _client(lop['gv'])
    assert c.post(GHI % lop['id'], {}, format='json').status_code == 400
    assert c.post(GHI % lop['id'], [1, 2], format='json').status_code == 400, 'thân là mảng'
    r = c.post(GHI % lop['id'], {'phieu': ['x'] * (V.MAX_PHIEU + 1)}, format='json')
    assert r.status_code == 400 and str(V.MAX_PHIEU) in r.data['error']


# ── Phân quyền ────────────────────────────────────────────────────────────

def test_tro_giang_khong_cham_duoc(lop, monkeypatch):
    tg = _nguoi('TG Nhap KQ', ROLE_ASSISTANT, 'tg_nkq@example.com')
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})
    tep = _gia_lap(monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})
    assert _doc(tg, lop['id'], tep).status_code == 403
    assert _ghi(tg, lop['id'], phieu, ghi=True).status_code == 403
    assert _dem_kq(lop['em'].id) == 0


def test_giang_vien_lop_khac_nhan_404(lop, monkeypatch):
    gv2 = _nguoi('GV Khac NKQ', ROLE_TEACHER, 'gvkhac_nkq@example.com')
    phieu = _phieu(lop['gv'], lop['id'], monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})
    tep = _gia_lap(monkeypatch, {'an.pdf': _to('Nguyễn Văn An')})
    assert _doc(gv2, lop['id'], tep).status_code == 404, 'không lộ ra rằng lớp này có tồn tại'
    assert _ghi(gv2, lop['id'], phieu, ghi=True).status_code == 404
    assert _dem_kq(lop['em'].id) == 0
