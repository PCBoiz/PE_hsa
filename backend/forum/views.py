"""Port routes/forum.py — bài viết, bình luận (lồng 1 cấp), 6 loại reaction, @mention."""
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from common.db import q, q1, x
from common.params import so_nguyen
from common.permissions import is_admin
from notifications.service import notify

_CATEGORIES = ('question', 'share', 'discuss')
_REACTIONS = ('like', 'love', 'haha', 'wow', 'sad', 'angry')

# Bảng/cột trong các helper dưới đây LUÔN là hằng nội bộ (không phải input user)
# — f-string SQL an toàn, giữ nguyên cấu trúc bản Flask.


def _is_name_mentioned(content, name):
    """@mention khớp theo RANH GIỚI: '@name' phải đứng cuối chuỗi hoặc theo sau bởi
    ký tự không phải chữ/số/gạch dưới. Tránh bug substring: user 'An' bị coi là được
    nhắc trong '@Anh'. Ký tự có dấu tiếng Việt tính là chữ (str.isalnum()=True)."""
    if not name or not content:
        return False
    needle = '@' + name
    start = 0
    while True:
        i = content.find(needle, start)
        if i == -1:
            return False
        after = i + len(needle)
        nxt = content[after] if after < len(content) else ''
        if not (nxt.isalnum() or nxt == '_'):
            return True
        start = i + 1


def _notify_mentions(post_id, actor_id, content, parent_id):
    """Tạo thông báo cho user được @nhắc trong bình luận (reply + @tên)."""
    actor = q1('SELECT name FROM users WHERE id=%s', (actor_id,))
    actor_name = (actor['name'] if actor else '') or 'Ai đó'

    targets = {}

    if parent_id:
        prow = q1('SELECT user_id FROM comments WHERE id=%s', (parent_id,))
        if prow and prow['user_id'] and prow['user_id'] != actor_id:
            targets[prow['user_id']] = 'comment_reply'

    if '@' in (content or ''):
        parts = q('''SELECT DISTINCT u.id, u.name FROM users u
                     WHERE u.id IN (
                         SELECT user_id FROM comments WHERE post_id=%s AND user_id IS NOT NULL
                         UNION
                         SELECT user_id FROM posts WHERE id=%s AND user_id IS NOT NULL
                     )''', (post_id, post_id))
        for p in parts:
            if p['id'] == actor_id or not p['name']:
                continue
            if _is_name_mentioned(content, p['name']):
                targets.setdefault(p['id'], 'mention')

    snippet = (content or '').strip()
    if len(snippet) > 120:
        snippet = snippet[:117] + '...'
    for uid, ntype in targets.items():
        if ntype == 'comment_reply':
            title = f'{actor_name} đã trả lời bình luận của bạn'
            title_multi = '{n} trả lời mới cho bình luận của bạn'
        else:
            title = f'{actor_name} đã nhắc đến bạn trong một bình luận'
            title_multi = 'Bạn được nhắc đến trong {n} bình luận'
        # Gộp các thông báo cùng loại trong COALESCE_MINUTES (notifications/service.py)
        notify(uid, ntype, title, snippet, 'post', post_id, title_multi=title_multi)

    # Chủ bài viết nhận thông báo "bình luận mới" (trừ khi tự comment bài mình
    # hoặc đã nhận thông báo reply/mention ở trên — tránh 2 thông báo cho 1 comment)
    post_row = q1('SELECT user_id FROM posts WHERE id=%s', (post_id,))
    owner_id = post_row and post_row['user_id']
    if owner_id and owner_id != actor_id and owner_id not in targets:
        notify(owner_id, 'post_comment',
               f'{actor_name} đã bình luận về bài viết của bạn', snippet,
               'post', post_id,
               title_multi='{n} bình luận mới trong bài viết của bạn')


def _zero_reactions():
    return {k: 0 for k in _REACTIONS}


def _reaction_map(table, id_col, ids, uid):
    """(counts_by_id, my_by_id) — 1 query GROUP BY + 1 query my_reaction, không N+1."""
    ids = list(ids)
    counts = {i: _zero_reactions() for i in ids}
    my = {i: None for i in ids}
    if not ids:
        return counts, my
    rows = q(f'SELECT {id_col}, reaction_type, count(*) AS n FROM {table} '
             f'WHERE {id_col} = ANY(%s) GROUP BY {id_col}, reaction_type', (ids,))
    for r in rows:
        counts[r[id_col]][r['reaction_type']] = r['n']
    mine = q(f'SELECT {id_col}, reaction_type FROM {table} '
             f'WHERE {id_col} = ANY(%s) AND user_id = %s', (ids, uid))
    for r in mine:
        my[r[id_col]] = r['reaction_type']
    return counts, my


