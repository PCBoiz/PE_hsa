"""
URL gốc — giữ NGUYÊN path/method của bản Flask (ràng buộc #2 MIGRATION_PLAN §1).
Mỗi app tự khai path đầy đủ (không prefix chung) vì path cũ không theo chuẩn
router lồng (vd /api/course/rating số ít, /api/courses-enrolled).
"""
import os

from allauth.socialaccount import views as xh_views
from django.http import JsonResponse
from django.urls import include, path


def _ban():
    """Bảy ký tự đầu của commit đang chạy, hoặc chuỗi rỗng.

    Render đặt `RENDER_GIT_COMMIT` cho mọi lượt deploy; `PE_BAN` là đường đặt tay (máy dev,
    phép kiểm). Bảy ký tự vì đó là độ dài `git log --oneline` in ra — dán vào lệnh git là chạy.

    Đọc mỗi lượt gọi chứ không ghim lúc nạp mô-đun: gunicorn giữ tiến trình sống qua nhiều
    lượt, và một giá trị ghim lúc nạp sẽ nói dối nếu ai đó đổi biến rồi khởi động lại mềm.
    """
    return (os.environ.get('RENDER_GIT_COMMIT') or os.environ.get('PE_BAN') or '')[:7]


def health(request):
    """Health check + giữ Neon ấm. Dùng common.db.q (retry + reset pool) để
    lúc deploy/cold-start Neon vừa được đánh thức vừa KHÔNG 500 làm hỏng
    healthCheck của Render (MIGRATION_NOTES §Neon).

    `ban` = commit đang chạy (28/09/2026). Đẩy `master` là Render dựng lại mất ~45 phút, và
    trong 45 phút ấy câu "production đã lên bản mới chưa" chỉ trả lời được bằng cách đi thử
    một tính năng CHỈ bản mới có — mỗi lượt đẩy phải nghĩ ra một phép thử mới, và nghĩ sai thì
    kết luận sai theo cả hai chiều. Dấu bản biến câu hỏi ấy thành một lời gọi.

    Repo CÔNG KHAI nên mã commit không phải bí mật. Thiếu biến thì trả chuỗi rỗng — cửa này là
    health check của Render, nó ném là Render coi như dịch vụ chết và lăn ngược bản deploy.
    """
    from common.db import q
    q('SELECT 1')
    return JsonResponse({'status': 'ok', 'ban': _ban()})


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
    path('', include('yeu_cau.urls')),
    path('', include('lich.urls')),
    # CHỈ phần mạng xã hội của allauth (27/09/2026, audit bảo mật). Nạp cả `allauth.urls`
    # kéo theo NGUYÊN BỘ giao diện tài khoản của thư viện — đăng nhập, đăng ký, đổi mật
    # khẩu, quên mật khẩu, đổi email — và đo được là chúng MỞ: `/accounts/login/` trả 200
    # kèm biểu mẫu "Sign In". Đó là cửa xác thực THỨ HAI, ngoài mọi hàng rào của dự án:
    # không nâng `tokens_valid_from` (đổi mật khẩu mà thẻ cũ vẫn sống), không ghi
    # `admin_audit` (nhìn nhật ký thấy "không ai đổi mật khẩu"), trần dò riêng cộng thêm
    # vào trần của mình, thư đi ngoài hàng rào §61, và chữ tiếng Anh giữa sản phẩm tiếng
    # Việt. `User.set_password` ghi đúng định dạng werkzeug nên hai cửa nối thẳng vào nhau.
    #
    # Thứ DUY NHẤT cần ở gói này là đường đăng nhập Google, và nó nằm trong `socialaccount`.
    # `accounts/tests_cua_xac_thuc_thu_hai.py` giữ cả hai vế: bảy cửa kia phải 404, đường
    # Google phải còn.
    # Chỉ đường của NHÀ CUNG CẤP Google, không phải cả `socialaccount`: gói ấy còn kèm
    # `/accounts/signup/` (đăng ký qua mạng xã hội) và trang "kết nối tài khoản" — hai thứ
    # dự án không dùng, và đo được là `/accounts/signup/` vẫn mở sau lượt vá đầu.
    path('accounts/', include('allauth.socialaccount.providers.google.urls')),
    # Hai đường BÁO LỖI của allauth thì giữ: luồng OAuth hỏng giữa chừng sẽ `reverse` đúng
    # hai tên này, mất chúng là đổi một lỗi đăng nhập thành một trang 500 không ai hiểu.
    path('accounts/login/cancelled/', xh_views.login_cancelled,
         name='socialaccount_login_cancelled'),
    path('accounts/login/error/', xh_views.login_error, name='socialaccount_login_error'),
]

handler404 = 'common.errors.handler404'
handler500 = 'common.errors.handler500'
