'use client';

import { useState } from 'react';

import { Button, Field } from '@/components/ui';

/**
 * Đổi mật khẩu.
 *
 * Dùng cho hai tình huống, và chúng KHÁC nhau về mặt con người:
 *  · Bắt buộc lần đầu (`lanDau`): học viên vừa nhận mật khẩu tạm từ trợ giảng.
 *    Người khác đang biết mật khẩu của họ, nên phải nói rõ vì sao bắt đổi —
 *    không thì đây chỉ là một rào cản vô cớ trước khi được vào học.
 *  · Tự nguyện: đổi cho yên tâm.
 *
 * Kiểm ngay ở trình duyệt phần kiểm được (độ dài, hai ô có khớp nhau không) để
 * học viên không phải chờ một vòng gọi mạng chỉ để biết mình gõ lệch. Phần còn
 * lại vẫn do máy chủ quyết.
 */
const MIN_LEN = 8;

export default function ChangePasswordForm({ lanDau }: { lanDau: boolean }) {
  const [loading, setLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [errors, setErrors] = useState<{ current?: string; next?: string; confirm?: string }>({});

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFormError(null);
    setErrors({});

    const f = new FormData(e.currentTarget);
    const current = String(f.get('current') || '');
    const next = String(f.get('next') || '');
    const confirm = String(f.get('confirm') || '');

    const local: typeof errors = {};
    if (!current) local.current = lanDau ? 'Nhập mật khẩu tạm trung tâm đã cấp.' : 'Nhập mật khẩu hiện tại.';
    if (next.length < MIN_LEN) local.next = `Mật khẩu mới cần ít nhất ${MIN_LEN} ký tự.`;
    else if (next === current) local.next = 'Mật khẩu mới phải khác mật khẩu cũ.';
    if (confirm !== next) local.confirm = 'Hai lần nhập chưa khớp nhau.';
    if (Object.keys(local).length) {
      setErrors(local);
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('/api/user/password', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ current, new: next }),
      });
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        if (data.errors?.new) setErrors({ next: data.errors.new });
        else
          setFormError(
            typeof data.error === 'string'
              ? data.error
              : data.error?.message || 'Không đổi được mật khẩu. Thử lại giúp tôi.',
          );
        return;
      }
      // ĐI THẲNG VỀ ĐĂNG NHẬP, không về /dashboard.
      //
      // Từ §39 (T67), đổi mật khẩu đặt mốc `tokens_valid_from` và mốc đó cắt
      // MỌI phiên — kể cả phiên đang gõ. Về `/dashboard` thì lời gọi đầu tiên
      // của trang đó nhận 401, lớp làm mới token thử refresh, refresh cũng đã
      // bị thu hồi, rồi mới đá về `/login` — người dùng đi qua hai lần nhảy
      // trang và một khoảnh khắc màn hình hỏng, ngay sau khi vừa làm đúng.
      //
      // Cắt cả phiên hiện tại là CÓ CHỦ Ý: người ta đổi mật khẩu chính vì nghi
      // có ai khác đang dùng tài khoản mình, nên "đăng nhập lại ở mọi nơi" mới
      // là thứ họ mong đợi.
      window.location.href = '/login?vua-doi-mat-khau=1';
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
        id="pw-current"
        name="current"
        type="password"
        autoComplete="current-password"
        label={lanDau ? 'Mật khẩu tạm trung tâm đã cấp' : 'Mật khẩu hiện tại'}
        error={errors.current}
      />

      <Field
        id="pw-next"
        name="next"
        type="password"
        autoComplete="new-password"
        label="Mật khẩu mới"
        hint={`Ít nhất ${MIN_LEN} ký tự. Chọn thứ bạn nhớ được mà người khác không đoán ra.`}
        error={errors.next}
      />

      <Field
        id="pw-confirm"
        name="confirm"
        type="password"
        autoComplete="new-password"
        label="Nhập lại mật khẩu mới"
        error={errors.confirm}
      />

      <Button type="submit" full loading={loading}>
        {loading ? 'Đang lưu…' : 'Đổi mật khẩu'}
      </Button>
    </form>
  );
}
