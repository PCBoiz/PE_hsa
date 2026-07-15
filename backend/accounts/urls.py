from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts import views
from accounts.oauth import oauth_complete

urlpatterns = [
    path('auth/login', views.LoginView.as_view()),
    path('auth/register', views.RegisterView.as_view()),
    path('auth/logout', views.LogoutView.as_view()),
    path('auth/refresh', TokenRefreshView.as_view()),      # MỚI: refresh JWT (bắt buộc với JWT)
    path('auth/oauth-complete', oauth_complete),           # allauth callback → JWT → redirect Next
    path('api/user', views.UserView.as_view()),
    path('api/user/password', views.PasswordView.as_view()),
    path('api/users/<int:user_id>/follow', views.FollowView.as_view()),
    path('api/users/<int:user_id>/following', views.FollowingView.as_view()),
    path('api/survey', views.SurveyView.as_view()),
]
