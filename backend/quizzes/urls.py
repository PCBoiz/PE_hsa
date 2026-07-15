from django.urls import path

from quizzes import views

urlpatterns = [
    path('api/courses/<str:course_id>/quiz/generate', views.GenerateQuizView.as_view()),
    path('api/courses/<str:course_id>/quiz/history', views.QuizHistoryView.as_view()),
    path('api/quizzes/<int:quiz_id>/submit', views.SubmitQuizView.as_view()),
    path('api/quizzes/<int:quiz_id>', views.QuizView.as_view()),
]
