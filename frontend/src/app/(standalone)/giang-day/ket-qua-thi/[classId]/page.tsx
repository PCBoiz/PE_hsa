import Link from 'next/link';

import { ThemeToggle } from '@/components/ui';
import { HD_CHI_TIET_LOP, type ChiTietLop } from '@/lib/hinhDang';
import { serverJson } from '@/lib/server-api';

import NhapKetQuaClient from './NhapKetQuaClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Nhập kết quả thi thử | TopHSA' };

/**
 * Nhập kết quả thi thử từ hệ thống khảo thí của trung tâm.
 *
 * Vì sao màn này tồn tại: hệ thống khảo thí TopHSA đang dùng "chỉ xem được trên
 * web" — không có đường nối máy với máy. Nhưng tờ PDF nó xuất cho từng em thì
 * đọc được, và trong đó có thứ báo cáo phụ huynh đang thiếu: điểm một kỳ thi
 * THẬT cùng tỉ lệ đúng theo từng đơn vị kiến thức. Nên đường vào là học vụ kéo
 * thả tệp, không cần bên kia mở gì cả.
 */
export default async function NhapKetQuaThiPage({
  params,
}: {
  params: Promise<{ classId: string }>;
}) {
  const { classId } = await params;
  const detail = await serverJson<ChiTietLop>(
    `/api/teach/classes/${classId}`, { requireAuth: true }, HD_CHI_TIET_LOP);

  // 404 = lớp không tồn tại HOẶC không phụ trách — backend cố ý trả cùng một mã.
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
        <Link
          href="/dashboard"
          className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline"
        >
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
              href={`/giang-day/bao-cao/${klass.id}`}
              className="-my-3 py-3 text-small text-brand-ink underline"
            >
              Báo cáo phụ huynh
            </Link>
            <ThemeToggle className="ml-auto" />
          </div>
        </div>
        <div className="mx-auto max-w-5xl px-4 py-6">
        <h2 className="text-title text-ink">Nhập kết quả thi thử của trung tâm</h2>
        <p className="mt-2 max-w-3xl text-body text-ink-2">
          Tải tờ PDF kết quả mà hệ thống khảo thí xuất cho từng em. Hệ thống đọc điểm ba phần, tổng
          điểm và tỉ lệ đúng theo từng đơn vị kiến thức, rồi đưa vào báo cáo phụ huynh — thay cho
          việc chép tay từng con số.
        </p>
        <NhapKetQuaClient classId={klass.id} />
        </div>
      </main>
    </div>
  );
}
