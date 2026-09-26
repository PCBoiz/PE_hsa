# Cấu trúc mã theo miền

> **Sinh tự động — đừng sửa tay.** Sinh lại: `python scripts/cau_truc.py` (sau khi sửa `scripts/so_mien.json`, lược đồ `backend/sql/*.sql` hay thêm / dời tệp). Cổng pre-push `python scripts/cau_truc.py --kiem` đỏ khi tệp này cũ.

16 miền · 200 tệp backend · 180 tệp frontend (src) · 11 tệp JS cũ · 11 mục nợ ghi chéo. Mỗi tệp thuộc đúng MỘT miền (glob cụ thể nhất trong `scripts/so_mien.json` thắng). Cột "ghi bảng" = câu `INSERT/UPDATE/DELETE/TRUNCATE` trong chuỗi SQL của tệp; *nghiêng* = ghi bảng miền khác. Số dòng đo lúc sinh, không làm cổng đỏ khi lệch.

## Đặt mã mới ở đâu

1. Tìm miền theo VIỆC (bảng dưới). Miền đã có thư mục riêng (`backend/chuong_trinh/`) → đặt vào đó. Miền còn nằm trong `teaching/` → tệp MỚI đặt ở `backend/<miền>/` (glob đã chờ sẵn); chỉ sửa tệp cũ tại chỗ.
2. Không `INSERT/UPDATE/DELETE` bảng của miền khác — gọi hàm dịch vụ của miền ấy (vd `chuong_trinh.dich_vu`). Cần thật thì thêm `cho_ghi` ở miền CHỦ bảng, kèm lý do, trong cùng commit.
3. Bảng mới: thêm vào `bang` của miền sở hữu trong `so_mien.json` cùng lúc thêm mục lược đồ.
4. Tệp mới không khớp glob nào → cổng đỏ: thêm glob (hoặc đường dẫn đủ) vào miền của nó.
5. Tệp cũ TRỘN (`tach_khi_cham`): tách phần của miền khác khi đang sửa chính chỗ ấy; mỗi lần tách, mục nợ tương ứng biến mất → xoá nó khỏi `no_ghi_cheo` (cổng đòi).
6. Việc phụ (thông báo, nhật ký) đi SAU commit qua `notifications.gui` / `gui_sau_commit`.
7. Sửa xong: `python scripts/cau_truc.py` rồi commit hai tệp docs sinh ra.

