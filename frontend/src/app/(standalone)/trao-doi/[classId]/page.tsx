import Link from 'next/link';

import DienDanLop from '@/components/DienDanLop';
import { HD_DS_BAI, type DsBai } from '@/lib/dienDan';
import { serverJson } from '@/lib/server-api';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Trao đổi của lớp | TopHSA' };

/**
 * `/trao-doi/<classId>` — diễn đàn riêng của lớp, phía HỌC VIÊN (§75, dòng 20).
 *
 * VÌ SAO KHÔNG DÙNG CHUNG ĐƯỜNG DẪN VỚI NGƯỜI DẠY. Khu `/giang-day/...` có thanh điều hướng
 * của người dạy và lấy tên lớp qua `/api/teach/classes/<id>` — một cửa `IsTeachingStaff`.
 * Học viên gọi cửa ấy sẽ nhận 403 và màn hỏng vì lý do không liên quan gì tới quyền đọc
 * diễn đàn. Nên phía em là một trang riêng, lấy tên lớp từ CHÍNH cửa diễn đàn (§75 trả kèm
 * `lop.ten`) — em chỉ gọi đúng cửa em được phép gọi.
 *
 * Hàng rào vẫn là một: `forum/views.py::vao_duoc_dien_dan_lop`. Em không học lớp ấy thì cửa
 * trả 404, và trang này hiện đúng câu ấy — không tự dựng thêm luật nào.
 */
export default async function TraoDoiCuaEmPage({
  params,
}: {
  params: Promise<{ classId: string }>;
}) {
  const { classId } = await params;
  const ds = await serverJson<DsBai>(
    `/api/posts?lop=${classId}&page=1&per_page=1`, { requireAuth: true }, HD_DS_BAI);

  if (!ds.ok || !ds.data.lop) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="text-title text-ink">Không mở được phần trao đổi này</h1>
        <p className="mt-2 text-body text-ink-2">
          {ds.ok
            ? 'Lớp không tồn tại, hoặc bạn không còn học lớp đó.'
            : ds.status === 404
              ? 'Lớp không tồn tại, hoặc bạn không còn học lớp đó.'
              : ds.message}
        </p>
        <Link href="/dashboard" className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline">
          ← Về trang của tôi
        </Link>
      </main>
    );
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6">
      <div>
        <Link href="/dashboard" className="-mx-2 inline-flex min-h-11 items-center px-2 text-small text-ink-3 hover:text-brand-ink">
          ← Trang của tôi
        </Link>
        <h1 className="text-title text-ink">Trao đổi · {ds.data.lop.ten}</h1>
        <p className="mt-1 text-body text-ink-2">
          Cả lớp đọc được. Việc riêng của em thì gửi qua{' '}
          <Link href="/yeu-cau" className="text-brand-ink underline">Hỏi &amp; yêu cầu</Link>.
        </p>
      </div>
      <DienDanLop classId={Number(classId)} tenLop={ds.data.lop.ten} />
    </div>
  );
}
