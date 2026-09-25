from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chatbot"

    def ready(self):
        # Nghe "nhật ký đổi" của `stats` để bỏ đệm hồ sơ học (`profile.py`) — chiều phụ thuộc
        # đúng là chatbot → stats; stats không biết chatbot (25/09/2026, phá vòng S5).
        from chatbot import profile
        from stats.tin_hieu import nhat_ky_doi

        def _bo_dem(sender, user_id, **kwargs):
            profile.invalidate(user_id)

        nhat_ky_doi.connect(_bo_dem, weak=False, dispatch_uid='chatbot.profile.bo_dem_nhat_ky')
