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

**Nhánh:** `erp`, 20 commit trước `master`. **P0 đã xong toàn bộ.** **Chưa push** (lệnh `git push` bị chặn,
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

### 31/08/2026 — T46 xong: bấm Lưu xong thì thấy được là đã lưu

`ToastProvider` dựng từ T19 nhưng **chưa nơi nào gắn** — mã chết. Nay gắn ở màn
hình buổi học.

Đo trên trình duyệt thật, 390×844, khung nhìn cao 844px:
```
                              truoc      sau
nut "Luu diem danh"          top=764    top=687
chu "Chua luu"               top=868    top=700   (lech 104px -> 13px)
loi xac nhan sau khi luu      khong co   top=766 bottom=828  (trong khung)
```

Trước đây tín hiệu DUY NHẤT báo lưu xong là chữ "Chưa lưu" biến mất — mà nó nằm
ngoài khung nhìn 104px, tức đúng tư thế giảng viên bấm Lưu thì không nhìn thấy
kết quả, trong khi lần lưu mất 3,5 giây. Hai vế đều đã vá: lời xác nhận neo
`fixed bottom-4` nên luôn hiện, và "Chưa lưu" gộp chung một khối với nút Lưu nên
hai thứ luôn xuống dòng cùng nhau (trước là ba anh em của cùng một `flex-wrap`
nên ở 390px mỗi cái rơi một dòng).

Lời xác nhận **nhắc lại con số** ("Đã lưu điểm danh — 3 có mặt.") chứ không chỉ
"Đã lưu": giảng viên vừa tick hai chục ô, thứ họ cần yên tâm là máy đếm đúng
bằng số mình tick. Nhãn lấy từ chính mảng `MARKS` đang vẽ bốn nút bấm, nên câu
thông báo không thể gọi tên trạng thái khác với nút vừa bấm.

**Vá kèm:** màn hình nay đọc `skipped` — danh sách id backend CỐ Ý báo lại (chú
thích trong `sessions.py`: "để người gửi biết chứ không tưởng là đã lưu") mà
frontend đang vứt đi. Trường hợp thật: học viên rời lớp ở tab khác trong lúc
giảng viên đang tick, trước đây sẽ báo thành công cho một lần lưu thiếu người.

Kiểm 7 phép qua giao diện thật, 7 đạt (gồm 0 lỗi console, 0 tràn ngang ở 390px).
Buổi học tạo ra để kiểm đã xoá bằng chính endpoint xoá: CSDL về đúng 5 tài
khoản / 37 sự kiện / 0 buổi / 0 điểm danh.

**Nhìn thấy trong ảnh chụp, chưa vá:** danh sách điểm danh có một dòng tên
"Quản trị viên" — bằng chứng thị giác cho T42 (`class_members` chứa `user_id=7`
role admin). Quản trị viên đang được điểm danh như học viên.

**Còn một điểm nhỏ chưa xử:** lời xác nhận neo đáy màn hình che mất nút "Đánh
dấu cả lớp có mặt" trong 4 giây. Chấp nhận được vì vừa lưu xong thì khó cần tới
nút đó ngay, và có nút đóng — nhưng nếu sau này thêm hành động ở đáy thì phải
xem lại.

### 31/08/2026 — T42+T43+T44 xong: bất biến, đợt học, và con dấu điểm danh

**Đo trước khi đề xuất bất cứ câu DDL nào.** Câu hỏi phải trả lời trước là "dữ
liệu đang có CÓ vi phạm ràng buộc sắp thêm không" — thêm bừa là gãy deploy, vì
`bootstrap_schema` ném lỗi ở câu đầu tiên hỏng và nó chạy trong `buildCommand`
của Render.

```
users.role      'Học viên' 3 | 'admin' 1 | 'Giảng viên' 1   -> khop ASSIGNABLE_ROLES
users.status    'active' 5                                   -> khong vi pham
classes.status  'active' 1                                   -> khong vi pham
dong mo coi     enrollments 0 | lesson_progress 0 | course_ratings 0
                roadmap_progress 0 | surveys 1  <- DUY NHAT
```

Đáng chú ý: `users.role` đang chứa **hai thứ tiếng lẫn nhau** — `'admin'` cạnh
`'Giảng viên'`/`'Học viên'`. Đó chính là lý do nhật ký kiểm toán hiện chuỗi trần
`admin` cho người đọc (phần còn lại của T49). CHECK viết đúng ba giá trị đang có
chứ không "dọn" chúng: đổi giá trị vai trò là đổi dữ liệu quyền trên tài khoản
thật, việc đó cần một lượt riêng có kế hoạch quay lui.

**Chạy thử toàn bộ tệp HAI LƯỢT trong transaction rồi cuộn lại: 310 câu, 0 hỏng**
— chứng minh DDL chạy lại được trước khi đụng vào Neon.

**§35 — bất biến:** 4 CHECK + 9 khoá ngoại cho 5 bảng trước đây không có cái
nào, kèm chỉ mục cho cột con (khoá ngoại CASCADE không có chỉ mục thì mỗi lần
xoá một tài khoản là một lần quét toàn bảng). Dòng mồ côi `surveys` id=4 đã in
nội dung ra rồi xoá theo quyết định của anh; khoá ngoại đã VALIDATE.

**§36 — học lại lớp cũ.** Khoá chính `(class_id, user_id)` cho đúng MỘT dòng mỗi
cặp, nên đường thêm vào lớp chạy `ON CONFLICT DO UPDATE SET left_at = NULL` —
tức xoá trắng mốc rời lớp lần trước. Đi thẳng ngược §29, chỗ đã chốt giữ dữ liệu
của người rời lớp. Nay khoá chính là `id`, hàng rào chống trùng thành chỉ mục
duy nhất MỘT PHẦN `WHERE left_at IS NULL` — dựng TRƯỚC khi bỏ khoá cũ nên không
có khoảnh khắc nào bảng mất hàng rào.

Thay đổi đó **đẻ ra một lỗi mới mà tôi phải tự tìm**: câu `UPDATE class_members
SET left_at=... WHERE class_id=%s AND user_id=%s` không lọc dòng đang học. Với
một dòng mỗi cặp thì đúng; với nhiều lượt học thì nó dập mốc rời lớp lên CẢ
những lượt đã đóng từ đợt trước — ghi đè lịch sử bằng ngày hôm nay. Vá bằng
`AND left_at IS NULL`, và nhân tiện: câu cũ không khớp dòng nào vẫn trả
`{'ok': True}`, tức báo "đã cho rời lớp" cho một em không hề ở trong lớp.

**§37 — con dấu điểm danh.** Trước đây "buổi X, 0 vắng" mơ hồ giữa *cả lớp đi
đủ* và *giảng viên quên tick*. Nay màn hình nói "Chưa mở sổ điểm danh" hoặc
"3 có mặt · đã điểm danh 31/08 · 02:56". Nhật ký giữ `changed` — từ trạng thái
nào sang trạng thái nào — để khiếu nại "hôm đó cháu có đi học" còn đối chiếu
được, thứ openSIS giữ bằng cặp `attendance_code`/`attendance_teacher_code`.

**Kiểm 17 + 7 phép, tất cả đạt.** 17 phép hành vi chạy trong transaction rồi
cuộn lại; 7 phép qua trình duyệt thật ở 390×844, buổi tạo ra đã xoá bằng chính
endpoint xoá. CSDL về đúng 5 tài khoản / 1 lớp / 4 thành viên / 37 sự kiện.

Hai lỗi trong phép kiểm của chính tôi, không phải của mã: `LIKE '...%'` bị
psycopg hiểu `%` là chỗ điền tham số, và `admin_audit.target_id` là TEXT chứ
không phải số.

### 31/08/2026 — Bộ kiểm: 33 hỏng → 0. CI backend xanh lần đầu.

Bắt đầu từ một việc nhỏ: khoá ngoại `enrollments_course_fk` vừa thêm ở §35 làm
12 phép kiểm đổi từ "failed" sang "error". Tổng số hỏng không đổi (33) và số đạt
không đổi (60) — tức không phép nào từ đạt thành hỏng — nhưng phải truy cho ra.

**Ràng buộc không sai; nó PHƠI RA dữ liệu kiểm thử cũ.** `TEST_COURSE_ID =
'python'` và `COURSE_ID = 'db_design'` là di sản ProgrammingEdu, trong khi CSDL
HSA chỉ có ba khoá `hsa_*`. Luồng thật an toàn tuyệt đối: `EnrollView` tra khoá
học và trả 404 nếu không có, nên không đường nào ghi được `course_id` bịa.

Kéo sợi chỉ đó ra thì lòi cả cuộn:

```
truoc  18 hong / 59 dat / 15 loi   (tren master, do 31/08)
sau     0 hong / 94 dat /  0 loi
```

**Ba lớp mục ruỗng, không cái nào do đợt này gây ra:**

1. **Dữ liệu mẫu ghim chết trong phép kiểm.** Bốn phép đòi đúng
   `['frontend','backend','python','cpp']`, đòi có khoá `'python'`, đòi mã
   `'xp_1000'` (đã thay bằng `xp_500`/`xp_2000`). Viết lại thành kiểm HÌNH DẠNG
   — có ít nhất một lộ trình, mỗi khoá có `id` và `title` — vì giáo trình SẼ
   được soạn lại (schema §26), và phép kiểm ghim tên dữ liệu thì hỏng mỗi lần
   nội dung đổi mà chẳng ai làm sai gì.

2. **Sáu phép kiểm chuỗi ngày CHƯA TỪNG CHẠY** kể từ khi nhiệm vụ chuyển từ
   "nhiệm vụ SQL pe_test" sang chấm bằng số liệu HSA. Chúng vá vào
   `stats.views._verify_mission_by_course`, một cái tên nay chỉ còn trong MỘT
   DÒNG CHÚ THÍCH ("Bản cũ (...) chấm nhiệm vụ bằng..."). `monkeypatch.setattr`
   trên tên không tồn tại ném lỗi ngay khâu dựng — và nó báo "error" chứ không
   "fail", thứ dễ lướt qua hơn nhiều khi nhìn bảng kết quả.

   Viết lại đi qua đường THẬT: hoàn thành một bài học, tức
   `common/streak.py:touch_streak`, chỗ duy nhất viết cột `streak`. Phát hiện
   kèm khi đọc: nhận thưởng nhiệm vụ KHÔNG chạm chuỗi ngày, và điều đó đúng —
   nhiệm vụ chỉ đủ điều kiện sau khi đã học thật.

3. **Một phép kiểm khẳng định luật cũ.** `test_streak_resets_at_exactly_two_days_gap`
   đòi chuỗi về 1 khi nghỉ đúng một ngày — luật TRƯỚC khi có vé bảo hiểm chuỗi.
   Tách làm hai để cả hai nhánh đều có người canh: còn vé thì chuỗi tăng và tiêu
   đúng một vé; hết vé thì về 1.

**Và một LỖI SẢN PHẨM THẬT do bộ kiểm chỉ ra**, không phải lỗi của phép kiểm:
`AdminLessonsView.post` bơm số bài bằng `sort_order` gửi lên, mà thiếu trường đó
thì nó mặc định 0 và `_bump_lesson_count` bỏ qua giá trị 0. Hậu quả: thêm bài
vào một khoá xong, danh sách khoá học vẫn hiện "0 bài". Vá bằng cách lấy sàn từ
`COUNT(*)` thật trong bảng `lessons` — vẫn giữ đúng luật "chỉ đi lên" của hàm đó.

Đây là lần đầu bộ kiểm được chạy trong cả đợt ERP này (pytest không có sẵn trong
venv nên chưa ai chạy). Bài học ghi vào RULES: **"CI xanh" không có nghĩa gì nếu
chưa ai xác nhận bộ kiểm CÓ CHẠY** — và ở đây nó đã đỏ sẵn từ trước.

### 31/08/2026 — T27 xong: báo cáo gửi phụ huynh (khối ERP §6)

Tính năng mới, không phải vá lỗi. Đặc tả §9 xếp đây là khối kế tiếp và ghi "ít
phụ thuộc TopHSA, làm được ngay" — đúng vậy: toàn bộ đọc từ `learning_events` +
`classes`, không cần bảng mới.

**Khác hẳn hồ sơ học viên đã có** (`TeachStudentView`), dù cùng nói về một em.
Cái kia là bàn làm việc của giảng viên. Cái này là tờ giấy gửi về nhà, người đọc
là phụ huynh — thường không biết "chỉ số thành thạo" là gì, chỉ cần ba câu trả
lời, và trang được dựng đúng theo ba câu đó: **con có đi học không · con có tiến
bộ không · con cần giúp chỗ nào**.

**Ba ranh giới cố ý:**

1. **Không lộ nhật ký em tự ghi.** Đặc tả mục "Quyền riêng tư" chốt: tiến độ và
   điểm thì hợp lý, nhật ký thì phải hỏi ý học viên. Chưa hỏi thì chưa gửi.
2. **Chuyên cần chỉ tính trên buổi ĐÃ điểm danh.** Đây là chỗ T44 vừa làm hôm
   nay trả công ngay: buổi giảng viên quên tick mà đem chia vào mẫu số sẽ thành
   "con vắng" trong mắt phụ huynh — một lời buộc tội sai, gửi tới tận nhà, không
   ai ở đó để đính chính. Số buổi chưa tick báo riêng ở `sessionsUnmarked`.
3. **Không có dữ liệu thì nói không có, không viết 0.** "Điểm trung bình 0" đọc
   như con làm sai hết, trong khi sự thật là con chưa thi lần nào.

**Một lỗi tự tìm ra khi đo.** Xu hướng điểm sắp theo `event_date` — mà thi hai
đề trong cùng một ngày là chuyện thường (dữ liệu thật: em id 13 có hai lượt cùng
ngày 25/08). Cùng ngày thì thứ tự là bất kỳ thứ gì Postgres trả về, nên xu hướng
LẬT NGƯỢC ngẫu nhiên. Sửa thành `ORDER BY event_date, occurred_at`. Câu "con
đang đi xuống" gửi về nhà cho một em đang tiến bộ là kiểu sai không đính chính
được.

**Một lần tôi nghi oan cho mã của mình.** Phép kiểm báo `mockTrend` sai; hoá ra
dữ liệu thật là 5/9 rồi 2/9, tức em đó đi xuống thật và mã đúng. Tôi đoán thứ tự
từ một bản kết xuất trước — mà bản đó cũng sắp theo `event_date` nên chính nó
cũng tuỳ tiện. Bản vá vẫn giữ: trước đây câu trả lời đúng là do may.

**Lời cũng là một phần tính năng.** Em mới thi đúng một lượt và được 0 điểm thì
tờ giấy hiện "Điểm trung bình 0%" in đậm — đúng số học, nhưng đọc như kết luận
về năng lực. Thêm một câu: "Con mới làm một đề nên chưa đủ để nói đang lên hay
xuống." Và mục "Con đang làm tốt" đứng cạnh mục "Nên tập trung", có chủ đích —
một tờ giấy chỉ toàn phần kém đọc như bản kiểm điểm, và phụ huynh đọc xong
thường quay sang trách con thay vì giúp con.

**In bằng `window.print()`, KHÔNG sinh PDF ở máy chủ.** Hộp in của trình duyệt
đã có "Lưu thành PDF", giữ đúng phông tiếng Việt đang hiển thị, và cho giảng
viên xem trước khi gửi. Thêm bộ sinh PDF phía máy chủ là thêm một phông phải cài
trên Render, một khác biệt nữa giữa dev và production, một chỗ nữa để hỏng.

**Lối vào nằm ở BẢNG HỌC VIÊN** trong khu Giảng dạy, cạnh nút "Xem" — bài học từ
T1: màn hình không có lối vào từ đâu cả thì coi như không tồn tại.

Kiểm 23 phép ở tầng view + 12 phép trên trình duyệt thật (390px và 1280px, có
kiểm bản in ẩn thanh điều hướng). CSDL không đổi một dòng.

### 31/08/2026 — T45 xong: bảng thành thẻ trên điện thoại

```
                        truoc                sau
Tai khoan @390px   bang 796px / khung 306px   306 / 306, giau 0px
                   -> giau 490px = 62%
nut "Dat lai mat khau"  ngoai khung           x=133..270, cao 44px
Nhat ky @390px     giau 45%, mat cot Noi dung 0px, doc duoc
@1280px            bang                       van la bang (table-cell)
```

Cách vá: dưới 640px mỗi dòng thành một THẺ — nhãn cột bên trái, giá trị bên
phải; trên 640px giữ nguyên bảng vì màn hình công cụ cần mật độ cao để quét mắt.
`overflow-x-auto` vẫn giữ (trang không được trượt ngang), nhưng nó chỉ dời vấn
đề vào trong khung: không có gợi ý thị giác nào báo còn nội dung bên phải.

**Hàng rào quan trọng hơn bản vá:** `Td` khai `label` là **bắt buộc** trong kiểu.
Nhờ vậy `tsc` liệt kê ngay 25 ô còn thiếu, và từ nay thêm cột mới mà quên nhãn
là gãy build — thay vì phải trông chờ ai đó mở đúng trang đó trên điện thoại.

**Một lần phép kiểm của tôi vu oan cho mã.** Nó báo nút chỉ cao 36px, dưới chuẩn
44px. Nhưng `Button` đã đúng sẵn: `min-h-11`, chỉ co xuống `min-h-9` khi
`@media(pointer:fine)`. Playwright không bật `hasTouch` nên Chromium báo
`pointer: fine` → 36px. Đúng cái bẫy PROGRESS đã ghi từ trước mà tôi vẫn vấp.
Đã thêm `hasTouch` vào `scratchpad/session.mjs` kèm chú thích, để lần sau không
ai mất lượt đo vì chuyện này.

**Vá kèm — nốt phần còn lại của T49 (ngôn ngữ máy lọt ra màn hình, RULES §10).**
Ảnh chụp lộ ra ngay: ô vai trò hiện chữ `admin` trần. Gốc là `users.role` chứa
LẪN hai thứ tiếng — `'admin'` cạnh `'Giảng viên'`/`'Học viên'`. Chỉ sửa chỗ HIỂN
THỊ, cố ý không đổi giá trị trong CSDL: `'admin'` là thứ `ROLE_ADMIN` và
`users_role_check` (§35) đang dựa vào.

Và tôi bỏ sót đúng chỗ dễ sót nhất ở lượt đầu: sửa ô chọn TRONG DÒNG mà quên ô
LỌC bên trên. Chip đọc được tiếng Việt trong khi ô lọc vẫn liệt kê
`attendance.mark` thì người dùng không nối được hai thứ với nhau — mà ô lọc mới
là chỗ họ chạm vào trước. Phép kiểm bắt được vì nó quét toàn bộ chữ trên trang,
không chỉ chỗ tôi vừa sửa.

**Phát hiện mới, chưa vá:** màn `/admin` cũ vẫn giấu cột — đo ở 390px, ba bảng
giấu 83px / 165px / 234px. Chúng là `<table>` HTML thuần nên không hưởng bố cục
thẻ. Đã ghi vào T35 (chuyển màn hình cũ sang React) kèm số đo.

Kiểm 12 + 6 phép trên trình duyệt thật, tất cả đạt.

### 31/08/2026 — T51 xong: lớp đếm theo VAI, không theo tư cách thành viên

`class_members` trả lời "ai đang ở trong lớp", không trả lời "ai là học viên của
lớp". Hai câu đó khác nhau, và sự khác biệt lọt thẳng vào mọi con số: tài khoản
quản trị viên (id 7) đang là thành viên lớp 1 nên nó vào sĩ số, vào bảng điểm
danh, vào mẫu số tiến độ. Anh chốt GIỮ tài khoản đó trong lớp (để xem giao
diện), nên hàng rào phải nằm ở chỗ ĐẾM chứ không trông chờ không ai thêm nhầm.

```
                         truoc   sau
si so (summary.students)   3       2
the lop                    3/25    2/25
tieu de bang               3 dang hoc + 1 da roi   2 dang hoc + 1 da roi
bang tick diem danh        co Quan tri vien        chi 2 hoc vien
tick cho tai khoan admin   ghi duoc                bi tu choi, bao lai id
```

**Luật đặt ở MỘT chỗ** — `teaching/vocab.py:chi_hoc_vien(alias)` — rồi áp cho
năm câu tra ở `reports.py` và `sessions.py`. Vá ở tầng truy vấn chứ không lọc
trong Python là có chủ ý: ba trong năm chỗ là subselect `COUNT(*)`, lọc sau khi
đã đếm thì không lọc được nữa.

Một chi tiết dễ bỏ: danh sách HIỆN RA để tick và danh sách CHẤP NHẬN được khi
lưu phải là MỘT. Lệch nhau thì có người hiện trên màn hình mà gửi lên lại bị báo
"không thuộc lớp này", hoặc ngược lại — tick được cho người không hề hiện ra.

**Loại bỏ nhưng KHÔNG im lặng.** `summary.nonStudents` và một câu trên màn hình:
"1 tài khoản khác đang ở trong lớp nhưng không mang vai Học viên (quản trị viên,
giảng viên phụ…) nên không tính vào các con số trên." Sĩ số tự tụt một người mà
không giải thích là cách chắc chắn để người đọc mất niềm tin vào con số — cùng
nguyên tắc với `sessionsUnmarked` ở báo cáo phụ huynh.

