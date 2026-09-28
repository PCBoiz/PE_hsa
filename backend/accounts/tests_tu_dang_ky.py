"""HỌC VIÊN TỰ ĐĂNG KÝ (§73, E5 — dòng 26 bảng TopHSA) — `accounts/tu_dang_ky.py`.

Đi ĐÚNG ĐƯỜNG người thật đi (RULES §19): mọi bước qua bộ định tuyến HTTP
(`APIClient`), mã xác thực đọc RA TỪ LÁ THƯ chứ không lấy từ CSDL, và trạng thái
sau mỗi bước cũng hỏi lại bằng CỬA API (đăng nhập được chưa, học vụ có thấy trong
hộp Yêu cầu chưa) — không phải bằng một câu `SELECT` riêng.

Vì sao không đọc thẳng bảng để xác nhận: câu `SELECT` của phép kiểm đi bằng một
KẾT NỐI KHÁC với lời gọi API, nên nó xanh khi chạy một mình và đỏ khi chạy cả bộ.
Chỗ nào vẫn đọc bảng thì chỉ để đối chiếu *bản ghi* (cột nào được đặt), không để
kết luận về *hành vi*.

Thư đi ở CHẾ ĐỘ THỬ (ghi `.eml` vào thư mục tạm, không mở SMTP nào). Chạy trong
giao dịch cuộn lại (`conftest.py`) và chỉ đếm dữ liệu của chính nó.
"""
import email
import re
import uuid

import pytest
from rest_framework.test import APIClient

from accounts import quen_mat_khau, tu_dang_ky
from accounts.hashers import make_werkzeug_password
from common.db import q, q1
from common.permissions import ROLE_ACADEMIC, ROLE_STUDENT

MK = 'MatKhauMoi#2026'
GOC = 'https://vi-du.tophsa.test'


def _dc():
    """Một địa chỉ / số mới mỗi lần — hai lượt chạy song song không tranh chỉ mục duy nhất."""
    r = uuid.uuid4().hex[:10]
    return 'dk_%s@example.com' % r, '09' + str(int(r[:8], 16))[:8].rjust(8, '1')


@pytest.fixture
def thu(db, tmp_path, monkeypatch, settings):
    monkeypatch.setenv('EMAIL_CHE_DO_THU', '1')
    monkeypatch.setenv('EMAIL_THU_MUC_THU', str(tmp_path))
    monkeypatch.setattr(tu_dang_ky, 'GUI_NGAY', True)
    monkeypatch.setattr(quen_mat_khau, 'GUI_NGAY', True)
    settings.FRONTEND_URL = GOC
    return tmp_path


@pytest.fixture
def hoc_vu(db):
    r = q1('INSERT INTO users (name, email, password, role, streak) '
           'VALUES (%s, %s, %s, %s, 0) RETURNING id',
           ('Học vụ E5', 'hv_e5_%s@example.com' % uuid.uuid4().hex[:8],
            make_werkzeug_password(MK), ROLE_ACADEMIC))
    return r['id']


@pytest.fixture
def hoc_vu_api(hoc_vu):
    from accounts.models import User
    c = APIClient()
    c.force_authenticate(user=User.objects.get(id=hoc_vu))
    return c


@pytest.fixture
def lop(db):
    return q1("INSERT INTO classes (name, status) VALUES (%s, 'active') RETURNING id",
              ('Lớp E5 %s' % uuid.uuid4().hex[:6],))['id']


def _than(**doi):
    """Phiếu đăng ký hợp lệ; `**doi` GHI ĐÈ từng ô (kể cả đè bằng chuỗi rỗng — nên không
    dùng `x or mặc_định`, cái bẫy làm phép kiểm "thiếu số điện thoại" xanh giả)."""
    e, p = _dc()
    d = {'name': 'Em Tự Đăng Ký', 'email': e, 'phone': p,
         'password': MK, 'nguon': 'facebook', 'truong': 'THPT Chu Văn An',
         'lopOTruong': '12', 'mucTieu': 'Thi HSA 100+'}
    d.update({k: v for k, v in doi.items() if v is not None})
    return d


def _dang_ky(than):
    return APIClient().post('/auth/dang-ky', than, format='json')


def _dang_nhap(email_, mk=MK):
    return APIClient().post('/auth/login', {'email': email_, 'password': mk}, format='json')


def _thu_cuoi(thu_muc):
    tep = sorted(thu_muc.glob('*.eml'))
    assert tep, 'không có lá thư nào'
    m = email.message_from_bytes(tep[-1].read_bytes())
    chu = ''
    for phan in m.walk():
        if phan.get_content_type() == 'text/plain':
            chu = phan.get_payload(decode=True).decode(phan.get_content_charset() or 'utf-8')
    return m, chu


