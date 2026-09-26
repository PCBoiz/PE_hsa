import Link from 'next/link';

import { chanTu } from '@/lib/chanTu';
import { HD_CHI_TIET_LOP, type ChiTietLop } from '@/lib/hinhDang';
import { serverJson } from '@/lib/server-api';
import { HD_DS_LOP, type DsLop } from '@/lib/thongBaoSoan';

import SoanThongBaoLop from './SoanThongBaoLop';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Thông báo lớp | TopHSA' };

/**
 * `/giang-day/thong-bao/<classId>` — giảng viên và TRỢ GIẢNG nhắn cho lớp mình (dòng 20).
 *
 * ── VÌ SAO ĐẶT TRONG KHU GIẢNG DẠY, THEO LỚP ──────────────────────────────
 *
 * Cửa backend là `/api/teach/classes/<id>/thong-bao`: đối tượng CỐ ĐỊNH là lớp trên đường
 * dẫn, và `can_see_class` quyết định ai mở được. Một trang cấp khu (`/giang-day/thong-bao`)
 * sẽ phải tự dựng ô chọn lớp — tức dựng lại đúng thứ đường dẫn đã mang, và mở thêm một chỗ
 * để lệch với hàng rào của máy chủ. Nên nó là tab THỨ TƯ của lớp, cạnh Buổi học và Bài tập,
 * đúng chỗ người ta đang đứng khi nghĩ "phải nhắc cả lớp".
 *
 * Trợ giảng vào được (anh Sơn chốt 26/09/2026, quyết định 1: trợ giảng là người nhắc học
 * viên hằng ngày) — nên tab này KHÔNG bị lọc khỏi thanh của trợ giảng, khác tab "Báo cáo
 * phụ huynh". Hàng rào thật vẫn ở `permission_classes` + `can_see_class`.
 *
 * Tải danh sách NGAY trên máy chủ, cùng lối với `/thong-bao`: người gửi mở màn này để
 * kiểm "tối qua tôi nhắc chưa" trước khi soạn, nên danh sách phải có sẵn trong HTML đầu.
 */
export default async function ThongBaoLopPage({
  params,
}: {
  params: Promise<{ classId: string }>;
}) {
  const { classId } = await params;
  const [chiTiet, ds] = await Promise.all([
    serverJson<ChiTietLop>(`/api/teach/classes/${classId}`, { requireAuth: true }, HD_CHI_TIET_LOP),
    serverJson<DsLop>(`/api/teach/classes/${classId}/thong-bao`, { requireAuth: true }, HD_DS_LOP),
  ]);

  // 404 = lớp không tồn tại HOẶC không phụ trách — backend cố ý trả cùng một mã để không
  // lộ lớp có tồn tại hay không. Mọi mã khác phải nói đúng câu của nó, không mượn câu này.
  const lop = chiTiet.ok ? chiTiet.data.class : undefined;
  if (!lop) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16" data-chan={chanTu(chiTiet.ok ? 404 : chiTiet.status)}>
        <h1 className="text-title text-ink">Không mở được lớp này</h1>
        <p className="mt-2 text-body text-ink-2">
          {!chiTiet.ok && chiTiet.status !== 404
            ? chiTiet.message
            : 'Lớp không tồn tại, hoặc bạn không phụ trách lớp đó.'}
        </p>
        <Link
          href="/giang-day"
          className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline"
        >
          ← Về khu Giảng dạy
        </Link>
      </main>
    );
  }

  return (
    <main>
      {/* Dải tiêu đề nằm TRONG `<main>`: là `<header>` ngoài `main` thì thành banner thứ hai
          (axe `landmark-no-duplicate-banner`), là `div` ngoài `main` thì rơi ngoài mọi mốc
          (axe `region`). Cùng khuôn với ba trang lớp còn lại. */}
      <div className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-5xl flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-4">
          <Link href="/giang-day" className="-my-3 py-3 text-small text-ink-3 hover:text-brand-ink">
            ← Việc hôm nay
          </Link>
          <h1 className="text-section text-ink">Thông báo · {lop.name}</h1>
          <Link
            href={`/giang-day/buoi-hoc/${lop.id}`}
            className="-my-3 py-3 text-small text-brand-ink underline"
          >
            Buổi học &amp; điểm danh
          </Link>
        </div>
      </div>
      <div className="mx-auto max-w-5xl px-4 py-6">
        <SoanThongBaoLop
          classId={Number(classId)}
          tenLop={lop.name}
          dauTien={ds.ok ? ds.data.items : []}
          // KHÔNG nuốt lỗi bằng `dauTien={ok ? … : []}`: danh sách rỗng vì chưa gửi gì, và
          // rỗng vì không đọc được, trông y hệt nhau — và ở trường hợp thứ hai người gửi sẽ
          // nhắc lại lần thứ hai một điều đã nhắc.
          loiTai={ds.ok ? null : ds.message}
        />
      </div>
    </main>
  );
}
