import { KhongDocDuoc, KhongDuQuyen } from '../ChanVai';
import { layVai } from '../layVai';
import { VAI_HOC_VU, VAI_QUAN_TRI, duocVao } from '../vai';

/**
 * Cổng riêng của trang "Chấm công" — `IsAdminOrAcademic`, khớp `teaching/cham_cong.py`.
 * Học vụ vào được: bảng khách (dòng 6.3) đòi báo cáo chấm công giảng viên và trợ giảng,
 * và người đối chiếu buổi dạy hằng tháng là học vụ.
 */
export default async function Cong({ children }: { children: React.ReactNode }) {
  const kq = await layVai();
  if (!kq.ok) return <KhongDocDuoc loi={kq.loi} />;
  if (!duocVao(kq.vai, [VAI_QUAN_TRI, VAI_HOC_VU])) {
    return <KhongDuQuyen can="quản trị viên hoặc quản lý học vụ" />;
  }
  return <>{children}</>;
}
