"""Port routes/courses.py — giữ nguyên SQL, tên field camelCase và message."""
from datetime import datetime, timezone

from django.core.cache import cache
from django.db import transaction
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.clock import local_now
from lessons.views import quen_ghi_danh
from common.db import q, q1, x

_ICONS = {'cpp': '📘', 'htmlcss': '📗', 'python': '📙', 'java': '📕'}


#: Chú thích SQL dùng chung cho hai câu đọc danh sách khoá.
CHU_DIEM_SAO = '''-- ĐIỂM SAO LẤY TỪ `course_ratings`, KHÔNG lấy `c.rating` (L15, 31/08/2026).
            -- `courses.rating` là con số SEED: cả ba khoá đang là 5.0 trong khi
            -- `course_ratings` RỖNG — tức mọi trang khoá khoe "5.0 ★" mà chưa một
            -- ai đánh giá. `CourseRatingView` tính đúng con số thật nhưng không
            -- nơi nào gọi (rà cả frontend: 0 kết quả).
            -- Chưa ai đánh giá thì trả NULL để màn hình nói "chưa có đánh giá",
            -- chứ một con số bịa thì không ai đọc ra được là bịa.'''


class CoursesView(APIView):
    def get(self, request):
        uid = request.user.id
        qs = request.query_params.get('q', '').strip()
        level = request.query_params.get('level', '').strip()
        languages = request.query_params.getlist('language')

        where_clauses = []
        params = [uid]

        if qs:
            q_lower = qs.lower()
            if q_lower == 'c' or q_lower == 'c++':
                where_clauses.append(
                    '(c.title ILIKE %s OR c.subtitle ILIKE %s OR c.description ILIKE %s OR c.tag ILIKE %s)')
                params.extend(['%c / c++%'] * 4)
            else:
                query_value = f'%{qs}%'
                where_clauses.append(
                    '(c.title ILIKE %s OR c.subtitle ILIKE %s OR c.description ILIKE %s OR c.tag ILIKE %s)')
                params.extend([query_value] * 4)

        if level and level != 'all':
            if level == 'Cơ bản':
                where_clauses.append('c.level ILIKE %s')
                params.append('%cơ bản%')
            elif level == 'Trung cấp':
                where_clauses.append('c.level ILIKE %s')
                params.append('%trung cấp%')
            elif level == 'Nâng cao':
                where_clauses.append('c.level ILIKE %s')
                params.append('%nâng cao%')
            elif level == 'Phù hợp người mới':
                where_clauses.append('c.level ILIKE %s')
                params.append('%phù hợp người mới%')

        lang_clauses = []
        for lang in languages:
            if lang == 'Python':
                lang_clauses.append('(c.title ILIKE %s OR c.tag ILIKE %s)')
                params.extend(['%python%', '%python%'])
            elif lang == 'JS':
                lang_clauses.append('(c.title ILIKE %s OR c.tag ILIKE %s OR c.subtitle ILIKE %s)')
                params.extend(['%js%', '%js%', '%javascript%'])
            elif lang == 'Java':
                lang_clauses.append('(c.title ILIKE %s OR c.tag ILIKE %s)')
                params.extend(['%java%', '%java%'])
            elif lang == 'SQL':
                lang_clauses.append('(c.title ILIKE %s OR c.tag ILIKE %s OR c.description ILIKE %s)')
                params.extend(['%sql%', '%sql%', '%sql%'])

        if lang_clauses:
            where_clauses.append('(' + ' OR '.join(lang_clauses) + ')')

        query = '''
            SELECT c.*,
                   ''' + CHU_DIEM_SAO + '''
                   dg.diem_tb AS rating, COALESCE(dg.so_luot, 0) AS rating_count,
                   CASE WHEN e.course_id IS NOT NULL THEN 1 ELSE 0 END AS enrolled
            FROM courses c
            LEFT JOIN enrollments e ON c.id = e.course_id AND e.user_id = %s
            LEFT JOIN (SELECT course_id, ROUND(AVG(rating)::numeric, 1) AS diem_tb,
                              COUNT(*) AS so_luot
                       FROM course_ratings GROUP BY course_id) dg ON dg.course_id = c.id
        '''
        if where_clauses:
            query += ' WHERE ' + ' AND '.join(where_clauses)

        rows = q(query, tuple(params))
        result = []
        for d in rows:
            d['enrolled'] = bool(d['enrolled'])
            d['accentColor'] = d.pop('accent_color')
            result.append(d)
        return Response(result)


