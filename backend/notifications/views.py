"""Port routes/notifications.py — settings (notification_settings) + feed (notifications).

Bổ sung: SSE stream đẩy badge real-time (notifications/service.py gộp comment).
"""
import json
import time

from django.http import JsonResponse, StreamingHttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from common.db import q, q1, x
from notifications.service import unread_state


class NotificationSettingsView(APIView):
    def get(self, request):
        row = q1('SELECT * FROM notification_settings WHERE user_id=%s', (request.user.id,))
        if not row:
            return Response({'emailNotif': True, 'pushNotif': False,
                             'studyRemind': True, 'contentUpdate': False})
        return Response({
            'emailNotif': bool(row['email_notif']),
            'pushNotif': bool(row['push_notif']),
            'studyRemind': bool(row['study_remind']),
            'contentUpdate': bool(row['content_update']),
        })

    def put(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        x('''INSERT INTO notification_settings
                 (user_id, email_notif, push_notif, study_remind, content_update)
             VALUES (%s,%s,%s,%s,%s)
             ON CONFLICT(user_id) DO UPDATE SET
               email_notif=excluded.email_notif,
               push_notif=excluded.push_notif,
               study_remind=excluded.study_remind,
               content_update=excluded.content_update''',
          (request.user.id,
           int(data.get('emailNotif', True)),
           int(data.get('pushNotif', False)),
           int(data.get('studyRemind', True)),
           int(data.get('contentUpdate', False))))
        return Response({'ok': True})


class FeedView(APIView):
    def get(self, request):
        uid = request.user.id
        rows = q('''SELECT id, type, title, body, ref_type, ref_id, is_read, created_at,
                           COALESCE(coalesce_count, 1) AS coalesce_count
                    FROM notifications WHERE user_id=%s
                    ORDER BY created_at DESC LIMIT 30''', (uid,))
        unread = q1('SELECT COUNT(*) AS n FROM notifications '
                    'WHERE user_id=%s AND is_read=FALSE', (uid,))['n']
        return Response({'items': rows, 'unread': unread})


def feed_stream(request):
    """GET /api/notifications/stream?token=<access JWT> — Server-Sent Events.

    EventSource không set được header Authorization nên nhận access token qua
    query param (chỉ chứa trong URL nội bộ client↔backend, không log referer).
    Mỗi 3s poll (unread_count, latest_id); chỉ đẩy event khi trạng thái đổi.
    Kết nối tự đóng sau ~1h — EventSource phía client tự reconnect (retry).
    Dev: runserver stream tốt (1 thread/kết nối). Prod: chạy gunicorn với
    worker gthread/gevent để không cạn worker vì kết nối treo.
    """
    try:
        token = AccessToken(request.GET.get('token', ''))
        uid = token['user_id']
    except Exception:
        return JsonResponse({'error': 'Token không hợp lệ hoặc đã hết hạn'}, status=401)

    def gen():
        yield 'retry: 5000\n\n'
        last = None
        quiet = 0
        for _ in range(1200):  # 1200 vòng × 3s ≈ 1 giờ rồi để client reconnect
            try:
                state = unread_state(uid)
            except Exception:
                break  # DB lỗi → đóng stream, client tự nối lại
            if state != last:
                last = state
                quiet = 0
                yield 'data: ' + json.dumps(
                    {'unread': state[0], 'latest': state[1]}) + '\n\n'
            else:
                quiet += 1
                if quiet >= 8:  # heartbeat ~24s giữ kết nối qua proxy/LB
                    quiet = 0
                    yield ': ping\n\n'
            time.sleep(3)

    resp = StreamingHttpResponse(gen(), content_type='text/event-stream')
    resp['Cache-Control'] = 'no-cache'
    resp['X-Accel-Buffering'] = 'no'  # tắt buffering khi đứng sau nginx
    return resp


class FeedReadView(APIView):
    def post(self, request, notif_id):
        x('UPDATE notifications SET is_read=TRUE WHERE id=%s AND user_id=%s',
          (notif_id, request.user.id))
        return Response({'ok': True})


class FeedReadAllView(APIView):
    def post(self, request):
        x('UPDATE notifications SET is_read=TRUE WHERE user_id=%s AND is_read=FALSE',
          (request.user.id,))
        return Response({'ok': True})
