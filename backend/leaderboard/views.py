"""Port routes/leaderboard.py — BXH weekly | streak | friends."""
from rest_framework.response import Response
from rest_framework.views import APIView

from datetime import timedelta

from common.clock import local_today
from common.db import q, q1

MEDALS = {1: '🥇', 2: '🥈', 3: '🥉'}


def _json_list(v):
    """json_agg từ psycopg3 thường đã là list; phòng khi trả str thì parse lại."""
    if v is None:
        return []
    if isinstance(v, str):
        import json
        try:
            return json.loads(v)
        except ValueError:
            return []
    return v


def _json_obj(v):
    if v is None or isinstance(v, dict):
        return v
    if isinstance(v, str):
        import json
        try:
            return json.loads(v)
        except ValueError:
            return None
    return None

AVATAR_BY_INITIAL = {
    'A': '🧑‍💻', 'B': '👩‍🎓', 'C': '🧑‍💼', 'D': '👨‍🔬', 'E': '👩‍🔬',
    'F': '🧑‍🎨', 'G': '👨‍🎨', 'H': '👩‍🚀', 'I': '🧑‍🚀', 'J': '👨‍🚀',
    'K': '🧝', 'L': '🧙', 'M': '🧛', 'N': '🦸', 'O': '🦹',
    'P': '👨‍⚕️', 'Q': '👩‍⚕️', 'R': '🧑‍⚕️', 'S': '👨‍🌾', 'T': '👩‍🌾',
    'U': '🧑‍🌾', 'V': '👨‍🍳', 'W': '👩‍🍳', 'X': '🧑‍🍳', 'Y': '👨‍🔧',
    'Z': '👩‍🔧',
}


def _avatar_for(name: str) -> str:
    if not name:
        return '🧑'
    initial = name.strip()[0].upper()
    return AVATAR_BY_INITIAL.get(initial, '🧑')


def _looks_like_test_name(name: str) -> bool:
    """Heuristic ẩn danh tài khoản test/dev trên leaderboard (giữ nguyên bản Flask)."""
    if not name:
        return True
    n = name.strip()
    if len(n) < 3:
        return True
    low = n.lower()
    if len(set(low.replace(' ', ''))) <= 2 and len(low) > 3:
        return True
    for kw in ('test', 'dev', 'user', 'demo', 'sample', 'aaa', 'xxx'):
        if kw in low:
            return True
    if low == low and all(c.isascii() and c.islower() or c in ' _.' for c in low) and not any(
            c in 'ăâđêôơưáàảãạằẳẵặắấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ'
            for c in low):
        if ' ' not in low or len(low) < 8:
            return True
    return False


def _display_name_for(name: str, user_id: int) -> str:
    if _looks_like_test_name(name):
        return f'Học viên #{user_id}'
    return name


def _attach_medal(entries: list) -> list:
    for e in entries:
        e['medal'] = MEDALS.get(e['rank'], '')
    return entries


def _fetch_top_weekly(uid: int, limit: int = 10):
    """Top N theo XP TRONG TUẦN (từ thứ 2), từ user_daily_xp_logs.

    PERF 2026-07-19: gộp 4 query (top, tổng của tôi, tên của tôi, hạng của tôi)
    thành 1 câu CTE — mỗi round trip tới Neon ~240ms."""
    # Mốc đầu tuần tính ở PYTHON theo giờ Việt Nam, không phải bằng
    # `date_trunc('week', CURRENT_DATE)` của SQL.
    #
    # Django đặt TimeZone của kết nối là UTC (đã đo), nên `CURRENT_DATE` là ngày
    # UTC. Trong khi `user_daily_xp_logs.log_date` được GHI bằng `local_today()`
    # tức ngày Việt Nam (stats/streak.py). Hai đồng hồ cho cùng một khái niệm
    # "tuần này" — đúng thứ RULES §7 cấm.
    # Hậu quả cụ thể: mỗi thứ Hai từ 0h đến 7h sáng giờ VN, `CURRENT_DATE` vẫn
    # là Chủ nhật nên `date_trunc('week')` trả về thứ Hai TUẦN TRƯỚC — bảng xếp
    # hạng tuần hiện dữ liệu tuần cũ suốt bảy tiếng, đúng lúc học viên vào xem
    # tuần mới bắt đầu thế nào.
    hom_nay = local_today()
    dau_tuan = hom_nay - timedelta(days=hom_nay.weekday())  # weekday(): thứ Hai = 0
    row = q1('''WITH weekly AS (
                    SELECT user_id, SUM(xp_earned) AS wxp
                    FROM user_daily_xp_logs
                    WHERE log_date >= %s
                    GROUP BY user_id
                ),
                top AS (
                    SELECT u.id, u.name, w.wxp
                    FROM weekly w JOIN users u ON u.id = w.user_id
                    ORDER BY w.wxp DESC, u.name ASC
                    LIMIT %s
                ),
                me AS (
                    SELECT COALESCE((SELECT wxp FROM weekly WHERE user_id = %s), 0) AS wxp
                )
                SELECT
                    (SELECT COALESCE(json_agg(json_build_object('id', id, 'name', name, 'wxp', wxp)
                                              ORDER BY wxp DESC, name ASC), '[]'::json)
                     FROM top) AS top_rows,
                    (SELECT wxp FROM me) AS me_wxp,
                    (SELECT COUNT(*) + 1 FROM weekly, me WHERE weekly.wxp > me.wxp) AS me_rank,
                    (SELECT name FROM users WHERE id = %s) AS me_name,
                    EXISTS(SELECT 1 FROM users WHERE id = %s) AS me_exists''',
             (dau_tuan, limit, uid, uid, uid))
    top_rows = _json_list(row['top_rows'])
    me_row = {'wxp': row['me_wxp']}
    me_name_row = {'id': uid, 'name': row['me_name']} if row['me_exists'] else None
    rank_row = {'r': row['me_rank']}

    top_list = [
        {
            'rank': idx + 1,
            'id': r['id'],
            'name': r['name'] or f'User #{r["id"]}',
            'avatar': _avatar_for(r['name'] or ''),
            'value': r['wxp'] or 0,
        }
        for idx, r in enumerate(top_rows)
    ]
    _attach_medal(top_list)

    me = None
    if me_name_row:
        me = {
            'rank': rank_row['r'] if me_row['wxp'] else (len(top_list) + 1),
            'id': me_name_row['id'],
            'name': me_name_row['name'] or f'User #{me_name_row["id"]}',
            'avatar': _avatar_for(me_name_row['name'] or ''),
            'value': me_row['wxp'] or 0,
        }
    return top_list, me


