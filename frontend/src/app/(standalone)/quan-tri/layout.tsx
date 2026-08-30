import Link from 'next/link';

import { serverJson } from '@/lib/server-api';

/**
 * Khu VẬN HÀNH của trung tâm — tài khoản, lớp, nhật ký.
 *
 * Tách khỏi trang /admin cũ là có chủ đích. Trang đó quản lý NỘI DUNG (khoá,
 * bài, nhập giáo trình) — việc làm vài lần rồi thôi. Khu này quản lý CON NGƯỜI
 * — việc làm mỗi ngày, mỗi khi có học viên mới đăng ký học. Trộn hai thứ vào
 * một trang dài 700 dòng thì việc hằng ngày bị chôn dưới việc hằng quý.
 */
export const dynamic = 'force-dynamic';

const TABS = [
  { href: '/quan-tri/tai-khoan', label: 'Tài khoản' },
  { href: '/quan-tri/dot-hoc', label: 'Đợt học' },
  { href: '/quan-tri/nhat-ky', label: 'Nhật ký' },
  { href: '/admin', label: 'Nội dung & lớp' },
];

export default async function QuanTriLayout({ children }: { children: React.ReactNode }) {
  // Chặn ngay trên máy chủ. Không có câu này thì người không phải quản trị viên
  // vẫn tải được cả khung trang rồi mới nhận 403 từ API — nhìn như hệ thống
  // hỏng chứ không như "bạn không có quyền".
  const me = await serverJson<{ role?: string }>('/api/user', { requireAuth: true });
  // Không đọc được tài khoản KHÔNG đồng nghĩa với "không đủ quyền": backend sập
  // hay mạng hỏng cũng rơi vào đây, và nói "bạn không có quyền" lúc đó là đẩy
  // người dùng đi hỏi nhầm chỗ. Tách hai câu ra.
  if (!me.ok) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="text-title text-ink">Chưa mở được khu quản trị</h1>
        <p className="mt-2 text-body text-ink-2">{me.message}</p>
        <Link href="/dashboard" className="mt-6 inline-block text-body text-brand-ink underline">
          ← Về trang của tôi
        </Link>
      </main>
    );
  }
  if (me.data.role !== 'admin') {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="text-title text-ink">Khu vực dành cho quản trị viên</h1>
        <p className="mt-2 text-body text-ink-2">
          Tài khoản của bạn không có quyền vào đây. Nếu bạn là trợ giảng của TopHSA và cần
          quyền này, liên hệ người quản lý hệ thống.
        </p>
        <Link href="/dashboard" className="mt-6 inline-block text-body text-brand-ink underline">
          ← Về trang của tôi
        </Link>
      </main>
    );
  }

  return (
    <div className="min-h-dvh bg-ground">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-4">
          <Link href="/dashboard" className="text-small text-ink-3 hover:text-brand-ink">
            ← Trang của tôi
          </Link>
          <h1 className="text-section text-ink">Vận hành trung tâm</h1>
          {/* Cuộn ngang chứ không xuống dòng: thanh điều hướng phải giữ đúng
              một hàng để phần nội dung không bị đẩy xuống trên điện thoại. */}
          <nav className="-mx-1 flex min-w-0 flex-1 gap-1 overflow-x-auto px-1">
            {TABS.map((t) => (
              <Link
                key={t.href}
                href={t.href}
                className="min-h-11 shrink-0 rounded-md px-3 py-2 text-small font-semibold whitespace-nowrap text-ink-2 hover:bg-sunken hover:text-brand-ink"
              >
                {t.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
