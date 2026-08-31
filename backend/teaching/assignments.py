"""Giao bài & chấm tay — đặc tả ERP §5, lược đồ `sql/legacy_schema.sql` §38.

Tới hôm nay hệ thống chỉ chấm được TRẮC NGHIỆM. Trung tâm luyện thi HSA cần giao
bài tự luận — và phần Định tính gần như chỉ đo được bằng cách đó.

VÌ SAO LÀM ĐƯỢC DÙ CHƯA CÓ CÂU TRẢ LỜI CỦA TopHSA. Đặc tả §5 để ngỏ ba câu, và
không câu nào đổi hình dạng của mã dưới đây:
  · "có chấm tự luận không" → đổi việc mô-đun này CÓ ĐƯỢC DÙNG hay không;
  · "thang điểm nào"        → mỗi bài tự khai `max_score`, hệ thống quy về %;
  · "ai chấm"               → đổi đúng MỘT dòng `permission_classes`.
Chỗ duy nhất phải sửa khi có câu trả lời là phân quyền, nên chờ chỉ mất thời gian.

ĐIỂM TỰ LUẬN VÀO THẲNG BẢN ĐỒ NĂNG LỰC. Chấm xong đẻ `learning_events` với
`kind='assignment'` — không có luật tính riêng nào, vì bản đồ năng lực đọc từ
dòng sự kiện chứ không đọc từ bảng nguồn. Đây là lợi tức của kỷ luật một-cửa ở
`common/events.py`: thêm một loại hoạt động mới mà không phải sửa màn hình nào.

CHẤM CẢ LỚP LÀ MỘT LƯỢT GHI. Cùng lý do với điểm danh (T41): gọi `record_event`
trong vòng lặp tốn ba lượt tới Neon cho mỗi em. Giảng viên chấm xong hai chục bài
rồi bấm Lưu một lần, và đang chờ trước màn hình.
"""
import logging
from decimal import Decimal, InvalidOperation

from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from common import audit
from common.clock import local_now
from common.db import q, q1, x
from common.events import (KIND_ASSIGNMENT, SOURCE_SYSTEM, forget_events, pct,
                           record_events)
from common.permissions import IsTeacherOrAdmin, can_see_class
from teaching.vocab import chi_hoc_vien

#: Vòng đời một bài tập. Khớp `assignments_status_check` ở §38.
#: 'draft' = đang soạn, học viên CHƯA thấy. Có trạng thái này vì soạn đề tự luận
#: mất thời gian, và một bài soạn dở mà học viên đã thấy thì họ hỏi ngay.
ASSIGNMENT_STATUS = ('draft', 'open', 'closed')

TEXT_FIELDS = {'title': 200, 'description': 4000, 'attachment_url': 400}

#: Trần số bài chấm trong MỘT lần gửi. Khác trần 50 của nhập tài khoản (chỗ đó
#: bị chặn bởi chi phí băm mật khẩu): ở đây mỗi bài chỉ là một dòng UPDATE, nên
#: rộng tay hơn. Vẫn phải có trần để một thân request hỏng không thành một câu
#: SQL vài nghìn tham số.
MAX_GRADE_PER_BATCH = 200

logger = logging.getLogger(__name__)

_NOT_FOUND = {'error': 'Không tìm thấy bài tập này.'}


def khoa_cua_lop(class_id):
    """`course_id` của khoá mà lớp đang dạy. None nếu lớp không tồn tại."""
    r = q1('SELECT course_id FROM classes WHERE id = %s', (class_id,))
    return r['course_id'] if r else None


def chu_de_cua_lop(class_id):
    """Danh mục chủ đề hợp lệ cho một lớp: `lessons.module` của khoá lớp đang dạy.

    VÌ SAO KHÔNG ĐỂ GÕ TỰ DO. Bản đầu của mô-đun này nhận `topic` là văn bản
    120 ký tự bất kỳ. Nhưng bản đồ năng lực của HỌC VIÊN
    (`stats/competency.py`) dựng ô từ `lessons.module`, còn bản đồ của GIẢNG VIÊN
    (`teaching/reports.py`) dựng ô từ chính `topic` của sự kiện — hai nguồn khác
    nhau, trước nay luôn khớp vì `topic` do hệ thống sinh ra.

    Đo 31/08/2026: giao hai bài gắn chủ đề "Doc hieu" (thiếu dấu) rồi hai bài
    "Đọc hiểu" (đúng dấu) → bản đồ của giảng viên hiện HAI ô cho cùng một chủ
    đề (16% và 49%), còn bản đồ của em thì không có ô nào. Một dấu tiếng Việt
    gõ thiếu là đủ — và không màn hình nào báo gì.

    Nên chọn từ danh mục chứ không gõ. Để trống vẫn được (điểm vào sổ, không vào
    bản đồ) — nhưng đã gắn thì phải gắn vào một ô có thật.
    """
    return [r['module'] for r in q(
        """SELECT DISTINCT l.module
             FROM lessons l JOIN classes c ON c.course_id = l.course_id
             WHERE c.id = %s AND l.module IS NOT NULL AND l.module <> ''
             ORDER BY l.module""", (class_id,))]


