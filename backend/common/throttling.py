"""
Rate limit — port từ Flask-Limiter (extensions.py: 200/day + 50/hour theo IP).

QUAN TRỌNG (khác biệt semantics phải giữ): Flask-Limiter đếm PER-ENDPOINT
per-IP — mỗi route có quota 50/hour riêng. DRF throttle mặc định đếm GỘP mọi
endpoint chung 1 quota → 1 lần load dashboard (~20 API call) sẽ đốt gần hết
50/hour, tái diễn đúng lớp bug 429 mà AUDIT-FIX 2026-07-07 đã xử lý.
→ Key cache ở đây gồm cả tên view để quota tính riêng từng endpoint như cũ.
"""
from rest_framework.throttling import SimpleRateThrottle

from common.net import client_ip


class _IPKhach:
    """Lấy IP khách qua `common.net.client_ip`, KHÔNG qua `get_ident` của DRF.

    Hai hàm ấy cùng công thức và cùng đọc `NUM_PROXIES`, nên hôm nay chúng bằng
    nhau. Nhưng nhật ký kiểm toán cũng phải trả lời đúng câu hỏi này, và một
    trong hai bản sẽ được sửa trước bản kia — đã xảy ra: `audit._client_ip` lấy
    phần tử ĐẦU trong khi `get_ident` lấy phần tử CUỐI, tức cùng một request bị
    chặn vì IP này lại vào sổ dưới IP kia.

    Nên ở đây là MỘT cửa (`RULES §6`), không phải hai bản trùng khớp.
    """
    def get_ident(self, request):
        return client_ip(request)


class _PerViewIPThrottle(_IPKhach, SimpleRateThrottle):
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


class LoginThrottle(_IPKhach, SimpleRateThrottle):
    """Chống dò mật khẩu ở /auth/login. Mức THẬT nằm ở `DEFAULT_THROTTLE_RATES`.

    ── CHÚ THÍCH NÀY TỪNG NÓI DỐI (sửa 07/09/2026) ──────────────────────────

    Nó ghi `@limiter.limit("5 per minute")` — mức của bản Flask cũ. Mức đang
    chạy là **20/phút ở production**, 100/phút ở dev. Người đọc tin vào dòng
    ấy sẽ tưởng cửa đăng nhập chặt gấp bốn lần sự thật, và đó là loại hiểu sai
    đắt nhất: nó nằm ở đúng chỗ người ta đến để KIỂM TRA an ninh.

    20/phút là con số CÓ CÂN NHẮC, không phải lỏng lẻo: giới hạn đếm theo IP,
    mà cả một lớp học ngồi sau một NAT dùng chung một IP (xem chú thích ở
    `settings.py`). Siết xuống 5 là khoá cửa với một lớp đang đăng nhập vào
    đầu buổi học.

    ĐÃ ĐO 07/09/2026: bắn liên tiếp ở dev, bị chặn (429) đúng ở lần thứ 101
    trong 36,4 giây — khớp mức 100/phút.

    (Lần đo đầu dùng vòng lặp `curl` trong bash mất hơn 60 giây, tức vượt cửa
    sổ một phút, và suýt kết luận "không có giới hạn". Phép đo về tần suất phải
    tính cả thời gian nó chạy.)
    """
    scope = 'login'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class RegisterThrottle(_IPKhach, SimpleRateThrottle):
    """Giới hạn ở /auth/register. Mức THẬT nằm ở `DEFAULT_THROTTLE_RATES`.

    Cùng lỗi với `LoginThrottle`: chú thích ghi "3 per minute" (mức Flask cũ),
    mức đang chạy là 10/phút ở production, 100/phút ở dev. Sửa 07/09/2026.

    Từ 27/08/2026 đường này còn đòi `IsAdminRole` (không còn tự đăng ký), nên
    giới hạn tần suất ở đây là lớp thứ hai chứ không phải lớp duy nhất.
    """
    scope = 'register'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}
