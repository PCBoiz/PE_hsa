"""
OAuth Google/Facebook — port luồng nghiệp vụ routes/oauth.py (flask-dance)
sang django-allauth, giữ nguyên 3 bước:
  1. Đã có (oauth_provider, oauth_provider_id) → đăng nhập.
  2. Email trùng tài khoản thường (oauth_provider IS NULL) → tự động LIÊN KẾT.
  3. Chưa có → tạo user mới (name mặc định 'Người dùng').

Khác Flask (bắt buộc vì frontend khác domain — MIGRATION_NOTES §OAuth):
sau callback KHÔNG render/redirect trang Django mà cấp JWT rồi redirect về
`{FRONTEND_URL}/auth/callback#access=...&refresh=...` (dùng URL FRAGMENT thay
vì query string: fragment không bị gửi lên server/log trung gian).
"""
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework_simplejwt.tokens import RefreshToken

from common.identity import norm_email
from common.db import q1, x


class LegacySocialAccountAdapter(DefaultSocialAccountAdapter):
    """Map user allauth ↔ bảng users legacy theo đúng logic _login_or_create cũ."""

    def pre_social_login(self, request, sociallogin):
        provider = sociallogin.account.provider          # 'google' | 'facebook'
        provider_id = str(sociallogin.account.uid)
        email = norm_email(sociallogin.user.email)

        # 1. Đã có tài khoản OAuth này
        row = q1('SELECT id FROM users WHERE oauth_provider = %s AND oauth_provider_id = %s',
                 (provider, provider_id))
        if row:
            self._attach_existing(sociallogin, row['id'])
            return

        # 2. Email trùng tài khoản đăng ký thường → tự động liên kết OAuth
        if email:
            # `lower(email)` chứ không phải email nguyên văn: Google trả về
            # đúng chuỗi người dùng đã đăng ký ở Google, có thể là "An@gmail.com"
            # trong khi trung tâm đã tạo tài khoản "an@gmail.com". Tra nguyên
            # văn thì không thấy → allauth tưởng là người mới → thử tạo tài
            # khoản → đụng chỉ mục duy nhất `idx_users_email_lower` → 500.
            existing = q1('SELECT id, oauth_provider FROM users WHERE lower(email) = %s',
                          (email,))
            if existing and existing['oauth_provider'] is None:
                x('UPDATE users SET oauth_provider=%s, oauth_provider_id=%s WHERE id=%s',
                  (provider, provider_id, existing['id']))
                self._attach_existing(sociallogin, existing['id'])
                return
        # 3. Không tìm thấy tài khoản nào khớp.
        #
        # TRƯỚC 27/08/2026: rơi xuống save_user để TẠO tài khoản mới. Từ khi bỏ
        # tự đăng ký, nhánh đó thành một cửa sau: bất kỳ ai có Gmail đều tự mở
        # được tài khoản, đúng thứ chính sách "chỉ trung tâm mới cấp tài khoản"
        # muốn ngăn. Nay chặn ngay tại đây và nói rõ lý do bằng tiếng Việt.
        #
        # Vẫn giữ nhánh 1 và 2 ở trên: học viên được trung tâm cấp tài khoản
        # bằng chính Gmail của mình thì bấm "đăng nhập bằng Google" vẫn vào
        # được, và lần đầu làm vậy tài khoản tự liên kết.
        raise ImmediateHttpResponse(
            HttpResponseRedirect(f'{settings.FRONTEND_URL}/login?error=chua_co_tai_khoan')
        )

    def _attach_existing(self, sociallogin, user_id):
        from accounts.models import User
        sociallogin.user = User.objects.get(id=user_id)

    def is_open_for_signup(self, request, sociallogin):
        """Không ai tự mở tài khoản qua mạng xã hội — trung tâm cấp tài khoản."""
        return False

    def save_user(self, request, sociallogin, form=None):
        """Chốt chặn thứ hai. `pre_social_login` đã chặn trước rồi; tới được đây
        nghĩa là allauth đổi luồng ở bản mới, nên thà hỏng to còn hơn âm thầm
        tạo tài khoản ngoài tầm kiểm soát của trung tâm."""
        raise ImmediateHttpResponse(
            HttpResponseRedirect(f'{settings.FRONTEND_URL}/login?error=chua_co_tai_khoan')
        )


def oauth_complete(request):
    """LOGIN_REDIRECT_URL của allauth: cấp JWT rồi bàn giao về frontend Next."""
    if not request.user.is_authenticated:
        return HttpResponseRedirect(f'{settings.FRONTEND_URL}/login?error=oauth_failed')
    refresh = RefreshToken.for_user(request.user)
    # Fragment (#) thay vì query (?): token không lọt vào access log/Referer
    return HttpResponseRedirect(
        f'{settings.FRONTEND_URL}/auth/callback'
        f'#access={refresh.access_token}&refresh={refresh}'
    )
