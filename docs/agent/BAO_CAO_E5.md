# E5 — Học viên tự đăng ký + hàng chờ xếp lớp (§73)

Nhánh **cục bộ** `agent/e5` (nền `erp` `0438a46`). Đóng **dòng 26** của bảng nghiệm thu
(*"Học sinh · tài khoản + tự đăng ký"*, đang MỘT PHẦN) và mốc **"Đăng ký"** của **dòng 4**.

---

## 1 · Sáu câu phải trả lời trước khi viết một dòng mã

### 1.1 Ai đăng ký được, cần những gì

Ai cũng vào được `/dang-ky` — đây là cửa tuyển sinh, không phải cửa nội bộ. Phiếu hỏi:

| Ô | Bắt buộc | Vì sao |
|---|---|---|
| Họ tên | có | học vụ gọi lại phải biết gọi ai |
| Email | **có** | kênh xác thực DUY NHẤT, và là đường em tự lấy lại mật khẩu sau này (§52) |
| Số điện thoại | **có** | trung tâm luyện thi gọi điện tư vấn xếp lớp; không có số thì hàng chờ vô dụng |
| Mật khẩu | có | em tự chọn — không cấp mật khẩu tạm, nên không ai ngoài em từng biết nó |
| Biết TopHSA từ đâu | có | `users.enroll_source` (§51) — số liệu tuyển sinh; danh mục lấy TỪ MÁY CHỦ |
| Trường / lớp ở trường / mục tiêu | không | xếp lớp đúng trình độ; thiếu thì học vụ hỏi lúc gọi |

Vai luôn là `Học viên` — hằng trong mã, không đọc từ thân yêu cầu. `_kiem()` đọc đúng tám
khoá ấy, nên không có đường "gán hàng loạt" để nhét `role` hay `is_verified` vào.

### 1.2 Có xác thực email không, và nếu chưa có kênh gửi thì sao

**Có, và bắt buộc.** `LoginView` chặn `self_registered AND NOT is_verified`. Tài khoản
chưa bấm thư là **tài khoản chết**: không đăng nhập được → không có token → không gọi
được API nào → không đốt được một xu tiền trợ lý AI (đúng lỗ hổng mà lần bỏ tự đăng ký
27/08/2026 đã bịt).

Kênh gửi **đã có sẵn**: hộp thư đi §61 (E2) — cùng đường mà `quen_mat_khau` đang dùng
thật. Nên câu hỏi "nếu chưa có kênh gửi thì làm gì" không còn phải trả lời bằng giả định.

Điều kiện cứng để hàng rào này không làm hỏng ai: nó chỉ chặn khi `self_registered`. Cột
`users.is_verified` có trong lược đồ từ đầu nhưng **chưa ai từng ghi**, nên với toàn bộ
học viên hiện có nó là FALSE/NULL — chặn theo `is_verified` trần là khoá cửa cả TopHSA.
Phép kiểm `test_tai_khoan_TRUNG_TAM_CAP_khong_bi_hang_rao_moi_chan` giữ đúng chỗ ấy.

**Tài khoản chưa xác thực có thành lỗ hổng không?** Ba đường đã bịt:

1. không đăng nhập được (trên);
2. **không vào hàng chờ của học vụ** — dòng `yeu_cau` chỉ sinh ra ở cửa *xác nhận email*,
   nên ai bơm địa chỉ bừa cũng không làm bẩn hộp việc, chỉ để lại vài dòng `users` trơ;
3. **không khoá được một địa chỉ email khỏi TopHSA**: một dòng chưa xác thực **nhận lại
   được** — người thật đăng ký lại trên chính dòng ấy, họ tên / mật khẩu / hồ sơ ghi đè,
   mã cũ chết. Không có luật này thì bất kỳ ai cũng chiếm vĩnh viễn email của em bằng một
   lượt POST. (Dòng ĐÃ xác thực hoặc do trung tâm cấp thì KHÔNG nhận lại được.)

### 1.3 Hàng rào chống lạm dụng