| Miền | Việc | Bảng | Backend | Frontend (src + JS cũ) |
|---|---|---|---|---|
| [lop_hoc](#lop_hoc) | Lớp học | 4 | 9 tệp · 2357 dòng | 18 tệp · 3643 dòng |
| [lich](#lich) | Lịch & buổi học | 2 | 7 tệp · 1868 dòng | 7 tệp · 2205 dòng |
| [diem_danh](#diem_danh) | Điểm danh | 2 | 1 tệp · 96 dòng | 1 tệp · 81 dòng |
| [bai_tap](#bai_tap) | Bài tập & kiểm tra | 3 | 2 tệp · 1058 dòng | 7 tệp · 1688 dòng |
| [chuong_trinh](#chuong_trinh) | Chương trình (E1) | 7 | 11 tệp · 1803 dòng | 8 tệp · 1396 dòng |
| [bao_cao](#bao_cao) | Báo cáo | 0 | 8 tệp · 3968 dòng | 14 tệp · 2506 dòng |
| [phu_huynh](#phu_huynh) | Phụ huynh | 3 | 5 tệp · 1838 dòng | 10 tệp · 1789 dòng |
| [ho_so](#ho_so) | Hồ sơ học viên | 0 | 5 tệp · 1849 dòng | 11 tệp · 2494 dòng |
| [yeu_cau](#yeu_cau) | Yêu cầu | 2 | 7 tệp · 1450 dòng | 0 tệp · 0 dòng |
| [thong_bao](#thong_bao) | Thông báo | 2 | 8 tệp · 405 dòng | 0 tệp · 0 dòng |
| [tai_khoan](#tai_khoan) | Tài khoản | 2 | 12 tệp · 1597 dòng | 14 tệp · 1432 dòng |
| [chung](#chung) | Chung (hạt nhân) | 2 | 43 tệp · 6217 dòng | 67 tệp · 6793 dòng |
| [hoc_truc_tuyen](#hoc_truc_tuyen) | Học trực tuyến | 19 | 64 tệp · 8617 dòng | 34 tệp · 13773 dòng |
| [dien_dan](#dien_dan) | Diễn đàn | 5 | 5 tệp · 525 dòng | 0 tệp · 0 dòng |
| [thi_cu](#thi_cu) | Thi thử (ĐÓNG BĂNG) | 3 | 10 tệp · 1718 dòng | 0 tệp · 0 dòng |
| [cong_cu](#cong_cu) | Công cụ dữ liệu mẫu | 0 | 3 tệp · 1170 dòng | 0 tệp · 0 dòng |

## Sổ nợ ghi chéo (chỉ được co)

Vi phạm có sẵn ngày dựng sổ. Mục nào hết xảy ra thì cổng đỏ cho tới khi xoá nó; vi phạm MỚI không được thêm vào đây — dùng hàm dịch vụ, hoặc `cho_ghi` có lý do.

| Miền ghi → miền chủ | Tệp | Bảng | Lý do |
|---|---|---|---|
| chung → hoc_truc_tuyen | `backend/common/streak.py` | `user_daily_xp_logs` | có sẵn 25/09 — tách khi chạm: streak / XP là trò chơi hoá của học trực tuyến mà nằm ở common/ — dời tệp sang miền hoc_truc_tuyen |
| chung → tai_khoan | `backend/common/streak.py` | `users` | có sẵn 25/09 — tách khi chạm: cột streak / xp / gems trên users — dời tệp sang hoc_truc_tuyen rồi xin `cho_ghi` cột trò chơi hoá |
| ho_so → lop_hoc | `backend/teaching/admin_users.py` | `class_members` | có sẵn 25/09 — tách khi chạm: nhập tài khoản hàng loạt kèm xếp lớp — gọi dịch vụ xếp lớp của lop_hoc |
| hoc_truc_tuyen → tai_khoan | `backend/stats/views.py` | `users` | có sẵn 25/09 — tách khi chạm: nhận thưởng nhiệm vụ cộng xp / gems thẳng vào users — gọi `common.streak.award_xp` thay vì lặp câu |
| lich → diem_danh | `backend/teaching/sessions.py` | `attendance` | có sẵn 25/09 — tách khi chạm: tệp TRỘN buổi + điểm danh — tách `SessionAttendanceView` sang miền diem_danh |
| lich → diem_danh | `backend/teaching/sessions.py` | `attendance_history` | có sẵn 25/09 — tách khi chạm: tệp TRỘN buổi + điểm danh — tách cùng `SessionAttendanceView` |
| lop_hoc → tai_khoan | `backend/teaching/views.py` | `users` | có sẵn 25/09 — tách khi chạm: tệp TRỘN: đổi vai / đặt lại mật khẩu / tạo tài khoản nằm ở views lớp — tách sang ho_so / accounts |
| phu_huynh → tai_khoan | `backend/teaching/lien_he_phu_huynh.py` | `users` | có sẵn 25/09 — tách khi chạm: cột liên hệ phụ huynh trên users (§47) — đưa vào dịch vụ hồ sơ (ho_so) |
| tai_khoan → dien_dan | `backend/accounts/views.py` | `user_follows` | có sẵn 25/09 — tách khi chạm: theo dõi người dùng nằm ở accounts — dời view sang forum/ |
| tai_khoan → hoc_truc_tuyen | `backend/accounts/views.py` | `roadmaps` | có sẵn 25/09 — tách khi chạm: đăng ký / khảo sát đầu vào sinh lộ trình mặc định `u<id>_generated` — chuyển thành hàm dịch vụ của roadmap |
| tai_khoan → hoc_truc_tuyen | `backend/accounts/views.py` | `surveys` | có sẵn 25/09 — tách khi chạm: lưu khảo sát đầu vào ngay trong luồng tài khoản — chuyển thành hàm dịch vụ của stats/roadmap |

## lop_hoc

**Lớp học** — Lớp, thành viên lớp (xếp lớp, chuyển lớp, rời lớp, nhận xét từng em), đợt học và ngày nghỉ của đợt, lớp gia sư.

- Bảng sở hữu: `classes`, `class_members`, `terms`, `term_holidays`
- Miền khác được ghi bảng của miền này: chuong_trinh ghi `classes` — cột gắn khung `classes.syllabus_version_id` (§64) — chỉ `chuong_trinh.dich_vu.nhan_khung` ghi, trong cùng giao dịch gắn buổi; cong_cu (mọi bảng) — dựng / gỡ dữ liệu trình diễn phải chạm mọi miền một lượt; chỉ chạy tay (lệnh quản trị), không nằm trên đường phục vụ người dùng; *nợ*: `backend/teaching/admin_users.py` ghi `class_members`
- Glob: `backend/teaching/views.py`, `backend/teaching/chuyen_lop.py`, `backend/teaching/roi_lop.py`, `backend/teaching/lop_gia_su.py`, `backend/teaching/terms.py`, `backend/teaching/nhap_hoc_vien.py`, `backend/teaching/lich_su_lop.py`, `backend/teaching/danh_gia.py`, `backend/teaching/lop_cua_toi.py`, `backend/lop_hoc/**/*.py`, `frontend/src/app/(standalone)/quan-tri/lop-hoc/**`, `frontend/src/app/(standalone)/quan-tri/dot-hoc/**`, `frontend/src/app/(standalone)/giang-day/NutCanHoTro.tsx`, `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/[userId]/DanhGiaEm.tsx`, `frontend/src/components/LopCuaToi*.tsx`
- Tách khi chạm — `backend/teaching/views.py`: TRỘN: lớp + thành viên (lop_hoc) với tạo tài khoản / đổi vai / đặt lại mật khẩu (tai_khoan, ho_so) và hồ sơ học viên cho GV (bao_cao). Tách phần users sang ho_so khi chạm.
- Tách khi chạm — `backend/teaching/lop_cua_toi.py`: màn học viên CHỈ ĐỌC gom lớp + buổi + chuyên cần + tiến độ; để ở lop_hoc vì trục là 'lớp của em'.

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/teaching/chuyen_lop.py` | 155 dòng | `class_members` |
| `backend/teaching/danh_gia.py` | 181 dòng | `class_members` |
| `backend/teaching/lich_su_lop.py` | 63 dòng | — |
| `backend/teaching/lop_cua_toi.py` | 179 dòng | — |
| `backend/teaching/lop_gia_su.py` | 122 dòng | `classes` |
| `backend/teaching/nhap_hoc_vien.py` | 242 dòng | — |
| `backend/teaching/roi_lop.py` | 54 dòng | `class_members` |
| `backend/teaching/terms.py` | 357 dòng | `term_holidays`, `terms` |
| `backend/teaching/views.py` | 1004 dòng | `class_members`, `classes`, *`users`* |

| Tệp frontend | Dòng |
|---|---|
| `frontend/src/app/(standalone)/giang-day/NutCanHoTro.tsx` | 103 dòng |
| `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/[userId]/DanhGiaEm.tsx` | 192 dòng |
| `frontend/src/app/(standalone)/quan-tri/dot-hoc/NgayNghiDot.tsx` | 231 dòng |
| `frontend/src/app/(standalone)/quan-tri/dot-hoc/TermsClient.tsx` | 339 dòng |
| `frontend/src/app/(standalone)/quan-tri/dot-hoc/layout.tsx` | 26 dòng |
| `frontend/src/app/(standalone)/quan-tri/dot-hoc/page.tsx` | 37 dòng |
| `frontend/src/app/(standalone)/quan-tri/lop-hoc/BoLocLop.tsx` | 146 dòng |
| `frontend/src/app/(standalone)/quan-tri/lop-hoc/ChuyenLop.tsx` | 146 dòng |
| `frontend/src/app/(standalone)/quan-tri/lop-hoc/LichSuLop.tsx` | 116 dòng |
| `frontend/src/app/(standalone)/quan-tri/lop-hoc/LopHocClient.tsx` | 962 dòng |
| `frontend/src/app/(standalone)/quan-tri/lop-hoc/NhapTuTep.tsx` | 216 dòng |
| `frontend/src/app/(standalone)/quan-tri/lop-hoc/TaoLopGiaSu.tsx` | 263 dòng |
| `frontend/src/app/(standalone)/quan-tri/lop-hoc/giaSu.ts` | 94 dòng |
| `frontend/src/app/(standalone)/quan-tri/lop-hoc/lop.ts` | 219 dòng |
| `frontend/src/app/(standalone)/quan-tri/lop-hoc/page.tsx` | 147 dòng |
| `frontend/src/components/LopCuaToi.tsx` | 296 dòng |
| `frontend/src/components/LopCuaToiKhung.tsx` | 44 dòng |
| `frontend/src/components/LopCuaToiNguon.tsx` | 66 dòng |

## lich

**Lịch & buổi học** — Buổi học (tạo, sửa, huỷ, sinh hàng loạt, buổi bù), người thuộc buổi, trùng lịch, lịch gộp, ngày lễ gợi ý.

- Bảng sở hữu: `class_sessions`, `session_participants`
- Miền khác được ghi bảng của miền này: chuong_trinh ghi `class_sessions` — cột gắn khung `class_sessions.syllabus_session_id` + điền `topic` còn trống khi nhận khung (§64) — chỉ `chuong_trinh` ghi, qua `dich_vu` / gắn tay ở `lop.py`; cong_cu (mọi bảng) — dựng / gỡ dữ liệu trình diễn phải chạm mọi miền một lượt; chỉ chạy tay (lệnh quản trị), không nằm trên đường phục vụ người dùng
- Glob: `backend/teaching/sessions.py`, `backend/teaching/sinh_buoi.py`, `backend/teaching/trung_lich.py`, `backend/teaching/lich.py`, `backend/teaching/ngay_le.py`, `backend/teaching/buoi_bu.py`, `backend/teaching/nguoi_buoi.py`, `backend/lich/**/*.py`, `frontend/src/app/(standalone)/giang-day/lich/**`, `frontend/src/app/(standalone)/giang-day/buoi-hoc/**`, `frontend/src/lib/noiHoc.ts`
- Tách khi chạm — `backend/teaching/sessions.py`: TRỘN: buổi (lich) + điểm danh + lịch sử điểm danh (diem_danh). Tách `SessionAttendanceView`, `SessionAttendanceHistoryView` sang diem_danh khi chạm.
- Tách khi chạm — `frontend/src/app/(standalone)/giang-day/buoi-hoc/[classId]/SessionsClient.tsx`: TRỘN: danh sách buổi + bảng điểm danh; tách phần điểm danh khi chạm.

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/teaching/buoi_bu.py` | 134 dòng | `class_sessions`, `session_participants` |
| `backend/teaching/lich.py` | 117 dòng | — |
| `backend/teaching/ngay_le.py` | 37 dòng | — |
| `backend/teaching/nguoi_buoi.py` | 20 dòng | — |
| `backend/teaching/sessions.py` | 1059 dòng | *`attendance`*, *`attendance_history`*, `class_sessions` |
| `backend/teaching/sinh_buoi.py` | 349 dòng | `class_sessions` |
| `backend/teaching/trung_lich.py` | 152 dòng | — |

| Tệp frontend | Dòng |
|---|---|
| `frontend/src/app/(standalone)/giang-day/buoi-hoc/[classId]/SessionsClient.tsx` | 1113 dòng |
| `frontend/src/app/(standalone)/giang-day/buoi-hoc/[classId]/SinhBuoi.tsx` | 345 dòng |
| `frontend/src/app/(standalone)/giang-day/buoi-hoc/[classId]/TaoBuoiBu.tsx` | 146 dòng |
| `frontend/src/app/(standalone)/giang-day/buoi-hoc/[classId]/XuatLop.tsx` | 69 dòng |
| `frontend/src/app/(standalone)/giang-day/buoi-hoc/[classId]/page.tsx` | 177 dòng |
| `frontend/src/app/(standalone)/giang-day/lich/page.tsx` | 329 dòng |
| `frontend/src/lib/noiHoc.ts` | 26 dòng |

## diem_danh

**Điểm danh** — Điểm danh từng buổi, lịch sử sửa điểm danh, luật đếm vắng (nơi DUY NHẤT).

- Bảng sở hữu: `attendance`, `attendance_history`
- Miền khác được ghi bảng của miền này: cong_cu (mọi bảng) — dựng / gỡ dữ liệu trình diễn phải chạm mọi miền một lượt; chỉ chạy tay (lệnh quản trị), không nằm trên đường phục vụ người dùng; *nợ*: `backend/teaching/sessions.py` ghi `attendance`; *nợ*: `backend/teaching/sessions.py` ghi `attendance_history`
- Glob: `backend/teaching/attendance.py`, `backend/diem_danh/**/*.py`, `frontend/src/app/(standalone)/giang-day/buoi-hoc/[classId]/LichSuDiemDanh.tsx`

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/teaching/attendance.py` | 96 dòng | — |

| Tệp frontend | Dòng |
|---|---|
| `frontend/src/app/(standalone)/giang-day/buoi-hoc/[classId]/LichSuDiemDanh.tsx` | 81 dòng |

## bai_tap

**Bài tập & kiểm tra** — Giao bài, đối tượng nhận bài, nộp bài, chấm tay; bài kiểm tra ngoại tuyến (V-h).

- Bảng sở hữu: `assignments`, `submissions`, `assignment_targets`
- Miền khác được ghi bảng của miền này: cong_cu (mọi bảng) — dựng / gỡ dữ liệu trình diễn phải chạm mọi miền một lượt; chỉ chạy tay (lệnh quản trị), không nằm trên đường phục vụ người dùng
- Glob: `backend/teaching/assignments.py`, `backend/teaching/nhan_bai.py`, `backend/bai_tap/**/*.py`, `frontend/src/app/(standalone)/giang-day/bai-tap/**`, `frontend/src/app/(standalone)/giang-day/cham/**`, `frontend/src/app/(standalone)/bai-tap/**`

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/teaching/assignments.py` | 1028 dòng | `assignment_targets`, `assignments`, `submissions` |
| `backend/teaching/nhan_bai.py` | 30 dòng | — |

| Tệp frontend | Dòng |
|---|---|
| `frontend/src/app/(standalone)/bai-tap/MyAssignmentsClient.tsx` | 267 dòng |
| `frontend/src/app/(standalone)/bai-tap/page.tsx` | 86 dòng |
| `frontend/src/app/(standalone)/giang-day/bai-tap/[classId]/AssignmentsClient.tsx` | 598 dòng |
| `frontend/src/app/(standalone)/giang-day/bai-tap/[classId]/[assignmentId]/GradingClient.tsx` | 471 dòng |
| `frontend/src/app/(standalone)/giang-day/bai-tap/[classId]/[assignmentId]/page.tsx` | 115 dòng |
| `frontend/src/app/(standalone)/giang-day/bai-tap/[classId]/page.tsx` | 121 dòng |
| `frontend/src/app/(standalone)/giang-day/cham/[assignmentId]/page.tsx` | 30 dòng |

## chuong_trinh

**Chương trình (E1)** — Khung chương trình theo buổi (phiên bản, nội dung, tài liệu), lớp nhận khung, sổ đầu bài (§70), tiến độ lớp / em.

- Bảng sở hữu: `syllabus_versions`, `syllabus_sessions`, `syllabus_items`, `syllabus_materials`, `session_logs`, `session_log_items`, `session_support`
- Miền khác được ghi bảng của miền này: cong_cu (mọi bảng) — dựng / gỡ dữ liệu trình diễn phải chạm mọi miền một lượt; chỉ chạy tay (lệnh quản trị), không nằm trên đường phục vụ người dùng
- Glob: `backend/chuong_trinh/**/*.py`, `backend/courseadmin/syllabus.py`, `frontend/src/app/(standalone)/giang-day/chuong-trinh/**`, `frontend/src/app/(standalone)/giang-day/so-dau-bai/**`, `frontend/src/app/(standalone)/giao-trinh/khung-chuong-trinh/**`, `frontend/src/lib/chuongTrinh.ts`, `frontend/src/lib/tienDoChu.ts`

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/chuong_trinh/__init__.py` | 0 dòng | — |
| `backend/chuong_trinh/apps.py` | 11 dòng | — |
| `backend/chuong_trinh/dich_vu.py` | 206 dòng | *`class_sessions`*, *`classes`*, `session_log_items` |
| `backend/chuong_trinh/du_lieu_mau.py` | 111 dòng | `session_log_items`, `session_logs`, `syllabus_items`, `syllabus_sessions`, `syllabus_versions` |
| `backend/chuong_trinh/khung.py` | 44 dòng | — |
| `backend/chuong_trinh/lop.py` | 231 dòng | *`class_sessions`* |
| `backend/chuong_trinh/so_dau_bai.py` | 290 dòng | `session_log_items`, `session_logs`, `session_support` |
| `backend/chuong_trinh/tien_do.py` | 284 dòng | — |
| `backend/chuong_trinh/tu_vung.py` | 38 dòng | — |
| `backend/chuong_trinh/urls.py` | 22 dòng | — |
| `backend/courseadmin/syllabus.py` | 566 dòng | `syllabus_items`, `syllabus_materials`, `syllabus_sessions`, `syllabus_versions` |

| Tệp frontend | Dòng |
|---|---|
| `frontend/src/app/(standalone)/giang-day/chuong-trinh/[classId]/ChuongTrinhLopClient.tsx` | 276 dòng |
| `frontend/src/app/(standalone)/giang-day/chuong-trinh/[classId]/page.tsx` | 54 dòng |
| `frontend/src/app/(standalone)/giang-day/so-dau-bai/[sessionId]/SoDauBaiClient.tsx` | 273 dòng |
| `frontend/src/app/(standalone)/giang-day/so-dau-bai/[sessionId]/page.tsx` | 56 dòng |
| `frontend/src/app/(standalone)/giao-trinh/khung-chuong-trinh/KhungClient.tsx` | 485 dòng |
| `frontend/src/app/(standalone)/giao-trinh/khung-chuong-trinh/page.tsx` | 80 dòng |
| `frontend/src/lib/chuongTrinh.ts` | 149 dòng |
| `frontend/src/lib/tienDoChu.ts` | 23 dòng |

## bao_cao

**Báo cáo** — CHỈ ĐỌC: báo cáo lớp, tổng quan trung tâm, xuất CSV/Excel/PDF, cơ sở học phí, chấm công, việc hôm nay. Không sở hữu bảng — đọc qua dịch vụ các miền.

- Bảng sở hữu: không có
- Miền khác được ghi bảng của miền này: không
- Glob: `backend/teaching/reports.py`, `backend/teaching/overview.py`, `backend/teaching/exports.py`, `backend/teaching/bao_cao_pdf.py`, `backend/teaching/bao_cao_lop_pdf.py`, `backend/teaching/co_so_hoc_phi.py`, `backend/teaching/cham_cong.py`, `backend/teaching/viec_hom_nay.py`, `backend/bao_cao/**/*.py`, `frontend/src/app/(standalone)/giang-day/page.tsx`, `frontend/src/app/(standalone)/giang-day/bao-cao/**`, `frontend/src/app/(standalone)/quan-tri/tong-quan/**`, `frontend/src/app/(standalone)/quan-tri/cham-cong/**`, `frontend/src/app/(standalone)/quan-tri/co-so-hoc-phi/**`, `frontend/src/components/ChonDinhDang.tsx`
- Tách khi chạm — `backend/teaching/bao_cao_pdf.py`: PDF tờ PHỤ HUYNH — §4 xếp vào bao_cao (cùng bộ dựng PDF với báo cáo lớp); nếu chỉ phu_huynh dùng thì dời sang phu_huynh khi chạm.

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/teaching/bao_cao_lop_pdf.py` | 307 dòng | — |
| `backend/teaching/bao_cao_pdf.py` | 636 dòng | — |
| `backend/teaching/cham_cong.py` | 151 dòng | — |
| `backend/teaching/co_so_hoc_phi.py` | 267 dòng | — |
| `backend/teaching/exports.py` | 851 dòng | — |
| `backend/teaching/overview.py` | 749 dòng | — |
| `backend/teaching/reports.py` | 738 dòng | — |
| `backend/teaching/viec_hom_nay.py` | 269 dòng | — |

| Tệp frontend | Dòng |
|---|---|
| `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/[userId]/loading.tsx` | 28 dòng |
| `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/[userId]/page.tsx` | 166 dòng |
| `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/page.tsx` | 253 dòng |
| `frontend/src/app/(standalone)/giang-day/page.tsx` | 360 dòng |
| `frontend/src/app/(standalone)/quan-tri/cham-cong/layout.tsx` | 17 dòng |
| `frontend/src/app/(standalone)/quan-tri/cham-cong/page.tsx` | 146 dòng |
| `frontend/src/app/(standalone)/quan-tri/co-so-hoc-phi/BangCoSo.tsx` | 178 dòng |
| `frontend/src/app/(standalone)/quan-tri/co-so-hoc-phi/layout.tsx` | 21 dòng |
| `frontend/src/app/(standalone)/quan-tri/co-so-hoc-phi/page.tsx` | 154 dòng |
| `frontend/src/app/(standalone)/quan-tri/tong-quan/TheTongQuan.tsx` | 454 dòng |
| `frontend/src/app/(standalone)/quan-tri/tong-quan/ViecCanLam.tsx` | 106 dòng |
| `frontend/src/app/(standalone)/quan-tri/tong-quan/layout.tsx` | 26 dòng |
| `frontend/src/app/(standalone)/quan-tri/tong-quan/page.tsx` | 550 dòng |
| `frontend/src/components/ChonDinhDang.tsx` | 47 dòng |

## phu_huynh

**Phụ huynh** — Tờ báo cáo phụ huynh, đường dẫn riêng (không mật khẩu), gửi cả lớp, thư báo cáo, liên hệ phụ huynh, từ chối nhận.

- Bảng sở hữu: `parent_report_links`, `parent_report_sends`, `parent_report_optout`
- Miền khác được ghi bảng của miền này: cong_cu (mọi bảng) — dựng / gỡ dữ liệu trình diễn phải chạm mọi miền một lượt; chỉ chạy tay (lệnh quản trị), không nằm trên đường phục vụ người dùng
- Glob: `backend/teaching/parent_report.py`, `backend/teaching/parent_link.py`, `backend/teaching/parent_send.py`, `backend/teaching/lien_he_phu_huynh.py`, `backend/teaching/thu_bao_cao.py`, `backend/phu_huynh/**/*.py`, `frontend/src/app/(standalone)/bc/**`, `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/DanLienHe.tsx`, `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/GuiCaLop.tsx`, `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/[userId]/DuongDanDaCap.tsx`, `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/[userId]/KhoiDuongDan.tsx`, `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/[userId]/TaoDuongDan.tsx`, `frontend/src/components/ToBaoCao.tsx`, `frontend/src/components/KhungToBaoCao.tsx`, `frontend/src/components/KhoaLienHePhuHuynh.tsx`

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/teaching/lien_he_phu_huynh.py` | 378 dòng | *`users`* |
| `backend/teaching/parent_link.py` | 226 dòng | `parent_report_links` |
| `backend/teaching/parent_report.py` | 715 dòng | — |
| `backend/teaching/parent_send.py` | 322 dòng | `parent_report_links`, `parent_report_sends` |
| `backend/teaching/thu_bao_cao.py` | 197 dòng | — |

| Tệp frontend | Dòng |
|---|---|
| `frontend/src/app/(standalone)/bc/[token]/loading.tsx` | 74 dòng |
| `frontend/src/app/(standalone)/bc/[token]/page.tsx` | 91 dòng |
| `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/DanLienHe.tsx` | 299 dòng |
| `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/GuiCaLop.tsx` | 203 dòng |
| `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/[userId]/DuongDanDaCap.tsx` | 258 dòng |
| `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/[userId]/KhoiDuongDan.tsx` | 51 dòng |
| `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/[userId]/TaoDuongDan.tsx` | 155 dòng |
| `frontend/src/components/KhoaLienHePhuHuynh.tsx` | 83 dòng |
| `frontend/src/components/KhungToBaoCao.tsx` | 53 dòng |
| `frontend/src/components/ToBaoCao.tsx` | 522 dòng |

## ho_so

**Hồ sơ học viên** — Hồ sơ mở rộng (mã HV, trường, tỉnh, người tư vấn, mục tiêu, tình trạng), học vụ cấp tài khoản / nhập hàng loạt, dòng thời gian. Không bảng riêng — ghi cột hồ sơ của `users` qua cho_ghi.

- Bảng sở hữu: không có
- Miền khác được ghi bảng của miền này: không
- Glob: `backend/teaching/ho_so.py`, `backend/teaching/admin_users.py`, `backend/teaching/dong_thoi_gian.py`, `backend/teaching/tinh_trang.py`, `backend/teaching/tinh_thanh.py`, `backend/ho_so/**/*.py`, `frontend/src/app/(standalone)/quan-tri/tai-khoan/**`, `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/[userId]/MucTieuEm.tsx`, `frontend/src/lib/tinhThanh.ts`

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/teaching/admin_users.py` | 1059 dòng | *`class_members`*, *`users`* |
| `backend/teaching/dong_thoi_gian.py` | 226 dòng | — |
| `backend/teaching/ho_so.py` | 443 dòng | *`users`* |
| `backend/teaching/tinh_thanh.py` | 51 dòng | — |
| `backend/teaching/tinh_trang.py` | 70 dòng | — |

| Tệp frontend | Dòng |
|---|---|
| `frontend/src/app/(standalone)/giang-day/bao-cao/[classId]/[userId]/MucTieuEm.tsx` | 126 dòng |
| `frontend/src/app/(standalone)/quan-tri/tai-khoan/AccountsClient.tsx` | 1173 dòng |
| `frontend/src/app/(standalone)/quan-tri/tai-khoan/XuatTaiKhoan.tsx` | 123 dòng |
| `frontend/src/app/(standalone)/quan-tri/tai-khoan/[id]/DongThoiGian.tsx` | 84 dòng |
| `frontend/src/app/(standalone)/quan-tri/tai-khoan/[id]/HoSoClient.tsx` | 499 dòng |
| `frontend/src/app/(standalone)/quan-tri/tai-khoan/[id]/hoSo.ts` | 141 dòng |
| `frontend/src/app/(standalone)/quan-tri/tai-khoan/[id]/page.tsx` | 66 dòng |
| `frontend/src/app/(standalone)/quan-tri/tai-khoan/layout.tsx` | 25 dòng |
| `frontend/src/app/(standalone)/quan-tri/tai-khoan/loc.ts` | 98 dòng |
| `frontend/src/app/(standalone)/quan-tri/tai-khoan/page.tsx` | 111 dòng |
| `frontend/src/lib/tinhThanh.ts` | 48 dòng |

## yeu_cau

**Yêu cầu** — Hộp Yêu cầu chung (E3, §65): hỗ trợ học tập / lịch / kỹ thuật / tài khoản, câu hỏi gửi GV–TG, TG báo lên, báo lỗi bản ghi buổi học, phụ huynh gửi qua link tờ báo cáo; xin → học vụ DUYỆT trong MỘT giao dịch → gọi dịch vụ miền lớp học (chuyển lớp / môn, bảo lưu, huỷ khoá, học lại). Trả lời + lịch sử một bảng, ghi chú nội bộ ẩn với HS / PH.

- Bảng sở hữu: `yeu_cau`, `yeu_cau_su_kien`
- Miền khác được ghi bảng của miền này: cong_cu (mọi bảng) — dựng / gỡ dữ liệu trình diễn phải chạm mọi miền một lượt; chỉ chạy tay (lệnh quản trị), không nằm trên đường phục vụ người dùng
- Glob: `backend/yeu_cau/**/*.py`, `frontend/src/app/(standalone)/yeu-cau/**`, `frontend/src/components/YeuCau*.tsx`, `frontend/src/lib/yeuCau*.ts`

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/yeu_cau/__init__.py` | 0 dòng | — |
| `backend/yeu_cau/apps.py` | 11 dòng | — |
| `backend/yeu_cau/dich_vu.py` | 689 dòng | `yeu_cau`, `yeu_cau_su_kien` |
| `backend/yeu_cau/loai.py` | 141 dòng | — |
| `backend/yeu_cau/thuc_thi.py` | 180 dòng | — |
| `backend/yeu_cau/urls.py` | 31 dòng | — |
| `backend/yeu_cau/views.py` | 398 dòng | — |

## thong_bao

**Thông báo** — Chuông trong ứng dụng, cài đặt nhận tin, mặt tiền gửi `gui` / `gui_sau_commit`, báo đổi lịch. Sắp có (E2): hộp thư đi (outbox), thông báo lớp / trung tâm (announcements).

- Bảng sở hữu: `notifications`, `notification_settings`
- Miền khác được ghi bảng của miền này: cong_cu (mọi bảng) — dựng / gỡ dữ liệu trình diễn phải chạm mọi miền một lượt; chỉ chạy tay (lệnh quản trị), không nằm trên đường phục vụ người dùng
- Glob: `backend/notifications/**/*.py`, `backend/teaching/bao_doi_lich.py`, `backend/thong_bao/**/*.py`

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/notifications/__init__.py` | 0 dòng | — |
| `backend/notifications/apps.py` | 6 dòng | — |
| `backend/notifications/gui.py` | 78 dòng | — |
| `backend/notifications/models.py` | 31 dòng | — |
| `backend/notifications/service.py` | 63 dòng | `notifications` |
| `backend/notifications/urls.py` | 12 dòng | — |
| `backend/notifications/views.py` | 90 dòng | `notification_settings`, `notifications` |
| `backend/teaching/bao_doi_lich.py` | 125 dòng | — |

## tai_khoan

**Tài khoản** — Người dùng, đăng nhập (mật khẩu, OAuth, ghi nhớ), quên / đổi mật khẩu, hoạt động gần nhất. Chủ bảng `users`.

- Bảng sở hữu: `users`, `password_reset_tokens`
- Miền khác được ghi bảng của miền này: ho_so ghi `users` — cột HỒ SƠ (mã HV, trường, tỉnh, tư vấn, mục tiêu, tình trạng — §51, V-m) + học vụ cấp tài khoản Học viên (`admin_users`) — thiết kế §4: ho_so sở hữu cột hồ sơ trên `users`; cong_cu (mọi bảng) — dựng / gỡ dữ liệu trình diễn phải chạm mọi miền một lượt; chỉ chạy tay (lệnh quản trị), không nằm trên đường phục vụ người dùng; *nợ*: `backend/common/streak.py` ghi `users`; *nợ*: `backend/stats/views.py` ghi `users`; *nợ*: `backend/teaching/lien_he_phu_huynh.py` ghi `users`; *nợ*: `backend/teaching/views.py` ghi `users`
- Glob: `backend/accounts/**/*.py`, `frontend/src/app/(standalone)/login/**`, `frontend/src/app/(standalone)/doi-mat-khau/**`, `frontend/src/app/(standalone)/dat-lai-mat-khau/**`, `frontend/src/app/(standalone)/quen-mat-khau/**`, `frontend/src/app/auth/**`, `frontend/src/lib/auth.ts`, `frontend/src/lib/phienGhiNho.ts`

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/accounts/__init__.py` | 0 dòng | — |
| `backend/accounts/apps.py` | 6 dòng | — |
| `backend/accounts/authentication.py` | 139 dòng | — |
| `backend/accounts/ghi_nho.py` | 81 dòng | — |
| `backend/accounts/hashers.py` | 107 dòng | — |
| `backend/accounts/hoat_dong.py` | 79 dòng | `users` |
| `backend/accounts/models.py` | 123 dòng | — |
| `backend/accounts/oauth.py` | 94 dòng | `users` |
| `backend/accounts/quen_mat_khau.py` | 221 dòng | `password_reset_tokens`, `users` |
| `backend/accounts/urls.py` | 23 dòng | — |
| `backend/accounts/validators.py` | 54 dòng | — |
| `backend/accounts/views.py` | 670 dòng | *`roadmaps`*, *`surveys`*, *`user_follows`*, `users` |

| Tệp frontend | Dòng |
|---|---|
| `frontend/src/app/(standalone)/dat-lai-mat-khau/DatLaiForm.tsx` | 172 dòng |
| `frontend/src/app/(standalone)/dat-lai-mat-khau/page.tsx` | 29 dòng |
| `frontend/src/app/(standalone)/doi-mat-khau/ChangePasswordForm.tsx` | 163 dòng |
| `frontend/src/app/(standalone)/doi-mat-khau/page.tsx` | 61 dòng |
| `frontend/src/app/(standalone)/login/LoginForm.tsx` | 293 dòng |
| `frontend/src/app/(standalone)/login/page.tsx` | 107 dòng |
| `frontend/src/app/(standalone)/quen-mat-khau/QuenMatKhauForm.tsx` | 87 dòng |
| `frontend/src/app/(standalone)/quen-mat-khau/page.tsx` | 44 dòng |
| `frontend/src/app/auth/[...path]/route.ts` | 111 dòng |
| `frontend/src/app/auth/callback/page.tsx` | 51 dòng |
| `frontend/src/app/auth/logout/route.ts` | 42 dòng |
| `frontend/src/app/auth/session/route.ts` | 67 dòng |
| `frontend/src/lib/auth.ts` | 157 dòng |
| `frontend/src/lib/phienGhiNho.ts` | 48 dòng |

## chung

**Chung (hạt nhân)** — Hạ tầng dùng chung: truy cập CSDL, đồng hồ giờ VN, quyền, nhật ký quản trị, sự kiện học tập, thư, lược đồ; cấu hình; khung giao diện, thành phần UI, thư viện frontend dùng chung.

- Bảng sở hữu: `admin_audit`, `learning_events`
- Miền khác được ghi bảng của miền này: cong_cu (mọi bảng) — dựng / gỡ dữ liệu trình diễn phải chạm mọi miền một lượt; chỉ chạy tay (lệnh quản trị), không nằm trên đường phục vụ người dùng
- Glob: `backend/common/**/*.py`, `backend/config/**/*.py`, `backend/manage.py`, `backend/inspectdb_snapshot.py`, `backend/teaching/__init__.py`, `backend/teaching/apps.py`, `backend/teaching/urls.py`, `backend/teaching/vocab.py`, `frontend/src/*.ts`, `frontend/src/app/*.tsx`, `frontend/src/app/api/**`, `frontend/src/app/(base)/layout.tsx`, `frontend/src/app/(base)/page.tsx`, `frontend/src/app/(standalone)/layout.tsx`, `frontend/src/app/(standalone)/huong-dan/**`, `frontend/src/app/(standalone)/thiet-ke/**`, `frontend/src/app/(standalone)/giang-day/layout.tsx`, `frontend/src/app/(standalone)/giang-day/KhungGiangDay.tsx`, `frontend/src/app/(standalone)/quan-tri/*.ts`, `frontend/src/app/(standalone)/quan-tri/*.tsx`, `frontend/src/app/(standalone)/quan-tri/huong-dan/**`, `frontend/src/app/(standalone)/quan-tri/vai-tro/**`, `frontend/src/app/(standalone)/quan-tri/nhat-ky/**`, `frontend/src/components/ui/**`, `frontend/src/components/AppShell.tsx`, `frontend/src/components/navMuc.ts`, `frontend/src/components/bieuTuong.tsx`, `frontend/src/components/PageStyles.tsx`, `frontend/src/components/NutIn.tsx`, `frontend/src/components/BangHuongDan.tsx`, `frontend/src/components/KhuNhanSu.tsx`, `frontend/src/components/LegacyScripts.tsx`, `frontend/src/components/NapTruocScript.tsx`, `frontend/src/components/NapTruocDuLieu.tsx`, `frontend/src/lib/*.ts`
- Tách khi chạm — `backend/teaching/vocab.py`: từ vựng trạng thái dùng bởi NHIỀU miền của teaching — dời sang common/ khi chạm.
- Tách khi chạm — `backend/teaching/urls.py`: tuyến gộp của mọi miền teaching — mỗi miền mới có urls.py riêng (như chuong_trinh/).

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/common/__init__.py` | 0 dòng | — |
| `backend/common/apps.py` | 46 dòng | — |
| `backend/common/audit.py` | 217 dòng | `admin_audit` |
| `backend/common/bangtinh.py` | 484 dòng | — |
| `backend/common/clock.py` | 30 dòng | — |
| `backend/common/db.py` | 200 dòng | — |
| `backend/common/do_proxy.py` | 60 dòng | — |
| `backend/common/errors.py` | 93 dòng | — |
| `backend/common/events.py` | 317 dòng | `learning_events` |
| `backend/common/hang_rao_csdl.py` | 64 dòng | — |
| `backend/common/identity.py` | 62 dòng | — |
| `backend/common/keepalive.py` | 40 dòng | — |
| `backend/common/logging.py` | 82 dòng | — |
| `backend/common/luoc_do_sql.py` | 587 dòng | — |
| `backend/common/mail.py` | 234 dòng | — |
| `backend/common/management/__init__.py` | 0 dòng | — |
| `backend/common/management/commands/__init__.py` | 0 dòng | — |
| `backend/common/management/commands/backfill_learning_events.py` | 252 dòng | — |
| `backend/common/management/commands/bootstrap_schema.py` | 135 dòng | — |
| `backend/common/management/commands/chan_doan_oa.py` | 173 dòng | — |
| `backend/common/management/commands/kiem_luoc_do.py` | 314 dòng | — |
| `backend/common/management/commands/thu_email.py` | 160 dòng | — |
| `backend/common/management/commands/thu_zns.py` | 98 dòng | — |
| `backend/common/management/commands/ve_erd.py` | 217 dòng | — |
| `backend/common/middleware.py` | 75 dòng | — |
| `backend/common/net.py` | 133 dòng | — |
| `backend/common/params.py` | 133 dòng | — |
| `backend/common/permissions.py` | 268 dòng | — |
| `backend/common/streak.py` | 65 dòng | *`user_daily_xp_logs`*, *`users`* |
| `backend/common/throttling.py` | 149 dòng | — |
| `backend/common/views.py` | 52 dòng | — |
| `backend/common/zalo.py` | 291 dòng | — |
| `backend/config/__init__.py` | 0 dòng | — |
| `backend/config/asgi.py` | 16 dòng | — |
| `backend/config/settings.py` | 488 dòng | — |
| `backend/config/urls.py` | 52 dòng | — |
| `backend/config/wsgi.py` | 16 dòng | — |
| `backend/inspectdb_snapshot.py` | 340 dòng | — |
| `backend/manage.py` | 22 dòng | — |
| `backend/teaching/__init__.py` | 0 dòng | — |
| `backend/teaching/apps.py` | 5 dòng | — |
| `backend/teaching/urls.py` | 172 dòng | — |
| `backend/teaching/vocab.py` | 75 dòng | — |

| Tệp frontend | Dòng |
|---|---|
| `frontend/src/app/(base)/layout.tsx` | 44 dòng |
| `frontend/src/app/(base)/page.tsx` | 27 dòng |
| `frontend/src/app/(standalone)/giang-day/KhungGiangDay.tsx` | 80 dòng |
| `frontend/src/app/(standalone)/giang-day/layout.tsx` | 42 dòng |
| `frontend/src/app/(standalone)/huong-dan/layout.tsx` | 52 dòng |
| `frontend/src/app/(standalone)/huong-dan/page.tsx` | 27 dòng |
| `frontend/src/app/(standalone)/layout.tsx` | 32 dòng |
| `frontend/src/app/(standalone)/quan-tri/ChanVai.tsx` | 42 dòng |
| `frontend/src/app/(standalone)/quan-tri/TieuDeTrang.tsx` | 19 dòng |
| `frontend/src/app/(standalone)/quan-tri/huong-dan/layout.tsx` | 24 dòng |
| `frontend/src/app/(standalone)/quan-tri/huong-dan/page.tsx` | 51 dòng |
| `frontend/src/app/(standalone)/quan-tri/layVai.ts` | 39 dòng |
| `frontend/src/app/(standalone)/quan-tri/layout.tsx` | 76 dòng |
| `frontend/src/app/(standalone)/quan-tri/nhat-ky/layout.tsx` | 22 dòng |
| `frontend/src/app/(standalone)/quan-tri/nhat-ky/page.tsx` | 251 dòng |
| `frontend/src/app/(standalone)/quan-tri/vai-tro/SoDoVaiTro.tsx` | 208 dòng |
| `frontend/src/app/(standalone)/quan-tri/vai-tro/layout.tsx` | 23 dòng |
| `frontend/src/app/(standalone)/quan-tri/vai-tro/page.tsx` | 192 dòng |
| `frontend/src/app/(standalone)/quan-tri/vai.ts` | 106 dòng |
| `frontend/src/app/(standalone)/thiet-ke/page.tsx` | 266 dòng |
| `frontend/src/app/api/[...path]/route.ts` | 28 dòng |
| `frontend/src/app/error.tsx` | 61 dòng |
| `frontend/src/app/global-error.tsx` | 42 dòng |
| `frontend/src/app/layout.tsx` | 102 dòng |
| `frontend/src/app/not-found.tsx` | 27 dòng |
| `frontend/src/components/AppShell.tsx` | 671 dòng |
| `frontend/src/components/BangHuongDan.tsx` | 157 dòng |
| `frontend/src/components/KhuNhanSu.tsx` | 77 dòng |
| `frontend/src/components/LegacyScripts.tsx` | 76 dòng |
| `frontend/src/components/NapTruocDuLieu.tsx` | 69 dòng |
| `frontend/src/components/NapTruocScript.tsx` | 48 dòng |
| `frontend/src/components/NutIn.tsx` | 24 dòng |
| `frontend/src/components/PageStyles.tsx` | 14 dòng |
| `frontend/src/components/bieuTuong.tsx` | 83 dòng |
| `frontend/src/components/navMuc.ts` | 95 dòng |
| `frontend/src/components/ui/Button.tsx` | 92 dòng |
| `frontend/src/components/ui/Card.tsx` | 93 dòng |
| `frontend/src/components/ui/Chip.tsx` | 56 dòng |
| `frontend/src/components/ui/EmptyState.tsx` | 42 dòng |
| `frontend/src/components/ui/Field.tsx` | 79 dòng |
| `frontend/src/components/ui/Modal.tsx` | 87 dòng |
| `frontend/src/components/ui/Table.tsx` | 168 dòng |
| `frontend/src/components/ui/ThemeToggle.tsx` | 54 dòng |
| `frontend/src/components/ui/Tile.tsx` | 64 dòng |
| `frontend/src/components/ui/Toast.tsx` | 89 dòng |
| `frontend/src/components/ui/index.ts` | 20 dòng |
| `frontend/src/lib/api.ts` | 197 dòng |
| `frontend/src/lib/chanTu.ts` | 23 dòng |
| `frontend/src/lib/chuDe.ts` | 62 dòng |
| `frontend/src/lib/coAnh.ts` | 35 dòng |
| `frontend/src/lib/daGan.ts` | 20 dòng |
| `frontend/src/lib/dieuHuong.ts` | 21 dòng |
| `frontend/src/lib/form.ts` | 20 dòng |
| `frontend/src/lib/gioVN.ts` | 56 dòng |
| `frontend/src/lib/goiLegacy.ts` | 82 dòng |
| `frontend/src/lib/hinhDang.ts` | 121 dòng |
| `frontend/src/lib/huongDan.ts` | 594 dòng |
| `frontend/src/lib/khuTheoVai.ts` | 108 dòng |
| `frontend/src/lib/kiemDang.ts` | 61 dòng |
| `frontend/src/lib/nhomVai.ts` | 59 dòng |
| `frontend/src/lib/proxy.ts` | 227 dòng |
| `frontend/src/lib/quyenVai.ts` | 532 dòng |
| `frontend/src/lib/server-api.ts` | 193 dòng |
| `frontend/src/lib/useVaiHienTai.ts` | 47 dòng |
| `frontend/src/lib/vaiTro.ts` | 43 dòng |
| `frontend/src/lib/viecNhatKy.ts` | 105 dòng |
| `frontend/src/proxy.ts` | 146 dòng |

## hoc_truc_tuyen

**Học trực tuyến** — Sản phẩm học: khoá, bài học, tiến độ bài, trắc nghiệm, lộ trình, khảo sát, nhật ký / kế hoạch học, năng lực, nhiệm vụ, thành tích, XP, bảng xếp hạng, trợ lý AI; soạn khoá (courseadmin). Tầng JS cũ `public/static/js` (chỉ co).

- Bảng sở hữu: `courses`, `lessons`, `lesson_progress`, `enrollments`, `quizzes`, `review_quiz_results`, `topic_self_marks`, `course_ratings`, `surveys`, `roadmaps`, `roadmap_progress`, `study_logs`, `study_plans`, `study_plan_items`, `missions`, `user_missions`, `achievements`, `user_achievements`, `user_daily_xp_logs`
- Miền khác được ghi bảng của miền này: cong_cu (mọi bảng) — dựng / gỡ dữ liệu trình diễn phải chạm mọi miền một lượt; chỉ chạy tay (lệnh quản trị), không nằm trên đường phục vụ người dùng; *nợ*: `backend/accounts/views.py` ghi `roadmaps`; *nợ*: `backend/accounts/views.py` ghi `surveys`; *nợ*: `backend/common/streak.py` ghi `user_daily_xp_logs`
- Glob: `backend/courses/**/*.py`, `backend/lessons/**/*.py`, `backend/quizzes/**/*.py`, `backend/roadmap/**/*.py`, `backend/stats/**/*.py`, `backend/achievements/**/*.py`, `backend/leaderboard/**/*.py`, `backend/chatbot/**/*.py`, `backend/courseadmin/**/*.py`, `frontend/src/app/(base)/dashboard/**`, `frontend/src/app/(standalone)/courses/**`, `frontend/src/app/(standalone)/lesson/**`, `frontend/src/app/(standalone)/questionaire/**`, `frontend/src/app/(standalone)/giao-trinh/**`, `frontend/src/components/BaHopPhan.tsx`, `frontend/src/components/Chatbot.tsx`, `frontend/src/components/HocTiep*.tsx`, `frontend/src/components/LessonHsa.tsx`, `frontend/src/components/NhiemVu*.tsx`, `frontend/src/components/RoadmapSection.tsx`, `frontend/src/components/TheSoHsa*.tsx`, `frontend/src/components/TienDoHopPhan.tsx`, `frontend/src/lib/duLieuHsa.ts`, `frontend/src/lib/nguCanhBaiHoc.ts`, `frontend/src/lib/soanBai.ts`, `frontend/src/lib/dinhDangTinNhan.ts`, `frontend/public/static/js/**`
- Tách khi chạm — `frontend/src/app/(base)/dashboard/DashboardClient.tsx`: trang đầu dùng chung mọi vai (1.031 dòng) — mỗi vai nhận 'Việc hôm nay' riêng khi chạm (THIET_KE §3).

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/achievements/__init__.py` | 0 dòng | — |
| `backend/achievements/apps.py` | 6 dòng | — |
| `backend/achievements/models.py` | 26 dòng | — |
| `backend/achievements/services.py` | 40 dòng | `user_achievements` |
| `backend/achievements/urls.py` | 7 dòng | — |
| `backend/achievements/views.py` | 29 dòng | — |
| `backend/chatbot/__init__.py` | 0 dòng | — |
| `backend/chatbot/apps.py` | 17 dòng | — |
| `backend/chatbot/graph.py` | 222 dòng | — |
| `backend/chatbot/profile.py` | 173 dòng | — |
| `backend/chatbot/urls.py` | 7 dòng | — |
| `backend/chatbot/views.py` | 267 dòng | — |
| `backend/courseadmin/__init__.py` | 0 dòng | — |
| `backend/courseadmin/apps.py` | 6 dòng | — |
| `backend/courseadmin/urls.py` | 28 dòng | — |
| `backend/courseadmin/views.py` | 681 dòng | `courses`, `lessons` |
| `backend/courses/__init__.py` | 0 dòng | — |
| `backend/courses/apps.py` | 6 dòng | — |
| `backend/courses/enrollment.py` | 74 dòng | `enrollments` |
| `backend/courses/models.py` | 56 dòng | — |
| `backend/courses/truy_cap.py` | 138 dòng | — |
| `backend/courses/urls.py` | 17 dòng | — |
| `backend/courses/views.py` | 393 dòng | `course_ratings` |
| `backend/leaderboard/__init__.py` | 0 dòng | — |
| `backend/leaderboard/apps.py` | 6 dòng | — |
| `backend/leaderboard/urls.py` | 7 dòng | — |
| `backend/leaderboard/views.py` | 309 dòng | — |
| `backend/lessons/__init__.py` | 0 dòng | — |
| `backend/lessons/apps.py` | 6 dòng | — |
| `backend/lessons/content.py` | 362 dòng | — |
| `backend/lessons/do_thi.py` | 200 dòng | — |
| `backend/lessons/grading.py` | 430 dòng | `lesson_progress` |
| `backend/lessons/luoc_do.py` | 87 dòng | — |
| `backend/lessons/management/__init__.py` | 0 dòng | — |
| `backend/lessons/management/commands/__init__.py` | 0 dòng | — |
| `backend/lessons/management/commands/nap_minh_hoa.py` | 167 dòng | `lessons` |
| `backend/lessons/minh_hoa/__init__.py` | 64 dòng | — |
| `backend/lessons/minh_hoa/hsa_quantitative.py` | 290 dòng | — |
| `backend/lessons/minh_hoa/hsa_science.py` | 317 dòng | — |
| `backend/lessons/minh_hoa/hsa_verbal.py` | 301 dòng | — |
| `backend/lessons/models.py` | 38 dòng | — |
| `backend/lessons/urls.py` | 14 dòng | — |
| `backend/lessons/views.py` | 620 dòng | `enrollments`, `lesson_progress` |
| `backend/quizzes/__init__.py` | 0 dòng | — |
| `backend/quizzes/apps.py` | 6 dòng | — |
| `backend/quizzes/models.py` | 29 dòng | — |
| `backend/quizzes/urls.py` | 10 dòng | — |
| `backend/quizzes/views.py` | 477 dòng | `quizzes`, `review_quiz_results` |
| `backend/roadmap/__init__.py` | 0 dòng | — |
| `backend/roadmap/apps.py` | 6 dòng | — |
| `backend/roadmap/models.py` | 33 dòng | — |
| `backend/roadmap/urls.py` | 10 dòng | — |
| `backend/roadmap/views.py` | 149 dòng | `roadmap_progress`, `roadmaps` |
| `backend/stats/__init__.py` | 0 dòng | — |
| `backend/stats/apps.py` | 6 dòng | — |
| `backend/stats/competency.py` | 362 dòng | — |
| `backend/stats/goals.py` | 165 dòng | — |
| `backend/stats/gradebook.py` | 296 dòng | — |
| `backend/stats/journal.py` | 403 dòng | `study_logs`, `study_plans` |
| `backend/stats/models.py` | 29 dòng | — |
| `backend/stats/plan.py` | 672 dòng | `study_plan_items`, `study_plans` |
| `backend/stats/tin_hieu.py` | 10 dòng | — |
| `backend/stats/urls.py` | 27 dòng | — |
| `backend/stats/views.py` | 516 dòng | `surveys`, `topic_self_marks`, `user_daily_xp_logs`, `user_missions`, *`users`* |

| Tệp frontend | Dòng |
|---|---|
| `frontend/src/app/(base)/dashboard/DashboardClient.tsx` | 1031 dòng |
| `frontend/src/app/(base)/dashboard/page.tsx` | 96 dòng |
| `frontend/src/app/(standalone)/courses/[courseId]/page.tsx` | 403 dòng |
| `frontend/src/app/(standalone)/giao-trinh/NoiDungBai.tsx` | 808 dòng |
| `frontend/src/app/(standalone)/giao-trinh/SoanClient.tsx` | 699 dòng |
| `frontend/src/app/(standalone)/giao-trinh/page.tsx` | 123 dòng |
| `frontend/src/app/(standalone)/lesson/[courseId]/page.tsx` | 24 dòng |
| `frontend/src/app/(standalone)/questionaire/page.tsx` | 302 dòng |
| `frontend/src/components/BaHopPhan.tsx` | 145 dòng |
| `frontend/src/components/Chatbot.tsx` | 278 dòng |
| `frontend/src/components/HocTiep.tsx` | 148 dòng |
| `frontend/src/components/HocTiepRong.tsx` | 35 dòng |
| `frontend/src/components/LessonHsa.tsx` | 268 dòng |
| `frontend/src/components/NhiemVu.tsx` | 36 dòng |
| `frontend/src/components/NhiemVuClient.tsx` | 104 dòng |
| `frontend/src/components/RoadmapSection.tsx` | 117 dòng |
| `frontend/src/components/TheSoHsa.tsx` | 14 dòng |
| `frontend/src/components/TheSoHsaClient.tsx` | 134 dòng |
| `frontend/src/components/TienDoHopPhan.tsx` | 49 dòng |
| `frontend/src/lib/dinhDangTinNhan.ts` | 28 dòng |
| `frontend/src/lib/duLieuHsa.ts` | 63 dòng |
| `frontend/src/lib/nguCanhBaiHoc.ts` | 63 dòng |
| `frontend/src/lib/soanBai.ts` | 279 dòng |

JS cũ (chỉ co): 11 tệp · 8526 dòng — `course_detail.js`, `dashboard.js`, `icons.js`, `lesson_hsa.js`, `main.js`, `lesson-topbar.hydrate.js`, `pe-bridge.js`, `questionaire.js`, `review_quiz.js`, `roadmap.js`, `roadmapData.js`

## dien_dan

**Diễn đàn** — Bài viết, bình luận, thích, theo dõi người dùng.

- Bảng sở hữu: `posts`, `comments`, `post_likes`, `comment_likes`, `user_follows`
- Miền khác được ghi bảng của miền này: cong_cu (mọi bảng) — dựng / gỡ dữ liệu trình diễn phải chạm mọi miền một lượt; chỉ chạy tay (lệnh quản trị), không nằm trên đường phục vụ người dùng; *nợ*: `backend/accounts/views.py` ghi `user_follows`
- Glob: `backend/forum/**/*.py`

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/forum/__init__.py` | 0 dòng | — |
| `backend/forum/apps.py` | 6 dòng | — |
| `backend/forum/models.py` | 57 dòng | — |
| `backend/forum/urls.py` | 12 dòng | — |
| `backend/forum/views.py` | 450 dòng | `comments`, `posts` |

## thi_cu

**Thi thử (ĐÓNG BĂNG)** — Thi thử trực tuyến (đã tháo tuyến, giữ dữ liệu) + nhập kết quả thi ngoài từ PDF. ĐÓNG BĂNG: không thêm tính năng, chỉ vá.

- Bảng sở hữu: `mock_exams`, `mock_attempts`, `ket_qua_thi_ngoai`
- Miền khác được ghi bảng của miền này: cong_cu (mọi bảng) — dựng / gỡ dữ liệu trình diễn phải chạm mọi miền một lượt; chỉ chạy tay (lệnh quản trị), không nằm trên đường phục vụ người dùng
- Glob: `backend/mockexam/**/*.py`, `backend/teaching/nhap_ket_qua*.py`, `backend/config/urls_thi_da_thao.py`

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/config/urls_thi_da_thao.py` | 28 dòng | — |
| `backend/mockexam/__init__.py` | 0 dòng | — |
| `backend/mockexam/apps.py` | 6 dòng | — |
| `backend/mockexam/models.py` | 34 dòng | — |
| `backend/mockexam/nhap.py` | 281 dòng | — |
| `backend/mockexam/quan_tri.py` | 248 dòng | `mock_exams` |
| `backend/mockexam/urls.py` | 25 dòng | — |
| `backend/mockexam/views.py` | 497 dòng | `mock_attempts` |
| `backend/teaching/nhap_ket_qua_thi.py` | 242 dòng | — |
| `backend/teaching/nhap_ket_qua_view.py` | 357 dòng | `ket_qua_thi_ngoai` |

## cong_cu

**Công cụ dữ liệu mẫu** — Bộ dữ liệu trình diễn (§49) và lệnh nạp dữ liệu mẫu — dựng / gỡ một trung tâm giả.

- Bảng sở hữu: không có
- Được ghi MỌI bảng: dựng / gỡ dữ liệu trình diễn phải chạm mọi miền một lượt; chỉ chạy tay (lệnh quản trị), không nằm trên đường phục vụ người dùng
- Miền khác được ghi bảng của miền này: không
- Glob: `backend/teaching/du_lieu_mau.py`, `backend/common/management/commands/du_lieu_mau.py`, `backend/common/management/commands/seed_data.py`

| Tệp backend | Dòng | Ghi bảng |
|---|---|---|
| `backend/common/management/commands/du_lieu_mau.py` | 81 dòng | — |
| `backend/common/management/commands/seed_data.py` | 356 dòng | *`achievements`*, *`courses`*, *`missions`*, *`mock_exams`*, *`posts`*, *`roadmaps`* |
| `backend/teaching/du_lieu_mau.py` | 733 dòng | *`assignments`*, *`attendance`*, *`class_members`*, *`class_sessions`*, *`classes`*, *`enrollments`*, *`ket_qua_thi_ngoai`*, *`lesson_progress`*, *`mock_attempts`*, *`parent_report_links`*, *`parent_report_sends`*, *`submissions`*, *`syllabus_versions`*, *`user_daily_xp_logs`*, *`users`* |
