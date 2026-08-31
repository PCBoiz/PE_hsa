# TODO — backlog pe_hsa

Task trên cùng chưa gạch là task đang tới lượt. Tiêu chuẩn thực hiện: `RULES.md`.
Nhật ký: `PROGRESS.md`.

Ký hiệu: `[ ]` chưa làm · `[~]` đang làm · `[x]` xong · `[?]` chờ TopHSA trả lời

---

> **Việc cần anh Sơn làm tay** (khoá bí mật, bảng điều khiển Render/Vercel,
> quyết định sản phẩm, câu hỏi cho TopHSA) nằm ở **`docs/VIEC_CUA_ANH.md`**.
> Tệp này chỉ chứa việc tôi tự làm được.

## P0 — CHẶN ĐƯỜNG. Phải xong trước khi gộp vào `master`

### [x] T1 · Màn hình buổi học & điểm danh không chạy được — XONG 30/08
1.212 dòng mã (commit `f528391` + `f4b2651`) chết vì lệch tên khoá JSON ở ba tầng.

| Nơi | Frontend đọc | Backend trả |
|---|---|---|
| `giang-day/buoi-hoc/[classId]/page.tsx:10,34,55` | `detail.klass` | `reports.py:322` → `class` |
| `SessionsClient.tsx:10-16` | `starts_at`, `duration_minutes`, `counts` | `sessions.py:270` → `startsAt`, `durationMinutes`, `attendance` |
| `SessionsClient.tsx:22,27` | `user_id`, `absences` | `sessions.py:606` → `userId`, `absentTotal` |

Hệ quả: `if (!detail?.klass)` **luôn đúng** → trang luôn hiện "Không mở được lớp
này". `SessionsClient.tsx:319` gửi `user_id: undefined` → 400. Chip "chưa điểm
danh" — con số chú thích gọi là "giảng viên cần nhất" — không bao giờ hiện.

Ngoài ra `/giang-day/*` **không được liên kết từ đâu cả**.

**Xong khi:** mở thật trong trình duyệt đã đăng nhập, thấy được danh sách buổi,
tick được điểm danh, và có lối vào từ giao diện. Kèm ảnh chụp đã xem lại.

**Đã làm:** đổi kiểu + mọi chỗ ĐỌC sang camelCase (thân request vẫn snake_case —
backend nhận và trả hai quy ước khác nhau, đã ghi rõ thành chú thích); lối vào
thêm vào báo cáo lớp trong `dashboard.js` (không tạo trang danh sách lớp thứ hai
— khu Giảng dạy cũ đã có sẵn một cái). Chạy trọn vòng ghi trên trình duyệt thật:
tạo buổi → chip "3 chưa điểm danh" → tick cả lớp → lưu → chip "3 có mặt" → xoá
buổi (dọn 3 dòng điểm danh + 3 sự kiện). 0 lỗi console, 0 tràn ngang ở 390px.

### [x] T2 · Bộ lọc tài khoản của màn hình khác của file xuất — XONG 30/08
`admin_users.py:135` `build_user_filters` (có `norm_phone`) vs `exports.py:568`
`_filters` (chỉ `ILIKE` chuỗi thô). Đo thật: tìm `+84 987 654 321` → màn hình 1
kết quả, CSV **0 kết quả**. Trợ giảng lọc 30 em, tải về 28, không ai biết.

Chú thích ở **cả hai** tệp khẳng định sai rằng chúng dùng chung bộ lọc.

Ba điểm lệch khác: `class_id` rác → màn hình trả 0 dòng còn CSV trả 400 ·
`lower() LIKE` vs `ILIKE` · thứ tự sắp xếp khác nhau.

**Đã làm:** `exports.py` dùng `build_user_filters`, xoá `_filters` (2.158 ký tự).
Thêm `any_user_filter()` cạnh chính bộ lọc để câu hỏi "có lọc gì không" (dùng
đặt tên tệp) không bao giờ lệch khỏi bộ lọc. Thống nhất luôn thứ tự sắp xếp.
**Đo 10 ca, 0 lệch**, gồm đúng ca từng lệch (`+84 987 654 321` → cả hai đều 1).

### [x] T3 · CI đang đỏ trên nhánh `erp` — XONG 30/08
`pnpm exec eslint src` → exit 1. Hai lỗi nằm trong tệp mới của chính nhánh này:
`SessionsClient.tsx:167` và `LoginForm.tsx:45` (`react-hooks/set-state-in-effect`).
Còn `MockExam.tsx:30,71` (tệp cũ) và 2 cảnh báo.

**Đã làm:** 3 lỗi → **0 lỗi**. `LoginForm` nhận `oauthError` qua prop từ Server
Component (câu lỗi nay nằm sẵn trong HTML thay vì chỉ hiện sau khi JavaScript
chạy xong — người bị đá về từ Google trên mạng chậm từng thấy biểu mẫu trống
không giải thích gì). `NewSession` tính giờ gợi ý trong trình xử lý sự kiện.
`MockExam` gán ref trong effect, và bọc `start` bằng `useCallback` như `submit`.

**Đánh đổi đã nhận:** `/login` chuyển từ dựng sẵn tĩnh sang dựng theo yêu cầu vì
nay đọc `searchParams`. Chọn đúng hơn thay vì nhanh hơn một chút.

Còn 2 cảnh báo ở tệp cũ (`no-css-tags`, `no-img-element`) — T16 sẽ siết
`--max-warnings 0`.

### [x] T4 · Đăng xuất không thu hồi refresh token — XONG 30/08
`accounts/views.py:187-190` — `except Exception: pass` quanh `blacklist()`.
Cookie bị xoá phía Next nên trông như đã ra, **nhưng refresh token còn sống 8
tiếng**. Trung tâm dùng máy chung → không phải rủi ro lý thuyết.

Cùng tệp, `:166-167`: `return {'error': f'...{str(e)}'}` — `str(e)` của psycopg
chứa tên bảng, tên cột, đôi khi cả SQL và tham số, trả thẳng cho client. Và
`except Exception` nuốt luôn `Http404`/`PermissionDenied` thành 500, vô hiệu hoá
`common/errors.py` đã lo việc này tử tế.

**Đã làm:** tách `TokenError` (bình thường, log mức info) khỏi `DatabaseError`
(nghiêm trọng, log mức error kèm câu nói rõ phiên còn sống 8 tiếng). Trả thêm
`revoked` để bên gọi và log biết chuyện thật sự xảy ra. Bỏ hẳn `except Exception`
ở `RegisterView`, bắt riêng `IntegrityError` → 400 có câu sửa được.
**Kiểm chứng:** bảng blacklist tồn tại và đã thu hồi 17 token nên cơ chế đang
chạy — `except Exception: pass` là bẫy cho tương lai chứ chưa hỏng hôm nay. Đo:
thu hồi thật `revoked=True`, thu hồi lại `revoked=False`, token rác `revoked=False`,
và token đã thu hồi thì không dùng lại được.

### [x] T5 · `RegisterView` còn ghi định danh chưa chuẩn hoá — XONG 30/08
`accounts/views.py:155-165` kiểm trùng bằng `norm_*` rồi **INSERT chuỗi thô**.
Tạo tài khoản bằng `+84912345678` → `LoginView` tra `0912345678` → **không bao
giờ khớp**, khoá ngoài vĩnh viễn.

Phụ: `LoginView:49` chạy `validate_phone_field` trên chuỗi **thô**, nên
`"0912 345 678"` bị 400 trước khi `norm_phone` kịp sửa.

**Đã làm:** chuẩn hoá NGAY khi đọc thân request, để mọi bước sau tự động dùng
chung một giá trị — không còn chỗ cho hai bên lệch. `LoginView` kiểm định dạng
trên số ĐÃ chuẩn hoá.
**Đo:** bốn cách viết số điện thoại (`0964245623`, có dấu cách, dạng quốc tế có
dấu cách, có dấu gạch) đều qua được bước kiểm định dạng — cả bốn trả 401 "sai
mật khẩu" tức là ĐÃ TÌM THẤY tài khoản, thay vì 400 chặn ngay từ cửa.

---

### [x] T36 · `serverFetch` nuốt chuyển hướng + đua nhau làm mới token — XONG 30/08
Phát sinh khi kiểm T1. Hai lỗi, cả hai chỉ lộ sau khi access token hết hạn
(30 phút) nên gần như không bao giờ thấy lúc phát triển:
1. `SIMPLE_JWT` bật `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION`, mà một
   trang gọi vài `serverJson` song song trong `Promise.all` — cả nhóm cùng gửi
   đi làm mới bằng CÙNG một refresh token, cái xong trước giết token của những
   cái còn lại. Vá bằng `cache()` của React để gộp thành một lời gọi.
2. `catch { return null }` trong `serverFetch` **nuốt luôn cú `redirect()`** của
   Next (Next chuyển hướng bằng cách ném lỗi). Hậu quả: phiên hết hạn không đá
   về trang đăng nhập mà hiện "bạn không phải giảng viên phụ trách lớp này" cho
   đúng người đang phụ trách lớp đó. Vá bằng cách đưa `redirect()` ra ngoài try.

### [x] T37 · Lưu điểm danh xong không có xác nhận nào — XONG 31/08 (gộp vào T46)
Đo trên trình duyệt thật: lưu mất **2–5 giây**, và tín hiệu duy nhất báo xong là
chữ "Chưa lưu" BIẾN MẤT — một tín hiệu phủ định, rất dễ bỏ sót. Giảng viên đang
dạy, bấm Lưu trên điện thoại, không thấy gì đổi thì sẽ bấm lại hoặc tưởng hỏng.
Cần một xác nhận khẳng định (`Toast` đã dựng sẵn nhưng chưa gắn vào đâu — xem
T19). Phần lớn 2–5 giây là độ trễ dev từ VN, nhưng N+1 ở `_emit_events` (T21)
cũng góp vào.

## P1 — Đúng đắn dữ liệu

### [x] T6 · Bốn chỗ nuốt lỗi khiến báo cáo nói dối êm ái — XONG 31/08
Hai hàm trong `reports.py` nay trả `(data, ok)`, và `class_report` gom tên mảng
hỏng vào `summary.incomplete` — màn hình tự khai phần nào không đáng tin.
Hai chỗ trong `exports.py`: cột "Số buổi vắng" ghi "không đọc được" thay vì 0;
file điểm danh **trả 503 chứ không xuất** khi đọc hỏng — cả tệp chỉ có một nội
dung là chuyên cần, xuất ra một bảng chỉ có tên thì người ta mang nó đi họp.
Ghi rõ luật vào chú thích đầu module: ĐỪNG thêm `try/except` cho các hàm còn
lại — chúng để lỗi nổ ra là ĐÚNG, vì chúng chưa có đường báo ra.
`reports.py:86` `_events_by_user` → bản đồ năng lực trống, đọc thành "chưa đủ dữ
liệu" · `reports.py:194` `_lag_by_user` → **"cả lớp đúng tiến độ"** ·
`exports.py:284` `_absence_counts` → cột vắng = 0 toàn lớp · `exports.py:462`
`_attendance_data` → file chỉ có tên, trông y hệt "lớp chưa học buổi nào".

