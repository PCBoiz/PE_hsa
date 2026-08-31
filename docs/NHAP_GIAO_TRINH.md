# Nhập giáo trình vào hệ thống — 14/08/2026

Tài liệu này mô tả cách đưa nội dung bài học của đối tác vào nền tảng, để khi
TopHSA bàn giao giáo trình thì không phải sửa tay mã nguồn.

---

## Vì sao cần đường ống này

Trước 14/08/2026, toàn bộ 76 bài HSA nằm trong **một file JavaScript 364 kB phía
client** (`frontend/public/static/js/lesson_content_hsa.js`). Cột
`lessons.content_json` có sẵn trong cơ sở dữ liệu nhưng **không chỗ nào phục vụ
nó cho engine bài học**, nên trang Quản trị tạo bài xong thì học viên không bao
giờ nhìn thấy bài đó.

Hệ quả: nhận giáo trình đối tác về = mở file JS 364 kB ra sửa tay.

Giờ nội dung lưu trong cơ sở dữ liệu, engine đọc qua API. **Bài nào cơ sở dữ
liệu chưa có thì vẫn dùng bản trong file JS** — chuyển đổi được từng phần, bản
demo không gãy giữa chừng.

---

## Cách hoạt động

```
                 ┌── có trong DB?  ──→  dùng bản DB      (content_json)
engine bài học ──┤
                 └── chưa có       ──→  dùng bản file JS (lesson_content_hsa.js)
```

Trộn theo trường `index`. API lỗi hoặc mất mạng → rơi hết về file JS, học viên
vẫn học được bình thường.

---

## Ba đầu mối API

| Việc | Gọi |
|------|-----|
| Học viên đọc nội dung khoá | `GET /api/courses/<course_id>/content` |
| Soạn/sửa nội dung một bài | `GET/PUT /api/admin/lessons/<lesson_id>/content` |
| **Nhập cả khoá từ một file JSON** | `POST /api/admin/courses/<course_id>/import` |

Hai đầu mối `admin` đòi quyền quản trị.

### Nhập cả khoá

```bash
curl -X POST https://<host>/api/admin/courses/hsa_quantitative/import \
     -H "Authorization: Bearer <token quản trị>" \
     -H "Content-Type: application/json" \
     --data-binary @giao_trinh.json
```

Thân yêu cầu:

```json
{
  "lessons": [ { …bài 1… }, { …bài 2… } ],
  "total_lessons": 30
}
```

- `lessons` — mảng bài, tối đa **300 bài** mỗi lần.
- `total_lessons` — *không bắt buộc*. Đặt **chính xác** tổng số bài của khoá.
  Bỏ trống thì hệ thống chỉ **nâng** tổng số bài lên bằng `index` lớn nhất, không
  bao giờ hạ xuống (xem phần cảnh báo bên dưới).

Phản hồi: `{"ok": true, "created": 12, "updated": 15, "total": 27}`

**Kiểm toàn bộ trước khi ghi.** Chỉ cần một bài sai là **không bài nào** được
ghi — không có trạng thái nửa vời. Lỗi trả về nêu rõ vị trí:

```json
{
  "error": "3 lỗi trong dữ liệu nhập.",
  "details": [
    "bài thứ 1: thiếu trường bắt buộc \"theory\"",
    "bài thứ 2.test.questions[1]: \"answer\" phải nằm trong \"options\"",
    "bài thứ 5: \"index\" 4 trùng với bài thứ 4"
  ]
}
```

Nhập lại cùng một file là **cập nhật**, không nhân đôi (khớp theo `index`).

---

## Cấu trúc một bài

File mẫu chạy được: [`docs/mau_nhap_giao_trinh.json`](mau_nhap_giao_trinh.json)

