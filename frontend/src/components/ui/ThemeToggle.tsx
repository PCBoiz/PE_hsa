'use client';

import { useCallback, useSyncExternalStore } from 'react';

/**
 * Nút đổi sáng/tối cho khu `(standalone)`.
 *
 * VÌ SAO CẦN MỘT BẢN RIÊNG. Nút của trang legacy nằm trong `Topbar.tsx` và gọi
 * `window.toggleTheme()` của `main.js`. Khu `(standalone)` cố ý KHÔNG nạp
 * main.js, nên suốt thời gian qua các màn quản trị, bài tập và đổi mật khẩu
 * **theo được chủ đề nhưng không đổi được** — giảng viên mở `/quan-tri/...` phải
 * quay về dashboard mới bật/tắt được bản tối. Đo 01/09/2026: `body.dark` áp
 * đúng ở cả 5 màn, `#theme-toggle` có ở 1.
 *
 * LUẬT PHẢI GIỐNG HỆT `main.js::applyTheme`, gồm cả class `light`:
 * `lesson_db_design.css` viết theo lối tối-trước và bản sáng nằm sau
 * `body.light`, nên chỉ gỡ class `dark` là chưa đủ.
 *
 * Trạng thái đầu đọc từ DOM chứ không từ `localStorage`: layout đã đặt class
 * trước khi React chạy (script chống nháy màu), nên DOM là nguồn đã tính đủ cả
 * "chưa chọn thì theo hệ điều hành". Đọc lại `localStorage` ở đây là dựng lại
 * cùng phép suy ở chỗ thứ hai — và hai bản sẽ trôi.
 *
 * `useSyncExternalStore` chứ không `useState` + `useEffect`: DOM ở đây là một
 * kho NGOÀI React, và bản `useEffect` đặt state ngay lúc gắn — một vòng render
 * thừa, và eslint bắt đúng (`react-hooks/set-state-in-effect`). Bản này còn
 * được thêm một thứ: `MutationObserver` giữ nút KHỚP với chủ đề kể cả khi thứ
 * khác đổi nó (main.js trên trang legacy, hoặc một tab khác đã chuyển).
 */
const dangKy = (goi: () => void) => {
  const mo = new MutationObserver(goi);
  mo.observe(document.body, { attributes: true, attributeFilter: ['class'] });
  return () => mo.disconnect();
};

const docDOM = () => document.body.classList.contains('dark');
/* Máy chủ không có `document`. Trả `false` để bản dựng sẵn khớp với nhánh
   "sáng"; lượt đồng bộ đầu ở trình duyệt sẽ chỉnh lại nếu đang tối. */
const docMayChu = () => false;

export default function ThemeToggle({ className = '' }: { className?: string }) {
  const toi = useSyncExternalStore(dangKy, docDOM, docMayChu);

  const doi = useCallback(() => {
    const moi = !document.body.classList.contains('dark');
    document.body.classList.toggle('dark', moi);
    document.body.classList.toggle('light', !moi);
    try {
      localStorage.setItem('theme', moi ? 'dark' : 'light');
    } catch {
      /* chế độ riêng tư chặn ghi — vẫn đổi được cho phiên này */
    }
    // Không `setState`: `MutationObserver` ở trên thấy class đổi và tự đồng bộ.
  }, []);

  return (
    <button
      type="button"
      onClick={doi}
      /* `min-h-11` = 44px: đây là đích chạm, và khu này mở nhiều trên máy tính
         bảng ở trung tâm. */
      className={`inline-flex min-h-11 min-w-11 items-center justify-center rounded-md
        border border-line text-ink-2 hover:border-brand hover:text-brand-ink ${className}`}
      title={toi ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối'}
      aria-label={toi ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối'}
      aria-pressed={toi}
    >
      {/* SVG chứ không emoji: emoji do phông màu của HỆ ĐIỀU HÀNH vẽ nên không
          nhận `currentColor`, và ở bản tối nó giữ nguyên màu của bản sáng. */}
      {toi ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      )}
    </button>
  );
}
