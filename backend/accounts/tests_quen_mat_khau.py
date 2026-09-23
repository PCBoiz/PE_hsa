"""QUÊN MẬT KHẨU QUA EMAIL (§52) — `accounts/quen_mat_khau.py`.

Đi đúng đường thật: gọi qua bộ định tuyến (`APIClient`), thư đi qua `common.mail`
ở CHẾ ĐỘ THỬ (ghi `.eml` vào thư mục tạm, không mở kết nối SMTP nào), rồi đọc
đường dẫn RA TỪ LÁ THƯ — không lấy chìa từ đâu khác. Chạy trên DB production
trong giao dịch cuộn lại (`conftest.py`), lọc về dữ liệu chính nó dựng.
"""
import email
import hashlib
import re
import time

import pytest
from rest_framework.test import APIClient

from accounts import quen_mat_khau
from accounts.hashers import make_werkzeug_password
from common.db import q, q1

MK_CU = 'MatKhauCu#2026'
MK_MOI = 'MatKhauMoi#2026'
GOC = 'https://vi-du.tophsa.test'


@pytest.fixture
def thu(tmp_path, monkeypatch, settings):
    monkeypatch.setenv('EMAIL_CHE_DO_THU', '1')
    monkeypatch.setenv('EMAIL_THU_MUC_THU', str(tmp_path))
    monkeypatch.setattr(quen_mat_khau, 'GUI_NGAY', True)
    settings.FRONTEND_URL = GOC
    return tmp_path


@pytest.fixture
def em(db):
    r = q1('INSERT INTO users (name, email, password, role, streak) '
           "VALUES ('Em QMK', 'em_qmk@example.com', %s, 'Học viên', 0) RETURNING id",
           (make_werkzeug_password(MK_CU),))
    return r['id']


def _xin(email_, **kw):
    return APIClient().post('/auth/quen-mat-khau', {'email': email_}, format='json', **kw)


def _cac_thu(thu_muc):
    return sorted(thu_muc.glob('*.eml'))


def _chia_trong_thu(tep):
    """Đọc đường dẫn từ CHÍNH lá thư, rồi tách chìa sau `#chia=`."""
    m = email.message_from_bytes(tep.read_bytes())
    chu = ''
    for phan in m.walk():
        if phan.get_content_type() == 'text/plain':
            chu = phan.get_payload(decode=True).decode(phan.get_content_charset() or 'utf-8')
    duong_dan = re.search(r'(\S+/dat-lai-mat-khau#chia=([A-Za-z0-9_\-]+))', chu)
    assert duong_dan, 'thư không có đường dẫn đặt lại: %r' % chu[:300]
    return m, duong_dan.group(1), duong_dan.group(2)


def _dang_nhap(mk):
    return APIClient().post('/auth/login', {'email': 'em_qmk@example.com', 'password': mk}, format='json')


# ── Xin chìa ────────────────────────────────────────────────────────────────

def test_xin_chia_gui_toi_chinh_email_va_chi_luu_bam(thu, em):
    r = _xin('EM_QMK@Example.com')          # gõ hoa vẫn là tài khoản ấy
    assert r.status_code == 200 and r.data['message'] == quen_mat_khau.CAU_CHUNG
    tep = _cac_thu(thu)
    assert len(tep) == 1
    m, duong_dan, chia = _chia_trong_thu(tep[0])
    assert m['To'].endswith('em_qmk@example.com')
    assert duong_dan.startswith(GOC + '/dat-lai-mat-khau#chia=')
    dong = q('SELECT token_hash FROM password_reset_tokens WHERE user_id=%s', (em,))
    assert len(dong) == 1
    # CHỈ BĂM: ai đọc được bảng cũng không dựng lại được đường dẫn.
    assert dong[0]['token_hash'] == hashlib.sha256(chia.encode()).hexdigest()
    assert chia not in dong[0]['token_hash']


def test_email_khong_co_tai_khoan_tra_loi_y_het_va_khong_gui(thu, em):
    co = _xin('em_qmk@example.com').data
    for f in thu.glob('*.eml'):
        f.unlink()
    khong = _xin('khong_ai_ca_qmk@example.com')
    assert khong.status_code == 200 and khong.data == co, 'câu trả lời khác nhau là lộ ai có tài khoản'
    assert not _cac_thu(thu)


def test_tai_khoan_bi_khoa_khong_duoc_cap(thu, em):
    q1("UPDATE users SET status='suspended' WHERE id=%s RETURNING id", (em,))
    r = _xin('em_qmk@example.com')
    assert r.status_code == 200 and r.data['message'] == quen_mat_khau.CAU_CHUNG
    assert not _cac_thu(thu)
    assert q1('SELECT count(*) AS n FROM password_reset_tokens WHERE user_id=%s', (em,))['n'] == 0


def test_sai_dang_email_bao_ngay(thu):
    r = _xin('khong-phai-email')
    assert r.status_code == 400 and 'email' in r.data['errors']


def test_tran_moi_gio_va_van_tra_cung_cau(thu, em):
    cau = [_xin('em_qmk@example.com').data for _ in range(quen_mat_khau.TRAN_MOI_GIO + 1)]
    assert all(c == cau[0] for c in cau)
    n = q1('SELECT count(*) AS n FROM password_reset_tokens WHERE user_id=%s', (em,))['n']
    assert n == quen_mat_khau.TRAN_MOI_GIO


