"""VIỆC HÔM NAY của giảng viên — một màn mở mỗi tối, gom mọi lớp mình phụ trách.

── VÌ SAO CÓ (14/09/2026) ─────────────────────────────────────────────────

Tới hôm nay mọi màn giảng dạy đều gắn với MỘT lớp: muốn biết "tối qua tôi đã
điểm danh chưa, còn bài nào chưa chấm" thì phải mở từng lớp rồi tự cộng. Lớp 1
bắt đầu học từ 15/09 nên từ tối mai đây là việc hằng ngày. LMS thường đặt đúng
hai thứ ở trang đầu của giáo viên: bài chưa chấm (tô đỏ khi chờ quá 5 ngày) và
lối tắt vào buổi thiếu điểm danh.

Anh Sơn chốt bốn khối + buổi sắp tới:
  · buổi ĐÃ BẮT ĐẦU mà chưa mở sổ điểm danh (kèm cờ "đang diễn ra");
  · bài ĐÃ NỘP mà chưa chấm, chờ lâu nhất trước, đỏ khi quá `CHAM_QUA_NGAY`;
  · em vắng LIỀN từ `VANG_LIEN` buổi đã điểm danh — chưa có ở đâu khác;
  · em có cảnh báo mức cao — CÙNG luật với báo cáo lớp (`reports.canh_bao_muc_cao`);
  · buổi trong 24 giờ tới, kèm cờ thiếu link phòng.
Thêm 25/09/2026 (V-f): em được giảng viên / trợ giảng ĐÁNH DẤU "cần hỗ trợ" (tay, kèm
lý do — `teaching/danh_gia.py`), khác "cần chú ý" do máy tự tính.

── TRỢ GIẢNG ──────────────────────────────────────────────────────────────

Chỉ lớp được gán (`_lop_cua` → `visible_class_ids`), nhưng ĐỦ các khối. Tới
25/09/2026 trợ giảng không nhận hai khối về từng em (vắng liền, cần chú ý) — ranh
giới cũ "tín hiệu gọi phụ huynh là của giảng viên". Bảng yêu cầu TopHSA 24/09
dòng 21 đòi ngược lại: trợ giảng theo dõi "dấu hiệu bỏ học, danh sách cần nhắc /
cần báo" (kế hoạch v2, V-b). Hai khối này chỉ có TÊN em và lớp — không liên lạc
phụ huynh, nên ranh giới riêng tư của tờ báo cáo (`IsSeniorTeachingStaff`) vẫn
nguyên: trợ giảng thấy "em nào", còn gọi ai vẫn là việc của giảng viên.

── SỐ CÂU SQL KHÔNG THEO SỐ LỚP ───────────────────────────────────────────

Số câu cố định dù 1 hay 30 lớp (`tests_viec_hom_nay` canh — so hai lượt, không ghim
một con số). Gọi `class_report` cho từng lớp là 6 câu × N — đúng cái bẫy
`overview.py` đã tránh.
"""
from datetime import timedelta

from rest_framework.response import Response
from rest_framework.views import APIView

from common.clock import local_now, local_today
from common.db import q
from common.permissions import IsTeachingStaff, is_assistant, visible_class_ids
from teaching.nguoi_buoi import thuoc_buoi
from teaching.nhan_bai import giao_cho
from teaching.reports import _last_activity, canh_bao_muc_cao
from teaching.sessions import DEFAULT_SESSION_MINUTES
from teaching.vocab import LOP_TAM_DUNG, chi_hoc_vien

#: Bài nộp chờ chấm quá ngần này ngày thì tô đỏ (mốc các LMS hay dùng).
CHAM_QUA_NGAY = 5
#: Vắng liền từ ngần này buổi đã điểm danh thì nêu tên.
VANG_LIEN = 2
#: Chỉ nhìn lại ngần này buổi đã điểm danh gần nhất mỗi lớp khi đếm vắng liền —
#: chuỗi dài hơn thế thì đã phải gọi phụ huynh từ lâu, và không cần đọc cả kỳ.
VANG_LIEN_NHIN_LAI = 10
#: Trần dòng mỗi khối — màn này là danh sách việc, không phải sổ.
TRAN = 50


