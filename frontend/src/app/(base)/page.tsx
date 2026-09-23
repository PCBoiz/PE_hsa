import { redirect } from 'next/navigation';

import { trangDau } from '@/lib/khuTheoVai';

import { layVai } from '../(standalone)/quan-tri/layVai';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'TopHSA' };

/**
 * TRANG GỐC = CỔNG VÀO (24/09/2026, anh Sơn chốt theo góp ý TopHSA).
 *
 * Trước hôm nay `/` là trang quảng cáo ~7.000 ký tự chép từ sản phẩm lập trình cũ
 * ("Miễn phí", "Chứng chỉ hoàn thành", tông neon, ba khối thi thử). Hệ thống bán
 * cho MỘT trung tâm: người mở `/` là học viên, giáo viên, học vụ của TopHSA —
 * không phải khách vãng lai cần thuyết phục; quảng bá nằm ở website riêng của
 * trung tâm. Nên `/` chỉ làm một việc: đưa người đã đăng nhập về khu của vai
 * mình (`TRANG_DAU`), người chưa đăng nhập tới màn đăng nhập.
 *
 * `layVai` gọi `/api/user` với `requireAuth` — chưa đăng nhập thì chính nó đưa
 * về `/login`. Máy chủ không trả lời được thì cũng về `/login`: màn ấy tự đánh
 * thức máy chủ và nói đang chờ gì.
 */
export default async function TrangGoc() {
  const vai = await layVai();
  redirect(vai.ok ? trangDau(vai.vai) : '/login');
}
