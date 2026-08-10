import type { Metadata } from 'next';

// Root layout TỐI THIỂU — không import CSS global nào ở đây.
// Mỗi page/layout con tự import ĐÚNG tổ hợp CSS của template gốc
// (MIGRATION_PLAN.md §4) để tránh class trùng tên giữa các file đè nhau.

export const metadata: Metadata = {
  title: 'ProgrammingEdu × TopHSA — Luyện thi Đánh giá năng lực HSA',
  description:
    'Nền tảng luyện thi Đánh giá năng lực (HSA) ĐHQG Hà Nội — ProgrammingEdu hợp tác TopHSA. Chẩn đoán năng lực, lộ trình cá nhân hoá, luyện bấm giờ và thi thử CBT đầy đủ.',
  icons: {
    // favicon 🎯 (đổi từ 🚀) — nhận diện luyện thi HSA
    icon: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%8E%AF%3C/text%3E%3C/svg%3E",
  },
};

const API_ORIGIN = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9000';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        {/* Template gốc nào cũng có meta csrf-token; course_detail.js/course_db_design.js
            đọc .content KHÔNG guard → meta phải tồn tại (rỗng — auth giờ là JWT). */}
        <meta name="csrf-token" content="" />
        {/* Origin backend cho pe-bridge.js — phải có TRƯỚC mọi script legacy */}
        <script
          dangerouslySetInnerHTML={{
            __html: `window.__PE_API_ORIGIN=${JSON.stringify(API_ORIGIN)};`,
          }}
        />
      </head>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
