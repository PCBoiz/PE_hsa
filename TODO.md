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

### [x] T19 (XONG) · Mã chết — nhưng DANH SÁCH NÀY PHẦN LỚN ĐÃ SAI
Rà lại từng mục 01/09/2026. Bốn trong bảy mục **không còn đúng**, và bản ghi chép
này chính là thứ nó tố cáo: một danh sách chép tay thì sẽ trôi (§20, cùng họ với
T21 ngay dưới).

| Mục | Sự thật 01/09/2026 |
|---|---|
| `Toast.tsx` "0 lời gọi" | SAI — dùng ở 3 màn (`MyAssignments`, `Grading`, `Sessions`) |
| "7 chỗ còn `alert()`" | SAI — `src/` còn đúng **1**, và nó nằm trong chú thích |
| `Chip.LEVEL_TONE` "0 lời gọi" | SAI — `Chip.tsx:48` dùng, `ui/index.ts` xuất ra |
| `_pick_roadmap_template` | SAI — `roadmap/views.py:51` gọi |
| 27 bộ chọn CSS mermaid | ĐÚNG → gỡ **77 dòng** khỏi `dashboard.css` |
| `'oauth-complete'` | ĐÚNG → gỡ khỏi `ISSUES_TOKENS` |
| hai endpoint CSV của lớp | ĐÚNG là chưa có nút — nhưng **KHÔNG xoá** (xem dưới) |

**Hai endpoint CSV: gắn nút chứ không xoá.** `attendance.csv` (bảng chéo, đúng
hình cuốn sổ điểm danh giấy) và `progress.csv` (lọc theo cột cảnh báo sớm) là thứ
giảng viên cần; xoá đi là vứt một tính năng đã viết xong vì nó thiếu một cái nút.
Đặt ở màn buổi học — màn giảng viên thực sự mở cho một lớp, vì không có màn báo
cáo cấp lớp (`bao-cao/` chỉ có cấp học viên). Kiểm bằng cách bấm thật: cả hai trả
`200 text/csv` với tiêu đề tiếng Việt, nút cao 46px, 0 lời gọi ghi.

**`'oauth-complete'` đáng gỡ vì lý do BẢO MẬT, không chỉ vì chết:** nhánh dùng nó
chỉ chạy với `POST`, mà `accounts/oauth.py::oauth_complete` là chuyển hướng GET
của allauth ở phía Django. Giữ lại là nới rộng vô cớ một danh sách trắng CẤP
TOKEN — thứ đáng ra phải hẹp nhất có thể.

### [ ] T20 · Gom trùng lặp
`common/paging.py` (`read_paging`, `page_with_total` — nhân rộng ý tưởng
`LEFT JOIN LATERAL`), `common/params.py` (`read_date_range` — luật "`to` tính cả
ngày đó" đang viết lại ở hai chỗ), `teaching/classes.py` (hai `_class_row` cùng
tên), hạ `_temp_password`/`_user_label` xuống `common/`, `readCookie` ba bản y
hệt → `lib/auth.ts`, `type Payload` khai hai lần.

### [x] T21 (XONG) · Chú thích khẳng định sai sự thật
- `sessions.py:21` "số câu cố định" — **nay ĐÚNG**: `_emit_events` đã chuyển sang
  `record_events` (một câu cho cả lớp). Không phải sửa gì.
- `legacy_schema.sql` liệt kê động từ nhật ký, ghi `user.password` trong khi hằng
  thật là `user.password_reset`. Sửa bằng cách **bỏ hẳn danh sách chép tay** và
  chỉ tay sang `common/audit.py` (20 hằng): một danh sách chép tay là một danh
  sách sẽ trôi, và người đọc tin nó rồi thôi không đi kiểm.
- `legacy_schema.sql` hai câu mâu thuẫn — câu đầu ("DO $$ vì…") còn sót từ thời
  khối `DO`, trong khi mã đã đổi sang DROP-rồi-ADD. Gộp lại còn một câu đúng.
- `EmptyState.tsx` nói "bắt buộc có action hoặc hint" mà cả hai đều `?`. Sửa
  bằng cách **ép ở KIỂU** (union hai nhánh) chứ không hạ giọng chú thích — nay
  quên cả hai là lỗi biên dịch, không phải một ngõ cụt lặng lẽ. `tsc` xanh trên
  cả 11 chỗ đang dùng, và đã kiểm nó ĐỎ được (TS2322 với `<EmptyState title/>`).

### [x] T22 · Hai hình dạng JSON lỗi → `[object Object]` — XONG 30/08 (gộp vào T49)
`errorText()` trong `lib/api.ts` đọc được cả ba hình dạng, có bảng câu tiếng Việt
theo mã HTTP làm mức cuối. Đo ba ca đã hỏng, `[object Object]` biến mất.
CÒN LẠI ở T47: `serverJson` (tầng dựng trang) vẫn vứt toàn bộ thân lỗi.

<details><summary>Ghi chép gốc</summary>

`common/errors.py` trả `error` là **object**; view mới trả `error` là **chuỗi**.
`AccountsClient.tsx:147,197` và `SessionsClient.tsx:197,289,326` chỉ xử lý chuỗi.
Trợ giảng bấm nhanh → 429 → banner đỏ hiện `[object Object]`.
</details>

### [x] T23 (XONG) · `MAX_BATCH` khai hai nơi — máy chủ đã gửi con số xuống
`teaching/admin_users.py` trả `maxPerBatch` trong kết quả xem trước. Frontend nay
đọc nó (`tranMe = preview?.maxPerBatch ?? MAX_BATCH_DUONG_LUI`) ở CẢ HAI chỗ —
trước đó câu gợi ý dùng hằng chép tay còn cảnh báo "quá trần" mới đọc máy chủ.
Hằng còn lại được đổi tên thành `MAX_BATCH_DUONG_LUI` và chú thích nói rõ nó chỉ
dùng khi CHƯA hỏi máy chủ lần nào — vì con số thật tính từ chi phí băm mật khẩu,
tức nó sẽ đổi khi đổi máy, còn hằng chép tay thì không.

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

### [x] T60 (XONG) · Kỳ in trên giấy ≠ kỳ dùng để tính, khi em học lại lớp cũ
> Vá 01/09/2026: `parent_report` lấy TẤT CẢ các đợt (`class_members`) chứ không
> `LIMIT 1`, và chuyên cần bó theo HỢP của các đợt — buổi trong quãng nghỉ vẫn
> bị loại. Khối `membership` nay lấy ngày vào của đợt ĐẦU, ngày rời để trống
> nếu còn đợt đang mở, và thêm `stints` để tờ giấy nói được vì sao hai mốc ấy
> không liền một mạch.
>
> Test hồi quy đi qua VIEW thật, ĐỎ trên mã cũ với đúng con số của cảnh này:
> `sessionsCounted 1, present 0` — tức phụ huynh nhận tờ giấy ghi 0% trong khi
> em có mặt đủ hai buổi của đợt trước. Hiện 0 cặp (lớp, em) có nhiều đợt, nên
> đây là lỗi TIỀM ẨN — nhưng nó in ra giấy gửi về nhà.
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

### [x] T62 (XONG cả hai nửa) · Hai nơi trả lời cùng một câu hỏi bằng hai phép tính
> Nửa "chậm bao nhiêu": xong 31/08 (`reports._lag_by_user` ủy quyền cho
> `stats.plan`).
>
> Nửa BẢN ĐỒ NĂNG LỰC, vá 01/09/2026. `reports` dựng ô từ cột `topic` của SỰ
> KIỆN, `competency` giao với danh mục `lessons.module`. Sự kiện giữ tên chủ đề
> LÚC NÓ XẢY RA, nên sau một lần đổi tên chương: màn của em hiện ô MỚI trống
> trơn, bảng của giảng viên hiện ô CŨ có dữ liệu — và không ai biết vì sao.
>
> Nay cả hai đi qua `competency.chu_de_trong_giao_trinh()`. Và thêm một CHUÔNG
> BÁO: `stats/tests.py` đọc dữ liệu thật, đỏ ngay ngày ai đó đổi tên chương mà
> quên chép ngược `learning_events.topic` — chứ không phải sáu tháng sau khi có
> người hỏi "sao ô Số học của em trống". Đã kiểm chuông REO ĐƯỢC: chèn một chủ
> đề không có thật trong giao dịch → bắt được; cuộn lại → sạch.
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

