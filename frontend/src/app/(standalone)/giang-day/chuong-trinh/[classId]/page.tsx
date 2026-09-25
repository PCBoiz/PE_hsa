import Link from 'next/link';

import { chanTu } from '@/lib/chanTu';
import { HD_CT_LOP, type CtLop } from '@/lib/chuongTrinh';
import { serverJson } from '@/lib/server-api';

import ChuongTrinhLopClient from './ChuongTrinhLopClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Chương trình lớp | TopHSA' };

/**
 * CHƯƠNG TRÌNH CỦA MỘT LỚP (E1, 25/09/2026) — bảng yêu cầu TopHSA dòng 4, 5, 9.
 *
 * Mọi người dạy lớp (giảng viên, trợ giảng, học vụ, quản trị) xem: khung lớp đang theo,
 * buổi học gắn với buổi khung nào, sổ đầu bài từng buổi, tiến độ lớp và % từng em.
 * Học vụ / quản trị có thêm ô "Nhận khung" (`quyen.nhanKhung` — máy chủ tính bằng chính
 * lớp quyền của cửa ghi). Một lượt `api/teach/classes/<id>/chuong-trinh`; 404 = không
 * được xem lớp này (cùng luật mọi trang lớp).
 */
export default async function ChuongTrinhLopPage({ params }: { params: Promise<{ classId: string }> }) {
  const { classId } = await params;
  const kq = await serverJson<CtLop>(`/api/teach/classes/${classId}/chuong-trinh`, { requireAuth: true }, HD_CT_LOP);
  if (!kq.ok) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16" data-chan={chanTu(kq.status)}>
        <h1 className="text-title text-ink">Không mở được chương trình của lớp này</h1>
        <p className="mt-2 text-body text-ink-2">
          {kq.status === 404 ? 'Lớp không tồn tại, hoặc bạn không dạy lớp đó.' : kq.message}
        </p>
        <Link href="/giang-day" className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline">
          ← Việc hôm nay
        </Link>
      </main>
    );
  }
  const lop = kq.data.class;
  return (
    <main>
      <div className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-5xl flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-4">
          <Link href={`/giang-day/buoi-hoc/${lop.id}`} className="-my-3 py-3 text-small text-ink-3 hover:text-brand-ink">
            ← Buổi học &amp; điểm danh
          </Link>
          <h1 className="text-section text-ink">Chương trình · {lop.name}</h1>
          {lop.courseTitle && <span className="text-small text-ink-3">{lop.courseTitle}</span>}
        </div>
      </div>
      <div className="mx-auto max-w-5xl px-4 py-6">
        <ChuongTrinhLopClient initial={kq.data} />
      </div>
    </main>
  );
}
