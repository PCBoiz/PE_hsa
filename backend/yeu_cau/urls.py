"""Tuyến của hộp Yêu cầu (E3). Gắn từ `config/urls.py`. Tiền tố `api/admin/` và `api/teach/`
để phép kiểm "học viên bị chặn ở mọi đường quản trị / giảng dạy" (`common/tests_ma_tran_quyen.py`)
tự quét luôn các tuyến này."""
from django.urls import path

from yeu_cau import views as v

urlpatterns = [
    # ── Học viên ──
    path('api/yeu-cau', v.YeuCauCuaToiView.as_view()),
    path('api/yeu-cau/lua-chon', v.LuaChonHocVienView.as_view()),
    path('api/yeu-cau/<int:yc_id>', v.YeuCauCuaToiChiTietView.as_view()),
    path('api/yeu-cau/<int:yc_id>/tra-loi', v.HocVienTraLoiView.as_view()),
    path('api/yeu-cau/<int:yc_id>/huy', v.HocVienHuyView.as_view()),
    # ── Nhân sự (GV / TG / học vụ / quản trị) ──
    path('api/teach/yeu-cau', v.YeuCauNhanSuView.as_view()),
    path('api/teach/yeu-cau/lua-chon', v.LuaChonNhanSuView.as_view()),
    path('api/teach/yeu-cau/<int:yc_id>', v.YeuCauNhanSuChiTietView.as_view()),
    path('api/teach/yeu-cau/<int:yc_id>/tra-loi', v.NhanSuTraLoiView.as_view()),
    path('api/teach/yeu-cau/<int:yc_id>/trang-thai', v.NhanSuTrangThaiView.as_view()),
    path('api/teach/yeu-cau/<int:yc_id>/chuyen-tiep', v.ChuyenTiepView.as_view()),
    path('api/teach/yeu-cau/<int:yc_id>/nguoi-nhan', v.NguoiNhanView.as_view()),
    # ── Học vụ / quản trị ──
    path('api/admin/yeu-cau/<int:yc_id>/giao', v.GiaoView.as_view()),
    path('api/admin/yeu-cau/<int:yc_id>/duyet', v.DuyetView.as_view()),
    path('api/admin/yeu-cau/<int:yc_id>/tu-choi', v.TuChoiView.as_view()),
    path('api/admin/yeu-cau/<int:yc_id>/lop', v.LopChuyenToiView.as_view()),
    # ── Phụ huynh (link) ──
    path('api/public/phu-huynh/<str:token>/yeu-cau', v.PhuHuynhYeuCauView.as_view()),
]
