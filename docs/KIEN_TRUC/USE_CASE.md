# Use case — ai làm được gì

Viết tay, đo 01/09/2026. Ba vai trò trong `users.role`: `admin`,
`Giảng viên`, `Học viên` (`backend/common/permissions.py`).

**Quyền ở đây theo NGỮ CẢNH, không theo vai trò.** Là giảng viên không có nghĩa
là xem được mọi lớp — câu hỏi thật luôn là *"tôi có phụ trách lớp này không"*
(`can_see_class`). Quản trị viên thì xem được tất cả. Mỗi endpoint tự kiểm một
kiểu là cách chắc chắn để hở dữ liệu học viên, nên chỉ có một hàm giữ luật ấy.

---

## Bản đồ use case

```mermaid
flowchart LR
  HV(("👤 Học viên"))
  GV(("👤 Giảng viên"))
  QT(("👤 Quản trị viên"))

  subgraph H["Học"]
    U1["Học một bài<br/><small>kiểm tra → lý thuyết → phòng luyện</small>"]
    U2["Làm quiz ôn tập"]
    U3["Thi thử CBT"]
    U4["Xem bản đồ năng lực"]
    U5["Xem / bám kế hoạch học"]
    U6["Ghi nhật ký học"]
    U7["Hỏi trợ lý"]
    U8["Diễn đàn"]
  end
  subgraph D["Giảng dạy"]
    T1["Quản lớp & thành viên"]
    T2["Điểm danh buổi học"]
    T3["Giao bài & chấm tay"]
    T4["Xem báo cáo lớp"]
    T5["Xuất báo cáo cho phụ huynh"]
    T6["Đặt lại mật khẩu học viên"]
  end
  subgraph A["Quản trị"]
    A1["Cấp tài khoản & đổi vai trò"]
    A2["Nhập giáo trình"]
    A3["Quản đợt học"]
    A4["Xem nhật ký quản trị"]
  end

  HV --> U1 & U2 & U3 & U4 & U5 & U6 & U7 & U8
  GV --> T1 & T2 & T3 & T4 & T5 & T6
  QT --> A1 & A2 & A3 & A4
  QT -.->|"xem được mọi lớp"| D
```

---

## Bốn luồng có luật riêng — đọc kỹ trước khi sửa

### UC-1 · Học một bài

```mermaid
sequenceDiagram
  autonumber
  actor HV as Học viên
  participant FE as Engine bài học
  participant BE as Django
  participant DB as Postgres

  HV->>FE: mở bài
  FE->>BE: GET /api/courses/{k}/content
  BE-->>FE: nội dung ĐÃ CẮT đáp án
  Note over BE: bo_dap_an cắt ở TẦNG ĐỌC,<br/>không ở từng view

  HV->>FE: trả lời bài kiểm tra đầu vào
  FE->>BE: POST .../lessons/{n}/check
  BE->>DB: GHI NHẬN câu trả lời (lần đầu thắng)
  BE-->>FE: đúng/sai + đáp án + lời giải
  Note over BE: gửi bừa để moi đáp án thì<br/>bộ bừa ấy CHÍNH LÀ bài làm

  HV->>FE: phòng luyện, từng câu
  FE->>BE: POST .../check {phan:"drill"}
  BE-->>FE: CHỈ đúng/sai (không đáp án)

  HV->>FE: hoàn thành
  FE->>BE: POST /api/lessons/{n}/complete {answers, drill}
  BE->>DB: chấm trên phần ĐÃ GHI NHẬN
  BE->>DB: lesson_progress · enrollments · learning_events
  BE-->>FE: xpGained (máy chủ tính)
```

**Ba luật của luồng này** — đổi một cái là mở lại một lỗ đã đo được:

1. Đáp án không rời máy chủ trước khi học viên trả lời.
2. Điểm và XP được **TÍNH**, không được **NHẬN** — thân request không quyết định
   được con số nào.
