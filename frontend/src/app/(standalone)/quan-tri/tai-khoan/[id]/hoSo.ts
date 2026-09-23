/**
 * Kiểu + hình dạng của hồ sơ học viên (`teaching/ho_so.py`) — MỘT chỗ cho cả
 * trang máy chủ lẫn form ở trình duyệt.
 *
 * Tệp thường, KHÔNG `'use client'`: giá trị nhập từ một tệp `'use client'` vào
 * Server Component chỉ là tham chiếu tới trình duyệt, gọi `.safeParse` trên đó
 * là hỏng. `zod/mini` cho cả hai phía: trình duyệt cần gói nhỏ (xem chú thích ở
 * `AccountsClient.tsx`), còn máy chủ chỉ cần `safeParse` — `HinhDang` là kiểu
 * cấu trúc, không đòi bản `zod` đầy đủ.
 */
import * as z from 'zod/mini';

import type { HinhDang } from '@/lib/kiemDang';

export type HoSo = {
  id: number;
  name: string | null;
  email: string | null;
  phone: string | null;
  birthday: string | null;
  role: string;
  status: string | null;
  studentCode: string | null;
  username: string | null;
  school: string | null;
  schoolGrade: string | null;
  region: string | null;
  consultantId: number | null;
  consultantName: string | null;
  enrollSource: string | null;
  studyGoal: string | null;
  aspiration: string | null;
  parentName: string | null;
  parentPhone: string | null;
  parentEmail: string | null;
};

export type NguonTuyenSinh = { ma: string; nhan: string };
export type NguoiTuVan = { id: number; name: string | null; role: string };

export type HoSoPayload = {
  profile: HoSo;
  sources: NguonTuyenSinh[];
  consultants: NguoiTuVan[];
};

const chu = z.nullable(z.string());

const HD_HO_SO = z.looseObject({
  id: z.number(),
  name: chu,
  email: chu,
  phone: chu,
  birthday: chu,
  role: z.string(),
  status: chu,
  studentCode: chu,
  username: chu,
  school: chu,
  schoolGrade: chu,
  region: chu,
  consultantId: z.nullable(z.number()),
  consultantName: chu,
  enrollSource: chu,
  studyGoal: chu,
  aspiration: chu,
  parentName: chu,
  parentPhone: chu,
  parentEmail: chu,
}) satisfies HinhDang<HoSo>;

/** `GET /api/admin/users/<id>/profile`. */
export const HD_TRANG_HO_SO = z.looseObject({
  profile: HD_HO_SO,
  sources: z.array(z.looseObject({ ma: z.string(), nhan: z.string() })),
  consultants: z.array(z.looseObject({ id: z.number(), name: chu, role: z.string() })),
}) satisfies HinhDang<HoSoPayload>;

/** `PATCH` cùng đường — máy chủ trả lại hồ sơ SAU khi ghi (đã chuẩn hoá). */
export const HD_DA_LUU = z.looseObject({ profile: HD_HO_SO }) satisfies HinhDang<{ profile: HoSo }>;

/** Một mốc của dòng thời gian (`teaching/dong_thoi_gian.py`). */
export type MocThoiGian = {
  loai: string;
  /** ISO. `caNgay` thì chỉ có ngày ('2026-09-20') — KHÔNG có giờ để hiện. */
  luc: string;
  caNgay: boolean;
  tieuDe: string;
  chiTiet: string | null;
  boi: string | null;
};

export type DongThoiGian = { events: MocThoiGian[]; tong: number; catBot: boolean };

/** `GET /api/admin/users/<id>/timeline`. */
export const HD_DONG_THOI_GIAN = z.looseObject({
  events: z.array(z.looseObject({
    loai: z.string(),
    luc: z.string(),
    caNgay: z.boolean(),
    tieuDe: z.string(),
    chiTiet: chu,
    boi: chu,
  })),
  tong: z.number(),
  catBot: z.boolean(),
}) satisfies HinhDang<DongThoiGian>;
