"""Tuyến của miền chương trình (E1). Gắn từ `config/urls.py` như mọi app.

`api/admin/…` cho việc SOẠN khung (`IsCurriculumPlanner`) và NHẬN khung cho một lớp
(`IsAdminOrAcademic`); `api/teach/…` cho việc của người dạy (`IsTeachingStaff` +
`can_see_class`). Đặt dưới hai tiền tố sẵn có để phép kiểm "học viên bị chặn ở mọi đường
quản trị / giảng dạy" (`common/tests_ma_tran_quyen.py`) tự quét luôn các tuyến này.
"""
from django.urls import path

from chuong_trinh import khung, lop, so_dau_bai

urlpatterns = [
    # ── Soạn khung ──
    path('api/admin/khung-chuong-trinh', khung.KhungListView.as_view()),
    path('api/admin/khung-chuong-trinh/<int:syllabus_id>', khung.KhungDetailView.as_view()),
    path('api/admin/khung-chuong-trinh/<int:syllabus_id>/ban-moi', khung.BanMoiView.as_view()),
    path('api/admin/khung-chuong-trinh/phien-ban/<int:version_id>',
         khung.PhienBanView.as_view()),
    path('api/admin/khung-chuong-trinh/phien-ban/<int:version_id>/xuat-ban',
         khung.XuatBanView.as_view()),
    # ── Lớp nhận khung, gắn buổi ──
    path('api/admin/classes/<int:class_id>/chuong-trinh', lop.NhanKhungView.as_view()),
    path('api/teach/classes/<int:class_id>/chuong-trinh', lop.LopChuongTrinhView.as_view()),
    path('api/teach/sessions/<int:session_id>/chuong-trinh', lop.GanBuoiView.as_view()),
    # ── Sổ đầu bài ──
    path('api/teach/sessions/<int:session_id>/so-dau-bai', so_dau_bai.SoDauBaiView.as_view()),
]
