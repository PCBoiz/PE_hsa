import { cache } from 'react';
import { redirect } from 'next/navigation';

import { backendOrigin, readAccess, readRefresh, refreshTokens } from '@/lib/auth';

/**
 * server-api.ts — gọi dữ liệu ngay trên máy chủ, lúc đang dựng trang.
 *
 * Đây là phần "khoẻ hơn" của lần chuyển này. Trước đây mọi màn hình đi theo
 * đường: trình duyệt tải HTML rỗng → tải JavaScript → chạy JavaScript → mới
 * gọi dữ liệu → vẽ. Người dùng nhìn khung trống suốt bốn bước đó.
 *
 * Với hàm này, máy chủ Next gọi Django **trước** rồi mới trả HTML — trang tới
 * nơi là đã có nội dung. Máy chủ Next (Vercel) và Django (Render) đều ở Mỹ, và
 * Render cùng vùng với Neon nên chặng gọi này dưới 5ms.
 *
 * Chỉ chạy trong Server Component hoặc route handler. Gọi từ component
 * 'use client' sẽ lỗi lúc dựng bản — đúng như mong muốn.
 */

type Options = {
  /** Không có token, hoặc token hỏng → đá về /login thay vì trả null. */
  requireAuth?: boolean;
};

/**
 * Đổi refresh lấy access mới — GỘP mọi lời gọi trùng trong cùng một lượt dựng
 * trang thành MỘT.
 *
 * BẮT BUỘC phải gộp, vì `SIMPLE_JWT` bật `ROTATE_REFRESH_TOKENS` kèm
 * `BLACKLIST_AFTER_ROTATION` (config/settings.py): mỗi lần làm mới thành công
 * sẽ VÔ HIỆU HOÁ refresh token cũ. Mà một trang thường gọi vài `serverJson`
 * song song trong `Promise.all` — cả nhóm cùng gặp 401, cùng đọc một refresh
 * token trong cookie, rồi cùng gửi đi làm mới. Cái nào xong trước sẽ giết token
 * mà những cái còn lại đang cầm, nên chúng chết hàng loạt.
 *
 * Lỗi này chỉ lộ ra sau khi access token hết hạn (30 phút), tức là gần như
 * không bao giờ thấy trong lúc phát triển và luôn thấy với người dùng thật.
 * Tìm ra 30/08/2026 khi mở lại màn hình điểm danh sau nửa tiếng.
 *
 * `cache()` của React gộp theo tham số trong phạm vi MỘT lượt dựng trang — đúng
 * phạm vi cần, và tự tan khi lượt đó xong nên không giữ token trong bộ nhớ.
 */
const refreshOnce = cache(async (refresh: string) => refreshTokens(refresh));

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

  let res: Response | null = null;
  let phienHetHan = false;

  try {
    res = await call(access);

    // Access hết hạn: thử làm mới một lần. KHÔNG ghi cookie mới được ở đây —
    // Server Component không có quyền đặt cookie. Lượt này vẫn ra dữ liệu đúng;
    // cookie sẽ được cập nhật ở lời gọi /api/* kế tiếp qua lớp trung gian.
    if (res.status === 401) {
      const refresh = await readRefresh();
      const fresh = refresh ? await refreshOnce(refresh) : null;
      if (fresh) res = await call(fresh.access);
      else phienHetHan = true;
    }
  } catch {
    return null; // backend đang ngủ hoặc mạng hỏng — nơi gọi tự xử lý
  }

  // `redirect()` PHẢI nằm ngoài khối try.
  //
  // Next chuyển hướng bằng cách NÉM một lỗi đặc biệt, nên một `catch` bắt tất
  // như ở trên sẽ nuốt mất nó. Bản trước gọi `redirect()` ngay trong try, và
  // hậu quả là phiên hết hạn KHÔNG đá người dùng về trang đăng nhập mà lặng lẽ
  // trả `null` — màn hình điểm danh hiện "bạn không phải giảng viên phụ trách
  // lớp này" cho một giảng viên đúng là đang phụ trách lớp đó. Câu trả lời sai,
  // và sai theo hướng khiến người ta đi hỏi nhầm chỗ.
  if (phienHetHan && requireAuth) redirect('/login');

  return res;
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
