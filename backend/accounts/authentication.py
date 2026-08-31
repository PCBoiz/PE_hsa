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
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

USER_CACHE_SECONDS = 60
_KEY = 'auth_user:{}'

#: Đường được đi khi tài khoản còn cờ `must_change_password`.
#:
#: Đúng bốn thứ, và mỗi thứ có lý do riêng: đọc hồ sơ mình (màn hình cần tên để
#: vẽ), đổi mật khẩu (chính việc phải làm), làm mới token (phiên không được chết
#: giữa chừng), đăng xuất (luôn phải thoát được).
#:
#: SO KHỚP CHÍNH XÁC, KHÔNG SO TIỀN TỐ. Bản đầu dùng `startswith('/api/user')`,
#: và `/api/users/11/follow` (số NHIỀU) bắt đầu bằng đúng chuỗi đó — đo
#: 31/08/2026: tài khoản còn mật khẩu tạm vẫn theo dõi người khác được. Nhẹ về
#: nghiệp vụ, nhưng nó chứng minh tiền tố không giữ nổi lời hứa "đúng bốn thứ":
#: mọi URL `/api/user*` thêm sau này sẽ tự động lọt mà không ai nhận ra.
CHO_PHEP_KHI_PHAI_DOI_MK = frozenset({
    '/api/user',
    '/api/user/password',
    '/auth/refresh',
    '/auth/logout',
})


def invalidate_user_cache(user_id):
    cache.delete(_KEY.format(user_id))


def _epoch_vn(naive_vn):
    """TIMESTAMP naive theo giờ VN → số giây UTC, để so được với `iat` của token."""
    return timezone.make_aware(naive_vn, timezone.get_current_timezone()).timestamp()


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

        if self._da_thu_hoi(user, token):
            # 401, KHÁC hẳn hàng rào mật khẩu tạm ở dưới (403). Ở đây phiên
            # THẬT SỰ đã kết thúc, nên để lớp làm mới token của frontend chạy
            # đúng vòng của nó: thử refresh → refresh cũng đã bị thu hồi → về
            # trang đăng nhập. Đó chính là thứ ta muốn.
            raise AuthenticationFailed(
                'Phiên đăng nhập đã kết thúc vì mật khẩu vừa được đổi. '
                'Đăng nhập lại bằng mật khẩu mới.')

        if getattr(user, 'must_change_password', False):
            duong = (request.path or '').rstrip('/')
            if duong not in CHO_PHEP_KHI_PHAI_DOI_MK:
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

    @staticmethod
    def _da_thu_hoi(user, token):
        """Token được cấp TRƯỚC lần thu hồi gần nhất của tài khoản này?

        VÌ SAO KHÔNG CHỈ DÙNG DANH SÁCH ĐEN. `token_blacklist` của SimpleJWT chỉ
        chặn được REFRESH token — access token được kiểm bằng CHỮ KÝ, không tra
        CSDL, nên nó sống đủ 30 phút bất kể ta làm gì với refresh. Trợ giảng bấm
        "Đặt lại mật khẩu" vì nghi tài khoản bị người khác dùng, mà người đang
        chiếm tài khoản vẫn thao tác bình thường thêm nửa tiếng.

        SO BẰNG EPOCH, không so hai đối tượng datetime. `iat` trong token là số
        giây UTC; `tokens_valid_from` là TIMESTAMP naive theo giờ VIỆT NAM (xem
        `common/clock.local_now`). So thẳng hai thứ đó là lệch đúng 7 tiếng —
        chính cái bẫy mà `common/clock.py` được viết ra để dập.

        Thiếu `iat` (token cũ cấp trước khi bật claim này) thì KHÔNG thu hồi:
        thà để một token cũ sống nốt hạn của nó còn hơn đá tất cả mọi người ra
        vì một thay đổi hạ tầng.
        """
        moc = getattr(user, 'tokens_valid_from', None)
        if not moc:
            return False
        try:
            iat = int(token['iat'])
        except (KeyError, TypeError, ValueError):
            return False
        return iat < _epoch_vn(moc)

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
