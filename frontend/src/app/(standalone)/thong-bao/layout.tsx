import AppShell from '@/components/AppShell';
import PageStyles from '@/components/PageStyles';
import { VAI_GIANG_VIEN, VAI_HOC_VU, VAI_QUAN_TRI, VAI_TRO_GIANG } from '@/lib/vaiTro';

import KhungGiangDay from '../giang-day/KhungGiangDay';
import { layVai } from '../quan-tri/layVai';
import { mucCho } from '../quan-tri/vai';

/**
 * Khung của trang THÔNG BÁO (§61) — cùng lối với `/yeu-cau` của E3, và vì cùng một lý do:
 * chuông chỉ mang được MỘT địa chỉ cho mọi người nhận, nên `/thong-bao` phải mở được ở mọi
 * vai và tự mặc khung của khu người ấy đang đứng.
 *
 *   học viên              → thanh học viên
 *   giảng viên, trợ giảng → khung Giảng dạy
 *   học vụ, quản trị      → khung Vận hành
 *
 * Không có cổng quyền ở đây: máy chủ chỉ trả dòng của chính người đăng nhập
 * (`WHERE user_id = request.user.id`), nên không có gì để lọc thêm ở màn.
 */
export const dynamic = 'force-dynamic';

const GIANG_DAY = [VAI_GIANG_VIEN, VAI_TRO_GIANG];
const VAN_HANH = [VAI_QUAN_TRI, VAI_HOC_VU];

export default async function ThongBaoLayout({ children }: { children: React.ReactNode }) {
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
        <AppShell trang="/thong-bao" spa={false} dieuKhien="react" vai={vai} ten={ten} />
      )}
      {/* Bù chiều cao thanh cố định bằng chính token của thanh (như khu Giảng dạy). */}
      <div className="pt-[var(--topbar-h)]">{children}</div>
    </div>
  );
}
