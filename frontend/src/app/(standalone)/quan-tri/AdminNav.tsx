'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

/**
 * Thanh điều hướng khu vận hành.
 *
 * Tách thành phần client CHỈ vì một lý do: `usePathname()` không dùng được
 * trong Server Component, mà đánh dấu mục đang mở thì cần biết đường dẫn hiện
 * tại. Phần còn lại của layout vẫn dựng ở máy chủ.
 *
 * Vì sao phải đánh dấu: đo 31/08/2026 trên hai trang khác nhau, cả bốn tab đều
 * giống hệt — cùng màu, cùng độ đậm, `aria-current` là null. Người dùng bấm
 * xong không có gì xác nhận là đã tới nơi, nên bấm lại. Trang cũ `/dashboard`
 * ĐÃ làm đúng chuyện này bằng `.nav-btn.active` kèm thanh gạch chân; khu mới bỏ
 * quên một thứ khu cũ đã có.
 */
export default function AdminNav({ tabs }: { tabs: { href: string; label: string }[] }) {
  const duong = usePathname();

  return (
    // `aria-label` bằng tiếng Việt: trình đọc màn hình đọc nhãn này lên cho
    // người dùng, mà người dùng ở đây là trợ giảng người Việt.
    //
    // Cuộn ngang chứ không xuống dòng: thanh điều hướng phải giữ đúng một hàng
    // để phần nội dung không bị đẩy xuống trên điện thoại.
    <nav
      aria-label="Khu vận hành trung tâm"
      className="-mx-1 flex min-w-0 flex-1 gap-1 overflow-x-auto px-1"
    >
      {tabs.map((t) => {
        // So bằng TIỀN TỐ chứ không so bằng nhau: trang con (ví dụ
        // `/quan-tri/tai-khoan/123`) vẫn phải sáng đúng tab cha.
        const dangMo = duong === t.href || duong.startsWith(t.href + '/');
        return (
          <Link
            key={t.href}
            href={t.href}
            aria-current={dangMo ? 'page' : undefined}
            className={[
              'min-h-11 shrink-0 rounded-md px-3 py-2 text-small font-semibold whitespace-nowrap',
              dangMo
                ? 'bg-sunken text-brand-ink'
                : 'text-ink-2 hover:bg-sunken hover:text-brand-ink',
            ].join(' ')}
          >
            {t.label}
          </Link>
        );
      })}
    </nav>
  );
}
