"""LỊCH HỌC GỘP — theo trung tâm, giảng viên, lớp, học viên (bảng yêu cầu TopHSA,
tab "Nhi" #4), 23/09/2026.

  GET /api/teach/lich?tu=YYYY-MM-DD&den=YYYY-MM-DD[&lop=][&giang_vien=][&hoc_vien=]

Ai thấy gì — CÙNG luật với mọi màn giảng dạy (`visible_class_ids`), không luật
riêng: quản trị viên và học vụ thấy mọi lớp và lọc được theo giảng viên / lớp /
học viên; giảng viên thấy lớp mình phụ trách; trợ giảng thấy lớp được gán.

Lọc theo HỌC VIÊN tính tư cách thành viên TẠI GIỜ BUỔI HỌC (vào lớp trước giờ
ấy, chưa rời trước giờ ấy) — em chuyển lớp giữa kỳ thì lịch cũ của em vẫn đúng
là lịch lớp cũ, không bị lịch lớp mới đè lên quá khứ.

Chỉ đọc. Mỗi buổi kèm hình thức / phòng HIỆU LỰC (§53: buổi để trống = theo lớp)
và cờ `trung` nếu chồng giờ với buổi khác CÙNG giảng viên — thứ người xếp lịch
cần thấy ngay trên lịch chứ không phải lúc mở từng buổi.
"""
import datetime

from rest_framework.response import Response
from rest_framework.views import APIView

from common.clock import local_today
from common.db import q
from common.permissions import IsTeachingStaff, is_academic, is_admin, visible_class_ids
from stats.goals import as_date

#: Xem tối đa hai tháng một lần — đủ cho tuần / tháng, không kéo cả năm.
TRAN_NGAY = 62
PHUT_MAC_DINH = 90


class LichView(APIView):
    permission_classes = [IsTeachingStaff]

    def get(self, request):
        p = request.query_params
        hom_nay = local_today()          # giờ Việt Nam — Render chạy UTC
        tu = as_date(p.get('tu')) if p.get('tu') else hom_nay - datetime.timedelta(days=hom_nay.weekday())
        den = as_date(p.get('den')) if p.get('den') else tu + datetime.timedelta(days=6)
        if not tu or not den or den < tu:
            return Response({'error': 'Khoảng ngày không hợp lệ (tu, den dạng YYYY-MM-DD, den ≥ tu).'},
                            status=400)
        if (den - tu).days >= TRAN_NGAY:
            return Response({'error': 'Xem tối đa %d ngày một lần.' % TRAN_NGAY}, status=400)

        lop_thay = visible_class_ids(request.user)
        quan_ly = is_admin(request.user) or is_academic(request.user)
        loc = {}
        where = ['s.class_id = ANY(%(lop_thay)s)', 's.starts_at >= %(tu)s', 's.starts_at < %(den)s']
        ts = {'lop_thay': lop_thay, 'tu': datetime.datetime.combine(tu, datetime.time()),
              'den': datetime.datetime.combine(den + datetime.timedelta(days=1), datetime.time())}

        for khoa, cot in (('lop', 'lop'), ('giang_vien', 'giang_vien'), ('hoc_vien', 'hoc_vien')):
            raw = (p.get(khoa) or '').strip()
            if not raw:
                continue
            try:
                loc[cot] = int(raw)
            except ValueError:
                return Response({'error': 'Tham số "%s" phải là số.' % khoa}, status=400)
        if 'lop' in loc:
            where.append('s.class_id = %(lop)s')
            ts['lop'] = loc['lop']
        if 'giang_vien' in loc:
            where.append('c.teacher_id = %(giang_vien)s')
            ts['giang_vien'] = loc['giang_vien']
        if 'hoc_vien' in loc:
            where.append('''EXISTS (SELECT 1 FROM class_members m
                                    WHERE m.class_id = s.class_id AND m.user_id = %(hoc_vien)s
                                      AND m.joined_at <= s.starts_at
                                      AND (m.left_at IS NULL OR m.left_at > s.starts_at))''')
            ts['hoc_vien'] = loc['hoc_vien']

        rows = q('''SELECT s.id, s.class_id, s.starts_at, s.duration_minutes, s.topic, s.status,
                           s.meeting_url, coalesce(s.mode, c.mode) AS mode_hl,
                           coalesce(s.room, c.room) AS room_hl, c.name AS lop, c.code AS ma_lop,
                           c.teacher_id, t.name AS giang_vien,
                           EXISTS (SELECT 1 FROM class_sessions s2 JOIN classes c2 ON c2.id = s2.class_id
                                    WHERE c2.teacher_id = c.teacher_id AND c.teacher_id IS NOT NULL
                                      AND s2.id <> s.id AND s2.class_id <> s.class_id
                                      AND s2.status <> 'cancelled' AND s.status <> 'cancelled'
                                      AND s2.starts_at < s.starts_at
                                          + (COALESCE(s.duration_minutes, %(mac_dinh)s) * INTERVAL '1 minute')
                                      AND s2.starts_at + (COALESCE(s2.duration_minutes, %(mac_dinh)s)
                                          * INTERVAL '1 minute') > s.starts_at) AS trung_gv
                      FROM class_sessions s
                      JOIN classes c ON c.id = s.class_id
                      LEFT JOIN users t ON t.id = c.teacher_id
                     WHERE ''' + ' AND '.join(where) + '''
                     ORDER BY s.starts_at, s.id''', dict(ts, mac_dinh=PHUT_MAC_DINH))

        out = {
            'tu': tu.isoformat(), 'den': den.isoformat(), 'loc': loc,
            'buoi': [{
                'id': r['id'], 'lopId': r['class_id'], 'lop': r['lop'], 'maLop': r['ma_lop'],
                'giangVien': r['giang_vien'], 'batDau': r['starts_at'].isoformat(),
                'phut': r['duration_minutes'] or PHUT_MAC_DINH, 'chuDe': r['topic'],
                'trangThai': r['status'], 'hinhThuc': r['mode_hl'], 'phong': r['room_hl'],
                'linkPhong': r['meeting_url'], 'trungGiangVien': bool(r['trung_gv']),
            } for r in rows],
            # Danh sách cho ô lọc — chỉ trong phạm vi người xem thấy.
            'lopChon': [{'id': r['id'], 'ten': r['name']} for r in
                        q("SELECT id, name FROM classes WHERE id = ANY(%s) AND status <> 'cancelled' "
                          'ORDER BY name', (lop_thay,))],
        }
        if quan_ly:
            out['giangVienChon'] = [{'id': r['id'], 'ten': r['name'] or r['email']} for r in
                                    q("SELECT id, name, email FROM users WHERE role IN ('Giảng viên', 'admin') "
                                      "AND coalesce(status, 'active') <> 'suspended' ORDER BY name")]
            if 'hoc_vien' in loc:
                em = q('SELECT name, email, student_code FROM users WHERE id = %s', (loc['hoc_vien'],))
                out['hocVien'] = ({'id': loc['hoc_vien'], 'ten': em[0]['name'] or em[0]['email'],
                                   'ma': em[0]['student_code']} if em else None)
        return Response(out)