#: Trần của `NUMERIC(6,2)` ở §38. Vượt trần là Postgres ném, mà lỗi CSDL thì
#: thành 500 — một mã báo "lỗi của chúng tôi" cho thứ thật ra là gõ nhầm.
DIEM_MIN = Decimal('0.01')
DIEM_MAX = Decimal('9999.99')


def _so(raw):
    """Chuỗi/số → Decimal HỮU HẠN, hoặc None. Không bao giờ ném.

    `Decimal('NaN')` và `Decimal('Infinity')` là Decimal HỢP LỆ — chúng đi lọt
    qua `try` rồi mới nổ ở tầng CSDL thành 500. Đo 31/08/2026: `max_score` nhận
    'NaN', 'Infinity', '1e30', '9999.999' và '0.001' đều ra 500 kèm
    `CheckViolation`/`numeric field overflow` trong log. Chặn ngay ở đây.
    """
    if raw in (None, ''):
        return None
    try:
        v = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return v if v.is_finite() else None


def _clean(body, class_id):
    """Body → (dict cột CSDL, lỗi). Chỉ lấy trường thật sự được gửi.

    Dùng chung cho POST và PATCH: hai đường kiểm riêng thì sớm muộn tạo được thứ
    mà sửa lại không được.
    """
    data = {}
    for field, limit in TEXT_FIELDS.items():
        if field in body:
            # Tiêu đề rỗng phải chặn Ở ĐÂY, không phải ở riêng đường tạo.
            # `title TEXT NOT NULL` (§38), nên PATCH với "   " biến thành None,
            # lọt qua `if not data` (dict khác rỗng!) rồi nổ IntegrityError →
            # 500. Đúng cái bẫy docstring hàm này cảnh báo: "hai đường kiểm
            # riêng thì sớm muộn tạo được thứ mà sửa lại không được".
            if field == 'title':
                tieu_de = body[field]
                if tieu_de is None or not str(tieu_de).strip():
                    return None, 'Bài tập phải có tiêu đề.'
            # `body[field] is not None` PHẢI kiểm trước — thiếu vế đó thì
            # `str(None)` ra chuỗi "None", truthy, và đi thẳng vào CSDL. Đã trả
            # giá cho lỗi này ở `terms.py` và `views.py` ngày 31/08/2026.
            raw = body[field]
            val = (str(raw).strip() or None) if raw is not None else None
            data[field] = val[:limit] if val else None

    if 'topic' in body:
        raw = body['topic']
        tp = (str(raw).strip() or None) if raw is not None else None
        if tp is not None:
            hop_le = chu_de_cua_lop(class_id)
            if tp not in hop_le:
                return None, ('Chủ đề phải chọn từ danh mục của khoá lớp đang học. '
                              'Hợp lệ: %s. Để trống nếu bài này không thuộc chủ đề nào.'
                              % (', '.join(hop_le) or '(khoá này chưa chia chủ đề)'))
            # GẮN KHOÁ THEO LỚP, KHÔNG CHỜ MÀN HÌNH GỬI.
            #
            # Đây là chỗ đã làm hỏng lời hứa trung tâm của cả mô-đun. Bản đồ
            # năng lực khoá ô theo CẶP `(course_id, topic)` — xem
            # `stats/competency.py:134`, và `_CATALOG_SQL` còn đòi
            # `l.course_id IS NOT NULL`. Màn hình thì không gửi `course_id` (rà
            # cả thư mục bài tập: 0 kết quả), nên mọi bài giao qua giao diện có
            # `course_id = NULL`, sự kiện rơi vào ô `(None, 'Số học')` — một ô
            # KHÔNG TỒN TẠI. Đo 31/08/2026: chấm 9/10 xong, ô "Số học" của em
            # không đổi một chữ; còn bản đồ của giảng viên mọc thêm một ô "Số
            # học" thứ hai. Đúng cái "hai bản đồ" mà `chu_de_cua_lop` vừa tuyên
            # bố đã bịt.
            #
            # `topic` ĐÃ được ràng vào `lessons.module` của khoá lớp, nên khoá
            # suy ra được từ chính lớp — không có gì để người dùng chọn, và
            # cũng không có gì để họ chọn sai.
            data['course_id'] = khoa_cua_lop(class_id)
        else:
            # Bỏ chủ đề thì bỏ luôn khoá: một sự kiện mang khoá mà không mang
            # chủ đề vẫn không vào được ô nào, chỉ tốn thêm một cột trông như
            # có nghĩa.
            data['course_id'] = None
        data['topic'] = tp

    # `course_id` KHÔNG nhận từ bên ngoài. Nó SUY RA từ lớp (xem nhánh `topic`
    # ngay trên), nên không có gì để người dùng chọn — và cũng không có gì để
    # họ chọn mâu thuẫn với chủ đề. Bản đầu vừa nhận từ body vừa suy ra, tức
    # một thân request khéo tay đặt được `topic` của khoá A với `course_id` của
    # khoá B, và cái ô sinh ra không thuộc về ai.

    if 'due_at' in body:
        raw = body['due_at']
        if raw in (None, ''):
            data['due_at'] = None
        else:
            from teaching.sessions import _parse_starts_at
            dt = _parse_starts_at(raw)
            if dt is None:
                return None, ('Hạn nộp phải theo ISO 8601, ví dụ "2026-09-08T23:59".')
            data['due_at'] = dt

    if 'max_score' in body:
        v = _so(body['max_score'])
        # `NUMERIC(6,2)` LÀM TRÒN trước khi kiểm ràng buộc, nên 0.001 thành 0.00
        # rồi mới đụng CHECK `max_score > 0`. Kiểm trần ở đây bằng đúng con số
        # của cột, không để CSDL nói hộ bằng một mã 500.
        if v is None or v < DIEM_MIN or v > DIEM_MAX:
            return None, ('Thang điểm phải là số trong khoảng %s–%s.'
                          % (DIEM_MIN, DIEM_MAX))
        data['max_score'] = v

    if 'status' in body:
        st = str(body['status'] or '').strip()
        if st not in ASSIGNMENT_STATUS:
            return None, ('Trạng thái bài tập phải là một trong: %s.'
                          % ', '.join(ASSIGNMENT_STATUS))
        data['status'] = st

    return data, None


