from django.apps import AppConfig


class ChuongTrinhConfig(AppConfig):
    """Miền KHUNG CHƯƠNG TRÌNH + SỔ ĐẦU BÀI (E1, 25/09/2026) — `docs/THIET_KE_HE_THONG.md` §4.

    Thư mục riêng từ ngày đầu (luật S4): sở hữu bảng §63–§64, miền khác chỉ gọi ba
    hàm ở `dich_vu.py`. Không có model Django — mọi bảng đều do `legacy_schema.sql`
    dựng, đọc ghi bằng `common.db`.
    """
    name = 'chuong_trinh'
