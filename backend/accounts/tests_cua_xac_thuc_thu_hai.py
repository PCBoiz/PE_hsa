"""CỬA XÁC THỰC THỨ HAI của `django-allauth` — audit bảo mật 27/09/2026.

`config/urls.py` nạp cả `allauth.urls` để lấy một thứ duy nhất: đường đăng nhập Google
(`/accounts/google/login/`). Nhưng gói ấy kéo theo **cả bộ giao diện tài khoản của thư
viện** — đăng nhập, đăng ký, đổi mật khẩu, quên mật khẩu, đổi email. Đo bằng GET trên máy
dev 27/09: `/accounts/login/` trả **200 kèm biểu mẫu "Sign In"**, `/accounts/password/reset/`
trả **200 kèm biểu mẫu**.

VÌ SAO ĐÓ LÀ LỖ, chứ không phải một trang thừa vô hại — không hàng rào nào của dự án chạm
tới chúng:

  · **không thu hồi phiên**: ba đường đổi mật khẩu của dự án đều nâng `tokens_valid_from`
    để mọi thẻ cũ chết. Đường của thư viện thì không — kẻ đã chiếm tài khoản đổi mật khẩu
    ở đó, người thật đổi lại, mà thẻ của kẻ kia vẫn sống;
  · **không để lại dấu**: mọi lượt đổi mật khẩu của dự án vào `admin_audit`. Đường này
    không ghi gì, nên nhìn nhật ký sẽ thấy "không ai đổi mật khẩu";
  · **trần dò mật khẩu riêng**, cộng thêm vào trần của dự án thay vì dùng chung;
  · **hàng rào thư §61 không áp**: thư của thư viện đi bằng `django.core.mail`, không qua
    hộp chờ và không qua hàng rào chỉ-gửi-địa-chỉ-thử;
  · chữ tiếng Anh giữa một sản phẩm tiếng Việt (RULES §10).

`User.set_password` ghi ĐÚNG định dạng werkzeug (`accounts/models.py`), nên mật khẩu đặt
qua cửa thư viện dùng đăng nhập bằng cửa của dự án được ngay — hai cửa nối thẳng vào nhau.

Phép kiểm này giữ đúng một điều: **chỉ đường OAuth còn sống, mọi cửa tài khoản khác của thư
viện phải biến mất.** Đăng nhập Google là thứ mình cố ý nạp gói ấy để có.
"""
import pytest
from django.urls import NoReverseMatch, reverse

#: Những cửa của thư viện phải KHÔNG còn đường tới. Mỗi dòng là một cửa đã đo được là mở
#: trước khi vá — không phải một danh sách phòng xa.
CUA_PHAI_MAT = [
    '/accounts/login/',
    '/accounts/signup/',
    '/accounts/logout/',
    '/accounts/password/reset/',
    '/accounts/password/change/',
    '/accounts/password/set/',
    '/accounts/email/',
]


@pytest.mark.parametrize('duong', CUA_PHAI_MAT)
def test_cua_tai_khoan_cua_thu_vien_khong_con_duong_toi(client, duong):
    """404 chứ không 200/302: đường không tồn tại thì không ai gõ vào được."""
    assert client.get(duong).status_code == 404, duong


def test_duong_dang_nhap_google_VAN_SONG():
    """Thứ DUY NHẤT mình cần ở gói ấy phải còn — vá mà mất nó là hỏng đăng nhập Google.

    Dùng `reverse` chứ không gọi GET: gọi thật sẽ đi tới Google, và một phép kiểm phụ thuộc
    mạng bên ngoài là một phép kiểm thỉnh thoảng đỏ vì lý do không liên quan.
    """
    try:
        duong = reverse('google_login')
    except NoReverseMatch:
        pytest.fail('mất đường đăng nhập Google — đó là lý do duy nhất nạp allauth')
    assert duong.startswith('/accounts/'), duong
