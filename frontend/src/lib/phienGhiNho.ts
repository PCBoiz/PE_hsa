/**
 * THỜI HẠN COOKIE PHIÊN theo ô "Ghi nhớ đăng nhập" (góp ý TopHSA #1, 24/09/2026).
 *
 * Backend đặt claim `nho` vào refresh token khi người dùng tick ô ghi nhớ, và
 * SimpleJWT chép claim ấy sang access token (`backend/accounts/ghi_nho.py`).
 * Ở đây chọn thời hạn cookie theo claim:
 *
 *   · có `nho` → cookie có Max-Age: access = tuổi token (30 phút), refresh = thời
 *                gian còn lại tới `exp` (≤ 30 ngày). Máy riêng — mở lại trình
 *                duyệt vẫn còn đăng nhập.
 *   · không    → cookie PHIÊN (không Max-Age): đóng trình duyệt là hết. Máy dùng
 *                chung ở trung tâm — người sau không mở được tài khoản người trước.
 *
 * Đọc claim KHÔNG xác minh chữ ký — cùng lối với `conHan` ở `src/proxy.ts`: chỉ
 * để chọn thời hạn cookie. Thẩm quyền thật vẫn là Django, xác minh mọi lời gọi.
 * Token lạ / hỏng → cookie phiên (mặc định an toàn hơn, không ném).
 *
 * Tệp THUẦN (không import Next): hai nơi ghi cookie — `setTokenCookies` ở
 * `lib/auth.ts` và `src/proxy.ts` — cùng gọi, và phép kiểm gọi thẳng được.
 */

/** Tuổi access token — khớp `ACCESS_TOKEN_LIFETIME` ở `backend/config/settings.py`. */
export const TUOI_ACCESS = 30 * 60;
/** Trần refresh khi ghi nhớ — khớp `HAN_GHI_NHO` ở `backend/accounts/ghi_nho.py`. */
export const TRAN_GHI_NHO = 30 * 24 * 60 * 60;

function docClaims(token: string | undefined): Record<string, unknown> | null {
  const phan = (token ?? '').split('.');
  if (phan.length !== 3) return null;
  try {
    const p: unknown = JSON.parse(Buffer.from(phan[1], 'base64url').toString('utf8'));
    return p && typeof p === 'object' ? (p as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

/**
 * Max-Age (giây) cho cookie của `token`, hoặc `undefined` = cookie phiên.
 * `loai`: `'access'` sống đúng tuổi token; `'refresh'` sống tới `exp` của nó.
 */
export function hanCookie(token: string | undefined, loai: 'access' | 'refresh'): number | undefined {
  const c = docClaims(token);
  if (c?.nho !== true) return undefined;
  if (loai === 'access') return TUOI_ACCESS;
  const conLai = typeof c.exp === 'number' ? Math.floor(c.exp - Date.now() / 1000) : 0;
  return conLai > 0 ? Math.min(conLai, TRAN_GHI_NHO) : undefined;
}
