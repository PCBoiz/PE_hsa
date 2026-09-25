"""CHƯƠNG TRÌNH CỦA MỘT LỚP — nhận khung, xem buổi học gắn với buổi khung nào, gắn tay.

Ba cửa:
  · GET  /api/teach/classes/<id>/chuong-trinh — giảng viên, trợ giảng, học vụ, quản trị
    (`IsTeachingStaff` + `can_see_class`): phiên bản lớp đang theo, buổi khung, buổi học
    kèm tình trạng sổ đầu bài, tiến độ lớp và từng em. Người nhận khung được (học vụ,
    quản trị) có thêm `luaChon` — các bản đang dùng của đúng môn lớp.
  · PUT  /api/admin/classes/<id>/chuong-trinh `{versionId, dryRun}` — học vụ / quản trị
    (`IsAdminOrAcademic`): nhận khung. `dryRun` cho xem trước buổi nào gắn vào đâu, buổi
    thừa, buổi khung thiếu — không ghi gì. Luật ở `dich_vu.nhan_khung`. Thay cho
    `ClassSyllabusView` của 3f47421 (cùng đường dẫn, cùng tên khoá thân yêu cầu).
  · PATCH /api/teach/sessions/<id>/chuong-trinh `{syllabusSessionId}` — gắn tay MỘT buổi
    (`IsTeachingStaff` + `can_see_class`); `null` = bỏ gắn. Chỉ buổi khung của đúng phiên
    bản lớp đang theo.

404 chứ không 403 khi không được xem lớp — cùng luật mọi cửa giảng dạy (không lộ lớp nào
tồn tại).
"""
from rest_framework.response import Response
from rest_framework.views import APIView

from chuong_trinh.dich_vu import LoiChuongTrinh, nhan_khung, tien_do_lop
from chuong_trinh.tien_do import sql_tin_chi, tien_do_tung_em
from chuong_trinh.tu_vung import BAN_XUAT_BAN, NHAN_LOAI_MUC, NHAN_TRANG_THAI_BAN
from common.audit import SESSION_SYLLABUS, record
from common.clock import local_now
from common.db import q, q1, x
from common.params import so_nguyen
from common.permissions import IsAdminOrAcademic, IsTeachingStaff, can_see_class

_KHONG_THAY_LOP = {'error': 'Không tìm thấy lớp này.'}
_KHONG_THAY_BUOI = {'error': 'Không tìm thấy buổi học này.'}


def _than(request):
    return request.data if isinstance(request.data, dict) else {}


def _doc_khoa(body, *ten):
    """Giá trị của khoá đầu tiên CÓ trong thân (camelCase của 3f47421 hoặc snake_case)."""
    for t in ten:
        if t in body:
            return True, body[t]
    return False, None


def noi_dung_ban(version_id):
    """Buổi khung (kèm SỐ THỨ TỰ = hạng theo `sort_order`) + nội dung — HAI câu."""
    buoi = q('''SELECT id, name, duration_minutes, homework,
                       ROW_NUMBER() OVER (ORDER BY sort_order, id) AS so
                  FROM syllabus_sessions WHERE version_id = %s
                 ORDER BY sort_order, id''', (version_id,))
    muc = {}
    if buoi:
        for i in q('''SELECT i.id, i.session_id, i.kind, i.title, i.weight, i.lesson_id
                        FROM syllabus_items i
                        JOIN syllabus_sessions ss ON ss.id = i.session_id
                       WHERE ss.version_id = %s
                       ORDER BY i.session_id, i.sort_order, i.id''', (version_id,)):
            muc.setdefault(i['session_id'], []).append({
                'id': i['id'], 'kind': i['kind'], 'kindLabel': NHAN_LOAI_MUC.get(i['kind'], i['kind']),
                'title': i['title'], 'weight': float(i['weight']), 'lessonId': i['lesson_id']})
    return [{'id': b['id'], 'soBuoi': b['so'], 'name': b['name'],
             'durationMinutes': b['duration_minutes'], 'homework': b['homework'],
             'items': muc.get(b['id'], [])} for b in buoi]


def _lop(class_id):
    return q1('''SELECT c.id, c.name, c.code, c.course_id, c.status, c.syllabus_version_id,
                        co.title AS course_title, v.name AS ten_khung, v.status AS trang_thai_ban
                   FROM classes c
                   LEFT JOIN courses co ON co.id = c.course_id
                   LEFT JOIN syllabus_versions v ON v.id = c.syllabus_version_id
                  WHERE c.id = %s''', (class_id,))


