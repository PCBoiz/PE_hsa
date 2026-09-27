# Em xem lại được cả khoá, không chỉ bốn buổi gần nhất — lượt 27/09/2026

Nguồn việc: anh Sơn 27/09/2026 — *"tập trung hoàn thiện bản mock production này đã để mình có
sản phẩm demo đưa họ"*. Chỗ cụ thể do agent soát bảng phân rã tìm ra
(`docs/agent/BAO_CAO_PHAN_RA.md` §3.3, §3.4, và câu hỏi **Q7**): bảng tóm tắt ghi dòng 29
"CÓ" là quá tay — thẻ lớp của học viên chỉ lấy **bốn** bản ghi và **bốn** tài liệu, không màn
nào liệt kê đủ theo buổi, và không có ô tìm.

Worktree `agent/hv2` (gốc `8724c08`). **Không dựng máy chủ nào** — không `next dev`, không
`runserver`; lượt này chỉ viết mã và chạy phép kiểm. Mọi con số dưới đây tự đo ngày
**27/09/2026** trên máy này.

---

## V0 · Đo đã có gì TRƯỚC khi viết một dòng mã

| Đã có | Ở đâu | Trần / giới hạn |
|---|---|---|
| Bản ghi trên thẻ lớp của em | `backend/teaching/lop_cua_toi.py:107-119` | `SO_BAN_GHI = 4` (`:44`) |
| Học liệu trên thẻ lớp của em | `lop_cua_toi.py:124-140` | `SO_HOC_LIEU = 4` (`:48`) |
| Ghi nhận "em đã mở bản ghi" | `backend/teaching/ban_ghi.py:87-114` (`POST /api/sessions/<id>/ban-ghi/da-mo`) | đếm `recording_views.lan_mo`, không đếm phút xem |
| Trợ giảng xem ai chưa mở | `ban_ghi.py:117-186` | `SO_BUOI = 12` buổi gần nhất |
| Danh sách học liệu ĐỦ cho NHÂN SỰ | `backend/teaching/hoc_lieu.py::danh_sach` (`:120`) | không phân trang, không ô tìm |
| Hàng rào buổi bù | `backend/teaching/nguoi_buoi.py::thuoc_buoi` | **đòi tên cột có tiền tố bảng** |
| Màn thẻ lớp | `frontend/src/components/LopCuaToi.tsx:400` (khối "Xem lại:"), `:423` (khối "Tài liệu:") | bốn dòng, và trước lượt này KHÔNG có đường đi tiếp |

Kết luận đo: **hai** trần 4 là toàn bộ đường của em tới bản ghi và tài liệu. Nhân sự có danh
sách đủ từ lâu; người PHẢI XEM LẠI BÀI thì không. Lớp 24 buổi → mười một buổi trước đó biến
mất khỏi màn của em, và không có cách nào xem lại.

**Dùng lại, không viết lại:** `thuoc_buoi` (§62e) · `common/params.py::mau_like` (thoát `%`,
`_` — dùng chung với danh sách tài khoản) · `common/params.py::so_nguyen` · cửa ghi nhận
"đã mở" của §72 (màn mới gọi đúng cửa ấy, không đếm bằng đường thứ hai) ·
`lib/hocLieu.ts::tenMien`.

**Một chỗ CỐ Ý không gọi lại:** `hoc_lieu.py::_la_hoc_vien_dang_hoc`. Cửa mới cần CẢ tên lớp
cho tiêu đề màn, nên hàng rào `left_at IS NULL` gộp vào chính câu lấy dòng lớp
(`hv_xem_du.py::_lop_cua_em`) — một lượt đi Neon thay vì hai. Chú thích tại chỗ nói rõ đây là
cùng một luật với `hoc_lieu.py` và `ban_ghi.py::_thuoc_lop`, và đột biến số 8 canh nó.

---

## V1 · Một cửa API cho em xem ĐỦ

`backend/teaching/hv_xem_du.py` (mới, 207 dòng) · tuyến
`GET /api/lop-cua-toi/<class_id>/xem-du` (`backend/teaching/urls.py:125`).

