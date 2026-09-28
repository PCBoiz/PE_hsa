# Báo cáo E3 — hộp Yêu cầu (§65), dòng 11 bảng phân rã TopHSA

Nhánh `agent/e3`, worktree `D:\pe_hsa_wt\e3`. Ngày đo: **26/09/2026**.
Cổng riêng của lượt đo: Django 9600, Next 3700 (Neon dev).

Dòng 11 — *Giáo vụ · Hỗ trợ lớp học*: "Tiếp nhận yêu cầu hỗ trợ · Phân loại yêu
cầu: học tập / lịch học / kỹ thuật / tài khoản · Phân công người xử lý · Theo dõi
trạng thái xử lý · Ghi nhận kết quả xử lý · Chuyển yêu cầu cho GV/TG · Lưu lịch
sử hỗ trợ".

---

## 1 · Từng gạch đầu dòng: chạy được chưa

Cột "đo trên màn thật" là bước tương ứng trong `scripts/do_yeu_cau.mjs` — bộ đo
mở trình duyệt đã đăng nhập và BẤM, không gọi API tay.

| # | Gạch đầu dòng | Chạy được | Mã (tệp:dòng) | Đo trên màn thật |
|---|---|---|---|---|
| ① | Tiếp nhận yêu cầu hỗ trợ | **CÓ** | `backend/yeu_cau/dich_vu.py:411` (`tao`) · `backend/yeu_cau/views.py:78` (học viên) · `:391` (phụ huynh qua link) | `dong11-1` ✓ — học viên gửi, hộp học vụ nhận |
| ② | Phân loại: học tập / lịch học / kỹ thuật / tài khoản | **CÓ** | `backend/yeu_cau/dich_vu.py:605` (`phan_loai`) · `backend/yeu_cau/loai.py:86` (`PHAN_LOAI_DUOC`) · `backend/yeu_cau/views.py:335` | `dong11-2` ✓ — đổi "Hỗ trợ học tập" → "Hỗ trợ kỹ thuật" |
| ③ | Phân công người xử lý | **CÓ** | `backend/yeu_cau/dich_vu.py:571` (`giao`) · `backend/yeu_cau/views.py:299` | `dong11-3` ✓ — giao cho một giảng viên có thật của lớp |
| ④ | Theo dõi trạng thái xử lý | **CÓ** | `backend/yeu_cau/dich_vu.py:543` (`chuyen_trang_thai`) · `backend/yeu_cau/loai.py:55` (bảng chuyển hợp lệ) · `backend/yeu_cau/views.py:235` | `dong11-4` ✓ — chip đổi "Mới" → "Đang xử lý" → "Đã xong" |
| ⑤ | Ghi nhận kết quả xử lý | **CÓ** | `backend/yeu_cau/dich_vu.py:534` (`_dat_trang_thai`, cột `ket_qua`) | `dong11-5` ✓ — ô "Kết quả (người gửi đọc được)", học viên đọc lại thấy |
| ⑥ | Chuyển yêu cầu cho GV/TG | **CÓ** | `backend/yeu_cau/dich_vu.py:595` (`kieu = 'giao' \| 'chuyen_tiep'`) · `backend/yeu_cau/views.py:248`, `:261` (`/nguoi-nhan`) | `dong11-6` ✓ — ô "Giao cho" liệt kê "Ha Thai Son · Giảng viên", "Lê Văn Trợ Giảng · Trợ giảng" |
| ⑦ | Lưu lịch sử hỗ trợ | **CÓ** | `backend/yeu_cau/dich_vu.py:264` (`su_kien_cua`) · bảng `yeu_cau_su_kien` (§65b) · `frontend/src/components/YeuCauDongThoiGian.tsx` | `dong11-7` ✓ — 7 mốc: Gửi yêu cầu → Chuyển sang "Đang xử lý" → Đổi loại → Giao cho → Trả lời → Ghi chú nội bộ → Chuyển sang "Đã xong" |

