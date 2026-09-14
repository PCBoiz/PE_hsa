import { z } from 'zod';

import NhiemVuClient, { type NhiemVuMot } from '@/components/NhiemVuClient';
import type { HinhDang } from '@/lib/kiemDang';
import { serverJson } from '@/lib/server-api';

/**
 * NHIỆM VỤ HÔM NAY — lấy dữ liệu Ở MÁY CHỦ, đưa xuống khối client có nút "Nhận".
 *
 * Khối thứ ba chuyển theo khuôn `HocTiep`/`LopCuaToiNguon` (14/09/2026): trước
 * đó `dashboard.js::loadMissions` gọi `/api/missions/today` SAU khi hydrate và
 * vẽ bằng chuỗi HTML. Nay nội dung nằm sẵn trong HTML đầu tiên; tầng cũ bớt
 * một lượt mạng và ~60 dòng (`renderMissions`/`loadMissions`).
 *
 * Hỏng thì hiện "Chưa có nhiệm vụ nào cho hôm nay." — cùng câu tầng cũ dùng
 * khi máy chủ trả rỗng; đây là khối gợi ý, không phải nội dung chính.
 */
export const HD_NHIEM_VU = z.looseObject({
  date: z.string(),
  missions: z.array(z.looseObject({
    code: z.string(),
    title: z.string(),
    description: z.string(),
    xpReward: z.number(),
    progress: z.number(),
    target: z.number(),
    done: z.boolean(),
    claimed: z.boolean(),
  })),
  allDone: z.boolean(),
}) satisfies HinhDang<{ date: string; missions: NhiemVuMot[]; allDone: boolean }>;

export default async function NhiemVu() {
  const kq = await serverJson('/api/missions/today', { requireAuth: true }, HD_NHIEM_VU);
  return <NhiemVuClient banDau={kq.ok ? kq.data.missions : []} />;
}
