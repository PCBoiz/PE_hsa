from django.urls import path

from courses import views

urlpatterns = [
    path('api/courses', views.CoursesView.as_view()),
    path('api/enrolled', views.EnrolledView.as_view()),
    path('api/courses-enrolled', views.CoursesEnrolledView.as_view()),
    path('api/courses/<str:course_id>/enroll', views.EnrollView.as_view()),
    # ĐẶT SAU .../enroll: Django khớp theo thứ tự, để trước sẽ nuốt mất path enroll.
    path('api/courses/<str:course_id>', views.CourseDetailView.as_view()),
    path('api/course/rating', views.RateCourseView.as_view()),          # path SỐ ÍT — giữ nguyên
    path('api/course/<str:course_id>/rating', views.CourseRatingView.as_view()),
    path('api/skills', views.SkillsView.as_view()),
]
