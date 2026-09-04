import { KhongDocDuoc, KhongDuQuyen } from '../ChanVai';
import { layVai } from '../layVai';
import { VAI_HOC_VU, VAI_QUAN_TRI, duocVao } from '../vai';

/**
 * Cổng riêng của trang "Đợt học".
 *
 * Trang này MỞ cho `Quản lý học vụ` — API của nó dùng `IsAdminOrAcademic`
 * (`teaching/terms.py`), và mở đợt học là việc hằng ngày của vai ấy.
 *
 * Vẫn phải có cổng riêng dù nó không siết hơn cổng khu: cổng khu chỉ hỏi "vai
 * này vào được ÍT NHẤT MỘT trang trong khu", nên nó KHÔNG trả lời được câu hỏi
 * của từng trang. Hôm nay hai câu trả lời trùng nhau; ngày mai thêm một vai vào
 * `VAI_VAO_KHU` cho một trang khác thì vai ấy lặng lẽ vào được cả trang này.
 *
 * Đây là trang duy nhất trong khu từng thiếu cổng — `e2e/unit/cong-quan-tri.test.mjs`
 * bắt được đúng nó, và nay canh cả năm trang.
 */
export default async function Cong({ children }: { children: React.ReactNode }) {
  const kq = await layVai();
  if (!kq.ok) return <KhongDocDuoc loi={kq.loi} />;
  if (!duocVao(kq.vai, [VAI_QUAN_TRI, VAI_HOC_VU])) {
    return <KhongDuQuyen can="quản trị viên và quản lý học vụ" />;
  }
  return <>{children}</>;
}
