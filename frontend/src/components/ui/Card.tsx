import type { ReactNode } from 'react';

/**
 * Thẻ — khối nội dung nổi trên nền trang.
 *
 * `tone="sunken"` dùng cho ô phụ nằm BÊN TRONG một thẻ khác (ô thống kê, ô
 * nhập). Lồng thẻ nổi trong thẻ nổi làm mắt không biết cái nào là cấp trên.
 */
export default function Card({
  children,
  tone = 'raised',
  padding = 'md',
  className = '',
  as: Tag = 'div',
}: {
  children: ReactNode;
  tone?: 'raised' | 'sunken' | 'flat';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  className?: string;
  as?: 'div' | 'section' | 'article' | 'li';
}) {
  const TONE = {
    raised: 'bg-surface border border-line shadow-e1',
    sunken: 'bg-sunken',
    flat: 'bg-surface border border-line',
  }[tone];

  const PAD = { none: '', sm: 'p-3', md: 'p-4', lg: 'p-6' }[padding];

  return (
    <Tag className={['rounded-lg', TONE, PAD, className].filter(Boolean).join(' ')}>
      {children}
    </Tag>
  );
}

/** Đầu thẻ: tiêu đề bên trái, hành động phụ bên phải. */
export function CardHead({
  title,
  hint,
  action,
}: {
  title: string;
  hint?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-3 flex flex-wrap items-start gap-3">
      <div className="min-w-0 flex-1">
        <h3 className="text-section text-ink">{title}</h3>
        {hint && <p className="mt-1 text-small text-ink-3">{hint}</p>}
      </div>
      {action}
    </div>
  );
}
