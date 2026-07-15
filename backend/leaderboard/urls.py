from django.urls import path

from leaderboard import views

urlpatterns = [
    path('api/leaderboard', views.LeaderboardView.as_view()),
]
