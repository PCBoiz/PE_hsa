"""Bộ dữ liệu TRÌNH DIỄN — một trung tâm đang chạy, đánh dấu được, gỡ được (§49).

── VÌ SAO CÓ (16/09/2026) ────────────────────────────────────────────────

pe_hsa đang được chuẩn bị để bán đứt cho TopHSA. Buổi trình diễn cần thấy một
trung tâm ĐANG CHẠY: lớp có buổi học đã điểm danh, bài tự luận đã chấm, học viên
đã học bài và thi thử, tờ báo cáo phụ huynh đủ các khối. CSDL mới có ba học viên
thử — mọi màn hình trông như chưa ai dùng.

── LUẬT ─────────────────────────────────────────────────────────────────

1. ĐÁNH DẤU. Mọi tài khoản và lớp tạo ra mang `is_demo = TRUE`; tên lớp có chữ
   "lớp mẫu"; email đuôi `@example.com` — tên miền dành riêng cho tài liệu (RFC
   2606), khai MX rỗng (RFC 7505) nên không máy chủ thư nào nhận. Người xem không
   được nhầm em bịa ra là em thật.
   (Bản đầu dùng `@example.invalid`. `LoginView` chặn nó ngay ở bước kiểm định dạng
   email — nghe như an toàn hơn, nhưng thế là phép kiểm đăng nhập KHÔNG BAO GIỜ tới
   được chỗ so mật khẩu, và lỗ mật khẩu thô ở luật 3 nằm im không ai thấy.)
2. KHÔNG GỬI. `teaching/parent_send.py` bỏ qua học viên mẫu (trạng thái `mau`).
3. KHÔNG ĐĂNG NHẬP ĐƯỢC. Mật khẩu là bản băm scrypt THẬT của một chuỗi ngẫu nhiên
   sinh lúc chạy rồi bỏ đi — không ai, kể cả người chạy lệnh, biết mật khẩu.
   KHÔNG được thay bằng một chuỗi thô "không phải bản băm": `accounts/views.py::
   LoginView` còn nhánh mật khẩu THÔ cũ (không phải băm thì so NGUYÊN VĂN rồi nâng
   cấp) — chuỗi thô ấy chính là mật khẩu, mà kho mã công khai. Bản đầu mắc đúng lỗi
   này; `tests_du_lieu_mau::test_tai_khoan_mau_KHONG_dang_nhap_duoc` đăng nhập được
   (200) bằng chuỗi ấy trước khi sửa.
4. ĐI ĐÚNG ĐƯỜNG GHI. Sự kiện học tập qua `common.events.record_events`, bộ đệm
   tiến độ qua `courses.enrollment.tinh_lai`, XP lượt thi qua `mockexam._mock_xp`
   — không tự tính lại lần hai. Nhờ vậy bản đồ năng lực, sổ điểm, báo cáo phụ
   huynh đọc dữ liệu mẫu đúng như đọc dữ liệu thật; lệch công thức ở đâu thì dữ
   liệu mẫu lệch theo, chứ không che đi.
5. TẤT ĐỊNH. Cùng hạt giống + cùng ngày chạy → cùng tên, cùng điểm.
6. GỠ SẠCH. `go()` xoá hai gốc (`classes`, `users` có `is_demo`); mọi thứ khác đi
   theo ON DELETE CASCADE.
7. LÀM MỚI TRƯỚC BUỔI TRÌNH DIỄN (17/09/2026). Bộ dữ liệu neo vào NGÀY DỰNG, nên nó
   cũ đi mỗi ngày: một ngày sau khi dựng, tổng quan quản trị đã hiện "2 buổi đã dạy
   chưa ai điểm danh — Cần làm ngay"; vài tuần sau, khối "Con có học đều không" của
   tờ báo cáo phụ huynh ra các tuần gần nhất trống trơn và danh sách "em cần chú ý"
   đầy "N ngày không mở bài" — một trung tâm trông như đang chết, đúng lúc người mua
   xem. `lam_moi()` gỡ rồi dựng lại neo vào hôm nay trong MỘT giao dịch; lệnh đếm
   báo hoạt động mẫu gần nhất cách đây bao nhiêu ngày.

── SỐ CÂU TRUY VẤN ──────────────────────────────────────────────────────

Chạy từ máy dev, mỗi câu tới Neon mất ~240 ms. Nên mỗi LOẠI dòng là MỘT câu
`INSERT … SELECT FROM unnest(mảng)`, không phải một câu mỗi dòng. Ngoại lệ có chủ
ý: `tinh_lai` gọi từng cặp (học viên, khoá) — giữ một chỗ duy nhất tính bộ đệm
tiến độ đáng giá hơn vài chục giây của một lệnh chạy một lần.
"""
import json
import random
import secrets
from collections import defaultdict
from datetime import datetime, time, timedelta

from django.db import transaction

from accounts.hashers import make_werkzeug_password
from common.clock import local_now, local_today
from common.db import q, q1, x
from common.events import (
    KIND_ASSIGNMENT,
    KIND_ATTENDANCE,
    KIND_DRILL,
    KIND_LESSON,
    KIND_MOCK,
    KIND_MOCK_SECTION,
    SOURCE_SYSTEM,
    record_events,
)
from common.permissions import (
    ROLE_ACADEMIC,
    ROLE_ASSISTANT,
    ROLE_EDITOR,
    ROLE_STUDENT,
    ROLE_TEACHER,
)

HAT_GIONG = 20260916

#: Hoạt động mẫu gần nhất cũ hơn chừng này ngày thì lệnh đếm nhắc chạy `--lam-moi`.
#: Hai ngày chứ không một: dựng tối hôm trước để sáng trình diễn là chuyện bình thường.
CU_SAU_NGAY = 2
DUOI_EMAIL = '@example.com'

