"""HÀNG RÀO THƯ Ở MÁY DEV (§61, E2 — quyết định 3 của anh Sơn 26/09/2026).

Câu hỏi: trên máy dev (CSDL KHÔNG phải production), một dòng hộp thư đi tới email THẬT
của học viên có rời khỏi máy chủ không?

Mọi phép kiểm chạy trong giao dịch cuộn lại (`conftest.py`) và không mở SMTP: `mail.gui`
bị thay bằng bản giả ghi lại lời gọi — nên "không gửi" ở đây là đo được bằng `da_gui == []`
chứ không phải tin vào trạng thái dòng.
"""
import pytest

from common.db import q1, x
from notifications import hang_rao_thu

pytestmark = pytest.mark.django_db

THAT = 'phuhuynh.thuc.te@gmail.com'


@pytest.fixture
def thu(monkeypatch):
    """Email đã cấu hình, `mail.gui` giả (ghi lại lời gọi, luôn thành công)."""
    from common import mail
    da_gui = []
    monkeypatch.setattr(mail, 'da_cau_hinh', lambda: True)
    monkeypatch.setattr(mail, 'che_do_thu', lambda: False)
    monkeypatch.setattr(mail, 'gui', lambda den, td, chu, html=None, dk=():
                        (da_gui.append(den), (True, '<gia>', None))[1])
    return da_gui


@pytest.fixture
def khong_production(monkeypatch):
    """CSDL KHÔNG phải production — hàng rào BẬT (không phụ thuộc .env của máy đang chạy)."""
    from common import hang_rao_csdl
    monkeypatch.setattr(hang_rao_csdl, 'dang_tro_production', lambda *a, **k: False)


@pytest.fixture(autouse=True)
def sach_bien(monkeypatch):
    """Không để biến môi trường của máy đang chạy quyết định kết quả phép kiểm."""
    for b in (hang_rao_thu.BIEN_DIA_CHI, hang_rao_thu.BIEN_SO, hang_rao_thu.BIEN_E2E):
        monkeypatch.delenv(b, raising=False)
    monkeypatch.setattr(hang_rao_thu, 'THE_E2E', 'khong-co-tep-nay.json')


def _gui(den, channel='email', **k):
    from notifications.hop_thu import gui_ngay, xep
    oid = xep(channel, den, 'Tiêu đề', 'Thân', **k)
    gui_ngay([oid])
    return q1('SELECT status, error, attempts, next_try_at, sent_at FROM outbox WHERE id = %s', (oid,))


# ── Hàng rào bật / tắt ──────────────────────────────────────────────────────

def test_hang_rao_bat_khi_csdl_khong_phai_production(khong_production):
    assert hang_rao_thu.bat() is True


def test_hang_rao_tat_khi_csdl_la_production(monkeypatch):
    from common import hang_rao_csdl
    monkeypatch.setattr(hang_rao_csdl, 'dang_tro_production', lambda *a, **k: True)
    assert hang_rao_thu.bat() is False
    assert hang_rao_thu.ly_do_chan('email', THAT) is None, 'trên production thư phải đi như thường'


def test_may_nay_dang_bat_hang_rao():
    """ĐO máy đang chạy: CSDL dev thì hàng rào phải đang bật THẬT, không chỉ bật khi giả.

    Nếu phép kiểm này đỏ nghĩa là máy đang nối CSDL production — lúc ấy `hang_rao_csdl`
    đã chặn pytest từ `conftest`, nên đỏ ở đây là dấu hiệu hàng rào kia bị tắt bằng
    `CHO_PHEP_PRODUCTION=1`."""
    assert hang_rao_thu.bat() is True


# ── Địa chỉ thật bị bỏ ──────────────────────────────────────────────────────

def test_dia_chi_that_bi_bo_khong_mo_smtp(khong_production, thu):
    d = _gui(THAT)
    assert d['status'] == 'dropped', 'thư tới địa chỉ thật phải bị bỏ trên máy dev'
    assert thu == [], 'không được gọi tới lớp gửi thư'
    assert d['sent_at'] is None


def test_ly_do_bang_tieng_viet_va_che_dia_chi(khong_production, thu):
    loi = _gui(THAT)['error']
    assert 'hàng rào thư' in loi and 'không gửi' in loi
    assert THAT not in loi, 'lý do lỗi hiện trên màn quản trị — không chép email thật vào đó'
    assert 'ph***@gmail.com' in loi, 'vẫn phải đủ để người trực nhận ra là ai'
    assert hang_rao_thu.BIEN_DIA_CHI in loi, 'phải nói cách mở cho địa chỉ ấy'


def test_bo_HAN_khong_thu_lai(khong_production, thu):
    """`failed` là "thử lại sau" — thử bao nhiêu lần cũng vẫn là địa chỉ ấy."""
    d = _gui(THAT)
    assert d['status'] == 'dropped' and d['attempts'] == 1


# ── Địa chỉ được phép ───────────────────────────────────────────────────────

@pytest.mark.parametrize('den', ['a@example.com', 'b@example.org', 'c@example.net'])
def test_ten_mien_vi_du_van_di_qua(khong_production, thu, den):
    assert _gui(den)['status'] == 'sent'
    assert thu == [den]


