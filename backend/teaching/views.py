"""API khu vực giảng dạy + quản lý lớp.

Quyền theo NGỮ CẢNH, không theo vai trò: vào được khu vực này (giảng viên hoặc
quản trị viên) không có nghĩa là xem được mọi lớp. Mỗi endpoint chạm vào một lớp
cụ thể đều phải đi qua ``can_see_class`` — xem common/permissions.py.
"""
import logging

from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import invalidate_user_cache
from accounts.validators import validate_email_field, validate_name_field, validate_phone_field
from common import audit
from common.clock import local_now
from common.db import q, q1, x
from common.events import forget_events
from common.identity import norm_email, norm_phone
from common.params import kiem_lien_ket
from common.permissions import (
    ASSIGNABLE_ROLES,
    ROLE_ADMIN,
    ROLE_STUDENT,
    IsAdminOrAcademic,
    IsAdminRole,
    IsTeachingStaff,
    can_see_class,
    is_admin,
    last_active_admin,
    visible_class_ids,
)
from stats import competency, gradebook, journal, plan
from stats.goals import read_goals
from teaching import reports
from teaching.vocab import LEAVE_LABEL, LEAVE_REASONS, chi_hoc_vien

logger = logging.getLogger(__name__)

#: Trạng thái lớp hợp lệ.
CLASS_STATUS = ('draft', 'active', 'finished')
#: Trường được sửa qua API quản trị lớp, kèm độ dài tối đa cho trường chữ.
CLASS_TEXT_FIELDS = {
    'code': 40, 'name': 160, 'schedule': 160, 'meeting_url': 400, 'note': 1000,
}
CLASS_DATE_FIELDS = ('starts_on', 'ends_on', 'exam_date')


class TeachClassesView(APIView):
    """GET /api/teach/classes — lớp tôi phụ trách (quản trị viên thấy tất cả)."""
    permission_classes = [IsTeachingStaff]

    def get(self, request):
        ids = visible_class_ids(request.user)
        return Response({
            'classes': reports.class_list(ids),
            'isAdmin': is_admin(request.user),
        })


class TeachClassDetailView(APIView):
    """GET /api/teach/classes/<id> — báo cáo đầy đủ một lớp."""
    permission_classes = [IsTeachingStaff]

    def get(self, request, class_id):
        if not can_see_class(request.user, class_id):
            # 404 chứ không 403: không tiết lộ lớp đó có tồn tại hay không.
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        data = reports.class_report(class_id)
        if data is None:
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        return Response(data)


