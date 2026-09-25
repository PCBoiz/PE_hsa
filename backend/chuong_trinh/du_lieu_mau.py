"""Khung chương trình MẪU cho bộ dữ liệu trình diễn (`teaching/du_lieu_mau.py`, §49).

Một khung 24 buổi cho môn Toán HSA (`hsa_quantitative`), đánh dấu `is_demo` — gỡ bằng
`go()` của bộ dữ liệu mẫu. Lớp mẫu học môn ấy nhận khung qua ĐÚNG cửa thật
(`dich_vu.nhan_khung`), rồi các buổi đã dạy có sổ đầu bài: đủ để màn "Chương trình
lớp", "Sổ đầu bài", ô tiến độ ở Tổng quan và % của em có số mà xem. Khung thật của
TopHSA do học vụ nhập sau.

Sổ mẫu: mọi buổi đã dạy ghi "đã dạy", TRỪ buổi gần nhất CHƯA ghi sổ (để thấy lời nhắc
"đã dạy mà chưa ghi sổ") và buổi kề trước dạy một phần mục cuối.
"""
from common.db import q, q1, x

#: (tên buổi, [(loại, tên mục, trọng số)…], bài về nhà)
KHUNG_MAU = [
    ('Làm quen đề HSA phần Toán', [('chu_de', 'Cấu trúc đề và cách tính điểm', 1),
                                    ('chu_de', 'Chiến thuật phân bổ thời gian', 1)],
     'Làm 20 câu khởi động'),
    ('Số học: chia hết và đồng dư', [('chu_de', 'Dấu hiệu chia hết', 1),
                                     ('chu_de', 'Đồng dư và số dư', 1)], None),
    ('Đại số: phương trình và bất phương trình', [('chu_de', 'Phương trình chứa căn', 1),
                                                  ('chu_de', 'Bất phương trình bậc hai', 1)],
     'Bộ 15 câu phương trình'),
    ('Đại số: hệ phương trình', [('chu_de', 'Hệ đối xứng', 1), ('bai_tap', 'Luyện tập hệ', 1)],
     None),
    ('Hàm số: đơn điệu và cực trị', [('chu_de', 'Xét tính đơn điệu', 1),
                                    ('chu_de', 'Tìm cực trị', 1)], None),
    ('Hàm số: đồ thị và tương giao', [('chu_de', 'Đọc đồ thị hàm bậc ba', 1),
                                     ('chu_de', 'Số giao điểm', 1)], 'Bộ 20 câu đồ thị'),
    ('Mũ và lôgarit', [('chu_de', 'Tính chất lôgarit', 1),
                       ('chu_de', 'Phương trình mũ', 1)], None),
    ('Kiểm tra giữa chặng 1', [('kiem_tra', 'Bài kiểm tra 45 phút', 2)], None),
    ('Chữa bài kiểm tra và ôn lỗi sai', [('chu_de', 'Chữa đề giữa chặng', 1)], None),
    ('Hình học phẳng: hệ thức lượng', [('chu_de', 'Định lí sin, côsin', 1),
                                      ('chu_de', 'Diện tích tam giác', 1)], None),
    ('Hình học phẳng: toạ độ trong mặt phẳng', [('chu_de', 'Phương trình đường thẳng', 1),
                                              ('chu_de', 'Đường tròn', 1)], 'Bộ 15 câu toạ độ'),
    ('Hình học không gian: góc', [('chu_de', 'Góc giữa đường và mặt', 1),
                                  ('chu_de', 'Góc giữa hai mặt', 1)], None),
    ('Hình học không gian: khoảng cách', [('chu_de', 'Khoảng cách điểm tới mặt', 1),
                                          ('chu_de', 'Khoảng cách hai đường chéo nhau', 1)], None),
    ('Thể tích khối đa diện', [('chu_de', 'Thể tích chóp và lăng trụ', 1),
                               ('bai_tap', 'Luyện tập thể tích', 1)], None),
    ('Toạ độ trong không gian', [('chu_de', 'Mặt phẳng', 1), ('chu_de', 'Mặt cầu', 1)], None),
    ('Kiểm tra giữa chặng 2', [('kiem_tra', 'Bài kiểm tra 45 phút', 2)], None),
    ('Tổ hợp và xác suất', [('chu_de', 'Quy tắc đếm', 1), ('chu_de', 'Xác suất cổ điển', 1)],
     None),
    ('Xác suất có điều kiện', [('chu_de', 'Công thức Bayes', 1)], 'Bộ 10 câu xác suất'),
    ('Thống kê: đọc biểu đồ', [('chu_de', 'Số trung bình, trung vị', 1),
                               ('chu_de', 'Đọc biểu đồ', 1)], None),
    ('Dãy số và cấp số', [('chu_de', 'Cấp số cộng', 1), ('chu_de', 'Cấp số nhân', 1)], None),
    ('Nguyên hàm và tích phân', [('chu_de', 'Tính tích phân', 1),
                                 ('chu_de', 'Diện tích hình phẳng', 1)], None),
    ('Bài toán thực tế', [('chu_de', 'Lãi suất và tăng trưởng', 1),
                          ('chu_de', 'Tối ưu đơn giản', 1)], None),
    ('Luyện đề tổng hợp', [('bai_tap', 'Đề luyện 50 câu', 2)], 'Hoàn thành đề ở nhà'),
    ('Thi thử cuối khoá và dặn dò', [('kiem_tra', 'Thi thử phần Toán', 2)], None),
]
MON_MAU = 'hsa_quantitative'