def test_email_tai_khoan_e2e_di_qua(khong_production, thu, monkeypatch):
    monkeypatch.setenv(hang_rao_thu.BIEN_E2E, 'Tai.Khoan.E2E@tophsa.vn')
    assert _gui('tai.khoan.e2e@tophsa.vn')['status'] == 'sent', 'so địa chỉ không phân biệt hoa thường'
    assert _gui('nguoi.khac@tophsa.vn')['status'] == 'dropped', 'chỉ đúng địa chỉ ấy, không cả tên miền'


def test_email_tai_khoan_e2e_doc_tu_the(khong_production, thu, monkeypatch, tmp_path):
    """Thẻ `.the/e2e.json`: CHỈ đọc khoá `email`, không đọc mật khẩu."""
    p = tmp_path / 'e2e.json'
    p.write_text('{"email": "e2e@tophsa.vn", "password": "khong-doc"}', encoding='utf-8')
    monkeypatch.setattr(hang_rao_thu, 'THE_E2E', str(p))   # đường tuyệt đối: pathlib bỏ gốc repo
    assert 'e2e@tophsa.vn' in hang_rao_thu.dia_chi_cho_phep()


def test_the_e2e_hong_thi_coi_nhu_khong_co(khong_production, monkeypatch, tmp_path):
    p = tmp_path / 'e2e.json'
    p.write_text('{ khong phai JSON', encoding='utf-8')
    monkeypatch.setattr(hang_rao_thu, 'THE_E2E', str(p))
    assert hang_rao_thu.dia_chi_cho_phep(), 'không được ném — vẫn còn @example.com'
    assert hang_rao_thu.ly_do_chan('email', THAT), 'và vẫn chặn địa chỉ thật'


def test_danh_sach_bien_moi_truong_nhan_ca_dia_chi_va_ten_mien(khong_production, thu, monkeypatch):
    monkeypatch.setenv(hang_rao_thu.BIEN_DIA_CHI, ' Anh.Son@tophsa.vn , @noi-bo.test ')
    assert _gui('anh.son@tophsa.vn')['status'] == 'sent'
    assert _gui('bat-ky-ai@noi-bo.test')['status'] == 'sent', 'mục bắt đầu bằng @ là cả tên miền'
    assert _gui(THAT)['status'] == 'dropped'


# ── Zalo ────────────────────────────────────────────────────────────────────

def test_zalo_chi_di_toi_so_trong_danh_sach(khong_production, monkeypatch):
    from common import zalo
    da_gui = []
    monkeypatch.setattr(zalo, 'da_cau_hinh', lambda: True)
    monkeypatch.setattr(zalo, 'che_do_thu', lambda: False)
    monkeypatch.setattr(zalo, 'gui_zns', lambda so, ts: (da_gui.append(so), (True, 'g', None))[1])
    assert _gui('0900000001', 'zalo')['status'] == 'dropped' and da_gui == []
    monkeypatch.setenv(hang_rao_thu.BIEN_SO, '0900000001')
    assert _gui('0900000001', 'zalo')['status'] == 'sent' and da_gui == ['0900000001']


def test_ly_do_zalo_che_so_dien_thoai(khong_production):
    loi = hang_rao_thu.ly_do_chan('zalo', '0987654321')
    assert '0987654321' not in loi and hang_rao_thu.BIEN_SO in loi


# ── Hàng rào không lệ thuộc chế độ thử ──────────────────────────────────────

def test_che_do_thu_khong_mo_hang_rao(khong_production, monkeypatch):
    """`EMAIL_CHE_DO_THU=1` ghi `.eml` ra đĩa — không gửi thật, nhưng tệp ấy chứa email và
    nội dung THẬT của một em. Hàng rào vẫn chặn."""
    from common import mail
    da_ghi = []
    monkeypatch.setattr(mail, 'da_cau_hinh', lambda: False)
    monkeypatch.setattr(mail, 'che_do_thu', lambda: True)
    monkeypatch.setattr(mail, 'gui', lambda den, td, chu, html=None, dk=():
                        (da_ghi.append(den), (True, 'THU:x', None))[1])
    assert _gui(THAT)['status'] == 'dropped' and da_ghi == []


def test_thu_hang_loat_cung_bi_chan(khong_production, thu):
    from notifications.hop_thu import HANG_LOAT
    assert _gui(THAT, uu_tien=HANG_LOAT)['status'] == 'dropped'


def test_khong_dinh_gi_vao_dong_duoc_phep(khong_production, thu):
    """Dòng đi được không mang dấu vết của hàng rào (không ghi `error` lúc thành công)."""
    oid_den = 'ok@example.com'
    d = _gui(oid_den)
    assert d['status'] == 'sent' and d['error'] is None


def test_nhieu_nguoi_mot_luot_chi_nguoi_an_toan_di(khong_production, thu):
    """Thông báo cả lớp trên máy dev: em có email thật bị bỏ, em @example.com vẫn nhận."""
    from notifications.hop_thu import gui_het, xep
    ids = [xep('email', d, 'T', 'N') for d in ('em1@example.com', THAT, 'em2@example.com')]
    x('UPDATE outbox SET next_try_at = now() WHERE id = ANY(%s)', (ids,))
    gui_het()
    tt = [q1('SELECT status FROM outbox WHERE id = %s', (i,))['status'] for i in ids]
    assert tt == ['sent', 'dropped', 'sent']
    assert sorted(thu) == ['em1@example.com', 'em2@example.com']