**Hai lần phép kiểm của tôi đo hụt, cả hai cùng một nguyên nhân:**
`document.body.innerText` KHÔNG trả về nội dung chưa được dựng hình (phần dưới
màn, trong nút chưa cuộn tới). Cả hai lần đều báo "không tìm thấy" cho thứ đang
hiển thị đúng. Phải truy thẳng phần tử (`.tc-sec-t`, `.tc-muted`, `.tc-class`).

Và lần thứ ba tôi vấp bẫy heredoc nuốt `
` — PROGRESS đã ghi từ trước là phải
dùng công cụ ghi tệp trực tiếp. Từ giờ mọi tệp có `
` trong chuỗi đều ghi bằng
công cụ, không qua heredoc.

Kiểm 8 phép ở tầng view + 6 phép trên trình duyệt thật. CSDL không đổi một dòng.

### 31/08/2026 — T47 xong: câu lỗi của backend đi được tới màn hình

`serverJson` cũ là `if (!res || !res.ok) return null` — mọi thứ hỏng rơi vào
cùng một giá trị: 400 kèm hướng dẫn sửa, 403 thiếu quyền, 500 sập CSDL, backend
đang ngủ. Bốn chuyện khác hẳn nhau, màn hình nhận đúng một `null`.

Đo lại ca đã hỏng, `/quan-tri/nhat-ky?from=abc`:
```
truoc:  "Khong doc duoc nhat ky"  +  "Chua co hanh dong nao duoc ghi"
        hai cau mau thuan cung luc, khong cau nao noi ngay sai o dau;
        o chon Hanh dong rong theo nen KHONG CON NUT NAO de thoat.
sau:    "Khong doc duoc nhat ky"
        'Ngay "from" khong hop le (dinh dang YYYY-MM-DD).'
        [Xoa bo loc va xem lai tu dau]  -> bam mot cai la ve 25 hanh dong
```

Kiểu trả về nay là **union có thẻ** `Ket<T>`, nên `tsc` liệt kê ngay toàn bộ 7
nơi gọi và bắt buộc từng nơi xử lý nhánh hỏng. Cùng thủ pháp đã dùng cho `label`
của `Td` ở T45: đưa luật vào KIỂU thì không ai quên được, thay vì trông chờ
người sau nhớ.

Câu lỗi dựng bằng chính `errorText` mà phía trình duyệt dùng — một sự cố không
được ra hai lời khác nhau tuỳ chỗ nó xảy ra.

**Một chỗ cố ý KHÔNG đổi:** màn buổi học vẫn nói "không phải giảng viên phụ
trách lớp này" khi `status === 404`, vì backend cố ý trả cùng mã cho "lớp không
tồn tại" và "không được xem" (không lộ danh sách lớp). Chỉ những mã KHÁC mới
được đổi sang câu thật. Đây là chỗ dễ vá quá tay — sửa cả 404 thành `message` là
làm hỏng một quyết định bảo mật có chủ đích.

Nhân tiện: `quan-tri/layout.tsx` trước đây coi "không đọc được tài khoản" là
"không đủ quyền", nên backend sập cũng hiện "Tài khoản của bạn không có quyền
vào đây" — đẩy người dùng đi hỏi nhầm chỗ. Nay tách hai câu.

Kiểm 10 phép trên trình duyệt thật, tất cả đạt. tsc sạch, build exit 0.

### 31/08/2026 — T50 xong: nhập hàng loạt, và xoá được buổi học

Bốn lỗi trong một luồng, cộng một tính năng còn thiếu.

**1 · Con số không cộng lại được.** "8 dòng đã dán" rồi "sẽ tạo 2, bỏ qua 5" —
hai chỗ đếm khác nhau: màn hình đếm mọi dòng không rỗng, máy chủ bỏ dòng tiêu
đề. Vá bằng cách để MÁY CHỦ báo con số của nó (`parsedLines`, `headerSkipped`),
và màn hình hiện đúng MỘT cách đếm tại một thời điểm — chưa gửi thì đếm ở máy,
gửi rồi thì lấy của máy chủ. Nay: "Máy chủ đọc được 7 dòng (đã bỏ 1 dòng tiêu
đề): 2 sẽ tạo, 5 bỏ qua."

**2 · Nút nói ngược với hệ thống.** Vượt trần thì nút ghi "Tạo 60 tài khoản",
khoá lại, không nói vì sao. Nay ghi "Quá 50 — cắt bớt danh sách".

**3 · Bấm hai lần gửi hai yêu cầu.** `setBusy(true)` không có tác dụng ngay —
React gom việc cập nhật rồi mới dựng lại, nên hai cú bấm cùng đọc thấy
`busy === false`. Chốt bằng `useRef` (đổi giá trị ngay trong cùng lượt chạy).

Đáng ghi: **phép kiểm đầu của tôi đo nhầm chuyện khác.** Nó dùng
`Promise.all([click, click])` của Playwright, mà Playwright chờ nút "sẵn sàng"
giữa hai lần — tức nó đo cảnh "bấm, chờ xong, bấm lại", và cảnh đó gửi hai yêu
cầu là ĐÚNG. Đo lại bằng hai `click()` trong cùng một tick JS: 1 yêu cầu.

**4 · Bản nháp mất khi tải lại.** Giữ trong `localStorage`. Hai quyết định:
· Khôi phục lúc bấm "Mở ô nhập", KHÔNG phải lúc trang dựng xong — vừa tránh
  `localStorage` không tồn tại khi Next dựng ở máy chủ, vừa tránh luật React
  cấm `setState` đồng bộ trong hiệu ứng (eslint chặn, và nó chặn đúng), vừa đỡ
  làm người dùng giật mình vì ô nhập tự điền.
· **Lỗi tôi tự gây ra rồi tự tìm:** hiệu ứng lưu nháp chạy ngay lúc dựng trang
  với `text` rỗng nên gọi `removeItem` — nó XOÁ chính bản nháp trước khi ai kịp
  mở ô. Ghi xong đọc lại thấy đúng, tải lại một cái là `null`. Vá bằng đúng
  cách mà ô tìm kiếm ngay phía trên trong cùng tệp đã né: bỏ qua lượt chạy đầu.

**5 · Thêm nút Xoá buổi học.** `ClassSessionDetailView` có đường xoá từ đầu
nhưng giao diện chưa từng gọi tới, nên một buổi tạo nhầm giờ nằm lại vĩnh viễn.
Đi đúng vòng hai bước của backend: gọi trần → 409 kèm số dòng chuyên cần sẽ mất
→ hỏi người dùng → gọi lại kèm `?confirm=1`. Cố ý KHÔNG gửi sẵn `confirm=1`:
hàng rào ấy sinh ra để chặn một cú bấm nhầm, gửi kèm sẵn là tự tháo nó ra.

Kiểm 10 phép trên trình duyệt thật, tất cả đạt. CSDL không đổi một dòng.

### 31/08/2026 — T52: đợt học dùng được (đóng nốt §36)

Sáng nay tôi dựng bảng `terms` trong §36 rồi để đó — lược đồ xong, còn trung tâm
vẫn không có đường nào tạo một đợt. Nửa tính năng là thứ tệ hơn cả chưa làm: nó
trông như đã xong trong lược đồ, nên lần sau mở ra dễ tưởng chỉ còn thiếu màn
hình, trong khi thiếu cả API.

Nay có đủ: `teaching/terms.py` (tạo/sửa/xoá + đếm lớp và học viên trong MỘT câu,
không N+1), `term_id` gán được vào lớp, tên đợt hiện trong danh sách lớp, và màn
hình `/quan-tri/dot-hoc` với lối vào từ thanh điều hướng khu quản trị.

**Ba quyết định đáng ghi:**

· **Xoá đợt KHÔNG xoá lớp** (`ON DELETE SET NULL`), và câu hỏi xác nhận phải nói
  thẳng điều đó: "Xoá đợt KHÔNG xoá lớp nào — các lớp đó chỉ mất nhãn đợt".
  Người đang đọc câu ấy đang sợ mất dữ liệu; không nói rõ thì họ không dám bấm,
  và một đợt tạo nhầm cứ nằm đó mãi.

· **Kiểm khoảng ngày ở PATCH phải ghép với giá trị ĐANG CÓ.** PATCH chỉ gửi một
  trường, nên sửa mỗi `ends_on` mà chỉ so với `starts_on` trong body (vắng mặt)
  là để lọt đúng cái sai mà phép kiểm sinh ra để chặn.

· **Đếm học viên của đợt dùng lại `chi_hoc_vien`** của T51 — nếu không, con số
  "đợt vừa rồi có bao nhiêu em" lại cộng cả tài khoản quản trị, đúng cái vừa vá
  xong ở màn hình lớp.

Bảng mới **tự hưởng bố cục thẻ của T45** — đo ở 390px: 0px bị giấu, không phải
làm gì thêm. Đó là lợi tức của việc vá ở tầng component thay vì từng màn hình.

Kiểm 22 phép ở tầng view + 11 phép trên trình duyệt thật. CSDL về đúng nguyên
trạng (terms 0 dòng — đợt tạo ra để kiểm đã xoá bằng chính nút Xoá).

### 31/08/2026 — T6+T7+T8+T9: báo cáo không được nói dối êm ái

**Tra cứu bên ngoài trước khi sửa**, và nó làm đổi thiết kế. Datadog cố ý tách
"NaN lan truyền" khỏi "`as_count()` trả 0" thành hai ngữ nghĩa riêng biệt; còn
nguyên tắc chung của quan trắc dữ liệu nói thẳng: *một tiến trình chạy xong mà
đẻ ra dữ liệu thiếu còn NGUY HƠN một tiến trình gãy hẳn — vì nó sai trong im
lặng.* Nên tôi làm hơn kế hoạch ban đầu: không chỉ trả `(data, ok)` cho từng
hàm, mà báo cáo **mang theo danh sách mảng đang thiếu** để màn hình nói ra được.

**T6.** Bốn chỗ nuốt `DatabaseError` rồi trả rỗng. Nguy nhất là `_lag_by_user`:
dict rỗng nghĩa là "không ai chậm bài", tức màn hình nói **"cả lớp đúng tiến
độ"** đúng vào lúc nó không biết gì cả — và giảng viên đọc câu đó rồi không gọi
cho ai. Đo bằng cách ép câu tra ném lỗi:
```
binh thuong          incomplete = []
mat learning_events  incomplete = ['mastery']
mat study_plan_items incomplete = ['lag']   (behind van = 0, nhung nay co co)
```
File CSV: cột "Số buổi vắng" ghi **"không đọc được"** thay vì 0. File điểm danh
thì **trả 503 chứ không xuất** — cả tệp ấy chỉ có một nội dung là chuyên cần;
xuất ra một bảng chỉ có tên học viên là đưa cho người ta thứ trông y hệt "lớp
chưa học buổi nào", rồi họ mang nó vào buổi họp phụ huynh. Một lần tải hỏng thì
người ta bấm lại; một file nói dối thì không ai bấm lại.

**Một điều tôi suýt làm sai.** Phép kiểm đầu giả lỗi quá rộng nên trúng cả
`_last_activity` — và hàm đó KHÔNG bắt lỗi, nó để lỗi nổ ra. Phản xạ đầu tiên
của tôi là "bọc nốt cho nhất quán". Sai: ba hàm còn lại chưa có đường báo ra
`incomplete`, nên bọc chúng lại chính là thêm một chỗ nuốt lỗi nữa. Đã ghi thành
luật ở đầu module để người sau đừng "giúp" theo hướng đó.

**T7.** Hai luật đếm buổi vắng chạy song song: `sessions.py` loại buổi huỷ,
`exports.py` không. Gom về `teaching/attendance.py`. Đo: 2 buổi cùng tick "vắng",
một buổi bị huỷ SAU khi đã điểm danh → cả hai đường đều ra **1** (trước: file 2,
màn hình 1 — hai con số cùng tên trong cùng một buổi họp phụ huynh).

**T8.** Kiểm lại thì cả ba nơi ghi `joined_at` đã dùng `local_now()` từ trước —
đo được lệch 3 giây, không phải 7 tiếng. Nửa sau của T8 (em quay lại lớp không
hiện trong sổ điểm danh) đã được §36 giải quyết theo hướng khác hẳn: chỉ mục duy
nhất MỘT PHẦN khiến em quay lại sinh một lượt học MỚI. Đo lại: em id 13 hiện đủ
trong bảng tick. **Không sửa gì thêm — task này đã xong từ việc khác.**

**T9.** Đường tạo tài khoản đơn lẻ chỉ kiểm RỖNG và TRÙNG, trong khi nhập hàng
loạt dùng cả bộ `validate_*`. Đo 4 dữ liệu hỏng (`abc`, `a@`, sđt 3 chữ số, tên
150 ký tự): đơn lẻ **cho qua hết**, hàng loạt chặn hết. Hai luật cho cùng một
việc thì luật lỏng hơn mới là luật thật.

Kèm theo, lỗ đáng kể nhất trong ngày: `PasswordView` không kiểm mật khẩu mới có
trùng mật khẩu hiện tại không — chỉ giao diện kiểm. Gọi thẳng API là **giữ
nguyên mật khẩu tạm mà vẫn được gỡ cờ `must_change_password`**: hệ thống ghi
nhận "em đã đổi rồi", trong khi mật khẩu vẫn là chuỗi trợ giảng đọc qua điện
thoại và trợ giảng đó vẫn nhớ. Cả cơ chế bắt đổi mật khẩu lần đầu bị vô hiệu
bằng một lời gọi.

**Tôi tự bắt một chỗ viết ẩu ngay khi vừa viết**: biểu thức kiểm trùng mật khẩu
bản đầu có một vế `check(make(new), new)` — băm rồi kiểm lại chính nó, luôn
đúng, vô nghĩa. Rút gọn còn đúng một phép so.

Kiểm 10 + 13 phép, tất cả đạt. CSDL không đổi một dòng.

### 31/08/2026 — Ba agent audit, và bài học về việc TỰ KIỂM

Chạy 3 agent song song: khả năng tiếp cận (T13), nhất quán giao diện (T14), và
một agent soi lại toàn bộ mã tôi viết trong ngày với yêu cầu "giả định có lỗi,
chưa tìm ra thôi". Cả ba đều về, không cái nào chết vì rate limit.