def chi_tiet_lop(class_id, co_the_nhan):
    """Mọi thứ màn "Chương trình lớp" cần — số câu cố định (tối đa 8, thêm 1 cho `luaChon`)."""
    lop = _lop(class_id)
    vid = lop['syllabus_version_id']
    khung = noi_dung_ban(vid) if vid else []

    # Mức đã dạy của từng MỤC (cao nhất qua mọi buổi của lớp) → % từng buổi khung.
    tin_chi = {}
    if vid:
        tin_chi = {r['item_id']: float(r['tc']) for r in q(
            '''SELECT li.item_id, MAX(''' + sql_tin_chi('li.status') + ''') AS tc
                 FROM session_log_items li
                 JOIN class_sessions cs ON cs.id = li.session_id AND cs.class_id = %s
                WHERE li.item_id IS NOT NULL
                GROUP BY li.item_id''', (class_id,))}
    for k in khung:
        w = sum(i['weight'] for i in k['items'])
        xong = sum(i['weight'] * tin_chi.get(i['id'], 0) for i in k['items'])
        k['pctDaDay'] = round(xong * 100 / w) if w else None

    buoi = q('''SELECT cs.id, cs.starts_at, cs.duration_minutes, cs.status, cs.topic,
                       cs.syllabus_session_id, cs.makeup_for, ss.version_id AS ban_cua_buoi,
                       sl.logged_at, sl.comprehension,
                       (SELECT COUNT(*) FILTER (WHERE li.status = 'done') FROM session_log_items li
                         WHERE li.session_id = cs.id) AS muc_xong,
                       (SELECT COUNT(*) FILTER (WHERE li.status = 'partial') FROM session_log_items li
                         WHERE li.session_id = cs.id) AS muc_mot_phan,
                       (SELECT COUNT(*) FILTER (WHERE li.status = 'not_done') FROM session_log_items li
                         WHERE li.session_id = cs.id) AS muc_chua
                  FROM class_sessions cs
                  LEFT JOIN syllabus_sessions ss ON ss.id = cs.syllabus_session_id
                  LEFT JOIN session_logs sl ON sl.session_id = cs.id
                 WHERE cs.class_id = %s
                 ORDER BY cs.starts_at, cs.id''', (class_id,))
    so_theo_id = {k['id']: k['soBuoi'] for k in khung}
    nay = local_now()
    ra = {
        'class': {'id': lop['id'], 'name': lop['name'], 'code': lop['code'],
                  'courseId': lop['course_id'], 'courseTitle': lop['course_title'],
                  'status': lop['status']},
        'khung': None if not vid else {
            'versionId': vid, 'name': lop['ten_khung'], 'status': lop['trang_thai_ban'],
            'statusLabel': NHAN_TRANG_THAI_BAN.get(lop['trang_thai_ban'], lop['trang_thai_ban']),
        },
        'buoiKhung': khung,
        'buoi': [{
            'id': b['id'], 'startsAt': b['starts_at'].isoformat(),
            'durationMinutes': b['duration_minutes'], 'status': b['status'], 'topic': b['topic'],
            'started': b['starts_at'] <= nay,
            'makeupFor': b['makeup_for'],
            'syllabusSessionId': b['syllabus_session_id'],
            'soBuoi': so_theo_id.get(b['syllabus_session_id']),
            # Gắn vào buổi khung của bản KHÁC bản lớp đang theo — nói ra, đừng giấu.
            'lechBan': bool(b['syllabus_session_id'] and b['ban_cua_buoi'] != vid),
            'soDauBai': None if not b['logged_at'] else {
                'loggedAt': b['logged_at'].isoformat(), 'comprehension': b['comprehension'],
                'xong': b['muc_xong'], 'motPhan': b['muc_mot_phan'], 'chua': b['muc_chua']},
        } for b in buoi],
        'tienDo': tien_do_lop([class_id], nay).get(class_id),
        'tungEm': tien_do_tung_em(class_id) if vid else [],
        'quyen': {'nhanKhung': co_the_nhan, 'ganBuoi': True},
    }
    if co_the_nhan:
        # Bản ĐANG DÙNG của mọi chuỗi; lớp có môn thì chỉ khung của môn ấy.
        dk, tham = ['v.status = %s'], [BAN_XUAT_BAN]
        if lop['course_id']:
            dk.append('v.course_id = %s')
            tham.append(lop['course_id'])
        ra['luaChon'] = [{
            'versionId': r['id'], 'name': r['name'], 'courseId': r['course_id'],
            'courseTitle': r['course_title'], 'soBuoi': r['so_buoi'],
        } for r in q('''SELECT v.id, v.name, v.course_id, co.title AS course_title,
                               (SELECT COUNT(*) FROM syllabus_sessions ss
                                 WHERE ss.version_id = v.id) AS so_buoi
                          FROM syllabus_versions v
                          LEFT JOIN courses co ON co.id = v.course_id
                         WHERE ''' + ' AND '.join(dk) + '''
                         ORDER BY co.title, v.name, v.id''', tuple(tham))]
    return ra