Mẫu sửa: trả `(data, ok)`; `ok=False` → ô ghi "không đọc được" hoặc dựng `alert`
mức `high`. `exports._rate` và `events.pct` đã theo đúng luật đó.

### [x] T7 · Số buổi vắng tính bằng hai luật — XONG 31/08
Gom về `teaching/attendance.py:dem_theo_hoc_vien`. Đo: 2 buổi cùng tick "vắng",
một buổi bị huỷ sau đó → cả file CSV lẫn màn hình đều ra **1**, trước đây file
ra 2 còn màn hình ra 1.
`sessions.py:594` loại buổi `cancelled`; `exports.py:277` **không**. Màn hình nói
"nghỉ 2 buổi", file mang đi họp phụ huynh nói "nghỉ 4". Gom thành
`teaching/attendance.py` dùng chung.

### [x] T8 · `joined_at` hai đồng hồ + em quay lại không hiện — XONG 31/08
Cả ba nơi ghi `class_members` đều đã dùng `local_now()`; đo lại: lệch 3 giây so
với giờ Việt Nam, không phải 7 tiếng. Nửa sau (em quay lại lớp không hiện trong
sổ điểm danh) đã được §36 giải quyết theo hướng khác — chỉ mục duy nhất MỘT PHẦN
cho em quay lại sinh một LƯỢT HỌC MỚI; đo lại: em id 13 hiện đủ trong bảng tick.
`admin_users.py:616` và `views.py:307` dùng `local_now()`; `views.py:536` **không
truyền** → `DEFAULT now()` = UTC. Cột "Ngày vào lớp" trong CSV sai ngày với em
được thêm lúc 1h sáng. Cùng dòng: `ON CONFLICT DO NOTHING` thay vì
`DO UPDATE SET left_at = NULL` → em quay lại lớp không hiện trong sổ điểm danh.

### [x] T9 · Hai luật kiểm cho cùng việc "tạo tài khoản" — XONG 31/08
Đường tạo đơn lẻ nay dùng CÙNG `validate_name/email/phone_field` với nhập hàng
loạt. Đo 4 dữ liệu hỏng (`abc`, `a@`, sđt 3 chữ số, tên 150 ký tự): trước đây
đơn lẻ cho qua hết, nay cả hai đường cùng từ chối.
`PasswordView` nay chặn đặt lại ĐÚNG mật khẩu hiện tại — trước đây gọi thẳng API
là giữ nguyên mật khẩu tạm mà vẫn được gỡ cờ `must_change_password`, tức vô hiệu
hoá cả cơ chế bắt đổi mật khẩu lần đầu bằng một lời gọi.
Nhập hàng loạt dùng `validate_name/email/phone_field`; tạo một tài khoản chỉ
kiểm rỗng và trùng. `"abc"` lọt vào cột email qua form đơn lẻ.
Phụ: `PasswordView` **không kiểm** `next === current` (chỉ client kiểm), nên gọi
API thẳng vẫn đặt lại đúng mật khẩu tạm cũ và cờ `must_change_password` được gỡ.

---

## P2 — Năm mảng audit chưa chạy (3 agent mỗi lượt)

### [x] T10 · Audit bảo mật — XONG 30/08, đẻ ra T38–T40
OWASP ASVS + danh mục Django production + mẫu xác thực App Router. Săn kỹ
`safeTarget` trong `lib/proxy.ts` (đã từng thủng bằng `..%2f`), SSRF, phân quyền
theo đối tượng, dò tài khoản, SQL injection ở câu dựng động, giới hạn tần suất
cho endpoint mới. Chạy `manage.py check --deploy`.

**Kết quả:** phân quyền theo đối tượng, SQL injection và lỗ `..%2f` của proxy —
agent tự tấn công lại toàn bộ, **không thủng**. Đã vá trong đợt này: cổng
`/auth/session` fail-open · `/api/user` trả `SELECT *` kèm ghi chú nội bộ của
quản trị viên về học viên · `FollowingView` không kiểm chủ sở hữu · dò tài khoản
qua thời gian phản hồi (134,8 ms → **4,7 ms**) · `.gitignore` hở `.env.prod`,
`.env.backup`, `scratchpad/` · lớp trung gian chuyển tiếp `X-Forwarded-For` của
trình duyệt. Ba việc còn lại cần anh: T38, T39, T40.

### [ ] T38 · Giới hạn tần suất bị vô hiệu bằng một header — CẦN ĐO TRÊN PRODUCTION
**Đo được:** DRF lấy nguyên chuỗi `X-Forwarded-For` do client gửi làm khoá
throttle (`NUM_PROXIES` chưa đặt). 300 lần đăng nhập xoay `X-Forwarded-For`
ngẫu nhiên → **300 lần đều lọt**; cùng 300 lần với IP cố định → 200 lần bị chặn.
Đã bịt đường đi QUA lớp trung gian (proxy nay loại `x-forwarded-for`). Đường gọi
THẲNG vào `pe-hsa-backend.onrender.com` vẫn còn.

Vá đúng cần `NUM_PROXIES` = số chặng proxy THẬT, và con số đó phải **đo**, không
đoán — đặt sai theo hướng ngược lại thì mọi người dùng dồn vào chung một khoá
throttle và một em gõ sai mật khẩu sẽ khoá cả lớp. Cách đo: gọi một endpoint
trên Render (a) qua trình duyệt đi đường Vercel, (b) bằng `curl` thẳng, rồi in
`request.META['HTTP_X_FORWARDED_FOR']` xem có mấy phần tử và phần tử nào là thật.

### [ ] T39 · `SECRET_KEY` 19 byte ký JWT HS256 — CẦN ANH XOAY KHOÁ
**Đo được:** `len(SECRET_KEY) = 19` byte = 152 bit. RFC 7518 §3.2 nói khoá HS256
**PHẢI** dài ít nhất bằng đầu ra băm (256 bit). `check --deploy` báo
`security.W009`. Đã kiểm kỹ: khoá **không** nằm trong lịch sử git (lần quét đầu
báo có là dương tính giả do `&&` bám vào exit code của `head`).

Khoá lộ = chiếm toàn bộ hệ thống: tự ký JWT `user_id=7, role=admin`, không
request nào tới máy chủ nên throttle và nhật ký đều không thấy gì, và danh sách
thu hồi vô dụng vì token đó chưa từng được cấp.

Sinh khoá mới: `python -c "import secrets;print(secrets.token_urlsafe(48))"`.
Dán vào `backend/.env` và vào Render → Environment. **Hệ quả:** mọi người đang
đăng nhập bị đăng xuất (mật khẩu KHÔNG bị ảnh hưởng — chúng băm bằng werkzeug,
độc lập với khoá này).

### [ ] T40 · Bộ đếm giới hạn tần suất nằm trong bộ nhớ tiến trình
`CACHES` chưa cấu hình → `LocMemCache`. Production chạy `--workers 2` nên bộ đếm
chia đôi, trần hiệu dụng gấp ~2 lần con số khai báo, và reset mỗi lần deploy.
Cần cache dùng chung (Redis) hoặc ghi rõ đây là giới hạn "mềm".

### [x] T11 · Audit luồng đầu-cuối — XONG 30/08, đẻ ra T45–T50
Theo vai người dùng: trợ giảng cấp tài khoản · tìm một em · giảng viên điểm danh
· đọc nhật ký · quyền theo vai · mất mạng giữa chừng · điện thoại 390px.

**Đi hết mọi luồng trên trình duyệt thật, 28 ảnh chụp đều đã xem lại. CSDL trở
về nguyên trạng.** Phần TỐT, đã kiểm và không cần soi lại: quyền theo vai kín
tuyệt đối (5 ca, không màn nào dựng khung rồi mới đổ lỗi) · chấm điểm từng dòng
khi nhập hàng loạt · đổi bộ lọc lúc đang ở trang 3 không ra danh sách rỗng · CSV
khớp màn hình cả về số dòng lẫn BOM lẫn dấu · tràn ngang **0 trên toàn bộ 10 tổ
hợp** trang × bộ màu · vùng chạm đạt 44px · bấm Lưu hai lần không lọt.

**Đã vá trong đợt này:** F-1 (phiên 30 phút → 8 tiếng, xem PROGRESS) · A-8 (chip
"Còn mật khẩu tạm" báo động giả 5/5) · G-2 (`ul/ol` chưa reset, ăn 80px trên màn
390px).

### [x] T45 · Bảng giấu 62% cột trên điện thoại — XONG 31/08
Dưới 640px mỗi dòng thành một THẺ (nhãn cột bên trái, giá trị bên phải), trên
640px vẫn là bảng nguyên vẹn. Đo lại ở 390px: bảng Tài khoản **796px → 306px,
giấu 0px**; nút "Đặt lại mật khẩu" nay nằm trong khung, vùng chạm 44px. Nhật ký
cũng 0px và cột "Nội dung" đọc được.
Hàng rào: `Td` BẮT BUỘC thuộc tính `label`, nên `tsc` chặn ngay khi ai thêm cột
mới mà quên — không phải trông chờ ai đó mở trang trên điện thoại mới phát hiện.
Vá kèm (phần còn lại của T49): ô vai trò và ô lọc hiện "Quản trị viên" thay vì
`admin`; nhật ký hiện "Điểm danh" thay vì `attendance.mark`, ở CẢ chip lẫn ô lọc.
CÒN LẠI: màn `/admin` cũ (chưa qua React, xem T35) vẫn giấu cột — đo 31/08 ở
390px: ba bảng giấu 83px / 165px / 234px.
Đo ở 390px: bảng Tài khoản rộng 796px trong khung 306px → **giấu 490px**. Cột bị
mất gồm **Thao tác**, tức trợ giảng KHÔNG bấm được "Đặt lại mật khẩu" và "Khoá"
trên điện thoại — việc chính của màn hình đó. Nhật ký giấu 45%, mất cột **Nội
dung** (thứ duy nhất nói chuyện gì đã xảy ra). Bảng "Kiểm tra trước" cắt cụt cột
**Kết quả** — tức chính cơ chế an toàn của nhập hàng loạt trở nên vô hình.
`TableWrap` cuộn ngang là đúng để trang không trượt, nhưng không có gợi ý thị
giác nào báo còn nội dung bên phải. Cần bố cục thẻ ở khổ hẹp thay vì bảng.

