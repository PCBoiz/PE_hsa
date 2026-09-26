# E2 — HỘP THƯ ĐI (§61) + THÔNG BÁO TRUNG TÂM · đưa `agent/e2` về đích

26/09/2026. Người làm: agent E2 (trước đó là agent soát — xem `SOAT_26_09.md`).
Việc: commit phần còn treo, gộp `erp`, chạy lược đồ + test + đột biến, đo màn
thật, qua cổng pre-push, rồi giao lại cho lead gộp vào `erp`.

## Kết luận ngắn

**Backend §61 XONG và đo được.** Nhánh dừng ở `<HEAD>`, gộp `erp` tới `7f903f7`.

**Nhưng nhánh này KHÔNG tự đóng được dòng 20 và dòng 27** — vì E2 là backend
thuần: trong 29 tệp E2 viết, đúng **một** tệp thuộc frontend (`src/lib/viecNhatKy.ts`,
một dòng nhãn nhật ký). Không tệp nào trong `frontend/src` gọi `/api/admin/thong-bao`
hay `/api/teach/classes/<id>/thong-bao`; `/thong-bao` và `/notifications` đều trả
"Không có trang này". Chi tiết ở §5.

---

## 1 · Năm (thật ra MƯỜI MỘT) tệp treo trong worktree

Lời giao nói 5 tệp; cây có **9 tệp sửa + 2 tệp mới**. Tất cả là MỘT khối việc —
bốn quyết định anh Sơn chốt 26/09 — nên commit thành một lượt (`bda7cf9`).

| # | Quyết định | Tệp | Kiểm được ở đâu |
|---|---|---|---|
| 1 | Trợ giảng gửi thông báo cho **lớp mình** | `views_thong_bao.py` | §4 đo API |
| 2 | Bản xem trước đếm đúng thứ **sắp xảy ra** (`gui_email` mặc định False) | `thong_bao.py`, `views_thong_bao.py` | §4 đo API |
| 3 | **Hàng rào thư ở máy dev** | `hang_rao_thu.py` (mới), `tests_hang_rao_thu.py` (mới), `hop_thu.py` | §4 đo thật |
| 4 | **Ưu tiên** giao dịch/hàng loạt + **trần ngày** | `legacy_schema.sql` §61a, `hop_thu.py`, `gui.py`, `nhac_han.py`, `thong_bao.py`, `kiem_luoc_do.py` | §4 đo thật |

Giữ hết, không bỏ gì. Hai chỗ đáng nêu vì làm đúng:

- **`ALTER TABLE outbox ADD COLUMN IF NOT EXISTS priority`** vẫn có mặt dù
  `CREATE TABLE` ở trên đã khai cột. Không thừa: CSDL nào đã dựng bảng theo bản
  §61a đầu thì `CREATE TABLE IF NOT EXISTS` bỏ qua **cả bảng**, và cột mới sẽ
  không bao giờ tới. Đây đúng là trường hợp của Neon dev.
- **Mốc "0h00 hôm nay giờ VN" viết bằng SQL**, không dựng ở Python. `sent_at =
  now()` đi qua `SET TIME ZONE` của phiên (Django đặt UTC), nên so với một mốc
  naive dựng theo giờ VN là lệch 7 tiếng — đúng lớp lỗi `common/clock.py` mô tả.

---

## 2 · Gộp `erp` (`7f903f7`) — hai chỗ đụng, cùng một dạng

Cả hai đều là: **`erp` viết lại LỜI THƯ, `e2` đổi ĐƯỜNG ĐI của thư**. Giữ cả hai
— lời của `erp`, đường của `e2`.

