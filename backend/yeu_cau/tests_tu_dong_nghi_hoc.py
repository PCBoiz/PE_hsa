"""DUYỆT = TỰ LÀM cho "xin nghỉ học" và "xin học bù" (bảng TopHSA dòng 12).

Bảng ghi *"MỘT PHẦN (E3: duyệt = tự làm 5/8 loại)"*. Ba loại còn để tay:
`tt_chuyen_lich`, `tt_hoc_bu`, `tt_nghi_hoc` — học vụ bấm Duyệt xong vẫn phải đi làm tay
ở một màn khác, và **không gì bắt họ nhớ**. Yêu cầu đóng lại, còn việc thì chưa ai làm.

── HAI LOẠI TỰ LÀM ĐƯỢC, MỘT LOẠI KHÔNG ─────────────────────────────────────

  · **`tt_nghi_hoc`** → ghi "có phép" (`excused`) vào sổ điểm danh cho các buổi em xin
    nghỉ. Rõ ràng, không cần người quyết gì thêm.
  · **`tt_hoc_bu`** → xếp em vào MỘT buổi bù đã có (`session_participants`, §62e). Buổi
    bù phải tồn tại sẵn — tạo buổi mới là việc xếp lịch, cần người nhìn cả lớp.
  · **`tt_chuyen_lich`** vẫn để TAY, và đó là quyết định chứ không phải bỏ sót: "chuyển
    lịch" ở TopHSA nghĩa là đổi giờ học của em, mà đổi đi đâu thì phụ thuộc lớp nào còn
    chỗ, giờ nào em học được, giảng viên nào dạy — ba thứ hệ thống không biết. Tự đoán
    một lớp rồi xếp em vào là làm hỏng nhiều hơn làm được. `VIEC_TAY` nói rõ việc ấy.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. Duyệt "xin nghỉ học" → các buổi trong khoảng ngày thành `excused`, và `thuc_thi`
     ghi rõ đã đánh dấu mấy buổi.
  2. Buổi NGOÀI khoảng ngày không bị đụng tới.
  3. Buổi em đã có điểm danh khác (`present`) thì **ghi đè thành `excused`** — học vụ
     duyệt đơn nghỉ phép là quyết định cuối cùng, nhưng `thuc_thi` phải nói ra là đã ghi
     đè, để còn lần lại được.
  4. Duyệt "xin học bù" → em có tên trong `session_participants` của buổi bù ấy.
  5. Xếp vào buổi KHÔNG phải buổi bù → từ chối, kèm câu nói rõ vì sao.
  6. Duyệt lần hai → 409, và KHÔNG làm lại việc (cùng luật với năm loại đã có).
  7. Việc hỏng → cuộn lại hết: yêu cầu KHÔNG ở trạng thái đã duyệt.

Chạy trên CSDL thật, giao dịch CUỘN LẠI; chỉ đếm dữ liệu của chính mình.
"""
from datetime import timedelta

import pytest

from accounts.models import User
from common.clock import local_now, local_today
from common.db import q, q1, x
from common.permissions import ROLE_ACADEMIC, ROLE_STUDENT, ROLE_TEACHER
from yeu_cau import dich_vu
from yeu_cau.dich_vu import LoiYeuCau

pytestmark = pytest.mark.django_db


def _nguoi(ten, vai):
    r = q1("INSERT INTO users (name, email, password, role, streak) "
           "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
           (ten, '%s_td@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=r['id'])


def _buoi(lop, cach_ngay):
    """Buổi cách hôm nay `cach_ngay` ngày (âm = đã qua)."""
    return q1('''INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status)
                 VALUES (%s, %s, 90, 'planned') RETURNING id''',
              (lop, local_now() + timedelta(days=cach_ngay)))['id']


@pytest.fixture
def canh():
    gv = _nguoi('GV Tu Dong', ROLE_TEACHER)
    hv = _nguoi('Hoc Vu Tu Dong', ROLE_ACADEMIC)
    em = _nguoi('Em Tu Dong', ROLE_STUDENT)
    lop = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
             "VALUES ('Lop tu dong', 'hsa_quantitative', %s, 'active') RETURNING id",
             (gv.id,))['id']
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s)',
      (lop, em.id, local_now() - timedelta(days=30)))
    return {'gv': gv, 'hv': hv, 'em': em, 'lop': lop}


def _lam(u):
    """`NguoiLam` bọc một tài khoản — cùng thứ mà view truyền vào `dich_vu.duyet`."""
    return dich_vu.NguoiLam(user=u)


def _tao(canh, loai, du_lieu=None, session_id=None):
    """Tạo thẳng một yêu cầu ở trạng thái chờ duyệt (không đi qua cửa gửi của học viên)."""
    import json
    return q1('''INSERT INTO yeu_cau (loai, trang_thai, nguon, nguoi_tao, hoc_vien_id,
                                      class_id, session_id, tieu_de, du_lieu)
                 VALUES (%s, 'moi', 'hoc_vien', %s, %s, %s, %s, %s, %s::jsonb) RETURNING id''',
              (loai, canh['em'].id, canh['em'].id, canh['lop'], session_id,
               'Thu ' + loai, json.dumps(du_lieu or {})))['id']


