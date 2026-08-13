# Nghiên cứu 5 hướng chưa audit — 14/08/2026

Mọi con số dưới đây **đo được**, không ước lượng: đếm trực tiếp trong mã nguồn,
truy vấn thẳng NeonDB, hoặc lái trình duyệt thật (Playwright, 1440px + 390px,
cả hai theme). Chưa sửa gì trong đợt này — đây là bản khảo sát để chốt ưu tiên.

---

## Tóm tắt: xếp theo mức độ đáng làm

| # | Hướng | Tình trạng | Công sức | Đáng làm |
|---|-------|-----------|----------|----------|
| 1 | **Gamification** | Mã nguồn XONG, bảng dữ liệu RỖNG | Rất thấp (seed) | ⭐⭐⭐⭐⭐ |
| 2 | **Nội dung 76 bài + đồ thị** | Nội dung đủ, minh họa 13% | Cao (66 bài) | ⭐⭐⭐⭐⭐ |
| 3 | **Responsive / mobile** | Không vỡ, nhưng chạm & chữ chưa đạt | Trung bình | ⭐⭐⭐⭐ |
| 4 | **Diễn đàn + cộng đồng** | Chạy được, không một bài nào | Thấp–TB | ⭐⭐⭐ |
| 5 | **Landing + đăng ký + khảo sát** | Ổn nhất trong 5 | Thấp | ⭐⭐ |

---

## 1. Gamification & động lực — **thứ đáng làm nhất, rẻ nhất**

### Phát hiện chính: động cơ đã lắp xong, chỉ thiếu xăng

`achievements/services.py` có đủ logic trao thành tích, chạy trong transaction
của `lessons.complete`, so số liệu thật (`lesson_count`, `streak_days`,
`xp_total`, `course_complete`) với điều kiện từng thành tích.

**Nhưng bảng `achievements` có 0 dòng.** Vòng lặp `for a in rows` không chạy lần
nào → không học viên nào từng nhận được thành tích, và không bao giờ nhận được.

```
achievements       0 dòng   ← trang "Thành tích" hiện 0/0 vĩnh viễn
missions           0 dòng
user_achievements  0 dòng
user_daily_xp_logs 0 dòng   (nay đã bắt đầu ghi, sau khi vá đường ống tiến độ)
```

Đây thuần túy là **thiếu dữ liệu mồi**, không phải thiếu tính năng. Viết ~12 dòng
INSERT là cả hệ thành tích sống dậy, không đụng một dòng mã nào.

### Đề xuất bộ thành tích HSA (dùng đúng 4 `condition_type` sẵn có)

| code | Tên | Điều kiện |
|------|-----|-----------|
| `first_lesson` | Bước đầu tiên | `lesson_count` ≥ 1 |
| `ten_lessons` | Vào guồng | `lesson_count` ≥ 10 |
| `half_way` | Nửa chặng đường | `lesson_count` ≥ 38 |
| `all_lessons` | Cày hết 76 bài | `lesson_count` ≥ 76 |
| `streak_3` / `streak_7` / `streak_30` | Chuỗi 3 / 7 / 30 ngày | `streak_days` |
| `xp_500` / `xp_2000` | 500 / 2.000 XP | `xp_total` |
| `finish_section` | Xong một hợp phần | `course_complete` ≥ 1 |

### Tàn dư pe_test cần dọn

Bảng `missions` có cột `correct_condition` và `correct_action` — đó là khái niệm
**nhiệm vụ SQL của pe_test** (điều kiện WHERE + hành động), vô nghĩa với HSA.
`/api/mission/complete` và `_verify_mission_by_course` đi kèm cũng vậy. Hoặc bỏ
hẳn, hoặc đổi thành nhiệm vụ ngày kiểu "làm 1 bài + 10 câu luyện tốc độ".

### Còn thiếu (cần viết mã)

- Không có **nhiệm vụ hằng ngày** thật → chuỗi ngày học không có việc để làm.
- Không có **bảo hiểm chuỗi** (streak freeze). Mất 1 ngày là về 1 —
  với thí sinh ôn thi 6 tháng, đây là điểm bỏ cuộc kinh điển.
- XP chỉ cộng khi xong bài; **thi thử và luyện tốc độ không cộng XP**.

---

## 2. Nội dung 76 bài + đồ thị

### Nội dung: ĐỦ và đều

```
Tổng             76 bài  (khớp đúng con số TOTAL_LESSONS trong backend)
  Định lượng     27 bài  ql_01 … ql_27
  Định tính      23 bài  vb_01 … vb_23
  Khoa học       26 bài  kh_01 … kh_26
```

