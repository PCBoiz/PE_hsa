# PROGRESS — nhật ký vòng lặp pe_hsa

Đọc tệp này để biết đang ở đâu. Backlog: `TODO.md`. Tiêu chuẩn: `RULES.md`.
Ghi lại sau **mỗi** task, không phải sau mỗi chặng.

---

## Công cụ — đọc trước khi làm gì

**Máy chủ** (nếu chưa chạy):
```bash
# Django 9000 — --noreload là bắt buộc
Start-Process D:\pe_hsa\backend\.venv\Scripts\python.exe `
  -ArgumentList "manage.py","runserver","9000","--noreload" `
  -WorkingDirectory D:\pe_hsa\backend -WindowStyle Hidden
# Next 3100
cd frontend && npx --yes pnpm@11.12.0 dev
```

**Phiên trình duyệt ĐÃ ĐĂNG NHẬP, không ghi CSDL** — bắt buộc cho mọi việc kiểm
giao diện (xem `RULES.md` §1):
1. Sinh token: `accounts.views._tokens_for(7)` (id 7 = admin) → ghi ra
   `scratchpad/tokens.json`.
2. Đặt vào cookie `pe_at` / `pe_rt` (tên lấy từ `src/lib/auth.ts`).
   Sẵn có ở `scratchpad/session.mjs` — xuất `openSession({viewport, theme})`.

Vai khác: id 11 = Giảng viên · id 12, 13 = Học viên.

**Playwright** nằm trong bố cục pnpm nên `import 'playwright'` **không phân giải
được**. Phải nạp bằng đường dẫn tuyệt đối:
`node_modules/.pnpm/playwright@1.61.1/node_modules/playwright/index.mjs`.

**Bẫy đã biết:**
- `pnpm` không có trong PATH → `npx --yes pnpm@11.12.0`.
- Git-Bash `/tmp` **không** cùng thư mục mà Python nhìn thấy → dùng scratchpad.
- Viết mã có `\n` trong chuỗi qua heredoc: dấu escape bị một lớp trung gian
  nuốt, biến thành xuống dòng thật và làm hỏng tệp. Đã hỏng hai lần
  (`admin.inline.js`, `AccountsClient.tsx`). Dùng công cụ ghi tệp trực tiếp.
- `elementHandle.screenshot()` phá mô phỏng `pointer: coarse` — đo vùng chạm ở
  lượt chạy không chụp ảnh phần tử.

---

## Trạng thái 30/08/2026

**Nhánh:** `erp`, 19 commit trước `master`. **P0 đã xong toàn bộ.** **Chưa push** (lệnh `git push` bị chặn,
chờ người dùng cho phép). `master` có `autoDeploy: true` nên gộp vào đó là deploy
production ngay.

**CSDL:** DDL §31–33 **đã chạy thật** trên Neon. 47 → 50 bảng. Dữ liệu: 5 tài
khoản, 1 lớp (`hsa_quantitative`, 27 bài), 37 sự kiện, 0 buổi học, 0 điểm danh,
0 dòng nhật ký kiểm toán.

### Đã xong
- Hệ thiết kế frontend: Tailwind v4 không preflight, phông tự phục vụ, 9 component, thang chữ 8 bậc.
- Tương phản: 9/9 nhãn đạt cả hai bộ màu, thấp nhất 4,99 (sáng) và 5,08 (tối). Trước là 3,96.
- Token vào cookie httpOnly sau lớp trung gian Next; vá lỗ `..%2f` từng trả JWT thô.
- Bỏ tự đăng ký ở cả ba đường; chính sách trung tâm cấp tài khoản khép kín.
- Vá lỗi định danh: email phân biệt hoa/thường và số điện thoại hai định dạng — học viên từng bị khoá ngoài không có đường tự thoát.
- `User.is_active` phản ánh `users.status` → khoá tài khoản cắt hiệu lực cả token đã cấp.
- ERP: quản lý tài khoản quy mô lớn + nhập hàng loạt · buổi học & điểm danh (backend) · xuất CSV · nhật ký kiểm toán.
- Vá mẫu số tiến độ: 76 → 27 bài. Em học xong trọn khoá từng hiện 36%.
- Cắt 3,44 MB mã chết khỏi dashboard (mermaid 3,41 MB + svg-pan-zoom 29 kB, cả hai không làm gì).
- CI kiểm cú pháp 15 tệp JS thuần không đi qua bundler.

