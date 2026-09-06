'use client';

import { useSyncExternalStore } from 'react';

/**
 * Đọc và đổi chủ đề sáng/tối — MỘT bản, dùng chung.
 *
 * ── VÌ SAO TÁCH RA (06/09/2026) ─────────────────────────────────────────────
 *
 * Cùng một phép logic từng nằm ở BA chỗ: `main.js::applyTheme`,
 * `course_detail.js` (bản sao gần như từng chữ), và `ui/ThemeToggle.tsx`. Khi
 * khung điều hướng gộp về một component thì sắp có chỗ thứ tư — nên tách.
 *
 * ── HAI LUẬT DỄ QUÊN, ĐÃ TRẢ GIÁ ────────────────────────────────────────────
 *
 * ① Phải đặt CẢ `light` lẫn `dark`. `lesson_db_design.css` viết theo lối
 *    tối-trước và bản sáng nằm sau `body.light`, nên chỉ gỡ class `dark` là
 *    trang bài học kẹt ở bản tối.
 *
 * ② Trạng thái đầu đọc từ DOM, KHÔNG đọc `localStorage`. Script chống nháy màu
 *    ở layout đã chạy trước React và đã tính đủ cả nhánh "chưa chọn thì theo hệ
 *    điều hành". Đọc lại `localStorage` ở đây là dựng lại cùng phép suy ở chỗ
 *    thứ hai — và hai bản sẽ trôi khỏi nhau.
 */

const dangKy = (goi: () => void) => {
  // `MutationObserver` chứ không chỉ state: chủ đề còn bị đổi bởi thứ NGOÀI
  // React (main.js trên trang legacy), và nút phải khớp trong cả trường hợp đó.
  const mo = new MutationObserver(goi);
  mo.observe(document.body, { attributes: true, attributeFilter: ['class'] });
  return () => mo.disconnect();
};

const docDOM = () => document.body.classList.contains('dark');

/* Máy chủ không có `document`. Trả `false` để bản dựng sẵn khớp với nhánh
   "sáng"; lượt đồng bộ đầu ở trình duyệt sẽ chỉnh lại nếu đang tối. */
const docMayChu = () => false;

/**
 * `true` khi đang ở bộ màu tối. Tự cập nhật kể cả khi JS cũ đổi chủ đề.
 *
 * Tiền tố `use` là BẮT BUỘC dù mọi tên khác trong kho này là tiếng Việt: đây
 * thật sự là một hook, và `react-hooks/rules-of-hooks` nhận diện hook bằng quy
 * ước tên. Đặt tên `dangToi` thì luật báo lỗi, và cách chữa duy nhất còn lại là
 * `eslint-disable` — tức tắt một luật đang nói đúng. Đổi tên rẻ hơn nhiều.
 */
export function useDangToi(): boolean {
  return useSyncExternalStore(dangKy, docDOM, docMayChu);
}

/** Đảo chủ đề và ghi nhớ lựa chọn. Không trả gì: `dangToi()` tự thấy. */
export function doiChuDe(): void {
  const moi = !document.body.classList.contains('dark');
  document.body.classList.toggle('dark', moi);
  document.body.classList.toggle('light', !moi);
  try {
    localStorage.setItem('theme', moi ? 'dark' : 'light');
  } catch {
    /* chế độ riêng tư chặn ghi — vẫn đổi được cho phiên này */
  }
}
