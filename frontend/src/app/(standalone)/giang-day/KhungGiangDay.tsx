'use client';

import { usePathname } from 'next/navigation';

import AppShell from '@/components/AppShell';

/**
 * Khung của khu GIẢNG DẠY.
 *
 * ── VÌ SAO CÓ (07/09/2026) ────────────────────────────────────────────────
 *
 * Khu này KHÔNG có `layout.tsx` nào — năm trang, mỗi trang tự dựng phần đầu
 * của mình. Hậu quả đúng bằng hai lỗ đã vá trước đó ở màn Thi thử (06/09) và
 * khu Vận hành (07/09 sáng): giảng viên đang ở trong lớp thì **không có đường
 * Đăng xuất**, và không chỗ nào cho biết đang đăng nhập bằng ai.
 *
 * Đây là lần thứ BA cùng một lỗ. Nó lặp lại vì mỗi khu mới ra đời đều bắt đầu
 * bằng "một trang thôi, chưa cần khung" — nên ghi lại ở đây: khu nào có nhiều
 * hơn một trang thì khu ấy cần khung chung.
 *
 * ── BA TAB LẤY TỪ ĐƯỜNG DẪN, KHÔNG TỪ PROP ───────────────────────────────
 *
 * Cả năm trang của khu đều nhận `classId`, nhưng `layout.tsx` của Next KHÔNG
 * nhận `params` của trang con. Đọc từ `usePathname()` là cách duy nhất để
 * khung biết đang ở lớp nào mà không phải truyền tay qua năm trang.
 *
 * Không có `classId` trong đường dẫn (trang cấp khu `/giang-day` — "Việc hôm
 * nay", thêm 14/09/2026) thì thanh chỉ có tab ấy — không dựng ba tab lớp trỏ
 * vào `/giang-day/buoi-hoc/undefined`.
 */
const TAB = [
  // `clock` chứ không `calendar` (24/09/2026): biểu tượng lịch nay thuộc tab
  // "Lịch học" gộp mọi lớp — hai tab cạnh nhau không được cùng một hình.
  { doan: 'buoi-hoc', nhan: 'Buổi học', icon: 'clock', troGiang: true },
  { doan: 'bai-tap', nhan: 'Bài tập', icon: 'pencil', troGiang: true },
  // Trợ giảng không mở được báo cáo phụ huynh (`IsSeniorTeachingStaff`) — không
  // dựng tab dẫn tới một trang 403. Hàng rào thật vẫn ở máy chủ.
  { doan: 'bao-cao', nhan: 'Báo cáo phụ huynh', icon: 'file-text', troGiang: false },
] as const;

export default function KhungGiangDay({
  troGiang = false, ten, vai,
}: { troGiang?: boolean; ten?: string; vai?: string }) {
  const duong = usePathname();
  // `/giang-day/<doan>/<classId>/…` → phần tử 3 sau khi tách. Chỉ nhận chuỗi
  // toàn chữ số: một đoạn đường dẫn lạ không được biến thành một `classId`.
  const phan = duong.split('/');
  const lop = /^\d+$/.test(phan[3] ?? '') ? phan[3] : null;

  return (
    <AppShell
      khu="Giảng dạy"
      dieuKhien="react"
      spa={false}
      /* Tên + vai lấy từ CÙNG lượt `layVai()` của layout — khu này không nạp
         `dashboard.js` nên không ai điền `#chip-name`; thiếu là chip hiện "?"
         và "—" ở mọi trang của khu (đo 20/09/2026, cả điện thoại lẫn máy tính). */
      ten={ten}
      vai={vai}
      muc={[
        // "Việc hôm nay" đứng đầu và có mặt ở MỌI trang của khu: đó là chỗ
        // giảng viên quay về sau khi làm xong một việc trong lớp.
        { trang: null, nhan: 'Việc hôm nay', icon: 'check-circle-2', emoji: '', url: '/giang-day', chinhXac: true },
        // Lịch gộp mọi lớp (§53) — cấp KHU như "Việc hôm nay", không gắn một lớp,
        // nên có mặt cả khi đang ở trong một lớp. Trợ giảng cũng xem được
        // (`LichView` là `IsTeachingStaff`), phạm vi là lớp được gán.
        { trang: null, nhan: 'Lịch học', icon: 'calendar', emoji: '', url: '/giang-day/lich' },
        // Hộp Yêu cầu (E3, 26/09/2026) — cấp KHU như "Lịch học": câu hỏi của em, việc được giao /
        // chuyển tiếp, báo lên. Máy chủ lọc lớp mình + việc giao cho mình.
        { trang: null, nhan: 'Yêu cầu', icon: 'inbox', emoji: '', url: '/yeu-cau' },
        ...(lop
          ? TAB.filter((t) => !troGiang || t.troGiang).map((t) => ({
            trang: null,
            nhan: t.nhan,
            icon: t.icon,
            emoji: '',
            url: `/giang-day/${t.doan}/${lop}`,
          }))
          : []),
      ]}
    />
  );
}
