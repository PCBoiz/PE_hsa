"""Soạn giáo trình — CRUD khoá học, bài giảng, và nội dung 5 bước của một bài.

AI ĐƯỢC LÀM GÌ (chốt 04/09/2026, xem `common/permissions.py`):

    quản trị viên      · tất cả
    Biên tập nội dung  · tất cả, TRỪ tạo và xoá một khoá học

Vì sao hai việc ấy giữ riêng cho quản trị viên: xoá một khoá kéo theo `lessons`
treo dưới nó và tiến độ đã học của người thật; tạo một khoá thì rẻ nhưng khoá
rỗng hiện ngay trên danh sách của mọi học viên. Sửa NỘI DUNG thì sai còn sửa
lại được, nên mở rộng.

Trước 04/09 mọi đường ở đây đòi `IsAdminRole`, tức người soạn giáo trình phải là
quản trị viên — mà quản trị viên thì thấy luôn tài khoản, mật khẩu, học viên.
Cấp quyền quản trị cho một người chỉ để họ gõ bài học là cấp thừa rất nhiều.
"""
import json
import re

from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from common import audit
from common.db import q, q1, x
from common.permissions import IsContentEditor, IsCourseOwner, is_admin
from lessons import luoc_do
from lessons.content import loi_html, validate_lesson
from lessons.grading import quen_dap_an

_COURSE_FIELDS = (
    'title', 'subtitle', 'description', 'image', 'level',
    'duration', 'students', 'color', 'accent_color', 'tag',
)

# ── KIỂM TRƯỜNG KHOÁ HỌC TRƯỚC KHI GHI (vá 04/09/2026) ──────────────────────
#
# Mọi trường trên đây được đổ THÔ vào `innerHTML` ở tầng frontend cũ:
#
#     main.js:817   '<img src="/' + c.image + '" alt="' + c.title + '" …'
#     main.js:825   '<div class="card-tag">' + c.tag + '</div>'
#     main.js:830   '<div class="card-desc">' + c.description + '</div>'
#     main.js:822   style="background:linear-gradient(135deg,' + c.color + ',' + c.accentColor + ')"
#     pages/landing.inline.js:58   '<strong>' + c.title + '</strong>'      ← TRANG CHỦ CÔNG KHAI
#
# Trang chủ không cần đăng nhập, nên một khoá học bị sửa tên là mã chạy trên
# máy của khách vãng lai và của cả đối tác mở link. Và từ 04/09 đường
# `PUT /api/admin/courses/<id>` mở cho vai `Biên tập nội dung` — vai sinh ra để
# KHÔNG phải cấp quyền quản trị cho người gõ nội dung. Không kiểm ở đây thì vai
# ấy leo thẳng lên quyền quản trị qua trình duyệt của người khác.
#
# CHẶN Ở ĐƯỜNG GHI, không chỉ ở chỗ hiển thị: `c.color` một mình xuất hiện ở SÁU
# chỗ dựng CSS trong `main.js`. Ép nó là mã màu hex thì cả sáu an toàn cùng lúc,
# và chỗ thứ bảy mọc ra ngày mai cũng thế.
#
# Trường CHỮ đi qua `lessons.content.loi_html` — CÙNG danh sách trắng với nội
# dung bài học, không phải một bản chép.

#: Mã màu: chỉ hex. Hai cột này đi thẳng vào `linear-gradient(...)`, tức là CSS.
_MAU = re.compile(r'^#[0-9a-fA-F]{3,8}$')

#: Ảnh: đường dẫn TƯƠNG ĐỐI trong `static/`. Không lược đồ, không `..`, không
#: dấu nháy — nó nằm trong `src="/…"`.
#:
#: Không cho `/` ở ĐẦU (vá 04/09/2026, vòng kiểm định thứ hai). Bản trước cho
#: phép, mà sink dựng `"/" + image`, nên `image = /evil.com/x.png` thành
#: `src="//evil.com/x.png"` — URL GIAO THỨC TƯƠNG ĐỐI, tức trình duyệt tải ảnh
#: từ máy chủ của kẻ khác. Không chạy được JS (nó là `src` của `<img>`), nhưng
#: mọi người mở trang khoá đều gửi IP và referrer sang đó, và nội dung ảnh do
#: kẻ ấy quyết định. Sink còn sống ở React: `courses/[courseId]/page.tsx:93`
#: dựng `/${course.image}` rồi đổ thẳng vào `<img src>`.
#:
#: Ý định của hàng rào vốn ĐÃ là "đường dẫn trong thư mục static", mà đường dẫn
#: như thế không bao giờ bắt đầu bằng `/`. Đây là siết cho khớp ý định, không
#: phải thêm luật mới. Ba khoá đang chạy đều dạng `static/images/…`.
_ANH = re.compile(r'^[A-Za-z0-9._-][A-Za-z0-9._/-]{0,199}$')

