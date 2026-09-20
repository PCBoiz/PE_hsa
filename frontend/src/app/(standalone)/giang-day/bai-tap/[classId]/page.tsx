import Link from 'next/link';

import { HD_CHI_TIET_LOP, type ChiTietLop } from '@/lib/hinhDang';
import { serverJson, type HinhDang } from '@/lib/server-api';
import { z } from 'zod';

import AssignmentsClient, { type Assignment } from './AssignmentsClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Bài tập & chấm bài | TopHSA' };

/** Xem chú thích ở `buoi-hoc/[classId]/page.tsx`: khoá là `class`, KHÔNG phải `klass`. */
type ClassDetail = ChiTietLop;
type DsBai = { assignments: Assignment[]; topics: string[] };
/* Hình dạng `/api/teach/classes/<id>/assignments` (T18 mức 2). */
const HD_BAI = z.looseObject({
  assignments: z.array(z.looseObject({
    id: z.number(), classId: z.number(), title: z.string(),
    description: z.string().nullable(), topic: z.string().nullable(),
    courseId: z.string().nullable(), status: z.string(), dueAt: z.string().nullable(),
    maxScore: z.number().nullable(), attachmentUrl: z.string().nullable(),
    createdAt: z.string().nullable(),
    submitted: z.number().optional(), graded: z.number().optional(),
    ungraded: z.number().optional(), members: z.number().optional(),
  })),
  topics: z.array(z.string()),
}) satisfies HinhDang<DsBai>;

/**
 * Giao bài & chấm tay — đặc tả ERP §5.
 *
 * Màn hình này là cửa duy nhất đưa được ĐÁNH GIÁ CỦA CON NGƯỜI vào hệ thống.
 * Mọi thứ khác đo được đều là trắc nghiệm chấm máy; phần Định tính của HSA thì
 * gần như chỉ đo được bằng bài tự luận có người đọc.
 */
export default async function BaiTapPage({
  params,
}: {
  params: Promise<{ classId: string }>;
}) {
  const { classId } = await params;
  const [detail, list] = await Promise.all([
    serverJson<ClassDetail>(`/api/teach/classes/${classId}`, { requireAuth: true }, HD_CHI_TIET_LOP),
    serverJson<DsBai>(`/api/teach/classes/${classId}/assignments`, { requireAuth: true }, HD_BAI),
  ]);

  // 404 = lớp không tồn tại HOẶC không phụ trách — backend cố ý trả cùng một mã
  // để không lộ ra lớp có tồn tại hay không. Mọi mã khác phải nói đúng câu của
  // nó, không mượn câu này.
  const klass = detail.ok ? detail.data.class : undefined;

  if (!klass) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="text-title text-ink">Không mở được lớp này</h1>
        <p className="mt-2 text-body text-ink-2">
          {!detail.ok && detail.status !== 404
            ? detail.message
            : 'Lớp không tồn tại, hoặc bạn không phải giảng viên phụ trách lớp đó.'}
        </p>
        <Link href="/dashboard" className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline">
          ← Về khu Giảng dạy
        </Link>
      </main>
    );
  }

  return (
    <div className="min-h-dvh bg-ground">
      <main>
          {/* Dải tiêu đề nằm TRONG `<main>`: là `<header>` ngoài `main` thì thành
              banner thứ hai (axe `landmark-no-duplicate-banner`), là `div` ngoài
              `main` thì rơi ngoài mọi mốc (axe `region`) — đo 20/09/2026. */}
        <div className="border-b border-line bg-surface">
          <div className="mx-auto flex max-w-5xl flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-4">
            <Link href="/dashboard" className="-my-3 py-3 text-small text-ink-3 hover:text-brand-ink">
              ← Khu Giảng dạy
            </Link>
            <h1 className="text-section text-ink">{klass.name}</h1>
            <Link
              href={`/giang-day/buoi-hoc/${klass.id}`}
              className="-my-3 py-3 text-small text-brand-ink underline"
            >
              Buổi học &amp; điểm danh
            </Link>
          </div>
        </div>
        <div className="mx-auto max-w-5xl px-4 py-6">
        <AssignmentsClient
          classId={Number(classId)}
          className={klass.name}
          initial={list.ok ? list.data.assignments : []}
          topics={list.ok ? (list.data.topics ?? []) : []}
          // KHÔNG nuốt lỗi bằng `initial={ok ? … : []}`. Danh sách rỗng vì chưa
          // có bài, và danh sách rỗng vì không đọc được, trông y hệt nhau — và
          // ở trường hợp thứ hai giảng viên sẽ giao lại một bài đã có.
          loiTai={list.ok ? null : list.message}
        />
        </div>
      </main>
    </div>
  );
}
