/**
 * Đăng xuất. `main.js` cũ điều hướng thẳng tới `/auth/logout` nên đường dẫn này
 * phải tồn tại và phải trả về một trang — ở đây là lệnh chuyển hướng về '/'.
 *
 * Trước đây việc này do một trang React làm: đọc token trong localStorage, gọi
 * backend rồi tự xoá. Nay token nằm trong cookie httpOnly nên chỉ máy chủ mới
 * xoá được — và đó cũng là điểm mạnh: một đoạn script lạ trên trang không thể
 * đăng xuất người dùng, mà cũng không thể đọc trộm token.
 */
import { RT, backendOrigin, clearTokenCookies } from '@/lib/auth';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

function readCookie(req: Request, name: string): string | null {
  const raw = req.headers.get('cookie');
  if (!raw) return null;
  for (const part of raw.split(';')) {
    const i = part.indexOf('=');
    if (i > 0 && part.slice(0, i).trim() === name) return part.slice(i + 1).trim();
  }
  return null;
}

async function handle(req: Request): Promise<Response> {
  const refresh = readCookie(req, RT);

  // Thu hồi refresh token ở backend — cố gắng, nhưng hỏng cũng vẫn đăng xuất:
  // người bấm "đăng xuất" phải luôn được đăng xuất, kể cả lúc backend đang ngủ.
  if (refresh) {
    try {
      await fetch(`${backendOrigin()}/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
        cache: 'no-store',
      });
    } catch {
      /* backend không với tới được — vẫn xoá cookie ở dưới */
    }
  }

  const res = new Response(null, {
    status: 303, // 303: sau POST cũng chuyển sang GET đúng cách
    headers: { Location: new URL('/', req.url).toString() },
  });
  clearTokenCookies(res);
  return res;
}

export const GET = handle;
export const POST = handle;
