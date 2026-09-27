import { KhongDocDuoc, KhongDuQuyen } from '../ChanVai';
import { layVai } from '../layVai';
import { VAI_HOC_VU, VAI_QUAN_TRI, duocVao } from '../vai';

/**
 * Cổng riêng của trang "Kết quả theo môn" — `IsAdminOrAcademic`, khớp
 * `teaching/bao_cao_cheo.py::BaoCaoCheoView`.
 *
 * Học vụ vào được: quyết định 01/09/2026 ghi học vụ "xem MỌI lớp, báo cáo trung tâm", và
 * đây là một báo cáo trung tâm (số gộp theo môn và lớp, không có liên lạc của em nào).
 * Giảng viên và trợ giảng KHÔNG: bảng này đặt mọi lớp của mọi người cạnh nhau.
 */
export default async function Cong({ children }: { children: React.ReactNode }) {
  const kq = await layVai();
  if (!kq.ok) return <KhongDocDuoc loi={kq.loi} />;
  if (!duocVao(kq.vai, [VAI_QUAN_TRI, VAI_HOC_VU])) {
    return <KhongDuQuyen can="quản trị viên hoặc quản lý học vụ" />;
  }
  return <>{children}</>;
}