### [x] T64 (XONG) · `must_change_password` chỉ ép ở frontend
> Kiểm lại 01/09/2026: hàng rào nằm ở LỚP XÁC THỰC
> (`accounts/authentication.py::CachedJWTAuthentication`) với danh sách trắng
> `CHO_PHEP_KHI_PHAI_DOI_MK` so khớp CHÍNH XÁC (không so tiền tố). Đặt ở lớp xác
> thực chứ không ở `DEFAULT_PERMISSION_CLASSES` vì view khai
> `permission_classes` riêng sẽ ghi đè danh sách mặc định.
Backend không view nào từ chối khi cờ còn TRUE: tài khoản mật khẩu tạm gọi
thẳng `GET /api/user`, `GET /api/stats` đều 200. Trợ giảng biết mật khẩu tạm
(vừa đọc cho học viên) dùng được toàn quyền tài khoản trong cửa sổ trước khi em
đổi. Hẹp về thời gian nên xếp sau, nhưng nó là hàng rào chỉ tồn tại ở lớp vẽ.

### [x] T65 (XONG) · `meeting_url` không kiểm lược đồ
> Vá 01/09/2026: danh sách trắng lược đồ ở ĐẦU VÀO (`_clean_class_payload`),
> chỉ `https://` và `http://`. Chặn ở đầu vào chứ không ở chỗ hiển thị: chỗ
> hiển thị có thể mọc thêm (bản in, email nhắc lịch, ứng dụng di động), còn
> đường ghi thì chỉ có một. Test phủ `javascript:`, `JavaScript:`, `data:`,
> `vbscript:` và một link Google Meet thật — ĐỎ trên mã cũ (nhận 201).
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

### [x] T62 (XONG) · Hai nơi đếm "chậm" — nguyên nhân SÂU HƠN đã nghĩ
> Kiểm lại 01/09/2026: `teaching/reports.py::_lag_by_user` ỦY QUYỀN cho
> `stats.plan.do_cham_theo_hoc_vien`. Không viết lại SQL cho giống được vì phép
> suy "mục nào đã xong" CÓ TRẠNG THÁI.
Không chỉ khác bộ lọc `kind`. Hai bên còn hỏi hai BẢNG khác nhau để biết "bài
này xong chưa": `stats/plan._done_lookup` đọc `learning_events` (`meta.lessonNo`),
`teaching/reports._lag_by_user` đọc `lesson_progress` JOIN `lessons.sort_order`.
Hôm nay chúng tình cờ khớp. Một dòng lệch giữa hai bảng là hai con số lệch mà
không ai giải thích được. Đo thật hôm nay: uid 12 — học viên thấy **14**, giảng
viên thấy **12**. Cần chốt MỘT nguồn trước khi sửa.

### [x] T60 (XONG) · Kỳ in trên giấy ≠ kỳ dùng để tính
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

### [~] T53-b · Còn lại của khối tiếp cận — rà lại 01/09/2026
Hai mục hoá ra **không còn đúng**, một mục hoá ra **sai từ đầu**:

- **`/dashboard` hiện số 0 giả lúc đang tải — ĐÃ VÁ.** Đo bằng cách làm chậm mọi
  lời gọi đọc 2,5 giây rồi chụp lúc 1,2 giây: bốn ô đều hiện dấu `—`, không phải
  `0`. Cả thanh tiến trình cũng để trống.
- **`HTTP_VI` có nhánh chết — SAI.** Mọi lỗi qua DRF đều mang khoá `error`
  (`common/errors.api_exception_handler` là `EXCEPTION_HANDLER`), nên `errorText`
  trả câu của máy chủ. Nhưng lỗi ở tầng DƯỚI DRF thì không có khoá ấy: 502 lúc
  Render khởi động lại, 504, 413 của reverse proxy, trang lỗi HTML thô. Đó đúng
  là lúc 12 câu tiếng Việt kia được dùng — và ở một trung tâm chạy 4G thì đó là
  lỗi hay gặp. **Không xoá.**
- **Mục điều hướng đang mở nằm NGOÀI tầm nhìn trên điện thoại — mục MỚI, đo hôm
  nay.** Thanh nav `overflow-x: auto` có 8–10 mục mà ở 390px chỉ thấy 159px. Mở
  `/dashboard#skills` thì trang Kỹ năng hiện đúng nhưng mục "Kỹ năng" nằm ở
  238–282 trong khi thanh chỉ thấy 62–221 và `scrollLeft` = 0. Người dùng đang ở
  một trang mà thanh điều hướng không cho biết mình ở đâu. Vá: `navigate()` kéo
  mục đang mở vào giữa tầm nhìn (`block: 'nearest'` để không cuộn dọc cả trang).
  Đo lại: `scrollLeft` 0 → 118, mục nằm gọn trong khung.

Còn thật: chưa có `loading.tsx` · chưa có nút đổi bộ màu trong khu `(standalone)`
· bóng đổ bộ tối là mã chết · chính tả dấu không nhất quán (khóa/khoá, hủy/huỷ,
xóa/xoá).


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

### [x] T67 (XONG) · Đặt lại mật khẩu KHÔNG thu hồi token cũ
> Kiểm lại 01/09/2026: `teaching/views.py` đặt `tokens_valid_from`, gọi
> `_thu_hoi_refresh(user_id)` và `invalidate_user_cache(user_id)`. Ba thứ, vì
> mỗi thứ bịt một lỗ khác nhau: danh sách đen chỉ chặn được REFRESH token
> (access token kiểm bằng chữ ký, sống nốt 30 phút), còn bộ đệm user 60 giây
> khiến hàng rào chậm một phút.
Cờ và bộ đệm nay xử đúng, nhưng refresh token cấp trước đó vẫn sống. Nên "đặt
lại mật khẩu" mới chỉ chặn được lần ĐĂNG NHẬP sau, chưa cắt phiên đang mở —
đúng cảnh trợ giảng dùng nó để đuổi người đang chiếm tài khoản. Cần đưa token
của người bị reset vào danh sách đen.

### [ ] T68 · Bảng chấm lớp lớn: 692 KB JSON dựng trong một lượt
Đo với 35 em × bài làm 20 000 ký tự: **2 272 ms, 1 008 840 byte** nhét cả vào
HTML server-render lẫn state React. Chưa phải lỗi (lớp thật chưa tới cỡ đó)
nhưng là trần quy mô nhìn thấy được. Hướng: chỉ gửi đoạn đầu bài làm, tải đủ
khi bấm "Xem bài làm".

### [x] T69 (XONG — xem mục cùng số ở dưới) · `/courses/<id>` hỏng CSS ở bộ TỐI
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

### [x] T70 (XONG) · Trang chi tiết khoá học có thanh điều hướng RIÊNG
`courses/[courseId]/page.tsx` chép lại khối topbar thay vì dùng `<Topbar />`:
nó hiện "Kỹ năng" và thiếu "Kế hoạch", "Thi thử", "Bài tập". Nên mục nav mới
thêm hôm nay không có ở đó, và mọi mục thêm sau này cũng vậy. Hai bản sao của
một khối điều hướng là hai bản sẽ trôi khỏi nhau — đã trôi rồi.

**Vá phần thực dụng 31/08:** thêm ba mục còn thiếu ("Kế hoạch", "Thi thử",
"Bài tập") vào bản sao đó, dùng đúng idiom `location.href` của trang.

**Vá phần GỐC 01/09/2026 — và nó lộ ra một trang KHÔNG VÀO ĐƯỢC.** Rà lại thì
danh sách đã trôi theo **cả hai chiều**: bản CHÍNH thiếu **"Kỹ năng"**. Mà
`page-skills` không phải khung trống — đo 01/09/2026 nó chạy đầy đủ với dữ liệu
thật: *20 kỹ năng · 1 đạt · 1 cần ôn · 18 chưa bắt đầu*, có ô tìm kiếm riêng và
`dashboard.js::renderSkills` nạp dữ liệu. Nghĩa là suốt thời gian đó, cách duy
nhất vào được trang ấy là **đi vòng qua màn chi tiết khoá học**, hoặc tự gõ
`#skills`. Một trang đầy đủ mà không có đường nào tới từ thanh điều hướng chính.

Không gộp hai BẢN DỰNG (làm thế phải kéo main.js + dashboard.js vào màn học viên
mở hằng ngày — rủi ro lớn hơn giá trị). Thay vào đó tách phần SINH RA sự trôi:
danh sách mục nay nằm ở `components/navMuc.ts`, cả hai bản dựng cùng đọc từ đó.
Bản dựng vẫn riêng (emoji vs `icons.js`, `location.href` vs `navigate()`), nhưng
thêm một mục là sửa đúng một chỗ.

