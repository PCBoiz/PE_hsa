# GD — MÀN SOẠN THÔNG BÁO (§61): đóng nửa còn lại của dòng 20, và chiều GỬI của dòng 27

26/09/2026. Người làm: agent GD (worktree `D:/pe_hsa_wt/e2`, nhánh `agent/gd`, nền `7e6c4e9`).
Việc: dựng hai màn cho sáu tuyến backend E2 đã viết xong mà **không màn nào gọi**.

---

## 1 · Số đo thật

Một bộ đo, `scripts/do_thong_bao_lop.mjs`, **bấm chuột trên màn thật trong trình duyệt đã
đăng nhập** — không gọi API tay. Nó gọi `chay()` của `scripts/lib/phien_do.mjs`, không tự
gọi `chromium.launch()`.

```
PE_WEB=http://localhost:3600 PE_THE=D:/pe_hsa_wt/e2/.the node scripts/do_thong_bao_lop.mjs --anh <thư mục>
→ 24/24 bước ĐẠT
```

| Màn | Vai đo | Bước | Kết quả |
|---|---|---|---|
| `/giang-day/thong-bao/7586` | **Trợ giảng** (id 36882) | 13 | 13 ĐẠT |
| `/quan-tri/thong-bao` | **Quản lý học vụ** (id 35743) | 11 | 11 ĐẠT |

Những con số bộ đo đọc ĐƯỢC trên màn (không phải từ API):

- xem trước lớp: *"Sẽ báo cho 3 em qua chuông trong ứng dụng, 3 em nhận email."*
- bước hỏi lại: *"Gửi ngay cho 3 em của lớp AUDIT2009 Lớp thử — Ca tối?"* — nêu đúng số,
  không hỏi "bạn có chắc không";
- gửi xong: *"Đã báo cho 3 em…"*, danh sách lớp 3 → 4 dòng, dòng đầu ghi "3 em nhận";
- lớp KHÔNG phụ trách (`/giang-day/thong-bao/1` bằng thẻ trợ giảng): *"Không mở được lớp
  này"*, và **không có khối soạn nào trên trang**;
- ô chọn lớp của học vụ: **6 lớp**, dựng từ danh mục máy chủ trả;
- ô chọn môn: *Tư duy Định lượng · Tư duy Định tính · Khoa học & Tiếng Anh* — không một
  chuỗi `hsa_*` nào;
- xem trước theo MÔN: **58 em**; huỷ nháp đổi nhãn sang "Đã huỷ" và mất nút Gửi; gửi nháp
  báo *"Đã gửi … tới 2 em."*

Ảnh chụp đã XEM LẠI (RULES §1), không chỉ được tạo ra: `soan-lop-xem-truoc.png`,
`soan-lop-da-gui.png`, `thong-bao-trung-tam.png`, `thong-bao-trung-tam-cuoi.png`.

**Bộ đo này GHI THẬT** — nó bấm Gửi. Ô "Gửi kèm email" để TRỐNG ở mọi bước gửi: dữ liệu là
giả nên chuông thì thoải mái, nhưng thư ra khỏi hệ thống là không cuộn lại được. Và nó chọn
**lớp nhỏ nhất theo con số trên chính ô tick** trước khi gửi bản nháp, nên mỗi lượt đo đẻ ra
2–3 dòng chứ không 58.

**Axe (WCAG 2.x + best-practice)** trên đúng hai màn mới, hai khổ (390 và 1366), thẻ quản trị:

```
node scripts/do_axe.mjs --chi "thông báo"
[390]  GD soạn thông báo lớp   0      [390]  QT thông báo trung tâm   0
[1366] GD soạn thông báo lớp   0      [1366] QT thông báo trung tâm   0
TỔNG: 0 nút vi phạm / 4 lượt · 0 lượt không đo được
```

Cổng: `bash .githooks/pre-push < /dev/null` → **Cổng kiểm ĐẠT** (13 bước, 63 giây).
Backend: `pytest notifications/tests_thong_bao.py -q` → **23 passed**.

---

## 2 · Hai màn đã dựng

### A · `/giang-day/thong-bao/<classId>` — giảng viên & TRỢ GIẢNG (dòng 20)

Tab **"Thông báo lớp"** thứ tư của lớp, cạnh Buổi học và Bài tập (`KhungGiangDay.tsx`).
`troGiang: true` — anh Sơn chốt 26/09 rằng trợ giảng gửi cho lớp mình y như giảng viên, nên
tab này KHÔNG bị lọc khỏi thanh của trợ giảng (khác tab "Báo cáo phụ huynh").

