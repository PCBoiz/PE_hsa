"""CỔNG MỞ MÔN — môn học mở QUA LỚP (mục 1.3 kế hoạch thử nghiệm, 24/09/2026).

Góp ý TopHSA số 3: "mục Học không rõ để đăng ký hay để quản lý; giáo viên, trợ giảng
cũng thấy nút Đăng ký". Chủ sản phẩm chốt: học viên KHÔNG tự đăng ký — học vụ xếp em
vào lớp thì môn của lớp mở; nhân sự xem bài ở chế độ chỉ-đọc.

Đây là cổng DUY NHẤT trả lời "người này mở được môn nào, ở chế độ nào":

  · nhân sự (mọi vai không phải Học viên) → mọi môn, chế độ `'xem'`: đọc bài, chấm thử
    được, KHÔNG ghi tiến độ, không ghi bài làm;
  · học viên → `'hoc'` cho môn của mọi lớp em ĐANG học (`left_at IS NULL`) mà lớp chưa
    huỷ. Lớp `course_id IS NULL` = lớp học cả ba môn. Lớp đã kết thúc mà em chưa bị cho
    rời thì VẪN mở (em ôn lại được) — mặc định đã báo anh Sơn.

Bảng `enrollments` KHÔNG còn là cổng: nó giữ vai bộ nhớ tiến độ (phần trăm, bài kế
tiếp) mà `CompleteLessonView` vẫn ghi.

ĐỆM 60 GIÂY theo người dùng — phòng luyện hỏi cổng này MỖI CÂU (cùng lý lẽ với đệm ghi
danh cũ ở `lessons/views.py`). Mọi chỗ đổi lớp của một em gọi `quen_truy_cap(uid)`;
đổi môn / trạng thái của CẢ lớp gọi `quen_truy_cap_lop(class_id)`. Giới hạn đã biết:
không có Redis thì đệm nằm trong TỪNG tiến trình — tiến trình kia trễ tối đa 60 giây.
"""
from django.core.cache import cache

from common.db import q
from common.permissions import ROLE_STUDENT

HOC = 'hoc'
XEM = 'xem'
TTL = 60

#: Ba môn HSA — lớp để trống môn là lớp học cả ba. Cùng thứ tự với
#: `stats.competency.COURSE_ORDER` (không nhập chéo: `stats` nhập `courses`).
BA_MON = ('hsa_quantitative', 'hsa_verbal', 'hsa_science')

#: Mệnh đề SQL "lượt học ĐANG MỞ MÔN": em chưa rời lớp, lớp chưa huỷ (lớp đã kết thúc
#: vẫn mở — xem đầu tệp). Bí danh bắt buộc: ``m`` = class_members, ``c`` = classes.
#: Màn Tài khoản (1.4b) đọc CÙNG mệnh đề cho cột "Lớp" và ô lọc "chưa xếp lớp" — em hiện
#: "chưa xếp lớp" ở đó đúng là em không mở được môn nào ở đây.
LOP_DANG_HOC = "m.left_at IS NULL AND c.status <> 'cancelled'"


def mon_mo(course_ids):
    """Tập môn mở từ các ``classes.course_id`` của lớp em đang học — NULL = cả ba môn."""
    mon = set()
    for course_id in course_ids:
        if course_id is None:
            mon.update(BA_MON)
        else:
            mon.add(course_id)
    return mon


def _khoa(uid):
    return 'truycap:%s' % uid


def la_nhan_su(user):
    return (getattr(user, 'role', None) or ROLE_STUDENT) != ROLE_STUDENT


def _mon_hoc_vien(user_id):
    """Môn đang mở cho MỘT học viên qua lớp, TRỪ khoá nháp — MỘT câu (danh sách khoá nháp
    đi chung câu, câu con không tương quan nên Postgres tính một lần). Lõi của cổng
    (`quyen_khoa`, có đệm) và của màn hiển thị (`cac_mon_da_mo`, không đệm)."""
    rows = q('SELECT DISTINCT c.course_id, '
             'ARRAY(SELECT id FROM courses WHERE is_published IS FALSE) AS nhap '
             'FROM class_members m JOIN classes c ON c.id = m.class_id '
             'WHERE m.user_id = %s AND ' + LOP_DANG_HOC, (user_id,))
    nhap = set(rows[0]['nhap'] or ()) if rows else set()
    return sorted(mon_mo(r['course_id'] for r in rows) - nhap)


