from django.urls import path

from accounts import ghi_nho, quen_mat_khau, views
from accounts.oauth import oauth_complete

urlpatterns = [
    path('auth/login', views.LoginView.as_view()),
    path('auth/register', views.RegisterView.as_view()),
    path('auth/logout', views.LogoutView.as_view()),
    # Làm mới JWT — bản của SimpleJWT GIỮ chế độ "ghi nhớ đăng nhập" khi xoay (24/09/2026).
    path('auth/refresh', ghi_nho.LamMoiView.as_view()),
    path('auth/oauth-complete', oauth_complete),           # allauth callback → JWT → redirect Next
    # Quên mật khẩu qua email (§52, 23/09/2026). Ba cửa KHÔNG cần đăng nhập —
    # xem docstring `accounts/quen_mat_khau.py` về những điều cố ý.
    path('auth/quen-mat-khau', quen_mat_khau.QuenMatKhauView.as_view()),
    path('auth/dat-lai-mat-khau', quen_mat_khau.DatLaiMatKhauView.as_view()),
    path('auth/dat-lai-mat-khau/kiem', quen_mat_khau.KiemChiaView.as_view()),
    path('api/user', views.UserView.as_view()),
    path('api/user/password', views.PasswordView.as_view()),
    path('api/users/<int:user_id>/follow', views.FollowView.as_view()),
    path('api/users/<int:user_id>/following', views.FollowingView.as_view()),
    path('api/survey', views.SurveyView.as_view()),
]
