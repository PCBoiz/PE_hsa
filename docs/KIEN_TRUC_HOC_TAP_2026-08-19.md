# Đặc tả: nâng pe_hsa lên nền học tập kiểu Moodle/ERP — 19/08/2026

**Phạm vi**: đặc tả kiến trúc, chưa viết mã. Bốn trụ cột, hướng tới **thí sinh tự
học** — đợt này *không* làm vai trò giáo viên và lớp học.

---

## 1. Vấn đề gốc: dữ liệu học tập đang nằm rải rác

Mọi thứ cần cho một sổ điểm đã tồn tại, nhưng ở **năm nơi khác nhau**, mỗi nơi
một hình dạng, không nơi nào biết nơi nào:

| Nguồn | Bảng | Đang giữ gì |
|---|---|---|
| Bài học | `lesson_progress` | `quiz_score` (%), `xp_earned`, `completed_at` |
| Thi thử CBT | `mock_attempts` | `score/total`, `section_scores_json`, `duration_seconds` |
| Quiz ôn tập | `review_quiz_results` | `score/total`, `answers_json` |
| Nhiệm vụ ngày | `user_missions` | `xp_earned`, `mission_date` |
| XP theo ngày | `user_daily_xp_logs` | `xp_earned` mỗi ngày |

Hệ quả đo được:
- Không có màn hình nào trả lời được câu hỏi quan trọng nhất của thí sinh:
  **"tôi đang mạnh yếu ở đâu và tiến bộ tới đâu rồi?"**
- Mỗi lần thêm một loại hoạt động lại phải sửa mọi chỗ hiển thị.
- `topic_tag`/`module` — **19 chủ đề** đã gắn sẵn cho đủ 76 bài — chưa được
  dùng để chấm mạnh–yếu lần nào.

## 2. Nguyên tắc kiến trúc: một dòng sự kiện, nhiều cách đọc

Moodle giải bài toán này bằng cặp *Completion API* + *Gradebook*: hoạt động chỉ
việc **báo cáo một sự kiện**, còn sổ điểm và báo cáo tự đọc lại. Đề xuất làm
đúng như vậy, ở quy mô vừa với dự án:

```
   bài học ─┐
  thi thử ──┤
quiz ôn tập ┼──►  learning_events  ──►  sổ điểm · năng lực chủ đề
 nhiệm vụ ──┤     (một dòng/hoạt động)   kế hoạch · đường cong · trợ lý AI
 tự ghi nhận┘
```

**Vì sao đáng làm**: bốn trụ cột phía dưới nếu làm rời sẽ là bốn kho dữ liệu
riêng; nếu làm trên một dòng sự kiện thì trụ cột thứ hai trở đi gần như chỉ là
truy vấn khác nhau trên cùng một bảng.

### Bảng `learning_events`

```sql
CREATE TABLE learning_events (
    id           BIGSERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    occurred_at  TIMESTAMP NOT NULL,      -- giờ Việt Nam (common/clock.py)
    event_date   DATE NOT NULL,           -- tách sẵn để nhóm theo ngày cho rẻ
    kind         TEXT NOT NULL,           -- lesson | mock | review_quiz | mission | self_log
    course_id    TEXT,                    -- hsa_quantitative | hsa_verbal | hsa_science
    topic        TEXT,                    -- 1 trong 19 chủ đề (lessons.module)
    ref_type     TEXT,                    -- lesson | mock_attempt | quiz | mission
    ref_id       TEXT,
    score        NUMERIC(5,2),            -- điểm đạt (thang tự do theo max_score)
    max_score    NUMERIC(5,2),            -- mốc tối đa; NULL = hoạt động không chấm
    minutes      INTEGER,                 -- thời gian bỏ ra, nếu đo được
    xp           INTEGER DEFAULT 0,
    source       TEXT NOT NULL DEFAULT 'system',  -- system | self
    meta         JSONB
);
CREATE INDEX ON learning_events (user_id, event_date DESC);
CREATE INDEX ON learning_events (user_id, topic);
CREATE INDEX ON learning_events (user_id, kind, occurred_at DESC);
```

