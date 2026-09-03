import Link from 'next/link';

import { serverJson } from '@/lib/server-api';

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

const DUOC_VAO = new Set(['admin', 'Biên tập nội dung']);

export default async function SoanGiaoTrinhPage() {
  const me = await serverJson<{ role?: string }>('/api/user', { requireAuth: true });

  // "Không đọc được tài khoản" KHÁC "không đủ quyền": backend ngủ dậy hay mạng
  // hỏng cũng rơi vào đây, và nói "bạn không có quyền" lúc đó là đẩy người dùng
  // đi hỏi nhầm chỗ. Cùng luật với khu `/quan-tri`.
  if (!me.ok) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="text-title text-ink">Chưa mở được khu soạn giáo trình</h1>
        <p className="mt-2 text-body text-ink-2">{me.message}</p>
        <Link href="/dashboard" className="mt-6 inline-block text-body text-brand-ink underline">
          ← Về trang của tôi
        </Link>
      </main>
    );
  }

  const vai = me.data.role || '';
  if (!DUOC_VAO.has(vai)) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="text-title text-ink">Khu này dành cho người soạn giáo trình</h1>
        <p className="mt-2 text-body text-ink-2">
          Tài khoản của bạn đang ở vai <b>{vai || 'chưa đặt'}</b>. Cần vai{' '}
          <b>Biên tập nội dung</b> hoặc <b>quản trị viên</b> để vào đây — nhờ quản trị viên
          đổi giúp nếu bạn phụ trách nội dung.
        </p>
        <Link href="/dashboard" className="mt-6 inline-block text-body text-brand-ink underline">
          ← Về trang của tôi
        </Link>
      </main>
    );
  }

  const kq = await serverJson<{ courses: KhoaRow[] }>('/api/admin/courses', { requireAuth: true });

  return (
    <SoanClient
      initial={kq.ok ? kq.data.courses : []}
      laQuanTri={vai === 'admin'}
      loi={kq.ok ? null : kq.message}
    />
  );
}