class TeachStudentView(APIView):
    """GET /api/teach/classes/<id>/students/<uid> — hồ sơ một học viên.

    Dùng lại đúng các phép tính học viên tự thấy (bản đồ năng lực, sổ điểm,
    kế hoạch, mục tiêu tuần). Giảng viên và học viên phải nhìn CÙNG một con số:
    hai bên thấy hai số khác nhau cho cùng một chủ đề là hỏng cả buổi tư vấn.
    """
    permission_classes = [IsTeachingStaff]

    def get(self, request, class_id, user_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        # `chi_hoc_vien` BẮT BUỘC ở đây, không chỉ ở báo cáo phụ huynh.
        #
        # Đo 31/08/2026: tài khoản quản trị viên đang là thành viên lớp 1 (anh
        # chốt giữ). Thiếu bộ lọc này thì giảng viên phụ trách lớp đọc được hồ
        # sơ ĐẦY ĐỦ của tài khoản ấy — email, số điện thoại, mục tiêu, sổ điểm,
        # và NHẬT KÝ TỰ GHI. HTTP 200, trả admin@pe-hsa.vn. `parent_report.py`
        # đã chặn đúng cảnh này; đường này — trả về NHIỀU HƠN — thì quên.
        #
        # Không phải chuyện riêng của tài khoản quản trị: lỗ hổng đúng cho MỌI
        # tài khoản không-học-viên tình cờ nằm trong danh sách lớp, kể cả một
        # giảng viên khác được thêm vào để dự giờ.
        member = q1('''SELECT 1 FROM class_members m
                       JOIN users u ON u.id = m.user_id
                       WHERE m.class_id = %s AND m.user_id = %s
                         AND ''' + chi_hoc_vien('u'), (class_id, user_id))
        if not member:
            return Response({'error': 'Học viên không thuộc lớp này.'}, status=404)
        user = q1('SELECT id, name, email, phone, streak, xp, created_at '
                  'FROM users WHERE id=%s', (user_id,))
        return Response({
            'user': {
                'id': user['id'], 'name': user['name'], 'email': user['email'],
                'phone': user['phone'], 'streak': user['streak'] or 0,
                'xp': user['xp'] or 0,
            },
            'goals': read_goals(user_id),
            'competency': competency.compute(user_id),
            'gradebook': gradebook.gradebook(user_id, 20),
            'curve': gradebook.progress_curve(user_id, 12),
            'week': journal.week_progress(user_id, journal.read_target(user_id)),
            'plan': plan.read(user_id, weeks=2),
            # Nhật ký học viên tự ghi: đây là dữ liệu RIÊNG TƯ theo nghĩa khác
            # với điểm số — giảng viên xem được vì để tư vấn, nhưng học viên
            # phải biết điều đó. Xem đặc tả ERP mục "Quyền riêng tư".
            'journal': journal.recent_logs(user_id, 14),
        })


# ── Quản trị lớp (chỉ quản trị viên) ────────────────────────────────────────

def _user_label(row, fallback_id=None):
    """Tên người dùng để chép vào nhật ký kiểm toán.

    Tài khoản chưa kịp điền tên thì lấy email, cùng lắm là ``#12``. Một dòng
    nhật ký ghi 'đã khoá tài khoản None' là một dòng vô dụng, mà nhật ký chỉ
    được đọc đúng vào lúc người ta cần biết chuyện gì đã xảy ra.
    """
    if row:
        return row.get('name') or row.get('email') or ('#%s' % row.get('id'))
    return '#%s' % fallback_id


def _audit_detail(data):
    """Đưa payload lớp về dạng JSON ghi được vào nhật ký.

    ``json.dumps`` không nuốt được ``date``, và ``common/audit.py`` bắt luôn
    ``TypeError`` rồi bỏ dòng nhật ký đó — tức là ngày khai giảng lọt vào
    payload là mất TRỌN dòng kiểm toán chứ không phải mất mỗi trường ngày, mà
    lại mất im lặng (chỉ còn vết trong log ứng dụng).
    """
    return {k: (v.isoformat() if hasattr(v, 'isoformat') else v)
            for k, v in data.items()}


def _clean_class_payload(body):
    data, err = {}, None
    for field, limit in CLASS_TEXT_FIELDS.items():
        if field in body:
            # `body[field] is not None` PHẢI kiểm trước. Thiếu vế đó thì
            # `str(None)` ra chuỗi "None" — bốn ký tự, truthy — và nó đi thẳng
            # vào CSDL. Giao diện gửi `code: code.trim() || null` cho ô để
            # trống, nên đây không phải trường hợp hiếm mà là đường đi THƯỜNG
            # NHẤT. Đo 31/08/2026: tạo hai đợt học đều bỏ trống mã thì cái thứ
            # hai bị chặn bằng câu 'Mã đợt "None" đã có rồi.'
            # Và `PATCH {note: null}` KHÔNG xoá được ghi chú mà ghi đè thành
            # chữ "None".
            val = (str(body[field]).strip() or None) if body[field] is not None else None
            data[field] = val[:limit] if val else None
    # Lược đồ của `meeting_url` phải nằm trong danh sách trắng.
    #
    # Đo 31/08/2026: hiện KHÔNG khai thác được — nơi duy nhất đổ nó vào `href`
    # có `target="_blank"`, và Chromium CHẶN điều hướng `javascript:` khi mở tab
    # mới. Bỏ `target` ra thì chạy. Tức hàng rào duy nhất đang giữ chỗ này là
    # một thuộc tính đặt vào vì lý do KHÁC HẲN (mở link họp ở tab mới), và ai
    # bỏ nó đi để sửa một chuyện về bố cục sẽ mở lại lỗ này mà không hề biết.
    #
    # Chặn ở ĐẦU VÀO chứ không ở chỗ hiển thị: chỗ hiển thị có thể mọc thêm
    # (bản in, email nhắc lịch, ứng dụng di động), còn đường ghi thì chỉ có đây.
    loi_link = kiem_lien_ket(data.get('meeting_url'), 'Link họp')
    if loi_link:
        return None, loi_link
    for field in CLASS_DATE_FIELDS:
        if field in body:
            from stats.goals import as_date
            raw = body[field]
            if raw in (None, ''):
                data[field] = None
            else:
                d = as_date(raw)
                if not d:
                    return None, 'Ngày "%s" không hợp lệ (định dạng YYYY-MM-DD).' % field
                data[field] = d
    if 'course_id' in body:
        cid = (body['course_id'] or '').strip() or None
        if cid and not q1('SELECT 1 FROM courses WHERE id=%s', (cid,)):
            return None, 'Không có khoá học này.'
        data['course_id'] = cid
    if 'teacher_id' in body:
        tid = body['teacher_id']
        if tid in (None, '', 0):
            data['teacher_id'] = None
        else:
            row = q1('SELECT role FROM users WHERE id=%s', (tid,))
            if not row:
                return None, 'Không có tài khoản này.'
            if row['role'] not in ('Giảng viên', 'admin'):
                return None, 'Tài khoản này chưa có vai trò Giảng viên.'
            data['teacher_id'] = int(tid)
    if 'term_id' in body:
        # Cho phép NULL: lớp đã có từ trước khi bảng `terms` ra đời chưa thuộc
        # đợt nào, và ép chúng vào một đợt bịa ra thì con số của đợt đó sai ngay
        # từ đầu (§36).
        tid = body['term_id']
        if tid in (None, '', 0):
            data['term_id'] = None
        else:
            try:
                tid = int(tid)
            except (TypeError, ValueError):
                return None, 'Mã đợt học không hợp lệ.'
            if not q1('SELECT 1 FROM terms WHERE id=%s', (tid,)):
                return None, 'Không có đợt học này.'
            data['term_id'] = tid
    if 'capacity' in body:
        try:
            data['capacity'] = max(0, min(500, int(body['capacity'] or 0))) or None
        except (TypeError, ValueError):
            return None, 'Sĩ số phải là một số nguyên.'
    if 'status' in body:
        # `str(...)` trước khi `.strip()`: gửi `{"status": 5}` thì
        # `(5 or '').strip()` ném AttributeError, và DRF biến nó thành 500
        # "Lỗi máy chủ nội bộ" — một dữ liệu vào sai lại hiện ra như hệ thống
        # hỏng. Dữ liệu vào sai phải là 400 kèm câu chữ đọc được.
        st = str(body['status'] or '').strip()
        if st not in CLASS_STATUS:
            return None, 'Trạng thái phải là một trong: %s.' % ', '.join(CLASS_STATUS)
        data['status'] = st
    return data, err


class AdminClassesView(APIView):
    """GET/POST /api/admin/classes — danh sách & tạo lớp."""
    # `IsAdminOrAcademic`: quản lý học vụ xếp lớp và đợt học là việc HÀNG NGÀY
    # của họ. Đổi vai trò và đặt lại mật khẩu thì KHÔNG — hai việc ấy vẫn
    # `IsAdminRole` (anh Sơn chốt 01/09/2026).
    permission_classes = [IsAdminOrAcademic]

    def get(self, request):
        return Response({
            'classes': reports.class_list(visible_class_ids(request.user)),
            'teachers': [dict(r) for r in _teachers()],
            'statuses': list(CLASS_STATUS),
        })

    def post(self, request):
        body = request.data if isinstance(request.data, dict) else {}
        data, err = _clean_class_payload(body)
        if err:
            return Response({'error': err}, status=400)
        if not data.get('name'):
            return Response({'error': 'Lớp phải có tên.'}, status=400)
        cols = list(data) + ['created_at']
        vals = list(data.values()) + [local_now()]
        row = q1('INSERT INTO classes (%s) VALUES (%s) RETURNING id'
                 % (', '.join(cols), ', '.join(['%s'] * len(vals))), tuple(vals))
        audit.record(request, audit.CLASS_CREATE, target_type='class',
                     target_id=row['id'], target_label=data['name'],
                     summary='Tạo lớp "%s"%s.' % (data['name'],
                                                  ' (mã %s)' % data['code']
                                                  if data.get('code') else ''),
                     detail=_audit_detail(data))
        return Response({'ok': True, 'id': row['id']}, status=201)


def _teachers():
    from common.db import q
    return q("SELECT id, name, email FROM users WHERE role IN ('Giảng viên','admin') "
             "ORDER BY name")


class AdminClassDetailView(APIView):
    """PUT/DELETE /api/admin/classes/<id> — sửa hoặc xoá lớp."""
    # `IsAdminOrAcademic`: quản lý học vụ xếp lớp và đợt học là việc HÀNG NGÀY
    # của họ. Đổi vai trò và đặt lại mật khẩu thì KHÔNG — hai việc ấy vẫn
    # `IsAdminRole` (anh Sơn chốt 01/09/2026).
    permission_classes = [IsAdminOrAcademic]

    def put(self, request, class_id):
        # Lấy luôn tên hiện tại (thay cho `SELECT 1`) để nhật ký chép được nhãn
        # TẠI THỜI ĐIỂM SỬA. Đọc lại tên lúc xem nhật ký thì thấy tên MỚI, và
        # dòng "đổi tên lớp X" sẽ tự mâu thuẫn với chính nó.
        before = q1('SELECT id, code, name FROM classes WHERE id=%s', (class_id,))
        if not before:
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        body = request.data if isinstance(request.data, dict) else {}
        data, err = _clean_class_payload(body)
        if err:
            return Response({'error': err}, status=400)
        if not data:
            return Response({'error': 'Không có trường hợp lệ để cập nhật.'}, status=400)
        sets = ', '.join('%s = %%s' % k for k in data)
        x('UPDATE classes SET %s, updated_at = %%s WHERE id = %%s' % sets,
          tuple(data.values()) + (local_now(), class_id))
        audit.record(request, audit.CLASS_UPDATE, target_type='class',
                     target_id=class_id, target_label=before['name'],
                     summary='Sửa lớp "%s" — đổi: %s.' % (before['name'],
                                                          ', '.join(sorted(data))),
                     detail=_audit_detail(data))
        return Response({'ok': True})

    def delete(self, request, class_id):
        """Xoá lớp. ĐÒI `?confirm=1` khi lớp còn dữ liệu.

        Vì sao có hàng rào này (30/08/2026): ba bảng trỏ vào `classes` đều
        `ON DELETE CASCADE`, nên một lời gọi DELETE quét sạch `class_members`,
        `class_sessions` VÀ `attendance` của cả lớp. Từ hôm nay có buổi học và
        điểm danh, sức công phá của nút này lớn hơn hẳn lúc nó được viết.

        Nó còn mâu thuẫn thẳng với nguyên tắc ghi trong schema §29 — "giữ
        `left_at` thay vì xoá dòng: học viên nghỉ giữa chừng vẫn phải còn trong
        báo cáo của kỳ đó". Cả sản phẩm cẩn thận giữ lịch sử, rồi một nút xoá
        không hỏi câu nào lấy đi toàn bộ. Không có đường khôi phục.
        """
        # Đọc tên TRƯỚC khi xoá: sau lệnh DELETE thì không còn chỗ nào lấy lại
        # được, và một dòng nhật ký "đã xoá lớp #7" không nói lên điều gì với
        # người đọc ba tháng sau.
        before = q1('SELECT id, code, name FROM classes WHERE id=%s', (class_id,))
        if not before:
            # Trước đây trả `{'ok': True}` cho cả id bịa — giao diện báo "đã xoá"
            # cho một lớp chưa bao giờ tồn tại.
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)

        # ĐẾM CẢ BÀI TẬP VÀ BÀI ĐÃ NỘP. Thiếu hai dòng này thì hộp xác nhận
        # nói "mất 4 dòng ghi danh, 0 buổi học, 0 lượt điểm danh" trong khi thứ
        # thật sự mất là BÀI TỰ LUẬN của cả lớp — thứ các em bỏ công viết ra và
        # không có bản nào khác. Tệ hơn: lớp CHỈ có bài tập thì tổng bằng 0 nên
        # KHÔNG hỏi câu nào, xoá luôn (đo 31/08/2026).
        counts = q1('''SELECT (SELECT COUNT(*) FROM class_members WHERE class_id=%s) AS members,
                             (SELECT COUNT(*) FROM class_sessions WHERE class_id=%s) AS sessions,
                             (SELECT COUNT(*) FROM attendance a
                                JOIN class_sessions s ON s.id = a.session_id
                               WHERE s.class_id=%s) AS attendance,
                             (SELECT COUNT(*) FROM assignments WHERE class_id=%s)
                                                                              AS assignments,
                             (SELECT COUNT(*) FROM submissions sub
                                JOIN assignments a2 ON a2.id = sub.assignment_id
                               WHERE a2.class_id=%s AND sub.submitted_at IS NOT NULL)
                                                                              AS submissions''',
                    (class_id,) * 5)
        loss = sum(counts.values())
        if loss and request.query_params.get('confirm') != '1':
            return Response({
                'error': 'Lớp "%s" còn dữ liệu. Xoá là mất hẳn, không khôi phục được.'
                         % before['name'],
                'willDelete': dict(counts),
                'needsConfirm': True,
                'hint': 'Muốn đóng lớp mà giữ lịch sử thì đổi trạng thái lớp sang '
                        '"đã kết thúc" thay vì xoá.',
            }, status=409)

        # Giữ lại id các buổi TRƯỚC khi xoá: `class_sessions` đi theo lớp bằng
        # ON DELETE CASCADE, nên sau câu DELETE thì không còn chỗ nào tra ra
        # chúng nữa.
        buoi_ids = [r['id'] for r in q('SELECT id FROM class_sessions WHERE class_id=%s',
                                       (class_id,))]
        # Cùng lý do với `buoi_ids`, và ở đây HẬU QUẢ NẶNG HƠN HẲN. Sự kiện của
        # buổi học có `score` NULL nên vô hại về số liệu; sự kiện bài tập MANG
        # ĐIỂM, nên để lại là điểm của một bài KHÔNG CÒN TỒN TẠI tiếp tục kéo
        # con số thành thạo của em suốt đời — và không còn đường nào xoá, vì
        # `ref_id` trỏ tới một hàng đã mất. Đo 31/08/2026: xoá lớp xong, ô "Số
        # học" của em vẫn giữ nguyên nguồn `assignment` 90%.
        bai_ids = [r['id'] for r in q('SELECT id FROM assignments WHERE class_id=%s',
                                      (class_id,))]

        x('DELETE FROM classes WHERE id=%s', (class_id,))

        # Dọn sự kiện học tập của các buổi vừa mất. Đường xoá MỘT buổi
        # (`sessions.py`) đã gọi `forget_events` từ đầu, đường xoá cả lớp thì
        # chưa — bất đối xứng, và hậu quả nghiêng hẳn về phía nặng hơn: xoá một
        # lớp bỏ lại sự kiện của MỌI buổi trong lớp đó. Chúng vô hại về số liệu
        # (score và minutes đều NULL) nhưng vẫn tính vào "hoạt động gần nhất",
        # tức học viên của một lớp đã xoá vẫn trông như đang đi học.
        #
        # Đặt SAU câu DELETE là cố ý: xoá lớp hỏng giữa chừng thì sự kiện vẫn
        # còn nguyên cho một lớp vẫn còn tồn tại, thay vì mất trước rồi mới biết.
        quen = forget_events('class_session', buoi_ids) if buoi_ids else 0
        quen += forget_events('assignment', bai_ids) if bai_ids else 0

        if before:
            # Chỉ ghi khi lớp có thật. Gọi DELETE hai lần (bấm nhầm hai cái) mà
            # đẻ ra hai dòng nhật ký thì người đọc tưởng có hai lớp bị xoá.
            audit.record(request, audit.CLASS_DELETE, target_type='class',
                         target_id=class_id, target_label=before['name'],
                         summary='Xoá lớp "%s"%s — mất theo %d dòng ghi danh, '
                                 '%d buổi học, %d lượt điểm danh, %d bài tập '
                                 'và %d bài đã nộp.'
                                 % (before['name'],
                                    ' (mã %s)' % before['code'] if before['code'] else '',
                                    counts['members'], counts['sessions'],
                                    counts['attendance'], counts['assignments'],
                                    counts['submissions']),
                         detail=dict(_audit_detail(before), **dict(counts),
                                     forgottenEvents=quen))
        return Response({'ok': True, 'deleted': dict(counts), 'forgottenEvents': quen})