Đo sau khi vá: hai thanh ra **cùng 8 mục, cùng thứ tự**, trạng thái "đang mở"
đúng ở mỗi bên; bấm "Kỹ năng" từ dashboard → `page-skills`. Giao diện đo lại:
0 · 0 · 0 · 0/171.


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


---

## Audit khu HỌC VIÊN 31/08/2026 — hai khu chưa ai soi, và lỗ nặng nhất cả sản phẩm

Hai agent soi `stats/` và `lessons/ quizzes/ roadmap/ courses/`. 8 + 11 phát
hiện đã chứng minh. Anh chốt ba quyết định trước khi tôi bắt tay.

### [x] L1 (XONG) · Đáp án đi xuống trình duyệt TRƯỚC khi học viên trả lời
**Nặng nhất cả phiên.** Đo trong trình duyệt thật, ngay khi trang vừa mở:
`GET /api/courses/hsa_quantitative/content` → **297 trường `answer`** của cả
khoá, kể cả người chưa ghi danh. Và điểm thì do chính trình duyệt tự chấm rồi
tự khai: `POST complete {"quizScore": 999999}` → 200, ghi thẳng vào CSDL.

Nghĩa là con số nuôi bản đồ năng lực, sổ điểm của giảng viên và nhánh lý thuyết
thích ứng là con số HỌC VIÊN TỰ KHAI. Toàn bộ hệ đo lường của trung tâm không
có giá trị chứng cứ.

Anh chốt **vá toàn diện**. Đã làm:
- `lessons/grading.py` mới — nơi DUY NHẤT biết đáp án. Ba luật: đáp án không rời
  máy chủ trước khi học viên trả lời · điểm được TÍNH chứ không được NHẬN · đáp
  án đúng chỉ lộ SAU khi đã nhận câu trả lời cho đúng câu đó.
- `bo_dap_an` cắt `answer`/`explain` ở `content.py` — tức ở TẦNG ĐỌC, không ở
  từng view, để một endpoint mới quên cắt không làm lộ lại toàn bộ.
- `POST /api/courses/<khoá>/lessons/<số>/check` — chấm ở máy chủ, có đệm 60 giây
  cho bảng đáp án và cho phép kiểm ghi danh (đo: 270ms → **1ms** từ lần thứ hai,
  đủ cho phòng luyện bấm giờ).
- `CompleteLessonView` nhận `answers` và tự chấm. `quizScore` từ engine bản cũ
  bị **BỎ QUA** — bài vẫn hoàn thành, XP vẫn cộng, nhưng không ghi một con số
  người dùng tự khai. "Không biết điểm" và "điểm 100 vì người dùng nói thế" là
  hai chuyện khác nhau.
- Có ghi danh mới đọc được nội dung.
- Engine (`lesson_hsa.js`) gọi đường chấm; phần xem lại vẽ đáp án và lời giải
  TỪ phản hồi máy chủ.

Đo lại end-to-end trong trình duyệt: nội dung **0 đáp án** · em trả lời 2 đúng 1
sai → máy chủ chấm **2/3** · đáp án và lời giải hiện ra sau khi nộp · thân
`/complete` gửi `answers`, không còn `quizScore`. **9/9 phép kiểm.**

`lessons/tests.py` mới — 8 phép kiểm, trong đó hai cái quan trọng nhất (đáp án
có lộ không · chưa ghi danh có đọc được không) CHẠY ĐƯỢC trên mã cũ và đỏ ở đó
đúng lý do.

### [x] L2 (XONG) · Hai trong bốn học viên thật đang hỏng
Em id 9 học xong 5 bài nhưng `enrollments` rỗng → "Khoá học của tôi" trống,
trang khoá 0%, quiz ôn tập khoá vĩnh viễn — trong khi trang Kỹ năng nói 19%.
Nguyên nhân: đường DUY NHẤT tạo dòng `enrollments` là nút "Đăng ký học" ở trang
chi tiết khoá; vào thẳng `/lesson/<khoá>` thì học được nhưng không ghi danh — mà
đó chính là đường mọi liên kết "Học tiếp" dẫn tới.

`CompleteLessonView` nay tự ghi danh. Dữ liệu cũ: anh chốt vá luôn trên Neon —
chạy khô in ra đúng hai dòng rồi mới áp, `enrollments` 4 → 6, các bảng khác
không đổi một dòng. Đo lại: `/api/enrolled` của em 9 nay trả 19%.

### [x] L3 (XONG) · Đồng hồ UTC còn sót
`roadmap_progress.completed_at`, `roadmaps.updated_at`, `enrollments.enrolled_at`
còn dùng `now()` của SQL — lệch 7 tiếng. Cửa sổ hỏng là 00:00–07:00 giờ VN: ghi
danh lúc 00:30 ngày 1/9 được lưu thành 17:30 ngày 31/8. Nay đều `local_now()`.

### [x] L4 (XONG) · Thi thử — anh chốt "một lượt tính điểm, làm lại không cộng XP"
Đo được: nộp RỖNG → nhận đủ 9 đáp án → nộp lại → **9/9, +100 XP**; không giới
hạn lượt; đồng hồ hoàn toàn ở máy khách (`duration_seconds` nhận cả **−5000**);
`started_at` có cột nhưng KHÔNG dòng mã nào ghi; `MockSubmitView` không lọc
`is_published`.

Ba luật mới, ghi ngay đầu `mockexam/views.py`:
1. **Đồng hồ thuộc máy chủ.** `POST /start` mở dòng `mock_attempts` với
   `started_at`; thời lượng là hiệu hai mốc máy chủ tự ghi. F5 giữa chừng thì
   NỐI TIẾP lượt đang mở chứ không được cấp lại 20 phút.
2. **Đáp án chỉ lộ theo câu ĐÃ trả lời.** Bỏ trống thì lúc nộp không nhận được
   đáp án của câu đó — cùng luật với `lessons/grading.py`.
3. **Một lượt vào sổ.** Cột `counted` (§40). Lượt đầu nộp đúng giờ mới tính
   điểm, cộng XP, ghi `learning_events`. Làm lại vẫn được chấm và xem lại, chỉ
   không cộng gì. Nộp quá giờ + 2 phút ân hạn cũng không vào sổ.

Kèm: `MockSubmitView` lọc `is_published`; ba nơi đọc `mock_attempts` phải tránh
dòng ĐANG MỞ — đáng kể nhất là "điểm đề gần nhất" ở Trang của tôi, vì Postgres
xếp NULL **lên đầu** trong `ORDER BY ... DESC` nên vừa bấm "Bắt đầu" là báo 0/0.

CỐ Ý không siết: nhiệm vụ ngày "Làm 1 đề thi thử" vẫn đếm MỌI lượt nộp. Đo
31/08/2026: toàn hệ chỉ có **một** đề đã xuất bản, nên lọc `counted` ở đó là
làm nhiệm vụ này hỏng vĩnh viễn với người đã thi. Nó là nhiệm vụ THÓI QUEN, và
`user_missions` đã khoá theo (user, nhiệm vụ, ngày) nên không cày được.

Giao diện nói ra ở CẢ HAI đầu: nhãn "Lượt luyện · không tính điểm" hiện ngay
thanh đầu TRƯỚC khi làm, và ô giải thích sau khi nộp.

