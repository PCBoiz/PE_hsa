'use client';

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';

import { Button, Field } from '@/components/ui';
import { useDaGan } from '@/lib/daGan';
import { taiTrang } from '@/lib/dieuHuong';
import { oChu } from '@/lib/form';

const MIN_LEN = 8;   // khớp `accounts/validators.validate_password_field` (8–128)

type TrangThai = 'dang-kiem' | 'hop-le' | 'het-han';

/**
 * ── VÌ SAO HỎI MÁY CHỦ TRƯỚC KHI HIỆN Ô MẬT KHẨU ──────────────────────────
 * Đường dẫn chết (quá 30 phút, đã dùng, bị thư mới hơn thay) thì phải nói NGAY,
 * không để em gõ xong hai ô mật khẩu rồi mới biết.
 *
 * ── VÌ SAO XOÁ `#chia=…` KHỎI THANH ĐỊA CHỈ ─────────────────────────────────
 * Đọc xong là xoá (`history.replaceState`): chìa còn nằm trên thanh địa chỉ thì
 * nằm cả trong lịch sử trình duyệt, trong ảnh chụp màn hình em gửi nhờ hỏi, và
 * trong đường dẫn em lỡ chép. Chìa chỉ sống trong một `ref` của trang này.
 */
export default function DatLaiForm() {
  const daGan = useDaGan();
  const chia = useRef<string>('');
  const [trangThai, setTrangThai] = useState<TrangThai>('dang-kiem');
  const [emailChe, setEmailChe] = useState<string>('');
  const [cauHetHan, setCauHetHan] = useState<string>('');
  const [dangLuu, setDangLuu] = useState(false);
  const [loi, setLoi] = useState<{ next?: string; confirm?: string }>({});
  const [loiChung, setLoiChung] = useState<string | null>(null);

  useEffect(() => {
    const m = /(?:^|&)chia=([A-Za-z0-9_-]+)/.exec(window.location.hash.slice(1));
    chia.current = m ? m[1] : '';
    if (window.location.hash) {
      window.history.replaceState(null, '', window.location.pathname);
    }
    let huy = false;
    void (async () => {
      if (!chia.current) {
        setTrangThai('het-han');
        return;
      }
      try {
        const r = await fetch('/auth/dat-lai-mat-khau/kiem', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify({ chia: chia.current }),
        });
        const d = await r.json().catch(() => ({}));
        if (huy) return;
        if (r.ok && d?.hopLe) {
          setEmailChe(typeof d.email === 'string' ? d.email : '');
          setTrangThai('hop-le');
        } else {
          setCauHetHan(typeof d?.error === 'string' ? d.error : '');
          setTrangThai('het-han');
        }
      } catch {
        if (!huy) {
          setCauHetHan('Không kết nối được tới máy chủ. Tải lại trang để thử lại.');
          setTrangThai('het-han');
        }
      }
    })();
    return () => { huy = true; };
  }, []);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoi({});
    setLoiChung(null);
    const f = new FormData(e.currentTarget);
    const next = oChu(f, 'next');
    const confirm = oChu(f, 'confirm');
    const cucBo: typeof loi = {};
    if (next.length < MIN_LEN) cucBo.next = `Mật khẩu mới cần ít nhất ${MIN_LEN} ký tự.`;
    if (confirm !== next) cucBo.confirm = 'Hai lần nhập chưa khớp nhau.';
    if (Object.keys(cucBo).length) {
      setLoi(cucBo);
      document.getElementById(cucBo.next ? 'dl-next' : 'dl-confirm')?.focus();
      return;
    }
    setDangLuu(true);
    try {
      const r = await fetch('/auth/dat-lai-mat-khau', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ chia: chia.current, password: next }),
      });
      const d = await r.json().catch(() => ({}));
      if (r.ok) {
        // Cùng lời báo với đổi mật khẩu tự nguyện: mọi phiên cũ đã bị cắt.
        taiTrang('/login?vua-doi-mat-khau=1');
        return;
      }
      if (d?.errors?.password) {
        setLoi({ next: String(d.errors.password) });
      } else if (r.status === 400) {
        setCauHetHan(typeof d?.error === 'string' ? d.error : '');
        setTrangThai('het-han');
      } else if (r.status === 429) {
        setLoiChung('Đã có quá nhiều yêu cầu từ mạng này. Đợi một lúc rồi thử lại.');
      } else {
        setLoiChung('Chưa đặt được mật khẩu. Thử lại sau ít phút.');
      }
    } catch {
      setLoiChung('Không kết nối được tới máy chủ. Kiểm tra mạng rồi thử lại.');
    } finally {
      setDangLuu(false);
    }
  }

  if (trangThai === 'dang-kiem') {
    return <p className="mt-2 text-body text-ink-3" role="status">Đang kiểm tra đường dẫn…</p>;
  }

  if (trangThai === 'het-han') {
    return (
      <div className="mt-2 flex flex-col gap-4" data-chan="khong-thay">
        <p className="rounded-md border-l-[3px] border-danger bg-danger/10 px-4 py-3 text-body text-ink-2" role="alert">
          {cauHetHan || 'Đường dẫn này đã hết hạn hoặc đã được dùng.'}
        </p>
        <Link
          href="/quen-mat-khau"
          className="inline-flex min-h-11 items-center justify-center rounded-md bg-brand-fill px-4 text-body font-semibold text-white"
        >
          Xin đường dẫn mới
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={(e) => void submit(e)} noValidate className="mt-2 flex flex-col gap-5">
      <p className="text-body text-ink-3">
        Tài khoản <b className="text-ink-2">{emailChe}</b>. Đặt xong, mọi thiết bị đang đăng nhập tài khoản
        này đều bị đăng xuất.
      </p>
      {loiChung && (
        <p role="alert" className="rounded-md border-l-[3px] border-danger bg-danger/10 px-4 py-3 text-body text-ink-2">
          {loiChung}
        </p>
      )}
      <Field
        id="dl-next"
        name="next"
        type="password"
        autoComplete="new-password"
        label="Mật khẩu mới"
        hint={`Ít nhất ${MIN_LEN} ký tự. Chọn thứ bạn nhớ được mà người khác không đoán ra.`}
        error={loi.next}
      />
      <Field
        id="dl-confirm"
        name="confirm"
        type="password"
        autoComplete="new-password"
        label="Nhập lại mật khẩu mới"
        error={loi.confirm}
      />
      <Button type="submit" full loading={dangLuu} disabled={!daGan}>
        {dangLuu ? 'Đang lưu…' : 'Đặt mật khẩu mới'}
      </Button>
    </form>
  );
}