def _chia_xac_thuc(thu_muc):
    """Mã xác thực đọc RA TỪ THƯ — đúng đường em bấm."""
    m, chu = _thu_cuoi(thu_muc)
    d = re.search(r'\S+/xac-thuc-email#chia=([A-Za-z0-9_\-]+)', chu)
    assert d, 'thư không có đường dẫn xác thực: %r' % chu[:400]
    return m, d.group(1)


def _xac_thuc(chia):
    return APIClient().post('/auth/xac-thuc-email', {'chia': chia}, format='json')


def _uid(email_):
    r = q1('SELECT id FROM users WHERE lower(email)=%s', (email_.lower(),))
    return r['id'] if r else None


# ── Cửa đăng ký ─────────────────────────────────────────────────────────────

def test_dang_ky_tao_tai_khoan_hoc_vien_chua_xac_thuc(thu):
    t = _than()
    r = _dang_ky(t)
    assert r.status_code == 200, r.data
    assert r.data['message'] == tu_dang_ky.CAU_CHUNG
    # Không cấp phiên: em chưa chứng minh giữ được hộp thư ấy.
    assert 'access' not in r.data and 'refresh' not in r.data
    u = q1('SELECT role, self_registered, is_verified, phone, enroll_source, school, '
           'school_grade, study_goal, student_code, must_change_password '
           'FROM users WHERE lower(email)=%s', (t['email'],))
    assert u['role'] == ROLE_STUDENT
    assert u['self_registered'] is True
    assert not u['is_verified']
    assert u['phone'] == t['phone']
    assert u['enroll_source'] == 'facebook'
    assert u['school'] == 'THPT Chu Văn An' and u['school_grade'] == '12'
    assert u['study_goal'] == 'Thi HSA 100+'
    assert u['student_code'], 'học viên nào cũng phải có mã HV (§51)'
    assert not u['must_change_password'], 'em tự chọn mật khẩu, không ai cấp tạm'


def test_chua_xac_thuc_thi_KHONG_dang_nhap_duoc_va_cau_loi_noi_cach_sua(thu):
    t = _than()
    assert _dang_ky(t).status_code == 200
    r = _dang_nhap(t['email'])
    assert r.status_code == 403, 'tài khoản chưa xác thực phải bị chặn ở cửa đăng nhập'
    cau = r.data.get('error') or ''
    assert 'xác' in cau.lower(), cau
    assert '@' not in cau and '_' not in cau, 'câu lỗi không được in mã kỹ thuật (RULES §10)'


def test_xac_thuc_xong_thi_dang_nhap_duoc(thu):
    t = _than()
    _dang_ky(t)
    m, chia = _chia_xac_thuc(thu)
    assert m['To'].endswith(t['email'])
    assert _xac_thuc(chia).status_code == 200
    r = _dang_nhap(t['email'])
    assert r.status_code == 200, r.data
    assert r.data['role'] == ROLE_STUDENT


def test_chia_xac_thuc_dung_mot_lan(thu):
    t = _than()
    _dang_ky(t)
    _, chia = _chia_xac_thuc(thu)
    assert _xac_thuc(chia).status_code == 200
    lai = _xac_thuc(chia)
    assert lai.status_code == 400
    assert 'hết hạn' in (lai.data.get('error') or '')


def test_chia_bia_ra_khong_qua_duoc(thu):
    assert _xac_thuc('khong-phai-chia-cua-ai').status_code == 400


def test_tai_khoan_TRUNG_TAM_CAP_khong_bi_hang_rao_moi_chan(thu):
    """Hàng rào chỉ chặn `self_registered AND NOT is_verified`. Tài khoản cũ có
    `is_verified` FALSE/NULL vì chưa ai từng ghi cột ấy — chặn theo `is_verified`
    trần là khoá cửa với toàn bộ học viên hiện có."""
    e, _ = _dc()
    q1('INSERT INTO users (name, email, password, role, streak, is_verified) '
       "VALUES ('Em Cũ', %s, %s, %s, 0, FALSE) RETURNING id",
       (e, make_werkzeug_password(MK), ROLE_STUDENT))
    assert _dang_nhap(e).status_code == 200


# ── Không lộ ai có tài khoản ────────────────────────────────────────────────

