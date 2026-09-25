/**
 * KHUNG CHƯƠNG TRÌNH & TIẾN ĐỘ (E1, 25/09/2026) — hình dạng phản hồi và cách nói tiến độ.
 *
 * Một nơi cho mọi màn đọc tiến độ (danh sách lớp, Tổng quan, Lớp của tôi, tờ phụ huynh,
 * màn Chương trình lớp): cùng một câu cho cùng một con số. Ngưỡng "chậm" KHÔNG gõ lại ở
 * đây — máy chủ tính cờ `cham` (`chuong_trinh/tien_do.py`), màn hình chỉ đọc.
 *
 * Mọi khoá mới trên phản hồi của miền khác là TUỲ CHỌN (`z.optional`): máy chủ cũ chưa có khoá
 * thì màn hình vẫn dựng, chỉ không có dòng tiến độ.
 */
import * as z from 'zod/mini';

const so = z.number();
const soNull = z.nullable(z.number());
const chu = z.string();
const chuNull = z.nullable(z.string());

/** Tiến độ GỌN của một lớp — khoá `chuongTrinh` ở danh sách lớp và Tổng quan. */
export const HD_TIEN_DO_GON = z.optional(z.nullable(z.looseObject({
  pct: soNull,
  keHoachPct: soNull,
  treBuoi: soNull,
  cham: z.boolean(),
  chuaGhiSo: so,
})));
export type TienDoGon = z.infer<typeof HD_TIEN_DO_GON>;

/** % của MỘT em — khoá `chuongTrinh` ở Lớp của tôi và tờ phụ huynh. */
export const HD_TIEN_DO_EM = z.optional(z.nullable(z.looseObject({
  pct: soNull,
  keHoachPct: soNull,
})));
export type TienDoEm = z.infer<typeof HD_TIEN_DO_EM>;

/** Khối tiến độ ở Tổng quan trung tâm. */
export const HD_TONG_CHUONG_TRINH = z.optional(z.nullable(z.looseObject({
  lopCoKhung: so,
  lopCham: so,
  lopChuaGhiSo: so,
  buoiChuaGhiSo: so,
})));

export { cauTienDoEm, chipTienDo, phanTram } from './tienDoChu';

/* ── Màn soạn khung ─────────────────────────────────────────────────────── */

const HD_PHIEN_BAN = z.looseObject({
  id: so, name: chu, status: chu, statusLabel: chu, chuoi: so,
  soBuoi: so, soLop: so, isDemo: z.optional(z.boolean()), createdAt: chu,
});
export type PhienBan = z.infer<typeof HD_PHIEN_BAN>;

export const HD_MUC_LUC = z.looseObject({
  mon: z.array(z.looseObject({ id: chu, title: chu, versions: z.array(HD_PHIEN_BAN) })),
  trangThai: z.array(z.looseObject({ ma: chu, nhan: chu })),
  loaiMuc: z.array(z.looseObject({ ma: chu, nhan: chu })),
});
export type MucLuc = z.infer<typeof HD_MUC_LUC>;

export const HD_CAY = z.looseObject({
  id: so, courseId: chu, name: chu, status: chu,
  sessions: z.array(z.looseObject({
    id: so, sortOrder: so, name: chu, durationMinutes: soNull, homework: chuNull,
    items: z.array(z.looseObject({
      id: so, sortOrder: so, kind: chu, lessonId: soNull, title: chu, weight: so,
    })),
    materials: z.array(z.looseObject({
      id: so, title: chu, fileUrl: chuNull, fileType: chuNull, sortOrder: so,
    })),
  })),
});
export type Cay = z.infer<typeof HD_CAY>;

export const HD_OK = z.looseObject({ ok: z.boolean() });
export const HD_TAO = z.looseObject({ ok: z.boolean(), id: so });

/* ── Chương trình của một lớp ───────────────────────────────────────────── */

const HD_TIEN_DO_LOP = z.looseObject({
  tongTrongSo: so, phaiXong: so, daXong: so, treBuoi: soNull, tiLe: soNull, pct: soNull,
  keHoachPct: soNull, cham: z.boolean(), soBuoiKhung: so, soBuoiDenHan: so,
  buoiDaDay: so, chuaGhiSo: so,
  nguong: z.looseObject({ treBuoi: so, tiLe: so }),
});

