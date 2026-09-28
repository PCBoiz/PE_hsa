# Cải tiến DB — rà nhánh Neon `dev`, áp lên `dev test`

**Phạm vi & cách đo:** đọc trực tiếp `information_schema` + `pg_catalog` trên nhánh Neon
**`dev`** (biến `DATABASE_URL_DEV` trong `backend/.env`, CHỈ ĐỌC — không có câu ghi nào chạy
lên nhánh này). Mọi con số dưới đây là số đo thật ngày 28/09/2026, không phải suy đoán từ mã
nguồn. Việc sửa/thêm (nếu có) chỉ áp vào nhánh **`dev test`** (biến `DATABASE_URL`, nhánh
Django đang chạy) — nhánh `dev` giữ nguyên làm mốc so sánh.

`dev` hiện có 77 bảng, khớp cấu trúc mới nhất của `erp` (đã có `chuong_trinh`, `yeu_cau`,
`outbox`, `hoc_lieu`...) — tức đây không phải một nhánh cũ bỏ quên, mà đang được giữ khá mới.

---

## 1 · Đã ổn, không cần sửa

- **Mọi bảng đều có khoá chính.** Rà toàn bộ 77 bảng, không bảng nào thiếu PK.
- **Không có cột `*_id` "mồ côi".** Mọi cột tên dạng `*_id` (trừ các bảng Django/allauth) đều
  có khoá ngoại thật đứng sau — không có kiểu tham chiếu ngầm bằng quy ước tên cột mà thiếu
  ràng buộc.
- **41 CHECK constraint** đã phủ hầu hết các cột "luật/quyền/trạng thái" quan trọng: vai trò
  và trạng thái tài khoản, trạng thái lớp/hình thức/loại lớp, loại và trạng thái bài tập,
  khung chương trình, hộp Yêu cầu, hộp thư đi, thông báo trung tâm. Đây là kết quả của đợt
  audit T42 (31/08) và các đợt bồi thêm sau đó — không phải việc cần làm lại.
- **FK từ `users(id)`** (56 khoá, đã rà kỹ trong §76 tuần này): CASCADE cho dữ liệu của chính
  người dùng, SET NULL cho "ai đã tạo/duyệt" trên dữ liệu chung — đúng nguyên tắc, không lẫn
  lộn.

## 2 · Cần cải tiến — an toàn, nên làm luôn

### 2.1 · Sáu cột khoá ngoại chưa có chỉ mục

Postgres **không tự tạo chỉ mục cho cột khoá ngoại** — thiếu thì mọi câu JOIN hay
`ON DELETE`/`ON DELETE SET NULL` phải quét toàn bảng cha khi tìm dòng con. Sáu cột sau có FK
nhưng chưa có chỉ mục nào đứng đầu bằng đúng cột đó:

| Bảng | Cột |
|---|---|
| `class_members` | `can_ho_tro_by` |
| `class_members` | `de_xuat_huong_hoc_by` |
| `class_members` | `teacher_comment_by` |
| `recording_views` | `user_id` |
| `syllabus_materials` | `uploaded_by` |
| `syllabus_versions` | `created_by` |

Bàn giao rẻ (mỗi bảng vài chục đến vài trăm dòng lúc này) nhưng để lâu thành nợ — thêm chỉ mục
ngay khi bảng còn nhỏ không tốn gì, để tới lúc bảng lớn mới thêm thì phải `CREATE INDEX
CONCURRENTLY` cẩn thận hơn nhiều.

### 2.2 · Năm cột TEXT nên khoá bằng CHECK — đã đo giá trị thật, an toàn để khoá

| Bảng.Cột | Giá trị thật đang có | Đề xuất |
|---|---|---|
| `lesson_progress.status` | `'completed'` (1129), `'in_progress'` (26) | CHECK `IN ('not_started','in_progress','completed')` |
| `syllabus_materials.file_type` | `'link'` (3), `'pdf'` (3) | CHECK `IN ('link','pdf')` |
| `missions.condition_type` | `'mocks_today'`, `'xp_today'`, `'lessons_today'` (mỗi loại 1 dòng) | CHECK khoá đúng 3 giá trị này |

