import Link from 'next/link';

import { serverJson } from '@/lib/server-api';

import SessionsClient, { type SessionRow } from './SessionsClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Buổi học & điểm danh | TopHSA' };

/**
 * Hình dạng do `teaching/reports.py:class_report()` trả về.
 *
 * Khoá là `class`, KHÔNG phải `klass`. Bản đầu của tệp này đoán sai tên đó
 * (30/08/2026) và hậu quả là `if (!detail?.class)` luôn đúng — trang LUÔN hiện
 * "Không mở được lớp này" và chưa ai từng vào được màn hình điểm danh.
 * `tsc` không bắt được vì `serverJson<T>` chỉ ép kiểu, không kiểm gì lúc chạy:
 * kiểu ở đây là lời TỰ KHAI về thứ người viết TƯỞNG backend trả.
 *
 * Đừng sửa tên khoá ở đây mà không mở trang thật trong trình duyệt xem lại.
 */
type ClassDetail = {
  class?: { id: number; name: string; schedule?: string | null; courseTitle?: string | null };
};

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

  // 404 = lớp không tồn tại HOẶC không phụ trách lớp đó — backend cố ý trả cùng
  // một mã để không lộ ra lớp có tồn tại hay không, nên chỗ này mới là nơi duy
  // nhất được nói câu "không phải giảng viên phụ trách". Mọi mã khác (500, mất
  // kết nối) phải nói đúng câu của nó, không mượn câu này.
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
          {klass.schedule && <span className="text-small text-ink-3">{klass.schedule}</span>}
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <SessionsClient
          classId={Number(classId)}
          className={klass.name}
          initial={list.ok ? list.data.sessions : []}
        />
      </main>
    </div>
  );
}