def test_email_da_co_tai_khoan_tra_loi_Y_HET_va_khong_tao_them(thu):
    e, p1 = _dc()
    _, p2 = _dc()
    q1('INSERT INTO users (name, email, password, role, streak, is_verified) '
       "VALUES ('Em Đã Có', %s, %s, %s, 0, TRUE) RETURNING id",
       (e, make_werkzeug_password(MK), ROLE_STUDENT))
    moi = _dang_ky(_than(phone=p1))
    trung = _dang_ky(_than(email=e, phone=p2))
    assert trung.status_code == moi.status_code == 200
    assert trung.data == moi.data, 'câu trả lời khác nhau là lộ ai có tài khoản ở TopHSA'
    assert q1('SELECT count(*) AS n FROM users WHERE lower(email)=%s', (e.lower(),))['n'] == 1


def test_sdt_da_co_tai_khoan_tra_loi_Y_HET_va_khong_tao(thu):
    e1, p = _dc()
    e2, _ = _dc()
    q1('INSERT INTO users (name, email, phone, password, role, streak) '
       "VALUES ('Em Đã Có SĐT', %s, %s, %s, %s, 0) RETURNING id",
       (e1, p, make_werkzeug_password(MK), ROLE_STUDENT))
    moi = _dang_ky(_than())
    trung = _dang_ky(_than(email=e2, phone=p))
    assert trung.status_code == 200 and trung.data == moi.data
    assert _uid(e2) is None, 'không được tạo tài khoản khi số điện thoại đã thuộc người khác'


def test_dang_ky_lai_tren_email_CHUA_XAC_THUC_thi_nhan_lai_duoc(thu):
    """Tài khoản chưa xác thực không được thành cái chốt cửa: ai gõ bừa email của
    người khác thì người thật vẫn đăng ký lại được trên chính dòng ấy, và mã cũ chết."""
    t = _than()
    _dang_ky(t)
    _, chia_cu = _chia_xac_thuc(thu)
    uid = _uid(t['email'])
    lai = _dang_ky(_than(email=t['email'], name='Người Thật'))
    assert lai.status_code == 200
    assert _uid(t['email']) == uid, 'phải dùng lại dòng cũ, không tạo dòng thứ hai'
    _, chia_moi = _chia_xac_thuc(thu)
    assert chia_moi != chia_cu
    assert _xac_thuc(chia_cu).status_code == 400, 'mã cũ phải chết khi cấp mã mới'
    assert _xac_thuc(chia_moi).status_code == 200


# ── Bẫy §73b: hai việc trên MỘT bảng chìa ───────────────────────────────────

def test_xin_dat_lai_mat_khau_KHONG_huy_ma_xac_thuc(thu):
    """`quen_mat_khau` có ba câu chạm `password_reset_tokens` theo `user_id`. Không lọc
    `purpose='reset'` thì một lượt xin đặt lại mật khẩu huỷ luôn mã xác thực em chưa bấm,
    và em vừa đăng ký xong mất đường vào."""
    t = _than()
    _dang_ky(t)
    _, chia = _chia_xac_thuc(thu)
    r = APIClient().post('/auth/quen-mat-khau', {'email': t['email']}, format='json')
    assert r.status_code == 200
    assert _xac_thuc(chia).status_code == 200, 'mã xác thực bị lượt quên-mật-khẩu huỷ mất'


def test_dat_lai_mat_khau_KHONG_huy_ma_xac_thuc(thu):
    t = _than()
    _dang_ky(t)
    _, chia_xt = _chia_xac_thuc(thu)
    APIClient().post('/auth/quen-mat-khau', {'email': t['email']}, format='json')
    _, chu = _thu_cuoi(thu)
    d = re.search(r'\S+/dat-lai-mat-khau#chia=([A-Za-z0-9_\-]+)', chu)
    assert d, chu[:300]
    assert APIClient().post('/auth/dat-lai-mat-khau',
                            {'chia': d.group(1), 'password': 'KhacHan#2026'},
                            format='json').status_code == 200
    assert _xac_thuc(chia_xt).status_code == 200, 'đặt lại mật khẩu không được huỷ mã xác thực'


def test_ma_xac_thuc_khong_dat_lai_duoc_mat_khau(thu):
    """Ngược lại: mã `verify` không được dùng ở cửa đặt lại mật khẩu — nếu được thì
    chiếm tài khoản chỉ cần một lượt đăng ký trùng email."""
    t = _than()
    _dang_ky(t)
    _, chia = _chia_xac_thuc(thu)
    r = APIClient().post('/auth/dat-lai-mat-khau', {'chia': chia, 'password': 'ChiemTK#2026'},
                         format='json')
    assert r.status_code == 400, 'mã xác thực email không được đổi được mật khẩu'


