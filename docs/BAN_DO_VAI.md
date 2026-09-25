# Tầng vai (G2, bản dò đầu) — trang × vai × API — sinh tự động, đừng sửa tay

Sinh lại: `node scripts/ban_do.mjs` rồi `python scripts/tang_vai.py docs/BAN_DO_VAI.md <tệp json ra>`. Cổng pre-push: `python scripts/tang_vai.py --kiem`. Lệch ở mức NÚT phải ghi vào `DA_GIAI_THICH` kèm lý do.

QT quản trị viên · HV học vụ · GV giảng viên · TG trợ giảng · BT biên tập · HS học viên.

| Trang | Cổng trang (vai vào được) | Menu hiện cho | Số API | Lớp quyền API cần |
|---|---|---|---|---|
| `/` | mọi người đăng nhập / công khai | — | 0 | — |
| `/auth/callback` | mọi người đăng nhập / công khai | — | 0 | — |
| `/bai-tap` | mọi người đăng nhập / công khai | — | 1 | (mặc định: IsAuthenticated) |
| `/bc/[token]` | mọi người đăng nhập / công khai | — | 1 | AllowAny |
| `/courses/[courseId]` | mọi người đăng nhập / công khai | — | 4 | (mặc định: IsAuthenticated) |
| `/dashboard` | mọi người đăng nhập / công khai | — | 0 | — |
| `/dat-lai-mat-khau` | mọi người đăng nhập / công khai | — | 2 | AllowAny |
| `/doi-mat-khau` | mọi người đăng nhập / công khai | — | 3 | (mặc định: IsAuthenticated), AllowAny |
| `/giang-day` | theo mã API (chanTu) | Việc hôm nay: GV TG HV QT | 1 | IsTeachingStaff |
| `/giang-day/bai-tap/[classId]` | theo mã API (chanTu) | Bài tập: GV TG HV QT | 3 | IsTeachingStaff |
| `/giang-day/bai-tap/[classId]/[assignmentId]` | theo mã API (chanTu) | — | 2 | IsTeachingStaff |
| `/giang-day/bao-cao/[classId]` | theo mã API (chanTu) | Báo cáo phụ huynh: GV HV QT | 2 | IsSeniorTeachingStaff |
| `/giang-day/bao-cao/[classId]/[userId]` | theo mã API (chanTu) | — | 4 | IsSeniorTeachingStaff |
| `/giang-day/buoi-hoc/[classId]` | theo mã API (chanTu) | Buổi học: GV TG HV QT | 8 | IsTeachingStaff |
| `/giang-day/cham/[assignmentId]` | theo mã API (chanTu) | — | 1 | IsTeachingStaff |
| `/giang-day/lich` | theo mã API (chanTu) | — | 1 | IsTeachingStaff |
| `/giao-trinh` | QT BT | Giáo trình: BT QT | 8 | (mặc định: IsAuthenticated) |
| `/huong-dan` | mọi người đăng nhập / công khai | — | 0 | — |
| `/lesson/[courseId]` | mọi người đăng nhập / công khai | — | 0 | — |
| `/login` | mọi người đăng nhập / công khai | — | 2 | (mặc định: IsAuthenticated), AllowAny |
| `/quan-tri/co-so-hoc-phi` | QT | Cơ sở học phí: QT | 1 | IsAdminRole |
| `/quan-tri/dot-hoc` | QT HV | Đợt học: QT HV | 4 | IsAdminOrAcademic |
| `/quan-tri/huong-dan` | QT HV | Hướng dẫn: QT HV; Hướng dẫn từng bước: HV QT | 0 | — |
| `/quan-tri/lop-hoc` | QT HV | Lớp học: QT HV | 11 | AllowAny, IsAdminOrAcademic, IsTeachingStaff |
| `/quan-tri/nhat-ky` | QT | Nhật ký: QT | 1 | IsAdminRole |
| `/quan-tri/tai-khoan` | QT HV | Tài khoản: QT HV | 8 | IsAdminOrAcademic, IsAdminRole |
| `/quan-tri/tai-khoan/[id]` | QT HV | — | 2 | IsAdminOrAcademic |
| `/quan-tri/tong-quan` | QT HV | Toàn trung tâm: QT HV; Vận hành trung tâm: HV QT | 1 | IsAdminOrAcademic |
| `/quan-tri/vai-tro` | QT HV | Ai làm được gì: QT HV | 0 | — |
| `/quen-mat-khau` | mọi người đăng nhập / công khai | — | 1 | AllowAny |
| `/questionaire` | mọi người đăng nhập / công khai | — | 0 | — |
| `/thiet-ke` | mọi người đăng nhập / công khai | — | 0 | — |

## Đã giải thích (lệch ở mức nút, đã soi mã)

- `/quan-tri/tai-khoan` · Quản lý học vụ — nút xuất CSV / đổi vai / khoá chỉ vẽ khi máy chủ KHÔNG trả `chiHocVien` (AccountsClient.tsx `!chiHocVien`)

## Chỗ lệch: trang cho vai vào nhưng API trang gọi từ chối vai ấy

Không có.