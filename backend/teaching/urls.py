from django.urls import path

from teaching import admin_users, exports, sessions, views

urlpatterns = [
    # ── Khu vực giảng dạy — quyền theo NGỮ CẢNH (lớp mình phụ trách) ──
    path('api/teach/classes', views.TeachClassesView.as_view()),
    path('api/teach/classes/<int:class_id>', views.TeachClassDetailView.as_view()),
    path('api/teach/classes/<int:class_id>/students/<int:user_id>',
         views.TeachStudentView.as_view()),

    # ── Buổi học & điểm danh (đặc tả ERP §4) ──
    path('api/teach/classes/<int:class_id>/sessions', sessions.ClassSessionsView.as_view()),
    path('api/teach/sessions/<int:session_id>', sessions.ClassSessionDetailView.as_view()),
    path('api/teach/sessions/<int:session_id>/attendance',
         sessions.SessionAttendanceView.as_view()),

    # ── Xuất dữ liệu (đặc tả ERP §6) ──
    path('api/teach/classes/<int:class_id>/export/progress.csv',
         exports.ClassProgressCsvView.as_view()),
    path('api/teach/classes/<int:class_id>/export/attendance.csv',
         exports.ClassAttendanceCsvView.as_view()),
    path('api/admin/export/users.csv', exports.AdminUsersCsvView.as_view()),

    # ── Quản trị lớp & vai trò — chỉ quản trị viên ──
    path('api/admin/classes', views.AdminClassesView.as_view()),
    path('api/admin/classes/<int:class_id>', views.AdminClassDetailView.as_view()),
    path('api/admin/classes/<int:class_id>/members', views.AdminClassMembersView.as_view()),

    # ── Tài khoản ──
    path('api/admin/users', admin_users.AdminUsersView.as_view()),
    path('api/admin/users/create', views.AdminCreateUserView.as_view()),
    path('api/admin/users/bulk', admin_users.AdminBulkCreateUsersView.as_view()),
    path('api/admin/users/<int:user_id>/role', views.AdminUserRoleView.as_view()),
    path('api/admin/users/<int:user_id>/status', admin_users.AdminUserStatusView.as_view()),
    path('api/admin/users/<int:user_id>/reset-password',
         views.AdminResetPasswordView.as_view()),

    # ── Nhật ký kiểm toán (đặc tả ERP §9, khối 5) ──
    path('api/admin/audit', admin_users.AdminAuditView.as_view()),
]