# ── Gửi lại thư xác thực ────────────────────────────────────────────────────

def test_gui_lai_xac_thuc_cap_ma_moi_va_luon_mot_cau(thu):
    t = _than()
    _dang_ky(t)
    _, chia_cu = _chia_xac_thuc(thu)
    co = APIClient().post('/auth/gui-lai-xac-thuc', {'email': t['email']}, format='json')
    assert co.status_code == 200
    _, chia_moi = _chia_xac_thuc(thu)
    assert chia_moi != chia_cu and _xac_thuc(chia_moi).status_code == 200
    khong = APIClient().post('/auth/gui-lai-xac-thuc', {'email': 'khong_ai_e5@example.com'},
                             format='json')
    assert khong.status_code == 200 and khong.data == co.data


# ── Hàng rào chống lạm dụng ─────────────────────────────────────────────────

def test_tran_theo_IP_chan_lam_hang_loat_tai_khoan(thu):
    """Lớp thứ hai, đếm trong CSDL: bộ đếm tần suất của DRF sống trong bộ nhớ từng
    tiến trình nên khởi động lại là mất, còn trần này thì không."""
    ma = []
    for _ in range(tu_dang_ky.TRAN_IP_MOI_NGAY + 2):
        t = _than()
        ma.append((_dang_ky(t).status_code, t['email']))
    tao_duoc = [e for c, e in ma if c == 200 and _uid(e)]
    assert len(tao_duoc) == tu_dang_ky.TRAN_IP_MOI_NGAY, \
        'tạo được %d tài khoản, trần là %d' % (len(tao_duoc), tu_dang_ky.TRAN_IP_MOI_NGAY)
    # Vượt trần vẫn là CÙNG một câu trả lời — trần không được thành cách dò.
    assert all(c == 200 for c, _ in ma)


@pytest.mark.parametrize('doi,o', [
    ({'name': ''}, 'name'),
    ({'email': 'khong-phai-email'}, 'email'),
    ({'email': ''}, 'email'),
    ({'phone': ''}, 'phone'),
    ({'phone': '123'}, 'phone'),
    ({'password': '123'}, 'password'),
    ({'nguon': 'tu-dau-ra'}, 'nguon'),
])
def test_thieu_hoac_sai_thi_noi_dung_o_nao(thu, doi, o):
    r = _dang_ky(_than(**doi))
    assert r.status_code == 400, r.data
    assert o in (r.data.get('errors') or {}), r.data


# ── Hàng chờ của học vụ = hộp Yêu cầu §65, KHÔNG phải hộp mới ───────────────

def _hang_cho(api):
    r = api.get('/api/teach/yeu-cau?loai=tk_dang_ky')
    assert r.status_code == 200, r.data
    return r.data['yeuCau']


def test_chua_xac_thuc_thi_KHONG_vao_hang_cho_cua_hoc_vu(thu, hoc_vu_api):
    t = _than()
    _dang_ky(t)
    uid = _uid(t['email'])
    assert not [y for y in _hang_cho(hoc_vu_api) if (y['hocVien'] or {}).get('id') == uid], \
        'tài khoản chưa xác thực không được làm bẩn hộp việc của học vụ'


def test_xac_thuc_xong_thi_hien_trong_hang_cho_kem_thong_tin_da_khai(thu, hoc_vu_api):
    t = _than()
    _dang_ky(t)
    _, chia = _chia_xac_thuc(thu)
    _xac_thuc(chia)
    uid = _uid(t['email'])
    cua_em = [y for y in _hang_cho(hoc_vu_api) if (y['hocVien'] or {}).get('id') == uid]
    assert len(cua_em) == 1, 'một lượt đăng ký = đúng một việc trong hàng chờ'
    yc = cua_em[0]
    assert yc['trangThai'] == 'moi' and yc['canDuyet'] is True
    assert yc['loaiNhan'] and yc['loaiNhan'] != 'tk_dang_ky', 'màn phải nhận NHÃN, không nhận mã'
    assert yc['duLieu'].get('sdt') == t['phone']
    assert yc['chonLopToi'] is True, 'màn duyệt cần biết loại này phải chọn lớp'


