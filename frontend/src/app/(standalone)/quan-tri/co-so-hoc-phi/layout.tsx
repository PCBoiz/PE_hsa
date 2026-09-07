import { KhongDocDuoc, KhongDuQuyen } from '../ChanVai';
import { layVai } from '../layVai';
import { VAI_QUAN_TRI, duocVao } from '../vai';

/**
 * Cổng riêng của trang "Cơ sở tính học phí".
 *
 * `IsAdminRole`, khớp `teaching/co_so_hoc_phi.py`. Trang gộp dữ liệu CẢ TRUNG
 * TÂM — cùng loại với "Toàn trung tâm", vốn đã chốt là chỉ quản trị viên.
 *
 * `Quản lý học vụ` có lẽ mới là người thật sự ngồi làm bảng học phí, nên đây
 * là chỗ nên nới sau. Chưa nới vì vai ấy hiện CHƯA CÓ AI (đo 07/09/2026:
 * 1 quản trị, 1 giảng viên, 4 học viên) — nới bây giờ là nới cho một cột trống,
 * và nới quyền cho dữ liệu tiền bạc thì nên là một quyết định có người gật.
 */
export default async function Cong({ children }: { children: React.ReactNode }) {
  const kq = await layVai();
  if (!kq.ok) return <KhongDocDuoc loi={kq.loi} />;
  if (!duocVao(kq.vai, [VAI_QUAN_TRI])) return <KhongDuQuyen can="quản trị viên" />;
  return <>{children}</>;
}