#: Ba tài khoản NHÂN SỰ mẫu — để bộ trình diễn có đủ SÁU vai (thêm 20/09/2026).
#:
#: Vì sao: người mua (và cả người kiểm) muốn thấy mỗi vai nhìn thấy gì — trợ giảng
#: có bị cắt khỏi báo cáo phụ huynh thật không, học vụ có thấy khu Vận hành không.
#: Trước đây bộ mẫu chỉ có học viên; ba vai kia phải tạo tay, và tạo tay thì lần
#: sau không còn (hoặc còn mà thành tài khoản rác — đúng chuyện "a"/"Test Reg").
#: Giảng viên KHÔNG nằm ở đây: lớp mẫu vẫn gắn vào giảng viên THẬT (xem
#: `_chon_giang_vien`) để anh Sơn mở đúng lớp mình khi trình diễn.
#: Trợ giảng được xếp vào lớp mẫu thứ nhất (`class_members`) — không xếp thì vai
#: ấy không thấy lớp nào, tức không có gì để trình diễn.
NHAN_SU_MAU = (
    ('Phạm Thị Học Vụ', 'hocvu.mau' + DUOI_EMAIL, ROLE_ACADEMIC),
    ('Lê Văn Trợ Giảng', 'trogiang.mau' + DUOI_EMAIL, ROLE_ASSISTANT),
    ('Trần Thị Biên Tập', 'bientap.mau' + DUOI_EMAIL, ROLE_EDITOR),
)
#: XP một bài học — cùng mức `lessons/views.py` đang cộng cho bài không khai `xp_reward`.
XP_BAI_HOC = 50

HO = ('Nguyễn', 'Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ',
      'Đặng', 'Bùi', 'Đỗ', 'Hồ', 'Ngô', 'Dương')
DEM = {
    'nam': ('Văn', 'Minh', 'Đức', 'Quang', 'Hoàng', 'Gia', 'Anh', 'Thành', 'Hữu', 'Tuấn'),
    'nu': ('Thị', 'Ngọc', 'Thu', 'Minh', 'Phương', 'Khánh', 'Bảo', 'Thanh', 'Hải', 'Diệu'),
}
TEN = {
    'nam': ('An', 'Bình', 'Cường', 'Dũng', 'Hiếu', 'Huy', 'Khang', 'Khoa', 'Lâm', 'Long',
            'Minh', 'Nam', 'Nghĩa', 'Phong', 'Phúc', 'Quân', 'Sơn', 'Tài', 'Thắng', 'Trung',
            'Tùng', 'Việt', 'Vinh', 'Đạt'),
    'nu': ('Anh', 'Chi', 'Giang', 'Hà', 'Hân', 'Hương', 'Lan', 'Linh', 'Mai', 'My', 'Ngân',
           'Nhi', 'Như', 'Oanh', 'Phương', 'Quỳnh', 'Tâm', 'Thảo', 'Trang', 'Trâm', 'Uyên',
           'Vy', 'Yến', 'Hạnh'),
}

#: Hai lớp mẫu. `khoa` None = lớp ôn cả ba hợp phần.
LOP = (
    {'ma': 'HSA-MAU-01', 'ten': 'Luyện HSA đợt 1/2027 — Ca chiều (lớp mẫu)',
     'lich': 'Thứ 2, 4 · 17:30–19:00', 'thu': (0, 2), 'gio': time(17, 30), 'phut': 90,
     'khoa': 'hsa_quantitative', 'so_em': 26},
    {'ma': 'HSA-MAU-02', 'ten': 'Tăng tốc HSA cuối tuần (lớp mẫu)',
     'lich': 'Thứ 7, CN · 08:30–10:30', 'thu': (5, 6), 'gio': time(8, 30), 'phut': 120,
     'khoa': None, 'so_em': 22},
)
TAT_CA_KHOA = ('hsa_quantitative', 'hsa_verbal', 'hsa_science')

#: Độ khó tương đối của chủ đề (âm = khó hơn). Không có trong bảng = 0.
DO_KHO = {
    'Giải tích': -0.12, 'Hình học': -0.08, 'Thống kê & Xác suất': -0.04, 'Hàm số': -0.03,
    'Số học': 0.05, 'Chiến thuật': 0.06, 'Đọc hiểu': -0.05, 'Văn học': -0.06,
    'Vật lý': -0.08, 'Hóa học': -0.07, 'Từ vựng': 0.04,
}

#: Năm bài tự luận mỗi lớp: (khoá, chủ đề, tiêu đề).
BAI_TU_LUAN = {
    'HSA-MAU-01': (
        ('hsa_quantitative', 'Đại số', 'Giải phương trình chứa căn — trình bày đủ điều kiện'),
        ('hsa_quantitative', 'Hàm số', 'Khảo sát và đọc đồ thị hàm bậc ba'),
        ('hsa_quantitative', 'Hình học', 'Tính góc và khoảng cách trong hình chóp'),
        ('hsa_quantitative', 'Thống kê & Xác suất', 'Đọc biểu đồ và tính xác suất có điều kiện'),
        ('hsa_quantitative', 'Giải tích', 'Ứng dụng tích phân tính diện tích hình phẳng'),
    ),
    'HSA-MAU-02': (
        ('hsa_verbal', 'Đọc hiểu', 'Tóm tắt luận điểm của một văn bản nghị luận'),
        ('hsa_quantitative', 'Hình học', 'Hệ thức lượng trong tam giác'),
        ('hsa_science', 'Vật lý', 'Giải thích hiện tượng bằng định luật bảo toàn'),
        ('hsa_verbal', 'Văn học', 'Phân tích hình ảnh trong một đoạn thơ'),
        ('hsa_quantitative', 'Thống kê & Xác suất', 'Đọc số liệu và rút ra kết luận'),
    ),
}
NHAN_XET = (
    'Trình bày rõ ràng; còn thiếu câu kết luận ở cuối.',
    'Đúng hướng, sai dấu ở bước biến đổi thứ hai — xem lại quy tắc chuyển vế.',
    'Lập luận chặt. Có thể rút gọn phần tính toán trung gian.',
    'Thiếu điều kiện xác định ở đầu bài.',
    'Ý chính đủ, nhưng dẫn chứng chưa bám văn bản.',
    'Làm tốt. Thử thêm cách giải thứ hai để tiết kiệm thời gian.',
)
SO_DAU_BAI = (
    'Chữa bài tuần trước; lớp còn chậm ở bước đặt ẩn.',
    'Luyện dạng bài {chu_de} có bấm giờ — khoảng 2/3 lớp kịp giờ.',
    'Ôn lý thuyết {chu_de}, làm 10 câu trắc nghiệm tại lớp.',
    'Chữa đề thi thử phần {chu_de}; nhắc lại mẹo loại trừ đáp án.',
)

