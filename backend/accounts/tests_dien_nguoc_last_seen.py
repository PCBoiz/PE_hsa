"""Điền ngược §56 `last_seen_at` từ lịch sử cấp phiên (migration `accounts/0002`, 25/09/2026).

Chạy ĐÚNG câu SQL của migration trên dữ liệu của chính test (CSDL cuộn lại sau test).
Câu ấy UPDATE toàn bảng — trong giao dịch của test nên không để lại gì, chỉ giữ khoá dòng
vài giây.
"""
import importlib
import uuid
from datetime import datetime

import pytest

from common.db import q1, x

pytestmark = pytest.mark.django_db

MIG = importlib.import_module('accounts.migrations.0002_dien_nguoc_last_seen_at')


def _nguoi(tao_luc, da_thay=None):
    return q1('INSERT INTO users (name, email, password, streak, created_at, last_seen_at) '
              "VALUES ('DN', %s, 'x', 0, %s, %s) RETURNING id",
              ('dn_%s@example.com' % uuid.uuid4().hex[:10], tao_luc, da_thay))['id']


def _the(uid, luc_utc):
    """Một dòng token như SimpleJWT ghi — `luc_utc` là chuỗi ISO có múi."""
    x('INSERT INTO token_blacklist_outstandingtoken (token, created_at, expires_at, user_id, jti) '
      "VALUES ('t', %s::timestamptz, %s::timestamptz + INTERVAL '30 days', %s, %s)",
      (luc_utc, luc_utc, uid, uuid.uuid4().hex))


def _thay(uid):
    return q1('SELECT last_seen_at FROM users WHERE id=%s', (uid,))['last_seen_at']


def test_dien_luot_muon_nhat_theo_gio_viet_nam():
    a = _nguoi(datetime(2026, 9, 1, 8, 0))
    _the(a, '2026-09-10T01:00:00+00:00')
    _the(a, '2026-09-20T01:00:00+00:00')          # 08:00 giờ Việt Nam
    x(MIG.SQL_DIEN_NGUOC)
    assert _thay(a) == datetime(2026, 9, 20, 8, 0), _thay(a)


def test_bo_phien_cap_luc_tao_tai_khoan_va_khong_ghi_de():
    # Chỉ có token cấp NGAY lúc tạo tài khoản (lượt đăng ký) → chủ tài khoản chưa từng vào.
    b = _nguoi(datetime(2026, 9, 1, 8, 0))
    _the(b, '2026-09-01T01:01:00+00:00')          # 08:01 VN — một phút sau khi tạo
    # Đã có dấu thật → không đè bằng số cũ hơn.
    c = _nguoi(datetime(2026, 9, 1, 8, 0), da_thay=datetime(2026, 9, 23, 20, 0))
    _the(c, '2026-09-15T01:00:00+00:00')
    x(MIG.SQL_DIEN_NGUOC)
    assert _thay(b) is None
    assert _thay(c) == datetime(2026, 9, 23, 20, 0)


def test_chay_lai_khong_doi_gi():
    a = _nguoi(datetime(2026, 9, 1, 8, 0))
    _the(a, '2026-09-20T01:00:00+00:00')
    x(MIG.SQL_DIEN_NGUOC)
    truoc = _thay(a)
    _the(a, '2026-09-22T01:00:00+00:00')          # lượt đăng nhập mới SAU khi đã điền
    x(MIG.SQL_DIEN_NGUOC)
    assert _thay(a) == truoc, 'điền ngược chỉ lấp ô trống — dấu mới do lượt đăng nhập tự đóng'