Tham số: `loai` (`ban-ghi` mặc định | `hoc-lieu`) · `tim` · `truoc` (khoá phân trang) ·
`limit` (mặc định 20, trần 50) · `chuaMo=1` (chỉ buổi em chưa mở) · `chi=chung|buoi` (kho
chung của lớp / tài liệu gắn vào buổi).

Trả `{lop:{id,name,code}, loai, items, tiep}`. Chỉ ĐỌC — không ghi bảng nào, nên không có
dòng nào trong sổ ghi chéo miền. Hai câu SQL một lượt gọi (dòng lớp + danh sách), số câu CỐ
ĐỊNH dù phân trang tới đâu.

**Ba điều bắt buộc, và chỗ canh từng điều:**

1. **Chỉ lớp em đang học → 404, không 403.** `hv_xem_du.py:120-124`. Lớp không tồn tại, lớp
   của người khác, và lớp em đã rời — cùng một câu trả lời, vì một cửa lớp trả 403 là đã nói
   ra rằng lớp đó có thật.
2. **Tài liệu đang ẩn KHÔNG tới em.** `AND NOT h.an` — `hv_xem_du.py:88`. Kiểm cả đường ô
   TÌM (`test_tai_lieu_dang_an_khong_lot_qua_o_tim`): ô tìm là cửa sau dễ quên nhất.
3. **Bản ghi / tài liệu của buổi BÙ chỉ tới em có trong buổi ấy.** Gọi `thuoc_buoi` với tên
   cột **CÓ TIỀN TỐ BẢNG** ở cả hai câu: `thuoc_buoi('s.id', '%s')` (`:74`) và
   `thuoc_buoi('h.session_id', '%s')` (`:89`). Đọc docstring của `thuoc_buoi` trước khi sửa —
   bỏ tiền tố thì `sp.session_id = sp.session_id` luôn đúng, không lỗi cú pháp, không cảnh báo.

**Phân trang THEO KHOÁ, và khoá là một CẶP.** Mốc là `(thời điểm, id)`, không phải `id` một
mình: lịch sinh hàng loạt rồi chèn buổi bù cho ra lớp mà thứ tự `id` **không** trùng thứ tự
thời gian. Máy chủ tự tra mốc từ chính dòng ấy bằng phép so HÀNG của Postgres
(`(s.starts_at, s.id) < (SELECT k.starts_at, k.id …)`), nên màn chỉ gửi lại một số nguyên —
trình duyệt không ghép mốc thời gian, nên múi giờ không có chỗ nào làm lệch một dòng. Câu con
lấy mốc có `k.class_id = %s`: thiếu nó thì `truoc` là id của dòng lớp KHÁC vẫn cho ra mốc hợp
lệ, tức một cách dò thứ tự thời gian của lớp khác. Không có mốc → câu con trả NULL → trang
rỗng: hỏng về phía an toàn.

Học liệu sắp "theo buổi" bằng `COALESCE(buổi.starts_at, h.created_at) DESC, h.id DESC` — tài
liệu của buổi nào thì theo giờ buổi ấy, kho chung theo lúc gắn.

---

## V2 · Bộ kiểm — ĐỎ trước, rồi mới làm xanh

`backend/teaching/tests_hv_xem_du.py` (mới, 27 phép kiểm).

Đo thật, theo đúng thứ tự:

* **Lượt ĐỎ** (viết test xong, chưa có một dòng mã nào của `hv_xem_du.py`):
  **24 đỏ / 3 xanh**, 107,96 s. Ba phép kiểm xanh là ba phép kiểm 404 — tuyến chưa tồn tại
  nên Django cũng trả 404; chúng được canh bằng đột biến số 8 và 11 chứ không bằng lượt này.
* **Lượt XANH** (sau khi viết `hv_xem_du.py` + tuyến): **27 xanh / 27**, 126,31 s.

Phủ đúng bảy điều brief đòi, cộng bốn điều đo được thêm:

| Điều đang canh | Phép kiểm |
|---|---|
| phân trang không trùng, không sót | `test_phan_trang_ban_ghi_khong_trung_khong_sot`, `..._hoc_lieu_...`, `test_trang_cuoi_khong_con_tiep` |
| ô tìm thật sự lọc | `test_o_tim_ban_ghi_loc_theo_chu_de`, `..._theo_ngay`, `test_o_tim_hoc_lieu_loc_theo_ten_va_mo_ta`, `test_o_tim_dau_phan_tram_khong_tra_ve_tat_ca` |
| tài liệu ẩn không lọt | `test_tai_lieu_dang_an_khong_lot_toi_em`, `..._khong_lot_qua_o_tim` |
| buổi bù chỉ em trong buổi thấy | `test_ban_ghi_buoi_bu_chi_em_trong_buoi_thay`, `test_tai_lieu_buoi_bu_...` |
| **buổi THƯỜNG tới cả lớp** | `test_ban_ghi_buoi_thuong_toi_ca_lop`, `test_tai_lieu_buoi_thuong_toi_ca_lop`, `test_kho_chung_cua_lop_toi_moi_em` |
| em lớp khác → 404 | `test_em_lop_khac_nhan_404_chu_khong_403`, `test_lop_khong_co_thi_404`, `test_ban_ghi_lop_khac_khong_lot_vao_danh_sach` |
| em đã rời lớp | `test_em_da_roi_lop_khong_xem_duoc_nua` |
| lớp rỗng → danh sách rỗng | `test_lop_chua_co_ban_ghi_nao_tra_danh_sach_rong` |
| *(thêm)* buổi huỷ / chưa diễn ra không hiện | `test_buoi_da_huy_va_buoi_chua_dien_ra_khong_hien` |
| *(thêm)* tham số rác không ra 500 | `test_tham_so_rac_khong_lam_do_man` |
| *(thêm)* `loai` lạ → 400 bằng lời tiếng Việt | `test_loai_khong_biet_thi_400_bang_loi_tieng_viet` |
| *(thêm)* "đã mở / chưa mở" + ô lọc | `test_da_mo_va_loc_chi_buoi_chua_mo`, `test_loc_kho_chung_va_theo_buoi` |

**Hai phép kiểm là một cặp, không phải một phép kiểm lặp lại.** "Buổi bù chỉ em trong buổi
thấy" và "buổi THƯỜNG tới cả lớp" canh HAI nhánh khác nhau của cùng một lỗi: bỏ tiền tố bảng
khi gọi `thuoc_buoi` làm điều kiện **luôn đúng** với em đã có dòng `session_participants` và
**luôn sai** với em chưa có dòng nào. Chỉ phép kiểm thứ hai bắt được nhánh sau — đúng nhánh
đã làm tài liệu buổi thường biến mất khỏi thẻ lớp hôm nay.

**Đo qua cửa API, không đọc thẳng bảng sau một lời gọi API** (tiền lệ 26/09: đọc thẳng bảng đi
bằng kết nối khác nên xanh khi chạy riêng, đỏ khi chạy cả bộ). Email sinh bằng `uuid4` nên hai
lượt song song không tranh khoá chỉ mục duy nhất (tiền lệ 16/09: cả lượt pytest treo vĩnh viễn).

---

## V3 · Đột biến

`scripts/dot_bien/hv_xem_du.json` — **16 đột biến**, mỗi mẫu khớp ĐÚNG một chỗ (`--xem` xác
nhận trước khi chạy). Nhắm vào đúng năm chỗ brief đòi, cộng bốn chỗ khác đáng canh:

