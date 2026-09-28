# Báo cáo luồng A1 — vận hành lớp, mẻ vá rẻ (V-a … V-h)

Nhánh `agent/luong-a1`. Phiên cloud 25/09/2026 làm tiếp WIP `919a0b8` của agent cục bộ.
Máy cloud: Postgres 16 cục bộ, bảng `lessons` TRỐNG, không có tài khoản rà soát → **không chạy
e2e Playwright, không chạy `do_axe.mjs`, không chụp màn** (việc lead, xem cuối tệp).

## Commit

| Commit | Nội dung |
|---|---|
| `ad58370` | V-b — trợ giảng thấy `vangLien` / `canChuY` của lớp mình |
| `930e831` | V-c — trạng thái lớp "Tạm dừng" |
| `fb7ec55` | §62b–§62f — lược đồ cả luồng |
| `5b2c4d9` | V-a + V-f — nhận xét GV, cờ "cần hỗ trợ", đề xuất hướng học |
| `196d3aa` | V-d — lịch sử sửa điểm danh + học viên xem điểm danh từng buổi |
| `919a0b8` | WIP (agent cục bộ): V-e, V-g, phần lớn V-h |
| `e1fe37b` | gộp `origin/erp` (`0544692`: vá token cùng giây, thước sổ lược đồ) — không xung đột |
| `44524ff` | V-g — test canh thêm "buổi đã huỷ" (đột biến còn sống → đã giết) |
| `a8f467f` | V-h — hoàn tất: tờ phụ huynh + PDF khối "Bài kiểm tra", thẻ lớp không đếm, nhãn dòng thời gian, hướng dẫn, ma trận quyền, NGHIEM_THU |

`erp` đã có tới `5b2c4d9` + lược đồ (qua `b9a78d3`). **Chưa vào erp**: `196d3aa`, `919a0b8`, `44524ff`,
`a8f467f` (+ tệp này).

## Từng mục

Số test là số phép kiểm của mô-đun riêng mục ấy. "Đỏ trước" = chạy test mới trên mã TRƯỚC mục.
Đột biến: nền xanh, mỗi đột biến phải làm module đỏ (exit 1); đột biến còn sống thì thêm test tới khi
đỏ, không báo là đã phủ.

| Mục | Trạng thái | Test | Đỏ trước | Đột biến | Đo ở đâu |
|---|---|---|---|---|---|
| V-a nhận xét GV (dòng 18, 24) | XONG | `tests_danh_gia.py` 7 | 7/7 | 7/7 (gộp V-f) | agent cục bộ, commit `5b2c4d9` |
| V-b TG thấy vắng liền / cần chú ý (dòng 21) | XONG | `tests_viec_hom_nay.py` 11 | 2 hỏng trên mã cũ | 3/3 | agent cục bộ, commit `ad58370` |
| V-c lớp "Tạm dừng" (dòng 4) | XONG | `tests_sinh_buoi` 30, `tests_viec_hom_nay` 11, `courses/tests_truy_cap::test_lop_tam_dung_van_giu_quyen_mon`, `tests_tong_quan` 11 | 4 hỏng trên mã cũ (`930e831`) | 2/2 (cục bộ, viec_hom_nay) + **4/4 đỏ trên cloud** (sinh_buoi ×3, chưa điểm danh). `truy_cap` CHƯA đo — mô-đun cần bài thật | cục bộ + cloud |
| V-d lịch sử điểm danh (dòng 9, 14, 28) | XONG | `tests_lich_su_diem_danh.py` 4 + `tests_lop_cua_toi` 10 | 4/4 | 7/7 | agent cục bộ, commit `196d3aa` |
| V-e đối tượng nhận bài (dòng 17) | XONG | `tests_nhan_bai.py` 10 | **10/10 hỏng trên `196d3aa`** | **8/8 đỏ** | **cloud, đo thật** |
| V-f cờ cần hỗ trợ + hướng học (dòng 18) | XONG | `tests_danh_gia.py` (chung V-a) | 7/7 | 7/7 | agent cục bộ |
| V-g buổi bù (dòng 10) | XONG | `tests_buoi_bu.py` 7 | **7/7 hỏng trên `196d3aa`** | **13/13 đỏ** (lần đầu 12/13 — "buổi đã huỷ" trên thẻ lớp chưa ai canh → thêm assert ở `44524ff`) | **cloud, đo thật** |
| V-h bài kiểm tra trên lớp (dòng 4, 17) | XONG | `tests_kiem_tra.py` 6 + `tests_bao_cao_pdf.py` 2 mới (23 cả mô-đun) | **6/6 hỏng trên `196d3aa`; 1 test PDF hỏng trước khi thêm khối** | **17/17 đỏ** | **cloud, đo thật** |

