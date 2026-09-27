# Audit bảo mật — 27/09/2026

Nguồn việc: anh Sơn 27/09 — *"audit kĩ để không có lỗ hổng"*. Nhánh `agent/sec`, gốc `7f93250`.

Phạm vi đo: 199 đường dẫn có lớp view (297 cửa nếu đếm theo phương thức), 6 vai, toàn bộ
`backend/`, tầng React `frontend/src/`, tầng JS cũ `frontend/public/static/js/`.

Mọi con số dưới đây do chính lượt này đo (RULES §15). Phép kiểm chạy trên CSDL dev
(`dang_tro_production = False`, đo được), trong giao dịch cuộn lại. **Không một lá thư nào
rời máy chủ trong lượt audit** — phần đo về thư dừng ở tầng soạn thư; hàng rào `§61` đã kiểm
và đang BẬT trên máy này (`ly_do_chan('email','phuhuynh@gmail.com')` trả lý do chặn).

| Mức | Số |
|---|---|
| CHẶN DEMO | 0 |
| Phải vá trước khi có dữ liệu thật | 1 (chưa vá — lead quyết) |
| Đã vá trong lượt này | 2 nhóm / 8 cửa |
| Ghi sổ nợ | 5 |
| Nghi, chưa chứng minh | 2 |

---

## 1 · PHẢI VÁ TRƯỚC KHI CÓ DỮ LIỆU THẬT — cửa xác thực thứ hai của `django-allauth` mở trên tên miền backend

**Chỗ:** `backend/config/urls.py:49` — `path('accounts/', include('allauth.urls'))`.

**Khai thác được thế nào.** Người lạ CHƯA đăng nhập, chỉ cần biết tên miền Render của
backend. Đo 27/09 trên Django dev cổng 9000, **chỉ GET**:

```
GET /accounts/login/            → HTTP 200, form HTML "Sign In"  (input name="login", "remember")
GET /accounts/password/reset/   → HTTP 200, form HTML "Password Reset" (input name="email")
GET /accounts/signup/           → HTTP 500
GET /accounts/password/change/  → 302 về /accounts/login/?next=…   (có phiên là vào được)
GET /accounts/password/set/     → 302 về /accounts/login/?next=…
GET /accounts/email/            → 302 về /accounts/login/?next=…
```

`path('accounts/', include('allauth.urls'))` được thêm để có `google/login/` + callback (chú
thích ngay dòng ấy nói đúng thế). Nó kéo theo **28 đường** khác, trong đó bốn cửa quản lý
tài khoản đầy đủ. Đây là mã của thư viện, không phải mã dự án, nên không một hàng rào nào
của dự án chạm tới nó:

| Thứ dự án đã dựng | `/auth/*` (mã dự án) | `/accounts/*` (allauth) |
|---|---|---|
| Trần dò mật khẩu | `LoginThrottle` 20/phút/IP | **bộ đếm RIÊNG** của allauth, 10/phút/IP + 5/300s/khoá (đo: `allauth.account.app_settings.RATE_LIMITS`) |
| Trần quên mật khẩu | `QuenMatKhauThrottle` 30/giờ/IP + trần theo TÀI KHOẢN trong CSDL | bộ đếm riêng 20/phút/IP |
| Thu hồi phiên sau khi đổi mật khẩu | `tokens_valid_from` + `_thu_hoi_refresh` — cả ba đường của dự án đều làm (`accounts/views.py:494`, `accounts/quen_mat_khau.py:277`, `teaching/views.py:820`) | **KHÔNG** |
| Xoá đệm người dùng 60 s | `invalidate_user_cache` | **KHÔNG** |
| Dòng nhật ký kiểm toán | `audit.record` | **KHÔNG** |
| Hàng rào thư §61 | `hop_thu` → `hang_rao_thu.ly_do_chan` | **KHÔNG** — allauth gửi bằng `django.core.mail`, một đường thư thứ hai |
| Hàng rào §73 "chưa bấm thư xác nhận thì chưa vào được" | `LoginView` gọi `chua_xac_thuc` | **KHÔNG** |
| Chữ tiếng Việt (RULES §10) | có | **không** — "Sign In", "Password Reset" |

Ba hệ quả CỤ THỂ, xếp theo thứ tự chắc chắn:

1. **Kênh dò mật khẩu thứ hai, không ai đếm.** Hai bộ đếm độc lập nên tổng trần thực tế là
   30 lượt/phút chứ không phải 20, và lượt dò ở cửa allauth không đi qua `common/audit.py`
   nên không để lại dấu ở chỗ trung tâm nhìn. **Đã đo:** cửa `/accounts/login/` trả 200 với
   form đầy đủ; trần riêng của allauth đọc được từ `app_settings.RATE_LIMITS`. **Chưa đo:**
   tôi KHÔNG bắn thử mật khẩu sai — đó là một đường GHI (đếm hỏng, khoá khoá) trên CSDL
   dùng chung, và §18 cấm.
