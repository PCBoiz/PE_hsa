from django.urls import path

from courseadmin import views

urlpatterns = [
    path('api/admin/courses', views.AdminCoursesView.as_view()),
    path('api/admin/courses/<str:course_id>', views.AdminCourseDetailView.as_view()),
    path('api/admin/courses/<str:course_id>/lessons', views.AdminCourseLessonsView.as_view()),
    path('api/admin/lessons', views.AdminLessonsView.as_view()),
    path('api/admin/lessons/<int:lesson_id>', views.AdminLessonDetailView.as_view()),
    # Soạn nội dung 5 bước + nhập cả khoá từ JSON (nhận giáo trình đối tác).
    path('api/admin/lessons/<int:lesson_id>/content', views.AdminLessonContentView.as_view()),
    path('api/admin/courses/<str:course_id>/import', views.AdminCourseImportView.as_view()),
]
