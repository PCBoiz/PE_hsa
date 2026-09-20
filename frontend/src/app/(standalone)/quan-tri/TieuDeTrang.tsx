'use client';

import { usePathname } from 'next/navigation';

import { TABS } from './vai';

/**
 * h1 của từng trang khu Vận hành — CHỈ cho trình đọc màn hình.
 *
 * axe-core 20/09/2026 (`page-has-heading-one`): cả 8 trang của khu không có h1.
 * Người nhìn biết mình ở đâu nhờ tab đang sáng trên thanh; người dùng trình
 * đọc màn hình đi bằng tiêu đề, và không có h1 là không có điểm neo. Lấy nhãn
 * từ chính `TABS` để tên trang chỉ có một nguồn.
 */
export default function TieuDeTrang() {
  const duong = usePathname();
  const tab = TABS.find((t) => duong === t.href || duong.startsWith(t.href + '/'));
  return <h1 className="sr-only">{tab ? tab.label : 'Vận hành trung tâm'}</h1>;
}