class AdminClassMembersView(APIView):
    """POST/DELETE /api/admin/classes/<id>/members — thêm/bớt học viên."""
    # `IsAdminOrAcademic`: quản lý học vụ xếp lớp và đợt học là việc HÀNG NGÀY
    # của họ. Đổi vai trò và đặt lại mật khẩu thì KHÔNG — hai việc ấy vẫn
    # `IsAdminRole` (anh Sơn chốt 01/09/2026).
    permission_classes = [IsAdminOrAcademic]

    def post(self, request, class_id):
        klass = q1('SELECT id, name FROM classes WHERE id=%s', (class_id,))
        if not klass:
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        body = request.data if isinstance(request.data, dict) else {}
        email = norm_email(body.get('email')) or ''
        uid = body.get('user_id')
        row = None
        if email:
            row = q1('SELECT id, name, email FROM users WHERE lower(email)=%s', (email,))
            if not row:
                return Response({'error': 'Không có tài khoản với email này.'}, status=404)
            uid = row['id']
        if not uid:
            return Response({'error': 'Cần user_id hoặc email.'}, status=400)
        if row is None:
            # Tra tên CHỈ để chép vào nhật ký, cố ý KHÔNG chặn khi không thấy:
            # thêm một cửa 404 ở đây là đổi hành vi của endpoint đang chạy.
            row = q1('SELECT id, name, email FROM users WHERE id=%s', (uid,))
        # `WHERE left_at IS NULL` trong mệnh đề ON CONFLICT là để trỏ đúng chỉ
        # mục duy nhất MỘT PHẦN của §36 — và nó cũng chính là thay đổi hành vi:
        # em ĐANG học lớp này thì không có gì để làm (DO NOTHING), còn em ĐÃ RỜI
        # lớp và nay quay lại thì không xung đột nữa nên sinh MỘT DÒNG MỚI, tức
        # một lượt học mới nối tiếp.
        #
        # Bản cũ `DO UPDATE SET left_at = NULL` hồi sinh chính dòng cũ, tức XOÁ
        # TRẮNG mốc rời lớp lần trước — lượt học cũ biến mất không dấu vết.
        x('''INSERT INTO class_members (class_id, user_id, joined_at)
             VALUES (%s, %s, %s)
             ON CONFLICT (class_id, user_id) WHERE left_at IS NULL DO NOTHING''',
          (class_id, uid, local_now()))
        ten = _user_label(row, uid)
        audit.record(request, audit.CLASS_MEMBER_ADD, target_type='class',
                     target_id=class_id, target_label=klass['name'],
                     summary='Thêm "%s" vào lớp "%s".' % (ten, klass['name']),
                     detail={'userId': uid, 'userName': ten, 'classId': class_id})
        return Response({'ok': True, 'userId': uid})

    def delete(self, request, class_id):
        uid = request.query_params.get('user_id') or (request.data or {}).get('user_id')
        if not uid:
            return Response({'error': 'Cần user_id.'}, status=400)

        # "Học xong" và "bỏ giữa chừng" là HAI con số khác nhau khi trung tâm
        # báo tỉ lệ bỏ học của một đợt; gộp lại thì mọi lớp kết thúc đều trông
        # như bỏ học 100%. Không đoán: thiếu lý do thì để NULL và báo cáo gọi đó
        # là "chưa ghi lý do", chứ không mặc định thành 'dropped'.
        ly_do = ((request.query_params.get('leave_reason')
                  or (request.data or {}).get('leave_reason') or '').strip() or None)
        if ly_do is not None and ly_do not in LEAVE_REASONS:
            return Response({'error': 'leave_reason phải là một trong: %s.'
                                      % ', '.join(LEAVE_REASONS)}, status=400)

        # Đánh dấu rời lớp, KHÔNG xoá: học viên nghỉ giữa chừng vẫn phải còn
        # trong báo cáo của kỳ đó.
        #
        # `AND left_at IS NULL` là BẮT BUỘC từ §36. Trước đây mỗi cặp lớp–người
        # chỉ có đúng một dòng nên không cần lọc; nay một em học lại lớp cũ sẽ
        # có nhiều dòng, và câu không lọc sẽ dập mốc rời lớp lên CẢ những lượt
        # học đã đóng từ đợt trước — ghi đè lịch sử bằng ngày hôm nay.
        rows = q('''UPDATE class_members SET left_at=%s, leave_reason=%s
                    WHERE class_id=%s AND user_id=%s AND left_at IS NULL
                    RETURNING id''',
                 (local_now(), ly_do, class_id, uid))
        if not rows:
            # Trước đây câu UPDATE không khớp dòng nào vẫn trả `{'ok': True}` —
            # giao diện báo "đã cho rời lớp" cho một em không hề ở trong lớp.
            return Response({'error': 'Học viên này không đang học lớp đó.'}, status=404)

        klass = q1('SELECT id, name FROM classes WHERE id=%s', (class_id,))
        row = q1('SELECT id, name, email FROM users WHERE id=%s', (uid,))
        ten = _user_label(row, uid)
        audit.record(request, audit.CLASS_MEMBER_REMOVE, target_type='class',
                     target_id=class_id,
                     target_label=klass['name'] if klass else '#%s' % class_id,
                     summary='Cho "%s" rời lớp "%s"%s. Dữ liệu học của em giữ nguyên.'
                             % (ten, klass['name'] if klass else '#%s' % class_id,
                                ' (%s)' % LEAVE_LABEL[ly_do] if ly_do else ''),
                     detail={'userId': uid, 'userName': ten, 'classId': class_id,
                             'leaveReason': ly_do})
        return Response({'ok': True, 'leaveReason': ly_do})


