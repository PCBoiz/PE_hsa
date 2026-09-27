"""BƠM CHỮ VÀO THÂN THƯ ĐĂNG KÝ (audit bảo mật 27/09/2026).

`POST /auth/dang-ky` nhận HAI thứ do người gửi tự gõ và đưa cả hai vào một lá thư
mà máy chủ TopHSA gửi đi bằng SMTP thật:

  · `email` — ĐỊA CHỈ NHẬN. Bất kỳ địa chỉ nào chưa có tài khoản đều nhận được thư
    "Xác nhận email tài khoản TopHSA". Đây là bản chất của việc xác nhận email,
    không vá được, và cũng không nguy nếu thân thư là cố định.
  · `name` — đi thẳng vào câu chào `Chào %s,` ở ĐẦU thân thư, tối đa 100 ký tự và
    KHÔNG lọc xuống dòng.

Ghép hai thứ ấy: một người lạ chưa đăng nhập soạn được vài dòng chữ tuỳ ý rồi bắt
máy chủ TopHSA gửi tới địa chỉ họ chọn — thư đi từ tên miền thật, qua SPF/DKIM
thật, nên nó vượt bộ lọc rác tốt hơn hẳn thư giả mạo. Thứ mất đi là uy tín người
gửi của trung tâm, và nạn nhân là người ngoài hệ thống (không ai trong TopHSA
thấy chuyện đang xảy ra).

Tiêu đề và địa chỉ nhận thì KHÔNG tiêm được (`email_validator` chặn xuống dòng, và
`common/mail.py::_XUONG_DONG` là lưới thứ hai) — đây không phải tiêm header.

Phép kiểm chạy Ở TẦNG SOẠN THƯ, không gọi cửa `/auth/dang-ky`: cửa ấy TẠO một dòng
`users` và XẾP một lá thư thật vào hộp thư đi, và nhịp hộp thư chạy nền có thể lấy
ra gửi trước khi giao dịch của phép kiểm kịp cuộn lại. Chuỗi đi vào `_soan_thu` là
đúng chuỗi cửa ấy truyền vào (`v['ten']`, xem `DangKyView._mo_tai_khoan`), nên đây
vẫn là đường mà người tấn công đi.
"""
import pytest

from accounts.tu_dang_ky import _soan_thu, _soan_thu_da_co

#: Đúng hình dạng một kẻ tấn công sẽ gõ: kết thúc câu chào rồi viết tiếp thân thư.
TEN_TIEM = ('ban,\n\nCANH BAO: tai khoan cua ban se bi khoa trong 24 gio.\n'
            'Xac minh tai: https://gia-mao.example.com/khan\n\nTopHSA')

#: Địa chỉ dụ nằm trong tên tiêm. Sau khi vá thì câu chào bị cắt ngắn nên nó không
#: còn nguyên vẹn ở bất kỳ đâu trong thư — đó là thứ đo được, không phải suy.
MIEN_DU = 'gia-mao.example.com'


@pytest.mark.parametrize('soan', [
    pytest.param(lambda t: _soan_thu(t, 'https://tophsa.vn/xac-thuc-email#chia=X'), id='xac-nhan'),
    pytest.param(lambda t: _soan_thu_da_co(t), id='da-co-tai-khoan'),
])
def test_ten_nguoi_gui_khong_xuong_dong_duoc_trong_than_thu(soan):
    """Tên đi vào câu chào không được mang xuống dòng — cả bản chữ lẫn bản HTML.

    Câu chào là DÒNG ĐẦU của thân thư, nên "không xuống dòng được" = mọi thứ người
    gửi gõ vẫn nằm trong đúng dòng ấy.
    """
    chu, trang = soan(TEN_TIEM)
    dong_dau = chu.split('\n', 1)[0]
    assert dong_dau.startswith('Chào ') and dong_dau.endswith(','), dong_dau
    assert MIEN_DU not in chu, (
        'chữ do người gửi gõ xuống dòng được trong thân thư, nên họ soạn được nhiều '
        'dòng tuỳ ý ở ĐẦU một lá thư TopHSA gửi tới địa chỉ họ chọn:\n---\n%s\n---' % chu[:400])
    assert MIEN_DU not in trang, 'bản HTML cũng vậy'
    assert '\n' not in trang.split('</p>')[0], 'đoạn <p> chào phải nằm trên một dòng'


@pytest.mark.parametrize('soan', [
    pytest.param(lambda t: _soan_thu(t, 'https://tophsa.vn/xac-thuc-email#chia=X'), id='xac-nhan'),
    pytest.param(lambda t: _soan_thu_da_co(t), id='da-co-tai-khoan'),
])
def test_ten_qua_dai_khong_day_noi_dung_that_xuong_duoi(soan):
    """Tên 100 ký tự vẫn để lọt một đoạn dài ở đầu thư. Cắt ngắn cho câu chào là câu chào."""
    chu, _ = soan('x' * 100)
    assert len(chu.split(',', 1)[0]) <= 45, (
        'câu chào dài %d ký tự — đủ chỗ cho một câu dụ' % len(chu.split(',', 1)[0]))


def test_ten_binh_thuong_van_hien_nguyen(soan=None):
    """Hàng rào không được ăn vào tên thật: dấu tiếng Việt, khoảng trắng giữa các từ."""
    chu, trang = _soan_thu('Nguyễn Thị Mai Anh', 'https://tophsa.vn/x#chia=X')
    assert chu.startswith('Chào Nguyễn Thị Mai Anh,')
    assert '<p>Chào Nguyễn Thị Mai Anh,</p>' in trang


def test_ten_rong_van_ra_ban():
    """Tên trống (tài khoản cũ chưa có tên) vẫn phải ra câu chào đọc được."""
    chu, _ = _soan_thu('   ', 'https://tophsa.vn/x#chia=X')
    assert chu.startswith('Chào bạn,')
