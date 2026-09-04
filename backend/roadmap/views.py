"""Port routes/roadmap.py."""
import json

from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.views import _pick_roadmap_template
from common.clock import local_now
from common.db import q, q1, x

_TEMPLATE_ORDER = """
    ORDER BY CASE id
        WHEN 'frontend' THEN 0
        WHEN 'backend'  THEN 1
        WHEN 'python'   THEN 2
        WHEN 'cpp'      THEN 3
        ELSE 4
    END"""


def _jsonb(v, default):
    """psycopg3 có thể trả JSONB là str — chuẩn hóa về dict/list như psycopg2 wrapper cũ."""
    if v is None:
        return default
    if isinstance(v, str):
        try:
            return json.loads(v)
        except ValueError:
            return default
    return v


class RoadmapsView(APIView):
    def get(self, request):
        """Lộ trình THỰC TẾ cho user theo khảo sát gần nhất; chưa khảo sát → tất cả template."""
        uid = request.user.id
        # PERF 2026-07-19: survey mới nhất lấy kèm trong CÙNG câu lệnh (2 query
        # → 1 round trip); template chỉ vài dòng nên lọc theo survey ở Python.
        rows = q("""SELECT id, title, icon, color, mermaid_def,
                           COALESCE(nodes_json, '{}'::jsonb) AS nodes_json,
                           COALESCE(edges_json, '[]'::jsonb) AS edges_json,
                           (SELECT data_json FROM surveys
                            WHERE user_id=%s ORDER BY id DESC LIMIT 1) AS _survey
                    FROM roadmaps WHERE user_id IS NULL""" + _TEMPLATE_ORDER,
                 (uid,))

        matched_id = None
        if rows and rows[0]['_survey']:
            data = _jsonb(rows[0]['_survey'], {})
            if isinstance(data, dict):
                matched_id = _pick_roadmap_template(data)
        if matched_id:
            rows = [r for r in rows if r['id'] == matched_id]

        result = []
        for item in rows:
            item.pop('_survey', None)
            item['nodes'] = _jsonb(item.pop('nodes_json'), {}) or {}
            item['edges'] = _jsonb(item.pop('edges_json'), []) or []
            result.append(item)
        return Response(result)


class RoadmapProgressView(APIView):
    """GET /api/roadmap — những mục học viên đã đánh dấu xong.

    ── VÌ SAO TRẢ THÊM `done` (vá 04/09/2026) ─────────────────────────────

    `doneItems` là danh sách `item_id` TRẦN, không kèm lộ trình. Mà `item_id` do
    `roadmap.js::normalize` sinh theo VỊ TRÍ — `0-m`, `1-l0`, `2-r1` — nên `0-m`
    tồn tại trong CẢ 26 lộ trình tĩnh.

    Hệ quả ở client: đánh dấu xong chặng đầu của "Tư duy Định lượng" thì chặng
    đầu của cả 25 lộ trình còn lại cũng hiện ✓. Chính chú thích trong
    `roadmap.js` tự thú điều đó ("đánh dấu mọi khoá đang có đuôi khớp") — nó mô
    tả đúng việc đang làm, chỉ không nói rằng việc ấy sai.

    Bảng `roadmap_progress` LUÔN lưu `roadmap_id` (client gửi trong thân `PUT`),
    và view này đã có sẵn bộ lọc `?roadmap_id=`. Thứ thiếu chỉ là trả CẶP về để
    client khỏi phải đoán: một lượt gọi, khớp chính xác.

    Giữ `doneItems` để không phá bản client đang chạy — một trang đã mở sẵn
    trong trình duyệt học viên vẫn đọc khoá cũ cho tới khi họ tải lại.
    """

    def get(self, request):
        uid = request.user.id
        roadmap_id = request.query_params.get('roadmap_id')
        if roadmap_id:
            rows = q('SELECT roadmap_id, item_id FROM roadmap_progress '
                     'WHERE user_id=%s AND roadmap_id=%s AND done=TRUE', (uid, roadmap_id))
        else:
            rows = q('SELECT roadmap_id, item_id FROM roadmap_progress '
                     'WHERE user_id=%s AND done=TRUE', (uid,))
        return Response({
            'doneItems': [r['item_id'] for r in rows],
            'done': [{'roadmapId': r['roadmap_id'], 'itemId': r['item_id']} for r in rows],
        })


class MyRoadmapView(APIView):
    def get(self, request):
        row = q1("SELECT mermaid_def, title, icon, color, "
                 "COALESCE(nodes_json, '{}'::jsonb) AS nodes_json, "
                 "COALESCE(edges_json, '[]'::jsonb) AS edges_json "
                 "FROM roadmaps "
                 "WHERE user_id=%s AND source IN ('generated','custom') "
                 "ORDER BY updated_at DESC LIMIT 1", (request.user.id,))
        if not row:
            return Response({'mermaid_def': '', 'nodes': {}, 'edges': []})
        return Response({
            'mermaid_def': row['mermaid_def'] or '',
            'title': row['title'],
            'icon': row['icon'],
            'color': row['color'],
            'nodes': _jsonb(row['nodes_json'], {}) or {},
            'edges': _jsonb(row['edges_json'], []) or [],
        })

    def post(self, request):
        uid = request.user.id
        body = request.data if isinstance(request.data, dict) else {}
        mdef = body.get('mermaid_def', '')
        rid = f'u{uid}_custom'
        # `local_now()` chứ không `now()` của SQL — xem chú thích ở
        # `common/clock.py`. Kết nối Neon chạy UTC, lệch 7 tiếng.
        gio = local_now()
        x('''INSERT INTO roadmaps (id, user_id, source, mermaid_def, updated_at)
             VALUES (%s, %s, 'custom', %s, %s)
             ON CONFLICT (id) DO UPDATE
                 SET mermaid_def = EXCLUDED.mermaid_def, updated_at = EXCLUDED.updated_at''',
          (rid, uid, mdef, gio))
        return Response({'ok': True})


class AiRoadmapView(APIView):
    def post(self, request):
        return Response({'error': 'Premium',
                         'message': 'Tính năng này chỉ dành cho tài khoản Premium'}, status=402)


class UpdateRoadmapItemView(APIView):
    def put(self, request, item_id):
        uid = request.user.id
        body = request.data if isinstance(request.data, dict) else {}
        done = bool(body.get('done', False))
        roadmap_id = body.get('roadmap_id')
        if not roadmap_id:
            return Response({'error': 'roadmap_id là bắt buộc'}, status=400)
        x('''INSERT INTO roadmap_progress (user_id, roadmap_id, item_id, done, completed_at)
             VALUES (%s,%s,%s,%s, CASE WHEN %s THEN %s END)
             ON CONFLICT (user_id, roadmap_id, item_id) DO UPDATE
                 SET done=EXCLUDED.done, completed_at=EXCLUDED.completed_at''',
          (uid, roadmap_id, item_id, done, done, local_now()))
        return Response({'ok': True})
