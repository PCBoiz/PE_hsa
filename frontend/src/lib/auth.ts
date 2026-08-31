/**
 * auth.ts — nơi DUY NHẤT biết token nằm ở đâu.
 *
 * Trước 27/08/2026 token JWT nằm trong `localStorage`, nên mọi màn hình đều
 * phải tải xong JavaScript rồi mới gọi được dữ liệu — người dùng nhìn khung
 * trống vài giây. Và bất kỳ đoạn script nào chạy trên trang cũng đọc được token.
 *
 * Nay token nằm trong cookie `httpOnly`: JavaScript phía trình duyệt KHÔNG đọc
 * được, còn máy chủ Next đọc được nên dựng sẵn nội dung trước khi trả trang.
 *
 * Vì sao Next làm trung gian thay vì để trình duyệt gọi thẳng Django:
 * frontend ở vercel.app còn backend ở onrender.com — hai tên miền khác nhau,
 * nên cookie sẽ là cookie bên thứ ba và Safari trên iPhone chặn. Cho trình
 * duyệt chỉ nói chuyện với Vercel thì cookie thành cùng miền, chạy ở mọi trình
 * duyệt. Django không phải sửa gì: lớp trung gian đọc cookie rồi tự gắn
 * `Authorization: Bearer` đúng như trước.
 */
import { cookies } from 'next/headers';

export const AT = 'pe_at'; // access token
export const RT = 'pe_rt'; // refresh token

/** Gốc backend Django. KHÔNG có tiền tố NEXT_PUBLIC_ → không lộ ra trình duyệt. */
export function backendOrigin(): string {
  return (
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL || // tương thích ngược lúc chuyển đổi
    'http://localhost:9000'
  );
}

const PROD = process.env.NODE_ENV === 'production';

/** Vòng đời cookie: access ngắn, refresh dài — khớp cấu hình SimpleJWT. */
export const COOKIE_BASE = {
  httpOnly: true,
  sameSite: 'lax' as const,
  secure: PROD,
  path: '/',
};
/* Khớp ĐÚNG vòng đời token trong config/settings.py (SIMPLE_JWT):
   access 30 phút, refresh 8 giờ. Cho cookie sống lâu hơn token là để lại trong
   máy người dùng một mẩu dữ liệu đã chết — access hết hạn thì lớp trung gian
   tự đổi refresh lấy cái mới, còn refresh hết hạn thì phải đăng nhập lại. */
export const AT_MAX_AGE = 30 * 60;
export const RT_MAX_AGE = 8 * 60 * 60;

/** Đọc access token phía máy chủ (Server Component, route handler). */
export async function readAccess(): Promise<string | null> {
  const jar = await cookies();
  return jar.get(AT)?.value ?? null;
}

export async function readRefresh(): Promise<string | null> {
  const jar = await cookies();
  return jar.get(RT)?.value ?? null;
}

/** Gắn cặp token vào response. Bỏ trống refresh thì giữ nguyên cái đang có. */
export function setTokenCookies(res: Response, access?: string, refresh?: string): void {
  const parts: string[] = [];
  const flags = `Path=/; HttpOnly; SameSite=Lax${PROD ? '; Secure' : ''}`;
  if (access) parts.push(`${AT}=${access}; ${flags}; Max-Age=${AT_MAX_AGE}`);
  if (refresh) parts.push(`${RT}=${refresh}; ${flags}; Max-Age=${RT_MAX_AGE}`);
  for (const p of parts) res.headers.append('Set-Cookie', p);
}

export function clearTokenCookies(res: Response): void {
  const flags = `Path=/; HttpOnly; SameSite=Lax${PROD ? '; Secure' : ''}; Max-Age=0`;
  res.headers.append('Set-Cookie', `${AT}=; ${flags}`);
  res.headers.append('Set-Cookie', `${RT}=; ${flags}`);
}

/**
 * Đổi refresh token lấy access token mới.
 * Trả null khi refresh cũng hỏng — người gọi phải coi như đã đăng xuất.
 */
/**
 * Kết quả làm mới phiên. `lyDo` PHẢI phân biệt được hai chuyện:
 *  · `'invalid'`  — máy chủ trả lời rằng refresh token hỏng/đã thu hồi. Phiên
 *                   hết thật, đá về đăng nhập là đúng.
 *  · `'unreachable'` — chưa hỏi được máy chủ (mất mạng, Render khởi động lại,
 *                   Neon đang thức dậy, 5xx). Phiên có thể vẫn còn nguyên.
 */
export type KetLamMoi =
  | { ok: true; access: string; refresh?: string }
  | { ok: false; lyDo: 'invalid' | 'unreachable' };

/**
 * Đổi refresh token lấy access token mới.
 *
 * VÌ SAO TRẢ UNION CHỨ KHÔNG TRẢ `null`. Bản trước trả `null` cho CẢ HAI: fetch
 * ném (backend không với tới được) và `!r.ok` (backend trả 5xx). Bên gọi
 * (`server-api.ts`) chỉ thấy `null` nên kết luận "phiên hết hạn" và đá người
 * dùng về `/login`.
 *
 * Hậu quả thật: access token sống 30 phút. Render khởi động lại hoặc Neon
 * cold-start (chính `common/db.py` ghi 5–20 giây để Neon thức) rơi đúng vào lúc
 * đó thì giảng viên đang giữa buổi bị văng ra màn đăng nhập — trong khi refresh
 * token còn sống bảy tiếng rưỡi.
 *
 * Đây là ẢNH SOI GƯƠNG của chính lỗi mà `server-api.ts` đã vá ở tầng trên: ở đó
 * `serverJson` tách rất kỹ `status: null` với `status: 4xx`, rồi đánh mất đúng
 * sự phân biệt đó ở tầng làm mới này.
 */
export async function refreshTokens(refresh: string): Promise<KetLamMoi> {
  let r: Response;
  try {
    r = await fetch(`${backendOrigin()}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
      cache: 'no-store',
    });
  } catch {
    return { ok: false, lyDo: 'unreachable' };
  }

  // 401/403 = máy chủ ĐÃ xem token và từ chối → phiên hết thật.
  // 5xx và mọi mã khác = máy chủ chưa trả lời được → chưa kết luận gì.
  if (!r.ok) {
    return { ok: false, lyDo: r.status === 401 || r.status === 403 ? 'invalid' : 'unreachable' };
  }
  let d: { access?: string; refresh?: string };
  try {
    d = (await r.json()) as { access?: string; refresh?: string };
  } catch {
    return { ok: false, lyDo: 'unreachable' };
  }
  return d?.access
    ? { ok: true, access: d.access, refresh: d.refresh }
    : { ok: false, lyDo: 'invalid' };
}
