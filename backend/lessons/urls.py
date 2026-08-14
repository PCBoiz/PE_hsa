from django.urls import path

from lessons import views

urlpatterns = [
    path('api/lessons/<int:lesson_no>/complete', views.CompleteLessonView.as_view()),
    # Nội dung bài học lấy từ DB (engine fallback về file JS nếu DB chưa có).
    path('api/courses/<str:course_id>/content', views.CourseContentView.as_view()),
]
