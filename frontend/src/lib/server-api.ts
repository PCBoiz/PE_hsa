import { cache } from 'react';
import { redirect } from 'next/navigation';

import { errorText } from '@/lib/api';
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
  // Thiếu access mà VẪN CÒN refresh thì chưa phải hết phiên — `src/middleware.ts`
  // lẽ ra đã làm mới trước khi tới đây. Chỉ đá về đăng nhập khi không còn gì cả.
  // Bản trước đá đi ngay khi thiếu access, và vì cookie `pe_at` có Max-Age đúng
  // bằng tuổi thọ token (30 phút) nên phiên 8 tiếng thực chất chỉ sống 30 phút.
  if (!access && !(await readRefresh()) && requireAuth) redirect('/login');

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
      const kq = refresh ? await refreshOnce(refresh) : null;
      if (kq?.ok) {
        res = await call(kq.access);
      } else if (!kq || kq.lyDo === 'invalid') {
        // CHỈ đá về đăng nhập khi máy chủ đã xem token và TỪ CHỐI nó.
        // `unreachable` (Render khởi động lại, Neon cold-start, 5xx) thì giữ
        // nguyên phiên và để trang tự xử lý như mọi lần backend không với tới
        // được — refresh token còn sống bảy tiếng rưỡi, không có lý do gì bỏ.
        phienHetHan = true;
      }
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

/**
 * Kết quả một lời gọi: hoặc có dữ liệu, hoặc có một câu giải thích ĐỌC ĐƯỢC.
 *
 * `status` là mã HTTP; `null` nghĩa là chưa tới được máy chủ (backend đang ngủ,
 * mạng hỏng) — khác hẳn với "máy chủ trả lời rằng không được", và màn hình cần
 * phân biệt hai chuyện đó để nói đúng.
 */
export type Ket<T> =
  | { ok: true; data: T }
  | { ok: false; status: number | null; message: string };

/**
 * Gọi và đọc JSON.
 *
 * ── Vì sao KHÔNG còn trả `null` ────────────────────────────────────────────
 * Bản trước là `if (!res || !res.ok) return null`, tức mọi thứ hỏng đều rơi vào
 * cùng một giá trị: 400 kèm hướng dẫn sửa, 403 không đủ quyền, 500 sập CSDL, và
 * backend đang ngủ — bốn chuyện khác hẳn nhau, màn hình nhận đúng một `null`.
 *
 * Backend viết sẵn những câu tử tế (`Ngày "from" không hợp lệ (định dạng
 * YYYY-MM-DD)`) và chúng bị vứt ngay tại đây. Hậu quả đo được ngày 30/08/2026 ở
 * `/quan-tri/nhat-ky?from=abc`: trang hiện HAI câu mâu thuẫn cùng lúc — "Không
 * đọc được nhật ký" và "Chưa có hành động nào" — tải lại vẫn hỏng mãi, và ô
 * chọn Hành động rỗng đi nên KHÔNG CÒN NÚT NÀO bấm để thoát; người dùng phải tự
 * sửa URL. Một lỗi gõ nhầm ngày biến thành một màn hình chết.
 *
 * Kiểu trả về là union có thẻ, nên `tsc` bắt buộc mọi nơi gọi phải xử lý nhánh
 * hỏng — không thể vô tình bỏ qua như khi `null` lẫn vào cùng kiểu dữ liệu.
 *
 * Câu lỗi dựng bằng `errorText` — CÙNG hàm mà các màn hình phía trình duyệt
 * dùng, để một sự cố không ra hai lời khác nhau tuỳ chỗ nó xảy ra.
 */
export async function serverJson<T>(path: string, opts: Options = {}): Promise<Ket<T>> {
  const res = await serverFetch(path, opts);
  if (!res) {
    return {
      ok: false,
      status: null,
      message: 'Chưa kết nối được máy chủ. Thử tải lại sau ít phút.',
    };
  }

  let body: unknown = null;
  let docDuoc = true;
  try {
    body = await res.json();
  } catch {
    // Thân rỗng hoặc không phải JSON. Với phản hồi hỏng thì bình thường (một số
    // lỗi hạ tầng trả HTML), nhưng với phản hồi 2xx thì chính nó là sự cố.
    docDuoc = false;
  }

  // Tài khoản còn mật khẩu tạm: máy chủ chặn MỌI đường trừ bốn đường cho phép
  // (`accounts/authentication.py`). Không đưa họ tới đúng nơi thì họ gặp một
  // bức tường 403 ở mọi trang và không có cách nào đoán ra việc cần làm.
  //
  // `redirect()` nằm NGOÀI mọi khối try — Next chuyển hướng bằng cách NÉM một
  // lỗi đặc biệt, một `catch` bắt tất sẽ nuốt mất nó (xem chú thích ở
  // `serverFetch`). Ở đây đã ngoài try, giữ nguyên như vậy.
  if (res.status === 403
      && (body as { mustChangePassword?: boolean } | null)?.mustChangePassword) {
    redirect('/doi-mat-khau');
  }

  if (!res.ok) {
    return { ok: false, status: res.status, message: errorText(res.status, body) };
  }
  if (!docDuoc) {
    return {
      ok: false,
      status: res.status,
      message: 'Máy chủ trả về dữ liệu không đọc được. Báo kỹ thuật giúp nhé.',
    };
  }
  return { ok: true, data: body as T };
}

/** Đã đăng nhập hay chưa — dùng để chọn nhánh hiển thị ngay trên máy chủ. */
export async function isSignedIn(): Promise<boolean> {
  return (await readAccess()) !== null;
}