class LopChuongTrinhView(APIView):
    """GET /api/teach/classes/<id>/chuong-trinh — không ghi gì."""
    permission_classes = [IsTeachingStaff]

    def get(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response(_KHONG_THAY_LOP, status=404)
        # Cờ năng lực cho NÚT "Nhận khung": tính bằng CHÍNH lớp quyền của cửa ghi.
        co_the = IsAdminOrAcademic().has_permission(request, self)
        return Response(chi_tiet_lop(class_id, co_the))


class NhanKhungView(APIView):
    """PUT /api/admin/classes/<id>/chuong-trinh `{versionId, dryRun}` (nhận cả snake_case)."""
    permission_classes = [IsAdminOrAcademic]

    def put(self, request, class_id):
        body = _than(request)
        _, raw = _doc_khoa(body, 'versionId', 'version_id')
        vid = so_nguyen(raw, None, 1)
        if not vid:
            return Response({'error': 'Chọn một phiên bản chương trình (versionId).'}, status=400)
        _, dry = _doc_khoa(body, 'dryRun', 'dry_run')
        try:
            ket = nhan_khung(class_id, vid, dry_run=dry in (True, 1, '1', 'true'),
                             request=request)
        except LoiChuongTrinh as e:
            return Response({'error': e.cau}, status=e.ma)
        return Response(ket)


class GanBuoiView(APIView):
    """PATCH /api/teach/sessions/<id>/chuong-trinh `{syllabusSessionId | null}`.

    Gắn tay MỘT buổi — nội dung buổi khung kéo dài hai buổi học, buổi dời, lớp đổi lịch.
    Lượt nhận khung sau đó KHÔNG đè gắn này (`dich_vu.nhan_khung`). Trợ giảng làm được:
    cùng cửa với sổ đầu bài của buổi ấy.
    """
    permission_classes = [IsTeachingStaff]

    def patch(self, request, session_id):
        b = q1('''SELECT cs.id, cs.class_id, cs.starts_at, cs.topic, cs.syllabus_session_id,
                         c.name AS class_name, c.syllabus_version_id
                    FROM class_sessions cs JOIN classes c ON c.id = cs.class_id
                   WHERE cs.id = %s''', (session_id,))
        if not b or not can_see_class(request.user, b['class_id']):
            return Response(_KHONG_THAY_BUOI, status=404)
        co, moi = _doc_khoa(_than(request), 'syllabusSessionId', 'syllabus_session_id')
        if not co:
            return Response({'error': 'Cần syllabusSessionId (null = bỏ gắn).'}, status=400)
        khung = None
        if moi not in (None, ''):
            moi = so_nguyen(moi, None, 1)
            if not b['syllabus_version_id']:
                return Response({'error': 'Lớp chưa nhận khung chương trình nào.'}, status=400)
            khung = q1('''SELECT id, name, so FROM (
                              SELECT id, name, ROW_NUMBER() OVER (ORDER BY sort_order, id) AS so
                                FROM syllabus_sessions WHERE version_id = %s) k
                           WHERE id = %s''', (b['syllabus_version_id'], moi))
            if not khung:
                return Response({'error': 'Buổi khung này không thuộc khung lớp đang theo.'},
                                status=400)
        else:
            moi = None
        x('UPDATE class_sessions SET syllabus_session_id = %s WHERE id = %s', (moi, session_id))
        ngay = b['starts_at'].strftime('%d/%m/%Y')
        record(request, SESSION_SYLLABUS, target_type='class_session', target_id=session_id,
               target_label=b['topic'] or b['starts_at'].strftime('%d/%m/%Y %H:%M'),
               summary=('Gắn buổi %s lớp %s vào buổi khung %d "%s"'
                        % (ngay, b['class_name'], khung['so'], khung['name']) if khung
                        else 'Bỏ gắn buổi %s lớp %s khỏi khung' % (ngay, b['class_name'])),
               detail={'truoc': b['syllabus_session_id'], 'sau': moi})
        return Response({'ok': True, 'syllabusSessionId': moi,
                         'soBuoi': khung['so'] if khung else None})
