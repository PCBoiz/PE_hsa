# Báo cáo E1 — khung chương trình theo buổi + sổ đầu bài + tiến độ

Nhánh `agent/e1`, phiên cloud 25/09/2026 (Postgres 16 cục bộ, không Neon). Đã gộp `origin/erp`
(`0544692`, gồm vá token cùng giây + thước sổ lược đồ) — lần gộp cuối: "Already up to date".
Không đẩy erp / master.

## Commit (theo thứ tự)

| Hash | Nội dung |
|---|---|
| `42b5c86` | WIP E1 (agent cục bộ) — tạm dừng vì trùng 3f47421 |
| `8e09dcf` | gộp erp f0b55a0 (khung §64 của Nhân, A1 §62) |
| `f281cf0` | dựng trên §64: chuỗi phiên bản, trọng số > 0, sổ đầu bài §70, nhận khung mới |
| `7107ef3` | WIP bàn giao sang cloud (test viết, chưa chạy) |
| `4f3ddad` | gộp origin/erp (vá token cùng giây, thước sổ lược đồ) |
| `7be6b2a` | tiến độ ở Tổng quan / danh sách lớp / Lớp của tôi / tờ phụ huynh + test sổ đầu bài |
| `1b6ef6c` | khung mẫu 24 buổi `hsa_quantitative` + sổ mẫu trong bộ dữ liệu trình diễn |
| `c257a4b` | mục lục khung cho màn soạn (học vụ đọc được), câu lỗi chữ người dùng, bảng quyền |
| `2b8b96b` | giao diện: soạn khung, Chương trình lớp, Sổ đầu bài, chip, ô Tổng quan, %, tờ phụ huynh |
| `ab4d9b0` | spec e2e `chuong-trinh.spec.ts`; fieldset sổ đầu bài |
| `4dd5e93` | bộ đột biến `scripts/dot_bien_e1.py` 30/30; vá hai phép kiểm |
| `6042f01` | ô Tổng quan tách hàng riêng (axe) |
| `c902bb9` | `docs/NGHIEM_THU_TOPHSA.md` các ô E1 |

## Xong

- **Lược đồ** (của phiên trước, `f281cf0`): §64 sửa tại chỗ (§64g chuỗi phiên bản `lineage_id` + hai chỉ
  mục duy nhất một phần, `is_demo`; §64h trọng số NOT NULL DEFAULT 1 CHECK > 0), §70 sổ đầu bài
  (`session_logs`, `session_log_items`, `session_support`). Giữ `syllabus_materials`. Không DDL mới
  trong phiên này. `bootstrap_schema` ×2 → lượt 2: 0/63 mục; `kiem_luoc_do` 62/62.
- **Backend** `backend/chuong_trinh/`: `dich_vu.py` (`nhan_khung`, `tien_do_lop`, `tien_do_em`),
  `tien_do.py` (1 câu cho mọi số lớp, +1 khi kèm danh sách buổi chưa ghi), `lop.py` (GET chương trình
  lớp, PUT nhận khung = tuyến DUY NHẤT `api/admin/classes/<id>/chuong-trinh`, PATCH gắn tay), `so_dau_bai.py`,
  `khung.py` (MỚI: `GET api/admin/chuong-trinh/khung` — mục lục môn + phiên bản, `IsCurriculumPlanner`,
  vì học vụ không đọc được `api/admin/courses`), `du_lieu_mau.py` (MỚI).
- **Buổi bù tính cho buổi gốc**: erp đã có `class_sessions.makeup_for` (§62e của A1) nên luật được
  code thật (không TODO) — `tests_tien_do.py::test_buoi_bu_tinh_cho_buoi_goc`; nhận khung bỏ qua buổi bù.
- **Nối vào miền khác** (chỉ gọi `dich_vu`, khoá `chuongTrinh` tuỳ chọn): Tổng quan (khối + từng lớp,
  vẫn ≤ 9 câu), danh sách lớp (chip), Lớp của tôi (`chuongTrinh.pct`), tờ phụ huynh.
- **Giao diện**: `/giao-trinh/khung-chuong-trinh` (admin + học vụ + biên tập), `/giang-day/chuong-trinh/<lớp>`,
  `/giang-day/so-dau-bai/<buổi>`; nút "Chương trình" + chip ở Lớp học; nút "Sổ đầu bài" từng buổi và
  liên kết "Chương trình & tiến độ" ở Buổi học; ô "Tiến độ chương trình" ở Toàn trung tâm; dòng % ở
  Lớp của tôi và tờ phụ huynh. Thẻ "Khung chương trình" ở khu làm việc (cổng `IsCurriculumPlanner`).
