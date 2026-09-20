import Link from 'next/link';

/**
 * Trang 404 của cả sản phẩm.
 *
 * Trước 20/09/2026 gõ sai một đường dẫn trong khu quản trị ra trang mặc định
 * của Next — "404 This page could not be found." bằng tiếng Anh, không có lối
 * về — giữa một ERP toàn tiếng Việt (rà luồng quản trị viên). Cùng khung với
 * `quan-tri/ChanVai.tsx` để hai trang lỗi trông là một nhà.
 */
export default function NotFound() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-16">
      <h1 className="text-title text-ink">Không có trang này</h1>
      <p className="mt-2 text-body text-ink-2">
        Đường dẫn có thể gõ sai hoặc trang đã được dời đi. Nếu bạn đi tới đây từ một
        liên kết trong hệ thống, báo lại cho người quản lý.
      </p>
      <Link
        href="/dashboard"
        className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline"
      >
        ← Về trang của tôi
      </Link>
    </main>
  );
}
