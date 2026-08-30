import type { Metadata } from 'next';
import { Be_Vietnam_Pro, JetBrains_Mono } from 'next/font/google';

import './tailwind.css';

/* ══════════════════════════════════════════════════════════════════════════
 * Root layout.
 *
 * PHÔNG CHỮ (sửa 27/08/2026) — trước đây sản phẩm có BỐN thực tại chữ khác
 * nhau: đăng nhập dùng Sora, Trang của tôi dùng Inter, bài học và thi thử
 * không nạp phông nào (rơi về phông hệ điều hành), khảo sát nạp Inter bằng
 * @import chặn hiển thị. Người dùng đi từ đăng nhập vào bài học thấy nét chữ
 * đổi ba lần.
 *
 * Tệ hơn: **Sora không có bộ ký tự tiếng Việt** (chỉ latin + latin-ext), nên
 * mọi chữ có dấu chồng — ệ, ộ, ữ, ẩ — rơi về phông dự phòng, ngay trên màn
 * hình đầu tiên người dùng nhìn thấy.
 *
 * Nay: một họ chữ duy nhất cho cả sản phẩm, khai ở đây. `next/font` tải phông
 * về máy chủ của mình lúc dựng bản (không còn request chạy ra Google lúc
 * người dùng mở trang) và tự sinh phông dự phòng khớp kích thước, nên chữ
 * không nhảy khi phông thật tải xong.
 *
 * Be Vietnam Pro: bộ chữ vẽ riêng cho tiếng Việt — dấu được thiết kế từ đầu
 * chứ không phải chắp vào một bộ Latin có sẵn.
 * JetBrains Mono: dành cho CON SỐ (điểm, phút, phần trăm, số ngày còn lại).
 * Trong sổ điểm và bảng lớp, chữ số phải thẳng cột — đó là chức năng, không
 * phải sở thích. Bộ này vốn đã có mặt ở 104 chỗ trong CSS cũ.
 * ══════════════════════════════════════════════════════════════════════════ */

const body = Be_Vietnam_Pro({
  subsets: ['vietnamese', 'latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-body',
  display: 'swap',
});

const num = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '700'],
  variable: '--font-num',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'ProgrammingEdu × TopHSA — Luyện thi Đánh giá năng lực HSA',
  description:
    'Nền tảng luyện thi Đánh giá năng lực (HSA) ĐHQG Hà Nội — ProgrammingEdu hợp tác TopHSA. Chẩn đoán năng lực, lộ trình cá nhân hoá, luyện bấm giờ và thi thử CBT đầy đủ.',
  icons: {
    icon: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%8E%AF%3C/text%3E%3C/svg%3E",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className={`${body.variable} ${num.variable}`} suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        {/* Template gốc nào cũng có meta csrf-token; course_detail.js đọc .content
            KHÔNG guard → meta phải tồn tại (rỗng — xác thực giờ là JWT). */}
        <meta name="csrf-token" content="" />

        {/* theme.css nạp ở TẦNG CHUNG (trước đây mỗi trang tự nạp).
            File này chỉ chứa biến màu, không có class nào, nên không thể đè
            lên CSS của trang — mà lại là thứ mọi trang đều cần. Nạp ở đây còn
            là điều kiện để token Tailwind (trỏ var() vào chính các biến này)
            hoạt động ở mọi màn hình. */}
        <link rel="stylesheet" href="/static/css/theme.css" />

        {/* Mọi lời gọi /api/* và /auth/* nay đi qua chính miền này rồi mới
            xuống Django (xem src/lib/proxy.ts). Để rỗng nghĩa là "cùng miền":
            JavaScript cũ giữ nguyên đường dẫn tương đối và tự nhiên chạy đúng,
            còn token thì nằm trong cookie httpOnly ngoài tầm với của nó. */}
        <script
          dangerouslySetInnerHTML={{
            __html: `window.__PE_API_ORIGIN="";`,
          }}
        />
      </head>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
