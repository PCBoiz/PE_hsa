import Link from 'next/link';

import AppShell from '@/components/AppShell';
import PageStyles from '@/components/PageStyles';

import { HD_TOI, type Toi } from '@/lib/hinhDang';
import { serverJson, type HinhDang } from '@/lib/server-api';
import { z } from 'zod';
import { VAI_BIEN_TAP, VAI_QUAN_TRI } from '@/lib/vaiTro';

import { type DeRow } from './DeThi';
import SoanClient, { type KhoaRow } from './SoanClient';

/**
 * SOẠN GIÁO TRÌNH — khoá học, bài học, và nội dung 5 bước của một bài.
 *
 * ── VÌ SAO VIẾT LẠI BẰNG REACT (T35, 04/09/2026) ──────────────────────────
 *
 * Bản cũ là một vỏ HTML tĩnh được `public/static/js/pages/admin.inline.js`
 * (749 dòng, KHÔNG đi qua bundler) làm cho sống. Hai hệ quả đo được:
 *
 * 1. **Bộ soạn nội dung không dùng được.** Nó đọc/ghi `drill.seconds` trong khi
 *    engine đọc `drill.time_seconds`, nên bộ kiểm phía máy chủ từ chối mọi lần
 *    lưu bài có phòng luyện — tức cả 76 bài đang có. Và nó xử lý `note` số ít,
 *    một trường KHÔNG bài nào có, trong khi khối `notes` thật (`tip`,
 *    `formula`, `key_points`) không hiện ra ở đâu và sẽ bị bỏ khi lưu.
 * 2. Một lỗi cú pháp trong tệp ấy đi thẳng lên production qua MỌI cửa kiểm —
 *    đã xảy ra 27/08 và giết cả màn Quản trị. Đó là lý do CI phải chạy
 *    `node --check` riêng cho 15 tệp JS thuần.
 *
 * Lỗi ① là lỗi TÊN TRƯỜNG, thứ `tsc` bắt được ngay lúc biên dịch nếu có kiểu.
 * Nay có: `src/lib/soanBai.ts` khai kiểu, và phép gộp nằm ở một hàm THUẦN có
 * bộ kiểm riêng chạy trong CI (`e2e/unit/soan-bai.test.mjs`).
 *
 * ── GÁC QUYỀN Ở MÁY CHỦ ───────────────────────────────────────────────────
 *
 * Bản cũ không gác gì cả — nó dựng cả trang rồi để API trả 403, nên người
 * không có quyền thấy một màn hình đầy bảng trống trông như hệ thống hỏng.
 */
export const dynamic = 'force-dynamic';
export const metadata = { title: 'Soạn giáo trình | TopHSA' };

// Lấy từ bảng vai CHUNG, không gõ lại chuỗi. Hai chuỗi gõ tay ở đây là bảng
// thứ tư trả lời câu "ai vào được đâu" — và ba bảng trước đã trôi khỏi nhau
// đúng vì thế (xem `quan-tri/vai.ts`). Một hàng rào quyền trôi thì không kêu.
const DUOC_VAO = new Set([VAI_QUAN_TRI, VAI_BIEN_TAP]);

/* Hình dạng hai danh sách khu này đọc (T18 mức 2). */
const HD_KHOA = z.looseObject({
  courses: z.array(z.looseObject({
    id: z.string(), title: z.string(),
    subtitle: z.string().nullable().optional(), lessons: z.number().nullable().optional(),
  })),
}) satisfies HinhDang<{ courses: KhoaRow[] }>;
const HD_DE = z.looseObject({
  exams: z.array(z.looseObject({
    id: z.number(), title: z.string(), durationMinutes: z.number().nullable(),
    totalQuestions: z.number().nullable(), isPublished: z.boolean(), attempts: z.number(),
  })),
}) satisfies HinhDang<{ exams: DeRow[] }>;

export default async function SoanGiaoTrinhPage() {
  const me = await serverJson<Toi>('/api/user', { requireAuth: true }, HD_TOI);

  // "Không đọc được tài khoản" KHÁC "không đủ quyền": backend ngủ dậy hay mạng
  // hỏng cũng rơi vào đây, và nói "bạn không có quyền" lúc đó là đẩy người dùng
  // đi hỏi nhầm chỗ. Cùng luật với khu `/quan-tri`.
  if (!me.ok) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="text-title text-ink">Chưa mở được khu soạn giáo trình</h1>
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
        <h1 className="text-title text-ink">Khu này dành cho người soạn giáo trình</h1>
        <p className="mt-2 text-body text-ink-2">
          Tài khoản của bạn đang ở vai <b>{vai || 'chưa đặt'}</b>. Cần vai{' '}
          <b>Biên tập nội dung</b> hoặc <b>quản trị viên</b> để vào đây — nhờ quản trị viên
          đổi giúp nếu bạn phụ trách nội dung.
        </p>
        <Link href="/dashboard" className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline">
          ← Về trang của tôi
        </Link>
      </main>
    );
  }

  const [kq, de] = await Promise.all([
    serverJson<{ courses: KhoaRow[] }>('/api/admin/courses', { requireAuth: true }, HD_KHOA),
    serverJson<{ exams: DeRow[] }>('/api/admin/mock-exams', { requireAuth: true }, HD_DE),
  ]);

  /* THANH CHUNG cho khu này (20/09/2026). Đây là chỗ THỨ TƯ của cùng một lỗ —
     Thi thử (06/09), Vận hành (07/09), Giảng dạy (07/09) đều đã vá: một khu
     dựng vỏ riêng thì mất tên người đăng nhập, mất chuông, và mất ĐƯỜNG ĐĂNG
     XUẤT. Nặng nhất với vai Biên tập nội dung: /admin là màn duy nhất của họ,
     nên trước hôm nay họ không có cách nào thoát tài khoản.
     `dieuKhien="react"` vì khu này không nạp `main.js`; `spa={false}` vì không
     có trang nào của SPA cũ ở đây. */
  return (
    <div className="min-h-dvh bg-ground">
      <PageStyles hrefs={['/static/css/theme.css', '/static/css/shell.css']} />
      <AppShell
        khu="Soạn giáo trình"
        dieuKhien="react"
        spa={false}
        vai={vai}
        ten={me.data.name ?? undefined}
        muc={[
          { trang: null, nhan: 'Giáo trình', icon: 'book-open', emoji: '', url: '/admin' },
          ...(vai === VAI_QUAN_TRI
            ? [{ trang: null, nhan: 'Khu vận hành', icon: 'shield', emoji: '', url: '/quan-tri/tong-quan' }]
            : []),
        ]}
      />
      <SoanClient
        initial={kq.ok ? kq.data.courses : []}
        // Danh sách đề hỏng thì khối giáo trình vẫn phải dùng được: hai thứ độc
        // lập nhau, và cho một lỗi phụ đánh sập cả trang là đổi một khối hỏng
        // thành một trang hỏng.
        deThi={de.ok ? de.data.exams : []}
        laQuanTri={vai === 'admin'}
        loi={kq.ok ? null : kq.message}
      />
    </div>
  );
}
