/**
 * Cửa cho tệp lịch `.ics` (§71, 26/09/2026): `/lich/<chìa>.ics` → backend.
 *
 * VÌ SAO PHẢI CÓ ĐƯỜNG NÀY. Tuyến thật nằm ở Django, còn địa chỉ phát cho người
 * dùng lại dựng trên tên miền của trang web — không có route này thì Next trả
 * 404 và ứng dụng lịch IM LẶNG bỏ qua, người dùng chỉ thấy "lịch trống" mà không
 * có dòng lỗi nào. (Đo 26/09: `/lich/abc.ics` trên Next = 404 trong khi cùng
 * đường ấy ở backend trả đúng 404 "không tìm thấy lịch" — hai cái 404 khác nghĩa
 * nhau, và chỉ lần mở màn thật mới lộ ra.)
 *
 * Đi qua tên miền trang web chứ không phát thẳng địa chỉ máy chủ Django: người
 * dùng dán địa chỉ này vào điện thoại MỘT lần và nó sống nhiều tháng — đổi nhà
 * cung cấp máy chủ mà chìa vẫn chạy thì mới đáng gọi là "thêm một lần".
 *
 * Không đính kèm cookie hay token: chìa nằm trong đường dẫn là đủ, và ứng dụng
 * lịch của điện thoại vốn không mang theo phiên đăng nhập nào.
 */
import { proxyToBackend } from '@/lib/proxy';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

type Ctx = { params: Promise<{ chia: string }> };

async function handle(req: Request, ctx: Ctx): Promise<Response> {
  const { chia } = await ctx.params;
  // `encodeURIComponent` để một chìa bịa đặt mang `..%2f` không trèo sang đường
  // khác; `safeTarget` trong proxy còn kiểm lại tiền tố một lần nữa.
  return proxyToBackend(req, `/lich/${encodeURIComponent(chia)}`, '/lich/');
}

export const GET = handle;
export const HEAD = handle;