def _lop_cua(user):
    ids = visible_class_ids(user)
    if not ids:
        return [], {}
    lop = q('SELECT id, name, meeting_url, status FROM classes WHERE id = ANY(%s) ORDER BY name',
            (ids,))
    return ids, {r['id']: r for r in lop}


def _iso(dt):
    return dt.isoformat() if dt else None


def _sap_toi(ids, lop, nay):
    rows = q('''SELECT id, class_id, starts_at, duration_minutes, topic, meeting_url
                FROM class_sessions
                WHERE class_id = ANY(%s) AND status <> 'cancelled'
                  AND starts_at > %s AND starts_at <= %s
                ORDER BY starts_at LIMIT %s''', (ids, nay, nay + timedelta(hours=24), TRAN))
    return [{
        'sessionId': r['id'], 'classId': r['class_id'], 'className': lop[r['class_id']]['name'],
        'startsAt': _iso(r['starts_at']), 'durationMinutes': r['duration_minutes'],
        'topic': r['topic'],
        # Link của buổi kế thừa link của lớp lúc tạo; lớp nhận link SAU đó thì
        # buổi vẫn trống — nên hỏi cả hai trước khi báo thiếu.
        'thieuLink': not (r['meeting_url'] or lop[r['class_id']]['meeting_url']),
    } for r in rows]


def _chua_diem_danh(ids, lop, nay):
    """Buổi ĐÃ bắt đầu mà điểm danh CHƯA XONG.

    "Chưa xong" gồm cả buổi TICK DỞ (vá 21/09/2026): bản cũ chỉ hỏi
    `attendance_taken_at IS NULL`, tức "đã bấm lưu lần nào chưa" — buổi 21/09
    tick 1/3 em thì màn này báo "0 buổi chưa điểm danh", màn Buổi học báo "2
    chưa tick", tờ phụ huynh nói "giảng viên ghi sót", còn giảng viên không được
    nhắc ở đâu. Nay cùng tiêu chí với màn Buổi học (`sessions._session_dict`):
    còn HỌC VIÊN đang ở lớp chưa có dòng điểm danh. Em vào lớp SAU buổi đó
    không tính — không thì mỗi lần xếp thêm một em, cả lịch sử bật đỏ.

    Lớp TẠM DỪNG (V-c, 25/09/2026) không vào khối này: buổi còn nằm trong lịch
    mà lớp nghỉ thì không phải việc tồn của ai — nhắc mỗi tối là dạy người ta
    bỏ qua dòng đỏ, kể cả dòng thật.
    """
    ids = [i for i in ids if lop[i]['status'] != LOP_TAM_DUNG]
    if not ids:
        return {'tong': 0, 'ds': []}
    thieu = '''(SELECT COUNT(*) FROM class_members m JOIN users u ON u.id = m.user_id
                 WHERE m.class_id = s.class_id AND m.left_at IS NULL
                   AND m.joined_at::date <= s.starts_at::date AND ''' + chi_hoc_vien('u') + '''
                   AND ''' + thuoc_buoi('s.id', 'm.user_id') + '''
                   AND NOT EXISTS (SELECT 1 FROM attendance a
                                   WHERE a.session_id = s.id AND a.user_id = m.user_id))'''
    rows = q('''SELECT * FROM (
                  SELECT s.id, s.class_id, s.starts_at, s.duration_minutes, s.topic,
                         s.attendance_taken_at, ''' + thieu + ''' AS con_thieu
                  FROM class_sessions s
                  WHERE s.class_id = ANY(%s) AND s.status <> 'cancelled' AND s.starts_at <= %s
                ) x
                WHERE x.attendance_taken_at IS NULL OR x.con_thieu > 0
                ORDER BY x.starts_at DESC''', (ids, nay))
    ds = []
    for r in rows[:TRAN]:
        ket = r['starts_at'] + timedelta(minutes=r['duration_minutes'] or DEFAULT_SESSION_MINUTES)
        ds.append({'sessionId': r['id'], 'classId': r['class_id'],
                   'className': lop[r['class_id']]['name'], 'startsAt': _iso(r['starts_at']),
                   'topic': r['topic'], 'dangDienRa': ket > nay,
                   # Đã lưu một phần: còn bao nhiêu em. Chưa lưu lần nào thì None.
                   'conThieu': int(r['con_thieu']) if r['attendance_taken_at'] else None})
    return {'tong': len(rows), 'ds': ds}