def _duyet(canh, yc_id, tham_so=None):
    return dich_vu.duyet(_lam(canh['hv']), yc_id, tham_so or {})


def _diem_danh(buoi):
    return {r['user_id']: r['status'] for r in
            q('SELECT user_id, status FROM attendance WHERE session_id = %s', (buoi,))}


# ── 1. Xin nghỉ học → ghi "có phép" ─────────────────────────────────────────

def test_duyet_nghi_hoc_ghi_co_phep_cho_buoi_trong_khoang(canh):
    b1, b2 = _buoi(canh['lop'], 2), _buoi(canh['lop'], 4)
    tu = local_today() + timedelta(days=1)
    den = local_today() + timedelta(days=5)
    yc = _tao(canh, 'tt_nghi_hoc', {'tu_ngay': tu.isoformat(), 'den_ngay': den.isoformat()})
    _duyet(canh, yc)
    for b in (b1, b2):
        assert _diem_danh(b).get(canh['em'].id) == 'excused', 'buổi %s chưa được ghi có phép' % b


def test_buoi_ngoai_khoang_ngay_khong_bi_dung(canh):
    trong = _buoi(canh['lop'], 2)
    ngoai = _buoi(canh['lop'], 20)
    tu = local_today() + timedelta(days=1)
    den = local_today() + timedelta(days=5)
    _duyet(canh, _tao(canh, 'tt_nghi_hoc', {'tu_ngay': tu.isoformat(), 'den_ngay': den.isoformat()}))
    assert _diem_danh(trong).get(canh['em'].id) == 'excused'
    assert canh['em'].id not in _diem_danh(ngoai), 'buổi ngoài khoảng ngày bị đụng tới'


def test_thuc_thi_noi_ro_may_buoi_va_may_buoi_bi_ghi_de(canh):
    """Ghi đè một lượt điểm danh đã có là quyết định cuối của học vụ — nhưng phải NÓI RA."""
    b1 = _buoi(canh['lop'], 2)
    _buoi(canh['lop'], 3)
    x('''INSERT INTO attendance (session_id, user_id, status) VALUES (%s,%s,'present')''',
      (b1, canh['em'].id))
    tu = local_today() + timedelta(days=1)
    den = local_today() + timedelta(days=5)
    yc = _tao(canh, 'tt_nghi_hoc', {'tu_ngay': tu.isoformat(), 'den_ngay': den.isoformat()})
    _duyet(canh, yc)
    tt = q1('SELECT thuc_thi FROM yeu_cau WHERE id = %s', (yc,))['thuc_thi']
    import json
    tt = tt if isinstance(tt, dict) else json.loads(tt)
    assert tt['cach'] == 'tu_dong'
    assert tt.get('soBuoi') == 2, tt
    assert tt.get('ghiDe') == 1, 'không nói ra là đã ghi đè một lượt điểm danh đã có'


def test_khong_co_buoi_nao_trong_khoang_thi_tu_choi(canh):
    """Duyệt một đơn không làm gì cả thì đóng yêu cầu mà chẳng thay đổi gì — nói thẳng hơn."""
    _buoi(canh['lop'], 30)
    tu = local_today() + timedelta(days=1)
    den = local_today() + timedelta(days=5)
    yc = _tao(canh, 'tt_nghi_hoc', {'tu_ngay': tu.isoformat(), 'den_ngay': den.isoformat()})
    with pytest.raises(LoiYeuCau):
        _duyet(canh, yc)
    assert q1('SELECT trang_thai FROM yeu_cau WHERE id = %s', (yc,))['trang_thai'] == 'moi'


# ── 2. Xin học bù → xếp em vào buổi bù ──────────────────────────────────────

def _buoi_bu(lop, goc):
    """Buổi BÙ: có `session_participants` nên chỉ những em được xếp mới thuộc buổi."""
    b = _buoi(lop, 7)
    x('UPDATE class_sessions SET makeup_of = %s WHERE id = %s', (goc, b)) \
        if q1("SELECT 1 FROM information_schema.columns WHERE table_name='class_sessions' "
              "AND column_name='makeup_of'") else None
    # Dấu hiệu chắc chắn của buổi bù: có ít nhất một dòng `session_participants`.
    khac = q1("INSERT INTO users (name, email, password, role, streak) "
              "VALUES ('Em Khac Bu', 'em_khac_bu_td@example.com', 'x', %s, 0) RETURNING id",
              (ROLE_STUDENT,))['id']
    x('INSERT INTO session_participants (session_id, user_id) VALUES (%s,%s)', (b, khac))
    return b


