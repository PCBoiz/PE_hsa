'use client';

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';

/**
 * Thông báo ngắn.
 *
 * Hai điều bắt buộc, đều vì lý do tiếp cận:
 *  · `aria-live="polite"` để trình đọc màn hình đọc lên — nhưng KHÔNG cướp
 *    tiêu điểm bàn phím, vì người dùng có thể đang gõ dở.
 *  · Tự tắt sau 4 giây, và vẫn có nút đóng cho người đọc chậm.
 *
 * Thay cho `alert()` đang dùng ở 7 chỗ trong mã cũ: `alert` chặn cả trang, mất
 * hết ngữ cảnh, và trên điện thoại thì xấu.
 */
type Tone = 'ok' | 'error' | 'info';
type Item = { id: number; text: string; tone: Tone };

const Ctx = createContext<(text: string, tone?: Tone) => void>(() => {});

export function useToast() {
  return useContext(Ctx);
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Item[]>([]);

  const push = useCallback((text: string, tone: Tone = 'info') => {
    setItems((prev) => [...prev, { id: Date.now() + Math.random(), text, tone }]);
  }, []);

  return (
    <Ctx.Provider value={push}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex flex-col items-center gap-2 px-4"
      >
        {items.map((t) => (
          <ToastItem
            key={t.id}
            item={t}
            onDone={() => setItems((prev) => prev.filter((x) => x.id !== t.id))}
          />
        ))}
      </div>
    </Ctx.Provider>
  );
}

function ToastItem({ item, onDone }: { item: Item; onDone: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDone, 4000);
    return () => clearTimeout(t);
  }, [onDone]);

  const TONE = {
    ok: 'border-success/40 text-success',
    error: 'border-danger/40 text-danger',
    info: 'border-line text-ink-2',
  }[item.tone];

  return (
    <div
      className={`pointer-events-auto flex max-w-[min(92vw,440px)] items-start gap-3 rounded-md border bg-surface px-4 py-3 text-body shadow-e2 ${TONE}`}
    >
      <span className="flex-1">{item.text}</span>
      <button
        type="button"
        onClick={onDone}
        aria-label="Đóng thông báo"
        className="-my-1 -mr-1 grid size-11 shrink-0 place-items-center rounded-sm text-ink-3 hover:text-ink"
      >
        <svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M6 18 18 6M6 6l12 12" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  );
}
