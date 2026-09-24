# Tầng vai (G2, bản dò đầu) — trang × vai × API — sinh tự động, đừng sửa tay

Sinh lại: `node scripts/ban_do.mjs` rồi `python scripts/tang_vai.py docs/BAN_DO_VAI.md <tệp json ra>`. "Lệch" ở mức NÚT (vd học vụ ở Tài khoản: nút chỉ-quản-trị bị ẩn theo `chiHocVien`) thước này chưa thấy.

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
| `/giang-day` | mọi người đăng nhập / công khai | Việc hôm nay: GV TG HV QT | 1 | IsTeachingStaff |
| `/giang-day/bai-tap/[classId]` | mọi người đăng nhập / công khai | Bài tập: GV TG HV QT | 3 | IsTeachingStaff |
| `/giang-day/bai-tap/[classId]/[assignmentId]` | mọi người đăng nhập / công khai | — | 2 | IsTeachingStaff |
| `/giang-day/bao-cao/[classId]` | mọi người đăng nhập / công khai | Báo cáo phụ huynh: GV HV QT | 2 | IsSeniorTeachingStaff |
| `/giang-day/bao-cao/[classId]/[userId]` | mọi người đăng nhập / công khai | — | 4 | IsSeniorTeachingStaff |
| `/giang-day/buoi-hoc/[classId]` | mọi người đăng nhập / công khai | Buổi học: GV TG HV QT | 8 | IsTeachingStaff |
| `/giang-day/cham/[assignmentId]` | mọi người đăng nhập / công khai | — | 1 | IsTeachingStaff |
| `/giang-day/lich` | mọi người đăng nhập / công khai | — | 1 | IsTeachingStaff |
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

## Chỗ lệch: trang cho vai vào nhưng API trang gọi từ chối vai ấy

