import Link from 'next/link';

import { chanTu } from '@/lib/chanTu';
import { HD_SO_DAU_BAI, type SoDauBai } from '@/lib/chuongTrinh';
import { lucVN } from '@/lib/gioVN';
import { serverJson } from '@/lib/server-api';

import SoDauBaiClient from './SoDauBaiClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Sổ đầu bài | TopHSA' };

/**
 * SỔ ĐẦU BÀI MỘT BUỔI (E1, 25/09/2026) — bảng yêu cầu TopHSA dòng 15, 16.
 *
 * Giảng viên, trợ giảng của lớp, học vụ, quản trị (`IsTeachingStaff` + `can_see_class`
 * ở máy chủ — người không dạy lớp nhận 404 như mọi trang buổi học). Luật ghi và mọi
 * kiểm tra ở `chuong_trinh/so_dau_bai.py`; trang này chỉ dựng biểu mẫu.
 */
export default async function SoDauBaiPage({ params }: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await params;
  const kq = await serverJson<SoDauBai>(`/api/teach/sessions/${sessionId}/so-dau-bai`, { requireAuth: true }, HD_SO_DAU_BAI);
  if (!kq.ok) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16" data-chan={chanTu(kq.status)}>
        <h1 className="text-title text-ink">Không mở được sổ đầu bài</h1>
        <p className="mt-2 text-body text-ink-2">
          {kq.status === 404 ? 'Buổi học không tồn tại, hoặc bạn không dạy lớp này.' : kq.message}
        </p>
        <Link href="/giang-day" className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline">
          ← Việc hôm nay
        </Link>
      </main>
    );
  }
  const s = kq.data.session;
  return (
    <main>
      <div className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-4xl flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-4">
          <Link href={`/giang-day/buoi-hoc/${s.classId}`} className="-my-3 py-3 text-small text-ink-3 hover:text-brand-ink">
            ← {s.className}
          </Link>
          <h1 className="text-section text-ink">Sổ đầu bài · {lucVN(s.startsAt)}</h1>
          {s.topic && <span className="text-small text-ink-3">{s.topic}</span>}
          <Link href={`/giang-day/chuong-trinh/${s.classId}`} className="-my-3 py-3 text-small text-brand-ink underline">
            Chương trình lớp
          </Link>
        </div>
      </div>
      <div className="mx-auto max-w-4xl px-4 py-6">
        <SoDauBaiClient initial={kq.data} />
      </div>
    </main>
  );
}
