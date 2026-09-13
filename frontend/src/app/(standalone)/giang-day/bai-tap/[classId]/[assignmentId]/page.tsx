import Link from 'next/link';

import { serverJson, type HinhDang } from '@/lib/server-api';
import { z } from 'zod';

import GradingClient, { type HocVien } from './GradingClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Chấm bài | TopHSA' };

/** Hình dạng do `AssignmentGradingView.get` trả về. */
type Payload = {
  assignment: {
    id: number;
    title: string;
    topic: string | null;
    maxScore: number | null;
    status: string;
    dueAt: string | null;
  };
  className: string;
  students: HocVien[];
};
/* Hình dạng `/api/teach/assignments/<id>/submissions` (T18 mức 2). */
const HINH_DANG = z.looseObject({
  assignment: z.looseObject({
    id: z.number(), title: z.string(), topic: z.string().nullable(),
    maxScore: z.number().nullable(), status: z.string(), dueAt: z.string().nullable(),
  }),
  className: z.string(),
  students: z.array(z.looseObject({
    userId: z.number(), name: z.string().nullable(), email: z.string().nullable(),
    submittedAt: z.string().nullable(), content: z.string().nullable(),
    contentLen: z.number().nullable(), fileUrl: z.string().nullable(),
    score: z.number().nullable(), scorePct: z.number().nullable(),
    feedback: z.string().nullable(), gradedAt: z.string().nullable(),
    gradedByName: z.string().nullable(),
  })),
}) satisfies HinhDang<Payload>;

export default async function ChamBaiPage({
  params,
}: {
  params: Promise<{ classId: string; assignmentId: string }>;
}) {
  const { classId, assignmentId } = await params;
  const kq = await serverJson<Payload>(
    `/api/teach/assignments/${assignmentId}/submissions`,
    { requireAuth: true },
    HINH_DANG,
  );

  if (!kq.ok) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="text-title text-ink">Không mở được bảng chấm</h1>
        <p className="mt-2 text-body text-ink-2">
          {kq.status === 404
            ? 'Bài tập không tồn tại, hoặc bạn không phải giảng viên phụ trách lớp đó.'
            : kq.message}
        </p>
        <Link
          href={`/giang-day/bai-tap/${classId}`}
          className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline"
        >
          ← Về danh sách bài tập
        </Link>
      </main>
    );
  }

  const { assignment: bai, className, students } = kq.data;

  return (
    <div className="min-h-dvh bg-ground">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-5xl flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-4">
          <Link
            href={`/giang-day/bai-tap/${classId}`}
            className="text-small text-ink-3 hover:text-brand-ink"
          >
            ← Bài tập
          </Link>
          <h1 className="text-section text-ink">{className}</h1>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <GradingClient
          assignmentId={Number(assignmentId)}
          title={bai.title}
          // `maxScore` không bao giờ NULL trên đường thường (§38 có NOT NULL
          // DEFAULT 10), nhưng kiểu vẫn cho phép null vì `_dict` trả về theo
          // hàng CSDL. Chốt về 10 ở đây thay vì rắc `?? 10` khắp màn hình chấm.
          maxScore={bai.maxScore ?? 10}
          topic={bai.topic}
          students={students}
        />
      </main>
    </div>
  );
}