Hai điểm cố ý:
- **`source`** tách rạch ròi việc hệ thống ghi nhận với việc học viên **tự khai**.
  Mọi biểu đồ phải phân biệt được hai loại, nếu không số liệu thành nửa thật nửa
  tự nhận mà người xem không biết.
- **`topic`** chép lại lúc ghi sự kiện, không join ngược. Giáo trình sẽ được soạn
  lại theo TopHSA; chép giá trị giữ cho số liệu lịch sử không đổi nghĩa khi
  chương mục thay đổi.

### Cách nạp dữ liệu đang có

Ba nơi đã ghi đủ thông tin, chỉ cần thêm một lời gọi:
`lessons/views.py:CompleteLessonView` · `mockexam/views.py:MockSubmitView` ·
`quizzes/views.py:SubmitQuizView` · `stats/views.py:ClaimMissionView`.

Dữ liệu cũ nạp một lần bằng lệnh quản trị `backfill_learning_events` đọc lại 5
bảng ở mục 1. Rủi ro thấp: đây là bảng **đọc thêm**, không có gì đang phụ thuộc.

---

## 3. Trụ cột 1 — Sổ điểm & đường cong tiến bộ

### Câu hỏi cần trả lời
"Điểm tôi đang bao nhiêu, so với mục tiêu còn bao xa, và mấy tuần qua tôi có
khá lên không?"

### Dữ liệu
Đọc thẳng `learning_events`. Không thêm bảng.

### API
```
GET /api/hsa/gradebook
    → { rows: [ {kind, label, course, score, max, pct, at} … ],   # sổ điểm
        byKind: { lesson: {n, avgPct}, mock: {…}, review_quiz: {…} } }

GET /api/hsa/progress-curve?weeks=12
    → { points: [ {week, mockPct, lessonPct, minutes, events} … ],
        target: "Trên 105", daysToExam: 213 }
```

### Màn hình
Một khối mới trên **Trang của tôi**, dưới "Năng lực theo hợp phần":
- Đường điểm thi thử theo thời gian, mỗi lượt một điểm, có đường xu hướng.
- Cột thời lượng học mỗi tuần ở nền, thang riêng — cho thấy tương quan
  "học nhiều ↔ điểm lên" mà không trộn hai đơn vị vào một trục.
- Dải mục tiêu nằm ngang, để khoảng cách tới đích là thứ nhìn thấy chứ không
  phải tự tính.

> **Cần TopHSA xác nhận**: quy đổi từ `score/total` của đề thi thử sang thang
> điểm HSA thật. Cho tới lúc đó, biểu đồ chỉ hiện **phần trăm đúng** và ghi rõ
> đó không phải điểm HSA quy đổi.

---

## 4. Trụ cột 2 — Năng lực theo chủ đề

### Vì sao đây là trụ cột đáng giá nhất
19 chủ đề đã gắn sẵn cho đủ 76 bài (`lessons.module`) mà **chưa dùng lần nào**.
Đây là thứ biến số liệu thành hành động: thay vì "bạn được 62%", nói được
"Hình học 45% — yếu nhất; ôn tiếp 3 bài này".

| Hợp phần | Chủ đề |
|---|---|
| Định lượng | Số học · Đại số · Hàm số · Giải tích · Hình học · Thống kê & Xác suất · Xử lý số liệu · Chiến thuật |
| Định tính | Từ vựng · Ngữ pháp · Đọc hiểu · Văn học · Ngôn ngữ – Văn hóa · Chiến thuật |
| Khoa học | Vật lý · Hóa học · Sinh học · Lịch sử · Địa lý · Chiến thuật |

### Cách chấm một chủ đề
Điểm thành thạo 0–100, gộp bốn nguồn theo trọng số, **chỉ tính khi có dữ liệu**:

| Nguồn | Trọng số | Ghi chú |
|---|---|---|
| Kiểm tra đầu vào của bài (`test`) | 30% | phản ánh nền sẵn có |
| Luyện tốc độ (`drill`) | 20% | phản ánh tốc độ xử lý |
| Quiz ôn tập | 25% | phản ánh khả năng nhớ lâu |
| Thi thử (theo hợp phần) | 25% | phản ánh trong điều kiện thi |

