'use client';

import { useState } from 'react';
// `zod/mini` ở mã trình duyệt — xem `e2e/unit/zod-phia-trinh-duyet.test.mjs`.
import * as z from 'zod/mini';

import { layJson, loiBatDuoc } from '@/lib/api';

/**
 * Bảng xếp hạng — phần chạy ở trình duyệt: ba tab, nhớ dữ liệu từng tab đã tải.
 *
 * Tab "Tuần" có sẵn từ máy chủ (`BangXepHang.tsx`); "Streak" và "Bạn bè" tải
 * khi bấm lần đầu rồi giữ lại — cùng hành vi bộ nhớ đệm của `dashboard.js` cũ.
 * Giữ nguyên class CSS cũ (`lb-*`) để giao diện không đổi một điểm ảnh nào.
 */
type Dong = { rank: number; id: number; name: string; avatar: string; value: number; medal?: string };
export type BangDuLieu = {
  type: string;
  unit: string;
  label: string;
  entries: Dong[];
  me: Dong | null;
};
type Loai = 'weekly' | 'streak' | 'friends';

const DONG_MINI = {
  rank: z.number(), id: z.number(), name: z.string(), avatar: z.string(), value: z.number(),
};
const HD_BANG_MINI = z.looseObject({
  type: z.string(),
  unit: z.string(),
  label: z.string(),
  entries: z.array(z.looseObject({ ...DONG_MINI, medal: z.optional(z.string()) })),
  me: z.nullable(z.looseObject(DONG_MINI)),
});

const TAB: { loai: Loai; nhan: string }[] = [
  { loai: 'weekly', nhan: '⏱ Tuần' },
  { loai: 'streak', nhan: '🔥 Streak' },
  { loai: 'friends', nhan: '👥 Bạn bè' },
];

/** Dấu chấm ngăn nghìn viết tay — `toLocaleString` phụ thuộc ICU của máy chạy,
 *  máy chủ và trình duyệt lệch nhau một ký tự là React báo lỗi hydrate. */
function nghin(n: number) {
  return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}
function giaTri(v: number, unit: string) {
  return unit === 'ngày' ? `${v} ngày` : `${nghin(v)} XP`;
}

function Hang({ e, laToi, unit }: { e: Dong; laToi: boolean; unit: string }) {
  const top = e.rank === 1 ? ' lb-top1' : e.rank === 2 ? ' lb-top2' : e.rank === 3 ? ' lb-top3' : '';
  return (
    <li className={`lb-row${top}${laToi ? ' lb-row-me' : ''}`}>
      <div className="lb-rank">
        <span className="lb-rank-text">{e.medal ?? ''}</span>
        <span className="lb-rank-num">#{e.rank}</span>
      </div>
      <div className="lb-avatar">{e.avatar || '🧑'}</div>
      <div className="lb-info">
        {/* "Bạn" là CHIP riêng, không nối vào tên (21/09/2026): hàng "vị trí của
            bạn" từng hiện "AUDIT2009 Lê Chi (B" — chính cái nhãn cho biết đây là
            mình lại là phần bị cắt. Tên dài thì cắt tên, chip luôn còn. */}
        <div className="lb-name">
          <span className="lb-name-text">{e.name}</span>
          {laToi && <span className="lb-me-chip">Bạn</span>}
        </div>
      </div>
      <div className="lb-value">{giaTri(e.value, unit)}</div>
    </li>
  );
}

export default function BangXepHangClient({ banDau }: { banDau: BangDuLieu | null }) {
  const [loai, setLoai] = useState<Loai>('weekly');
  const [kho, setKho] = useState<Partial<Record<Loai, BangDuLieu>>>(banDau ? { weekly: banDau } : {});
  const [dangTai, setDangTai] = useState(false);
  const [loi, setLoi] = useState<string | null>(banDau ? null : 'Không tải được bảng xếp hạng.');

  async function chon(l: Loai) {
    setLoai(l);
    setLoi(null);
    if (kho[l]) return;
    setDangTai(true);
    try {
      const d = await layJson(`/api/leaderboard?type=${l}`, HD_BANG_MINI);
      setKho((k) => ({ ...k, [l]: d }));
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Không tải được bảng xếp hạng.'));
    } finally {
      setDangTai(false);
    }
  }

  const d = kho[loai];
  const me = d?.me ?? null;
  const trongTop = !!me && !!d?.entries.some((e) => e.id === me.id);
  // Bảng TRỐNG ("chưa ai có điểm") thì không có hạng nào để nói: tầng cũ vẫn
  // hiện "Vị trí của bạn: #1 · 0 XP" — hạng nhất với không điểm là câu sai
  // nghĩa (thấy khi bấm thử tab Tuần đầu tuần, 14/09/2026).
  const coHang = !!d && !!me && !trongTop && d.entries.length > 0;

  let meta: string;
  if (dangTai) meta = 'Đang tải…';
  else if (loi || !d) meta = loi ?? 'Không tải được bảng xếp hạng.';
  else meta = `${d.label}${d.entries.length ? ` · Top ${d.entries.length} học viên` : ' · chưa ai có điểm'}`;

  return (
    <>
      <div className="lb-header">
        <div className="section-title" style={{ marginBottom: 0 }}>
          <span className="title-icon-blue">🏆</span><span>Bảng xếp hạng</span>
        </div>
        <div className="lb-tabs" role="tablist" aria-label="Bảng xếp hạng">
          {TAB.map((t) => (
            <button
              key={t.loai}
              type="button"
              className={`lb-tab${loai === t.loai ? ' active' : ''}`}
              role="tab"
              aria-selected={loai === t.loai}
              onClick={() => void chon(t.loai)}
            >
              {t.nhan}
            </button>
          ))}
        </div>
      </div>
      <div className="lb-meta" id="lb-meta">{meta}</div>
      <ol className="lb-list" id="lb-list" aria-live="polite">
        {dangTai ? (
          <li className="lb-skel">Đang tải bảng xếp hạng…</li>
        ) : !d ? (
          <li className="lb-skel">Vui lòng thử lại sau.</li>
        ) : (
          d.entries.map((e) => <Hang key={e.id} e={e} laToi={!!me && e.id === me.id} unit={d.unit} />)
        )}
      </ol>
      {/* "Vị trí của bạn" chỉ khi em có hạng mà nằm ngoài top. Nhân viên xem
          bảng thì `me` là null (backend 14/09) — khối không hiện. */}
      <div className="lb-me" id="lb-me" hidden={!coHang || dangTai}>
        {coHang && d && me && (
          <>
            <div className="lb-me-label">Vị trí của bạn</div>
            <ol className="lb-list"><Hang e={me} laToi unit={d.unit} /></ol>
          </>
        )}
      </div>
    </>
  );
}
