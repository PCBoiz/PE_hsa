import Link from 'next/link';

import NutIn from '@/components/NutIn';
import { ToBaoCao, type BaoCao } from '@/components/ToBaoCao';
import { serverJson } from '@/lib/server-api';

import TaoDuongDan from './TaoDuongDan';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Báo cáo gửi phụ huynh | TopHSA' };

/**
 * Hình dạng do `teaching/parent_report.py:ParentReportView` trả về.
 *
 * CẢNH BÁO đã trả giá một lần ở màn hình buổi học: `serverJson<T>` chỉ ÉP KIỂU,
 * không kiểm gì lúc chạy — kiểu ở đây là lời tự khai về thứ người viết TƯỞNG
 * backend trả. Đổi tên khoá thì phải mở trang thật xem lại.
 */
export default async function BaoCaoPhuHuynhPage({
  params,
  searchParams,
}: {
  params: Promise<{ classId: string; userId: string }>;
  searchParams: Promise<{ from?: string; to?: string }>;
}) {
  const { classId, userId } = await params;
  const { from, to } = await searchParams;
  const qs = new URLSearchParams();
  if (from) qs.set('from', from);
  if (to) qs.set('to', to);

  const kq = await serverJson<BaoCao>(
    `/api/teach/classes/${classId}/students/${userId}/parent-report${qs.size ? `?${qs}` : ''}`,
    { requireAuth: true },
  );

  if (!kq.ok) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="text-title text-ink">Không mở được báo cáo này</h1>
        {/* Nói ĐÚNG chuyện đã xảy ra. Bản trước in một câu cố định "học viên
            không thuộc lớp này", nên một sự cố máy chủ cũng hiện y hệt và người
            đọc đi tìm nhầm chỗ. */}
        <p className="mt-2 text-body text-ink-2">{kq.message}</p>
        <Link
          href={`/giang-day/buoi-hoc/${classId}`}
          className="mt-6 inline-block text-body text-brand-ink underline"
        >
          ← Về lớp
        </Link>
      </main>
    );
  }

  const bc = kq.data;

  return (
    <div className="min-h-dvh bg-ground print:bg-white">
      {/* Thanh điều hướng KHÔNG in ra giấy: tờ gửi phụ huynh không nên có nút
          bấm và đường dẫn quay lại — nó chỉ làm rối và tốn mực. */}
      <header className="border-b border-line bg-surface print:hidden">
        <div className="mx-auto flex max-w-3xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-4">
          <Link
            href={`/giang-day/buoi-hoc/${classId}`}
            className="-my-3 inline-block py-3 text-small text-ink-3 hover:text-brand-ink"
          >
            ← Về lớp
          </Link>
          <h1 className="flex-1 text-section text-ink">Báo cáo gửi phụ huynh</h1>
          {/* Nói ngay ở thanh: tờ này sẽ tới ai. Trước 07/09/2026 màn hình
              không có chỗ nào cho biết, nên giảng viên in ra rồi mới phát hiện
              không có số nào để gửi. */}
          <span className="text-small text-ink-3">
            {bc.parent.phone
              ? <>Gửi tới {bc.parent.name || 'phụ huynh'} · {bc.parent.phone}</>
              : <span className="text-warning-ink">Chưa có số Zalo của phụ huynh</span>}
          </span>
          <NutIn />
        </div>
      </header>

      <main className="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6 print:max-w-none print:gap-0 print:px-0 print:py-0">
        {/* Cấp đường dẫn cho phụ huynh mở. Đặt TRÊN tờ báo cáo chứ không dưới:
            đây là việc giảng viên vào trang này để làm, còn tờ báo cáo là thứ
            họ liếc qua để kiểm trước khi gửi. */}
        <TaoDuongDan classId={classId} userId={userId} coSoPhuHuynh={!!bc.parent.phone} />

        {bc.warnings.length > 0 && (
          <p
            role="alert"
            className="mb-4 rounded-md bg-warning/10 px-3 py-2 text-small text-warning-ink print:hidden"
          >
            {bc.warnings.join(' ')}
          </p>
        )}

        <ToBaoCao bc={bc} />
      </main>
    </div>
  );
}
