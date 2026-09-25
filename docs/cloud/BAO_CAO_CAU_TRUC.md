# Báo cáo CẤU TRÚC — sổ miền + cấu trúc dữ liệu + cấu trúc mã (tự sinh, có cổng kiểm)

Nhánh `cloud/cau-truc-b` từ `origin/erp` `8bc4873` (đã có A1, A2, E1). Phiên cloud 25/09/2026, không CSDL.
Không đẩy erp / master.

## Commit

| Việc | Nội dung |
|---|---|
| 1–3 | `scripts/so_mien.json`, `scripts/cau_truc.py`, `docs/CAU_TRUC_DU_LIEU.md`, `docs/CAU_TRUC_MA.md`, bước f7 ở `.githooks/pre-push` |
| 4 | `CLAUDE.md` (49 dòng), `REVIEW.md` (29 dòng) |
| 6 | báo cáo này |

## Số đo (`python scripts/cau_truc.py --kiem`, mã 0)

- **16 miền**: 10 miền vận hành (lop_hoc, lich, diem_danh, bai_tap, chuong_trinh, bao_cao, phu_huynh, ho_so,
  yeu_cau, thong_bao) + 6 miền nền (tai_khoan, chung, hoc_truc_tuyen, dien_dan, thi_cu, cong_cu).
- **54 bảng** (52 ở `legacy_schema.sql`, 2 ở `mockexam_schema.sql`), **99 khoá ngoài**; 12 miền có bảng; 0 bảng
  không chủ. Chương trình nhận 7 bảng, gồm 3 bảng §70 (`session_logs`, `session_log_items`, `session_support`).
- **192 tệp backend** (.py, bỏ test / conftest / migrations), **180 tệp frontend** (`src/**/*.ts(x)`),
  11 tệp JS cũ; **0 tệp không miền, 0 tệp hoà giữa hai miền**.
- `cho_ghi` (được phép, có lý do): `users` ← ho_so (cột hồ sơ + cấp tài khoản); `classes.syllabus_version_id`
  và `class_sessions.syllabus_session_id / topic` ← chuong_trinh (gắn khung §64). `cong_cu` được ghi mọi bảng
  (dữ liệu trình diễn, chỉ chạy tay). thi_cu không cần `cho_ghi`: nó chỉ ghi bảng của chính nó.
- **Sổ nợ ghi chéo: 11 mục** (mỗi mục = tệp → bảng), lý do "có sẵn 25/09 — tách khi chạm: …":

| Miền ghi → miền chủ | Số | Tệp → bảng |
|---|---|---|
| tai_khoan → hoc_truc_tuyen | 2 | `accounts/views.py` → `roadmaps`, `surveys` (khảo sát đầu vào) |
| tai_khoan → dien_dan | 1 | `accounts/views.py` → `user_follows` |
| lich → diem_danh | 2 | `teaching/sessions.py` → `attendance`, `attendance_history` (tệp TRỘN) |
| lop_hoc → tai_khoan | 1 | `teaching/views.py` → `users` (đổi vai, đặt lại mật khẩu, tạo tài khoản) |
| phu_huynh → tai_khoan | 1 | `teaching/lien_he_phu_huynh.py` → `users` (cột liên hệ PH §47) |
| ho_so → lop_hoc | 1 | `teaching/admin_users.py` → `class_members` (nhập hàng loạt kèm xếp lớp) |
| hoc_truc_tuyen → tai_khoan | 1 | `stats/views.py` → `users` (thưởng nhiệm vụ cộng xp) |
| chung → tai_khoan | 1 | `common/streak.py` → `users` (streak / xp) |
| chung → hoc_truc_tuyen | 1 | `common/streak.py` → `user_daily_xp_logs` |

## Tự kiểm + đột biến

Tự kiểm chạy MỖI lượt `--kiem`: tệp giả `backend/teaching/moi_khong_mien.py` → BẮT ĐƯỢC; câu giả
`UPDATE classes` quét bằng CHÍNH bộ quét, gắn vào một tệp miền bai_tap → BẮT ĐƯỢC. Bỏ sót = "thước mù" → mã 1.

Đột biến tay (sửa, chạy `--kiem`, hoàn nguyên bằng `git checkout`):

| # | Đột biến | Kết quả |
|---|---|---|
| 1 | bỏ `term_holidays` khỏi sổ | mã 1 — "bảng `term_holidays` (§46) không miền nào sở hữu" (+ hai docs cũ) |
| 2 | thêm `x('UPDATE classes …')` vào `teaching/nhan_bai.py` | mã 1 — "GHI CHÉO MỚI: … (miền bai_tap) ghi bảng `classes` của miền lop_hoc (dòng 34)" |
| 3 | xoá mục nợ `sessions.py → attendance` | mã 1 — "GHI CHÉO MỚI: `teaching/sessions.py` (miền lich) ghi `attendance`" |
| 4 | thêm mục nợ giả `terms.py → users` | mã 1 — "NỢ ĐÃ HẾT … xoá mục ấy" |
| 5 | thêm `app/(standalone)/moi-thu/page.tsx` | mã 1 — "tệp … không thuộc miền nào" |

Hoàn nguyên xong: mã 0.

