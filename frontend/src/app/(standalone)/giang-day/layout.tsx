import PageStyles from '@/components/PageStyles';

import KhungGiangDay from './KhungGiangDay';

/**
 * Khu GIẢNG DẠY — khung chung, giống mọi màn khác.
 *
 * Cổng quyền KHÔNG đặt ở đây, có chủ ý: năm trang của khu đều gắn với MỘT LỚP
 * cụ thể, và câu hỏi thật là "người này có phụ trách lớp ĐÓ không"
 * (`can_see_class`), chứ không phải "người này có vai giảng viên không". Một
 * cổng theo vai ở đây sẽ cho giảng viên A mở được lớp của giảng viên B — hàng
 * rào thật nằm ở `permission_classes` của từng API, và từng trang tự xử lý
 * phản hồi 404 của nó.
 *
 * `theme.css` phải đứng TRƯỚC `shell.css`: shell đọc `var(--t1)`, `var(--accent)`…
 * và theme là nơi khai chúng.
 */
export default function GiangDayLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh bg-ground">
      <PageStyles hrefs={['/static/css/theme.css', '/static/css/shell.css']} />
      <KhungGiangDay />
      {/* Bù chiều cao thanh: `.topbar` là `position: fixed`. Dùng chính token
          của thanh chứ không một con số chép lại — chép lại là hai chỗ sẽ trôi
          khỏi nhau khi thanh đổi cỡ.

          `print:pt-0`: tờ báo cáo gửi phụ huynh in ra giấy, và thanh đã
          `display:none` khi in (xem `shell.css`), nên chừa chỗ cho nó là chừa
          một dải trắng ở đầu trang giấy. */}
      <div className="pt-[var(--topbar-h)] print:pt-0">{children}</div>
    </div>
  );
}
