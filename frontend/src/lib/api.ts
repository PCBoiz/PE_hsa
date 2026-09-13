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

/**
 * Thân là CHUỖI mà không khai kiểu nội dung → trình duyệt tự gắn
 * `text/plain;charset=UTF-8`, và DRF trả **415 Unsupported Media Type**.
 *
 * ── VÌ SAO ĐẶT Ở ĐÂY, KHÔNG PHẢI Ở TỪNG NƠI GỌI (14/09/2026) ──────────────
 *
 * Rà luồng học viên đầu-cuối hôm nay: em bấm "Nộp bài" → màn hình hiện "Yêu
 * cầu không hợp lệ", máy chủ không ghi nhận gì. Quét cả `src/`: **bốn** lời
 * gọi cùng lỗi ấy — em nộp bài, giảng viên giao bài, sửa bài đã giao, và CHẤM
 * bài. Tức cả tính năng bài tập không dùng được qua giao diện, trong khi mọi
 * phép kiểm backend đều xanh (chúng gọi thẳng view với `format='json'`).
 *
 * Mười chín nơi gọi khác có khai header, nên lỗi không nhìn thấy được bằng
 * cách đọc một tệp: phải đọc cả hai mươi ba. Đặt mặc định ở đây thì nơi gọi
 * thứ hai mươi tư không thể quên. `FormData` (tải tệp) vẫn phải để trình duyệt
 * tự đặt `multipart/form-data; boundary=…` — nên chỉ chạm khi thân là chuỗi.
 */
function themKieuNoiDung(opts: RequestInit): RequestInit {
  if (typeof opts.body !== 'string') return opts;
  const h = new Headers(opts.headers);
  if (h.has('Content-Type')) return opts;
  h.set('Content-Type', 'application/json');
  return { ...opts, headers: h };
}

import { kiemHinhDang, type HinhDang } from '@/lib/kiemDang';

export async function apiFetch(path: string, opts: RequestInit = {}): Promise<Response> {
  const r = await fetch(path, {
    ...themKieuNoiDung(opts),
    credentials: 'same-origin', // cookie httpOnly phải đi cùng request
  });

  // Tài khoản còn mật khẩu tạm → máy chủ chặn mọi đường trừ bốn đường cho phép
  // (`accounts/authentication.py`). Đưa họ tới đúng nơi thay vì để 403 câm.
  //
  // `clone()` BẮT BUỘC: thân phản hồi chỉ đọc được MỘT lần, đọc ở đây là nơi
  // gọi nhận một luồng đã cạn. Chỉ tốn thêm một lần đọc trên đúng nhánh 403.
  if (r.status === 403 && typeof window !== 'undefined'
      && !window.location.pathname.startsWith('/doi-mat-khau')) {
    try {
      const d = (await r.clone().json()) as { mustChangePassword?: boolean };
      if (d?.mustChangePassword) window.location.href = '/doi-mat-khau?lan-dau=1';
    } catch {
      /* 403 vì lý do khác, thân không phải JSON — để nơi gọi tự xử */
    }
  }
  return r;
}

/**
 * GỌI GHI (POST/PATCH/PUT/DELETE) rồi đối chiếu phản hồi với hình dạng màn hình
 * mong đợi — T18 mức 2 cho chiều GHI (14/09/2026).
 *
 * ── VÌ SAO CHIỀU GHI CŨNG CẦN ─────────────────────────────────────────────
 *
 * Các màn ĐỌC đã có hình dạng từ sáng nay. Nhưng nhiều nút GHI cũng ĐỌC lại
 * phản hồi và hiện nó ra: "đặt lại mật khẩu" đọc `tempPassword` rồi bảo học vụ
 * đọc chuỗi ấy cho học viên; lưu điểm danh đọc `counts`/`marked` để nói "đã lưu
 * bao nhiêu"; nộp đề thi thử đọc cả tờ kết quả. Máy chủ đổi tên một khoá thì
 * học vụ đọc chữ "undefined" cho học viên chép, còn màn điểm danh báo "đã lưu 0
 * lượt" trong khi đã lưu đủ — hỏng theo kiểu KHÔNG kêu, đúng họ với hai lỗi
 * `klass`/`starts_at`.
 *
 * Ném `Error` chứ không trả union: mọi nơi gọi GHI ở đây đều đã nằm trong
 * `try/catch` + `loiBatDuoc`, nên ném là vào đúng đường hiển thị lỗi có sẵn.
 */
