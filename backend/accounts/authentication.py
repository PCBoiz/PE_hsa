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


def invalidate_user_cache(user_id):
    cache.delete(_KEY.format(user_id))


class CachedJWTAuthentication(JWTAuthentication):
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