| Lớp | Cái gì | Mức | Ở đâu |
|---|---|---|---|
| 1 | `DangKyThrottle` theo IP, dùng CHUNG cho cả ba cửa | 20/giờ (prod), 600/giờ (dev) | `common/throttling.py` |
| 2 | Tài khoản CHƯA xác thực một IP mở được trong 24 h | `TRAN_IP_MOI_NGAY = 5` | đếm trong CSDL |
| 3 | Mã xác nhận một TÀI KHOẢN xin được trong một giờ | `TRAN_MOI_GIO = 5` | đếm trong CSDL |

Lớp 1 nằm trong bộ đệm — `LocMemCache` sống theo từng tiến trình gunicorn, khởi động lại
là mất sạch. Lớp 2 và 3 đếm trong CSDL nên không mất. Lớp 2 đếm qua
`password_reset_tokens.requested_ip` (mã `verify` nào cũng ghi IP lúc cấp) — **không thêm
cột nào vào `users`** — và **chỉ đếm em CHƯA xác thực**, nên một lớp 35 em cùng đăng ký
sau một NAT vẫn đi được, chỉ không để lại 35 dòng trơ.

**Trùng email / số điện thoại: KHÔNG nói.** Email trùng, số điện thoại trùng, quá trần,
đụng chỉ mục duy nhất — tất cả nhận **cùng một câu 200**. Một câu "Email đã được sử dụng"
là một công cụ dò xem ai đang học ở TopHSA, mà nạn nhân ở đây là trẻ vị thành niên. Cùng
luật với `LoginView`, `QuenMatKhauView` và tờ báo cáo phụ huynh.
Trường hợp email đã có tài khoản THẬT thì gửi một lá thư "địa chỉ này đã có tài khoản,
đăng nhập ở đây, quên mật khẩu ở đây" — tới địa chỉ CỦA CHÍNH tài khoản ấy, nên không
phải một đường bơm thư tới người lạ.

### 1.4 Học vụ thấy người mới ở đâu, duyệt / xếp lớp thế nào

**Dùng lại hộp Yêu cầu §65 — không dựng hộp mới.** Loại mới `tk_dang_ky`, nhóm THAY_DOI,
`viec: 'tu_dong'`, `chon_lop_toi: True`, không `can_lop` (lúc gửi em chưa có lớp nào).

Nhờ vậy nó thừa hưởng nguyên bộ luật đã có: chỉ học vụ / quản trị duyệt và từ chối; giao
việc; trả lời; ghi chú nội bộ ẩn với em; nhật ký; **duyệt = thực thi trong MỘT giao dịch**;
duyệt hai lần chỉ xếp lớp một lần. Dựng một bảng "đăng ký chờ duyệt" riêng là dựng bản thứ
hai của cùng một máy trạng thái.

Duyệt → `yeu_cau/thuc_thi.py` gọi `AdminClassMembersView._ghi_thanh_vien` (luật S4: miền
`yeu_cau` không ghi bảng miền khác), nên trần lớp gia sư và mọi hàng rào xếp lớp khác vẫn
nguyên. Lớp lấy từ `den_lop_id` học vụ chọn lúc duyệt, **không** từ `yeu_cau.class_id`.

`tk_dang_ky` nằm trong `L.CHI_HOC_VU` cùng `ht_tai_khoan`: giảng viên và trợ giảng không
bao giờ thấy — lượt đăng ký mang số điện thoại và email của em.

### 1.5 Mốc "Đăng ký" trên dòng thời gian

Hai mốc, không một:

- `users.self_registered` → mốc đầu đổi từ *"Được cấp tài khoản"* thành **"Tự đăng ký tài
  khoản trên website"**;
- nhật ký `user.verify_email` → **"Xác nhận địa chỉ email"**.

Khoảng cách giữa hai mốc chính là thứ học vụ đọc khi một lượt đăng ký trông đáng ngờ. Nhãn
hai mã mới cũng vào `frontend/src/lib/viecNhatKy.ts` (guard `e2e/unit/nhan-nhat-ky.test.mjs`).

