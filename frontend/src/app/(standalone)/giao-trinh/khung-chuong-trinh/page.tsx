import Link from 'next/link';

import AppShell from '@/components/AppShell';
import PageStyles from '@/components/PageStyles';
import { HD_MUC_LUC, type MucLuc } from '@/lib/chuongTrinh';
import { HD_TOI, type Toi } from '@/lib/hinhDang';
import { serverJson } from '@/lib/server-api';
import { VAI_BIEN_TAP, VAI_HOC_VU, VAI_QUAN_TRI } from '@/lib/vaiTro';

import KhungClient from './KhungClient';

/**
 * SOẠN KHUNG CHƯƠNG TRÌNH THEO BUỔI (E1, 25/09/2026) — bảng yêu cầu TopHSA 5.2, dòng 4–6.
 *
 * Cổng RIÊNG, rộng hơn `/giao-trinh`: khung là thứ học vụ giao cho lớp và đối chiếu tiến
 * độ, nên học vụ soạn được (lead chốt 25/09). Trang gốc `/giao-trinh` (khoá, bài, câu hỏi)
 * vẫn chỉ biên tập + quản trị. `DUOC_VAO` ở đây phải khớp `IsCurriculumPlanner` —
 * `e2e/unit/khu-theo-vai.test.mjs` đối chiếu qua thẻ "Khung chương trình".
 *
 * Dữ liệu đầu: một lượt `api/admin/chuong-trinh/khung` (môn + phiên bản). Cây của một
 * phiên bản nạp khi bấm mở — cửa `courseadmin/syllabus.py`.
 */
export const dynamic = 'force-dynamic';
export const metadata = { title: 'Khung chương trình | TopHSA' };

const DUOC_VAO = new Set([VAI_QUAN_TRI, VAI_HOC_VU, VAI_BIEN_TAP]);

export default async function KhungChuongTrinhPage() {
  const me = await serverJson<Toi>('/api/user', { requireAuth: true }, HD_TOI);
  if (!me.ok) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="text-title text-ink">Chưa mở được khung chương trình</h1>
        <p className="mt-2 text-body text-ink-2">{me.message}</p>
        <Link href="/dashboard" className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline">
          ← Về trang của tôi
        </Link>
      </main>
    );
  }
  const vai = me.data.role || '';
  if (!DUOC_VAO.has(vai)) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16" data-chan="vai">
        <h1 className="text-title text-ink">Khu này dành cho người soạn chương trình</h1>
        <p className="mt-2 text-body text-ink-2">
          Tài khoản của bạn đang ở vai <b>{vai || 'chưa đặt'}</b>. Học vụ, biên tập nội dung và
          quản trị viên soạn được khung chương trình. Giảng viên xem khung của lớp mình ở màn
          Buổi học → Chương trình.
        </p>
        <Link href="/dashboard" className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline">
          ← Về trang của tôi
        </Link>
      </main>
    );
  }

  const kq = await serverJson<MucLuc>('/api/admin/chuong-trinh/khung', { requireAuth: true }, HD_MUC_LUC);
  const coGiaoTrinh = vai === VAI_QUAN_TRI || vai === VAI_BIEN_TAP;

  return (
    <div className="min-h-dvh bg-ground">
      <PageStyles hrefs={['/static/css/theme.css', '/static/css/shell.css']} />
      <AppShell
        khu="Giáo trình"
        dieuKhien="react"
        spa={false}
        vai={vai}
        ten={me.data.name ?? undefined}
        muc={[
          ...(coGiaoTrinh
            ? [{ trang: null, nhan: 'Giáo trình', icon: 'book-open', emoji: '', url: '/giao-trinh' }]
            : []),
          { trang: null, nhan: 'Khung chương trình', icon: 'calendar', emoji: '', url: '/giao-trinh/khung-chuong-trinh' },
        ]}
      />
      <KhungClient initial={kq.ok ? kq.data : null} loi={kq.ok ? null : kq.message} />
    </div>
  );
}