class AdminUserRoleView(APIView):
    """PUT /api/admin/users/<id>/role {role} — đổi vai trò một tài khoản."""
    permission_classes = [IsAdminRole]

    def put(self, request, user_id):
        body = request.data if isinstance(request.data, dict) else {}
        role = (body.get('role') or '').strip()
        if role not in ASSIGNABLE_ROLES:
            return Response({'error': 'Vai trò phải là một trong: %s.'
                                      % ', '.join(ASSIGNABLE_ROLES)}, status=400)
        # Lấy luôn vai trò CŨ (thay cho `SELECT 1`): nhật ký phải trả lời được
        # "trước đó em ấy là gì", mà sau lệnh UPDATE thì giá trị cũ không còn ở
        # đâu để đọc lại.
        before = q1('SELECT id, name, email, role FROM users WHERE id=%s', (user_id,))
        if not before:
            return Response({'error': 'Không có tài khoản này.'}, status=404)
        if int(user_id) == request.user.id and role != 'admin':
            # Tự hạ quyền mình xuống là mất luôn đường vào trang quản trị.
            return Response({'error': 'Không tự đổi vai trò của chính mình được.'},
                            status=400)
        # Câu trên chỉ chặn tự hạ quyền MÌNH. Hai quản trị viên hạ quyền LẪN NHAU
        # thì cả hai câu đều lọt, và hệ thống về không quản trị viên — không ai
        # vào được để phong lại quyền cho ai.
        if role != ROLE_ADMIN and last_active_admin(user_id):
            return Response({'error': 'Đây là quản trị viên đang hoạt động cuối cùng. '
                                      'Phong quyền cho một người khác trước đã.'},
                            status=400)
        x('UPDATE users SET role=%s WHERE id=%s', (role, user_id))
        ten = _user_label(before, user_id)
        audit.record(request, audit.USER_ROLE, target_type='user', target_id=user_id,
                     target_label=ten,
                     summary='Đổi vai trò của "%s": %s → %s.'
                             % (ten, before['role'] or '(chưa có)', role),
                     detail={'from': before['role'], 'to': role})
        return Response({'ok': True, 'role': role})


