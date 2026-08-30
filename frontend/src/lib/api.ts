/**
 * api.ts — gọi dữ liệu từ phía TRÌNH DUYỆT (component 'use client').
 *
 * Từ 27/08/2026 hàm này gần như không còn việc gì để làm, và đó là chủ đích.
 * Trước đây nó phải tự dựng URL tuyệt đối sang miền backend, đọc token trong
 * localStorage gắn vào header, rồi tự đổi refresh token khi gặp 401 — mỗi
 * bước là một chỗ có thể sai khác với pe-bridge.js đang làm y hệt bên cạnh.
 *
 * Nay `/api/...` là đường dẫn trên chính miền đang đứng; máy chủ Next đọc
 * cookie httpOnly và lo phần xác thực (src/lib/proxy.ts). Ở đây chỉ còn việc
 * gọi fetch và nhớ gửi kèm cookie.
 *
 * Cần dữ liệu ngay lúc dựng trang thì đừng dùng hàm này — dùng `serverFetch`
 * trong src/lib/server-api.ts, nội dung sẽ có sẵn trong HTML thay vì phải chờ
 * thêm một vòng gọi mạng sau khi trang đã hiện.
 */

export async function apiFetch(path: string, opts: RequestInit = {}): Promise<Response> {
  return fetch(path, {
    ...opts,
    credentials: 'same-origin', // cookie httpOnly phải đi cùng request
  });
}

/** Gọi và tự đọc JSON. Trả null khi lỗi — nơi gọi quyết định hiển thị gì. */
export async function apiJson<T>(path: string, opts: RequestInit = {}): Promise<T | null> {
  try {
    const r = await apiFetch(path, opts);
    if (!r.ok) return null;
    return (await r.json()) as T;
  } catch {
    return null;
  }
}
