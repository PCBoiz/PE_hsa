'use client';

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';

import { CAU_MAT_MANG } from '@/lib/dangKy';

type TrangThai = 'dang-gui' | 'xong' | 'hong';

/**
 * ── VÌ SAO GỬI NGAY, KHÔNG CHỜ EM BẤM THÊM MỘT NÚT ─────────────────────────
 * Em đã bấm một lần rồi — ở trong lá thư. Bắt bấm lần nữa là thêm một chỗ để em
 * bỏ dở, mà không thêm một chút an toàn nào: mã chỉ nằm trong hộp thư của em.
 * (Khác `/dat-lai-mat-khau`, nơi phải hỏi trước vì còn hai ô mật khẩu phải gõ.)
 *
 * ── VÌ SAO XOÁ `#chia=…` KHỎI THANH ĐỊA CHỈ ────────────────────────────────
 * Đọc xong là xoá (`history.replaceState`): mã còn trên thanh địa chỉ thì nằm cả
 * trong lịch sử trình duyệt, trong ảnh chụp màn hình em gửi nhờ hỏi, và trong
 * đường dẫn em lỡ chép cho bạn.
 *
 * ── VÌ SAO CÓ `daGui` (đo được 27/09/2026, mất một lượt đo vì chỗ này) ─────
 * React StrictMode — BẬT mặc định ở App Router khi chạy dev — gọi effect HAI LẦN.
 * Lần một đọc mã rồi `replaceState` xoá `#chia=…`; lần hai không còn thấy mã nữa
 * và ghi đè trạng thái thành "thiếu mã xác nhận", cho một đường dẫn hoàn toàn đúng.
 * Tệ hơn: hai lần gọi là HAI lượt POST, mà mã chỉ dùng được MỘT lần — lượt thứ hai
 * nhận đúng câu "đã hết hạn hoặc đã được dùng", tức màn báo hỏng NGAY SAU KHI nó
 * vừa xác nhận thành công. Một `ref` chốt lại: đọc mã một lần, gửi một lần.
 *
 * ── VÌ SAO KHÔNG TỰ CHUYỂN SANG TRANG ĐĂNG NHẬP ────────────────────────────
 * Xác nhận xong KHÔNG có nghĩa là đã đăng nhập (cửa này không cấp phiên — xem
 * `ISSUES_TOKENS` ở `app/auth/[...path]/route.ts`). Tự nhảy trang thì em không
 * đọc kịp câu "học vụ sẽ liên hệ xếp lớp", thứ duy nhất trả lời "rồi sao nữa".
 */
export default function XacThucForm() {
  const [trangThai, setTrangThai] = useState<TrangThai>('dang-gui');
  const [cau, setCau] = useState('');
  const daGui = useRef(false);

  useEffect(() => {
    // Chốt: chỉ chạy MỘT lần, kể cả khi StrictMode gọi effect hai lượt (xem trên).
    // KHÔNG dùng cờ `huy` trong hàm dọn dẹp như các màn khác: ở đây hàm dọn dẹp của
    // lượt một chạy TRƯỚC lượt hai, mà lượt hai đã bị chốt chặn — nên cờ ấy chỉ kịp
    // huỷ đúng lượt gửi duy nhất, và màn đứng mãi ở "Đang xác nhận…" trong khi máy
    // chủ đã xác nhận xong. Đo được 27/09/2026 trên màn thật.
    if (daGui.current) return;
    daGui.current = true;
    const m = /(?:^|&)chia=([A-Za-z0-9_-]+)/.exec(window.location.hash.slice(1));
    const chia = m ? m[1] : '';
    if (window.location.hash) {
      window.history.replaceState(null, '', window.location.pathname);
    }
    void (async () => {
      if (!chia) {
        setCau('Đường dẫn này thiếu mã xác nhận. Mở lại đúng đường dẫn trong thư TopHSA gửi bạn.');
        setTrangThai('hong');
        return;
      }
      try {
        const r = await fetch('/auth/xac-thuc-email', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify({ chia }),
        });
        const d = (await r.json().catch(() => ({}))) as { message?: unknown; error?: unknown };
        if (r.ok) {
          setCau(typeof d?.message === 'string' ? d.message : 'Đã xác nhận email.');
          setTrangThai('xong');
        } else {
          setCau(
            typeof d?.error === 'string'
              ? d.error
              : 'Chưa xác nhận được. Xin gửi lại thư xác nhận ở trang đăng nhập.',
          );
          setTrangThai('hong');
        }
      } catch {
        setCau(CAU_MAT_MANG);
        setTrangThai('hong');
      }
    })();
  }, []);

  if (trangThai === 'dang-gui') {
    return (
      <p className="mt-2 text-body text-ink-3" role="status">
        Đang xác nhận…
      </p>
    );
  }

  return (
    <div className="mt-2 flex flex-col gap-4" data-khu={trangThai === 'xong' ? 'xong' : 'khong-thay'}>
      <p
        role={trangThai === 'xong' ? 'status' : 'alert'}
        className={
          trangThai === 'xong'
            ? 'rounded-md border-l-[3px] border-success bg-success/10 px-4 py-3 text-body text-ink-2'
            : 'rounded-md border-l-[3px] border-danger bg-danger/10 px-4 py-3 text-body text-ink-2'
        }
      >
        {cau}
      </p>
      <Link
        href="/login"
        className="inline-flex min-h-11 items-center justify-center rounded-md bg-brand-fill px-4 text-body font-semibold text-white"
      >
        {trangThai === 'xong' ? 'Đăng nhập' : 'Về trang đăng nhập'}
      </Link>
    </div>
  );
}