### 1.6 Chỗ phải anh Sơn quyết

Ghi vào `docs/VIEC_CUA_ANH.md` mục **E5a**, kèm đề xuất và lý do:

1. **Bắt xác nhận email trước khi vào học?** — đã làm "BẮT" (an toàn hơn); đề xuất giữ.
2. **Số điện thoại trùng: nói thẳng hay im?** — đã làm "IM" (không lộ ai học ở TopHSA);
   đề xuất giữ, vì người thật gặp ca này gần như chắc chắn đã có tài khoản ở đây.

---

## 2 · Đã làm gì

**Lược đồ §73** (chỉ cộng thêm; `bootstrap_schema` lượt 2 = `0/70 mục`, `kiem_luoc_do`
83/83 ✓):

- `users.self_registered BOOLEAN NOT NULL DEFAULT FALSE` + chỉ mục PHẦN cho hàng chờ;
- `password_reset_tokens.purpose` (`reset` | `verify`) + CHECK + chỉ mục
  `(user_id, purpose, created_at)` — MỘT bảng chìa cho hai việc;
- `'tk_dang_ky'` thêm vào `yeu_cau_loai_check`.

**Backend** — `backend/accounts/tu_dang_ky.py` (miền `tai_khoan`, chủ bảng `users`), ba cửa
`AllowAny` + `authentication_classes = []`:
`POST /auth/dang-ky` · `POST /auth/xac-thuc-email` · `POST /auth/gui-lai-xac-thuc`
(+ `GET /auth/dang-ky` trả danh mục nguồn cho ô chọn — màn không gõ lại danh mục).
Mã đi trong `#…`, chỉ lưu băm sha256, hạn 72 giờ, dùng một lần, gốc đường dẫn từ
`FRONTEND_URL` chứ không từ header Host.

**Frontend** — `/dang-ky` (server page + `PhieuDangKy`), `/xac-thuc-email`, nút "Gửi lại
thư xác nhận" ngay tại chỗ bị chặn trên `/login`, và link "Đăng ký học" ở chân trang đăng
nhập.

---

## 3 · Số đo thật

| Phép đo | Kết quả |
|---|---|
| `scripts/do_dang_ky.mjs` (Chromium, màn thật, bấm chuột) | **20/20 bước ĐẠT** — vai khách (chưa đăng nhập) + học vụ; màn `/dang-ky`, `/login`, `/xac-thuc-email`, `/yeu-cau`, `/yeu-cau/<id>` |
| `backend/accounts/tests_tu_dang_ky.py` | **28/28 xanh** (đỏ trước: 27 hỏng / 1 đạt trên mã cũ) |
| Hồi quy `yeu_cau` + `quen_mat_khau` + `accounts` + `ho_so` | **110/110 xanh** |
| `bootstrap_schema` lượt 2 | `0/70 mục chạy` |
| `kiem_luoc_do` | `83/83 mục đã tới nơi` (thêm §73a–d) |
| `ruff` · `manage.py check` | sạch · 0 vấn đề |
| `pnpm lint` (`eslint --max-warnings 0`) · `pnpm build` | xanh · `✓ Compiled successfully in 36.8s` |
| `python scripts/cau_truc.py` | 16 miền, 61 bảng, **0 lỗi**, ghi chéo giữ nguyên 11 (không thêm nợ) |
| `quet_bi_mat.py --tat-ca` · `--tu-kiem` | 790 tệp sạch · 6/6 quy tắc đỏ đúng chỗ |
| axe-core 4.10.3 trên `/dang-ky` + `/xac-thuc-email` | **0 vi phạm** × 4 tổ hợp (1440 và 390 px, sáng và tối) |
| Tràn ngang ở khổ điện thoại | `scrollWidth = 390` = `innerWidth` — không tràn |
| Cổng `bash .githooks/pre-push` | **Cổng kiểm ĐẠT** (15 bước, 108 s) |

