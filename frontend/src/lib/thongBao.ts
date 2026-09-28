/**
 * TRANG "THÔNG BÁO" (§61, bảng TopHSA dòng 27) — hình dạng của `/api/notifications/feed`.
 *
 * Mọi NHÃN loại do máy chủ trả sẵn (`backend/notifications/loai.py`): màn hình không gõ
 * lại danh mục (RULES §7), và `type` là mã kỹ thuật nên không bao giờ được hiện thẳng
 * (RULES §10). Ở đây chỉ có cách ĐỌC một mốc thời gian thành câu tiếng Việt.
 *
 * `zod/mini`: tệp này được cả trang máy chủ lẫn component `'use client'` nhập
 * (`e2e/unit/zod-phia-trinh-duyet.test.mjs`).
 */
import * as z from 'zod/mini';

const so = z.number();
const soNull = z.nullable(z.number());
const chu = z.string();
const chuNull = z.nullable(z.string());

export const HD_DONG = z.looseObject({
  id: so,
  type: chuNull,
  /** Câu tiếng Việt của `type`, do máy chủ trả. Mã lạ → "Khác". */
  loaiNhan: chu,
  title: chuNull,
  body: chuNull,
  is_read: z.boolean(),
  created_at: chuNull,
  readAt: chuNull,
  link: chuNull,
  /** Số việc đã gộp vào dòng này (chuông gộp). 1 = không gộp. */
  coalesce_count: z.optional(so),
  announcementId: z.optional(soNull),
});
export type Dong = z.infer<typeof HD_DONG>;

export const HD_MOT_LOAI = z.looseObject({ loai: chu, nhan: chu, so, chuaDoc: so });
export type MotLoai = z.infer<typeof HD_MOT_LOAI>;

export const HD_TRANG = z.looseObject({
  items: z.array(HD_DONG),
  unread: so,
  /** Giá trị `truoc` cho trang kế. null = hết. Phân trang theo KHOÁ, không theo số trang. */
  tiep: z.optional(soNull),
  /** Chỉ có ở trang ĐẦU (máy chủ không đếm lại ở mỗi lần "tải thêm"). */
  cacLoai: z.optional(z.array(HD_MOT_LOAI)),
});
export type Trang = z.infer<typeof HD_TRANG>;

/** Trang đầu: 20 dòng. Vừa một màn điện thoại cuộn hai lần, và đủ để thấy có gì cần lọc. */
export const MOI_TRANG = 20;

export function duongTrang(truoc: number | null, loai: string | null, chuaDoc: boolean): string {
  const t = new URLSearchParams({ limit: String(MOI_TRANG) });
  if (truoc) t.set('truoc', String(truoc));
  if (loai) t.set('loai', loai);
  if (chuaDoc) t.set('chuaDoc', '1');
  return `/api/notifications/feed?${t}`;
}

const PHUT = 60_000;
const GIO = 60 * PHUT;
const NGAY = 24 * GIO;

/**
 * Mốc thời gian thành câu người đọc: "vừa xong", "3 giờ trước", "hôm qua", rồi ngày tháng.
 *
 * Mốc tuyệt đối vẫn giữ trong `title` của thẻ `<time>` — "2 ngày trước" trả lời câu hỏi
 * thường gặp, còn "24/09/2026 19:30" trả lời câu hỏi lúc người ta cần chính xác.
 */
export function khiNao(iso: string | null, bayGio: number = Date.now()): string {
  if (!iso) return '';
  const t = Date.parse(iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`);
  if (Number.isNaN(t)) return '';
  const cach = bayGio - t;
  if (cach < 0) return 'vừa xong';
  if (cach < PHUT) return 'vừa xong';
  if (cach < GIO) return `${Math.floor(cach / PHUT)} phút trước`;
  if (cach < NGAY) return `${Math.floor(cach / GIO)} giờ trước`;
  if (cach < 2 * NGAY) return 'hôm qua';
  if (cach < 7 * NGAY) return `${Math.floor(cach / NGAY)} ngày trước`;
  return ngayGio(iso);
}

/**
 * "24/09/2026 19:30". Tự ghép chứ không dùng `toLocaleDateString('vi-VN')`: bộ dựng trên
 * Node của Vercel nhả `24-09-2026` (gạch nối) cho cùng mã lệnh mà trình duyệt nhả dấu
 * gạch chéo, nên ngày tháng đổi hình dạng giữa HTML máy chủ và lần vẽ lại ở trình duyệt.
 */
export function ngayGio(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`);
  if (Number.isNaN(d.getTime())) return '';
  const hai = (n: number) => String(n).padStart(2, '0');
  return `${hai(d.getDate())}/${hai(d.getMonth() + 1)}/${d.getFullYear()} ${hai(d.getHours())}:${hai(d.getMinutes())}`;
}

/**
 * Trả lời của ba cửa đánh dấu (`/read`, `/unread`, `/read-all`).
 *
 * `unread` chỉ có ở `/unread` — cửa ấy đếm lại sau khi đổi. Khi có thì dùng số của máy
 * chủ chứ không tự cộng trừ ở màn: con số trên chuông là thứ hai nơi cùng hiện, và hai
 * nơi tự đếm riêng thì sớm muộn lệch nhau.
 */
export const HD_DANH_DAU = z.looseObject({
  ok: z.optional(z.boolean()),
  unread: z.optional(so),
});
export type DanhDau = z.infer<typeof HD_DANH_DAU>;