Đây đúng loại lỗ hổng mà audit T42 đã vá cho `users.role`/`status`/`classes.status` — cột
quyết định luồng nghiệp vụ mà không có gì chặn ở tầng CSDL, sai một dấu ở tầng ứng dụng là
lọt thẳng xuống, không ai biết.

**Không đề xuất khoá** hai cột có cùng dấu hiệu "tên như enum" vì thực ra không phải:
- `admin_audit.actor_role` / `admin_audit.target_type`, `learning_events.ref_type`,
  `notifications.ref_type`/`type`, `outbox.source_type` — đây là cột GHI LẠI LỊCH SỬ hoặc cột
  phân loại polymorphic mà tập giá trị **mở rộng theo tính năng mới** (thêm một loại thông
  báo là thêm một giá trị `type`). Khoá CHECK ở đây là tự trói: mỗi tính năng mới lại phải sửa
  CSDL trước, đúng kiểu cứng nhắc mà các bảng này cố ý tránh.
- `users.status_note` — đây là Ô GHI CHÚ TỰ DO ("lý do khoá"), không phải enum, dù tên có
  chữ "status".

## 3 · Cần quyết định — không tự làm, hỏi trước

### 3.1 · Bảng/tính năng gần như chưa có dữ liệu thật

| Bảng | Số dòng | Ghi chú |
|---|---|---|
| `comments`, `post_likes`, `comment_likes`, `course_ratings`, `user_follows` | 0 | Tính năng cộng đồng/diễn đàn kiểu cũ — không thấy dữ liệu |
| `roadmap_progress`, `term_holidays`, `parent_report_sends`, `account_emailconfirmation` | 0 | |
| `assignment_targets` | 0 | Đã kiểm: mọi `assignments` hiện có đều `target_mode='lop'` (giao cả lớp) — bảng này phục vụ `target_mode='nhom'` (V-e), tính năng đã xây nhưng CHƯA có lượt dùng thật nào, không phải bảng chết |
| `quizzes` | 1 dòng | `mock_exams` cũng chỉ 1 dòng — khớp quyết định "bỏ thi thử online" trong kế hoạch v2 (25/09), có thể coi là tính năng đang đóng băng |

Không đề xuất xoá bảng nào — 0 dòng có thể là "tính năng chưa ai dùng" (`assignment_targets`)
hoặc "tính năng đã chốt bỏ nhưng chưa dọn bảng" (`quizzes`/`mock_exams`). Cần anh Sơn/TopHSA
xác nhận cái nào thật sự không dùng nữa mới nên dọn — dọn nhầm là mất khả năng bật lại.

### 3.2 · Một chỉ mục có thể thừa (không khẩn)

`study_logs` có `idx_study_logs_user (user_id, log_date DESC)` cạnh
`study_logs_user_id_log_date_key (user_id, log_date)` (ràng buộc duy nhất, có sẵn). Hai chỉ
mục phủ gần hết cùng một việc — chỉ khác thứ tự `DESC`. Giữ lại nếu có màn hình thật sự cần
"log gần nhất trước" mà không muốn Postgres tự đảo chiều quét; bỏ nếu không.

### 3.3 · `users` không có cột `updated_at` chung

Có `created_at` nhưng không có một cột "sửa lần cuối lúc nào" áp dụng cho MỌI thay đổi — chỉ
có vài cột theo dõi riêng lẻ (`status_changed_at`, `password_changed_at`,
`parent_contact_locked_at`...). Không cấp bách vì mỗi thay đổi quan trọng đã có audit log
riêng (`admin_audit`) và cột thời điểm riêng, nhưng nếu sau này cần "lọc hồ sơ sửa gần đây"
nói chung thì sẽ thiếu.

---

## Việc đã/sẽ áp vào `dev test`

Mục 2.1 và 2.2 (chỉ mục + CHECK) áp được ngay, không phá dữ liệu hiện có (đã đo giá trị thật
ở trên, không có dòng nào phạm luật mới). Xem §-section tương ứng trong
`backend/sql/legacy_schema.sql` và mục trong `kiem_luoc_do.py`.

Mục 3 giữ nguyên làm ghi chú — không tự áp, chờ quyết định.
