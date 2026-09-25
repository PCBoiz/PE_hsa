"""BÁO CÁO CHẤM CÔNG theo tháng — giảng viên VÀ trợ giảng (V-o, bảng TopHSA dòng 6.3).

CHỈ ĐỌC. Khoá tháng và chỉnh tay là việc của Đ2 §59, không nằm ở đây.

Trước 25/09/2026 thứ gần nhất là thẻ "Điểm danh của giảng viên" ở Toàn trung tâm: nó chỉ
đếm theo GIẢNG VIÊN CHỦ LỚP (`classes.teacher_id`), trợ giảng không có dòng nào — trong
khi trung tâm trả công cho cả hai.

ĐỊNH NGHĨA (một câu SQL, xem `_SQL`):

  · Buổi ĐÃ DẠY trong tháng = buổi không huỷ (`attendance.KHONG_TINH`), bắt đầu trong tháng,
    và ĐÃ DIỄN RA theo sổ: trạng thái `done` HOẶC đã có người điểm danh. Buổi `planned` chưa
    ai mở sổ thì chưa tính — không có dấu vết nào nói buổi ấy đã dạy.
  · Buổi của GIẢNG VIÊN = buổi của lớp có `teacher_id` là người ấy (giảng viên gắn theo lớp;
    đổi giảng viên từng buổi là Đ2 §58 — khi ấy đổi thành COALESCE(buổi, lớp) ở đây).
  · Buổi của TRỢ GIẢNG = buổi của lớp mà trợ giảng là thành viên ĐANG Ở LỚP lúc buổi bắt đầu
    (`joined_at ≤ giờ học` và chưa rời hoặc rời SAU giờ học) — gán vào lớp giữa tháng thì
    chỉ các buổi sau ngày gán được tính.
  · Số phút = độ dài buổi; buổi không ghi độ dài tính `sessions.DEFAULT_SESSION_MINUTES`.
  · Đã điểm danh = buổi đã dạy mà người ấy là người điểm danh (`attendance_taken_by`).
  · Điểm danh MUỘN = trong số ấy, lượt điểm danh quá `TRE_DIEM_DANH_GIO` giờ sau KẾT THÚC
    buổi — cùng luật thẻ "Điểm danh của giảng viên" (`overview._diem_danh_giang_vien`).

Ai có dòng: mọi tài khoản Giảng viên / Trợ giảng đang hoạt động (kể cả tháng không dạy
buổi nào — "không có buổi" cũng là điều học vụ cần thấy), cộng bất kỳ ai là giảng viên chủ
lớp của một buổi trong tháng (quản trị viên đứng lớp).

MỘT câu SQL bất kể trung tâm có bao nhiêu lớp, buổi hay người (có phép kiểm đếm câu).
"""
import datetime

from rest_framework.response import Response
from rest_framework.views import APIView

from common.clock import local_today
from common.db import q
from common.permissions import ROLE_ASSISTANT, ROLE_TEACHER, IsAdminOrAcademic
from teaching.attendance import KHONG_TINH
from teaching.overview import TRE_DIEM_DANH_GIO
from teaching.sessions import DEFAULT_SESSION_MINUTES

#: Nhãn vai trong báo cáo (cột `users.role` lẫn `admin` tiếng Anh).
NHAN_VAI = {ROLE_TEACHER: 'Giảng viên', ROLE_ASSISTANT: 'Trợ giảng', 'admin': 'Quản trị viên'}

_KHONG_TINH = ', '.join("'%s'" % t for t in KHONG_TINH)   # hằng trong mã, không phải dữ liệu vào

