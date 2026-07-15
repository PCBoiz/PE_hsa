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
