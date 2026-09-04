import { KhongDocDuoc, KhongDuQuyen } from '../ChanVai';
import { layVai } from '../layVai';
import { VAI_QUAN_TRI, duocVao } from '../vai';

/**
 * Cổng riêng của trang "nhật ký kiểm toán".
 *
 * Layout của cả khu chỉ chặn "vào khu", và từ 04/09/2026 nó cho `Quản lý học vụ`
 * vào — vì hai trang khác trong khu (Lớp học, Đợt học) là việc hằng ngày của họ.
 * Trang này thì KHÔNG: API nó gọi dùng IsAdminRole (teaching/admin_users.py::AdminAuditView).
 *
 * Nới cổng khu mà không dựng cổng trang là nới QUYỀN, không phải sửa lỗi. Backend
 * vẫn trả 403 nên dữ liệu không rò, nhưng người dùng sẽ thấy một trang tải xong
 * rồi mọi ô báo lỗi — thứ trông y hệt hệ thống hỏng, và là đúng cái mà cổng
 * phía trên sinh ra để tránh.
 */
export default async function Cong({ children }: { children: React.ReactNode }) {
  const kq = await layVai();
  if (!kq.ok) return <KhongDocDuoc loi={kq.loi} />;
  if (!duocVao(kq.vai, [VAI_QUAN_TRI])) return <KhongDuQuyen can="quản trị viên" />;
  return <>{children}</>;
}
