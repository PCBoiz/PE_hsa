# Đặc tả: pe_hsa thành ERP cho giảng viên & học viên TopHSA — 24/08/2026

**Trạng thái**: mục 3 (vai trò + lớp + báo cáo giảng viên) **đã dựng xong và
chạy được**; các mục còn lại là đặc tả, chờ TopHSA chốt quy trình vận hành.

---

## 1. Nền đã có — và vì sao nó quan trọng

Năm trụ cột học tập dựng xong hôm nay (xem `KIEN_TRUC_HOC_TAP_2026-08-19.md`)
làm cho phần khó nhất của một ERP giáo dục **đã xong trước**:

| Đã có | Ý nghĩa với ERP |
|---|---|
| `learning_events` — một dòng sự kiện cho mọi hoạt động | Báo cáo lớp/khoá/trung tâm chỉ là các cách gom nhóm khác nhau trên MỘT bảng |
| Năng lực 20 chủ đề, có `confidence` | Giảng viên biết em nào yếu ở ĐÂU, không phải chỉ "điểm thấp" |
| Sổ điểm, đường tiến bộ | Báo cáo phụ huynh gần như chỉ cần đóng gói lại |
| Kế hoạch học có lịch + độ chậm | Cảnh báo sớm có sẵn thước đo |
| Nhật ký tự ghi | Dữ liệu định tính mà không LMS nào tự đo được |

Nói cách khác: **phần dữ liệu đã xong, phần còn lại chủ yếu là quy trình.**

## 2. Khoảng cách so với một ERP đầy đủ

| Nhóm | Thiếu gì |
|---|---|
| Tổ chức | ~~Vai trò giảng viên~~ · ~~lớp học~~ · trợ giảng, quản lý học vụ, phụ huynh · nhiều cơ sở |
| Vận hành | Buổi học có lịch · điểm danh · giao bài & chấm tay · sổ đầu bài |
| Báo cáo | ~~Bảng điều khiển lớp~~ · báo cáo phụ huynh định kỳ · báo cáo trung tâm · xuất Excel/PDF |
| Kinh doanh | Học phí, công nợ, hoá đơn · gói khoá & khuyến mãi · thù lao giảng viên |
| Chăm sóc | Cổng phụ huynh · thông báo Zalo/SMS/email · CRM tuyển sinh |
| Nền tảng | Nhật ký kiểm toán · sao lưu/xuất dữ liệu · phân quyền nhiều cấp |

(Gạch ngang = đã làm trong đợt này.)

---

## 3. ĐÃ LÀM — Vai trò Giảng viên, Lớp học, Báo cáo lớp

### 3.1 Vai trò và nguyên tắc phân quyền

Trước đây quyền là **nhị phân**: `is_admin(user)` — đúng với một sản phẩm tự
học, sai ngay từ gốc với một trung tâm. Nay:

- Thêm vai trò `Giảng viên` (ghi vào `users.role`, cột vốn đã là TEXT tự do).
- **Quyền theo NGỮ CẢNH, không theo vai trò**: `can_see_class(user, class_id)` —
  quản trị viên xem mọi lớp, giảng viên xem lớp mình phụ trách.
- Lớp không thuộc mình trả **404 chứ không 403** — không tiết lộ lớp đó có tồn
  tại hay không.

Cố ý **không** dùng lại `courses.instructor_id` (đã có sẵn nhưng luôn NULL): một
giảng viên phụ trách **lớp**, không phụ trách cả khoá — cả ba khoá HSA dùng
chung cho mọi lớp.

### 3.2 Bảng mới

`classes` (mã, tên, khoá, giảng viên, **lịch học**, **link phòng học**, khai
giảng, kỳ thi nhắm tới, sĩ số, trạng thái) và `class_members`.

Học viên rời lớp đánh dấu `left_at` chứ **không xoá dòng**: em nghỉ giữa chừng
vẫn phải còn trong báo cáo của kỳ đó.

### 3.3 Bảng điều khiển lớp

`GET /api/teach/classes/<id>` trả trong **6 lượt truy vấn cho cả lớp**, không
phải 2×N lượt — gọi bộ tính năng lực cho từng em trong lớp 30 người là 60 lượt
× 245ms ≈ 15 giây.

