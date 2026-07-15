from django.urls import path

from achievements import views

urlpatterns = [
    path('api/achievements', views.AchievementsView.as_view()),
]
