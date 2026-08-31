from django.urls import path

from lessons import views

urlpatterns = [
    path('api/lessons/<int:lesson_no>/complete', views.CompleteLessonView.as_view()),
    # Nội dung bài học lấy từ DB (engine fallback về file JS nếu DB chưa có).
    path('api/courses/<str:course_id>/content', views.CourseContentView.as_view()),
    # Chấm ở MÁY CHỦ (31/08/2026). Xem `lessons/grading.py` để biết vì sao đường
    # này phải tồn tại: trước nó, đáp án đi xuống trình duyệt trước khi học viên
    # trả lời, và điểm là con số học viên tự khai.
    path('api/courses/<str:course_id>/lessons/<int:lesson_no>/check',
         views.CheckAnswersView.as_view()),
]