| Tệp | `erp` làm gì | `e2` làm gì | Giải quyết |
|---|---|---|---|
| `accounts/quen_mat_khau.py` | viết lại thân thư, bản HTML có nút bấm | tách `_gui_thu` → `_soan_thu` trả `(chữ, html)`, xếp vào `outbox` cùng giao dịch với chìa | lấy chữ của `erp` đặt trong `_soan_thu`; bỏ `mail.gui` trực tiếp và nhánh `log.warning` — lỗi gửi nay ở `outbox.error`, không kèm đường dẫn |
| `teaching/bao_doi_lich.py` | thêm `_gio_dep` ("thứ Hai 29/09, 10:26"), `_ten` (không ra "Lớp Lớp …"), thân thư có lời chào/lời chúc | đưa thư qua `xep_thu` + `hop_thu.day_di` trong `transaction.atomic()` | lấy `chu_thu` của `erp`, giữ khối giao dịch của `e2`; `threading` + `_gui_thu` bỏ theo `e2` |

### `notifications/service.py` — chỗ lời giao dặn đọc kỹ

**Không đụng độ.** `service.py` vào nguyên bản `erp` (`git diff HEAD` rỗng cho
tệp ấy sau gộp). Lý do: E2 **không nhân bản** logic gộp — chỉ gọi `notify` qua
mặt tiền `gui.py:84`.

Ngữ nghĩa mới của `erp` (không `title_multi` → tiêu đề lấy của lần MỚI NHẤT) là
**đúng thứ E2 cần**: thông báo, nhắc hạn, đổi lịch đều là "bản mới đè bản cũ",
không phải cộng dồn. `grep title_multi` trong mã E2: không chỗ nào.

Một chỗ để lead biết, **không phải lỗi**: `gui()` không có tham số `title_multi`,
nên người gọi nào muốn kiểu TÍCH LUỸ ("3 thông báo mới") thì chưa có đường xin.
Hôm nay chưa ai cần. (Đây đúng lớp lỗi lượt soát tìm ra ở §72 — nên ghi lại kẻo
quên.)

### Kiểm sau gộp

- **§NN không trùng**: §61 (dòng 2146), §71 (2249), §72 (2281). Khoá kiểm
  `§61a–d`, `§71a–c`, `§72a–b` mỗi khoá đúng một lần. DDL chỉ cộng thêm nên thứ
  tự trong tệp không ảnh hưởng.
- **`scripts/lib/phien_do.mjs`** vào trọn từ `erp`: còn vai `tg` và tuỳ chọn
  chụp `{toanTrang, toi}`, không bị ghi đè.
