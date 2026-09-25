"""CHƯƠNG TRÌNH CỦA MỘT LỚP — nhận khung, xem buổi học gắn với buổi khung nào, gắn tay.

Ba cửa:
  · GET  /api/teach/classes/<id>/chuong-trinh — giảng viên, trợ giảng, học vụ, quản trị
    (`IsTeachingStaff` + `can_see_class`): phiên bản lớp đang theo, buổi khung, buổi học
    kèm tình trạng sổ đầu bài, tiến độ lớp và từng em. Người nhận khung được (học vụ,
    quản trị) có thêm `luaChon` — các bản đang dùng của đúng môn lớp.
  · PUT  /api/admin/classes/<id>/chuong-trinh `{version_id, dry_run}` — học vụ / quản trị
    (`IsAdminOrAcademic`): nhận khung. `dry_run` cho xem trước buổi nào gắn vào đâu, buổi
    thừa, buổi khung thiếu — không ghi gì. Luật ở `dich_vu.nhan_khung`.
  · PATCH /api/teach/sessions/<id>/chuong-trinh `{syllabus_session_id}` — gắn tay MỘT buổi
    (`IsTeachingStaff` + `can_see_class`); `null` = bỏ gắn. Chỉ buổi khung của đúng phiên
    bản lớp đang theo.

404 chứ không 403 khi không được xem lớp — cùng luật mọi cửa giảng dạy (không lộ lớp nào
tồn tại).
"""
from rest_framework.response import Response
from rest_framework.views import APIView

from chuong_trinh.dich_vu import LoiChuongTrinh, nhan_khung, tien_do_lop
from chuong_trinh.khung import noi_dung_ban
from chuong_trinh.tien_do import sql_tin_chi, tien_do_tung_em
from chuong_trinh.tu_vung import BAN_XUAT_BAN, NHAN_TRANG_THAI_BAN
from common.audit import SESSION_SYLLABUS, record
from common.clock import local_now
from common.db import q, q1, x
from common.params import so_nguyen
from common.permissions import IsAdminOrAcademic, IsTeachingStaff, can_see_class

_KHONG_THAY_LOP = {'error': 'Không tìm thấy lớp này.'}
_KHONG_THAY_BUOI = {'error': 'Không tìm thấy buổi học này.'}


def _lop(class_id):
    return q1('''SELECT c.id, c.name, c.code, c.course_id, c.status, c.syllabus_version_id,
                        co.title AS course_title, v.version, v.status AS trang_thai_ban,
                        v.published_at, s.id AS syllabus_id, s.name AS ten_khung
                   FROM classes c
                   LEFT JOIN courses co ON co.id = c.course_id
                   LEFT JOIN syllabus_versions v ON v.id = c.syllabus_version_id
                   LEFT JOIN syllabi s ON s.id = v.syllabus_id
                  WHERE c.id = %s''', (class_id,))