Ảnh đã XEM (không chỉ tạo): phiếu đăng ký, màn "đã gửi", màn bị chặn ở đăng nhập, màn xác
nhận xong, hàng chờ của học vụ, màn duyệt kèm ô "Xếp vào lớp" và câu xem trước
*"Hệ thống sẽ: Xếp Em Đo Đăng Ký vào lớp «AUDIT2009 Lớp thử — Ca tối» (môn Tư duy Định lượng)."*

---

## 4 · Dòng 26 nay đứng ở đâu — và CÒN THIẾU GÌ

**Đóng.** Cả luồng chạy thật trên màn: đăng ký → thư → xác nhận → đăng nhập → hàng chờ →
học vụ duyệt và xếp lớp.

Nói thẳng phần chưa làm:

1. **Chặn tần suất theo SỐ ĐIỆN THOẠI thì chưa có.** Trần đang đếm theo IP và theo tài
   khoản. Ai có nhiều IP vẫn mở được nhiều tài khoản, mỗi cái một số điện thoại bịa.
2. **Chưa dọn tài khoản chưa xác thực quá hạn.** Mã chết sau 72 giờ nhưng dòng `users` ở
   lại, giữ email và số điện thoại trong chỉ mục duy nhất (nhận lại được, nên không khoá
   ai, nhưng vẫn là rác). Cần một lệnh quản trị dọn định kỳ.
3. **Mỗi lượt đăng ký tiêu một số của `student_code_seq`** (mã HSA-xxxxx cấp ngay lúc
   tạo). Spam trong trần 5/IP/ngày thì thủng vài số — mã HV sẽ có lỗ. Sửa được bằng cách
   dời `cap_ma_hoc_vien` sang bước XÁC NHẬN; chưa làm vì `admin_users` gọi nó ngay lúc
   tạo và tôi không muốn hai đường lệch nhau trong cùng một lượt.
4. **Không có CAPTCHA**, và cũng không đề xuất thêm: nó đổi một cửa đang chạy tốt lấy một
   phụ thuộc bên ngoài. Trần theo IP + xác nhận email đã chặn đúng thứ đáng chặn.
5. **Thư đi tới đâu trên production phụ thuộc `FRONTEND_URL`** — việc **N3** của anh Sơn
   vẫn treo. Biến ấy sai thì đường dẫn trong thư xác nhận chết, đúng như thư quên mật khẩu.

---

## 5 · Soát bảo mật cửa công khai

Đã chạy skill `soat-bao-mat`. Kết quả:

- `quet_bi_mat.py --tat-ca`: 790 tệp, **0 bí mật**; `--tu-kiem`: 6/6 quy tắc đỏ đúng chỗ.
- `quet_quyen.py`: sau khi vá (mục 6.1 dưới) liệt kê **12 bề mặt công khai**, trong đó ba
  cửa mới đều `AllowAny` + `authentication_classes` rỗng đúng như thiết kế.
- Phép kiểm **từ chối đúng người cần từ chối**, không chỉ đường thuận:
  `test_hoc_vien_khong_tu_gui_duoc_loai_dang_ky` (400 + loại không có trong ô chọn),
  `test_giang_vien_khong_thay_yeu_cau_dang_ky`, `test_chua_xac_thuc_thi_KHONG_dang_nhap_duoc`,
  `test_ma_xac_thuc_khong_dat_lai_duoc_mat_khau`, `test_tran_theo_IP_chan_lam_hang_loat_tai_khoan`.
- Không có đường gán hàng loạt (`_kiem` đọc đúng tám khoá, `role` là hằng).
- Thư chỉ đi tới `@example.com` trong mọi lượt đo — hàng rào `notifications/hang_rao_thu.py`
  giữ nguyên, không nới một dòng nào.

---

## 6 · Lỗi tìm thấy trong mã CÓ SẴN

### 6.1 `scripts/quet_quyen.py:80` — bộ quét "bề mặt công khai" bỏ sót TOÀN BỘ `/auth/*`

`return [r for r in ra if r['duong'].startswith('api/')]`. Bảy cửa công khai không đăng
nhập — bốn cửa quên / đặt lại mật khẩu (§52, có từ 23/09) và ba cửa §73 — nằm **ngoài tầm
mắt** của chính cái báo cáo in ra dòng *"Mỗi dòng ở đây là một bề mặt công khai. Đọc từng
dòng."*