| # | Đột biến | Nhắm vào |
|---|---|---|
| 1 | `AND NOT h.an` → `(NOT h.an OR TRUE)` | bộ lọc tài liệu ẩn |
| 2 | `thuoc_buoi('h.session_id', …)` → `thuoc_buoi('session_id', …)` | **bỏ tiền tố bảng** (tài liệu) |
| 3 | `thuoc_buoi('s.id', …)` → `thuoc_buoi('id', …)` | **bỏ tiền tố bảng** (bản ghi) |
| 4 | bỏ hẳn mệnh đề `thuoc_buoi` của bản ghi | hàng rào buổi bù |
| 5 | khoá phân trang bản ghi `<` → `<=` | khoá phân trang (trùng dòng) |
| 6 | khoá phân trang bản ghi bỏ mốc thời gian, chỉ còn `id` | khoá phân trang (nhảy dòng) |
| 7 | khoá phân trang học liệu `<` → `<=` | khoá phân trang |
| 8 | `m.left_at IS NULL` → `(… OR TRUE)` | bộ lọc `left_at` |
| 9 | `s.class_id = %s` → `(… OR TRUE)` | hàng rào lớp (bản ghi) |
| 10 | `h.class_id = %s` → `(… OR TRUE)` | hàng rào lớp (học liệu) |
| 11 | `if not lop:` → `if False:` | hàng rào thành viên |
| 12 | `_tim` luôn trả `None` | ô tìm |
| 13 | `_tim` không thoát ký tự đại diện | ô tìm (một dấu `%` trả cả kho) |
| 14 | bỏ lọc buổi huỷ + buổi chưa diễn ra | danh sách bản ghi |
| 15 | `tiep` luôn `None` | nút "Xem thêm" |
| 16 | `daMo` luôn `True` | con số "đã xem lại" |

**Kết quả: 16/16 bị giết, đúng chỗ.**

Bảng đầy đủ (nền: `27 passed in 125.70s`):

| Đột biến | Kết quả | Test đỏ đầu tiên đáng kể |
|---|---|---|
| 1 · bỏ lọc tài liệu đang ẩn | giết ✓ | `test_tai_lieu_dang_an_khong_lot_toi_em`, `..._qua_o_tim` |
| 2 · `thuoc_buoi` TÀI LIỆU mất tiền tố | giết ✓ | **`test_tai_lieu_buoi_thuong_toi_ca_lop`** (+ 2) |
| 3 · `thuoc_buoi` BẢN GHI mất tiền tố | giết ✓ | **`test_ban_ghi_buoi_thuong_toi_ca_lop`** (+ 12) |
| 4 · bỏ hàng rào buổi bù của bản ghi | giết ✓ | `test_ban_ghi_buoi_bu_chi_em_trong_buoi_thay` |
| 5 · khoá phân trang bản ghi `<=` | giết ✓ | `test_phan_trang_ban_ghi_khong_trung_khong_sot` |
| 6 · khoá phân trang bản ghi chỉ còn `id` | giết ✓ | `test_phan_trang_ban_ghi_khong_trung_khong_sot` |
| 7 · khoá phân trang học liệu `<=` | giết ✓ | `test_phan_trang_hoc_lieu_khong_trung_khong_sot` |
| 8 · bỏ lọc `left_at` | giết ✓ | `test_em_da_roi_lop_khong_xem_duoc_nua` |
| 9 · bỏ hàng rào lớp của bản ghi | giết ✓ | `test_ban_ghi_lop_khac_khong_lot_vao_danh_sach` (+ 6) |
| 10 · bỏ hàng rào lớp của học liệu | giết ✓ | `test_ban_ghi_lop_khac_khong_lot_vao_danh_sach` (+ 5) |
| 11 · hàng rào thành viên bất chấp | giết ✓ | `test_em_lop_khac_nhan_404_chu_khong_403` (+ 2) |
| 12 · ô tìm bị bỏ qua | giết ✓ | bốn phép kiểm ô tìm |
| 13 · ô tìm không thoát ký tự đại diện | giết ✓ | `test_o_tim_dau_phan_tram_khong_tra_ve_tat_ca` |
| 14 · buổi huỷ / chưa học cũng hiện | giết ✓ | `test_buoi_da_huy_va_buoi_chua_dien_ra_khong_hien` |
| 15 · `tiep` luôn null | giết ✓ | hai phép kiểm phân trang |
| 16 · `daMo` luôn đúng | giết ✓ | `test_da_mo_va_loc_chi_buoi_chua_mo` |

**Không đột biến nào LỌT, và không đột biến nào giết NHẦM CHỖ** — mỗi đột biến làm đỏ đúng
phép kiểm đã ghi ở ô `cho` của nó.