2. **Đổi mật khẩu không thu hồi phiên.** Kẻ đã chiếm tài khoản đăng nhập ở
   `/accounts/login/` rồi đổi mật khẩu ở `/accounts/password/change/`: mật khẩu mới ghi
   bằng `User.set_password` → **đúng định dạng werkzeug** (`accounts/models.py:97`,
   `PASSWORD_HASHERS` đặt hai bộ werkzeug lên đầu), nên `LoginView` của dự án nhận nó ngay.
   Nhưng `tokens_valid_from` không nhích, `admin_audit` không có dòng nào. Cả cơ chế "đổi
   mật khẩu là cắt mọi phiên khác" mà `accounts/views.py:487` dựng lên bị đi vòng.
3. **Đường thư thứ hai, ngoài hàng rào §61.** `EMAIL_BACKEND` đang là
   `django.core.mail.backends.smtp.EmailBackend` với `EMAIL_HOST='localhost'` (đo được), nên
   HÔM NAY thư đặt lại mật khẩu của allauth không gửi được — máy dev lẫn Render đều không có
   MTA ở localhost. **Đó là một tai nạn may mắn, không phải một hàng rào.** Ai đặt
   `EMAIL_HOST`/`EMAIL_BACKEND` cho Django (một dòng, và là việc rất dễ có người làm khi
   thêm một tính năng gửi thư) thì đường ấy sống dậy ngay — và nó gửi tới địa chỉ THẬT của
   học viên từ máy dev, đúng thứ §61 sinh ra để chặn.

**Hậu quả:** mất dấu vết kiểm toán của mọi lượt chiếm tài khoản đi qua cửa ấy; mất hiệu lực
của việc "đổi mật khẩu để đuổi người lạ ra"; và một quả mìn hẹn giờ ở đường thư. Người dùng
là trẻ vị thành niên, nên "ai đang cầm tài khoản của em" là câu trung tâm phải trả lời được.

**Mức: phải vá trước khi có dữ liệu thật.** Không phải CHẶN DEMO — khách không gõ vào tên
miền backend, và cửa đăng ký đã 500 sẵn.

**KHÔNG TỰ VÁ** (brief mục 4: lỗ đụng luồng đăng nhập thì lead quyết). Hướng vá, rẻ nhất
trước:

- Chỉ nạp phần dự án THẬT SỰ dùng thay vì cả `allauth.urls`:
  `path('accounts/', include('allauth.socialaccount.urls'))` + hai tuyến provider. Phải đo
  lại trọn luồng Google OAuth sau khi đổi — `accounts/oauth.py` và
  `SOCIALACCOUNT_LOGIN_ON_GET` phụ thuộc vào cây tuyến này.
- Hoặc để nguyên và chặn ở middleware: 404 cho mọi đường `accounts/` không phải
  `3rdparty|social|google|facebook`. Rẻ hơn, nhưng là một danh sách sẽ trôi khi nâng allauth.
- Dù chọn đường nào: **đặt `EMAIL_BACKEND` của Django thành
  `django.core.mail.backends.dummy.EmailBackend`** và ghi lý do. Đường thư của dự án là
  `common/mail.py` + `notifications/hop_thu`, không đọc `EMAIL_*` của Django, nên việc này
  không mất gì mà bịt hẳn đường thư thứ hai.
- Cần một phép kiểm khẳng định `/accounts/login/` và `/accounts/password/reset/` trả 404 —
  không có nó thì lần nâng allauth sau sẽ mở lại.

---

## 2 · ĐÃ VÁ · Thư đăng ký §73 là một đường bơm chữ tới địa chỉ bất kỳ

**Chỗ:** `backend/accounts/tu_dang_ky.py:128` (`_soan_thu`) và `:158` (`_soan_thu_da_co`) —
câu chào `Chào %s,` nhận thẳng `name` từ thân yêu cầu.

**Khai thác được thế nào.** Người lạ CHƯA đăng nhập. `POST /auth/dang-ky` nhận hai thứ do
người gửi tự gõ và đưa cả hai vào một lá thư máy chủ TopHSA gửi bằng SMTP thật:

- `email` — **địa chỉ NHẬN**. Bất kỳ địa chỉ nào chưa có tài khoản đều nhận thư.
- `name` — tối đa 100 ký tự, `validate_name_field` chỉ kiểm độ dài, **không lọc xuống dòng**.

Đo 27/09 ở tầng soạn thư (không gọi cửa, không gửi gì — xem đầu tệp
`tests_tiem_thu_dang_ky.py` về lý do), gõ tên
`"ban,\n\nCANH BAO: tai khoan cua ban se bi khoa trong 24 gio.\nXac minh tai:
https://gia-mao.example.com/khan\n\nTopHSA"` — thân thư trả về đúng bốn dòng ấy Ở TRÊN nội
dung thật:

