from django.urls import path

from chatbot import views

urlpatterns = [
    path("api/chat", views.ChatView.as_view()),
]