Thiếu nguồn nào thì **chia lại trọng số cho các nguồn còn lại**, và trả kèm
`confidence` = số sự kiện đã có. Chủ đề mới học 1 bài phải hiện "chưa đủ dữ
liệu", tuyệt đối không hiện một con số nghe như đã đo được.

Điểm gần đây nặng hơn điểm cũ (trung bình có suy giảm theo thời gian) — người
học tiến bộ thì điểm phải phản ánh hiện tại, không bị bài làm sai tháng trước
kéo xuống mãi.

### API
```
GET  /api/hsa/competency
     → { topics: [ {topic, course, mastery, confidence, lessonsDone, lessonsTotal,
                    selfMarked, suggestion: {lessonIndex, title}} … ],
         weakest: [ … 3 chủ đề yếu nhất … ] }
PUT  /api/hsa/competency/<topic>/self   { known: true|false }
```

### Màn hình
- **Bản đồ năng lực** trên Trang của tôi: 19 ô, đậm nhạt theo mức thành thạo,
  ô chưa đủ dữ liệu để trống có gạch chéo.
- Ba chủ đề yếu nhất đẩy lên **Bảng điều khiển**, mỗi cái kèm đúng một nút:
  *"Ôn Hình học → Bài 12"*.

---

## 5. Trụ cột 3 — Kế hoạch học có lịch & hạn

### Câu hỏi cần trả lời
"Từ nay tới ngày thi, mỗi tuần tôi phải làm gì để kịp?"

Nguyên liệu đã có sẵn: `exam_date` / `exam_timing` (mục tiêu HSA), `study_time`
(khảo sát: giờ ôn mỗi ngày), 76 bài chia 19 chủ đề, và năng lực từng chủ đề ở
trụ cột 2.

### Bảng mới

```sql
CREATE TABLE study_plans (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMP NOT NULL,
    exam_date   DATE,                 -- chụp lại lúc sinh kế hoạch
    weekly_target JSONB,              -- {lessons: 5, mocks: 1, minutes: 300}
    is_active   BOOLEAN DEFAULT TRUE
);

CREATE TABLE study_plan_items (
    id          SERIAL PRIMARY KEY,
    plan_id     INTEGER NOT NULL REFERENCES study_plans(id) ON DELETE CASCADE,
    week_start  DATE NOT NULL,        -- thứ Hai của tuần
    kind        TEXT NOT NULL,        -- lesson | mock | review | topic_focus
    course_id   TEXT,
    lesson_no   INTEGER,
    topic       TEXT,
    status      TEXT DEFAULT 'todo',  -- todo | done | skipped
    done_at     TIMESTAMP
);
CREATE INDEX ON study_plan_items (plan_id, week_start);
```

### Cách sinh kế hoạch
1. Số tuần còn lại = từ hôm nay tới `exam_date` (thiếu thì suy từ `exam_timing`).
2. Sức chứa mỗi tuần = `study_time` × 7 ÷ thời lượng trung bình một bài.
3. Thứ tự bài: **chủ đề yếu trước**, nhưng chen bài của chủ đề đã học để không
   dồn toàn phần khó vào một tuần.
4. Mỗi 2 tuần chèn một đề thi thử; 2 tuần cuối chỉ luyện đề.
5. Không đủ thời gian cho 76 bài → nói thẳng *"lịch này bỏ qua N bài ít trọng số
   nhất"*, không im lặng cắt bớt.

Đánh dấu xong **không phải làm tay**: `study_plan_items` khớp với
`learning_events` theo `(kind, course_id, lesson_no)` và tự chuyển `done`.

### API
```
POST /api/hsa/study-plan          # sinh lại kế hoạch (ghi đè bản đang hoạt động)
GET  /api/hsa/study-plan          # tuần này + 3 tuần tới + % bám lịch
PUT  /api/hsa/study-plan/items/<id>   { status }   # bỏ qua một mục
```

### Màn hình
Khối **"Tuần này"** trên Bảng điều khiển, thay chỗ đang trống bên dưới nhiệm vụ:
danh sách việc của tuần, số việc đã xong / tổng, và một dòng trạng thái trung
thực — *"đang chậm 3 bài so với lịch"* — thay vì thanh tiến độ chung chung.

---

## 6. Trụ cột 4 — Học viên tự ghi nhận

