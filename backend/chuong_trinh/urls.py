"""Tuyến của miền chương trình (E1). Gắn từ `config/urls.py` như mọi app.

Soạn khung ở `courseadmin/urls.py` (`api/admin/courses/<id>/syllabus`, `api/admin/syllabus*`,
§64). Ở đây: lớp NHẬN khung (`api/admin/…`, `IsAdminOrAcademic`) và việc của người dạy
(`api/teach/…`, `IsTeachingStaff` + `can_see_class`). Hai tiền tố sẵn có để phép kiểm
"học viên bị chặn ở mọi đường quản trị / giảng dạy" (`common/tests_ma_tran_quyen.py`)
tự quét luôn các tuyến này.
"""
from django.urls import path

from chuong_trinh import khung, lop, so_dau_bai

urlpatterns = [
    # ── Mục lục khung cho màn soạn (sửa cây: courseadmin/urls.py) ──
    path('api/admin/chuong-trinh/khung', khung.MucLucKhungView.as_view()),
    # ── Lớp nhận khung, gắn buổi ──
    path('api/admin/classes/<int:class_id>/chuong-trinh', lop.NhanKhungView.as_view()),
    path('api/teach/classes/<int:class_id>/chuong-trinh', lop.LopChuongTrinhView.as_view()),
    path('api/teach/sessions/<int:session_id>/chuong-trinh', lop.GanBuoiView.as_view()),
    # ── Sổ đầu bài ──
    path('api/teach/sessions/<int:session_id>/so-dau-bai', so_dau_bai.SoDauBaiView.as_view()),
]
