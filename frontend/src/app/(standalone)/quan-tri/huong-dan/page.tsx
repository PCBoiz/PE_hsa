import BangHuongDan from '@/components/BangHuongDan';
import { Card, CardHead } from '@/components/ui';

import { layVai } from '../layVai';

/**
 * HƯỚNG DẪN VẬN HÀNH — trong ứng dụng, in ra được.
 *
 * Anh Sơn chốt 07/09/2026: tài liệu đặt ở đây chứ không ở một tệp `.md` trong
 * repo. Người đọc là học vụ và giảng viên; họ không mở GitHub, và họ đọc lúc
 * đang cần làm một việc cụ thể.
 *
 * Nội dung ở `lib/huongDan.ts`. Trang này chỉ dựng — tách ra để
 * `e2e/unit/huong-dan.test.mjs` đọc được dữ liệu mà không phải phân tích JSX.
 *
 * ── PHẦN "HỎNG THÌ SAO" KHÔNG PHẢI PHẦN PHỤ ─────────────────────────────
 *
 * Người mới không mắc ở bước "bấm nút nào". Họ mắc ở lúc màn hình hiện một thứ
 * không giống mong đợi — sáu dấu "—", một câu đỏ, một con số 0% — và không
 * biết đó là lỗi hay là bình thường. Nên mỗi bài có mục ấy, và nó được in ra
 * cùng cỡ chữ với các bước, không bị thu nhỏ thành ghi chú.
 */
export const dynamic = 'force-dynamic';
export const metadata = { title: 'Hướng dẫn vận hành | TopHSA' };

export default async function HuongDanPage() {
  const kq = await layVai();
  return (
    <div className="flex flex-col gap-5">
      {/* KHÔNG lọc ở khu Vận hành: người đọc ở đây là quản trị viên và học vụ,
          và việc của họ là biết TOÀN BỘ quy trình — kể cả phần họ không tự làm
          — để trả lời được khi giảng viên hỏi. Bản lọc theo vai nằm ở
          `/huong-dan`, khu mà mọi vai đều vào được. */}
      <BangHuongDan vai={kq.ok ? kq.vai : undefined} />

      <Card>
        <CardHead title="Bàn giao công nghệ" />
        <p className="text-body text-ink-2">
          Trang này dành cho người <strong>vận hành</strong>. Người tiếp nhận
          <strong> công nghệ</strong> (kiến trúc, triển khai, cách sửa) cần thứ
          khác hẳn — nằm trong repo:
        </p>
        <ul className="mt-2 flex list-disc flex-col gap-1 pl-5 text-body text-ink-2">
          <li><code className="font-mono">docs/KIEN_TRUC/</code> — kiến trúc từng khối</li>
          <li><code className="font-mono">docs/VIEC_CUA_ANH.md</code> — việc cần tài khoản bên ngoài (Zalo OA, Render, Neon)</li>
          <li><code className="font-mono">RULES.md</code> — luật đã trả giá mới rút ra được</li>
          <li><code className="font-mono">PROGRESS.md</code> — nhật ký từng thay đổi và lý do</li>
        </ul>
      </Card>
    </div>
  );
}