Ba việc, theo đúng thứ tự ưu tiên đã chốt.

### 6.1 Nhật ký học hàng ngày
```sql
CREATE TABLE study_logs (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date   DATE NOT NULL,
    minutes    INTEGER,
    topic      TEXT,             -- 1 trong 19 chủ đề, không bắt buộc
    what       TEXT,             -- hôm nay học gì
    difficulty TEXT,             -- easy | ok | hard
    note       TEXT,             -- vướng ở đâu
    created_at TIMESTAMP NOT NULL,
    UNIQUE (user_id, log_date)   -- mỗi ngày một bản ghi, sửa được
);
```
Ghi kèm một `learning_events` với `kind='self_log'`, `source='self'` → thời
lượng tự khai vào được biểu đồ nhưng **luôn phân biệt được với số hệ thống đo**.

Giá trị kép: trợ lý AI đọc `note` + `difficulty` để tư vấn sát, thay vì chỉ biết
điểm số. Đây là dữ liệu mà không hệ thống nào tự đo được.

### 6.2 Mục tiêu tuần
Lưu ở `study_plans.weekly_target`, học viên tự chỉnh (5 bài/tuần, 1 đề/tuần…).
Đối chiếu với `learning_events` của tuần, báo đạt hay chưa. Không cần bảng mới.

### 6.3 Tự đánh dấu đã nắm chủ đề
```sql
CREATE TABLE topic_self_marks (
    user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic     TEXT NOT NULL,
    known     BOOLEAN NOT NULL,
    marked_at TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, topic)
);
```
Quy tắc: đánh dấu "đã nắm" thì bộ sinh kế hoạch **hạ ưu tiên** chủ đề đó, nhưng
điểm thành thạo **vẫn tính theo bài làm thật**. Nếu thi thử cho thấy chủ đề tự
nhận đã nắm lại đang yếu, hệ thống nói thẳng: *"bạn đánh dấu đã nắm Hình học,
nhưng đề gần nhất chỉ đúng 40% — xem lại nhé?"*. Tự đánh giá là **đầu vào để
xếp lịch, không phải bằng chứng về năng lực** — lẫn hai thứ này là cách nhanh
nhất khiến số liệu mất giá trị.

### API
```
GET/PUT /api/hsa/study-log?date=YYYY-MM-DD
GET     /api/hsa/study-log/recent?days=30
PUT     /api/hsa/weekly-target        { lessons, mocks, minutes }
PUT     /api/hsa/competency/<topic>/self   { known }
```

---

## 7. Đối chiếu với Moodle — cái gì mượn, cái gì bỏ

| Khối của Moodle | Đề xuất ở đây | Lý do |
|---|---|---|
| Completion API | `learning_events` | Cùng ý tưởng, gọn hơn nhiều |
| Gradebook | Trụ cột 1 | Bỏ phần danh mục điểm có trọng số lồng nhau — HSA chỉ có 3 hợp phần |
| Competency framework | Trụ cột 2, dùng 19 chủ đề sẵn có | Không dựng cây năng lực riêng: chương mục đã là cây đó |
| Calendar + Deadline | Trụ cột 3 | Bỏ lịch dùng chung; thí sinh tự học chỉ cần lịch của mình |
| Question bank | **Không làm đợt này** | Câu hỏi đang nhúng trong `content_json`; tách ra chỉ đáng khi có giáo trình TopHSA |
| Cohort / Group / Vai trò giáo viên | **Không làm đợt này** | Anh đã chốt: tập trung tự học |
| Quiz với nhiều lượt, chấm theo luật | Đã có ở mức đủ dùng | `mock_attempts` + `review_quiz_results` |
| Badge | Đã có | `achievements` (10 mốc, đang chạy) |

**Cố ý không mượn**: mô hình vai trò/ngữ cảnh phân quyền của Moodle. Nó là thứ
đắt nhất trong Moodle và chỉ trả công khi đã có giáo viên, lớp, nhiều khoá —
chưa đúng lúc.

---

## 8. Thứ tự làm & khối lượng

