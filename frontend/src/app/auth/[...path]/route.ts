/**
 * Cửa cho `/auth/*` — nơi token được BẮT LẠI và cất vào cookie httpOnly.
 *
 * Đăng nhập và đăng ký là hai chỗ duy nhất Django trả token ra ngoài. Ở đây
 * token được lấy khỏi thân phản hồi rồi cất vào cookie, nên JavaScript phía
 * trình duyệt không bao giờ nhìn thấy chúng. Phần còn lại của thân phản hồi
 * ({ok, name, needs_questionnaire}) giữ nguyên — `main.js` cũ chỉ đọc chừng đó
 * nên không phải sửa gì.
 */
import { RT, backendOrigin, refreshTokens, setTokenCookies } from '@/lib/auth';
import { proxyToBackend } from '@/lib/proxy';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

type Ctx = { params: Promise<{ path: string[] }> };

/** Các endpoint trả token trong thân phản hồi và được cấp cookie phiên.
 *
 *  BỎ 'register' ngày 27/08/2026. Từ khi tài khoản do trung tâm cấp, người gọi
 *  `/auth/register` là QUẢN TRỊ VIÊN đang tạo tài khoản cho học viên — cắm
 *  token của tài khoản vừa tạo vào cookie sẽ đá quản trị viên ra khỏi phiên
 *  của chính mình và đưa họ vào tài khoản học viên đó. */
const ISSUES_TOKENS = new Set(['login', 'oauth-complete']);

function readCookie(req: Request, name: string): string | null {
  const raw = req.headers.get('cookie');
  if (!raw) return null;
  for (const part of raw.split(';')) {
    const i = part.indexOf('=');
    if (i > 0 && part.slice(0, i).trim() === name) return part.slice(i + 1).trim();
  }
  return null;
}

async function handle(req: Request, ctx: Ctx): Promise<Response> {
  const { path } = await ctx.params;
  const seg = path.join('/');

  // ── /auth/refresh: refresh token nằm trong cookie, không nằm ở thân request ──
  if (seg === 'refresh') {
    const refresh = readCookie(req, RT);
    const fresh = refresh ? await refreshTokens(refresh) : null;
    if (!fresh) {
      return new Response(JSON.stringify({ error: 'Phiên đăng nhập đã hết hạn' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    const res = new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
    setTokenCookies(res, fresh.access, fresh.refresh);
    return res;
  }

  // ── Đăng nhập / đăng ký: chuyển tiếp rồi giữ token lại ──
  // `seg` được ghép thẳng vào URL ở dưới, và `ISSUES_TOKENS.has(seg)` đã ràng
  // nó vào một danh sách trắng — nhưng ràng thêm một lớp nữa cho chắc, vì đây
  // là nhánh cấp token.
  if (req.method === 'POST' && ISSUES_TOKENS.has(seg) && !seg.includes('/')) {
    const body = await req.arrayBuffer();
    const upstream = await fetch(`${backendOrigin()}/auth/${seg}`, {
      method: 'POST',
      headers: {
        'Content-Type': req.headers.get('content-type') || 'application/json',
        Accept: 'application/json',
      },
      body,
      cache: 'no-store',
    });

    const text = await upstream.text();
    if (!upstream.ok) {
      return new Response(text, {
        status: upstream.status,
        headers: { 'Content-Type': upstream.headers.get('content-type') || 'application/json' },
      });
    }

    let data: Record<string, unknown>;
    try {
      data = JSON.parse(text) as Record<string, unknown>;
    } catch {
      return new Response(text, { status: upstream.status });
    }

    const access = typeof data.access === 'string' ? data.access : undefined;
    const refresh = typeof data.refresh === 'string' ? data.refresh : undefined;
    delete data.access;
    delete data.refresh;

    const res = new Response(JSON.stringify(data), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
    if (access) setTokenCookies(res, access, refresh);
    return res;
  }

  return proxyToBackend(req, `/auth/${seg}`, '/auth/');
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const DELETE = handle;