def _toggle_reaction(table, id_col, parent_table, row_id, reaction, uid):
    """Toggle: react cùng loại → gỡ; loại khác → upsert. Trả (status, dict)."""
    if reaction not in _REACTIONS:
        return 400, {'error': 'Loại cảm xúc không hợp lệ'}
    with transaction.atomic():
        exists = q1(f'SELECT id FROM {parent_table} WHERE id=%s', (row_id,))
        if not exists:
            label = 'bài viết' if parent_table == 'posts' else 'bình luận'
            return 404, {'error': f'Không tìm thấy {label}'}
        cur = q1(f'SELECT reaction_type FROM {table} WHERE {id_col}=%s AND user_id=%s',
                 (row_id, uid))
        if cur and cur['reaction_type'] == reaction:
            x(f'DELETE FROM {table} WHERE {id_col}=%s AND user_id=%s', (row_id, uid))
            my_reaction = None
        else:
            x(f'''INSERT INTO {table} ({id_col}, user_id, reaction_type)
                  VALUES (%s, %s, %s)
                  ON CONFLICT ({id_col}, user_id)
                  DO UPDATE SET reaction_type = EXCLUDED.reaction_type, created_at = now()''',
              (row_id, uid, reaction))
            my_reaction = reaction
        # posts giữ cache tổng like_count; comments không có cache
        if parent_table == 'posts':
            x('UPDATE posts SET like_count = '
              '(SELECT count(*) FROM post_likes WHERE post_id=%s) WHERE id=%s',
              (row_id, row_id))
        rows = q(f'SELECT reaction_type, count(*) AS n FROM {table} '
                 f'WHERE {id_col}=%s GROUP BY reaction_type', (row_id,))
    reactions = _zero_reactions()
    for r in rows:
        reactions[r['reaction_type']] = r['n']
    return 200, {'ok': True, 'reactions': reactions, 'my_reaction': my_reaction}


def _paging(request):
    page = so_nguyen(request.query_params.get('page'), 1, 1, None)
    per_page = so_nguyen(request.query_params.get('per_page'), 10, 1, 50)
    return page, per_page, (page - 1) * per_page


def _can_modify(table, row_id, user):
    """Chủ sở hữu HOẶC admin mới được sửa/xóa. Trả (row, (body, status)|None)."""
    row = q1(f'SELECT user_id FROM {table} WHERE id=%s', (row_id,))
    if not row:
        label = 'bài viết' if table == 'posts' else 'bình luận'
        return None, ({'error': f'Không tìm thấy {label}'}, 404)
    if row['user_id'] != user.id and not is_admin(user):
        return None, ({'error': 'Không có quyền chỉnh sửa nội dung này'}, 403)
    return row, None


# ───────────────────────── Bài viết ─────────────────────────