### [x] T46 · Lưu điểm danh: xác nhận nay nằm trong khung nhìn — XONG 31/08
Gắn `ToastProvider` (dựng từ T19, chưa nơi nào dùng). Đo lại ở 390×844 trên
trình duyệt thật: lời "Đã lưu điểm danh — 3 có mặt." ở top=766, bottom=828 —
trong khung 844px. Chữ "Chưa lưu" nay cách nút Lưu **13px** (trước 104px) nhờ
gộp chung một khối để hai thứ luôn xuống dòng cùng nhau. Thêm: màn hình nay
đọc `skipped` mà backend cố ý báo lại, trước đây vứt đi.
Mở rộng T37 bằng số đo. Lưu mất **4.716ms**; tín hiệu duy nhất báo xong là chữ
"Chưa lưu" biến mất. Ở 390×844: nút Lưu ở `top=764px` (trong khung), chữ "Chưa
lưu" ở `top=868px` — **ngoài khung nhìn 104px**. Đúng tư thế người ta bấm Lưu thì
không nhìn thấy thứ duy nhất báo đã xong. `Toast` đã dựng sẵn nhưng chưa gắn (T19).

### [x] T47 · `serverJson` vứt bỏ mọi câu lỗi backend — XONG 31/08
`serverJson` nay trả union có thẻ `Ket<T>` (`{ok,data}` | `{ok,status,message}`),
nên `tsc` BẮT BUỘC mọi nơi gọi xử lý nhánh hỏng — không thể vô tình bỏ qua như
khi `null` lẫn vào cùng kiểu dữ liệu. Câu lỗi dựng bằng chính `errorText` mà các
màn hình phía trình duyệt dùng, để một sự cố không ra hai lời khác nhau.
Đo lại `?from=abc`: màn hình nay hiện đúng câu backend viết — `Ngày "from" không
hợp lệ (định dạng YYYY-MM-DD).` — hết hai câu mâu thuẫn, và có liên kết "Xoá bộ
lọc và xem lại từ đầu" làm đường thoát (trước đây phải tự sửa URL).
`status === 404` vẫn giữ câu "không phải giảng viên phụ trách" ở màn buổi học —
backend cố ý trả cùng mã cho hai trường hợp; chỉ mã KHÁC mới đổi câu.
`server-api.ts` `if (!res || !res.ok) return null`. Backend viết sẵn câu tử tế
(`Ngày "from" không hợp lệ (định dạng YYYY-MM-DD)`) nhưng màn hình chỉ nhận
`null`. Hậu quả đo được: `/quan-tri/nhat-ky?from=abc` hiện **hai câu mâu thuẫn**
cùng lúc ("Không đọc được nhật ký" + "Chưa có hành động nào"), tải lại vẫn hỏng
mãi, và ô chọn Hành động rỗng đi nên **không còn nút nào bấm để thoát** — phải
tự sửa URL. 400 có hướng dẫn sửa và 500 sập CSDL đến màn hình là một.

### [x] T48 · Ba con số sĩ số khác nhau, và giục gọi em đã nghỉ — XONG 30/08
Khu Giảng dạy hiện đồng thời "3/25 học viên" · "4 học viên" · "HỌC VIÊN (4)".
`reports.py:335` trả `summary.students = len(students)` (tính cả em đã rời lớp)
trong khi mọi chỉ số khác tính trên `active`. Nặng hơn: ô **"Cần chú ý"** liệt kê
`ntn` — em đã rời lớp 5 ngày trước — và ở khu đó **không có** nhãn "(đã rời lớp)".
`dashboard.js:3947` thiếu điều kiện `!st.left`; `reports.py:316` `at_risk` cũng
duyệt toàn bộ `students` thay vì `active`.

**Đã làm:** `at_risk` và danh sách "Cần chú ý" nay chỉ tính học viên đang trong
lớp · `summary.students` đổi nghĩa thành sĩ số ĐANG HỌC (cùng nghĩa với mọi chỉ
số bên cạnh nó), thêm `enrolledEver` và `left` để tách hai khái niệm thay vì để
một tên mang hai nghĩa · tiêu đề bảng nói rõ "3 đang học + 1 đã rời lớp".
**Đo trên trình duyệt thật:** thẻ lớp 3/25 · ô thống kê 3 · tiêu đề "3 đang học
+ 1 đã rời lớp" · bảng vẫn 4 dòng (§29 giữ lịch sử) · "Cần chú ý" không còn em
đã rời lớp.
Ghi nhận thêm: frontend lọc theo `alerts.length` (MỌI mức) trong khi backend
`atRisk` chỉ đếm mức cao — hai luật khác nhau cho cùng một danh sách.

### [~] T49 · Ngôn ngữ máy lọt ra giao diện — VÁ MỘT PHẦN 30/08
· Nhật ký hiện thẳng `attendance.mark`, `session.create` làm chip VÀ làm nhãn ô
  chọn — người dùng phải chọn từ thực đơn toàn định danh tiếng Anh có dấu chấm.
· Ô vai trò hiện `admin` cạnh `Giảng viên`/`Học viên`; bản đồ nhãn
  `ROLE_LABELS` chỉ tồn tại ở `exports.py:71`, màn hình không có (RULES §7).
· `[object Object]` XÁC NHẬN SỐNG ở nút Đặt lại mật khẩu và ô đổi vai trò (T22)
  — nhưng KHÔNG ở đường tải danh sách. Sửa T22 mà chỉ vá đường tải là không chạm
  được lỗi.
· `Máy chủ trả lỗi 500` hiện thẳng cho trợ giảng (RULES §10) — trong khi cùng
  tình huống, màn hình điểm danh nói "Không tạo được buổi học".
· Bộ lọc màn hình Tài khoản **không vào URL** (bấm Quay lại nhảy ra
  `about:blank`), trong khi màn hình Nhật ký ngay cạnh lại làm đúng.
· Lớp hiện theo TÊN trên màn hình nhưng theo MÃ trong CSV.

**Đã vá:** thêm `errorText()` vào `lib/api.ts` — một cửa dịch cả BA hình dạng lỗi
backend đang trả (`{error: chuỗi}` · `{error: {message}}` của `common/errors.py`
· `{errors: {trường: câu}}`), có bảng câu tiếng Việt cho từng mã HTTP làm mức
cuối. Gắn vào 7 chỗ gọi ở hai màn hình. Đo ba ca đã hỏng:
`429 error=object` → "Bạn thao tác quá nhanh, chờ một chút." ·
`500 không thân` → "Hệ thống gặp lỗi. Thử lại; nếu vẫn vậy thì báo kỹ thuật." ·
`400 errors={...}` → câu lỗi của trường. `[object Object]` không còn trên trang.

**Còn lại:** nhật ký hiện `attendance.mark` · ô vai trò hiện `admin` · bộ lọc
màn hình Tài khoản không vào URL · lớp hiện theo tên trên màn hình, theo mã
trong CSV.

### [x] T50 · Nhập hàng loạt + xoá buổi học — XONG 31/08
Bốn lỗi, đo lại từng cái trên trình duyệt thật:
· **Con số** — máy chủ nay báo `parsedLines` và `headerSkipped`, màn hình hiện
  MỘT cách đếm tại một thời điểm: "Máy chủ đọc được 7 dòng (đã bỏ 1 dòng tiêu
  đề): 2 sẽ tạo, 5 bỏ qua" — 2+5=7. Trước là "8 dòng đã dán" cạnh "2 và 5".
· **Vượt trần** — nút nay ghi "Quá 50 — cắt bớt danh sách" thay vì "Tạo 60 tài
  khoản" (khoá, không nói vì sao) — một lời khẳng định ngược với điều vừa bị từ chối.
· **Bấm hai lần** — chốt `useRef` đồng bộ; `setBusy` của React không kịp. Đo hai
  cú bấm trong CÙNG một tick: 2 yêu cầu → **1**.
· **Bản nháp** — giữ trong `localStorage`, khôi phục khi bấm "Mở ô nhập" (một sự
  kiện, không phải hiệu ứng — tránh cả lỗi SSR lẫn luật React).
Thêm: nút **Xoá buổi học** trên từng dòng, đi đúng vòng xác nhận hai bước của
`ClassSessionDetailView` (409 kèm số dòng chuyên cần sẽ mất → hỏi → `?confirm=1`).
"8 dòng đã dán" rồi "Sẽ tạo 2, bỏ qua 5" — 2+5≠8 vì hai chỗ đếm khác nhau (máy
đếm cả dòng tiêu đề, máy chủ thì không). Vượt trần thì nút ghi "Tạo 60 tài khoản"
(đã khoá, không nói vì sao) cạnh câu "Sẽ tạo 60 tài khoản" — khẳng định ngược với
điều hệ thống vừa từ chối. Bấm "Kiểm tra trước" hai lần nhanh → **2 yêu cầu cùng
bay đi**; nút "Tạo" dùng chung hàm và chung cờ `busy` nên cùng khe hở, mà
`admin_users.py:478` gọi đó là "kịch bản tệ nhất trong tất cả". Tải lại trang
giữa chừng mất trắng danh sách đã dán, không có bản nháp.
Thêm: không có cách nào xoá hay sửa một buổi học từ giao diện, dù backend đã có
sẵn `ClassSessionDetailView` (cùng loại với T19).

### [x] T12 · Audit CSDL, truy vấn và đối chiếu ERD — XONG 30/08, đẻ ra T41–T44
N+1, chỉ mục thiếu/thừa, bất biến còn thiếu ở tầng CSDL, xoá dây chuyền,
`common/db.py` coi `PoolTimeout` là kết nối chết, múi giờ, kỷ luật một cửa của
`learning_events`. Đối chiếu ERD với Moodle / Canvas / OpenSIS — đặc biệt khái
niệm **kỳ học / đợt** mà pe_hsa chưa có.

**Đã vá:** `common/db.py` coi pool-bận là kết nối-chết (vòng xoáy tự khuếch đại,
xem PROGRESS) · 9 chỉ mục còn thiếu · 4 lỗi múi giờ gồm BXH tuần sai 7 tiếng mỗi
thứ Hai · `journal.py` phá kỷ luật một cửa · `dedup_key` của quiz khoá theo nhãn
thay đổi được · CI không kiểm cú pháp mô-đun lệnh quản trị.

**Agent BÁC BỎ một nghi ngờ cũ:** `check_and_award_achievements` đo được **5 câu**
chứ không phải ~23; trần tuyệt đối là 14. Không đáng vá. Và `plan.generate` là
85–139 INSERT chứ không phải 245.

### [x] T41 · Gộp các vòng lặp INSERT thành một câu — XONG 31/08
Đo lại sau khi vá: điểm danh 9 → **3 lượt** (và nay KHÔNG đổi theo sĩ số),
`plan.generate` 147 → **12 lượt**. Tìm thêm một vòng lặp thứ ba cùng loại:
`backfill_learning_events` chạy trên toàn bộ lịch sử học — đã gộp qua đệm ở
`_emit`/`_flush`. Kiểm 11 + 7 phép, dữ liệu ghi ra giống hệt từng ô.
`sessions.py:_emit_events` đo được **3N+1** câu (lớp 30 em = 91 lượt tới Neon,
0,46 s production / 23 s từ máy dev) — đây là phần N+1 của T37, và nó bác bỏ
chú thích đầu mô-đun khẳng định "số câu cố định". `stats/plan.py:245` là 85–139
INSERT tuần tự, tất cả trong một `atomic()` nên `common/db.py` từ chối thử lại →
một cú rớt kết nối huỷ trọn kế hoạch. Mẫu `INSERT ... SELECT FROM unnest(...)`
đã có sẵn ở `admin_users.py:632`.