Thước khác: `node scripts/ban_do.mjs --kiem` mã 0 (469 nút, 0 gãy); `python scripts/tang_vai.py --kiem` mã 0
(36 trang, 0 lệch, tự kiểm 24); `cd backend && pip install -r requirements.txt && python -m ruff check .` sạch
(`scripts/cau_truc.py` cũng sạch theo cấu hình ruff của backend). Chạy tay cả `pre-push`: `✓ cấu trúc --kiem 1s`;
các bước đỏ khác do máy cloud (không `.env` → `manage.py check` / guard hỏng khi đọc settings; không
`frontend/node_modules`) — không liên quan thay đổi này.

## Cách thước làm việc (tóm)

- Lược đồ: `common.luoc_do_sql.doc_tat_ca` tách câu (không bộ tách thứ hai); `cau_truc.py` chỉ dịch từng câu
  CREATE TABLE / ALTER TABLE (ADD/DROP COLUMN, ADD/DROP CONSTRAINT, ALTER COLUMN) theo đúng thứ tự mục, đặt
  tên ràng buộc ngầm như Postgres (`<bảng>_<cột>_check`, `_fkey`, `_key`, `_pkey`) để `DROP CONSTRAINT` sau khớp.
- Ghi: duyệt AST từng tệp, mọi hằng chuỗi (bỏ chuỗi đứng riêng làm câu lệnh = docstring), từ khoá VIẾT HOA +
  tên bảng thường có trong lược đồ; bỏ `FOR UPDATE`, `DO UPDATE`.
- Glob: `*` / `**`, `[` `]` là chữ. Mẫu cụ thể nhất thắng (đường dẫn đủ > glob; rồi phần chữ dài hơn); hoà
  giữa hai miền = lỗi. Danh sách tệp lấy từ `git ls-files --cached --others --exclude-standard`.
- Docs cũ: sinh lại trong bộ nhớ rồi so, BỎ QUA số dòng (`\d+ dòng`) — sửa một tệp mã không làm cổng đỏ; thêm /
  dời tệp, đổi sổ, đổi lược đồ thì đỏ.
- f7 dùng `$PY`, rơi về `python3` / `python` khi không có venv (thước chỉ cần thư viện chuẩn).

## Tệp khó gán — đã chọn gì, vì sao

| Tệp | Chọn | Vì sao |
|---|---|---|
| `teaching/views.py` | lop_hoc (`tach_khi_cham`) | phần lớn là lớp + thành viên; phần users (vai, mật khẩu, tạo TK) thành nợ lop_hoc → tai_khoan |
| `teaching/sessions.py` | lich (`tach_khi_cham`) | tên + phần lớn là buổi; điểm danh thành 2 mục nợ lich → diem_danh |
| `giang-day/buoi-hoc/**/SessionsClient.tsx` | lich (`tach_khi_cham`) | cùng lý do; riêng `LichSuDiemDanh.tsx` → diem_danh |
| `teaching/danh_gia.py`, `NutCanHoTro.tsx`, `DanhGiaEm.tsx` | lop_hoc | nhận xét / cần hỗ trợ là cột của `class_members` — gán lop_hoc thì không sinh nợ |
| `teaching/lop_cua_toi.py`, `components/LopCuaToi*.tsx` | lop_hoc | màn HS chỉ đọc; trục là "lớp của em" |
| `teaching/bao_cao_pdf.py` | bao_cao | theo §4 (bộ dựng PDF chung với báo cáo lớp) dù nội dung là tờ phụ huynh — ghi `tach_khi_cham` |
| `teaching/vocab.py`, `urls.py`, `apps.py` | chung | từ vựng / tuyến dùng bởi nhiều miền teaching |
| `teaching/tinh_trang.py`, `tinh_thanh.py`, `MucTieuEm.tsx`, `quan-tri/tai-khoan/**` | ho_so | cột hồ sơ trên `users` |
| `common/streak.py` | chung | theo luật "common/ = chung"; thực chất là trò chơi hoá → 2 mục nợ, đề xuất dời sang hoc_truc_tuyen |
| `config/urls_thi_da_thao.py` | thi_cu | tuyến thi đã tháo, đi cùng miền đóng băng |
| `chuong_trinh/du_lieu_mau.py` | chuong_trinh | chỉ ghi bảng của chính miền; thư mục miền |
| `courseadmin/syllabus.py` | chuong_trinh | đường dẫn đủ thắng glob `courseadmin/**` của hoc_truc_tuyen |
| `components/KhuNhanSu.tsx`, `ChonDinhDang.tsx` | chung / bao_cao | trang nhân sự dùng chung; chọn định dạng tải = xuất báo cáo |

## Chưa / để lại

- Ghi qua ORM Django và câu có tên bảng động (`f'DELETE FROM {table} …'`) thước không thấy. Grep 25/09 (bỏ test):
  không có `.save()` / `objects.create` / `.update()` / `.delete()` ORM nào; tên bảng động có ở 2 chỗ —
  `common/luoc_do_sql.py` (bảng sổ `luoc_do_da_chay`, ngoài lược đồ) và `forum/views.py:120-123`
  (`post_likes` / `comment_likes`, cùng miền dien_dan) — nên hiện không sót ghi chéo nào.
- `common/management/commands/ve_erd.py` còn một bảng `MIEN` riêng (nguồn thứ hai, chia theo nhóm cũ) — nên đọc
  `scripts/so_mien.json` khi chạm.
- Bảng sắp có (outbox, announcements, yeu_cau*) chưa nằm trong sổ: thêm vào `bang` của miền cùng lúc thêm mục lược đồ
  (cổng sẽ đòi).