- **Dữ liệu mẫu**: khung "Luyện Toán HSA 24 buổi (khung mẫu)" `is_demo`, lớp mẫu HSA-MAU-01 nhận khung qua
  `nhan_khung`, buổi đã dạy có sổ (buổi gần nhất cố ý chưa ghi, buổi kề trước một phần). `go()` gỡ khung.
- **Tài liệu / bảng**: `quyenVai.ts` (+`IsCurriculumPlanner`, 3 việc), `huongDan.ts` (2 bài),
  `NGHIEM_THU_TOPHSA.md` dòng 4, 5, 6, 9, 15, 16, 28; `ban_do.mjs` xoá 9 dòng lý do tạm (+1 dòng chú thích).
  Nhãn Nhật ký cho `syllabus.*`, `class.syllabus.assign`, `session.syllabus`, `session.log` đã có.

## Chưa / để lại

- Bài tập giao cho lớp chưa trỏ về mục khung (dòng 5 "Gắn bài tập" vẫn MỘT PHẦN).
- Ô "Đề xuất" là chữ tự do — E3 biến nó thành Yêu cầu (không dựng E3).
- Sửa trọng số / tên một nội dung ĐÃ thêm: API có (`PUT syllabus-items`), màn chỉ có thêm / xoá.
- Việc hôm nay chưa liệt kê "buổi đã dạy chưa ghi sổ" (`tien_do_lop(kem_buoi=True)` đã sẵn).

## Số đo THẬT (máy cloud)

- pytest `chuong_trinh` + `courseadmin/tests_syllabus.py`: **76/76 xanh** (57 + 19). Test mới phiên này:
  `tests_so_dau_bai.py` 14, `tests_noi_vao.py` 6, `tests_khung_chuoi.py` +2, `tests_tien_do.py` +1,
  `tests_nhan_khung.py` +1 khẳng định. Test mới tự dựng dữ liệu, không dựa bảng `lessons`.
- Module đã chạm chạy riêng: `common` 165/165, `tests_tong_quan` 11, `tests_danh_sach_lop` 9,
  `tests_lop_cua_toi` 10, `tests_parent_link` 21, `tests_quyen_bao_cao_phu_huynh` 3, `tests_bao_cao_pdf` 21,
  `tests_luong_erp` 5, `tests_viec_hom_nay` 11 — xanh. **Đỏ vì môi trường**: `teaching/tests.py` 25,
  `courseadmin/tests_thu_tu_bai.py` 3, `teaching/tests_du_lieu_mau.py` 2 — cùng 30 test đỏ y hệt khi chạy
  `origin/erp` gốc trên cùng CSDL (bảng `lessons` trống: "khoá này chưa chia chủ đề", thứ tự bài).
- Đột biến `python scripts/dot_bien_e1.py`: nền xanh, **30/30 bị giết** (lượt đầu 28/30 — hai đột biến
  sống đã giết bằng phép kiểm mới, xem `4dd5e93`). Gồm: ≥→> và 0,8→0,7 ở ngưỡng chậm, một phần 0,5,
  % chỉ có mặt/muộn, `chuaGhiSo`, MAX không SUM, buổi bù, bỏ buổi huỷ, không đè gắn tay, chỉ điền tên
  trống, 409 bản đã xuất bản, ngừng bản cũ khi xuất bản, không xoá bản đang dùng, nhân bản đủ cây,
  trọng số > 0, `can_see_class` (sổ + gắn tay), 409 buổi chưa diễn ra, 409 ghi đè, học vụ soạn được,
  bốn điểm nối, dữ liệu mẫu.
