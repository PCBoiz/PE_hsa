"""
URL gốc — giữ NGUYÊN path/method của bản Flask (ràng buộc #2 MIGRATION_PLAN §1).
Mỗi app tự khai path đầy đủ (không prefix chung) vì path cũ không theo chuẩn
router lồng (vd /api/course/rating số ít, /api/courses-enrolled).
"""
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    """Health check + giữ Neon ấm. Dùng common.db.q (retry + reset pool) để
    lúc deploy/cold-start Neon vừa được đánh thức vừa KHÔNG 500 làm hỏng
    healthCheck của Render (MIGRATION_NOTES §Neon)."""
    from common.db import q
    q('SELECT 1')
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('health', health),
    # CÙNG view, thêm tiền tố `/api/` (17/09/2026): trình duyệt chỉ với tới Django
    # qua `/api/*` (Vercel chuyển tiếp đúng tiền tố ấy — xem `frontend/src/app/api`),
    # nên màn đăng nhập không gọi được `/health` để ĐÁNH THỨC máy chủ trước khi
    # người dùng bấm Đăng nhập. Máy chủ gói rẻ ngủ sau ~15 phút và lượt gọi đầu mất
    # 70–90 giây (đo 17/09: 76,3 s; hai lượt sau 0,97 s và 0,50 s) — đánh thức sớm
    # là cắt phần lớn khoảng chờ ấy khỏi lượt đăng nhập.
    path('api/health', health),
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
    # `mockexam.urls` THÁO 24/09/2026 (bỏ thi, pha A — anh Sơn chốt "bỏ mọi thứ
    # về thi, giữ ngày thi HSA"). App vẫn trong INSTALLED_APPS, bảng giữ nguyên:
    # pha A đảo ngược được bằng đúng một dòng này. Mã app xoá ở pha C. Tuyến đã
    # vắng thật: `common/tests_bo_thi.py`; phép kiểm cũ của app chạy trên cây
    # tuyến riêng `config/urls_thi_da_thao.py`.
    path('', include('chatbot.urls')),
    path('', include('teaching.urls')),
    path('', include('chuong_trinh.urls')),
    path('', include('lich.urls')),
    path('accounts/', include('allauth.urls')),  # /accounts/google/login/ ...
]

handler404 = 'common.errors.handler404'
handler500 = 'common.errors.handler500'