def dung_khung_mau(lop_ids, nguoi_ghi, bay_gio):
    """Dựng khung mẫu, cho các lớp `lop_ids` (cùng môn `MON_MAU`) nhận nó, ghi sổ mẫu.
    Gọi TRONG giao dịch của `tao()`. Không có môn thì bỏ qua (CSDL chưa seed)."""
    from chuong_trinh.dich_vu import nhan_khung

    if not lop_ids or not q1('SELECT 1 FROM courses WHERE id = %s', (MON_MAU,)):
        return None
    vid = q1('''INSERT INTO syllabus_versions (course_id, name, status, created_by, is_demo)
                VALUES (%s, 'Luyện Toán HSA 24 buổi (khung mẫu)', 'xuat_ban', %s, TRUE)
                RETURNING id''', (MON_MAU, nguoi_ghi))['id']
    ss_ids = [r['id'] for r in q(
        '''INSERT INTO syllabus_sessions (version_id, sort_order, name, duration_minutes, homework)
           SELECT %s, t.so, t.ten, 90, t.bt
             FROM unnest(%s::int[], %s::text[], %s::text[]) AS t(so, ten, bt)
           RETURNING id''',
        (vid, list(range(1, len(KHUNG_MAU) + 1)), [k[0] for k in KHUNG_MAU],
         [k[2] for k in KHUNG_MAU]))]
    muc = [(ss, so, loai, ten, w) for ss, k in zip(ss_ids, KHUNG_MAU, strict=True)
           for so, (loai, ten, w) in enumerate(k[1], 1)]
    x('''INSERT INTO syllabus_items (session_id, sort_order, kind, title, weight)
         SELECT * FROM unnest(%s::int[], %s::int[], %s::text[], %s::text[], %s::numeric[])''',
      tuple(list(c) for c in zip(*muc, strict=True)))

    for lop in lop_ids:
        nhan_khung(lop, vid)
    # Buổi đã dạy, đã gắn khung: sổ mẫu (xem docstring đầu tệp).
    da_day = q('''SELECT cs.id, cs.class_id, cs.syllabus_session_id,
                         ROW_NUMBER() OVER (PARTITION BY cs.class_id
                                            ORDER BY cs.starts_at DESC) AS lui
                    FROM class_sessions cs
                   WHERE cs.class_id = ANY(%s) AND cs.syllabus_session_id IS NOT NULL
                     AND cs.status <> 'cancelled' AND cs.starts_at <= %s''',
                (list(lop_ids), bay_gio))
    ghi = [b for b in da_day if b['lui'] > 1]
    if not ghi:
        return vid
    x('''INSERT INTO session_logs (session_id, comprehension, logged_by, logged_at)
         SELECT t.s, t.m, %s, %s FROM unnest(%s::int[], %s::int[]) AS t(s, m)''',
      (nguoi_ghi, bay_gio, [b['id'] for b in ghi], [3 + b['id'] % 2 for b in ghi]))
    x('''INSERT INTO session_log_items (session_id, item_id, label, status)
         SELECT cs.id, i.id, i.title,
                CASE WHEN t.lui = 2 AND i.sort_order = (SELECT MAX(sort_order)
                                                          FROM syllabus_items
                                                         WHERE session_id = i.session_id)
                     THEN 'partial' ELSE 'done' END
           FROM unnest(%s::int[], %s::int[]) AS t(s, lui)
           JOIN class_sessions cs ON cs.id = t.s
           JOIN syllabus_items i ON i.session_id = cs.syllabus_session_id''',
      ([b['id'] for b in ghi], [b['lui'] for b in ghi]))
    return vid