- Frontend: `tsc --noEmit` sạch; eslint tệp đã sửa sạch; **35/35** `e2e/unit`; `ban_do.mjs --kiem` 0 gãy
  (0 tuyến không ai gọi chưa có lý do); `tang_vai.py --kiem` 0 lệch — chạy bản chép đổi `\` → `/` vì
  script gốc chỉ chạy trên Windows (không commit bản chép); `next build --webpack` xanh.
- Chạy thật (Django 9151 + `next start` 3251 + dữ liệu mẫu): 12 màn × 2 khổ không lỗi console, không
  tràn ngang; ảnh chụp đã xem. **axe 0 vi phạm** trên 8 màn × {1366, 390} × {sáng, tối} (lượt đầu 2 —
  đã sửa ở `6042f01`). **e2e `chuong-trinh.spec.ts` 4/4 xanh** (may-tinh + dien-thoai, `E2E_GHI=1`) bằng
  tài khoản CỤC BỘ; sau lượt chạy: 0 lớp, 0 khung "E2E tự dọn khung" còn lại.

## Hunk ở tệp dùng chung

| Tệp | Hunk |
|---|---|
| `backend/teaching/overview.py` | +1 import, khối `chuongTrinh` sau khối tài khoản ngủ, khoá `chuongTrinh` ở phản hồi |
| `backend/teaching/reports.py` | +1 import, 4 dòng trong `class_page` (chip lớp trên trang), docstring +1 dòng |
| `backend/teaching/lop_cua_toi.py` | +1 import, 2 dòng gọi `tien_do_em`, 1 khoá `chuongTrinh` (A1 cũng sửa tệp này) |
| `backend/teaching/parent_report.py` | +1 import, 1 khoá `chuongTrinh` trong `dung_bao_cao` |
| `backend/teaching/du_lieu_mau.py` | +1 import, 1 lời gọi trong `tao()`, 2 dòng `dem()`, 1 dòng `go()` |
| `backend/courseadmin/syllabus.py` | (phiên trước) luật chuỗi/xuất bản/nhân bản; (phiên này) câu lỗi chữ người dùng |
| `backend/common/permissions.py`, `audit.py`, `tests_ma_tran_quyen.py`, `config/*`, `kiem_luoc_do.py`, `sql/legacy_schema.sql` | phiên trước — xem `f281cf0` |
| `frontend/.../buoi-hoc/[classId]/SessionsClient.tsx` | import `Link`; nút "Sổ đầu bài" từng buổi; nhãn ô `note` "Sổ đầu bài" → "Tình hình lớp" |
| `frontend/.../buoi-hoc/[classId]/page.tsx` | 1 liên kết "Chương trình & tiến độ" |
| `frontend/.../quan-tri/lop-hoc/{LopHocClient.tsx,lop.ts,page.tsx}` | chip + nút "Chương trình"; kiểu + hình dạng `chuongTrinh` |
| `frontend/.../quan-tri/tong-quan/{TheTongQuan.tsx,page.tsx}` | thẻ `TheChuongTrinh`, hình dạng, nhãn thiếu |
| `frontend/src/components/{LopCuaToi,LopCuaToiNguon,ToBaoCao}.tsx`, `lib/hinhDang.ts` | dòng % / khối tiến độ + hình dạng |
| `frontend/src/lib/{khuTheoVai,quyenVai}.ts`, `e2e/unit/{khu-theo-vai,quyen-vai}.test.mjs` | thẻ + lớp quyền mới; phép kiểm đối chiếu `DUOC_VAO` của trang khung (chứng minh đỏ khi bỏ học vụ) |
| `scripts/ban_do.mjs` | xoá 10 dòng (9 lý do tạm + chú thích) |

## Việc lead phải làm khi gộp

1. `git merge agent/e1` vào erp; trên Neon dev: `bootstrap_schema` ×2 + `kiem_luoc_do` (§64g/h, §70 — đã
   áp ở phiên cục bộ trước theo `f281cf0`; lượt này để xác nhận 0 mục).
2. **Chạy e2e bằng tài khoản rà soát** (không có trên cloud):
   `E2E_GHI=1 npx playwright test -c e2e/playwright.config.ts chuong-trinh` — hai khổ; spec tự dọn lớp +
   khung "E2E tự dọn khung …". Và `node scripts/do_axe.mjs` (nên thêm ba màn mới vào `TRANG` với lớp
   7322 / một buổi của nó — chưa thêm vì id buổi phụ thuộc CSDL dev).
3. Chạy lại pytest các module ở bảng trên trên Neon (một module một lượt) — đặc biệt `teaching/tests.py`,
   `tests_du_lieu_mau.py`, `tests_thu_tu_bai.py` mà máy cloud không đo được vì thiếu bài học.
4. A1 cùng sửa `lop_cua_toi.py` — xung đột (nếu có) chỉ ở 3 dòng import / gọi `tien_do_em` / khoá `chuongTrinh`.
5. Dữ liệu mẫu trên dev: `python manage.py du_lieu_mau --lam-moi` để có khung + sổ mẫu cho buổi trình diễn.
6. `scripts/tang_vai.py` chỉ chạy trên Windows (đường dẫn `r'frontend\src\app'`) — nếu muốn chạy trên
   cloud/CI thì đổi sang `os.path.join` từng phần (chưa đổi vì ngoài phạm vi E1).
