# Việc của anh — pe_hsa

Những việc **chỉ anh làm được**: cần khoá bí mật, cần bảng điều khiển Render /
Vercel, cần quyết định sản phẩm, hoặc cần hỏi TopHSA. Mọi thứ khác nằm ở
`TODO.md` và tôi tự làm.

Cập nhật **31/08/2026**. Nhánh `erp` đã push lên
`github.com/PCBoiz/PE_hsa`, **chưa** gộp vào `master`.
Xem đang trước `master` bao nhiêu mốc: `git rev-list --count origin/master..erp`

Đánh dấu `[x]` khi xong để lần sau khỏi đọc lại từ đầu.

---

## A · Ba chốt bảo mật — chặn đường lên production

### [ ] A1. Xoay `SECRET_KEY`

**Vì sao gấp:** khoá hiện tại dài **19 byte**. RFC 7518 yêu cầu tối thiểu 32 byte
cho HS256 — thuật toán đang ký mọi JWT của hệ thống. Thư viện `pyjwt` cảnh báo
đúng chuyện này mỗi lần sinh token; cảnh báo đó xuất hiện suốt phiên làm việc
31/08.

```bash
python -c "import secrets;print(secrets.token_urlsafe(48))"
```

Dán chuỗi đó vào **hai** nơi:

1. `backend/.env` — dòng `SECRET_KEY=`
2. Render → dịch vụ `pe-hsa-backend` → **Environment** → `SECRET_KEY`

**Tôi cố ý không sinh sẵn khoá cho anh.** Sinh ra trong khung chat là nó nằm lại
trong bản ghi hội thoại — khoá lộ trước khi kịp dùng.

**Hệ quả khi đổi:** mọi người đang đăng nhập bị đăng xuất, phải đăng nhập lại.
Mật khẩu **không** ảnh hưởng — băm werkzeug độc lập với `SECRET_KEY`.

---

### [ ] A2. Đo `NUM_PROXIES` trên production

**Lỗ đã đo được:** xoay header `X-Forwarded-For` thì **300/300 request lọt qua**
giới hạn tần suất; cùng bộ đó với IP cố định thì **200/300 bị chặn**. Nghĩa là
giới hạn đăng nhập, giới hạn tạo tài khoản, giới hạn chat đều vô hiệu với bất kỳ
ai biết đặt một header.

**Nhưng đừng đoán con số.** Đặt sai theo chiều ngược lại thì Django lấy nhầm IP
và **nhốt toàn bộ người dùng vào chung một rọ** — một em bấm nhanh là cả trung
tâm bị chặn.

**Cách đo:**

1. Gọi bất kỳ endpoint nào trên production từ máy anh.
2. Vào Render → `pe-hsa-backend` → **Logs**, tìm dòng của request đó.
3. Đếm số IP trong header `X-Forwarded-For` (chúng ngăn nhau bằng dấu phẩy).

Con số đó chính là `NUM_PROXIES`. Cho tôi biết, tôi đặt vào `settings.py`.

*(Nếu Render không log sẵn header đó, báo tôi — tôi thêm một endpoint chẩn đoán
tạm, chỉ quản trị viên gọi được, đo xong gỡ đi.)*

---

### [ ] A3. Redis cho bộ đếm giới hạn tần suất

**Vấn đề:** `render.yaml` dòng 27 chạy `--workers 2`. Mỗi worker giữ một
`LocMemCache` **riêng**, mà bộ đếm giới hạn tần suất nằm trong đó. Nên **mọi
giới hạn đang bị nhân đôi** — đặt 5 lần/phút thì thực tế là 10.

**Việc của anh:** Render → **New** → **Key Value** (Redis), rồi đưa tôi
`REDIS_URL`. Phần mã tôi làm.

---

## B · Gộp vào `master` và deploy

**Cảnh báo:** `render.yaml` có `autoDeploy: true` và `branch: master` — **gộp là
deploy production ngay lập tức**, không có bước xác nhận nào.

### [ ] B1. Thứ tự đề nghị

1. Làm xong **A1** (khoá bí mật) — đây là thứ duy nhất thực sự chặn.
2. Gộp `erp` → `master`.
3. Mở Render → Logs, xem lượt build.
4. Rồi mới làm A2 và A3.

### Deploy sẽ chạy gì

`buildCommand` gọi `manage.py bootstrap_schema`. Các mục lược đồ §35–§37 tôi đã
áp tay lên Neon rồi, nên lượt đó là vô hại — đã chứng minh bằng cách chạy **cả
tệp hai lượt liên tiếp** trong transaction rồi cuộn lại: 310 câu, 0 hỏng.

### [ ] B2. Để mắt lần deploy đầu

`frontend/src/middleware.ts` khai `runtime = 'nodejs'`. Nó chạy tốt ở máy và
`pnpm build` xanh, nhưng đây là **lần đầu nó lên Vercel**. Nếu phiên đăng nhập
hết hạn sớm bất thường sau khi deploy, đó là chỗ cần nhìn trước tiên.

---

## C · Năm câu hỏi cho TopHSA

Anh chốt 31/08 là **vẫn theo đặc tả `docs/ERP_TOPHSA_2026-08-24.md` §9**, nên
đây là đường găng thật — không phải chuyện code chậm, mà là chưa biết phải code
cái gì.