def _chua_cham(ids, lop, nay):
    # Chỉ bài của HỌC VIÊN: tài khoản quản trị đang là thành viên lớp 1 và có
    # thể nộp thử — một "bài chưa chấm" của quản trị viên là việc giả.
    rows = q('''SELECT a.id, a.class_id, a.title, a.due_at,
                       COUNT(*) AS so_bai, MIN(s.submitted_at) AS cho_tu
                FROM submissions s
                JOIN assignments a ON a.id = s.assignment_id
                JOIN users u ON u.id = s.user_id
                WHERE a.class_id = ANY(%s) AND s.submitted_at IS NOT NULL
                  AND s.graded_at IS NULL AND ''' + chi_hoc_vien('u') + '''
                  AND ''' + giao_cho('a', 's.user_id') + '''
                GROUP BY a.id
                ORDER BY MIN(s.submitted_at) LIMIT %s''', (ids, TRAN))
    ra = []
    for r in rows:
        cho_ngay = (nay - r['cho_tu']).days
        ra.append({'assignmentId': r['id'], 'classId': r['class_id'],
                   'className': lop[r['class_id']]['name'], 'title': r['title'],
                   'dueAt': _iso(r['due_at']), 'soBai': int(r['so_bai']),
                   'choTu': _iso(r['cho_tu']), 'choNgay': cho_ngay,
                   'quaHan': cho_ngay > CHAM_QUA_NGAY})
    return ra


def _hoc_vien_dang_hoc(ids):
    """``[(class_id, user_id, name)]`` — học viên đang học của các lớp, một câu."""
    return q('''SELECT m.class_id, m.user_id, u.name
                FROM class_members m JOIN users u ON u.id = m.user_id
                WHERE m.class_id = ANY(%s) AND m.left_at IS NULL
                  AND ''' + chi_hoc_vien('u') + '''
                ORDER BY m.class_id, u.name''', (ids,))


def _vang_lien(ids, lop, hoc_vien):
    """Em vắng (`absent`) ở MỌI buổi trong chuỗi buổi đã điểm danh gần nhất.

    Chuỗi đứt ở buổi đầu tiên em không `absent` — kể cả buổi KHÔNG có dòng điểm
    danh (giảng viên tick sót): thiếu dữ liệu thì không kết tội. `excused` cũng
    làm đứt: nghỉ có phép là chuyện nhà đã báo, không phải tín hiệu để gọi.
    """
    rows = q('''SELECT s.class_id, s.id AS session_id, s.starts_at, a.user_id, a.status
                FROM (SELECT id, class_id, starts_at,
                             ROW_NUMBER() OVER (PARTITION BY class_id ORDER BY starts_at DESC) AS tt
                      FROM class_sessions
                      WHERE class_id = ANY(%s) AND status <> 'cancelled'
                        AND attendance_taken_at IS NOT NULL) s
                LEFT JOIN attendance a ON a.session_id = s.id
                WHERE s.tt <= %s
                ORDER BY s.class_id, s.starts_at DESC''', (ids, VANG_LIEN_NHIN_LAI))
    # buổi theo lớp, mới nhất trước; dòng điểm danh theo (buổi, em)
    buoi_cua_lop, tick = {}, {}
    for r in rows:
        ds = buoi_cua_lop.setdefault(r['class_id'], [])
        if not ds or ds[-1][0] != r['session_id']:
            ds.append((r['session_id'], r['starts_at']))
        if r['user_id'] is not None:
            tick[(r['session_id'], r['user_id'])] = r['status']

    ra = []
    for hv in hoc_vien:
        chuoi, cuoi = 0, None
        for sid, bd in buoi_cua_lop.get(hv['class_id'], []):
            if tick.get((sid, hv['user_id'])) != 'absent':
                break
            chuoi += 1
            cuoi = cuoi or bd
        if chuoi >= VANG_LIEN:
            ra.append({'userId': hv['user_id'], 'name': hv['name'], 'classId': hv['class_id'],
                       'className': lop[hv['class_id']]['name'], 'soBuoi': chuoi,
                       'buoiCuoi': _iso(cuoi)})
    ra.sort(key=lambda e: (-e['soBuoi'], e['name'] or ''))
    return ra[:TRAN]


