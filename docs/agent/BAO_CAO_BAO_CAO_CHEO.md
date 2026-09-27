# BC — BÁO CÁO CHÉO MÔN × LỚP: đóng ô cuối còn "MỘT PHẦN" của dòng 6

27/09/2026. Người làm: agent BC (worktree `D:/pe_hsa_wt/bc`, nhánh `agent/bc`, nền `198dc81`).

Việc: ô `Kết quả theo môn, hoàn thành bài tập (tổng)` của bảng nghiệm thu dòng 6 ghi
**MỘT PHẦN — "theo khoá / từng bài; chưa báo cáo chéo"**. Khách hỏi được *"lớp này em nào
chưa nộp bài"* và *"khoá này điểm thế nào"*, nhưng KHÔNG hỏi được câu ở giữa:
**"môn nào đang tụt so với môn khác, và lớp nào trong môn ấy tụt"**.

**Agent này KHÔNG đo màn** (máy anh Sơn còn 2,3–2,8 GB trống; một `next dev` đã từng giữ
3 GB và làm chết phiên). Phần cần lead tự đo ở **§7**.

---

## V0 · Đo đã có gì trước khi viết một dòng mã

Đọc `teaching/overview.py` (750 dòng), `teaching/cham_cong.py`, `teaching/exports.py`
(851 dòng), `common/bangtinh.py`, `teaching/assignments.py`, `teaching/reports.py`, và màn
`quan-tri/tong-quan/` (550 + 454 + 106 dòng).

| Thứ cần | Đã có ở đâu | Dùng lại thế nào |
|---|---|---|
| Sĩ số "đang học" đúng luật | `overview.py:176-197` (câu 1) — `left_at IS NULL` + `vocab.chi_hoc_vien` + mẹo `LEFT JOIN LATERAL` để lớp chỉ có thành viên KHÔNG phải học viên vẫn còn dòng | Chép **nguyên kiểu câu**, kèm lý do ở chú thích `bao_cao_cheo.py:245-250` |
| Phải nộp / đã nộp / đã chấm | `assignments.py:429-450` — nhưng **theo TỪNG BÀI**, không có bản gộp theo lớp | Viết câu gộp mới, **cùng phạm vi**: `left_at IS NULL` + `nhan_bai.giao_cho` |
| Điểm chuẩn hoá theo thang | `overview.py:283` làm đúng cho **đề thi thử** (`e.score * 100.0 / NULLIF(e.max_score,0)`) — không có bản nào cho `assignments.max_score` | Cùng công thức, cho `submissions.score / assignments.max_score` |
| Tỉ lệ chuyên cần | `attendance.ti_le` — nơi **DUY NHẤT** định nghĩa | GỌI nó, không tự chia |
| Phần trăm / `None` khi không có mẫu số | `overview._mot_phan_tram` | **Import lại chính hàm đó**, không sao chép (lý do ở `bao_cao_cheo.py:84-88`) |
| Tiến độ chương trình | `chuong_trinh.dich_vu.tien_do_lop` — cửa duy nhất của miền (luật S4) | GỌI nó, không đọc bảng sổ đầu bài |
| Đọc ngày `tu`/`den` | `overview._doc_ngay` | Import lại |
| Ghi `.xlsx` | `exports.xuat_bang` → `common.bangtinh.ghi_xlsx` (ô chữ không bao giờ thành công thức) | Gọi `xuat_bang` |
| `?dinh_dang=` | `exports.doc_dinh_dang` (lạ thì 400, không lặng lẽ rơi về CSV) | Gọi nó |

**KHÔNG viết lại gì trong danh sách trên.** Thứ duy nhất phải viết mới là **cách gộp**:
cả repo chưa có chỗ nào gộp theo `classes.course_id`.

Đo thêm được hai chỗ **thiếu** mà không ai có bản gộp:
`reports.py` (756 dòng) **không có** một câu nào về `submissions`; `viec_hom_nay._chua_cham`
chỉ đếm bài **chờ chấm** theo từng bài.

---

## V1 · Cửa API

`GET /api/admin/bao-cao-cheo?course_id=&term_id=&tu=&den=[&dinh_dang=xlsx]`
→ `backend/teaching/bao_cao_cheo.py` · tuyến ở `backend/teaching/urls.py:185-187`.