class PostsView(APIView):
    def get(self, request):
        page, per_page, offset = _paging(request)
        category = (request.query_params.get('category') or '').strip()
        sort = request.query_params.get('sort', 'newest')

        conds = []
        params = []
        if category and category in _CATEGORIES:
            conds.append('p.category = %s')
            params.append(category)
        if request.query_params.get('mine'):
            conds.append('p.user_id = %s')
            params.append(request.user.id)
        # Lọc theo bài học: học viên đang mở bài nào thì thấy thảo luận bài đó.
        course_id = (request.query_params.get('course_id') or '').strip()
        if course_id:
            conds.append('p.course_id = %s')
            params.append(course_id[:60])
        lesson_no = request.query_params.get('lesson_no')
        if lesson_no and str(lesson_no).isdigit():
            conds.append('p.lesson_no = %s')
            params.append(int(lesson_no))
        where = ('WHERE ' + ' AND '.join(conds)) if conds else ''

        order = {
            'oldest': 'p.created_at ASC',
            'likes': 'p.like_count DESC, p.created_at DESC',
        }.get(sort, 'p.created_at DESC')

        # PERF 2026-07-19: gộp count + reactions + my_reaction + comment_count
        # vào 1 câu lệnh (trước đây 5 query = 5 RTT ~240ms/câu tới Neon).
        # COUNT(*) OVER() tính trên tập đã lọc TRƯỚC LIMIT → chính là total.
        posts = q(f'''SELECT p.id, p.user_id, p.category, p.title, p.content,
                             p.like_count, p.created_at, p.updated_at,
                             p.course_id, p.lesson_no, p.is_sample,
                             u.name AS author_name,
                             COUNT(*) OVER() AS _total,
                             (SELECT COALESCE(jsonb_object_agg(r.reaction_type, r.n), '{{}}'::jsonb)
                              FROM (SELECT reaction_type, COUNT(*) AS n
                                    FROM post_likes WHERE post_id = p.id
                                    GROUP BY reaction_type) r) AS _reactions,
                             (SELECT reaction_type FROM post_likes
                              WHERE post_id = p.id AND user_id = %s) AS my_reaction,
                             (SELECT COUNT(*) FROM comments c
                              WHERE c.post_id = p.id
                                AND c.parent_comment_id IS NULL) AS comment_count
                      FROM posts p
                      LEFT JOIN users u ON u.id = p.user_id
                      {where}
                      ORDER BY {order}
                      LIMIT %s OFFSET %s''',
                  (request.user.id,) + tuple(params) + (per_page, offset))

        if posts:
            total = posts[0]['_total']
        else:
            # Trang vượt quá dữ liệu (rows rỗng) → window không có total, đếm riêng
            count_where = where.replace('p.', '')
            total = q1(f'SELECT COUNT(*) AS n FROM posts {count_where}', tuple(params))['n']

        for p in posts:
            p.pop('_total', None)
            raw = p.pop('_reactions', None) or {}
            if isinstance(raw, str):
                import json as _json
                try:
                    raw = _json.loads(raw)
                except ValueError:
                    raw = {}
            reactions = _zero_reactions()
            reactions.update({k: v for k, v in raw.items() if k in reactions})
            p['reactions'] = reactions
            p['comment_count'] = p['comment_count'] or 0

        return Response({
            'posts': posts,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page,
        })

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        content = (data.get('content') or '').strip()
        if not content:
            return Response({'error': 'Nội dung không được để trống'}, status=400)

        category = data.get('category', 'discuss')
        if category not in _CATEGORIES:
            category = 'discuss'
        title = (data.get('title') or '').strip()
        # Thẻ bài học (không bắt buộc): gửi lên khi học viên đăng từ trong bài.
        course_id = (str(data.get('course_id') or '').strip() or None)
        if course_id:
            course_id = course_id[:60]
        lesson_no = data.get('lesson_no')
        try:
            lesson_no = int(lesson_no) if lesson_no not in (None, '') else None
        except (TypeError, ValueError):
            lesson_no = None

        row = q1('INSERT INTO posts (user_id, category, title, content, course_id, lesson_no) '
                 'VALUES (%s, %s, %s, %s, %s, %s) RETURNING id',
                 (request.user.id, category, title, content, course_id, lesson_no))
        return Response({'ok': True, 'id': row['id']})


class PostDetailView(APIView):
    def get(self, request, post_id):
        post = q1('''SELECT p.id, p.user_id, p.category, p.title, p.content,
                            p.like_count, p.created_at, p.updated_at,
                            p.course_id, p.lesson_no, p.is_sample,
                            u.name AS author_name
                     FROM posts p
                     LEFT JOIN users u ON u.id = p.user_id
                     WHERE p.id = %s''', (post_id,))
        if not post:
            return Response({'error': 'Không tìm thấy bài viết'}, status=404)
        counts, my = _reaction_map('post_likes', 'post_id', [post_id], request.user.id)
        cmt = q1('SELECT count(*) AS n FROM comments '
                 'WHERE post_id=%s AND parent_comment_id IS NULL', (post_id,))
        post['reactions'] = counts[post_id]
        post['my_reaction'] = my[post_id]
        post['comment_count'] = cmt['n']
        return Response(post)

    def put(self, request, post_id):
        data = request.data if isinstance(request.data, dict) else {}
        fields = {}
        if 'title' in data:
            fields['title'] = (data.get('title') or '').strip()
        if 'content' in data:
            content = (data.get('content') or '').strip()
            if not content:
                return Response({'error': 'Nội dung không được để trống'}, status=400)
            fields['content'] = content
        if 'category' in data:
            category = data.get('category')
            if category not in _CATEGORIES:
                return Response({'error': 'Danh mục không hợp lệ'}, status=400)
            fields['category'] = category
        if not fields:
            return Response({'error': 'Không có dữ liệu để cập nhật'}, status=400)

        _, err = _can_modify('posts', post_id, request.user)
        if err:
            return Response(err[0], status=err[1])
        set_clause = ', '.join(f'{col}=%s' for col in fields)
        x(f'UPDATE posts SET {set_clause}, updated_at=now() WHERE id=%s',
          tuple(fields.values()) + (post_id,))
        return Response({'ok': True})

    def delete(self, request, post_id):
        _, err = _can_modify('posts', post_id, request.user)
        if err:
            return Response(err[0], status=err[1])
        x('DELETE FROM posts WHERE id=%s', (post_id,))
        return Response({'ok': True})