# `id` là trường DUY NHẤT của khoá học không đi qua `_clean_course_payload` —
# nó tới từ `data['id']` trên POST, và trước bản vá này chỉ bị kiểm "khác rỗng"
# và "chưa trùng". Trong khi nó được nội suy THÔ vào NĂM chuỗi JS nằm bên trong
# thuộc tính HTML:
#
#     main.js:855   onclick="window.location='/courses/'      + c.id + "'"
#     main.js:861   onclick="toggleEnroll('                   + c.id + "',false)"
#     main.js:923   onclick="window.location='" + COURSE_URLS[c.id] + "'"
#     main.js:1005  lessonUrl = COURSE_URLS[c.id] || '/lesson/' + c.id
#     dashboard.js:2415  onclick="window.location.href='" + '/lesson/' + c.id + "'"
#
# Một dấu nháy đơn trong `id` là đủ ở cả năm chỗ. `COURSE_URLS` là bảng cứng ba
# dòng nên khoá lạ luôn rơi vào nhánh nối chuỗi.
#
# Ép slug KHÔNG phải là làm cho đẹp: `id` đã là một đoạn ĐƯỜNG DẪN
# (`/courses/<id>`, `/lesson/<id>`), nên slug là hình dạng duy nhất chạy đúng.
# Ba khoá đang chạy — hsa_quantitative, hsa_science, hsa_verbal — đều khớp.
_MA_KHOA = re.compile(r'^[a-z0-9][a-z0-9_-]{0,63}$')


def _clean_course_payload(data):
    """Trả ``(updates, loi)``. ``loi`` khác None thì KHÔNG ghi gì."""
    updates = {f: data[f] for f in _COURSE_FIELDS if f in data}
    for truong, gia in list(updates.items()):
        if gia is None:
            continue
        chuoi = str(gia)
        if truong in ('color', 'accent_color'):
            if chuoi and not _MAU.match(chuoi):
                return None, ('"%s" phải là mã màu hex, ví dụ #8B7CF6 '
                              '(đang nhận %r).' % (truong, chuoi[:40]))
        elif truong == 'image':
            if chuoi and (not _ANH.match(chuoi) or '..' in chuoi):
                return None, ('"image" phải là đường dẫn ảnh trong thư mục static, '
                              'ví dụ img/hsa-quantitative.png (đang nhận %r).' % chuoi[:60])
        elif truong == 'students':
            if chuoi and not chuoi.isdigit():
                return None, '"students" phải là số.'
        else:
            e = loi_html(chuoi, truong)
            if e:
                return None, e[0]
            if len(chuoi) > 2000:
                return None, '"%s" dài %d ký tự, tối đa 2000.' % (truong, len(chuoi))
    return updates, None


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
    """Mặc định của khu soạn giáo trình: quản trị viên hoặc Biên tập nội dung."""

    permission_classes = [IsContentEditor]


class _ChuKhoa:
    """Trộn vào view nào có phương thức CHỈ quản trị viên được gọi.

    DRF khai quyền theo VIEW chứ không theo phương thức, nên tách bằng
    `get_permissions`. Liệt kê tên phương thức trong `CHI_QUAN_TRI`.
    """

    CHI_QUAN_TRI: tuple = ()

    def get_permissions(self):
        if (self.request.method or '').lower() in self.CHI_QUAN_TRI:
            return [IsCourseOwner()]
        return super().get_permissions()


class AdminCoursesView(_ChuKhoa, AdminBase):
    CHI_QUAN_TRI = ('post',)          # tạo khoá mới

    def get(self, request):
        rows = q('SELECT * FROM courses ORDER BY id')
        return Response({'courses': rows})

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        course_id = (data.get('id') or '').strip()
        title = (data.get('title') or '').strip()

        if not course_id:
            return Response({'error': 'Thiếu id khóa học'}, status=400)
        if not _MA_KHOA.match(course_id):
            return Response({'error': (
                'Mã khoá học chỉ gồm chữ thường, số, gạch dưới và gạch ngang, '
                'bắt đầu bằng chữ hoặc số, tối đa 64 ký tự — nó là một đoạn '
                'đường dẫn (/lesson/<mã>). Ví dụ: hsa_quantitative. '
                'Đang nhận %r.' % course_id[:60])}, status=400)
        if not title:
            return Response({'error': 'Thiếu tiêu đề khóa học'}, status=400)

        if q1('SELECT id FROM courses WHERE id=%s', (course_id,)):
            return Response({'error': 'Id khóa học đã tồn tại'}, status=400)

        _, loi = _clean_course_payload(data)
        if loi:
            return Response({'error': loi}, status=400)

        cols = ['id', 'title'] + [f for f in _COURSE_FIELDS if f != 'title']
        vals = [course_id, title] + [data.get(f) for f in _COURSE_FIELDS if f != 'title']
        placeholders = ', '.join(['%s'] * len(cols))
        x(f'INSERT INTO courses ({", ".join(cols)}) VALUES ({placeholders})', tuple(vals))
        audit.record(request, audit.COURSE_CREATE, target_type='course',
                     target_id=course_id, target_label=title,
                     summary='Tạo khoá học "%s" (mã %s).' % (title, course_id))
        return Response({'ok': True})