**Số đo:** trước 4 dòng `AllowAny`, sau khi vá **12**. Một danh sách bề mặt công khai
thiếu đúng nhóm cửa nguy hiểm nhất còn tệ hơn không có danh sách — nó làm người soát yên
tâm. **Đã vá** (`startswith(('api/', 'auth/'))`).

### 6.2 `frontend/src/app/(standalone)/yeu-cau/[id]/ChiTietYeuCau.tsx:341` — danh mục loại có bản thứ hai

`const canLop = yc.loai === 'tt_chuyen_lop' || yc.loai === 'tt_chuyen_mon';` — màn tự gõ
lại danh mục loại (RULES §7). Loại thứ ba cần chọn lớp thêm vào sẽ **lặng lẽ mất ô chọn
lớp**, học vụ bấm Duyệt và nhận 400 "Chọn lớp". Tôi vấp đúng cái đó khi thêm `tk_dang_ky`.

**Đã vá:** cờ `chon_lop_toi` về `yeu_cau/loai.py`, máy chủ trả `chonLopToi` trong mỗi yêu
cầu, màn đọc cờ ấy.

### 6.3 `accounts/quen_mat_khau.py:131,140,142,164,208,221` — bảng chìa dùng chung, không lọc việc

Sáu câu chạm `password_reset_tokens` không lọc `purpose`. Sau §73 thì một lượt xin đặt lại
mật khẩu sẽ **huỷ mã xác nhận email** em chưa bấm (và ngược lại, mã `verify` đổi được mật
khẩu → chiếm tài khoản chỉ bằng một lượt đăng ký trùng email). **Đã vá cả sáu câu**, giữ
bằng `test_xin_dat_lai_mat_khau_KHONG_huy_ma_xac_thuc`,
`test_dat_lai_mat_khau_KHONG_huy_ma_xac_thuc`, `test_ma_xac_thuc_khong_dat_lai_duoc_mat_khau`.
(Bẫy này kế hoạch đã ghi trước — tôi xác nhận nó có thật và đã bịt.)

### 6.4 `accounts/quen_mat_khau.py:128–150` — đồng hồ khai ra ai có tài khoản

Docstring viết *"để thời gian trả lời cũng không khác nhau"*, nhưng câu ấy chỉ đúng cho
phần GỬI THƯ (đã đẩy sang luồng riêng). Phần CSDL thì không: nhánh "có tài khoản" đi 4
vòng gọi Neon + scrypt, nhánh "không có" đi 1 vòng.

**Đo được 27/09 trên cửa đăng ký §73 (cùng hình dạng, đo dễ hơn):** nhánh tạo tài khoản
**3,82 / 3,98 / 4,00 s**; nhánh "email đã có tài khoản" **1,43 / 1,90 / 1,96 s** — chênh
gần **hai giây**, ổn định qua ba lượt, trong khi nội dung phản hồi giống hệt nhau.

**Đã làm ở §73:** `_can_dong_ho()` bằm mật khẩu rồi vứt đi ở các nhánh không tạo gì, trả
lại phần chi phí CPU (scrypt ~126 ms) — cùng cách `LoginView._DUMMY_HASH` đã dùng. **Không
xoá hết chênh lệch và chú thích nói thẳng như vậy**: phần dư là số vòng gọi CSDL, và trên
production (Render `ohio` cùng vùng Neon, mỗi vòng vài ms) phần dư ấy nhỏ hơn nhiễu mạng
còn scrypt thì không. **Cửa §52 CHƯA vá** — không sửa trong lượt này vì nó nằm ngoài phạm
vi E5 và cần đo riêng trên production.

### 6.5 Bộ đo: `locator('a, b').first().waitFor()` trả về khi CHƯA có gì khớp

