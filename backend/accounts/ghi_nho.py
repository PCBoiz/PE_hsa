"""GHI NHỚ ĐĂNG NHẬP — góp ý TopHSA #1 (24/09/2026), anh Sơn chốt cùng ngày.

Ô "Ghi nhớ đăng nhập" ở màn đăng nhập:
  · tick   → refresh token sống 30 ngày, cookie ở Next sống theo (máy riêng);
  · không  → refresh 8 giờ như trước và Next đặt cookie PHIÊN — đóng trình duyệt
             là hết (máy dùng chung ở trung tâm).

Chế độ nằm TRONG token (claim `nho`) chứ không ở cookie hay CSDL: SimpleJWT
chép mọi claim sang access token, nên cả hai tầng Next (route `/auth/*` và
`src/proxy.ts`) đọc được mà không phải hỏi ai; và khi XOAY, claim đi theo.

Chỗ phải sửa của SimpleJWT: lúc xoay (`TokenRefreshSerializer.validate`) nó gọi
`refresh.set_exp()` với hạn MẶC ĐỊNH — phiên "30 ngày" sẽ lặng lẽ thành 8 giờ
sau lần làm mới đầu tiên. `RefreshGhiNho.set_exp` chọn hạn theo claim, nên cấp
lần đầu, xoay, và dòng trong bảng thu hồi (`outstand`) đều cùng một hạn.

Vẫn đúng khuyến nghị OWASP Session Management: token ghi nhớ xoay mỗi lần làm
mới, token cũ bị thu hồi ngay (`BLACKLIST_AFTER_ROTATION`), đổi mật khẩu cắt
mọi phiên (`tokens_valid_from`, `accounts/authentication.py`), token không bao
giờ nằm ở localStorage (cookie httpOnly).
"""
from datetime import timedelta

from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.hoat_dong import danh_dau

CLAIM_NHO = 'nho'
HAN_GHI_NHO = timedelta(days=30)


def muon_ghi_nho(gia_tri):
    """Chỉ `true` thật (JSON boolean) mới bật — "false", 0, "co"… đều không."""
    return gia_tri is True


class RefreshGhiNho(RefreshToken):
    def set_exp(self, claim='exp', from_time=None, lifetime=None):
        if lifetime is None and claim == 'exp' and self.payload.get(CLAIM_NHO):
            lifetime = HAN_GHI_NHO
        super().set_exp(claim, from_time, lifetime)


def cap_refresh(user_id, nho=False):
    """Refresh token cho `user_id`. `nho` → claim + hạn 30 ngày, ghi đúng hạn vào
    bảng thu hồi (dựng tay thay vì `for_user`: `for_user` ghi dòng thu hồi TRƯỚC
    khi kịp gắn claim, tức với hạn 8 giờ)."""
    token = RefreshGhiNho()
    token[api_settings.USER_ID_CLAIM] = str(user_id)
    if nho:
        token[CLAIM_NHO] = True
        token.set_exp()
    token.outstand()
    return token


class LamMoiSerializer(TokenRefreshSerializer):
    token_class = RefreshGhiNho


class LamMoiView(TokenRefreshView):
    """`POST /auth/refresh` — như SimpleJWT, khác ở hai chỗ: GIỮ chế độ ghi nhớ khi
    xoay, và đóng dấu §56 `last_seen_at` (`accounts/hoat_dong.py`)."""
    serializer_class = LamMoiSerializer

    def post(self, request, *args, **kwargs):
        # `TokenViewBase.post` NÉM `InvalidToken` khi refresh hết hạn / đã thu hồi
        # (DRF dựng 401), chỉ TRẢ VỀ khi đã làm mới xong — nên tới dòng đóng dấu là
        # thành công, không cần kiểm mã trạng thái (một phép `if status == 200` ở
        # đây không bao giờ sai: đột biến bỏ nó vẫn xanh, đo 24/09/2026).
        # `test_lam_moi_hong_khong_dong_dau` canh hành vi ấy qua URL thật.
        res = super().post(request, *args, **kwargs)
        # Mã người dùng đọc từ access token VỪA CẤP — `super().post` đã kiểm refresh,
        # không đọc lại thân request thô. Đây là cửa đóng dấu thường xuyên nhất: phiên
        # ghi nhớ 30 ngày không đăng nhập lại, thiếu dòng này thì người dùng đều đặn
        # nhất trông như "ngủ".
        danh_dau(int(AccessToken(res.data['access'])[api_settings.USER_ID_CLAIM]))
        return res
