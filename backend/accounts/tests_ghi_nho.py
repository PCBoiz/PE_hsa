"""Ghi nhớ đăng nhập (góp ý TopHSA #1, 24/09/2026) — `accounts/ghi_nho.py`.

Đi qua URL THẬT (`/auth/login`, `/auth/refresh`). Luật:
  · không tick → refresh 8 giờ, không claim `nho` (Next đặt cookie PHIÊN);
  · tick → refresh 30 ngày + claim `nho`, access cũng mang claim (Next đọc nó để
    đặt cookie sống lâu);
  · XOAY giữ nguyên chế độ (bản gốc SimpleJWT đặt lại hạn 8 giờ khi xoay — phiên
    "30 ngày" sẽ lặng lẽ thành 8 giờ sau lần làm mới đầu tiên), token cũ bị thu hồi.
"""
import time
import uuid

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from accounts.hashers import make_werkzeug_password
from common.db import q1

pytestmark = pytest.mark.django_db
NGAY = 86400
MK = 'SecretPass123'


def _tai_khoan():
    email = 'dj_ghinho_%s@example.com' % uuid.uuid4().hex[:10]
    q1("INSERT INTO users (name, email, password, role, status, questionnaire_completed) "
       "VALUES ('Ghi Nho Tmp', %s, %s, 'Học viên', 'active', 1) RETURNING id",
       (email, make_werkzeug_password(MK)))
    return email


def _dang_nhap(email, **them):
    r = APIClient().post('/auth/login', dict({'email': email, 'password': MK}, **them), format='json')
    assert r.status_code == 200, r.content[:200]
    return r.json()


def _con_lai(tok):
    return RefreshToken(tok)['exp'] - time.time()


def test_khong_tick_thi_refresh_8_gio_khong_claim():
    d = _dang_nhap(_tai_khoan())
    assert 'nho' not in RefreshToken(d['refresh']).payload
    assert 'nho' not in AccessToken(d['access']).payload
    assert 7.5 * 3600 < _con_lai(d['refresh']) <= 8 * 3600 + 5


def test_tick_thi_refresh_30_ngay_access_mang_claim_bang_thu_hoi_dung_han():
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
    d = _dang_nhap(_tai_khoan(), nho=True)
    assert RefreshToken(d['refresh'])['nho'] is True
    assert 29 * NGAY < _con_lai(d['refresh']) <= 30 * NGAY + 5
    assert AccessToken(d['access'])['nho'] is True, 'Next đọc claim ở access để quyết cookie'
    ot = OutstandingToken.objects.get(jti=RefreshToken(d['refresh'])['jti'])
    # Hạn trong bảng thu hồi phải là 30 ngày — ghi 8 giờ thì lệnh dọn token hết hạn
    # xoá dòng ấy sớm và token còn sống không còn thu hồi được.
    assert (ot.expires_at - ot.created_at).days >= 29


def test_xoay_giu_ghi_nho_va_thu_hoi_token_cu():
    d = _dang_nhap(_tai_khoan(), nho=True)
    c = APIClient()
    r = c.post('/auth/refresh', {'refresh': d['refresh']}, format='json')
    assert r.status_code == 200, r.content[:200]
    moi = r.json()['refresh']
    assert RefreshToken(moi)['nho'] is True
    assert _con_lai(moi) > 29 * NGAY, 'xoay token làm phiên ghi nhớ tụt về 8 giờ'
    assert AccessToken(r.json()['access'])['nho'] is True
    assert c.post('/auth/refresh', {'refresh': d['refresh']}, format='json').status_code == 401


def test_xoay_phien_thuong_van_8_gio():
    d = _dang_nhap(_tai_khoan())
    r = APIClient().post('/auth/refresh', {'refresh': d['refresh']}, format='json')
    moi = r.json()['refresh']
    assert 'nho' not in RefreshToken(moi).payload
    assert _con_lai(moi) <= 8 * 3600 + 5


@pytest.mark.parametrize('gia_tri', ['false', 0, '', None, 'co'])
def test_chi_true_moi_bat_ghi_nho(gia_tri):
    d = _dang_nhap(_tai_khoan(), nho=gia_tri)
    assert 'nho' not in RefreshToken(d['refresh']).payload
