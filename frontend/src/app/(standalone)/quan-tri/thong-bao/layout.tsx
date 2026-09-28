import { KhongDocDuoc, KhongDuQuyen } from '../ChanVai';
import { layVai } from '../layVai';
import { VAI_HOC_VU, VAI_QUAN_TRI, duocVao } from '../vai';

/**
 * Cổng riêng của trang "Thông báo trung tâm".
 *
 * API của nó (`notifications/views_thong_bao.py::AdminThongBaoView` và ba cửa cùng cụm)
 * dùng `IsAdminOrAcademic`, và gửi thông báo cho cả khối là việc hằng ngày của học vụ.
 *
 * Vẫn phải có cổng riêng dù nó không siết hơn cổng khu: cổng khu chỉ hỏi "vai này vào được
 * ÍT NHẤT MỘT trang trong khu", nên nó không trả lời được câu hỏi của từng trang. Thêm một
 * vai vào `VAI_VAO_KHU` cho một trang khác là vai ấy lặng lẽ vào được cả trang này.
 * `e2e/unit/cong-quan-tri.test.mjs` canh cả hai vế.
 */
export default async function Cong({ children }: { children: React.ReactNode }) {
  const kq = await layVai();
  if (!kq.ok) return <KhongDocDuoc loi={kq.loi} />;
  if (!duocVao(kq.vai, [VAI_QUAN_TRI, VAI_HOC_VU])) {
    return <KhongDuQuyen can="quản trị viên và quản lý học vụ" />;
  }
  return <>{children}</>;
}
