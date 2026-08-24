from django.urls import path

from teaching import views

urlpatterns = [
    # Khu vực giảng dạy — quyền theo NGỮ CẢNH (lớp mình phụ trách).
    path('api/teach/classes', views.TeachClassesView.as_view()),
    path('api/teach/classes/<int:class_id>', views.TeachClassDetailView.as_view()),
    path('api/teach/classes/<int:class_id>/students/<int:user_id>',
         views.TeachStudentView.as_view()),
    # Quản trị lớp & vai trò — chỉ quản trị viên.
    path('api/admin/classes', views.AdminClassesView.as_view()),
    path('api/admin/classes/<int:class_id>', views.AdminClassDetailView.as_view()),
    path('api/admin/classes/<int:class_id>/members', views.AdminClassMembersView.as_view()),
    path('api/admin/users', views.AdminUsersView.as_view()),
    path('api/admin/users/<int:user_id>/role', views.AdminUserRoleView.as_view()),
]
