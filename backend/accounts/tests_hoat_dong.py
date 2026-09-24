"""Lần cuối thấy tài khoản — §56 `users.last_seen_at`, `accounts/hoat_dong.py` (24/09/2026).

Đi qua URL THẬT (`/auth/login`, `/auth/refresh`) và view OAuth thật. Luật:
  · đăng nhập ĐÚNG → đóng dấu; sai mật khẩu hay tài khoản đã khoá → KHÔNG;
  · làm mới token → đóng dấu lại (người đang dùng được thấy ít nhất 30 phút/lần);
  · đăng nhập Google/Facebook → đóng dấu;
  · CSDL hỏng lúc đóng dấu → đăng nhập VẪN thành công (dấu chỉ là số liệu phụ).
"""
import uuid
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.hashers import make_werkzeug_password
from common.clock import local_now
from common.db import q1, x

pytestmark = pytest.mark.django_db
MK = 'SecretPass123'


def _tai_khoan(status='active'):
    r = q1("INSERT INTO users (name, email, password, role, status, questionnaire_completed) "
           "VALUES ('Hoat Dong Tmp', %s, %s, 'Học viên', %s, 1) RETURNING id, email",
           ('dj_hoatdong_%s@example.com' % uuid.uuid4().hex[:10], make_werkzeug_password(MK), status))
    return r['id'], r['email']


def _thay(uid):
    return q1('SELECT last_seen_at FROM users WHERE id = %s', (uid,))['last_seen_at']


def _gan_ngay(uid, ngay):
    x('UPDATE users SET last_seen_at = %s WHERE id = %s', (local_now() - timedelta(days=ngay), uid))


def _gan_day(t):
    return t is not None and abs((local_now() - t).total_seconds()) < 120


def test_dang_nhap_dung_thi_dong_dau():
    uid, email = _tai_khoan()
    assert _thay(uid) is None
    r = APIClient().post('/auth/login', {'email': email, 'password': MK}, format='json')
    assert r.status_code == 200, r.content[:200]
    assert _gan_day(_thay(uid)), 'đăng nhập xong mà last_seen_at = %r' % _thay(uid)


def test_sai_mat_khau_khong_dong_dau():
    uid, email = _tai_khoan()
    r = APIClient().post('/auth/login', {'email': email, 'password': 'SaiRoi999'}, format='json')
    assert r.status_code == 401
    assert _thay(uid) is None, 'gõ sai mật khẩu không phải là "đã vào"'


def test_tai_khoan_da_khoa_khong_dong_dau():
    """Đúng mật khẩu nhưng trung tâm đã khoá → 403; em ấy KHÔNG vào được, nên không
    được tính là còn hoạt động (nếu không, một em đã nghỉ cứ thử đăng nhập là thoát
    khỏi danh sách "lâu không vào")."""
    uid, email = _tai_khoan(status='suspended')
    r = APIClient().post('/auth/login', {'email': email, 'password': MK}, format='json')
    assert r.status_code == 403
    assert _thay(uid) is None


def test_lam_moi_token_dong_dau_lai():
    uid, email = _tai_khoan()
    c = APIClient()
    d = c.post('/auth/login', {'email': email, 'password': MK}, format='json').json()
    _gan_ngay(uid, 20)
    r = c.post('/auth/refresh', {'refresh': d['refresh']}, format='json')
    assert r.status_code == 200, r.content[:200]
    assert _gan_day(_thay(uid)), 'làm mới token mà dấu vẫn là 20 ngày trước: %r' % _thay(uid)


def test_lam_moi_hong_khong_dong_dau():
    uid, email = _tai_khoan()
    c = APIClient()
    d = c.post('/auth/login', {'email': email, 'password': MK}, format='json').json()
    assert c.post('/auth/refresh', {'refresh': d['refresh']}, format='json').status_code == 200
    _gan_ngay(uid, 20)
    # Token cũ đã bị thu hồi khi xoay → 401, và không ai được "thấy" nhờ nó.
    assert c.post('/auth/refresh', {'refresh': d['refresh']}, format='json').status_code == 401
    assert (local_now() - _thay(uid)).days >= 19


def test_dang_nhap_oauth_dong_dau():
    from django.test import RequestFactory

    from accounts.models import User
    from accounts.oauth import oauth_complete
    uid, _ = _tai_khoan()
    req = RequestFactory().get('/auth/oauth-complete')
    req.user = User.objects.get(id=uid)
    r = oauth_complete(req)
    assert r.status_code == 302 and '#access=' in r['Location']
    assert _gan_day(_thay(uid))


def test_csdl_hong_luc_dong_dau_van_dang_nhap_duoc(monkeypatch):
    """Dấu là số liệu PHỤ: hỏng thì ghi log, KHÔNG được chặn người đăng nhập."""
    from django.db import DatabaseError

    from accounts import hoat_dong
    uid, email = _tai_khoan()

    def hong(*a, **k):
        raise DatabaseError('gia lap: cot last_seen_at chua co')

    monkeypatch.setattr(hoat_dong, 'x', hong)
    r = APIClient().post('/auth/login', {'email': email, 'password': MK}, format='json')
    assert r.status_code == 200, r.content[:200]
    assert r.json().get('access')