**Hình dạng**: `mon[]` — mỗi môn một nhóm, có `tong` (dòng tổng của môn), `lopTong`, và
`lop[]` (một dòng một lớp) — cộng `tong` (dòng tổng toàn trung tâm), `monOptions`,
`dotOptions`, `incomplete`, `generatedAt`.

**Cột mỗi dòng** (lớp, môn, trung tâm dùng ĐÚNG một bộ — `_o_rong` / `_cong` / `_chot`):
`dangHoc` · `phaiNop` / `daNop` / `tiLeNop` · `daCham` / `tiLeCham` · `soDiem` / `diemTB`
(chuẩn hoá thang) · `coMat` / `luotDiemDanh` / `tiLeChuyenCan` · `tienDoPct` /
`lopCoKhung` / `lopCham`.

### Bốn quyết định phải nói rõ

**1 · Chuẩn hoá thang, và cộng từ SỐ THÔ.** `score * 100 / max_score` cho **mỗi lượt**
trước khi cộng (`bao_cao_cheo.py:302`). Dòng tổng cộng chính bộ đếm thô ấy
(`_cong`, `bao_cao_cheo.py:160-172`), **không** lấy trung bình các phần trăm cấp lớp —
trung bình của trung bình cho mỗi lớp một phiếu bất kể lớp 3 em hay 30.
Cảnh cụ thể: bài thang 10 được 10 và bài thang 100 được 50 → **75 %**, cộng thô ra **30**.
Con số sai ấy còn chạy ĐÚNG HƯỚNG (môn hay dùng thang 100 trông càng tệ), nên nó không
trông như lỗi mà trông như một phát hiện.

**2 · Mẫu số của "đã chấm" là ĐÃ NỘP, không phải PHẢI NỘP** (`_chot`, `bao_cao_cheo.py:180`).
Chỉ chấm được thứ đã nộp; lấy `phaiNop` làm mẫu thì lớp nộp ít mà giảng viên chấm hết vẫn
hiện "chấm 50 %" và người đọc đi nhắc đúng người đang làm tốt nhất.

**3 · Bài NHÁP và bài KIỂM TRA.** `status='draft'` không vào mẫu số phải nộp (học viên chưa
thấy bài). Bài **kiểm tra trên lớp** (`kind='kiem_tra'`, §62f) **không nộp được**, nên nó
không vào tỉ lệ nộp — nhưng **ĐIỂM của nó vẫn vào điểm trung bình**, vì đó chính là "kết
quả theo môn" khách hỏi. Hai hằng số: `TRANG_THAI_BAI_DA_GIAO`, `LOAI_BAI_NOP`.

**4 · Quyền: quản trị viên + học vụ** (`IsAdminOrAcademic`), theo trang "Chấm công" và
"Toàn trung tâm" — **KHÔNG** theo `exports.py` (`IsAdminRole`). Quyết định 01/09/2026 ghi
học vụ "xem MỌI lớp, báo cáo trung tâm"; đây là số gộp, không có liên lạc của em nào.
Giảng viên / trợ giảng / học viên **403**: bảng này đặt mọi lớp của mọi người cạnh nhau,
tức nó là một bảng xếp hạng đồng nghiệp. Lý lẽ đủ ở docstring khối "AI XEM ĐƯỢC".

### Ba cái bẫy đã bịt

- **Chia cho 0 → `None` (màn vẽ `—`), không 0 %.** Lớp chưa giao bài nào thì `tiLeNop` là
  `None`; lớp đã giao mà không em nào nộp thì là `0`. Hai test riêng cho hai chiều
  (`test_lop_chua_giao_bai_thi_ti_le_la_gach_khong_phai_0`,
  `test_khong_em_nao_nop_thi_ti_le_la_0_khong_phai_gach`).
- **Lớp không có dòng nào vẫn có mặt.** Lớp chưa giao bài, chưa có buổi, **và cả lớp chưa
  xếp em nào** đều còn dòng với 0 / `—` (mẹo `LEFT JOIN LATERAL`, hai test riêng). Lớp biến
  mất khỏi báo cáo trông y như lớp đã đóng.
