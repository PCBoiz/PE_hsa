import type { Metadata } from 'next';
import Link from 'next/link';

import QuenMatKhauForm from './QuenMatKhauForm';

export const metadata: Metadata = {
  title: 'Quên mật khẩu — ProgrammingEdu × TopHSA',
};

/**
 * Xin đường dẫn đặt lại mật khẩu qua email (§52, 23/09/2026).
 *
 * Trang KHÔNG cần đăng nhập. Tài khoản không có email (chỉ số điện thoại hay
 * tên đăng nhập) vẫn phải nhờ học vụ — nói rõ ngay trên trang, để em không
 * gõ số điện thoại vào ô email rồi chờ một lá thư không bao giờ tới.
 */
export default function QuenMatKhauPage() {
  return (
    <main className="grid min-h-dvh place-items-center bg-ground px-4 py-10">
      <div className="w-full max-w-[440px]">
        <div className="rounded-lg border border-line bg-surface p-6 shadow-e2">
          <h1 className="text-title text-ink">Quên mật khẩu</h1>
          <p className="mt-1 mb-6 text-body text-ink-3">
            Nhập email của tài khoản. Hệ thống gửi tới đó một đường dẫn để bạn tự đặt mật khẩu mới.
          </p>
          <QuenMatKhauForm />
          <div className="mt-6 border-t border-line pt-5">
            <p className="text-small text-ink-3">
              <b className="text-ink-2">Tài khoản không có email?</b> (chỉ đăng nhập bằng số điện
              thoại hoặc tên đăng nhập) Nhắn học vụ hoặc giảng viên phụ trách lớp — họ cấp lại mật
              khẩu tạm cho bạn.
            </p>
            <Link
              href="/login"
              className="-mx-2 mt-3 inline-flex min-h-11 items-center px-2 text-small text-brand-ink underline"
            >
              ← Về đăng nhập
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