Hai dòng đáng đọc kỹ, vì chúng là bằng chứng cho cái cặp phép kiểm ở V2:

* **Đột biến 2** (bỏ tiền tố bảng ở tài liệu) làm đỏ `test_tai_lieu_buoi_thuong_toi_ca_lop`
  nhưng **KHÔNG** làm đỏ `test_tai_lieu_buoi_bu_chi_em_trong_buoi_thay`. Đúng như dự đoán: em
  A (có dòng `session_participants`) vẫn thấy, em B (chưa có dòng nào) mất SẠCH tài liệu của
  mọi buổi. Nếu tôi chỉ viết phép kiểm "buổi bù" thì lỗi này đi thẳng vào production —
  và nó đã từng đi, hôm 27/09 trên chính `lop_cua_toi.py`.
* **Đột biến 6** (phân trang bằng `id` một mình) chỉ đỏ được vì phép kiểm CỐ Ý chèn buổi theo
  thứ tự thời gian đảo (`(2, 11, 4, 9, 6, 13, 3, 8, 5)` ngày trước). Chèn buổi theo thứ tự
  tăng dần thì `id` trùng thứ tự thời gian, đột biến LỌT, và bộ kiểm xanh vì một lý do sai.

Lệnh đã chạy (loạt chạy 15:50–16:20, MỘT bảng, tệp tự phục hồi trong `finally`):

```
python scripts/dot_bien.py backend/teaching/hv_xem_du.py     --test teaching/tests_hv_xem_du.py --loat scripts/dot_bien/hv_xem_du.json
```


---

## V4 · Màn cho học viên

| Tệp | Việc |
|---|---|
| `frontend/src/lib/xemDu.ts` (mới) | hình dạng `zod/mini` + `duongTrang()` (dựng URL bằng `URLSearchParams`) + `buoiDay` / `ngayDay`. **Không khai `limit`** — số dòng một trang chỉ có ở máy chủ (RULES §7: bản đầu của tôi khai `MOI_TRANG = 20` ở CẢ hai phía, đúng lỗi đã mắc với trần 50 tài khoản) |
| `frontend/src/app/(standalone)/lop/[classId]/xem-lai/page.tsx` (mới) | trang máy chủ: tải sẵn trang ĐẦU của tab đang mở, thanh chung `AppShell`, 404 nói bằng lời người dùng |
| `frontend/src/app/(standalone)/lop/[classId]/xem-lai/XemLaiClient.tsx` (mới) | hai tab, ô tìm, ô lọc, "Xem thêm", ghi nhận "em đã mở" |
| `frontend/src/components/LopCuaToi.tsx` (sửa) | thêm HAI đường "Xem tất cả →" — bản ghi (`:415`) và tài liệu (`:432`) |

Thẻ lớp **giữ nguyên bốn dòng gần nhất**; chỉ thêm đường đi tiếp. Đường tài liệu mang
`?xem=tai-lieu` để mở sẵn đúng tab, không bắt em bấm thêm một lần. Ba bộ soát màn
(`scripts/man/nghiem_thu.json:402`, `nghiem_thu_e1.json:64`, `nghiem_thu_sau.json:286`) chỉ
đòi chữ "Xem lại" CÓ MẶT trên thẻ — đã dò, không bộ nào đếm số liên kết hay đòi chữ nào
VẮNG, nên thêm đường không làm bộ nào báo sai.

Đã làm đúng năm điều brief đòi:

* **Chữ tiếng Việt của người dùng.** Không `bai_tap`, không tên cột, không `r2` —
  `nguon === 'r2'` hiện thành lời (hoặc một câu nhờ nhắn giảng viên khi tài liệu chưa có
  đường mở), không bao giờ in mã. Cổng `e2e/unit/chu-nguoi-dung.test.mjs` **bắt được hai
  chuỗi của tôi** (hai ngày gõ cứng `24/09/2026` trong ô gợi ý và câu trạng thái rỗng) — đã
  đổi sang "theo dạng ngày/tháng/năm", cổng xanh lại.
