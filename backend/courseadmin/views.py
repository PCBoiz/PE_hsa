"""Port routes/admin.py — CRUD khóa học + bài giảng (quyền admin)."""
import json

from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from common.db import q, q1, x
from common.permissions import IsAdminRole
from lessons.content import validate_lesson

_COURSE_FIELDS = (
    'title', 'subtitle', 'description', 'image', 'level',
    'duration', 'students', 'color', 'accent_color', 'tag',
)


def _bump_lesson_count(course_id, at_least=None):
    """Nâng courses.lessons lên ít nhất `at_least`, KHÔNG bao giờ hạ xuống.

    Không được đếm số dòng bảng ``lessons``: bảng đó chứa cả stub tạo lười (xem
    lessons/views.py:_resolve_lesson_id) trong khi nội dung thật của phần lớn
    bài vẫn nằm ở file JS phía client. Đếm theo số dòng từng kéo tổng số bài của
    khoá Định lượng từ 27 xuống 4 và làm sai mọi phần trăm tiến độ (2026-08-14).

    Trong giai đoạn nội dung nằm ở HAI nguồn, số bài chỉ có thể ĐI LÊN. Khi đối
    tác bàn giao trọn giáo trình thì gửi kèm "total_lessons" để đặt con số chính
    xác — đó là lúc duy nhất được phép hạ.
    """
    if not at_least:
        return
    x('UPDATE courses SET lessons = GREATEST(COALESCE(lessons, 0), %s) WHERE id=%s',
      (int(at_least), course_id))


def _set_lesson_count(course_id, total):
    """Đặt CHÍNH XÁC tổng số bài — chỉ dùng khi bên soạn nội dung khẳng định."""
    x('UPDATE courses SET lessons=%s WHERE id=%s', (max(0, int(total)), course_id))


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
        _bump_lesson_count(course_id, data.get('sort_order') or 0)
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

        # Xoá bài KHÔNG hạ tổng số bài của khoá: bản trong file JS vẫn còn đó,
        # học viên vẫn học được. Muốn đổi tổng thì dùng total_lessons khi nhập.
        x('DELETE FROM lessons WHERE id=%s', (lesson_id,))
        return Response({'ok': True})


class AdminLessonContentView(AdminBase):
    """GET/PUT /api/admin/lessons/<id>/content — nội dung 5 bước của một bài.

    Nội dung lưu ở lessons.content_json và được /api/courses/<id>/content phục
    vụ cho engine. Trước 2026-08-14 trang quản trị chỉ ghi được cột `content`
    (TEXT) mà KHÔNG ai đọc, nên bài tạo ở đây học viên không bao giờ thấy.
    """

    def get(self, request, lesson_id):
        row = q1('SELECT id, course_id, title, module, sort_order, content_json '
                 'FROM lessons WHERE id=%s', (lesson_id,))
        if not row:
            return Response({'error': 'Không tìm thấy bài giảng'}, status=404)
        data = row.get('content_json')
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except ValueError:
                data = None
        row['content_json'] = data
        return Response(row)

    def put(self, request, lesson_id):
        row = q1('SELECT id, course_id, sort_order FROM lessons WHERE id=%s', (lesson_id,))
        if not row:
            return Response({'error': 'Không tìm thấy bài giảng'}, status=404)

        body = request.data if isinstance(request.data, dict) else {}
        content = body.get('content_json')
        if content in (None, '', {}):
            # Xoá nội dung → bài quay về dùng bản trong file JS.
            x('UPDATE lessons SET content_json=NULL WHERE id=%s', (lesson_id,))
            return Response({'ok': True, 'cleared': True})

        if isinstance(content, str):
            try:
                content = json.loads(content)
            except ValueError as exc:
                return Response({'error': f'JSON không hợp lệ: {exc}'}, status=400)

        errors = validate_lesson(content, path=f'bài #{row["sort_order"]}')
        if errors:
            return Response({'error': 'Nội dung chưa hợp lệ.', 'details': errors}, status=400)

        x('UPDATE lessons SET content_json=%s::jsonb, title=COALESCE(NULLIF(%s,\'\'), title) '
          'WHERE id=%s',
          (json.dumps(content, ensure_ascii=False), (content.get('title') or '').strip(), lesson_id))
        return Response({'ok': True})


class AdminCourseImportView(AdminBase):
    """POST /api/admin/courses/<course_id>/import — nhập cả khoá từ một mảng JSON.

    Đây là đường để nhận giáo trình đối tác bàn giao: một file JSON, một lần
    nhập. Kiểm TOÀN BỘ trước rồi mới ghi — sai một bài thì không bài nào được
    ghi, tránh trạng thái nửa vời khó gỡ.

    Ghi đè theo `index` (khớp sort_order). Bài chưa có thì tạo mới.
    """

    def post(self, request, course_id):
        if not q1('SELECT 1 FROM courses WHERE id=%s', (course_id,)):
            return Response({'error': 'Không tìm thấy khóa học'}, status=404)

        body = request.data if isinstance(request.data, dict) else {}
        lessons = body.get('lessons')
        if isinstance(lessons, str):
            try:
                lessons = json.loads(lessons)
            except ValueError as exc:
                return Response({'error': f'JSON không hợp lệ: {exc}'}, status=400)
        if not isinstance(lessons, list) or not lessons:
            return Response({'error': 'Cần một mảng "lessons" có ít nhất 1 bài.'}, status=400)
        if len(lessons) > 300:
            return Response({'error': 'Tối đa 300 bài mỗi lần nhập.'}, status=400)

        # Kiểm trước — không ghi gì cho tới khi mọi bài đều hợp lệ.
        errors, seen = [], {}
        for i, obj in enumerate(lessons, 1):
            path = f'bài thứ {i}'
            errs = validate_lesson(obj, path=path)
            idx = obj.get('index') if isinstance(obj, dict) else None
            if idx in seen:
                errs.append(f'{path}: "index" {idx} trùng với {seen[idx]}')
            elif idx is not None:
                seen[idx] = path
            errors.extend(errs)
        if errors:
            return Response({'error': f'{len(errors)} lỗi trong dữ liệu nhập.',
                             'details': errors[:40]}, status=400)

        created = updated = 0
        with transaction.atomic():
            for obj in lessons:
                idx = int(obj['index'])
                payload = json.dumps(obj, ensure_ascii=False)
                title = (obj.get('title') or f'Bài {idx}').strip()
                module = (obj.get('topic_tag') or '').split('·')[-1].strip()[:120] or None
                existing = q1('SELECT id FROM lessons WHERE course_id=%s AND sort_order=%s',
                              (course_id, idx))
                if existing:
                    x('UPDATE lessons SET title=%s, module=COALESCE(%s, module), '
                      'content_json=%s::jsonb WHERE id=%s',
                      (title, module, payload, existing['id']))
                    updated += 1
                else:
                    x('INSERT INTO lessons (course_id, title, module, sort_order, content_json) '
                      'VALUES (%s,%s,%s,%s,%s::jsonb)',
                      (course_id, title, module, idx, payload))
                    created += 1
            total = body.get('total_lessons')
            if isinstance(total, int) and total > 0:
                _set_lesson_count(course_id, total)
            else:
                _bump_lesson_count(course_id, max(int(o['index']) for o in lessons))

        return Response({'ok': True, 'created': created, 'updated': updated,
                         'total': created + updated})
