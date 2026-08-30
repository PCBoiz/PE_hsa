/**
 * proxy.ts — chuyển tiếp mọi lời gọi từ trình duyệt xuống Django.
 *
 * Trình duyệt gọi `/api/...` trên chính miền Vercel; hàm này đọc cookie, gắn
 * `Authorization: Bearer` rồi chuyển tiếp. Django nhận đúng thứ nó vẫn nhận từ
 * trước tới nay nên KHÔNG phải sửa một dòng nào.
 *
 * Hết hạn token được xử lý ngay tại đây: gặp 401 thì tự đổi refresh lấy access
 * mới, phát lại đúng một lần, rồi ghi cookie mới vào chính response đang trả.
 * Người dùng không thấy gì cả — trước đây việc này nằm ở pe-bridge.js phía
 * trình duyệt và có lúc đá người dùng ra ngoài oan khi hai lời gọi refresh
 * chạy song song.
 */
import { AT, RT, backendOrigin, refreshTokens, setTokenCookies } from '@/lib/auth';

/** Header không được chuyển tiếp: do fetch/hạ tầng tự quản. */
const STRIP = new Set([
  'host',
  'connection',
  'content-length',
  'transfer-encoding',
  'accept-encoding',
  'cookie', // token đi bằng Authorization, cookie không cần xuống Django
  // Danh tính CHỈ đến từ cookie httpOnly. Không loại header này thì một đoạn
  // script trên trang tự gắn `Authorization` là dùng được proxy như một tài
  // khoản khác, và lớp trung gian thôi không còn là nguồn định danh duy nhất.
  'authorization',
]);

function forwardHeaders(req: Request, access: string | null): Headers {
  const h = new Headers();
  req.headers.forEach((v, k) => {
    if (!STRIP.has(k.toLowerCase())) h.set(k, v);
  });
  if (access) h.set('Authorization', `Bearer ${access}`);
  // Django dựng URL tuyệt đối cho OAuth từ các header này.
  const proto = req.headers.get('x-forwarded-proto') || 'https';
  h.set('X-Forwarded-Proto', proto);
  return h;
}

function readCookie(req: Request, name: string): string | null {
  const raw = req.headers.get('cookie');
  if (!raw) return null;
  for (const part of raw.split(';')) {
    const i = part.indexOf('=');
    if (i > 0 && part.slice(0, i).trim() === name) return part.slice(i + 1).trim();
  }
  return null;
}

/** Response giữ nguyên thân + kiểu nội dung, bỏ header hạ tầng của Django. */
function passThrough(upstream: Response, body: ArrayBuffer): Response {
  const h = new Headers();
  upstream.headers.forEach((v, k) => {
    const lk = k.toLowerCase();
    if (lk === 'content-encoding' || lk === 'content-length' || lk === 'transfer-encoding') return;
    if (lk === 'set-cookie') return; // cookie của Django không dùng tới
    h.set(k, v);
  });
  return new Response(body, { status: upstream.status, headers: h });
}

/**
 * Ghép đường dẫn đích và BẮT BUỘC nó nằm trong tiền tố cho phép.
 *
 * Vì sao phải có hàm này (lỗ hổng ngày 27/08/2026, tự tay tôi tạo ra rồi tự
 * tìm thấy khi audit): bản đầu ghép chuỗi thẳng `${backendOrigin()}${path}`.
 * Trình duyệt gọi `/api/..%2f..%2fauth/login` thì Next trả đoạn đường dẫn là
 * `../../auth/login`, `fetch` rút gọn `..` và request đi tới `/auth/login` của
 * Django — tức là **vòng qua** đúng chỗ bóc token khỏi thân phản hồi. Kết quả
 * đo được: phản hồi chứa `access` và `refresh` dạng thô, JavaScript trên trang
 * đọc được. Toàn bộ lý do tồn tại của cookie httpOnly mất hiệu lực bằng một
 * chuỗi `..%2f`.
 *
 * Chặn bằng cách để chính bộ phân giải URL rút gọn `..` trước, RỒI mới kiểm
 * kết quả cuối có còn nằm trong tiền tố hay không — an toàn hơn là tự đi lọc
 * chuỗi, vì còn nhiều cách mã hoá khác của cùng ký tự.
 */
function safeTarget(path: string, search: string, prefix: string): string | null {
  const origin = backendOrigin();
  let u: URL;
  try {
    u = new URL(path + search, origin);
  } catch {
    return null;
  }
  if (u.origin !== new URL(origin).origin) return null;
  if (!u.pathname.startsWith(prefix)) return null;
  return u.toString();
}

export async function proxyToBackend(
  req: Request,
  path: string,
  prefix: string,
): Promise<Response> {
  const url = new URL(req.url);
  const target = safeTarget(path, url.search, prefix);
  if (!target) {
    return new Response(JSON.stringify({ error: 'Đường dẫn không hợp lệ' }), {
      status: 404,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // Thân request đọc thành buffer thay vì truyền luồng: payload của sản phẩm
  // đều nhỏ, và truyền luồng qua fetch đòi `duplex: 'half'` chưa được mọi
  // môi trường chạy Next hỗ trợ đồng đều.
  const body =
    req.method === 'GET' || req.method === 'HEAD' ? undefined : await req.arrayBuffer();

  const access = readCookie(req, AT);
  let upstream = await fetch(target, {
    method: req.method,
    headers: forwardHeaders(req, access),
    body,
    redirect: 'manual',
    cache: 'no-store',
  });

  // ── Access hết hạn → đổi refresh lấy cái mới, phát lại đúng MỘT lần ──
  let fresh: { access: string; refresh?: string } | null = null;
  if (upstream.status === 401) {
    const refresh = readCookie(req, RT);
    if (refresh) {
      fresh = await refreshTokens(refresh);
      if (fresh) {
        upstream = await fetch(target, {
          method: req.method,
          headers: forwardHeaders(req, fresh.access),
          body,
          redirect: 'manual',
          cache: 'no-store',
        });
      }
    }
  }

  const buf = await upstream.arrayBuffer();
  const res = passThrough(upstream, buf);
  if (fresh) setTokenCookies(res, fresh.access, fresh.refresh);
  return res;
}
