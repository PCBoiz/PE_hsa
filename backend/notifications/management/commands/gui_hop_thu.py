"""`manage.py gui_hop_thu` — chạy MỘT nhịp hộp thư đi (nhắc hạn nộp + gửi việc tới lượt).

Dùng cho cron của máy chủ, hoặc tay khi cần đẩy thư ngay. Chạy nhiều bản cùng lúc an
toàn (nhận việc bằng `FOR UPDATE SKIP LOCKED`, xem `notifications/hop_thu.py`).
"""
from django.core.management.base import BaseCommand

from notifications.hop_thu import nhip


class Command(BaseCommand):
    help = 'Chạy một nhịp hộp thư đi: quét nhắc hạn nộp rồi gửi mọi thư tới lượt.'

    def handle(self, *args, **opt):
        dem = nhip()
        self.stdout.write('nhắc hạn mới: %(nhacHan)d · đã gửi: %(sent)d · chờ thử lại: %(failed)d · bỏ: %(dropped)d'
                          % dem)
