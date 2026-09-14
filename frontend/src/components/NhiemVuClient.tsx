'use client';

import { useState } from 'react';
// `zod/mini` chứ KHÔNG `zod` (14/09/2026 tối): đây là mã chạy ở TRÌNH DUYỆT.
// Bản đầy đủ không rung cây được — đo A/B trên Thi thử: 956 kB (zod) → 608 kB
// (zod/mini), byte giải nén, ba lượt mỗi bên. Bản mini cùng luật
// `looseObject`/`safeParse`, viết dạng hàm (`z.optional(z.string())` thay vì
// `.optional()`). Mã máy chủ vẫn dùng `zod` đầy đủ — gói máy chủ không ai tải.
import * as z from 'zod/mini';

import { ghiJson, loiBatDuoc } from '@/lib/api';

/**
 * Khối "Nhiệm vụ hôm nay" — phần chạy ở trình duyệt: danh sách + nút "Nhận".
 *
 * Dữ liệu ban đầu do máy chủ đưa xuống (`NhiemVu.tsx`). Bấm "Nhận" thì gọi
 * `/api/missions/claim` qua `ghiJson` (có hình dạng — phản hồi mang lại CẢ danh
 * sách mới, nên khối vẽ lại từ đó, không tự đoán). Hai việc còn nhờ tầng cũ,
 * qua hai global nó đã công bố:
 *   · `__showAchievement` — thẻ "Mở khoá thành tích" góc màn hình;
 *   · `__refreshHsaTiles` — XP vừa cộng có thể làm xong luôn "kiếm 100 XP",
 *     nên hàng thẻ số phải đọc lại.
 * Không có hai global ấy (trang khác gắn khối này) thì bỏ qua, không lỗi.
 */
export type NhiemVuMot = {
  code: string;
  title: string;
  description: string;
  xpReward: number;
  progress: number;
  target: number;
  done: boolean;
  claimed: boolean;
};

const HD_NHAN = z.looseObject({
  ok: z.boolean(),
  xpGained: z.number(),
  missions: z.array(z.looseObject({
    code: z.string(), title: z.string(), description: z.string(), xpReward: z.number(),
    progress: z.number(), target: z.number(), done: z.boolean(), claimed: z.boolean(),
  })),
  newAchievements: z.array(z.looseObject({ name: z.optional(z.string()), icon: z.optional(z.string()) })),
});

type ThanhTich = { name?: string; icon?: string };
type CuaSo = Window & {
  __showAchievement?: (a: ThanhTich) => void;
  __refreshHsaTiles?: () => void;
};

export default function NhiemVuClient({ banDau }: { banDau: NhiemVuMot[] }) {
  const [ds, setDs] = useState(banDau);
  const [dangNhan, setDangNhan] = useState<string | null>(null);
  const [loi, setLoi] = useState<string | null>(null);

  async function nhan(code: string) {
    setDangNhan(code);
    setLoi(null);
    try {
      const d = await ghiJson('/api/missions/claim', { method: 'POST', body: JSON.stringify({ code }) }, HD_NHAN);
      setDs(d.missions);
      const w = window as CuaSo;
      d.newAchievements.forEach((a) => w.__showAchievement?.(a));
      w.__refreshHsaTiles?.();
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Chưa nhận được thưởng — thử lại giúp nhé.'));
    } finally {
      setDangNhan(null);
    }
  }

  if (ds.length === 0) return <div className="hsa-mis-empty">Chưa có nhiệm vụ nào cho hôm nay.</div>;

  return (
    <>
      {ds.map((m) => {
        const pct = Math.min(100, Math.round((m.progress / (m.target || 1)) * 100));
        const trangThai = m.claimed ? 'is-claimed' : m.done ? 'is-done' : '';
        return (
          <div key={m.code} className={`hsa-mis ${trangThai}`}>
            <div className="hsa-mis-top">
              <span className="hsa-mis-title">{m.title}</span>
              {m.claimed ? (
                <span className="hsa-mis-got">Đã nhận</span>
              ) : m.done ? (
                <button className="hsa-mis-claim" disabled={dangNhan === m.code} onClick={() => void nhan(m.code)}>
                  {dangNhan === m.code ? 'Đang nhận…' : `Nhận +${m.xpReward}`}
                </button>
              ) : (
                <span className="hsa-mis-xp">+{m.xpReward} XP</span>
              )}
            </div>
            <div className="hsa-mis-track"><i style={{ width: `${pct}%` }}></i></div>
            <div className="hsa-mis-meta">
              {m.progress}/{m.target} · {m.description}
            </div>
          </div>
        );
      })}
      {loi && <div className="hsa-mis-empty" role="alert">{loi}</div>}
    </>
  );
}
