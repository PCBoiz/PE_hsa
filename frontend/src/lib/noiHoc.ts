/**
 * NƠI HỌC của một buổi / một lớp — hình thức (trực tuyến / tại trung tâm) và
 * phòng (§53, bảng yêu cầu TopHSA tab "Nhi" #4, 23/09/2026).
 *
 * Buổi để trống thì theo lớp — máy chủ đã gộp sẵn thành `modeHieuLuc` /
 * `roomHieuLuc` (sổ buổi) hay `hinhThuc` / `phong` (lịch gộp); tệp này chỉ đặt
 * CÂU CHỮ, để bốn màn (sổ buổi, lịch, danh sách lớp, lớp của em) gọi cùng một tên.
 *
 * Mã thuần, không `'use client'`: dựng được ở cả máy chủ lẫn trình duyệt.
 */
export type HinhThuc = 'online' | 'offline';

export const NHAN_HINH_THUC: Record<HinhThuc, string> = {
  online: 'Trực tuyến',
  offline: 'Tại trung tâm',
};

/** "Trực tuyến" / "Phòng P201" / "Tại trung tâm" / null (chưa đặt hình thức). */
export function noiHoc(mode: string | null | undefined, room: string | null | undefined): string | null {
  if (mode === 'online') return NHAN_HINH_THUC.online;
  if (mode === 'offline') {
    const p = (room ?? '').trim();
    return p ? `Phòng ${p}` : NHAN_HINH_THUC.offline;
  }
  return null;
}