class CourseDetailView(APIView):
    """Một khoá theo id — trả CÙNG shape với /api/courses.

    Trang chi tiết trước đây tải TOÀN BỘ danh sách khoá rồi lọc ở client
    (audit 2026-08-13): tốn payload và thừa việc. Endpoint này trả đúng khoá
    cần. 404 nếu không có.
    """

    def get(self, request, course_id):
        row = q1('''
            SELECT c.*,
                   ''' + CHU_DIEM_SAO + '''
                   dg.diem_tb AS rating, COALESCE(dg.so_luot, 0) AS rating_count,
                   CASE WHEN e.course_id IS NOT NULL THEN 1 ELSE 0 END AS enrolled
            FROM courses c
            LEFT JOIN enrollments e ON c.id = e.course_id AND e.user_id = %s
            LEFT JOIN (SELECT course_id, ROUND(AVG(rating)::numeric, 1) AS diem_tb,
                              COUNT(*) AS so_luot
                       FROM course_ratings GROUP BY course_id) dg ON dg.course_id = c.id
            WHERE c.id = %s
        ''', (request.user.id, course_id))
        if not row:
            return Response({'error': {'status': 404, 'message': 'Không tìm thấy khoá học'}}, status=404)
        row['enrolled'] = bool(row['enrolled'])
        row['accentColor'] = row.pop('accent_color')
        return Response(row)


class EnrolledView(APIView):
    def get(self, request):
        rows = q('''
            SELECT c.id, c.title, c.subtitle, c.color, c.accent_color,
                   e.progress, e.completed_lessons,
                   c.lessons AS total_lessons, c.duration,
                   e.time_spent, e.last_lesson, e.next_lesson
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            WHERE e.user_id = %s
        ''', (request.user.id,))
        result = []
        for d in rows:
            d['accentColor'] = d.pop('accent_color')
            d['totalLessons'] = d.pop('total_lessons')
            d['completedLessons'] = d.pop('completed_lessons')
            d['timeSpent'] = d.pop('time_spent')
            d['lastLesson'] = d.pop('last_lesson')
            d['nextLesson'] = d.pop('next_lesson')
            d['icon'] = _ICONS.get(d['id'], '📘')
            result.append(d)
        return Response(result)


class CoursesEnrolledView(APIView):
    def get(self, request):
        """Trả về courses + enrolled detail trong 1 query, 1 request."""
        rows = q('''
            SELECT c.id, c.title, c.subtitle, c.description, c.image, c.level,
                   c.duration, c.students, c.lessons,
                   c.color, c.accent_color, c.tag,
                   -- ĐIỂM SAO LẤY TỪ `course_ratings`, KHÔNG lấy `c.rating` (L15, 31/08/2026).
            -- `courses.rating` là con số SEED: cả ba khoá đang là 5.0 trong khi
            -- `course_ratings` RỖNG — tức mọi trang khoá khoe "5.0 ★" mà chưa một
            -- ai đánh giá. `CourseRatingView` tính đúng con số thật nhưng không
            -- nơi nào gọi (rà cả frontend: 0 kết quả).
            -- Chưa ai đánh giá thì trả NULL để màn hình nói "chưa có đánh giá",
            -- chứ một con số bịa thì không ai đọc ra được là bịa.
                   dg.diem_tb AS rating, COALESCE(dg.so_luot, 0) AS rating_count,
                   CASE WHEN e.course_id IS NOT NULL THEN 1 ELSE 0 END AS enrolled,
                   e.progress, e.completed_lessons,
                   e.time_spent, e.last_lesson, e.next_lesson
            FROM courses c
            LEFT JOIN enrollments e ON c.id = e.course_id AND e.user_id = %s
            LEFT JOIN (SELECT course_id, ROUND(AVG(rating)::numeric, 1) AS diem_tb,
                              COUNT(*) AS so_luot
                       FROM course_ratings GROUP BY course_id) dg ON dg.course_id = c.id
        ''', (request.user.id,))

        courses_list = []
        enrolled_list = []
        for d in rows:
            enrolled = bool(d['enrolled'])
            accent_color = d.pop('accent_color')
            d['enrolled'] = enrolled
            d['accentColor'] = accent_color
            courses_list.append(d)
            if enrolled:
                enrolled_list.append({
                    'id': d['id'],
                    'title': d['title'],
                    'subtitle': d['subtitle'],
                    'color': d['color'],
                    'accentColor': accent_color,
                    'progress': d['progress'] or 0,
                    'completedLessons': d['completed_lessons'] or 0,
                    'totalLessons': d['lessons'],
                    'duration': d['duration'],
                    'timeSpent': d['time_spent'] or '0h',
                    'lastLesson': d['last_lesson'] or '',
                    'nextLesson': d['next_lesson'] or '',
                    'icon': _ICONS.get(d['id'], '📘'),
                })

        return Response({'courses': courses_list, 'enrolled': enrolled_list})


