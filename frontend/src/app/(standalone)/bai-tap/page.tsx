import { ThemeToggle } from '@/components/ui';
import Link from 'next/link';

import { serverJson, type HinhDang } from '@/lib/server-api';
import { z } from 'zod';

import MyAssignmentsClient, { type BaiCuaToi } from './MyAssignmentsClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Bài tập của bạn | TopHSA' };

/* Hình dạng `/api/assignments` (T18 mức 2). */
const HINH_DANG = z.looseObject({
  assignments: z.array(z.looseObject({
    id: z.number(), title: z.string(), description: z.string().nullable(),
    topic: z.string().nullable(), className: z.string(), status: z.string(),
    dueAt: z.string().nullable(), maxScore: z.number().nullable(),
    submittedAt: z.string().nullable(), content: z.string().nullable(),
    score: z.number().nullable(), scorePct: z.number().nullable(),
    feedback: z.string().nullable(), gradedAt: z.string().nullable(),
  })),
}) satisfies HinhDang<{ assignments: BaiCuaToi[] }>;

export default async function BaiTapCuaToiPage() {
  const kq = await serverJson<{ assignments: BaiCuaToi[] }>('/api/assignments', {
    requireAuth: true,
  }, HINH_DANG);

  return (
    <div className="min-h-dvh bg-ground">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-3xl flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-4">
          <Link href="/dashboard" className="-my-3 py-3 text-small text-ink-3 hover:text-brand-ink">
            ← Về trang chính
          </Link>
          <h1 className="text-section text-ink">Bài tập</h1>
          <ThemeToggle className="ml-auto" />
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
