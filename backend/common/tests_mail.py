"""Đường gửi thư ra ngoài, và các chốt hãm của nó.

KHÔNG lời gọi SMTP thật nào: `smtplib` của `common.mail` bị thay bằng bản giả.
Gọi thật trong bộ kiểm là gửi thư thật, tới người thật, từ hộp thư thật.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. `EMAIL_CHE_DO_THU=1` thì **không một kết nối SMTP nào** được mở. Chế độ
     thử mà vẫn gửi thì nó nguy hiểm hơn là không có.
  2. Chưa cấu hình mà KHÔNG ở chế độ thử thì **trả lỗi, không im lặng nuốt**.
     Một hàm gửi thư trả `True` khi chưa có mật khẩu là thứ khiến người ta
     tưởng phụ huynh đã nhận.
  3. Thư phải có **cả phần chữ thuần lẫn phần HTML**. Thư chỉ HTML bị bộ lọc
     rác chấm điểm thấp, và báo cáo học tập rơi vào Spam thì cả đường này vô
     nghĩa.
  4. **Lỗi là GIÁ TRỊ, không phải ngoại lệ** — đường gửi báo cáo là một vòng
     lặp cả lớp; ném ở em thứ ba thì 22 em còn lại không được gửi.
  5. Sai App Password phải nói ĐÚNG nguyên nhân. Đây là lỗi phổ biến nhất và
     câu lỗi gốc của Gmail không nhắc gì tới App Password.
"""
import email
import smtplib
from pathlib import Path

import pytest

from common import mail

THU_MUC = None  # đặt trong fixture


@pytest.fixture(autouse=True)
def moi_truong_sach(monkeypatch, tmp_path):
    """Mỗi phép kiểm chạy trên một môi trường không dính cấu hình của máy thật."""
    for k in ('EMAIL_CHE_DO_THU', 'EMAIL_USER', 'EMAIL_APP_PASSWORD',
              'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_TU_TEN'):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv('EMAIL_THU_MUC_THU', str(tmp_path / 'thu'))
    return tmp_path


@pytest.fixture
def smtp_gia(monkeypatch):
    """Thay `smtplib` của `common.mail`. Trả sổ ghi mọi lần kết nối và gửi."""
    so = {'ket_noi': [], 'dang_nhap': [], 'gui': [], 'nem': None}

    class SMTPGia:
        def __init__(self, host, port, timeout=None):
            so['ket_noi'].append((host, port, timeout))

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self, context=None):
            pass

        def login(self, u, m):
            if so['nem'] is not None:
                raise so['nem']
            so['dang_nhap'].append((u, m))

        def send_message(self, m):
            so['gui'].append(m)

    monkeypatch.setattr(mail.smtplib, 'SMTP', SMTPGia)
    return so


# ── 1. Chế độ thử ─────────────────────────────────────────────────────────

def test_che_do_thu_ghi_eml_va_KHONG_mo_ket_noi_nao(monkeypatch, smtp_gia):
    monkeypatch.setenv('EMAIL_CHE_DO_THU', '1')

    ok, dau_vet, loi = mail.gui('ai@example.com', 'Thử', 'chào')

    assert ok is True and loi is None
    assert dau_vet.startswith('THU:')
    assert smtp_gia['ket_noi'] == [], 'chế độ thử vẫn mở kết nối SMTP'
    p = Path(dau_vet[4:])
    assert p.exists() and p.read_bytes()[:1] not in (b'', None)


def test_che_do_thu_khong_can_mat_khau():
    """Không có EMAIL_USER/APP_PASSWORD mà chế độ thử vẫn chạy trọn luồng.

    Đây là toàn bộ mục đích của chế độ này: xem được thư TRƯỚC khi có mật khẩu.
    """
    import os
    os.environ['EMAIL_CHE_DO_THU'] = '1'
    try:
        assert mail.da_cau_hinh() is False
        ok, _, loi = mail.gui('ai@example.com', 'Thử', 'chào')
        assert ok is True and loi is None
    finally:
        os.environ.pop('EMAIL_CHE_DO_THU', None)


# ── 2. Chưa cấu hình thì phải BÁO ─────────────────────────────────────────

def test_chua_cau_hinh_va_khong_thu_thi_tra_LOI(smtp_gia):
    ok, dau_vet, loi = mail.gui('ai@example.com', 'Thử', 'chào')

    assert ok is False and dau_vet is None
    assert 'EMAIL_USER' in loi and 'EMAIL_APP_PASSWORD' in loi
    assert smtp_gia['ket_noi'] == []


def test_thieu_gi_neu_ten_bien_con_trong(monkeypatch):
    assert mail.thieu_gi() == ['EMAIL_USER', 'EMAIL_APP_PASSWORD']
    monkeypatch.setenv('EMAIL_USER', 'a@gmail.com')
    assert mail.thieu_gi() == ['EMAIL_APP_PASSWORD']
    monkeypatch.setenv('EMAIL_APP_PASSWORD', 'x' * 16)
    assert mail.thieu_gi() == [] and mail.da_cau_hinh() is True


