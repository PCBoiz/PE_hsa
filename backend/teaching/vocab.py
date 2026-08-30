"""Từ vựng chung của khu Giảng dạy — nơi DUY NHẤT đặt tên cho các trạng thái.

Sinh ra ngày 31/08/2026 cùng `class_members.leave_reason` (§36). Lý do có một
mô-đun riêng thay vì để hằng số nằm trong `views.py`: ba nơi cùng cần đọc bộ từ
vựng này — màn hình quản lý lớp, báo cáo lớp (`reports.py`) và file CSV mang đi
họp (`exports.py`) — mà `views.py` đã import `reports`, nên đặt ở đó là tạo vòng
import.

Quan trọng hơn: nhãn tiếng Việt phải khớp với danh sách giá trị mà `CHECK` của
CSDL cho phép. Để hai thứ ở hai tệp khác nhau thì thêm một lý do rời lớp mới sẽ
qua được CSDL nhưng hiện ra màn hình dưới dạng chuỗi trần — đúng lớp lỗi mà T49
đã gặp với `attendance.mark` và vai trò `admin`.
"""

#: Lý do rời lớp. NULL nghĩa là đang học; xem `sql/legacy_schema.sql` §36 —
#: `class_members_leave_reason_check` phải liệt kê đúng ba giá trị này.
LEAVE_REASONS = ('completed', 'dropped', 'transferred')

#: Nhãn hiển thị. Tách "học xong" khỏi "bỏ giữa chừng" là toàn bộ lý do cột
#: `leave_reason` tồn tại: gộp lại thì mọi lớp kết thúc đều trông như bỏ học
#: 100% trong báo cáo tỉ lệ bỏ học của một đợt.
LEAVE_LABEL = {
    'completed': 'học xong',
    'dropped': 'bỏ giữa chừng',
    'transferred': 'chuyển lớp',
}

#: Dùng cho cột trạng thái trong báo cáo và CSV. Đã rời lớp mà KHÔNG ghi lý do
#: thì nói thẳng là chưa ghi, đừng đoán thành 'bỏ giữa chừng' — con số bỏ học
#: là thứ trung tâm mang đi báo cáo, đoán sai một dòng là sai cả tỉ lệ.
def trang_thai(left_at, leave_reason=None):
    """Câu mô tả trạng thái một dòng ``class_members``."""
    if not left_at:
        return 'Đang học'
    if leave_reason in LEAVE_LABEL:
        return 'Đã rời lớp — %s' % LEAVE_LABEL[leave_reason]
    return 'Đã rời lớp — chưa ghi lý do'
