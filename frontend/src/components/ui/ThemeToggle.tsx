'use client';

import { useCallback } from 'react';

import { doiChuDe, useDangToi } from '@/lib/chuDe';

/**
 * Nút đổi sáng/tối cho khu `(standalone)`.
 *
 * VÌ SAO CẦN MỘT BẢN RIÊNG. Khu này cố ý KHÔNG nạp `main.js`, nên suốt thời
 * gian qua các màn quản trị, bài tập và đổi mật khẩu **theo được chủ đề nhưng
 * không đổi được** — giảng viên mở `/quan-tri/...` phải quay về dashboard mới
 * bật/tắt được bản tối. Đo 01/09/2026: `body.dark` áp đúng ở cả 5 màn,
 * `#theme-toggle` có ở 1.
 *
 * PHẦN LOGIC ĐÃ RA `@/lib/chuDe` (06/09/2026). Cùng một phép logic từng nằm ở
 * ba chỗ — `main.js`, `course_detail.js`, và tệp này — và khi khung điều hướng
 * gộp về `AppShell` thì sắp có chỗ thứ tư. Ở đây nay chỉ còn phần HÌNH DẠNG
 * (nút Tailwind của khu ERP); `AppShell` có hình dạng riêng của nó nhưng gọi
 * đúng hai hàm này.
 */

export default function ThemeToggle({ className = '' }: { className?: string }) {
  const toi = useDangToi();

  const doi = useCallback(() => doiChuDe(), []);

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
