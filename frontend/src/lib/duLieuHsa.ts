import { cache } from 'react';
import { z } from 'zod';

import type { HinhDang } from '@/lib/kiemDang';
import { serverJson } from '@/lib/server-api';

/**
 * HAI LƯỢT GỌI dựng phần số liệu của Trang của tôi — dùng CHUNG trong một lượt
 * dựng trang (14/09/2026, tối).
 *
 * Ba khối dựng ở máy chủ cùng đọc chúng: thẻ "Học tiếp", hàng bốn thẻ số, dải
 * tiến độ ba hợp phần. Mỗi khối chảy qua `Suspense` riêng, nên không đặt lời gọi
 * ở `page.tsx` (chặn cả trang — bài học LCP 4,3 s vòng 15). `cache()` của React
 * gộp các lời gọi trùng trong CÙNG một request thành một: ba khối, hai lượt API.
 *
 * Hình dạng khai ĐỦ mọi khoá ba khối đọc (T18 mức 2); `looseObject` nên máy chủ
 * thêm khoá thì không sao.
 */
export type TomTatHsa = {
  streakDays: number;
  lessonsDone: number;
  lessonsTotal: number;
  byCourse: Record<string, number>;
  targetScore: string | number | null;
  examTiming: string | null;
  examDate: string | null;
  daysToExam: number | null;
  lastMockScore: number | null;
  lastMockTotal: number | null;
};

export const HD_TOM_TAT = z.looseObject({
  streakDays: z.number(),
  lessonsDone: z.number(),
  lessonsTotal: z.number(),
  byCourse: z.record(z.string(), z.number()),
  targetScore: z.union([z.string(), z.number()]).nullable(),
  examTiming: z.string().nullable(),
  examDate: z.string().nullable(),
  daysToExam: z.number().nullable(),
  lastMockScore: z.number().nullable(),
  lastMockTotal: z.number().nullable(),
}) satisfies HinhDang<TomTatHsa>;

export type KhoaDangHoc = { id: string; title?: string | null; progress?: number | null };
export const HD_KHOA_DANG_HOC = z.looseObject({
  enrolled: z.array(z.looseObject({
    id: z.string(),
    title: z.string().nullable().optional(),
    progress: z.number().nullable().optional(),
  })),
}) satisfies HinhDang<{ enrolled: KhoaDangHoc[] }>;

export const layTomTat = cache(() => serverJson('/api/hsa/summary', { requireAuth: true }, HD_TOM_TAT));
export const layKhoaDangHoc = cache(() =>
  serverJson('/api/courses-enrolled', { requireAuth: true }, HD_KHOA_DANG_HOC));

/** Tổng số bài của từng hợp phần — CÙNG bảng với backend `TOTAL_LESSONS` chia theo khoá. */
export const HOP_PHAN = [
  { key: 'ql', id: 'hsa_quantitative', ten: 'Tư duy Định lượng', tong: 27 },
  { key: 'vb', id: 'hsa_verbal', ten: 'Tư duy Định tính', tong: 23 },
  { key: 'kh', id: 'hsa_science', ten: 'Khoa học', tong: 26 },
] as const;
