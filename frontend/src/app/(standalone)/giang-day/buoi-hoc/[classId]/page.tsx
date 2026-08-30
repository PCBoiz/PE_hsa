import Link from 'next/link';

import { serverJson } from '@/lib/server-api';

import SessionsClient, { type SessionRow } from './SessionsClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Buổi học & điểm danh | TopHSA' };

type ClassDetail = { klass?: { id: number; name: string; schedule?: string | null } };

/**
 * Buổi học của một lớp.
 *
 * Trước khối này, lớp chỉ có một dòng MÔ TẢ lịch ("Tối 2-4-6") nên hệ thống
 * không trả lời được câu hỏi vận hành nào: buổi tới dạy gì, hôm qua ai vắng,
 * em này đã nghỉ mấy buổi. Đặc tả ERP §4.
 */
export default async function BuoiHocPage({
  params,
}: {
  params: Promise<{ classId: string }>;
}) {
  const { classId } = await params;
  const [detail, list] = await Promise.all([
    serverJson<ClassDetail>(`/api/teach/classes/${classId}`, { requireAuth: true }),
    serverJson<{ sessions: SessionRow[] }>(`/api/teach/classes/${classId}/sessions`, {
      requireAuth: true,
    }),
  ]);

  // Không đọc được lớp = không phụ trách lớp đó (backend trả 404 cho cả hai
  // trường hợp, cố ý, để không lộ ra lớp có tồn tại hay không).
  if (!detail?.klass) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="text-title text-ink">Không mở được lớp này</h1>
        <p className="mt-2 text-body text-ink-2">
          Lớp không tồn tại, hoặc bạn không phải giảng viên phụ trách lớp đó.
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
        <div className="mx-auto flex max-w-5xl flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-4">
          <Link href="/dashboard" className="text-small text-ink-3 hover:text-brand-ink">
            ← Trang của tôi
          </Link>
          <h1 className="text-section text-ink">{detail.klass.name}</h1>
          {detail.klass.schedule && (
            <span className="text-small text-ink-3">{detail.klass.schedule}</span>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <SessionsClient
          classId={Number(classId)}
          className={detail.klass.name}
          initial={list?.sessions ?? []}
        />
      </main>
    </div>
  );
}