3. Điểm vào sổ là điểm của **lần đầu đo được**. Không phải sở thích: `/check`
   phải trả đáp án cho phần xem lại, và `/complete` xoá khoá để lần ôn sau bắt
   đầu sạch — hai thứ ấy cộng lại cho một đường vòng mà "giữ điểm cao nhất"
   không đóng được (0 → 100 là đi LÊN).

### UC-2 · Thi thử CBT

```mermaid
stateDiagram-v2
  [*] --> ChuaMo
  ChuaMo --> DangMo: POST /start<br/>(ghi started_at, chốt `counted`)
  DangMo --> DangMo: POST /save<br/>(lưu tạm, TỪ CHỐI sau chuông)
  DangMo --> DaNop: POST /submit trong hạn<br/>→ vào sổ nếu counted
  DangMo --> DaNop: POST /submit quá hạn<br/>→ KHÔNG vào sổ, `counted` GIỮ NGUYÊN
  DangMo --> DaNop: /start lần sau khi đã cạn giờ<br/>→ chấm phần đã lưu
  DaNop --> [*]
```

**Cột `counted` chốt lúc MỞ và không bao giờ đổi sau đó.** Chốt lúc nộp thì "mở
đề, đọc hết, đóng tab, hôm sau bắt đầu lại" là cách làm lại vô hạn mà vẫn được
tính điểm. Hai ràng buộc duy nhất phần trong CSDL giữ luật này, không để mã tự
canh — ở mức cách ly `read committed`, một câu SELECT rồi INSERT không chặn được
năm request song song.

### UC-3 · Giảng viên xem báo cáo lớp

Cửa vào là `IsTeacherOrAdmin`, nhưng vào được **không** có nghĩa là xem được mọi
lớp. Mỗi endpoint hỏi `can_see_class(user, class_id)`; quản trị viên luôn qua.
Đây là nơi dễ hở nhất trong cả hệ: một endpoint mới quên hỏi là lộ dữ liệu học
viên của lớp khác.

### UC-4 · Quản trị nhập giáo trình

```mermaid
flowchart LR
  QT["Quản trị viên"] --> V["validate_lesson<br/><small>kiểm test · theory · drill</small>"]
  V -->|"hợp lệ"| W["ghi content_json"]
  V -->|"lỗi"| E["trả danh sách lỗi<br/>kèm đường dẫn tới chỗ sai"]
  W --> C["quen_dap_an<br/><small>xoá đệm đáp án</small>"]
```

`index` trong nội dung **phải khớp** `sort_order` của dòng đang sửa. Lệch thì
học viên học bài 5 nhưng tiến độ ghi sang bài 28, và bài 5 được chấm bằng đáp án
của bài 28.

---

## Use case đã dựng nhưng CHƯA AI DÙNG

Đo từ số dòng trong CSDL (01/09/2026) — 12 bảng đang rỗng:

| Use case | Bảng rỗng | Nghĩa là |
|---|---|---|
| Giao bài & chấm tay | `assignments`, `submissions` | đã dựng đủ (ERP §5), chưa giao bài nào |
| Điểm danh | `attendance`, `class_sessions` | chưa mở buổi học nào |
| Đợt học | `terms` | chưa tạo đợt |
| Đánh giá khoá | `course_ratings` | **chưa ai chấm sao** — và trang khoá từng khoe 5.0 |
| Diễn đàn (bình luận, thích) | `comments`, `post_likes`, `comment_likes` | có 9 bài viết, chưa ai tương tác |
| Theo dõi nhau | `user_follows` | chưa dùng |
| Thông báo | `notifications` | chưa gửi cái nào |
| Lộ trình chi tiết | `roadmap_progress` | có 4 lộ trình, chưa tick mục nào |

Danh sách này đáng đọc lại **trước khi thêm tính năng mới**: một nửa hệ thống
đang chờ người dùng đầu tiên.