- **Học viên đã rời lớp không vào tử số lẫn mẫu số** — cả câu bài tập lẫn câu điểm. Thiếu
  vế ấy thì trong cảnh thử `phaiNop` phồng 4 → 6 và `diemTB` tụt 75 → 50.

### Quy ước bộ lọc — KHÔNG phát minh cái thứ hai

`tu`/`den` và `term_id` **giống hệt** `overview.py`: cả ngày `den` được tính, mặc định
`den` = hôm nay và `tu` = ngày 1 của tháng ấy, ngày sai dạng trả 400 kèm câu tiếng Việt,
`tu > den` trả 400. Kỳ xem lọc **bài** (mốc `COALESCE(held_on, due_at, created_at)`) và
**buổi học** (`starts_at`, cùng vế `overview._diem_danh_giang_vien`) — **không** lọc sĩ số:
"lớp này hiện có bao nhiêu em" là hiện trạng, không phải một khoảng thời gian.

**Số câu truy vấn: 7, không phụ thuộc số lớp** (4 câu gộp theo lớp + `tien_do_lop` + 2 câu
danh mục). Gọi báo cáo lớp cho từng lớp sẽ là 6 câu × ~400 lớp cho một màn hình.

**Cắt dòng**: mỗi môn tối đa `TRAN_LOP_MOI_MON = 50` lớp, **lớp tụt nhất lên đầu**
(`_khoa_xep_lop`); mọi phép đếm và mọi dòng tổng vẫn tính trên **toàn bộ** lớp, và bản
`.xlsx` **không** bị cắt. Thứ tự các **môn** cũng là câu trả lời: môn có tỉ lệ nộp thấp
nhất lên đầu (`_khoa_xep_mon`).

**Không một dòng DDL.** Báo cáo chỉ đọc; mọi cột cần đã có.

---

## V2 · Bộ kiểm — ĐỎ TRƯỚC, rồi mới làm xanh

`backend/teaching/tests_bao_cao_cheo.py` — **19 test**, viết **trước** khi có mã.

| Lượt | Ngày | Kết quả |
|---|---|---|
| ĐỎ trước (chưa có `bao_cao_cheo.py`) | 27/09/2026 | **19 thất bại** / 19 — `ModuleNotFoundError` cho mọi test, 286 s |
| Sau khi có mã, lượt 1 | 27/09/2026 | 16 thất bại / 3 đạt, 307 s — **bắt được một lỗi thật**: `_cong` đọc `_tongDiemChuan` trên dòng đã qua `_chot` (hàm này lọc mọi khoá `_`) → `KeyError` → HTTP 500. Sửa: `_cong` nhận bộ đếm **THÔ** |
| XANH | 27/09/2026 | *(xem §8 — số chốt)* |

Ba test đạt ngay từ lượt 1 là ba test **không đi qua đường tính số**: hàng rào 403, ngày
sai dạng, `dinh_dang` lạ. Tức hàng rào quyền và lớp kiểm tham số đúng ngay, còn toàn bộ
đường tính số thì sai — đúng thứ bộ kiểm tồn tại để nói.

Đi qua **VIEW THẬT** (`APIRequestFactory` + `force_authenticate`), **không đọc thẳng bảng
sau một lời gọi API** — tiền lệ 26/09: đọc thẳng dùng kết nối khác nên test xanh khi chạy
riêng, đỏ khi chạy cả bộ. CSDL cuộn lại sau mỗi test (`conftest.py`); cảnh thử ở tháng
**05/2032**, không dữ liệu thật nào nằm đó; mọi khẳng định dò theo `classId` / mã môn sinh
bằng `uuid`, nên dữ liệu có sẵn trên CSDL dev không làm test lung lay.

Phủ đủ bảy chỗ brief đòi, cộng bốn chỗ tự thấy: bài nháp · bài kiểm tra · lớp chưa xếp em
nào · bảng tính đi theo bộ lọc của màn.

---

## V3 · Đột biến

`scripts/dot_bien/bao_cao_cheo.json` — **14 đột biến**, nhắm vào đúng chỗ dễ sai:
chuẩn hoá thang · mẫu số của cả hai tỉ lệ · `left_at` (cả hai câu) · hàng rào quyền ·
ba bộ lọc (môn, đợt, ngày) · bài nháp · bài kiểm tra · chuyên cần ngoài kỳ · `LATERAL` →
`WHERE` · bảng tính bỏ bộ lọc.

