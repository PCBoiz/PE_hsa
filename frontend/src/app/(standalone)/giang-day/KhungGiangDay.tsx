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
 * Không có `classId` trong đường dẫn (không xảy ra hôm nay, nhưng sẽ xảy ra
 * khi thêm một trang cấp khu) thì thanh chỉ còn thương hiệu và danh tính —
 * không dựng ba tab trỏ vào `/giang-day/buoi-hoc/undefined`.
 */
const TAB = [
  { doan: 'buoi-hoc', nhan: 'Buổi học', icon: 'calendar' },
  { doan: 'bai-tap', nhan: 'Bài tập', icon: 'pencil' },
  { doan: 'bao-cao', nhan: 'Báo cáo phụ huynh', icon: 'file-text' },
] as const;

export default function KhungGiangDay() {
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
      muc={lop
        ? TAB.map((t) => ({
          trang: null,
          nhan: t.nhan,
          icon: t.icon,
          emoji: '',
          url: `/giang-day/${t.doan}/${lop}`,
        }))
        : []}
    />
  );
}
