from django.apps import AppConfig


class YeuCauConfig(AppConfig):
    """Miền HỘP YÊU CẦU (E3, 25/09/2026) — `docs/THIET_KE_HE_THONG.md` §4, luật S4.

    Sở hữu bảng §65 (`yeu_cau`, `yeu_cau_su_kien`). Miền khác chỉ gọi hàm ở `dich_vu.py`;
    khi duyệt, miền này gọi hàm sẵn có của miền lớp học (`thuc_thi.py`), không ghi thẳng
    bảng của họ. Không có model Django — bảng do `legacy_schema.sql` dựng.
    """
    name = 'yeu_cau'