```
python scripts/dot_bien.py backend/teaching/bao_cao_cheo.py \
    --test teaching/tests_bao_cao_cheo.py \
    --loat scripts/dot_bien/bao_cao_cheo.json
```

*(kết quả ở §8)*

---

## V4 · Tải bảng tính

`?dinh_dang=xlsx` → `exports.xuat_bang` → `common.bangtinh.ghi_xlsx`. **Cùng bộ lọc với
màn** (một test ghim: lọc đợt 1 thì lớp của đợt 2 **không** được có trong tệp), và **không
bị cắt 50 dòng** — tệp mang đi họp thì phải đủ.

17 cột, cùng thứ tự với màn. Hai chi tiết:
- Ô tỉ lệ là **số nguyên phần trăm** (75), tên cột mang sẵn `(%)`. Không ghi phân số 0,75:
  `ghi_xlsx` cố ý không nhận định dạng cho từng ô, nên 0,75 sẽ hiện đúng là "0.75" và người
  mở tệp đọc thành điểm 0,75. Số nguyên thì vẫn cộng / lọc / vẽ đồ thị được trong Excel.
- Tỉ lệ không tính được ghi `—`, **cùng ký tự với màn** (`GACH`) — không để trống (đọc
  thành "quên điền") và không ghi 0 (đọc thành "tệ hết mức"). Cột tử số và mẫu số bên cạnh
  vẫn là SỐ nên ai muốn tính lại vẫn tính được.
- Dòng tổng của môn nằm **SAU** các dòng lớp của môn ấy: người mở tệp kéo chọn một vùng để
  tính lại, và dòng tổng lẫn giữa các dòng lớp là cộng hai lần.

---

## V5 · Màn

**Trang RIÊNG** `/quan-tri/bao-cao-mon` (`frontend/src/app/(standalone)/quan-tri/bao-cao-mon/`
— `page.tsx` + `layout.tsx`), tab "Kết quả theo môn" ngay sau "Toàn trung tâm"
(`quan-tri/vai.ts:52-57`, biểu tượng `target`).

**Vì sao không phải một khu của "Toàn trung tâm"** — hai lý do đo được:
1. Trang ấy đã có **8 khối / 550 dòng mã**, khối cuối ("Từng lớp") đã phải cắt còn 50 dòng.
   Thêm một bảng chéo **có nhóm** (mỗi môn một bảng con) là đẩy nó xuống dưới nếp gấp thứ
   ba — đúng lỗi "màn đầu rối" TopHSA đã góp ý 24/09.
2. **Bộ lọc khác nhau**: trang kia lọc đợt + kỳ xem; trang này còn lọc **MÔN**. Hai biểu
   mẫu GET trên cùng một URL ăn tham số của nhau — `KyXem` đã phải mang `term_id` trong ô
   ẩn đúng vì lý do đó, thêm cái thứ ba là thêm hai ô ẩn nữa cho mỗi form.

Bố cục: **bảng so sánh các MÔN** (một dòng một môn + dòng "Toàn trung tâm"), rồi **một thẻ
cho mỗi môn** với bảng từng lớp, lớp tụt nhất lên đầu.

### Năm ràng buộc brief nêu

| Ràng buộc | Đã làm |
|---|---|
| Chữ tiếng Việt, không mã kỹ thuật | Không `hsa_*`, không tên cột. `classes.status` dịch qua `NHAN_TRANG_THAI_LOP` ở máy chủ. Cổng `e2e/unit/chu-nguoi-dung.test.mjs` + `thuat-ngu.test.mjs` **ĐẠT** (bắt hai lỗi thật của tôi: một `hint` 100 ký tự và chữ "hợp phần" — xem §6) |
| Không hardcode px | Chỉ `min-h-11`, `px-3`, `py-3.5`, `flex-[1_1_14rem]`, token màu có sẵn (`text-ink-3`, `border-line-input`, `bg-brand-fill`…). Không một giá trị `px` nào |
| Ô lọc khoá tới khi React gắn xong | **Không cần `useDaGan()`** — và đó là chủ ý, xem ngay dưới |
| Danh mục lấy từ máy chủ | `monOptions` / `dotOptions` trong cùng phản hồi; màn không gõ lại tên môn hay tên đợt nào (RULES §7) |
| `—` hiện là `—`, không `0%` | Hàm `pct()` ở màn; máy chủ đã trả `None` chứ không 0 |