export const HD_CT_LOP = z.looseObject({
  class: z.looseObject({ id: so, name: chu, code: chuNull, courseId: chuNull, courseTitle: chuNull }),
  khung: z.nullable(z.looseObject({ versionId: so, name: chu, status: chu, statusLabel: chu })),
  buoiKhung: z.array(z.looseObject({
    id: so, soBuoi: so, name: chu, durationMinutes: soNull, homework: chuNull,
    pctDaDay: soNull,
    items: z.array(z.looseObject({ id: so, kind: chu, kindLabel: chu, title: chu, weight: so })),
  })),
  buoi: z.array(z.looseObject({
    id: so, startsAt: chu, status: chu, topic: chuNull, started: z.boolean(),
    makeupFor: z.optional(soNull), syllabusSessionId: soNull, soBuoi: soNull, lechBan: z.boolean(),
    soDauBai: z.nullable(z.looseObject({
      loggedAt: chu, comprehension: soNull, xong: so, motPhan: so, chua: so,
    })),
  })),
  tienDo: z.optional(z.nullable(HD_TIEN_DO_LOP)),
  tungEm: z.array(z.looseObject({ userId: so, name: chu, pct: soNull })),
  quyen: z.looseObject({ nhanKhung: z.boolean(), ganBuoi: z.boolean() }),
  luaChon: z.optional(z.array(z.looseObject({
    versionId: so, name: chu, courseId: chu, courseTitle: chuNull, soBuoi: so,
  }))),
});
export type CtLop = z.infer<typeof HD_CT_LOP>;

export const HD_NHAN_KHUNG = z.looseObject({
  ok: z.boolean(), dryRun: z.boolean(), doiBan: z.boolean(),
  khung: z.looseObject({ name: chu }),
  ganMoi: z.array(z.looseObject({ sessionId: so, startsAt: chu, soBuoi: so, name: chu })),
  giuNguyen: so, dichSang: so, boGan: so, dienTen: so, boQuaBuoiHuy: so, boQuaBuoiBu: so,
  buoiThua: z.array(z.looseObject({ sessionId: so, startsAt: chu, topic: chuNull })),
  khungThieu: z.array(z.looseObject({ soBuoi: so, name: chu })),
});
export type NhanKhung = z.infer<typeof HD_NHAN_KHUNG>;

/* ── Sổ đầu bài ─────────────────────────────────────────────────────────── */

const HD_MUC_SO = z.looseObject({
  itemId: so, label: chu, kind: z.optional(chu), weight: z.optional(so), soBuoi: z.optional(soNull),
  status: chuNull, note: chuNull, ngoaiBan: z.optional(z.boolean()),
});
export type MucSo = z.infer<typeof HD_MUC_SO>;

export const HD_SO_DAU_BAI = z.looseObject({
  session: z.looseObject({
    id: so, classId: so, className: chu, startsAt: chu, durationMinutes: soNull,
    topic: chuNull, status: chu, note: chuNull, started: z.boolean(),
  }),
  lopCoKhung: z.boolean(),
  buoiKhung: z.nullable(z.looseObject({ id: so, soBuoi: soNull, name: chu, homework: chuNull })),
  buBuoiGoc: chuNull,
  mucKeHoach: z.array(HD_MUC_SO),
  mucNgoaiKeHoach: z.array(HD_MUC_SO),
  mucTuThem: z.array(z.looseObject({ label: chu, status: chu, note: chuNull })),
  mucKhac: z.array(z.looseObject({ itemId: so, soBuoi: soNull, label: chu, kind: chu })),
  soDauBai: z.nullable(z.looseObject({
    comprehension: soNull, deXuat: chuNull, loggedAt: chu, loggedBy: chuNull,
  })),
  hocVien: z.array(z.looseObject({
    userId: so, name: chu, diemDanh: chuNull, canHoTro: z.boolean(), ghiChu: chuNull,
  })),
  trangThaiMuc: z.array(z.looseObject({ ma: chu, nhan: chu })),
  ghiDuoc: z.boolean(),
});
export type SoDauBai = z.infer<typeof HD_SO_DAU_BAI>;
