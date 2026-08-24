"""Phân quyền.

LỊCH SỬ: bản đầu chỉ có ``is_admin`` (users.role == 'admin') — quyền NHỊ PHÂN,
đúng với một sản phẩm tự học nhưng sai ngay từ gốc với một trung tâm luyện thi:
giảng viên phải thấy học viên CỦA MÌNH và không thấy của người khác.

Từ 24/08/2026 thêm vai trò ``Giảng viên``, và nguyên tắc là quyền theo NGỮ CẢNH
chứ không theo vai trò: quyền xem một lớp = "tôi có phụ trách lớp đó không",
quản trị viên thì xem được tất cả. Kiểm tra ngữ cảnh nằm ở ``can_see_class`` để
mọi endpoint dùng chung đúng một luật — mỗi chỗ tự kiểm một kiểu là cách chắc
chắn để hở dữ liệu học viên.
"""
from rest_framework.permissions import BasePermission

from common.db import q, q1

ROLE_ADMIN = 'admin'
ROLE_TEACHER = 'Giảng viên'
ROLE_STUDENT = 'Học viên'
#: Vai trò hợp lệ khi quản trị viên đổi vai trò cho một tài khoản.
ASSIGNABLE_ROLES = (ROLE_ADMIN, ROLE_TEACHER, ROLE_STUDENT)


def is_admin(user) -> bool:
    return bool(user and user.is_authenticated and user.role == ROLE_ADMIN)


def is_teacher(user) -> bool:
    return bool(user and user.is_authenticated and user.role == ROLE_TEACHER)


class IsAdminRole(BasePermission):
    """@api_admin_required — 403 'Không có quyền truy cập' (message do errors.py)."""

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsTeacherOrAdmin(BasePermission):
    """Cửa vào khu vực giảng dạy. Vào được KHÔNG có nghĩa là xem được mọi lớp —
    từng endpoint vẫn phải gọi ``can_see_class``."""

    def has_permission(self, request, view):
        return is_admin(request.user) or is_teacher(request.user)


def can_see_class(user, class_id) -> bool:
    """Quản trị viên xem mọi lớp; giảng viên chỉ xem lớp mình phụ trách.

    Trả False khi lớp không tồn tại — endpoint trả 404 cho cả hai trường hợp để
    không lộ ra rằng lớp đó có tồn tại hay không.
    """
    if is_admin(user):
        return bool(q1('SELECT 1 FROM classes WHERE id=%s', (class_id,)))
    if not is_teacher(user):
        return False
    return bool(q1('SELECT 1 FROM classes WHERE id=%s AND teacher_id=%s',
                   (class_id, user.id)))


def visible_class_ids(user):
    """Danh sách lớp người dùng được xem. Dùng cho màn hình danh sách."""
    if is_admin(user):
        return [r['id'] for r in q('SELECT id FROM classes ORDER BY id')]
    if not is_teacher(user):
        return []
    return [r['id'] for r in q('SELECT id FROM classes WHERE teacher_id=%s ORDER BY id',
                               (user.id,))]
