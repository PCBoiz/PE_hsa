import AppShell from '@/components/AppShell';
import PageStyles from '@/components/PageStyles';

import { KhongDocDuoc, KhongDuQuyen } from './ChanVai';
import { layVai } from './layVai';
import { VAI_VAO_KHU, duocVao, mucCho } from './vai';

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
      {/* `theme.css` phải đứng TRƯỚC `shell.css`: shell đọc `var(--t1)`,
          `var(--accent)`… và theme là nơi khai chúng. Cùng tổ hợp mà
          `MockExam.tsx` dùng — khu nào nạp thanh thì nạp đúng hai tệp này. */}
      <PageStyles hrefs={['/static/css/theme.css', '/static/css/shell.css']} />
      {/* CÙNG một thanh với mọi màn khác, chỉ đổi hàng mục.
          Trước 07/09/2026 khu này tự dựng header Tailwind riêng — bản dựng
          THỨ TƯ, sót lại sau đợt gộp ba bản hôm 06/09. Hậu quả đo được: trong
          cả khu Vận hành **không có đường Đăng xuất** và không chỗ nào cho
          biết đang đăng nhập bằng ai (`.topbar` = 0, `.user-dropdown-item`
          = 0). Giảng viên muốn thoát phải quay về `/dashboard` trước.

          `dieuKhien='react'` vì khu này KHÔNG nạp `dashboard.js`, nên không có
          bộ xử lý menu nào của tầng cũ để nhường. `spa={false}` vì không có
          `main.js::navigate()`. Hai trục ấy độc lập — xem chú thích đầu
          `AppShell.tsx`.

          Danh sách mục ĐÃ LỌC THEO VAI ngay ở đây, trên máy chủ: hiện đủ tab
          rồi chặn ở trang đích là mời người ta bấm vào một bức tường, và họ sẽ
          báo là hệ thống lỗi chứ không phải là họ thiếu quyền. */}
      <AppShell
        khu="Vận hành trung tâm"
        muc={mucCho(kq.vai)}
        dieuKhien="react"
        spa={false}
        vai={kq.vai}
        ten={kq.ten}
      />
      {/* `pt-[var(--topbar-h)]` — thanh chung là `position: fixed`, nên KHÔNG
          chừa chỗ thì tiêu đề trang nằm dưới nó (đo 07/09/2026: chữ "Toàn
          trung tâm" bị cắt ngang). Cùng cách `mock.css` bù, và dùng chính
          token chiều cao của thanh chứ không phải một con số chép lại — chép
          lại là hai chỗ sẽ trôi khỏi nhau khi thanh đổi cỡ. */}
      <main className="mx-auto max-w-6xl px-4 pb-6 pt-[calc(var(--topbar-h)+1.5rem)]">
        {children}
      </main>
    </div>
  );
}