```
Chào ban,

CANH BAO: tai khoan cua ban se bi khoa trong 24 gio.
Xac minh tai: https://gia-mao.example.com/khan

TopHSA,

Bạn vừa đăng ký tài khoản học tại TopHSA. …
```

Bản HTML có `html.escape` nên thẻ không chạy, nhưng chữ vẫn hiện nguyên (chỉ mất xuống dòng).

**Đây không phải tiêm HEADER** — tiêu đề và địa chỉ nhận đã có `email_validator` và
`common/mail._XUONG_DONG` canh. Chỗ hở là THÂN thư, nơi chưa ai canh.

**Hậu quả:** thư đi từ tên miền thật của trung tâm, qua SPF/DKIM thật, nên nó vượt bộ lọc
rác tốt hơn hẳn một thư giả mạo. Thứ mất đi là **uy tín người gửi** của TopHSA (một lần bị
báo cáo lừa đảo là cả đường gửi báo cáo phụ huynh rơi vào hộp Spam), và nạn nhân ở NGOÀI hệ
thống nên không ai trong trung tâm thấy chuyện đang xảy ra. Trần: `TRAN_IP_MOI_NGAY = 5`
tài khoản chưa xác thực / IP / 24 giờ, cộng `dang_ky` 20/giờ/IP — tức 5 lá mỗi IP mỗi ngày,
nhân với số địa chỉ mạng kẻ gửi có.

**Mức: phải vá trước khi có dữ liệu thật.** **ĐÃ VÁ** — commit `933b7b6`.