**Vì sao KHÔNG `useDaGan()`.** Trang là **server component, không một dòng JS phía trình
duyệt**: bộ lọc là `<form method="get">` và liên kết thường, cùng khuôn với "Chấm công" và
bộ lọc Lớp học. Ô lọc dùng được **NGAY khi HTML về**, nên **không tồn tại** khoảng thời gian
"React chưa gắn" để bấm vào hư không. `useDaGan()` là hàng rào cho ô lọc **có JS** (nó khoá
ô tới khi React gắn xong); gắn nó vào một trang không có JS sẽ **tạo ra** đúng lỗi nó đi
chữa — ô bị `disabled` cho tới khi có một React chẳng bao giờ chạy ở đó. Cùng lý do,
trạng thái bộ lọc nằm trên URL: gửi link *"môn Định lượng tháng 9"* cho đồng nghiệp là họ
thấy đúng thứ mình thấy.

**Tô màu KHÔNG dùng ngưỡng nghĩ ra ở màn.** Không có chuẩn ngành nào cho "tỉ lệ nộp bài bao
nhiêu là khoẻ" — khác hẳn tỉ lệ giữ chân ở Toàn trung tâm (ngưỡng ấy **có tra cứu** và do
**máy chủ** cấp). Viết cứng "dưới 80 % là đỏ" ở đây sẽ là một giả định vô căn cứ nằm trong
giao diện, và giả định trong giao diện thì không ai bàn lại được. Thứ đo được là: **môn này
so với trung bình toàn trung tâm** — chip cam khi thấp hơn, xanh khi bằng hoặc hơn, xám khi
chưa đo được. `chiTiet` của thẻ nói đúng nghĩa ấy.

---

## 6 · Cổng kiểm đã chạy

| Cổng | Kết quả | Ghi chú |
|---|---|---|
| `ruff check` (tệp mới) | ĐẠT | hai lỗi `I001` (thứ tự import) đã sửa |
| `manage.py check` | ĐẠT — 0 vấn đề | |
| `tsc --noEmit` (cả frontend) | ĐẠT — 0 lỗi | phải nối `node_modules` của bản chính vào worktree (junction) vì worktree không có |
| `eslint --max-warnings 0` (tệp mới) | ĐẠT | |
| `node scripts/ban_do.mjs --kiem` | ĐẠT — 0 gãy | 576 nút / 1976 cạnh; tuyến mới + màn mới đã vào bản đồ |
| `scripts/tang_vai.py --kiem` | ĐẠT — 0 lệch chưa giải thích | tab mới khớp `IsAdminOrAcademic` |
| `e2e/unit/*.test.mjs` (từng tệp, như pre-push) | ĐẠT sau khi sửa | **bắt hai lỗi thật của tôi**: `hint` 100 ký tự (trần 90) và chữ "hợp phần" (phải là "môn học") trong câu EmptyState |
| `scripts/quet_bi_mat.py` | ĐẠT | |
| `pytest teaching/tests_bao_cao_cheo.py` | *(§8)* | |
| `pytest teaching/` (hồi quy) | *(§8)* | |
| `scripts/cau_truc.py` | *(§8)* | sinh lại `docs/CAU_TRUC_*` sau khi thêm tệp |

Sổ miền: tệp mới vào miền **`bao_cao`** (`scripts/so_mien.json`) — đúng miền cho việc CHỈ
ĐỌC, không sở hữu bảng. **Không một lệnh INSERT / UPDATE / DELETE nào** trong tệp mới, nên
luật S4 không bị đụng; tiến độ chương trình đi qua **cửa dịch vụ** `tien_do_lop` chứ không
đọc lén bảng sổ đầu bài của miền chương trình.

---

## 7 · Lead phải TỰ ĐO (tôi không đo màn)

Máy anh Sơn còn 2,3 GB trống khi tôi làm việc này, nên tôi **không** dựng `next dev` và
**không** dựng cả Django 9400 (bộ kiểm gọi view trực tiếp, không cần máy chủ HTTP).
Sáu bước cần mở trên màn thật, bằng tài khoản **quản lý học vụ** và **quản trị viên**:

