import Link from 'next/link';

import { serverJson } from '@/lib/server-api';

import AssignmentsClient, { type Assignment } from './AssignmentsClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Bài tập & chấm bài | TopHSA' };

/** Xem chú thích ở `buoi-hoc/[classId]/page.tsx`: khoá là `class`, KHÔNG phải `klass`. */
type ClassDetail = {
  class?: { id: number; name: string; schedule?: string | null };
};

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
    serverJson<ClassDetail>(`/api/teach/classes/${classId}`, { requireAuth: true }),
    serverJson<{ assignments: Assignment[]; topics: string[] }>(
      `/api/teach/classes/${classId}/assignments`,
      { requireAuth: true },
    ),
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
        <Link href="/dashboard" className="mt-6 inline-block text-body text-brand-ink underline">
          ← Về khu Giảng dạy
        </Link>
      </main>
    );
  }

  return (
    <div className="min-h-dvh bg-ground">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-5xl flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-4">
          <Link href="/dashboard" className="text-small text-ink-3 hover:text-brand-ink">
            ← Khu Giảng dạy
          </Link>
          <h1 className="text-section text-ink">{klass.name}</h1>
          <Link
            href={`/giang-day/buoi-hoc/${klass.id}`}
            className="text-small text-brand-ink underline"
          >
            Buổi học &amp; điểm danh
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
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
      </main>
    </div>
  );
}
