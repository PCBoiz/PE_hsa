import { serverJson } from '@/lib/server-api';
import { HD_TRANG, MOI_TRANG, type Trang } from '@/lib/thongBao';

import DanhSachThongBao from './DanhSachThongBao';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Thông báo | TopHSA' };

/**
 * `/thong-bao` — nơi xem lại MỌI thông báo (§61, bảng TopHSA dòng 27).
 *
 * Mọi vai đều vào được: chuông là của chung — học viên nhận bài tập mới và đổi lịch, giảng
 * viên nhận bài em nộp, trợ giảng nhận nhắc xem bản ghi. Máy chủ chỉ trả dòng CỦA CHÍNH
 * người đang đăng nhập (`WHERE user_id = request.user.id`), nên không cần gác vai ở đây.
 *
 * Trang đầu tải ngay trên máy chủ: chuông là thứ người ta mở rồi đóng trong mươi giây, và
 * bốn bước "HTML rỗng → JS → gọi API → vẽ" đủ lâu để họ đóng trước khi thấy gì.
 */
export default async function ThongBaoPage() {
  const d = await serverJson<Trang>(
    `/api/notifications/feed?limit=${MOI_TRANG}`,
    { requireAuth: true },
    HD_TRANG,
  );

  return (
    <main className="mx-auto max-w-3xl px-4 py-6">
      <h1 className="mb-1 text-section text-ink">Thông báo</h1>
      <p className="mb-4 text-small text-ink-3">
        Bài tập mới, đổi lịch học, nhắc xem bản ghi và thông báo của trung tâm.
      </p>
      <DanhSachThongBao
        dauTien={d.ok ? d.data : null}
        // Danh sách rỗng vì chưa có thông báo nào và rỗng vì không đọc được trông y hệt nhau.
        loiTai={d.ok ? null : d.message}
      />
    </main>
  );
}
