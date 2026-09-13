import Link from 'next/link';
import { z } from 'zod';

import HocTiepRong from '@/components/HocTiepRong';

import { serverJson } from '@/lib/server-api';
import type { HinhDang } from '@/lib/kiemDang';

/**
 * THẺ "HỌC TIẾP" — dựng Ở MÁY CHỦ, không chờ tầng JS cũ.
 *
 * ── VÌ SAO CHUYỂN (14/09/2026) ────────────────────────────────────────────
 *
 * Thẻ này là phần tử LCP của Trang của tôi (8.840 px², lớn nhất màn đầu). Nó
 * vốn do `dashboard.js::renderContinue` vẽ, mà tầng cũ chỉ chạy sau khi React
 * hydrate: đo được **2,2–2,5 s** mới hiện, trong khi trang đã vẽ xong từ giây
 * 0,5. Đưa về đây thì nó nằm sẵn trong HTML máy chủ trả về — người học thấy
 * việc-cần-làm-tiếp ngay lượt sơn đầu tiên.
 *
 * Hai lượt gọi dữ liệu chạy SONG SONG và đều có hình dạng (T18 mức 2). Hỏng
 * một lượt thì hiện khối rỗng "Bắt đầu hành trình HSA" — KHÔNG hiện lỗi đỏ:
 * đây là một khối gợi ý, không phải nội dung chính, và một câu lỗi kỹ thuật ở
 * đầu trang học viên thì đáng sợ hơn là hữu ích.
 *
 * ── LUẬT CHỌN BÀI (giữ NGUYÊN của `renderContinue`) ───────────────────────
 *
 * Số bài đã xong đếm từ `byCourse` (đếm thật trong `lesson_progress`), chỉ khi
 * thiếu mới suy từ `progress` — vì `enrollments.progress` là bộ nhớ đệm và
 * bằng 0 với người học thẳng từ lộ trình. Khoá được chọn là khoá **dở dang
 * nhiều nhất**; nếu mọi khoá đã xong thì lấy khoá đầu danh sách.
 */

/** Tổng số bài của từng hợp phần — CÙNG bảng với `dashboard.js::SECTIONS`. */
const TONG_BAI: Record<string, number> = {
  hsa_quantitative: 27,
  hsa_verbal: 23,
  hsa_science: 26,
};
const MAC_DINH = 27;

type Khoa = { id: string; title?: string | null; progress?: number | null };

const HD_SUMMARY = z.looseObject({
  byCourse: z.record(z.string(), z.number()),
}) satisfies HinhDang<{ byCourse: Record<string, number> }>;

const HD_KHOA = z.looseObject({
  enrolled: z.array(z.looseObject({
    id: z.string(),
    title: z.string().nullable().optional(),
    progress: z.number().nullable().optional(),
  })),
}) satisfies HinhDang<{ enrolled: Khoa[] }>;

function chonKhoa(ds: Khoa[], daXong: Record<string, number>) {
  const soXong = (c: Khoa) =>
    daXong[c.id] ?? Math.round(((c.progress ?? 0) / 100) * (TONG_BAI[c.id] ?? MAC_DINH));
  const xep = [...ds].sort((a, b) => soXong(b) - soXong(a));
  return xep.find((c) => soXong(c) < (TONG_BAI[c.id] ?? MAC_DINH)) ?? xep[0] ?? null;
}

export default async function HocTiep() {
  const [sum, khoa] = await Promise.all([
    serverJson('/api/hsa/summary', { requireAuth: true }, HD_SUMMARY),
    serverJson('/api/courses-enrolled', { requireAuth: true }, HD_KHOA),
  ]);

  const daXong = sum.ok ? sum.data.byCourse : {};
  const c = khoa.ok ? chonKhoa(khoa.data.enrolled, daXong) : null;
  if (!c) return <HocTiepRong />;

  const tong = TONG_BAI[c.id] ?? MAC_DINH;
  const xong = daXong[c.id] ?? Math.round(((c.progress ?? 0) / 100) * tong);
  const baiKe = Math.min(tong, xong + 1);
  const pct = Math.round((xong / tong) * 100);

  return (
    <Link className="hsa-cont-link" href={`/lesson/${c.id}?lesson=${baiKe}`}>
      <span className="hsa-cont-badge">{baiKe}</span>
      <span className="hsa-cont-txt">
        <span className="hsa-cont-eyebrow">Học tiếp</span>
        <div className="hsa-cont-title">
          {c.title || 'Khoá học'} — Bài {baiKe}
        </div>
        <span className="hsa-cont-meta">
          {pct}% hoàn thành · {tong} bài
        </span>
      </span>
      <span className="hsa-cont-go">Vào học →</span>
    </Link>
  );
}
