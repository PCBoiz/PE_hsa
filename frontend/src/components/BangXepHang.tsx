import { z } from 'zod';

import BangXepHangClient, { type BangDuLieu } from '@/components/BangXepHangClient';
import type { HinhDang } from '@/lib/kiemDang';
import { serverJson } from '@/lib/server-api';

/**
 * BẢNG XẾP HẠNG — tab "Tuần" dựng Ở MÁY CHỦ; hai tab còn lại tải khi bấm.
 *
 * Khối thứ tư theo khuôn `HocTiep`/`LopCuaToiNguon`/`NhiemVu` (14/09/2026).
 * Trước đó `dashboard.js::loadLeaderboard` gọi `/api/leaderboard` 200 ms SAU
 * `DOMContentLoaded` rồi đổ chuỗi HTML — khối đứng "Đang tải…" suốt lúc chờ.
 *
 * Cùng ngày đã vá backend: bảng chỉ xếp HỌC VIÊN (trước đó quản trị viên đứng
 * hạng 1), nhân viên xem thì `me` là null. Hình dạng dưới đây vì thế cho `me`
 * được null.
 */
const DONG = z.looseObject({
  rank: z.number(),
  id: z.number(),
  name: z.string(),
  avatar: z.string(),
  value: z.number(),
});
export const HD_BANG = z.looseObject({
  type: z.string(),
  unit: z.string(),
  label: z.string(),
  entries: z.array(DONG.extend({ medal: z.string().optional() })),
  me: DONG.nullable(),
}) satisfies HinhDang<BangDuLieu>;

export default async function BangXepHang() {
  const kq = await serverJson('/api/leaderboard?type=weekly', { requireAuth: true }, HD_BANG);
  return <BangXepHangClient banDau={kq.ok ? kq.data : null} />;
}