#: Danh mục đơn vị kiến thức của tờ báo cáo thi thật (hệ thống khảo thí TopHSA dùng).
#: Chỉ là DANH MỤC — không mang dữ liệu của em nào.
DON_VI = (
    (1, 'Định lượng và Xử lí số liệu', 'Phương trình, bất phương trình của các hàm số cơ bản'),
    (1, 'Định lượng và Xử lí số liệu', 'Thống kê'),
    (1, 'Định lượng và Xử lí số liệu', 'Hệ thức lượng trong tam giác, hình học Oxy'),
    (1, 'Định lượng và Xử lí số liệu', 'Dãy số, cấp số cộng, cấp số nhân, giới hạn, liên tục'),
    (1, 'Định lượng và Xử lí số liệu', 'Hàm số, đồ thị và các yếu tố liên quan'),
    (1, 'Định lượng và Xử lí số liệu', 'Hình học Oxyz'),
    (1, 'Định lượng và Xử lí số liệu', 'Hình học không gian'),
    (1, 'Định lượng và Xử lí số liệu', 'Số học, đại số tổ hợp và xác suất'),
    (1, 'Định lượng và Xử lí số liệu', 'Nguyên hàm, tích phân và ứng dụng'),
    (2, 'Định tính', 'Văn bản nghị luận'),
    (2, 'Định tính', 'Văn bản thông tin'),
    (2, 'Định tính', 'Văn bản văn học'),
    (2, 'Định tính', 'Ngôn ngữ - Tiếng việt'),
    (3, 'Tổ hợp', 'Antonyms'),
    (3, 'Tổ hợp', 'Cloze text'),
    (3, 'Tổ hợp', 'Dialogue arrangement'),
    (3, 'Tổ hợp', 'Sentence combination'),
    (3, 'Tổ hợp', 'Synonyms'),
    (3, 'Tổ hợp', 'Sentence completion'),
    (3, 'Tổ hợp', 'Logical thinking and problem solving'),
    (3, 'Tổ hợp', 'Dialogue completion'),
    (3, 'Tổ hợp', 'Sentence rewriting'),
    (3, 'Tổ hợp', 'Reading comprehension 2'),
    (3, 'Tổ hợp', 'Reading comprehension 1'),
)
TEN_PHAN = {1: 'Định lượng và Xử lí số liệu', 2: 'Định tính', 3: 'Tiếng Anh'}

#: Đếm theo từng loại dòng — MỘT câu truy vấn cho cả bảng.
BANG_DEM = (
    ('tài khoản mẫu', 'SELECT COUNT(*) FROM users WHERE is_demo'),
    ('lớp mẫu', 'SELECT COUNT(*) FROM classes WHERE is_demo'),
    ('buổi học', 'SELECT COUNT(*) FROM class_sessions s JOIN classes c ON c.id = s.class_id WHERE c.is_demo'),
    ('điểm danh', 'SELECT COUNT(*) FROM attendance a JOIN users u ON u.id = a.user_id WHERE u.is_demo'),
    ('bài tập', 'SELECT COUNT(*) FROM assignments a JOIN classes c ON c.id = a.class_id WHERE c.is_demo'),
    ('bài nộp', 'SELECT COUNT(*) FROM submissions s JOIN users u ON u.id = s.user_id WHERE u.is_demo'),
    ('tiến độ bài học', 'SELECT COUNT(*) FROM lesson_progress p JOIN users u ON u.id = p.user_id WHERE u.is_demo'),
    ('ghi danh', 'SELECT COUNT(*) FROM enrollments e JOIN users u ON u.id = e.user_id WHERE u.is_demo'),
    ('sự kiện học tập', 'SELECT COUNT(*) FROM learning_events e JOIN users u ON u.id = e.user_id WHERE u.is_demo'),
    ('lượt thi thử', 'SELECT COUNT(*) FROM mock_attempts m JOIN users u ON u.id = m.user_id WHERE u.is_demo'),
    ('kết quả thi tại trung tâm',
     'SELECT COUNT(*) FROM ket_qua_thi_ngoai k JOIN users u ON u.id = k.user_id WHERE u.is_demo'),
    ('nhật ký XP ngày', 'SELECT COUNT(*) FROM user_daily_xp_logs l JOIN users u ON u.id = l.user_id WHERE u.is_demo'),
)


class LoiDuLieuMau(Exception):
    """Không dựng / không gỡ được — thông điệp viết cho người chạy lệnh."""


def dem():
    """Số dòng dữ liệu mẫu theo từng loại. MỘT câu truy vấn."""
    r = q1('SELECT ' + ', '.join('(%s) AS c%d' % (sql, i) for i, (_, sql) in enumerate(BANG_DEM)))
    return {ten: r['c%d' % i] for i, (ten, _) in enumerate(BANG_DEM)}


def _kep(v, thap, cao):
    return max(thap, min(cao, v))


def ke_hoach(so_em_moi_lop=None, hat_giong=HAT_GIONG):
    """Phần THUẦN của bộ dữ liệu: ai, tên gì, học giỏi tới đâu. Không chạm CSDL.

    Tách riêng để phép kiểm soi được tính tất định mà không phải dựng cả trung tâm.
    """
    rng = random.Random(hat_giong)
    da_dung = set()
    ket = []
    for i, spec in enumerate(LOP, 1):
        n = so_em_moi_lop or spec['so_em']
        ds = []
        while len(ds) < n:
            gioi = rng.choice(('nam', 'nu'))
            ho_ten = '%s %s %s' % (rng.choice(HO), rng.choice(DEM[gioi]), rng.choice(TEN[gioi]))
            if ho_ten in da_dung:
                continue
            da_dung.add(ho_ten)
            k = len(ds) + 1
            ds.append({
                'ho_ten': ho_ten,
                'email': 'hv.mau.%d%02d%s' % (i, k, DUOI_EMAIL),
                'phu_huynh': '%s %s %s' % (rng.choice(HO), rng.choice(DEM['nu']), rng.choice(TEN['nu'])),
                'email_ph': 'phuhuynh.mau.%d%02d%s' % (i, k, DUOI_EMAIL),
                'nang_luc': _kep(rng.gauss(0.62, 0.14), 0.32, 0.92),
                'chuyen_can': _kep(rng.gauss(0.88, 0.08), 0.62, 0.99),
                'ma': 'MAU%d%03d' % (i, k),
            })
        ket.append({**spec, 'hoc_vien': ds})
    return ket


