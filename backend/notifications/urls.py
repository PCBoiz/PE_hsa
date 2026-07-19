from django.urls import path

from notifications import views

urlpatterns = [
    path('api/notifications', views.NotificationSettingsView.as_view()),
    path('api/notifications/feed', views.FeedView.as_view()),
    # /stream (SSE) đã bỏ 2026-07-19 — badge chuyển sang client poll endpoint này
    path('api/notifications/badge', views.BadgeView.as_view()),
    path('api/notifications/feed/<int:notif_id>/read', views.FeedReadView.as_view()),
    path('api/notifications/feed/read-all', views.FeedReadAllView.as_view()),
]
