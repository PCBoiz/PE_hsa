from django.urls import path

from mockexam import views

urlpatterns = [
    path('api/mock-exams', views.MockExamsView.as_view()),
    # `GET /api/mock-exams/<id>` ĐÃ BỎ (31/08/2026). Nó phục vụ đủ câu hỏi cho
    # bất kỳ tài khoản đăng nhập nào mà KHÔNG mở đồng hồ, tức là một cửa xem
    # trước đề: đọc kỹ, chuẩn bị, rồi mới bấm bắt đầu lượt tính điểm duy nhất.
    # Frontend đã chuyển hẳn sang /start nên nó không còn người dùng nào.
    path('api/mock-exams/<int:exam_id>/start', views.MockStartView.as_view()),
    path('api/mock-exams/<int:exam_id>/save', views.MockSaveView.as_view()),
    path('api/mock-exams/<int:exam_id>/submit', views.MockSubmitView.as_view()),
    path('api/mock-attempts', views.MockAttemptsView.as_view()),
]
