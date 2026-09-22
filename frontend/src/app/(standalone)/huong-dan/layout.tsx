import AppShell from '@/components/AppShell';
import PageStyles from '@/components/PageStyles';

import { KhongDocDuoc } from '../quan-tri/ChanVai';
import { layVai } from '../quan-tri/layVai';

/**
 * KHU TÀI LIỆU — hướng dẫn cho MỌI vai, nằm NGOÀI khu Vận hành.
 *
 * ── VÌ SAO CÓ KHU NÀY (22/09/2026) ────────────────────────────────────────
 *
 * Hướng dẫn trước nay chỉ có ở `/quan-tri/huong-dan`, mà cổng khu ấy chỉ cho
 * quản trị viên và quản lý học vụ. Nghĩa là các bài viết CHO giảng viên, trợ
 * giảng và biên tập nội dung vẫn nằm đó — đúng người cần thì không mở được.
 * Chính `quan-tri/huong-dan/layout.tsx` đã ghi nhận khoảng trống ấy và chỉ ra
 * cách sửa: "một khu tài liệu riêng ngoài khu Vận hành, không phải nới cổng
 * khu". Đây là khu ấy.
 *
 * ── KHÔNG CÓ CỔNG VAI, VÀ ĐÓ LÀ CHỦ Ý ────────────────────────────────────
 *
 * Khu này chỉ đòi ĐĂNG NHẬP. Không chặn theo vai, vì nội dung là tài liệu —
 * không có dữ liệu của một học viên nào trong đó, và một trợ giảng đọc được
 * phần việc của giảng viên là chuyện nên khuyến khích chứ không nên chặn.
 *
 * Ranh giới thật vẫn nằm nguyên ở cổng của từng màn hình: đọc được hướng dẫn
 * "gửi báo cáo phụ huynh" KHÔNG làm trợ giảng mở được màn hình ấy — họ bấm
 * vào là gặp "Không có quyền truy cập", đúng như trước.
 *
 * `layVai` vẫn gọi vì trang cần biết vai để LỌC, và vì thanh chung cần tên
 * người đang đăng nhập. Không đọc được vai thì hiện lý do thật thay vì đoán.
 */
export const dynamic = 'force-dynamic';

export default async function HuongDanLayout({ children }: { children: React.ReactNode }) {
  const kq = await layVai();
  if (!kq.ok) return <KhongDocDuoc loi={kq.loi} />;

  return (
    <div className="min-h-dvh bg-ground">
      {/* `theme.css` TRƯỚC `shell.css`: shell đọc `var(--t1)`, `var(--accent)`…
          mà theme là nơi khai chúng. Cùng tổ hợp khu Vận hành dùng. */}
      <PageStyles hrefs={['/static/css/theme.css', '/static/css/shell.css']} />
      {/* `muc={[]}`: khu này không có tab con — một trang duy nhất. Thanh vẫn
          dựng để người đọc có đường đăng xuất và biết mình đang là ai; thiếu
          nó thì đây là ngõ cụt phải bấm Back mới ra được. */}
      <AppShell khu="Hướng dẫn" muc={[]} dieuKhien="react" spa={false} vai={kq.vai} ten={kq.ten} />
      <main className="mx-auto max-w-6xl px-4 pb-6 pt-[calc(var(--topbar-h)+1.5rem)]">
        {children}
      </main>
    </div>
  );
}
