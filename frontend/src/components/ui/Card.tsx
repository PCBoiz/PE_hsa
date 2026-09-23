import type { ReactNode } from 'react';
import { BieuTuong } from '@/components/bieuTuong';

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

/**
 * Đầu thẻ: tiêu đề bên trái, hành động phụ bên phải.
 *
 * `hint` là MỘT dòng nói điều người dùng cần để dùng thẻ này — không quá 90 ký
 * tự (`e2e/unit/chu-nguoi-dung.test.mjs` đo). Lời giải thích dài hơn mà vẫn
 * đáng giữ thì đưa vào `chiTiet`: nó nằm gập sau nút "Chi tiết", ai cần mới mở.
 *
 * Vì sao có `chiTiet` (24/09/2026): TopHSA dùng thử và chê "nhiều chữ, màn đầu
 * rối". Đo khi ấy: 32 câu `hint` quá 90 ký tự, câu dài nhất 197 — nhiều thẻ mở
 * đầu bằng một đoạn văn xám mà người vận hành phải lướt qua mỗi ngày.
 */
export function CardHead({
  title,
  hint,
  chiTiet,
  action,
}: {
  title: string;
  hint?: string;
  chiTiet?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="mb-3 flex flex-wrap items-start gap-3">
      {/* `basis-56` (14rem) chứ không để co tự do (21/09/2026): `flex-1 min-w-0`
          cho khối tiêu đề co tới 0 nên hàng nút KHÔNG bao giờ xuống dòng — ở
          390px đầu khung soạn bài đo được tiêu đề rộng 17px, cao 205px (8 dòng)
          và câu nhắc 24 dòng, ô nhập đầu tiên rơi xuống y=1.156. Có mốc tối
          thiểu thì thiếu chỗ là hàng nút xuống dòng, tiêu đề giữ bề ngang. */}
      <div className="min-w-0 flex-1 basis-56">
        {/* h2, không h3: thẻ là mục cấp một dưới h1 của trang. axe-core
            `heading-order` đỏ ở 9 trang (20/09/2026) vì h1 → h3 bỏ cấp. */}
        <h2 className="text-section text-ink">{title}</h2>
        {hint && <p className="mt-1 text-small text-ink-3">{hint}</p>}
        {/* `<details>` chứ không state: gập/mở bằng bàn phím sẵn, trình đọc
            màn hình báo đúng "đã mở/đã đóng", không cần JS phía trình duyệt
            (thẻ này dựng cả ở máy chủ). Cùng lối khối gập của bộ soạn bài.
            `list-none` + ẩn `::-webkit-details-marker`: bỏ tam giác mặc định
            (mỗi trình duyệt vẽ một kiểu) để dùng mũi tên của bộ biểu tượng.
            `min-h-11` — sàn vùng chạm 44px như `Button`. */}
        {chiTiet && (
          <details className="group mt-1">
            <summary className="inline-flex min-h-11 cursor-pointer list-none items-center gap-1 rounded-sm text-small font-medium text-ink-2 hover:text-brand-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand [&::-webkit-details-marker]:hidden">
              <span className="-rotate-90 transition-transform group-open:rotate-0 motion-reduce:transition-none">
                <BieuTuong ten="chevron-down" co={14} />
              </span>
              Chi tiết
            </summary>
            <div className="max-w-[70ch] pb-1 text-small text-ink-2">{chiTiet}</div>
          </details>
        )}
      </div>
      {action}
    </div>
  );
}