class AdminCourseDetailView(_ChuKhoa, AdminBase):
    CHI_QUAN_TRI = ('delete',)        # xoá khoá — kéo theo bài và tiến độ

    def put(self, request, course_id):
        data = request.data if isinstance(request.data, dict) else {}
        updates, loi = _clean_course_payload(data)
        if loi:
            return Response({'error': loi}, status=400)
        if not updates:
            return Response({'error': 'Không có dữ liệu để cập nhật'}, status=400)

        if not q1('SELECT id FROM courses WHERE id=%s', (course_id,)):
            return Response({'error': 'Không tìm thấy khóa học'}, status=404)

        set_clause = ', '.join(f'{col}=%s' for col in updates)
        x(f'UPDATE courses SET {set_clause} WHERE id=%s',
          tuple(updates.values()) + (course_id,))
        audit.record(request, audit.COURSE_UPDATE, target_type='course',
                     target_id=course_id, target_label=updates.get('title') or course_id,
                     summary='Sửa khoá học %s (%s).' % (course_id, ', '.join(updates)),
                     detail={k: str(v)[:200] for k, v in updates.items()})
        return Response({'ok': True})

    def delete(self, request, course_id):
        if not q1('SELECT id FROM courses WHERE id=%s', (course_id,)):
            return Response({'error': 'Không tìm thấy khóa học'}, status=404)

        enrolled = q1('SELECT 1 FROM enrollments WHERE course_id=%s LIMIT 1', (course_id,))
        if enrolled:
            return Response(
                {'error': 'Không thể xóa: vẫn còn học viên đăng ký khóa học này'}, status=409)

        x('DELETE FROM courses WHERE id=%s', (course_id,))
        audit.record(request, audit.COURSE_DELETE, target_type='course',
                     target_id=course_id, target_label=course_id,
                     summary='Xoá khoá học %s — bài học của khoá bị xoá theo.' % course_id)
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
        # Lấy sàn từ SỐ BÀI THẬT trong bảng, không chỉ từ `sort_order` gửi lên.
        # Thiếu `sort_order` thì nó mặc định 0, mà `_bump_lesson_count` bỏ qua
        # giá trị 0 — nên một khoá vừa được thêm bài vẫn hiện "0 bài" trên danh
        # sách khoá học. Đếm thật vẫn giữ đúng luật "chỉ đi lên" của hàm đó, vì
        # COUNT không bao giờ nhỏ hơn số bài đang có.
        thuc_te = q1('SELECT COUNT(*) AS n FROM lessons WHERE course_id=%s',
                     (course_id,))['n']
        _bump_lesson_count(course_id, max(int(thuc_te or 0),
                                          int(data.get('sort_order') or 0)))
        audit.record(request, audit.LESSON_CREATE, target_type='lesson',
                     target_label=title,
                     summary='Thêm bài "%s" vào khoá %s.' % (title, course_id),
                     detail={'courseId': course_id, 'sortOrder': data.get('sort_order')})
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
        audit.record(request, audit.LESSON_UPDATE, target_type='lesson',
                     target_id=lesson_id, target_label=updates.get('title') or str(lesson_id),
                     summary='Sửa bài #%s (%s).' % (lesson_id, ', '.join(updates)),
                     detail={k: str(v)[:200] for k, v in updates.items()})
        return Response({'ok': True})

    def delete(self, request, lesson_id):
        row = q1('SELECT course_id, title FROM lessons WHERE id=%s', (lesson_id,))
        if not row:
            return Response({'error': 'Không tìm thấy bài giảng'}, status=404)

        # XOÁ MỘT BÀI LÀ XOÁ TIẾN ĐỘ ĐÃ HỌC CỦA NGƯỜI THẬT (vá 04/09/2026).
        #
        # `lesson_progress_lesson_fk` là `ON DELETE CASCADE` (đo trên CSDL thật),
        # nên câu `DELETE` một dòng ở đây kéo theo mọi dòng `lesson_progress`
        # trỏ tới bài ấy — điểm, XP, ngày hoàn thành. Đo 04/09: bài id=1 đang
        # treo 4 dòng của học viên thật.
        #
        # Cửa xoá KHOÁ đã có hàng rào đúng loại này từ đầu (còn `enrollments`
        # thì 409). Cửa xoá BÀI thì không — và từ 04/09 nó mở cho vai `Biên tập
        # nội dung`, tức người KHÔNG phải quản trị viên. Câu xác nhận trên giao
        # diện cũng chỉ hỏi "Xoá bài ...?", không một chữ nào về tiến độ.
        #
        # Chặn theo hai mức, đúng lối `terms.py` đã dùng: người biên tập thì
        # không bao giờ; quản trị viên thì phải nói rõ ý định bằng `?confirm=1`.
        hoc = q1('SELECT COUNT(*) AS n FROM lesson_progress WHERE lesson_id=%s',
                 (lesson_id,))['n']
        if hoc:
            xac_nhan = str(request.query_params.get('confirm') or '') in ('1', 'true')
            if not is_admin(request.user):
                return Response(
                    {'error': 'Bài này đã có %d lượt học được ghi nhận. Xoá bài sẽ xoá '
                              'luôn tiến độ ấy, nên chỉ quản trị viên làm được. Muốn bỏ '
                              'bài khỏi giáo trình thì sửa nội dung, đừng xoá dòng.' % hoc},
                    status=403)
            if not xac_nhan:
                return Response(
                    {'error': 'Bài này đã có %d lượt học được ghi nhận, và xoá bài sẽ XOÁ '
                              'HẲN số liệu ấy — không khôi phục được. Gửi lại kèm '
                              '?confirm=1 nếu chắc chắn.' % hoc,
                     'needsConfirm': True, 'progressRows': hoc}, status=409)

        # Xoá bài KHÔNG hạ tổng số bài của khoá: bản trong file JS vẫn còn đó,
        # học viên vẫn học được. Muốn đổi tổng thì dùng total_lessons khi nhập.
        x('DELETE FROM lessons WHERE id=%s', (lesson_id,))
        audit.record(request, audit.LESSON_DELETE, target_type='lesson',
                     target_id=lesson_id, target_label=row['title'],
                     summary='Xoá bài "%s" của khoá %s%s.'
                             % (row['title'], row['course_id'],
                                ' — kèm %d lượt học đã ghi nhận' % hoc if hoc else ''),
                     detail={'courseId': row['course_id'], 'progressRows': hoc})
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
        # LƯỢC ĐỒ ĐI KÈM (04/09/2026, anh Sơn chốt "một lược đồ, hai bên dùng").
        #
        # Ba khoảng số của nội dung bài — `index`, `xp_reward`,
        # `drill.time_seconds` — trước đây viết cứng ở `lessons/content.py` VÀ
        # viết cứng lần nữa trong `admin/NoiDungBai.tsx`. Hôm ấy chúng khớp;
        # không có gì giữ cho chúng khớp.
        #
        # Gửi kèm ở ĐÂY chứ không mở một endpoint riêng: biểu mẫu soạn bài vốn
        # đã gọi đúng đường này để nạp nội dung. Thêm một cửa nữa là thêm một
        # lượt tải, một trạng thái chờ, và một chỗ hỏng được — cho một bảng hằng
        # số vài dòng.
        row['schema'] = luoc_do.cho_client()
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
        # `index` PHẢI khớp `sort_order` của chính dòng đang sửa (A16,
        # 31/08/2026). Engine đọc `index` để biết mình là bài số mấy rồi gọi
        # `/complete` và `/check` theo số đó. Dán mẫu có `"index": 28` vào ô nội
        # dung của bài đang ở `sort_order = 5` thì em học bài 5 nhưng tiến độ ghi
        # sang bài 28, và bài 5 được chấm bằng đáp án của bài 28.
        #
        # Đường nhập cả khoá ép `sort_order = index` nên không hở; chỉ đường sửa
        # lẻ này mới nhận hai con số rồi để chúng lệch nhau. Đo trên 76 bài đang
        # có: 0 bài lệch, nên hàng rào này không chặn nội dung nào đang chạy.
        idx = content.get('index')
        if idx != row['sort_order']:
            errors = list(errors) + [
                'bài #%s: "index" trong nội dung là %r nhưng bài này đang ở vị trí %s. '
                'Sửa "index" cho khớp, hoặc dùng đường nhập cả khoá nếu muốn đổi vị trí.'
                % (row['sort_order'], idx, row['sort_order'])]
        if errors:
            return Response({'error': 'Nội dung chưa hợp lệ.', 'details': errors}, status=400)

        x('UPDATE lessons SET content_json=%s::jsonb, title=COALESCE(NULLIF(%s,\'\'), title) '
          'WHERE id=%s',
          (json.dumps(content, ensure_ascii=False), (content.get('title') or '').strip(), lesson_id))
        # Xoá đệm đáp án. Không có dòng này thì giảng viên sửa một đáp án
        # sai xong, trong tối đa 60 giây tiếp theo máy chủ vẫn CHẤM bằng
        # đáp án CŨ — và từ 31/08/2026 con số ấy đi thẳng vào XP và bản đồ
        # năng lực. `quen_dap_an` có sẵn từ sáng nhưng chưa nơi nào trong mã
        # chạy thật gọi nó; một hàm chỉ có phép kiểm gọi là một hàm không
        # tồn tại trên đường chạy thật.
        quen_dap_an(row['course_id'], row['sort_order'])
        audit.record(request, audit.LESSON_CONTENT_UPDATE, target_type='lesson',
                     target_id=lesson_id, target_label=content.get('title') or str(lesson_id),
                     summary='Sửa nội dung bài #%s (%s, bài số %s).'
                             % (lesson_id, row['course_id'], row['sort_order']),
                     detail={'courseId': row['course_id'], 'index': content.get('index')})
        return Response({'ok': True})


