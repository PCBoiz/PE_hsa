/**
 * Cửa duy nhất cho mọi lời gọi `/api/*` từ trình duyệt.
 *
 * Nhờ có route này, JavaScript cũ trong `public/static/js` gọi `/api/...` bằng
 * đường dẫn tương đối là chạy đúng — không cần pe-bridge.js viết lại URL sang
 * miền khác nữa, và không đoạn script nào trên trang chạm được vào token.
 */
import { proxyToBackend } from '@/lib/proxy';

export const dynamic = 'force-dynamic'; // luôn gọi thật, không nằm cache dựng sẵn
export const runtime = 'nodejs';

type Ctx = { params: Promise<{ path: string[] }> };

async function handle(req: Request, ctx: Ctx): Promise<Response> {
  const { path } = await ctx.params;
  // Tiền tố `/api/` được ép ở lớp dưới (xem safeTarget trong src/lib/proxy.ts):
  // không có nó thì `..%2f` đi xuyên sang đường /auth/ và vòng qua chỗ bóc
  // token ra khỏi thân phản hồi.
  return proxyToBackend(req, `/api/${path.join('/')}`, '/api/');
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
export const HEAD = handle;