Mỗi học viên: tiến độ, chuỗi ngày, hoạt động gần nhất, số đề đã làm, xu hướng
điểm thi thử, độ chậm kế hoạch, 3 chủ đề yếu nhất.

**Cảnh báo sớm** — mỗi cái là một câu *nói được làm gì tiếp*:
- `10 ngày không mở bài nào.`
- `Chưa làm đề thi thử nào.`
- `Điểm thi thử giảm 12 điểm % so với lượt trước.`
- `Chậm 7 bài so với kế hoạch.`

"Nam đang yếu" thì giảng viên không làm gì được; "Nam 9 ngày không mở bài" thì
gọi điện được.

### 3.4 Ba ranh giới đã đặt

1. **Không xếp hạng học viên trong lớp.** Bảng sắp theo "cần chú ý trước", nhưng
   không có cột hạng — bảng xếp hạng nội bộ làm hỏng động lực của đúng những em
   cần giữ lại nhất, mà giảng viên vẫn đọc được thứ tự từ số liệu.
2. **Giảng viên và học viên nhìn CÙNG một con số.** Hồ sơ học viên trong khu
   giảng dạy dùng lại đúng các hàm học viên tự thấy. Hai bên thấy hai số khác
   nhau cho cùng một chủ đề là hỏng cả buổi tư vấn.
3. **Nhật ký tự ghi là dữ liệu riêng tư kiểu khác.** Giảng viên xem được vì để
   tư vấn, nhưng giao diện ghi rõ: *"Đây là phần học viên tự viết cho mình. Dùng
   để tư vấn, đừng đọc lại trước lớp."* Xem mục 8.

### 3.5 Bản đồ năng lực cấp lớp

Trung bình chỉ tính trên những học viên **đã đo được** ô đó. Không lấy trung
bình toàn lớp: người chưa đủ dữ liệu mà tính là 0 thì mọi chủ đề đều trông như
cả lớp đang dốt. Mỗi ô kèm `2/3 học viên đã đo`.

---

## 4. Buổi học & điểm danh (chưa làm — cần TopHSA xác nhận)

Anh cho biết TopHSA dạy **lớp online có lịch cố định**, nên mô-đun này là bước
tiếp theo tự nhiên. Đợt này mới lưu **mô tả** lịch (`classes.schedule`) và link
phòng học; từng buổi cụ thể chưa có.

```sql
CREATE TABLE class_sessions (
    id SERIAL PRIMARY KEY,
    class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
    starts_at TIMESTAMP NOT NULL,
    duration_minutes INTEGER,
    topic TEXT,                -- chủ đề buổi, nối được với 20 chủ đề sẵn có
    lesson_refs JSONB,         -- các bài trong giáo trình buổi này dạy
    meeting_url TEXT,
    recording_url TEXT,
    status TEXT,               -- planned | done | cancelled
    note TEXT                  -- sổ đầu bài
);
CREATE TABLE attendance (
    session_id INTEGER REFERENCES class_sessions(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    status TEXT NOT NULL,      -- present | late | absent | excused
    minutes INTEGER,           -- số phút có mặt, nếu nền tảng họp trả về được
    marked_by INTEGER,
    marked_at TIMESTAMP,
    PRIMARY KEY (session_id, user_id)
);
```

**Điểm danh đẻ một `learning_events`** với `kind='attendance'` — nhờ đó số buổi
đi học vào thẳng đường cong tiến bộ và cảnh báo sớm mà không phải viết lại gì.

**Câu phải hỏi TopHSA trước khi làm**: dạy trên nền tảng nào (Zoom/Meet/Zalo)? Có
API lấy danh sách người tham dự không? Nếu có thì điểm danh tự động; nếu không
thì giảng viên tick tay — hai thiết kế khác hẳn nhau.

## 5. Giao bài & chấm tay (chưa làm)

Hiện chỉ chấm được trắc nghiệm. Trung tâm luyện thi cần giao bài tự luận, đặc
biệt phần Định tính.

