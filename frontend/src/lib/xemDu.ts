/**
 * XEM LẠI ĐỦ CẢ KHOÁ — hình dạng của `/api/lop-cua-toi/<id>/xem-du` (dòng 29, 30).
 *
 * Thẻ lớp ở bảng điều khiển chỉ giữ BỐN dòng gần nhất (`backend/teaching/lop_cua_toi.py`
 * `SO_BAN_GHI` / `SO_HOC_LIEU`). Cửa này là chỗ em xem đủ: bản ghi buổi học và học liệu của
 * cả khoá, có ô tìm, phân trang THEO KHOÁ.
 *
 * Vì sao khoá phân trang chỉ là MỘT SỐ NGUYÊN (`truoc`): mốc thật là cặp (thời điểm, id) và
 * máy chủ tự tra nó từ chính dòng ấy — trình duyệt không ghép mốc thời gian, nên không có
 * chỗ nào để múi giờ hay định dạng làm lệch một dòng.
 *
 * `zod/mini`: tệp này được cả trang máy chủ lẫn component `'use client'` nhập
 * (`e2e/unit/zod-phia-trinh-duyet.test.mjs`).
 */
import * as z from 'zod/mini';

const so = z.number();
const soNull = z.nullable(z.number());
const chu = z.string();
const chuNull = z.nullable(z.string());

/** Hai danh sách cửa này phục vụ — đúng chữ máy chủ nhận trên URL. */
export const BAN_GHI = 'ban-ghi';
export const HOC_LIEU = 'hoc-lieu';
export type Loai = typeof BAN_GHI | typeof HOC_LIEU;

export const HD_LOP_GON = z.looseObject({ id: so, name: chu, code: chuNull });
export type LopGon = z.infer<typeof HD_LOP_GON>;

/** Một buổi đã học có bản ghi. `daMo` = em đã BẤM mở, không phải đã xem hết (§72). */
export const HD_BAN_GHI = z.looseObject({
  sessionId: so,
  startsAt: chuNull,
  topic: chuNull,
  recordingUrl: chu,
  daMo: z.boolean(),
  lanMo: so,
});
export type BanGhi = z.infer<typeof HD_BAN_GHI>;

/** Một tài liệu. Máy chủ đã bỏ phần đang ẩn và phần của buổi em không thuộc — màn không lọc lại. */
export const HD_TAI_LIEU = z.looseObject({
  id: so,
  ten: chu,
  moTa: chuNull,
  nguon: chu,
  url: chuNull,
  /** null = kho chung của lớp; có số = tài liệu của riêng buổi ấy. */
  sessionId: soNull,
  buoiLuc: chuNull,
  buoiChuDe: chuNull,
  luc: chuNull,
});
export type TaiLieu = z.infer<typeof HD_TAI_LIEU>;

export const HD_TRANG_BAN_GHI = z.looseObject({
  lop: HD_LOP_GON,
  loai: chu,
  items: z.array(HD_BAN_GHI),
  /** Khoá xin trang kế. null = đã hết — nút "Xem thêm" biến đi. */
  tiep: soNull,
});
export type TrangBanGhi = z.infer<typeof HD_TRANG_BAN_GHI>;

export const HD_TRANG_HOC_LIEU = z.looseObject({
  lop: HD_LOP_GON,
  loai: chu,
  items: z.array(HD_TAI_LIEU),
  tiep: soNull,
});
export type TrangHocLieu = z.infer<typeof HD_TRANG_HOC_LIEU>;

/** Ô lọc của danh sách tài liệu. `null` = không lọc. */
export type Chi = 'chung' | 'buoi' | null;

export type ThamTrang = {
  /** Khoá dòng cuối trang trước. `null` = trang đầu. */
  truoc?: number | null;
  tim?: string;
  chuaMo?: boolean;
  chi?: Chi;
  /** CỐ Ý không có `limit`: số dòng một trang do MÁY CHỦ quyết (`hv_xem_du.MOI_TRANG`).
      Khai lại ở đây là hai nguồn sự thật cho một con số (RULES §7) — đúng lỗi đã mắc với
      trần 50 tài khoản, và cái lệch khi ấy là số dòng phải bốc về từ Neon. */
};

/**
 * Đường dẫn một trang.
 *
 * `URLSearchParams` chứ không tự ghép chuỗi: ô tìm là chữ em gõ, và một dấu `&` hay `#`
 * trong đó mà không mã hoá thì phần sau bị cắt mất — ô tìm im lặng trả sai.
 */
export function duongTrang(
  lopId: number,
  loai: Loai,
  { truoc = null, tim = '', chuaMo = false, chi = null }: ThamTrang = {},
): string {
  const p = new URLSearchParams({ loai });
  if (truoc !== null) p.set('truoc', String(truoc));
  if (tim.trim()) p.set('tim', tim.trim());
  if (chuaMo) p.set('chuaMo', '1');
  if (chi) p.set('chi', chi);
  return `/api/lop-cua-toi/${lopId}/xem-du?${p.toString()}`;
}

/** "Thứ Năm 24/09 · 19:30" — buổi học nói bằng lời người dùng, không phải mốc ISO. */
const THU = ['Chủ nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];

export function buoiDay(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const hai = (n: number) => String(n).padStart(2, '0');
  return `${THU[d.getDay()]} ${hai(d.getDate())}/${hai(d.getMonth() + 1)}/${d.getFullYear()}`
    + ` · ${hai(d.getHours())}:${hai(d.getMinutes())}`;
}

/** "24/09/2026" — dùng cho lúc GẮN tài liệu, nơi giờ phút không nói thêm gì. */
export function ngayDay(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const hai = (n: number) => String(n).padStart(2, '0');
  return `${hai(d.getDate())}/${hai(d.getMonth() + 1)}/${d.getFullYear()}`;
}

/**
 * Tên miền của một địa chỉ ("drive.google.com") — người bấm nên biết mình sắp rời TopHSA đi
 * đâu TRƯỚC khi bấm, nhất là khi đường dẫn do người khác dán vào.
 *
 * Cùng hàm với `lib/hocLieu.ts::tenMien`; nhập lại chứ không viết lại.
 */
export { tenMien } from '@/lib/hocLieu';