### [x] T42 · Bất biến ở tầng CSDL — XONG 31/08
Đo trước khi thêm: `users.role` có đúng ba giá trị khớp `ASSIGNABLE_ROLES`,
`status` và `classes.status` chỉ có 'active' — không dòng nào vi phạm. Thêm 4
CHECK + 9 khoá ngoại cho 5 bảng trước đây không có cái nào (§35). Dòng mồ côi
`surveys` id=4 đã xoá (anh duyệt), khoá ngoại đã VALIDATE. `forget_events` nay
có ở cả đường xoá lớp, nhận danh sách id để không gọi N lần.
CÒN LẠI: quản trị viên (id 7) vẫn trong lớp 1 — anh chốt GIỮ, xem T51.
**Đã đo trên dữ liệu production:** `surveys` id=4 trỏ `user_id=10` — tài khoản
KHÔNG tồn tại (bảng `surveys` không có FK nào). Và `class_members` chứa `user_id=7`
role `admin` — quản trị viên đang là học viên của lớp 1, xuất hiện trong danh
sách điểm danh và sĩ số.
Thiếu `CHECK` cho `users.role`, `users.status`, `classes.status` (ba cột khoá
quyền đang là TEXT tự do) trong khi `class_sessions.status` và `attendance.status`
ĐÃ có — bất nhất ngay trong cùng một lược đồ. Thiếu FK cho `surveys`,
`enrollments`, `lesson_progress`, `course_ratings`, `roadmap_progress`.
Thiếu `forget_events` ở đường xoá lớp (`teaching/views.py`) trong khi đường xoá
một buổi (`sessions.py`) đã có — bất đối xứng.

### [x] T43 · `terms` + `class_members` đổi khoá chính — XONG 31/08
Làm đúng lúc rẻ nhất: 1 lớp / 4 thành viên. Khoá chính nay là `id`, hàng rào
chống trùng chuyển sang chỉ mục duy nhất MỘT PHẦN `WHERE left_at IS NULL` —
dựng TRƯỚC khi bỏ khoá cũ nên không có khoảnh khắc hở. Em đã rời lớp quay lại
nay sinh LƯỢT HỌC MỚI thay vì xoá trắng lượt cũ (đo: 1 dòng → 2, mốc cũ nguyên).
Thêm `leave_reason` (completed/dropped/transferred) + bảng `terms` một tầng.
Hai việc kiến trúc duy nhất mà chi phí **chỉ tăng theo thời gian**. Hiện
`classes` = 1 dòng, `class_members` = 4, `learning_events` = 37.
· PK `(class_id, user_id)` cho đúng MỘT dòng mỗi cặp, nên em quay lại lớp cũ ở
  đợt sau sẽ **ghi đè vĩnh viễn** lượt học trước (`ON CONFLICT DO UPDATE SET
  left_at = NULL` xoá trắng `left_at` cũ). Mâu thuẫn trực diện với §29.
· "Học xong" và "bỏ học" hiện là cùng một giá trị — hai con số hoàn toàn khác
  nhau khi trung tâm báo tỉ lệ bỏ học. §31 đã nhận ra đúng điều này cho
  `users.status` rồi chọn TEXT; lý lẽ đó chưa được áp cho `class_members`.
· Không có khái niệm ĐỢT, nên "đợt 1/2027 so với đợt 2/2027" phải đoán từ
  `starts_on` và **đọc tên lớp** — đúng cái bẫy Moodle mắc và phải vá bằng lồng
  thư mục. Đề xuất: bảng `terms` một tầng (không lồng bốn tầng như openSIS).

### [x] T44 · `attendance_taken_at/by` — XONG 31/08
Hai cột trên `class_sessions`, đặt trong cùng khối atomic với câu ghi điểm danh.
Màn hình nay phân biệt "Chưa mở sổ điểm danh" với "3 có mặt · đã điểm danh
31/08 02:56" — trước đây hai chuyện đó trông y hệt nhau. `admin_audit.detail`
giữ `firstTime` và `changed` (từ trạng thái nào sang trạng thái nào), để khiếu
nại của phụ huynh còn đối chiếu được.
Hôm nay "buổi X không có dòng `attendance` nào" **mơ hồ giữa "cả lớp có mặt" và
"giảng viên quên tick"**. openSIS có hẳn bảng `attendance_completed` chống lưng
cho báo cáo "hôm nay ai quên điểm danh". Vá rẻ: hai cột trên `class_sessions`,
đặt trong `SessionAttendanceView.post`. Kèm: `admin_audit.detail` nên chứa trạng
thái TRƯỚC khi sửa, để khiếu nại của phụ huynh còn đối chiếu được (openSIS giữ
cả `attendance_code` lẫn `attendance_teacher_code`).

### [x] T51 · Báo cáo lớp lọc theo VAI — XONG 31/08
Luật đặt ở MỘT chỗ (`teaching/vocab.py:chi_hoc_vien`), áp cho 5 câu tra đếm/liệt
kê thành viên ở `reports.py` và `sessions.py`. Vá ở tầng truy vấn chứ không lọc
trong Python vì mấy chỗ đếm là subselect `COUNT(*)` — lọc sau khi đã đếm thì
không lọc được nữa.
Đo lại: sĩ số 3 → **2**, thẻ lớp 2/25, tiêu đề "2 đang học + 1 đã rời lớp", bảng
tick bỏ quản trị viên, và tick cho tài khoản không phải học viên bị từ chối.
Loại bỏ nhưng KHÔNG im lặng: `summary.nonStudents` + một câu trên màn hình nói
rõ có bao nhiêu tài khoản khác đang trong lớp và vì sao không được tính.
Anh chốt 31/08 giữ tài khoản quản trị viên (id 7) trong lớp 1 để xem giao diện.
Nhưng hôm nay nó bị đếm như học viên: vào sĩ số, vào bảng điểm danh, vào mẫu số
tiến độ lớp. Vá đúng chỗ là lọc theo `users.role` ở `reports.py` và
`sessions.py`, để tài khoản quản trị nằm trong lớp bao nhiêu lần cũng không làm
lệch con số — thay vì trông chờ không ai thêm nhầm.

### [x] T52 · Đợt học dùng được — XONG 31/08
Bảng `terms` dựng ở §36 nhưng chưa có đường nào tạo hay đọc, tức nửa tính năng.
Nay có `teaching/terms.py` (CRUD + đếm lớp/học viên trong MỘT câu), `term_id`
gắn được vào lớp, tên đợt hiện trong danh sách lớp, và màn hình
`/quan-tri/dot-hoc`.
Xoá đợt KHÔNG xoá lớp (`ON DELETE SET NULL`) — câu hỏi xác nhận nói rõ điều đó,
vì người đang đọc nó sợ mất dữ liệu.
Kiểm 22 phép ở tầng view + 11 phép trên trình duyệt thật.
CÒN LẠI: báo cáo SO SÁNH giữa các đợt (tỉ lệ bỏ học, điểm trung bình theo đợt) —
nay đã có đủ dữ liệu để làm, trước thì không.

### [x] T13 · Audit khả năng tiếp cận — CHẠY XONG 31/08, đẻ ra T53
axe-core 4.12 thật, 7 trang × 2 bộ màu × 2 khổ = 28 lượt. **5 trang React sạch
hoàn toàn với axe ở bộ sáng**; nợ tập trung ở `/dashboard` cũ.
ĐÃ VÁ: bản in bộ tối (báo cáo phụ huynh in ra gần trắng giấy — 25 đoạn chữ dưới
ngưỡng, tiêu đề 1,23:1) · viền ô nhập 1,18–1,23:1 → 4,49/5,10:1 · nút nguy hiểm
bộ tối 2,77:1 → 6,47:1 · nhãn cột trong cây trợ năng ở khổ điện thoại.
CÒN LẠI → T53.
axe-core chạy thật + WCAG 2.2 AA. Đo trên pixel thật cả hai bộ màu. **Bẫy:**
`elementHandle.screenshot()` phá mô phỏng `pointer: coarse` — đo vùng chạm ở
lượt không chụp ảnh.

### [x] T14 · Audit nhất quán giao diện — CHẠY XONG 31/08, đẻ ra T53
Đo `getComputedStyle` trên trình duyệt thật. Kết quả đáng chú ý: **7 trang React
0 lệch thang chữ trên 344 phần tử, 0 lệch bo góc**; `/dashboard` cũ lệch 86/155
cỡ chữ và 92/124 bo góc.
ĐÃ VÁ: `term.*` thiếu trong bảng nhãn (mã máy lọt ra ngay sau khi tôi thêm tính
năng đợt học) · vai trò `admin` trần trong nhật ký · "Failed to fetch" tiếng Anh
ở 11 chỗ · mọi liên kết React bị gạch chân.
CÒN LẠI → T53.
Màn hình mới lệch khỏi hệ thiết kế của chính nó · đứt gãy ở ranh giới cũ–mới ·
bộ tối · trạng thái rỗng/đang tải/lỗi · ngôn ngữ trên giao diện (nhật ký đang
hiện thẳng `user.password_reset` cho người dùng đọc).

---

## P3 — Hàng rào tự động (để CI bắt thay vì audit tay)

### [x] T54 · Bảng điều khiển TOÀN TRUNG TÂM — XONG 31/08 (đặc tả ERP §6, nửa "Trung tâm")
Trước đó mọi báo cáo dừng ở cấp lớp; quản lý học vụ muốn biết lớp nào đang rơi
thì phải mở từng lớp rồi tự cộng trong đầu.
Ba con số chọn theo tra cứu chuẩn ngành dạy thêm: **giữ chân** (≥80% khoẻ, <70%
báo động) · **so sánh theo đợt** · **chỉ báo sớm** (chuyên cần + điểm + tiến độ).
Tỉ lệ bỏ học CHỈ tính được từ hôm nay, nhờ `leave_reason` của T43 tách "học
xong" khỏi "bỏ giữa chừng".
Đúng **5 câu SQL, không đổi theo số lớp** (đo: 1 lớp và 5 lớp cùng số câu).
Không đoán: rời lớp chưa ghi lý do thì KHÔNG vào tử lẫn mẫu, báo riêng ở
`leftUnknown`. Chưa tính được thì hiện dấu gạch, không hiện 0.
Kiểm 16 phép ở tầng view + 10 phép trên trình duyệt thật.
Vá kèm (một mục của T53): thanh điều hướng khu quản trị nay đánh dấu tab đang mở
(`aria-current="page"` + nền) và `<nav>` có `aria-label` tiếng Việt.

### [ ] T53 · Nợ khả năng tiếp cận & nhất quán còn lại (từ T13 + T14)
Xếp theo tác động, đã đo hết, chưa vá:
· **Không đăng xuất được bằng bàn phím** — `#user-chip-btn` là `<div>` không
  `tabindex`; Tab 60 lần không chạm tới. Trên máy dùng chung ở trung tâm đó là
  vấn đề riêng tư. Sửa: đổi thành `<button>`.