def test_dia_chi_hong_thi_dung_truoc_khi_dung_thu(monkeypatch, smtp_gia):
    monkeypatch.setenv('EMAIL_USER', 'a@gmail.com')
    monkeypatch.setenv('EMAIL_APP_PASSWORD', 'x' * 16)

    for xau in ('', 'khong-co-cham-a', None):
        ok, _, loi = mail.gui(xau, 'Thử', 'chào')
        assert ok is False and 'không hợp lệ' in loi
    assert smtp_gia['ket_noi'] == []


# ── 3. Hình dạng lá thư ───────────────────────────────────────────────────

def test_thu_co_ca_chu_thuan_lan_html_va_dinh_kem(monkeypatch, smtp_gia):
    monkeypatch.setenv('EMAIL_USER', 'gui@gmail.com')
    monkeypatch.setenv('EMAIL_APP_PASSWORD', 'x' * 16)

    ok, _, loi = mail.gui('nhan@example.com', 'Tiêu đề Việt — có dấu',
                          'chữ thuần', '<p>html</p>',
                          (('a.pdf', 'application/pdf', b'%PDF-1.4 gia'),))
    assert ok is True and loi is None

    m = smtp_gia['gui'][0]
    kieu = [p.get_content_type() for p in m.walk()]
    assert kieu[0] == 'multipart/mixed'
    assert 'text/plain' in kieu and 'text/html' in kieu and 'application/pdf' in kieu
    # Tiêu đề có dấu phải được mã hoá đúng chuẩn, không rơi rụng dấu.
    assert 'Tiêu đề Việt — có dấu' in str(email.header.make_header(
        email.header.decode_header(m['Subject'])))
    assert [p.get_filename() for p in m.walk() if p.get_filename()] == ['a.pdf']


def test_moi_thu_co_mot_Message_ID_rieng(monkeypatch, smtp_gia):
    """Không có Message-ID thì `gui()` trả về dấu vết rỗng, và sổ gửi ghi một ô
    trống cho mọi lá thư — tức sổ không lần lại được thư nào."""
    monkeypatch.setenv('EMAIL_USER', 'gui@gmail.com')
    monkeypatch.setenv('EMAIL_APP_PASSWORD', 'x' * 16)

    _, a, _ = mail.gui('x@example.com', 'A', 'a')
    _, b, _ = mail.gui('x@example.com', 'B', 'b')
    assert a and b and a != b


def test_ten_hien_thi_lay_tu_bien_moi_truong(monkeypatch, smtp_gia):
    monkeypatch.setenv('EMAIL_USER', 'gui@gmail.com')
    monkeypatch.setenv('EMAIL_APP_PASSWORD', 'x' * 16)
    monkeypatch.setenv('EMAIL_TU_TEN', 'TopHSA')

    mail.gui('x@example.com', 'A', 'a')
    assert 'TopHSA' in smtp_gia['gui'][0]['From']


# ── 4 & 5. Lỗi là giá trị, và câu lỗi phải chỉ đúng nguyên nhân ───────────

def test_sai_app_password_thi_noi_DUNG_nguyen_nhan(monkeypatch, smtp_gia):
    monkeypatch.setenv('EMAIL_USER', 'gui@gmail.com')
    monkeypatch.setenv('EMAIL_APP_PASSWORD', 'mat-khau-google-thuong')
    smtp_gia['nem'] = smtplib.SMTPAuthenticationError(535, b'bad creds')

    ok, dau_vet, loi = mail.gui('x@example.com', 'A', 'a')

    assert ok is False and dau_vet is None
    # Câu lỗi gốc của Gmail KHÔNG nhắc gì tới App Password, mà đó đúng là
    # nguyên nhân trong hầu hết các lần. Nói thẳng ra thì người đọc sửa được.
    assert 'App Password' in loi


def test_mang_hong_thi_tra_loi_chu_KHONG_nem(monkeypatch, smtp_gia):
    monkeypatch.setenv('EMAIL_USER', 'gui@gmail.com')
    monkeypatch.setenv('EMAIL_APP_PASSWORD', 'x' * 16)
    smtp_gia['nem'] = OSError('mạng chết')

    ok, _, loi = mail.gui('x@example.com', 'A', 'a')

    assert ok is False and 'mạng chết' in loi


# ── Tên tệp .eml ──────────────────────────────────────────────────────────

def test_ten_tep_eml_khong_chua_ky_tu_windows_tu_choi(monkeypatch):
    monkeypatch.setenv('EMAIL_CHE_DO_THU', '1')

    ok, dau_vet, _ = mail.gui('ai@example.com',
                              'Báo cáo: A/B — kỳ 10/08 – 07/09 <thử>', 'x')

    assert ok is True
    ten = Path(dau_vet[4:]).name
    for c in '\\/:*?"<>|':
        assert c not in ten, 'tên tệp chứa %r — Windows từ chối' % c


