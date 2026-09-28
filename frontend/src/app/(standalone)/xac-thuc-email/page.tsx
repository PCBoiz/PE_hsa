import type { Metadata } from 'next';

import XacThucForm from './XacThucForm';

export const metadata: Metadata = {
  title: 'Xác nhận email — TopHSA',
  // Trang mở từ một đường dẫn mang mã: không để công cụ tìm kiếm lập chỉ mục, và
  // không để trình duyệt gửi Referer khi em bấm sang trang khác.
  robots: { index: false, follow: false },
  referrer: 'no-referrer',
};

/**
 * Xác nhận địa chỉ email của tài khoản vừa tự đăng ký (§73, 27/09/2026).
 *
 * Mã nằm sau dấu `#` — máy chủ Next không bao giờ thấy nó; chỉ đoạn mã ở trình
 * duyệt đọc rồi gửi lên bằng POST. Cùng cách với `/dat-lai-mat-khau`.
 */
export default function XacThucEmailPage() {
  return (
    <main className="grid min-h-dvh place-items-center bg-ground px-4 py-10">
      <div className="w-full max-w-[440px]">
        <div
          className="rounded-lg border border-line bg-surface p-6 shadow-e2"
          data-khu="xac-thuc-email"
        >
          <h1 className="text-title text-ink">Xác nhận email</h1>
          <XacThucForm />
        </div>
      </div>
    </main>
  );
}
