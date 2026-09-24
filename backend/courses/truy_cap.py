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


def quyen_khoa(user):
    """`{course_id: 'hoc' | 'xem'}` — môn KHÔNG có trong dict là môn chưa mở."""
    if la_nhan_su(user):
        return {r['id']: XEM for r in q('SELECT id FROM courses ORDER BY id')}
    khoa = _khoa(user.id)
    ds = cache.get(khoa)
    if ds is None:
        ds = sorted(mon_mo(r['course_id'] for r in q(
            'SELECT DISTINCT c.course_id FROM class_members m JOIN classes c ON c.id = m.class_id '
            'WHERE m.user_id = %s AND ' + LOP_DANG_HOC, (user.id,))))
        cache.set(khoa, ds, TTL)
    return {m: HOC for m in ds}


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


#: Câu từ chối dùng chung — một câu, mọi cửa nói giống nhau.
CHUA_MO = 'Môn này chưa mở cho lớp của em — học vụ xếp em vào lớp có môn này thì bài mở ngay.'
NHAN_SU_CHI_XEM = 'Tài khoản nhân sự chỉ xem bài, không ghi tiến độ.'