def _chon_giang_vien(giang_vien_id):
    if giang_vien_id:
        gv = q1('SELECT id, role FROM users WHERE id=%s AND NOT is_demo', (giang_vien_id,))
        if not gv:
            raise LoiDuLieuMau('Không có tài khoản #%s (hoặc đó là tài khoản mẫu).' % giang_vien_id)
        return gv['id']
    gv = q1('''SELECT id FROM users WHERE role=%s AND status='active' AND NOT is_demo
               ORDER BY id LIMIT 1''', (ROLE_TEACHER,))
    if not gv:
        raise LoiDuLieuMau('Chưa có tài khoản Giảng viên nào để phụ trách lớp mẫu — '
                           'tạo một tài khoản hoặc truyền --giang-vien.')
    return gv['id']


def tao(giang_vien_id=None, so_em_moi_lop=None, hom_nay=None, hat_giong=HAT_GIONG):
    """Dựng bộ dữ liệu mẫu trong MỘT giao dịch. Trả `dem()` sau khi dựng."""
    if hom_nay is None:
        hom_nay, bay_gio = local_today(), local_now()
    else:
        bay_gio = datetime.combine(hom_nay, time(21, 0))
    rng = random.Random(hat_giong + 1)

    with transaction.atomic():
        co_san = dem()
        if co_san['tài khoản mẫu'] or co_san['lớp mẫu']:
            raise LoiDuLieuMau('Đã có dữ liệu mẫu (%d tài khoản, %d lớp) — chạy --go trước.'
                               % (co_san['tài khoản mẫu'], co_san['lớp mẫu']))
        gv = _chon_giang_vien(giang_vien_id)
        dot = q1("SELECT id, exam_date FROM terms WHERE status='active' "
                 "ORDER BY starts_on DESC NULLS LAST LIMIT 1")
        bai_theo_khoa = defaultdict(list)
        for b in q('''SELECT id, course_id, module, sort_order, title FROM lessons
                      WHERE course_id = ANY(%s) ORDER BY course_id, sort_order''',
                   (list(TAT_CA_KHOA),)):
            bai_theo_khoa[b['course_id']].append(b)
        tong_bai = {r['id']: r['lessons'] for r in q(
            'SELECT id, lessons FROM courses WHERE id = ANY(%s)', (list(TAT_CA_KHOA),))}
        de = q1('SELECT id, questions_json FROM mock_exams WHERE is_published ORDER BY id LIMIT 1')

        ke = ke_hoach(so_em_moi_lop, hat_giong)
        bat_dau = hom_nay - timedelta(weeks=6)
        bat_dau -= timedelta(days=bat_dau.weekday())
        ket_thuc = bat_dau + timedelta(weeks=12)
        vao_lop = datetime.combine(bat_dau - timedelta(days=3), time(9, 0))
        su_kien = []

        # ── Tài khoản ────────────────────────────────────────────────────
        tat_ca = [e for lop in ke for e in lop['hoc_vien']]
        id_theo_email = {r['email']: r['id'] for r in q(
            '''INSERT INTO users (name, email, password, role, status, parent_name,
                                  parent_phone, parent_email, is_demo,
                                  questionnaire_completed, created_at)
               SELECT t.n, t.e, %s, %s, 'active', t.ph, '', t.eph, TRUE, 1, %s
                 FROM unnest(%s::text[], %s::text[], %s::text[], %s::text[]) AS t(n, e, ph, eph)
               RETURNING id, email''',
            # Bản băm scrypt THẬT của một chuỗi ngẫu nhiên sinh ngay tại đây rồi bỏ đi
            # — xem luật 3 ở đầu tệp: một chuỗi thô ở đây chính là mật khẩu.
            (make_werkzeug_password(secrets.token_urlsafe(32)), ROLE_STUDENT, vao_lop,
             [e['ho_ten'] for e in tat_ca], [e['email'] for e in tat_ca],
             [e['phu_huynh'] for e in tat_ca], [e['email_ph'] for e in tat_ca]))}
        for e in tat_ca:
            e['id'] = id_theo_email[e['email']]
        # Ba vai nhân sự — cùng luật 1 và 3 với học viên mẫu (đánh dấu, không
        # đăng nhập được). Không có liên hệ phụ huynh: họ không phải học viên.
        nhan_su = {r['role']: r['id'] for r in q(
            '''INSERT INTO users (name, email, password, role, status, parent_phone,
                                  is_demo, questionnaire_completed, created_at)
               SELECT t.n, t.e, %s, t.r, 'active', '', TRUE, 1, %s
                 FROM unnest(%s::text[], %s::text[], %s::text[]) AS t(n, e, r)
               RETURNING id, role''',
            (make_werkzeug_password(secrets.token_urlsafe(32)), vao_lop,
             [n for n, _, _ in NHAN_SU_MAU], [e for _, e, _ in NHAN_SU_MAU],
             [r for _, _, r in NHAN_SU_MAU]))}

        # ── Lớp + thành viên ─────────────────────────────────────────────
        id_theo_ma = {r['code']: r['id'] for r in q(
            '''INSERT INTO classes (code, name, course_id, teacher_id, schedule, starts_on,
                                    ends_on, exam_date, capacity, status, note, term_id, is_demo)
               SELECT t.ma, t.ten, t.khoa, %s, t.lich, %s, %s, %s, 30, 'active', %s, %s, TRUE
                 FROM unnest(%s::text[], %s::text[], %s::text[], %s::text[]) AS t(ma, ten, khoa, lich)
               RETURNING id, code''',
            (gv, bat_dau, ket_thuc, (dot or {}).get('exam_date') or hom_nay + timedelta(days=80),
             'Dữ liệu trình diễn — gỡ bằng: python manage.py du_lieu_mau --go',
             (dot or {}).get('id'),
             [lop['ma'] for lop in ke], [lop['ten'] for lop in ke],
             [lop['khoa'] for lop in ke], [lop['lich'] for lop in ke]))}
        for lop in ke:
            lop['id'] = id_theo_ma[lop['ma']]
        x('''INSERT INTO class_members (class_id, user_id, joined_at)
             SELECT t.c, t.u, %s FROM unnest(%s::int[], %s::int[]) AS t(c, u)''',
          (vao_lop, [lop['id'] for lop in ke for _ in lop['hoc_vien']],
           [e['id'] for lop in ke for e in lop['hoc_vien']]))
        # Trợ giảng mẫu vào lớp mẫu thứ nhất — đúng cách `can_see_class` nhận ra
        # trợ giảng (một dòng `class_members`, `left_at IS NULL`), và `chi_hoc_vien`
        # lọc theo vai nên dòng này không lọt vào sĩ số hay bảng điểm danh.
        x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, %s)',
          (ke[0]['id'], nhan_su[ROLE_ASSISTANT], vao_lop))

        # ── Buổi học + điểm danh ─────────────────────────────────────────
        buoi = []
        for lop in ke:
            khoa = [lop['khoa']] if lop['khoa'] else list(TAT_CA_KHOA)
            chu_de = []
            for k in khoa:
                for b in bai_theo_khoa[k]:
                    if b['module'] and b['module'] not in chu_de:
                        chu_de.append(b['module'])
            chu_de = chu_de or ['Ôn tập tổng hợp']
            d, j = bat_dau, 0
            while d <= ket_thuc:
                if d.weekday() in lop['thu']:
                    bat = datetime.combine(d, lop['gio'])
                    xong = bat + timedelta(minutes=lop['phut'])
                    da_day = xong <= bay_gio
                    cd = chu_de[j % len(chu_de)]
                    buoi.append({
                        'lop': lop, 'bat': bat, 'phut': lop['phut'], 'chu_de': cd,
                        'trang_thai': 'done' if da_day else 'planned',
                        'ghi_chu': rng.choice(SO_DAU_BAI).format(chu_de=cd) if da_day else None,
                        'tick': xong + timedelta(minutes=5) if da_day else None,
                    })
                    j += 1
                d += timedelta(days=1)
        id_buoi = {(r['class_id'], r['starts_at']): r['id'] for r in q(
            '''INSERT INTO class_sessions (class_id, starts_at, duration_minutes, topic, status,
                                           note, created_by, attendance_taken_at,
                                           attendance_taken_by)
               SELECT t.c, t.bat, t.phut, t.cd, t.tt, t.gc, %s, t.tick,
                      CASE WHEN t.tick IS NULL THEN NULL ELSE %s END
                 FROM unnest(%s::int[], %s::timestamp[], %s::int[], %s::text[], %s::text[],
                             %s::text[], %s::timestamp[]) AS t(c, bat, phut, cd, tt, gc, tick)
               RETURNING id, class_id, starts_at''',
            (gv, gv, [b['lop']['id'] for b in buoi], [b['bat'] for b in buoi],
             [b['phut'] for b in buoi], [b['chu_de'] for b in buoi],
             [b['trang_thai'] for b in buoi], [b['ghi_chu'] for b in buoi],
             [b['tick'] for b in buoi]))}
        dd = []
        for b in buoi:
            if b['trang_thai'] != 'done':
                continue
            sid = id_buoi[(b['lop']['id'], b['bat'])]
            for e in b['lop']['hoc_vien']:
                if rng.random() < e['chuyen_can']:
                    tt = 'late' if rng.random() < 0.07 else 'present'
                else:
                    tt = 'excused' if rng.random() < 0.4 else 'absent'
                dd.append((sid, e['id'], tt, b['tick']))
                su_kien.append({
                    'uid': e['id'], 'kind': KIND_ATTENDANCE, 'dedup_key': 'attendance:%s' % sid,
                    'occurred_at': b['bat'], 'event_date': b['bat'].date(),
                    'course_id': b['lop']['khoa'], 'topic': b['chu_de'],
                    'ref_type': 'class_session', 'ref_id': sid, 'minutes': None, 'xp': 0,
                    'source': SOURCE_SYSTEM,
                    'meta': {'attendance': tt, 'minutes': None, 'class_id': b['lop']['id']},
                })
        if dd:
            x('''INSERT INTO attendance (session_id, user_id, status, marked_by, marked_at)
                 SELECT t.s, t.u, t.tt, %s, t.luc
                   FROM unnest(%s::int[], %s::int[], %s::text[], %s::timestamp[]) AS t(s, u, tt, luc)''',
              (gv, [r[0] for r in dd], [r[1] for r in dd], [r[2] for r in dd], [r[3] for r in dd]))

        # ── Bài tự luận + bài nộp ────────────────────────────────────────
        bai = []
        for lop in ke:
            ds_bai = BAI_TU_LUAN[lop['ma']]
            for i, (khoa, cd, tieu_de) in enumerate(ds_bai):
                han = (datetime.combine(hom_nay + timedelta(days=4), time(23, 59))
                       if i == len(ds_bai) - 1
                       else datetime.combine(bat_dau + timedelta(days=9 + 7 * i), time(23, 59)))
                bai.append({'lop': lop, 'khoa': khoa, 'cd': cd, 'tieu_de': tieu_de, 'han': han,
                            'tt': 'closed' if han < bay_gio else 'open',
                            'tao_luc': han - timedelta(days=7)})
        id_bai = {(r['class_id'], r['title']): r['id'] for r in q(
            '''INSERT INTO assignments (class_id, title, description, topic, course_id, due_at,
                                        max_score, status, created_by, created_at)
               SELECT t.c, t.td, %s, t.cd, t.k, t.han, 10, t.tt, %s, t.tao
                 FROM unnest(%s::int[], %s::text[], %s::text[], %s::text[], %s::timestamp[],
                             %s::text[], %s::timestamp[]) AS t(c, td, cd, k, han, tt, tao)
               RETURNING id, class_id, title''',
            ('Bài tự luận trong bộ dữ liệu trình diễn.', gv,
             [b['lop']['id'] for b in bai], [b['tieu_de'] for b in bai], [b['cd'] for b in bai],
             [b['khoa'] for b in bai], [b['han'] for b in bai], [b['tt'] for b in bai],
             [b['tao_luc'] for b in bai]))}
        nop = []
        for b in bai:
            aid = id_bai[(b['lop']['id'], b['tieu_de'])]
            for e in b['lop']['hoc_vien']:
                if b['tt'] == 'closed':
                    if rng.random() >= 0.72 + 0.25 * e['chuyen_can']:
                        continue
                    luc_nop = b['han'] - timedelta(hours=rng.randint(2, 70))
                    diem = _kep(round((e['nang_luc'] + DO_KHO.get(b['cd'], 0)
                                       + rng.gauss(0, 0.12)) * 20) / 2, 2.0, 10.0)
                    cham = b['han'] + timedelta(days=rng.randint(1, 3), hours=rng.randint(0, 5))
                    if cham > bay_gio:
                        diem, cham = None, None
                else:
                    if rng.random() >= 0.4:
                        continue
                    luc_nop = max(b['tao_luc'] + timedelta(hours=6),
                                  bay_gio - timedelta(hours=rng.randint(1, 60)))
                    diem, cham = None, None
                nop.append((aid, e['id'], luc_nop, diem,
                            rng.choice(NHAN_XET) if diem is not None else None, cham))
                if diem is not None:
                    su_kien.append({
                        'uid': e['id'], 'kind': KIND_ASSIGNMENT, 'dedup_key': 'assignment:%s' % aid,
                        'occurred_at': cham, 'event_date': cham.date(),
                        'course_id': b['khoa'], 'topic': b['cd'],
                        'ref_type': 'assignment', 'ref_id': aid,
                        'score': diem, 'max_score': 10, 'minutes': None, 'xp': 0,
                        'source': SOURCE_SYSTEM,
                        'meta': {'title': b['tieu_de'], 'classId': b['lop']['id']},
                    })
        if nop:
            x('''INSERT INTO submissions (assignment_id, user_id, submitted_at, content, score,
                                          feedback, graded_by, graded_at)
                 SELECT t.a, t.u, t.nop, %s, t.diem, t.nx,
                        CASE WHEN t.cham IS NULL THEN NULL ELSE %s END, t.cham
                   FROM unnest(%s::int[], %s::int[], %s::timestamp[], %s::numeric[],
                               %s::text[], %s::timestamp[]) AS t(a, u, nop, diem, nx, cham)''',
              ('Bài làm trong bộ dữ liệu trình diễn.', gv,
               [r[0] for r in nop], [r[1] for r in nop], [r[2] for r in nop],
               [r[3] for r in nop], [r[4] for r in nop], [r[5] for r in nop]))

        # ── Bài học đã học (+ phòng luyện) ───────────────────────────────
        tien_do, xp_ngay, cap_ghi_danh = [], defaultdict(int), set()
        so_ngay = max(1, (hom_nay - bat_dau).days - 1)
        for lop in ke:
            khoa = [lop['khoa']] if lop['khoa'] else list(TAT_CA_KHOA)
            for e in lop['hoc_vien']:
                hop = {}
                ds_hoc = []
                for k in khoa:
                    n = len(bai_theo_khoa[k])
                    if not n:
                        continue
                    so = (round(3 + e['nang_luc'] * 24 + rng.gauss(0, 2)) if lop['khoa']
                          else round(1 + e['nang_luc'] * 13 + rng.gauss(0, 2)))
                    ds_hoc.extend(bai_theo_khoa[k][:_kep(so, 1, n)])
                    cap_ghi_danh.add((e['id'], k))
                for j, b in enumerate(ds_hoc):
                    ngay = bat_dau + timedelta(days=_kep(
                        round((j + 1) * so_ngay / (len(ds_hoc) + 1)) + rng.randint(-1, 1), 1, so_ngay))
                    luc = datetime.combine(ngay, time(rng.randint(19, 22), rng.randint(0, 59)))
                    cd = b['module'] or None
                    hop.setdefault(cd, rng.gauss(0, 0.08))
                    muc = e['nang_luc'] + DO_KHO.get(cd, 0) + hop[cd]
                    diem = _kep(round((muc + rng.gauss(0, 0.1)) * 10) * 10, 20, 100)
                    tien_do.append((e['id'], b['id'], b['course_id'], diem, luc))
                    xp_ngay[(e['id'], ngay)] += XP_BAI_HOC
                    su_kien.append({
                        'uid': e['id'], 'kind': KIND_LESSON, 'dedup_key': 'lesson:%s' % b['id'],
                        'occurred_at': luc, 'event_date': ngay, 'course_id': b['course_id'],
                        'topic': cd, 'ref_type': 'lesson', 'ref_id': str(b['id']),
                        'score': diem, 'max_score': 100, 'xp': XP_BAI_HOC, 'source': SOURCE_SYSTEM,
                        'meta': {'lessonNo': b['sort_order'], 'title': b['title'] or ''},
                    })
                    if rng.random() < 0.6:
                        dung = _kep(round((muc + rng.gauss(0, 0.12)) * 10), 0, 10)
                        su_kien.append({
                            'uid': e['id'], 'kind': KIND_DRILL, 'dedup_key': 'drill:%s' % b['id'],
                            'occurred_at': luc + timedelta(minutes=2), 'event_date': ngay,
                            'course_id': b['course_id'], 'topic': cd,
                            'ref_type': 'lesson', 'ref_id': str(b['id']),
                            'score': dung, 'max_score': 10, 'minutes': rng.randint(4, 9),
                            'xp': 0, 'source': SOURCE_SYSTEM,
                            'meta': {'lessonNo': b['sort_order'],
                                     'maxCombo': rng.randint(1, dung) if dung else 0,
                                     'answered': _kep(dung + rng.randint(0, 3), dung, 10)},
                        })
        if tien_do:
            x('''INSERT INTO lesson_progress (user_id, lesson_id, course_id, status, quiz_score,
                                              xp_earned, completed_at)
                 SELECT t.u, t.l, t.k, 'completed', t.d, %s, t.luc
                   FROM unnest(%s::int[], %s::int[], %s::text[], %s::int[], %s::timestamp[])
                        AS t(u, l, k, d, luc)''',
              (XP_BAI_HOC, [r[0] for r in tien_do], [r[1] for r in tien_do],
               [r[2] for r in tien_do], [r[3] for r in tien_do], [r[4] for r in tien_do]))
        if cap_ghi_danh:
            cap = sorted(cap_ghi_danh)
            x('''INSERT INTO enrollments (user_id, course_id, progress, completed_lessons,
                                          time_spent, last_lesson, next_lesson, enrolled_at)
                 SELECT t.u, t.k, 0, 0, '0h', '', '', %s
                   FROM unnest(%s::int[], %s::text[]) AS t(u, k)
                 ON CONFLICT (user_id, course_id) DO NOTHING''',
              (vao_lop, [c[0] for c in cap], [c[1] for c in cap]))
            # MỘT chỗ tính bộ đệm tiến độ — xem docstring `courses/enrollment.py`.
            from courses.enrollment import tinh_lai
            for uid, k in cap:
                tinh_lai(uid, k, tong_bai.get(k))

        # ── Thi thử trong ứng dụng ───────────────────────────────────────
        if de:
            from mockexam.views import SECTION_COURSE, SECTION_LABELS, _mock_xp
            cau = de['questions_json']
            cau = json.loads(cau) if isinstance(cau, str) else (cau or [])
            so_cau = defaultdict(int)
            for c in cau:
                so_cau[c.get('section')] += 1
            tong = sum(so_cau.values())
            luot = []
            for e in tat_ca:
                if not tong or rng.random() >= 0.8:
                    continue
                nop_luc = datetime.combine(
                    bat_dau + timedelta(days=rng.randint(14, max(14, so_ngay))), time(20, rng.randint(0, 50)))
                giay = rng.randint(780, 1180)
                dung = {s: sum(rng.random() < _kep(e['nang_luc'] + rng.gauss(0, 0.08), 0.05, 0.98)
                               for _ in range(n)) for s, n in so_cau.items()}
                diem = sum(dung.values())
                luot.append({'e': e, 'nop': nop_luc, 'giay': giay, 'dung': dung, 'diem': diem,
                             'xp': _mock_xp(diem, tong)})
            if luot:
                id_luot = {r['user_id']: r['id'] for r in q(
                    '''INSERT INTO mock_attempts (user_id, exam_id, score, total, section_scores_json,
                                                  answers_json, duration_seconds, started_at,
                                                  submitted_at, counted)
                       SELECT t.u, %s, t.d, %s, t.ss::jsonb, '{}'::jsonb, t.g,
                              t.nop - make_interval(secs => t.g), t.nop, TRUE
                         FROM unnest(%s::int[], %s::int[], %s::text[], %s::int[], %s::timestamp[])
                              AS t(u, d, ss, g, nop)
                       RETURNING id, user_id''',
                    (de['id'], tong, [r['e']['id'] for r in luot], [r['diem'] for r in luot],
                     [json.dumps({SECTION_LABELS.get(s, s): {'correct': r['dung'][s], 'total': n}
                                  for s, n in so_cau.items()}, ensure_ascii=False) for r in luot],
                     [r['giay'] for r in luot], [r['nop'] for r in luot]))}
                for r in luot:
                    aid, uid = id_luot[r['e']['id']], r['e']['id']
                    xp_ngay[(uid, r['nop'].date())] += r['xp']
                    su_kien.append({
                        'uid': uid, 'kind': KIND_MOCK, 'dedup_key': 'mock:%s' % aid,
                        'occurred_at': r['nop'], 'event_date': r['nop'].date(),
                        'ref_type': 'mock_attempt', 'ref_id': str(aid),
                        'score': r['diem'], 'max_score': tong,
                        'minutes': max(1, round(r['giay'] / 60)), 'xp': r['xp'],
                        'source': SOURCE_SYSTEM, 'meta': {'examId': de['id']},
                    })
                    for s, n in so_cau.items():
                        khoa = SECTION_COURSE.get(s)
                        if not khoa or not n:
                            continue
                        su_kien.append({
                            'uid': uid, 'kind': KIND_MOCK_SECTION,
                            'dedup_key': 'mocksec:%s:%s' % (aid, khoa),
                            'occurred_at': r['nop'], 'event_date': r['nop'].date(),
                            'course_id': khoa, 'ref_type': 'mock_attempt', 'ref_id': str(aid),
                            'score': r['dung'][s], 'max_score': n, 'xp': 0, 'source': SOURCE_SYSTEM,
                            'meta': {'examId': de['id'], 'section': SECTION_LABELS.get(s, s)},
                        })

        # ── Hai kỳ thi thử tại trung tâm (§48) ───────────────────────────
        ky = [(hom_nay - timedelta(days=24), 'Thi thử tại trung tâm lần 1'),
              (hom_nay - timedelta(days=3), 'Thi thử tại trung tâm lần 2')]
        kq = []
        for e in tat_ca:
            tien_bo = rng.gauss(0.045, 0.035)
            for i, (ngay, dot_thi) in enumerate(ky):
                if ngay < bat_dau or rng.random() >= 0.9:
                    continue
                muc = e['nang_luc'] + (tien_bo if i else 0)
                phan = {p: muc + {1: -0.04, 2: 0.03, 3: 0.0}[p] + rng.gauss(0, 0.06) for p in (1, 2, 3)}
                diem_phan = [{'phan': p, 'ten': TEN_PHAN[p],
                              'diem': _kep(round(50 * phan[p] + rng.gauss(0, 1.5)), 4, 50), 'toiDa': 50}
                             for p in (1, 2, 3)]
                don_vi = [{'phan': p, 'phanTen': pt, 'ten': ten,
                           'pct': _kep(round(100 * (phan[p] + rng.gauss(0, 0.16))), 0, 100)}
                          for p, pt, ten in DON_VI]
                kq.append((e['id'], ngay, dot_thi, e['ma'], sum(d['diem'] for d in diem_phan),
                           json.dumps(diem_phan, ensure_ascii=False),
                           json.dumps(don_vi, ensure_ascii=False), e['ho_ten']))
        if kq:
            x('''INSERT INTO ket_qua_thi_ngoai (user_id, ngay_thi, dot, ma_hoc_sinh, hinh_thuc,
                                                dia_diem, tong_diem, tong_toi_da, diem_phan,
                                                don_vi, ten_tren_to, nhap_boi)
                 SELECT t.u, t.ngay, t.dot, t.ma, 'Offline', %s, t.tong, 150, t.dp::jsonb,
                        t.dv::jsonb, t.ten, %s
                   FROM unnest(%s::int[], %s::date[], %s::text[], %s::text[], %s::int[],
                               %s::text[], %s::text[], %s::text[]) AS t(u, ngay, dot, ma, tong, dp, dv, ten)''',
              ('Trung tâm (dữ liệu mẫu)', gv, *[[r[i] for r in kq] for i in range(8)]))

        # ── XP, chuỗi ngày học, nhật ký XP ngày (nguồn BXH tuần) ─────────
        if xp_ngay:
            khoa_xp = sorted(xp_ngay)
            x('''INSERT INTO user_daily_xp_logs (user_id, log_date, xp_earned)
                 SELECT t.u, t.ngay, t.xp FROM unnest(%s::int[], %s::date[], %s::int[]) AS t(u, ngay, xp)''',
              ([k[0] for k in khoa_xp], [k[1] for k in khoa_xp], [xp_ngay[k] for k in khoa_xp]))
            ngay_hoc = defaultdict(set)
            for uid, ngay in xp_ngay:
                ngay_hoc[uid].add(ngay)
            nguoi = sorted(ngay_hoc)
            tong_xp, cuoi, chuoi = [], [], []
            for uid in nguoi:
                ngay_cuoi = max(ngay_hoc[uid])
                n = 0
                if ngay_cuoi >= hom_nay - timedelta(days=1):
                    while ngay_cuoi - timedelta(days=n) in ngay_hoc[uid]:
                        n += 1
                tong_xp.append(sum(v for (u, _), v in xp_ngay.items() if u == uid))
                cuoi.append(ngay_cuoi)
                chuoi.append(n)
            x('''UPDATE users u SET xp = t.xp, gems = t.xp, last_study_date = t.cuoi, streak = t.chuoi
                   FROM unnest(%s::int[], %s::int[], %s::date[], %s::int[]) AS t(id, xp, cuoi, chuoi)
                  WHERE u.id = t.id''', (nguoi, tong_xp, cuoi, chuoi))

        # ── Sự kiện học tập: MỘT cửa ghi, và phải ghi ĐỦ ─────────────────
        # `record_events` nuốt dòng hỏng (đúng cho đường của người dùng: một sự
        # kiện hỏng không được làm hỏng lượt lưu điểm danh). Ở đây thì khác: thiếu
        # một dòng là bản đồ năng lực của em ấy lệch mà không ai biết — nên đếm, và
        # thiếu thì huỷ CẢ giao dịch.
        can_ghi = len({(e['uid'], e['dedup_key']) for e in su_kien})
        da_ghi = record_events(su_kien)
        if da_ghi != can_ghi:
            raise LoiDuLieuMau('Chỉ ghi được %d/%d sự kiện học tập — đã huỷ toàn bộ, xem log.'
                               % (da_ghi, can_ghi))
        return dem()