Đột biến đã chạy trên cloud (`scratchpad/dot_bien.py`, cùng luật với bản gốc: nền xanh, exit 1 mỗi đột biến):
- **V-e (8)**: `giao_cho` luôn đúng; Việc hôm nay / thẻ lớp / tờ phụ huynh / danh sách bài học viên / nộp bài bỏ
  lọc nhóm (mỗi chỗ một đột biến); báo lại em đã nhận; trợ giảng đổi được người nhận.
- **V-g (13)**: `thuoc_buoi` luôn đúng; sổ điểm danh bỏ lọc (đọc, ghi); thẻ lớp buổi tới, buổi huỷ; lịch
  em; cơ sở học phí; "chưa điểm danh"; tờ phụ huynh; báo đổi lịch; nhận em ngoài lớp; không báo; bỏ
  `can_see_class`; không ghi `makeup_for`.
- **V-h (17)**: học viên nộp được; thẻ lớp đếm "chưa nộp"; lẫn vào khối bài tập của tờ; mất cờ vắng; bỏ
  khối; "vắng" ở bài thường; vắng kèm điểm; vắng không rút điểm khỏi sổ; sổ không tách loại; dòng thời gian
  ×3 (bỏ, sai mốc, không nói vắng); sự kiện không mang `loai`; chuông cho em vắng; chuông không nói "kiểm
  tra"; PDF ×2.

- **V-c (4, thêm trên cloud)**: sinh lịch cho lớp tạm dừng; màn vẫn mời sinh lịch; màn không báo tạm dừng;
  "chưa điểm danh" gồm lớp tạm dừng.

Mục V-a, V-b, V-d, V-f: phiên cloud KHÔNG đo lại đột biến — số liệu lấy từ thông điệp commit của agent cục bộ.
Test của chúng xanh lại trên cloud (bảng dưới).

Việc V-h phiên này thêm (`a8f467f`): thẻ "Lớp của bạn" không đếm bài kiểm tra là "chưa nộp"; tờ phụ huynh
khối riêng `kiemTra` (`parent_report._kiem_tra_lop` — chỉ bài đã nhập điểm hoặc ghi vắng, theo ngày làm bài
trong kỳ) và bài kiểm tra rời khối "Bài tập giảng viên giao"; màn `ToBaoCao.tsx` (zod `.optional()`) và PDF
`bao_cao_pdf.py` in "Bài kiểm tra"; nhãn "Bài kiểm tra" ở dòng thời gian hồ sơ; hướng dẫn + ma trận quyền;
NGHIEM_THU dòng 4 và 17.

## Kiểm cuối (cloud, sau khi gộp `origin/erp` @ `0544692`)