Cả 76 bài đều đủ 4 phần `test` / `theory` / `note` / `drill`. File nội dung
364 kB.

### Lý thuyết thích ứng: CÓ CHẠY THẬT — đã kiểm

Câu hỏi cũ của anh ("làm đúng hết thì lý thuyết có ngắn đi không, hay đúng sai
vẫn thế") — **có ngắn đi thật**:

- Cả 76 bài đều có **hai bản** lý thuyết: `theory.condensed` (77) và
  `theory.full` (77).
- `lesson_hsa.js:75` chấm bài kiểm tra đầu vào → `state.level`;
  `strong` → `condensed`, `ok`/`weak` → `full`.
- Người học thấy nhãn "Bản tóm tắt — bạn đã khá vững" hoặc "Bản đầy đủ — theo
  kết quả kiểm tra".

Chỉ có một điểm chặt: phải đúng **toàn bộ** (`strong_min` mặc định = số câu) mới
được bản gọn. Có thể nới xuống "đúng ≥ 2/3".

### Đồ thị: **10/76 bài — 13%**

```
có `visual`   10 bài
  bars         5
  curve        2
  flow         2
  numline      1
66 bài không có một minh họa nào
```

Đây chính là cái anh nói "lý thuyết quá ngán". Bộ máy vẽ (`renderVisual`) đã
chạy tốt và có sẵn 4 kiểu; việc còn lại thuần là **soạn dữ liệu `visual`** cho
66 bài, không phải viết mã.

Kiểu đồ thị còn thiếu mà HSA rất cần:
- **Bảng số liệu** (đọc bảng là dạng câu hỏi rất phổ biến của Định lượng)
- **Biểu đồ tròn** (cơ cấu, tỉ trọng)
- **Sơ đồ cây / phân loại** (Sinh học, Ngữ văn — phân loại từ loại)
- **Trục thời gian** (Lịch sử)

---

## 3. Responsive / mobile

Đo ở 390 × 844 (iPhone 14) và 1440 × 900, cả 2 theme.

### Đạt

- **Không trang nào tràn ngang** ở 390px — kể cả Trang của tôi, sau khi vá
  `.page` trong đợt này (trước đó tràn 401 > 390).
- 0 lỗi JS ở mọi trang, cả 2 bề ngang.
- Không ảnh nào thiếu `alt`.

### Chưa đạt

**Vùng chạm dưới 44×44px** (Apple HIG / Material 48dp):

| Trang | Số vùng | Tệ nhất |
|-------|---------|---------|
| Diễn đàn | 41 | `bell-btn` 32×32 · `theme-toggle-btn` 34×34 · `nav-btn` 36×32 |
| Bài học | 11 | `exit-btn` 32×38 · `nav-btn` 44×33 |
| Đăng ký | 6 | `toggle-eye` **17×17** · liên kết 69×14 |
| Đăng nhập | 5 | `toggle-eye` **17×17** |
| Khảo sát | 5 | radio **15×15** (bấm vào nhãn thì vẫn được) |
| Thi thử | 5 | `mk-nav-link` cao 25px |

`toggle-eye` 17×17 ở màn đăng nhập là nghiêm trọng nhất: nút hiện/ẩn mật khẩu
nhỏ hơn nửa ngưỡng, ngay ở màn hình đầu tiên người dùng chạm vào.

**Chữ dưới 12px:**

| Trang | Số phần tử | Nhỏ nhất |
|-------|-----------|----------|
| Diễn đàn | 53 | 9.5px |
| Bài học | 16 | `xp-text` **9px** |
| Landing | 8 | 11px |

**Cấu trúc tiêu đề:** trang Khảo sát và Bảng điều khiển/Diễn đàn **không có
`<h1>`** — trình đọc màn hình mất mốc điều hướng.

### Việc nên làm

1. Nâng sàn vùng chạm: một luật chung `min-height: 44px` cho `button`/`a` trong
   `@media (pointer: coarse)`, cộng vùng chạm nới rộng cho các nút icon.
2. Nâng sàn cỡ chữ mobile lên 12px (nhãn phụ) / 16px (chữ chạy — tránh Safari iOS
   tự phóng to ô nhập).
3. Thêm `<h1>` ẩn về mặt thị giác cho khảo sát và các trang con của bảng điều khiển.

---

## 4. Diễn đàn + cộng đồng

### Tính năng: đã dựng gần đủ

| Có | Không có |
|----|----------|
| Đăng bài, sửa, xoá | Trích dẫn / trả lời lồng nhau |
| 3 chuyên mục: Câu hỏi · Chia sẻ · Thảo luận | Đánh dấu "đã giải quyết" cho Câu hỏi |
| Bình luận + thả cảm xúc (6 loại) | Gắn thẻ theo hợp phần / bài học |
| Theo dõi người dùng (`user_follows`) | Thông báo khi có người trả lời bài của mình |
| Lọc theo chuyên mục, sắp xếp | Tìm kiếm trong diễn đàn |

### Vấn đề thật sự: rỗng hoàn toàn

```
posts          0
comments       0
post_likes     0
comment_likes  0
user_follows   0
users          3   (2 tài khoản thật + 1 quản trị)
```

Diễn đàn **không hỏng** — nó chỉ chưa có ai dùng. Với PoC, một diễn đàn trống
trông như tính năng chết. Hai lựa chọn:

- **A.** Mồi 8–12 bài mẫu đúng chất HSA ("Câu 47 đề minh hoạ giải sao ạ?",
  "Mẹo loại trừ nhanh phần đọc hiểu") — nhãn rõ là bài mẫu để không lừa người xem.
- **B.** Chưa mồi, nhưng thay khối rỗng bằng lời mời cụ thể + gợi ý chủ đề, thay
  vì dòng "Chưa có bài viết nào".

Điểm đáng nối nhất: **liên kết diễn đàn với bài học**. Học viên đang ở bài 12
Định lượng thì thấy ngay các câu hỏi gắn với bài 12 — dữ liệu ngữ cảnh đã có
sẵn (chatbot đang dùng), chỉ thiếu cột `lesson_id` trên `posts`.

---

## 5. Landing + đăng ký + khảo sát — **lành nhất trong 5 hướng**

- Cả 3 trang: **không tràn ngang**, **0 lỗi JS**, có `<h1>`, ảnh có `alt`.
- Khảo sát 16 bước chạy đúng, khoá nút "Tiếp tục" khi chưa trả lời, có thanh
  tiến trình.

### Điểm cần chỉnh

1. **`toggle-eye` 17×17** ở đăng nhập/đăng ký (xem mục 3).
2. **Điều khoản 11.52px** ở trang đăng ký — chữ pháp lý mà nhỏ nhất trang.
3. **Nút CTA của landing cao 39px** — dưới 44px ở cả desktop.
4. Khảo sát **không có `<h1>`**.
5. Khảo sát hỏi mốc thi dạng **khoảng tương đối** ("Trong 1 tháng"), trong khi
   đợt này đã thêm ô **ngày thi chính xác** ở Cài đặt → nên hỏi luôn ở khảo sát,
   để thẻ đếm ngược đúng ngay từ đầu.
6. Landing chưa nói rõ **HSA là gì / thi để làm gì** — người chưa biết ĐGNL sẽ
   không hiểu đang bán cái gì.

---

## Việc "chưa kiểm lúc lên kế hoạch" — đã kiểm xong

| Việc | Kết quả |
|------|---------|
| Responsive 390 / 768 | Xong — không trang nào tràn ngang |
| Tương phản tự động 2 theme | Xong — 17 chỗ #9CA3AF (2.5:1) đã nâng lên 4.8:1 |
| Diễn đàn | Xong — chạy được, dữ liệu rỗng |
| Khảo sát | Xong — 16 bước chạy đúng |

Còn nợ: **tương phản ở Bảng điều khiển / Khóa học / Diễn đàn**. Máy quét báo
dashboard 39/57, courses 30/43, forum 48/62 phần tử đạt chuẩn — nhưng bộ đo hiện
tại tính sai với nền bán trong suốt nên **con số này chưa chắc chắn**, cần kiểm
lại bằng bộ đo có ghép alpha trước khi coi là lỗi.

---

## Đề xuất thứ tự làm

1. **Seed thành tích** (~30 phút) — mở khoá cả hệ gamification, không sửa mã.
2. **Sàn vùng chạm + cỡ chữ mobile** (~1–2 giờ) — một khối CSS, ăn cả app.
3. **Đồ thị cho 66 bài còn lại** — việc lớn nhất, nên chia theo hợp phần và làm
   Định lượng trước (dạng bài đọc số liệu cần minh họa nhất).
4. **Dọn tàn dư `missions`** của pe_test.
5. **Gắn diễn đàn vào bài học** (`posts.lesson_id`) + mồi nội dung.
6. Landing: thêm phần giải thích HSA.