def chi_tiet_lop(class_id, co_the_nhan):
    """Mọi thứ màn "Chương trình lớp" cần — số câu cố định (6, thêm 1 cho `luaChon`)."""
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
                       cs.syllabus_session_id, cs.attendance_taken_at, ss.so_buoi,
                       ss.version_id AS ban_cua_buoi, sl.logged_at, sl.comprehension,
                       (SELECT COUNT(*) FROM session_log_items li
                         WHERE li.session_id = cs.id AND li.status = 'done') AS muc_xong,
                       (SELECT COUNT(*) FROM session_log_items li
                         WHERE li.session_id = cs.id AND li.status = 'partial') AS muc_mot_phan,
                       (SELECT COUNT(*) FROM session_log_items li
                         WHERE li.session_id = cs.id AND li.status = 'not_done') AS muc_chua
                  FROM class_sessions cs
                  LEFT JOIN syllabus_sessions ss ON ss.id = cs.syllabus_session_id
                  LEFT JOIN session_logs sl ON sl.session_id = cs.id
                 WHERE cs.class_id = %s
                 ORDER BY cs.starts_at, cs.id''', (class_id,))
    tien_do = tien_do_lop([class_id]).get(class_id)
    nay = local_now()
    ra = {
        'class': {'id': lop['id'], 'name': lop['name'], 'code': lop['code'],
                  'courseId': lop['course_id'], 'courseTitle': lop['course_title'],
                  'status': lop['status']},
        'khung': None if not vid else {
            'versionId': vid, 'version': lop['version'], 'syllabusId': lop['syllabus_id'],
            'name': lop['ten_khung'], 'status': lop['trang_thai_ban'],
            'statusLabel': NHAN_TRANG_THAI_BAN.get(lop['trang_thai_ban'], lop['trang_thai_ban']),
            'publishedAt': lop['published_at'].isoformat() if lop['published_at'] else None,
        },
        'buoiKhung': khung,
        'buoi': [{
            'id': b['id'], 'startsAt': b['starts_at'].isoformat(),
            'durationMinutes': b['duration_minutes'], 'status': b['status'], 'topic': b['topic'],
            'started': b['starts_at'] <= nay,
            'syllabusSessionId': b['syllabus_session_id'],
            'soBuoi': b['so_buoi'] if b['ban_cua_buoi'] == vid else None,
            # Gắn vào buổi khung của bản KHÁC (lớp vừa đổi bản mà chưa nhận lại) — nói ra.
            'lechBan': bool(b['syllabus_session_id'] and b['ban_cua_buoi'] != vid),
            'soDauBai': None if not b['logged_at'] else {
                'loggedAt': b['logged_at'].isoformat(), 'comprehension': b['comprehension'],
                'xong': b['muc_xong'], 'motPhan': b['muc_mot_phan'], 'chua': b['muc_chua']},
        } for b in buoi],
        'tienDo': tien_do,
        'tungEm': tien_do_tung_em(class_id) if vid else [],
        'quyen': {'nhanKhung': co_the_nhan, 'ganBuoi': True},
    }
    if co_the_nhan:
        # Bản ĐANG DÙNG của mọi khung chưa cất; lớp có môn thì chỉ khung của môn ấy.
        dk, tham = ['v.status = %s', 's.archived_at IS NULL'], [BAN_XUAT_BAN]
        if lop['course_id']:
            dk.append('s.course_id = %s')
            tham.append(lop['course_id'])
        ra['luaChon'] = [{
            'versionId': r['id'], 'version': r['version'], 'syllabusId': r['syllabus_id'],
            'name': r['name'], 'courseTitle': r['course_title'], 'soBuoi': r['so_buoi'],
        } for r in q('''SELECT v.id, v.version, s.id AS syllabus_id, s.name, co.title AS course_title,
                               (SELECT COUNT(*) FROM syllabus_sessions ss
                                 WHERE ss.version_id = v.id) AS so_buoi
                          FROM syllabus_versions v
                          JOIN syllabi s ON s.id = v.syllabus_id
                          LEFT JOIN courses co ON co.id = s.course_id
                         WHERE ''' + ' AND '.join(dk) + '''
                         ORDER BY co.title, s.name''', tuple(tham))]
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
    """PUT /api/admin/classes/<id>/chuong-trinh `{version_id, dry_run}`."""
    permission_classes = [IsAdminOrAcademic]

    def put(self, request, class_id):
        body = request.data if isinstance(request.data, dict) else {}
        vid = so_nguyen(body.get('version_id'), None, 1)
        if not vid:
            return Response({'error': 'Chọn một phiên bản khung (version_id).'}, status=400)
        dry = body.get('dry_run') in (True, 1, '1', 'true')
        try:
            ket = nhan_khung(class_id, vid, dry_run=dry, request=request)
        except LoiChuongTrinh as e:
            return Response({'error': e.cau}, status=e.ma)
        return Response(ket)


class GanBuoiView(APIView):
    """PATCH /api/teach/sessions/<id>/chuong-trinh `{syllabus_session_id | null}`.

    Gắn tay MỘT buổi — nội dung buổi khung kéo dài hai buổi học, buổi dạy bù, buổi dời.
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
        body = request.data if isinstance(request.data, dict) else {}
        if 'syllabus_session_id' not in body:
            return Response({'error': 'Cần syllabus_session_id (null = bỏ gắn).'}, status=400)
        moi = body.get('syllabus_session_id')
        khung = None
        if moi not in (None, ''):
            moi = so_nguyen(moi, None, 1)
            if not b['syllabus_version_id']:
                return Response({'error': 'Lớp chưa nhận khung chương trình nào.'}, status=400)
            khung = q1('SELECT id, so_buoi, title FROM syllabus_sessions '
                       'WHERE id = %s AND version_id = %s', (moi, b['syllabus_version_id']))
            if not khung:
                return Response({'error': 'Buổi khung này không thuộc khung lớp đang theo.'},
                                status=400)
        else:
            moi = None
        x('UPDATE class_sessions SET syllabus_session_id = %s WHERE id = %s', (moi, session_id))
        record(request, SESSION_SYLLABUS, target_type='class_session', target_id=session_id,
               target_label=b['topic'] or b['starts_at'].strftime('%d/%m/%Y %H:%M'),
               summary=('Gắn buổi %s lớp %s vào buổi khung %d' % (
                   b['starts_at'].strftime('%d/%m/%Y'), b['class_name'], khung['so_buoi'])
                        if khung else 'Bỏ gắn buổi %s lớp %s khỏi khung' % (
                   b['starts_at'].strftime('%d/%m/%Y'), b['class_name'])),
               detail={'truoc': b['syllabus_session_id'], 'sau': moi})
        return Response({'ok': True, 'syllabusSessionId': moi,
                         'soBuoi': khung['so_buoi'] if khung else None})