class AdminCourseImportView(AdminBase):
    """POST /api/admin/courses/<course_id>/import — nhập cả khoá từ một mảng JSON.

    Đây là đường để nhận giáo trình đối tác bàn giao: một file JSON, một lần
    nhập. Kiểm TOÀN BỘ trước rồi mới ghi — sai một bài thì không bài nào được
    ghi, tránh trạng thái nửa vời khó gỡ.

    Ghi đè theo `index` (khớp sort_order). Bài chưa có thì tạo mới.
    """

    def post(self, request, course_id):
        body = request.data if isinstance(request.data, dict) else {}

        # QUYỀN KIỂM TRƯỚC, dữ liệu kiểm sau. Đặt sau thì cùng một việc bị cấm
        # trả về hai mã khác nhau tuỳ file người ta gửi có hợp lệ hay không —
        # người biên tập sẽ đi sửa file, sửa xong mới biết mình không có quyền.
        # Đúng lỗi thứ tự đã mắc hôm 30/08 ở đường tạo tài khoản hàng loạt (dán
        # 60 dòng → "sẽ tạo 60 tài khoản" → bấm Tạo → mới bị từ chối vì quá trần).
        #
        # `total_lessons` là ĐƯỜNG DUY NHẤT hạ được tổng số bài của khoá, và
        # tổng ấy là mẫu số của mọi phần trăm tiến độ: nhập một file 10 bài kèm
        # `total_lessons: 10` cho khoá 27 bài là kéo tiến độ của mọi học viên
        # lên gần gấp ba, im lặng. Nên nó giữ cho quản trị viên.
        if body.get('total_lessons') is not None and not is_admin(request.user):
            return Response(
                {'error': 'Chỉ quản trị viên đặt được tổng số bài của khoá. '
                          'Bỏ trường "total_lessons" thì hệ thống tự nâng tổng '
                          'lên theo bài có số thứ tự lớn nhất.'}, status=403)

        if not q1('SELECT 1 FROM courses WHERE id=%s', (course_id,)):
            return Response({'error': 'Không tìm thấy khóa học'}, status=404)

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
                # Cùng lý do với đường sửa lẻ ở trên: nhập đè nội dung mà không
                # xoá đệm thì tối đa 60 giây tiếp theo vẫn chấm bằng đáp án cũ.
                quen_dap_an(course_id, idx)
            # Quyền đặt `total_lessons` đã kiểm ở ĐẦU `post()` — xem lý do ở đó.
            total = body.get('total_lessons')
            if isinstance(total, int) and total > 0:
                _set_lesson_count(course_id, total)
            else:
                _bump_lesson_count(course_id, max(int(o['index']) for o in lessons))

        audit.record(request, audit.COURSE_IMPORT, target_type='course',
                     target_id=course_id, target_label=course_id,
                     summary='Nhập giáo trình vào khoá %s — thêm %d bài, cập nhật %d bài.'
                             % (course_id, created, updated),
                     detail={'created': created, 'updated': updated,
                             'totalLessons': body.get('total_lessons')})
        return Response({'ok': True, 'created': created, 'updated': updated,
                         'total': created + updated})
