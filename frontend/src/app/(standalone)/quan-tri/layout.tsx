import { ThemeToggle } from '@/components/ui';
import Link from 'next/link';

import AdminNav from './AdminNav';
import { KhongDocDuoc, KhongDuQuyen } from './ChanVai';
import { layVai } from './layVai';
import { VAI_VAO_KHU, duocVao, tabsCho } from './vai';

/**
 * Khu VẬN HÀNH của trung tâm — tài khoản, lớp, đợt học, nhật ký.
 *
 * Tách khỏi trang /admin cũ là có chủ đích. Trang đó quản lý NỘI DUNG (khoá,
 * bài, nhập giáo trình) — việc làm vài lần rồi thôi. Khu này quản lý CON NGƯỜI
 * — việc làm mỗi ngày, mỗi khi có học viên mới đăng ký học. Trộn hai thứ vào
 * một trang dài 700 dòng thì việc hằng ngày bị chôn dưới việc hằng quý.
 *
 * CỔNG Ở ĐÂY CHỈ CHẶN "VÀO KHU", KHÔNG CHẶN TỪNG TRANG. Năm trang trong khu
 * không cùng một mức quyền — `lop-hoc` và `dot-hoc` mở cho `Quản lý học vụ`,
 * ba trang còn lại thì không — nên mỗi trang có `layout.tsx` riêng của nó làm
 * cổng của mình. Bảng vai duy nhất nằm ở `./vai.ts`.
 *
 * Trước 04/09/2026 cổng này là `role !== 'admin'`, tức nó chặn `Quản lý học vụ`
 * khỏi ĐÚNG hai trang mà backend vừa mở cho họ.
 */
export const dynamic = 'force-dynamic';

export default async function QuanTriLayout({ children }: { children: React.ReactNode }) {
  // Chặn ngay trên máy chủ. Không có câu này thì người không đủ quyền vẫn tải
  // được cả khung trang rồi mới nhận 403 từ API — nhìn như hệ thống hỏng chứ
  // không như "bạn không có quyền".
  const kq = await layVai();
  if (!kq.ok) return <KhongDocDuoc loi={kq.loi} />;
  if (!duocVao(kq.vai, VAI_VAO_KHU)) return <KhongDuQuyen />;

  return (
    <div className="min-h-dvh bg-ground">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-4">
          <Link href="/dashboard" className="-my-3 py-3 text-small text-ink-3 hover:text-brand-ink">
            ← Trang của tôi
          </Link>
          <h1 className="text-section text-ink">Vận hành trung tâm</h1>
          {/* Nút đổi sáng/tối: khu này KHÔNG nạp main.js nên nút của Topbar
              legacy không có ở đây — trước 01/09/2026 giảng viên phải quay về
              dashboard mới bật/tắt được bản tối. `ml-auto` đẩy nó về cuối hàng
              để không chen vào giữa tiêu đề và các tab. */}
          <ThemeToggle className="ml-auto" />
          {/* Chỉ hiện tab người này VÀO ĐƯỢC. Hiện đủ tab rồi chặn ở trang đích
              là mời người ta bấm vào một bức tường — và họ sẽ báo là hệ thống
              lỗi, không phải là họ thiếu quyền. */}
          <AdminNav tabs={tabsCho(kq.vai)} />
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
