"""AI ĐỨNG LỚP NÀY — một câu trả lời cho mọi chỗ cần báo tin về một lớp.

Miền khác (hộp Yêu cầu, thông báo) gọi hàm này thay vì tự đọc `classes` + `class_members`:
luật S4 nói mã của miền này không đi ghi bảng miền khác, và cùng lý do ấy, một câu hỏi về
lớp nên có ĐÚNG MỘT câu trả lời — không phải một bản sao trong mỗi miền, rồi hai bản trôi
khỏi nhau (RULES §7).

── VÌ SAO KHÔNG GỘP NGƯỜI NHÌN THẤY MỌI LỚP ────────────────────────────────

`can_see_class` trả True cho quản trị viên và cho MỌI học vụ, kể cả người chưa được gán vào
lớp nào — đó là quyền XEM, đúng cho việc xem. Nhưng "ai cần biết chuyện của lớp này" thì
khác: báo cho mọi học vụ nghĩa là mỗi đơn xin nghỉ của cả trung tâm rơi vào chuông của họ,
và sau tuần đầu không ai đọc chuông nữa. Nên hàm này chỉ trả người ĐƯỢC GÁN:

  · giảng viên phụ trách (`classes.teacher_id`),
  · trợ giảng và học vụ phụ trách (`class_members`, chưa rời lớp).

`left_at IS NULL` không phải chi tiết vặt — gỡ một người khỏi lớp là ghi `left_at`, và thiếu
vế ấy thì người đã rời vẫn nhận tin của lớp cũ mãi mãi (cùng lỗi mà `_la_tro_giang_cua_lop`
đã chừa lại chú thích).
"""
from common.db import q, q1
from common.permissions import ROLE_STUDENT


def nhan_su_cua_lop(class_id, tru=None):
    """``set`` id của người ĐƯỢC GÁN đứng lớp ``class_id``, trừ các id trong ``tru``.

    ``tru`` nhận một id hoặc một tập id — thường là người vừa bấm nút, vì không ai cần
    chuông báo lại việc chính mình vừa làm.
    """
    ids = set()
    lop = q1('SELECT teacher_id FROM classes WHERE id = %s', (class_id,))
    if lop and lop['teacher_id']:
        ids.add(lop['teacher_id'])
    # Không phải học viên = trợ giảng hoặc học vụ phụ trách. Viết theo chiều PHỦ ĐỊNH của
    # `chi_hoc_vien` để một vai mới thêm sau này (ví dụ "cố vấn học tập") tự vào danh sách
    # người đứng lớp, thay vì lặng lẽ bị bỏ sót cho tới khi ai đó phát hiện.
    for r in q("""SELECT m.user_id FROM class_members m
                    JOIN users u ON u.id = m.user_id
                   WHERE m.class_id = %s AND m.left_at IS NULL AND u.role <> %s""",
               (class_id, ROLE_STUDENT)):
        ids.add(r['user_id'])
    if tru is None:
        return ids
    return ids - ({tru} if isinstance(tru, int) else set(tru))