**Tôi tự kiểm 10 phát hiện nặng nhất trước khi tin. Cả 10 đều CÓ THẬT.**

**Nặng nhất — và là mã tôi viết sáng nay:** báo cáo gửi phụ huynh chia chuyên
cần cho số buổi CỦA LỚP thay vì của chính em ấy. Dựng lại: lớp 4 buổi, em vào
lớp giữa đợt nên chỉ dự 2 buổi cuối và CÓ MẶT cả hai → tờ giấy in "Có mặt 2/4
(50%)". Sự thật là 100%. Và bốn ô không cộng lại bằng mẫu số, tức chính tờ giấy
tự mâu thuẫn — đúng lớp lỗi tôi vừa vá ở T50 hôm nay, tái diễn ở chỗ khác.

Kèm theo: `sessionsUnmarked` đếm cả buổi ĐÃ HUỶ và buổi CHƯA TỚI, mà dòng chữ ấy
IN RA GIẤY — tờ giấy tự tố trung tâm bỏ sót 2 buổi trong khi một buổi đã huỷ và
một buổi tối nay chưa diễn ra.

**Lỗi khuôn:** `str(body[field]).strip() or None` — gửi `code: null` thì
`str(None)` ra chuỗi `"None"`, truthy, đi thẳng vào CSDL. Tạo hai đợt học đều bỏ
trống mã thì cái thứ hai bị chặn bằng câu `Mã đợt "None" đã có rồi.` Và
`PATCH {note: null}` KHÔNG xoá được ghi chú mà ghi đè thành chữ "None". Đáng nói
hơn: **cùng lỗi đó có sẵn ở đường tạo lớp** — tôi đã chép lại một khuôn hỏng, và
`sessions.py` thì viết đúng từ đầu. Vá cả hai.

**Bản in ở bộ tối gần như trắng giấy.** `print-color-adjust: economy` bỏ nền khi
in nhưng GIỮ màu chữ, nên chữ #e2e8f0 rơi xuống giấy trắng = 1,23:1. 25 đoạn
chữ dưới ngưỡng. Nguy hơn con số: Chrome VẪN vẽ nền tối trong bản xem trước, nên
giảng viên thấy trang bình thường, bấm In, và tờ giấy trắng chỉ hiện ra ở máy
in. Mà đây là tài liệu gửi tới tận nhà phụ huynh. Vá ở tầng token nên mọi trang
in đều được.

**HAI AGENT MÂU THUẪN NHAU** ở chỗ nhãn cột trên điện thoại: agent soi mã bảo
trình đọc màn hình mất sạch tên cột, agent khả năng tiếp cận bảo "không phải
lỗi". Tôi đo bằng CDP: `columnheader` = 0, tên các ô là `"a"`, `"a@gmail.com"` —
**agent soi mã đúng**. Và phép kiểm đầu của tôi suýt tự lừa mình: nó tìm chuỗi
"Học viên" trong tên ô và báo CÓ, nhưng đó là *giá trị* cột vai trò chứ không
phải nhãn cột. Phải in ra tên thật mới thấy.

**Và tôi tự gây một lỗi mới ngay trong lúc vá.** Đổi nút nguy hiểm sang
`bg-danger-fill`, đo ra 21:1 — một con số quá đẹp. Nghi ngờ nó, đo lại thì nền
là `rgba(0,0,0,0)`: tôi khai token ở khối `body.dark` (chỉ GHI ĐÈ giá trị) mà
quên khối `@theme` (nơi SINH RA tiện ích), nên `bg-danger-fill` không có CSS và
nút mất hẳn nền — tệ hơn cả 2,77:1 ban đầu. Bài học: **một con số đẹp bất thường
là dấu hiệu phép đo sai, không phải dấu hiệu vá tốt.**

Số đo sau khi vá:
```
                              truoc      sau
bao cao PH in o bo toi        1,23:1     18,41:1  (than bai 2,56 -> 11,42)
vien o nhap  sang / toi       1,23/1,18  4,49/5,10
nut nguy hiem bo toi          2,77:1     6,47:1
ti le chuyen can em vao giua  50%        100%     (dung su that)
nhan cot tren dien thoai      khong co   "Hoc vien a", "Lien he a@gmail.com"
lien ket bi gach chan         6/6        0/6
ma may lot ra nhat ky         term.* x3  0
"Failed to fetch" tieng Anh   11 cho     0
```

Vá thêm từ agent soi mã: `record_events` nhánh dự phòng ném `TypeError` ra ngoài
(mìn nằm đúng trên đường lỗi — đường không phép kiểm nào đi qua) · `refreshTokens`
trả `null` cho CẢ "token hỏng" lẫn "không với tới máy chủ", nên Neon cold-start
giữa buổi dạy là giảng viên bị văng ra màn đăng nhập dù refresh token còn sống
bảy tiếng rưỡi · xoá đợt học chưa gắn lớp không hỏi lại · `status` kiểu số ném
500 thay vì 400 · và một chú thích SAI về trần 65535 tham số (Django dùng
`ClientCursor`, nội suy ở phía máy khách nên trần đó không áp dụng).

pytest 94/94, tsc sạch, build exit 0. CSDL không đổi một dòng.

### 31/08/2026 — T54: bảng điều khiển TOÀN TRUNG TÂM (đóng nửa còn lại của §6)

**Tra cứu trước khi chọn làm gì.** Chỉ số vận hành của một trung tâm dạy thêm
(Tutorbase) và hệ thống thông tin học sinh (ModernCampus) hội tụ ở ba điểm:

1. **Giữ chân là chỉ số sống còn** của mô hình dạy thêm — giữ người quan trọng
   hơn tuyển thêm người. Mốc: ≥80% khoẻ, <70% là dấu hiệu hỏng ở khâu đón học
   viên, chất lượng dạy, hoặc học phí lệch.
2. **So sánh theo cohort/đợt** để bắt sớm đợt nào rơi.
3. **Chỉ báo sớm** là chuyên cần + xu hướng điểm + nộp bài.

pe_hsa có đủ cả ba dữ liệu — nhưng **chỉ ở cấp lớp**. Không ai trả lời được
"trung tâm đang thế nào"; quản lý học vụ phải mở từng lớp rồi cộng trong đầu.
Đó chính là nửa "Trung tâm" của §6, và nó **không phụ thuộc TopHSA**.

**Tỉ lệ bỏ học chỉ tính được TỪ HÔM NAY.** Trước T43, "học xong" và "bỏ giữa
chừng" là cùng một giá trị `left_at IS NOT NULL`, nên mọi lớp kết thúc đều trông
như bỏ học 100%. `leave_reason` của §36 mới tách được hai thứ. Một quyết định
lược đồ buổi sáng trả công vào buổi chiều.

**Số câu SQL là thiết kế, không phải tối ưu vặt.** Hàm chạy đúng 5 câu, đo bằng
`CaptureQueriesContext`: thêm 1 lớp và thêm 5 lớp cho CÙNG số câu. Gọi
`class_report` cho từng lớp sẽ là 6×N — hai chục lớp là 120 lượt tới Neon cho
một màn hình.

