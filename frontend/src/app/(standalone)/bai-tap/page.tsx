import Link from 'next/link';

import AppShell from '@/components/AppShell';
import PageStyles from '@/components/PageStyles';

import { nhomCuaVai } from '@/lib/nhomVai';
import { serverJson, type HinhDang } from '@/lib/server-api';
import { z } from 'zod';

import { layVai } from '../quan-tri/layVai';
import MyAssignmentsClient, { type BaiCuaToi } from './MyAssignmentsClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Bài tập của bạn | TopHSA' };

/* Hình dạng `/api/assignments` (T18 mức 2). */
const HINH_DANG = z.looseObject({
  assignments: z.array(z.looseObject({
    id: z.number(), title: z.string(), description: z.string().nullable(),
    topic: z.string().nullable(), className: z.string(), status: z.string(),
    dueAt: z.string().nullable(), maxScore: z.number().nullable(),
    submittedAt: z.string().nullable(), content: z.string().nullable(),
    score: z.number().nullable(), scorePct: z.number().nullable(),
    feedback: z.string().nullable(), gradedAt: z.string().nullable(),
  })),
}) satisfies HinhDang<{ assignments: BaiCuaToi[] }>;

export default async function BaiTapCuaToiPage() {
  /* Hai lượt gọi SONG SONG: thêm vai không được cộng một vòng mạng vào trang.
     Vì sao cần vai (20/09/2026, lượt đi sáu vai): trợ giảng gắn với lớp qua
     CÙNG bảng `class_members` với học viên, nên `/api/assignments` liệt kê bài
     của lớp họ phụ trách và trang này mời họ "Làm bài" bài mình sẽ chấm. Thanh
     đã ẩn mục với nhân sự; đây là chốt cho đường dẫn gõ thẳng. Không phải hàng
     rào — bài nộp của nhân sự vẫn bị máy chủ lọc `chi_hoc_vien` khi chấm. */
  const [kq, vai] = await Promise.all([
    serverJson<{ assignments: BaiCuaToi[] }>('/api/assignments', { requireAuth: true }, HINH_DANG),
    layVai(),
  ]);
  const nhanSu = vai.ok && nhomCuaVai(vai.vai) === 'nhan-su';

  return (
    <div className="min-h-dvh bg-ground">
      {/* THANH CHUNG (21/09/2026). Trang này từng tự dựng một dải đầu riêng:
          "← Về trang chính", tiêu đề, nút mặt trăng — không có dãy điều hướng,
          không chuông, không Đăng xuất. Muốn sang Thi thử phải quay về Trang
          của tôi trước (agent rà điện thoại, F30). Cùng lỗ đã vá ở Thi thử,
          Vận hành, Giảng dạy và Soạn giáo trình. `dieuKhien="react"` vì trang
          không nạp `main.js`. */}
      <PageStyles hrefs={['/static/css/theme.css', '/static/css/shell.css']} />
      <AppShell
        trang="/bai-tap"
        spa={false}
        dieuKhien="react"
        vai={vai.ok ? vai.vai : undefined}
        ten={vai.ok ? vai.ten : undefined}
      />
      <main className="mx-auto max-w-3xl px-4 pb-6 pt-[calc(var(--topbar-h)+1.5rem)]">
        <h1 className="mb-4 text-section text-ink">Bài tập</h1>
        {nhanSu ? (
          <section className="rounded-lg border border-line bg-surface p-5 text-ink" aria-labelledby="bt-nhan-su" data-chan="vai">
            <h2 id="bt-nhan-su" className="m-0 text-lg font-semibold">Trang này dành cho học viên</h2>
            <p className="mt-2 mb-0 text-ink-2">
              Bạn đang đăng nhập với vai nhân sự. Giao bài, xem bài nộp và chấm ở khu Giảng dạy —
              chọn lớp rồi vào mục <strong>Bài tập</strong>.
            </p>
            <p className="mt-3 mb-0">
              <Link href="/giang-day" className="font-semibold text-brand-ink underline-offset-2 hover:underline">
                Tới Việc hôm nay →
              </Link>
            </p>
          </section>
        ) : (
          <MyAssignmentsClient
            initial={kq.ok ? kq.data.assignments : []}
            // Danh sách rỗng vì chưa được giao bài, và danh sách rỗng vì không đọc
            // được, trông y hệt nhau — và ở trường hợp thứ hai em sẽ tưởng mình
            // không có bài phải làm.
            loiTai={kq.ok ? null : kq.message}
          />
        )}
      </main>
    </div>
  );
}