1. `/quan-tri/bao-cao-mon` mở được, tab "Kết quả theo môn" hiện đúng chỗ (sau "Toàn trung
   tâm"), biểu tượng không trùng tab bên cạnh **ở khổ hẹp** (dưới 70rem `shell.css` ẩn nhãn
   chữ).
2. Bảng so sánh môn có dòng cho **từng môn** + dòng "Toàn trung tâm"; số của dòng tổng
   khớp với tổng các dòng môn.
3. Đổi ô **Môn** → bảng đổi; đổi **Đợt học** → bảng đổi; đổi **Từ/Đến ngày** → cột chuyên
   cần và cột nộp bài đổi theo. Link "Bỏ lọc" về trạng thái đủ.
4. Lớp nào chưa giao bài hiện **`—`**, không `0%`. Lớp chưa xếp em nào vẫn có dòng.
5. Bấm **Tải Excel** → tệp mở được bằng Excel, tên cột tiếng Việt, dòng "TỔNG MÔN" nằm sau
   các lớp của môn, **và số dòng khớp bộ lọc đang đặt trên màn**.
6. Đăng nhập bằng **giảng viên** rồi mở `/quan-tri/bao-cao-mon` → phải ra trang "Không đủ
   quyền" (cổng `layout.tsx`), và `GET /api/admin/bao-cao-cheo` phải **403**.

Thêm một bước ở khổ **điện thoại**: bảng 8 cột ở dạng thẻ (`Td label`) — kiểm không có
thanh cuộn ngang ở trang, và mỗi ô còn đọc được tên cột của nó.

---

## 8 · Số chốt

*(mục này điền sau khi hai lượt chạy dài xong — xem câu trả lời gửi lead)*

---

## 9 · Còn sót / cần anh Sơn quyết

1. **Kỳ xem mặc định là THÁNG NÀY.** Cùng quy ước `overview.py` (brief yêu cầu không phát
   minh quy ước thứ hai), nhưng hệ quả: mở trang ngày 1 hằng tháng thì gần như mọi ô là
   `—`. Màn in rõ "Từ … đến …" nên không ai đọc sai, nhưng nếu anh muốn mặc định là **đợt
   học hiện hành** thay vì tháng thì đó là một quyết định sản phẩm, không phải một bản vá.
2. **Tiến độ của một MÔN là trung bình theo LỚP** (mỗi lớp một phiếu), không cân theo sĩ số
   — vì "chương trình có bị chậm không" là chuyện của lớp, không của đầu người. Nếu anh
   muốn cân theo sĩ số thì đổi một dòng (`_cong`).
3. **Môn chưa có lớp nào KHÔNG hiện.** Nhóm môn lấy từ các lớp khớp bộ lọc. Một môn vừa mở
   mà chưa xếp lớp sẽ không có dòng — đúng cho câu "môn nào đang tụt", nhưng nếu khách muốn
   thấy "môn này chưa có lớp" thì phải đổi.
4. **Mốc của bài không có hạn nộp là `created_at`**, mà cột ấy do `DEFAULT now()` của CSDL
   ghi (**giờ UTC, lệch giờ VN 7 tiếng**). Bài tạo lúc 0–7 giờ sáng ngày 1 có thể rơi sang
   tháng trước. Chỉ ảnh hưởng bài **không đặt hạn và không phải bài kiểm tra**; vá được
   bằng cách cộng 7 giờ, nhưng đó là một quy ước mới nên tôi không tự đặt.
5. **Nhóm "lớp không gắn môn"** hiện với tên `MON_KHONG_GAN`. Nó gồm lớp ôn cả ba môn HSA —
   thường là lớp đông nhất của một trung tâm luyện thi — nên nó nằm ngang hàng các môn khác
   chứ không bị gom vào cuối. Nếu TopHSA muốn nó có tên khác thì đổi một hằng số.
6. **Dòng 6 bảng nghiệm thu** chỉ được đổi từ "MỘT PHẦN" sang "CÓ" **sau khi lead đo xong
   §7** — bảng ấy là dòng khách đọc, không được tick bằng suy luận (RULES §1).