* **Không hardcode px.** `min-h-11`, `basis-64`, `rounded-xl`, `gap-2`, `px-4`, và
  `pt-[calc(var(--topbar-h)+1.5rem)]` — không con số px nào. Token màu dùng bộ có sẵn:
  `text-ink` / `text-ink-2` / `text-ink-3` / `text-brand-ink` / `text-danger-ink` /
  `border-line` / `bg-surface` / `bg-brand-soft`. Cổng `e2e/unit/lop-chu-ton-tai.test.mjs`
  xanh — **không lớp `text-*` nào Tailwind không sinh được** (đây là cổng bắt `text-warn-ink`,
  cái tên KHÔNG tồn tại mà Tailwind v4 nuốt lặng lẽ).
* **Mọi ô, mọi nút khoá tới khi React gắn xong** — `useDaGan()`, `disabled={!daGan}` trên cả
  hai tab, ô tìm, nút Tìm, nút Xoá ô tìm, ba ô lọc và nút "Xem thêm".
* **"Xem thêm" nối thêm theo khoá**, không theo số trang (`truoc` = `tiep` của lượt vừa rồi),
  nên không trùng dòng kể cả khi giảng viên gắn thêm tài liệu giữa hai lần bấm.
* **Bấm mở bản ghi thì ghi nhận "em đã mở" qua đúng cửa §72**
  (`POST /api/sessions/<id>/ban-ghi/da-mo`) — cùng cửa thẻ lớp đang gọi, nên con số
  "1/2 em đã mở" của trợ giảng vẫn đếm cùng một thứ. Việc báo chạy ngầm: máy chủ lỗi thì em
  vẫn mở được bản ghi.

Và hai chỗ học từ lỗi cũ trong repo: đổi tab / đổi lọc / tìm lại **dọn sạch danh sách trước**
(không để nhãn mới đứng trên số liệu cũ), và trạng thái rỗng nói **hai câu khác nhau** cho
"chưa có gì" và "ô tìm không khớp".

---

## Cổng đã chạy

| Cổng | Kết quả |
|---|---|
| `ruff check .` | All checks passed |
| `manage.py check` | no issues |
| `pytest teaching/tests_hv_xem_du.py` | **27/27 xanh** |
| `pytest teaching/ -q` (hồi quy) | **669 xanh / 0 đỏ**, 1:18:05 (brief đoán ~330 — số thật là 669) |
| `tsc --noEmit` | 0 lỗi |
| `eslint . --max-warnings 0` | 0 lỗi |
| 38 bộ `e2e/unit/*.test.mjs` | tất cả xanh (một bộ đỏ giữa lượt, đã vá — xem V4) |
| `node scripts/ban_do.mjs --kiem` | 0 lời gọi không khớp · 0 tuyến không ai gọi |
| `python scripts/quet_bi_mat.py` | 20 tệp, không thấy bí mật nào |
| `python scripts/cau_truc.py` (+ `--kiem`) | sinh lại xanh: 16 miền · 221 tệp backend · 214 tệp frontend · **11 mục nợ ghi chéo — KHÔNG tăng** · 0 lỗi |
| `next build` | **CHƯA CHẠY** — hộp cát của agent từ chối (ghi `.next/`, tài nguyên dùng chung). Lead nên chạy một lượt: `tsc` không bắt được lỗi riêng của Next (biên client/server, kiểu `searchParams`) |
| DDL | **không thêm gì** — cửa này chỉ đọc `class_sessions`, `recording_views`, `hoc_lieu`, `class_members`, `classes` |

Sổ miền: `scripts/so_mien.json` thêm `backend/teaching/hv_xem_du.py`,
`frontend/src/app/(standalone)/lop/**`, `frontend/src/lib/xemDu.ts` vào miền **lop_hoc** —
cùng miền với `lop_cua_toi.py` và `hoc_lieu.py`, vì trục vẫn là "lớp của em".

---

## Ba liên kết tôi đã tạo trong worktree — lead phải biết trước khi gỡ worktree