### Đã kiểm chứng
- Bộ 45 phép kiểm ở tầng API: **45/45 đạt**, CSDL không đổi một dòng.
- **Nhưng bộ đó bỏ lọt T1** — xem `RULES.md` §1. Đây là bài học đắt nhất tới giờ.

### Audit
- Chất lượng mã: **xong**, 18 nhóm phát hiện → đã thành T1–T24.
- Bảo mật, luồng đầu-cuối, CSDL/ERD, khả năng tiếp cận, nhất quán giao diện:
  **chết vì rate limit 429** khi chạy 6 agent song song. → T10–T14. Chạy **3
  agent mỗi lượt**.

---

## Nhật ký

### 30/08/2026 — Dựng khung vòng lặp
Tạo `RULES.md`, `TODO.md`, `PROGRESS.md`. Backlog 35 task, chia P0–P6.

### 30/08/2026 — T1 xong: màn hình buổi học & điểm danh sống lại
Đổi kiểu và mọi chỗ ĐỌC sang camelCase. Ghi rõ thành chú thích một điều dễ nhầm:
backend **nhận** thân request bằng `snake_case` nhưng **trả** phản hồi bằng
`camelCase`. Lối vào nối từ báo cáo lớp trong `dashboard.js` — cố ý KHÔNG dựng
trang danh sách lớp thứ hai, vì khu Giảng dạy cũ đã có sẵn một cái.

Chạy trọn vòng ghi trên trình duyệt thật, tự dọn sau:
```
OK  tạo buổi học qua giao diện
OK  chip "chưa điểm danh" hiện ra          | 3 chưa điểm danh
OK  bảng tick hiện đủ học viên đang trong lớp | 3 em
OK  ô thống kê sĩ số / đã tick / chưa tick
OK  chip "có mặt" cập nhật sau khi lưu     | 3 có mặt
OK  dọn buổi                                | xoá 3 dòng điểm danh + 3 sự kiện
    0 lỗi console · 0 tràn ngang ở 390px
```
CSDL trở lại nguyên trạng. Còn lại 3 dòng trong `admin_audit` ghi đúng ba thao
tác vừa chạy — đó là việc nhật ký kiểm toán sinh ra để làm, giữ lại làm bằng chứng.

**Ba lần "SAI" trong quá trình là phép kiểm của tôi đo quá sớm, không phải lỗi
ứng dụng** — đã sửa phép kiểm để đợi đúng phần tử thay vì đợi theo đồng hồ. Một
lần khác `has-text("Có mặt")` khớp nhầm cả nút "Đánh dấu cả lớp **có mặt**".

**Hai lỗi mới tìm ra khi kiểm T1** (T36, đã vá): `serverFetch` nuốt cú
`redirect()` của Next, và các lời gọi song song đua nhau làm mới cùng một refresh
token trong khi `ROTATE_REFRESH_TOKENS` bật. Cả hai chỉ lộ ra sau 30 phút — tức
gần như không bao giờ thấy lúc phát triển, và luôn thấy với người dùng thật.

### 30/08/2026 — T2 xong: file xuất và màn hình nay cùng một bộ lọc
`exports.py` dùng thẳng `build_user_filters` của màn hình; xoá bản chép lại.
Đo 10 ca, **0 lệch**:

```
khong loc — toan bo                             tong=5   5 dong   OK
so dien thoai dang quoc te (CA DA TUNG LECH)    tong=1   1 dong   OK
so dien thoai dang noi dia                      tong=1   1 dong   OK
ky tu dai dien LIKE — "100%"                    tong=0   0 dong   OK
loc theo vai tro / trang thai / lop / ket hop   ...              OK
ma lop khong phai so                            tong=0   0 dong   OK
```

Ca thứ hai chính là ca agent đã chứng minh lệch: trước đây màn hình 1 kết quả,
tệp CSV 0 kết quả.

