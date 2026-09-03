from django.urls import path

from mockexam import quan_tri, views

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

    # ── Khu soạn đề (quản trị viên hoặc Biên tập nội dung) ──────────────────
    # Tới 04/09/2026 KHÔNG có đường nào tạo đề: đề duy nhất trên CSDL đến từ
    # `seed_data`, nên muốn có đề thứ hai là phải sửa mã nguồn.
    path('api/admin/mock-exams', quan_tri.AdminMockExamsView.as_view()),
    path('api/admin/mock-exams/template.xlsx',
         quan_tri.AdminMockExamTemplateView.as_view()),
    path('api/admin/mock-exams/import', quan_tri.AdminMockExamImportView.as_view()),
    path('api/admin/mock-exams/<int:exam_id>/publish',
         quan_tri.AdminMockExamPublishView.as_view()),
]
