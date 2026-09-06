import { KhongDocDuoc, KhongDuQuyen } from '../ChanVai';
import { layVai } from '../layVai';
import { VAI_HOC_VU, VAI_QUAN_TRI, duocVao } from '../vai';

/**
 * Cổng riêng của trang "Hướng dẫn".
 *
 * Nội dung là tài liệu, không phải dữ liệu — nhưng nó mô tả chi tiết cách vận
 * hành trung tâm, và quy ước của khu là MỌI trang có cổng riêng
 * (`cong-quan-tri.test.mjs`). Một ngoại lệ "trang này không cần" là chỗ ngoại
 * lệ thứ hai bám vào.
 *
 * Giảng viên và trợ giảng KHÔNG vào được khu này, nên họ chưa đọc được hướng
 * dẫn phần dạy học. Đó là một khoảng trống có thật, ghi ở PROGRESS — cách sửa
 * đúng là một khu tài liệu riêng ngoài khu Vận hành, không phải nới cổng khu.
 */
export default async function Cong({ children }: { children: React.ReactNode }) {
  const kq = await layVai();
  if (!kq.ok) return <KhongDocDuoc loi={kq.loi} />;
  if (!duocVao(kq.vai, [VAI_QUAN_TRI, VAI_HOC_VU])) {
    return <KhongDuQuyen can="quản trị viên và quản lý học vụ" />;
  }
  return <>{children}</>;
}
