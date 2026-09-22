import Link from 'next/link';

import NutIn from '@/components/NutIn';
import { ToBaoCao, type BaoCao } from '@/components/ToBaoCao';
import { HD_BAO_CAO } from '@/lib/hinhDang';
import { serverJson } from '@/lib/server-api';

import KhoiDuongDan from './KhoiDuongDan';

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
    HD_BAO_CAO,
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
          className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline"
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

      <main>
          {/* Dải tiêu đề nằm TRONG `<main>`: là `<header>` ngoài `main` thì thành
              banner thứ hai (axe `landmark-no-duplicate-banner`), là `div` ngoài
              `main` thì rơi ngoài mọi mốc (axe `region`) — đo 20/09/2026. */}
        <div className="border-b border-line bg-surface print:hidden">
          <div className="mx-auto flex max-w-3xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-4">
            {/* Về DANH SÁCH báo cáo của lớp, không về trang buổi học (22/09/2026,
                agent GV→PH F12): làm tờ cho em thứ hai từng phải Về lớp → tab
                Báo cáo phụ huynh → Xem tờ. */}
            <Link
              href={`/giang-day/bao-cao/${classId}`}
              className="-my-3 inline-block py-3 text-small text-ink-3 hover:text-brand-ink"
            >
              ← Báo cáo cả lớp
            </Link>
            {/* `min-w-[14ch]`: khổ điện thoại, tiêu đề bị ép chung hàng với "Về lớp"
                và dòng người nhận thành một cột chữ năm dòng (soi ảnh 17/09/2026).
                Có bề rộng tối thiểu thì flex-wrap đẩy phần còn lại xuống hàng dưới. */}
            <h1 className="min-w-[14ch] flex-1 text-section text-ink">Báo cáo gửi phụ huynh</h1>
            <NutIn />
            {/* Nói ngay ở thanh: tờ này sẽ tới ai. Trước 07/09/2026 màn hình
                không có chỗ nào cho biết, nên giảng viên in ra rồi mới phát hiện
                không có số nào để gửi. Email trước số Zalo: email là kênh CHÍNH từ
                07/09 — bản trước chỉ đọc số Zalo nên báo "chưa có" cho cả em đã có
                email (17/09). */}
            <span className="basis-full text-small text-ink-3">
              {bc.parent.email || bc.parent.phone
                ? <>Gửi tới {bc.parent.name || 'phụ huynh'} · {[bc.parent.email, bc.parent.phone].filter(Boolean).join(' · ')}</>
                : <span className="text-warning-ink">Chưa có email hay số Zalo của phụ huynh</span>}
            </span>
          </div>
        </div>
        <div className="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6 print:max-w-none print:gap-0 print:px-0 print:py-0">
       {/* Cấp đường dẫn cho phụ huynh mở. Đặt TRÊN tờ báo cáo chứ không dưới:
            đây là việc giảng viên vào trang này để làm, còn tờ báo cáo là thứ
            họ liếc qua để kiểm trước khi gửi. */}
        <KhoiDuongDan
          classId={classId}
          userId={userId}
          coLienLac={!!(bc.parent.email || bc.parent.phone)}
        />

        {bc.warnings.length > 0 && (
          <p
            role="alert"
            className="mb-4 rounded-md bg-warning/10 px-3 py-2 text-small text-warning-ink print:hidden"
          >
            {bc.warnings.join(' ')}
          </p>
        )}

        <ToBaoCao bc={bc} />
        </div>
      </main>
    </div>
  );
}