**Bảy trên bảy chạy được trên màn thật.** Bộ đo: **17/17 bước ĐẠT**
(`node scripts/do_yeu_cau.mjs`, 26/09).

Ba bước ngoài dòng 11 cũng đo luôn, vì chúng là hàng rào của dòng 11:

- `hv-khong-xu-ly` ✓ — học viên KHÔNG thấy thẻ "Xử lý" của nhân sự.
- `hv-an-noi-bo` ✓ — ghi chú nội bộ ẩn với học viên (đọc lại bằng thẻ học viên,
  không suy từ mã).
- `ph-gui` ✓ — phụ huynh gửi được yêu cầu qua link tờ báo cáo, không đăng nhập.

---

## 2 · Lỗi tìm ra và đã vá trong lượt này

### 2.1 · §65 không biết tới BUỔI BÙ (agent soát tìm ra, tôi vá)

`grep -rn thuoc_buoi backend/yeu_cau/` ra **0 dòng** — §65 là chỗ cuối cùng còn
đọc theo từng em mà không qua mệnh đề chung. Buổi bù (V-g, §62e
`session_participants`) chỉ vài em, nhưng:

- ô chọn buổi của hộp Yêu cầu đưa buổi bù cho **cả lớp**;
- POST thẳng `session_id` của một buổi bù mình chưa từng dự vẫn được **201**.

Vá theo đúng nếp §72 (`backend/teaching/ban_ghi.py`), **ba cửa**:

| Cửa | Tệp:dòng |
|---|---|
| Ô chọn buổi của học viên lọc bằng `thuoc_buoi('s.id', '%s')` | `backend/yeu_cau/views.py:101-110` |
| Học viên tự gửi — `_du_buoi(nguoi.id, session_id)`, trả **404** (không lộ buổi bù của bạn khác) | `backend/yeu_cau/dich_vu.py:450-452` |
| Nhân sự gõ hộ em — cùng hàng rào, trả 400 "Em này không dự buổi học đã chọn." | `backend/yeu_cau/dich_vu.py:469-471` |
| Hàm chung `_du_buoi`, gọi thẳng `teaching.nguoi_buoi.thuoc_buoi` | `backend/yeu_cau/dich_vu.py:378` |

Bẫy đã ghi thành chú thích trong mã: chuỗi `thuoc_buoi` sinh ra có `uid` đứng
**trước** `sid`, nên truyền `(uid, session_id)`. Đột biến D5 (đảo thứ tự) có
trong loạt chính vì chỗ này.

### 2.2 · Tờ báo cáo phụ huynh không có tiêu đề cấp một

E3 là nhánh đã đưa `/bc/<chìa>` vào bộ đo axe (commit `cef55e7`), và trang ấy
đỏ: thân tờ bắt đầu ở `h2` (tên em) rồi `h3` từng mục, thanh trên chỉ là một
`span`. axe: `page-has-heading-one`, MODERATE, 2 lượt trang (390 và 1366).
Đổi `span` → `h1` kèm `m-0`, giữ nguyên `text-section` nên không đổi một pixel
nào trên màn: `frontend/src/app/(standalone)/bc/[token]/page.tsx:87`.

### 2.3 · `/nguoi-nhan` lộ email nhân sự chưa đặt tên

`views.py` cũ trả `r['name'] or r['email']`, mà tuyến này **trợ giảng gọi
được** — một giảng viên chưa đặt tên là một email nằm trong ô "Chuyển tiếp…".
Nay chỉ học vụ / quản trị đọc email thay tên, người khác thấy "Giảng viên #id":
`backend/yeu_cau/views.py:285-294`. Cùng ranh giới `dich_vu._ten_em` đã đặt cho
phía học viên.

---

## 3 · Số tôi TỰ ĐO (26/09/2026)

