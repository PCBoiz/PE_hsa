import AppShell from '@/components/AppShell';
import PageStyles from '@/components/PageStyles';
import { VAI_GIANG_VIEN, VAI_HOC_VU, VAI_QUAN_TRI, VAI_TRO_GIANG } from '@/lib/vaiTro';

import KhungGiangDay from '../giang-day/KhungGiangDay';
import { layVai } from '../quan-tri/layVai';
import { mucCho } from '../quan-tri/vai';

/**
 * Khung của HỘP YÊU CẦU (E3) — một đường `/yeu-cau` cho mọi vai, khung theo KHU của vai ấy:
 *
 *   học viên            → thanh học viên (mục "Hỏi & yêu cầu")
 *   giảng viên, trợ giảng → khung Giảng dạy (tab "Yêu cầu" cạnh Việc hôm nay, Lịch học)
 *   học vụ, quản trị    → khung Vận hành (tab "Yêu cầu")
 *
 * Một đường chung vì thông báo (chuông) chỉ mang được MỘT địa chỉ cho mọi người nhận:
 * `/yeu-cau/<id>` mở đúng màn của vai người bấm. Cổng quyền KHÔNG ở đây — máy chủ lọc
 * phạm vi từng yêu cầu (`yeu_cau/dich_vu.py::pham_vi_yeu_cau`), trang tự dựng màn chặn.
 */
export const dynamic = 'force-dynamic';

const GIANG_DAY = [VAI_GIANG_VIEN, VAI_TRO_GIANG];
const VAN_HANH = [VAI_QUAN_TRI, VAI_HOC_VU];

export default async function YeuCauLayout({ children }: { children: React.ReactNode }) {
  const kq = await layVai();
  const vai = kq.ok ? kq.vai : undefined;
  const ten = kq.ok ? kq.ten : undefined;
  return (
    <div className="min-h-dvh bg-ground">
      <PageStyles hrefs={['/static/css/theme.css', '/static/css/shell.css']} />
      {vai && GIANG_DAY.includes(vai) ? (
        <KhungGiangDay troGiang={vai === VAI_TRO_GIANG} ten={ten} vai={vai} />
      ) : vai && VAN_HANH.includes(vai) ? (
        <AppShell khu="Vận hành trung tâm" muc={mucCho(vai)} dieuKhien="react" spa={false} vai={vai} ten={ten} />
      ) : (
        <AppShell trang="/yeu-cau" spa={false} dieuKhien="react" vai={vai} ten={ten} />
      )}
      {/* Bù chiều cao thanh cố định bằng chính token của thanh (như khu Giảng dạy). */}
      <div className="pt-[var(--topbar-h)]">{children}</div>
    </div>
  );
}
