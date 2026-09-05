/**
 * Gọi một hàm toàn cục của tầng JS cũ — CHỜ nó tới nếu chưa có.
 *
 * ── LỖI THẬT, TÁI HIỆN ĐƯỢC (05/09/2026) ────────────────────────────────────
 *
 * `Topbar` được React dựng và gắn handler NGAY, còn `main.js` thì
 * `LegacyScripts` chèn SAU khi markup mount và nạp bất đồng bộ. Giữa hai mốc ấy
 * có một cửa sổ: handler đã sống, hàm nó gọi thì chưa.
 *
 * Chứng minh bằng cách giữ chậm `main.js` 6 giây rồi chạm vào ô tìm kiếm:
 *
 *     bấm ô  → W(...).showSearchSuggestions is not a function
 *     gõ chữ → W(...).filterCourses is not a function
 *
 * Trên máy này cửa sổ ấy chỉ ~200ms nên hiếm khi trúng. Nhưng dashboard nạp SÁU
 * tệp script thực thi nối tiếp (`icons`, `roadmapData`, `roadmap`, `main`,
 * `chatbot`, `dashboard` — riêng `main.js` và `dashboard.js` đã 5.200 dòng), và
 * trên điện thoại mạng chậm cửa sổ ấy tính bằng GIÂY. Đúng lúc một người sốt
 * ruột bấm vào ô tìm kiếm.
 *
 * ── VÌ SAO KHÔNG CHỈ THÊM `?.` ──────────────────────────────────────────────
 *
 * `W().filterCourses?.()` hết ném, nhưng cú bấm BIẾN MẤT: người dùng gõ, không
 * gì xảy ra, không gì giải thích. Đó là đổi một lỗi ồn lấy một lỗi câm — cả
 * phiên làm việc này đi sửa đúng chuyện ấy.
 *
 * Ở đây có sẵn một tín hiệu tử tế: `LegacyScripts` phát `pe:legacy-ready` trên
 * `document` sau khi mọi script đã nạp. Nên chờ nó rồi gọi — cú bấm sớm được
 * THỰC HIỆN, chỉ là muộn vài trăm mili giây.
 *
 * Quá hạn thì báo ra console: script không bao giờ tới là một sự cố thật, và im
 * lặng ở đó chính là cách trợ lý chat chết ba tuần mà không ai biết.
 */

/** Bao lâu thì thôi chờ. Dài hơn một lượt nạp chậm, ngắn hơn kiên nhẫn con người. */
const HAN_MS = 8000;

type HamCu = (...a: unknown[]) => unknown;

function layHam(ten: string): HamCu | null {
  const w = window as unknown as Record<string, unknown>;
  return typeof w[ten] === 'function' ? (w[ten] as HamCu) : null;
}

/**
 * Gọi `window[ten](...doi)`. Có sẵn thì gọi ngay; chưa có thì chờ
 * `pe:legacy-ready` rồi gọi.
 */
export function goiLegacy(ten: string, ...doi: unknown[]): void {
  if (typeof window === 'undefined') return;

  const ngay = layHam(ten);
  if (ngay) {
    ngay(...doi);
    return;
  }

  let xong = false;
  const chay = () => {
    if (xong) return;
    xong = true;
    document.removeEventListener('pe:legacy-ready', chay);
    clearTimeout(hen);
    const f = layHam(ten);
    if (f) f(...doi);
    // Script đã nạp xong mà hàm vẫn không có → tên sai hoặc tệp thiếu.
    // Nói ra; đây đúng là lớp lỗi mà im lặng làm mất ba tuần.
    else console.error(`[goiLegacy] "${ten}" không tồn tại dù script cũ đã nạp xong.`);
  };

  const hen = setTimeout(() => {
    if (xong) return;
    xong = true;
    document.removeEventListener('pe:legacy-ready', chay);
    console.error(`[goiLegacy] chờ "${ten}" quá ${HAN_MS}ms — script cũ chưa nạp xong.`);
  }, HAN_MS);

  document.addEventListener('pe:legacy-ready', chay);
}

/** Bản dùng trong `onClick`/`onInput`: trả một handler đã gắn sẵn tên hàm. */
export const goiKhiBam = (ten: string, ...doi: unknown[]) => () => goiLegacy(ten, ...doi);