### 30/08/2026 — T3 xong: CI xanh lại
3 lỗi eslint → **0 lỗi**. Cả ba đều là lỗi thật chứ không phải nhiễu:
`LoginForm` đọc thanh địa chỉ trong effect rồi `setState` (câu lỗi OAuth chỉ
hiện sau khi JavaScript chạy xong) · `MockExam` gán ref giữa lúc dựng · và
`Date.now()` trong một hàm khai trần. Nay `LoginForm` nhận lỗi qua prop từ
Server Component, `MockExam` gán ref trong effect và bọc `start` bằng
`useCallback`.

Đánh đổi đã nhận: `/login` chuyển từ tĩnh sang dựng theo yêu cầu.

### 30/08/2026 — T4 + T5 xong: HẾT P0
Cả hai nằm trong `accounts/views.py`. Đo 15 phép kiểm, 14 đạt — phép kiểm còn
lại là dương tính giả của chính tôi (tìm chuỗi mà **chú thích** vẫn nhắc lại;
kiểm lại trên mã đã bỏ chú thích: sạch).

Đáng ghi: bảng thu hồi token **tồn tại và đã thu hồi 17 token**, nên
`except Exception: pass` là bẫy cho tương lai chứ chưa hỏng hôm nay. Báo đúng
mức thay vì thổi phồng.

**TOÀN BỘ P0 ĐÃ XONG.** Nhánh `erp` giờ đủ điều kiện cân nhắc gộp vào `master`,
sau khi chạy nốt năm mảng audit ở P2.

### 30/08/2026 — T10 xong: audit bảo mật
**Tin tốt, đã tự tấn công lại và không thủng:** phân quyền theo đối tượng (ma
trận đầy đủ cho giảng-viên-không-phụ-trách / học viên / ẩn danh trên mọi endpoint
`teaching/`) · SQL injection (mọi câu dựng động chỉ ghép định danh trong danh
sách trắng) · lỗ `..%2f` của proxy (thử lại 9 biến thể mã hoá + hướng SSRF) ·
kỷ luật một cửa của `common/identity.py`.

**Đã vá trong đợt này, tất cả đều đo lại:**
| | trước | sau |
|---|---|---|
| Dò tài khoản qua thời gian | chênh **134,8 ms** | **4,7 ms** |
| `/auth/session` thiếu header `Sec-Fetch-Site` | `200` + đặt cookie | `403` |
| `/api/user` | `SELECT *`, 25 cột, có `status_note` | 21 cột trong danh sách trắng |
| `/api/users/<id>/following` | ai đọc của ai cũng được | `403` nếu không phải mình |
| `.gitignore` | hở `.env.prod`, `.env.backup`, `scratchpad/` | chặn hết, giữ `.env.example` |
| Lớp trung gian | chuyển tiếp `X-Forwarded-For` của trình duyệt | loại bỏ |

`status_note` đáng nói riêng: đó là **ghi chú nội bộ của quản trị viên về học
viên** (ví dụ lý do khoá tài khoản), và chính em đó đọc được ghi chú viết về
mình. Nguy hơn về lâu dài là mọi cột thêm vào bảng `users` sau này sẽ tự rò ra
API mà không ai phải làm gì.

**Ba việc cần anh** — T38 (đo `NUM_PROXIES` trên production), T39 (xoay
`SECRET_KEY`), T40 (cache dùng chung cho throttle).

### 30/08/2026 — T12 xong: audit CSDL + đối chiếu ERD
**Vá nặng nhất:** `common/db.py` coi *pool đang bận* là *kết nối đã chết*.
`PoolTimeout` kế thừa `psycopg.OperationalError`, Django bọc lại thành
`django.db.OperationalError` → rơi thẳng vào nhánh **huỷ cả pool dùng chung**.
Mà `pool.close()` đá ngay mọi luồng đang chờ ra với `PoolClosed` — cũng
`OperationalError` — nên chúng cũng đi huỷ pool. Vòng xoáy tự khuếch đại: với
`gunicorn timeout=30`, một yêu cầu vượt ngưỡng ngay ở lần thử **thứ hai** →
worker bị giết → kéo theo 8 yêu cầu đang chạy dở.

