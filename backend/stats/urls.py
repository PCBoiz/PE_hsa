from django.urls import path

from stats import views

urlpatterns = [
    path('api/stats', views.StatsView.as_view()),
    path('api/stats/xp-by-course', views.XpByCourseView.as_view()),
    # Gộp 4 chỉ số cho hàng thẻ đầu Dashboard (audit 2026-08-14).
    path('api/hsa/summary', views.HsaSummaryView.as_view()),
    path('api/hsa/goals', views.HsaGoalsView.as_view()),
    # Nhiệm vụ hằng ngày HSA — thay /api/mission/complete (nhiệm vụ SQL pe_test).
    path('api/missions/today', views.TodayMissionsView.as_view()),
    path('api/missions/claim', views.ClaimMissionView.as_view()),
    path('api/streak/review-quiz-status', views.ReviewQuizStatusView.as_view()),
    # Bản đồ năng lực theo chủ đề — 20 ô (khoá × chương mục), xem stats/competency.py.
    path('api/hsa/competency', views.CompetencyView.as_view()),
    path('api/hsa/competency/self', views.TopicSelfMarkView.as_view()),
    # Sổ điểm + đường cong tiến bộ — đọc lại learning_events, không thêm bảng.
    path('api/hsa/gradebook', views.GradebookView.as_view()),
    path('api/hsa/progress-curve', views.ProgressCurveView.as_view()),
    # Học viên tự ghi nhận: nhật ký ngày + mục tiêu tuần (stats/journal.py).
    path('api/hsa/journal', views.JournalView.as_view()),
    path('api/hsa/weekly-target', views.WeeklyTargetView.as_view()),
]