- **`.githooks/pre-push`** giữ `node --max-old-space-size=2048` cho eslint.
- **Thuật ngữ**: `frontend/e2e/unit/thuat-ngu.test.mjs` → `ĐẠT` (0 chỗ "hợp
  phần", 0 chỗ mở đầu "Mọi ").
- Lead đã vá §72 theo lượt soát trước: `ban_ghi.py` nay dùng `thuoc_buoi` ở cả
  ba chỗ (`_thuoc_lop`, mẫu số thống kê, danh sách nhắc).

---

## 3 · Lược đồ và bộ kiểm

```
bootstrap_schema lượt 1 → 0/67 mục chạy (3 câu) · bảng: 76 -> 76
bootstrap_schema lượt 2 → 0/67 mục chạy (3 câu) · bảng: 76 -> 76
kiem_luoc_do            → 72/72 mục đã tới nơi   (không dòng ✗ nào)
manage.py check         → System check identified no issues (0 silenced)
ruff check .            → All checks passed!
```

pytest **từng mô-đun** (Neon dev dùng chung):

| Mô-đun | Kết quả |
|---|---|
| `notifications/tests_hang_rao_thu.py` | 19 passed in 49.05s |
| `notifications/tests_hop_thu.py` | 29 passed in 109.93s |
| `notifications/tests_thong_bao.py` | 20 passed in 172.77s |
| `notifications/tests.py` (gộp chuông, của `erp`) | 8 passed in 23.12s |
| `notifications/tests_gui.py` | 9 passed in 35.77s |
| `notifications/tests_feed.py` | 7 passed in 33.94s |
| `notifications/tests_nhac_han.py` | 10 passed in 50.60s |
| `notifications/tests_chuyen_hop_thu.py` | 6 passed in 51.58s |
| `accounts/tests_quen_mat_khau.py` | 13 passed in 86.76s |

Chạy sáu mô-đun TRONG MỘT lượt: `100 passed, 36 warnings in 535.79s`.

### Một chỗ tự vấp, ghi lại để người sau khỏi mất giờ

Lượt đột biến đầu báo **"Nền ĐỎ — dừng"** trong khi từng mô-đun đều xanh. Không
phải lỗi mã: tôi đã cho bộ đột biến chạy **song song** với một lượt pytest khác
trên **cùng CSDL Neon dev**. Đúng thứ `backend/conftest.py` cảnh báo ("hai lượt
CI song song đập nhau"). Chạy lại khi CSDL yên tĩnh thì nền xanh.

---

## 4 · ĐO TRÊN MÀN THẬT (Next 3600 → Django 9500, nhánh `agent/e2`)

Thẻ cấp lại ngay trước mỗi lượt. Lớp đo: **7586 "AUDIT2009 Lớp thử — Ca tối"**,
cả 3 học viên đều `@example.com` — thư ra khỏi hệ thống là không rút lại được
nên chỉ đo trên lớp toàn địa chỉ thử.

### 4.1 · Quyết định 2 — bản xem trước đếm đúng thứ sắp xảy ra

```
POST /api/admin/thong-bao/preview  {"audience":{"classIds":[7586]}}
→ {"tong":3,"chuong":3,"email":0,...}          ← ô "Gửi kèm email" để TRỐNG

POST /api/admin/thong-bao/preview  {...,"sendEmail":true}
→ {"tong":3,"chuong":3,"email":3,...}
```

### 4.2 · Trọn vòng: học vụ gửi → hộp thư đi → chuông của em

```
POST /api/admin/thong-bao        → {"id":36,"status":"draft","recipientCount":0}
POST /api/admin/thong-bao/36/gui → {"id":36,"status":"sent","recipientCount":3}
```

Dòng `outbox` (ưu tiên **1 = HÀNG LOẠT**, đúng: 3 người nhận):

```
{'id':1409,'to_addr':'audit2009.hv1@example.com','priority':1,'status':'sent','attempts':1,'error':None,'sent_at':2026-09-26 10:55:56}
{'id':1410,'to_addr':'audit2009.hv2@example.com','priority':1,'status':'sent','attempts':1,'error':None,'sent_at':2026-09-26 10:55:59}
{'id':1411,'to_addr':'audit2009.hv3@example.com','priority':1,'status':'sent','attempts':1,'error':None,'sent_at':2026-09-26 10:56:03}
```

Chuông của em (màn thật, **đã soi ảnh** `e2_chuong_hoc_vien.png`): badge **4**,
panel mở ra có đúng thông báo vừa gửi ở dòng đầu, kèm "2 phút trước" và
"(chưa đọc)".

```
/api/notifications/badge → 200 {"unread":4,"latest":3945}
/api/notifications/feed (KHÔNG tham số — tầng JS cũ gọi thế này)
  → khoá ["items","unread"], 5 dòng, unread=4, dòng đầu "E2 thử nghiệm: hộp thư đi §61"
```

**Tương thích ngược giữ được**: `FeedView` viết lại nhưng không tham số thì vẫn
trả đúng hình dạng cũ, nên `frontend/public/static/js/dashboard.js` (tầng JS cũ,
nơi chuông thật sự sống) không phải sửa một dòng.

### 4.3 · Ruột mới: phân trang theo khoá, lọc, chưa đọc

```
?limit=2              → 2 dòng, tiep=586, cacLoai=["assignment_graded:3","assignment_new:1","thong_bao:1"]
trang 1 id=[3945,586] | trang 2 (truoc=586) id=[585,584] | TRÙNG: không
?chuaDoc=1&limit=50   → 4 dòng, trong đó ĐÃ đọc: 0
?loai=thong_bao       → 1 dòng, các loại trả về = ["thong_bao"]
```

### 4.4 · Quyết định 3 — hàng rào thư CHẶN địa chỉ thật

Đo bằng một hộp thư **không tồn tại**, để nếu hàng rào hỏng thì cũng không tới ai:

```
hàng rào đang BẬT? True
địa chỉ được phép: ['@example.com', '@example.org', '@example.net']

xếp thư tới 'khong-ton-tai-pe-hsa-soat-26092026@gmail.com' → id 1412
kết quả: ('dropped', None, 'Máy này không nối CSDL production nên hàng rào thư
  đang bật: chỉ gửi tới @example.com, email tài khoản kiểm thử, hoặc địa chỉ
  trong OUTBOX_DIA_CHI_CHO_PHEP. Địa chỉ kh***@gmail.com không có trong danh
  sách nên không gửi …')
```

Hai điều làm đúng: trạng thái là `dropped` (**không** `failed` — thử lại bao
nhiêu lần cũng vẫn địa chỉ ấy), và cột `error` **che** địa chỉ (`kh***@gmail.com`)
trong khi `to_addr` giữ nguyên để còn gửi lại được khi lên production.

### 4.5 · Quyết định 1 — trợ giảng gửi được LỚP MÌNH, không hơn

Thẻ trợ giảng id 36882 (phụ trách lớp 7586):

| Việc | Mã | Ghi chú |
|---|---|---|
| Xem trước lớp MÌNH (7586) | **200** | `{"tong":3,"chuong":3,...}` |
| GỬI lớp MÌNH (7586) | **201** | |
| GỬI lớp KHÁC (7322) | **404** | `{"error":"Không tìm thấy lớp này."}` — không lộ lớp có tồn tại |
| Tuyến học vụ, cả khối | **403** | `IsAdminOrAcademic` vẫn chặn |

---

## 5 · Hai dòng bị chặn — còn thiếu đúng một thứ: MÀN

E2 viết 29 tệp; **một** tệp thuộc frontend (`src/lib/viecNhatKy.ts`, một dòng).
`grep` toàn `frontend/src`: **không nơi nào** gọi `/api/admin/thong-bao`,
`/api/teach/classes/<id>/thong-bao`, hay tham số mới của `/api/notifications/feed`.

### Dòng 20 · Trợ giảng · nhắn / nhắc

- **Có rồi**: API gửi thông báo cho lớp mình, phân quyền đã đo (§4.5), thư đi qua
  hộp thư đi, chuông tới em.
- **Còn thiếu**: (a) **màn soạn** cho trợ giảng/giảng viên trong khu Giảng dạy;
  (b) phần "nhắn **hai chiều**" — đó là E3 (hộp Yêu cầu §65), không phải E2.
- Nói cho đúng: E2 đóng được nửa "nhắc", **không** đóng được nửa "nhắn".

### Dòng 27 · Học sinh · thông báo

- **Có rồi**: chuông chạy thật trên màn (§4.2, có ảnh), thông báo trung tâm tới
  nơi, ruột phân trang/lọc/chưa đọc đã đúng (§4.3).
- **Còn thiếu**: **màn "Thông báo"** — `/thong-bao` và `/notifications` đều trả
  "Không có trang này". Phân trang theo khoá, bộ lọc và `cacLoai` hiện chỉ gọi
  được bằng `fetch`, chưa ai bấm tới được.

> **Đề nghị lead**: mở một việc giao diện nhỏ (E2-GD) cho hai màn này. Backend đã
> đứng sẵn và có phép kiểm; phần còn lại thuần React. Không có nó thì hai dòng ấy
> vẫn là "MỘT PHẦN" dù mã đã viết xong.

---

## 6 · Hai chỗ E2 bỏ sót — cổng bắt được cả hai, đã vá

### 6.1 · f7 · `scripts/cau_truc.py --kiem` — hai bảng mới không có chủ

```
✗ bảng `outbox` (§61) không miền nào sở hữu — thêm vào `bang` của một miền ở so_mien.json
✗ bảng `announcements` (§61) không miền nào sở hữu — …
✗ `docs/CAU_TRUC_DU_LIEU.md` đã cũ … ✗ `docs/CAU_TRUC_MA.md` đã cũ …
cấu trúc: … 4 lỗi
```

E2 dựng hai bảng mới suốt 7 commit mà chưa ghi chủ trong `scripts/so_mien.json`.
Đã thêm `outbox` + `announcements` vào miền `thong_bao`, viết lại `mo_ta` (không
còn "sắp có"), chạy lại `scripts/cau_truc.py`. Nay: **0 lỗi**.

### 6.2 · f5 · `scripts/ban_do.mjs --kiem` — tám tuyến mới không ai gọi

```
gãy: 0 lời gọi không khớp · 8 tuyến không ai gọi chưa có lý do · …
mã thoát = 1
```

Tám tuyến ấy là **đúng những tuyến E2 vừa dựng**:

```
/api/admin/thong-bao            /api/teach/classes/*/thong-bao
/api/admin/thong-bao/preview    /api/teach/classes/*/thong-bao/preview
/api/admin/thong-bao/*/gui      /api/notifications/feed/*/unread
/api/admin/thong-bao/*/huy      /api/noi-bo/tick
```

Cổng làm đúng việc của nó: nó **từ chối cho backend-không-có-màn đi qua trong im
lặng**. Chú thích ngay trong `ban_do.mjs` đã nói trước: *"Tuyến mới mà không ai
gọi sẽ làm `--kiem` đỏ: hoặc nối nó vào giao diện, hoặc ghi vào đây kèm lý do."*

Dựng màn nằm ngoài việc này, nên tôi **ghi nợ cho đúng tên**:

- `/api/noi-bo/tick` → `KHONG_CAN_NGUOI_GOI`. Tuyến này có người gọi thật, chỉ
  là người gọi ở ngoài mã của mình — một cron gõ vào kèm `X-Tick-Key`. Cùng loại
  với hai tuyến `.ics` của §71.
- Bảy tuyến còn lại → **`CHO_MAN`**, một danh sách MỚI. Không nhét vào
  `UNG_VIEN_GO` được: danh sách ấy nghĩa là "nợ chờ anh Sơn quyết gỡ hay nối
  lại", còn đây là **việc còn dở đã có người nhận**. Mỗi dòng phải biến mất khi
  màn ấy dựng xong, và `lyDoMoCoi` canh để dòng nào trỏ vào tuyến đã tháo thì
  cổng đỏ.

Sau khi vá: `0 tuyến không ai gọi chưa có lý do`, mã thoát 0. Tự kiểm của chính
máy quét vẫn bắt đủ sáu trường hợp (`--kiem --tu-kiem`), trong đó có *"tuyến
không ai gọi → BẮT ĐƯỢC"* và *"lý do cho tuyến đã tháo → BẮT ĐƯỢC"* — tôi không
làm cùn cái thước khi nới nó.

### 6.3 · Việc thêm cho anh Sơn

Đã thêm **E2a** vào `docs/VIEC_CUA_ANH.md`: đặt `OUTBOX_TICK_SECRET` trên Render
nếu muốn cron ngoài đẩy hộp thư đi. **Không đặt cũng chạy** —`ENABLE_OUTBOX=1`
đã có sẵn trong `render.yaml`, luồng nền tự gửi mỗi 60 giây.

---

## 7 · Đột biến

`scripts/dot_bien_e2.py` (mới, cùng khuôn `dot_bien_e1.py`): 16 đột biến trên các
luật then chốt của §61 — hàng rào thư, ưu tiên + trần ngày, xoá thân thư có chìa,
thư quá hạn, nhận việc không đè nhau, xem trước, quyền trợ giảng.

Lời giao nhắc dùng `scripts/dot_bien.py` (loạt JSON) — **tệp ấy chưa có trên
`erp` tại `7f903f7`**, chỉ có `scripts/dot_bien_e1.py`. Có lẽ phiên lead đứt
trước khi commit. Nên tôi viết `dot_bien_e2.py` theo khuôn cũ; khi `dot_bien.py`
lên `erp` thì chuyển 16 mục này thành JSON là xong.

<KET_QUA_DOT_BIEN>

---

## 8 · Cổng pre-push

<KET_QUA_CONG>

---

## 9 · Dọn

<KET_QUA_DON>