def _dict(r):
    """Một bài tập ở dạng JSON. camelCase cho khớp phần còn lại của teaching/."""
    out = {
        'id': r['id'], 'classId': r['class_id'], 'title': r['title'],
        'description': r['description'], 'topic': r['topic'],
        'courseId': r['course_id'], 'status': r['status'],
        'dueAt': r['due_at'].isoformat() if r.get('due_at') else None,
        'maxScore': float(r['max_score']) if r.get('max_score') is not None else None,
        'attachmentUrl': r['attachment_url'],
        'createdAt': r['created_at'].isoformat() if r.get('created_at') else None,
    }
    for k in ('submitted', 'graded', 'members'):
        if k in r:
            out[k] = r[k] or 0
    # Con số giảng viên hỏi mỗi tối: "còn mấy bài chưa chấm".
    #
    # Đếm bằng MỘT phép đếm riêng, KHÔNG lấy `submitted - graded`. Hai tập ấy
    # không lồng nhau: chấm điểm cố ý không đụng `submitted_at` (giảng viên chấm
    # bài nộp trên giấy), nên 5 em nộp online (3 đã chấm) + 2 em chấm giấy ra
    # `submitted=5, graded=5` → hiệu bằng 0, trong khi còn đúng 2 bài chưa chấm.
    # Một con số nói "đã chấm hết" khi chưa chấm hết là con số tệ hơn không có.
    if 'ungraded' in r:
        out['ungraded'] = r['ungraded'] or 0
    return out


def _load(request, assignment_id):
    """Bài tập + tên lớp, đã kiểm quyền xem lớp. None nếu không được xem.

    Trả 404 chứ không 403 cho lớp không phụ trách — cùng quy ước với cả module
    `teaching/`: 403 là tự thú nhận "lớp đó có tồn tại".
    """
    row = q1('''SELECT a.*, c.name AS class_name, c.code AS class_code
                FROM assignments a JOIN classes c ON c.id = a.class_id
                WHERE a.id = %s''', (assignment_id,))
    if not row or not can_see_class(request.user, row['class_id']):
        return None
    return row


# ── 1. Danh sách & tạo ──────────────────────────────────────────────────────

