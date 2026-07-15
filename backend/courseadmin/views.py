"""Port routes/admin.py — CRUD khóa học + bài giảng (quyền admin)."""
from rest_framework.response import Response
from rest_framework.views import APIView

from common.db import q, q1, x
from common.permissions import IsAdminRole

_COURSE_FIELDS = (
    'title', 'subtitle', 'description', 'image', 'level',
    'duration', 'students', 'color', 'accent_color', 'tag',
)


def _sync_lesson_count(course_id):
    """Đồng bộ cột courses.lessons với số bài giảng thực tế."""
    x('UPDATE courses SET lessons = '
      '(SELECT COUNT(*) FROM lessons WHERE course_id=%s) WHERE id=%s',
      (course_id, course_id))


class AdminBase(APIView):
    permission_classes = [IsAdminRole]


class AdminCoursesView(AdminBase):
    def get(self, request):
        rows = q('SELECT * FROM courses ORDER BY id')
        return Response({'courses': rows})

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        course_id = (data.get('id') or '').strip()
        title = (data.get('title') or '').strip()

        if not course_id:
            return Response({'error': 'Thiếu id khóa học'}, status=400)
        if not title:
            return Response({'error': 'Thiếu tiêu đề khóa học'}, status=400)

        if q1('SELECT id FROM courses WHERE id=%s', (course_id,)):
            return Response({'error': 'Id khóa học đã tồn tại'}, status=400)

        cols = ['id', 'title'] + [f for f in _COURSE_FIELDS if f != 'title']
        vals = [course_id, title] + [data.get(f) for f in _COURSE_FIELDS if f != 'title']
        placeholders = ', '.join(['%s'] * len(cols))
        x(f'INSERT INTO courses ({", ".join(cols)}) VALUES ({placeholders})', tuple(vals))
        return Response({'ok': True})


class AdminCourseDetailView(AdminBase):
    def put(self, request, course_id):
        data = request.data if isinstance(request.data, dict) else {}
        updates = {f: data[f] for f in _COURSE_FIELDS if f in data}
        if not updates:
            return Response({'error': 'Không có dữ liệu để cập nhật'}, status=400)

        if not q1('SELECT id FROM courses WHERE id=%s', (course_id,)):
            return Response({'error': 'Không tìm thấy khóa học'}, status=404)

        set_clause = ', '.join(f'{col}=%s' for col in updates)
        x(f'UPDATE courses SET {set_clause} WHERE id=%s',
          tuple(updates.values()) + (course_id,))
        return Response({'ok': True})

    def delete(self, request, course_id):
        if not q1('SELECT id FROM courses WHERE id=%s', (course_id,)):
            return Response({'error': 'Không tìm thấy khóa học'}, status=404)

        enrolled = q1('SELECT 1 FROM enrollments WHERE course_id=%s LIMIT 1', (course_id,))
        if enrolled:
            return Response(
                {'error': 'Không thể xóa: vẫn còn học viên đăng ký khóa học này'}, status=409)

        x('DELETE FROM courses WHERE id=%s', (course_id,))
        return Response({'ok': True})


class AdminCourseLessonsView(AdminBase):
    def get(self, request, course_id):
        rows = q('SELECT * FROM lessons WHERE course_id=%s ORDER BY sort_order, id',
                 (course_id,))
        return Response({'lessons': rows})


class AdminLessonsView(AdminBase):
    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        course_id = (data.get('course_id') or '').strip()
        title = (data.get('title') or '').strip()

        if not course_id:
            return Response({'error': 'Thiếu course_id'}, status=400)
        if not title:
            return Response({'error': 'Thiếu tiêu đề bài giảng'}, status=400)

        if not q1('SELECT id FROM courses WHERE id=%s', (course_id,)):
            return Response({'error': 'Không tìm thấy khóa học'}, status=404)

        x('INSERT INTO lessons (course_id, module, title, content, sort_order) '
          'VALUES (%s, %s, %s, %s, %s)',
          (course_id, data.get('module', ''), title,
           data.get('content', ''), data.get('sort_order', 0)))
        _sync_lesson_count(course_id)
        return Response({'ok': True})


class AdminLessonDetailView(AdminBase):
    def put(self, request, lesson_id):
        data = request.data if isinstance(request.data, dict) else {}
        fields = ('module', 'title', 'content', 'sort_order')
        updates = {f: data[f] for f in fields if f in data}
        if not updates:
            return Response({'error': 'Không có dữ liệu để cập nhật'}, status=400)
        if 'title' in updates and not (updates['title'] or '').strip():
            return Response({'error': 'Tiêu đề bài giảng không được để trống'}, status=400)

        if not q1('SELECT id FROM lessons WHERE id=%s', (lesson_id,)):
            return Response({'error': 'Không tìm thấy bài giảng'}, status=404)

        set_clause = ', '.join(f'{col}=%s' for col in updates)
        x(f'UPDATE lessons SET {set_clause} WHERE id=%s',
          tuple(updates.values()) + (lesson_id,))
        return Response({'ok': True})

    def delete(self, request, lesson_id):
        row = q1('SELECT course_id FROM lessons WHERE id=%s', (lesson_id,))
        if not row:
            return Response({'error': 'Không tìm thấy bài giảng'}, status=404)

        x('DELETE FROM lessons WHERE id=%s', (lesson_id,))
        _sync_lesson_count(row['course_id'])
        return Response({'ok': True})