def quyen_khoa(user):
    """`{course_id: 'hoc' | 'xem'}` — môn KHÔNG có trong dict là môn chưa mở.

    Khoá NHÁP (`courses.is_published = FALSE`, V-i 25/09/2026) không mở cho học viên,
    kể cả khi lớp em đang học mang khoá ấy; nhân sự vẫn xem được. Danh sách khoá nháp
    đi CHUNG câu với lớp của em (câu con không tương quan — Postgres tính một lần), nên
    lượt hỏi khi đệm nguội vẫn là một câu. `NULL` = đang mở (dữ liệu trước cột này)."""
    if la_nhan_su(user):
        return {r['id']: XEM for r in q('SELECT id FROM courses ORDER BY id')}
    khoa = _khoa(user.id)
    ds = cache.get(khoa)
    if ds is None:
        ds = _mon_hoc_vien(user.id)
        cache.set(khoa, ds, TTL)
    return {m: HOC for m in ds}


def an_voi(user, course_row):
    """Khoá này có phải GIẤU khỏi `user` không — khoá nháp, người xem là học viên.

    Dùng ở các danh sách khoá (`courses/views.py`): học viên không thấy khoá nháp
    trong danh sách, nhân sự vẫn thấy (chế độ chỉ-xem)."""
    return course_row.get('is_published') is False and not la_nhan_su(user)


def cac_mon_da_mo(user_id):
    """Course id đã mở cho MỘT học viên qua lớp — cho màn HIỂN THỊ (hồ sơ học viên, yêu
    cầu TopHSA 3.2 "khóa học đã đăng ký"), không phải cổng chặn nên KHÔNG đệm, KHÔNG rẽ
    nhánh nhân sự. CÙNG hàm lõi với nhánh học viên của `quyen_khoa()` (kể cả trừ khoá
    nháp) — hồ sơ nói "em học được môn X" đúng khi và chỉ khi cổng mở môn X cho em."""
    return _mon_hoc_vien(user_id)


def che_do(user, course_id):
    """`'hoc'`, `'xem'` hoặc `None` (chưa mở) cho MỘT môn."""
    return quyen_khoa(user).get(course_id)


def quen_truy_cap(uid):
    """Xoá đệm quyền của một người — gọi ngay sau khi em vào / rời / chuyển lớp."""
    cache.delete(_khoa(uid))


def quen_truy_cap_lop(class_id):
    """Xoá đệm quyền của mọi thành viên một lớp — đổi môn, trạng thái, hay xoá lớp."""
    for r in q('SELECT DISTINCT user_id FROM class_members WHERE class_id = %s', (class_id,)):
        quen_truy_cap(r['user_id'])


def quen_truy_cap_khoa(course_id):
    """Xoá đệm quyền của mọi em đang học một lớp MANG khoá này — đổi "Đang mở / Nháp".

    Lớp để trống môn học cả ba môn HSA (`mon_mo`), nên khoá thuộc `BA_MON` kéo theo cả
    các lớp ấy. MỘT câu + MỘT lệnh xoá nhiều khoá đệm (`delete_many`): khoá phổ biến là
    hàng trăm em, xoá từng khoá một là hàng trăm lượt gọi Redis."""
    rows = q('SELECT DISTINCT m.user_id FROM class_members m JOIN classes c ON c.id = m.class_id '
             'WHERE ' + LOP_DANG_HOC + ' AND (c.course_id = %s OR (c.course_id IS NULL AND %s))',
             (course_id, course_id in BA_MON))
    if rows:
        cache.delete_many([_khoa(r['user_id']) for r in rows])


#: Câu từ chối dùng chung — một câu, mọi cửa nói giống nhau.
CHUA_MO = 'Môn này chưa mở cho lớp của em — học vụ xếp em vào lớp có môn này thì bài mở ngay.'
NHAN_SU_CHI_XEM = 'Tài khoản nhân sự chỉ xem bài, không ghi tiến độ.'