Vá bằng `common/mail.ten_goi_trong_thu` (đặt cạnh `don_header`, chỗ đã giữ luật "dọn gì
trước khi vào thư"): gộp mọi khoảng trắng kể cả xuống dòng về một dấu cách · bỏ ký tự không
in được (`\x01` không phải khoảng trắng nên lọt lưới trên) · cắt về 40 ký tự. **Cắt độ dài
là phần không được bỏ:** một dòng 100 ký tự vẫn đủ chỗ cho một câu dụ. Sau vá, câu chào ra
`Chào ban, CANH BAO: tai khoan cua ban se bi k,` — một dòng, cụt giữa chừng, và địa chỉ dụ
không còn trong thư.

Phép kiểm: `backend/accounts/tests_tiem_thu_dang_ky.py` — **4 ĐỎ trước khi vá** (hai bản
soạn thư × hai luật: không xuống dòng, không quá dài), 2 xanh sẵn (tên thật có dấu và tên
rỗng vẫn phải chạy đúng). Sau vá **6/6 ĐẠT**. Hồi quy `accounts/` **96 ĐẠT**.

**Phần KHÔNG vá được, và không nên giả vờ là đã vá:** địa chỉ nhận vẫn do người gửi chọn —
đó là bản chất của việc xác nhận email. Cái đã bịt là phần thân thư.

---

## 3 · ĐÃ VÁ · Bảy cửa trả 403 ở chỗ luật dự án đòi 404 (khe lộ sự tồn tại)

**Luật bị vi phạm**, ghi ở ba chỗ độc lập: `docs/ERP_TOPHSA_2026-08-24.md` dòng 48 ·
`common/permissions.py::can_see_class` · `forum/views.py` §75 (`_KHONG_THAY`).

**Chỗ và cách khai thác** — kẻ tấn công là **một học viên bất kỳ đã đăng nhập** (hai cửa
`teach` thì là giảng viên / trợ giảng của một lớp khác). Đo bằng
`backend/common/tests_lo_ton_tai.py`: dựng hai lớp riêng biệt, cầm thẻ người lớp A gõ id của
lớp B, so với mã trả về khi gõ một id không tồn tại.

| Cửa | id CÓ THẬT của người khác | id KHÔNG TỒN TẠI |
|---|---|---|
| `POST /api/sessions/<id>/ban-ghi/da-mo` (`teaching/ban_ghi.py:88`, trước vá `:84`) | **403** | 404 |
| `POST /api/sessions/<id>/ban-ghi/bao-loi` (`ban_ghi.py:244`, trước vá `:229`) | **403** | 404 |
| `GET /api/teach/classes/<id>/ban-ghi` (`ban_ghi.py:117`, trước vá `:109`) | **403** | 403 |
| `POST /api/teach/classes/<id>/ban-ghi/<s>/nhac` (`ban_ghi.py:195`, trước vá `:183`) | **403** | 403 |
| `PUT /api/posts/<id>` (`forum/views.py:414`, trước vá `:398` → `_can_modify:186`) | **403** | 404 |
| `DELETE /api/posts/<id>` (`forum/views.py:423`, trước vá `:407`) | **403** | 404 |
| `PUT /api/comments/<id>` (`forum/views.py:541`, trước vá `:525`) | **403** | 404 |

**Hậu quả.** Nội dung thì KHÔNG lộ — hàng rào §75 và `_thuoc_lop` chặn đúng. Cái lộ là SỰ
TỒN TẠI, và id buổi / id bài là số nguyên tăng dần, nên một vòng lặp cho ra: trung tâm có
bao nhiêu lớp, mỗi lớp bao nhiêu buổi đã học, diễn đàn riêng của lớp khác có bao nhiêu bài
và bài mới nhất id bao nhiêu — tức **quy mô và nhịp hoạt động của TopHSA**, đo được bởi bất
kỳ em nào có tài khoản, mà không đọc nổi một chữ nội dung. Hai cửa `teach/` còn lộ theo
chiều khác: ở đó 403 trả về cho CẢ hai trường hợp, tức chúng lệch với mọi cửa khác của
`teaching/` — và chính sự lệch ấy là thứ làm bộ kiểm ma trận quyền **ĐỎ trên HEAD**.

**Mức: ghi sổ nợ** (không mất dữ liệu của em nào). **ĐÃ VÁ** — commit `744194b`, vì nó rẻ và
vì để lại thì bộ kiểm ma trận quyền không bao giờ xanh lại được.

- `teaching/ban_ghi.py` — bốn chỗ 403 → 404, sửa cả docstring đầu module (nó đang khai 403;
  RULES §20: chú thích sai tắt phản xạ kiểm tra của người sau).
- `forum/views.py::_can_modify` — chạy hàng rào §75 TRƯỚC hàng rào sở hữu. Đặt trong hàm
  dùng chung chứ không ở bốn thân hàm gọi nó, để cửa sửa/xoá mới sau này tự có hàng rào
  (RULES §7).
- `teaching/tests_ban_ghi.py` — sáu `assert` khẳng định luật CŨ **viết lại** cho khớp luật
  mới, không xoá (RULES §13).

Phép kiểm: **7 ĐỎ trước khi vá, 7 ĐẠT sau.** Hồi quy `tests_ban_ghi` + `forum/tests` +
`forum/tests_dien_dan_lop` = **44 ĐẠT**.

Từ chối theo VAI thì vẫn 403 và phải giữ thế: câu trả lời ấy không phụ thuộc id nên không
khai ra gì (học viên gõ vào cửa `IsTeachingStaff`).

---

## 4 · ĐÃ VÁ · Bộ kiểm ma trận quyền ĐỎ thường trực, tức không còn canh gì

**Chỗ:** `backend/common/tests_ma_tran_quyen.py:226`.

Chạy trên HEAD `7f93250` trước khi sửa gì: **2 HỎNG / 2**. Một do bốn cửa `ban_ghi` ở mục 3.
Cái còn lại là **một phát hiện giả**: `test_khong_view_nao_bo_trong_hang_rao_o_khu_quan_tri`
coi MỌI mã khác 403 là "học viên lọt", nhưng `api/teach/classes/<id>/hoc-lieu` cố ý là một
cửa cho hai phía (`teaching/hoc_lieu.py:120` — người dạy thấy tài liệu đang ẩn, em đang học
chỉ thấy phần đã mở và chỉ buổi mình thuộc) nên cổng nằm trong thân hàm và trả 404, đúng
luật.

**Hậu quả:** một phép kiểm đỏ thường trực là chỗ một cửa THẬT SỰ quên `permission_classes`
sẽ lẫn vào mà không ai nhận ra. Đây đúng là RULES §13 ("CI xanh chưa phải bằng chứng") nhìn
từ phía ngược lại.

**Mức: ghi sổ nợ.** **ĐÃ VÁ** — commit `fc52c34`. Thêm `CONG_TRONG_THAN` (khai tường minh
cửa gác trong thân hàm, mỗi dòng kèm lý do; với cửa ấy "đã từ chối" nhận cả 403 lẫn 404, mọi
cửa khác vẫn phải 403), và thêm `test_cua_gac_trong_than_van_con_that` canh chính danh sách
ấy: đường phải còn tồn tại, và cửa phải THẬT SỰ từ chối học viên lạ. **3 ĐẠT.**

### Bốn chỗ bộ kiểm ấy KHÔNG phủ (brief mục A yêu cầu tìm)

1. **Chỉ hai tiền tố.** `test_khong_view_nao_bo_trong_hang_rao…` chỉ quét `api/admin/` và
   `api/teach/`. Ngoài vòng: `api/lop-cua-toi/*`, `api/sessions/*`, `api/posts/*`,
   `api/comments/*`, `api/yeu-cau/*`, `api/hsa/*`, `api/public/*`, và toàn bộ `auth/*`.
   Tôi đã soát tay bằng tuyến (mục "Đã soát và KHÔNG thấy gì") — nhưng không có bộ kiểm.
2. **Chỉ quyền theo VAI, không bao giờ theo ĐỐI TƯỢNG.** Bảng `MONG_DOI` là vai × lớp
   quyền; nó không hỏi được "giảng viên lớp A có đọc được lớp B không". Toàn bộ lớp lỗ hổng
   ngang (mục 3 ở trên) nằm ngoài nó. `common/tests_lo_ton_tai.py` vừa thêm phủ 7 cửa; còn
   lại chưa có bộ kiểm chung.
3. **View không phải lớp bị bỏ im lặng.** `cls is None → continue`. Hôm nay chỉ `api/health`
   rơi vào đó, nên chưa hại — nhưng một view hàm `@api_view` mới sẽ biến mất khỏi ma trận mà
   không ai được báo.
4. **Lớp quyền lạ bị bỏ im lặng.** Vòng lặp chỉ ghi nhận view có lớp quyền NẰM TRONG
   `MONG_DOI`. `LaHocVien` (`yeu_cau/views.py:35`, gác 6 cửa) không có trong bảng → 6 cửa ấy
   không nằm trong ma trận. Chúng an toàn (đã đọc tay, xem dưới), nhưng "an toàn vì tôi đọc"
   khác "an toàn vì có người canh".

---

## 5 · Sổ nợ

### 5.1 · Chìa báo cáo phụ huynh lưu THÔ trong CSDL

`backend/sql/legacy_schema.sql:1456` — `parent_report_links.token TEXT NOT NULL UNIQUE`.
So với `password_reset_tokens.token_hash` (đã băm SHA-256) và `lich/chia.py` (đã băm), đây
là bảng chìa DUY NHẤT còn lưu thô. Ai đọc được một bản sao CSDL (sao lưu, một lượt xuất, một
lỗ tương lai ở chỗ khác) là mở được thẳng mọi tờ báo cáo còn hạn — trong đó có tên, chuyên
cần, điểm của từng em.

Không vá được rẻ: `ParentReportLinkView.get` trả chìa về cho giảng viên để gửi lại, nên băm
là mất tính năng ấy. Cách đúng là đổi thành "gửi lại = cấp chìa mới, thu hồi chìa cũ" rồi
mới băm — đó là một quyết định về sản phẩm, không phải một ô sửa. **Lead quyết.**

### 5.2 · `quen_mat_khau._soan_thu` cùng hình dạng với lỗ ở mục 2

`backend/accounts/quen_mat_khau.py:93` — `goi = (ten or '').strip() or 'bạn'`, y hệt bản
chưa vá của `tu_dang_ky`. **KHÔNG khai thác được:** địa chỉ nhận luôn là địa chỉ của chính
tài khoản ấy, không do người gọi chọn, nên kẻ tấn công chỉ tự gửi cho mình. Không tự vá vì
brief cấm đụng luồng mật khẩu; dùng `common/mail.ten_goi_trong_thu` ở đó là **một dòng**.

### 5.3 · Đếm được id người dùng nào có thật

`backend/accounts/views.py:512` — `POST /api/users/<id>/follow` trả 404 khi id không có,
200 khi có. Bất kỳ học viên nào đếm được tổng số tài khoản của trung tâm. Không kèm tên hay
email (`FollowingView` đã chặn đúng từ 30/08/2026). Là một đường GHI nên tôi **không bắn
thử** — kết luận đọc từ mã, chưa đo. Mức thấp; vá thì phải nghĩ lại cả ngữ nghĩa "theo dõi".

### 5.4 · Mỗi lượt đăng ký thất bại để lại một dòng `users` rác

`backend/accounts/tu_dang_ky.py:_mo_tai_khoan` tạo dòng `users` mang `name`, `email`,
`phone`, `school`, `study_goal` (500 ký tự) do người lạ gõ. Trần 5/IP/24 giờ. Chúng KHÔNG
vào hộp Yêu cầu của học vụ (dòng `tk_dang_ky` chỉ sinh sau khi bấm thư — thiết kế đúng), nên
hại duy nhất là bảng `users` phình và một danh sách tài khoản khó đọc. Cần một việc dọn định
kỳ "xoá tài khoản chưa xác thực quá N ngày" — chưa có.

### 5.5 · `SOCIALACCOUNT_LOGIN_ON_GET = True`

`backend/config/settings.py:400`. Mở luồng OAuth bằng một lượt GET, tức một trang bên thứ ba
gài `<img src="…/accounts/google/login/">` là ép được trình duyệt nạn nhân bắt đầu một luồng
đăng nhập. Tác động thực tế nhỏ (login-CSRF, không đọc được gì), và chú thích ngay dòng ấy
nói rõ nó ở đó để giữ luồng redirect như `flask-dance`. Gộp chung với mục 1 khi lead sửa
`accounts/`.

---

## 6 · Nghi, chưa chứng minh

1. **Trần `dang_ky` không chặn nhánh "địa chỉ này đã có tài khoản".** `tu_dang_ky.py:322` —
   nhánh ấy xếp một lá thư mỗi lần gọi, không đi qua `_cap_chia` nên không chịu
   `TRAN_MOI_GIO = 5`. Nghĩa là kẻ biết email của một em gửi được tới ~20 lá/giờ/IP vào hộp
   thư em ấy (trần `dang_ky`). **Chưa chứng minh:** tôi không bắn thử vì đó là đường GHI + đường
   gửi thư; con số 20 đọc từ `DEFAULT_THROTTLE_RATES`, chưa đo bằng lượt gọi thật.
2. **`_qua_tran_ip` đếm theo `requested_ip` của bảng chìa.** Nếu `NUM_PROXIES` đặt sai trên
   Render thì `client_ip` trả IP của Cloudflare/Vercel chứ không của khách, và trần 5/ngày
   sẽ đếm chung cả thế giới vào một xô — hoặc ngược lại, kẻ tấn công đổi được IP ghi nhận
   bằng header. `common/tests_cau_hinh.py` có canh `NUM_PROXIES`, nhưng tôi **chưa đo trên
   production** nên không kết luận.

---

## 7 · Đã soát và KHÔNG thấy gì

Liệt kê ra đây để lead biết phạm vi đã phủ tới đâu — một báo cáo chỉ toàn lỗi không nói được
điều đó.

**A · Phân quyền theo vai.**
- 199 đường dẫn có lớp view, đã dựng bảng đầy đủ (tuyến × lớp view × lớp quyền × có
  `can_see_class` hay không). Không đường `api/admin/*` hay `api/teach/*` nào thiếu
  `permission_classes` — `common/tests_khai_cong.py` đã canh sẵn điều đó ở tầng mã, và ma
  trận quyền canh ở tầng gọi thật.
- **Mọi** tuyến mang `class_id` đều có `can_see_class` trên đường đi: 20/20 dưới
  `api/teach/`, và 6 tuyến `api/admin/*` không gọi nó là ĐÚNG (`IsAdminOrAcademic` — hai vai
  ấy xem mọi lớp theo thiết kế). `api/lop-cua-toi/<id>/xem-du` gác bằng `_lop_cua_em`
  (`hv_xem_du.py:178`), chặt hơn `can_see_class`.
- Mọi tuyến mang `session_id` dưới `api/teach/` đều qua `can_see_class`; hai tuyến
  `api/sessions/*` qua `_thuoc_lop` (kiểm CẢ "còn trong lớp" LẪN "thuộc buổi" — buổi bù).
- Bốn tệp mới hôm nay: `forum/views.py` §75 (`vao_duoc_dien_dan_lop` gác đủ cửa đọc, viết,
  bình luận, thả cảm xúc; hai cửa sửa/xoá đã vá ở mục 3) · `teaching/hv_xem_du.py` (chỉ đọc,
  `_lop_cua_em` + `thuoc_buoi` có tiền tố bảng đúng ở cả hai câu SQL) ·
  `chuong_trinh/lop.py` (3/3 view có `can_see_class` hoặc `IsAdminOrAcademic`) ·
  `teaching/assignments.py` (mọi cửa qua `_load` → `can_see_class`, trả 404).
  `teaching/bao_cao_cheo.py` **chưa tồn tại** trên gốc `7f93250` — không soát được.
- `yeu_cau/`: mọi lượt đọc một yêu cầu đi qua `dich_vu._doc` → `pham_vi_yeu_cau`, ném
  `KhongThay` (404) khi ngoài phạm vi. Bốn phạm vi (học vụ · GV/TG · học viên · phụ huynh
  qua chìa) khai ở MỘT chỗ.

**B · Rò rỉ dữ liệu ngang.** Ngoài bảy cửa đã vá: không thấy đường nào đọc được của người
khác. Kiểm cụ thể — bản ghi và học liệu của lớp khác (404) · bài nộp (`MyAssignmentsView`
không nhận `user_id` ở CẢ hai phương thức; `AssignmentSubmissionView` qua `_load`) · tờ báo
cáo phụ huynh (`IsSeniorTeachingStaff` + `can_see_class`, trợ giảng bị cắt) · yêu cầu của em
khác (`pham_vi_yeu_cau` lọc `nguoi_tao`, và bản đầu từng rộng hơn — đã sửa 26/09) · hồ sơ
người khác (`IsAdminOrAcademic`) · danh sách theo dõi (`FollowingView` chặn id ≠ mình).
Phân trang theo khoá của `hv_xem_du` có `k.class_id = %s` trong câu con — thiếu nó là một
cách dò thứ tự thời gian của lớp khác; nó có.

**C · Cửa không cần đăng nhập.** 5 cửa `AllowAny` + 9 cửa `auth/*` + `lich/<chìa>.ics`.
- `auth/quen-mat-khau`, `auth/dang-ky`, `auth/gui-lai-xac-thuc`: cùng MỘT câu trả lời cho
  mọi nhánh; `_can_dong_ho` cân lại phần chi phí scrypt. Khe đồng hồ đã đo trên production
  27/09 (−0,037 s, không quan sát được) — không đo lại theo brief.
- `api/public/parent-report/<token>`: chìa 32 byte, hạn 45 ngày, thu hồi được, `noindex`, và
  ba lý do từ chối (sai / hết hạn / đã thu hồi) gộp thành một câu. Kỳ báo cáo ghim cứng vào
  chìa, không đọc `?from=/?to=`.
- `api/public/phu-huynh/<token>/yeu-cau`: có `GuiYeuCauPhuHuynhThrottle` riêng + trần
  `TRAN_MO_PHU_HUYNH` đếm trong CSDL.
- `lich/<chìa>.ics`: chìa **đã băm** trong CSDL (`lich/chia.py:31`), tài khoản bị khoá thì
  tắt lịch và tắt GIỐNG chìa sai, có `NhipDocLich` + `HourlyIPThrottle` (khai lại lớp theo
  IP là đúng — khai `throttle_classes` là THAY hẳn bộ mặc định).
- `api/noi-bo/tick`: khoá trong header, so bằng `hmac.compare_digest`, biến trống thì cửa
  TẮT (404), `TickThrottle` 30/phút.
- `api/notifications/badge` không có throttle — **có lý do viết ra** (poll nền 80 lần/giờ/tab,
  không được đốt quota của người thật sau NAT) và vẫn đòi JWT. Chấp nhận được.

**D · Bí mật và dấu vết.**
- `scripts/quet_bi_mat.py --tat-ca`: **835 tệp, 0 bí mật**. `--tu-kiem`: **6/6 quy tắc đỏ
  được đúng chỗ của nó** (bộ quét tự chứng minh nó còn đỏ được).
- `git log --all --name-only | grep -i "\.env"`: chỉ `backend/.env.example` và
  `frontend/.env.example`. **`.env` chưa bao giờ lọt vào lịch sử.**
- Không một câu `log.*` hay `print` nào in mật khẩu, chìa, token hay email. Chỗ duy nhất
  khớp grep là `common/mail.py:242` — in ĐƯỜNG DẪN tệp thư ở chế độ thử, không in nội dung.
- `admin_audit`: hai đường đặt lại mật khẩu ghi `detail={'role': …}` và một câu tiếng Việt,
  **không có mật khẩu tạm** (chú thích `teaching/views.py:840` nói rõ vì sao).
- Câu lỗi trả người dùng: `common/errors.py` làm phẳng 500 thành "Lỗi máy chủ nội bộ" kèm
  `request_id`; `PermissionDenied` làm phẳng thành một câu duy nhất. Không tên bảng, không
  tên cột, không dấu vết ngăn xếp.
- Cấu hình: `DEBUG` theo biến môi trường (mặc định 0) · `ALLOWED_HOSTS` và
  `CORS_ALLOWED_ORIGINS` là danh sách trắng, **không** `CORS_ALLOW_ALL_ORIGINS` ·
  `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS=SAMEORIGIN`, HSTS 1 năm và
  `SESSION_COOKIE_SECURE` khi production.

**E · Tiêm và ép kiểu.** SQL của dự án là SQL thuần; đã soát MỌI chỗ ghép chuỗi:
- `thuoc_buoi()` — 18 chỗ gọi, **cả 18 truyền hằng trong mã** (`'s.id'`, `'%s'`, `'m.user_id'`),
  không một giá trị người dùng nào. Tên cột đều có tiền tố bảng (cái bẫy ghi trong docstring).
- `ORDER BY` động: 2 chỗ, cả hai **danh sách trắng** — `leaderboard/views.py:171`
  (`if order_col not in ('xp','streak'): return`) và `forum/views.py:241` (`sort` → từ điển, `ORDER BY {order}` ở `:283`) (tra từ điển, có
  mặc định). `LIMIT`/`OFFSET` luôn là `%s` qua `so_nguyen`/`doc_trang` đã kẹp biên.
- `UPDATE … SET %s` động: 7 chỗ (`ho_so.py` ×2, `danh_gia.py`, `terms.py`, `views.py`,
  `assignments.py`, `syllabus.py`, `courseadmin/views.py` ×3) — **mọi tên cột đều lấy từ
  bộ/từ điển hằng trong mã**, giá trị luôn đi qua `%s`.
- `f'…{table}…{id_col}…'` trong `forum/views.py`: hằng nội bộ, có chú thích nói đúng thế.
- Ô tìm đi qua `mau_like` (thoát `\`, `%`, `_`) — không thoát thì gõ một dấu `%` là nhận cả
  bảng.

**F · Phía màn.**
- 10 chỗ `dangerouslySetInnerHTML` trong `frontend/src/`: script nạp trước / token màu /
  SVG biểu tượng / `dinhDangTinNhan` của chatbot. Không chỗ nào nhận chuỗi thô từ API của
  người dùng khác.
- `target="_blank"`: quét bằng bộ phân tích thẻ đa dòng (grep một dòng cho kết quả SAI vì
  `rel` nằm dòng kế) — **0 thẻ `<a>` nào thiếu `rel="noopener"`/`noreferrer"`**.
- `href` mang dữ liệu người dùng: bốn cột (`hoc_lieu.url`, `class_sessions.recording_url`,
  `class_sessions.meeting_url`, `classes.meeting_url`) đều chặn ở ĐƯỜNG GHI bằng danh sách
  trắng `http/https` (`common/params.kiem_lien_ket`, `hoc_lieu.dia_chi_hop_le`). **Đo trên
  CSDL dev: 0/45 dòng có link lệch lược đồ** — tức không còn dữ liệu cũ từ trước bản vá §60.
- Tầng JS cũ (`public/static/js`, 111 chỗ `innerHTML`): quét toàn tệp mọi nội suy `${…}` vào
  chuỗi HTML — **0 chỗ khả nghi**; bảy chỗ còn lại là số nguyên từ máy chủ
  (`question_no`, `score`, `total`, `percentage`) hoặc bộ chọn CSS với tên hằng.
- Token: `pe_at`/`pe_rt` là cookie `httpOnly`, chỉ đọc ở tầng máy chủ Next
  (`src/lib/auth.ts`, `proxy.ts`, `server-api.ts`). **Không một chỗ nào trong
  `frontend/src/` hay `public/static/js/` đọc token vào JavaScript của trang.** Gốc backend
  không có tiền tố `NEXT_PUBLIC_`.

**G · Thư và tin nhắn.**
- `hang_rao_thu`: đo trên máy này — `dang_tro_production = False`, `bat() = True`,
  `phuhuynh@gmail.com` bị chặn, `ai@example.com` đi được. Mặc định là TỪ CHỐI.
- 5 chỗ xếp thư vào hộp thư đi: 4 gửi tới địa chỉ của CHÍNH tài khoản / của phụ huynh đã
  được trung tâm nhập. Chỗ thứ 5 (`tu_dang_ky.py:204`) là địa chỉ do người gửi chọn — bản
  chất của xác nhận email, thân thư đã bịt ở mục 2.
- Không có cửa nào gửi thư tới địa chỉ TUỲ Ý do người dùng nhập vào một ô khác (kiểu "gửi
  bản sao tới…").
- **Đường thư duy nhất đi vòng qua hàng rào là allauth** — mục 1.

---

## 8 · Cổng đã chạy

```
python -m ruff check .                 → All checks passed!
python manage.py check                 → 0 issues
python scripts/quet_bi_mat.py --tat-ca → 835 tệp, 0 bí mật
python scripts/quet_bi_mat.py --tu-kiem→ 6/6 quy tắc đỏ đúng chỗ
python scripts/tang_vai.py --kiem      → 46 trang, 0 lệch chưa giải thích
pytest common/tests_lo_ton_tai.py      → 7 ĐẠT   (7 ĐỎ trước khi vá)
pytest accounts/tests_tiem_thu_dang_ky → 6 ĐẠT   (4 ĐỎ trước khi vá)
pytest common/tests_ma_tran_quyen.py   → 3 ĐẠT   (2 HỎNG trên HEAD)
pytest teaching/tests_ban_ghi.py forum/tests.py forum/tests_dien_dan_lop.py → 44 ĐẠT
pytest accounts/                       → 96 ĐẠT
```

**Chưa chạy:** `pytest` toàn bộ (~54 phút) · `pnpm build` / `pnpm lint` (brief cấm dựng
`next dev`; không sửa tệp `.tsx` nào nên tsc không có gì mới để đọc) · `bash .githooks/pre-push`
(gọi hai lệnh trên).

**Chưa soát:** `teaching/bao_cao_cheo.py` (chưa có trên gốc `7f93250`) · luồng Google OAuth
đi thật (`accounts/oauth.py` — đọc mã, không đăng nhập thử) · nội dung 66 đường của allauth
ngoài bốn cửa đã đo · `chatbot/` (tiêm nhắc AI — một trục khác hẳn, không đủ thời gian) ·
không mở màn nào trong trình duyệt (brief cấm dựng `next dev`; lượt này không sửa giao diện).
