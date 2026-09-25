/**
 * Cách NÓI tiến độ chương trình (E1) — hàm thuần, không nhập `zod`, để màn học viên
 * (`LopCuaToi`, chạy ở trình duyệt) dùng mà không kéo bộ kiểm hình dạng vào gói trang.
 * Hình dạng phản hồi ở `chuongTrinh.ts`.
 */
export const phanTram = (v: number | null | undefined) =>
  v == null ? '—' : `${Math.round(v)}%`;

/** Một cụm chữ ngắn cho chip ở danh sách lớp: tông + chữ. */
export function chipTienDo(t: { cham: boolean; treBuoi: number | null; chuaGhiSo: number; pct: number | null }): { tone: 'good' | 'warn' | 'bad'; chu: string } {
  if (t.cham) {
    const tre = t.treBuoi != null && t.treBuoi >= 1 ? ` · trễ ${t.treBuoi} buổi` : '';
    return { tone: 'bad', chu: `Chậm tiến độ${tre}` };
  }
  if (t.chuaGhiSo > 0) return { tone: 'warn', chu: `${phanTram(t.pct)} · ${t.chuaGhiSo} buổi chưa ghi sổ` };
  return { tone: 'good', chu: `Đúng tiến độ · ${phanTram(t.pct)}` };
}

/** Câu một dòng cho em / phụ huynh: "Đã học 40% chương trình (kế hoạch tới nay: 50%)." */
export function cauTienDoEm(t: { pct: number | null; keHoachPct: number | null }): string {
  const ke = t.keHoachPct != null ? ` (kế hoạch tới nay: ${phanTram(t.keHoachPct)})` : '';
  return `Đã học ${phanTram(t.pct)} chương trình${ke}.`;
}
