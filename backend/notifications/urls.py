from django.urls import path

from notifications import views, views_hop_thu
from notifications import views_thong_bao as tb

urlpatterns = [
    path('api/notifications', views.NotificationSettingsView.as_view()),
    path('api/notifications/feed', views.FeedView.as_view()),
    # /stream (SSE) đã bỏ 2026-07-19 — badge chuyển sang client poll endpoint này
    path('api/notifications/badge', views.BadgeView.as_view()),
    path('api/notifications/feed/<int:notif_id>/read', views.FeedReadView.as_view()),
    path('api/notifications/feed/read-all', views.FeedReadAllView.as_view()),
    path('api/notifications/feed/<int:notif_id>/unread', views.FeedUnreadView.as_view()),
    # Thông báo trung tâm (§61, E2).
    path('api/admin/thong-bao', tb.AdminThongBaoView.as_view()),
    path('api/admin/thong-bao/preview', tb.AdminThongBaoXemTruocView.as_view()),
    path('api/admin/thong-bao/<int:aid>/gui', tb.AdminThongBaoGuiView.as_view()),
    path('api/admin/thong-bao/<int:aid>/huy', tb.AdminThongBaoHuyView.as_view()),
    path('api/teach/classes/<int:class_id>/thong-bao', tb.LopThongBaoView.as_view()),
    path('api/teach/classes/<int:class_id>/thong-bao/preview', tb.LopThongBaoXemTruocView.as_view()),
    # Hộp thư đi (§61, E2): nhịp cho máy gọi ngoài.
    path('api/noi-bo/tick', views_hop_thu.TickView.as_view()),
]