**Bản vá đầu của tôi SAI và phép đo bác bỏ nó.** Tôi viết `except PoolTimeout`
và `_reset_pool` vẫn bị gọi đủ 6 lần — vì `DatabaseErrorWrapper` **ném ra một
ngoại lệ MỚI**, bản gốc chỉ còn ở `__cause__`. Sửa lại thành soi `__cause__`:
```
OK  pool BAN (khong phai conn chet)    _reset_pool goi 0 lan (mong 0)
OK  connection CHET that (Neon ngu)    _reset_pool goi 6 lan (mong 6)
```

**Chỉ mục:** thêm 9 cái, mỗi cái đã EXPLAIN ra `Seq Scan`. Và ở đây tôi cũng tự
sai một lần: đặt chỉ mục trigram trên `name` trong khi câu tra dùng
`lower(name)` — ép `enable_seqscan=off` vẫn ra Seq Scan. Đặt lại trên
`lower(...)` thì mới dùng được.

**Bốn lỗi múi giờ**, nặng nhất là bảng xếp hạng tuần: `log_date` ghi bằng giờ VN
nhưng mốc đầu tuần so bằng `CURRENT_DATE` (UTC) — **mỗi thứ Hai từ 0h đến 7h
sáng, BXH hiện dữ liệu tuần trước suốt bảy tiếng.**

**Kỷ luật một cửa:** kéo câu `DELETE learning_events` cuối cùng ở `journal.py` về
`common/events.py`, và gom luật đặt `dedup_key` về một hàm duy nhất. `dedup_key`
của quiz khoá theo **tên chương mục** — một nhãn thay đổi được, mà schema §26 ghi
rõ giáo trình *sẽ* được soạn lại; chạy lại lệnh nạp sau khi đổi tên sẽ **đếm đôi
mọi quiz, im lặng**. Vá bằng xoá-rồi-ghi.

**Agent BÁC BỎ hai nghi ngờ cũ của tôi:** `check_and_award_achievements` là **5
câu** chứ không phải ~23 (trần tuyệt đối 14), và `plan.generate` là 85–139 INSERT
chứ không phải 245. Không thổi phồng theo.

**Dữ liệu rác đã có thật:** `surveys` id=4 trỏ tới `user_id=10` không tồn tại.

### 30/08/2026 — T11 xong: audit luồng đầu-cuối, và lỗi nặng nhất cả đợt
**F-1 — phiên 8 tiếng thực chất chỉ sống 30 phút.** Hai tầng chồng nhau:
`pe_at` có `Max-Age` đúng bằng tuổi thọ token nên phút thứ 30 trình duyệt tự xoá
nó, và `serverFetch` đá người dùng đi **trước khi nhìn tới `pe_rt`** vẫn còn sống
bảy tiếng rưỡi. Nguy hơn: khi nó CÓ làm mới được thì rotation thu hồi token cũ
ngay, mà **Server Component không ghi cookie được** — nên việc làm mới ở tầng
dựng trang không chỉ vô ích, nó **chủ động giết phiên**.

Kịch bản thật: giảng viên đăng nhập trước giờ dạy, dạy 40 phút, mở sổ điểm danh →
phải gõ lại mật khẩu trước mặt cả lớp.

Vá bằng `src/middleware.ts` — chỗ duy nhất trong App Router vừa chạy trước khi
dựng trang vừa ghi được cookie. Đo lại:
```
OK  ca hai cookie                       -> /quan-tri/tai-khoan
OK  CHI con pe_rt (sau 30 phut)         -> /quan-tri/tai-khoan   (truoc: /login)
OK  refresh token da XOAY va ghi lai duoc vao trinh duyet
OK  vao lai bang refresh token vua xoay -> /quan-tri/tai-khoan
OK  khong cookie nao                    -> /login
```

**Phần TỐT, đã kiểm, không cần soi lại:** quyền theo vai kín tuyệt đối · chấm
điểm từng dòng khi nhập hàng loạt · đổi bộ lọc lúc ở trang 3 không ra danh sách
rỗng · CSV khớp màn hình · **tràn ngang 0 trên toàn bộ 10 tổ hợp** · vùng chạm
44px · bấm Lưu hai lần không lọt.