# ── CHÈN HEADER THƯ (audit 07/09/2026) ─────────────────────────────────────
#
# Tiêu đề thư chứa TÊN HỌC VIÊN lấy từ CSDL, và địa chỉ người nhận là
# `users.parent_email` — cả hai là chuỗi người khác nhập. Một ký tự xuống dòng
# trong đó biến thành một header THẬT: "\nBcc: ke-trom@..." làm báo cáo của một
# đứa trẻ đi kèm tới một địa chỉ lạ.
#
# Audit đo được: `EmailMessage` CHẶN được, nhưng chặn bằng `ValueError` — mà
# `gui()` hứa với mọi nơi gọi là không ném ngoại lệ, và nó nằm giữa vòng lặp
# gửi cả lớp. Một em có tên lạ làm hỏng lượt gửi của 24 em còn lại.

XUONG_DONG = ['\n', '\r', '\r\n', '\u2028']


def test_dia_chi_co_xuong_dong_bi_TU_CHOI_bang_gia_tri(monkeypatch, smtp_gia):
    """Địa chỉ thì TỪ CHỐI, không dọn: gửi tới một địa chỉ đã bị sửa là gửi
    báo cáo của một đứa trẻ cho người khác."""
    monkeypatch.setenv('EMAIL_USER', 'gui@gmail.com')
    monkeypatch.setenv('EMAIL_APP_PASSWORD', 'x' * 16)

    for nl in XUONG_DONG:
        xau = 'a@b.com%sBcc: ke-trom@evil.com' % nl
        ok, dau_vet, loi = mail.gui(xau, 'Thử', 'x')   # KHÔNG được ném
        assert ok is False and dau_vet is None
        assert 'không hợp lệ' in loi
    assert smtp_gia['gui'] == [], 'đã gửi một lá thư có địa chỉ bị chèn'


def test_tieu_de_co_xuong_dong_bi_DON_chu_khong_lam_hong_ca_luot(monkeypatch, smtp_gia):
    """Tiêu đề thì DỌN: tên học viên có ký tự lạ không được biến thành lý do
    em ấy vĩnh viễn không nhận báo cáo."""
    monkeypatch.setenv('EMAIL_USER', 'gui@gmail.com')
    monkeypatch.setenv('EMAIL_APP_PASSWORD', 'x' * 16)

    ok, _, loi = mail.gui('nhan@example.com',
                          'Báo cáo của Lê An\nBcc: ke-trom@evil.com', 'x')
    assert ok is True and loi is None, loi

    m = smtp_gia['gui'][0]
    assert m.get('Bcc') is None, 'chèn được header Bcc qua tiêu đề'
    # Và không có DÒNG header Bcc nào trong thân thô — kiểm ở tầng byte, vì
    # `m.get` chỉ đọc những header mà bộ phân tích công nhận.
    assert not any(d.startswith(b'Bcc:') for d in bytes(m).split(b'\r\n'))


def test_ten_hien_thi_co_xuong_dong_cung_bi_don(monkeypatch, smtp_gia):
    """`EMAIL_TU_TEN` đọc từ biến môi trường — trên Render là ô người ta gõ tay."""
    monkeypatch.setenv('EMAIL_USER', 'gui@gmail.com')
    monkeypatch.setenv('EMAIL_APP_PASSWORD', 'x' * 16)
    monkeypatch.setenv('EMAIL_TU_TEN', 'TopHSA\nBcc: ke-trom@evil.com')

    ok, _, _ = mail.gui('nhan@example.com', 'Thử', 'x')
    assert ok is True
    assert not any(d.startswith(b'Bcc:') for d in bytes(smtp_gia['gui'][0]).split(b'\r\n'))


def test_gui_KHONG_BAO_GIO_nem_du_soan_thu_hong(monkeypatch, smtp_gia):
    """Lưới chặn cuối. `gui()` hứa "lỗi là giá trị" với một vòng lặp gửi cả
    lớp; lời hứa ấy chỉ đáng tin khi có chỗ bắt tất cả."""
    monkeypatch.setenv('EMAIL_USER', 'gui@gmail.com')
    monkeypatch.setenv('EMAIL_APP_PASSWORD', 'x' * 16)

    def no(*a, **k):
        raise ValueError('hỏng giả lập')
    monkeypatch.setattr(mail, 'soan', no)

    ok, dau_vet, loi = mail.gui('a@b.com', 'Thử', 'x')   # KHÔNG được ném
    assert ok is False and dau_vet is None
    assert 'hỏng giả lập' in loi


def test_don_header_giu_nguyen_chu_viet():
    """Dọn xuống dòng KHÔNG được đụng tới dấu tiếng Việt."""
    assert mail.don_header('Nguyễn Thị Hà — kỳ 10/08') == 'Nguyễn Thị Hà — kỳ 10/08'
    assert mail.don_header(None) == ''
