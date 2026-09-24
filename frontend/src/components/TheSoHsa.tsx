import TheSoHsaClient from '@/components/TheSoHsaClient';
import { layTomTat } from '@/lib/duLieuHsa';

/**
 * Hàng thẻ số (ba thẻ từ 24/09/2026, bỏ thi pha A) — lấy `/api/hsa/summary` Ở MÁY CHỦ (dùng chung lượt gọi với
 * "Học tiếp" và dải tiến độ qua `cache()`), đưa xuống phần client.
 *
 * Hỏng thì phần client hiện "—" ở mọi ô — đúng trạng thái trước khi có dữ liệu
 * của bản cũ, không bịa số 0.
 */
export default async function TheSoHsa() {
  const kq = await layTomTat();
  return <TheSoHsaClient banDau={kq.ok ? kq.data : null} />;
}
