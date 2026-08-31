import Link from 'next/link';

import { serverJson } from '@/lib/server-api';

import MyAssignmentsClient, { type BaiCuaToi } from './MyAssignmentsClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Bài tập của bạn | TopHSA' };

export default async function BaiTapCuaToiPage() {
  const kq = await serverJson<{ assignments: BaiCuaToi[] }>('/api/assignments', {
    requireAuth: true,
  });

  return (
    <div className="min-h-dvh bg-ground">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-3xl flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-4">
          <Link href="/dashboard" className="text-small text-ink-3 hover:text-brand-ink">
            ← Về trang chính
          </Link>
          <h1 className="text-section text-ink">Bài tập</h1>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-6">
        <MyAssignmentsClient
          initial={kq.ok ? kq.data.assignments : []}
          // Danh sách rỗng vì chưa được giao bài, và danh sách rỗng vì không đọc
          // được, trông y hệt nhau — và ở trường hợp thứ hai em sẽ tưởng mình
          // không có bài phải làm.
          loiTai={kq.ok ? null : kq.message}
        />
      </main>
    </div>
  );
}