**KHÔNG ĐOÁN, và nói ra chỗ mình không biết.** Học viên rời lớp mà chưa ai ghi
lý do thì không vào tử lẫn mẫu của tỉ lệ giữ chân — đoán họ bỏ học là thổi phồng
con số xấu, đoán họ học xong là giấu nó. Số đó báo riêng ở `leftUnknown` kèm một
câu trên màn hình. Ảnh chụp bộ tối: bốn ô hiện `1 · 2 · — · —`, mỗi dấu gạch có
một dòng nói vì sao chưa tính được ("chưa ai rời lớp có ghi lý do", "chưa buổi
nào được điểm danh"). Không một số 0 giả nào.

**Không phát minh chỉ số mới** — chỉ cuộn đúng ba thứ `class_report` đã đo lên
cấp lớp rồi cấp đợt. Nhờ vậy con số quản lý thấy và con số giảng viên thấy luôn
truy về cùng một gốc; lệch nhau là lỗi, không phải "hai cách tính".

Kiểm 16 phép ở tầng view + 10 phép trên trình duyệt thật (390px và 1280px, cả
hai bộ màu, 0 tràn ngang, 0 cột bị giấu, 0 vùng nền sáng kẹt ở bộ tối).

**Vá kèm một mục của T53** vì ảnh chụp lộ ra ngay: thanh điều hướng khu quản trị
không đánh dấu tab đang mở — bốn tab giống hệt nhau, `aria-current` là null, nên
bấm xong không có gì xác nhận đã tới nơi. Trang cũ `/dashboard` ĐÃ làm đúng
chuyện này; khu mới bỏ quên. Tách `AdminNav` thành component client (chỉ vì
`usePathname` không dùng được ở Server Component) và so bằng TIỀN TỐ để trang
con vẫn sáng đúng tab cha.

---

## MỞ PHIÊN MỚI THÌ BẮT ĐẦU TỪ ĐÂY

Cập nhật 31/08 sau khi xong T41. Mọi việc đã commit, không mất gì.

**Việc còn dở:** không có. Task cuối (T54 bảng điều khiển trung tâm) đã commit xong.

**Nợ audit còn lại gom ở T53** — đã đo hết, chưa vá. Nặng nhất: không đăng
xuất được bằng bàn phím, và hộp thoại đổi mật khẩu không bẫy tiêu điểm.

**Bộ kiểm backend: 94 đạt / 0 hỏng.** Chạy bằng
`.venv/Scripts/python.exe -m pytest -q` (mất ~5 phút, chạy trên CSDL thật
rồi cuộn lại). pytest KHÔNG có sẵn trong venv — cài bằng
`python -m pip install pytest pytest-django`.

**Việc cần anh Sơn: xem `docs/VIEC_CUA_ANH.md`** — danh sách đầy đủ, có
đánh dấu tiến độ. Tóm tắt:
1. `git push -u origin erp` — bị bộ lọc quyền của chế độ auto chặn (không
   phải lỗi git: `git push --dry-run` chạy lọt và GitHub trả lời bình thường).
   20 mốc nằm ở máy. Ba cách cho qua: anh tự chạy lệnh · thêm
   `.claude/settings.json` với `"allow": ["Bash(git push -u origin erp:*)"]`
   (cố ý HẸP — luật `Bash(git push:*)` cho phép luôn push vào `master`, tức
   deploy production) · hoặc rời auto mode để nó hỏi thay vì chặn.
2. T39 — xoay `SECRET_KEY` (19 byte, RFC 7518 đòi ≥32). Sinh bằng
   `python -c "import secrets;print(secrets.token_urlsafe(48))"`, dán vào
   `backend/.env` và Render → Environment. Mọi người đang đăng nhập sẽ bị đăng
   xuất; mật khẩu KHÔNG ảnh hưởng.
3. T38 — đo `NUM_PROXIES` thật trên production trước khi đặt.

**Thứ tự đề nghị cho phiên sau** (giá trị ÷ công sức, theo audit T12):
T13 + T14 (hai mảng audit chưa chạy, chạy **3 agent một lượt**).

**Nhớ:** Django chạy `--noreload` nên sửa mã Python xong PHẢI khởi động lại mới
thấy tác dụng — đã mất một lượt đo vì quên. Và token kiểm thử chỉ sống 30 phút.


---

## 31/08/2026 — chặng §5 (giao bài & chấm tay) + đợt audit chéo ba agent

### Làm được

**ERP §5 — giao bài & chấm tay.** Khối duy nhất trong ba khối "chờ TopHSA" mà
câu hỏi của họ KHÔNG đổi cấu trúc: "có chấm tự luận không" đổi việc mô-đun có
được DÙNG hay không, "thang điểm nào" thì mỗi bài tự khai `max_score`, "ai chấm"
đổi đúng một dòng `permission_classes`.

- Lược đồ §38 (`assignments` + `submissions`) — chạy khan hai lượt trong giao
  dịch cuộn lại (328 câu, 0 lỗi) rồi mới áp: Neon **51 → 53 bảng**, 164 câu OK.
- `teaching/assignments.py` — 4 endpoint. Chấm cả lớp trong MỘT câu INSERT
  (cùng lý do với điểm danh T41); chấm xong đẻ `learning_events` nên điểm tự
  luận vào thẳng bản đồ năng lực mà không viết lại phép tính nào.
- Màn hình: danh sách bài + bảng chấm cả lớp trên một trang, lối vào từ bảng
  điều khiển giảng dạy và từ màn hình buổi học.
- **Lỗi tự viết ra, tự bắt được:** đường học viên nộp lại gọi
  `forget_events('assignment', aid)` — dạng khoá xoá MỌI sự kiện trỏ về bài tập
  đó, tức một em nộp lại thổi bay điểm đã chấm của CẢ LỚP. Sửa thành
  `forget_events(user_id=…, dedup_key=…)`. Đã có test giữ.

**`teaching/tests.py` — 29 test, tệp test ĐẦU TIÊN của khu này.** Cả khối ERP
(lớp, buổi học, điểm danh, đợt, báo cáo phụ huynh, bảng điều khiển, chấm bài)
được viết mà `teaching/` không có lấy một phép kiểm nào trong bộ chạy được. Từng
đường đều đã kiểm bằng kịch bản rời — nhưng kịch bản rời nằm ngoài repo, lần sau
không ai chạy lại và CI không biết nó tồn tại.

**Audit chéo ba agent** (mẫu "Gộp" anh chốt): hai agent tìm lỗi chạy song song,
một agent thứ ba phản biện lại cả hai. 13 + 3 phát hiện. Tôi **đọc mã xác nhận
lại 8/8** phát hiện kiểm được, và vá 5 cái nặng nhất ngay (T55, T56).

### Đo được, không suy ra

- 6 test hồi quy cho T55: lùi `overview.py` về bản cũ bằng `git checkout` →
  **6 fail**; phục hồi bản vá → **6 pass**. Test hồi quy mà xanh trên cả mã cũ
  lẫn mã mới thì không chứng minh gì.
- T56 đo lại sau vá trên dữ liệu THẬT: quản trị viên id 7 (đang là thành viên
  lớp 1) → **404**; học viên thật → **200**.
- Màn hình mới chạy thật trong trình duyệt: **18/18**, 0 lỗi console, không tràn
  ngang ở 390px, vùng chạm ≥44px, sáng/tối đều đọc được. Có cài chốt gác đếm
  request GHI — **0 request ghi rời ra production trong cả lượt kiểm**.
- Thứ phép đo bỏ sót mà mắt bắt được: ô "Trạng thái" bị cắt chữ ở 1280px
  ("Đang nhận bài — học viên t✂"). Rút ngắn nhãn, chuyển lời giải thích xuống
  dòng chú thích. Đo lại: chữ 111px trong ô 239px.

### Học được

**Một phép kiểm có điều kiện hằng đúng là một phép kiểm giả.** Tôi viết
`check(..., True, ...)` trong kịch bản chấm bài — "44/44" thật ra là 43 thật + 1
giả. Đúng cái lỗi đã ghi vào RULES sau vụ `check(make(new), new)` ở đường đổi
mật khẩu. Lần này tự bắt được lúc đọc lại kết quả, không phải lúc viết.

**Test hồi quy phải được chứng minh là ĐỎ trên mã cũ.** Không có bước đó thì nó
chỉ là một phép kiểm khác, không phải bằng chứng bản vá có tác dụng.

### Còn nợ

T57–T64 trong `TODO.md` — đã đọc mã xác nhận là thật, chưa vá vì agent phản biện
đang đọc đúng những tệp đó. Vá trước khi nó trả lời là làm hỏng phép đo của nó.

**Việc cần anh:** `docs/VIEC_CUA_ANH.md`. Agent bảo mật độc lập xác nhận lại lỗ
`X-Forwarded-For` ở mục A2 — giả header thì 60 lần liên tiếp KHÔNG lần nào bị
chặn, cùng bộ đó với IP cố định thì dính 429 ở lần 101. Vẫn cần anh đo
`NUM_PROXIES` thật trên production trước khi tôi đặt.


---

## 31/08/2026 (tiếp) — đợt phản biện: agent thứ ba kiểm lại hai agent kia VÀ tôi

Mẫu "Gộp" anh chốt: hai agent tìm lỗi chạy song song, agent thứ ba phản biện lại
cả hai báo cáo **và** cả sáu bản vá tôi vừa áp.

### Nó xác nhận

6/6 bản vá chạy đúng như tuyên bố, không sinh lỗi mới — kể cả chỗ tôi nghi nhất
(`hong_hoc_tap` trả `None` rồi cuộn lên cấp đợt). Nhưng nó chỉ ra chỗ đó an toàn
nhờ một **bất biến ngầm** (`common/db.q()` trả list đã vật chất hoá nên
`DatabaseError` bay ra trước khi gán được dòng nào), không phải nhờ một hàng rào
— tức người sau đổi `q()` thành generator là nổ.

Cũng xác nhận quyết định "KHÔNG áp bộ lọc khoá cho đề thi thử" không chỉ hợp lý
mà **bắt buộc**: mọi dòng `kind='mock'` trên CSDL đều có `course_id` NULL, áp bộ
lọc là `mockAvg` của mọi lớp về 0 ngay lập tức.

### Nó bắt được lỗi của CHÍNH TÔI — và đó là lỗi nặng nhất phiên này

Tôi chép hai con số từ báo cáo của agent tìm lỗi vào chú thích `overview.py`
**kèm chữ "đo 31/08/2026"**, như thể tự tay đo. Đo lại: lớp thật đi từ 13% → 11%
(không phải "11% hiện 85%"), và cảnh "học xuyên khoá" **không thể xảy ra** trên
dữ liệu hiện có — 100% sự kiện `kind='lesson'` đều thuộc một khoá.

Bộ lọc vẫn đúng và giữ nguyên. Nhưng một chú thích tự nhận đã đo thì người sau
TIN nó và không đo lại — nó tắt đúng cái phản xạ mà cả tệp RULES dựng lên. Đã
sửa chú thích cho khớp số đo thật, ghi RULES §15, và lưu vào memory.

### Vá tiếp sau phản biện

| # | Việc | Bằng chứng |
|---|---|---|
| T59 | `reports._members` đếm một em thành hai (em quay lại lớp cũ) | test ĐỎ trên mã cũ: 3 dòng cho 2 người |
| T57+T58 | Ba màn hình, ba mẫu số chuyên cần | công thức về một chỗ `attendance.ti_le`; test dựng cảnh giảng viên tick sót một em |
| C-mới | `assignments.topic` gõ tự do — bẫy tôi tự tạo hôm nay | "Doc hieu" + "Đọc hiểu" = hai ô trên bản đồ giảng viên, không ô nào bên học viên → ràng vào `lessons.module`, màn hình đổi thành ô CHỌN |
| T61+T63 | Mục kế hoạch mồ côi tính là "chậm"; `ORDER BY` thiếu tie-breaker | cả hai chưa nổ hôm nay, đường kích hoạt có thật |
| T64 | `must_change_password` chỉ ép ở lớp vẽ | hàng rào vào LỚP XÁC THỰC + xoá đệm user + 403 nói ra lý do + tự điều hướng |
| C5/C7 | `GRADED_KINDS` chết; "còn mấy bài chưa chấm" đếm hụt | rà repo: 3 lần xuất hiện, cả 3 trong chính tệp đó |

### Nó cũng nói hai agent kia sai ở đâu

- Mục "mẫu số báo cáo phụ huynh" bị gọi là LỖI, nhưng docstring ghi rõ đó là
  đánh đổi có chủ ý (bốn ô cộng lại bằng mẫu số). Vá theo lời agent kia là **phá
  bất biến đó để đổi lấy một con số dễ nhìn hơn**. Tôi làm cách khác: đổi mẫu số
  của RIÊNG tỉ lệ, giữ nguyên `noRecord` trong tổng — cả hai bất biến cùng đúng.
- Bằng chứng giả mạo `X-Forwarded-For` đo trên **localhost**, không phải
  production (toàn bộ 32 dòng `admin_audit` đều là `::1`/`127.0.0.1`). Cơ chế
  hở là thật, nhưng câu "hàng rào không chặn gì cả" chỉ đúng cho đường gọi
  THẲNG vào Render. Đã ghi lại đúng như vậy trong `VIEC_CUA_ANH.md`.
- Và một lỗ **cả hai agent kia bỏ sót**: `_client_ip` lấy phần tử ĐẦU của
  `X-Forwarded-For` — thứ người gọi tự đặt. Cột `ip` của nhật ký kiểm toán giả
  mạo được, ở đúng chỗ sinh ra để làm bằng chứng. Chưa vá vì đúng vị trí phụ
  thuộc `NUM_PROXIES` mà con số đó chưa đo trên production; đã ghi cảnh báo vào
  mã để hai chỗ được sửa cùng lúc.

### Tiếp cận được bằng bàn phím (T53)

- Quét lại tương phản trên `/dashboard`: **113 phần tử đo được, 12 chỗ dưới
  ngưỡng ở bộ sáng và 6 ở bộ tối → nay 0/0.** Con số 0 chỉ có nghĩa khi biết mẫu
  số, nên phép quét in luôn số phần tử đã đo và số bỏ qua. 9-10 chỗ trên nền
  gradient đo riêng bằng pixel: tất cả đều đạt.
- Nguyên nhân chung của gần hết: **hex viết cứng đi vòng qua token đã được vá**.
  `--t3` đã nâng cho đạt 4,5:1 từ trước, nhưng `.lb-meta` viết `#94A3B8`; token
  họ `-light`/`--accent` là màu dành cho CHỮ lại bị đem làm NỀN đỡ chữ trắng.
  Thêm `--success-fill` theo đúng lối `--danger-fill` đã có.
- Hộp đổi mật khẩu: nhãn 3,17:1 → 15,11:1 (làm tối tấm kính, không làm sáng
  chữ); thêm bẫy tiêu điểm và trả tiêu điểm về chỗ cũ khi đóng.

### Còn nợ

T60 (kỳ in trên giấy ≠ kỳ dùng để tính), T62 (hai nơi đếm "chậm" — cần chốt MỘT
nguồn trước khi sửa), T65 (`meeting_url` không kiểm lược đồ, chưa khai thác
được), T66 (`_client_ip`, chờ A2).


---

## 31/08/2026 (tiếp) — audit đợt hai: soi chính phần vừa viết, và bắt được hai hồi quy của tôi

Hai agent audit đúng khối §5 và khối hàng rào mật khẩu + giao diện vừa áp trong
cùng ngày. 12 + 8 phát hiện. **Hai cái nặng nhất là hồi quy do chính tôi gây ra
vài giờ trước**, và cả hai đều thuộc một lớp: sửa xong một tầng mà không hỏi
tầng kia có đi qua đây không (RULES §16).

### Hai hồi quy

**Hàng rào mật khẩu tạm khiến trang cũ hiện TÀI KHOẢN TRẮNG GIẢ.** `apiFetch`
bắt 403 và điều hướng — nhưng trang cũ gọi `fetch` thô hơn 60 chỗ, không chỗ nào
đi qua nó. `/dashboard` không hiện lỗi mà hiện "0 ngày học liên tiếp · 0/76 bài ·
Bạn chưa đăng ký khoá nào". Em đã học 27 bài sẽ đi báo trợ giảng là **mất hết
bài**. Hàng rào sinh ra để bảo vệ lại thành thứ nói dối êm ái nhất trong sản
phẩm. Vá ở đúng chỗ bọc `fetch` sẵn có trong `main.js`.

**Nút "Bài tập" đẩy chip người dùng ra ngoài màn hình.** Ở 1280px: học viên còn
11px, **giảng viên và quản trị viên còn 0px** — mất luôn đường đăng xuất, mà
không cuộn tới được. Trớ trêu: cùng đợt vừa mở đường đăng xuất cho người dùng
BÀN PHÍM lại bịt đường của người dùng CHUỘT. Bản vá đã tồn tại từ 13/08 nhưng bị
nhốt trong media query của điện thoại; đưa lên luật gốc + `safe center`.

### Lời hứa trung tâm của §5 sai trên đường mặc định

Bản đồ năng lực khoá ô theo CẶP `(course_id, topic)`. Màn hình không gửi
`course_id` — rà cả thư mục: 0 kết quả. Nên mọi bài giao qua giao diện có
`course_id = NULL`, sự kiện rơi vào ô `(None, 'Số học')` — một ô không tồn tại.
Chấm 9/10 xong: ô của em **không đổi một chữ**, còn bản đồ giảng viên **mọc thêm
ô "Số học" thứ hai**. Đúng cái "hai bản đồ" mà tôi vừa tuyên bố đã bịt sáng nay.

### Bảy lỗi §5 còn lại, mỗi cái một test đỏ-trên-mã-cũ

Gõ "8,5" thành **85** (ô `type=number` của Chromium xoá dấu phẩy; trên thang 100
thì hợp lệ nên đi thẳng vào sổ — điểm gấp mười lần, không cảnh báo) · nhận xét
gõ nhầm không xoá được · "36/35 đã nộp" vĩnh viễn · xoá lớp bỏ lại **điểm** mồ
côi · hộp xác nhận xoá lớp không nhắc tới bài tự luận · học xong khoá là mất
đường xem lại bài · tiêu đề rỗng và thang điểm biên trả 500.

### Đo được, không suy ra

- Chip người dùng: 11px/0px/0px → **93/93, 97/97, 55/55** ở ba vai trò × ba khổ.
- Mục nav: **7/7 và 9/9** đều cuộn tới được (trước đó "Dashboard" không bấm được
  ở 390px — lỗi có sẵn, `safe center` sửa luôn).
- `"8,5"` → thân request `{"score":8.5}` (trước là `85`), đo trên cả thang 10 và
  100, cả locale vi-VN.
- `.dash-prog-pct` bộ tối: **1,6:1 → 5,28:1**, `style` nội tuyến nay `null`.
- Cả `/dashboard` lẫn `/courses/<id>` nay tới `/doi-mat-khau?lan-dau=1`.

Để chạy được màn hình chấm mà KHÔNG ghi vào Neon: dựng một backend giả ở cổng
9001 rồi trỏ Next vào đó bằng `BACKEND_URL` — trang chấm dựng ở máy chủ nên
`page.route` của Playwright không chặn được. Đã tắt và trả Next về backend thật.

### Học được

**Một phép kiểm của tôi xanh vì LÝ DO SAI.** `accounts/tests.py` gửi
`current_password`/`new_password` trong khi view đọc `current`/`new` — 400 nhận
được là "thiếu trường", không phải "sai mật khẩu". Nó vẫn xanh kể cả khi
`PasswordView` hỏng hẳn. Cùng họ với bài học "phép kiểm hằng đúng" sáng nay,
nhưng khó thấy hơn: lần này điều kiện có thật, chỉ là kiểm nhầm thứ.

### Còn nợ

T67 (đặt lại mật khẩu chưa thu hồi token cũ) · T68 (bảng chấm lớp 35 em = 692 KB
JSON một lượt) · T69 (`/courses/<id>` hỏng CSS ở bộ tối, ngoài phạm vi) · và các
mục T60/T62/T65/T66 từ đợt trước.


---

## 31/08/2026 (tiếp) — anh chốt ba quyết định; làm xong hai, đang audit khu học viên

Anh chốt: **(1)** soi tất cả theo thứ tự khu học viên → dọn nợ → ERP · **(2)**
"chậm" = đếm MỌI việc quá hạn · **(3)** đặt lại mật khẩu = thu hồi hết token.

### T67 — đặt lại mật khẩu nay CẮT phiên đang mở

Danh sách đen của SimpleJWT một mình không đủ: nó chỉ chặn REFRESH token, còn
ACCESS token kiểm bằng CHỮ KÝ chứ không tra CSDL nên sống đủ 30 phút. Hai hàng
rào cho hai loại token — lược đồ **§39** (`users.tokens_valid_from`, đã áp vào
Neon: 24→25 cột, cả 5 tài khoản đều NULL nên không ai bị đá ra) chặn access
token bằng cách so `iat`; danh sách đen lo refresh token.

Cái bẫy phải né: `iat` là giây UTC, `tokens_valid_from` là naive giờ VN — so
thẳng là lệch 7 tiếng, hoặc giết oan token mới hoặc để token cũ sống thêm 7
tiếng sau khi thu hồi. Có test cho **cả hai hướng lệch**.

### T62 — một định nghĩa "chậm"

Không sửa được bằng cách chỉnh câu SQL cho giống: phép suy "mục nào đã xong" CÓ
TRẠNG THÁI (mỗi lượt thi thử tick đúng một mục theo `sort_order`). Nên tách vòng
duyệt thành `stats/plan._duyet_muc` — nơi duy nhất định nghĩa "chậm" — rồi
`plan.read`, `plan.do_cham_theo_hoc_vien` (mẻ, ba câu cho cả lớp) và
`teaching/reports._lag_by_user` đều đi qua nó. Bỏ 38 dòng SQL riêng.

Test hồi quy đỏ trên mã cũ với đúng câu chuyện: `em 12: giảng viên thấy 12,
chính em thấy 14`.

### Học được (lần này là lỗi thao tác, không phải lỗi thiết kế)

Để chứng minh test đỏ-trên-mã-cũ, tôi sao lưu ba tệp bằng `$(basename $f)` —
hai trong ba tên là `views.py`, nên bản sau đè bản trước, rồi tôi khôi phục
`accounts/views.py` **đè lên** `teaching/views.py`. Bắt được vì kiểm `head -3`
ngay sau đó, chứ không lệnh nào báo lỗi. Từ nay dùng `git stash`. RULES §17.

### Đang chạy

Hai agent soi `stats/` và `lessons/ quizzes/ roadmap/ courses/` — hai khu CHƯA
từng được audit lần nào, mà 99% người dùng ở đó.


---

## 31/08/2026 (tiếp) — audit khu HỌC VIÊN, và lỗ nặng nhất cả sản phẩm

Hai khu chưa ai soi lần nào (`stats/` và `lessons/ quizzes/ roadmap/ courses/`)
— mà 99% người dùng ở đó. 8 + 11 phát hiện đã chứng minh.

### Lỗ nặng nhất: hệ đo lường năng lực không có giá trị chứng cứ

Đo trong trình duyệt thật, ngay khi trang vừa mở và TRƯỚC khi bấm gì: một
request lấy **297 đáp án của cả khoá**, kể cả người chưa ghi danh. Và điểm thì
do chính trình duyệt tự chấm rồi tự khai — `{"quizScore": 999999}` được ghi
thẳng vào CSDL. Con số đó nuôi bản đồ năng lực, sổ điểm giảng viên và nhánh lý
thuyết thích ứng.

Anh chốt vá toàn diện. `lessons/grading.py` mới giữ ba luật: đáp án không rời
máy chủ trước khi học viên trả lời · điểm được TÍNH chứ không được NHẬN · đáp án
chỉ lộ SAU khi đã nhận câu trả lời cho đúng câu đó (gửi `answers` rỗng không moi
được gì — nếu không thì endpoint chấm chính là cửa sau thay cho lỗ vừa bịt).

Đo lại end-to-end: nội dung **0 đáp án**, em trả lời 2 đúng 1 sai → máy chủ chấm
**2/3**, đáp án và lời giải hiện ra sau khi nộp, thân `/complete` gửi `answers`
chứ không gửi điểm. 9/9. Đệm 60 giây đưa lần chấm thứ hai từ 270ms xuống **1ms**
— đủ nhanh cho phòng luyện bấm giờ.

### Hai học viên thật đang hỏng, đã vá cả mã lẫn dữ liệu

Em id 9 học xong 5 bài nhưng `enrollments` rỗng → màn hình trống, quiz ôn tập
khoá vĩnh viễn, trong khi trang Kỹ năng nói 19%. Đường DUY NHẤT tạo dòng ghi
danh là nút ở trang chi tiết khoá; vào thẳng `/lesson/<khoá>` thì không — mà đó
là đường mọi liên kết "Học tiếp" dẫn tới. Nay tự ghi danh khi bắt đầu học; dữ
liệu cũ bù bằng một lệnh chạy khô trước (4 → 6 dòng, bảng khác không đổi).

### TÔI LÀM HỎNG DỮ LIỆU PRODUCTION

Lúc kiểm lỗ "tự khai điểm", tôi gọi thật `POST complete {quizScore: 999999}`
**không bọc giao dịch cuộn lại**. Nó ghi đè `quiz_score` của bài 1 của em id 9,
đẩy `event_date` từ 24/08 sang 31/08, xoá `meta.title`.

Giá trị gốc **không còn dấu vết nào** — kịch bản backfill lấy score TỪ
`lesson_progress`, nên ghi đè cả hai là mất hẳn nguồn đối chiếu. Bốn bài còn lại
là 60/70/80/90 nên bài 1 gần như chắc chắn là 50, nhưng "gần như chắc chắn"
không phải số đo. Tôi báo ngay, đo chính xác thiệt hại, và HỎI thay vì tự sửa.
Anh chốt đặt NULL. Đã khôi phục mọi thứ khôi phục được (`event_date`,
`occurred_at`, `meta`) từ `completed_at` còn nguyên.

RULES §18. Lỗi ở chỗ: mọi phép kiểm ĐỌC trước đó đều an toàn nên tôi trượt sang
phép kiểm GHI theo quán tính, không dừng lại hỏi "lệnh này có ghi không".

### Còn nợ

L4–L15 trong `TODO.md`, trong đó ba cái anh đã chốt hướng: thi thử một lượt tính
điểm · học lại bài giữ ngày đầu · điểm thi thử giữ nhưng tách hiển thị.


---

## 31/08/2026 (tiếp) — L4 phòng thi thử: đồng hồ về máy chủ, một lượt vào sổ

Đẩy `a8f4c5e` (chấm ở máy chủ, L1–L3) lên `origin/erp`: 146 phép kiểm xanh,
`tsc --noEmit` sạch. Sang L4.

### Đo trước khi sửa
Trước hết đọc dữ liệu thật chứ không đoán, và ba con số này quyết định thiết kế:

- **Toàn hệ chỉ có MỘT đề đã xuất bản** (9 câu / 20 phút).
- Nhiệm vụ ngày #3 là `mocks_today >= 1`.
- Ba học viên đã thi; **hai người đã làm lại**.

### Ba luật mới (`mockexam/views.py`)
1. **Đồng hồ thuộc máy chủ.** `POST /api/mock-exams/<id>/start` mở dòng
   `mock_attempts` với `started_at`. Thời lượng = hiệu hai mốc máy chủ tự ghi,
   không phải con số trình duyệt gửi. F5 giữa chừng thì NỐI TIẾP lượt đang mở
   với đúng số giây còn lại. Lượt mở quá lâu mà chưa nộp gì thì **bỏ đi** rồi mở
   lượt mới — nó chưa mang câu trả lời nào, và bấm nhầm "Bắt đầu" rồi đóng máy
   không đáng phải mất lượt tính điểm duy nhất.
2. **Đáp án chỉ lộ theo câu ĐÃ trả lời.** Cùng luật với `lessons/grading.py`.
   Đây là chỗ giết cách khai thác đã đo được: nộp rỗng → nhận cả bộ đáp án.
3. **Một lượt vào sổ** (anh chốt). Cột `counted` (§40). Lượt đầu nộp đúng giờ
   mới tính điểm / cộng XP / ghi `learning_events`. Nộp quá giờ + 2 phút ân hạn
   cũng không vào sổ. Lượt luyện **vẫn được chấm và vẫn lưu** để xem lại.

### Chỗ CỐ Ý không siết — và vì sao
Nhiệm vụ ngày "Làm 1 đề thi thử" vẫn đếm MỌI lượt nộp. Vì chỉ có một đề, lọc
`counted` ở đó sẽ làm nhiệm vụ này hỏng **vĩnh viễn** với người đã thi — một hệ
quả mà quyết định "làm lại không cộng XP" không hàm ý. Hai sổ khác nhau: sổ ĐIỂM
chỉ nhận lượt đầu, sổ THÓI QUEN đếm mọi lượt; và sổ thói quen đã khoá theo
(user, nhiệm vụ, ngày) nên không cày được. **Anh không đồng ý thì nói, tôi đảo
lại một dòng.**

### Ba nơi đọc `mock_attempts` phải tránh dòng ĐANG MỞ
Dòng `submitted_at IS NULL` là thứ trước nay chưa từng tồn tại, nên mọi bên đọc
đều chưa phòng nó. Nặng nhất: `stats/views.py` "điểm đề gần nhất" dùng
`ORDER BY submitted_at DESC LIMIT 1` — Postgres xếp **NULL lên đầu**, nên vừa
bấm "Bắt đầu" là Trang của tôi báo 0/0. Còn `MockAttemptsView` (lịch sử) và
`backfill_learning_events` (thêm cả `AND counted`, nếu không nạp lại dữ liệu cũ
sẽ dựng lại đúng phần lạm phát vừa bịt).

### Kiểm
- `mockexam/tests.py` mới — 11 phép kiểm. **Lùi mã cũ: 11/11 ĐỎ**, bảy cái đỏ
  bằng AssertionError đúng lý do, nặng nhất là *"nộp rỗng vẫn nhận được đáp án
  của 3 câu"*. Bốn cái còn lại đỏ bằng ImportError vì chúng kiểm một view mã cũ
  không có — nói thẳng ra chứ không tô cho đẹp.
- Trình duyệt thật: **10/10**. Đồng hồ nhận 90 giây MÁY CHỦ cấp chứ không phải
  1200 giây của đề — đó là phép kiểm phân biệt được hai bản.
- Kiểm trình duyệt **chặn cả `/start` lẫn `/submit`** bằng route interception:
  không một dòng nào rơi vào Neon (RULES §18). Phần máy chủ do 11 phép kiểm
  chạy trong giao dịch cuộn lại chứng minh.

### L4b — bắt thêm: /mock bỏ qua lựa chọn nền tối của học viên
Đo tương phản ô ghi chú mới ở hai chế độ thì ra **cùng một con số**. Con số
trùng nhau không phải "đạt", nó là dấu hiệu phép đo không chạm được thứ định đo.
Truy ra: `mock.css` khai cầu token ở `:root`, còn công tắc nền tối là class
`body.dark` — hậu duệ của `:root`, nên `var(--t1)` trong khai báo ở `:root`
được thay ngay tại đó, nơi `body.dark` chưa tồn tại.

Học viên chọn nền tối rồi vào /mock: `--t1` trên body đổi thành `#E2E8F0` nhưng
`--mk-t1` kẹt `#16121F` — trang hiện SÁNG, chỉ còn viền `body` tối lòi quanh
mép. Chạm được thật: `(standalone)/layout.tsx` đặt `body.dark` theo lựa chọn đã
lưu. Vá `:root, body`. Đo lại: nền tối ra `fg=226,232,240 / bg=7,9,15`, **0 chỗ
dưới 4.5:1 ở cả hai chế độ**. `lesson_hsa.css` không mắc (dùng token thẳng
trong quy tắc).

### Còn treo
L5–L15 trong `TODO.md`. Kế: **L5** (học viên INSERT được bài học giả vào bảng
`lessons` dùng chung, và bài giả hiện trong trang Kỹ năng của MỌI người).


---

## 31/08/2026 (tiếp) — L5, và một hồi quy của chính tôi đã đẩy lên production

### L5 · bảng `lessons` là bảng DÙNG CHUNG, học viên không được viết vào
`_resolve_lesson_id`, khi không tìm thấy bài, INSERT một dòng vào `lessons` với
`title`/`module` **lấy từ thân request của học viên** và `sort_order` lấy từ
URL. `SkillsView` đọc bảng ấy không lọc theo người dùng, nên dòng giả hiện
trong trang Kỹ năng của MỌI học viên.

Đo trước khi sửa, và chính con số đo quyết định cách sửa: **cả 76 bài của ba
khoá đều đã có `content_json`**, 0 dòng stub, 0 dòng vượt số bài của khoá, và
bản dự phòng nội dung phía client đã bỏ từ 19/08/2026. Bài học viên học được thì
LUÔN có dòng sẵn — nhánh tạo stub sinh ra thời nội dung còn nằm trong tệp JS
364 kB, nay chỉ còn là cái lỗ. `_tim_bai` nay CHỈ ĐỌC; không có bài thì 404.

Ba thứ cùng một họ với nó, đều là "NHẬN thay vì TÍNH", vá luôn:
- **XP** lấy từ `content_json.xp_reward`. Bản cũ kẹp `xpEarned` 0–500 rồi cộng
  thẳng, nên `{"xpEarned": 500}` cho 76 bài là 38.000 XP thay vì 3.800.
- **Tiêu đề trong nhật ký** lấy từ dòng `lessons`, không từ thân request.
- **Kết quả phòng luyện** — xem dưới.

KHÔNG làm: chặn "đánh dấu xong bài chưa mở khoá". Rà cả frontend lẫn backend —
sản phẩm này **không có luật mở khoá tuần tự** ở đâu cả, và kế hoạch học còn cố
ý giao bài theo CHỦ ĐỀ. Dựng một cái khoá chưa từng tồn tại là bịa ra luật mới.

### TÔI ĐẨY MỘT HỒI QUY LÊN `origin/erp` SÁNG NAY
`bo_dap_an` trong `a8f4c5e` cắt `answer` khỏi **cả phần `drill`**, mà
`answerDrill` chấm tại chỗ bằng `norm(val) === norm(q.answer)` — so với
`undefined`. Kết quả: **mọi câu phòng luyện đều sai**, combo không bao giờ nổ,
XP luôn 0, "Chính xác 0%". Tôi không phát hiện lúc kiểm L1 vì phép kiểm hôm ấy
chỉ đi qua bước KIỂM TRA ĐẦU VÀO, không vào phòng luyện.

Cắt đáp án là ĐÚNG — `KIND_DRILL` nằm trong `stats/competency.KIND_TO_SOURCE`,
tức phòng luyện là một nguồn của bản đồ năng lực, nên đáp án của nó phải bí mật
y như bài kiểm tra. Cái sai là chỗ CHẤM. Nay chuyển hẳn sang máy chủ:
- `answerDrill` gọi `/check` từng câu. Nằm gọn trong 470ms hiển thị phản hồi vốn
  đã có, và đường chấm có đệm 60 giây nên từ câu thứ hai là 1ms. Mất mạng giữa
  chừng thì KHÔNG tô đỏ như thể em làm sai — câu vẫn nằm trong `drill.answers`
  nên lúc hoàn thành vẫn chấm được.
- Lúc hoàn thành chỉ gửi `drill.answers` + `seconds`. `cham_phong_luyen` dựng
  lại số câu đúng VÀ chuỗi combo theo THỨ TỰ CÂU TRONG ĐỀ — combo đáng 5 XP mỗi
  nấc, mà trước nay do trình duyệt tự đếm rồi tự khai.
- Màn chúc mừng lấy XP từ phản hồi máy chủ, không từ ước lượng tại chỗ.

### Kiểm
- `lessons/tests.py` 8 → **15 phép kiểm**. Lùi mã cũ: 6/7 phép kiểm mới ĐỎ đúng
  lý do, nói thẳng ra sự việc — *"học viên đẻ được dòng {'id': 1425,
  'sort_order': 9999} vào bảng lessons"*, *"đã ghi một dòng năng lực
  {score: 4.00, max_score: 4.00} dựng từ con số tự khai"*, *"assert 500 == 50"*.
  Phép kiểm thứ bảy (đáp án phòng luyện có lộ không) XANH trên mã cũ vì hàng rào
  ấy đã đi cùng `a8f4c5e` — nói ra chứ không tính vào thành tích hôm nay.
