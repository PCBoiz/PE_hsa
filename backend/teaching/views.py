"""API khu vực giảng dạy + quản lý lớp.

Quyền theo NGỮ CẢNH, không theo vai trò: vào được khu vực này (giảng viên hoặc
quản trị viên) không có nghĩa là xem được mọi lớp. Mỗi endpoint chạm vào một lớp
cụ thể đều phải đi qua ``can_see_class`` — xem common/permissions.py.
"""
from rest_framework.response import Response
from rest_framework.views import APIView

from common.clock import local_now
from common.db import q1, x
from common.permissions import (ASSIGNABLE_ROLES, IsAdminRole, IsTeacherOrAdmin,
                                can_see_class, is_admin, visible_class_ids)
from stats import competency, gradebook, journal, plan
from stats.goals import read_goals
from teaching import reports

#: Trạng thái lớp hợp lệ.
CLASS_STATUS = ('draft', 'active', 'finished')
#: Trường được sửa qua API quản trị lớp, kèm độ dài tối đa cho trường chữ.
CLASS_TEXT_FIELDS = {
    'code': 40, 'name': 160, 'schedule': 160, 'meeting_url': 400, 'note': 1000,
}
CLASS_DATE_FIELDS = ('starts_on', 'ends_on', 'exam_date')


class TeachClassesView(APIView):
    """GET /api/teach/classes — lớp tôi phụ trách (quản trị viên thấy tất cả)."""
    permission_classes = [IsTeacherOrAdmin]

    def get(self, request):
        ids = visible_class_ids(request.user)
        return Response({
            'classes': reports.class_list(ids),
            'isAdmin': is_admin(request.user),
        })


class TeachClassDetailView(APIView):
    """GET /api/teach/classes/<id> — báo cáo đầy đủ một lớp."""
    permission_classes = [IsTeacherOrAdmin]

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
    permission_classes = [IsTeacherOrAdmin]

    def get(self, request, class_id, user_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        member = q1('SELECT 1 FROM class_members WHERE class_id=%s AND user_id=%s',
                    (class_id, user_id))
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

def _clean_class_payload(body):
    data, err = {}, None
    for field, limit in CLASS_TEXT_FIELDS.items():
        if field in body:
            val = (str(body[field]).strip() or None)
            data[field] = val[:limit] if val else None
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
    if 'capacity' in body:
        try:
            data['capacity'] = max(0, min(500, int(body['capacity'] or 0))) or None
        except (TypeError, ValueError):
            return None, 'Sĩ số phải là một số nguyên.'
    if 'status' in body:
        st = (body['status'] or '').strip()
        if st not in CLASS_STATUS:
            return None, 'Trạng thái phải là một trong: %s.' % ', '.join(CLASS_STATUS)
        data['status'] = st
    return data, err


class AdminClassesView(APIView):
    """GET/POST /api/admin/classes — danh sách & tạo lớp."""
    permission_classes = [IsAdminRole]

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
        return Response({'ok': True, 'id': row['id']}, status=201)


def _teachers():
    from common.db import q
    return q("SELECT id, name, email FROM users WHERE role IN ('Giảng viên','admin') "
             "ORDER BY name")


class AdminClassDetailView(APIView):
    """PUT/DELETE /api/admin/classes/<id> — sửa hoặc xoá lớp."""
    permission_classes = [IsAdminRole]

    def put(self, request, class_id):
        if not q1('SELECT 1 FROM classes WHERE id=%s', (class_id,)):
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
        return Response({'ok': True})

    def delete(self, request, class_id):
        x('DELETE FROM classes WHERE id=%s', (class_id,))
        return Response({'ok': True})


class AdminClassMembersView(APIView):
    """POST/DELETE /api/admin/classes/<id>/members — thêm/bớt học viên."""
    permission_classes = [IsAdminRole]

    def post(self, request, class_id):
        if not q1('SELECT 1 FROM classes WHERE id=%s', (class_id,)):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        body = request.data if isinstance(request.data, dict) else {}
        email = (body.get('email') or '').strip().lower()
        uid = body.get('user_id')
        if email:
            row = q1('SELECT id FROM users WHERE lower(email)=%s', (email,))
            if not row:
                return Response({'error': 'Không có tài khoản với email này.'}, status=404)
            uid = row['id']
        if not uid:
            return Response({'error': 'Cần user_id hoặc email.'}, status=400)
        x('''INSERT INTO class_members (class_id, user_id, joined_at)
             VALUES (%s, %s, %s)
             ON CONFLICT (class_id, user_id) DO UPDATE SET left_at = NULL''',
          (class_id, uid, local_now()))
        return Response({'ok': True, 'userId': uid})

    def delete(self, request, class_id):
        uid = request.query_params.get('user_id') or (request.data or {}).get('user_id')
        if not uid:
            return Response({'error': 'Cần user_id.'}, status=400)
        # Đánh dấu rời lớp, KHÔNG xoá: học viên nghỉ giữa chừng vẫn phải còn
        # trong báo cáo của kỳ đó.
        x('UPDATE class_members SET left_at=%s WHERE class_id=%s AND user_id=%s',
          (local_now(), class_id, uid))
        return Response({'ok': True})


class AdminUserRoleView(APIView):
    """PUT /api/admin/users/<id>/role {role} — đổi vai trò một tài khoản."""
    permission_classes = [IsAdminRole]

    def put(self, request, user_id):
        body = request.data if isinstance(request.data, dict) else {}
        role = (body.get('role') or '').strip()
        if role not in ASSIGNABLE_ROLES:
            return Response({'error': 'Vai trò phải là một trong: %s.'
                                      % ', '.join(ASSIGNABLE_ROLES)}, status=400)
        if not q1('SELECT 1 FROM users WHERE id=%s', (user_id,)):
            return Response({'error': 'Không có tài khoản này.'}, status=404)
        if int(user_id) == request.user.id and role != 'admin':
            # Tự hạ quyền mình xuống là mất luôn đường vào trang quản trị.
            return Response({'error': 'Không tự đổi vai trò của chính mình được.'},
                            status=400)
        x('UPDATE users SET role=%s WHERE id=%s', (role, user_id))
        return Response({'ok': True, 'role': role})


class AdminUsersView(APIView):
    """GET /api/admin/users?q= — tìm tài khoản để gán lớp hoặc đổi vai trò."""
    permission_classes = [IsAdminRole]

    def get(self, request):
        from common.db import q
        term = (request.query_params.get('q') or '').strip().lower()
        if term:
            rows = q("SELECT id, name, email, role FROM users "
                     "WHERE lower(name) LIKE %s OR lower(email) LIKE %s "
                     "ORDER BY name LIMIT 50", ('%' + term + '%', '%' + term + '%'))
        else:
            rows = q('SELECT id, name, email, role FROM users ORDER BY id DESC LIMIT 50')
        return Response({'users': [dict(r) for r in rows],
                         'roles': list(ASSIGNABLE_ROLES)})
