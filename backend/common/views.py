"""Lớp cha cho view của NGƯỜI DÙNG ĐÃ ĐĂNG NHẬP — nói rõ điều trước đây để ngầm.

── VÌ SAO CÓ (13/09/2026) ──────────────────────────────────────────────────

Đo được 60/107 view `api/` không khai `permission_classes`, chỉ dựa vào
`DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` trong settings. Mặc định ấy
đúng, nhưng:

  · một view mới quên khai sẽ mở cho mọi người đã đăng nhập, IM LẶNG;
  · ai "dọn" settings rồi bỏ dòng mặc định là 60 view cùng lúc thành công khai.

`common/tests_khai_cong.py` nay bắt mọi view phải KHAI. Lớp này là cách khai
gọn nhất cho nhóm đông nhất: "phải đăng nhập, và view tự lọc theo người gọi".

── ĐIỀU LỚP NÀY *KHÔNG* HỨA ────────────────────────────────────────────────

Nó chỉ chặn người CHƯA đăng nhập. Nó KHÔNG chặn học viên A đọc dữ liệu của
học viên B — việc đó là của từng view (lọc theo `request.user`), và được canh
bởi `common/tests_do_cua_nguoi_khac.py`. Kế thừa lớp này là một LỜI KHAI:
"view này thuộc về chính người gọi", chứ không phải một lớp bảo vệ thêm.

View cần vai trò (giảng viên, quản trị, biên tập) thì KHÔNG dùng lớp này —
dùng `permission_classes = [IsTeachingStaff]` v.v. như đang làm.
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView


class NguoiDungView(APIView):
    """Phải đăng nhập; dữ liệu của chính người gọi — view tự lọc theo `request.user`."""
    permission_classes = [IsAuthenticated]


def da_khai_cong(cls) -> bool:
    """View `cls` có TỰ KHAI `permission_classes` không — ở chính nó hoặc ở một
    lớp cha do dự án viết. Kế thừa `APIView` rồi thôi thì KHÔNG tính.

    Đặt ở đây (không phải trong tệp test) vì HAI nơi cần cùng một câu trả lời:
    `common/tests_khai_cong.py` (cổng CI) và `scripts/kiem_ke_san_pham.py` (hồ
    sơ gửi TopHSA). Bản đầu của bộ kiểm kê tự đếm bằng `vars(cls)` và báo 71
    thay vì 60 — nó đếm cả 11 view khai qua `AdminBase`. Hai bộ đếm cùng một
    thứ mà ra hai số là đúng loại lỗi làm mất tin vào cả hồ sơ.

    Phải DỪNG ở `APIView`: chính nó cũng có `permission_classes` trong
    `__dict__` (dòng đọc từ settings), đi tiếp là mọi view đều "đã khai".
    """
    for lop in cls.__mro__:
        if lop is APIView:
            return False
        if 'permission_classes' in vars(lop):
            return True
    return False