- Trình duyệt thật, phòng luyện: gửi 6 đúng 2 sai → **"6/8 Đúng · 75% Chính xác
  · combo ×3 · +75 XP"**, 8 lời gọi `/check`, thân `/complete` không còn
  `correct`/`maxCombo`. **10/10.**
- Đường GHI (`/complete`) bị chặn bằng route interception; đường `/check` để đi
  thật vì nó chỉ ĐỌC. Kiểm lại Neon sau cả phiên: 76 dòng `lessons`,
  5 dòng `mock_attempts`, 0 dòng đang mở — **không một dòng nào rơi vào**.

### L11 · bốn endpoint đổ 500 vì một chuỗi trên URL
`?limit=abc`, `?weeks=abc`, `?days=abc`, `?weeks=1e9` → 500. Gom về
`common/params.so_nguyen(raw, mặc_định, lo, hi)`, và kéo cả hai nơi đã tự viết
đúng khối `try/except` ấy (`forum/views._paging`, `teaching/sessions`) về dùng
chung — ba bản tự viết là ba bản sẽ trôi khỏi nhau.

`common/tests.py` mới, 13 phép kiểm. Lùi mã cũ: **6 phép kiểm endpoint đỏ bằng
đúng `500 == 200`**; 4 phép kiểm đơn vị đỏ vì mô-đun chưa tồn tại; 3 cái còn lại
XANH cả trên mã cũ và tôi ghi rõ chúng là hàng rào cho phần đã đúng sẵn, không
tính vào thành tích.

**Suýt lặp lại một lỗi cũ.** Lần stash đầu tiên `git stash push -- <đường dẫn>`
IM LẶNG không làm gì vì trong danh sách có một tệp chưa theo dõi
(`common/params.py`), nên "13 passed" ấy là chạy trên mã MỚI — một màu xanh
không chứng minh gì. Đúng cái bẫy `git stash` đã vấp với `grading.py` sáng nay.
Phải `-u`, và phải kiểm `ls` xem tệp đã biến mất thật chưa trước khi tin kết quả.

### Còn treo
L6–L10, L12–L15 trong `TODO.md`.

**L6 cần anh quyết, tôi không tự chọn.** `lesson_progress.quiz_score` dùng
COALESCE (điểm MỚI NHẤT thắng) trong khi `xp_earned` dùng GREATEST (điểm CAO
NHẤT thắng). Bản audit gọi đó là "một bảng hai chính sách", nhưng đọc kỹ thì hai
cột đo hai thứ khác nhau và cả hai chính sách đều có lý:

- **Giữ CAO NHẤT** — sổ điểm mà phạt người ôn lại thì không ai dám ôn lại. Khớp
  với quyết định L7 của anh ("học lại giữ ngày ĐẦU"): làm lại không được xoá quá
  khứ. Và bản đồ năng lực vốn đọc `learning_events` (có suy giảm theo thời gian),
  nên "mới nhất" đã được thể hiện ở đó rồi.
- **Giữ MỚI NHẤT** — điểm phải nói đúng mức nắm bài HIỆN TẠI của em, kể cả khi
  nó tụt.

Tôi nghiêng về **giữ CAO NHẤT**, nhưng đây là quyết định sản phẩm chứ không phải
lỗi có một đáp án đúng, nên tôi dừng ở đây chờ anh. Một lưu ý kèm theo: lệnh
`backfill_learning_events` lấy `score` TỪ `lesson_progress.quiz_score`, nên nếu
hai bảng theo hai luật khác nhau thì chạy nạp lại sẽ kéo `learning_events` về
theo luật của `lesson_progress`.


---

## 31/08/2026 (tiếp) — hai agent soi chéo, và chúng bắt được nhiều thứ của tôi

Gọi hai agent đọc mã: một soi phòng thi thử (L4), một soi khu bài học + phòng
luyện (L5). Tôi tự kiểm lại từng phát hiện bằng chính mã và bằng số đo trên Neon
trước khi vá — bác lại ba chỗ, vá mười một chỗ, và ghi rõ sáu chỗ chưa vá.

### Ba thứ đáng viết vào sổ hơn cả danh sách lỗi

**1. Bộ kiểm của tôi đang GHIM một lỗ hổng lại.** Bốn phép kiểm phòng thi thử
nộp bài KHÔNG qua `/start` rồi khẳng định `counted is True`. Tức là tôi viết
phép kiểm mô tả đúng cái lỗ, và mỗi lần chạy nó xanh, tôi càng tin là mình đã
bịt. Một phép kiểm sai còn tệ hơn không có phép kiểm nào — nó tắt phản xạ nghi
ngờ. Đây là họ hàng gần của bài học "test hồi quy phải đỏ trước" (RULES §18)
nhưng ở chiều ngược lại: đỏ-trước không đủ, phải hỏi thêm *"phép kiểm này đi
đường nào, và đường đó có phải đường tôi định bảo vệ không"*.

**2. Tôi vá đúng chỗ nhưng bỏ sót thứ đã mất.** Với lượt thi cạn giờ, tôi viết
trong docstring: *"dòng ấy chưa mang câu trả lời nào nên không có gì để mất"* —
đúng về câu trả lời, và bỏ sót rằng **đề đã lộ cho em rồi**. Một lý lẽ nghe rất
chắc mà chỉ kiểm được một nửa cái nó khẳng định.

**3. Tôi lại làm hồi quy, và lần này đã đẩy lên production.** `_chuan` trong
`a8f4c5e` giữ dấu `%` trong khi `norm` cũ bỏ nó, kèm một chú thích tự nhận là
"giữ đúng luật engine đang dùng". Tôi tự đo lại trên nội dung thật: 151 câu điền,
**14 câu hỏi "bao nhiêu %" mà đáp án lưu là số trần**. Em gõ `30%` cho câu
*"A chiếm bao nhiêu % tổng?"* thì trước hôm ấy ĐÚNG, sau đó SAI. Chú thích sai
là thứ nguy hiểm ngang mã sai: nó khiến người đọc sau (kể cả tôi) thôi kiểm.

### Vá được (11)
A1 bỏ `/start` là bỏ toàn bộ giới hạn giờ · A2 hết giờ rồi bắt đầu lại vẫn tính
điểm · A3 lỡ F5 mất trắng bài làm · A4 năm `/submit` song song đều tính điểm ·
A5 `x()` vứt rowcount nên hàng rào chỉ nằm trên giấy · A6 cột `counted` khai sai
tệp làm hỏng triển khai trên CSDL rỗng · A7 luật so đáp án bị siết · A8
`OverflowError` với `seconds: 1e400` · A9 engine nuốt im lặng 404 · A10
`quen_dap_an` chưa nơi nào gọi · A11 ba phép kiểm hằng đúng.

Hai thay đổi thiết kế đáng nói:
- **`counted` chốt lúc MỞ, không đợi lúc nộp.** Mở đề là đã thấy đề.
- **Ràng buộc để Postgres giữ, không để mã tự canh.** Hai chỉ mục duy nhất phần
  (`uq_mock_attempt_dang_mo`, `uq_mock_attempt_tinh_diem`), với điều kiện
  `started_at IS NOT NULL` để năm dòng lịch sử nằm ngoài — khớp đúng quyết định
  "không hồi tố" đã ghi trong schema.

### Chưa vá (6) — ghi ra chứ không giấu
A12 (nặng nhất) `/check` vẫn moi được trọn bộ đáp án bằng MỘT request, áp dụng
cho cả bài kiểm tra lẫn phòng luyện · A13 phòng luyện nay bắn 9 request/bài,
một phòng máy dùng chung NAT sẽ đụng trần 1000/giờ · A14 `validate_lesson`
không kiểm khối `drill` · A15 mẫu nhập giáo trình viết `drill.seconds` còn
engine đọc `drill.time_seconds` · A16 đường sửa nội dung lẻ không đối chiếu
`index` với `sort_order` · A17 `/complete` không kiểm ghi danh.

### Kiểm
- Phòng thi thử: 19 phép kiểm (từ 11), có cả hai phép kiểm bắn thẳng vào ràng
  buộc CSDL. Khu bài học: 15. Tham số URL: 13.
- Trình duyệt thật, phòng thi: **12/12** — gồm khôi phục câu trả lời đã lưu và
  lưu tạm lên máy chủ. Phòng luyện: **10/10** sau khi sửa luật chuẩn hoá.
- Đường GHI đều bị chặn bằng route interception; đường `/check` để đi thật vì
  nó chỉ ĐỌC.

### Kế
**A12 trước tiên** — nó làm rỗng ruột chính bản vá quan trọng nhất hôm nay. Rồi
mới tới L6 (đang chờ anh chốt), L7–L15.


---

## A12 (XONG) · `/check` không còn là chỗ moi đáp án miễn phí

Đây là lỗ làm **rỗng ruột chính bản vá quan trọng nhất hôm nay**. Chấm ở máy chủ
mới chỉ bỏ được con số client tự khai; chừng nào `/complete` còn chấm trên CÂU
TRẢ LỜI TRONG THÂN REQUEST thì cả bản vá đi vòng được bằng hai lời gọi:

```
1. POST .../check {"phan":"drill","answers":{"d1":"x", … ,"d8":"x"}}
   → nhận trọn 8 đáp án (sai hết vẫn nhận — đó là chỗ hở)
2. POST /api/lessons/1/complete với đúng 8 đáp án vừa lấy
   → 8/8, 120 XP phòng luyện, một dòng bản đồ năng lực 8/8
```

