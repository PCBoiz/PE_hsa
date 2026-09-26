"""Cho một người RỜI LỚP — hàm dịch vụ của miền lớp học (`docs/THIET_KE_HE_THONG.md` §4).

Trước 25/09/2026 câu đóng lượt nằm thẳng trong `AdminClassMembersView.delete`. Hộp Yêu cầu
(E3) cần đúng việc ấy khi duyệt bảo lưu / huỷ khoá, và luật S4 cấm miền khác `UPDATE` thẳng
`class_members` — nên tách ra đây, view và `yeu_cau` cùng gọi một hàm.

KHÔNG tự xoá đệm quyền môn: bên gọi làm SAU khi giao dịch chốt (`quen_truy_cap`), để một
lượt đọc chen giữa không đệm lại quyền cũ.
"""
from common import audit
from common.clock import local_now
from common.db import q, q1
from common.permissions import ROLE_ASSISTANT
from teaching.vocab import LEAVE_LABEL, LEAVE_REASONS


def _ten(row, uid):
    if not row:
        return '#%s' % uid
    return row.get('name') or row.get('email') or '#%s' % uid


def roi_lop(request, class_id, uid, ly_do=None, *, luc=None, reserve_until=None, actor=None):
    """Đóng lượt học ĐANG MỞ của `uid` ở lớp `class_id`. Trả id lượt vừa đóng, hoặc None khi
    người ấy không đang học lớp đó. Ghi nhật ký `class.member.remove`.

    `reserve_until` chỉ có nghĩa với `ly_do='reserved'` (bảo lưu tới ngày nào, §65c).
    """
    if ly_do is not None and ly_do not in LEAVE_REASONS:
        raise ValueError('leave_reason lạ: %r' % ly_do)
    # `AND left_at IS NULL` BẮT BUỘC từ §36: một em học lại lớp cũ có nhiều lượt, câu không
    # lọc sẽ dập mốc rời lớp lên cả những lượt đã đóng từ đợt trước.
    rows = q('''UPDATE class_members SET left_at=%s, leave_reason=%s,
                       reserve_until=CASE WHEN %s = 'reserved' THEN %s ELSE reserve_until END
                WHERE class_id=%s AND user_id=%s AND left_at IS NULL
                RETURNING id''',
             (luc or local_now(), ly_do, ly_do, reserve_until, class_id, uid))
    if not rows:
        return None
    klass = q1('SELECT id, name FROM classes WHERE id=%s', (class_id,))
    row = q1('SELECT id, name, email, role FROM users WHERE id=%s', (uid,))
    ten = _ten(row, uid)
    ten_lop = klass['name'] if klass else '#%s' % class_id
    if row and row.get('role') == ROLE_ASSISTANT:
        tom_tat = 'Gỡ trợ giảng "%s" khỏi lớp "%s".' % (ten, ten_lop)
    else:
        tom_tat = ('Cho "%s" rời lớp "%s"%s. Dữ liệu học của em giữ nguyên.'
                   % (ten, ten_lop, ' (%s)' % LEAVE_LABEL[ly_do] if ly_do else ''))
    chi_tiet = {'userId': uid, 'userName': ten, 'classId': class_id, 'leaveReason': ly_do}
    if reserve_until is not None and ly_do == 'reserved':
        chi_tiet['reserveUntil'] = reserve_until.isoformat()
    audit.record(request, audit.CLASS_MEMBER_REMOVE, target_type='class', target_id=class_id,
                 target_label=ten_lop, summary=tom_tat, detail=chi_tiet, actor=actor)
    return rows[0]['id']