def hoat_dong_gan_nhat():
    """Ngày của sự kiện học tập mẫu gần nhất, hoặc None khi chưa có dữ liệu mẫu.

    Đọc SỰ KIỆN chứ không đọc ngày tạo lớp: thứ làm màn hình trông cũ là hoạt động
    của học viên dừng lại, không phải lớp được tạo từ bao giờ."""
    r = q1('''SELECT MAX(e.event_date) AS d FROM learning_events e
                JOIN users u ON u.id = e.user_id WHERE u.is_demo''')
    return r['d'] if r else None


def lam_moi(giang_vien_id=None, so_em_moi_lop=None):
    """Gỡ rồi dựng lại bộ dữ liệu mẫu, neo vào HÔM NAY, trong MỘT giao dịch.

    MỘT giao dịch là điểm chính: `go()` và `tao()` mỗi hàm tự có giao dịch, gọi nối
    tiếp thì một lần dựng hỏng giữa chừng (Neon rớt kết nối, gặp nhiều lần tuần này)
    để lại một trung tâm KHÔNG CÓ lớp mẫu nào — ngay trước buổi trình diễn. Bọc
    ngoài thì hai giao dịch trong thành điểm lưu: dựng hỏng là bộ cũ còn nguyên.

    Giữ giảng viên đang phụ trách lớp mẫu (nếu không truyền): làm mới không được
    lặng lẽ chuyển lớp mẫu sang "Giảng viên đầu tiên" của CSDL.

    Trả `(trước, sau)` như `go()`.
    """
    with transaction.atomic():
        if giang_vien_id is None:
            cu = q1('SELECT teacher_id FROM classes WHERE is_demo AND teacher_id IS NOT NULL '
                    'ORDER BY id LIMIT 1')
            giang_vien_id = cu['teacher_id'] if cu else None
        truoc, _ = go()
        sau = tao(giang_vien_id=giang_vien_id, so_em_moi_lop=so_em_moi_lop)
    return truoc, sau


def go():
    """Gỡ SẠCH dữ liệu mẫu trong MỘT giao dịch. Trả `(trước, sau)`."""
    with transaction.atomic():
        truoc = dem()
        # Hai khoá ngoại tới `users` KHÔNG có ON DELETE: `parent_report_links.created_by`
        # và `parent_report_sends.requested_by`. Tài khoản mẫu không đăng nhập được nên
        # không tự tạo ra chúng — xoá trước vẫn cần, để `--go` không bao giờ gãy giữa chừng.
        x('DELETE FROM parent_report_sends WHERE requested_by IN (SELECT id FROM users WHERE is_demo)')
        x('DELETE FROM parent_report_links WHERE created_by IN (SELECT id FROM users WHERE is_demo)')
        x('DELETE FROM classes WHERE is_demo')
        x('DELETE FROM users WHERE is_demo')
        sau = dem()
    return truoc, sau
