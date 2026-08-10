from django.urls import path

from mockexam import views

urlpatterns = [
    path('api/mock-exams', views.MockExamsView.as_view()),
    path('api/mock-exams/<int:exam_id>', views.MockExamDetailView.as_view()),
    path('api/mock-exams/<int:exam_id>/submit', views.MockSubmitView.as_view()),
    path('api/mock-attempts', views.MockAttemptsView.as_view()),
]