class ClassAssignmentsView(APIView):
    """GET/POST /api/teach/classes/<class_id>/assignments."""
    permission_classes = [IsTeacherOrAdmin]

    def get(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)

        # MỘT câu cho cả danh sách, kèm hai con số đếm. Gọi thêm một câu cho mỗi
        # bài là đúng cái N+1 mà module này cấm — một lớp 20 bài là 40 lượt Neon.
        # Ba phép đếm PHẢI cùng phạm vi với `si_so` ngay dưới và với bảng chấm
        # (`AssignmentGradingView.get`) — cả hai chỗ đó lọc `left_at IS NULL`.
        # Không lọc ở đây thì bài của em đã rời lớp vẫn được cộng, ra những con
        # số như "36/35 đã nộp · còn 1 bài chưa chấm" — một huy hiệu vàng KHÔNG
        # BAO GIỜ TẮT và không có ô nào để bấm, vì bảng chấm đã giấu em ấy đi.
        # Sau vài ngày giảng viên học cách bỏ qua nó, và bỏ qua luôn những bài
        # chưa chấm THẬT. Phân số 36/35 còn tự tố cáo là số liệu hỏng.
        rows = q('''SELECT a.*,
                           COUNT(s.user_id) FILTER (WHERE s.submitted_at IS NOT NULL) AS submitted,
                           COUNT(s.user_id) FILTER (WHERE s.graded_at IS NOT NULL)    AS graded,
                           COUNT(s.user_id) FILTER (WHERE s.submitted_at IS NOT NULL
                                                     AND s.graded_at IS NULL)         AS ungraded
                    FROM assignments a
                    LEFT JOIN submissions s
                           ON s.assignment_id = a.id
                          AND s.user_id IN (SELECT m.user_id FROM class_members m
                                            JOIN users u ON u.id = m.user_id
                                            WHERE m.class_id = a.class_id
                                              AND m.left_at IS NULL
                                              AND ''' + chi_hoc_vien('u') + ''')
                    WHERE a.class_id = %s
                    GROUP BY a.id
                    ORDER BY a.due_at DESC NULLS LAST, a.id DESC''', (class_id,))
        si_so = q1('''SELECT COUNT(*) AS n FROM class_members m
                      JOIN users u ON u.id = m.user_id
                      WHERE m.class_id = %s AND m.left_at IS NULL
                        AND ''' + chi_hoc_vien('u'), (class_id,))['n']
        return Response({
            'assignments': [dict(_dict(r), members=si_so) for r in rows],
            'statuses': list(ASSIGNMENT_STATUS),
            # Danh mục chủ đề gửi kèm để màn hình vẽ ô CHỬN thay vì ô gõ — xem
            # `chu_de_cua_lop`. Gửi từ máy chủ chứ không viết cứng ở màn hình: danh
            # mục này đổi theo giáo trình, mà giáo trình thì TopHSA sẽ soạn lại.
            'topics': chu_de_cua_lop(class_id),
        })

    def post(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        body = request.data if isinstance(request.data, dict) else {}
        data, err = _clean(body, class_id)
        if err:
            return Response({'error': err}, status=400)
        if not data.get('title'):
            return Response({'error': 'Bài tập phải có tiêu đề.'}, status=400)

        data['class_id'] = class_id
        data['created_by'] = request.user.id
        data.setdefault('created_at', local_now())
        cols = list(data)
        row = q1('INSERT INTO assignments (%s) VALUES (%s) RETURNING id'
                 % (', '.join(cols), ', '.join(['%s'] * len(cols))),
                 tuple(data[c] for c in cols))

        audit.record(request, audit.ASSIGNMENT_CREATE, target_type='assignment',
                     target_id=row['id'], target_label=data['title'],
                     summary='Giao bài "%s" cho lớp.' % data['title'],
                     detail={'classId': class_id, 'topic': data.get('topic'),
                             'maxScore': str(data.get('max_score') or '')})
        return Response({'ok': True, 'id': row['id']}, status=201)


# ── 2. Sửa & xoá ────────────────────────────────────────────────────────────

class AssignmentDetailView(APIView):
    """PATCH/DELETE /api/teach/assignments/<id>."""
    permission_classes = [IsTeacherOrAdmin]

    def patch(self, request, assignment_id):
        before = _load(request, assignment_id)
        if not before:
            return Response(_NOT_FOUND, status=404)
        body = request.data if isinstance(request.data, dict) else {}
        data, err = _clean(body, before['class_id'])
        if err:
            return Response({'error': err}, status=400)
        if not data:
            return Response({'error': 'Không có trường hợp lệ để cập nhật.'}, status=400)

        data['updated_at'] = local_now()
        cols = list(data)
        x('UPDATE assignments SET %s WHERE id=%%s' % ', '.join('%s=%%s' % c for c in cols),
          tuple(data[c] for c in cols) + (assignment_id,))

        canh_bao = None
        # Đổi thang điểm SAU khi đã chấm là đổi ý nghĩa của mọi điểm đã cho.
        # Không chặn — giảng viên có quyền sửa nhầm — nhưng phải nói ra, vì
        # phần trăm đã ghi vào `learning_events` KHÔNG tự tính lại.
        if 'max_score' in data:
            da_cham = q1('SELECT COUNT(*) AS n FROM submissions '
                         'WHERE assignment_id=%s AND graded_at IS NOT NULL',
                         (assignment_id,))['n']
            if da_cham:
                canh_bao = ('Đã chấm %d bài theo thang cũ. Điểm phần trăm của những bài đó '
                            'KHÔNG tự tính lại — chấm lại từng bài nếu muốn cập nhật.' % da_cham)

        audit.record(request, audit.ASSIGNMENT_UPDATE, target_type='assignment',
                     target_id=assignment_id,
                     target_label=data.get('title') or before['title'],
                     summary='Sửa bài tập "%s".' % (data.get('title') or before['title']),
                     detail={k: (v.isoformat() if hasattr(v, 'isoformat') else str(v))
                             for k, v in data.items()})
        after = _load(request, assignment_id)
        out = {'ok': True, 'assignment': _dict(after)}
        if canh_bao:
            out['warning'] = canh_bao
        return Response(out)

    def delete(self, request, assignment_id):
        before = _load(request, assignment_id)
        if not before:
            return Response(_NOT_FOUND, status=404)

        n = q1('SELECT COUNT(*) AS n FROM submissions WHERE assignment_id=%s '
               'AND submitted_at IS NOT NULL', (assignment_id,))['n']
        confirm = str(request.query_params.get('confirm') or '').strip().lower() \
            in ('1', 'true', 'yes')
        if n and not confirm:
            # 409 chứ không 400: yêu cầu hợp lệ, chỉ đang xung đột với dữ liệu.
            # Xoá bài tập là xoá luôn BÀI LÀM của học viên — thứ các em bỏ công
            # viết ra và không có bản nào khác.
            return Response({
                'error': ('Bài này đã có %d học viên nộp. Xoá là mất luôn bài làm của các '
                          'em — không khôi phục được. Gửi lại kèm ?confirm=1 nếu vẫn muốn '
                          'xoá; muốn dừng nhận bài thì đổi trạng thái sang "closed".' % n),
                'submissions': n, 'needsConfirm': True,
            }, status=409)

        x('DELETE FROM assignments WHERE id=%s', (assignment_id,))
        # Dọn sự kiện học tập của bài vừa xoá — cùng lý do với đường xoá buổi
        # học: để lại thì điểm của một bài không còn tồn tại vẫn nằm trong bản
        # đồ năng lực và sổ điểm của em.
        quen = forget_events('assignment', assignment_id)

        audit.record(request, audit.ASSIGNMENT_DELETE, target_type='assignment',
                     target_id=assignment_id, target_label=before['title'],
                     summary='Xoá bài tập "%s" — mất theo %d bài đã nộp.'
                             % (before['title'], n),
                     detail={'classId': before['class_id'], 'submissions': n,
                             'forgottenEvents': quen, 'confirmed': confirm})
        return Response({'ok': True, 'deletedSubmissions': n, 'forgottenEvents': quen})


# ── 3. Bảng chấm ────────────────────────────────────────────────────────────

class AssignmentGradingView(APIView):
    """GET/POST /api/teach/assignments/<id>/submissions — bảng chấm cả lớp.

    GET trả về MỌI học viên đang học, kể cả em chưa nộp — cùng lý do với bảng
    điểm danh: giảng viên mở ra phải thấy ngay cả lớp, không phải tự đối chiếu
    hai danh sách trong đầu để biết ai còn thiếu.
    """
    permission_classes = [IsTeacherOrAdmin]

    def get(self, request, assignment_id):
        row = _load(request, assignment_id)
        if not row:
            return Response(_NOT_FOUND, status=404)

        hs = q('''SELECT m.user_id, u.name, u.email,
                         s.submitted_at, s.content, s.file_url, s.score, s.feedback,
                         s.graded_at, gb.name AS graded_by_name
                  FROM class_members m
                  JOIN users u ON u.id = m.user_id
                  LEFT JOIN submissions s
                         ON s.assignment_id = %s AND s.user_id = m.user_id
                  LEFT JOIN users gb ON gb.id = s.graded_by
                  WHERE m.class_id = %s AND m.left_at IS NULL
                    AND ''' + chi_hoc_vien('u') + '''
                  ORDER BY u.name, m.user_id''', (assignment_id, row['class_id']))

        thang = float(row['max_score'])
        return Response({
            'assignment': _dict(row),
            'className': row['class_name'],
            'students': [{
                'userId': r['user_id'], 'name': r['name'], 'email': r['email'],
                'submittedAt': r['submitted_at'].isoformat() if r['submitted_at'] else None,
                'content': r['content'], 'fileUrl': r['file_url'],
                'score': float(r['score']) if r['score'] is not None else None,
                # Phần trăm tính SẴN ở đây để màn hình và sổ điểm không tự chia
                # lấy — hai chỗ chia là hai chỗ có thể làm tròn khác nhau.
                'scorePct': pct(r['score'], thang) if r['score'] is not None else None,
                'feedback': r['feedback'],
                'gradedAt': r['graded_at'].isoformat() if r['graded_at'] else None,
                'gradedByName': r['graded_by_name'],
            } for r in hs],
        })

    def post(self, request, assignment_id):
        row = _load(request, assignment_id)
        if not row:
            return Response(_NOT_FOUND, status=404)

        body = request.data if isinstance(request.data, dict) else {}
        grades = body.get('grades')
        if not isinstance(grades, list) or not grades:
            return Response({'error': 'Cần danh sách grades: '
                                      '[{"user_id": 12, "score": 8.5, "feedback": "..."}].'},
                            status=400)
        if len(grades) > MAX_GRADE_PER_BATCH:
            return Response({'error': 'Một lần chấm tối đa %d bài. Chia nhỏ ra.'
                                      % MAX_GRADE_PER_BATCH}, status=400)

        thang = Decimal(str(row['max_score']))
        members = {r['user_id'] for r in q(
            'SELECT m.user_id FROM class_members m JOIN users u ON u.id = m.user_id '
            'WHERE m.class_id = %s AND m.left_at IS NULL AND ' + chi_hoc_vien('u'),
            (row['class_id'],))}

        sach, bo_qua = {}, []
        for g in grades:
            if not isinstance(g, dict):
                return Response({'error': 'Mỗi phần tử của grades phải là một đối tượng.'},
                                status=400)
            try:
                uid = int(g.get('user_id'))
            except (TypeError, ValueError):
                return Response({'error': 'user_id phải là số.'}, status=400)
            if uid not in members:
                # Cùng cách xử lý với điểm danh: KHÔNG ghi bừa id lạ, và BÁO LẠI
                # để người gửi biết chứ không tưởng là đã lưu.
                bo_qua.append(uid)
                continue
            diem = _so(g.get('score'))
            if diem is None:
                return Response({'error': 'Điểm phải là số. Chưa chấm thì bỏ em đó ra '
                                          'khỏi danh sách gửi lên.'}, status=400)
            if diem < 0 or diem > thang:
                return Response({'error': 'Điểm phải trong khoảng 0–%s theo thang của bài này.'
                                          % thang}, status=400)
            # PHÂN BIỆT "không gửi trường" với "gửi chuỗi rỗng".
            #
            # Bản đầu gộp cả hai thành `None` rồi dựa vào
            # `COALESCE(EXCLUDED.feedback, submissions.feedback)` để giữ nhận
            # xét cũ — hệ quả: nhận xét gõ nhầm KHÔNG XOÁ ĐƯỢC. Trong một bảng
            # 35 dòng thì gõ nhầm ô là chuyện thường, và học viên đọc lời nhận
            # xét dành cho bạn khác trên màn hình của mình.
            if 'feedback' in g:
                nx = str(g.get('feedback') or '').strip()[:4000] or None
                doi_nx = True
            else:
                nx, doi_nx = None, False
            # Trùng user_id trong cùng mẻ: giữ dòng CUỐI. Bắt buộc — Postgres ném
            # "ON CONFLICT DO UPDATE command cannot affect row a second time".
            sach[uid] = {'user_id': uid, 'score': diem, 'feedback': nx,
                         'doi_nx': doi_nx}

        if not sach:
            return Response({'error': 'Không có học viên hợp lệ nào trong danh sách '
                                      '(không ai trong số đó đang học lớp này).',
                             'skipped': bo_qua}, status=400)

        rows = list(sach.values())
        now = local_now()

        # Nhận xét cuối cùng tính SẴN ở đây, không nhờ `COALESCE` ở SQL nói hộ.
        # Một câu INSERT chạy cho cả mẻ nên không thể mỗi dòng một luật; muốn
        # dòng này giữ nhận xét cũ còn dòng kia xoá nó thì phải quyết trong
        # Python rồi mới gửi xuống.
        cu = {r['user_id']: r['feedback'] for r in q(
            'SELECT user_id, feedback FROM submissions WHERE assignment_id=%s '
            'AND user_id = ANY(%s)', (assignment_id, [g['user_id'] for g in rows]))}
        for g in rows:
            if not g['doi_nx']:
                g['feedback'] = cu.get(g['user_id'])

        params = []
        for g in rows:
            params += [assignment_id, g['user_id'], g['score'], g['feedback'],
                       request.user.id, now]
        values = ', '.join(['(%s, %s, %s, %s, %s, %s)'] * len(rows))

        with transaction.atomic():
            # MỘT câu cho cả lớp, cùng lý do với điểm danh (T41).
            #
            # `submitted_at` KHÔNG bị đụng tới: chấm điểm không phải là nộp bài.
            # Giảng viên chấm một bài nộp trên giấy thì dòng vẫn phải ghi rõ là
            # em chưa nộp qua hệ thống — đó là hai sự kiện khác nhau.
            x('INSERT INTO submissions '
              '(assignment_id, user_id, score, feedback, graded_by, graded_at) '
              'VALUES ' + values +
              ' ON CONFLICT (assignment_id, user_id) DO UPDATE SET '
              '  score     = EXCLUDED.score,'
              # KHÔNG `COALESCE`: giá trị gửi xuống ĐÃ là giá trị cuối cùng
              # (xem chỗ dựng `cu` ở trên). COALESCE ở đây biến "xoá nhận xét"
              # thành "giữ nguyên nhận xét cũ", vĩnh viễn.
              '  feedback  = EXCLUDED.feedback,'
              '  graded_by = EXCLUDED.graded_by,'
              '  graded_at = EXCLUDED.graded_at', tuple(params))

        # Sự kiện học tập nằm NGOÀI khối atomic, có chủ đích — cùng lý do đã ghi
        # ở `sessions.py`: điểm đã chốt, sự kiện là việc ghi thêm.
        so_su_kien = self._emit(row, rows, now)

        label = row['title']
        summary = 'Chấm %d bài của "%s" (lớp %s).' % (len(rows), label, row['class_name'])
        # Điểm đã vào `submissions` nhưng KHÔNG vào được dòng sự kiện: sổ điểm
        # và bản đồ năng lực nói hai chuyện khác nhau, và không mặt nào báo gì —
        # màn hình vẫn hiện "đã chấm hết", nhật ký kiểm toán vẫn ghi thành công.
        # Vết duy nhất là một dòng log trên Render mà không ai đọc.
        #
        # Chấm lại chính là đường sửa (sự kiện quay lại), nhưng người ta chỉ
        # chấm lại nếu BIẾT là cần.
        thieu = len(rows) - so_su_kien
        if thieu > 0:
            logger.error('[assignments] bài %s: chấm %d nhưng chỉ ghi được %d sự kiện '
                         'học tập — điểm KHÔNG vào bản đồ năng lực của %d em',
                         assignment_id, len(rows), so_su_kien, thieu)
        audit.record(request, audit.ASSIGNMENT_GRADE, target_type='assignment',
                     target_id=assignment_id, target_label=label, summary=summary,
                     detail={'classId': row['class_id'], 'graded': len(rows),
                             'skipped': bo_qua, 'maxScore': str(thang)})
        ra = {'ok': True, 'graded': len(rows), 'events': so_su_kien,
              'skipped': bo_qua, 'summary': summary}
        if thieu > 0:
            ra['warning'] = ('Đã lưu %d điểm, nhưng %d điểm CHƯA vào được bản đồ năng '
                             'lực. Bấm Lưu lại để thử — điểm trong sổ vẫn đúng.'
                             % (len(rows), thieu))
        return Response(ra)

    @staticmethod
    def _emit(row, rows, now):
        """Mỗi bài đã chấm đẻ một ``learning_events`` (đặc tả ERP §5).

        Nhờ vậy điểm tự luận vào thẳng bản đồ năng lực và sổ điểm mà không phải
        viết lại phép tính nào — bản đồ đọc từ dòng sự kiện, không đọc từ bảng
        nguồn.

        `topic` và `course_id` lấy từ BÀI TẬP: đó là thứ quyết định điểm này rơi
        vào ô nào trên bản đồ. Bài chưa gắn chủ đề thì sự kiện vẫn ghi (vào sổ
        điểm) nhưng không vào được ô nào — và đó là lý do màn hình nhắc giảng
        viên gắn chủ đề khi tạo bài.
        """
        return record_events([{
            'uid': g['user_id'], 'kind': KIND_ASSIGNMENT,
            'dedup_key': 'assignment:%s' % row['id'],
            'occurred_at': now, 'event_date': now.date(),
            'course_id': row['course_id'], 'topic': row['topic'],
            'ref_type': 'assignment', 'ref_id': row['id'],
            'score': g['score'], 'max_score': row['max_score'],
            # CỐ Ý để `minutes=None`: thời gian em bỏ ra làm bài tự luận không ai
            # đo được, và bịa ra một con số sẽ trộn vào chỉ tiêu tuần.
            'minutes': None, 'xp': 0, 'source': SOURCE_SYSTEM,
            'meta': {'title': row['title'], 'classId': row['class_id']},
        } for g in rows])


# ── 4. Phía học viên ────────────────────────────────────────────────────────

class MyAssignmentsView(APIView):
    """GET/POST /api/assignments — bài tập của chính mình.

    Không nhận `user_id` từ bên ngoài, ở CẢ HAI phương thức: nó luôn là
    `request.user.id`. Một endpoint học viên mà nhận id người khác là cửa để đọc
    và ghi đè bài làm của bạn cùng lớp.

    ĐỌC không lọc `left_at`, GHI thì có. Bản đầu lọc `m.left_at IS NULL` ở cả
    hai, nên học xong khoá là mất sạch đường xem lại bài và nhận xét của thầy —
    đúng lúc cần nhất, vì em luyện thi HSA ôn lại trước ngày thi. Dữ liệu vẫn
    còn nguyên trong `submissions`, chỉ mất đường vào. Trái với chính nguyên tắc
    §29 ("giữ `left_at` thay vì xoá dòng: học viên nghỉ giữa chừng vẫn phải còn
    trong báo cáo"). Hàng rào ở đường NỘP thì giữ nguyên: đã rời lớp thì không
    nộp thêm được.
    """

    def get(self, request):
        uid = request.user.id
        rows = q('''SELECT a.*, c.name AS class_name,
                           s.submitted_at, s.content, s.score, s.feedback, s.graded_at
                    FROM assignments a
                    JOIN classes c ON c.id = a.class_id
                    JOIN class_members m ON m.class_id = a.class_id AND m.user_id = %s
                    LEFT JOIN submissions s ON s.assignment_id = a.id AND s.user_id = %s
                    WHERE a.status <> 'draft'
                    ORDER BY a.due_at NULLS LAST, a.id DESC''', (uid, uid))
        return Response({'assignments': [dict(
            _dict(r), className=r['class_name'],
            submittedAt=r['submitted_at'].isoformat() if r['submitted_at'] else None,
            content=r['content'],
            score=float(r['score']) if r['score'] is not None else None,
            scorePct=(pct(r['score'], r['max_score']) if r['score'] is not None else None),
            feedback=r['feedback'],
            gradedAt=r['graded_at'].isoformat() if r['graded_at'] else None,
        ) for r in rows]})

    def post(self, request):
        uid = request.user.id
        body = request.data if isinstance(request.data, dict) else {}
        try:
            aid = int(body.get('assignment_id'))
        except (TypeError, ValueError):
            return Response({'error': 'Thiếu assignment_id.'}, status=400)

        bai = q1('''SELECT a.id, a.status, a.title FROM assignments a
                    JOIN class_members m ON m.class_id = a.class_id
                                        AND m.user_id = %s AND m.left_at IS NULL
                    WHERE a.id = %s''', (uid, aid))
        if not bai:
            return Response({'error': 'Không tìm thấy bài tập này trong lớp của bạn.'},
                            status=404)
        if bai['status'] != 'open':
            return Response({'error': 'Bài này đã đóng, không nhận bài nộp nữa. '
                                      'Liên hệ giảng viên nếu bạn nộp muộn có lý do.'},
                            status=409)

        noi_dung = str(body.get('content') or '').strip()[:20000] or None
        if not noi_dung:
            return Response({'error': 'Bài nộp không được để trống.'}, status=400)

        # Nộp lại là SỬA bài nộp cũ, không đẻ dòng mới (khoá chính §38).
        #
        # Nộp lại XOÁ điểm đã chấm — có chủ đích và phải nói rõ ở giao diện: một
        # điểm chấm cho bản cũ mà treo trên bản mới là con số nói dối. Giảng
        # viên chấm lại thì `graded_at` mới có giá trị.
        x('''INSERT INTO submissions (assignment_id, user_id, submitted_at, content)
             VALUES (%s, %s, %s, %s)
             ON CONFLICT (assignment_id, user_id) DO UPDATE SET
                 submitted_at = EXCLUDED.submitted_at,
                 content      = EXCLUDED.content,
                 score        = NULL,
                 graded_by    = NULL,
                 graded_at    = NULL''',
          (aid, uid, local_now(), noi_dung))
        # Điểm cũ đã bị xoá thì sự kiện học tập tương ứng cũng phải đi theo,
        # nếu không bản đồ năng lực vẫn giữ điểm của một bản bài đã bị thay.
        #
        # XOÁ THEO (user_id, dedup_key), KHÔNG theo ref_type/ref_id. Dạng thứ
        # hai xoá MỌI sự kiện trỏ về bài tập này — tức một em nộp lại sẽ thổi
        # bay điểm đã chấm của cả lớp. Đây là lý do `forget_events` cố tình có
        # hai dạng khoá: một dạng cho "đối tượng biến mất", một dạng cho "một
        # người, một bản ghi".
        forget_events(user_id=uid, dedup_key='assignment:%s' % aid)
        return Response({'ok': True, 'note': 'Đã nộp. Nộp lại sẽ xoá điểm cũ và '
                                             'giảng viên phải chấm lại từ đầu.'})
