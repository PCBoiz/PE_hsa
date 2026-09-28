"""Port routes/notifications.py — settings (notification_settings) + feed (notifications).

Bổ sung: /api/notifications/badge cho client poll badge chuông (thay SSE).
"""
from rest_framework.response import Response

from common.db import q, q1, x
from common.views import NguoiDungView
from notifications import loai as sol
from notifications.service import unread_state


class NotificationSettingsView(NguoiDungView):
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


#: Khoá mới của mỗi dòng chuông (E2) — cộng thêm, tuyến cũ vẫn đủ khoá cũ.
_COT = '''id, type, title, body, ref_type, ref_id, is_read, created_at,
          COALESCE(coalesce_count, 1) AS coalesce_count, link, announcement_id, read_at'''


def _so(v, mac_dinh, thap, cao):
    try:
        return max(thap, min(cao, int(v)))
    except (TypeError, ValueError):
        return mac_dinh


def _hinh(r):
    r['link'] = r.get('link') or None
    r['announcementId'] = r.pop('announcement_id', None)
    r['readAt'] = r.pop('read_at', None)
    # Nhãn đi KÈM từng dòng chứ không để màn hình tra: `type` là mã kỹ thuật, và ba chỗ
    # hiện nó (panel chuông, ô lọc trang Thông báo, danh sách) phải nói cùng một câu.
    r['loaiNhan'] = sol.nhan(r.get('type'))
    return r


class FeedView(NguoiDungView):
    """GET /api/notifications/feed

    Không tham số: như cũ — 30 dòng mới nhất theo `created_at` (thông báo gộp nhảy lên đầu).

    Có `truoc` / `loai` / `chuaDoc` / `limit` (trang "Thông báo", E2): PHÂN TRANG THEO KHOÁ
    `id` giảm dần — `truoc=<id>` lấy các dòng có id nhỏ hơn. Không trùng, không sót kể cả
    khi có thông báo mới chen vào giữa hai lần "tải thêm" (phân trang theo số trang thì
    lệch ngay). Trả thêm `tiep` (giá trị `truoc` cho trang kế, null = hết) và `cacLoai`
    (các loại người này có, để dựng bộ lọc).
    """

    def get(self, request):
        # PERF 2026-07-19: unread đếm bằng subquery cùng câu lệnh — 1 round trip
        uid = request.user.id
        p = request.query_params
        if not ({'truoc', 'loai', 'chuaDoc', 'limit'} & set(p)):
            rows = q('''SELECT ''' + _COT + ''',
                               (SELECT COUNT(*) FROM notifications
                                WHERE user_id=%s AND is_read=FALSE) AS _unread
                        FROM notifications WHERE user_id=%s
                        ORDER BY created_at DESC LIMIT 30''', (uid, uid))
            unread = rows[0].pop('_unread') if rows else 0
            for r in rows:
                r.pop('_unread', None)
            return Response({'items': [_hinh(r) for r in rows], 'unread': unread})

        n = _so(p.get('limit'), 30, 1, 100)
        truoc = _so(p.get('truoc'), None, 1, 2 ** 31 - 1)
        loai = (p.get('loai') or '').strip()[:50] or None
        chua_doc = p.get('chuaDoc') in ('1', 'true')
        rows = q('''SELECT ''' + _COT + ''' FROM notifications
                    WHERE user_id = %s AND (%s::int IS NULL OR id < %s)
                      AND (%s::text IS NULL OR type = %s) AND (NOT %s OR is_read = FALSE)
                    ORDER BY id DESC LIMIT %s''', (uid, truoc, truoc, loai, loai, chua_doc, n + 1))
        tiep = rows[n - 1]['id'] if len(rows) > n else None
        cac_loai = q('''SELECT type AS loai, COUNT(*) AS so, COUNT(*) FILTER (WHERE NOT is_read) AS chua_doc
                         FROM notifications WHERE user_id = %s AND type IS NOT NULL
                        GROUP BY type ORDER BY type''', (uid,)) if not truoc else None
        unread, _ = unread_state(uid)
        ra = {'items': [_hinh(r) for r in rows[:n]], 'unread': unread, 'tiep': tiep}
        if cac_loai is not None:
            ra['cacLoai'] = [{'loai': r['loai'], 'nhan': sol.nhan(r['loai']),
                              'so': r['so'], 'chuaDoc': r['chua_doc']} for r in cac_loai]
        return Response(ra)


class BadgeView(NguoiDungView):
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


class FeedReadView(NguoiDungView):
    def post(self, request, notif_id):
        x('''UPDATE notifications SET is_read=TRUE, read_at=coalesce(read_at, now())
             WHERE id=%s AND user_id=%s''', (notif_id, request.user.id))
        return Response({'ok': True})


class FeedUnreadView(NguoiDungView):
    """POST /api/notifications/feed/<id>/unread — đánh dấu CHƯA đọc (E2, bảng TopHSA dòng 27)."""

    def post(self, request, notif_id):
        if not q1('''UPDATE notifications SET is_read=FALSE, read_at=NULL
                     WHERE id=%s AND user_id=%s RETURNING id''', (notif_id, request.user.id)):
            return Response({'error': 'Không tìm thấy thông báo này.'}, status=404)
        unread, latest = unread_state(request.user.id)
        return Response({'ok': True, 'unread': unread, 'latest': latest})


class FeedReadAllView(NguoiDungView):
    def post(self, request):
        x('''UPDATE notifications SET is_read=TRUE, read_at=now()
             WHERE user_id=%s AND is_read=FALSE''', (request.user.id,))
        return Response({'ok': True})