Đặt theo LỚP chứ không cấp khu, vì cửa backend cố định đối tượng là lớp trên đường dẫn
(`_soan(request, {'classIds': [class_id]}, True)`). Một trang cấp khu sẽ phải tự dựng ô chọn
lớp — dựng lại đúng thứ đường dẫn đã mang, và mở thêm một chỗ để lệch với `can_see_class`.

### B · `/quan-tri/thong-bao` — học vụ & quản trị (dòng 27, chiều GỬI)

Tab "Thông báo" trong khu Vận hành. Danh sách + soạn + xem trước + **lưu nháp** + **gửi
nháp** + **huỷ nháp**. Cổng riêng `layout.tsx` như bốn trang khác của khu, và
`e2e/unit/cong-quan-tri.test.mjs` nay canh cả nó (`AdminThongBaoView` phải còn
`IsAdminOrAcademic`).

---

## 3 · Sáu tuyến đã rời `CHO_MAN` — danh sách nay TRỐNG

```
/api/teach/classes/*/thong-bao           → /giang-day/thong-bao/<lớp>
/api/teach/classes/*/thong-bao/preview   → nút "Xem trước người nhận" ở màn ấy
/api/admin/thong-bao                     → /quan-tri/thong-bao (GET danh sách + POST soạn)
/api/admin/thong-bao/preview             → nút "Xem trước người nhận"
/api/admin/thong-bao/*/gui               → nút "Gửi" trên dòng nháp
/api/admin/thong-bao/*/huy               → nút "Huỷ nháp"
```

`node scripts/ban_do.mjs --kiem` → *0 lời gọi không khớp · 0 tuyến không ai gọi chưa có lý do*.
`CHO_MAN` nay là `{}` — và chú thích trong `ban_do.mjs` ghi lại cả bảy dòng đã rời khỏi nó
trong ngày, để danh sách ấy không lặng lẽ thành một ngoại lệ vĩnh viễn.

---

## 4 · Một thay đổi BACKEND, và test ĐỎ trước

Màn của học vụ cần biết "có những lớp nào, những môn nào". Không có cửa nào trả cái đó cho
`IsAdminOrAcademic` kèm nhãn tiếng Việt của môn, nên `GET /api/admin/thong-bao` nay trả thêm
khoá **`chon`**:

```python
# notifications/thong_bao.py
def danh_muc():   # lớp chưa huỷ (kèm sĩ số, đếm CÙNG luật với người nhận) + BA_MON kèm courses.title
```

Ba phép kiểm viết TRƯỚC, chạy trên mã cũ:

```
FAILED test_get_tra_ve_danh_muc_lop_va_mon_cho_man_soan   (KeyError: 'chon')
FAILED test_danh_muc_lop_khong_gom_lop_da_huy             (KeyError: 'chon')
PASSED test_giang_vien_khong_doc_duoc_danh_muc_ca_trung_tam   ← hàng rào 403 đã đúng sẵn
```

Phép kiểm thứ ba xanh ngay từ đầu, và tôi GIỮ nó: nó khẳng định danh mục cả-trung-tâm nằm
sau `IsAdminOrAcademic`, tức nếu mai ai nới cửa ấy thì có một cái tên cụ thể đỏ lên (RULES
§19). Sau khi vá: **23 passed**.

Vì sao không gõ ba môn vào React: bảng ấy sống ở `courses.truy_cap.BA_MON`, nhãn sống ở
`courses.title`. Chép sang màn là dựng nguồn sự thật thứ hai (RULES §7), và nó sẽ trôi ngay
lần TopHSA mở môn thứ tư.

---

## 5 · Ba lỗi tìm được trong mã của lead

### 5.1 · `scripts/nap_lai_be.ps1:33` — nhánh cứu hộ cho worktree KHÔNG chạy trong worktree

```
powershell -File scripts/nap_lai_be.ps1 -Cong 9600
→ nap_lai_be.ps1 : Không thấy python của backend (thử cả repo chính)
```

`Join-Path` của PowerShell 5.1 **không** bỏ qua phần con khi phần con là đường tuyệt đối:

```
Join-Path 'D:\pe_hsa_wt\e2' 'D:/pe_hsa/.git'  →  D:\pe_hsa_wt\e2\D:/pe_hsa/.git
```

Và `git rev-parse --git-common-dir` trong worktree trả về **đường tuyệt đối** (đo hôm nay:
`D:/pe_hsa/.git`). Nên `Resolve-Path` về `$null`, `$py` không đổi, script chết — ở **chính
tình huống nhánh ấy sinh ra để cứu**. Chú thích ngay trên nó ghi *"Thiếu bước này thì script
chạy ở gốc mà đổ ở mọi worktree — tức đổ đúng chỗ agent cần nó nhất"*; bản vá có chú thích
đúng nhưng mã vẫn đổ. Đã sửa (tự kiểm `IsPathRooted` trước khi ghép) và chạy lại được: nạp
lại backend 9600 thành công, API mới lên ngay.