Vá bằng cột `lesson_progress.answers_json` (§40) và luật **LẦN ĐẦU THẮNG**:
`/check` GHI NHẬN câu trả lời ngay lúc học viên trả lời, `/complete` chấm trên
phần đã ghi nhận chứ không trên thân request. Ai xem đáp án bằng cách gửi bừa
thì con số bừa ấy **chính là bài làm của họ**. Xoá về NULL khi `/complete` xong,
để lần ôn lại bắt đầu từ giấy trắng.

Kèm hai điều chỉnh:
- **Phòng luyện không nhận `answer`** nữa, chỉ nhận đúng/sai. Giao diện của nó
  chỉ cần thế để tô màu. Trả ít hơn mức cần là cách rẻ nhất để một endpoint
  không thành cửa sau.
- **Nút "Bắt đầu" của phòng luyện xoá phần đã ghi nhận** của riêng phần `drill`.
  Nó vốn là nút LÀM LẠI. Bài kiểm tra đầu vào thì KHÔNG được reset — `/check`
  của nó có trả đáp án, cho reset là mở lại đúng cửa vừa bịt.

### Đo, không đoán
Thêm việc ghi nhận làm `/check` chậm hẳn: **810ms mỗi câu drill** (3 câu SQL),
trong một trò bấm giờ 75 giây cho 8 câu. Phát hiện được vì phép kiểm trình duyệt
chỉ bắt được **4/8 lời gọi** — nhịp bấm của kịch bản vượt qua nhịp phản hồi.

Gộp còn một câu SQL (`RETURNING` thay cho SELECT lại, và đệm 60 giây cho
`id_bai`): **810ms → 259ms**, lọt gọn trong 470ms hiển thị phản hồi vốn đã có.

Và chính phép đo trình duyệt lộ ra hệ quả thật của luật lần-đầu-thắng: lần chạy
trước bỏ dở đã khoá `d2` bằng một đáp án sai, nên lần sau gõ đúng vẫn bị tính
sai — **5/8 thay vì 6/8**. Đó là lý do nút "Bắt đầu" phải xoá.

### [ ] A18 · RỦI RO CÒN LẠI, nói thẳng
Xoá được thì cũng dò được: trả lời → xem đúng/sai → bấm "Bắt đầu" → trả lời
khác. Với câu trắc nghiệm 4 lựa chọn thì việc ấy rẻ. Cái đang chặn nó là XP chỉ
cộng ở LẦN HOÀN THÀNH ĐẦU của bài (`existed` trong `CompleteLessonView`) — đủ
cho XP, **chưa đủ cho bản đồ năng lực**, vì `record_event` dùng
`COALESCE(EXCLUDED.score, …)` nên lần chạy sau ghi đè điểm lần trước.

Cách vá đúng: dòng sự kiện phòng luyện chỉ ghi ở LẦN CHẠY ĐẦU của bài, cùng luật
"một lượt vào sổ" mà anh đã chốt cho thi thử. Chưa làm — cần anh xác nhận vì nó
đổi ý nghĩa của con số phòng luyện trên bản đồ năng lực.

### [x] A13 (XONG) · quota đường chấm nay đếm theo NGƯỜI DÙNG, không theo IP
Quota theo IP đúng cho đường ẩn danh, sai cho một trung tâm luyện thi: cả phòng
máy đi ra Internet bằng MỘT địa chỉ NAT, nên 30 em ngồi cùng phòng chia nhau
đúng một quota 1000/giờ. Mà từ hôm nay phòng luyện gọi `/check` 10 lần mỗi bài
(8 câu + 1 lượt chấm bài kiểm tra + 1 lượt xoá khi bắt đầu lại), nên 30 em ×
4 bài/giờ = 1200 — vượt trần. Chạm trần thì bước kiểm tra đầu vào **chặn hẳn**
không cho đi tiếp: cả lớp đứng.

`_PerViewUserThrottle` mới, `user_hour: 600/giờ`, `user_day: 2000/ngày`. Phép
kiểm bắn thẳng vào DANH TÍNH mà bộ đếm dùng (hai em cùng IP phải ra hai bộ đếm;
một em đổi mạng vẫn một bộ đếm) chứ không bắn 1000 request.

Kèm một cái bẫy đã ghi ra thành phép kiểm: đặt `throttle_classes` trên view là
**GHI ĐÈ** mặc định chứ không bổ sung — cùng cái bẫy với `permission_classes`.

### [x] A14 (XONG) · `validate_lesson` nay kiểm cả khối `drill`
Khối này trước nay không được kiểm một chữ, dù XP phòng luyện (tối đa 120, gấp
2,4 lần phần thưởng cả bài) và một trong bốn nguồn của bản đồ năng lực đều dựng
từ nó. Ba cách nó hỏng câm: thiếu `id` (câu bị lọc khỏi bảng đáp án, học viên
thấy mọi câu hiện *"Chưa chấm được câu này — vẫn tính khi bạn hoàn thành bài"*,
mà câu an ủi ấy là nói dối) · `id` trùng · sai tên khoá thời lượng.

Đo trước khi siết: **0/76 bài đang có bị bộ kiểm mới chặn** — có phép kiểm hồi
quy chạy trên chính 76 bài thật, để lần sau siết thêm cũng không ai chặn nhầm
nội dung đang chạy.

### [x] A15 (XONG) · mẫu nhập giáo trình chính thức ghi sai tên khoá
`docs/NHAP_GIAO_TRINH.md` và `docs/mau_nhap_giao_trinh.json` viết
`drill.seconds`, engine đọc `drill.time_seconds`. Bài nhập ĐÚNG theo mẫu chính
thức sẽ có đồng hồ phòng luyện chạy mãi không hết giờ (`NaN <= 0` luôn sai). Đã
sửa cả hai tệp, và bộ kiểm nay từ chối `seconds` với thông báo nói rõ vì sao.

### [x] A16 (XONG) · đường sửa nội dung lẻ không đối chiếu `index` với `sort_order`
Engine đọc `index` để biết mình là bài số mấy rồi gọi `/complete` và `/check`
theo số đó. Dán mẫu có `"index": 28` vào ô nội dung của bài đang ở
`sort_order = 5`: em học bài 5 nhưng tiến độ ghi sang bài 28, và bài 5 được chấm
bằng đáp án của bài 28. Đường nhập cả khoá ép `sort_order = index` nên không hở;
chỉ đường sửa lẻ nhận hai con số rồi để chúng lệch. Đo: 0/76 bài đang lệch.

### [x] A17 · KHÔNG PHẢI LỖ HỔNG — tôi bác lại agent
Agent báo `/complete` không kiểm ghi danh nên "hai request là đọc được nội dung
khoá chưa ghi danh". Đúng về cơ chế, sai về hệ quả: **ghi danh là việc tự làm
được**, `CourseEnrollView` mở cho chính học viên. Hàng rào ghi danh chưa bao giờ
là ranh giới phân quyền — nó là hàng rào TOÀN VẸN DỮ LIỆU (đừng để tiến độ rơi
vào một khoá không có dòng ghi danh). Dựng thêm rào ở `/complete` chỉ làm hỏng
đúng bản vá L2 hôm nay, cái sinh ra để TỰ ghi danh.


---

## 31/08/2026 (tiếp) — L9 và L10: hai lỗi nhỏ, hai con số thật đổi

### [x] L9 (XONG) · Bài học #2 và quiz ôn tập #2 bị đếm thành MỘT hoạt động
`stats/competency` đếm "số hoạt động khác nhau" bằng `ref_id` TRẦN. Nhưng mỗi
loại tham chiếu có KHÔNG GIAN ID RIÊNG: bài học #2 và quiz ôn tập #2 chỉ trùng
số thứ tự trong CSDL. Gộp nhầm làm `confidence` tụt xuống dưới `MIN_ACTIVITIES`,
và ô chủ đề hiện **"chưa đủ dữ liệu"** thay vì một con số có thật.

Đo trên dữ liệu thật trước khi sửa — va chạm CÓ THẬT, không phải giả định:

```
user 9, ref_id '2' → ['lesson', 'quiz']
user 7, ref_id '3' → ['lesson', 'mock_attempt']
```

Và tác động đo được, trên chính em id 9, chủ đề **"Số học"**:

| | trước | sau |
|---|---|---|
| mastery | `None` | **22** |
| confidence | 1 | 2 |
| status | `low_data` | `ok` |

Khoá nay là CẶP `(ref_type, ref_id)`. Cặp này vẫn giữ đúng chỗ CỐ Ý gộp: sự kiện
`lesson` và `drill` của cùng một bài dùng chung cả `ref_type` lẫn `ref_id` nên
vẫn là một lần chạm vào chủ đề — có phép kiểm riêng ghim điều đó lại.

### [x] L10 (XONG) · Ngày thi HÔM NAY bị coi là "chưa đặt mốc thi"
`days_to_exam` trả `0` cho ngày thi hôm nay, và `0` là falsy trong Python. Hai
nơi tiêu thụ dùng `if days`, nên **đúng cái ngày cần siết nhất thì hệ NỚI RA**:

- còn 1 ngày → kế hoạch 1 tuần, chế độ luyện đề dày;
- còn 0 ngày → kế hoạch **12 tuần**, chế độ thư thả, như thể chưa đặt mốc thi.

Phép kiểm đi qua đường THẬT (`stats.plan.generate`) chứ không kiểm lại một biểu
thức tự viết trong chính phép kiểm — RULES §19. Lùi mã cũ, nó đỏ đúng câu:
*"còn 0 ngày mà kế hoạch dựng 12 tuần"*, và hai tham số còn lại XANH cả trên mã
cũ, đúng như phải thế (chỉ `days = 0` mới rơi vào nhánh sai).

Frontend không mắc lỗi này — nó đã dùng `!= null` ở cả năm chỗ, và còn phân biệt
"đã khảo sát nhưng mốc đã trôi qua" để dẫn thẳng vào Cài đặt.


---

## 31/08/2026 (tiếp) — L7 và L8, hai quyết định anh đã chốt

### [x] L7 (XONG) · Học lại bài cũ GIỮ NGÀY ĐẦU
`learning_events` có HAI cột thời gian và chúng trả lời HAI câu khác nhau. Bản
cũ ghi đè cả hai khi học lại, nên chúng nói cùng một câu — và câu đó sai một
nửa số nơi đọc.

- **`event_date` nay GIỮ NGÀY ĐẦU** (`LEAST(...)`). Nó là trục thời gian của
  đường cong tiến bộ và của "chỉ tiêu tuần". Ghi đè thẳng thì ôn lại một bài cũ
  ĐỔI HÌNH DẠNG tuần trước: điểm biến khỏi chỗ nó từng ở, chỉ tiêu tuần nhích
  lên trong khi nhiệm vụ ngày vẫn 0/1.
- **`occurred_at` vẫn cập nhật.** Nó trả lời "lần gần nhất em chạm vào việc này".

Đổi cột thì phải đổi cả bên đọc — hai nơi:
- `teaching/reports._last_activity` chuyển sang `MAX(occurred_at)`. Giảng viên
  nhìn cột này để biết em nào mất hút; hỏi sai câu thì một em ôn bài hôm nay
  vẫn hiện là bặt tin từ tháng trước.
- `stats/competency._events` chuyển sang `occurred_at::date`. Phép suy giảm hỏi
  "kết quả này ĐO ĐƯỢC bao lâu rồi"; dùng ngày đầu là đánh tụt trọng số của
  đúng phần em vừa ôn.

Lùi mã cũ, phép kiểm đỏ đúng câu: *"ôn lại hôm nay mà ngày của lần đầu bị đẩy
sang 2026-08-31"*. Phép kiểm thứ hai ("bảng của giảng viên đọc lần gần nhất")
XANH cả trên mã cũ — nói ra chứ không tính vào thành tích: trên mã cũ hai cột
trùng nhau nên nó chưa phân biệt được gì; nó là hàng rào cho tương lai.

### [x] L8 (XONG) · Điểm đề thi thử GIỮ trong số hiện, TÁCH khỏi quyết định
Đề thi thử chỉ chia theo HỢP PHẦN, không biết câu nào thuộc chủ đề nào — chính
chú thích trong `competency.py` đã ghi *"dùng để chấm nhưng KHÔNG được tính là
bằng chứng về chủ đề"*, nhưng mã thì rải đều 25% của nó vào MỌI ô chủ đề.

Đo trên ba học viên thật, trước khi sửa:

| học viên · chủ đề | số hiện (trộn) | chỉ bằng chứng chủ đề | chênh |
|---|---|---|---|
| id 9 · Đại số | 42 | **62** | 20 |
| id 9 · Số học | 22 | 33 | 11 |
| id 7 · Số học | 31 | 37 | 6 |

Và hệ quả đo được trên lịch học:

```
mã cũ  → user 9: xếp lịch ôn ['Số học', 'Đại số']
mã mới → user 9: xếp lịch ôn ['Số học']
```

"Đại số" biến khỏi danh sách vì 62 đã trên ngưỡng 60 — đúng 17 buổi "Ôn lại Đại
số" mà bản audit đo được.

Anh chốt "giữ nhưng tách hiển thị", nên:
- `mastery` GIỮ NGUYÊN cách tính (vẫn gộp điểm đề) — đó là con số lớn trên ô.
- `masteryTopic` mới, chỉ từ bằng chứng thật của chủ đề.
- Mọi QUYẾT ĐỊNH (`_weak_topics`, ưu tiên cắt bài) chuyển sang `masteryTopic`.
- Ô năng lực hiện thêm một dòng khi hai số khác nhau: *"Riêng chủ đề 62% · số
  lớn đã gộp điểm đề thi thử"*. Im lặng thì con số 42 trông như một lời phán về
  Đại số.

Phép kiểm dựng kịch bản hai số nằm HAI BÊN ngưỡng, và có một assert riêng canh
đúng điều đó — lần đầu chạy nó bắt được chính tôi đặt số sai (62 vs ngưỡng 60,
chưa qua bên kia). Lùi mã cũ, nó đỏ đúng hệ quả: *"chủ đề làm 85% vẫn bị xếp
lịch ôn vì điểm đề kéo xuống"*.


---

## 31/08/2026 (tiếp) — L13, L14, L15: ba con số nói dối trên màn hình

### [x] L13 (XONG) · Xem lại quiz ôn tập hiện MÃ lựa chọn và không bao giờ hiện lời giải
Hai lỗi chồng nhau trong cùng một màn hình:

- `review_quiz.js` in thẳng `your_answer`/`correct_answer`, vốn là `o1`/`o2`.
  Màn hình hiện **"Bạn chọn: o1 — Đáp án đúng: o2"** — thứ không ai đọc được,
  kể cả người vừa làm bài xong. Nay máy chủ trả kèm `*_text` và giao diện in chữ
  (vẫn giữ đường lùi về mã cho quiz sinh TRƯỚC bản vá).
- `explanation` luôn `None` với mọi câu HSA: dạng HSA để lời giải ở **cấp câu
  hỏi** (`explain`), còn `_add_hsa` vứt nó đi và phần chấm chỉ tìm
  `option.explanation` (dạng pe_test). Nghĩa là phần xem lại của quiz ôn tập
  **chưa bao giờ giải thích gì**. Nay `explain` được giữ qua kho câu hỏi và
  được đọc trước, rồi mới tới lời giải cấp lựa chọn.

### [x] L14 (XONG) · Một luật mở quiz, ba phát biểu
Không phải hai như bản audit nêu — rà ra **ba**:

1. `quizzes/views` kiểm số **CÂU HỎI** trong kho (`len(pool) < 5`);
2. thông báo lỗi của chính nó nói "hoàn thành ít nhất 5 **BÀI**";
3. `stats/ReviewQuizStatusView` gác bằng **CHUỖI NGÀY** (`streak >= 5`) — thứ
   không liên quan gì tới việc em đã học đủ chưa, và endpoint ấy **không có nơi
   nào gọi** (rà cả frontend: 0 kết quả).

Câu (2) sai theo cả hai chiều: một bài có 8 câu là đủ, còn 5 bài mỗi bài một câu
điền thì vẫn không đủ. Câu (3) là luật KHÔNG được thi hành — chuỗi 30 ngày mà
chưa xong bài nào thì kho vẫn rỗng và `GenerateQuizView` vẫn từ chối.

Rút `pool_cau_hoi(uid, course_id)` thành nơi DUY NHẤT trả lời câu hỏi ấy. Thông
báo nay nói đúng thứ đang kiểm và nói em đang có bao nhiêu. `ReviewQuizStatusView`
hỏi lại chính nơi giữ luật.

Đáng nói: **một phép kiểm cũ đang GHIM câu thông báo sai lại** —
`assert 'ít nhất 5 bài' in error`. Đúng cái bẫy RULES §19 vừa ghi hôm nay, gặp
lại sau vài giờ.

**Một hệ quả tôi bỏ sót và bộ kiểm bắt được.** Đổi hình dạng phản hồi của
`ReviewQuizStatusView` làm **5 phép kiểm cũ đỏ**. Đọc kỹ thì chúng chia hai
loại: ba cái khẳng định thẳng luật `streak >= 5` (luật vừa bị gỡ — sửa thành
phép kiểm cho luật thật), và hai cái thật ra đang kiểm CHUỖI NGÀY, chỉ mượn
trường `is_unlocked` làm câu khẳng định thêm (bỏ đúng dòng ấy, giữ nguyên phần
kiểm chuỗi). `streak` được trả lại vào phản hồi: nó là con số thật và miễn phí;
thứ bị bỏ là việc DÙNG nó làm điều kiện mở quiz.

