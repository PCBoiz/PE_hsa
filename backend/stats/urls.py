from django.urls import path

from stats import views

urlpatterns = [
    path('api/stats', views.StatsView.as_view()),
    path('api/stats/xp-by-course', views.XpByCourseView.as_view()),
    path('api/mission/complete', views.CompleteMissionView.as_view()),
    path('api/streak/review-quiz-status', views.ReviewQuizStatusView.as_view()),
]
