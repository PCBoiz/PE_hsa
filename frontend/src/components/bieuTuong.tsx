/* ══════════════════════════════════════════════════════════════════════════
 * SINH TỰ ĐỘNG TỪ `public/static/js/icons.js` — ĐỪNG SỬA TAY.
 *
 * Vì sao có bản sao này. `icons.js` là một script THUẦN: nó quét `[data-icon]`
 * MỘT LẦN lúc `DOMContentLoaded` rồi thôi. React dựng sau mốc ấy (và dựng lại
 * mỗi lần điều hướng trong ứng dụng), nên ô biểu tượng do React tạo ra sẽ rỗng.
 * Đó là lý do `Topbar.tsx` từng để ô trống chờ script điền, còn màn chi tiết
 * khoá học thì bỏ cuộc và dùng emoji — hai màn không thể giống nhau được.
 *
 * Vì sao không sợ trôi. `e2e/unit/bieu-tuong-khop.test.mjs` đọc CẢ HAI tệp và
 * so từng đường path; lệch một ký tự là đỏ. Nên đây là bản sao ĐƯỢC ĐO, không
 * phải bản sao chép tay.
 *
 * Muốn đổi một biểu tượng: sửa `icons.js`, rồi chạy lại
 *     python scripts/sinh_bieu_tuong.py
 * ══════════════════════════════════════════════════════════════════════════ */

/** Đường vẽ SVG, khớp từng ký tự với `icons.js`. */
export const DUONG_VE: Record<string, string> = {
  home: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.8V20a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9.8"/><path d="M9.5 21v-6h5v6"/>',
  library: '<path d="M4 4v16"/><path d="M8 4v16"/><rect x="11.5" y="4" width="4.5" height="16" rx="1"/><path d="m18.6 5.4 2.6 14.1"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
  map: '<path d="m9 4 6 2.5L21 4v15l-6 2.5L9 19l-6 2.5V6z"/><path d="M9 4v15"/><path d="M15 6.5v15"/>',
  medal: '<path d="M7.21 15 2.66 7.14a2 2 0 0 1 .13-2.2L4.4 2.8A2 2 0 0 1 6 2h12a2 2 0 0 1 1.6.8l1.6 2.14a2 2 0 0 1 .14 2.2L16.79 15"/><circle cx="12" cy="17" r="5"/><path d="M12 17v.01"/>',
  chat: '<path d="M21 12a8 8 0 0 1-11.5 7.2L3 21l1.8-6.5A8 8 0 1 1 21 12z"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
  pencil: '<path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  shield: '<path d="M12 3l8 3v6c0 5-3.4 8.3-8 9.6C7.4 20.3 4 17 4 12V6z"/>',
  wrench: '<path d="M15.5 3.5a5.5 5.5 0 0 0-7 7L3 16v5h5l5.5-5.5a5.5 5.5 0 0 0 7-7l-3.2 3.2-2.8-.7-.7-2.8z"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>',
  moon: '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',
  bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
  "chevron-down": '<path d="m6 9 6 6 6-6"/>',
  user: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
  "log-out": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
};

/**
 * Một biểu tượng SVG. `currentColor` chứ không màu cứng: nút đổi màu chữ khi rê
 * chuột thì biểu tượng phải đổi theo — đó là điều emoji không bao giờ làm được.
 */
export function BieuTuong({ ten, co = 17 }: { ten: string; co?: number }) {
  const d = DUONG_VE[ten];
  // Tên sai thì KHÔNG vẽ ô trống im lặng — ô trống trông y như "đang tải".
  if (!d) return null;
  return (
    <svg
      width={co}
      height={co}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      dangerouslySetInnerHTML={{ __html: d }}
    />
  );
}