def test_duyet_dang_ky_thi_em_vao_lop_that(thu, hoc_vu_api, lop):
    t = _than()
    _dang_ky(t)
    _, chia = _chia_xac_thuc(thu)
    _xac_thuc(chia)
    uid = _uid(t['email'])
    yc = [y for y in _hang_cho(hoc_vu_api) if (y['hocVien'] or {}).get('id') == uid][0]
    # Xem trước rồi duyệt — đúng thứ tự học vụ bấm trên màn.
    xt = hoc_vu_api.get('/api/admin/yeu-cau/%d/duyet?den_lop_id=%d' % (yc['id'], lop))
    assert xt.status_code == 200 and xt.data['cach'] == 'tu_dong', xt.data
    r = hoc_vu_api.post('/api/admin/yeu-cau/%d/duyet' % yc['id'], {'den_lop_id': lop},
                        format='json')
    assert r.status_code == 200, r.data
    assert r.data['trangThai'] == 'da_xong'
    assert q1('SELECT 1 AS c FROM class_members WHERE class_id=%s AND user_id=%s '
              'AND left_at IS NULL', (lop, uid)), 'duyệt xong mà em không vào lớp'
    # Duyệt lần hai không được xếp lớp lần hai.
    lai = hoc_vu_api.post('/api/admin/yeu-cau/%d/duyet' % yc['id'], {'den_lop_id': lop},
                          format='json')
    assert lai.status_code == 409
    assert q(('SELECT id FROM class_members WHERE class_id=%s AND user_id=%s'), (lop, uid)).__len__() == 1


def test_duyet_ma_khong_chon_lop_thi_noi_ro(thu, hoc_vu_api):
    t = _than()
    _dang_ky(t)
    _, chia = _chia_xac_thuc(thu)
    _xac_thuc(chia)
    uid = _uid(t['email'])
    yc = [y for y in _hang_cho(hoc_vu_api) if (y['hocVien'] or {}).get('id') == uid][0]
    r = hoc_vu_api.post('/api/admin/yeu-cau/%d/duyet' % yc['id'], {}, format='json')
    assert r.status_code == 400 and 'lớp' in (r.data.get('error') or '').lower(), r.data


def test_hoc_vien_khong_tu_gui_duoc_loai_dang_ky(thu, lop):
    """`tk_dang_ky` chỉ sinh ra ở cửa xác thực email. Để em tự gửi được thì hàng chờ
    xếp lớp thành một đường ai cũng nhét việc vào được."""
    from accounts.models import User
    t = _than()
    _dang_ky(t)
    _, chia = _chia_xac_thuc(thu)
    _xac_thuc(chia)
    c = APIClient()
    c.force_authenticate(user=User.objects.get(id=_uid(t['email'])))
    r = c.post('/api/yeu-cau', {'loai': 'tk_dang_ky', 'tieu_de': 'Xếp lớp cho em'}, format='json')
    assert r.status_code == 400, r.data
    # Và loại ấy không nằm trong danh sách em được chọn.
    lc = c.get('/api/yeu-cau/lua-chon')
    assert lc.status_code == 200
    assert 'tk_dang_ky' not in [l['code'] for l in lc.data['loai']]


def test_giang_vien_khong_thay_yeu_cau_dang_ky(thu, lop):
    """Lượt đăng ký mang số điện thoại và email của em — cùng ranh giới với
    `ht_tai_khoan`: giảng viên và trợ giảng không thấy."""
    from accounts.models import User
    from common.permissions import ROLE_TEACHER
    t = _than()
    _dang_ky(t)
    _, chia = _chia_xac_thuc(thu)
    _xac_thuc(chia)
    gv = q1('INSERT INTO users (name, email, password, role, streak) '
            'VALUES (%s, %s, %s, %s, 0) RETURNING id',
            ('GV E5', 'gv_e5_%s@example.com' % uuid.uuid4().hex[:8],
             make_werkzeug_password(MK), ROLE_TEACHER))['id']
    c = APIClient()
    c.force_authenticate(user=User.objects.get(id=gv))
    r = c.get('/api/teach/yeu-cau?loai=tk_dang_ky')
    assert r.status_code == 200
    assert not [y for y in r.data['yeuCau']
                if (y['hocVien'] or {}).get('id') == _uid(t['email'])]


# ── Mốc "Đăng ký" trên dòng thời gian (dòng 4) ──────────────────────────────

def test_dong_thoi_gian_co_moc_tu_dang_ky_va_xac_thuc(thu, hoc_vu_api):
    t = _than()
    _dang_ky(t)
    _, chia = _chia_xac_thuc(thu)
    _xac_thuc(chia)
    r = hoc_vu_api.get('/api/admin/users/%d/timeline' % _uid(t['email']))
    assert r.status_code == 200, r.data
    tieu_de = [e['tieuDe'] for e in r.data['events']]
    assert any('tự đăng ký' in s.lower() for s in tieu_de), tieu_de
    assert any('xác' in s.lower() and 'email' in s.lower() for s in tieu_de), tieu_de
