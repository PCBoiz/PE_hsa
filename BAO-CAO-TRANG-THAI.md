# Báo cáo trạng thái — số đo thật

*Sinh tự động ngày 13/09/2026 bằng `python scripts/kiem_ke_san_pham.py --md`. Mọi con số dưới đây được đếm lại từ mã
nguồn hoặc đo trực tiếp trên CSDL tại thời điểm chạy lệnh.*

*Bản này CHỈ ĐO, không nhận định. Muốn biết vì sao một con số ra như vậy thì đọc
`PROGRESS.md`. Đừng chép số từ đây sang tài liệu khác — chép ra là bắt đầu cũ đi.*

---

## Mã nguồn

| Hạng mục | Số đo | Nguồn |
|---|---|---|
| Vai trò người dùng | 6 | `permissions.py` → `ASSIGNABLE_ROLES` |
| Lớp cổng phân quyền | 6 | `permissions.py` → `Is*` |
| Đường API | 108 | `get_resolver()` — đường bắt đầu bằng `api/` |
| · không cần đăng nhập | 2 | AllowAny hoặc `authentication_classes = []` |
| · chỉ cần đăng nhập | 60 | `permission_classes == [IsAuthenticated]` |
| · · trong đó KHÔNG tự khai cổng | 0 | dựa vào mặc định của khung |
| · có cổng vai trò | 46 | lớp `Is*` khác |
| Trang giao diện | 26 | `frontend/src/app/**/page.tsx` |
| Bảng CSDL | 55 | `information_schema.tables` |
| · có dữ liệu | 36 | count(*) > 0 |
| Tệp kiểm thử backend | 35 | `backend/**/tests*.py` |
| Tệp kiểm thử frontend | 33 | `frontend/e2e/**` |

## Dữ liệu nghiệp vụ trên CSDL

| Hạng mục | Số đo |
|---|---|
| Hợp phần (khoá học) | 3 |
| Bài học | 76 |
| Tài khoản | 5 |
| · học viên | 3 |
| Lớp | 1 |
| Đợt học | 1 |
| Buổi học | 4 |
| Lượt điểm danh | 6 |
| Đề thi thử | 1 |
| Học viên có email phụ huynh | 0 |
| Học viên có số phụ huynh | 0 |

## Đường API chỉ cần đăng nhập mà KHÔNG tự khai cổng

*Mặc định của khung là "phải đăng nhập" — đúng, nhưng một đường mới quên khai sẽ
mở cho mọi người đã đăng nhập, im lặng. Liệt kê để đối chiếu từng dòng.*

(không có)

---

*Sinh bởi `scripts/kiem_ke_san_pham.py --md`. Chạy lại bất cứ lúc nào để có số mới.*
