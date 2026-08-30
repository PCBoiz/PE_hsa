import type { ReactNode } from 'react';

/**
 * Ô số thống kê.
 *
 * Ba điều đã cân nhắc kỹ:
 *
 * 1. Số dùng phông đơn cách + `tabular-nums`. Trong một hàng ô thống kê hoặc
 *    một cột bảng, chữ số phải thẳng hàng — nếu không, mắt phải đọc từng con
 *    số thay vì quét cả cột. Đây là chức năng, không phải sở thích.
 *
 * 2. Số 26px so với nhãn 13px. Bản cũ để số 20px và nhãn 11px — chênh lệch
 *    quá nhỏ nên mắt không biết đọc cái nào trước.
 *
 * 3. `tone="warn"` chỉ được dùng KHI SỐ LỚN HƠN 0. Một bảng lúc nào cũng đỏ
 *    thì mắt bỏ qua ngay, và cảnh báo mất hết tác dụng. Quy tắc này có từ
 *    bảng điều khiển lớp và phải giữ.
 */
export default function Tile({
  value,
  label,
  tone = 'neutral',
  hint,
}: {
  value: ReactNode;
  label: string;
  tone?: 'neutral' | 'warn' | 'good';
  hint?: string;
}) {
  const TONE = {
    neutral: 'bg-sunken',
    warn: 'bg-warning/10',
    good: 'bg-success/10',
  }[tone];

  // Bộ `-ink` chứ không phải màu gốc: nền ở đây là bản pha 10% của chính màu
  // đó, và màu gốc đặt lên nền ấy chỉ đạt 4.2–4.5:1 (xem theme.css).
  const NUM = {
    neutral: 'text-ink',
    warn: 'text-warning-ink',
    good: 'text-success-ink',
  }[tone];

  return (
    <div className={`rounded-md px-4 py-3 ${TONE}`}>
      <b
        className={`block font-mono text-[26px] leading-[1.2] font-bold tracking-[-0.02em] tabular-nums ${NUM}`}
      >
        {value}
      </b>
      <span className="mt-1 block text-small text-ink-3">{label}</span>
      {hint && <span className="mt-1 block text-label text-ink-3 normal-case">{hint}</span>}
    </div>
  );
}

/** Hàng ô thống kê — tự xuống dòng, không bao giờ ép trang trượt ngang. */
export function TileRow({ children }: { children: ReactNode }) {
  return (
    <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,140px),1fr))]">
      {children}
    </div>
  );
}
