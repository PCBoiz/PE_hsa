from django.apps import AppConfig


class LichConfig(AppConfig):
    """Miền LỊCH — phần đưa lịch RA NGOÀI (địa chỉ lịch .ics, §71, 26/09/2026).

    Thư mục riêng theo luật S4 (`docs/THIET_KE_HE_THONG.md` §4): sở hữu bảng
    `calendar_links`. Phần lịch bên trong sản phẩm vẫn ở `teaching/lich.py`,
    `teaching/sessions.py` — mục này chỉ ĐỌC buổi học qua câu SQL của chính nó và
    không ghi bảng của miền khác.
    """
    name = 'lich'