class ReactPostView(APIView):
    def post(self, request, post_id):
        data = request.data if isinstance(request.data, dict) else {}
        reaction = (data.get('reaction') or '').strip()
        status, payload = _toggle_reaction('post_likes', 'post_id', 'posts',
                                           post_id, reaction, request.user.id)
        return Response(payload, status=status)


# ───────────────────────── Bình luận ─────────────────────────

class CommentsView(APIView):
    def get(self, request, post_id):
        page, per_page, offset = _paging(request)
        post = q1('SELECT id FROM posts WHERE id=%s', (post_id,))
        if not post:
            return Response({'error': 'Không tìm thấy bài viết'}, status=404)

        # Phân trang 2 tầng: đếm/trang theo comment gốc, reply lấy kèm theo cha
        total = q1('SELECT COUNT(*) AS n FROM comments '
                   'WHERE post_id=%s AND parent_comment_id IS NULL', (post_id,))['n']

        top = q('''SELECT c.id, c.post_id, c.user_id, c.parent_comment_id, c.content,
                          c.created_at, c.updated_at, u.name AS author_name
                   FROM comments c
                   LEFT JOIN users u ON u.id = c.user_id
                   WHERE c.post_id = %s AND c.parent_comment_id IS NULL
                   ORDER BY c.created_at ASC
                   LIMIT %s OFFSET %s''', (post_id, per_page, offset))
        top_ids = [r['id'] for r in top]

        replies = []
        if top_ids:
            replies = q('''SELECT c.id, c.post_id, c.user_id, c.parent_comment_id, c.content,
                                  c.created_at, c.updated_at, u.name AS author_name
                           FROM comments c
                           LEFT JOIN users u ON u.id = c.user_id
                           WHERE c.parent_comment_id = ANY(%s)
                           ORDER BY c.created_at ASC''', (top_ids,))

        comments = top + replies
        cids = [c['id'] for c in comments]
        counts, my = _reaction_map('comment_likes', 'comment_id', cids, request.user.id)
        for c in comments:
            c['reactions'] = counts[c['id']]
            c['my_reaction'] = my[c['id']]

        return Response({
            'comments': comments,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page,
        })

    def post(self, request, post_id):
        data = request.data if isinstance(request.data, dict) else {}
        content = (data.get('content') or '').strip()
        if not content:
            return Response({'error': 'Nội dung không được để trống'}, status=400)

        parent_id = data.get('parent_comment_id')

        with transaction.atomic():
            post = q1('SELECT id FROM posts WHERE id=%s', (post_id,))
            if not post:
                return Response({'error': 'Không tìm thấy bài viết'}, status=404)
            if parent_id is not None:
                # Chỉ lồng 1 cấp: cha phải cùng post VÀ không phải là reply
                parent = q1('SELECT parent_comment_id FROM comments WHERE id=%s AND post_id=%s',
                            (parent_id, post_id))
                if not parent:
                    return Response({'error': 'Không tìm thấy bình luận cha'}, status=404)
                if parent['parent_comment_id'] is not None:
                    return Response({'error': 'Không thể trả lời một trả lời'}, status=400)
            uid = request.user.id
            row = q1('INSERT INTO comments (post_id, user_id, parent_comment_id, content) '
                     'VALUES (%s, %s, %s, %s) RETURNING id',
                     (post_id, uid, parent_id, content))
            _notify_mentions(post_id, uid, content, parent_id)
        return Response({'ok': True, 'id': row['id']})


class ReactCommentView(APIView):
    def post(self, request, comment_id):
        data = request.data if isinstance(request.data, dict) else {}
        reaction = (data.get('reaction') or '').strip()
        status, payload = _toggle_reaction('comment_likes', 'comment_id', 'comments',
                                           comment_id, reaction, request.user.id)
        return Response(payload, status=status)


class CommentDetailView(APIView):
    def put(self, request, comment_id):
        data = request.data if isinstance(request.data, dict) else {}
        content = (data.get('content') or '').strip()
        if not content:
            return Response({'error': 'Nội dung không được để trống'}, status=400)

        _, err = _can_modify('comments', comment_id, request.user)
        if err:
            return Response(err[0], status=err[1])
        x('UPDATE comments SET content=%s, updated_at=now() WHERE id=%s',
          (content, comment_id))
        return Response({'ok': True})

    def delete(self, request, comment_id):
        _, err = _can_modify('comments', comment_id, request.user)
        if err:
            return Response(err[0], status=err[1])
        x('DELETE FROM comments WHERE id=%s', (comment_id,))
        return Response({'ok': True})