Worktree `hv2` không có `.env`, không có `.venv`, không có `node_modules`, nên `pytest`,
`tsc` và `eslint` đều không chạy được. Đã nối sang bản chính bằng liên kết cấp hệ tệp thay vì
SAO CHÉP — sao chép `.env` là nhân bản bí mật ra một chỗ thứ hai, và sao chép `node_modules`
là vài trăm MB đĩa:

| Đường trong worktree | Kiểu | Trỏ tới |
|---|---|---|
| `backend/.env` | hard link | `D:/pe_hsa/backend/.env` |
| `backend/.venv` | junction (thư mục) | `D:/pe_hsa/backend/.venv` |
| `frontend/node_modules` | junction (thư mục) | `D:/pe_hsa/frontend/node_modules` |

Cả ba đều bị `.gitignore` chặn (`git check-ignore` xác nhận: `.gitignore:5`, `:30`,
`frontend/.gitignore:4`), nên không có đường nào lọt vào commit. **Nhưng `git worktree remove`
có thể vướng ở hai junction** — gỡ chúng trước bằng `Remove-Item` (xoá junction KHÔNG xoá thư
mục đích), rồi mới gỡ worktree. `.venv` là chỗ `scripts/dot_bien.py` tìm Python: nó gọi
`<gốc>/backend/.venv/Scripts/python.exe` bằng đường CỐ ĐỊNH, nên không có junction thì loạt
đột biến chết ngay ở lượt nền với `WinError 2` (đã gặp thật, lượt đầu).

---

## Việc còn sót — nói thẳng

1. **Chưa mở màn thật trong trình duyệt.** Brief cấm dựng máy chủ (máy còn 2,4 GB lúc nhận
   việc), nên lượt này không có một con số nào đo trên màn. **Lead phải tự đo** — danh sách ở
   cuối.
2. **Đường "Xem tất cả" chỉ hiện khi lớp ĐÃ có ít nhất một bản ghi / một tài liệu**, vì nó nằm
   trong chính hai khối ấy của thẻ lớp. Lớp chưa có gì thì không có đường vào trang (cũng
   không có gì để xem). Nếu anh Sơn muốn đường vào luôn hiện thì đó là thêm một dòng vào thẻ
   lớp — một quyết định về bố cục, không phải một lỗi.
3. **Chưa có spec Playwright** cho màn mới (`e2e/nghiem-thu/…`). Phép kiểm backend phủ hành vi,
   nhưng "em bấm Xem tất cả rồi bấm Xem thêm hai lần" thì chưa có bộ đo nào chạy.
4. **Chưa cập nhật `docs/NGHIEM_THU_TOPHSA.md`.** Ô tóm tắt dòng 29 hiện ghi "MỘT PHẦN" kèm
   con số 4; sau lượt này nó nâng được lên CÓ, nhưng chỉ sau khi lead đo trên màn thật —
   không tự tick một dòng nghiệm thu bằng phép kiểm backend.
5. **Ô tìm bản ghi tìm theo `topic` và theo ngày `DD/MM/YYYY`**, không tìm theo nội dung buổi
   (sổ đầu bài `session_logs`). Chưa làm vì đó là dữ liệu của miền khác và bảng của khách
   không đòi.
6. **`hv_xem_du.py` lặp lại luật `left_at IS NULL`** thay vì gọi
   `hoc_lieu.py::_la_hoc_vien_dang_hoc` (lý do ở V0). Đây là chỗ thứ tư trong repo viết cùng
   một luật. Nếu lead thấy đáng gom thì chỗ gom đúng là một hàm dựng mệnh đề SQL dùng chung,
   không phải một hàm trả `bool` — vì ba trong bốn chỗ cần mệnh đề, không cần câu trả lời.

---

## Lead phải tự đo gì trên màn thật (tôi không đo được — brief cấm dựng máy chủ)

Dùng lớp **22102** (lớp mẫu có khung đầy đủ; lớp 1 đang gắn một khung thử ba mục). Thẻ học
viên: `.the/tokens_hv.json`, sống 30 phút.

