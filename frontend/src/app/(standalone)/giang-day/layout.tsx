import PageStyles from '@/components/PageStyles';
import { VAI_TRO_GIANG } from '@/lib/vaiTro';

import { layVai } from '../quan-tri/layVai';
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
 * Đọc VAI ở đây thì có (14/09/2026) — KHÔNG để chặn, mà để khung đừng dựng tab
 * "Báo cáo phụ huynh" cho trợ giảng: rà luồng trên trình duyệt thật thấy tab ấy
 * hiện ra và dẫn tới "Không có quyền truy cập". `layVai` gói `cache()` nên cả
 * khu tốn thêm đúng một lượt `/api/user` mỗi lần dựng trang.
 *
 * `theme.css` phải đứng TRƯỚC `shell.css`: shell đọc `var(--t1)`, `var(--accent)`…
 * và theme là nơi khai chúng.
 */
export default async function GiangDayLayout({ children }: { children: React.ReactNode }) {
  const vai = await layVai();
  const troGiang = vai.ok && vai.vai === VAI_TRO_GIANG;
  return (
    <div className="min-h-dvh bg-ground">
      <PageStyles hrefs={['/static/css/theme.css', '/static/css/shell.css']} />
      <KhungGiangDay troGiang={troGiang} ten={vai.ok ? vai.ten : undefined} vai={vai.ok ? vai.vai : undefined} />
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