Không phải lỗi sản phẩm, nhưng đã ăn **bốn lượt đo** của tôi nên ghi lại. Câu
`locator('[data-khu="cho-xac-thuc"], [role="alert"]').first().waitFor()` trả về sau
**54 ms** trong khi trang chưa có phần tử nào khớp (lời gọi `/auth/login` còn chưa bay đi)
— bộ đo đọc chuỗi rỗng rồi chấm HỎNG cho một màn hoàn toàn đúng. Cùng phép đo với bộ chọn
ĐƠN: **880 ms, ĐẠT**. Đã ghi vào chú thích `scripts/do_dang_ky.mjs`.

### 6.6 `scripts/lib/phien_do.mjs:44` — đường dẫn Playwright ghim cứng, chỉ chết trong worktree

`createRequire('D:/pe_hsa/frontend/package.json')`. Trong worktree agent, `do_axe.mjs` tự
nạp `@playwright/test` theo đường TƯƠNG ĐỐI (kho của worktree) còn `phien_do.mjs` nạp theo
đường TUYỆT ĐỐI (kho chính) — hai bản khác nhau, và Playwright chết ngay:
`Error: Requiring @playwright/test second time`. Ở kho chính hai đường trỏ cùng một chỗ
nên lỗi **chỉ lộ ra trong worktree**, tức đúng chỗ agent làm việc. **Đã vá**: nạp từ
`frontend/` của chính kho đang chạy, lùi về kho chính nếu worktree chưa cài `node_modules`.

### 6.7 React StrictMode gọi effect hai lần — màn đọc mã trong `#…` hỏng ở dev

`XacThucForm` (mã tôi vừa viết, nhưng cùng hình dạng với `DatLaiForm` có sẵn): lần một đọc
mã rồi `replaceState` xoá `#chia=…`; lần hai không còn thấy mã và ghi đè trạng thái thành
"thiếu mã xác nhận" — cho một đường dẫn hoàn toàn đúng. Tệ hơn, hai lần gọi là **hai lượt
POST** mà mã chỉ dùng được một lần.

Và cái bẫy thứ hai ngay sau khi vá: chốt bằng `ref` rồi mà **vẫn** giữ cờ `huy` trong hàm
dọn dẹp thì hàm dọn dẹp của lượt một chạy trước lượt hai (đã bị chốt chặn) nên nó huỷ đúng
lượt gửi DUY NHẤT — màn đứng mãi ở "Đang xác nhận…" trong khi máy chủ đã xác nhận xong.
Đã vá và ghi lý do trong tệp.

**`DatLaiForm.tsx:38–41` có cùng hình dạng:** lượt hai ghi `chia.current = ''` rồi đặt
trạng thái "hết hạn". Ở đó lượt gọi là `/kiem` (chỉ đọc) nên không đốt mã, và tôi **chưa
đo** màn ấy trong phiên này — nên ghi ra đây như một chỗ đáng đo, không phải một kết luận.

---

## 7 · Cách chạy lại

```bash
cd backend && python manage.py bootstrap_schema          # lượt 2 phải "0/N mục"
cd backend && python manage.py kiem_luoc_do              # §73a–d phải ✓
cd backend && python -m pytest accounts/tests_tu_dang_ky.py -q

powershell -File scripts/nap_lai_be.ps1 -Cong 9600
cd frontend && BACKEND_URL=http://localhost:9600 NODE_OPTIONS=--max-old-space-size=1536 \
  npx next dev -p 3600 --webpack
python scripts/cap_the.py --vai "Quản lý học vụ" --ra .the/tokens_hvu.json
PE_THE=<worktree>/.the PE_WEB=http://localhost:3600 PE_BE=<worktree>/backend \
  node scripts/do_dang_ky.mjs --anh <thư mục ảnh>
powershell -File scripts/don_may.ps1 -Don -Worktree
```

Bộ đo tự DỌN tài khoản `do_dk_…@example.com` chưa xác thực trước mỗi lượt — không có bước
ấy thì lượt thứ sáu bị chính `TRAN_IP_MOI_NGAY` chặn và bước "chưa xác nhận thì không đăng
nhập được" nhận 401 thay vì 403.