· **Hộp thoại đổi mật khẩu không bẫy tiêu điểm** — Tab 22 lần thì 14 lần rơi ra
  trang nền. `components/ui/Modal.tsx` đã làm ĐÚNG (0/16), dùng lại mẫu đó.
· **Hộp thoại đổi mật khẩu không đọc được ở bộ SÁNG** — nhãn 2,09:1, tiêu đề
  2,57:1; nó được vẽ cho nền tối, không có nhánh bộ sáng.
· **`/dashboard` hiện SỐ 0 GIẢ khi đang tải** — "0/76 bài", "0 ngày học liên
  tiếp". Chính `EmptyState.tsx` của hệ mới cấm điều này.
· Phần trăm tiến độ bộ tối 1,60:1 (màu lấy từ dữ liệu khoá học, không đổi theo
  bộ màu) · chữ thương hiệu bộ sáng 1,86:1 (đang dùng mã màu của bộ TỐI).
· Khu quản trị: không đánh dấu tab đang mở, không có `loading.tsx`, không có
  công tắc bộ màu — cả ba thứ trang cũ ĐÃ có.
· `HTTP_VI` trong `lib/api.ts` là mã chết: `errorText` ưu tiên `d.error` nên 12
  câu tiếng Việt đã soạn không bao giờ tới người dùng.
· `initial={list.ok ? ... : []}` nuốt lỗi tải danh sách con thành "rỗng".
· Bóng đổ bộ tối là mã chết (Tailwind v4 nội suy token lúc dựng bản).
· Chính tả dấu lệch giữa hai nửa (khóa/khoá, hủy/huỷ, xóa/xoá).
· `<dialog>` chưa có `aria-labelledby`; `<nav>` chưa có `aria-label`; bảng chưa
  có `caption`; `<th>` chưa có `scope`.

### [ ] T15 · `backend/pyproject.toml` — ruff + mypy
Cấu hình đã đo sẵn: 28 lỗi trên 12 tệp mới, 137 toàn backend, 24 tự sửa được.
Bật `DTZ` (cưỡng chế luật của `clock.py` — đã bắt được `datetime.utcnow()` thật
ở `accounts/views.py:416`), `BLE`, `I`, `F`, `B`. **Không** bật `S608` (raw SQL
là chủ ý), `DJ` (145 lỗi trên model `managed=False`), `UP031`, `RUF001/2/3` (dấu
tiếng Việt), `RUF012`. mypy `--check-untyped-defs` = 19 lỗi, 2 lỗi thật.
Chạy `ruff --fix` thành **commit riêng** để không lẫn vào diff nghiệp vụ.

### [ ] T16 · eslint tầng type-aware + `--max-warnings 0`
Thêm `typescript-eslint` `recommendedTypeChecked`. Đây là tầng duy nhất bắt được
`as never` ở `AccountsClient.tsx:148`. Thêm `no-restricted-syntax` chặn `as never`
tái diễn. `globalIgnores` phải loại `public/**` để `pnpm lint` và CI quét cùng
phạm vi.

### [ ] T17 · CI thêm bước lint backend
`ruff check .` trước `pytest` — chạy dưới 1 giây, bắt lỗi rẻ hơn một vòng pytest
chạm DB thật.

### [ ] T18 · Hàng rào cho lớp lỗi đắt nhất: sai hình dạng JSON
**Không bộ luật nào ở trên bắt được T1.** Ba mức, chọn theo giá:
1. Test hợp đồng: gọi thật endpoint rồi `assert` tên khoá (~1 giờ).
2. `zod` cho payload màn hình quản trị/giảng dạy; `serverJson` `parse` thay vì
   `as T` (~nửa ngày) — trả công cao nhất.
3. Sinh type từ backend (drf-spectacular → OpenAPI → `openapi-typescript`).

Kèm: **chốt `camelCase`** cho mọi khoá do ứng dụng dựng, và **cấm trả `SELECT *`
thẳng ra API** (`AdminAuditView`, `UserView.get` — cột mới thêm vào bảng sẽ tự
động rò ra API).

---

## P4 — Dọn nợ

### [ ] T19 · Mã chết
`Toast.tsx` toàn bộ (0 lời gọi, `ToastProvider` chưa gắn vào layout nào, trong
khi 7 chỗ mã cũ vẫn dùng `alert()`) · `Chip.LEVEL_TONE` (0 lời gọi) ·
`_pick_roadmap_template` · hai import thừa · 27 bộ chọn CSS `#roadmap-mermaid-wrap`
và `.svg-pan-zoom-control*` còn sót sau đợt cắt 3,44 MB · `'oauth-complete'`
trong `ISSUES_TOKENS` (chỉ tồn tại dạng GET redirect) · hai endpoint xuất CSV của
lớp chưa có nút nào bấm.

### [ ] T20 · Gom trùng lặp
`common/paging.py` (`read_paging`, `page_with_total` — nhân rộng ý tưởng
`LEFT JOIN LATERAL`), `common/params.py` (`read_date_range` — luật "`to` tính cả
ngày đó" đang viết lại ở hai chỗ), `teaching/classes.py` (hai `_class_row` cùng
tên), hạ `_temp_password`/`_user_label` xuống `common/`, `readCookie` ba bản y
hệt → `lib/auth.ts`, `type Payload` khai hai lần.

### [ ] T21 · Chú thích khẳng định sai sự thật
`sessions.py:21` nói "số câu cố định" trong khi `_emit_events` gọi `record_event`
một lần mỗi học viên · `legacy_schema.sql:651` ghi `user.password` còn hằng thật
là `user.password_reset` · `legacy_schema.sql:725` hai câu mâu thuẫn nhau ·
`EmptyState.tsx:6` nói "bắt buộc có action hoặc hint" nhưng cả hai đều tuỳ chọn.

### [x] T22 · Hai hình dạng JSON lỗi → `[object Object]` — XONG 30/08 (gộp vào T49)
`errorText()` trong `lib/api.ts` đọc được cả ba hình dạng, có bảng câu tiếng Việt
theo mã HTTP làm mức cuối. Đo ba ca đã hỏng, `[object Object]` biến mất.
CÒN LẠI ở T47: `serverJson` (tầng dựng trang) vẫn vứt toàn bộ thân lỗi.

<details><summary>Ghi chép gốc</summary>

`common/errors.py` trả `error` là **object**; view mới trả `error` là **chuỗi**.
`AccountsClient.tsx:147,197` và `SessionsClient.tsx:197,289,326` chỉ xử lý chuỗi.
Trợ giảng bấm nhanh → 429 → banner đỏ hiện `[object Object]`.
</details>

### [ ] T23 · `MAX_BATCH` khai hai nơi — trong khi máy chủ đã gửi con số xuống
`admin_users.py:553` **đã trả** `maxPerBatch`; frontend chỉ không khai nó trong
type nên không ai biết nó có ở đó.

