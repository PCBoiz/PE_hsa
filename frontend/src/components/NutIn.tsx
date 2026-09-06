'use client';

import { Button } from '@/components/ui';

/**
 * Nút in. Phải là client component vì `window.print()` chỉ có trên trình duyệt.
 *
 * Dùng chung cho CẢ HAI đường tới tờ báo cáo (giảng viên và phụ huynh) — nên
 * nó ở `components/` chứ không nằm trong thư mục của một tuyến. Chuyển ra đây
 * 07/09/2026 khi đường công khai ra đời.
 *
 * Cố ý KHÔNG sinh PDF ở máy chủ: hộp in của trình duyệt đã có sẵn mục "Lưu
 * thành PDF", giữ được đúng phông chữ tiếng Việt đang hiển thị, và cho giảng
 * viên xem trước trước khi gửi. Thêm một bộ sinh PDF phía máy chủ là thêm một
 * phông chữ phải cài trên Render, thêm một khác biệt giữa máy dev và
 * production, và thêm một chỗ nữa để hỏng — đổi lấy đúng một cú bấm.
 */
export default function NutIn() {
  return (
    <Button variant="ghost" onClick={() => window.print()}>
      In / Lưu PDF
    </Button>
  );
}
