import { KhongDocDuoc, KhongDuQuyen } from '../ChanVai';
import { layVai } from '../layVai';
import { VAI_HOC_VU, VAI_QUAN_TRI, duocVao } from '../vai';

/**
 * Cổng riêng của trang "tài khoản" và trang hồ sơ bên dưới nó.
 *
 * Mở cho quản trị viên và — từ 23/09/2026 — cho `Quản lý học vụ` (anh Sơn chốt:
 * học vụ tạo tài khoản và sửa hồ sơ HỌC VIÊN). Chốt thật nằm ở máy chủ:
 * `AdminUsersView` chỉ trả tài khoản vai Học viên cho học vụ; đổi vai trò và
 * khoá tài khoản vẫn `IsAdminRole`.
 *
 * Vẫn giữ cổng riêng thay vì dựa vào cổng khu: khu mở cho thêm vai nào thì trang
 * này KHÔNG tự mở theo. Nới cổng khu mà không dựng cổng trang là nới QUYỀN —
 * người dùng sẽ thấy một trang tải xong rồi mọi ô báo lỗi, thứ trông y hệt hệ
 * thống hỏng.
 */
export default async function Cong({ children }: { children: React.ReactNode }) {
  const kq = await layVai();
  if (!kq.ok) return <KhongDocDuoc loi={kq.loi} />;
  if (!duocVao(kq.vai, [VAI_QUAN_TRI, VAI_HOC_VU])) {
    return <KhongDuQuyen can="quản trị viên hoặc quản lý học vụ" />;
  }
  return <>{children}</>;
}