class EnrollView(APIView):
    def post(self, request, course_id):
        uid = request.user.id
        course = q1('SELECT id, title FROM courses WHERE id=%s', (course_id,))
        if not course:
            return Response({'error': 'Không tìm thấy khóa học'}, status=404)
        first_lesson = 'Bài 1: ' + course['title']
        with transaction.atomic():
            # `local_now()` chứ không `now()` của SQL. Kết nối Neon chạy ở UTC,
            # lệch 7 tiếng so với giờ Việt Nam — đo 31/08/2026: `local_now()`
            # trả 13:57 trong khi `SELECT now()` trả 06:57. Cửa sổ hỏng là
            # 00:00–07:00 giờ VN: một thao tác lúc 00:30 ngày 1/9 được lưu
            # thành 17:30 ngày 31/8, và mọi báo cáo nhóm theo ngày đếm lệch
            # một ngày. Đây là bẫy mà `common/clock.py` được viết ra để dập;
            # `lessons/`, `mockexam/`, `quizzes/` đã đi qua nó, ba chỗ này thì
            # còn sót.
            x('''INSERT INTO enrollments (user_id, course_id, progress, completed_lessons,
                                          time_spent, last_lesson, next_lesson, enrolled_at)
                 VALUES (%s, %s, 0, 0, '0h', '', %s, %s)
                 ON CONFLICT (user_id, course_id) DO NOTHING''',
              (uid, course_id, first_lesson, local_now()))
            quen_ghi_danh(uid, course_id)
            # Re-enroll sau unenroll: lesson_progress (nguồn thật) vẫn giữ tiến độ
            # cũ — tính lại cache để dashboard không hiển thị 0% sai.
            done_row = q1('''SELECT COUNT(*) AS n,
                                    COALESCE(SUM(COALESCE(l.estimated_minutes, 15)), 0) AS minutes
                             FROM lesson_progress lp
                             JOIN lessons l ON l.id = lp.lesson_id
                             WHERE lp.user_id=%s AND lp.course_id=%s AND lp.status='completed' ''',
                          (uid, course_id))
            if done_row['n']:
                total = q1('SELECT lessons FROM courses WHERE id=%s', (course_id,))['lessons'] or 0
                done = done_row['n']
                progress = min(100, round(done * 100 / total)) if total else 0
                x('UPDATE enrollments SET completed_lessons=%s, progress=%s, time_spent=%s '
                  'WHERE user_id=%s AND course_id=%s',
                  (done, progress, str(round(done_row['minutes'] / 60, 1)) + 'h', uid, course_id))
        return Response({'ok': True})

    def delete(self, request, course_id):
        uid = request.user.id
        x('DELETE FROM enrollments WHERE user_id=%s AND course_id=%s', (uid, course_id))
        # Xoá đệm NGAY: đệm ghi danh sống 60 giây, không xoá thì em vừa huỷ vẫn
        # đọc được nội dung khoá thêm một phút.
        quen_ghi_danh(uid, course_id)
        return Response({'ok': True})


class RateCourseView(APIView):
    def post(self, request):
        uid = request.user.id
        data = request.data if isinstance(request.data, dict) else {}
        course_id = data.get('course_id')
        rating = data.get('rating')

        if not course_id:
            return Response({'error': 'Thiếu course_id'}, status=400)

        course = q1('SELECT id FROM courses WHERE id=%s', (course_id,))
        if not course:
            return Response({'error': 'Không tìm thấy khóa học'}, status=404)

        enrolled = q1('SELECT 1 FROM enrollments WHERE user_id=%s AND course_id=%s',
                      (uid, course_id))
        if not enrolled:
            return Response({'error': 'Bạn chưa đăng ký khóa học này'}, status=403)

        if not isinstance(rating, int) or isinstance(rating, bool) or rating < 1 or rating > 5:
            return Response({'error': 'Đánh giá phải là số nguyên từ 1 đến 5'}, status=400)

        x('''INSERT INTO course_ratings (user_id, course_id, rating, created_at)
             VALUES (%s, %s, %s, %s)
             ON CONFLICT (user_id, course_id)
             DO UPDATE SET rating = EXCLUDED.rating, created_at = EXCLUDED.created_at''',
          (uid, course_id, rating, local_now().isoformat()))
        return Response({'ok': True})


class CourseRatingView(APIView):
    def get(self, request, course_id):
        course = q1('SELECT id FROM courses WHERE id=%s', (course_id,))
        if not course:
            return Response({'error': 'Không tìm thấy khóa học'}, status=404)
        row = q1('SELECT AVG(rating) AS avg_rating, COUNT(*) AS rating_count '
                 'FROM course_ratings WHERE course_id=%s', (course_id,))
        avg_raw = row['avg_rating']
        average = round(float(avg_raw), 1) if avg_raw is not None else None
        return Response({'average': average, 'count': row['rating_count']})


