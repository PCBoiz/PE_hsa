"""Tuyến miền LỊCH — phần đưa lịch ra ngoài (§71, 26/09/2026)."""
from django.urls import path

from . import views

urlpatterns = [
    path('api/lich/dia-chi', views.DiaChiLichView.as_view()),
    # Không nằm dưới /api/: ứng dụng lịch thích địa chỉ kết thúc bằng `.ics`, và
    # đường này bị gọi lại nhiều lần mỗi ngày nên bớt được một chặng proxy thì bớt.
    path('lich/<str:chia>.ics', views.TepLichView.as_view()),
]
