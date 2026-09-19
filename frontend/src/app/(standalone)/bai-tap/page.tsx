import { ThemeToggle } from '@/components/ui';
import Link from 'next/link';

import { nhomCuaVai } from '@/lib/nhomVai';
import { serverJson, type HinhDang } from '@/lib/server-api';
import { z } from 'zod';

import { layVai } from '../quan-tri/layVai';
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
  /* Hai lượt gọi SONG SONG: thêm vai không được cộng một vòng mạng vào trang.
     Vì sao cần vai (20/09/2026, lượt đi sáu vai): trợ giảng gắn với lớp qua
     CÙNG bảng `class_members` với học viên, nên `/api/assignments` liệt kê bài
     của lớp họ phụ trách và trang này mời họ "Làm bài" bài mình sẽ chấm. Thanh
     đã ẩn mục với nhân sự; đây là chốt cho đường dẫn gõ thẳng. Không phải hàng
     rào — bài nộp của nhân sự vẫn bị máy chủ lọc `chi_hoc_vien` khi chấm. */
  const [kq, vai] = await Promise.all([
    serverJson<{ assignments: BaiCuaToi[] }>('/api/assignments', { requireAuth: true }, HINH_DANG),
    layVai(),
  ]);
  const nhanSu = vai.ok && nhomCuaVai(vai.vai) === 'nhan-su';

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
        {nhanSu ? (
          <section className="rounded-lg border border-line bg-surface p-5 text-ink" aria-labelledby="bt-nhan-su">
            <h2 id="bt-nhan-su" className="m-0 text-lg font-semibold">Trang này dành cho học viên</h2>
            <p className="mt-2 mb-0 text-ink-2">
              Bạn đang đăng nhập với vai nhân sự. Giao bài, xem bài nộp và chấm ở khu Giảng dạy —
              chọn lớp rồi vào mục <strong>Bài tập</strong>.
            </p>
            <p className="mt-3 mb-0">
              <Link href="/giang-day" className="font-semibold text-brand-ink underline-offset-2 hover:underline">
                Tới Việc hôm nay →
              </Link>
            </p>
          </section>
        ) : (
          <MyAssignmentsClient
            initial={kq.ok ? kq.data.assignments : []}
            // Danh sách rỗng vì chưa được giao bài, và danh sách rỗng vì không đọc
            // được, trông y hệt nhau — và ở trường hợp thứ hai em sẽ tưởng mình
            // không có bài phải làm.
            loiTai={kq.ok ? null : kq.message}
          />
        )}
      </main>
    </div>
  );
}
