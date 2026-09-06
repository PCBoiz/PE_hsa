import { cache } from 'react';

import { serverJson } from '@/lib/server-api';

/**
 * Đọc vai của người đang đăng nhập — tách khỏi `./vai.ts` có chủ đích.
 *
 * `vai.ts` là BẢNG: tab, vai, hai hàm tra. Nó phải nạp được bằng Node thuần để
 * `e2e/unit/cong-quan-tri.test.mjs` đối chiếu nó với `permission_classes` bên
 * backend. Gộp hàm này vào đó thì bảng kéo theo `serverJson` → `next/headers`
 * → cả bộ nạp của Next, và phép kiểm phải dựng một nửa framework chỉ để đọc
 * một mảng hằng số. Hàng rào nào khó kiểm thì rốt cuộc sẽ không được kiểm.
 */

export type KetVai =
  /** `ten` để thanh chung hiện đúng ai đang đăng nhập — xem `layout.tsx`. */
  | { ok: true; vai: string | undefined; ten: string | undefined }
  | { ok: false; loi: string };

/**
 * Đọc vai của người đang đăng nhập.
 *
 * `cache()` của React gói lại để layout khu và layout con của từng trang gọi
 * bao nhiêu lần cũng chỉ tốn MỘT lượt hỏi backend trong cùng một request —
 * không có nó thì mỗi cổng thêm vào là thêm một vòng gọi mạng cho mỗi lần tải
 * trang, và cái giá ấy tăng đúng theo số cổng mình dựng thêm.
 */
export const layVai = cache(async (): Promise<KetVai> => {
  const me = await serverJson<{ role?: string; name?: string }>('/api/user', { requireAuth: true });
  // Không đọc được tài khoản KHÔNG đồng nghĩa với "không đủ quyền": backend sập
  // hay mạng hỏng cũng rơi vào đây, và nói "bạn không có quyền" lúc đó là đẩy
  // người dùng đi hỏi nhầm chỗ. Tách hai câu ra.
  if (!me.ok) return { ok: false, loi: me.message };
  /* `ten` lấy luôn từ CÙNG lượt gọi này. Khu Vận hành không nạp `dashboard.js`
     nên không có ai điền `#chip-name` hộ — không lấy ở đây thì chip người dùng
     trên thanh sẽ mang chữ "?" giữa một khu mà việc chính là quản lý CON NGƯỜI. */
  return { ok: true, vai: me.data.role, ten: me.data.name };
});
