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
export async function refreshTokens(
  refresh: string,
): Promise<{ access: string; refresh?: string } | null> {
  try {
    const r = await fetch(`${backendOrigin()}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
      cache: 'no-store',
    });
    if (!r.ok) return null;
    const d = (await r.json()) as { access?: string; refresh?: string };
    return d?.access ? { access: d.access, refresh: d.refresh } : null;
  } catch {
    return null;
  }
}