```sql
CREATE TABLE assignments (
    id SERIAL PRIMARY KEY, class_id INTEGER, title TEXT, description TEXT,
    topic TEXT, due_at TIMESTAMP, max_score NUMERIC(6,2),
    attachment_url TEXT, created_by INTEGER, created_at TIMESTAMP
);
CREATE TABLE submissions (
    assignment_id INTEGER, user_id INTEGER,
    submitted_at TIMESTAMP, content TEXT, file_url TEXT,
    score NUMERIC(6,2), feedback TEXT, graded_by INTEGER, graded_at TIMESTAMP,
    PRIMARY KEY (assignment_id, user_id)
);
```

Chấm xong đẻ `learning_events` với `kind='assignment'`, có `topic` → **điểm tự
luận vào thẳng bản đồ năng lực**, không cần luật riêng.

**Cần TopHSA**: có chấm tự luận không, thang điểm nào, ai chấm (giảng viên hay
trợ giảng)?

## 6. Báo cáo phụ huynh & trung tâm (chưa làm)

- **Phụ huynh**: báo cáo định kỳ (tuần/tháng) — tiến độ, chuyên cần, điểm thi
  thử, 3 chủ đề yếu, nhận xét của giảng viên. Gửi qua Zalo/email.
- **Trung tâm**: tỉ lệ hoàn thành theo lớp/giảng viên, tỉ lệ bỏ học, điểm thi
  thử trung bình theo đợt.
- **Xuất Excel/PDF** — bắt buộc với trung tâm, họ luôn cần bản mang đi họp.

Toàn bộ đọc từ `learning_events` + `classes`; **không cần bảng mới**.

**Cần TopHSA**: gửi qua kênh nào, tần suất, ai duyệt trước khi gửi.

## 7. Kinh doanh (chưa làm — phụ thuộc nặng nhất vào TopHSA)

Học phí, công nợ, hoá đơn, gói khoá, khuyến mãi, thù lao giảng viên, CRM tuyển
sinh. Đây là phần **không tận dụng được gì** đã dựng và sai một chi tiết là sai
sổ sách. Khuyến nghị: chỉ làm sau khi có quy trình thu chi thật của TopHSA, và
cân nhắc nối với phần mềm kế toán họ đang dùng thay vì viết lại.

## 8. Quyền riêng tư — phải chốt trước khi mở rộng

Càng nhiều vai trò thì càng nhiều người nhìn thấy dữ liệu của một đứa trẻ. Ba
điều nên chốt thành chính sách, không để mặc định:

1. **Nhật ký tự ghi**: học viên viết cho mình. Đợt này giảng viên xem được và
   giao diện nói rõ mục đích. Nếu TopHSA muốn chặt hơn, có thể cho học viên bật
   tắt quyền xem — cần quyết định, không nên để ngầm.
2. **Phụ huynh xem được gì**: tiến độ và điểm là hợp lý; nhật ký và ghi chú
   riêng thì nên hỏi ý học viên.
3. **Nhật ký kiểm toán**: ai xem/sửa dữ liệu của ai. Bắt buộc khi có nhiều vai
   trò — và rẻ nếu làm sớm, đắt nếu làm muộn.

## 9. Thứ tự đề nghị

| # | Việc | Phụ thuộc TopHSA | Ước lượng |
|---|---|---|---|
| ✅ 1 | Vai trò Giảng viên + lớp + báo cáo lớp | không | **xong** |
| 2 | Buổi học + điểm danh | **có** (nền tảng họp) | vừa |
| 3 | Báo cáo phụ huynh + xuất Excel/PDF | ít | vừa |
| 4 | Giao bài & chấm tay | **có** (có chấm tự luận không) | vừa |
| 5 | Nhật ký kiểm toán + phân quyền nhiều cấp | không | nhỏ |
| 6 | Thông báo Zalo/email ra ngoài | **có** (kênh nào) | vừa |
| 7 | Học phí, công nợ, thù lao, CRM | **có** (quy trình kế toán) | lớn nhất |

Việc 5 nên chen lên sớm dù nhỏ: nó rẻ khi làm trước, đắt khi làm sau.

## 10. Điều cố ý CHƯA làm

Trợ giảng, quản lý học vụ, cổng phụ huynh, nhiều cơ sở, và toàn bộ nhóm kinh
doanh. Lý do giống nhau: **chưa biết TopHSA có những chức danh và quy trình nào**,
mà dựng một bộ màn hình cho một vai trò không tồn tại thì vừa tốn vừa phải đập.