def test_goc_duong_dan_khong_lay_tu_header_host(thu, em):
    # Host LẠ hẳn thì Django đã chặn ở `ALLOWED_HOSTS` (400, không thư nào đi) —
    # một lớp tốt, nhưng không phải lớp đang kiểm. Ở đây Host HỢP LỆ mà khác
    # `FRONTEND_URL`, kèm `X-Forwarded-Host` lạ: đường dẫn vẫn phải theo cấu hình.
    _xin('em_qmk@example.com', HTTP_HOST='localhost', HTTP_X_FORWARDED_HOST='ke-xau.example')
    tep = _cac_thu(thu)
    assert tep, 'không có thư nào — Host "localhost" bị chặn thì phép kiểm này không đo gì'
    _, duong_dan, _ = _chia_trong_thu(tep[0])
    assert duong_dan.startswith(GOC + '/'), duong_dan


# ── Dùng chìa ───────────────────────────────────────────────────────────────

def test_dat_lai_thanh_cong_dung_mot_lan(thu, em):
    _xin('em_qmk@example.com')
    _, _, chia = _chia_trong_thu(_cac_thu(thu)[0])
    k = APIClient().post('/auth/dat-lai-mat-khau/kiem', {'chia': chia}, format='json')
    assert k.data['hopLe'] is True and k.data['email'] == 'e***@example.com'

    r = APIClient().post('/auth/dat-lai-mat-khau', {'chia': chia, 'password': MK_MOI}, format='json')
    assert r.status_code == 200, r.data
    assert _dang_nhap(MK_MOI).status_code == 200
    assert _dang_nhap(MK_CU).status_code == 401
    assert q1('SELECT must_change_password FROM users WHERE id=%s', (em,))['must_change_password'] is False

    lan_hai = APIClient().post('/auth/dat-lai-mat-khau', {'chia': chia, 'password': 'KhacNua#2026'},
                               format='json')
    assert lan_hai.status_code == 400 and lan_hai.data['error'] == quen_mat_khau.CAU_HET_HAN
    assert APIClient().post('/auth/dat-lai-mat-khau/kiem', {'chia': chia},
                            format='json').data['hopLe'] is False


def test_mat_khau_yeu_khong_dot_mat_chia(thu, em):
    _xin('em_qmk@example.com')
    _, _, chia = _chia_trong_thu(_cac_thu(thu)[0])
    yeu = APIClient().post('/auth/dat-lai-mat-khau', {'chia': chia, 'password': '1'}, format='json')
    assert yeu.status_code == 400 and 'password' in yeu.data['errors']
    assert q1('SELECT used_at FROM password_reset_tokens WHERE user_id=%s', (em,))['used_at'] is None
    ok = APIClient().post('/auth/dat-lai-mat-khau', {'chia': chia, 'password': MK_MOI}, format='json')
    assert ok.status_code == 200


def test_chia_het_han(thu, em):
    _xin('em_qmk@example.com')
    _, _, chia = _chia_trong_thu(_cac_thu(thu)[0])
    q1("UPDATE password_reset_tokens SET expires_at = expires_at - interval '31 minutes' "
       'WHERE user_id=%s RETURNING id', (em,))
    assert APIClient().post('/auth/dat-lai-mat-khau/kiem', {'chia': chia},
                            format='json').data['hopLe'] is False
    r = APIClient().post('/auth/dat-lai-mat-khau', {'chia': chia, 'password': MK_MOI}, format='json')
    assert r.status_code == 400
    assert _dang_nhap(MK_CU).status_code == 200, 'chìa hết hạn không được đổi gì'


def test_chia_moi_thay_chia_cu(thu, em):
    _xin('em_qmk@example.com')
    _, _, cu = _chia_trong_thu(_cac_thu(thu)[0])
    for f in thu.glob('*.eml'):
        f.unlink()
    _xin('em_qmk@example.com')
    _, _, moi = _chia_trong_thu(_cac_thu(thu)[0])
    assert APIClient().post('/auth/dat-lai-mat-khau', {'chia': cu, 'password': MK_MOI},
                            format='json').status_code == 400
    assert APIClient().post('/auth/dat-lai-mat-khau', {'chia': moi, 'password': MK_MOI},
                            format='json').status_code == 200


def test_dat_lai_xong_moi_phien_cu_het_hieu_luc(thu, em):
    the = _dang_nhap(MK_CU).data['access']
    ai = APIClient()
    ai.credentials(HTTP_AUTHORIZATION='Bearer ' + the)
    assert ai.get('/api/user').status_code == 200
    time.sleep(1.1)            # `iat` tính theo GIÂY — cùng một giây thì chưa "cũ hơn"
    _xin('em_qmk@example.com')
    _, _, chia = _chia_trong_thu(_cac_thu(thu)[0])
    assert APIClient().post('/auth/dat-lai-mat-khau', {'chia': chia, 'password': MK_MOI},
                            format='json').status_code == 200
    assert ai.get('/api/user').status_code == 401, 'phiên của người đang giữ tài khoản phải bị đẩy ra'


def test_the_het_han_trong_cookie_khong_chan_cua_cong_khai(thu, em):
    ai = APIClient()
    ai.credentials(HTTP_AUTHORIZATION='Bearer the.hong.roi')
    assert ai.post('/auth/quen-mat-khau', {'email': 'em_qmk@example.com'}, format='json').status_code == 200


def test_nhat_ky_ghi_chinh_chu_tu_dat_lai(thu, em):
    _xin('em_qmk@example.com')
    _, _, chia = _chia_trong_thu(_cac_thu(thu)[0])
    APIClient().post('/auth/dat-lai-mat-khau', {'chia': chia, 'password': MK_MOI}, format='json')
    d = q1("SELECT actor_id, target_id FROM admin_audit WHERE action='user.password_self_reset' "
           'AND target_id=%s ORDER BY id DESC LIMIT 1', (str(em),))
    assert d and d['actor_id'] == em