export async function ghiJson<T>(
  path: string,
  opts: RequestInit,
  hinhDang: HinhDang<T>,
): Promise<T> {
  const r = await apiFetch(path, opts);
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(errorText(r.status, body));
  const kq = kiemHinhDang(path, body, r.status, hinhDang);
  if (!kq.ok) throw new Error(kq.message);
  return kq.data;
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

/**
 * Câu lỗi để HIỆN CHO NGƯỜI DÙNG, từ một phản hồi hỏng.
 *
 * Tồn tại vì backend trả lỗi theo BA hình dạng khác nhau, và mỗi màn hình tự
 * đoán một kiểu:
 *   · `{error: "câu tiếng Việt"}`            — các view mới viết
 *   · `{error: {status, message, detail}}`   — common/errors.py, dùng cho 429,
 *                                              500 và mọi lỗi tầng DRF
 *   · `{errors: {ten_truong: "câu lỗi"}}`    — lỗi biểu mẫu
 *
 * Hậu quả đo được ngày 30/08/2026 khi chưa có hàm này: bấm "Đặt lại mật khẩu"
 * hay đổi vai trò lúc bị giới hạn tần suất → banner đỏ hiện đúng chữ
 * **`[object Object]`**, vì `d.error` là một đối tượng. Và ở đường khác thì hiện
 * "Máy chủ trả lỗi 500" — mã HTTP trần trên màn hình trợ giảng, vi phạm
 * RULES §10 (người đọc là trợ giảng và học sinh, không phải lập trình viên).
 *
 * Những câu lỗi công phu nhất trong cả repo — ví dụ đoạn giải thích vì sao có
 * trần 50 tài khoản mỗi mẻ và phải chia ra sao — chỉ tới được người dùng khi
 * hình dạng thứ nhất trúng. Hàm này khiến cả ba hình dạng đều tới nơi.
 */
const HTTP_VI: Record<number, string> = {
  400: 'Dữ liệu gửi lên chưa hợp lệ. Xem lại các ô vừa nhập.',
  401: 'Phiên đăng nhập đã hết. Đăng nhập lại rồi thử lại.',
  403: 'Tài khoản của bạn không có quyền làm việc này.',
  404: 'Không tìm thấy thứ bạn vừa mở. Có thể nó đã bị xoá — tải lại trang.',
  409: 'Dữ liệu vừa bị người khác thay đổi. Tải lại trang rồi thử lại.',
  413: 'Nội dung gửi lên quá lớn. Chia nhỏ ra rồi làm nhiều lần.',
  429: 'Bạn thao tác hơi nhanh. Chờ một phút rồi thử lại.',
  500: 'Hệ thống gặp lỗi. Thử lại; nếu vẫn vậy thì báo kỹ thuật.',
  502: 'Máy chủ đang khởi động lại. Chờ khoảng một phút rồi thử lại.',
  503: 'Hệ thống đang bận. Chờ một chút rồi thử lại.',
  504: 'Máy chủ trả lời quá chậm. Thử lại sau ít phút.',
};

export function errorText(status: number, data: unknown): string {
  const d = (data ?? {}) as { error?: unknown; errors?: unknown };

  if (typeof d.error === 'string' && d.error.trim()) return d.error;

  if (d.error && typeof d.error === 'object') {
    const msg = (d.error as { message?: unknown }).message;
    if (typeof msg === 'string' && msg.trim()) return msg;
  }

  if (d.errors && typeof d.errors === 'object') {
    const dau = Object.values(d.errors as Record<string, unknown>).find(
      (v) => typeof v === 'string' && v.trim(),
    );
    if (typeof dau === 'string') return dau;
  }

  return HTTP_VI[status] ?? 'Không thực hiện được. Thử lại, nếu vẫn vậy thì báo kỹ thuật.';
}

/**
 * Câu lỗi cho một ngoại lệ bắt được ở `catch`.
 *
 * VÌ SAO CẦN: mẫu `catch (e) { e instanceof Error ? e.message : 'câu tiếng Việt' }`
 * nằm ở 11 chỗ, và nó KHÔNG BAO GIỜ chạy tới vế tiếng Việt — `TypeError` mà
 * `fetch` ném khi mất mạng CŨNG là một `Error`, nên người dùng nhận đúng chuỗi
 * `"Failed to fetch"` của trình duyệt. Đo được 31/08/2026 bằng cách chặn lời
 * gọi ngay trong trình duyệt.
 *
 * Đây lại là lỗi hay gặp NHẤT ở một trung tâm chạy 4G chập chờn, và là lỗi duy
 * nhất hiện ra bằng tiếng Anh. `/login` đã có lời giải đúng từ trước; hàm này
 * mang lời giải đó ra dùng chung.
 */
export function loiBatDuoc(e: unknown, macDinh: string): string {
  if (e instanceof TypeError) {
    // `fetch` chỉ ném TypeError khi KHÔNG gửi đi được: mất mạng, DNS hỏng, CORS
    // chặn. Máy chủ trả lỗi thì `fetch` vẫn thành công — đường đó đi qua
    // `errorText`, không qua đây.
    return 'Không kết nối được tới máy chủ. Kiểm tra mạng rồi thử lại.';
  }
  if (e instanceof Error && e.message && !/^Failed to fetch$/i.test(e.message)) {
    return e.message;
  }
  return macDinh;
}
