"""Tính lại bộ đệm tiến độ trong ``enrollments`` từ nguồn thật.

NGUỒN THẬT LÀ ``lesson_progress``. Bảng ``enrollments`` chỉ giữ một bản sao đã
tính sẵn (``completed_lessons``, ``progress``, ``time_spent``, ``completed_at``)
để dashboard không phải đếm lại mỗi lần mở. Bản sao thì phải có đúng MỘT chỗ
dựng lại nó.

VÌ SAO GOM (đo 01/09/2026). Trước đó có hai bản:

  · ``lessons/views.py`` — chạy khi học xong một bài. Đặt cả bốn cột.
  · ``courses/views.py`` — chạy khi ghi danh lại sau khi đã huỷ. Đặt BA cột,
    quên ``completed_at``.

Câu ``SELECT`` đếm bài của hai bản giống nhau đến từng ký tự; chỉ câu ``UPDATE``
lệch một cột. Hậu quả: em học hết khoá (progress 100, ``completed_at`` có giá
trị) → huỷ ghi danh (``DELETE`` xoá cả dòng) → ghi danh lại → tiến độ về đúng
100% nhưng ``completed_at`` là ``NULL``. Bản ghi nói "đã xong" mà không có ngày
xong.

Chưa ai thấy vì tới 01/09/2026 KHÔNG mã nào đọc ``enrollments.completed_at``
(đã grep cả repo — chỗ duy nhất tên giống là ``lesson_progress.completed_at``
bên ``stats/views.py``). Nhưng cột ấy tồn tại để có ngày cấp chứng nhận, và
ngày đầu tiên có người đọc nó thì em ghi danh lại sẽ vô hình.

Bản gộp này đặt ``completed_at`` ở CẢ HAI đường — tức đường ghi danh lại được
sửa, chứ không phải đường kia bị hạ xuống cho khớp.
"""
from common.clock import local_now
from common.db import q1, x


def tinh_lai(uid, course_id, tong_bai=None):
    """Dựng lại bộ đệm tiến độ của một (học viên, khoá). Trả dict đã ghi.

    ``tong_bai`` truyền vào khi người gọi đã cầm sẵn số bài của khoá, để khỏi
    thêm một vòng gọi Neon (``common/db.py`` — số câu truy vấn là thứ phải đếm).
    Bỏ trống thì tự hỏi.

    KHÔNG tự mở transaction: cả hai người gọi đều đã nằm trong một
    ``transaction.atomic()`` bao ngoài, và mở lồng thêm ở đây sẽ giấu mất việc
    phần ghi này phải nguyên tử CÙNG với phần gọi nó.
    """
    row = q1('''SELECT COUNT(*) AS n,
                       COALESCE(SUM(COALESCE(l.estimated_minutes, 15)), 0) AS minutes
                FROM lesson_progress lp
                JOIN lessons l ON l.id = lp.lesson_id
                WHERE lp.user_id=%s AND lp.course_id=%s AND lp.status='completed' ''',
             (uid, course_id))
    xong = row['n']
    phut = row['minutes']

    if tong_bai is None:
        tong_bai = (q1('SELECT lessons FROM courses WHERE id=%s', (course_id,)) or {}).get('lessons')
    tong_bai = tong_bai or 0

    # `min(100, ...)`: `courses.lessons` là một con số ghi tay, và nếu nó nhỏ hơn
    # số bài có thật thì tiến độ vọt quá 100 — thanh tiến độ tràn ra ngoài khung.
    tien_do = min(100, round(xong * 100 / tong_bai)) if tong_bai else 0
    gio = str(round(phut / 60, 1)) + 'h'

    # `completed_at` CHỈ ĐI MỘT CHIỀU: `COALESCE` giữ nguyên mốc cũ, và nhánh
    # `ELSE` không xoá. Học xong rồi mà giáo trình thêm bài mới (tiến độ tụt
    # xuống dưới 100) thì em vẫn đã học xong vào ngày ấy — sửa lại lịch sử vì
    # một thay đổi của người lớn là chuyện khác hẳn.
    x('''UPDATE enrollments
         SET completed_lessons = %s,
             progress          = %s,
             time_spent        = %s,
             completed_at      = CASE WHEN %s >= 100 THEN COALESCE(completed_at, %s)
                                      ELSE completed_at END
         WHERE user_id=%s AND course_id=%s''',
      (xong, tien_do, gio, tien_do, local_now(), uid, course_id))

    return {'completed_lessons': xong, 'progress': tien_do, 'time_spent': gio}
