# Báo cáo luồng A2 — vận hành lớp (V-i, V-j, V-k, V-m, V-n, V-o)

Nhánh `agent/luong-a2`, phiên cloud 25/09/2026, nối tiếp WIP `6539306` của agent cục bộ.
Môi trường đo: Postgres 16 CỤC BỘ trong container (không phải Neon dev), bảng `lessons` trống.
Mọi con số dưới đây ĐO trong phiên này, trừ chỗ ghi rõ "theo commit".

## Commit

| Hash | Nội dung |
|---|---|
| `cde836a` | V-i trạng thái khoá Đang mở / Nháp (phiên cục bộ) |
| `def7bc0` | V-k xuất Excel + bộ lọc (phiên cục bộ) |
| `139aed0` | V-j nhập học viên từ tệp mẫu (phiên cục bộ) |
| `0421225`, `fee6656`, `d788d8c`, `6539306` | WIP V-m/V-n/V-o + gộp erp f0b55a0 (phiên cục bộ) |
| `2b1a23a` | gộp `origin/erp` 0544692 |
| `d65f6e9` | V-m hoàn tất |
| `e58cf8a` | V-n hoàn tất (+ vá: sửa / huỷ buổi trước đó không hiện) |
| `3fb785f` | V-o hoàn tất |
| `7beb3c3` | §63: đổi nhãn học phí cũ → mã trước khi khai CHECK mới; ma trận dòng 3, 7 |

## Từng mục

| Mục | Trạng thái | Test (đo phiên này) | Đỏ trước | Đột biến |
|---|---|---|---|---|
| V-i | xong | `courses/tests_khoa_nhap.py` 3/3 xanh | 3/3 (theo commit) | 10/10 (theo commit, không chạy lại) |
| V-j | xong | `teaching/tests_nhap_hoc_vien.py` 7/7 xanh | có (theo commit) | 15/15 (theo commit, không chạy lại) |
| V-k | xong | `teaching/tests_xuat_excel.py` 5/5 xanh | 4/5 (theo commit) | 18/18 (theo commit, không chạy lại) |
| V-m | xong | `teaching/tests_tinh_trang_hoc_vien.py` 7/7 xanh; `tests_ho_so_hoc_vien.py` 40 xanh | 6/6 (cài đặt trả về bản erp) + 1/1 (test §63 với §63 cũ) | 18/18 + 3/3 (câu đổi nhãn §63) |
| V-n | xong | `teaching/tests_lich_su_lop.py` 2/2 xanh | truy vấn cũ 1/2 đỏ, không mô-đun 2/2 đỏ | 12/12 |
| V-o | xong | `teaching/tests_cham_cong.py` 5/5 xanh | 5/5 (không có mô-đun) | 23/23 |

Đột biến chạy bằng bộ chạy tự viết trong scratchpad (tệp `dot_bien.py` gốc ở máy Windows không có
trên cloud): mỗi đột biến thay một chuỗi xuất hiện đúng một lần, nền xanh, mỗi đột biến mã thoát 1.
Đột biến sống đã xử lý: V-m "lọc chưa đặt học phí bỏ `chi_hoc_vien`" (test thêm quản trị viên);
V-n "bỏ nhánh `detail.class_id`" (test thêm tạo + xoá buổi); V-o "tháng sau = +31 ngày" (test tháng 2)
và "UNION ALL" (đột biến viết lần đầu là tương đương — thay bằng bản thật, test trợ giảng đứng lớp).

