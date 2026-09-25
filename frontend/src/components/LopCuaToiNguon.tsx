import { z } from 'zod';

import LopCuaToi, { type DuLieu } from '@/components/LopCuaToi';
import type { HinhDang } from '@/lib/kiemDang';
import { serverJson } from '@/lib/server-api';
import { HD_TIEN_DO_EM } from '@/lib/chuongTrinh';

/**
 * Lấy dữ liệu "Lớp của bạn" Ở MÁY CHỦ rồi đưa xuống khối hiển thị.
 *
 * Tách làm hai tệp vì khối hiển thị cần `useState` (nút "Dùng ngày thi của
 * lớp") nên phải là `'use client'`, mà component client thì không `await` được
 * ở máy chủ. Đây là cùng một khuôn với `HocTiep`: máy chủ lấy dữ liệu, client
 * lo tương tác.
 *
 * Hỏng thì trả `null` — KHÔNG hiện lỗi đỏ ở đầu trang học viên. Khối này là
 * lời nhắc, thiếu nó bảng điều khiển vẫn dùng được; còn một câu lỗi kỹ thuật
 * ngay dòng đầu thì làm em tưởng cả trang hỏng.
 */
const chu = z.string().nullable();
const BUOI = {
  sessionId: z.number(),
  startsAt: chu,
  durationMinutes: z.number().nullable(),
  topic: chu,
  meetingUrl: chu,
  // Tuỳ chọn: máy chủ trước 24/09/2026 (§53) không trả — khối vẫn phải dựng được.
  hinhThuc: chu.optional(),
  phong: chu.optional(),
  dangDienRa: z.boolean(),
};
const HINH_DANG = z.looseObject({
  lop: z.array(z.looseObject({
    id: z.number(),
    name: z.string(),
    schedule: chu,
    teacherName: chu,
    examDate: chu,
    mode: chu.optional(),
    room: chu.optional(),
    buoiToi: z.looseObject(BUOI).nullable(),
    sapToi: z.array(z.looseObject(BUOI)),
    // `daHuy` cũng đi qua `_buoi_dict` nên có ĐỦ khoá như một buổi thường —
    // khai thiếu ở đây là kiểu của trang hẹp hơn dữ liệu thật, `tsc` bắt ngay.
    daHuy: z.array(z.looseObject(BUOI)),
    // Tên khoá ĐÚNG như `lop_cua_toi.py` trả: `sessionsCounted/present/late/
    // absent/excused/attendedPct` — cùng bộ từ với tờ báo cáo phụ huynh.
    chuyenCan: z.looseObject({
      sessionsCounted: z.number(), present: z.number(), late: z.number(),
      absent: z.number(), excused: z.number(), attendedPct: z.number().nullable(),
    }),
    ngayThiLech: z.boolean(),
    baiTap: z.looseObject({ chuaNop: z.number(), hanSom: chu }),
    // V-d (25/09/2026) — tuỳ chọn: Vercel lên trước Render, máy chủ cũ không trả.
    diemDanh: z.array(z.looseObject({
      sessionId: z.number(), startsAt: chu, topic: chu, daDiemDanh: z.boolean(), trangThai: chu,
    })).optional(),
    chuongTrinh: HD_TIEN_DO_EM,
  })),
  mucTieu: z.looseObject({ examDate: chu }),
}) satisfies HinhDang<DuLieu>;

export default async function LopCuaToiNguon() {
  const kq = await serverJson('/api/lop-cua-toi', { requireAuth: true }, HINH_DANG);
  return <LopCuaToi dl={kq.ok ? kq.data : null} />;
}
