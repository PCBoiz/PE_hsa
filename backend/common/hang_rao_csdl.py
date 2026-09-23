"""HÀNG RÀO CSDL PRODUCTION cho máy dev và pytest (H1, 24/09/2026).

Tới 24/09 máy dev và production dùng CHUNG một Neon: mọi lượt pytest, mọi cú bấm
thử trên localhost đều ghi vào dữ liệu thật. Anh Sơn đã chuyển máy dev sang
nhánh Neon `dev`. Tệp này canh để khỏi lỡ quay về: `.env` bị chép đè, chuỗi
kết nối dán nhầm, một máy mới lấy chuỗi production từ Render sang.

Cách nhận ra "đang trỏ production": so ĐIỂM CUỐI Neon (nhãn đầu của host, bỏ
đuôi `-pooler`) của CSDL Django đang dùng với biến `PE_DB_HOST_PRODUCTION` —
biến CHỈ đặt trên máy dev (`backend/.env`, không commit). Render không đặt biến
ấy nên production không bao giờ tự chặn mình.

Chưa đặt biến → không biết production là gì → KHÔNG chặn (chỉ nhắc một lần):
chặn khi không biết sẽ làm hỏng CI và máy mới. `CHO_PHEP_PRODUCTION=1` là lối
thoát có chủ ý (đo trên production, sao lưu).

Không bao giờ in chuỗi kết nối — chỉ in điểm cuối (không chứa mật khẩu).
"""
import os
from urllib.parse import urlparse

BIEN_PRODUCTION = 'PE_DB_HOST_PRODUCTION'
BIEN_CHO_PHEP = 'CHO_PHEP_PRODUCTION'


def diem_cuoi(host):
    """'ep-abc-123-pooler.c-4.us-east-2.aws.neon.tech' → 'ep-abc-123'.

    Nhận cả chuỗi kết nối đầy đủ (người dán nhầm cả chuỗi vào biến host)."""
    host = (host or '').strip()
    if '://' in host:
        host = urlparse(host).hostname or ''
    nhan = host.lower().split('.')[0]
    return nhan[:-len('-pooler')] if nhan.endswith('-pooler') else nhan


def host_dang_dung():
    """Host CSDL Django THẬT SỰ dùng — đọc từ settings, không đọc lại `.env`."""
    from django.conf import settings
    return (settings.DATABASES.get('default') or {}).get('HOST') or ''


def dang_tro_production(host=None, host_production=None):
    host = host_dang_dung() if host is None else host
    prod = os.environ.get(BIEN_PRODUCTION, '') if host_production is None else host_production
    if not diem_cuoi(prod) or not diem_cuoi(host):
        return False
    return diem_cuoi(host) == diem_cuoi(prod)


def loi_neu_production(viec):
    """Câu lỗi nếu `viec` sắp chạy trên production mà chưa cho phép; None nếu an toàn."""
    if os.environ.get(BIEN_CHO_PHEP) == '1' or not dang_tro_production():
        return None
    return ('%s đang trỏ vào CSDL PRODUCTION (điểm cuối %s = %s). Đổi DATABASE_URL trong '
            'backend/.env sang nhánh Neon dev; cố ý chạy trên production thì đặt %s=1.'
            % (viec, diem_cuoi(host_dang_dung()), BIEN_PRODUCTION, BIEN_CHO_PHEP))