# ``AdminUsersView`` chuyển sang teaching/admin_users.py (30/08/2026): bản ở đây
# cứng LIMIT 50 và không phân trang, nên với vài trăm học viên thì em thứ 51 trở
# đi không có đường nào hiện ra. Bản mới có tìm/lọc/phân trang và trả kèm danh
# sách lớp đang theo học.


# ─────────────── Đặt lại mật khẩu (chính sách tài khoản do trung tâm cấp) ────

#: Âm tiết tiếng Việt không dấu, dễ đọc qua điện thoại và khó nghe nhầm.
#: Cố ý bỏ những âm dễ lẫn khi nói ("b/p", "n/l" đứng một mình) và bỏ số 0/1
#: vì trợ giảng hay đọc nhầm thành chữ O và chữ l.
_SYLLABLES = ('an', 'binh', 'cao', 'dao', 'gia', 'hoa', 'khanh', 'lam', 'mai',
              'nam', 'phuc', 'quang', 'son', 'tam', 'vinh', 'yen')


def _temp_password() -> str:
    """Mật khẩu tạm để trợ giảng ĐỌC CHO HỌC VIÊN, không phải để máy sinh cho đẹp.

    Dạng ``hsa-mai-4827``: đọc qua điện thoại không nhầm, gõ trên bàn phím điện
    thoại không khổ, nhưng vẫn có 16 × 8000 khả năng nên không đoán được trong
    một buổi. Mật khẩu này chỉ sống tới lần đăng nhập đầu tiên — hệ thống bắt
    đổi ngay sau đó.
    """
    import secrets
    return f'hsa-{secrets.choice(_SYLLABLES)}-{secrets.randbelow(9000) + 1000}'


