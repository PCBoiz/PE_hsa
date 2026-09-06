import { KhongDocDuoc, KhongDuQuyen } from '../ChanVai';
import { layVai } from '../layVai';
import { VAI_HOC_VU, VAI_QUAN_TRI, duocVao } from '../vai';

/**
 * Cổng riêng của trang "Ai làm được gì".
 *
 * Trang này KHÔNG gọi API nào — nó dựng từ một bảng hằng số. Nên về mặt dữ
 * liệu thì không có gì để rò. Vẫn có cổng, vì hai lý do:
 *
 *   · Nó liệt kê ranh giới quyền của cả hệ thống. Đó là bản đồ chỉ đúng chỗ
 *     nào mềm — không phải thứ để mở cho học viên đọc.
 *   · Quy ước của khu là MỌI trang có cổng riêng (`cong-quan-tri.test.mjs`).
 *     Một ngoại lệ "trang này không cần" là chỗ ngoại lệ thứ hai bám vào.
 */
export default async function Cong({ children }: { children: React.ReactNode }) {
  const kq = await layVai();
  if (!kq.ok) return <KhongDocDuoc loi={kq.loi} />;
  if (!duocVao(kq.vai, [VAI_QUAN_TRI, VAI_HOC_VU])) {
    return <KhongDuQuyen can="quản trị viên và quản lý học vụ" />;
  }
  return <>{children}</>;
}