# ─────────────────────────── /api/skills ───────────────────────────

def _calc_progress(sub_skills):
    if not sub_skills:
        return 0
    done = sum(1 for s in sub_skills if s['done'])
    return round(done * 100 / len(sub_skills))


_SKILL_SET_ICONS = {'db_design': '🏗️', 'db_design_tc': '🌐', 'db_design_nc': '⚙️'}


_SKILLS_STRUCTURE_KEY = 'skills:structure'
_SKILLS_STRUCTURE_TTL = 300  # giây — bài học mới xuất hiện trên /api/skills trong ≤5 phút


class SkillsView(APIView):
    def get(self, request):
        """Kỹ năng THẬT gắn với user: skill set = khóa · skill = module · sub = bài.

        PERF 2026-07-19: cấu trúc bài học (lessons×courses, ~66 dòng ≈ 10kB) gần
        như tĩnh → cache 5 phút; mỗi request chỉ còn query tiến độ user (vài dòng).
        Payload lớn từ Neon tốn thêm 1 RTT TCP nên tách nhỏ + cache nhanh hơn hẳn
        1 câu JOIN to (đo: ~730ms → ~460ms)."""
        structure = cache.get(_SKILLS_STRUCTURE_KEY)
        if structure is None:
            structure = q('''SELECT l.id, l.course_id, l.module, l.title, l.sort_order,
                                    c.title AS course_title
                             FROM lessons l
                             JOIN courses c ON c.id = l.course_id
                             WHERE l.module <> '' AND l.module IS NOT NULL
                             ORDER BY l.course_id, l.sort_order''')
            cache.set(_SKILLS_STRUCTURE_KEY, structure, _SKILLS_STRUCTURE_TTL)

        done_ids = {r['lesson_id'] for r in q(
            "SELECT lesson_id FROM lesson_progress WHERE user_id=%s AND status='completed'",
            (request.user.id,))}
        rows = [dict(r, done=r['id'] in done_ids) for r in structure]

        sets = {}
        for r in rows:
            cid = r['course_id']
            st = sets.setdefault(cid, {
                'id': cid,
                'title': r['course_title'],
                'icon': _SKILL_SET_ICONS.get(cid, '📘'),
                '_modules': {},
            })
            st['_modules'].setdefault(r['module'], []).append(
                {'title': 'Bài ' + str(r['sort_order']) + ': ' + r['title'],
                 'done': bool(r['done'])})

        result = []
        for st in sets.values():
            skills_out = []
            for m_idx, (m_title, subs) in enumerate(st['_modules'].items(), 1):
                skills_out.append({
                    'id': st['id'] + '-m' + str(m_idx),
                    'title': m_title,
                    'progress': _calc_progress(subs),
                    'sub_skills': subs,
                })
            total_subs = sum(len(sk['sub_skills']) for sk in skills_out)
            done_subs = sum(s['done'] for sk in skills_out for s in sk['sub_skills'])
            result.append({
                'id': st['id'],
                'title': st['title'],
                'icon': st['icon'],
                'progress': round(done_subs * 100 / total_subs) if total_subs else 0,
                'skills': skills_out,
            })
        order = {'db_design': 0, 'db_design_tc': 1, 'db_design_nc': 2}
        result.sort(key=lambda s: order.get(s['id'], 99))
        return Response({'skill_sets': result})


class PublicCoursesView(APIView):
    """GET /api/public/courses — danh sách khoá cho TRANG CHỦ, không cần đăng nhập.

    Trang chủ trước đây gọi /api/courses (yêu cầu đăng nhập) nên khách vãng lai
    nhận 401, khối khoá học không render và để lại một khoảng TRỐNG khổng lồ giữa
    trang — đúng thứ người ngoài nhìn thấy khi mở link (audit 2026-08-14).

    Không nới quyền cho /api/courses: view đó còn mang bộ lọc theo ngôn ngữ lập
    trình của pe_test và cần user id để tính cờ "đã ghi danh". Ở đây chỉ trả
    những trường trang giới thiệu cần, của khoá ĐÃ XUẤT BẢN.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        rows = q("SELECT id, title, subtitle, description, tag, level, duration, "
                 "lessons, color, accent_color, image, "
                 "(SELECT ROUND(AVG(r.rating)::numeric, 1) FROM course_ratings r "
                 " WHERE r.course_id = courses.id) AS rating, "
                 "(SELECT COUNT(*) FROM course_ratings r "
                 " WHERE r.course_id = courses.id) AS rating_count "
                 "FROM courses WHERE is_published IS NOT FALSE ORDER BY id")
        return Response({'courses': rows, 'count': len(rows)})