`mockexam/tests.py` mới — 11 phép kiểm, **11/11 đỏ trên mã cũ**, trong đó bảy
cái đỏ bằng AssertionError đúng lý do (nặng nhất: *"nộp rỗng vẫn nhận được đáp
án của 3 câu"*). Trình duyệt thật: 10/10.

### [x] L4b (XONG) · /mock bỏ qua lựa chọn nền tối của học viên
Phát hiện khi đo tương phản ô ghi chú mới: hai chế độ ra **cùng một con số** —
dấu hiệu bật nền tối không đổi được gì. `mock.css` khai cầu token
(`--mk-t1: var(--t1, …)`) ở `:root`, mà công tắc nền tối của app là class
`body.dark` — **hậu duệ** của `:root`. `var(--t1)` trong khai báo đặt ở `:root`
được thay ngay tại `:root`, nơi `body.dark` chưa tồn tại.

Đo: học viên chọn nền tối → `--t1` trên body đổi thành `#E2E8F0` nhưng
`--mk-t1` vẫn kẹt `#16121F`; trang hiện SÁNG, chỉ còn viền `body` tối lòi ra
quanh mép. Vá: khai lại cầu trên `:root, body`. Đo lại: nền tối ra đúng
`fg=226,232,240 / bg=7,9,15`, **0 chỗ dưới 4.5:1 ở cả hai chế độ**.
`lesson_hsa.css` KHÔNG mắc bệnh này (nó dùng token thẳng trong quy tắc).

### [x] L5 (XONG) · Học viên tạo được bài học GIẢ trong bảng dùng chung
`_resolve_lesson_id` INSERT vào `lessons` từ endpoint của học viên: đo được một
dòng `"<b>BAI GIA MAO</b>"` với `sort_order 9999`. `SkillsView` đọc `lessons`
không lọc theo user, nên dòng giả hiện trong trang Kỹ năng của MỌI học viên.

Đo trước khi sửa, và con số đo quyết định cách sửa: **cả 76 bài của ba khoá đều
đã có `content_json`**, không còn dòng stub nào, và bản dự phòng nội dung phía
client đã bỏ từ 19/08/2026. Nghĩa là bài học viên học được thì LUÔN có dòng sẵn;
nhánh tạo stub chỉ còn là cái lỗ. Nay `_tim_bai` CHỈ ĐỌC, không có thì trả 404.

Kèm ba thứ cùng họ, đều là "nhận thay vì tính":
- **XP** lấy từ `content_json.xp_reward` chứ không từ `xpEarned` của thân
  request. Bản cũ kẹp 0–500 rồi cộng thẳng: `{"xpEarned": 500}` cho 76 bài là
  38.000 XP thay vì 3.800 — mà bảng xếp hạng thì các em thi nhau thật.
- **Tiêu đề trong nhật ký** lấy từ dòng `lessons`, không từ thân request.
- **Kết quả phòng luyện** — xem L5b.

KHÔNG làm: chặn "đánh dấu xong bài chưa mở khoá". Rà cả frontend lẫn backend
31/08/2026: sản phẩm này **không có luật mở khoá tuần tự** ở đâu cả, và kế hoạch
học còn cố ý giao bài theo CHỦ ĐỀ chứ không theo thứ tự. Dựng một cái khoá chưa
từng tồn tại là bịa ra luật mới, không phải vá lỗi.

### [x] L5b (XONG) · HỒI QUY CỦA CHÍNH TÔI: phòng luyện chấm sai mọi câu
`bo_dap_an` (đẩy lên trong `a8f4c5e` sáng nay) cắt cả đáp án phòng luyện, mà
`answerDrill` chấm tại chỗ bằng `norm(val) === norm(q.answer)` — so với
`undefined`, nên **mọi câu đều sai**: combo không bao giờ nổ, XP luôn 0, "Chính
xác 0%". Tôi đẩy lỗi này lên `origin/erp` trước khi phát hiện.

Cắt là ĐÚNG: `KIND_DRILL` nằm trong `stats/competency.KIND_TO_SOURCE`, tức
phòng luyện là một nguồn của bản đồ năng lực, nên đáp án của nó phải bí mật y
như bài kiểm tra đầu vào. Cái sai là chỗ CHẤM. Nay:
- `answerDrill` gọi `/check` từng câu (nằm gọn trong 470ms hiển thị phản hồi vốn
  đã có; đường chấm có đệm 60 giây nên từ câu thứ hai là 1ms).
- Lúc hoàn thành chỉ gửi `drill.answers`; `cham_phong_luyen` dựng lại số câu
  đúng VÀ chuỗi combo theo THỨ TỰ CÂU TRONG ĐỀ.
- Màn chúc mừng lấy XP từ phản hồi máy chủ.

Đo trong trình duyệt thật: gửi 6 đúng 2 sai → **"6/8 Đúng · 75% Chính xác ·
combo ×3 · +75 XP"**, 8 lời gọi `/check`, thân `/complete` chỉ mang `answers`.
**10/10 phép kiểm.**

### [x] L6 (XONG) · Làm lại bài ghi đè điểm cũ bằng điểm mới THẤP HƠN
> Kiểm lại 01/09/2026: `lessons/views.py:328` nay `quiz_score = COALESCE(cũ, mới)`
> — điểm ĐẦU giữ, đúng luật "lượt đầu vào sổ".
`quiz_score` dùng `COALESCE` trong khi `xp_earned` dùng `GREATEST` — cùng một
bảng, hai chính sách. Ôn lại bài đã 100 rồi bấm cẩu thả là điểm tụt, không có
đường khôi phục.

### [x] L7 (XONG) · Anh chốt: học lại bài cũ GIỮ NGÀY ĐẦU
> Kiểm lại 01/09/2026: `common/events.py:145` `event_date = LEAST(cũ, mới)`.
`lesson_progress.completed_at` giữ lần đầu nhưng `learning_events.event_date`
nhảy sang hôm nay → đường cong tiến bộ của tuần trước ĐỔI HÌNH DẠNG, và "Chỉ
tiêu tuần" nhích lên trong khi "Nhiệm vụ ngày" vẫn 0/1. Cần `event_date` giữ lần
đầu, "hoạt động gần nhất" chuyển sang đọc `occurred_at`.

### [x] L8 (XONG) · Anh chốt: điểm thi thử GIỮ nhưng TÁCH hiển thị
> Kiểm lại 01/09/2026: `competency.py:264` trả `masteryTopic`; `plan.py:111`
> `_diem_chu_de` dùng nó để xếp lịch ôn; `dashboard.js:2871` hiện hai số.
Điểm cả đề đang tính 25% vào TỪNG ô chủ đề. Đại số của em id 9 đáng lẽ 62, hiện
42 → dưới ngưỡng 60 → hệ xếp **17 buổi "Ôn lại Đại số"** vào lịch của em. Cần ô
hiện hai số rõ ràng ("chủ đề 62 · đề thi thử 0") và chốt ngưỡng xếp lịch ôn dùng
số nào.

### [x] L9 (XONG) · `MIN_ACTIVITIES` gộp nhầm hai hoạt động khác loại
> Kiểm lại 01/09/2026: `competency.py:178` khoá `(ref_type, ref_id)`.
Đếm bằng `ref_id` trần, mà quiz #2 và bài học #2 là hai không gian id riêng. Đo:
cùng khối lượng học, một bên hiện 36 một bên hiện "—", khác biệt duy nhất là số
thứ tự trong CSDL. Sửa: khoá `(ref_type, ref_id)` — một dòng.

### [x] L10 (XONG) · Ngày thi HÔM NAY bị coi là "chưa đặt mốc thi"
> Kiểm lại 01/09/2026: `journal.py:254` và `plan.py:158` đều `is not None`.
`days_to_exam` trả `0`, và ba nơi tiêu thụ dùng `if days` — `0` là falsy. Còn 1
ngày → chế độ báo động (3 đề/tuần, cảnh báo "bỏ 68 bài"); còn 0 ngày → chế độ
thư thả (1 đề/tuần, cảnh báo biến mất, lịch trải 12 tuần). Và câu chữ "CHƯA ĐẶT
MỐC THI" là lời nói dối thẳng. Với ngày thi đã qua thì tình trạng này VĨNH VIỄN.

### [x] L11 (XONG) · Bốn endpoint trả 500 với tham số không phải số
`?weeks=abc`, `?limit=abc`, `?days=abc`, `?weeks=1e9` → 500. Tham số trên URL là
thứ NGƯỜI DÙNG gõ được, nên chỗ nào đọc số từ đó cũng phải trả ra màn hình mặc
định chứ không phải trang lỗi.

`common/params.so_nguyen(raw, mặc_định, lo, hi)`. Ba nơi khác trong repo đã tự
viết đúng khối `try/except` ấy (`forum/views._paging`, `teaching/sessions`) —
gom về một bản, vì ba bản tự viết là ba bản sẽ trôi khỏi nhau. Nhân tiện kéo
`MIN_WEEKS = 4` ra khỏi chỗ chôn trong `max(4, …)` giữa thân hàm.

`common/tests.py` mới — 13 phép kiểm. Lùi mã cũ: **6 phép kiểm endpoint đỏ bằng
đúng `500 == 200`**, 4 phép kiểm đơn vị đỏ vì mô-đun chưa tồn tại. Ba cái còn
lại (`?limit=-1`, `?weeks=0`, phân trang diễn đàn) XANH cả trên mã cũ — chúng là
phép kiểm HÀNG RÀO cho phần đã đúng sẵn, không tính vào thành tích.

### [x] L12 (XONG) · Kế hoạch vừa sinh đã có mục "đã xong"; `totals.done` lệch
> Phần mốc sàn: xong ở B16 (chính xác tới GIỜ).
> Phần `totals.done` (01/09/2026): mục đã xong bị đặt vào tuần DỰ KIẾN, nên một
> việc đến hạn tuần trước mà làm xong hôm nay rơi vào tuần đã qua — mà tuần đã
> qua thì không hiện. Người học tick xong thì việc BIẾN MẤT, còn ô tổng vẫn
> cộng thêm một: hai con số cạnh nhau không khớp. Nay đặt vào tuần MUỘN HƠN
> giữa tuần dự kiến và tuần thực sự hoàn thành — phép này chỉ tăng độ hiện,
> không bao giờ giảm. Test hồi quy đã chứng minh ĐỎ trên mã cũ (`weeks` rỗng
> trong khi `totals.done` = 1).
`floor` dùng thứ Hai của tuần sinh thay vì `generated_at`, nên hoạt động làm
TRƯỚC khi kế hoạch tồn tại vẫn tick nó. Và mục "Ôn lại" bị tick bởi một bài học
thường. Riêng `totals.done` thì mã làm NGƯỢC với chú thích của chính nó: chú
thích viết "không giấu đi", mã lọc `k >= today_key`.

### [x] L13 (XONG) · Xem lại quiz ôn tập hiện MÃ lựa chọn, không hiện lời giải
> Kiểm lại 01/09/2026: `quizzes/views.py` trả `explain` ở cấp câu hỏi + `*_text`.
In ra "Bạn chọn: o1 — Đáp án đúng: o2". `explanation` luôn `None` vì pool chỉ
dựng `{id, text, correct}`, trong khi dữ liệu gốc có `explain` ở cấp câu hỏi.

### [x] L14 (XONG) · Ngưỡng mở quiz ôn tập: ba cách phát biểu một luật
> Kiểm lại 01/09/2026: `quizzes/views.py:13` `MIN_QUESTIONS = 5`, và câu chữ
> trả về nói đúng "câu" kèm số đang có.
Ba câu phát biểu khác nhau cho cùng một luật.

### [x] L15 (XONG) · Điểm sao 5.0 trên mọi trang khoá là con số CỨNG
> Kiểm lại 01/09/2026: `courses/views.py` nhắc `course_ratings` 11 lần — cả
> bốn đường đọc đều JOIN.
`courses.rating` = 5.0 cho cả ba khoá; `course_ratings` rỗng; `CourseRatingView`
tính đúng nhưng KHÔNG ai gọi (grep frontend: 0 kết quả).


---

## Audit chéo hai agent 31/08/2026 — soi chính phần vừa viết

Hai agent đọc mã, mỗi agent một khu. Tôi tự kiểm lại từng phát hiện bằng chính
mã và bằng số đo trên Neon trước khi vá — có cái đúng, có cái tôi bác.

### [x] A1 (VÁ) · Bỏ qua `/start` là bỏ qua TOÀN BỘ giới hạn giờ
Nhánh "không có lượt đang mở" của `MockSubmitView` đặt `het_gio = False` vô điều
kiện rồi vẫn cho `counted=TRUE`. Cộng với `GET /api/mock-exams/<id>` phục vụ đủ
câu hỏi mà không mở đồng hồ: lấy đề → ngồi ba tiếng tra đáp án → nộp → 9/9 +
100 XP. Luật "đồng hồ thuộc máy chủ" chỉ ràng buộc được trình duyệt tử tế.

**Và bốn phép kiểm của tôi đi đúng đường đó rồi khẳng định nó ĐÚNG** — bộ kiểm
đang ghim lỗ hổng lại. Đó là chỗ đáng sợ hơn cả lỗ hổng.

Vá: nộp không qua `/start` thì vẫn chấm và vẫn lưu (đừng để em mất công) nhưng
KHÔNG vào sổ, KHÔNG cộng XP, không ghi sự kiện. Bỏ hẳn `GET /api/mock-exams/<id>`.

### [x] A2 (VÁ) · Hết giờ rồi bấm "Bắt đầu" lại = một lượt 20 phút mới, vẫn tính điểm
Bản đầu ngày XOÁ dòng đã cạn giờ rồi mở lượt mới; vì chưa từng nộp nên `counted`
lại TRUE. Lý lẽ của tôi ("dòng ấy chưa mang câu trả lời nào nên không có gì để
mất") đúng về câu trả lời và **bỏ sót thứ đã mất thật: đề đã lộ rồi**.

Vá: `counted` chốt ngay lúc MỞ, không đợi lúc nộp. Lượt cạn giờ được ĐÓNG LẠI
như một lần nộp, chấm chính phần đã lưu.

### [x] A3 (VÁ) · Lỡ F5 giữa bài là mất trắng bài làm
Hồi quy do chính bản vá của tôi: `/start` nối tiếp đúng đồng hồ nhưng trả
`answers = {}`, và vì `con > 0` nên không xin được lượt mới. Trước bản vá, F5
cấp lại 20 phút — dở về gian lận nhưng em không mất bài.

Vá: `POST /save` lưu tạm (gộp nhịp 1,5 giây), `/start` trả lại `savedAnswers`.
Nhờ nó lượt bỏ dở cũng chấm được đúng phần đã kịp làm.

### [x] A4 (VÁ) · Không khoá: năm `/submit` song song đều tính điểm
`_da_co_luot_tinh_diem` là một câu SELECT trần, mức cách ly `read committed`, và
`mock_attempts` không có ràng buộc UNIQUE nào. Năm request song song → +500 XP
và đề bị đếm năm lần trong sổ điểm.

Vá bằng hai chỉ mục DUY NHẤT PHẦN, để Postgres trả lời thay vì mã tự canh:
`uq_mock_attempt_dang_mo` và `uq_mock_attempt_tinh_diem`. Điều kiện
`started_at IS NOT NULL` để năm dòng lịch sử (đều có `started_at` NULL, và hai
học viên đang có 2 dòng counted) nằm NGOÀI chỉ mục — khớp quyết định không hồi tố.

### [x] A5 (VÁ) · `x()` vứt rowcount: hàng rào trên giấy
`WHERE ... AND submitted_at IS NULL` được viết ra đúng nhưng không ai đọc kết
quả, và mã gán `attempt_id` rồi đi tiếp bất kể UPDATE có trúng dòng nào không.
Kịch bản: tab A hết giờ tự nộp, tab B bấm bắt đầu và đóng lượt đó → bài của A
biến mất, mà XP vẫn cộng và sự kiện vẫn ghi trỏ vào dòng không còn.

Vá: thêm `common/db.xn()` trả số dòng; trúng 0 dòng thì lưu thành lượt luyện và
không cộng gì.

### [x] A6 (VÁ) · Cột `counted` khai sai tệp — hỏng cả lần triển khai trên CSDL rỗng
`bootstrap_schema` đọc thư mục `sql/` theo `sorted()`, mà "legacy" < "mockexam",
nên `ALTER TABLE mock_attempts` đặt trong `legacy_schema.sql` chạy TRƯỚC lệnh
`CREATE TABLE` — và lệnh ấy `raise` chứ không bỏ qua. Production hiện tại an
toàn (cột đã có thật), rủi ro nằm ở CSDL thứ hai. Đã chuyển sang
`mockexam_schema.sql`, cạnh bảng nó thuộc về.

### [x] A7 (VÁ) · HỒI QUY CỦA TÔI trong `a8f4c5e`: luật so đáp án bị siết
`_chuan` chỉ gộp khoảng trắng và GIỮ dấu `%`, kèm chú thích tự nhận là "giữ đúng
luật engine" trong khi `norm` cũ **bỏ hết khoảng trắng và bỏ hết `%`**. Tôi tự
đo lại trên nội dung thật: **151 câu dạng điền, 14 câu hỏi "bao nhiêu %" mà đáp
án lưu là số trần** — *"A = 30, B = 70. A chiếm bao nhiêu % tổng? (nhập số)"*,
đáp án `"30"`. Em gõ `30%` thì trước 31/08 là ĐÚNG, sau đó thành SAI. Cùng lỗi
với `x = 3` gõ thành `x=3`. Đã trả `_chuan` về đúng luật cũ + NFC.

### [x] A8 (VÁ) · `int(inf)` ném `OverflowError`, không nằm trong khối except
`json.loads` biến `1e400` thành `inf` — số thực bình thường nên `STRICT_JSON`
không chặn — và `int(inf)` ném `OverflowError`. Kết quả: 500, học viên mất cả
bài vừa học.

### [x] A9 (VÁ) · Engine nuốt im lặng 404 của `/complete`
`/complete` NAY 404 được (L5), mà engine chỉ có `r.ok ? r.json() : null` rồi vẫn
vẽ màn chúc mừng + pháo hoa + "+50 XP". Học viên thấy xong bài, CSDL trống.

### [x] A10 (VÁ) · `quen_dap_an` chưa nơi nào trong mã chạy thật gọi
Ba lời gọi, cả ba trong tệp test. Giảng viên sửa một đáp án sai xong, tối đa 60
giây tiếp theo máy chủ vẫn chấm bằng đáp án CŨ — và nay con số ấy đi thẳng vào
XP và bản đồ năng lực. Đã gọi từ cả hai đường soạn bài.

### [x] A11 (VÁ) · Ba phép kiểm hằng đúng, một phép kiểm mù
- `duration_seconds >= 0`: mọi đường ghi đều đã qua `max(0, …)`.
- `secondsLeft b <= a`: hai lời gọi cách nhau vài mili giây nên một bản mã luôn
  cấp lại 1200 giây vẫn thoả. Nay lùi đồng hồ 5 phút giữa hai lần gọi.
- `?limit=-1`, `?weeks=0`, phân trang diễn đàn: xanh cả trên mã cũ — đã ghi rõ
  chúng là hàng rào, không tính vào thành tích.
- `test_XP_lay_tu_NOI_DUNG_BAI`: bài thật có `xp_reward = 50` mà mặc định cũng
  là 50 — gõ sai tên khoá SQL thì phép kiểm vẫn xanh. (Phép kiểm phòng luyện
  làm đúng: bài tạm đặt `xp_reward = 40`.)

### [ ] A12 · CHƯA VÁ, và đây là cái nặng nhất còn lại
`POST /check` trả `answer` cho MỌI id có mặt trong `answers`, bất kể đúng sai.
Nên `{"phan":"drill","answers":{"d1":"x",…,"d8":"x"}}` là **một request lấy trọn
bộ đáp án**, rồi `/complete` với bộ đáp án ấy cho 120 XP phòng luyện + một dòng
năng lực 8/8. **Áp dụng cho cả `phan="test"`** — tức bản vá "chấm ở máy chủ"
sáng nay của tôi cũng đi vòng được đúng kiểu đó.

Vá đúng cần trạng thái phía máy chủ cho lượt học: `/check` GHI NHẬN câu trả lời
lần đầu cho từng câu, `/complete` chấm trên phần đã ghi nhận chứ không trên thân
request. Cần thêm bảng/cột và một quyết định về "làm lại bài thì sao" — tôi
không làm vội trong phiên này. **Đây là việc đầu tiên của phiên sau.**

### [x] A13 (XONG) · phòng luyện bắn 9 request/bài, đụng trần rate-limit lớp học
> Kiểm lại 01/09/2026: `lessons/views.py:474` `CheckAnswersView` có bốn lớp
> throttle riêng — và chú thích ngay trên nhắc rằng đặt `throttle_classes` là
> GHI ĐÈ mặc định chứ không cộng thêm.
`ip_hour = 1000/giờ` đếm theo IP × theo view, mà một phòng máy dùng chung NAT.
30 em × 4 bài/giờ × 9 = 1080 request/giờ trên cùng một IP. Chạm trần thì
`gradeTest` CHẶN HẲN không cho đi tiếp. Cần cho `/check` một luật riêng, hoặc
gộp lượt chấm phòng luyện.

### [x] A14 (XONG) · `validate_lesson` không kiểm khối `drill`
> Kiểm lại 01/09/2026: khối `drill` được kiểm (`questions` phải là mảng ≥ 1).
Không ai bắt câu drill phải có `id`, `id` phải duy nhất, hay phải có `answer` —
trong khi XP và bản đồ năng lực nay dựng từ đúng khối đó. Thiếu `id` thì mọi câu
hiện "Chưa chấm được câu này" và câu an ủi ấy là nói dối.

### [x] A15 (XONG) · mẫu nhập giáo trình chính thức đặt sai tên khoá
> Kiểm lại 01/09/2026: cả `NHAP_GIAO_TRINH.md` lẫn `mau_nhap_giao_trinh.json`
> nay viết `time_seconds`, khớp engine.
`docs/NHAP_GIAO_TRINH.md` và `docs/mau_nhap_giao_trinh.json` viết
`drill.seconds`, engine đọc `drill.time_seconds`. Bài nhập đúng theo mẫu chính
thức sẽ có đồng hồ phòng luyện **không bao giờ hết giờ** (`NaN <= 0` luôn sai).

### [x] A16 (XONG) · `AdminLessonContentView` không đối chiếu `index`/`sort_order`
> Kiểm lại 01/09/2026: `courseadmin/views.py` ép `index == sort_order`, kèm số
> đo "0/76 bài lệch" nên hàng rào không chặn nội dung nào đang chạy.
Dán mẫu có `"index": 28` vào ô nội dung của bài đang ở `sort_order = 5`: engine
đọc `index = 28`, ghi tiến độ sang bài 28, và chấm bằng đáp án của bài 28.

### [~] A17 (BÁC, có lý do) · `/complete` không kiểm ghi danh
> Kiểm lại 01/09/2026: không có khái niệm khoá TRẢ PHÍ nào trong mã —
> `courses/views.py` không nhắc `price` một lần. Ghi danh là tự phục vụ, mọi
> tài khoản đã đăng nhập đều gọi `/enroll` được. Nên "hai request đọc được nội
> dung khoá chưa ghi danh" không giành thêm quyền gì so với một request
> `/enroll`. Đây không phải ranh giới phân quyền. Ngày nào có khoá trả phí thì
> mở lại mục này TRƯỚC khi bật tính năng đó.
`CourseContentView` và `CheckAnswersView` đều kiểm `_da_ghi_danh`, riêng
`CompleteLessonView` thì không — mà nó TỰ ghi danh. Hai request là đọc được nội
dung khoá mình chưa ghi danh.

### Những chỗ tôi BÁC lại agent
- **Thứ tự dict trong `dap_an()`**: agent lo `jsonb` không giữ thứ tự. Đã truy
  trọn đường: `questions` là MẢNG, mà jsonb chỉ sắp xếp lại khoá của OBJECT.
  Thứ tự được giữ; combo máy chủ dựng lại trùng với combo em thấy trên màn hình.
- **`_luot_dang_mo` để lại dòng rác vĩnh viễn**: không. Dòng thừa vô hình với
  mọi bên đọc rồi bị nhặt và dọn ở lần `/start` kế tiếp.
- **Test ghi rò ra Neon**: không có. Đã kiểm lại sau cả phiên — 76 dòng
  `lessons`, `mock_attempts` không thêm dòng nào.


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

### [x] N2 (XONG) · Việc làm được ngay, không cần thêm người
Chú thích của `HALF_LIFE_DAYS` phải nói ra: (a) con số này chưa được kiểm chứng,
(b) đo 31/08/2026 nó đáng tới 11 điểm với một học viên thật, (c) nó là trọng số
theo ĐỘ MỚI CỦA BẰNG CHỨNG, không phải mô hình quên. Ba thứ đó khác nhau, và
gộp chúng lại là cách con số 45 sống sót mà không ai hỏi.

> Viết xong 01/09/2026 tại `stats/competency.py`, kèm CÁCH kiểm chứng khi đủ dữ
> liệu (tìm chu kỳ bán rã làm nhỏ nhất sai số giữa điểm dự đoán và điểm thật ở
> lần làm sau) và một hệ quả chưa ghi ở đâu: ngưỡng xếp lịch ôn là 60, nên 11
> điểm đủ để một chủ đề nhảy qua nhảy lại ranh giới "cần ôn" — con số chưa kiểm
> chứng này đang QUYẾT ĐỊNH lịch học của người ta.

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

### [x] B12 (XONG phần mã) · `LocMemCache` theo tiến trình, Render chạy 2 worker
> `config/settings.py` đọc `REDIS_URL`; không có biến thì chạy y như cũ. CHỜ ANH
> bật hạ tầng (3 bước ghi trong chú thích ở chính tệp đó).
`config/settings.py` không khai `CACHES` → LocMemCache, sống trong bộ nhớ TỪNG
tiến trình. Ba hệ quả:
- `quen_dap_an` (bản vá A10 hôm qua) chỉ xoá đệm của MỘT worker — worker kia vẫn
  chấm bằng đáp án CŨ tới hết 60 giây TTL. Bản vá ấy đang có tác dụng một nửa.
- `quen_ghi_danh` y hệt: huỷ ghi danh xong vẫn đọc được nội dung thêm một phút.
- **Trần request thực tế GẤP ĐÔI con số cấu hình**: mỗi worker đếm riêng, nên
  `user_hour = 600` thực tế là ~1200/giờ/người.

Đây chính là hạng mục Redis (A3) đang chờ anh. Ba hệ quả trên là lý do cụ thể.

### [x] B13 (XONG) · phòng luyện vẫn là máy dò đáp án
> Kiểm lại 01/09/2026: `lessons/views.py:145` `_chot_luot_drill` chốt lượt đang
> dở ngay lúc bấm "Bắt đầu" lại — lượt DÒ chính là lượt đầu.
`reset` cho thử vô hạn; trắc nghiệm 4 lựa chọn thì ≤ 4 lượt/câu là biết chắc.
**Tôi từng ghi "XP đã chặn" — SAI**: `existed` chỉ chặn lần thứ HAI, còn lần thứ
nhất (lần duy nhất được tính) đã là 120 XP + ô năng lực 8/8 do dò ra. Cần anh
chốt hướng, như đã hỏi.

### [x] B14 (XONG) · `CREATE INDEX ON mock_attempts` chạy trước `CREATE TABLE`
> Kiểm lại 01/09/2026: `sql/mockexam_schema.sql` — mọi `CREATE INDEX` nằm sau
> `CREATE TABLE` trong cùng tệp, kèm chú thích giải thích thứ tự `sorted()`.
Nằm ở `legacy_schema.sql:780`, NGOÀI dải commit của phiên (có từ trước). Nhưng
`bootstrap_schema` nay nằm trong `buildCommand` của Render và `raise` ở câu lệnh
đầu tiên hỏng, nên trên một CSDL RỖNG (staging, khôi phục sau sự cố) nó làm
**chết cả lần triển khai**. Chuyển hai dòng ấy sang `mockexam_schema.sql`.

### [x] B15 (XONG) · `/complete` bỏ qua phần phòng luyện ĐÃ ghi nhận
> Kiểm lại 01/09/2026: `lessons/views.py:84` đọc `doc_ghi_nhan` khi thân request
> thiếu — thân chỉ là BẢN SAO LƯU.
`_cham_drill` trả `None` ngay khi thân request thiếu khoá `drill`, TRƯỚC khi
chạm tới `answers_json`. Em làm đủ 8 câu rồi tải lại trang trước khi bấm Hoàn
thành → máy chủ có sẵn bài làm nhưng không dùng, rồi `xoa_ghi_nhan` xoá luôn.
Không phải hồi quy, nhưng đúng là điều A12 tuyên bố đã sửa.

### [x] B16 (XONG) · `_moc_san` chỉ chính xác tới NGÀY
> Kiểm lại 01/09/2026: `stats/plan.py:301` `_truoc_moc_san` so ở mức GIỜ.
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

### [x] N3 (XONG) · `roadmaps` là bảng DUY NHẤT của mình còn `NO ACTION`
Chưa hại ai (chưa có đường xoá tài khoản), nhưng ngày dựng đường ấy thì nó chặn.

> **Đếm lại 01/09/2026 trên CSDL thật: 9 khoá `NO ACTION`, không phải 4** — và 7
> trong số đó thuộc bảng do Django quản (`socialaccount_*`, `token_blacklist_*`),
> Django tự lo dây chuyền ở tầng Python. Của mình đúng HAI, cả hai trên
> `roadmaps`: `user_id` → `CASCADE` (lộ trình cá nhân chết theo chủ; `user_id
> IS NULL` là MẪU nên mẫu không bị đụng — 3 dòng cá nhân, 1 dòng mẫu), và
> `generated_from_survey_id` → `SET NULL` (xuất xứ, không phải danh tính).
>
> `legacy_schema.sql` §42. Đo trước khi đổi: 0 dòng mồ côi ở cả hai cột. Đã chạy
> thử cả hai lệnh trong giao dịch rồi CUỘN LẠI — xác nhận `CASCADE`/`SET NULL`
> có hiệu lực trong giao dịch và Neon trở về `NO ACTION` sau khi cuộn.

---

## 01/09/2026 — Giao diện: đo lại từ đầu vì phép đo cũ nói dối

### Bộ đo — 5 lỗi TRONG CHÍNH NÓ, tìm ra trước khi tin bất cứ con số nào
`scripts/do_giao_dien.mjs`. Trước khi báo một con số, chạy `--tu-kiem`: nó nhét
`color: #F2F2F4` vào mọi phần tử rồi đòi bộ đo phải BẮT ĐƯỢC. Đạt: 1291 vi phạm.

Năm lỗi đã mắc, mỗi lỗi từng sinh ra một danh sách việc phải làm mà không có
việc nào có thật:

1. **Bỏ qua nền gradient** → chữ trắng trên hero tím tính là trắng-trên-trắng,
   26 dương tính giả.
2. **Bỏ qua chữ gradient** (`background-clip: text`) → tiêu đề bài ra 1:1.
3. **Không đọc được `color(srgb 1 1 1 / .95)`** → thanh gần trắng báo 2,1:1.
4. **`[\d.]` trong template literal bị nuốt gạch chéo** thành `[d.]` → không rút
   được số nào, mọi tương phản thành `NaN`, và `NaN < 4.5` là FALSE. Bộ đo báo
   **0 vi phạm** kể cả khi tôi cố ý đặt chữ chính gần trắng. Số 0 giả.
5. **Chặng gradient TRONG SUỐT bị tính như nền đục** → nút "Nộp & xem đánh giá"
   phủ `rgba(6,182,212,0.18)` (18%) bị tính như cyan đặc: báo 2,03:1 trong khi
   thật là 4,94:1.

Và hai lỗi nữa ở phần vùng chạm:

6. **Đo khổ máy tính bằng ngưỡng cảm ứng 44px.** `hasTouch` sai làm Chromium báo
   `pointer: fine`, nút mang `[@media(pointer:fine)]:min-h-9` co xuống 36px —
   *và ngay cả khi đúng*, 44 là hướng dẫn CẢM ỨNG; chuột thì chuẩn đang áp là
   WCAG 2.2 SC 2.5.8 = **24×24**. Hai cái cộng lại: **158 phát hiện, không cái
   nào vi phạm chuẩn nào**, và chúng chôn mất 11 phát hiện thật.
7. **Trả hộp của `<label for>` thay vì hộp ô nhập** → ô mật khẩu cao 44px bị báo
   là 292×17 (đó là dòng chữ nhãn nằm trên nó).

Thêm: mở ngữ cảnh trình duyệt THỨ HAI với cùng cặp thẻ thì lượt sau bị đẩy về
màn đăng nhập (proxy đã xoay thẻ làm mới ở lượt đầu) — và bộ đo lặng lẽ đo cái
vỏ đăng nhập. Dấu hiệu: **mọi trang ở khổ sau ra CÙNG một con số**. Nay có chốt
chặn dừng hẳn thay vì báo số.

### [x] Kết quả sau khi vá — 6 gốc tương phản, 5 gốc vùng chạm
| | trước | sau |
|---|---|---|
| vi phạm tương phản | 8 | **0** |
| vùng chạm dưới ngưỡng | 19 | **1** (cố ý) |
| tràn ngang · lỗi JS · lời gọi ghi lọt | 0 · 0 · 0 | 0 · 0 · 0 |

**Một nguyên nhân chung cho cả 6 gốc tương phản:** chữ nhỏ dùng bản màu dành cho
NỀN/VIỀN thay vì bản dành cho CHỮ. Token `--brand-ink: #5B47D4` đã có sẵn đúng
cho việc này từ đợt 31/08 — mấy chỗ này bị sót trong chính đợt đó.

- `.brand-short` "PE×T" 3,32:1 — sót đúng ba dòng dưới chỗ `.brand-c1/.brand-c2`
  đã vá hôm 31/08, cùng tệp, cùng lỗi.
- `.mk-nav-link.is-active` 4,2:1 · `.progress-step.active` 4,3:1 · `.nav-next`
  4,16:1 — đều là `--accent`/`--module-accent`/`--primary` dùng làm màu chữ.
- `.cd-enroll-btn.unenroll` 3,44:1 — đỏ 500 trên nền đỏ 50 → đỏ 700.
- `.player-pill .xp-text` **1,69:1 ở 9px** — nặng nhất. Viên thuốc thiết kế cho
  nền TỐI (`rgba(11,17,33,.5)`) nhưng `lesson_hsa.css` đã trỏ `--text-500` sang
  giá trị nền sáng; nền tối 50% hoà thành xám giữa. Sửa **bề mặt** theo chủ đề
  chứ không sửa riêng màu chữ — cái hỏng là quan hệ giữa hai thứ.

Và một lỗi phép đo tĩnh KHÔNG bắt được, chỉ đọc CSS mới thấy: `.nav-next:hover`
đặt `color: #fff` — chữ trắng trên nền cyan 28% phủ trên trắng, ≈1,2:1, chữ biến
mất khi rê chuột. Đã vá cùng chỗ.

### [x] `--module-accent-ink` phải khai lại trong `lesson_hsa.css`
Đúng cái bẫy mà chú thích sẵn có trong tệp đã cảnh báo cho `--module-accent`:
token tính ở `:root` nên đã "đóng băng" mã cyan `#0A6F80` của chủ đề cũ.

### [ ] Còn 1 vùng chạm CỐ Ý giữ nguyên
Liên kết tên lớp trong bảng quản trị: 205×36. Kéo lên 44 sẽ chồng lên dòng tên
đợt ngay dưới. 36 vượt chuẩn thật sự đang áp (SC 2.5.8 = 24×24) mà giữ được mật
độ bảng. Nếu sau này bảng đổi sang bố cục thẻ trên điện thoại thì nâng lên 44.

### [x] Chủ đề TỐI — chưa từng quét, và có 47 vi phạm / 12 gốc
`--toi` đặt `localStorage.theme` TRƯỚC khi trang chạy rồi kiểm lại `body.dark`
đúng chưa; sai chủ đề thì dừng hẳn. Phép tự kiểm cũng phải theo chủ đề: nhét
`#F2F2F4` vào nền tối là chữ gần trắng trên nền đen — tương phản CAO, và phép tự
kiểm "thất bại" mà chẳng chứng minh gì.

Hai lỗi bộ đo nữa lộ ra ở lượt này:
- **Gradient bị `background-clip: text` bị tính như nền.** Nó chỉ tô trong nét
  chữ của chính nút đó. Tính là nền làm `.brand-c1` (#8B7CF6) nằm trên chặng
  gradient #8B7CF6 → đúng **1:1**, vi phạm nặng nhất bảng mà không có thật. Và
  nó CHE một lỗi thật: `.cd-module-prog` #10B981 trên nền trắng = 2,54:1.
- **Đo tương phản trên emoji.** "📘" là ảnh nhiều màu do phông màu vẽ, `color`
  không quyết định pixel nào của nó.

**Một hồi quy do CHÍNH TÔI gây ra hôm 31/08:** `--module-accent-ink: #0A6F80` bị
đặt vào `:root` của `lesson_chrome.css` — mà `:root` ở tệp đó là bảng màu TỐI.
`.step-pill` xuống **2,88:1 ở 10 chỗ**, và không ai thấy vì lượt đo hôm đó chỉ
quét chủ đề sáng. Nay `:root` dùng `var(--module-accent)`, bản tối màu nằm trong
khối `body.light`.

Nguyên nhân chung của 12 gốc còn lại, đúng một câu: **token dành cho CHỮ bị dùng
làm NỀN, và ngược lại.** Tệp `theme.css` đã có tiền lệ (`--danger` phải tách khỏi
`--danger-fill` vì chữ trắng trên nền đỏ-chữ chỉ 2,77:1) nhưng chưa ai áp cho
xanh lá và tím:
- `--success-ink` làm chặng gradient nền → bản tối lật thành #34D399, nút "Tiếp
  tục học" chữ trắng còn **1,92:1**. Thêm `--success-fill-2` (token nền KHÔNG
  lật theo chủ đề — nút xanh lá đọc như nhau ở cả hai bản).
- `--mk-violet`/`#8B7CF6` làm nền nút chính → 3,33:1. Dùng cặp `--brand-fill`.
- `#64748B` viết cứng làm chữ phụ trên thẻ tối, ba chỗ → 3,07–3,75:1.
- `--brand-ink` bản tối tự ghi 4,64:1 trong chú thích — đo thật trên `.cd-card`
  còn 4,4:1. Nâng lên `#A78BFA` (6,75:1) cho có biên.

Kết quả: **sáng 0 · tối 0**, cả hai đều đã chạy `--tu-kiem` ngay trước khi lấy số.

### [x] Trạng thái TƯƠNG TÁC — `--trang-thai`
Ba lỗi bộ đo nữa (thành mười hai) trước khi lấy được con số nào dùng được:

10. **`if (r.cssRules) { đệ quy; continue; }` nuốt sạch luật thường.** Từ Chrome
    112 (CSS Nesting) MỌI `CSSStyleRule` đều CÓ `cssRules` — rỗng, nhưng tồn
    tại. Kết quả: 371 luật quét được, **0 luật chứa `:hover`**, và lượt đo báo
    "0 lỗi rê chuột" vĩnh viễn. Một số 0 giả nữa, trông hệt số 0 thật.
11. **Chuyển tiếp thắng cả `!important` nội tuyến.** Vừa ép màu là một
    `transition` khởi động, và `getComputedStyle` ngay sau đó trả về màu CŨ —
    tức 0 vi phạm cho mọi nút có `transition`, tức gần như mọi nút. Phải chèn
    `* { transition: none !important; animation: none !important }` trước khi đo.
12. **Ép KHAI BÁO của một luật là bỏ qua tầng xếp lớp.** Bản vá
    `body.light .nav-next:hover` đã có vẫn bị báo là lỗi, vì bộ đo ép thẳng luật
    gốc đè lên nó. Ba dương tính giả kiểu này. Nay dùng CDP
    `CSS.forcePseudoState` — bảo trình duyệt coi phần tử đang được rê chuột rồi
    để CHÍNH NÓ giải tầng xếp lớp.

Và một lỗi giải mã màu: `color-mix(in oklab, …)` tính ra `oklab(0.958 …)` — màu
rất SÁNG — nhưng đọc số thô ra gần ĐEN (dấu trừ của thành phần `a`/`b` còn bị
nuốt): **29 vi phạm 1,05:1 không có thật** ở khu quản trị. Nay để canvas của
trình duyệt giải mã, nhận mọi cú pháp CSS Color 4 kể cả cú pháp sinh sau bản này.

**Đã tự kiểm bằng chính con lỗi tìm được bằng mắt:** lùi bản vá
`body.light .nav-next:hover` → bộ đo báo ĐỎ 1,14:1 đúng chỗ; phục hồi → xanh.

Hai lỗi THẬT tìm được ở bản tối, cùng một kiểu và là kiểu phép đo tĩnh không thể
thấy: nền khi rê chuột `#293548` sáng hơn mặt thẻ đủ nhiều để kéo `--t3` xuống
**4,1:1** — chữ phụ ĐẠT lúc đứng yên rồi TRƯỢT lúc chạm vào. Hạ nấc nâng xuống
`#1F2937`: vẫn rõ là một nấc nâng, và giữ 4,85:1.

### Bảng cuối — bốn chiều, hai chủ đề, hai khổ, 11 trang
| | sáng | tối |
|---|---|---|
| tương phản tĩnh | 0 | 0 |
| tương phản khi rê chuột / lấy nét | 0 | 0 |
| vùng chạm dưới ngưỡng | 1 (cố ý) | 1 (cố ý) |
| tràn ngang · lỗi JS · lời gọi ghi lọt | 0 · 0 · 0 | 0 · 0 · 0 |
| tự kiểm bắt được | 1250 | 1296 |

### [x] Vòng nét bàn phím — WCAG 2.4.7, và nó ĐẠT
Đo màu không trả lời được câu hỏi của 2.4.7: một nút có thể đủ tương phản mà khi
Tab tới thì **chẳng đổi gì**, và người dùng bàn phím mất dấu hoàn toàn. Cách
kiểm: chụp dáng vẻ trước, bật `:focus-visible` qua CDP, chụp lại; y hệt nhau là
không có dấu hiệu nào.

Lấy mẫu theo HÌNH DÁNG (thẻ + hai lớp đầu, tối đa 2 mỗi nhóm, trần 40 mỗi trang)
chứ không quét hết — trang chính có 258 phần tử lấy nét được, phần lớn là cùng
một nút lặp lại.

**Kết quả: 0/171 thiếu vòng nét.** Đã tự kiểm: thêm
`*:focus-visible { outline: none !important; box-shadow: none !important }` →
báo **60/171**; gỡ ra → 0. (Còn 111 phần tử vẫn khác nhau vì dấu hiệu lấy nét
của chúng không phải vòng nét mà là đổi nền hoặc viền — vẫn hợp lệ.)

### [ ] Chưa làm
- Trạng thái **vô hiệu** (`:disabled`) chưa đo.
- Mới 11 trang. Các trang giảng dạy (`/giang-day/...`) chưa nằm trong danh sách.
- Chưa đo **độ dày / độ tương phản** của vòng nét (SC 2.4.13, mức AAA) — mới đo
  nó có TỒN TẠI hay không.
