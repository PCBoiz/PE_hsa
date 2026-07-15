"""Port utils/__init__.py: _is_admin = (users.role == 'admin')."""
from rest_framework.permissions import BasePermission


def is_admin(user) -> bool:
    return bool(user and user.is_authenticated and user.role == 'admin')


class IsAdminRole(BasePermission):
    """@api_admin_required — 403 'Không có quyền truy cập' (message do errors.py)."""

    def has_permission(self, request, view):
        return is_admin(request.user)
