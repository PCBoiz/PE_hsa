"""
conftest.py — cấu hình pytest-django cho bộ test migration.

Bộ test Flask gốc (tests/test_*.py) chạy TRỰC TIẾP trên DB thật với user tạm
(tạo → xóa tay). Bản Django giữ nguyên triết lý đó nhưng an toàn hơn:
django_db_setup no-op (dùng chính DB trong DATABASE_URL, không tạo/destroy
test database — models managed=False không thể migrate ra DB mới), và mọi
test @pytest.mark.django_db chạy trong transaction được ROLLBACK cuối test
→ không ghi gì vĩnh viễn vào DB.
"""
import pytest
from django.core.cache import cache


@pytest.fixture(scope='session')
def django_db_setup():
    """No-op: dùng DB thật từ DATABASE_URL (như bộ test Flask cũ)."""


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """DRF throttle đếm theo cache — xóa giữa các test để login-throttle
    (5/min) không làm fail các test auth chạy liên tiếp."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def temp_user(db):
    """User tạm (INSERT thẳng như fixture Flask cũ) — rollback tự dọn."""
    from common.db import q1
    row = q1(
        "INSERT INTO users (name, email, password, streak, last_study_date) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING id",
        ('Django Tester', 'django_test_tmp@example.com', 'x', 0, None))
    return row['id']


@pytest.fixture
def auth_api(api, temp_user):
    """APIClient đã đăng nhập với temp_user (tương đương _login_as session cũ)."""
    from accounts.models import User
    api.force_authenticate(user=User.objects.get(id=temp_user))
    return api