| Phép đo | Lệnh | Kết quả |
|---|---|---|
| Lược đồ, lượt 1 và lượt 2 | `manage.py bootstrap_schema` (×2) | `0/67 mục chạy` cả hai lượt |
| Đối chiếu lược đồ | `manage.py kiem_luoc_do` | **71/71 mục đã tới nơi**, 0 dòng hỏng |
| Phép kiểm miền `yeu_cau` | `pytest yeu_cau/tests_yeu_cau.py -q` | **39 xanh** / 502,86 s (trước lượt này: 36) |
| Ba phép kiểm vừa siết, trên mã đúng | `pytest -k "hai_lan or lua_chon_em or phu_huynh_chi_thay_yeu_cau_phu_huynh"` | 3 xanh / 53,16 s |
| Ma trận quyền (tự quét tuyến mới) | `pytest common/tests_ma_tran_quyen.py -q` | 2 xanh / 112,20 s |
| Đột biến | `python scripts/dot_bien_e3.py` | 36 · **33 giết** · 3 sống có chủ ý · **0 lọt** (xem §4) |
| Giao diện, 4 màn Yêu cầu × 2 khổ | `node scripts/do_giao_dien.mjs` | **0** vi phạm mọi hạng mục (tương phản, vùng chạm < 44 px, chữ < 12 px, tràn ngang, khối cắt ngoài khung, lỗi JS, CSP, lời gọi ghi lọt ra) |
| Bộ đo giao diện có ĐỎ được không | `node scripts/do_giao_dien.mjs --tu-kiem` | **ĐẠT** — cả 4 lượt đỏ khi nhét quy tắc hỏng (188 vi phạm tương phản, 190 chữ dưới sàn) |
| Tiếp cận (axe-core), 23 trang × 2 khổ + view/tối | `node scripts/do_axe.mjs` | lượt 1: **2 nút vi phạm / 114 lượt**; vá rồi lượt 2: *(điền)* |
| Trọn luồng dòng 11 trên màn thật | `node scripts/do_yeu_cau.mjs` | **17/17 bước ĐẠT** |
| Kiểm lại bản vá buổi bù qua API thật (cổng 9600, Neon dev) | kịch bản tạm | ô chọn của em KHÔNG dự: không có buổi bù; POST → **404**. Em CÓ dự: có buổi bù; POST → **201**. Đã dọn buổi vừa dựng. |

### Test ĐỎ TRƯỚC (trên mã cũ)

| Phép kiểm | Đỏ vì |
|---|---|
| `test_buoi_bu_chi_em_du_moi_bao_loi_duoc` | ô chọn có buổi bù + POST trả 201 thay vì 404 |
| `test_nhan_su_tao_ho_em_khong_du_buoi_bu_thi_chan` | `assert 201 == 400` |
| `test_nguoi_nhan_khong_lo_email_voi_tro_giang` | `'dj_yc_…@example.com' not in [...]` — email nằm trong danh sách trợ giảng đọc được |

---

## 4 · Đột biến

Năm đột biến mới của lượt này đã đưa vào loạt chung `scripts/dot_bien_e3.py`
(không để ở kịch bản tạm nữa). Ghi chú công cụ: `scripts/dot_bien.py` — bộ chạy
loạt dùng chung, ăn một tệp JSON — **chưa có trên `erp`** lúc tôi đo
(`git ls-tree -r --name-only erp | grep dot_bien` chỉ ra `scripts/dot_bien_e1.py`);
nó đang nằm trong cây làm việc của lead. Khi nó vào `erp`, chuyển loạt E3 sang
nó là một lượt sửa nhỏ.

### Năm đột biến của bản vá buổi bù + lỗ email — **5/5 bị giết**

| Đột biến | Kết quả |
|---|---|
| bỏ lọc `thuoc_buoi` ở ô chọn buổi của học viên | **ĐỎ ✓** |
| bỏ hàng rào `_du_buoi` khi HỌC VIÊN tự gửi | **ĐỎ ✓** |
| bỏ hàng rào `_du_buoi` khi NHÂN SỰ gõ hộ em | **ĐỎ ✓** |
| đảo THỨ TỰ tham số `thuoc_buoi` (`uid` ↔ `sid`) | **ĐỎ ✓** |
| `/nguoi-nhan` trả email cho MỌI vai | **ĐỎ ✓** |