| # | Việc | Phụ thuộc | Ước lượng |
|---|---|---|---|
| 1 | `learning_events` + nạp dữ liệu cũ + 4 chỗ ghi | — | Nhỏ |
| 2 | Trụ cột 2 — năng lực 19 chủ đề + bản đồ | 1 | Vừa |
| 3 | Trụ cột 1 — sổ điểm + đường cong | 1 | Vừa |
| 4 | Trụ cột 4 — nhật ký, mục tiêu tuần, tự đánh dấu | 1 | Vừa |
| 5 | Trụ cột 3 — kế hoạch có lịch | 1, 2 | Lớn nhất |

Đề nghị làm theo đúng thứ tự này. Việc 1 rẻ và mở đường cho cả bốn. Việc 2 cho
giá trị nhìn thấy được sớm nhất (biến số liệu thành lời khuyên cụ thể). Việc 5
để cuối vì bộ sinh lịch chỉ tốt khi đã có điểm năng lực ở việc 2.

---

## 9. Rủi ro & điều phải giữ đúng

1. **Số tự khai không được trộn lẫn với số đo được.** Cột `source` tồn tại cho
   việc đó; mọi biểu đồ phải tách hai loại. Trộn vào là mất tin cậy của toàn bộ
   phần số liệu.
2. **Chưa đủ dữ liệu thì nói chưa đủ.** Điểm thành thạo tính từ 1–2 sự kiện
   không phải là đo lường. Luôn trả kèm `confidence` và để trống khi thấp.
3. **Giáo trình sẽ được soạn lại theo TopHSA.** Vì vậy `learning_events` chép
   `topic` thay vì tham chiếu, và không đầu tư vào ngân hàng câu hỏi lúc này.
4. **Quy đổi điểm HSA là của TopHSA, không phải của mình.** Trước khi có bảng
   quy đổi chính thức, mọi nơi chỉ hiện phần trăm đúng và ghi rõ như vậy.
5. **Múi giờ.** Mọi mốc ngày phải đi qua `common/clock.py`. Bài học rút ra hôm
   14/08: hai đồng hồ lệch 7 tiếng từng làm nhiệm vụ ngày đếm sai.
6. **Kế hoạch không được nói dối về sức chứa.** Không đủ tuần cho 76 bài thì nói
   rõ bỏ bài nào, thay vì lặng lẽ cắt.

---

## 10. Điều KHÔNG làm đợt này

- Vai trò giáo viên, lớp học, điểm danh, báo cáo lớp.
- Nhập điểm thi thử từ nguồn ngoài — anh chưa chọn; và nó cần quy tắc chống
  khai khống trước khi cho vào cùng biểu đồ với số đo được.
- Ngân hàng câu hỏi tách rời, học phí/đơn hàng, cổng phụ huynh.

Ba mục đầu là bước tự nhiên **sau khi** TopHSA chốt quy trình vận hành: lúc đó
`learning_events` đã sẵn sàng làm nguồn cho báo cáo lớp mà không phải dựng lại.

---

## 11. Trạng thái thực hiện — 24/08/2026

**ĐÃ LÀM: việc 1 (dòng sự kiện) và việc 2 (năng lực theo chủ đề).**
Việc 3, 4, 5 vẫn ở dạng đặc tả.

### Đã dựng

| Phần | Nơi |
|---|---|
| Bảng `learning_events` + `topic_self_marks` | `sql/legacy_schema.sql` §26 |
| Bộ ghi sự kiện (bọc savepoint) | `common/events.py` |
| Bốn chỗ ghi | `lessons/views.py` · `mockexam/views.py` · `quizzes/views.py` · `stats/views.py` |
| Nạp dữ liệu cũ | `common/management/commands/backfill_learning_events.py` |
| Chấm năng lực | `stats/competency.py` |
| API | `GET /api/hsa/competency` · `PUT /api/hsa/competency/self` |
| Giao diện | Bản đồ 20 ô ở Trang của tôi · khối "Nên ôn tiếp" ở Bảng điều khiển |

### Bốn chỗ lệch so với đặc tả gốc — và lý do

**1. 20 ô, không phải 19 chủ đề.** Khoá là CẶP (khoá học, chủ đề), không phải
tên chủ đề. "Chiến thuật" tồn tại ở cả ba hợp phần; gộp theo tên thì chiến thuật
làm bài Định lượng và chiến thuật Khoa học dồn chung một ô. 20 = 8 + 6 + 6.

