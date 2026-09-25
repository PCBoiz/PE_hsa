import os
import sys

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        # Luồng gửi hộp thư đi (§61, E2) — cùng điều kiện "đang phục vụ request" với luồng
        # giữ ấm của `common/apps.py`, cộng cờ `ENABLE_OUTBOX=1` (kiểm trong hàm bật).
        argv = sys.argv
        prog = os.path.basename(argv[0]) if argv else ''
        if 'runserver' in argv:
            if os.environ.get('RUN_MAIN') != 'true' and '--noreload' not in argv:
                return
        elif not (os.environ.get('ENABLE_KEEPALIVE') == '1'
                  or prog.startswith(('gunicorn', 'uwsgi', 'uvicorn'))):
            return
        from notifications.hop_thu import bat_luong_nen_neu_duoc

        bat_luong_nen_neu_duoc()