- `bootstrap_schema` ×2: lượt 2 = `0/62 mục chạy` (chỉ mục chạy mỗi lượt §57). `kiem_luoc_do`: 57/57 mục.
- pytest **từng mô-đun một**, cả 69 mô-đun: 1062 qua, 70 hỏng trong 11 mô-đun. **70 hỏng ấy trùng khớp
  từng tên** với khi chạy cùng 11 mô-đun trên worktree `origin/erp` (so `diff` tập tên FAILED: không khác)
  → do môi trường, không do nhánh. Nguyên nhân chính: `lessons` trống (vd. `tests_bao_cao_tuan`: "em chỉ học
  Định lượng mà tờ báo cáo in cả hợp phần…", cần bài thật); `accounts/tests.py` "token cũ phải chết ngay"
  cũng hỏng y hệt trên erp.
  Mô-đun luồng A1 đều xanh: `tests_nhan_bai` 10, `tests_buoi_bu` 7, `tests_kiem_tra` 6, `tests_bao_cao_pdf`
  23, `tests_lich_su_diem_danh` 4, `tests_danh_gia` 7, `tests_viec_hom_nay` 11, `tests_dong_thoi_gian` 6,
  `tests_lop_cua_toi` 10, `tests_sinh_buoi` 30, `tests_tong_quan` 11, `common/tests_ma_tran_quyen` 2,
  `common/tests_luoc_do_muc` 40, `common/tests` 41, `common/tests_hop_dong` 10.
  Ngoại lệ: `courses/tests_truy_cap.py` 3 hỏng (gồm `test_lop_tam_dung_van_giu_quyen_mon` của V-c) — 404
  vì không có bài học nào; cả 3 hỏng y hệt trên erp. **Lead chạy lại mô-đun này trên Neon dev.**
- Frontend: `npx tsc --noEmit` sạch; `npx eslint --max-warnings 0` trên 19 tệp đã sửa của luồng sạch; mọi
  `e2e/unit/*.test.mjs` xanh (gồm `chu-nguoi-dung`, `chot-ham-tang-cu`, `lop-hoc`);
  `node scripts/ban_do.mjs --kiem`: 0 gãy; `npx next build --webpack`: exit 0.
- `python scripts/tang_vai.py --kiem`: bản trong repo **không chạy trên Linux** (đường dẫn viết
  `r'frontend\src\app'`). Chạy bản sao đổi `\` → `/` trong scratchpad: "32 trang, 0 lệch chưa giải
  thích". Tệp gốc KHÔNG sửa (ngoài phạm vi luồng) — nên vá bằng `os.path.join` từng đoạn.

## Hunk ở tệp dùng chung (chưa vào erp)

- `backend/common/audit.py` — `record(..., luc=)` (V-d: dòng nhật ký mang đúng mốc của lịch sử).
- `backend/teaching/sessions.py` — lịch sử điểm danh trong giao dịch lưu (V-d); sổ điểm danh đọc/ghi qua
  `thuoc_buoi` (V-g).
- `backend/teaching/parent_report.py` — `giao_cho` (V-e), `thuoc_buoi` (V-g), `_kiem_tra_lop` + khoá
  `kiemTra` (V-h).
- `backend/teaching/viec_hom_nay.py`, `lop_cua_toi.py`, `lich.py`, `co_so_hoc_phi.py`, `bao_doi_lich.py`,
  `exports.py`, `dong_thoi_gian.py`, `urls.py` (2 tuyến mới: `sessions/<id>/attendance/history`,
  `sessions/<id>/buoi-bu`).
- `backend/stats/gradebook.py` — loại "Bài kiểm tra" (`meta.loai = 'kiem_tra'`).
- `frontend/src/lib/hinhDang.ts` (khoá mới đều `.optional()`), `huongDan.ts`, `quyenVai.ts`,
  `components/ToBaoCao.tsx`, `components/LopCuaToi.tsx`.
- `docs/NGHIEM_THU_TOPHSA.md` — dòng 4, 9, 10, 14, 17, 18, 21, 28 (cột "Spec" để nguyên cho lead).

## Lead phải làm khi gộp

1. **Lược đồ**: §62b–§62f và §35 (`paused`) đã có trên erp — gộp nhánh này KHÔNG đổi SQL. Không có bước
   thứ tự lược đồ mới.
2. **Deploy**: backend (Render) trước hoặc cùng lúc frontend — frontend đọc `kiemTra`, `kind`, `heldOn`,
   `absent`, `diemDanh`… đều `.optional()`, nên Vercel đi trước ~40 phút vẫn an toàn.
3. **E2E cần chạy** (không chạy được trên cloud), cả `may-tinh` và `dien-thoai`, `E2E_GHI=1`, trên dữ liệu
   `audit2009.*`:
   - V-e: giao bài "Chọn học viên" 2 em → em thứ ba không thấy bài ở mục Bài tập, không bị đếm "chưa nộp".
   - V-g: sổ buổi học → "Tạo buổi bù" trên một buổi → chỉ em được chọn thấy buổi ở "Lớp của bạn" và có tên
     trong sổ điểm danh buổi bù.
   - V-h: "Giao bài mới" → Loại "Bài kiểm tra trên lớp (nhập điểm)" + ngày → "Nhập điểm" → điểm / "Vắng" →
     Lưu; học viên thấy điểm (không có ô nộp); tờ báo cáo của em có khối "Bài kiểm tra"; hồ sơ có mốc
     "Bài kiểm tra".
   - V-d: sửa điểm danh một em → "Lịch sử sửa điểm danh" có dòng mới; lưu lại y hệt → không thêm dòng.
   - Luồng này CHƯA thêm spec e2e nào (`frontend/e2e/nghiem-thu/dong-NN.spec.ts` vẫn `—`).
4. **`scripts/do_axe.mjs`** + ảnh hai khổ trên: `/giang-day/bai-tap/<lớp>` (form giao bài), trang nhập điểm
   bài kiểm tra, `/giang-day/buoi-hoc/<lớp>` (Tạo buổi bù, Lịch sử sửa), `/bai-tap` (học viên),
   `/giang-day/bao-cao/<lớp>/<em>` (khối "Bài kiểm tra"), trang của tôi (thẻ lớp, điểm danh từng buổi).
5. Chạy lại trên Neon dev: `courses/tests_truy_cap.py` và 10 mô-đun cần bài thật đã nêu ở trên.
