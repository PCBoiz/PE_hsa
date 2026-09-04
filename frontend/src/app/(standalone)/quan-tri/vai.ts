/**
 * Ai vào được trang nào trong khu Vận hành — MỘT bảng, dùng cho CẢ HAI việc.
 *
 * ── VÌ SAO GỘP LẠI (04/09/2026) ─────────────────────────────────────────────
 *
 * Trước hôm nay có HAI sự thật rời nhau về cùng một câu hỏi:
 *
 *   `layout.tsx`  · `if (me.data.role !== 'admin')` → chặn TẤT CẢ trừ quản trị
 *   `AdminNav`    · hiện đủ mọi tab cho bất kỳ ai qua được cổng trên
 *
 * Và một sự thật THỨ BA ở backend, khác cả hai: `/api/admin/classes` và
 * `/api/admin/terms` dùng `IsAdminOrAcademic` — tức `Quản lý học vụ` ĐƯỢC làm
 * hai việc ấy, vì xếp lớp và mở đợt học là việc hằng ngày của họ. Cổng ở đây
 * chặn họ khỏi chính hai trang backend vừa mở.
 *
 * Ba bảng cho một câu hỏi thì chúng sẽ lệch nhau; chúng đã lệch. Nay chỉ còn
 * bảng này, và nó khai vai trò NGAY CẠNH đường dẫn — thêm một trang mà quên
 * khai vai thì TypeScript không cho biên dịch.
 *
 * ── CỔNG NÀY KHÔNG PHẢI HÀNG RÀO AN NINH ────────────────────────────────────
 *
 * Hàng rào thật là `permission_classes` ở backend; không có `permission_classes`
 * thì mọi thứ ở đây chỉ là trang trí. Cổng này giải quyết một chuyện KHÁC: để
 * người không đủ quyền nhìn thấy câu "bạn không có quyền" thay vì thấy một
 * trang tải xong rồi mọi ô đều báo lỗi 403 — thứ trông y hệt hệ thống hỏng.
 */

export const VAI_QUAN_TRI = 'admin';
export const VAI_HOC_VU = 'Quản lý học vụ';

/** Vai được vào khu Soạn giáo trình (`/admin`) — xem `common/permissions.py`. */
export const VAI_BIEN_TAP = 'Biên tập nội dung';

export type Tab = {
  href: string;
  label: string;
  /** Vai trò vào được trang này. Phải khớp `permission_classes` của API nó gọi. */
  vai: readonly string[];
};

export const TABS: readonly Tab[] = [
  // `IsAdminRole` — bảng điều khiển toàn trung tâm (teaching/overview.py).
  { href: '/quan-tri/tong-quan', label: 'Toàn trung tâm', vai: [VAI_QUAN_TRI] },
  // `IsAdminRole` — đổi vai trò và đặt lại mật khẩu KHÔNG mở cho học vụ
  // (anh Sơn chốt 01/09/2026).
  { href: '/quan-tri/tai-khoan', label: 'Tài khoản', vai: [VAI_QUAN_TRI] },
  // `IsAdminOrAcademic` — teaching/views.py::AdminClassesView.
  { href: '/quan-tri/lop-hoc', label: 'Lớp học', vai: [VAI_QUAN_TRI, VAI_HOC_VU] },
  // `IsAdminOrAcademic` — teaching/terms.py.
  { href: '/quan-tri/dot-hoc', label: 'Đợt học', vai: [VAI_QUAN_TRI, VAI_HOC_VU] },
  // `IsAdminRole` — nhật ký kiểm toán (teaching/admin_users.py::AdminAuditView).
  { href: '/quan-tri/nhat-ky', label: 'Nhật ký', vai: [VAI_QUAN_TRI] },
  // Liên kết SANG khu khác, không phải trang của khu này.
  { href: '/admin', label: 'Soạn giáo trình', vai: [VAI_QUAN_TRI, VAI_BIEN_TAP] },
] as const;

/** Vai nào vào được khu này (bất kỳ trang nào của nó). */
export const VAI_VAO_KHU: readonly string[] = [VAI_QUAN_TRI, VAI_HOC_VU];

export function tabsCho(vai: string | undefined): Tab[] {
  return TABS.filter((t) => !!vai && t.vai.includes(vai));
}

export function duocVao(vai: string | undefined, cho: readonly string[]): boolean {
  return !!vai && cho.includes(vai);
}