- `/giang-day` · vai **Biên tập nội dung** · 1 API bị chặn: /api/teach/viec-hom-nay → teaching.ViecHomNayView (IsTeachingStaff)
- `/giang-day` · vai **Học viên** · 1 API bị chặn: /api/teach/viec-hom-nay → teaching.ViecHomNayView (IsTeachingStaff)
- `/giang-day/bai-tap/[classId]` · vai **Biên tập nội dung** · 3 API bị chặn: /api/teach/assignments/* → teaching.AssignmentDetailView (IsTeachingStaff); /api/teach/classes/* → teaching.TeachClassDetailView (IsTeachingStaff); /api/teach/classes/*/assignments → teaching.ClassAssignmentsView (IsTeachingStaff)
- `/giang-day/bai-tap/[classId]` · vai **Học viên** · 3 API bị chặn: /api/teach/assignments/* → teaching.AssignmentDetailView (IsTeachingStaff); /api/teach/classes/* → teaching.TeachClassDetailView (IsTeachingStaff); /api/teach/classes/*/assignments → teaching.ClassAssignmentsView (IsTeachingStaff)
- `/giang-day/bai-tap/[classId]/[assignmentId]` · vai **Biên tập nội dung** · 2 API bị chặn: /api/teach/assignments/*/submissions → teaching.AssignmentGradingView (IsTeachingStaff); /api/teach/assignments/*/submissions/* → teaching.AssignmentSubmissionView (IsTeachingStaff)
- `/giang-day/bai-tap/[classId]/[assignmentId]` · vai **Học viên** · 2 API bị chặn: /api/teach/assignments/*/submissions → teaching.AssignmentGradingView (IsTeachingStaff); /api/teach/assignments/*/submissions/* → teaching.AssignmentSubmissionView (IsTeachingStaff)
- `/giang-day/bao-cao/[classId]` · vai **Biên tập nội dung** · 2 API bị chặn: /api/teach/classes/*/parent-contacts → teaching.ParentContactsImportView (IsSeniorTeachingStaff); /api/teach/classes/*/parent-report/send-all → teaching.ParentReportSendAllView (IsSeniorTeachingStaff)
- `/giang-day/bao-cao/[classId]` · vai **Học viên** · 2 API bị chặn: /api/teach/classes/*/parent-contacts → teaching.ParentContactsImportView (IsSeniorTeachingStaff); /api/teach/classes/*/parent-report/send-all → teaching.ParentReportSendAllView (IsSeniorTeachingStaff)
- `/giang-day/bao-cao/[classId]` · vai **Trợ giảng** · 2 API bị chặn: /api/teach/classes/*/parent-contacts → teaching.ParentContactsImportView (IsSeniorTeachingStaff); /api/teach/classes/*/parent-report/send-all → teaching.ParentReportSendAllView (IsSeniorTeachingStaff)
- `/giang-day/bao-cao/[classId]/[userId]` · vai **Biên tập nội dung** · 4 API bị chặn: /api/teach/classes/*/students/*/parent-report → teaching.ParentReportView (IsSeniorTeachingStaff); /api/teach/classes/*/students/*/parent-report/link → teaching.ParentReportLinkView (IsSeniorTeachingStaff); /api/teach/classes/*/students/*/profile → teaching.MucTieuHocVienView (IsSeniorTeachingStaff); /api/teach/parent-report/links/*/revoke → teaching.ParentReportLinkRevokeView (IsSeniorTeachingStaff)
- `/giang-day/bao-cao/[classId]/[userId]` · vai **Học viên** · 4 API bị chặn: /api/teach/classes/*/students/*/parent-report → teaching.ParentReportView (IsSeniorTeachingStaff); /api/teach/classes/*/students/*/parent-report/link → teaching.ParentReportLinkView (IsSeniorTeachingStaff); /api/teach/classes/*/students/*/profile → teaching.MucTieuHocVienView (IsSeniorTeachingStaff); /api/teach/parent-report/links/*/revoke → teaching.ParentReportLinkRevokeView (IsSeniorTeachingStaff)
- `/giang-day/bao-cao/[classId]/[userId]` · vai **Trợ giảng** · 4 API bị chặn: /api/teach/classes/*/students/*/parent-report → teaching.ParentReportView (IsSeniorTeachingStaff); /api/teach/classes/*/students/*/parent-report/link → teaching.ParentReportLinkView (IsSeniorTeachingStaff); /api/teach/classes/*/students/*/profile → teaching.MucTieuHocVienView (IsSeniorTeachingStaff); /api/teach/parent-report/links/*/revoke → teaching.ParentReportLinkRevokeView (IsSeniorTeachingStaff)
- `/giang-day/buoi-hoc/[classId]` · vai **Biên tập nội dung** · 8 API bị chặn: /api/teach/classes/* → teaching.TeachClassDetailView (IsTeachingStaff); /api/teach/classes/*/export/attendance.csv → teaching.ClassAttendanceCsvView (IsTeachingStaff); /api/teach/classes/*/export/progress.csv → teaching.ClassProgressCsvView (IsTeachingStaff); /api/teach/classes/*/export/report.pdf → teaching.ClassReportPdfView (IsTeachingStaff)
- `/giang-day/buoi-hoc/[classId]` · vai **Học viên** · 8 API bị chặn: /api/teach/classes/* → teaching.TeachClassDetailView (IsTeachingStaff); /api/teach/classes/*/export/attendance.csv → teaching.ClassAttendanceCsvView (IsTeachingStaff); /api/teach/classes/*/export/progress.csv → teaching.ClassProgressCsvView (IsTeachingStaff); /api/teach/classes/*/export/report.pdf → teaching.ClassReportPdfView (IsTeachingStaff)
- `/giang-day/cham/[assignmentId]` · vai **Biên tập nội dung** · 1 API bị chặn: /api/teach/assignments/*/submissions → teaching.AssignmentGradingView (IsTeachingStaff)
- `/giang-day/cham/[assignmentId]` · vai **Học viên** · 1 API bị chặn: /api/teach/assignments/*/submissions → teaching.AssignmentGradingView (IsTeachingStaff)
- `/giang-day/lich` · vai **Biên tập nội dung** · 1 API bị chặn: /api/teach/lich → teaching.LichView (IsTeachingStaff)
- `/giang-day/lich` · vai **Học viên** · 1 API bị chặn: /api/teach/lich → teaching.LichView (IsTeachingStaff)
- `/quan-tri/tai-khoan` · vai **Quản lý học vụ** · 3 API bị chặn: /api/admin/export/users.csv → teaching.AdminUsersCsvView (IsAdminRole); /api/admin/users/*/role → teaching.AdminUserRoleView (IsAdminRole); /api/admin/users/*/status → teaching.AdminUserStatusView (IsAdminRole)