1. Thẻ lớp ở bảng điều khiển học viên: hai đường **"Xem tất cả →"** có hiện không (một ở dòng
   "Xem lại:", một ở dòng "Tài liệu:"), và bấm có sang `/lop/22102/xem-lai` không. Đường tài
   liệu phải mở SẴN tab "Tài liệu".
2. Trang `/lop/22102/xem-lai`: **đếm số dòng** và so với số buổi có bản ghi trong CSDL — đây là
   con số chứng minh trần 4 đã hết. Bấm **"Xem thêm"** cho tới hết rồi đếm lại: không dòng nào
   xuất hiện hai lần.
3. Gõ ô tìm một chủ đề buổi, rồi gõ một NGÀY dạng `24/09/2026`. Cả hai phải lọc thật.
4. Bấm ô lọc **"Chưa xem lại"**, mở một bản ghi, tải lại trang: buổi ấy phải rời khỏi danh sách
   lọc và mang nhãn "Bạn đã mở". Rồi mở màn trợ giảng `/giang-day/buoi-hoc/22102` xem con số
   "đã mở / chưa mở" có nhích đúng một — **đây là phép đo quan trọng nhất**, nó chứng minh màn
   mới không dựng một đường đếm thứ hai.
5. **Bấm ô tìm và ô lọc NGAY khi trang vừa hiện** (trước khi React gắn): chúng phải mờ và không
   bấm được, chứ không phải bấm mà không có gì xảy ra.
6. Khổ **390 px**: ô tìm xuống dòng riêng, không tràn ngang, hai nút vẫn chạm được.
7. Bộ tối và bộ sáng: chip "Chưa xem lại" và câu lỗi đỏ phải đọc được ở cả hai.
8. Gõ thẳng `/lop/<một lớp em không học>/xem-lai` → phải ra thẻ "Không tìm thấy lớp này",
   **không** phải một trang lỗi.

Sau khi đo xong, chỗ cần sửa trong `docs/NGHIEM_THU_TOPHSA.md`: ô tóm tắt **dòng 71** (dòng 29
— nâng MỘT PHẦN → CÓ nếu bước 2 và 3 đạt), **dòng 72** (dòng 30 — gỡ câu "Lưu ý thêm" về trần
4), và hai mục chi tiết ở **dòng 490** và **dòng 509**. Tôi **không tự sửa** tài liệu nghiệm
thu: một dòng nghiệm thu chỉ được tick bằng số đo trên màn thật (RULES §1), và lượt này không
có số nào như thế.

---

## Câu hỏi cần anh Sơn quyết

**H1 · Trang này có cần cho PHỤ HUYNH không?** Hôm nay chỉ em đang học lớp mở được. Phụ huynh
có tờ báo cáo riêng, nhưng "con tôi đã xem lại bài chưa" là câu họ sẽ hỏi — và nó là một cửa
mới, không phải một ô sửa.

**H2 · Em đã RỜI LỚP có được xem lại bản ghi không?** Hôm nay: **không** (404), giữ đúng luật
§60 và §72 đang có. Nhưng em học xong một khoá ba tháng rồi ôn thi bằng chính bản ghi ấy là
việc rất thường. Nếu mở thì mở tới đâu — bao nhiêu ngày sau khi rời lớp, và có mở cả tài liệu
hay chỉ bản ghi?

**H3 · Trần 4 trên thẻ lớp có giữ nguyên không?** Nay đã có đường "Xem tất cả" thì bốn dòng là
đủ, và đó là con số làm thẻ đọc được trong mươi giây. Nhưng nếu anh muốn thẻ hiện nhiều hơn
thì đổi đúng hai hằng (`SO_BAN_GHI`, `SO_HOC_LIEU`) — rẻ nhất trong cả hệ thống.

**H4 · Có cần nút "tải tài liệu về" không?** Hôm nay mọi tài liệu là LIÊN KẾT NGOÀI (anh chốt
26/09), nên màn chỉ mở tab mới. Cột `nguon = 'r2'` đã chừa sẵn ở lược đồ và màn đã đọc được
nó, nhưng chưa có khoá Cloudflare R2 nên chưa có tệp nào tải thẳng lên.
