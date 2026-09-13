import { KhongDocDuoc, KhongDuQuyen } from '../ChanVai';
import { layVai } from '../layVai';
import { VAI_HOC_VU, VAI_QUAN_TRI, duocVao } from '../vai';

/**
 * Cổng riêng của trang "bảng điều khiển toàn trung tâm".
 *
 * Layout của cả khu chỉ chặn "vào khu". Cổng trang này phải KHỚP `permission_classes`
 * của API nó gọi (`teaching/overview.py::AdminOverviewView`) — nới cổng khu mà
 * không dựng cổng trang là để người dùng thấy một trang tải xong rồi mọi ô báo
 * lỗi, thứ trông y hệt hệ thống hỏng.
 *
 * Từ 14/09/2026 API ấy là `IsAdminOrAcademic` (quyết định 01/09: học vụ xem "báo
 * cáo trung tâm"), nên cổng này mở cho học vụ. Rà luồng học vụ hôm ấy thấy tab
 * đã hiện mà trang vẫn "Không đủ quyền" — ba cổng (tab, trang, API) cho một
 * màn thì sửa một cổng là hai cổng kia nói dối. `cong-quan-tri.test.mjs` canh
 * tab với API; cổng trang canh bằng phép đo trên trình duyệt thật.
 */
export default async function Cong({ children }: { children: React.ReactNode }) {
  const kq = await layVai();
  if (!kq.ok) return <KhongDocDuoc loi={kq.loi} />;
  if (!duocVao(kq.vai, [VAI_QUAN_TRI, VAI_HOC_VU])) {
    return <KhongDuQuyen can="quản trị viên hoặc quản lý học vụ" />;
  }
  return <>{children}</>;
}
