/**
 * HỘP YÊU CẦU (E3, §65) — hình dạng phản hồi và cách nói lịch sử một yêu cầu.
 *
 * Mọi NHÃN (loại, trạng thái, mốc trước / sau trong lịch sử) do máy chủ trả sẵn từ
 * `backend/yeu_cau/loai.py` — màn hình không gõ lại danh mục (RULES §7). Ở đây chỉ có câu
 * nối (“chuyển sang …”, “giao cho …”) và màu chip theo nhóm trạng thái.
 *
 * `zod/mini`: tệp này được cả trang máy chủ lẫn component `'use client'` nhập
 * (`e2e/unit/zod-phia-trinh-duyet.test.mjs`).
 */
import * as z from 'zod/mini';

import { NHAN_VAI } from './vaiTro';

const so = z.number();
const soNull = z.nullable(z.number());
const chu = z.string();
const chuNull = z.nullable(z.string());
const co = z.boolean();

const HD_NGUOI = z.nullable(z.looseObject({ id: soNull, ten: chuNull }));

export const HD_SU_KIEN = z.looseObject({
  id: so,
  kieu: chu,
  noiBo: co,
  ai: z.looseObject({ id: soNull, ten: chuNull, vai: chuNull }),
  tu: chuNull,
  den: chuNull,
  tuNhan: z.optional(chuNull),
  denNhan: z.optional(chuNull),
  noiDung: chuNull,
  luc: chuNull,
});
export type SuKien = z.infer<typeof HD_SU_KIEN>;

const HD_CO_THE = z.looseObject({
  traLoi: z.optional(co), ghiChu: z.optional(co), nhan: z.optional(co), moLai: z.optional(co),
  xong: z.optional(co), tuChoi: z.optional(co), huy: z.optional(co), duyet: z.optional(co),
  giao: z.optional(co), chuyenTiep: z.optional(co), phanLoai: z.optional(co),
});
export type CoThe = z.infer<typeof HD_CO_THE>;

export const HD_YEU_CAU = z.looseObject({
  id: so,
  loai: chu,
  loaiNhan: chu,
  nhom: chu,
  canDuyet: co,
  trangThai: chu,
  trangThaiNhan: chu,
  nguon: chu,
  tieuDe: chu,
  noiDung: chuNull,
  duLieu: z.record(z.string(), z.unknown()),
  ketQua: chuNull,
  hocVien: HD_NGUOI,
  lop: HD_NGUOI,
  buoi: z.nullable(z.looseObject({ id: so, luc: chuNull })),
  nguoiTao: HD_NGUOI,
  nguoiXuLy: HD_NGUOI,
  nguoiDuyet: HD_NGUOI,
  duyetLuc: chuNull,
  createdAt: chuNull,
  updatedAt: chuNull,
  closedAt: chuNull,
  thucThi: z.optional(z.nullable(z.record(z.string(), z.unknown()))),
  coThe: HD_CO_THE,
  suKien: z.optional(z.array(HD_SU_KIEN)),
});
export type YeuCau = z.infer<typeof HD_YEU_CAU>;

export const HD_DS = z.looseObject({ yeuCau: z.array(HD_YEU_CAU), coTheDuyet: z.optional(co) });
export type DanhSach = z.infer<typeof HD_DS>;

const HD_LOAI_TAO = z.looseObject({
  code: chu, nhan: chu, nhom: chu, canLop: co, canBuoi: co, canDuyet: co,
});
export type LoaiTao = z.infer<typeof HD_LOAI_TAO>;

/** `/api/yeu-cau/lua-chon` — học viên. */
export const HD_LUA_CHON_HV = z.looseObject({
  loai: z.array(HD_LOAI_TAO),
  lop: z.array(z.looseObject({ id: so, ten: chu, dangHoc: co })),
  buoi: z.array(z.looseObject({ id: so, classId: so, luc: chu, chuDe: chuNull, coBanGhi: co })),
});
export type LuaChonHV = z.infer<typeof HD_LUA_CHON_HV>;

/** `/api/teach/yeu-cau/lua-chon` — nhân sự. */
export const HD_LUA_CHON_NS = z.looseObject({
  loai: z.array(HD_LOAI_TAO),
  tatCaLoai: z.array(z.looseObject({ code: chu, nhan: chu, canDuyet: co, phanLoai: z.optional(co) })),
  trangThai: z.array(z.looseObject({ code: chu, nhan: chu })),
  lop: z.array(z.looseObject({ id: so, ten: chu })),
  /** Chỉ khi hỏi kèm `?class_id=` — em đang học + buổi đã diễn ra của lớp ấy. */
  hocVien: z.optional(z.array(z.looseObject({ id: so, ten: chu }))),
  buoi: z.optional(z.array(z.looseObject({ id: so, luc: chu, chuDe: chuNull }))),
});
export type LuaChonNS = z.infer<typeof HD_LUA_CHON_NS>;