def _can_chu_y(lop, hoc_vien, nay):
    uids = sorted({hv['user_id'] for hv in hoc_vien})
    hoat_dong = _last_activity(uids)
    hom_nay = local_today()
    ra, da_neu = [], set()
    for hv in hoc_vien:
        # Một em học hai lớp của cùng giảng viên thì nêu một lần — cảnh báo này
        # về EM, không về lớp.
        if hv['user_id'] in da_neu:
            continue
        last = (hoat_dong.get(hv['user_id']) or {}).get('last_day')
        ly_do = canh_bao_muc_cao((hom_nay - last).days if last else None)
        if ly_do:
            da_neu.add(hv['user_id'])
            ra.append({'userId': hv['user_id'], 'name': hv['name'], 'classId': hv['class_id'],
                       'className': lop[hv['class_id']]['name'], 'lyDo': ly_do})
    return ra[:TRAN]


def _can_ho_tro(ids, lop):
    """Em được ĐÁNH DẤU cần hỗ trợ (§62b) ở lượt đang học — mới đánh dấu trước.

    Chỉ lượt đang mở: em đã rời lớp thì cờ trên lượt cũ không còn là việc của lớp.
    Cùng bộ lọc học viên với mọi khối khác (tài khoản quản trị trong lớp không lọt).
    """
    rows = q('''SELECT m.class_id, m.user_id, u.name, m.can_ho_tro_ly_do, m.can_ho_tro_at,
                       b.name AS boi
                FROM class_members m
                JOIN users u ON u.id = m.user_id
                LEFT JOIN users b ON b.id = m.can_ho_tro_by
                WHERE m.class_id = ANY(%s) AND m.left_at IS NULL AND m.can_ho_tro
                  AND ''' + chi_hoc_vien('u') + '''
                ORDER BY m.can_ho_tro_at DESC NULLS LAST, u.name
                LIMIT %s''', (ids, TRAN))
    return [{'userId': r['user_id'], 'name': r['name'], 'classId': r['class_id'],
             'className': lop[r['class_id']]['name'], 'lyDo': r['can_ho_tro_ly_do'],
             'luc': _iso(r['can_ho_tro_at']), 'boi': r['boi']} for r in rows]


class ViecHomNayView(APIView):
    """GET /api/teach/viec-hom-nay — không ghi gì."""
    permission_classes = [IsTeachingStaff]

    def get(self, request):
        nay = local_now()
        ids, lop = _lop_cua(request.user)
        hoc_vien = _hoc_vien_dang_hoc(ids) if ids else []
        return Response({
            # Màn hình vẫn cần biết để dẫn trợ giảng tới đúng chỗ (họ không mở
            # được tờ báo cáo phụ huynh) — không còn dùng để giấu khối nào.
            'troGiang': is_assistant(request.user),
            'lop': [{'id': r['id'], 'name': r['name']} for r in lop.values()],
            'nguong': {'chamQuaNgay': CHAM_QUA_NGAY, 'vangLien': VANG_LIEN},
            'sapToi': _sap_toi(ids, lop, nay) if ids else [],
            'chuaDiemDanh': _chua_diem_danh(ids, lop, nay) if ids else {'tong': 0, 'ds': []},
            'chuaCham': _chua_cham(ids, lop, nay) if ids else [],
            'vangLien': _vang_lien(ids, lop, hoc_vien) if ids else [],
            'canChuY': _can_chu_y(lop, hoc_vien, nay) if ids else [],
            'canHoTro': _can_ho_tro(ids, lop) if ids else [],
        })
