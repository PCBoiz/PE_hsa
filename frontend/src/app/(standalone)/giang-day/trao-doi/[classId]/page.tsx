import Link from 'next/link';

import DienDanLop from '@/components/DienDanLop';
import { chanTu } from '@/lib/chanTu';
import { HD_CHI_TIET_LOP, type ChiTietLop } from '@/lib/hinhDang';
import { serverJson } from '@/lib/server-api';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Trao đổi của lớp | TopHSA' };

/**
 * `/giang-day/trao-doi/<classId>` — diễn đàn riêng của lớp, phía người dạy (§75, dòng 20).
 *
 * VÌ SAO LÀ MÀN NÀY, KHÔNG PHẢI HỘP CHAT. Anh Sơn chốt 27/09/2026: *"Những phần như này thì
 * mình biến thành nhắn tin qua Zalo hoặc qua diễn đàn riêng của lớp, không làm thành 1
 * messenger trong ứng dụng mình đâu"*.
 *
 * Trợ giảng VÀO ĐƯỢC — cùng lý do với tab "Thông báo lớp": trợ giảng là người trao đổi với
 * học viên hằng ngày. Hàng rào thật nằm ở máy chủ (`forum/views.py::vao_duoc_dien_dan_lop`),
 * tab này chỉ là lối đi.
 *
 * Trang chỉ lấy TÊN LỚP ở máy chủ; phần bài và trả lời để component tải sau khi gắn — một
 * lớp chạy cả khoá thì danh sách dài, và HTML đầu không cần mang theo nó.
 */
export default async function TraoDoiLopPage({
  params,
}: {
  params: Promise<{ classId: string }>;
}) {
  const { classId } = await params;
  const chiTiet = await serverJson<ChiTietLop>(
    `/api/teach/classes/${classId}`, { requireAuth: true }, HD_CHI_TIET_LOP);
  const klass = chiTiet.ok ? chiTiet.data.class : undefined;

  // 404 = lớp không tồn tại HOẶC không phụ trách — máy chủ cố ý trả cùng một mã.
  if (!klass) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16" data-chan={chanTu(chiTiet.ok ? 404 : chiTiet.status)}>
        <h1 className="text-title text-ink">Không mở được lớp này</h1>
        <p className="mt-2 text-body text-ink-2">
          {!chiTiet.ok && chiTiet.status !== 404
            ? chiTiet.message
            : 'Lớp không tồn tại, hoặc bạn không phụ trách lớp đó.'}
        </p>
        <Link href="/giang-day" className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline">
          ← Về khu Giảng dạy
        </Link>
      </main>
    );
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6">
      <div>
        <h1 className="text-title text-ink">Trao đổi · {klass.name}</h1>
        <p className="mt-1 text-body text-ink-2">
          Chỗ nhắn cho cả lớp và đọc lại được về sau. Việc riêng của một em thì dùng hộp{' '}
          <Link href="/yeu-cau" className="text-brand-ink underline">Yêu cầu</Link>.
        </p>
      </div>
      <DienDanLop classId={Number(classId)} tenLop={klass.name} />
    </div>
  );
}
