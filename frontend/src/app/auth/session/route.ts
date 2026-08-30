/**
 * Nhận token sau khi đăng nhập bằng Google/Facebook rồi cất vào cookie.
 *
 * Vì sao phải có route riêng: backend trả token về qua **fragment** của URL
 * (`/auth/callback#access=...`). Fragment không bao giờ được gửi lên máy chủ —
 * đó là thiết kế của trình duyệt — nên chỉ JavaScript trên trang đọc được.
 * Trang callback đọc fragment rồi nộp vào đây; từ giây phút đó token nằm trong
 * cookie httpOnly và không đoạn script nào chạm tới được nữa.
 */
import { setTokenCookies } from '@/lib/auth';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function POST(req: Request): Promise<Response> {
  // Chỉ nhận lời gọi phát ra từ chính trang này. Không có kiểm tra đó thì một
  // trang web khác có thể ép trình duyệt người dùng nhận token của kẻ tấn công.
  const site = req.headers.get('sec-fetch-site');
  if (site && site !== 'same-origin') {
    return new Response(JSON.stringify({ error: 'Nguồn gọi không hợp lệ' }), {
      status: 403,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  let body: { access?: unknown; refresh?: unknown };
  try {
    body = (await req.json()) as { access?: unknown; refresh?: unknown };
  } catch {
    return new Response(JSON.stringify({ error: 'Dữ liệu không đọc được' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const access = typeof body.access === 'string' ? body.access : '';
  const refresh = typeof body.refresh === 'string' ? body.refresh : undefined;
  if (!access) {
    return new Response(JSON.stringify({ error: 'Thiếu token' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const res = new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
  setTokenCookies(res, access, refresh);
  return res;
}