**2. `PUT /api/hsa/competency/self` nhận `{courseId, topic, known}` trong body**
thay vì `/competency/<topic>/self`. Tên chủ đề là tiếng Việt có dấu, và đường
dẫn không nói được thuộc hợp phần nào.

**3. Thi thử tách làm hai loại sự kiện.** `mock` (tổng cả đề, nuôi đường cong
tiến bộ ở việc 3) và `mock_section` (theo hợp phần, nuôi bản đồ năng lực). Mỗi
dòng mang đúng một nghĩa; bên đọc chọn một loại nên không bao giờ cộng trùng.

**4. `dedup_key` bắt buộc, thay cho khoá tổ hợp.** Nhờ nó lệnh nạp dữ liệu cũ
chạy lại bao nhiêu lần cũng ra đúng một dòng, và học lại một bài thì CẬP NHẬT
dòng cũ — khớp với `lesson_progress`, bảng cũng chỉ giữ một dòng mỗi cặp
học viên–bài.

### Thêm ngoài đặc tả

**Phòng luyện tốc độ giờ mới được ghi lại.** Trước đây kết quả chỉ hiện lên màn
hình rồi biến mất — không nơi nào lưu, dù đó là thứ duy nhất trong sản phẩm đo
được TỐC ĐỘ dưới đồng hồ, đúng thứ kỳ thi HSA chấm. Nay `lesson_hsa.js` gửi kèm
lúc hoàn thành bài. Chấm trên TỔNG số câu, không phải số câu kịp làm: hết giờ mà
chưa xong cũng là một kết quả trong bài thi tính giờ.

**`bootstrap_schema` vào `render.yaml`.** Nó là nguồn DDL duy nhất cho 20+ bảng
legacy (`managed=False` nên `migrate` không đụng tới) mà trước giờ chạy tay —
mỗi lần thêm bảng là một lần mã lên production trước schema. Lệnh idempotent nên
chạy mọi lần deploy là an toàn.

**`review_quiz_results.submitted_at` ghi giờ Việt Nam** thay vì để `now()` của
Postgres (Neon trả UTC, lệch 7 tiếng — đúng cái bẫy ở mục 9.5).

### Cách chấm, viết gọn

Điểm 0–100 cho mỗi ô, gộp bốn nguồn theo trọng số 30/20/25/25, **chuẩn hoá lại**
khi thiếu nguồn, và **suy giảm theo thời gian** (bán rã 45 ngày).

Ô chỉ hiện số khi có **từ 2 HOẠT ĐỘNG trở lên** gắn với chính chủ đề đó. Đếm
theo hoạt động chứ không theo sự kiện: một bài học sinh ra 2 sự kiện (kiểm tra +
phòng luyện) nhưng vẫn chỉ là một lần chạm vào chủ đề. Điểm thi thử tham gia
phép tính nhưng **không được tính là bằng chứng về chủ đề** — đề chỉ chia theo
hợp phần, không biết câu nào thuộc chủ đề nào.

### Đã kiểm bằng cách chạy thật

Học 5 bài (có kèm phòng luyện) → sinh và nộp quiz ôn tập → nộp một đề thi thử,
tất cả qua HTTP thật với tài khoản thử. Kết quả khớp tay:

- Số học: kiểm tra (50+60)/2 = 55%, phòng luyện (1+2)/10 = 30%
  → (0,3×55 + 0,2×30) / 0,5 = **45**
- Quiz ôn tập 8 câu tách đúng theo chủ đề: 2/5 Đại số + 0/3 Số học = 2/8 tổng
- Một lượt thi thử → 1 dòng `mock` + 3 dòng `mock_section`, không trùng
- Chạy `backfill_learning_events` ba lần: vẫn đúng 11 dòng
- Sự kiện hỏng giữa giao dịch ghi tiến độ: giao dịch **vẫn commit** (savepoint)

### Việc còn phải làm khi deploy

Bản deploy hiện tại chưa có hai bảng mới. `render.yaml` đã thêm
`bootstrap_schema` nên lần deploy tới sẽ tự tạo; sau đó chạy một lần:

```
python manage.py backfill_learning_events
```