### [ ] C1. Dạy trên nền tảng nào? Có API lấy danh sách người tham dự không?

→ Quyết định **điểm danh tự động hay tick tay** — hai thiết kế khác hẳn nhau.
Hiện tôi đã dựng đường tick tay và để sẵn cột `attendance.minutes` cho đường tự
động, nên câu trả lời "có API" sẽ không phải đập đi làm lại.

### [ ] C2. Có chấm tự luận không? Thang điểm nào? Ai chấm — giảng viên hay trợ giảng?

→ Quyết định khối §5 (giao bài & chấm tay). Đặc tả đã phác sẵn hai bảng
`assignments` / `submissions`, chấm xong đẻ `learning_events` nên điểm tự luận
vào thẳng bản đồ năng lực, không cần luật riêng.

### [ ] C3. Báo cáo phụ huynh gửi qua kênh nào? Tần suất? Ai duyệt trước khi gửi?

→ Nội dung báo cáo **đã làm xong** (T27, xem `/giang-day/bao-cao/<lớp>/<em>`),
in ra PDF được. Còn thiếu đúng phần **gửi tự động**, mà phần đó phụ thuộc câu
trả lời này (Zalo OA? email? ai bấm nút gửi?).

### [ ] C4. Quy trình thu chi kế toán thật? Có phần mềm kế toán đang dùng không?

→ Khối §7 (học phí, công nợ, thù lao, CRM). Đặc tả ghi rõ đây là khối **lớn
nhất** và *"không tận dụng được gì đã dựng"*. Khuyến nghị trong đặc tả: cân nhắc
nối với phần mềm họ đang dùng thay vì viết lại — sai một chi tiết là sai sổ sách.

### [ ] C5. Phút ngồi lớp có tính vào chỉ tiêu tự học hằng tuần không?

→ Điểm danh đang **cố ý** để `learning_events.minutes = NULL` chờ đúng câu này
(xem chú thích ở `teaching/sessions.py:_emit_events`). Đổ phút vào bây giờ là âm
thầm thổi phồng một chỉ số đang tranh luận, và **gỡ ra thì không gỡ được**. Số
phút vẫn được giữ nguyên trong `meta`, nên chốt xong chỉ là một câu UPDATE.

---

## D · Hai quyết định nhỏ của anh

### [ ] D1. Đợt học đầu tiên

Bảng `terms` đã dựng (§36) nhưng **0 dòng**. Anh muốn:

- Đợt đầu tên gì? (ví dụ "Đợt 1/2027")
- Ngày bắt đầu / kết thúc / ngày thi?
- Có gán lớp `Luyện HSA đợt 1/2027 — Ca tối` vào đợt đó không?

Trả lời xong tôi làm màn hình quản lý đợt và gán lớp.

### [ ] D2. Tài khoản quản trị viên đang nằm trong lớp 1

Anh chốt **giữ** (để xem giao diện). Tôi đã ghi T51: báo cáo lớp nên lọc theo
**vai trò**, để tài khoản quản trị nằm trong lớp bao nhiêu lần cũng không làm
lệch sĩ số / bảng điểm danh / mẫu số tiến độ. Không cần anh làm gì thêm — chỉ để
anh biết con số hiện tại đang cộng cả tài khoản đó.

---

## E · Tuỳ chọn — cho tôi tự push

Suốt phiên 30–31/08, lệnh `git push` bị bộ lọc quyền của chế độ auto chặn (không
phải lỗi git: `git push --dry-run` chạy lọt bình thường). Ba cách:

- **Anh tự chạy** `git push` khi cần — không đổi thiết lập gì.
- **Cấp quyền hẹp:** tạo `D:\pe_hsa\.claude\settings.json`

  ```json
  { "permissions": { "allow": ["Bash(git push -u origin erp:*)"] } }
  ```

  Cố ý **hẹp**. Luật rộng `"Bash(git push:*)"` cho phép luôn `git push origin
  master`, tức là tôi deploy production được mà không hỏi ai.
- **Rời chế độ auto:** gõ `/permissions`, hoặc Shift+Tab — khi đó nó hiện hộp xác
  nhận thay vì chặn thẳng.

---

## Phụ lục — trạng thái hiện tại

| | |
|---|---|
| Nhánh | `erp`, đã push, chưa gộp vào `master` |
| Bộ kiểm backend | **94 đạt / 0 hỏng** (trước 31/08: 18 hỏng / 15 lỗi) |
| `pnpm build` · `tsc` · `eslint` | xanh (2 cảnh báo có sẵn ở `layout.tsx`, `Chatbot.tsx`) |
| CSDL Neon | 51 bảng · 5 tài khoản · 1 lớp · 4 dòng ghi danh · 37 sự kiện |
| ERP §9 | khối 1, 2, 5 xong · khối 3 xong phần báo cáo, còn phần gửi · khối 4, 6, 7 chờ TopHSA |

**Chạy bộ kiểm:** `pytest` không có sẵn trong venv.

```bash
cd D:\pe_hsa\backend
.venv\Scripts\python.exe -m pip install pytest pytest-django
.venv\Scripts\python.exe -m pytest -q        # ~5 phút, chạy trên CSDL thật rồi cuộn lại
```