### Cả loạt E3: 35 đột biến → 3 cái LỌT, đã siết

Loạt đầy đủ báo `35 đột biến · 30 bị giết · 2 sống có chủ ý · 3 sống ngoài dự
kiến`. Ba cái lọt KHÔNG phải của bản vá lượt này, nhưng luật là "đột biến lọt
nghĩa là test yếu, phải siết" — nên tôi soi từng cái:

| Đột biến lọt | Vì sao lọt | Đã làm gì | Nay |
|---|---|---|---|
| danh sách em của lớp ngoài phạm vi | phép kiểm đòi `hocVien == []` trên lớp B, mà lớp B **vốn không có em nào** — nó xanh vì lý do khác | cho lớp B một em, và bắt GV lớp B phải THẤY em ấy trước khi đòi trợ giảng lớp A không thấy | **ĐỎ ✓** |
| PH chọn được em / lớp khác qua thân request | đột biến ở tầng dịch vụ **không quan sát được qua HTTP**: `PhuHuynhYeuCauView.post` không chuyển `hoc_vien_id` / `class_id` xuống `tao()` | đánh dấu đúng là "hai lớp chặn", và thêm một đột biến gỡ **CẢ hai** (view chuyển khoá xuống + dịch vụ nhận) | cái gỡ cả hai: **ĐỎ ✓**; cái gỡ một lớp: SỐNG có chủ ý |
| duyệt hai lần: gỡ CẢ kiểm "đã duyệt" lẫn máy trạng thái | **hai** nguyên nhân — (a) test chỉ đòi mã 409, mà gỡ hàng rào thì việc chuyển lớp (lớp thứ ba) cũng trả 409, bằng câu *"Em không đang học lớp …"*; (b) **lỗi trong chính bộ chạy** | (a) đòi đúng câu "đã được duyệt"; (b) vá bộ chạy | **ĐỎ ✓** |

**Lỗi trong bộ chạy đột biến** (đáng báo riêng): `scripts/dot_bien_e3.py` viết
`noi = goc.get(p) or open(p).read()`, nên cặp thay thế **thứ hai trong cùng một
tệp** được áp lên bản GỐC — cặp đầu bị xoá sạch. Mọi đột biến "gỡ CẢ hai lớp"
nằm trong MỘT tệp thật ra chỉ gỡ MỘT, rồi báo "SỐNG" vì lớp kia vẫn chặn. Nghĩa
là công cụ **báo yên tâm sai**. Đã vá: đọc lại từ đĩa mỗi cặp, chỉ lưu bản gốc ở
cặp đầu. Trong loạt E3 chỉ mục "duyệt hai lần: gỡ CẢ…" có hai cặp cùng tệp, nên
chỉ mục ấy đổi kết quả; các mục khác là VIEW + DỊCH VỤ (hai tệp) nên không ảnh
hưởng.

Sau khi siết: **36 đột biến · 33 bị giết · 3 sống có chủ ý (một lớp chặn, lớp
kia còn) · 0 sống ngoài dự kiến.**

---

## 5 · Ảnh đã soi