/** `/api/public/phu-huynh/<chìa>/yeu-cau` — phụ huynh. */
export const HD_PHU_HUYNH = z.looseObject({
  yeuCau: z.array(HD_YEU_CAU),
  loai: z.array(HD_LOAI_TAO),
  tranMo: so,
});
export type PhuHuynhDS = z.infer<typeof HD_PHU_HUYNH>;

export const HD_XEM_TRUOC = z.looseObject({ cach: chu, moTa: chuNull, canhBao: z.array(chu) });
export type XemTruoc = z.infer<typeof HD_XEM_TRUOC>;

export const HD_NGUOI_NHAN = z.looseObject({
  nguoi: z.array(z.looseObject({ id: so, ten: chu, vai: chu })),
});
export const HD_LOP_CHUYEN = z.looseObject({
  lop: z.array(z.looseObject({ id: so, ten: chu, giaSu: co, mon: chuNull })),
});

/* ── Cách nói ──────────────────────────────────────────────────────────── */

/** Còn mở = chưa ai đóng (cùng bộ với `loai.MO` ở máy chủ, chỉ để tô màu). */
export function toneTrangThai(ma: string): 'brand' | 'warn' | 'good' | 'bad' | 'neutral' {
  if (ma === 'moi') return 'warn';
  if (ma === 'dang_xu_ly' || ma === 'da_duyet') return 'brand';
  if (ma === 'da_xong') return 'good';
  if (ma === 'tu_choi') return 'bad';
  return 'neutral';
}

/** Tên vai đọc được — `admin` không được lên màn (RULES §10). Phụ huynh đi nguyên chữ. */
export function nhanVaiNguoi(vai: string | null | undefined): string | null {
  if (!vai) return null;
  return NHAN_VAI[vai] ?? vai;
}

/** Nguồn → chữ ngắn cho dòng tóm tắt ở hộp nhân sự. */
export const NHAN_NGUON: Record<string, string> = {
  hoc_vien: 'Học viên gửi',
  phu_huynh: 'Phụ huynh gửi',
  tro_giang: 'Trợ giảng báo',
  giang_vien: 'Giảng viên gửi',
  hoc_vu: 'Học vụ tạo',
};

/** MỘT câu cho một dòng lịch sử. `noiDung` (trả lời, ghi chú, kết quả) in riêng bên dưới. */
export function cauSuKien(s: SuKien): string {
  const den = s.denNhan ?? s.den ?? '';
  switch (s.kieu) {
    case 'tao': return 'Gửi yêu cầu';
    case 'tra_loi': return 'Trả lời';
    case 'ghi_chu': return 'Ghi chú nội bộ';
    case 'trang_thai': return `Chuyển sang “${den}”`;
    case 'giao': return `Giao cho ${den || 'học vụ'}`;
    case 'chuyen_tiep': return `Chuyển tiếp cho ${den || 'học vụ'}`;
    case 'duyet': return 'Duyệt yêu cầu';
    case 'thuc_thi': return 'Hệ thống đã làm';
    case 'tu_choi': return 'Từ chối';
    case 'loi': return 'Duyệt không thành';
    case 'phan_loai': return `Đổi loại: ${s.tuNhan ?? s.tu ?? ''} → ${den}`;
    default: return 'Cập nhật';
  }
}

/** Nhóm loại cho ô chọn khi gửi — thứ tự theo việc người gửi hay cần. */
export const NHOM_LOAI: { ma: string; nhan: string }[] = [
  { ma: 'hoi_dap', nhan: 'Hỏi giảng viên, trợ giảng' },
  { ma: 'ho_tro', nhan: 'Cần trung tâm hỗ trợ' },
  { ma: 'bao_loi', nhan: 'Bản ghi buổi học bị lỗi' },
  { ma: 'bao_cao', nhan: 'Báo lên giảng viên, học vụ' },
  { ma: 'thay_doi', nhan: 'Xin thay đổi việc học (cần học vụ duyệt)' },
];

/** Khoá `duLieu` hiện trên thẻ chi tiết (nhân sự) — nhãn người đọc. */
export const NHAN_DU_LIEU: Record<string, string> = {
  sdt: 'Số điện thoại liên hệ',
  ngay_mong_muon: 'Ngày mong muốn',
  lop_mong_muon: 'Lớp / lịch mong muốn',
  den_ngay: 'Bảo lưu tới ngày',
  den_lop_id: 'Lớp muốn chuyển tới (mã lớp)',
  khong_phan_hoi: 'Em không phản hồi',
};

export const O_CHU =
  'w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 py-2 text-input text-ink placeholder:text-ink-3/70 focus:outline-2 focus:outline-brand';
export const O_CHON =
  'min-h-11 w-full rounded-md border border-line-input bg-sunken px-3 text-input text-ink focus:outline-2 focus:outline-brand';
