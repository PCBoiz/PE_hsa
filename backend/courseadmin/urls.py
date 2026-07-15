from django.urls import path

from courseadmin import views

urlpatterns = [
    path('api/admin/courses', views.AdminCoursesView.as_view()),
    path('api/admin/courses/<str:course_id>', views.AdminCourseDetailView.as_view()),
    path('api/admin/courses/<str:course_id>/lessons', views.AdminCourseLessonsView.as_view()),
    path('api/admin/lessons', views.AdminLessonsView.as_view()),
    path('api/admin/lessons/<int:lesson_id>', views.AdminLessonDetailView.as_view()),
]
