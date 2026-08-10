"""
URL gốc — giữ NGUYÊN path/method của bản Flask (ràng buộc #2 MIGRATION_PLAN §1).
Mỗi app tự khai path đầy đủ (không prefix chung) vì path cũ không theo chuẩn
router lồng (vd /api/course/rating số ít, /api/courses-enrolled).
"""
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    """Endpoint cho cron ping ngoài giữ Neon compute ấm (MIGRATION_NOTES §Neon)."""
    from django.db import connection
    with connection.cursor() as cur:
        cur.execute('SELECT 1')
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('health', health),
    path('', include('accounts.urls')),
    path('', include('courses.urls')),
    path('', include('lessons.urls')),
    path('', include('quizzes.urls')),
    path('', include('stats.urls')),
    path('', include('notifications.urls')),
    path('', include('roadmap.urls')),
    path('', include('leaderboard.urls')),
    path('', include('achievements.urls')),
    path('', include('forum.urls')),
    path('', include('courseadmin.urls')),
    path('', include('mockexam.urls')),
    path('', include('chatbot.urls')),
    path('accounts/', include('allauth.urls')),  # /accounts/google/login/ ...
]

handler404 = 'common.errors.handler404'
handler500 = 'common.errors.handler500'