**Giá của nó**: đây đúng là cái bẫy "`--noreload` không nạp mã mới" mà lead mất ba lượt đo
vì nó; lệnh viết ra để chặn bẫy ấy lại hỏng ở worktree agent, tức ở người cần nó nhất.

### 5.2 · `scripts/do_axe.mjs:88` — bộ đo a11y vẫn tự gọi `chromium.launch()`

`phien_do.mjs` (26/09, chính lead viết) ghi luật: *"bộ đo KHÔNG được tự gọi
`chromium.launch()`. Gọi `chay()`."* — vì tám trên chín bộ đo mở Chromium mà không có
`finally`, và máy anh Sơn đứng vì 11 Chromium mồ côi giữ 788 MB. `do_axe.mjs` **chưa
chuyển**: nó `const b = await chromium.launch()` ở thân tệp. Một lượt chạy trên máy tôi
hôm nay vượt 10 phút chưa xong — đúng khoảng thời gian người ta hay Ctrl-C, và Ctrl-C là
một trong bốn đường mà `finally` KHÔNG chạy.

**Chưa sửa** phần `chromium.launch()` (nằm ngoài việc này, và đổi một bộ đo đang là cổng
RULES §4 thì phải đo lại cả bộ) — ghi ở đây để lead quyết. Tôi CÓ thêm cờ `--chi <chuỗi>`
để đo được đúng màn vừa dựng mà không phải chạy cả 60 lượt; lượt đầy đủ vẫn là mặc định,
cờ không đổi cổng.

### 5.3 · `frontend/src/lib/thongBao.ts` + `DanhSachThongBao.tsx` — không lỗi, một ghi nhận

Đọc kỹ cả trang `/thong-bao` lead dựng hôm nay: **không tìm được lỗi**. Ba chỗ tôi soi kỹ
nhất đều đúng — `khiNao()` tự ghép ngày tháng thay vì `toLocaleDateString('vi-VN')` (tránh
lệch máy chủ/trình duyệt), `doiLoc` dọn danh sách TRƯỚC khi gọi, `doiDaDoc` chờ máy chủ rồi
mới đổi màn. Nói ra vì §15: không tìm thấy lỗi là một kết quả đo, không phải một lời khen.

Một ghi nhận nhỏ về `useDaGan` ở màn của tôi thì có, và nó làm **cái thước** của tôi sai chứ
không phải mã: bản đầu bộ đo dò `useDaGan` trên nút "Lưu nháp" và báo HỎNG — nút ấy còn khoá
vì một lý do THỨ HAI (chưa nhập tiêu đề), nên nó không tách được "React chưa gắn" với "biểu
mẫu chưa đủ". Đã đổi sang dò trên ô tick môn (chỉ `daGan` khoá nó). 23/24 → 24/24.

---

## 6 · Cái CÒN THIẾU — nói thẳng

1. **Trợ giảng vẫn không nhắn được RIÊNG một em.** Dòng 20 nói "nhắn / nhắc": nửa **nhắc**
   nay bấm được và đo được; nửa **nhắn** thì chưa — hộp Yêu cầu (E3) là kênh do HỌC VIÊN mở
   trước, còn thông báo lớp thì cả lớp cùng nhận. Đây là chỗ anh Sơn chưa quyết, không phải
   chỗ tôi bỏ sót. Dòng 20 vì vậy vẫn là **MỘT PHẦN**, tôi không tick lên CÓ.
2. **Đối tượng "chọn tay người nhận" (`userIds` + `groupName`) chưa có ô trên màn.** Backend
   nhận, `tests_thong_bao.py::test_doi_tuong_theo_mon_va_nhom_chon_tay` canh, nhưng màn của
   học vụ mới có Lớp và Môn. Nó cần một ô tìm–chọn tài khoản, đủ lớn để là một việc riêng.
3. **Zalo ZNS**: ô "Gửi kèm Zalo" chưa dựng. OA chưa xác thực nên máy chủ trả 400 cho mọi
   lượt bật; màn chỉ HIỆN LẠI lý do máy chủ trả (`zalo.lyDo`), không bày một ô bấm vào là
   lỗi. Dựng ô ấy khi có OA.
4. **Chưa có spec nghiệm thu** `frontend/e2e/nghiem-thu/dong-20.spec.ts`. Bộ đo của tôi là
   một kịch bản Node chạy tay, không phải spec Playwright trong cổng e2e.
