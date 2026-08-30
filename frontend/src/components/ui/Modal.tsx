'use client';

import { useEffect, useRef, type ReactNode } from 'react';

/**
 * Hộp thoại.
 *
 * Dùng thẻ `<dialog>` của trình duyệt thay vì tự dựng lớp phủ: trình duyệt lo
 * sẵn phần khó — bẫy tiêu điểm bàn phím, phím Esc, và khoá phần nền khỏi trình
 * đọc màn hình. Tự viết lại mấy thứ đó gần như luôn sai ở đâu đó.
 *
 * Chuyển động: vào 220ms, ra 150ms. Ra nhanh hơn vào là có chủ đích — người
 * dùng đã quyết định đóng rồi thì đừng bắt họ chờ.
 */
export default function Modal({
  open,
  onClose,
  title,
  children,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    if (!open && el.open) el.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(e) => {
        // Bấm ra ngoài để đóng: `<dialog>` coi cả vùng nền là chính nó, nên so
        // sánh target với chính thẻ dialog là cách nhận biết cú bấm ngoài.
        if (e.target === ref.current) onClose();
      }}
      className={[
        'w-[min(92vw,520px)] rounded-lg border border-line bg-surface p-0 text-ink-2 shadow-e3',
        'backdrop:bg-black/40 backdrop:backdrop-blur-[2px]',
        'open:animate-[modal-in_220ms_var(--ease-out-soft)]',
      ].join(' ')}
    >
      <div className="flex items-start gap-3 border-b border-line px-6 py-4">
        <h2 className="flex-1 text-section text-ink">{title}</h2>
        <button
          type="button"
          onClick={onClose}
          aria-label="Đóng"
          className="grid size-11 shrink-0 place-items-center rounded-md text-ink-3 hover:bg-sunken hover:text-ink"
        >
          <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M6 18 18 6M6 6l12 12" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      <div className="px-6 py-4 text-body">{children}</div>

      {footer && (
        <div className="flex flex-wrap justify-end gap-2 border-t border-line px-6 py-4">
          {footer}
        </div>
      )}

      <style>{`
        @keyframes modal-in {
          from { opacity: 0; transform: translateY(8px) scale(.98); }
          to   { opacity: 1; transform: none; }
        }
      `}</style>
    </dialog>
  );
}
