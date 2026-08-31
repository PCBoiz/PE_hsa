"""
Rate limit — port từ Flask-Limiter (extensions.py: 200/day + 50/hour theo IP).

QUAN TRỌNG (khác biệt semantics phải giữ): Flask-Limiter đếm PER-ENDPOINT
per-IP — mỗi route có quota 50/hour riêng. DRF throttle mặc định đếm GỘP mọi
endpoint chung 1 quota → 1 lần load dashboard (~20 API call) sẽ đốt gần hết
50/hour, tái diễn đúng lớp bug 429 mà AUDIT-FIX 2026-07-07 đã xử lý.
→ Key cache ở đây gồm cả tên view để quota tính riêng từng endpoint như cũ.
"""
from rest_framework.throttling import SimpleRateThrottle


class _PerViewIPThrottle(SimpleRateThrottle):
    def get_cache_key(self, request, view):
        ident = self.get_ident(request)  # IP (get_remote_address tương đương)
        return self.cache_format % {
            'scope': f'{self.scope}.{view.__class__.__module__}.{view.__class__.__name__}',
            'ident': ident,
        }


class DailyIPThrottle(_PerViewIPThrottle):
    scope = 'ip_day'


class HourlyIPThrottle(_PerViewIPThrottle):
    scope = 'ip_hour'


class _PerViewUserThrottle(SimpleRateThrottle):
    """Đếm theo NGƯỜI DÙNG, không theo IP — vẫn tách riêng từng view.

    VÌ SAO CẦN (A13, 31/08/2026). Quota theo IP là đúng cho đường ẩn danh, nhưng
    sai cho một trung tâm luyện thi: cả phòng máy đi ra Internet bằng MỘT địa
    chỉ NAT, nên 30 em ngồi cùng phòng chia nhau đúng một quota. Từ 31/08 phòng
    luyện gọi `/check` MỖI CÂU (8 câu + 1 lượt chấm bài kiểm tra + 1 lượt xoá
    khi bắt đầu lại = 10 request mỗi bài), nên 30 em × 4 bài/giờ đã là 1200 —
    vượt trần 1000/giờ. Chạm trần thì bước kiểm tra đầu vào CHẶN HẲN không cho
    đi tiếp: cả lớp đứng.

    Ẩn danh thì trả `None` để throttle theo IP lo phần đó — đường này vốn đòi
    đăng nhập, nên nhánh ấy chỉ là phòng xa.
    """
    def get_cache_key(self, request, view):
        nguoi = getattr(request, 'user', None)
        if not (nguoi and nguoi.is_authenticated):
            return None
        return self.cache_format % {
            'scope': f'{self.scope}.{view.__class__.__module__}.{view.__class__.__name__}',
            'ident': nguoi.pk,
        }


class HourlyUserThrottle(_PerViewUserThrottle):
    scope = 'user_hour'


class DailyUserThrottle(_PerViewUserThrottle):
    scope = 'user_day'


class LoginThrottle(SimpleRateThrottle):
    """@limiter.limit("5 per minute") trên /auth/login."""
    scope = 'login'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class RegisterThrottle(SimpleRateThrottle):
    """@limiter.limit("3 per minute") trên /auth/register."""
    scope = 'register'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}