5. **`daGuiThu` / `daDoc` trên dòng danh sách chỉ đúng lúc TẢI TRANG.** Dòng vừa gửi trong
   phiên hiện `0 thư đã gửi` / `0 em đã đọc` vì màn tự dựng dòng ấy thay vì gọi lại danh
   sách — con số thật hiện ở lượt tải sau. Cố ý (một lượt gọi nữa trên gói miễn phí là vài
   giây người gửi ngồi nhìn màn chưa đổi), nhưng nó là một chỗ con số trên màn trẻ hơn sự
   thật trong vài phút.
6. **Axe: 0 vi phạm trên hai màn mới, nhưng tôi CHƯA chạy lượt đầy đủ.** Con số 0 ở §1 là
   của `--chi "thông báo"` — đúng hai màn tôi dựng. Lượt đầy đủ (~60 lần tải trang) tôi
   không chạy được: lượt thử đầu vượt 10 phút và góp phần làm máy anh Sơn hết RAM, nên tôi
   dừng. Nếu hai tab mới làm hỏng bố cục thanh ở một màn KHÁC thì con số của tôi không
   thấy được (RULES §16: đo lại phần KHÔNG sửa nằm cạnh phần vừa sửa). Lead chạy lượt đầy
   đủ ở lần gộp.

---

## 7 · Tệp đã chạm

```
backend/notifications/thong_bao.py            + danh_muc()
backend/notifications/views_thong_bao.py      + khoá `chon` trong GET
backend/notifications/tests_thong_bao.py      + 3 phép kiểm (2 đỏ trước)
frontend/src/lib/thongBaoSoan.ts              MỚI — hình dạng zod/mini + câu xem trước
frontend/src/app/(standalone)/giang-day/thong-bao/[classId]/{page,SoanThongBaoLop}.tsx   MỚI
frontend/src/app/(standalone)/quan-tri/thong-bao/{layout,page,ThongBaoTrungTam}.tsx      MỚI
frontend/src/app/(standalone)/giang-day/KhungGiangDay.tsx   + tab "Thông báo lớp"
frontend/src/app/(standalone)/quan-tri/vai.ts               + tab "Thông báo"
frontend/e2e/unit/cong-quan-tri.test.mjs                    + dòng canh AdminThongBaoView
scripts/do_thong_bao_lop.mjs                  MỚI — bộ đo, gọi chay()
scripts/do_axe.mjs                            + hai màn mới, + cờ `--chi <chuỗi>`
scripts/ban_do.mjs                            CHO_MAN → {}
scripts/nap_lai_be.ps1                        vá Join-Path (5.1)
scripts/so_mien.json + docs/CAU_TRUC_*.md     miền `thong_bao` nhận ba glob mới
docs/NGHIEM_THU_TOPHSA.md                     dòng 20 + dòng 27
```

---

## 8 · RAM — vì sao lượt đầu bị ngắt, và cái gì đã đổi

Lượt làm đầu tiên bị dừng giữa chừng: máy anh Sơn còn **1,5 GB trống / 15,9 GB**, và
`next dev` cổng 3600 của tôi MỘT MÌNH chiếm **3.047 MB**. Anh Sơn: *"Kiểm soát công việc
liên tục đi, toàn để bị OOM như này"*.

Đo lại sau khi đặt trần heap, cùng bộ đo, cùng hai màn:

| | `next dev` 3600 |
|---|---|
| không trần | **3.047 MB** |
| `NODE_OPTIONS=--max-old-space-size=1536` | **813 MB** |

Tức trần heap cắt **~73%** mà không hỏng lượt đo nào (24/24 vẫn ĐẠT, axe vẫn chạy). Lượt
làm thứ hai: dựng server → đo → `don_may.ps1 -Don` + dừng hẳn 9600/3600 ngay trong cùng
phiên; kết thúc còn **5 GB trống**, mồ côi **sạch**, và bản dev chính (9000 / 3100) không
bị đụng tới.

Hai điều đáng ghi lại:

- **`don_may.ps1 -Don` KHÔNG giết server đang giữ cổng** — nó chỉ dọn tiến trình MỒ CÔI.
  Lượt đầu tôi chạy nó rồi tưởng đã dọn xong, trong khi `next dev` 3 GB vẫn sống nguyên.
  Đúng như tên gọi của nó, nhưng "đo xong thì `don_may.ps1 -Don`" trong CLAUDE.md dễ đọc
  thành "lệnh này dọn hết".
- **Bộ đo nói đúng khi không đo được.** Lượt chạy lại đầu tiên gặp thẻ hết hạn và in
  `KHÔNG ĐO ĐƯỢC — thẻ trợ giảng hết hạn`, thoát 2, thay vì đổ 24 bước HỎNG lên một màn
  hoàn toàn đúng. Thẻ sống 30 phút; một lượt làm dài thì phải cấp lại trước khi đo.
