"""TẠO NHANH LỚP GIA SƯ (mục 1.2b kế hoạch thử nghiệm, 24/09/2026).

Ghi chú họp TopHSA: ~400 lớp gia sư cá nhân hoá. Tạo MỘT lớp như thế bằng màn cũ là
ba màn, bảy bước: tạo lớp → mở "Học viên" tìm em → sang Buổi học sinh lịch. Ở đây là
MỘT biểu mẫu: một em + một giảng viên + lịch tuần → lớp (loại `gia_su`, sĩ số 3),
em vào lớp, buổi sinh sẵn — trong MỘT giao dịch: bước nào hỏng thì không còn lớp mồ
côi thiếu em hay thiếu lịch.

`dry_run`: chạy ĐÚNG đường ghi trong giao dịch rồi CUỘN LẠI — xem trước dùng cùng
một luật với lượt tạo thật (trùng giờ giảng viên / em / phòng qua `trung_lich`,
ngày nghỉ của đợt, trần buổi) chứ không phải một bản chép luật để lệch dần.
"""
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from common import audit
from common.clock import local_now
from common.db import q1
from common.identity import norm_email
from common.permissions import ROLE_STUDENT, IsAdminOrAcademic
from teaching.sinh_buoi import _TEN_THU, _doc_than, _lop, tao_buoi
from teaching.views import AdminClassMembersView, _audit_detail, _clean_class_payload
from teaching.vocab import TRAN_GIA_SU

#: Trường lớp nhận từ biểu mẫu — loại lớp, sĩ số, trạng thái do CỬA NÀY đặt.
_TRUONG_LOP = ('name', 'code', 'schedule', 'course_id', 'term_id', 'starts_on', 'ends_on',
               'mode', 'room', 'meeting_url', 'note', 'exam_date')


def lich_chu(ts):
    """Lịch tuần → chữ ở cột "Lịch học" — ĐÚNG dạng `sinh_buoi.doan_lich` đọc ngược lại
    được ("T3, T5 · 19:30–21:00"), để lần sinh lịch sau điền sẵn đúng thứ và giờ."""
    bd = ts['gio'].hour * 60 + ts['gio'].minute
    kt = (bd + ts['phut']) % (24 * 60)
    return '%s · %s–%02d:%02d' % (', '.join(_TEN_THU[t] for t in ts['thu']),
                                  ts['gio'].strftime('%H:%M'), kt // 60, kt % 60)


def _tim_em(body):
    uid, email = body.get('student_id'), norm_email(body.get('student_email'))
    if uid not in (None, ''):
        try:
            row = q1('SELECT id, name, email, role FROM users WHERE id=%s', (int(uid),))
        except (TypeError, ValueError):
            row = None
    elif email:
        row = q1('SELECT id, name, email, role FROM users WHERE lower(email)=%s', (email,))
    else:
        return None, 'Chọn học viên cho lớp gia sư.'
    if not row:
        return None, 'Không có tài khoản học viên này.'
    if row['role'] != ROLE_STUDENT:
        return None, 'Tài khoản "%s" không phải Học viên — lớp gia sư chỉ xếp học viên.' % (
            row['name'] or row['email'])
    return row, None


class TaoLopGiaSuView(APIView):
    """POST /api/admin/classes/gia-su — một em + một giảng viên (+ lịch tuần) → một lớp.

    Thân: `student_id` | `student_email`; `teacher_id`; trường lớp tuỳ chọn (`name` —
    trống thì tự đặt "Gia sư · {em} · {giảng viên}", `course_id`, `term_id`, …);
    `generate` + `weekdays`, `start_time`, `duration_minutes`, `from`, `to` như sinh
    lịch; `dry_run`. 201 `{ok, classId, name, memberUserId, sessions}`.
    """
    permission_classes = [IsAdminOrAcademic]

    def post(self, request):
        body = request.data if isinstance(request.data, dict) else {}
        dry_run = bool(body.get('dry_run'))

        em, loi = _tim_em(body)
        if loi:
            return Response({'error': loi}, status=400)
        if body.get('teacher_id') in (None, '', 0):
            return Response({'error': 'Chọn giảng viên dạy lớp gia sư.'}, status=400)
        data, loi = _clean_class_payload({k: body[k] for k in (*_TRUONG_LOP, 'teacher_id') if k in body})
        if loi:
            return Response({'error': loi}, status=400)
        ts = None
        if body.get('generate'):
            ts, loi = _doc_than(body)
            if loi:
                return Response({'error': loi}, status=400)

        gv = q1('SELECT name, email FROM users WHERE id=%s', (data['teacher_id'],))
        ten_em, ten_gv = em['name'] or em['email'], gv['name'] or gv['email']
        data['name'] = data.get('name') or ('Gia sư · %s · %s' % (ten_em, ten_gv))[:160]
        data.update(class_type='gia_su', capacity=TRAN_GIA_SU, status='active')
        if ts and not data.get('schedule'):
            data['schedule'] = lich_chu(ts)

        with transaction.atomic():
            cols = list(data) + ['created_at']
            vals = list(data.values()) + [local_now()]
            lop_id = q1('INSERT INTO classes (%s) VALUES (%s) RETURNING id'
                        % (', '.join(cols), ', '.join(['%s'] * len(vals))), tuple(vals))['id']
            audit.record(request, audit.CLASS_CREATE, target_type='class', target_id=lop_id,
                         target_label=data['name'],
                         summary='Tạo lớp gia sư "%s" (em %s, giảng viên %s).' % (data['name'], ten_em, ten_gv),
                         detail=_audit_detail(data))
            AdminClassMembersView._ghi_thanh_vien(request, {'id': lop_id, 'name': data['name'],
                                                            'class_type': 'gia_su'}, em)
            buoi = None
            if ts:
                # Buổi sinh trong CÙNG giao dịch: em đã ở trong lớp nên cảnh báo trùng
                # giờ HỌC VIÊN (em đang học lớp khác lúc ấy) có mặt ngay ở bản xem trước.
                buoi, loi = tao_buoi(request, lop_id, _lop(lop_id), ts, dry_run)
                if loi:
                    transaction.set_rollback(True)
                    return Response({'error': loi}, status=400)
            if dry_run:
                transaction.set_rollback(True)

        sessions = ({'dem': buoi['dem'], 'buoi': buoi['buoi'], 'canhBao': buoi['canhBao'],
                     'ids': buoi['ids']} if buoi else None)
        if dry_run:
            return Response({'ok': True, 'dryRun': True, 'name': data['name'],
                             'schedule': data.get('schedule'), 'sessions': sessions})
        return Response({'ok': True, 'classId': lop_id, 'name': data['name'],
                         'memberUserId': em['id'], 'sessions': sessions}, status=201)
