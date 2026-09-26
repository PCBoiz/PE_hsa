"""ĐỒNG HỒ CỦA CỬA QUÊN MẬT KHẨU (§52) — không khai ra ai có tài khoản.

Thân phản hồi của hai nhánh giống hệt nhau (`CAU_CHUNG`) — đó là chủ ý, và docstring của
`QuenMatKhauView` nói *"để thời gian trả lời cũng không khác nhau"*. Nhưng câu ấy chỉ đúng
cho phần GỬI THƯ; phần còn lại thì không.

── ĐO ĐƯỢC 27/09/2026 (máy dev, VN → Neon us-east-2) ─────────────────────────

  email CÓ tài khoản:    2,034 s · 2,291 s
  email KHÔNG có:        0,250 s · 0,293 s · 0,356 s

Chênh gần HAI GIÂY, ổn định. Ai cũng dò được địa chỉ nào đã có tài khoản ở TopHSA bằng
một cái đồng hồ bấm giây — mà người dùng ở đây là trẻ vị thành niên, và danh sách "em nào
học TopHSA" không phải thứ để ai cũng lấy được.

ĐO LẠI SAU KHI CÂN phần CPU: 2,04–2,54 s so với 0,254–0,263 s. **Vẫn chênh** — phần nặng
là chín vòng gọi CSDL chứ không phải CPU, và trên máy dev mỗi vòng VN → Neon us-east-2 mất
~250 ms. `quen_mat_khau._can_dong_ho` nói rõ chỗ này chưa đóng và đóng nốt thì phải làm gì.

── VÌ SAO KHÔNG ĐO BẰNG GIÂY Ở ĐÂY ──────────────────────────────────────────

Một phép kiểm so hai mốc thời gian sẽ đỏ vì máy bận, vì mạng, vì Neon vừa ngủ dậy — rồi
người ta tắt nó đi. Thay vào đó ghim thứ ỔN ĐỊNH: nhánh KHÔNG có tài khoản phải LÀM đúng
những việc tốn CPU mà nhánh kia làm (soạn thư). Phần dư còn lại là số vòng gọi CSDL, và
chú thích trong mã nói thẳng như vậy chứ không nhận là đã xoá hết.
"""
import pytest

from accounts import quen_mat_khau
from common.db import q1

pytestmark = pytest.mark.django_db

DUONG = '/auth/quen-mat-khau'


def _goi(api, email):
    return api.post(DUONG, {'email': email}, format='json')


def test_hai_nhanh_tra_ve_cung_mot_cau(api):
    """Có tài khoản hay không, người gửi đọc được đúng một câu."""
    co = q1("SELECT email FROM users WHERE status IS DISTINCT FROM 'suspended' LIMIT 1")
    a = _goi(api, co['email'])
    b = _goi(api, 'khong-he-co-dia-chi-nay-27-09@example.com')
    assert a.status_code == b.status_code == 200
    assert a.data == b.data, 'hai nhánh trả lời khác nhau — đọc là biết ai có tài khoản'


def test_nhanh_khong_co_tai_khoan_van_soan_thu_de_can_dong_ho(api, monkeypatch):
    """Phần TỐN CPU phải chạy ở CẢ HAI nhánh, không chỉ nhánh có tài khoản.

    Ghim bằng SỐ LỜI GỌI chứ không bằng giây: một phép kiểm so đồng hồ sẽ đỏ vì máy bận
    rồi bị tắt đi, còn lời gọi thì đếm được chắc chắn.
    """
    dem = {'n': 0}
    goc = quen_mat_khau._soan_thu

    def dem_soan(*a, **k):
        dem['n'] += 1
        return goc(*a, **k)

    monkeypatch.setattr(quen_mat_khau, '_soan_thu', dem_soan)
    _goi(api, 'khong-he-co-dia-chi-nay-27-09b@example.com')
    assert dem['n'] >= 1, ('nhánh "không có tài khoản" trả lời mà không soạn thư — '
                           'đồng hồ khai ra địa chỉ nào đã có tài khoản')


def test_email_sai_dinh_dang_van_bi_tu_choi_som(api):
    """Cân đồng hồ KHÔNG được biến một địa chỉ hỏng thành một lượt soạn thư vô ích."""
    r = _goi(api, 'khong-phai-email')
    assert r.status_code == 400