Thư mục: thư mục nháp của phiên
(`…\scratchpad\anh_e3\`), không commit (ảnh mang tên học viên thật của lớp mẫu).

| Ảnh | Màn | Khổ · chủ đề |
|---|---|---|
| `01-hv-hop-1440-sang.png` | Hỏi & yêu cầu (học viên) | 1440 · sáng |
| `02-hv-dien-form.png`, `03-hv-da-gui.png` | biểu mẫu gửi, trước và sau | 1440 · sáng |
| `06-…` → `12-hvu-lich-su-384.png` | học vụ: nhận · đổi loại · giao · kết quả · lịch sử | 1440 · sáng |
| `13-hv-sau-khi-xong-384.png` | học viên đọc lại — có Kết quả, KHÔNG có ghi chú nội bộ | 1440 · sáng |
| `14-ph-to-bao-cao-1440-sang.png`, `16-ph-da-gui.png` | phụ huynh qua link tờ báo cáo | 1440 · sáng |
| `17-hv-hop-390-sang.png`, `17-hvu-hop-390-sang.png`, `17-hvu-chi-tiet-390-sang.png` | ba màn trên điện thoại | 390 · sáng |
| `18-hv-hop-1440-toi.png`, `18-hvu-hop-1440-toi.png`, `18-ph-to-bao-cao-1440-toi.png` | ba màn, chủ đề tối | 1440 · tối |
| `18-hv-hop-390-toi.png`, `18-hvu-hop-390-toi.png`, `18-ph-to-bao-cao-390-toi.png` | ba màn, điện thoại tối | 390 · tối |

Soi thấy gì: chữ trên màn là tiếng Việt người dùng, ô lọc viết "Tất cả loại" /
"Tất cả lớp" (đúng thước `frontend/e2e/unit/thuat-ngu.test.mjs`); ở 390 không
tràn ngang, chữ xuống dòng gọn; chủ đề tối đọc được cả chip trạng thái lẫn dòng
thời gian.

---

## 6 · Việc còn sót

1. **Không có hạn xử lý / cờ quá hạn.** Dòng 11 không đòi, nhưng giáo vụ thật
   sẽ hỏi ngay: hộp hiện không biết một yêu cầu đã nằm đó bao lâu.
2. **Phân loại không đổi được sang nhóm xin–duyệt** (`loai.py:86`). Cố ý — đổi
   một câu hỏi thành một lượt thực thi là việc khác hẳn — nhưng giáo vụ gặp
   trường hợp "em viết nhầm chỗ" thì phải bảo em gửi lại.
3. **Hộp không có ô tìm theo chữ**, chỉ lọc trạng thái / loại / lớp / "Chỉ việc
   giao cho tôi". Hộp mới 7 yêu cầu thì đủ; vài trăm thì không.
4. **Báo lỗi bản ghi có HAI hộp thư** (§72 chuông và §65 yêu cầu) — lead đã đưa
   lên anh Sơn, mục K4 `docs/VIEC_CUA_ANH.md`. Không đụng trong lượt này.

### Bốn cái vướng của công cụ, không phải của sản phẩm

1. `scripts/nap_lai_be.ps1` **không chạy được trong worktree agent**: nó đòi
   `<worktree>/backend/.venv/Scripts/python.exe`, mà worktree dùng venv của repo
   chính. Phải tắt/bật tay.
2. `scripts/don_may.ps1` **ném lỗi** khi một tiến trình không có `Pid`
   (`Where-Object { $dung.ContainsKey($_.Pid) }` → `Key cannot be null`) — chạy
   được lúc máy sạch, đổ lúc cần nó nhất.
3. `next dev` **Turbopack không chạy trong worktree**: `frontend/node_modules`
   là junction trỏ ra ngoài gốc dự án, Turbopack panic
   *"Symlink [project]/node_modules is invalid, it points out of the filesystem
   root"* và tắt máy chủ. Phải `next dev --webpack`. Mọi agent dùng worktree sẽ
   vấp — nên ghi vào `giao-viec-agent`.
4. `scripts/dot_bien_e3.py` **báo yên tâm sai** với đột biến nhiều cặp trong một
   tệp (§4) — đã vá trong lượt này. Nếu `scripts/dot_bien.py` của lead dựng theo
   cùng nếp `goc.get(p) or open(p)` thì nó mang y hệt lỗi ấy; nên soi trước khi
   tin số của nó.

## 7 · Câu cần anh Sơn quyết

Không có câu mới. Câu duy nhất còn treo của E3 là mục **K4** lead đã gửi (hai
hộp thư cho cùng một việc "bản ghi hỏng").
