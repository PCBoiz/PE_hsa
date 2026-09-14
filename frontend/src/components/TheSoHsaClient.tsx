'use client';

import { useEffect, useState } from 'react';
// `zod/mini` ở mã trình duyệt — xem `e2e/unit/zod-phia-trinh-duyet.test.mjs`.
import * as z from 'zod/mini';

import { BieuTuong } from '@/components/bieuTuong';
import { layJson } from '@/lib/api';
import { thuTrongTuanVN } from '@/lib/gioVN';

/**
 * HÀNG BỐN THẺ SỐ của Trang của tôi — phần chạy ở trình duyệt.
 *
 * Dữ liệu ban đầu do máy chủ đưa xuống (`TheSoHsa.tsx`). Trước 14/09/2026 tối,
 * `dashboard.js::renderTiles` đổ số vào sau khi tầng cũ chạy — bốn ô đứng "—"
 * cho tới lúc ấy.
 *
 * Hai nơi cần hàng thẻ VẼ LẠI mà không tải lại trang: nút "Nhận" nhiệm vụ (XP
 * vừa cộng) và nút lưu mục tiêu ở Cài đặt (đếm ngược đổi). Cả hai vốn gọi
 * `window.__refreshHsaTiles` của tầng cũ — khối này đăng ký lại đúng tên ấy,
 * nên hai nơi gọi không phải sửa gì.
 *
 * Dải 7 ngày tính "hôm nay" theo GIỜ VIỆT NAM (`thuTrongTuanVN`), không theo
 * `new Date().getDay()`: khối được dựng ở máy chủ UTC trước, và từ 0h–7h sáng
 * hai đồng hồ lệch một ngày — xem `e2e/unit/gio-vn.test.mjs`.
 */
export type TomTatTheSo = {
  streakDays: number;
  lessonsDone: number;
  lessonsTotal: number;
  targetScore: string | number | null;
  examTiming: string | null;
  daysToExam: number | null;
  lastMockScore: number | null;
  lastMockTotal: number | null;
};

const HD = z.looseObject({
  streakDays: z.number(),
  lessonsDone: z.number(),
  lessonsTotal: z.number(),
  targetScore: z.nullable(z.union([z.string(), z.number()])),
  examTiming: z.nullable(z.string()),
  daysToExam: z.nullable(z.number()),
  lastMockScore: z.nullable(z.number()),
  lastMockTotal: z.nullable(z.number()),
});

const THU = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

type CuaSo = Window & { __refreshHsaTiles?: () => void; navigate?: (trang: string) => void };

export default function TheSoHsaClient({ banDau }: { banDau: TomTatTheSo | null }) {
  const [s, setS] = useState(banDau);

  useEffect(() => {
    const w = window as CuaSo;
    // Lỗi mạng khi làm mới thì GIỮ số đang hiện — cùng hành vi tầng cũ.
    w.__refreshHsaTiles = () => { layJson('/api/hsa/summary', HD).then(setS, () => {}); };
    return () => { delete w.__refreshHsaTiles; };
  }, []);

  const hom = thuTrongTuanVN();
  const streak = s?.streakDays ?? 0;
  const tong = s?.lessonsTotal || 76;
  const xong = s?.lessonsDone ?? 0;
  const ngay = s?.daysToExam ?? null;
  const daKhaoSat = Boolean(s?.examTiming || s?.targetScore);
  const coDiem = s?.lastMockScore != null && s?.lastMockTotal != null;

  return (
    <>
      <div className="hsa-tile">
        <div className="hsa-tile-ic"><BieuTuong ten="flame" co={18} /></div>
        <div className="hsa-tile-body">
          {/* `—` chứ không `0` khi chưa có dữ liệu: "0 ngày học liên tiếp" trông
              y hệt một tài khoản trắng thật. */}
          <div className="hsa-tile-num" id="tile-streak">{s ? streak : '—'}</div>
          <div className="hsa-tile-lbl">ngày học liên tiếp</div>
          <div className="hsa-week" id="tile-week" aria-label="Lịch học tuần này">
            {s && THU.map((d, i) => {
              // streak ĐÃ tính cả hôm nay → các ngày trước được tô là streak - 1.
              const cls = i === hom ? 'is-today' : i < hom && streak > hom - i ? 'is-done' : undefined;
              return <span key={d} className={cls}>{d}</span>;
            })}
          </div>
        </div>
      </div>

      <div className="hsa-tile">
        <div className="hsa-tile-ic"><BieuTuong ten="book-open" co={18} /></div>
        <div className="hsa-tile-body">
          <div className="hsa-tile-num">
            <span id="tile-done">{s ? xong : '—'}</span><span className="hsa-tile-of">/{tong}</span>
          </div>
          <div className="hsa-tile-lbl">bài đã hoàn thành</div>
          <div className="hsa-tile-bar">
            <i id="tile-done-bar" style={{ width: `${s ? Math.round((xong / tong) * 100) : 0}%` }}></i>
          </div>
        </div>
      </div>

      <div className="hsa-tile">
        <div className="hsa-tile-ic"><BieuTuong ten="clock" co={18} /></div>
        <div className="hsa-tile-body">
          <div className="hsa-tile-num" id="tile-days">{ngay ?? '—'}</div>
          <div className="hsa-tile-lbl">ngày nữa tới kỳ thi</div>
          {/* Không suy ra được mốc thi thì để dấu gạch + lối tới nơi sửa được.
              Đã khảo sát nhưng mốc đã trôi → vào thẳng Cài đặt, không bắt làm lại
              cả bài khảo sát chỉ để đổi một dòng. */}
          <a
            className={`hsa-tile-cta${s && ngay != null ? ' hidden' : ''}`}
            id="tile-days-cta"
            href={daKhaoSat ? '#hsa-goals' : '/questionaire'}
            onClick={(e) => {
              if (!daKhaoSat) return;
              e.preventDefault();
              (window as CuaSo).navigate?.('settings');
              document.getElementById('hsa-goals')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }}
          >
            {daKhaoSat ? 'Cập nhật mốc thi' : 'Làm khảo sát để đặt mốc thi'}
          </a>
        </div>
      </div>

      <div className="hsa-tile">
        <div className="hsa-tile-ic"><BieuTuong ten="target" co={18} /></div>
        <div className="hsa-tile-body">
          <div className="hsa-tile-num" id="tile-score">{coDiem ? `${s?.lastMockScore}/${s?.lastMockTotal}` : '—'}</div>
          <div className="hsa-tile-lbl" id="tile-score-lbl">
            {s?.targetScore ? `điểm thi thử · mục tiêu ${s.targetScore}` : 'điểm thi thử gần nhất'}
          </div>
          <a className={`hsa-tile-cta${coDiem ? ' hidden' : ''}`} id="tile-score-cta" href="/mock">Làm đề thi thử</a>
        </div>
      </div>
    </>
  );
}
