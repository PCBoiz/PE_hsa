/**
 * TÊN VAI TRÒ — một nơi duy nhất trong cả frontend.
 *
 * ── VÌ SAO TÁCH RA KHỎI `quan-tri/vai.ts` (04/09/2026) ─────────────────────
 *
 * `quan-tri/vai.ts` mở đầu bằng đúng lời hứa "chỉ còn MỘT bảng" — sau khi gộp
 * ba bảng lệch nhau về cùng một chỗ. Nhưng vẫn còn bảng thứ tư ở ngoài tầm với
 * của nó:
 *
 *     admin/page.tsx:  const DUOC_VAO = new Set(['admin', 'Biên tập nội dung']);
 *
 * Hai chuỗi gõ tay, không import gì, không phép kiểm nào ràng với `vai.ts`.
 * Hôm nay hai bên trùng nhau nên chưa hỏng — nhưng cơ chế trôi-khỏi-nhau thì y
 * hệt cái vừa gây ra lỗi sáng nay, và một hàng rào quyền trôi thì không kêu.
 *
 * Đặt ở `src/lib/` chứ không ở `quan-tri/`: khu Soạn giáo trình không nằm dưới
 * khu Vận hành, nên bắt nó nhập từ thư mục của khu kia là dựng một phụ thuộc
 * ngược. Chuỗi vai trò không thuộc về khu nào cả.
 *
 * CÁC CHUỖI NÀY PHẢI KHỚP `backend/common/permissions.py` từng ký tự — chúng là
 * giá trị cột `users.role` trong CSDL, có dấu tiếng Việt. Phép kiểm
 * `e2e/unit/cong-quan-tri.test.mjs` đối chiếu lại với tệp .py ấy.
 */

export const VAI_QUAN_TRI = 'admin';
export const VAI_HOC_VU = 'Quản lý học vụ';
export const VAI_BIEN_TAP = 'Biên tập nội dung';
export const VAI_GIANG_VIEN = 'Giảng viên';
export const VAI_TRO_GIANG = 'Trợ giảng';
export const VAI_HOC_VIEN = 'Học viên';
