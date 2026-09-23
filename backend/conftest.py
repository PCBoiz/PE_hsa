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


def pytest_configure(config):
    """Dừng cả lượt nếu CSDL đang dùng là PRODUCTION (H1, 24/09/2026).

    "Cuộn lại cuối mỗi test" không phải "không đụng": vẫn chiếm kết nối, vẫn giữ
    khoá, và một test viết ngoài giao dịch thì cuộn lại không cứu. Xem
    `common/hang_rao_csdl.py`."""
    from common.hang_rao_csdl import loi_neu_production
    loi = loi_neu_production('pytest')
    if loi:
        pytest.exit(loi, returncode=3)


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
    """User tạm (INSERT thẳng như fixture Flask cũ) — rollback tự dọn.

    EMAIL DUY NHẤT MỖI LẦN, không phải một chuỗi cố định (sửa 17/09/2026). Lượt
    pytest toàn bộ ngày 16/09 TREO VĨNH VIỄN: `pg_stat_activity` cho thấy một
    phiên "idle in transaction" của một phép kiểm trước còn giữ dòng
    `django_test_tmp@example.com` (kết nối bị pool vứt sau khi Neon rớt, giao
    dịch phía máy chủ không bao giờ được cuộn lại), và câu INSERT cùng email ở
    kết nối mới đứng chờ khoá của chỉ mục duy nhất — mãi mãi, vì bên giữ khoá
    không chờ ai nên Postgres không thấy bế tắc. Cùng một email cũng là lý do
    hai lượt CI song song đập nhau (TODO §A2). Email khác nhau thì không có gì
    để tranh.
    """
    import uuid

    from common.db import q1
    row = q1(
        "INSERT INTO users (name, email, password, streak, last_study_date) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING id",
        ('Django Tester', 'django_test_%s@example.com' % uuid.uuid4().hex[:12], 'x', 0, None))
    return row['id']


@pytest.fixture
def auth_api(api, temp_user):
    """APIClient đã đăng nhập với temp_user (tương đương _login_as session cũ)."""
    from accounts.models import User
    api.force_authenticate(user=User.objects.get(id=temp_user))
    return api


@pytest.fixture
def temp_admin(db):
    """Quản trị viên tạm — rollback tự dọn.

    Cần từ 27/08/2026: cấp tài khoản đã chuyển thành việc CHỈ quản trị viên làm
    được, nên mọi phép kiểm đường ``/auth/register`` phải đi kèm một tài khoản
    có quyền, thay vì gọi ẩn danh như thời còn tự đăng ký.
    """
    from common.db import q1
    from common.permissions import ROLE_ADMIN
    row = q1(
        "INSERT INTO users (name, email, password, role, streak, last_study_date) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        ('Django Admin Tmp', 'django_admin_tmp@example.com', 'x', ROLE_ADMIN, 0, None))
    return row['id']


@pytest.fixture
def admin_api(api, temp_admin):
    """APIClient đã đăng nhập với quyền quản trị viên."""
    from accounts.models import User
    api.force_authenticate(user=User.objects.get(id=temp_admin))
    return api
