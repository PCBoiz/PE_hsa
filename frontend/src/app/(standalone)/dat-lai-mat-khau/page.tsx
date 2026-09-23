import type { Metadata } from 'next';

import DatLaiForm from './DatLaiForm';

export const metadata: Metadata = {
  title: 'Đặt mật khẩu mới — TopHSA',
  // Trang mở từ một đường dẫn mang chìa: không để công cụ tìm kiếm lập chỉ mục,
  // và không để trình duyệt gửi Referer khi em bấm sang trang khác.
  robots: { index: false, follow: false },
  referrer: 'no-referrer',
};

/**
 * Đặt mật khẩu mới từ đường dẫn trong email (§52, 23/09/2026). Không cần đăng
 * nhập. Chìa nằm sau dấu `#` — máy chủ Next không bao giờ thấy nó; chỉ đoạn mã
 * ở trình duyệt đọc rồi gửi lên bằng POST.
 */
export default function DatLaiMatKhauPage() {
  return (
    <main className="grid min-h-dvh place-items-center bg-ground px-4 py-10">
      <div className="w-full max-w-[440px]">
        <div className="rounded-lg border border-line bg-surface p-6 shadow-e2">
          <h1 className="text-title text-ink">Đặt mật khẩu mới</h1>
          <DatLaiForm />
        </div>
      </div>
    </main>
  );
}
