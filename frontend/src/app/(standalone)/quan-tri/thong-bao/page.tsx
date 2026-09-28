import { serverJson } from '@/lib/server-api';
import { HD_TRANG_TRUNG_TAM, type TrangTrungTam } from '@/lib/thongBaoSoan';

import ThongBaoTrungTam from './ThongBaoTrungTam';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Thông báo trung tâm | TopHSA' };

/**
 * `/quan-tri/thong-bao` — học vụ soạn và gửi thông báo cho cả khối (§61, dòng 27).
 *
 * MỘT lượt gọi mang về cả ba thứ màn cần: danh sách đã soạn, DANH MỤC đối tượng (lớp + môn,
 * khoá `chon`), và trạng thái Zalo OA. Danh mục đến từ máy chủ chứ không gõ lại ở màn
 * (RULES §7) — bảng ba môn HSA sống ở `courses.truy_cap.BA_MON`, và một bản chép sang React
 * sẽ trôi khỏi nó ngay lần TopHSA mở môn thứ tư.
 *
 * Không có cổng vai ở đây: `layout.tsx` cạnh tệp này làm cổng, cùng lối với bốn trang khác
 * của khu.
 */
export default async function ThongBaoTrungTamPage() {
  const d = await serverJson<TrangTrungTam>('/api/admin/thong-bao', { requireAuth: true }, HD_TRANG_TRUNG_TAM);

  return (
    <ThongBaoTrungTam
      dauTien={d.ok ? d.data : null}
      // Danh sách rỗng vì chưa gửi gì và rỗng vì không đọc được trông y hệt nhau.
      loiTai={d.ok ? null : d.message}
    />
  );
}