```json
{
  "id": "ql_01",
  "index": 1,
  "title": "Tỉ lệ & phần trăm",
  "subtitle": "Tăng – giảm phần trăm và bài toán thực tế",
  "topic_tag": "Định lượng · Số học",
  "xp_reward": 50,

  "test": {
    "intro": "Làm nhanh 3 câu để hệ thống định vị năng lực của bạn.",
    "questions": [
      { "id": "t1", "type": "mcq",
        "question": "Áo 400.000đ giảm 25%, còn bao nhiêu?",
        "options": ["375.000đ", "350.000đ", "320.000đ", "300.000đ"],
        "answer": "300.000đ",
        "explain": "400.000 × 0,75 = 300.000đ." },
      { "id": "t2", "type": "fill",
        "question": "10% của 200 là bao nhiêu? (nhập số)",
        "answer": "20", "explain": "200 × 0,1 = 20." }
    ]
  },

  "assess": { "strong_min": 3, "ok_min": 2 },

  "theory": {
    "condensed": { "title": "Tóm tắt nhanh", "cards": [ … ] },
    "full":      { "title": "Lý thuyết đầy đủ", "cards": [ … ] }
  },

  "note":  { "title": "Ghi chú", "points": ["…"] },
  "drill": { "intro": "…", "time_seconds": 60, "questions": [ … ] }
}
```

### Trường bắt buộc

`id` · `index` · `title` · `test` · `theory`

| Trường | Ràng buộc |
|--------|-----------|
| `index` | số nguyên ≥ 1, **không trùng** trong cùng lần nhập; quyết định `?lesson=N` |
| `xp_reward` | số nguyên 0–500 |
| `test.questions` | mảng ≥ 1 câu; mỗi câu cần `question` và `answer` |
| câu `type: "mcq"` | cần `options` ≥ 2 lựa chọn, và `answer` **phải nằm trong** `options` |
| `theory` | cần ít nhất một trong `condensed` / `full`; mỗi bản cần `cards` ≥ 1 thẻ |
| cả bài | tối đa 400.000 byte |

### Lý thuyết thích ứng

Học viên làm đúng **≥ `assess.strong_min`** câu → nhận `theory.condensed` (bản
tóm tắt). Dưới ngưỡng → nhận `theory.full` (bản đầy đủ).

> ⚠️ Minh hoạ (`visual`) đặt trong `condensed` và `full` là **hai bản riêng**.
> Chỉ đặt ở `full` thì học viên giỏi sẽ không bao giờ nhìn thấy đồ thị.

### Minh hoạ trong thẻ lý thuyết

Mỗi thẻ trong `cards` có thể kèm `visual`. Tám kiểu đang hỗ trợ:

| `type` | Dùng cho |
|--------|----------|
| `bars` | so sánh đại lượng |
| `numline` | khoảng nghiệm, bất phương trình |
| `curve` | đồ thị hàm số |
| `flow` | chuỗi bước, quan hệ nhân quả |
| `table` | **đọc bảng số liệu** — dạng phổ biến nhất của Định lượng |
| `pie` | cơ cấu, tỉ trọng |
| `tree` | phân loại (từ loại, sinh vật, hoá vô cơ) |
| `timeline` | mốc lịch sử |

Ví dụ đầy đủ của cả 8 kiểu: xem `frontend/public/static/js/lesson_hsa.js`,
phần `VIZ_RENDERERS`.

---

## Cảnh báo: tổng số bài của khoá

`courses.lessons` nuôi mọi phần trăm tiến độ. Trong giai đoạn nội dung nằm ở
**hai nguồn**, con số này chỉ được phép **đi lên**.

Lý do: bảng `lessons` còn chứa các dòng *stub* tạo lười mỗi khi học viên hoàn
thành một bài (để giữ khoá ngoại cho `lesson_progress`). Đếm số dòng của bảng
này từng kéo tổng số bài của khoá Định lượng **từ 27 xuống 4** và làm sai toàn
bộ phần trăm tiến độ.

Khi bàn giao trọn giáo trình, gửi kèm `total_lessons` để đặt con số chính xác —
đó là đường duy nhất được phép hạ.

---

## Việc còn lại

- Giao diện soạn bài trong trang Quản trị (hiện mới có API).
- Chuyển 76 bài đang nằm trong file JS vào cơ sở dữ liệu — chỉ nên làm **sau
  khi** chốt giáo trình với đối tác, vì nội dung sẽ được biên soạn lại.
