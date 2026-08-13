from django.urls import path

from stats import views

urlpatterns = [
    path('api/stats', views.StatsView.as_view()),
    path('api/stats/xp-by-course', views.XpByCourseView.as_view()),
    # Gộp 4 chỉ số cho hàng thẻ đầu Dashboard (audit 2026-08-14).
    path('api/hsa/summary', views.HsaSummaryView.as_view()),
    path('api/mission/complete', views.CompleteMissionView.as_view()),
    path('api/streak/review-quiz-status', views.ReviewQuizStatusView.as_view()),
]