### [x] L15 (XONG) · Điểm sao 5.0 trên mọi trang khoá là con số BỊA
Đo: `courses.rating` = **5.0 cho cả ba khoá**, `course_ratings` **rỗng 0 dòng**.
`CourseRatingView` tính đúng con số thật nhưng **không nơi nào gọi**. Nghĩa là
mọi trang khoá và mọi thẻ khoá đang khoe "5.0 ★" trong khi chưa một ai chấm.

Nay ba đường đọc khoá đều lấy trung bình THẬT từ `course_ratings`, kèm số lượt.
Chưa ai đánh giá thì trả `NULL`, và màn hình nói **"Chưa có đánh giá"** thay vì
một con số bịa — cùng luật với "không biết điểm khác điểm 100 vì người dùng nói
thế" ở `CompleteLessonView`.

Đo lại sau khi vá: `rating = None, rating_count = 0` cho cả ba khoá — đúng sự
thật. Lùi mã cũ, phép kiểm đỏ đúng câu *"chưa ai đánh giá mà vẫn hiện 5.0 sao"*
và *"assert 5.0 == 3.0"*.

**Bộ kiểm backend xanh mà màn hình vẫn nói dối.** Phép kiểm trình duyệt bắt được
đường đọc THỨ TƯ tôi bỏ sót: `CourseDetailView` (`/api/courses/<id>`) vẫn trả
`c.rating` = 5.0, nên trang chi tiết khoá vẫn khoe "5" trong khi ba đường kia đã
trả `None`. Phép kiểm cũ của tôi chỉ đi qua `/api/courses` — nó đúng, nhưng nó
không phải đường mà trang chi tiết dùng (RULES §19: *phép kiểm phải đi đúng
đường mà nó nhận là đang bảo vệ*).

Nay có một phép kiểm duyệt CẢ BỐN đường: `/api/courses` ·
`/api/courses-enrolled` · `/api/courses/<id>` · `/api/public/courses`. Một đường
quên là một màn hình nói dối.

**Một lỗi của chính tôi trong lúc đo**: kịch bản kiểm viết
`c.get('rating_count') or c.get('ratingCount')` — mà `0 or None` là `None`, nên
tôi suýt báo "rating_count không có". Đúng họ falsy-zero với L10 vừa vá xong
cùng phiên. Đo lại bằng truy cập thẳng khoá.

### [x] L12 (một phần) · Mục kế hoạch bị tick bởi việc không phải của nó

Hai chỗ, cùng một kiểu sai — một hoạt động tick nhiều thứ hơn phần của nó:

**(a) Mốc sàn lấy TUẦN ĐẦU thay vì lúc SINH kế hoạch.** Kế hoạch lập hôm thứ Tư
nhưng bắt đầu từ thứ Hai cùng tuần thì hai ngày đầu tuần nằm TRƯỚC lúc nó tồn
tại — mà bản cũ vẫn cho chúng tick, nên kế hoạch vừa lập ra đã có sẵn mục "đã
xong". Nay `_moc_san(rows, generated_at)`, và cả bản đọc CHO CẢ LỚP
(`do_cham_theo_hoc_vien`) dùng chung đúng hàm ấy — hai bản chép tay là hai bản
sẽ trôi khỏi nhau, đúng lỗi T62 vừa vá.

**(b) Học một bài mới tick luôn một buổi "Ôn lại chủ đề".** `topic_dates` gom
MỌI sự kiện có `topic`, kể cả `lesson` và `drill`. Nên MỘT lần hoàn thành bài
tick xong HAI mục: mục "học bài N" (qua `done_lessons`) và mục "Ôn lại X" (qua
`topic_dates`) — trong khi em chỉ làm một việc. Phòng luyện cùng lý do: nó sinh
ra từ đúng lần hoàn thành ấy, đếm nó là đếm lần thứ ba.

Nay `KHONG_TINH_LA_ON_LAI = (KIND_LESSON, KIND_DRILL)`. Còn lại vẫn tính là ôn:
quiz ôn tập (đúng tên nó), điểm hợp phần đề thi thử, bài tập giảng viên chấm —
có một phép kiểm riêng ghim điều đó, để siết mà không siết luôn việc ôn thật.

**KHÔNG một con số nào của học viên hiện tại đổi.** Đo trước/sau trên cả ba kế
hoạch đang hoạt động: `user 7 lag=2`, `user 9 lag=4`, `user 12 lag=14`, totals y
hệt. Bản vá đúng theo cấu trúc nhưng chưa chạm ai — ba kế hoạch ấy tình cờ không
rơi vào hai trường hợp trên. Nói ra chứ không khoe một tác động không có.

Phép kiểm phải TỰ DỰNG kịch bản, và bản đầu của nó sụp vì hôm nay đúng là thứ
Hai (mốc "thứ Hai" trùng "hôm nay" nên không còn khoảng cách nào để đo). Đã dựng
mốc tường minh thay vì suy từ ngày trong tuần.

**CÒN LẠI của L12, chưa làm:** `totals.done` đếm cả mục đã xong ở TUẦN ĐÃ QUA,
nhưng phần `weeks` lọc `k >= today_key` nên chúng không hiện ở đâu cả. Chú thích
ngay trên đó viết *"Không giấu đi: nhìn thấy việc đã tick xong trong tuần này
chính là phần thưởng của cả tuần"*, còn khối ngay dưới thì giấu. Hai chú thích
mâu thuẫn nhau trong mười dòng. Sửa đúng là cho mục đã xong hiện ở tuần HOÀN
THÀNH (kẹp về tuần này nếu sớm hơn) chứ không phải tuần dự kiến — nhưng
`study_plan_items` chưa có cột thời điểm hoàn thành, nên cần thêm cột hoặc suy
từ `learning_events`. Chưa làm trong phiên này.


---

## Nghiên cứu 31/08/2026 — bản đồ năng lực đang hứa nhiều hơn nó đo được

Tra tài liệu ngoài rồi soi lại chính mô hình mình đang cho là ổn. Hai kết luận,
cả hai đều có số đo trên dữ liệu thật của pe_hsa.

### 1. Hằng số `HALF_LIFE_DAYS = 45` là con số ĐƯỢC GÕ, không phải được chọn

Chú thích của nó chỉ MÔ TẢ — *"sau ngần này ngày, một kết quả chỉ còn nặng một
nửa"* — chứ không biện minh: không nguồn, không phép đo, không thí nghiệm.

Đo độ nhạy trên cả bốn học viên có dữ liệu, đổi chu kỳ bán rã từ 7 ngày tới
"không suy giảm":

```
user   chủ đề            7     14     30     45     90    180   ∞
7      Số học           40     35     32     31     30     29    29   ← chênh 11
9      Số học           22     22     22     22     22     22    22   ← chênh 0
9      Đại số           42     42     42     42     42     42    42   ← chênh 0
```

Hai điều đọc ra:

- **Với em id 9 nó không làm gì cả.** Mọi bằng chứng của em cùng 7 ngày tuổi,
  nên trọng số bằng nhau và con số y hệt ở mọi chu kỳ. Câu "có suy giảm theo
  thời gian" trong tài liệu, với em ấy, là một lời hứa rỗng.
- **Với em id 7 nó đổi 11 điểm** (40 ↔ 29) — chỉ vì hai bằng chứng cách nhau 5
  và 18 ngày. Một hằng số không ai chọn đang quyết định 11 điểm trên bản đồ mà
  giảng viên nhìn vào để xếp lịch ôn.

Chưa đổi con số: đổi 45 thành một con số gõ đại khác thì không khá hơn. Cái phải
đổi là CHÚ THÍCH — nói thẳng nó chưa được kiểm chứng và nó đáng bao nhiêu điểm.

### 2. Mô hình hiện tại KHÔNG biết độ khó, và chưa đủ người để biết

Rà toàn bộ nội dung: một câu hỏi chỉ có `answer, explain, id, options, question,
type`. **Không câu nào mang tín hiệu độ khó.** (Trường `difficulty` duy nhất
trong repo là học viên tự ghi "hôm nay thấy khó/dễ" trong nhật ký — không liên
quan tới câu hỏi.)

Nghĩa là hai em cùng đúng 8/10 thì ra cùng một con số, dù một em làm toàn câu dễ
và em kia làm toàn câu khó. Đây đúng là *"Proportion Correct method"* mà tài
liệu về Elo trong giáo dục nói là kém hơn Elo ở mẫu nhỏ.

**Nhưng đừng vội xây Elo.** Tra tiếp về ngưỡng mẫu: Elo cần **ít nhất 100 học
viên** mới cho ước lượng độ khó dùng được, và **200–250** mới đáng tin. pe_hsa
đang có **5 học viên**. Xây bây giờ là dựng một mô hình phức tạp trên dữ liệu
không nuôi nổi nó — nó sẽ cho ra những con số trông tinh vi hơn mà kém đúng hơn.

Kèm một cảnh báo trong tài liệu đáng nhớ: khi hệ thống vừa CHỌN câu theo rating
vừa CẬP NHẬT rating, phương sai phình lên theo thời gian và rating **không hội
tụ**. Nếu sau này làm adaptive thì phải tách hai việc ấy.

### [ ] N1 · Việc phải làm khi đủ người (ngưỡng: 100 học viên hoạt động)
Ước lượng độ khó từng câu bằng Elo, rồi chấm năng lực theo độ khó thay vì theo
tỉ lệ đúng trần. Trước ngưỡng đó thì KHÔNG làm — và lý do đã ghi ở trên để lần
sau không ai phải tra lại.

### [ ] N2 · Việc làm được ngay, không cần thêm người
Chú thích của `HALF_LIFE_DAYS` phải nói ra: (a) con số này chưa được kiểm chứng,
(b) đo 31/08/2026 nó đáng tới 11 điểm với một học viên thật, (c) nó là trọng số
theo ĐỘ MỚI CỦA BẰNG CHỨNG, không phải mô hình quên. Ba thứ đó khác nhau, và
gộp chúng lại là cách con số 45 sống sót mà không ai hỏi.

