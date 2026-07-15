from django.urls import path

from lessons import views

urlpatterns = [
    path('api/lessons/<int:lesson_no>/complete', views.CompleteLessonView.as_view()),
]