_SQL = '''
WITH buoi AS (
    SELECT s.id, s.class_id, s.starts_at, s.attendance_taken_by,
           COALESCE(s.duration_minutes, %(phut)s::int) AS phut,
           s.attendance_taken_at > s.starts_at
               + COALESCE(s.duration_minutes, %(phut)s::int) * INTERVAL '1 minute'
               + %(tre)s::int * INTERVAL '1 hour' AS muon
      FROM class_sessions s
     WHERE s.status NOT IN (''' + _KHONG_TINH + ''')
       AND (s.status = 'done' OR s.attendance_taken_at IS NOT NULL)
       AND s.starts_at >= %(tu)s AND s.starts_at < %(den)s
),
day AS (
    SELECT c.teacher_id AS uid, b.id AS buoi_id
      FROM buoi b JOIN classes c ON c.id = b.class_id
     WHERE c.teacher_id IS NOT NULL
    UNION
    SELECT m.user_id, b.id
      FROM buoi b
      JOIN class_members m ON m.class_id = b.class_id
      JOIN users tg ON tg.id = m.user_id AND tg.role = %(tro_giang)s
     WHERE m.joined_at <= b.starts_at AND (m.left_at IS NULL OR m.left_at > b.starts_at)
),
tong AS (
    SELECT d.uid, count(*) AS so_buoi, sum(b.phut) AS so_phut,
           array_agg(DISTINCT c.name ORDER BY c.name) AS lop
      FROM day d JOIN buoi b ON b.id = d.buoi_id JOIN classes c ON c.id = b.class_id
     GROUP BY d.uid
),
tick AS (
    SELECT attendance_taken_by AS uid, count(*) AS so_tick, count(*) FILTER (WHERE muon) AS so_muon
      FROM buoi WHERE attendance_taken_by IS NOT NULL
     GROUP BY attendance_taken_by
)
SELECT u.id, u.name, u.email, u.role,
       COALESCE(t.so_buoi, 0) AS so_buoi, COALESCE(t.so_phut, 0) AS so_phut,
       COALESCE(k.so_tick, 0) AS so_tick, COALESCE(k.so_muon, 0) AS so_muon,
       COALESCE(t.lop, ARRAY[]::text[]) AS lop
  FROM users u
  LEFT JOIN tong t ON t.uid = u.id
  LEFT JOIN tick k ON k.uid = u.id
 WHERE t.uid IS NOT NULL
    OR (u.role IN (%(giang_vien)s, %(tro_giang)s) AND COALESCE(u.status, 'active') = 'active')
 ORDER BY CASE u.role WHEN %(giang_vien)s THEN 0 WHEN %(tro_giang)s THEN 1 ELSE 2 END,
          lower(COALESCE(u.name, '')), u.id
'''


def doc_thang(raw):
    """``'YYYY-MM'`` → (ngày đầu tháng, ngày đầu tháng sau) hoặc None. Trống = tháng này."""
    raw = (raw or '').strip()
    if not raw:
        d = local_today().replace(day=1)
    else:
        try:
            nam, thang = raw.split('-')
            d = datetime.date(int(nam), int(thang), 1)
        except (ValueError, TypeError):
            return None
        if not 2000 <= d.year <= 2100:
            return None
    sau = (d.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    return d, sau


def cham_cong(tu, den):
    """Một dòng mỗi người — xem đầu tệp. MỘT câu SQL."""
    rows = q(_SQL, {'phut': DEFAULT_SESSION_MINUTES, 'tre': TRE_DIEM_DANH_GIO, 'tu': tu, 'den': den,
                    'giang_vien': ROLE_TEACHER, 'tro_giang': ROLE_ASSISTANT})
    return [{
        'id': r['id'], 'name': r['name'], 'email': r['email'], 'role': r['role'],
        'vai': NHAN_VAI.get(r['role'], r['role']),
        'soBuoi': r['so_buoi'], 'soPhut': int(r['so_phut'] or 0),
        'daDiemDanh': r['so_tick'], 'diemDanhMuon': r['so_muon'],
        'lop': list(r['lop'] or []),
    } for r in rows]


class ChamCongView(APIView):
    """GET /api/admin/cham-cong?thang=YYYY-MM[&dinh_dang=xlsx] — báo cáo chấm công, CHỈ ĐỌC."""
    permission_classes = [IsAdminOrAcademic]

    def get(self, request):
        khoang = doc_thang(request.query_params.get('thang'))
        if not khoang:
            return Response({'error': 'Tháng phải ở dạng YYYY-MM, ví dụ 2026-09.'}, status=400)
        tu, den = khoang
        nguoi = cham_cong(tu, den)
        dd = (request.query_params.get('dinh_dang') or '').strip().lower()
        if dd == 'xlsx':
            from teaching.exports import xuat_bang
            header = ['Họ tên', 'Email', 'Vai trò', 'Số buổi đã dạy', 'Tổng số phút', 'Số giờ',
                      'Buổi đã điểm danh', 'Điểm danh muộn (quá %d giờ)' % TRE_DIEM_DANH_GIO, 'Lớp']
            rows = [[n['name'], n['email'], n['vai'], n['soBuoi'], n['soPhut'], round(n['soPhut'] / 60, 2),
                     n['daDiemDanh'], n['diemDanhMuon'], ' · '.join(n['lop'])] for n in nguoi]
            return xuat_bang('xlsx', 'Chấm công tháng %s' % tu.strftime('%m-%Y'), header, rows, 'Chấm công')
        if dd not in ('', 'json'):
            return Response({'error': 'Định dạng tải về chỉ nhận xlsx.'}, status=400)
        return Response({
            'thang': tu.strftime('%Y-%m'),
            'tu': tu.isoformat(),
            'den': (den - datetime.timedelta(days=1)).isoformat(),
            'lateHours': TRE_DIEM_DANH_GIO,
            'nguoi': nguoi,
        })