### 30/08/2026 — T48 xong: ba con số sĩ số giờ khớp nhau
Khu Giảng dạy từng hiện đồng thời "3/25 học viên", "4 học viên" và
"HỌC VIÊN (4)". Gốc: `summary.students` đếm cả em đã rời lớp trong khi mọi chỉ
số bên cạnh tính trên `active`. Nay `students` = sĩ số đang học, thêm
`enrolledEver` và `left` để tách hai khái niệm.
Nặng hơn con số: ô **"Cần chú ý"** giục giảng viên gọi cho một em đã rời lớp năm
ngày trước, mà ở khu đó không có nhãn "(đã rời lớp)". Vá ở cả hai tầng.
Phát hiện kèm: frontend lọc `alerts.length` (mọi mức), backend `atRisk` chỉ đếm
mức cao — hai luật cho cùng một danh sách.
Đo trên trình duyệt thật sau khi khởi động lại Django: 3 · 3/25 · "3 đang học +
1 đã rời lớp", bảng vẫn 4 dòng, "Cần chú ý" sạch.

### 30/08/2026 — T49 (một phần): câu lỗi nói tiếng người
Backend trả lỗi theo BA hình dạng và mỗi màn hình tự đoán một kiểu, nên cùng một
sự cố ra hai kết quả tệ khác nhau: `[object Object]` khi `error` là đối tượng,
và "Máy chủ trả lỗi 500" — mã HTTP trần trên màn hình trợ giảng.
Gom về `errorText()` trong `lib/api.ts`: đọc được cả ba hình dạng, có bảng câu
tiếng Việt theo mã HTTP làm mức cuối. Nhờ vậy những câu lỗi công phu nhất trong
repo (ví dụ đoạn giải thích trần 50 tài khoản mỗi mẻ) mới thật sự tới được người
đọc — trước đây chúng chỉ tới nơi khi trúng đúng một trong ba hình dạng.
Đo ba ca đã hỏng, cả ba ra câu tiếng Việt đọc hiểu ngay; `[object Object]` biến mất.

**Tiếp theo:** T45–T50 (giao diện điện thoại, xác nhận lưu, ngôn ngữ máy lọt ra
màn hình) và T41–T44 (gộp INSERT, bất biến CSDL, `terms`, `attendance_taken_at`).
Còn T13 (khả năng tiếp cận) + T14 (nhất quán giao diện) chưa chạy.

### 31/08/2026 — T41 xong: ba vòng lặp INSERT gộp thành một câu

Đo trước khi sửa, không suy: mỗi `record_event` tốn **ba** lượt gọi Neon
(SAVEPOINT / INSERT / RELEASE) vì tự mở savepoint riêng.

```
                              trước   sau
diem danh 3 hoc vien             9      3      (va nay KHONG doi theo si so)
plan.generate user 9           147     12
plan.generate user 13           95     11
```

Điểm danh nay là **hằng số** chứ không tuyến tính theo sĩ số — lớp 30 em trước
đây là 90 lượt cho một lần bấm Lưu, trong khi giảng viên đứng chờ trước cả lớp.

**Tìm thêm vòng lặp THỨ BA** mà T41 không kể tên: `backfill_learning_events`
gọi `record_event` trong vòng lặp trên **toàn bộ** lịch sử học của mọi học viên,
tức số lượt tăng theo cỡ dữ liệu (5.000 sự kiện = 15.000 chặng khứ hồi). Điểm
nghẽn nằm gọn ở `_emit` nên vá bằng đệm + `_flush` sau mỗi nguồn. Nhân tiện bỏ
một tham số bị truyền lặp ở cả 5 chỗ gọi (`kind` xuất hiện hai lần, hai bản có
thể lệch nhau mà không ai biết).

**Giữ kỷ luật một cửa:** câu INSERT chỉ còn MỘT bản (`_COLS` / `_ROW` /
`_ON_CONFLICT`), dùng chung cho cả ghi lẻ lẫn ghi mẻ. Nếu để hai bản chép, chỉ
cần bản mẻ thiếu một `COALESCE` là ghi lẻ giữ được điểm cũ còn ghi mẻ xoá mất —
hai đường ghi cùng một bảng cho hai kết quả khác nhau, và không phép kiểm nào
bắt được vì cả hai đều "chạy được".

