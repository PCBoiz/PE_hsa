"""
CachedJWTAuthentication — PERF 2026-07-19.

JWTAuthentication gốc SELECT users theo id ở MỌI request chỉ để dựng
request.user. Với DB ở region xa (đo được ~260ms/query khi dev từ VN),
riêng bước này đã ăn quá nửa ngân sách 500ms/response.

Cache user 60s trong LocMemCache (per-process). Đánh đổi chấp nhận được:
đổi role/xóa user có hiệu lực chậm tối đa 60s trên API (JWT access token
vốn đã sống 30 phút nên đây không phải cửa thu hồi quyền). View nào GHI
vào bảng users (xp, gems, streak...) vẫn đúng vì chúng UPDATE bằng SQL
trực tiếp rồi SELECT lại — không đọc từ request.user.
"""
from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication

USER_CACHE_SECONDS = 60
_KEY = 'auth_user:{}'

#: Đường được đi khi tài khoản còn cờ `must_change_password`.
#:
#: Đúng bốn thứ, và mỗi thứ có lý do riêng: đọc hồ sơ mình (màn hình cần tên để
#: vẽ), đổi mật khẩu (chính việc phải làm), làm mới token (phiên không được chết
#: giữa chừng), đăng xuất (luôn phải thoát được).
CHO_PHEP_KHI_PHAI_DOI_MK = (
    '/api/user',            # bao gồm cả /api/user/password
    '/auth/refresh',
    '/auth/logout',
)


def invalidate_user_cache(user_id):
    cache.delete(_KEY.format(user_id))


class CachedJWTAuthentication(JWTAuthentication):
    """Xác thực JWT có bộ đệm, kèm hàng rào `must_change_password`.

    VÌ SAO HÀNG RÀO NẰM Ở ĐÂY. Cờ `must_change_password` trước 31/08/2026 chỉ
    được ép ở màn hình đăng nhập (`LoginForm.tsx` điều hướng đi). Backend không
    view nào đọc nó: đăng nhập cấp JWT đầy đủ, và gõ thẳng bất kỳ URL nào khác
    là dùng được cả ứng dụng mà không bao giờ đổi mật khẩu tạm — mật khẩu mà
    trợ giảng vừa đọc to cho học viên nghe.

    KHÔNG đặt ở `DEFAULT_PERMISSION_CLASSES`: view nào khai
    `permission_classes` riêng (gần như cả khu `teaching/`) sẽ ghi đè danh sách
    mặc định và đi vòng qua hàng rào. Lớp xác thực thì mọi view đều dùng.

    KHÔNG đặt ở middleware: middleware chạy TRƯỚC khi DRF xác thực, nên
    `request.user` lúc đó còn là ẩn danh.
    """

    def authenticate(self, request):
        kq = super().authenticate(request)
        if kq is None:
            return None
        user, token = kq
        if getattr(user, 'must_change_password', False):
            duong = request.path or ''
            if not any(duong.startswith(t) for t in CHO_PHEP_KHI_PHAI_DOI_MK):
                # 403 chứ KHÔNG 401: 401 khiến lớp làm mới token ở frontend
                # tưởng phiên hết hạn, thử refresh, rồi đá về trang đăng nhập —
                # và vòng đó lặp mãi vì đăng nhập lại vẫn còn nguyên cờ.
                # Nhập MUỘN, và chỉ trên nhánh từ chối. Nhập ở đầu tệp tạo
                # vòng: `common.errors` kéo `rest_framework.views` → DRF giải
                # `DEFAULT_AUTHENTICATION_CLASSES` → quay lại chính tệp này khi
                # nó còn đang nạp dở. Nhánh này hiếm khi chạy nên chi phí bằng
                # một lần tra `sys.modules`.
                from common.errors import PhaiDoiMatKhau
                raise PhaiDoiMatKhau(
                    'Bạn đang dùng mật khẩu tạm. Đổi mật khẩu rồi mới dùng được '
                    'phần còn lại của hệ thống.')
        return kq

    def get_user(self, validated_token):
        try:
            user_id = validated_token['user_id']
        except KeyError:
            return super().get_user(validated_token)
        key = _KEY.format(user_id)
        user = cache.get(key)
        if user is None:
            user = super().get_user(validated_token)
            cache.set(key, user, USER_CACHE_SECONDS)
        return user