def _fetch_top_by(uid: int, order_col: str, limit: int = 10):
    if order_col not in ('xp', 'streak'):
        return None, None  # tránh SQL injection

    # PERF 2026-07-19: top N + hàng của tôi trong 1 câu lệnh (2 query → 1)
    row = q1(f'''WITH top AS (
                     SELECT id, name, xp, streak FROM users
                     ORDER BY {order_col} DESC, name ASC LIMIT %s
                 )
                 SELECT
                     (SELECT COALESCE(json_agg(json_build_object(
                                 'id', id, 'name', name, 'xp', xp, 'streak', streak)
                                 ORDER BY {order_col} DESC, name ASC), '[]'::json)
                      FROM top) AS top_rows,
                     (SELECT row_to_json(m) FROM (
                          SELECT id, name, xp, streak,
                                 (SELECT COUNT(*) + 1 FROM users u2
                                  WHERE u2.{order_col} > u.{order_col}) AS my_rank
                          FROM users u WHERE id = %s) m) AS me_row''',
              (limit, uid))
    top_rows = _json_list(row['top_rows'])
    me_row = _json_obj(row['me_row'])

    top_list = [
        {
            'rank': idx + 1,
            'id': r['id'],
            'name': _display_name_for(r['name'] or '', r['id']),
            'avatar': _avatar_for(r['name'] or ''),
            'value': r[order_col] or 0,
        }
        for idx, r in enumerate(top_rows)
    ]
    _attach_medal(top_list)

    me = None
    if me_row:
        me = {
            'rank': me_row['my_rank'] or (len(top_list) + 1),
            'id': me_row['id'],
            'name': _display_name_for(me_row['name'] or '', me_row['id']),
            'avatar': _avatar_for(me_row['name'] or ''),
            'value': me_row[order_col] or 0,
        }
    return top_list, me


def _build_friends(uid: int, user_name: str, user_xp: int):
    rows = q('''SELECT u.id, u.name, u.xp, u.streak
                FROM user_follows f
                JOIN users u ON u.id = f.followee_id
                WHERE f.follower_id = %s''', (uid,))
    friends = [
        {
            'id': r['id'],
            'name': r['name'] or f'User #{r["id"]}',
            'avatar': _avatar_for(r['name'] or ''),
            'xp': r['xp'] or 0,
            'streak': r['streak'] or 0,
        }
        for r in rows
    ]
    merged = friends + [{
        'id': uid,
        'name': user_name or 'Bạn',
        'avatar': _avatar_for(user_name or ''),
        'xp': user_xp,
        'streak': 0,
    }]
    merged.sort(key=lambda f: -f['xp'])

    me_rank = next((i + 1 for i, f in enumerate(merged) if f['id'] == uid), len(merged) + 1)

    top = merged[:10]
    entries = [
        {
            'rank': i + 1,
            'id': f['id'],
            'name': f['name'],
            'avatar': f['avatar'],
            'value': f['xp'],
        }
        for i, f in enumerate(top)
    ]
    _attach_medal(entries)

    me_block = {
        'rank': me_rank,
        'id': uid,
        'name': user_name or 'Bạn',
        'avatar': _avatar_for(user_name or ''),
        'value': user_xp,
    }
    for e in entries:
        if e['id'] == uid:
            e['isMe'] = True
            break
    return entries, me_block


class LeaderboardView(APIView):
    def get(self, request):
        lb_type = (request.query_params.get('type') or 'weekly').lower()
        uid = request.user.id

        if lb_type == 'weekly':
            entries, me = _fetch_top_weekly(uid)
            unit, label = 'XP', 'Tuần này'
        elif lb_type == 'streak':
            entries, me = _fetch_top_by(uid, 'streak')
            unit, label = 'ngày', 'Chuỗi dài nhất'
        elif lb_type == 'friends':
            # PERF 2026-07-19: chỉ nhánh friends mới cần tên/XP của tôi — dời
            # query users vào đây (weekly/streak tự lo trong 1 câu CTE của chúng)
            me_row = q1('SELECT id, name, xp, streak FROM users WHERE id=%s', (uid,))
            me_name = (me_row['name'] if me_row else '') or 'Bạn'
            me_xp = (me_row['xp'] if me_row else 0) or 0
            entries, me = _build_friends(uid, me_name, me_xp)
            unit, label = 'XP', 'Bạn bè'
        else:
            return Response({'error': f'type không hợp lệ: {lb_type}'}, status=400)

        return Response({
            'type': lb_type,
            'unit': unit,
            'label': label,
            'entries': entries,
            'me': me,
        })
