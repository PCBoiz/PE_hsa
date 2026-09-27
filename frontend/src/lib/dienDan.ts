import { z } from 'zod';

/**
 * §75 · DIỄN ĐÀN RIÊNG CỦA LỚP — hình dạng dữ liệu và mấy câu chữ dùng chung.
 *
 * Anh Sơn chốt 27/09/2026: *"nhắn tin qua Zalo hoặc qua diễn đàn riêng của lớp, không làm
 * thành 1 messenger trong ứng dụng"*. Nên màn này KHÔNG phải hộp chat: nó là một bảng tin
 * của lớp — mỗi lượt là một bài, trả lời nằm dưới bài, và mọi thứ đều đọc lại được về sau.
 *
 * `looseObject`: máy chủ có thể trả thêm khoá (Vercel lên trước Render, và ngược lại) —
 * hình dạng chặt sẽ làm hỏng cả màn vì một khoá mới vô hại.
 */
const so = z.number();
const chu = z.string();
const chuNull = z.nullable(chu);
const soNull = z.nullable(so);

export const HD_BAI = z.looseObject({
  id: so,
  user_id: soNull,
  title: chuNull,
  content: chu,
  created_at: chuNull,
  author_name: chuNull,
  comment_count: z.optional(so),
});
export type Bai = z.infer<typeof HD_BAI>;

export const HD_DS_BAI = z.looseObject({
  // Vắng khi đang xem sân chung; màn lớp luôn có.
  lop: z.optional(z.looseObject({ id: so, ten: chu })),
  posts: z.array(HD_BAI),
  page: so,
  total: so,
  total_pages: so,
});
export type DsBai = z.infer<typeof HD_DS_BAI>;

export const HD_BINH_LUAN = z.looseObject({
  id: so,
  post_id: so,
  user_id: soNull,
  parent_comment_id: soNull,
  content: chu,
  created_at: chuNull,
  author_name: chuNull,
});
export type BinhLuan = z.infer<typeof HD_BINH_LUAN>;

export const HD_DS_BINH_LUAN = z.looseObject({
  comments: z.array(HD_BINH_LUAN),
  total: so,
});
export type DsBinhLuan = z.infer<typeof HD_DS_BINH_LUAN>;

export const HD_TAO_BAI = z.looseObject({ ok: z.boolean(), id: so });
export const HD_OK = z.looseObject({ ok: z.boolean() });

/** Trần ký tự — khớp `forum/views.py` để màn không cho gõ thứ máy chủ sẽ từ chối. */
export const TRAN_TIEU_DE = 200;
export const TRAN_NOI_DUNG = 5000;

/**
 * "3 phút trước" · "hôm qua 15:30" · "18/09 15:30".
 *
 * Tự ghép chứ không `toLocaleString`: máy chủ và trình duyệt chạy hai múi giờ khác nhau thì
 * cùng một dòng hiện hai giờ khác nhau, và bộ đo bắt được chuyện ấy như một lỗi giao diện.
 */
export function khiNao(iso: string | null): string {
  if (!iso) return '';
  const t = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`);
  if (Number.isNaN(t.getTime())) return '';
  const giay = Math.floor((Date.now() - t.getTime()) / 1000);
  if (giay < 60) return 'vừa xong';
  if (giay < 3600) return `${Math.floor(giay / 60)} phút trước`;
  if (giay < 86400) return `${Math.floor(giay / 3600)} giờ trước`;
  const hai = (n: number) => String(n).padStart(2, '0');
  const gio = `${hai(t.getHours())}:${hai(t.getMinutes())}`;
  if (giay < 172800) return `hôm qua ${gio}`;
  return `${hai(t.getDate())}/${hai(t.getMonth() + 1)} ${gio}`;
}