**Đánh đổi đã nhận và đã vá:** một câu INSERT thì một dòng hỏng kéo đổ cả mẻ,
trong khi vòng lặp cũ chỉ mất đúng dòng đó. Nên `record_events` khi mẻ hỏng sẽ
QUAY VỀ ghi lẻ từng dòng. Phép kiểm 4 đã kích hoạt đúng nhánh này (trộn một
`user_id` không tồn tại vào mẻ): log báo mẻ hỏng, rồi 3 dòng hợp lệ vẫn vào đủ.

**Kiểm 18 phép, 18 đạt**, mọi thứ chạy trong transaction rồi cuộn lại nên CSDL
không đổi một dòng:
```
ghi me vs ghi le — 15 cot x 3 dong giong het            OK
diem danh LAI -> CAP NHAT, khong de them dong           OK
trung user_id trong cung mot me (double-click)          OK   gop, giu dong CUOI
mot dong hong KHONG keo do nhung dong con lai           OK   3/3 dong hop le vao
plan.generate gop me vs tung cau — 136/13/85 muc        OK   giong het
qua CHINH VIEW: HTTP 200, 3 dong, id la duoc bao lai    OK   7/7
```

Bẫy đã tránh: trần 65.535 tham số mỗi câu lệnh của Postgres. Kế hoạch học có
trần lý thuyết 40 tuần × (100 bài + 25 buổi ôn + 20 đề) = 5.800 mục = 52.200
tham số — dưới ngưỡng nhưng sát, nên chia mẻ 500 dòng ở cả hai chỗ.

Một lỗi tự bắt được giữa chừng: nhánh dự phòng ban đầu cắt lát danh sách **gốc**
trong khi mẻ đã gộp trùng, nên khi mẻ hỏng nó sẽ ghi lại nhầm dòng. Sửa bằng
cách giữ cả tham số lẫn dict gốc theo cùng thứ tự.

---

## MỞ PHIÊN MỚI THÌ BẮT ĐẦU TỪ ĐÂY

Cập nhật 31/08 sau khi xong T41. Mọi việc đã commit, không mất gì.

**Việc còn dở:** không có. Task cuối (T41) đã commit xong.

**Ba việc CẦN NGƯỜI DÙNG, không tự làm được:**
1. `git push -u origin erp` — bị bộ lọc quyền của chế độ auto chặn (không
   phải lỗi git: `git push --dry-run` chạy lọt và GitHub trả lời bình thường).
   19 mốc nằm ở máy. Ba cách cho qua: anh tự chạy lệnh · thêm
   `.claude/settings.json` với `"allow": ["Bash(git push -u origin erp:*)"]`
   (cố ý HẸP — luật `Bash(git push:*)` cho phép luôn push vào `master`, tức
   deploy production) · hoặc rời auto mode để nó hỏi thay vì chặn.
2. T39 — xoay `SECRET_KEY` (19 byte, RFC 7518 đòi ≥32). Sinh bằng
   `python -c "import secrets;print(secrets.token_urlsafe(48))"`, dán vào
   `backend/.env` và Render → Environment. Mọi người đang đăng nhập sẽ bị đăng
   xuất; mật khẩu KHÔNG ảnh hưởng.
3. T38 — đo `NUM_PROXIES` thật trên production trước khi đặt.

**Thứ tự đề nghị cho phiên sau** (giá trị ÷ công sức, theo audit T12):
T46 (xác nhận lưu điểm danh — `Toast` đã dựng sẵn, chưa gắn) →
T45 (bảng giấu 62% cột trên điện thoại) →
T47 (`serverJson` vứt câu lỗi backend) →
T13 + T14 (hai mảng audit chưa chạy, chạy **3 agent một lượt**).

**Nhớ:** Django chạy `--noreload` nên sửa mã Python xong PHẢI khởi động lại mới
thấy tác dụng — đã mất một lượt đo vì quên. Và token kiểm thử chỉ sống 30 phút.
