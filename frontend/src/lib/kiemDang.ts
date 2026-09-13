/**
 * ĐỐI CHIẾU HÌNH DẠNG dữ liệu máy chủ trả về — dùng được ở CẢ HAI phía.
 *
 * Tách khỏi `server-api.ts` ngày 14/09/2026 vì tệp ấy nhập `next/navigation` và
 * `next/headers`: nhập nó vào một component `'use client'` là kéo theo cả tầng
 * máy chủ. Ở đây không nhập gì ngoài `errorText`, nên màn hình phía trình duyệt
 * dùng chung được đúng một bộ luật — và MỘT câu lỗi, thay vì hai câu khác nhau
 * tuỳ chỗ sự cố xảy ra.
 *
 * `server-api.ts` xuất lại `HinhDang` và `kiemHinhDang` từ đây, nên mọi nơi
 * đang nhập từ đó không phải đổi.
 */

/**
 * Kết quả một lượt gọi. `status` là mã HTTP; `null` nghĩa là chưa tới được máy
 * chủ (backend ngủ, mạng hỏng) — khác hẳn "máy chủ trả lời rằng không được".
 */
export type Ket<T> =
  | { ok: true; data: T }
  | { ok: false; status: number | null; message: string };

/**
 * HÌNH DẠNG dữ liệu mà một màn hình mong đợi — bất cứ thứ gì có `safeParse`
 * (zod là bản dùng thật; kiểu viết tối thiểu để tệp này không nhập zod).
 */
export type HinhDang<T> = {
  safeParse: (v: unknown) =>
    | { success: true; data: T }
    | { success: false; error: { issues: ReadonlyArray<{ path: ReadonlyArray<PropertyKey>; message: string }> } };
};

/** `sessions[0].startsAt` — đường tới ô lệch, viết cho người đọc lỗi. */
export function duongLech(path: ReadonlyArray<PropertyKey>): string {
  return path.map((p) => (typeof p === 'number' ? `[${p}]` : `.${String(p)}`)).join('').replace(/^\./, '') || '(gốc)';
}

/**
 * Đối chiếu thân phản hồi 2xx với hình dạng màn hình mong đợi. Tách riêng để
 * `e2e/unit/hinh-dang.test.mjs` gọi được mà không cần dựng request của Next.
 */
export function kiemHinhDang<T>(
  path: string,
  body: unknown,
  status: number,
  hinhDang: HinhDang<T>,
): Ket<T> {
  const kq = hinhDang.safeParse(body);
  if (kq.success) return { ok: true, data: kq.data };
  // Ba ô đầu là đủ để tìm ra chỗ lệch; in hết là một bức tường chữ.
  const o = kq.error.issues.slice(0, 3).map((i) => `${duongLech(i.path)}: ${i.message}`);
  // Log ĐẦY ĐỦ (máy chủ giữ stdout; trình duyệt thì hiện ở console của người
  // đang gặp lỗi) — câu trên màn chỉ cần đủ để người dùng biết đây là lỗi lệch
  // mã, không phải lỗi của họ.
  console.error('[hinh-dang] %s trả dữ liệu khác mong đợi: %s', path, o.join(' · '));
  return {
    ok: false,
    status,
    message: `Máy chủ trả dữ liệu khác hình dạng màn hình này mong đợi (${o[0]}). `
      + 'Mã màn hình và máy chủ đang lệch nhau — báo kỹ thuật giúp nhé.',
  };
}
