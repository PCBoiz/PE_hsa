import type { InputHTMLAttributes, ReactNode } from 'react';

/**
 * Ô nhập kèm nhãn.
 *
 * Ba ràng buộc không được bỏ:
 *  · Nhãn LUÔN hiện, không dùng placeholder thay nhãn. Placeholder biến mất
 *    ngay khi người dùng bắt đầu gõ, và lúc đó họ không còn biết ô này là ô gì.
 *  · Cỡ chữ 16px. Nhỏ hơn thì Safari trên iPhone tự phóng to cả trang khi
 *    người dùng chạm vào ô — trang nhảy, người dùng mất phương hướng.
 *  · Lỗi hiện NGAY DƯỚI ô sai, không gom lên đầu biểu mẫu. Và câu lỗi phải
 *    nói được cách sửa, không chỉ nói là sai.
 */
export default function Field({
  id,
  label,
  error,
  hint,
  icon,
  suffix,
  className = '',
  ...rest
}: {
  id: string;
  label: string;
  error?: string | null;
  hint?: string;
  icon?: ReactNode;
  suffix?: ReactNode;
} & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className="text-label text-ink-3">
        {label}
      </label>

      <div className="relative flex items-center">
        {icon && (
          <span className="pointer-events-none absolute left-3 grid place-items-center text-ink-3">
            {icon}
          </span>
        )}
        <input
          id={id}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
          className={[
            'min-h-11 w-full rounded-md border bg-sunken text-input text-ink',
            'placeholder:text-ink-3/70',
            'focus:outline-2 focus:outline-offset-0 focus:outline-brand',
            icon ? 'pl-10' : 'pl-3',
            suffix ? 'pr-12' : 'pr-3',
            error ? 'border-danger' : 'border-line',
            className,
          ]
            .filter(Boolean)
            .join(' ')}
          {...rest}
        />
        {suffix && <span className="absolute right-1 flex items-center">{suffix}</span>}
      </div>

      {error ? (
        <p id={`${id}-error`} role="alert" className="text-small text-danger">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="text-small text-ink-3">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
