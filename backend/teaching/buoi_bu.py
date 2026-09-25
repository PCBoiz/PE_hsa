"""BUỔI BÙ — tạo một buổi học bù cho MỘT buổi đã có, chỉ cho những em được chọn.

── VÌ SAO CÓ (25/09/2026, kế hoạch v2 V-g — bảng TopHSA dòng 10) ─────────────

"Tạo lịch học bù" tới hôm nay là thêm một buổi lẻ: không nói bù cho buổi nào, và cả lớp
thấy buổi ấy trong lịch, trong sổ điểm danh, trong mẫu số chuyên cần — em không cần bù
bị đếm "chưa điểm danh" / "không có dòng" ở một buổi không phải của mình.

Nay: `class_sessions.makeup_for` trỏ buổi GỐC, `session_participants` giữ đúng các em
học bù (§62e). Mọi chỗ đọc theo từng em đi qua `teaching/nguoi_buoi.thuoc_buoi`.

── AI TẠO ĐƯỢC ────────────────────────────────────────────────────────────────

Cùng cổng với tạo một buổi thường (`ClassSessionsView.post`): nhân sự của lớp, kể cả
trợ giảng. Em được chọn phải là HỌC VIÊN đang học lớp; id lạ → 400 nêu đúng id, không
lẳng lặng bỏ (một em bị bỏ sót là em không biết mình có buổi bù).

Báo chuông + thư "học bù" cho đúng các em ấy qua `notifications.gui.gui_sau_commit` —
SAU khi giao dịch ghi xong (giao dịch cuộn lại thì không ai nhận tin về buổi không có).
"""
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from common.audit import SESSION_CREATE, record
from common.clock import local_now
from common.db import q, q1, x
from common.permissions import IsTeachingStaff, can_see_class
from notifications.gui import gui_sau_commit
from teaching.sessions import (
    _NOT_FOUND_SESSION,
    _STARTS_AT_FORMAT,
    _clean_session_payload,
    _overlap_warning,
    _session_dict,
    _session_row,
    _sql_values,
)
from teaching.trung_lich import cau_canh_bao, tim_trung
from teaching.vocab import chi_hoc_vien

#: Trần số em của MỘT buổi bù — bù cho cả lớp thì là một buổi thường, không phải buổi bù.
TRAN_EM = 60


def _gio(dt):
    return dt.strftime('%H:%M %d/%m/%Y') if dt else ''


class BuoiBuView(APIView):
    """POST /api/teach/sessions/<session_id>/buoi-bu — tạo buổi bù cho buổi `session_id`.

    Thân: ``{starts_at, user_ids: [..], duration_minutes?, topic?, meeting_url?, mode?, room?}``.
    Trả 201 ``{ok, id, session, conflicts, warning?}``.
    """
    permission_classes = [IsTeachingStaff]

    def post(self, request, session_id):
        goc = _session_row(session_id)
        if not goc or not can_see_class(request.user, goc['class_id']):
            return Response(_NOT_FOUND_SESSION, status=404)
        body = request.data if isinstance(request.data, dict) else {}

        raw = body.get('user_ids')
        if not isinstance(raw, list) or not raw:
            return Response({'error': 'Chọn ít nhất một học viên học bù.'}, status=400)
        try:
            uids = sorted({int(v) for v in raw})
        except (TypeError, ValueError):
            return Response({'error': 'Danh sách học viên học bù phải là các số id.'}, status=400)
        if len(uids) > TRAN_EM:
            return Response({'error': 'Một buổi bù tối đa %d em — bù cho cả lớp thì tạo buổi '
                                      'học thường.' % TRAN_EM}, status=400)
        dang_hoc = {r['user_id'] for r in q(
            'SELECT m.user_id FROM class_members m JOIN users u ON u.id = m.user_id '
            'WHERE m.class_id = %s AND m.left_at IS NULL AND ' + chi_hoc_vien('u'),
            (goc['class_id'],))}
        la = [u for u in uids if u not in dang_hoc]
        if la:
            return Response({'error': 'Học viên %s không đang học lớp này — bỏ ra khỏi danh sách '
                                      'rồi tạo lại.' % ', '.join('#%d' % u for u in la)}, status=400)

        data, err = _clean_session_payload({k: body[k] for k in (
            'starts_at', 'duration_minutes', 'topic', 'meeting_url', 'mode', 'room') if k in body})
        if err:
            return Response({'error': err}, status=400)
        if not data.get('starts_at'):
            return Response({'error': 'Buổi bù phải có giờ bắt đầu. ' + _STARTS_AT_FORMAT},
                            status=400)
        ten_goc = goc['topic'] or goc['starts_at'].strftime('%d/%m')
        data.setdefault('topic', None)
        data['topic'] = data['topic'] or ('Học bù: %s' % ten_goc)[:200]
        if not data.get('meeting_url'):
            # Kế thừa link của buổi gốc, không có thì của lớp — cùng luật với tạo buổi.
            lop = q1('SELECT meeting_url FROM classes WHERE id = %s', (goc['class_id'],))
            data['meeting_url'] = goc['meeting_url'] or (lop or {}).get('meeting_url')
        data.setdefault('duration_minutes', goc['duration_minutes'])
        data.update(class_id=goc['class_id'], makeup_for=session_id, status='planned',
                    created_by=request.user.id, created_at=local_now())

        warning = _overlap_warning(goc['class_id'], data['starts_at'], data.get('duration_minutes'))
        trung = tim_trung(goc['class_id'], data['starts_at'], data.get('duration_minutes'),
                          mode=data.get('mode'), room=data.get('room'))
        warning = ' '.join(w for w in (warning, cau_canh_bao(trung)) if w) or None

        cols = list(data)
        with transaction.atomic():
            row = q1('INSERT INTO class_sessions (%s) VALUES (%s) RETURNING *'
                     % (', '.join(cols), ', '.join(_sql_values(cols))), tuple(data.values()))
            # Buổi + người học bù trong MỘT giao dịch: buổi bù thiếu dòng người tham gia
            # là một buổi CẢ LỚP — đúng thứ buổi bù sinh ra để tránh.
            x('INSERT INTO session_participants (session_id, user_id) VALUES '
              + ', '.join(['(%s, %s)'] * len(uids)),
              tuple(v for u in uids for v in (row['id'], u)))
            ten_lop = goc['class_name']
            gui_sau_commit(
                uids, 'hoc_bu', 'Lớp %s: buổi học bù %s' % (ten_lop, _gio(row['starts_at'])),
                'Bạn có buổi học bù cho buổi "%s" lúc %s (%s phút). Xem ở mục "Lớp của tôi".'
                % (ten_goc, _gio(row['starts_at']), row['duration_minutes'] or 90),
                ref=('class_session', row['id']), email=True)

        record(request, SESSION_CREATE, target_type='class_session', target_id=row['id'],
               target_label=row['topic'],
               summary='Tạo buổi bù cho buổi %s lớp %s (%s) — %d em'
                       % (ten_goc, goc['class_name'], _gio(row['starts_at']), len(uids)),
               detail={'class_id': goc['class_id'], 'makeup_for': session_id,
                       'participants': uids, 'starts_at': row['starts_at'].isoformat(),
                       'warning': warning})

        ra = _session_dict(row, so_tham_gia=len(uids))
        out = {'ok': True, 'id': row['id'], 'session': ra, 'conflicts': trung}
        if warning:
            out['warning'] = warning
        return Response(out, status=201)