**Nguồn:**
- [Applications of the Elo rating system in adaptive educational systems](https://www.sciencedirect.com/science/article/abs/pii/S036013151630080X)
- [Keeping Elo alive: Evaluating and improving measurement properties of learning systems based on Elo ratings](https://pmc.ncbi.nlm.nih.gov/articles/PMC12784335/)
- [Adaptive Assessment and Content Recommendation in Online Programming Courses: On the Use of Elo-rating](https://dl.acm.org/doi/fullHtml/10.1145/3511886)
- [On-the-fly parameter estimation based on item response theory in item-based adaptive learning systems](https://link.springer.com/article/10.3758/s13428-022-01953-x)
- [The FSRS Algorithm (open-spaced-repetition wiki)](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm)


---

## Audit chéo đợt hai 01/09/2026 — hai agent soi 7 commit của cả phiên

Một agent soi BẢO MẬT, một soi TÍNH ĐÚNG ĐẮN. Cái nặng nhất của cả hai đều là
hồi quy của chính những bản vá tôi vừa viết trong phiên này.

### [x] B1 (VÁ) · NẶNG NHẤT — nộp muộn TRẢ LẠI lượt tính điểm, kèm trọn đáp án
`/submit` ghi `counted = tinh_diem`, mà `tinh_diem` là FALSE khi nộp muộn. Nên
nộp muộn **HẠ cờ xuống FALSE**, dòng rơi khỏi `uq_mock_attempt_tinh_diem`, và
`_da_dung_luot_tinh_diem` lại trả False — lượt tính điểm được cấp lại. Cộng với
việc phản hồi trả đáp án cho mọi câu ĐÃ ĐIỀN (kể cả điền rác):

```
/start → chờ quá giờ → /submit rác (nhận trọn đáp án VÀ lấy lại lượt)
       → /start → /submit đúng → 9/9 + 100 XP
```

Đường `/start` (`_dong_luot_qua_gio`) đã cố ý KHÔNG đụng cột ấy ngay từ đầu.
**Hai đường, hai luật, và đường lỏng hơn là đường học viên gọi được trực tiếp.**
Đúng cái lớp lỗi tôi đi vá cả phiên, lần này trong mã của chính mình.

Vá: `counted` chốt lúc `/start` và KHÔNG BAO GIỜ đổi sau đó — đúng như docstring
đầu tệp vẫn hứa.

### [x] B2 (VÁ) · NẶNG — `/check` GHI mà `ghi_nhan` không điền `course_id`
Trước A12, đường DUY NHẤT tạo dòng `lesson_progress` là `/complete`, và nó luôn
điền `course_id`. Từ khi `/check` ghi nhận câu trả lời, đường này chèn TRƯỚC —
để trống thì lần chèn đầu không có `course_id`, mọi lần sau rơi vào `DO UPDATE`
(không đụng cột ấy), và cột ở **NULL vĩnh viễn**.

Bảy chỗ đọc lọc theo `lp.course_id`, nặng nhất là câu tính lại `enrollments`
NGAY SAU khi hoàn thành bài → **tiến độ đứng ở 0%** cho mọi học viên từ nay.

Đáng sợ nhất: `learning_events` KHÔNG hỏng (nó lấy `course_id` từ thân request),
nên bản đồ năng lực vẫn đúng — hai màn hình cùng nói về một em sẽ lệch nhau mà
không ai đoán được vì sao.

Đo: **0 dòng đã hỏng** trên Neon — bắt kịp trước khi có ai chạm vào. Vá cả hai
đầu: `ghi_nhan` điền `course_id` bằng truy vấn con, và `/complete` thêm
`course_id = COALESCE(cũ, mới)` để dòng hỏng lành lại ở lần hoàn thành kế tiếp.

### [x] B3 (VÁ) · NẶNG — `/complete` tự mở khoá, vòng thứ hai ghi đè điểm
Đúng lỗ mà A12 sinh ra để bịt, chỉ dịch đi một bước. `/check` trả đáp án cho câu
đã trả lời (phần xem lại cần), còn `/complete` XOÁ khoá "lần đầu thắng" để lần
ôn sau bắt đầu từ giấy trắng. Hai thứ cộng lại:

```
/check bừa (moi trọn đáp án) → /complete (điểm 0 vào sổ, khoá bị xoá)
                             → /complete lại bằng bộ vừa moi → 100 GHI ĐÈ số 0
```

**Giữ điểm CAO NHẤT cũng không chặn được**, vì 0 → 100 là đi LÊN. Chỉ "lần đầu
thắng" mới đóng. Đảo thứ tự `COALESCE`: ô đã có số thì giữ, ô trống thì điền.

Kèm: dòng sự kiện nay lấy đúng con số VỪA VÀO SỔ (đọc lại sau khi ghi) chứ không
lấy con số vừa chấm — nếu không thì `lesson_progress` giữ 0 còn `learning_events`
bị nâng lên 100, và đường vòng vẫn nâng được ô năng lực.

**Điều này quyết định luôn L6 — nhưng bằng ép buộc, không phải bằng sở thích.**
Tôi từng nghiêng về "giữ điểm cao nhất"; phép đo cho thấy nó không đóng được lỗ.

### [x] B4 (VÁ) · `answers_json` phình không trần — một tài khoản giết một worker
`ghi_nhan` GỘP THÊM chứ không thay thế (luật lần-đầu-thắng chỉ giữ khoá đã có,
khoá mới luôn được nhận), nên mỗi request nạp thêm tới 2,5 MB khoá rác vào ĐÚNG
MỘT dòng. Sau vài chục lượt, mỗi lần chấm kéo cả trăm MB từ Neon về rồi giải mã
JSON trong tiến trình — instance Render 512 MB hết bộ nhớ. Không cần quyền gì.

Vá: `kep_tra_loi` — trần 200 câu, 500 ký tự mỗi câu trả lời, 64 ký tự mỗi khoá.
Cắt lặng lẽ chứ không từ chối cả request (đừng để học viên mất bài).

### [x] B5 (VÁ) · `/save` không kiểm hạn giờ — đường vòng TỐT HƠN đường trung thực
Hết giờ → tra cứu vài ngày → `/save` bộ đáp án hoàn hảo → `/start` →
`_dong_luot_qua_gio` chấm chính bộ ấy và GIỮ NGUYÊN `counted` → 9/9 vào sổ.
Trong khi nộp muộn tử tế qua `/submit` thì không được tính điểm. Nay `/save` sau
chuông trả 409.

### [x] B6 (VÁ) · `teaching/reports` là bản song sinh mà tôi bỏ quên
Docstring của nó tự nhận *"lấy trực tiếp từ module kia (import), nên không thể
lệch nhau"*. Hai bản vá hôm qua (L7 đọc `occurred_at`; L9 đếm theo cặp
`(ref_type, ref_id)`) chỉ áp ở `stats/competency`, và bản này lệch ngay: cùng
một em, màn hình của em và bảng của giảng viên ra hai con số — đúng lớp lỗi T62
mà tôi đã vá một lần rồi.

Đã sửa cả mã lẫn docstring: **nhập chung HẰNG SỐ không bảo đảm chung LUẬT**;
phần luật nằm trong câu SQL và trong vòng duyệt thì vẫn phải sửa hai chỗ.

### [x] B7 (VÁ) · Câu chữ tự mâu thuẫn in thẳng cho học viên
Chủ đề được chọn bằng `masteryTopic` (L8) nhưng lý do in `mastery`. Với chủ đề có
bằng chứng 45 mà điểm đề 100: **"Điểm thành thạo đang 62/100, dưới ngưỡng 60."**

### [x] B8 (VÁ) · Chú thích nói một luật mà truy vấn không thi hành
`KHONG_TINH_LA_ON_LAI` bảo "điểm hợp phần đề thi thử và bài tập chấm tay vẫn
tính là ôn" — nhưng hai đường đọc chỉ lấy `[lesson, mock, review_quiz]`. Đã sửa
chú thích cho đúng, và ghi ra hệ quả đang chấp nhận (mục "Ôn lại" chỉ tick được
bằng quiz ôn tập). §20 lần thứ hai trong hai ngày.

### [x] B9 (VÁ) · Endpoint chấm mất hẳn trần theo MÁY
Đặt `throttle_classes` là GHI ĐÈ chứ không bổ sung. Bản đầu chỉ để hai lớp theo
người dùng, nên một máy giữ N tài khoản đẩy được N × 600 request/giờ. Nay giữ cả
bốn lớp. **KHÔNG phải lỗ xác thực** — agent kiểm đúng: `IsAuthenticated` chạy
TRƯỚC tầng throttle nên request ẩn danh nhận 401.

### [x] B10 (VÁ) · `SELECT c.*` cộng alias `rating` = hai cột cùng tên
`dict(zip(cols, row))` ra đúng chỉ nhờ thứ tự cột. Đúng vì may, không vì hàng
rào nào. Đã liệt kê cột tường minh.

### [x] B11 (VÁ) · Hai phép kiểm hằng đúng
`test_duong_cham_dung_quota_theo_nguoi_dung` chỉ so danh sách LỚP — chép lại
đúng dòng khai báo, nên nó xanh cả khi thiếu `user_day` trong
`DEFAULT_THROTTLE_RATES` (thứ làm view ném `ImproperlyConfigured` ở MỌI request).
Nay KHỞI TẠO từng lớp và đọc `rate`. Và
`test_luu_tam_khong_phai_cua_sau_de_lay_dap_an` dùng danh sách khoá cứng nên đỏ
ngay khi thêm một trường vô hại — viết lại theo Ý ĐỊNH (không rò khoá chấm điểm).

### [ ] B12 · CHƯA VÁ · `LocMemCache` theo tiến trình, mà Render chạy 2 worker
`config/settings.py` không khai `CACHES` → LocMemCache, sống trong bộ nhớ TỪNG
tiến trình. Ba hệ quả:
- `quen_dap_an` (bản vá A10 hôm qua) chỉ xoá đệm của MỘT worker — worker kia vẫn
  chấm bằng đáp án CŨ tới hết 60 giây TTL. Bản vá ấy đang có tác dụng một nửa.
- `quen_ghi_danh` y hệt: huỷ ghi danh xong vẫn đọc được nội dung thêm một phút.
- **Trần request thực tế GẤP ĐÔI con số cấu hình**: mỗi worker đếm riêng, nên
  `user_hour = 600` thực tế là ~1200/giờ/người.

Đây chính là hạng mục Redis (A3) đang chờ anh. Ba hệ quả trên là lý do cụ thể.

### [ ] B13 · CHƯA VÁ · phòng luyện vẫn là máy dò đáp án (A18 cũ, có sửa lại)
`reset` cho thử vô hạn; trắc nghiệm 4 lựa chọn thì ≤ 4 lượt/câu là biết chắc.
**Tôi từng ghi "XP đã chặn" — SAI**: `existed` chỉ chặn lần thứ HAI, còn lần thứ
nhất (lần duy nhất được tính) đã là 120 XP + ô năng lực 8/8 do dò ra. Cần anh
chốt hướng, như đã hỏi.

### [ ] B14 · CHƯA VÁ · `CREATE INDEX ON mock_attempts` chạy trước `CREATE TABLE`
Nằm ở `legacy_schema.sql:780`, NGOÀI dải commit của phiên (có từ trước). Nhưng
`bootstrap_schema` nay nằm trong `buildCommand` của Render và `raise` ở câu lệnh
đầu tiên hỏng, nên trên một CSDL RỖNG (staging, khôi phục sau sự cố) nó làm
**chết cả lần triển khai**. Chuyển hai dòng ấy sang `mockexam_schema.sql`.

### [ ] B15 · CHƯA VÁ · `/complete` bỏ qua phần phòng luyện ĐÃ ghi nhận
`_cham_drill` trả `None` ngay khi thân request thiếu khoá `drill`, TRƯỚC khi
chạm tới `answers_json`. Em làm đủ 8 câu rồi tải lại trang trước khi bấm Hoàn
thành → máy chủ có sẵn bài làm nhưng không dùng, rồi `xoa_ghi_nhan` xoá luôn.
Không phải hồi quy, nhưng đúng là điều A12 tuyên bố đã sửa.

### [ ] B16 · CHƯA VÁ · `_moc_san` chỉ chính xác tới NGÀY
Kế hoạch sinh 00:30 thì việc làm lúc 00:10 cùng ngày vẫn tick. Bất biến trong
docstring đúng ở mức ngày, không đúng ở mức giờ.

### Những chỗ agent kiểm mà KHÔNG có vấn đề (ghi lại để khỏi tra lại)
- **SQL injection**: không có. Mọi câu SQL mới đều tham số hoá; `CHU_DIEM_SAO`
  là hằng tĩnh toàn chú thích `--`, không giá trị người dùng nào chạm vào.
- **IDOR**: không có. `/start`, `/save`, `/submit`, `/mock-attempts` đều lấy
  `request.user.id` từ token, không nhận `user_id` từ thân request hay URL.
- **Phép gộp `jsonb` của `ghi_nhan`**: ĐÚNG "lần đầu thắng" ở cấp câu — toán
  hạng phải của `||` thắng, và bộ CŨ đứng bên phải trong phép gộp con.
- **Dòng `status='in_progress'`**: cả 12 chỗ đọc `lesson_progress` đều lọc
  `status='completed'`, nên nó thật sự vô hình với chúng.
- **Đua tranh trên `mock_attempts`**: hai chỉ mục duy nhất chặn được ở tầng CSDL.
- **Rò bí mật trong log**: không có dòng nào in token, mật khẩu, hay đáp án.
- **Test ghi rò ra Neon**: không có. (Nhưng ba phép kiểm mới chạy
  `DELETE FROM course_ratings` của một khoá THẬT — an toàn CHỈ nhờ cuộn lại.)


---

## 01/09/2026 — bốn việc treo + bộ tài liệu kiến trúc

Anh chốt bốn việc treo và chọn "Markdown + Mermaid trong repo" cho tài liệu.

### [x] B13 (XONG) · Phòng luyện: LƯỢT ĐẦU vào sổ
Cùng luật anh đã chốt cho thi thử. Nhưng gắn ở `/complete` thôi thì KHÔNG đóng
được máy dò đáp án: em cứ trả lời → xem đúng/sai → bấm Bắt đầu → thử khác, **và
không bao giờ gọi `/complete`**, cho tới khi biết hết; rồi mới làm một lượt sạch
— và lượt SẠCH ấy trở thành "lượt đầu".

Nên chốt ở CẢ HAI đầu: `_chot_luot_drill` ghi lượt đang dở vào sổ ngay lúc bấm
"Bắt đầu" lại, tức **lượt DÒ chính là lượt đầu**. Cùng ý với thi thử: mở đề là
đã thấy đề.

Và tôi phải sửa lại một điều đã nói sai hôm qua: tôi ghi "XP đã chặn, chỉ bản đồ
năng lực chưa" — SAI. `existed` chỉ chặn lần thứ HAI; lần thứ nhất, tức lần duy
nhất được tính, đã là 120 XP do dò ra.

### [x] B15 (XONG) · `/complete` bỏ qua phần phòng luyện đã ghi nhận
Em làm đủ 8 câu (mỗi câu một `/check` đã ghi nhận) rồi TẢI LẠI TRANG trước khi
bấm Hoàn thành: thân gửi `"drill": null` và bản cũ trả `None` ngay — máy chủ có
sẵn bài làm nhưng không dùng, rồi `xoa_ghi_nhan` xoá luôn. Nay thân request chỉ
là BẢN SAO LƯU đúng như A12 tuyên bố; thiếu nó thì đọc phần đã ghi nhận.

### [x] B16 (XONG) · Mốc sàn kế hoạch chính xác tới GIỜ
Cắt về `date` thì kế hoạch sinh lúc 00:30 vẫn bị tick bởi việc làm lúc 00:10
cùng ngày — 20 phút TRƯỚC khi nó tồn tại. Nay so `occurred_at` ở mức giờ, và
`event_date` giữ làm đường lùi cho dòng cũ chưa có `occurred_at`.

### [x] B12 (XONG phần mã) · Redis — anh chỉ việc bật hạ tầng
`config/settings.py` nay đọc `REDIS_URL`; **không có biến thì chạy y như cũ**
(LocMemCache), nên bật/tắt không phải sửa một dòng mã nào. `IGNORE_EXCEPTIONS`
để Redis chết không kéo cả app chết theo — bộ đệm ở đây chỉ để nhanh hơn và để
đếm quota, không phải nguồn sự thật nào.

**Anh làm ba bước:** Render → New → Key Value (Redis), cùng region `ohio` → copy
Internal Redis URL → thêm biến `REDIS_URL` cho service `pe-hsa-backend`. Ba hệ
quả nó chữa đã ghi ngay trong chú thích ở `settings.py`.

### [x] §41 · Khoá ngoại còn thiếu, phát hiện khi trích ERD
`notification_settings` là bảng nghiệp vụ DUY NHẤT không có khoá ngoại — có khoá
chính nên không đẻ dòng trùng, nhưng xoá một tài khoản là bỏ lại dòng mồ côi
vĩnh viễn, trong khi mọi bảng anh em đều đã `ON DELETE CASCADE`. Đo trước khi
thêm: 0 dòng mồ côi. Nay 57 khoá ngoại, 0 bảng đứng ngoài lưới.

---

## Bộ tài liệu kiến trúc — `docs/KIEN_TRUC/`

Bốn tệp, mỗi tệp trả lời một câu hỏi khác nhau. Nguyên tắc bao trùm: **sơ đồ vẽ
sai còn tệ hơn không có sơ đồ** — nó tắt phản xạ đi đọc mã (RULES §20).

| Tệp | Câu hỏi | Sinh ra hay viết tay |
|---|---|---|
| `C4.md` | Hệ gồm gì, chạy ở đâu, ai gọi ai | viết tay |
| `ERD.md` | Dữ liệu nằm đâu, nối thế nào | **SINH RA** |
| `USE_CASE.md` | Ai làm được gì | viết tay |
| `LUONG_CHAM_DIEM.md` | Một câu trả lời đi đường nào để thành con số | viết tay |

### ERD được SINH RA, không vẽ
`python manage.py ve_erd` đọc `information_schema` rồi ghi thẳng
`docs/KIEN_TRUC/ERD.md`. Sơ đồ vẽ tay đúng đúng một ngày — ngày người ta vẽ nó.
Phần DUY NHẤT bảo trì tay là bảng phân miền `MIEN`; thêm bảng mà quên xếp miền
thì tài liệu **tự in ra cảnh báo**, không im lặng bỏ qua.

Lệnh TỰ GHI TỆP chứ không in ra stdout để người dùng chuyển hướng: trên Windows
`OutputWrapper` của Django đổi xuống dòng thành CRLF, và **cả 8 khối mermaid của
ERD lọt khỏi bộ kiểm cú pháp mà không ai biết** — đúng vì thế mới phát hiện.

### Bộ kiểm sơ đồ — và nó ĐỎ ĐƯỢC
`node scripts/kiem_so_do.mjs` gọi `mermaid.parse`, tức đúng bộ phân tích trình
duyệt dùng. Đếm dấu ``` không chứng minh gì: nó xanh cả khi bên trong là rác.

Đã tự kiểm: cố ý làm hỏng một sơ đồ → báo ĐỎ đúng khối, đúng số dòng; sửa lại →
xanh. **18/18 khối sạch.**

### Ba thứ chỉ đọc SỐ mới thấy, nay nằm trong tài liệu
- **12 bảng đang RỖNG** — một nửa hệ thống đang chờ người dùng đầu tiên: bài tập
  chấm tay, điểm danh, đợt học, đánh giá khoá, bình luận, theo dõi, thông báo.
  Danh sách này đáng đọc TRƯỚC khi thêm tính năng mới.
- **Luật xoá trộn ba kiểu**: 43 `CASCADE`, 10 `SET NULL`, 4 `NO ACTION`. Trong
  đó `roadmaps.user_id NO ACTION` nghĩa là **không xoá được tài khoản đã có lộ
  trình** — hiện chưa hại ai vì chưa có đường xoá tài khoản nào trong mã.
- **5 tài khoản thật.** Con số quan trọng nhất khi đọc mọi tài liệu ở đây.

### [ ] N3 · `roadmaps.user_id` là `NO ACTION` trong khi 43 khoá khác `CASCADE`
Chưa hại ai (chưa có đường xoá tài khoản), nhưng ngày dựng đường ấy thì nó chặn.
Đổi sang `CASCADE` cho khớp phần còn lại — hoặc quyết định giữ lộ trình lại khi
xoá tài khoản, và ghi lý do ra.

## 01/09/2026 · Giao diện — 0 vi phạm tương phản, và bộ đo đã tự chứng minh nó đỏ được

Việc chính hôm nay không phải vá giao diện mà là **sửa phép đo**. Bộ đo cũ có 7
lỗi, mỗi lỗi sinh ra một danh sách việc không có thật — cao điểm là lần nó báo
"0 vi phạm" trong khi tôi đang cố ý đặt chữ chính gần trắng.

Nay `scripts/do_giao_dien.mjs --tu-kiem` nhét một quy tắc hỏng vào mọi trang rồi
đòi bộ đo phải bắt được (1291 vi phạm). Chạy nó TRƯỚC mỗi lần báo số.

Sau khi phép đo trung thực: 8 vi phạm tương phản → **0**; 19 vùng chạm dưới
ngưỡng → **1** (cố ý giữ, đã ghi lý do). 11 trang × 2 khổ, 0 tràn ngang, 0 lỗi
JS, 0 lời gọi ghi lọt ra Neon.

Sáu gốc tương phản quy về một nguyên nhân: chữ nhỏ dùng bản màu dành cho nền/
viền. `--brand-ink` đã có sẵn từ đợt 31/08 — đây là những chỗ sót của chính đợt
đó. Nặng nhất: số XP trong `.player-pill` được 1,69:1 ở cỡ 9px, vì viên thuốc
thiết kế cho nền tối còn token chữ đã trỏ sang nền sáng.

Suýt báo thêm một lỗi ma: ảnh chụp cho thấy một vòng tròn đè lên nút "Quay lại".
`elementsFromPoint` cho thấy đó là `NEXTJS-PORTAL` — huy hiệu dev của Next, không
phải phần tử sản phẩm.

Chi tiết đầy đủ, gồm cả bảy lỗi của bộ đo: `TODO.md` mục 01/09/2026.

## 01/09/2026 (tiếp) · Chủ đề TỐI — chưa từng quét, 47 vi phạm

Trong đó một cái là **hồi quy của chính tôi hôm 31/08**: `--module-accent-ink`
đặt nhầm vào `:root` của một tệp viết theo lối tối-trước, kéo `.step-pill` xuống
2,88:1 ở 10 chỗ. Lượt đo hôm đó chỉ quét chủ đề sáng nên không ai thấy — đúng
kiểu lỗi mà "đo một nửa" sinh ra.

Nguyên nhân chung của phần còn lại gói trong một câu: token dành cho CHỮ bị dùng
làm NỀN và ngược lại. `theme.css` đã có sẵn tiền lệ cho màu đỏ (`--danger` vs
`--danger-fill`) nhưng chưa ai áp cho xanh lá và tím.

Bộ đo lại lộ thêm hai lỗi (thành chín): gradient bị `background-clip: text` tính
như nền — vừa đẻ ra một vi phạm 1:1 không có thật, vừa CHE một lỗi thật
(`.cd-module-prog` 2,54:1); và đo tương phản trên emoji.

Nay: sáng 0 · tối 0, mỗi lượt đều chạy `--tu-kiem` ngay trước khi lấy số.
Còn nợ: trạng thái rê chuột / lấy nét / vô hiệu.

## 01/09/2026 (tiếp) · Trạng thái rê chuột — và ba lỗi bộ đo nữa

Đo được trạng thái `:hover`/`:focus` phải trả giá bằng ba lỗi nữa trong bộ đo
(thành mười hai). Đáng nhớ nhất là lỗi thứ mười: từ Chrome 112, CSS Nesting làm
MỌI `CSSStyleRule` đều có thuộc tính `cssRules` — rỗng, nhưng tồn tại — nên
`if (r.cssRules) { đệ quy; continue; }` nuốt sạch luật thường. 371 luật quét
được, 0 luật chứa `:hover`, và bộ đo báo "0 lỗi rê chuột" vĩnh viễn.

Lỗi thứ mười một dạy một điều về CSS tôi chưa biết: **giá trị đang chuyển tiếp
thắng cả `!important` nội tuyến**. Ép màu xong đọc ngay thì được màu CŨ.

Lỗi thứ mười hai là lỗi thiết kế: ép KHAI BÁO của một luật `:hover` là bỏ qua
tầng xếp lớp, nên bản vá đã có vẫn bị báo là lỗi. Nay dùng CDP
`CSS.forcePseudoState` — để chính trình duyệt giải tầng xếp lớp.

Tự kiểm bằng đúng con lỗi tôi đã tìm bằng MẮT sáng nay: lùi bản vá
`body.light .nav-next:hover` → bộ đo báo ĐỎ 1,14:1 đúng chỗ; phục hồi → xanh.

Hai lỗi thật ở bản tối, kiểu mà đo tĩnh không thể thấy: chữ phụ ĐẠT lúc đứng yên
rồi TRƯỢT xuống 4,1:1 lúc rê chuột, vì nền nâng `#293548` quá sáng.

Bốn chiều × hai chủ đề × hai khổ × 11 trang: **tất cả 0**, trừ một vùng chạm cố
ý giữ. Cả hai chủ đề đều chạy `--tu-kiem` ngay trước khi lấy số.
