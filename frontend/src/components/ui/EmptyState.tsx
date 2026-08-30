import type { ReactNode } from 'react';

/**
 * Trạng thái rỗng.
 *
 * Bắt buộc có `action` hoặc `hint`: một khung trống ghi "Chưa có dữ liệu" là
 * ngõ cụt — người dùng không biết phải làm gì tiếp. Ở sản phẩm này còn có một
 * dạng rỗng đặc biệt và rất quan trọng: **chưa đủ dữ liệu để đánh giá**. Hệ
 * thống cố ý KHÔNG chấm điểm một chủ đề khi mới có một lần làm bài, và phải
 * nói thẳng lý do thay vì hiện số 0 — số 0 ở đó là nói dối học viên.
 */
export default function EmptyState({
  title,
  hint,
  action,
  tone = 'neutral',
}: {
  title: string;
  hint?: string;
  action?: ReactNode;
  /** 'measuring' = chưa đủ dữ liệu để đo, không phải "không có gì". */
  tone?: 'neutral' | 'measuring';
}) {
  return (
    <div
      className={`flex flex-col items-start gap-2 rounded-md px-4 py-6 ${
        tone === 'measuring' ? 'bg-brand-soft' : 'bg-sunken'
      }`}
    >
      <p className={`text-subhead ${tone === 'measuring' ? 'text-brand-ink' : 'text-ink'}`}>
        {title}
      </p>
      {hint && <p className="max-w-[52ch] text-body text-ink-3">{hint}</p>}
      {action}
    </div>
  );
}
