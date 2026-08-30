import { redirect } from 'next/navigation';

import { backendOrigin, readAccess, readRefresh, refreshTokens } from '@/lib/auth';

/**
 * server-api.ts — gọi dữ liệu ngay trên máy chủ, lúc đang dựng trang.
 *
 * Đây là phần "khoẻ hơn" của lần chuyển này. Trước đây mọi màn hình đi theo
 * đường: trình duyệt tải HTML rỗng → tải JavaScript → chạy JavaScript → mới
 * gọi dữ liệu → vẽ. Người dùng nhìn khung trống suốt bốn bước đó, và mỗi lượt
 * gọi Neon mất khoảng 245 ms nên khung trống không hề ngắn.
 *
 * Với hàm này, máy chủ Next gọi Django **trước** rồi mới trả HTML — trang tới
 * nơi là đã có nội dung. Máy chủ Next (Vercel) và Django (Render) đều ở Mỹ,
 * nên chặng gọi này còn nhanh hơn chặng từ điện thoại một học sinh ở Hà Nội.
 *
 * Lưu ý khi dùng: hàm này chỉ chạy trong Server Component hoặc route handler.
 * Gọi từ component 'use client' sẽ lỗi lúc dựng bản — đúng như mong muốn.
 */

type Options = {
  /** Không có token, hoặc token hỏng → đá về /login thay vì trả null. */
  requireAuth?: boolean;
};

export async function serverFetch(
  path: string,
  { requireAuth = false }: Options = {},
): Promise<Response | null> {
  const access = await readAccess();
  if (!access && requireAuth) redirect('/login');

  const call = (token: string | null) =>
    fetch(`${backendOrigin()}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      cache: 'no-store', // dữ liệu học tập thay đổi liên tục, không được cache
    });

  try {
    let res = await call(access);

    // Access hết hạn: thử refresh một lần. KHÔNG ghi cookie mới được ở đây —
    // Server Component không có quyền đặt cookie. Lượt này vẫn ra dữ liệu
    // đúng; cookie sẽ được cập nhật ở lời gọi /api/* kế tiếp qua proxy.
    if (res.status === 401) {
      const refresh = await readRefresh();
      const fresh = refresh ? await refreshTokens(refresh) : null;
      if (fresh) res = await call(fresh.access);
      else if (requireAuth) redirect('/login');
    }

    return res;
  } catch {
    return null; // backend đang ngủ hoặc mạng hỏng — nơi gọi tự xử lý
  }
}

/** Gọi và đọc JSON. Trả null khi bất kỳ khâu nào hỏng. */
export async function serverJson<T>(path: string, opts: Options = {}): Promise<T | null> {
  const res = await serverFetch(path, opts);
  if (!res || !res.ok) return null;
  try {
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/** Đã đăng nhập hay chưa — dùng để chọn nhánh hiển thị ngay trên máy chủ. */
export async function isSignedIn(): Promise<boolean> {
  return (await readAccess()) !== null;
}