def _thu_hoi_refresh(user_id):
    """Đưa MỌI refresh token còn hiệu lực của một tài khoản vào danh sách đen.

    Mốc `tokens_valid_from` (§39) chặn được access token bằng cách so `iat`,
    nhưng refresh token sống 8 ngày và có thể đã bị lưu sẵn ở một máy khác.
    Hai hàng rào cho hai loại token; thiếu một là còn đường quay lại.

    KHÔNG ném lỗi ra ngoài: bảng danh sách đen trục trặc thì trợ giảng vẫn phải
    đặt lại được mật khẩu — mốc `tokens_valid_from` đã chặn phần lớn đường, và
    một thao tác an ninh đổ vỡ giữa chừng còn tệ hơn một thao tác thành công
    một nửa nhưng có ghi log.
    """
    try:
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )
        n = 0
        for t in OutstandingToken.objects.filter(user_id=user_id):
            _, moi = BlacklistedToken.objects.get_or_create(token=t)
            n += 1 if moi else 0
        return n
    except Exception as exc:                                  # noqa: BLE001
        logger.error('[reset] KHÔNG thu hồi được refresh token của user %s: %s',
                     user_id, exc)
        return 0


class AdminResetPasswordView(APIView):
    """POST /api/admin/users/<id>/reset-password — cấp lại mật khẩu tạm.

    Có endpoint này vì đã bỏ tự đăng ký: học viên quên mật khẩu thì không còn
    đường nào tự lấy lại, và hệ thống cũng chưa gửi được email. Trợ giảng mở
    màn hình Quản trị, bấm một nút, đọc mật khẩu tạm cho học viên là xong.

    Mật khẩu tạm được trả về ĐÚNG MỘT LẦN trong phản hồi này và không lưu ở
    dạng đọc được — muốn xem lại thì phải cấp lại cái mới.
    """
    permission_classes = [IsAdminRole]

    def post(self, request, user_id):
        from accounts.hashers import make_werkzeug_password

        target = q1('SELECT id, name, email, role FROM users WHERE id=%s', (user_id,))
        if not target:
            return Response({'error': 'Không tìm thấy tài khoản này'}, status=404)

        temp = _temp_password()
        # `tokens_valid_from` = mốc thu hồi (§39). Không có nó thì nút "Đặt lại
        # mật khẩu" chỉ chặn được lần ĐĂNG NHẬP SAU: người đang chiếm tài khoản
        # vẫn thao tác bình thường thêm 30 phút nữa, đúng lúc trợ giảng tưởng
        # mình vừa đuổi được họ ra.
        x('UPDATE users SET password=%s, must_change_password=TRUE, '
          'password_changed_at=NULL, tokens_valid_from=%s WHERE id=%s',
          (make_werkzeug_password(temp), local_now(), user_id))
        # Refresh token thì mốc trên chưa đủ: chúng sống 8 ngày và người kia có
        # thể đã lưu sẵn. Đưa hết vào danh sách đen — hạ tầng đã có sẵn
        # (`token_blacklist` trong INSTALLED_APPS, `LogoutView` dùng từ trước).
        _thu_hoi_refresh(user_id)
        # XOÁ BỘ ĐỆM NGAY. `CachedJWTAuthentication` giữ đối tượng user 60 giây,
        # và từ 31/08/2026 cờ `must_change_password` là thứ CHẶN mọi đường khác.
        # Không xoá đệm thì hàng rào chỉ bắt đầu có hiệu lực sau một phút.
        #
        # Đo 31/08/2026: trợ giảng đặt lại mật khẩu vì nghi tài khoản bị người
        # khác dùng — trong 60 giây kế tiếp người đang chiếm tài khoản vẫn thao
        # tác bình thường (`/api/user` trả 200).
        invalidate_user_cache(user_id)

        ten = _user_label(target, user_id)
        audit.record(request, audit.USER_PASSWORD_RESET, target_type='user',
                     target_id=user_id, target_label=ten,
                     summary='Đặt lại mật khẩu cho "%s". Mật khẩu cũ ngừng hiệu lực '
                             'ngay, hệ thống bắt em đổi ở lần đăng nhập kế tiếp.' % ten,
                     # TUYỆT ĐỐI không có `temp` ở đây. Nhật ký kiểm toán mọi
                     # quản trị viên đều đọc được và giữ vĩnh viễn; ghi mật khẩu
                     # tạm vào đó là biến sổ kiểm toán thành kho mật khẩu dạng
                     # đọc được — hỏng đúng thứ mà việc bắt đổi mật khẩu ở lần
                     # đăng nhập đầu sinh ra để bảo vệ.
                     detail={'role': target['role']})

        return Response({
            'ok': True,
            'userId': target['id'],
            'name': target['name'],
            'email': target['email'],
            'tempPassword': temp,
            'note': 'Đọc mật khẩu này cho học viên. Hệ thống sẽ bắt đổi ngay lần '
                    'đăng nhập đầu tiên.',
        })


