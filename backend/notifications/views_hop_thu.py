"""`POST /api/noi-bo/tick` — nhịp hộp thư đi cho MÁY GỌI NGOÀI (cron-job.org).

Render gói rẻ ngủ khi vắng khách, luồng nền trong tiến trình ngủ theo — thư quên mật
khẩu, nhắc hạn nộp phải chờ tới lúc có người vào. Một máy ngoài gọi cửa này mỗi vài phút
vừa đánh thức máy chủ vừa chạy một nhịp.

  · Khoá bí mật trong header `X-Tick-Key`, so với biến môi trường `OUTBOX_TICK_SECRET`
    (so hằng thời gian). Biến trống → cửa TẮT (404), không mở cho ai.
  · `authentication_classes = []`: máy gọi không có tài khoản; thẻ rác trong header
    Authorization không được làm 401 trước khi kịp xét khoá.
  · Giới hạn tốc độ theo IP: nhịp chồng nhau vô ích, và khoá lộ không thành cách đốt CSDL.
"""
import hmac
import os

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from common.net import client_ip
from notifications.hop_thu import nhip


class TickThrottle(SimpleRateThrottle):
    scope = 'outbox_tick'
    rate = '30/min'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': client_ip(request)}


class TickView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [TickThrottle]

    def post(self, request):
        khoa = (os.environ.get('OUTBOX_TICK_SECRET') or '').strip()
        if not khoa:
            return Response({'error': 'Không tìm thấy.'}, status=404)
        gui_len = (request.headers.get('X-Tick-Key') or '').strip()
        if not hmac.compare_digest(gui_len.encode(), khoa.encode()):
            return Response({'error': 'Khoá không đúng.'}, status=403)
        return Response(nhip())
