import type { ButtonHTMLAttributes, ReactNode } from 'react';

/**
 * Nút bấm.
 *
 * Chiều cao tối thiểu 44px là RÀNG BUỘC, không phải lựa chọn thẩm mỹ: đó là
 * sàn vùng chạm cho ngón tay. Bản cũ có nút cao 29px trong khối kế hoạch và
 * người dùng điện thoại bấm trượt. Cỡ `sm` vẫn giữ 44px trên thiết bị cảm ứng,
 * chỉ nhỏ lại khi có con trỏ chuột thật.
 *
 * `--brand-fill` chứ không phải `--brand` cho nền đặc: bản nền tối của
 * `--brand` được làm sáng lên để chữ tím đọc được trên nền tối, nhưng lấy
 * chính nó làm NỀN thì chữ trắng chỉ còn tương phản 3.3:1.
 */
type Variant = 'primary' | 'ghost' | 'danger';
type Size = 'md' | 'sm';

const VARIANT: Record<Variant, string> = {
  primary: 'bg-brand-fill text-white hover:brightness-110 active:brightness-95',
  ghost:
    'bg-transparent text-ink-2 border border-line hover:border-brand hover:text-brand',
  danger: 'bg-danger text-white hover:brightness-110 active:brightness-95',
};

const SIZE: Record<Size, string> = {
  md: 'min-h-11 px-4 text-body',
  sm: 'min-h-11 px-3 text-small [@media(pointer:fine)]:min-h-9',
};

export default function Button({
  variant = 'primary',
  size = 'md',
  full = false,
  loading = false,
  children,
  className = '',
  disabled,
  ...rest
}: {
  variant?: Variant;
  size?: Size;
  full?: boolean;
  /** Đang chờ mạng: khoá nút để không gửi hai lần, và nói rõ đang chờ. */
  loading?: boolean;
  children: ReactNode;
} & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={[
        'inline-flex items-center justify-center gap-2 rounded-md font-semibold',
        'transition-[filter,border-color,color] duration-150',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand',
        // ĐANG CHỜ không phải BỊ KHOÁ, nên không mờ đi. `disabled:opacity-50`
        // dùng chung cho cả hai kéo chữ trắng trên nền tím xuống 2.15:1 (đo
        // 30/08/2026) — mà đây lại đúng là lúc người dùng nhìn nút lâu nhất,
        // khi mạng chậm và họ đang chờ xem có ăn thua gì không. Nút vẫn khoá
        // để không gửi hai lần (thuộc tính `disabled` ở trên), chỉ là trông
        // vẫn còn sống. Con trỏ đồng hồ cát nói "đang chạy", không phải "hỏng".
        loading ? 'cursor-wait' : 'disabled:opacity-50 disabled:cursor-not-allowed',
        VARIANT[variant],
        SIZE[size],
        full ? 'w-full' : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {loading && (
        <span
          aria-hidden="true"
          className="size-4 shrink-0 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
      )}
      {children}
    </button>
  );
}
