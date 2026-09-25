"""Đột biến E1 (khung chương trình, sổ đầu bài, tiến độ) — 25/09/2026.

Mỗi mục: (tệp, chuỗi cũ, chuỗi mới, luật). Nền phải xanh; mỗi đột biến phải làm bộ
kiểm chuong_trinh + courseadmin/tests_syllabus.py đỏ; thoát 1 nếu còn đột biến sống.
Chạy (cần DATABASE_URL, SECRET_KEY): python scripts/dot_bien_e1.py
"""
import os
import subprocess
import sys

GOC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend') + os.sep
LENH = [sys.executable, '-m', 'pytest', '-x', '-q', '-p', 'no:cacheprovider',
        'chuong_trinh', 'courseadmin/tests_syllabus.py']
M = [
 ('chuong_trinh/tien_do.py', "tre >= NGUONG_TRE_BUOI", "tre > NGUONG_TRE_BUOI", 'chậm: ≥ 2 buổi → >'),
 ('chuong_trinh/tu_vung.py', "NGUONG_TI_LE = Decimal('0.8')", "NGUONG_TI_LE = Decimal('0.7')", 'ngưỡng tỉ lệ 0.8 → 0.7'),
 ('chuong_trinh/tu_vung.py', "MUC_MOT_PHAN: Decimal('0.5')", "MUC_MOT_PHAN: Decimal('1')", 'một phần = 0,5 → 1'),
 ('chuong_trinh/tien_do.py', "a.status IN ('present', 'late')", "a.status IN ('present')", '% em: bỏ muộn'),
 ('chuong_trinh/tien_do.py', "FILTER (WHERE sl.session_id IS NULL) AS chua_ghi", "FILTER (WHERE sl.session_id IS NOT NULL) AS chua_ghi", 'chuaGhiSo đảo'),
 ('chuong_trinh/tien_do.py', "cs.starts_at <= %(nay)s)\n     GROUP BY l.class_id", "TRUE)\n     GROUP BY l.class_id", 'phải xong gồm cả buổi chưa tới'),
 ('chuong_trinh/tien_do.py', "MAX(''' + sql_tin_chi('li.status') + ''') AS tc\n      FROM lop l\n      JOIN class_sessions cs ON cs.class_id = l.class_id\n      JOIN session_log_items", "SUM(''' + sql_tin_chi('li.status') + ''') AS tc\n      FROM lop l\n      JOIN class_sessions cs ON cs.class_id = l.class_id\n      JOIN session_log_items", 'mục ghi hai buổi: MAX → SUM'),
 ('chuong_trinh/tien_do.py', "(VALUES (cs.id), (cs.makeup_for))", "(VALUES (cs.id))", 'buổi bù không tính cho buổi gốc'),
 ('chuong_trinh/dich_vu.py', "and b['status'] != 'cancelled'\n", "\n", 'nhận khung: không bỏ buổi huỷ'),
 ('chuong_trinh/dich_vu.py', "for b, k in cap if b['topic'] is None]", "for b, k in cap]", 'điền tên cả buổi đã có tên'),
 ('chuong_trinh/dich_vu.py', "cho = [b for b in buoi if not b['syllabus_session_id'] and", "cho = [b for b in buoi if True and", 'đè gắn tay'),
 ('chuong_trinh/dich_vu.py', "if ban['status'] != BAN_XUAT_BAN:", "if False:", 'nhận cả bản nháp'),
 ('courseadmin/syllabus.py', "    if trang_thai != 'nhap':", "    if False:", 'sửa được bản đã xuất bản'),
 ('courseadmin/syllabus.py', "(BAN_NGUNG, v['lineage_id'] or v['id'], BAN_XUAT_BAN, version_id)", "(BAN_XUAT_BAN, v['lineage_id'] or v['id'], BAN_NGUNG, version_id)", 'xuất bản không ngừng bản cũ'),
 ('courseadmin/syllabus.py', "if q1('SELECT 1 FROM classes WHERE syllabus_version_id=%s', (version_id,)):", "if False:", 'xoá được bản lớp đang dùng'),
 ('courseadmin/syllabus.py', "SELECT sm.id, i.sort_order, i.kind, i.lesson_id, i.title, i.weight", "SELECT sc.id, i.sort_order, i.kind, i.lesson_id, i.title, i.weight", 'nhân bản: nội dung không sang bản mới'),
 ('courseadmin/syllabus.py', "if not w > 0 or w > 100:", "if w > 100:", 'trọng số ≤ 0 lọt'),
 ('chuong_trinh/so_dau_bai.py', "if not b or not can_see_class(request.user, b['class_id']):\n            return None", "if not b:\n            return None", 'sổ: bỏ can_see_class'),
 ('chuong_trinh/so_dau_bai.py', "if b['starts_at'] > nay:", "if False:", 'ghi sổ buổi chưa diễn ra'),
 ('chuong_trinh/so_dau_bai.py', "if not 1 <= muc_do <= 5:", "if not 0 <= muc_do <= 5:", 'mức tiếp thu 0 lọt'),
 ('chuong_trinh/so_dau_bai.py', "la = sorted(set(ho_tro) - trong_lop)", "la = []", 'hỗ trợ em ngoài lớp'),
 ('chuong_trinh/so_dau_bai.py', "if (body.get('phien_ban') or None) != thay:", "if False:", 'mất chặn ghi đè 409'),
 ('chuong_trinh/so_dau_bai.py', "muc.append((iid, theo_id[iid]['label'], tt, ghi_chu))", "muc.append((iid, m.get('label') or '', tt, ghi_chu))", 'nhãn lấy chữ trình duyệt'),
 ('common/permissions.py', "return is_admin(u) or is_academic(u) or is_editor(u)", "return is_admin(u) or is_editor(u)", 'học vụ mất quyền soạn khung'),
 ('chuong_trinh/lop.py', "if not b or not can_see_class(request.user, b['class_id']):\n            return Response(_KHONG_THAY_BUOI, status=404)\n        co, moi", "if not b:\n            return Response(_KHONG_THAY_BUOI, status=404)\n        co, moi", 'gắn tay: bỏ can_see_class'),
 ('teaching/overview.py', "'lopCham': sum(1 for t in tien_do.values() if t['cham'])", "'lopCham': sum(1 for t in tien_do.values() if not t['cham'])", 'Tổng quan đếm lớp chậm đảo'),
 ('teaching/reports.py', "d['chuongTrinh'] = None if not td else {", "d['chuongTrinhX'] = None if not td else {", 'danh sách lớp mất chip'),
 ('teaching/lop_cua_toi.py', "'chuongTrinh': chuong_trinh.get(cid),", "'chuongTrinh': None,", 'Lớp của tôi mất %'),
 ('teaching/parent_report.py', "'chuongTrinh': tien_do_em(user_id, [class_id]).get(class_id),", "'chuongTrinh': None,", 'tờ phụ huynh mất dòng'),
 ('chuong_trinh/du_lieu_mau.py', "ghi = [b for b in da_day if b['lui'] > 1]", "ghi = da_day", 'dữ liệu mẫu ghi cả buổi gần nhất'),
]
def chay():
    return subprocess.run(LENH, cwd=GOC, capture_output=True, text=True, timeout=900).returncode
if chay() != 0:
    print('NỀN ĐỎ — dừng'); sys.exit(2)
print('nền xanh')
song = []
for tep, cu, moi, luat in M:
    p = GOC + tep
    goc = open(p, encoding='utf-8').read()
    n = goc.count(cu)
    if n != 1:
        print('  ?? %s: chuỗi xuất hiện %d lần — %s' % (tep, n, luat)); song.append(luat); continue
    open(p, 'w', encoding='utf-8').write(goc.replace(cu, moi))
    try:
        rc = chay()
    finally:
        open(p, 'w', encoding='utf-8').write(goc)
    print('  %s %s' % ('ĐỎ ✓' if rc != 0 else 'SỐNG ✗', luat))
    if rc == 0: song.append(luat)
print('%d đột biến, %d bị giết, %d sống' % (len(M), len(M) - len(song), len(song)))
sys.exit(1 if song else 0)
