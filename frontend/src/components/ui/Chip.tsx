import type { ReactNode } from 'react';

/**
 * Chip — nhãn trạng thái ngắn.
 *
 * Màu ngữ nghĩa (tốt / cảnh báo / kém) tách hẳn khỏi màu thương hiệu: tím là
 * "đang làm / hành động", teal là "xong / đúng", cam là "cần chú ý", đỏ là
 * "sai / nguy hiểm". Trộn hai hệ này là cách nhanh nhất làm người dùng đọc
 * nhầm trạng thái.
 *
 * `level` 1..4 dùng cho bậc thành thạo của bản đồ năng lực — và dùng CHUNG
 * với bảng điều khiển lớp của giảng viên, để một chủ đề trông giống nhau ở cả
 * hai bên. Học viên và giảng viên phải thấy cùng một thứ.
 */
type Tone = 'neutral' | 'brand' | 'good' | 'warn' | 'bad';

/**
 * Nền là bản pha nhạt của màu, nên CHỮ phải dùng bộ `-ink` đậm hơn một bậc.
 * Dùng thẳng `text-brand`/`text-success`… ở đây thì tương phản rơi xuống
 * 3.96–4.23:1, dưới chuẩn AA 4.5:1 (đo 30/08/2026, ba trong bốn tông trượt).
 * Bộ `-ink` tự đổi theo bộ sáng/tối — xem theme.css.
 */
const TONE: Record<Tone, string> = {
  neutral: 'bg-sunken text-ink-3',
  brand: 'bg-brand-soft text-brand-ink',
  good: 'bg-success/10 text-success-ink',
  warn: 'bg-warning/10 text-warning-ink',
  bad: 'bg-danger/10 text-danger-ink',
};

/** Bậc thành thạo → tông màu. Giữ đúng thứ tự của bản đồ năng lực. */
export const LEVEL_TONE: Record<1 | 2 | 3 | 4, Tone> = {
  1: 'bad',
  2: 'warn',
  3: 'brand',
  4: 'good',
};

export default function Chip({
  children,
  tone = 'neutral',
  level,
}: {
  children: ReactNode;
  tone?: Tone;
  level?: 1 | 2 | 3 | 4;
}) {
  const t = level ? LEVEL_TONE[level] : tone;
  return (
    <span
      className={`inline-flex min-h-7 items-center rounded-full px-3 text-small font-medium whitespace-nowrap ${TONE[t]}`}
    >
      {children}
    </span>
  );
}