### [ ] T24 · Hàm quá dài
`AdminBulkCreateUsersView.post` 163 dòng (chính chỗ sinh ra lỗi "kiểm trần sau
`if dry_run`") · `SessionAttendanceView.post` 124 dòng với 5 điểm `return 400`
giữa vòng lặp — validate nửa danh sách rồi bỏ, người gửi không biết dòng nào hỏng.

---

## P5 — ERP còn lại (đặc tả `docs/ERP_TOPHSA_2026-08-24.md` §9)

- [?] T25 · Điểm danh tự động — **cần TopHSA**: dạy trên nền tảng nào, có API lấy danh sách người tham dự không
- [?] T26 · Giao bài & chấm tay — **cần TopHSA**: có chấm tự luận không, thang điểm nào, ai chấm
- [x] T27 · Báo cáo phụ huynh + in ra PDF — XONG 31/08
      `teaching/parent_report.py` + trang in `/giang-day/bao-cao/<lop>/<em>`, lối vào từ
      bảng học viên trong khu Giảng dạy. Ba ranh giới cố ý: KHÔNG lộ nhật ký em tự ghi ·
      chuyên cần chỉ tính trên buổi ĐÃ điểm danh (buổi quên tick không được biến thành
      "con vắng") · không có dữ liệu thì nói không có, không viết 0.
      In bằng `window.print()` chứ không sinh PDF ở máy chủ — xem chú thích ở `PrintButton`.
      Kiểm 23 phép ở tầng view + 12 phép trên trình duyệt thật.
      CÒN LẠI: gửi tự động theo kỳ (cần T28 — kênh gửi, phụ thuộc TopHSA).
- [?] T28 · Thông báo Zalo/email — **cần TopHSA**: kênh nào, tần suất, ai duyệt
- [?] T29 · Học phí, công nợ, thù lao — **cần TopHSA**: quy trình kế toán thật
- [ ] T30 · Quyết định treo: `stats/journal.py:343` cộng `sys_min + self_min` — có tính phút ngồi lớp vào chỉ tiêu tuần không. Điểm danh đang cố ý để `minutes=NULL` chờ chốt.

## P6 — Chuyển màn hình cũ sang React

Xếp theo tần suất người dùng thật chạm vào, không theo độ dễ.

- [ ] T31 · Dashboard (màn đầu tiên mọi học viên thấy mỗi ngày)
- [ ] T32 · Bài học (nơi học viên ở lâu nhất)
- [ ] T33 · Thi thử
- [ ] T34 · Danh sách khoá
- [ ] T35 · Trang quản trị nội dung (`/admin`) — tách nốt phần tài khoản còn trùng với `/quan-tri`.
      Đo 31/08 ở 390px: ba bảng còn giấu **83px / 165px / 234px** (chúng là `<table>` HTML
      thuần nên không hưởng bố cục thẻ của T45). Chuyển sang React là vá luôn chỗ này.


## P1 — Sai số liệu do audit chéo 31/08/2026 tìm ra (đã đọc mã xác nhận)

Ba agent chạy song song: hai agent tìm lỗi (bảo mật · đúng đắn dữ liệu), một
agent phản biện lại cả hai. Điểm chung của mọi phát hiện dưới đây: **không cái
nào làm sập gì cả** — chúng chỉ in ra một con số sai, mà con số sai thì trông y
hệt con số đúng. Đó là lý do phải có test hồi quy, không phải chỉ có bản vá.

### [x] T55 · Bốn lỗi ở bảng điều khiển trung tâm — XONG 31/08
Vá ở `teaching/overview.py`, kèm 6 test hồi quy trong `teaching/tests.py`.
Đã chứng minh test ĐỎ trên mã cũ và XANH trên mã vá (lùi tệp bằng
`git checkout` rồi chạy lại — 6 fail; phục hồi — 6 pass).

| # | Lỗi | Người đọc làm sai gì |
|---|---|---|
| 1 | Câu 4 đếm bài của cả người ĐÃ RỜI LỚP và của KHOÁ KHÁC, còn mẫu số chỉ nhân với số em đang học | Lớp càng nhiều em bỏ học trông càng tiến độ tốt (đo: thật 11% → hiện 85%) |
| 2 | Câu 3 đếm cả buổi CHƯA DIỄN RA | Màn hình in "11 buổi đã dạy nhưng chưa ai điểm danh" cho lớp mới xếp lịch tuần sau — lớp chuẩn bị kỹ nhất bị quy trách nhiệm nặng nhất |
| 3 | Câu tra học tập hỏng → trả **0** thay vì **None** | Cả trung tâm hiện "Tiến độ 0%", trông như chưa ai học bài nào |
| 4 | Lớp mà MỌI thành viên đều không phải học viên bị rơi khỏi `GROUP BY` | Lớp biến mất khỏi bảng điều khiển, `classCount` thiếu, không câu lỗi nào |

### [x] T56 · Rò rỉ hồ sơ qua `TeachStudentView` — XONG 31/08
`teaching/views.py` thiếu `chi_hoc_vien` mà `parent_report.py` đã có. Giảng viên
phụ trách lớp đọc được hồ sơ ĐẦY ĐỦ của tài khoản quản trị viên đang là thành
viên lớp 1 — email, số điện thoại, mục tiêu, sổ điểm, và **nhật ký tự ghi**.
Đường trả về ÍT dữ liệu hơn (`parent-report`) thì đã chặn; đường trả về NHIỀU
hơn thì quên. Đo lại sau bản vá: quản trị viên → 404, học viên thật → 200.

### [x] T57 (XONG 31/08) · Sổ điểm danh CSV cộng cả buổi ĐÃ HUỶ
`teaching/exports.py` ~440: `counts[status] += 1` không loại `cancelled`, nên
`_rate` chia cho mẫu số có cả buổi huỷ. `progress.csv` (đi qua
`attendance.dem_theo_hoc_vien`) thì đúng. Hai file xuất từ CÙNG một màn hình nói
hai con số khác nhau về cùng một em — trợ giảng tải cả hai cho buổi họp phụ
huynh. Đúng loại lỗi mà `teaching/attendance.py` mở đầu bằng câu "nay chỉ còn
một luật, ở một chỗ": `_absence_counts` đã đi qua cửa đó, bảng chéo thì chưa.

### [x] T58 (XONG 31/08) · Báo cáo phụ huynh: mẫu số chuyên cần sai
`teaching/parent_report.py` ~155: `attendedPct = co_mat / len(da_tick)` — mẫu số
là buổi CẢ LỚP đã tick, không phải buổi em ấy CÓ DÒNG. Giảng viên tick cả lớp mà
sót một em thì em đó vẫn bị chia. Em đi đủ 2/2 buổi có dòng → **giấy in 50%**.
`noRecord` có trả về nhưng frontend không hiển thị ở đâu (`grep` → 0 kết quả),
nên bốn ô trên giấy cộng lại không bằng mẫu số và không dòng nào giải thích.
Đây là tờ giấy GỬI VỀ NHÀ: lỗi hành chính của giảng viên bị đọc thành hạnh kiểm
của học sinh, và không ai ở đó đính chính.

### [x] T59 (XONG 31/08) · Học viên quay lại lớp cũ bị đếm HAI LẦN
`teaching/reports.py:_members` không lọc `left_at`, không gộp theo `user_id`. Từ
§36 một cặp lớp–người có thể có nhiều dòng. Hệ quả đo được: sổ điểm danh in hai
dòng cùng tên; `summary.left = 1` trong khi không ai rời lớp; bản đồ năng lực
của lớp bị kéo lệch (40% thay vì 50%) — và chính con số đó nuôi `weakestTopics`
mà giảng viên dùng để chọn chủ đề ôn lại.

### [ ] T60 · Kỳ in trên giấy ≠ kỳ dùng để tính, khi em học lại lớp cũ
`teaching/parent_report.py` ~248 lấy MỘT lượt học (`LIMIT 1`) để bó chuyên cần,
nhưng `_hoc_tap` dùng trọn kỳ và `period` in ra cũng là trọn kỳ. Em học 01–20/08
rồi quay lại 28/08: giấy in "học 5 bài, làm 2 đề, điểm đang lên" cạnh "chuyên
cần 0%", trong khi sự thật trong kỳ đó là 8/9 = 89%.

### [x] T61 (XONG 31/08) · Mục kế hoạch mồ côi thành "Chậm N bài"
`teaching/reports.py` ~231: `LEFT JOIN lessons` rồi `WHERE lp.user_id IS NULL` —
mục trỏ tới bài KHÔNG TỒN TẠI luôn tính là quá hạn. Hôm nay chưa nổ cho mục
`lesson` (0 mục mồ côi) nhưng ĐÃ CÓ 113 mục `mock`/`review` mồ côi, chúng chỉ
thoát nhờ bộ lọc `kind='lesson'`. §26 ghi rõ TopHSA sẽ soạn lại giáo trình, tức
`sort_order` sẽ đổi — ngày đó cả lớp đồng loạt hiện "chậm N bài" và vượt ngưỡng
`LAG_ITEMS = 5`. Sửa: `AND l.id IS NOT NULL`, và báo số mục mồ côi ra
`incomplete`.

### [ ] T62 · Hai nơi trả lời cùng một câu hỏi bằng hai phép tính
Không phải lỗi kỹ thuật mà là **quyết định chưa được ghi**. Cần chốt rồi mới sửa:
- "Chậm bao nhiêu": `reports.py` đếm `kind='lesson'`, `stats/plan.py` đếm mọi
  loại. Trên dữ liệu thật uid 12: giảng viên thấy **12**, học viên thấy **14**.
  Giảng viên gọi điện nói một số, em mở app thấy số khác.
- Bản đồ năng lực: `reports.py` dựng ô từ `topic` của SỰ KIỆN,
  `stats/competency.py` dựng từ `lessons.module`. Hôm nay hai bên khớp tuyệt đối
  (31/31, 21/21, 42/42) nên là mìn chờ, kích hoạt khi giáo trình đổi tên chủ đề.

### [x] T63 (XONG 31/08) · `ORDER BY occurred_at` thiếu tie-breaker
`teaching/reports.py` ~209, chỗ quyết định DẤU của xu hướng điểm thi thử
(ngưỡng cảnh báo `<= -8`). `parent_report.py` đã vá đúng lỗi này kèm 6 dòng chú
thích; `reports.py` thì không. Chưa tái hiện được lật dấu trên bảng nhỏ, nhưng
thứ tự vẫn là không xác định theo hợp đồng SQL. Sửa: thêm `, id` — một token,
khoá vĩnh viễn một lớp lỗi không có đường tái hiện.

### [ ] T64 · `must_change_password` chỉ ép ở frontend
Backend không view nào từ chối khi cờ còn TRUE: tài khoản mật khẩu tạm gọi
thẳng `GET /api/user`, `GET /api/stats` đều 200. Trợ giảng biết mật khẩu tạm
(vừa đọc cho học viên) dùng được toàn quyền tài khoản trong cửa sổ trước khi em
đổi. Hẹp về thời gian nên xếp sau, nhưng nó là hàng rào chỉ tồn tại ở lớp vẽ.

### [ ] T65 · `meeting_url` không kiểm lược đồ — chưa khai thác được, nhưng hàng rào là tình cờ
`teaching/views.py:_clean_class_payload` nhận `meeting_url` là chuỗi bất kỳ; nơi
duy nhất đổ nó vào `href` là `dashboard.js:3979`, và `escHtml` chỉ thoát HTML —
`javascript:alert(1)` đi qua nguyên vẹn.

**Nhưng ĐO ĐƯỢC 31/08/2026: không khai thác được.** Dựng đúng thẻ đó trong
Chromium rồi bấm: `target="_blank"` **chặn** điều hướng `javascript:` (false);
bỏ `target` ra thì chạy (true). Tức hàng rào duy nhất đang giữ chỗ này là một
thuộc tính đặt vào vì lý do khác hẳn.

Nên vẫn vá, ở ĐƯỜNG GHI chứ không ở đường vẽ: chỉ nhận `http://` và `https://`.
Ai đó gỡ `target="_blank"`, hoặc dựng một màn hình React mới đổ `meetingUrl` vào
`<a>`, là lỗ mở lại mà không ai biết mình vừa gỡ hàng rào gì. Ưu tiên THẤP: cần
quyền quản trị viên/giảng viên mới đặt được, mà vai đó đã tin cậy hơn thế nhiều.

---

## Đợt phản biện 31/08/2026 — agent thứ ba kiểm lại hai agent kia VÀ các bản vá

Kết quả: 6/6 bản vá chạy đúng như tuyên bố, không sinh lỗi mới — kể cả chỗ tôi
nghi nhất (`hong_hoc_tap` trả None ở tầng cuộn lên đợt). Nhưng nó bắt được
**lỗi của chính tôi**, và hai chỗ hai agent kia nói quá sự thật.

### [x] C1 (XONG 31/08) · Chú thích tôi viết TỰ NHẬN đã đo nhưng không tái hiện được
Tôi chép hai con số từ báo cáo của agent tìm lỗi ("lớp thật 11% hiện 85%",
"93% trong khi thật là 7%") vào chú thích `overview.py` **như thể tự tay đo**.
Đo lại trên production: lớp thật đi từ **13% → 11%**, và cảnh "học xuyên khoá"
KHÔNG THỂ xảy ra trên dữ liệu hiện có (100% sự kiện `kind='lesson'` đều thuộc
`hsa_quantitative`). Hai bộ lọc vẫn đúng và giữ nguyên; chú thích đã sửa cho
khớp số đo thật, và nói rõ chỗ nào là suy luận chứ chưa đo.

**Đây là lỗi nặng nhất của cả phiên** — nặng hơn mọi lỗi số liệu ở trên. Một
con số sai thì người sau đo lại là ra; một chú thích tự nhận đã đo thì người
sau TIN nó và không đo lại nữa.

### [x] C5 (XONG 31/08) · `GRADED_KINDS` là hằng số chết
Không mô-đun nào import (rà cả repo: ba lần xuất hiện, cả ba trong chính
`events.py`). Thêm `KIND_ASSIGNMENT` vào đó **không có tác dụng gì** — nguồn
thật là `competency.KIND_TO_SOURCE`, chỗ đó tôi sửa đúng. Đã sửa chú thích để
hằng số không còn nói dối về tầm ảnh hưởng của nó.

### [x] C7 (XONG 31/08) · "Còn mấy bài chưa chấm" đếm hụt
`ungraded = submitted - graded` sai vì hai tập không lồng nhau: chấm điểm cố ý
không đụng `submitted_at` (bài nộp trên giấy). 5 em nộp online (3 đã chấm) + 2
em chấm giấy → hiệu bằng 0 trong khi còn 2 bài chưa chấm. Đổi sang một phép
đếm riêng ở SQL.

### [x] C-mới (XONG 31/08) · `assignments.topic` là ô gõ tự do — bẫy tôi tự tạo ra hôm nay
Bản đồ năng lực của HỌC VIÊN dựng ô từ `lessons.module`; của GIẢNG VIÊN dựng ô
từ `topic` của sự kiện. Trước nay luôn khớp vì `topic` do hệ thống sinh. Mã mới
của tôi nhận `topic` là văn bản 120 ký tự bất kỳ. Đo được: hai bài "Doc hieu"
(thiếu dấu) + hai bài "Đọc hiểu" → bản đồ giảng viên hiện **hai ô cho cùng một
chủ đề (16% và 49%)**, bản đồ học viên không có ô nào. Đã ràng vào danh mục
`lessons.module` của khoá lớp đang dạy (backend từ chối 400, màn hình đổi thành
ô CHỌN).

### [ ] T66 · `common/audit.py::_client_ip` lấy phần tử ĐẦU của `X-Forwarded-For`
Cả hai agent tìm lỗi đều bỏ sót. Phần tử đầu là thứ người gọi TỰ ĐẶT, nên cột
`ip` của nhật ký kiểm toán giả mạo được — ở đúng chỗ sinh ra để làm bằng chứng.
**Không sửa mù**: đúng vị trí phụ thuộc `NUM_PROXIES`, mà con số đó chưa đo trên
production. Đã ghi cảnh báo vào mã; vá CÙNG LÚC với A2 trong `VIEC_CUA_ANH.md`.

### [ ] T62 (thay cho bản cũ) · Hai nơi đếm "chậm" — nguyên nhân SÂU HƠN đã nghĩ
Không chỉ khác bộ lọc `kind`. Hai bên còn hỏi hai BẢNG khác nhau để biết "bài
này xong chưa": `stats/plan._done_lookup` đọc `learning_events` (`meta.lessonNo`),
`teaching/reports._lag_by_user` đọc `lesson_progress` JOIN `lessons.sort_order`.
Hôm nay chúng tình cờ khớp. Một dòng lệch giữa hai bảng là hai con số lệch mà
không ai giải thích được. Đo thật hôm nay: uid 12 — học viên thấy **14**, giảng
viên thấy **12**. Cần chốt MỘT nguồn trước khi sửa.

### [ ] T60 (giữ nguyên) · Kỳ in trên giấy ≠ kỳ dùng để tính
Đã xác nhận lại: `period` in "01/01–31/12", ô học tập đếm trọn năm, ô chuyên cần
chỉ đếm 2 trong 4 buổi vì bị bó theo một lượt học.

### [x] T64 (XONG 31/08) · `must_change_password` chỉ ép ở frontend
Hàng rào nay nằm trong LỚP XÁC THỰC (`accounts/authentication.py`), không phải
ở permission hay middleware — và cả hai chỗ kia đều sai:
- `DEFAULT_PERMISSION_CLASSES`: view nào khai `permission_classes` riêng (gần
  như cả khu `teaching/`) ghi đè danh sách mặc định và đi vòng qua hàng rào.
- middleware: chạy TRƯỚC khi DRF xác thực, lúc đó `request.user` còn ẩn danh.

Bốn đường được phép: `/api/user` (kèm `/api/user/password`), `/auth/refresh`,
`/auth/logout`. Trả **403 kèm `mustChangePassword: true`**, không phải 401 — 401
khiến lớp làm mới token ở frontend tưởng phiên hết hạn, thử refresh, rồi đá về
đăng nhập, và vòng đó lặp mãi vì đăng nhập lại vẫn còn nguyên cờ.

**Hai thứ phải vá CÙNG LÚC, thiếu một là hỏng:**
1. `PasswordView` nay gọi `invalidate_user_cache`. `CachedJWTAuthentication` giữ
   đối tượng user 60 giây; không xoá đệm thì em vừa đổi mật khẩu xong vẫn bị
   chặn thêm tối đa một phút — đúng lúc đang mừng vì vừa làm đúng.
2. Lỗi 403 phải NÓI RA lý do. Bộ xử lý lỗi chung cố ý làm phẳng mọi
   `PermissionDenied` thành "Không có quyền truy cập"; ở đây thì ngược lại,
   người dùng PHẢI biết lý do, nếu không họ gặp tường 403 câm ở mọi trang. Đã
   thêm lớp `PhaiDoiMatKhau` riêng, và cả hai tầng frontend (SSR + trình duyệt)
   tự đưa họ tới `/doi-mat-khau`.

Đo được: 403 đúng chỗ, bốn đường cho phép vẫn 200, gỡ cờ là đi lại được NGAY
(không đợi 60 giây), và điều hướng KHÔNG lặp vô hạn khi đã ở trang đích.

### Ghi chú: bộ đếm sequence của Neon đã nhảy
Các phép kiểm chạy trong giao dịch cuộn lại KHÔNG trả lại sequence.
`classes_id_seq` nay ở khoảng ~105, `assignments_id_seq` ~55. Vô hại (không dòng
nào tồn tại, không ràng buộc nào vỡ) — nhưng lớp học THẬT tiếp theo sẽ mang id
lớn hơn 100 thay vì 2. Nói ra để anh không giật mình khi thấy.

### [x] T53-a (XONG 31/08) · Ba món tiếp cận nặng nhất
1. **Người dùng bàn phím không đăng xuất được, trên MỌI trang.** `#user-chip-btn`
   là `<div>` (Tab 80 lần không lần nào dừng), mà menu `visibility: hidden` khi
   đóng nên ba nút bên trong cũng không tới được. Đổi sang `<button>` ở CẢ HAI
   bản sao (Topbar + trang chi tiết khoá học). Đo lại: Tab 19 → Enter → Tab 3 →
   "Đăng xuất". Chiều cao chip vẫn 34px, có vòng tiêu điểm.
2. **Tương phản `/dashboard`**: quét 113 phần tử chữ → 12 chỗ dưới ngưỡng ở bộ
   sáng, 6 ở bộ tối. Nay **0/0** ở cả hai. Thêm 9-10 chỗ trên nền gradient đo
   riêng bằng pixel: tất cả đạt. Nguyên nhân chung là **hex viết cứng đi vòng
   qua token đã vá** — `--t3` đã nâng cho đạt 4,5:1 nhưng `.lb-meta` viết
   `#94A3B8`; token họ `-light`/`--accent` là màu dành cho CHỮ lại bị đem làm
   NỀN đỡ chữ trắng. Thêm `--success-fill` theo đúng lối `--danger-fill`.
3. **Hộp đổi mật khẩu**: nhãn 3,17:1 → 15,11:1 (làm tối tấm kính chứ không làm
   sáng chữ — chữ ở đây trắng); thêm bẫy tiêu điểm dùng chung
   (`window.bayTieuDiem`) và trả tiêu điểm về chỗ cũ khi đóng. Đo: 25 lần Tab
   không thoát ra ngoài, đóng xong tiêu điểm về đúng nút đã mở.
4. **Bảng**: `<caption>` nay BẮT BUỘC (kiểu ép, `tsc` bắt được — cùng lối với
   `label` của `Td`) và mọi `<th>` có `scope="col"`. Đo trên màn hình thật:
   caption 1×1px `absolute` (thật sự ẩn), 8/8 `th` có scope.

### [ ] T53-b · Còn lại của khối tiếp cận
Chưa làm: `/dashboard` hiện số 0 giả lúc đang tải · chưa có `loading.tsx` · chưa
có nút đổi bộ màu trong khu `(standalone)` · `HTTP_VI` có nhánh chết · bóng đổ
bộ tối là mã chết · chính tả dấu không nhất quán (khóa/khoá, hủy/huỷ, xóa/xoá) ·
hộp huỷ ghi danh (`main.js`) NAY đã dùng `window.bayTieuDiem` — đo: 12 lần Tab không thoát, đóng xong tiêu điểm về chỗ cũ, 0 lỗi JS.


---

## Đợt audit thứ hai 31/08/2026 — soi chính phần vừa viết

Hai agent audit đúng khối §5 và khối hàng rào mật khẩu + giao diện vừa áp. Kết
quả: **12 + 8 phát hiện**, trong đó hai cái nặng nhất là **hồi quy do chính
tôi gây ra cùng ngày**.

### [x] A1 (XONG) · Hàng rào mật khẩu tạm khiến trang cũ hiện TÀI KHOẢN TRẮNG GIẢ
Nặng nhất cả đợt, và nó là hậu quả trực tiếp của bản vá T64 vài giờ trước.
`apiFetch` có bắt 403 → điều hướng, nhưng **trang cũ gọi `fetch` thô hơn 60
chỗ**, không chỗ nào đi qua nó. Nên `/dashboard` không hiện lỗi mà hiện một
dashboard **trông hoàn toàn bình thường của người mới**: "0 ngày học liên tiếp",
"0/76 bài", "Bạn chưa đăng ký khoá nào". Em đã học 27 bài mở lên sẽ kết luận
**tài khoản mình bị xoá sạch**, đi báo trợ giảng "mất hết bài" — chứ không đời
nào đoán ra việc cần làm là đổi mật khẩu tạm.

Hàng rào sinh ra để bảo vệ lại thành thứ nói dối êm ái nhất trong sản phẩm.
Vá ở đúng chỗ bọc `fetch` sẵn có trong `main.js` — một nơi, phủ hết mọi lời gọi
cũ. Đo: cả `/dashboard` lẫn `/courses/<id>` nay tới `/doi-mat-khau?lan-dau=1`.

### [x] B1 (XONG) · Nút "Bài tập" tôi thêm đẩy chip người dùng RA NGOÀI màn hình
Cũng là hồi quy cùng ngày, và trớ trêu: cùng đợt sửa vừa mở đường đăng xuất cho
người dùng BÀN PHÍM lại bịt đường của người dùng CHUỘT.

Đo ở 1280px (khổ laptop phổ biến nhất): học viên còn nhìn thấy **11px** của
chip; **giảng viên và quản trị viên còn 0px**, mà `scrollWidth == innerWidth`
nên cũng không cuộn tới được. Mất luôn Đăng xuất, Cài đặt, chuông và nút đổi
bộ màu.

Bản vá **đã tồn tại** từ đợt audit 13/08 nhưng bị nhốt trong media query dưới
900px. Đưa lên luật gốc, thêm `justify-content: safe center`. Đo lại: chip hiện
đủ (93/93, 97/97, 55/55) ở cả ba vai trò × ba khổ, và **7/7 · 9/9 mục nav đều
cuộn tới được** — `safe center` sửa luôn lỗi "Dashboard không bấm được ở 390px"
đã tồn tại từ trước.

### [x] §5 · Điểm bài tập KHÔNG BAO GIỜ vào bản đồ năng lực của học viên
Lời hứa trung tâm của cả mô-đun, sai trên đường MẶC ĐỊNH. Bản đồ khoá ô theo
CẶP `(course_id, topic)`; màn hình không gửi `course_id` (rà cả thư mục: 0 kết
quả), nên mọi bài giao qua giao diện có `course_id = NULL` và sự kiện rơi vào ô
`(None, 'Số học')` — một ô KHÔNG TỒN TẠI. Đo: chấm 9/10 xong, ô của em không
đổi một chữ, còn bản đồ giảng viên **mọc thêm ô "Số học" thứ hai**.

Vá: `course_id` SUY RA từ lớp, và thôi nhận từ body (nhận cả hai là mở cửa cho
một thân request đặt `topic` khoá A với `course_id` khoá B).

### [x] §5 · Bảy lỗi còn lại, đều đã có test đỏ-trên-mã-cũ
| | Hậu quả |
|---|---|
| Gõ "8,5" thành **85** | Ô `type=number` của Chromium XOÁ dấu phẩy. Trên bài thang 100 thì 85 hợp lệ → điểm **gấp mười lần** vào sổ, vào bản đồ, vào báo cáo phụ huynh, không một cảnh báo. Đo cả với locale vi-VN |
| Nhận xét không xoá/sửa riêng được | Gõ nhầm vào ô em khác thì nằm lại vĩnh viễn; muốn thêm nhận xét mà không đổi điểm thì nút Lưu ghi "Chưa gõ điểm nào" và không nói vì sao |
| "36/35 đã nộp · còn 1 bài chưa chấm" | Em rời lớp vẫn được đếm trong khi bảng chấm đã giấu đi → huy hiệu vàng không bao giờ tắt, không có ô nào để bấm |
| Xoá lớp bỏ lại **điểm** mồ côi | Nặng hơn hẳn sự kiện điểm danh (score NULL): điểm của bài không còn tồn tại kéo con số thành thạo của em suốt đời, và không còn đường xoá |
| Hộp xác nhận xoá lớp nói thiếu | Đọc "mất 4 dòng ghi danh, 0 buổi học" rồi bấm đồng ý — thứ thật sự mất là **bài tự luận của cả lớp**. Lớp chỉ có bài tập thì KHÔNG hỏi câu nào |
| Học xong khoá là mất sạch bài và nhận xét | Đúng lúc em ôn lại trước ngày thi. Dữ liệu còn nguyên, chỉ mất đường vào |
| Tiêu đề rỗng / thang điểm biên → **500** | `Decimal('NaN')` là Decimal hợp lệ; PATCH `title="   "` nổ `IntegrityError`. 500 là mã báo "lỗi của chúng tôi" cho thứ thật ra là gõ nhầm |

### [x] Hàng rào mật khẩu — ba lỗ nữa
- `startswith('/api/user')` cho `/api/users/11/follow` (số NHIỀU) lọt → so khớp CHÍNH XÁC.
- `AdminResetPasswordView` đặt cờ mà **quên xoá đệm user**: 60 giây sau khi trợ
  giảng đặt lại mật khẩu vì nghi tài khoản bị chiếm, người đang chiếm vẫn thao
  tác bình thường.
- Điều hướng thiếu `?lan-dau=1` nên trang đích tặng người dùng một nút "Quay lại
  Trang của tôi" — dẫn thẳng về đúng màn hình hỏng ở A1.

### [x] Hai màu còn sót ở bộ tối
`.dash-prog-pct` nhận màu khoá học qua **kiểu nội tuyến từ JS** (`#4C1D95` tím
sẫm) — kiểu nội tuyến thắng mọi luật CSS nên `body.dark` không cứu được. Đo:
**1,6:1 → 5,28:1**, và `style` nội tuyến nay là `null`. `.lb-row-me .lb-name`
/`.lb-value`: 4,38 → 5,36.

### [ ] T67 · Đặt lại mật khẩu KHÔNG thu hồi token cũ
Cờ và bộ đệm nay xử đúng, nhưng refresh token cấp trước đó vẫn sống. Nên "đặt
lại mật khẩu" mới chỉ chặn được lần ĐĂNG NHẬP sau, chưa cắt phiên đang mở —
đúng cảnh trợ giảng dùng nó để đuổi người đang chiếm tài khoản. Cần đưa token
của người bị reset vào danh sách đen.

### [ ] T68 · Bảng chấm lớp lớn: 692 KB JSON dựng trong một lượt
Đo với 35 em × bài làm 20 000 ký tự: **2 272 ms, 1 008 840 byte** nhét cả vào
HTML server-render lẫn state React. Chưa phải lỗi (lớp thật chưa tới cỡ đó)
nhưng là trần quy mô nhìn thấy được. Hướng: chỉ gửi đoạn đầu bài làm, tải đủ
khi bấm "Xem bài làm".

### [ ] T69 · `/courses/<id>` hỏng CSS ở bộ TỐI (ngoài phạm vi đợt này)
`course_detail.css` còn màu bộ SÁNG lọt vào nền tối: `.cd-lesson-title` 1,93:1,
`.cd-lesson-num` 1,41:1, `.cd-lesson-icon` 1,34:1. Danh sách bài học không đọc
được ở bộ tối là chuyện học viên gặp hằng ngày.

### Ghi nhận: một phép kiểm của tôi xanh vì LÝ DO SAI
`accounts/tests.py` gửi `current_password`/`new_password` trong khi `PasswordView`
đọc `current`/`new`. Nên 400 nhận được là "thiếu trường", không phải "sai mật
khẩu" như chú thích nói — **nó vẫn xanh kể cả khi `PasswordView` hỏng hẳn**. Đã
sửa cho gọi đúng tên trường và khẳng định đúng thứ cần khẳng định.

### [x] T69 (XONG 31/08) · `/courses/<id>` hỏng CSS ở bộ TỐI
Cùng bệnh với dashboard: hex viết cứng bỏ lỡ đợt chuyển token, và **năm luật
`body.dark` tự viết hex riêng** nên chúng đè lên token đã được vá. Danh sách bài
học — thứ học viên mở mỗi ngày — đo được `.cd-lesson-num` **1,41:1**,
`.cd-lesson-title` 1,93:1, biểu tượng bài khoá còn giữ nguyên nền SÁNG.

Bỏ hẳn năm luật `body.dark` viết cứng (token `--t3` đã có bản cho cả hai bộ màu,
nên chúng không những thừa mà còn là chỗ để lệch), đổi 14 mã màu sang token.
Nhân tiện dọn cả bộ sáng: ngôi sao rỗng 1,47:1 → 3,30 (là HÌNH chỉ trạng thái,
ngưỡng 3:1), điểm đánh giá hổ phách 2,15:1 → dùng `--warning-ink`.

Đo: **6 lỗi bộ tối và 7 lỗi bộ sáng → 0/0**, trên 74 và 79 phần tử. Đã xem ảnh.

### [ ] T70 · Trang chi tiết khoá học có thanh điều hướng RIÊNG, lệch với trang chính
`courses/[courseId]/page.tsx` chép lại khối topbar thay vì dùng `<Topbar />`:
nó hiện "Kỹ năng" và thiếu "Kế hoạch", "Thi thử", "Bài tập". Nên mục nav mới
thêm hôm nay không có ở đó, và mọi mục thêm sau này cũng vậy. Hai bản sao của
một khối điều hướng là hai bản sẽ trôi khỏi nhau — đã trôi rồi.

**Vá phần thực dụng 31/08:** thêm ba mục còn thiếu ("Kế hoạch", "Thi thử",
"Bài tập") vào bản sao đó, dùng đúng idiom `location.href` của trang. Đo: 8 mục,
chip hiện đủ 79/79px ở 1280 và 57/57px ở 390, không tràn ngang. GỘP về một bản
vẫn còn nợ — nó cần đổi cả cơ chế nạp biểu tượng (emoji ở đây, `icons.js` ở kia)
và cả cách điều hướng (`location.href` ở đây, `navigate()` của main.js ở kia).


---

## 31/08/2026 (tiếp) — anh chốt ba quyết định, làm luôn hai cái không cần chờ

### [x] T67 (XONG) · Đặt lại mật khẩu nay CẮT phiên đang mở
Anh chốt: **thu hồi hết, đá ra ngay**.

Danh sách đen của SimpleJWT một mình không đủ — nó chỉ chặn được REFRESH token,
còn ACCESS token kiểm bằng CHỮ KÝ chứ không tra CSDL nên sống đủ 30 phút bất kể
ta làm gì. Nên cần **hai hàng rào cho hai loại token**:
- Lược đồ **§39**: cột `users.tokens_valid_from`. Token có `iat` sớm hơn mốc này
  bị từ chối ngay ở lớp xác thực. Đã áp vào Neon (24 → 25 cột, 5 tài khoản đều
  `NULL` nên không ai bị đá ra).
- Mọi refresh token còn hiệu lực bị đưa vào danh sách đen.

**Không dùng lại `password_changed_at`**: cột đó đã mang nghĩa khác và đang được
đọc (`IS NULL` = "vẫn dùng mật khẩu tạm", `exports.py`), mà chính đường đặt lại
mật khẩu SET nó về NULL — đúng lúc cần ghi một mốc thì nó phải bị xoá.

**Cái bẫy 7 tiếng**: `iat` là giây UTC, `tokens_valid_from` là TIMESTAMP naive
giờ VIỆT NAM. So thẳng hai thứ là lệch đúng 7 tiếng — hoặc giết oan token mới,
hoặc để token cũ sống thêm 7 tiếng sau khi đã thu hồi. Có test riêng cho cả hai
hướng lệch.

Tự đổi mật khẩu cũng cắt phiên (người ta đổi chính vì nghi có ai đang dùng tài
khoản mình), nên màn hình đi thẳng về `/login?vua-doi-mat-khau=1` với câu giải
thích — thay vì về dashboard rồi bị 401 và nhảy trang hai lần.

### [x] T62 (XONG) · Một định nghĩa "chậm", dùng chung
Anh chốt: **đếm mọi việc quá hạn**.

Không sửa được bằng cách chỉnh câu SQL bên `teaching/reports` cho giống: phép
suy "mục nào đã xong" CÓ TRẠNG THÁI (mỗi lượt thi thử tick đúng một mục, duyệt
theo `sort_order`). Nên tách hẳn vòng duyệt ấy thành `stats/plan._duyet_muc` —
**nơi duy nhất** định nghĩa "chậm" — rồi:
- `plan.read` (màn hình học viên) gọi nó;
- `plan.do_cham_theo_hoc_vien(uids)` mới, gọi nó theo mẻ trong **ba câu SQL cho
  cả lớp** (gọi `read()` trong vòng lặp là 3 câu × 30 em);
- `teaching/reports._lag_by_user` **uỷ quyền** cho hàm mẻ đó, bỏ 38 dòng SQL
  riêng.

Đổi nhãn cả hai phía sang "**việc**" cho khớp phép đếm — trước đó giảng viên nói
"chậm 12 bài" trong khi em mở app thấy "chậm 14 việc".

Test hồi quy đỏ trên mã cũ với đúng câu: `em 12: giảng viên thấy 12, chính em
thấy 14`.

### [ ] Đang chạy · Audit khu HỌC VIÊN (anh chốt "tất cả, theo thứ tự")
Hai agent đang soi `stats/` và `lessons/ quizzes/ roadmap/ courses/` — hai khu
CHƯA từng được audit lần nào, mà 99% người dùng ở đó.