class AdminCreateUserView(APIView):
    """POST /api/admin/users — cấp tài khoản cho học viên.

    Đây là mảnh khép kín chính sách "tài khoản do trung tâm cấp" (27/08/2026).
    Trước khi có endpoint này, việc bỏ tự đăng ký để lại một khoảng trống chết
    người: học viên không tự mở tài khoản được nữa, mà trợ giảng cũng KHÔNG có
    đường nào tạo — quy trình "tạo lớp rồi thêm học viên theo email" chỉ chạy
    khi học viên đã có tài khoản từ trước.

    Luồng thật ở trung tâm: học viên đăng ký học và để lại email/số điện thoại
    → trợ giảng nhập vào đây → đọc mật khẩu tạm cho học viên → học viên đăng
    nhập và bị bắt đổi ngay.

    Nhận luôn `class_id` để xếp vào lớp trong cùng một thao tác: trợ giảng cấp
    tài khoản là để cho vào một lớp cụ thể, tách làm hai bước chỉ tạo thêm chỗ
    quên.
    """
    permission_classes = [IsAdminRole]

    def post(self, request):
        from accounts.hashers import make_werkzeug_password

        data = request.data if isinstance(request.data, dict) else {}
        name = (data.get('name') or '').strip()
        # Qua common/identity.py, KHÔNG tự chuẩn hoá tại chỗ. `LoginView` tra
        # bằng `norm_phone(...)`; chỗ này chỉ `.strip()` thì trợ giảng nhập
        # "+84 964 245 623" là lưu nguyên chuỗi đó, còn học viên gõ
        # "0964245623" sẽ không bao giờ khớp — em không đăng nhập bằng số điện
        # thoại được, và `idx_users_phone` cũng không bắt được trùng vì hai
        # chuỗi khác nhau. Đúng cái khe mà module identity sinh ra để bịt.
        email = norm_email(data.get('email'))
        phone = norm_phone(data.get('phone'))
        role = (data.get('role') or ROLE_STUDENT).strip()
        class_id = data.get('class_id')

        # CÙNG bộ luật với nhập hàng loạt (`admin_users.py`), không phải một
        # bộ riêng. Trước 31/08/2026 đường này chỉ kiểm RỖNG và TRÙNG, nên chuỗi
        # `"abc"` lọt thẳng vào cột email qua form đơn lẻ trong khi cùng chuỗi
        # đó bị chặn nếu dán qua ô nhập hàng loạt. Hai luật cho cùng một việc thì
        # luật lỏng hơn mới là luật thật, còn luật chặt chỉ tạo cảm giác an toàn.
        errors = {}
        if not name:
            errors['name'] = 'Nhập họ tên học viên.'
        else:
            loi = validate_name_field(name)
            if loi:
                errors['name'] = loi
        if not email and not phone:
            errors['email'] = 'Cần ít nhất email hoặc số điện thoại để cấp tài khoản.'
        if email:
            loi = validate_email_field(email)
            if loi:
                errors['email'] = loi
        if phone:
            loi = validate_phone_field(phone)
            if loi:
                errors['phone'] = loi
        if role not in ASSIGNABLE_ROLES:
            errors['role'] = 'Vai trò không hợp lệ.'
        if errors:
            return Response({'errors': errors}, status=400)

        # So sánh email KHÔNG phân biệt hoa thường. Cột `users.email` chỉ UNIQUE
        # trên giá trị nguyên văn, nên 'An@x.vn' và 'an@x.vn' lọt thành HAI tài
        # khoản — rồi học viên đăng nhập bằng bản chữ thường và nhận "sai mật
        # khẩu" trong khi tài khoản vẫn nằm đó.
        if email and q1('SELECT id FROM users WHERE lower(email)=%s', (email,)):
            return Response({'errors': {'email': 'Email này đã có tài khoản.'}}, status=400)
        if phone and q1('SELECT id FROM users WHERE phone=%s', (phone,)):
            return Response({'errors': {'phone': 'Số điện thoại này đã có tài khoản.'}},
                            status=400)

        # Kiểm lớp TRƯỚC khi tạo tài khoản, không phải sau.
        #
        # Bản cũ tạo tài khoản rồi mới thử xếp lớp, bọc trong
        # `except (TypeError, ValueError)` — mà lỗi thật lại là `IntegrityError`
        # của khoá ngoại, không nằm trong hai loại đó. Chỉ cần ô chọn lớp còn giữ
        # một lớp vừa bị xoá: tài khoản ĐÃ ghi (autocommit), phản hồi trả 500,
        # nên **mật khẩu tạm mất vĩnh viễn** — mà email thì đã bị chiếm nên nhập
        # lại cũng không tạo lại được. Trợ giảng phải vào tìm tài khoản đó rồi
        # đặt lại mật khẩu, nếu đoán ra được chuyện gì vừa xảy ra.
        if class_id not in (None, ''):
            try:
                class_id = int(class_id)
            except (TypeError, ValueError):
                return Response({'errors': {'class_id': 'Lớp không hợp lệ.'}}, status=400)
            if not q1('SELECT id FROM classes WHERE id=%s', (class_id,)):
                return Response({'errors': {'class_id': 'Lớp này không còn tồn tại. '
                                                        'Tải lại trang rồi chọn lại.'}},
                                status=400)
        else:
            class_id = None

        temp = _temp_password()
        row = q1('INSERT INTO users (name, email, phone, role, password, '
                 'must_change_password, created_at) '
                 'VALUES (%s, %s, %s, %s, %s, TRUE, %s) RETURNING id',
                 (name, email, phone, role, make_werkzeug_password(temp),
                  local_now()))
        uid = row['id']

        added_to_class = False
        if class_id:
            # Lớp đã được kiểm ở trên nên câu này không còn đường hỏng.
            # `joined_at` phải truyền `local_now()`, không để `DEFAULT now()`.
            # DEFAULT của Postgres là UTC (Django đặt TimeZone kết nối = UTC),
            # lệch 7 tiếng — em được xếp lớp lúc 1h sáng giờ VN sẽ mang ngày vào
            # lớp của HÔM TRƯỚC, và cột đó đi thẳng vào file mang đi họp phụ
            # huynh. Hai đường ghi class_members kia đã truyền đúng; đây là chỗ
            # còn sót.
            # Tài khoản vừa được tạo nên không thể đã ở trong lớp; mệnh đề
            # ON CONFLICT ở đây chỉ để câu lệnh không hỏng nếu có ai gọi lại.
            # Vế `WHERE left_at IS NULL` là bắt buộc để trỏ đúng chỉ mục duy
            # nhất một phần của §36 — thiếu nó Postgres báo "no unique or
            # exclusion constraint matching the ON CONFLICT specification".
            x('INSERT INTO class_members (class_id, user_id, joined_at) '
              'VALUES (%s, %s, %s) '
              'ON CONFLICT (class_id, user_id) WHERE left_at IS NULL DO NOTHING',
              (class_id, uid, local_now()))
            added_to_class = True

        audit.record(request, audit.USER_CREATE, target_type='user', target_id=uid,
                     target_label=name,
                     summary='Cấp tài khoản "%s" (%s)%s.'
                             % (name, role, ' và xếp vào lớp' if added_to_class else ''),
                     # Không ghi mật khẩu tạm — xem chú thích ở
                     # AdminResetPasswordView.
                     detail={'email': email or None, 'phone': phone or None,
                             'role': role,
                             'classId': int(class_id) if added_to_class else None})

        return Response({
            'ok': True,
            'userId': uid,
            'name': name,
            'email': email,
            'addedToClass': added_to_class,
            'tempPassword': temp,
            'note': 'Đọc mật khẩu này cho học viên. Hệ thống sẽ bắt đổi ngay lần '
                    'đăng nhập đầu tiên.',
        }, status=201)
