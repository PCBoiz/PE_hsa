'use client';

import { useState } from 'react';

import { Button, Field } from '@/components/ui';
import { useDaGan } from '@/lib/daGan';
import { oChu } from '@/lib/form';

/**
 * Ô email + nút gửi. Máy chủ trả MỘT câu cho mọi trường hợp (có tài khoản hay
 * không) — màn hình hiện nguyên câu ấy, không tự thêm "đã gửi tới bạn" hay
 * "không tìm thấy", vì đó chính là thứ máy chủ cố ý không nói ra.
 */
export default function QuenMatKhauForm() {
  // Khoá nút tới khi React gắn xong — cùng lý do với `LoginForm`: Enter trước
  // khi hydrate là trình duyệt tự gửi GET, đưa email lên thanh địa chỉ.
  const daGan = useDaGan();
  const [dangGui, setDangGui] = useState(false);
  const [loiEmail, setLoiEmail] = useState<string | null>(null);
  const [loiChung, setLoiChung] = useState<string | null>(null);
  const [daGui, setDaGui] = useState<string | null>(null);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoiEmail(null);
    setLoiChung(null);
    const email = oChu(new FormData(e.currentTarget), 'email');
    if (!email.includes('@')) {
      setLoiEmail('Nhập địa chỉ email của tài khoản, ví dụ an.nguyen@gmail.com.');
      document.getElementById('qmk-email')?.focus();
      return;
    }
    setDangGui(true);
    try {
      const r = await fetch('/auth/quen-mat-khau', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ email }),
      });
      const d = await r.json().catch(() => ({}));
      if (r.status === 429) {
        setLoiChung('Đã có quá nhiều yêu cầu từ mạng này. Đợi khoảng một giờ rồi thử lại.');
      } else if (!r.ok) {
        if (d?.errors?.email) setLoiEmail(String(d.errors.email));
        else setLoiChung('Chưa gửi được yêu cầu. Thử lại sau ít phút.');
      } else {
        setDaGui(typeof d?.message === 'string' ? d.message : 'Đã nhận yêu cầu.');
      }
    } catch {
      setLoiChung('Không kết nối được tới máy chủ. Kiểm tra mạng rồi thử lại.');
    } finally {
      setDangGui(false);
    }
  }

  if (daGui) {
    return (
      <div role="status" className="rounded-md border-l-[3px] border-brand bg-brand-soft px-4 py-3">
        <p className="text-body text-ink-2">{daGui}</p>
      </div>
    );
  }

  return (
    <form onSubmit={(e) => void submit(e)} noValidate className="flex flex-col gap-5">
      {loiChung && (
        <p role="alert" className="rounded-md border-l-[3px] border-danger bg-danger/10 px-4 py-3 text-body text-ink-2">
          {loiChung}
        </p>
      )}
      <Field
        id="qmk-email"
        name="email"
        type="email"
        inputMode="email"
        autoComplete="email"
        label="Email của tài khoản"
        error={loiEmail}
        spellCheck={false}
      />
      <Button type="submit" full loading={dangGui} disabled={!daGan}>
        {dangGui ? 'Đang gửi…' : 'Gửi đường dẫn đặt lại'}
      </Button>
    </form>
  );
}
