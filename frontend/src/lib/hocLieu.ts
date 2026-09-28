/**
 * HỌC LIỆU CỦA LỚP (§60) — hình dạng của `/api/teach/classes/<id>/hoc-lieu`.
 *
 * Anh Sơn chốt 26/09: liên kết ngoài trước (Drive, YouTube, link đề), gắn được vào cả kho
 * chung của lớp lẫn từng buổi. Tệp tải thẳng lên (`nguon: 'r2'`) là chỗ đã chừa sẵn ở lược
 * đồ, chưa dựng — nên màn phải đọc được `nguon` ngay từ bây giờ và đừng giả định chỉ có một
 * loại: ngày thêm R2 sẽ chỉ là thêm một nhánh hiển thị, không phải sửa lại cả hình dạng.
 *
 * `zod/mini`: tệp này được cả trang máy chủ lẫn component `'use client'` nhập
 * (`e2e/unit/zod-phia-trinh-duyet.test.mjs`).
 */
import * as z from 'zod/mini';

const so = z.number();
const soNull = z.nullable(z.number());
const chu = z.string();
const chuNull = z.nullable(z.string());

export const HD_TAI_LIEU = z.looseObject({
  id: so,
  ten: chu,
  moTa: chuNull,
  /** 'link' = địa chỉ ngoài (hôm nay). 'r2' = tệp tải lên (chờ khoá của anh Sơn). */
  nguon: chu,
  url: chuNull,
  /** Đã gắn nhưng chưa mở cho học viên xem. Học viên không bao giờ nhận dòng này. */
  an: z.boolean(),
  /** null = kho chung của lớp; có số = tài liệu của riêng buổi ấy. */
  sessionId: soNull,
  buoiLuc: chuNull,
  nguoiTao: chuNull,
  luc: chuNull,
});
export type TaiLieu = z.infer<typeof HD_TAI_LIEU>;

export const HD_KHO = z.looseObject({
  items: z.array(HD_TAI_LIEU),
  /** Người đang xem có phải người của khu giảng dạy không (được gắn / gỡ). */
  coTheGan: z.boolean(),
});
export type Kho = z.infer<typeof HD_KHO>;

/**
 * Nhóm tài liệu: kho chung trước, rồi từng buổi theo thứ tự buổi.
 *
 * Nhóm ở MÀN chứ không đòi máy chủ trả sẵn hai danh sách: máy chủ đã sắp đúng thứ tự
 * (`ORDER BY session_id NULLS FIRST`), và một danh sách phẳng thì bộ lọc "chỉ buổi này"
 * sau đây chỉ là một phép lọc, không phải một lượt gọi mới.
 */
export function nhom(ds: TaiLieu[]): { sessionId: number | null; buoiLuc: string | null; items: TaiLieu[] }[] {
  const theo = new Map<number | null, { sessionId: number | null; buoiLuc: string | null; items: TaiLieu[] }>();
  for (const t of ds) {
    const k = t.sessionId ?? null;
    if (!theo.has(k)) theo.set(k, { sessionId: k, buoiLuc: t.buoiLuc, items: [] });
    theo.get(k)!.items.push(t);
  }
  return [...theo.values()];
}

/**
 * Tên miền của một địa chỉ, để hiện cạnh tên tài liệu ("drive.google.com").
 *
 * Người bấm nên biết mình sắp rời khỏi TopHSA đi đâu, TRƯỚC khi bấm — nhất là khi đường
 * dẫn do người khác dán vào. Địa chỉ hỏng thì trả chuỗi rỗng chứ không ném: một tên miền
 * không đọc ra được không đáng làm trắng cả trang.
 */
export function tenMien(url: string | null): string {
  if (!url) return '';
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return '';
  }
}

/** Ngày giờ buổi học: "24/09 19:30". Tự ghép — xem lý do ở `thongBao.ts::ngayGio`. */
export function buoiNgan(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`);
  if (Number.isNaN(d.getTime())) return '';
  const hai = (n: number) => String(n).padStart(2, '0');
  return `${hai(d.getDate())}/${hai(d.getMonth() + 1)} ${hai(d.getHours())}:${hai(d.getMinutes())}`;
}

/** Trả lời của cửa gỡ tài liệu. */
export const HD_GO = z.looseObject({ ok: z.optional(z.boolean()) });
