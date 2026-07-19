"""Port routes/notifications.py — settings (notification_settings) + feed (notifications).

Bổ sung: /api/notifications/badge cho client poll badge chuông (thay SSE).
"""
from rest_framework.response import Response
from rest_framework.views import APIView

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
        # PERF 2026-07-19: unread đếm bằng subquery cùng câu lệnh — 1 round trip
        uid = request.user.id
        rows = q('''SELECT id, type, title, body, ref_type, ref_id, is_read, created_at,
                           COALESCE(coalesce_count, 1) AS coalesce_count,
                           (SELECT COUNT(*) FROM notifications
                            WHERE user_id=%s AND is_read=FALSE) AS _unread
                    FROM notifications WHERE user_id=%s
                    ORDER BY created_at DESC LIMIT 30''', (uid, uid))
        unread = rows[0].pop('_unread') if rows else 0
        for r in rows:
            r.pop('_unread', None)
        return Response({'items': rows, 'unread': unread})


class BadgeView(APIView):
    """GET /api/notifications/badge → {unread, latest} — client poll ~45s.

    PERF 2026-07-19: thay SSE /api/notifications/stream. SSE giữ 1 thread/user
    suốt ~1h + poll DB 3s/kết nối → nhiều user online là cạn worker (gunicorn
    sync) và tự ăn ~30% công suất pool DB. Poll 45s phía client: cùng UX badge
    (trễ tối đa 45s thay vì 3s — chấp nhận được cho chuông thông báo), server
    không giữ kết nối treo, không cần gthread/gevent khi deploy.

    throttle_classes rỗng: poll nền chạy tự động (80 lần/giờ/tab) — không được
    đốt quota per-endpoint per-IP của user thật, nhất là nhiều người sau 1 NAT.
    Vẫn bắt buộc JWT (permission mặc định) nên không mở cửa cho DoS ẩn danh.
    """
    throttle_classes = []

    def get(self, request):
        unread, latest = unread_state(request.user.id)
        return Response({'unread': unread, 'latest': latest})


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