def test_duyet_hoc_bu_xep_em_vao_buoi_bu(canh):
    goc = _buoi(canh['lop'], -3)
    bu = _buoi_bu(canh['lop'], goc)
    yc = _tao(canh, 'tt_hoc_bu', session_id=bu)
    _duyet(canh, yc)
    co = q1('SELECT 1 AS c FROM session_participants WHERE session_id=%s AND user_id=%s',
            (bu, canh['em'].id))
    assert co, 'em không được xếp vào buổi bù'


def test_xep_vao_buoi_khong_phai_buoi_bu_thi_tu_choi(canh):
    """Buổi thường thì CẢ LỚP đã thuộc buổi — xếp thêm là vô nghĩa, và `session_participants`
    xuất hiện sẽ biến buổi thường thành buổi bù của đúng một em."""
    thuong = _buoi(canh['lop'], 7)
    yc = _tao(canh, 'tt_hoc_bu', session_id=thuong)
    with pytest.raises(LoiYeuCau):
        _duyet(canh, yc)
    assert q1('SELECT trang_thai FROM yeu_cau WHERE id = %s', (yc,))['trang_thai'] == 'moi'


def test_hoc_bu_khong_gan_buoi_thi_tu_choi(canh):
    yc = _tao(canh, 'tt_hoc_bu')
    with pytest.raises(LoiYeuCau):
        _duyet(canh, yc)


def test_duyet_lan_hai_khong_lam_lai_viec(canh):
    b = _buoi(canh['lop'], 2)
    tu = local_today() + timedelta(days=1)
    den = local_today() + timedelta(days=5)
    yc = _tao(canh, 'tt_nghi_hoc', {'tu_ngay': tu.isoformat(), 'den_ngay': den.isoformat()})
    _duyet(canh, yc)
    with pytest.raises(LoiYeuCau):
        _duyet(canh, yc)
    assert len(q('SELECT 1 FROM attendance WHERE session_id=%s AND user_id=%s',
                 (b, canh['em'].id))) == 1


# ── 3. Chuyển lịch vẫn để TAY — và đó là quyết định ─────────────────────────

def test_chuyen_lich_van_la_viec_tay(canh):
    """Không tự đoán lớp / giờ thay cho người: hệ thống không biết lớp nào còn chỗ, em học
    được giờ nào, giảng viên nào dạy."""
    import json
    yc = _tao(canh, 'tt_chuyen_lich')
    _duyet(canh, yc)
    tt = q1('SELECT thuc_thi FROM yeu_cau WHERE id = %s', (yc,))['thuc_thi']
    tt = tt if isinstance(tt, dict) else json.loads(tt)
    assert tt['cach'] == 'tay'
    assert 'Buổi học' in tt['mo_ta'] or 'lịch' in tt['mo_ta'].lower()


# ── 4. Xem trước phải nói ĐÚNG việc sắp làm ─────────────────────────────────

def test_xem_truoc_moi_loai_tu_dong_deu_noi_dung_viec_cua_no(canh):
    """`xem_truoc` từng viết `else:  # tt_hoc_lai` — một nhánh bắt HẾT.

    Nên hai loại thêm ngày 27/09 rơi thẳng vào đó: màn duyệt "xin học bù" hiện câu "Xếp em
    vào LẠI lớp …". Người duyệt đọc một việc rồi bấm, hệ thống làm việc khác, và không gì
    báo cho họ biết. Đo được trên màn thật trước khi vá.

    Phép kiểm này đi qua TỪNG loại tự động, nên loại thứ mười thêm vào mà quên bản xem
    trước sẽ đỏ ở đây chứ không đỏ trong đầu một người dùng thật.
    """
    from yeu_cau import loai as L
    from yeu_cau.thuc_thi import xem_truoc
    b = _buoi(canh['lop'], 3)
    x('INSERT INTO session_participants (session_id, user_id) VALUES (%s,%s)',
      (b, _nguoi('Em Cho Buoi Bu', ROLE_STUDENT).id))
    mau = {
        'tt_nghi_hoc': ('có phép', {'tu_ngay': local_today().isoformat()}),
        'tt_hoc_bu': ('buổi bù', {'session_id': b}),
        'tt_hoc_lai': ('vào lại lớp', {}),
        'tt_bao_luu': ('bảo lưu', {}),
        'tt_huy_khoa': ('bỏ giữa chừng', {}),
    }
    for lo, (tu_khoa, tham) in mau.items():
        assert L.LOAI[lo].get('viec') == 'tu_dong', lo
        yc = q1('SELECT * FROM yeu_cau WHERE id = %s', (_tao(canh, lo),))
        d = dict(yc)
        d['du_lieu'] = d['du_lieu'] if isinstance(d['du_lieu'], dict) else {}
        kq = xem_truoc(d, tham)
        assert kq['moTa'], (lo, kq)
        assert tu_khoa in kq['moTa'].lower(), \
            'xem trước của "%s" nói: %r — không có "%s"' % (lo, kq['moTa'], tu_khoa)
