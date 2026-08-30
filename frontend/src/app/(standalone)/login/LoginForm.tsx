'use client';

import { useState } from 'react';

import { Button, Field } from '@/components/ui';

/**
 * Biểu mẫu đăng nhập.
 *
 * Viết lại 27/08/2026, thay cho login.inline.js. Ba thứ bỏ đi có chủ đích:
 *
 *  · 30 hạt bay lơ lửng dựng bằng JavaScript — chạy liên tục, tốn pin, và
 *    không nói lên điều gì.
 *  · Hiệu ứng gợn sóng khi bấm nút — bản mô phỏng Material Design trên một
 *    sản phẩm không dùng Material.
 *  · Lớp phủ "Đăng nhập thành công" chờ 1,5 giây rồi mới chuyển trang. Bắt
 *    người dùng nhìn một hoạt cảnh trước khi cho vào là lấy mất thời gian của
 *    họ để đổi lấy thứ họ không cần.
 *
 * Giữ lại: hiện lỗi ĐÚNG DƯỚI ô sai (bản cũ đã làm đúng), phím Enter để gửi,
 * và các thông báo lỗi OAuth trên thanh địa chỉ.
 */

const OAUTH_ERRORS: Record<string, string> = {
  email_exists: 'Email này đã có tài khoản đặt bằng mật khẩu. Hãy đăng nhập bằng mật khẩu.',
  google_failed: 'Đăng nhập Google không thành công. Thử lại giúp tôi.',
  facebook_failed: 'Đăng nhập Facebook không thành công. Thử lại giúp tôi.',
  oauth_failed: 'Đăng nhập không thành công. Thử lại giúp tôi.',
  het_han: 'Phiên đăng nhập đã hết hạn. Đăng nhập lại để tiếp tục.',
  chua_co_tai_khoan:
    'Email này chưa có tài khoản trên hệ thống. Liên hệ trung tâm để được cấp tài khoản.',
};

type FieldErrors = { email?: string; password?: string };

/**
 * `oauthError` do Server Component đọc từ thanh địa chỉ rồi truyền xuống.
 *
 * Bản trước đọc `window.location.search` trong một `useEffect` rồi `setState`.
 * Hai cái giá: component vẽ hai lần cho một giá trị đã biết trước khi HTML rời
 * máy chủ, và câu lỗi CHỈ xuất hiện sau khi JavaScript chạy xong — người bị đá
 * về đây từ Google, trên mạng chậm, sẽ thấy một biểu mẫu trống không giải thích
 * gì trong suốt khoảng đó. Đọc trên máy chủ thì câu lỗi nằm sẵn trong HTML.
 */
export default function LoginForm({ oauthError }: { oauthError?: string | null }) {
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(
    (oauthError && OAUTH_ERRORS[oauthError]) || null,
  );
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFormError(null);
    setFieldErrors({});

    const form = new FormData(e.currentTarget);
    const email = String(form.get('email') || '').trim();
    const password = String(form.get('password') || '');

    if (!email || !password) {
      setFieldErrors({
        email: email ? undefined : 'Nhập email hoặc số điện thoại của bạn.',
        password: password ? undefined : 'Nhập mật khẩu.',
      });
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        if (data.errors) {
          setFieldErrors(data.errors as FieldErrors);
        } else {
          const msg =
            typeof data.error === 'string'
              ? data.error
              : data.error?.message || 'Sai email/số điện thoại hoặc mật khẩu.';
          setFormError(msg);
        }
        return;
      }

      // Tài khoản do trung tâm cấp, mật khẩu tạm → bắt đổi trước khi vào học.
      window.location.href = data.must_change_password
        ? '/doi-mat-khau?lan-dau=1'
        : '/dashboard?streak=1';
    } catch {
      setFormError('Không kết nối được tới máy chủ. Kiểm tra mạng rồi thử lại.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-5">
      {formError && (
        <p
          role="alert"
          className="rounded-md border-l-[3px] border-danger bg-danger/10 px-4 py-3 text-body text-ink-2"
        >
          {formError}
        </p>
      )}

      <Field
        id="login-email"
        name="email"
        label="Email hoặc số điện thoại"
        type="text"
        autoComplete="username"
        placeholder="ban@email.com"
        error={fieldErrors.email}
        icon={
          <svg viewBox="0 0 24 24" className="size-[18px]" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="4" width="20" height="16" rx="2" />
            <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
          </svg>
        }
      />

      <Field
        id="login-password"
        name="password"
        label="Mật khẩu"
        type={showPwd ? 'text' : 'password'}
        autoComplete="current-password"
        placeholder="••••••••"
        error={fieldErrors.password}
        icon={
          <svg viewBox="0 0 24 24" className="size-[18px]" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="11" width="18" height="11" rx="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
        }
        suffix={
          <button
            type="button"
            onClick={() => setShowPwd((v) => !v)}
            aria-label={showPwd ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
            aria-pressed={showPwd}
            className="grid size-11 place-items-center rounded-md text-ink-3 hover:text-ink"
          >
            {showPwd ? (
              <svg viewBox="0 0 24 24" className="size-[18px]" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                <path d="M1 1l22 22" strokeLinecap="round" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" className="size-[18px]" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            )}
          </button>
        }
      />

      <Button type="submit" id="loginBtn" full loading={loading}>
        {loading ? 'Đang đăng nhập…' : 'Đăng nhập'}
      </Button>
    </form>
  );
}