Kiểm khác (phiên này): `common/tests_ma_tran_quyen.py` 2/2, `common/tests.py` 41/41,
`common/tests_luoc_do_muc.py` 40/40, `common/tests_luoc_do_csdl.py` 14/14; `ruff check` sạch;
`npx tsc --noEmit` sạch; eslint trên các tệp đã sửa sạch; mọi `frontend/e2e/unit/*.test.mjs` xanh;
`node scripts/ban_do.mjs --kiem` 0 gãy; `tang_vai.py --kiem` 0 lệch chưa giải thích (chạy bằng một bản
chép sửa đường dẫn `\` → `/` — tệp gốc chỉ chạy trên Windows); `npx next build --webpack` thoát 0.
Bootstrap ×2: lượt đầu 4/63 mục (§63 đổi), lượt hai 0/63; `kiem_luoc_do` 58/58.

Toàn bộ pytest (CSDL cục bộ, riêng phiên này nên chạy cả bộ được): nhánh 70 đỏ / 1061 xanh / 4 bỏ qua;
`origin/erp` cùng CSDL 72 đỏ. 70 đỏ của nhánh ⊂ 72 đỏ của erp (thiếu bài trong `lessons` v.v. — môi
trường). Hai đỏ chỉ ở erp: `tests_ho_so_hoc_vien::test_hoc_vu_sua_tinh_trang_hoc_phi` (erp ghi NHÃN,
CSDL đã mang CHECK MÃ — đúng dự kiến) và một dòng log IntegrityError đi kèm.

Giao diện: dựng Django + Next cục bộ, dữ liệu demo qua view thật, chụp + axe-core 4.10.3 trên 6 trang
(chấm công, hồ sơ ×2 gồm em có tỉnh ghi tay, tài khoản lọc tình trạng, giáo trình, lớp học + mở
"Lịch sử thay đổi") × 390 / 1440: axe 0 vi phạm, không tràn ngang, 12/12 lượt. Đã xem ảnh.

## Việc đã sửa trong phiên này (ngoài hoàn tất WIP)

- **V-n thiếu sửa / huỷ buổi**: `session.update` không ghi lớp vào `detail` (`teaching/sessions.py`,
  tệp A1). Không sửa tệp A1 — `lich_su_lop.py` nhận dòng buổi qua `detail.class_id` HOẶC id buổi thuộc lớp.
- **Rủi ro gộp §63**: erp tới 0544692 lưu NHÃN học phí. CSDL nào đã có người chọn học phí qua bản đó sẽ
  làm `ADD CONSTRAINT` bản mã hỏng → cả lượt bootstrap đổ. Thêm một UPDATE có chặn giữa DROP và ADD.
- Trang Chấm công dùng `Field`/`Button` của `@/components/ui`; lịch sử lớp dùng `lucVN`; nhãn lùi "Bảo lưu" ở hồ sơ.

## Hunk ở tệp dùng chung / tệp của luồng khác

- `backend/teaching/dong_thoi_gian.py` (A1): một dòng nhãn `'tuition_status': 'tình trạng học phí'`.
- `frontend/.../buoi-hoc/[classId]/SessionsClient.tsx`: hộp "Tải bảng tính" thay hai liên kết CSV (V-k).
- `frontend/.../quan-tri/lop-hoc/LopHocClient.tsx`: gắn `NhapTuTep` (V-j) + `LichSuLop` (V-n).
- `frontend/.../quan-tri/vai.ts`: thêm tab Chấm công.
- `backend/sql/legacy_schema.sql` §63 SỬA TẠI CHỖ (CHECK lưu mã + câu đổi nhãn) — mục đổi nên §63 và MỌI
  mục sau (§64, §69, mockexam nền) chạy lại ở lượt bootstrap đầu tiên trên mỗi CSDL.
- `backend/common/audit.py` (`CLASS_MEMBER_IMPORT`), `common/bangtinh.py` (`ghi_xlsx`),
  `mockexam/quan_tri.py` (gọi `ghi_xlsx`), `teaching/admin_users.py` (`cap_tai_khoan` tách ra + lọc V-k/V-m),
  `src/lib/viecNhatKy.ts` (bảng nhãn nhật ký dời từ trang Nhật ký), `quyenVai.ts`, `huongDan.ts`.

## Mâu thuẫn với brief

- Brief nói §69a cho học phí; theo quyết định lead, học phí nằm ở §63 (sửa tại chỗ), §69 chỉ còn §69b.
- Brief giả định `detail` lưu id lớp cho mọi dòng buổi học — sai với `session.update` (xem trên).
- `scripts/do_axe.mjs` nạp axe từ jsdelivr — proxy cloud chặn; đã dùng axe-core qua `npm pack`.

## Việc lead phải làm khi gộp

1. Chạy e2e với `E2E_GHI=1` trên hai project: `frontend/e2e/van-hanh-a2.spec.ts` (mới),
   `ho-so-hoc-vien.spec.ts`, `danh-sach-hoc-vien.spec.ts`, `vai-tro-cong.spec.ts` — phiên cloud KHÔNG chạy
   được (không có tài khoản audit2009).
2. `scripts/do_axe.mjs` đủ bộ trên máy có jsdelivr.
3. Deploy: lượt bootstrap đầu chạy lại §63 → cuối tệp; câu UPDATE đổi mọi nhãn học phí cũ sang mã. Sau
   đó `kiem_luoc_do` (dòng §63b kiểm CHECK nhận `bao_luu`).
4. Chạy pytest đủ bộ trên CSDL có bài (ở đây `lessons` trống nên 70 phép kiểm đỏ vì môi trường).
5. Ma trận nghiệm thu: cột Spec để lead điền; dòng 3 ghi "chờ e2e".
