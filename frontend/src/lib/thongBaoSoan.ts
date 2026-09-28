/**
 * MÀN SOẠN THÔNG BÁO (§61, bảng TopHSA dòng 20 + 27) — hình dạng của hai cụm cửa:
 *
 *   `/api/teach/classes/<id>/thong-bao` (+ `/preview`)  — giảng viên & TRỢ GIẢNG, lớp mình
 *   `/api/admin/thong-bao` (+ `/preview`, `/<id>/gui`, `/<id>/huy`)  — học vụ & quản trị
 *
 * Tách khỏi `lib/thongBao.ts` có chủ đích: tệp ấy là hình dạng của CHUÔNG (`/feed`, thứ
 * người nhận đọc), tệp này là hình dạng của Ô SOẠN (thứ người gửi viết). Hai cửa khác
 * nhau, hai nhóm người dùng khác nhau, và gộp lại thì mỗi lần backend đổi một cửa là cả
 * hai màn phải đọc lại.
 *
 * `zod/mini`: cả trang máy chủ lẫn component `'use client'` đều nhập tệp này
 * (`e2e/unit/zod-phia-trinh-duyet.test.mjs`).
 *
 * DANH MỤC ĐỐI TƯỢNG (lớp, môn) do MÁY CHỦ trả — `chon` trong `GET /api/admin/thong-bao`,
 * dựng từ `courses.truy_cap.BA_MON` + `courses.title`. Màn hình KHÔNG gõ lại (RULES §7):
 * một bảng ba môn chép sang React sẽ trôi khỏi backend ngay lần TopHSA mở môn thứ tư.
 */
import * as z from 'zod/mini';

const so = z.number();
const soNull = z.nullable(z.number());
const chu = z.string();
const chuNull = z.nullable(z.string());

/** Trần độ dài — CÙNG con số với `notifications/thong_bao.py` (TRAN_TIEU_DE / TRAN_NOI_DUNG).
 *
 *  Đây là hai nguồn cho cùng một số, và đó là điều RULES §7 cấm — nên phải nói rõ nó được
 *  giữ khớp bằng cái gì: `maxLength` ở đây chỉ để trình duyệt CHẶN TRƯỚC khi gửi, còn luật
 *  thật vẫn ở máy chủ và nó trả `errors.title` / `errors.body` nếu lệch. Lệch thì người
 *  dùng thấy câu của máy chủ, không thấy màn hình im lặng cắt chữ của họ. */
export const TRAN_TIEU_DE = 200;
export const TRAN_NOI_DUNG = 5000;

const HD_AI = z.looseObject({ id: so, name: chuNull });

/** Bản XEM TRƯỚC người nhận — `POST …/preview`. Không ghi gì. */
export const HD_XEM_TRUOC = z.looseObject({
  tong: so,
  chuong: so,
  /** Số em sẽ nhận EMAIL nếu bấm Gửi NGAY LÚC NÀY (0 khi ô "gửi kèm email" đang tắt). */
  email: so,
  tatEmail: so,
  mau: so,
  thieuEmail: z.array(HD_AI),
  zalo: z.looseObject({ sanSang: z.boolean(), lyDo: chuNull, coSo: so }),
  danhSach: z.array(HD_AI),
});
export type XemTruoc = z.infer<typeof HD_XEM_TRUOC>;

export const HD_DOI_TUONG = z.looseObject({
  classIds: z.optional(z.array(so)),
  courseIds: z.optional(z.array(chu)),
  userIds: z.optional(z.array(so)),
  groupName: z.optional(chu),
});
export type DoiTuong = z.infer<typeof HD_DOI_TUONG>;

/** Một thông báo đã soạn (nháp, đã gửi, hoặc đã huỷ). */
export const HD_MOT = z.looseObject({
  id: so,
  title: chuNull,
  body: chuNull,
  audience: HD_DOI_TUONG,
  sendEmail: z.boolean(),
  sendZalo: z.boolean(),
  status: chu,
  recipientCount: soNull,
  createdAt: chuNull,
  sentAt: chuNull,
  createdByName: chu,
  /** Số thư ĐÃ RA KHỎI hộp thư đi (§61) — khác `recipientCount`, là số người nhận chuông. */
  daGuiThu: so,
  daDoc: so,
});
export type MotThongBao = z.infer<typeof HD_MOT>;

/** `GET /api/teach/classes/<id>/thong-bao` — chỉ danh sách của lớp ấy. */
export const HD_DS_LOP = z.looseObject({ items: z.array(HD_MOT) });
export type DsLop = z.infer<typeof HD_DS_LOP>;

export const HD_LOP_CHON = z.looseObject({
  id: so, name: chu, code: chuNull, status: chu, soEm: so,
});
export type LopChon = z.infer<typeof HD_LOP_CHON>;

/** `GET /api/admin/thong-bao` — danh sách + danh mục đối tượng + trạng thái Zalo. */
export const HD_TRANG_TRUNG_TAM = z.looseObject({
  items: z.array(HD_MOT),
  chon: z.looseObject({
    lop: z.array(HD_LOP_CHON),
    mon: z.array(z.looseObject({ id: chu, nhan: chu })),
  }),
  zalo: z.looseObject({ sanSang: z.boolean(), lyDo: chuNull }),
});
export type TrangTrungTam = z.infer<typeof HD_TRANG_TRUNG_TAM>;

/** Trả lời của POST soạn / `…/gui` / `…/huy`. */
export const HD_DA_SOAN = z.looseObject({
  id: so,
  status: chu,
  recipientCount: z.optional(so),
});
export type DaSoan = z.infer<typeof HD_DA_SOAN>;

/**
 * Trạng thái → chữ người đọc. Ba giá trị này bị CHECK của lược đồ ghim
 * (`announcements_status_check`: draft / sent / cancelled), nên bảng ở đây là ĐỦ; giá trị
 * lạ vẫn có đường ra chứ không hiện mã kỹ thuật (RULES §10).
 */
const TRANG_THAI: Record<string, { nhan: string; tone: 'brand' | 'neutral' | 'good' | 'bad' }> = {
  draft: { nhan: 'Bản nháp', tone: 'brand' },
  sent: { nhan: 'Đã gửi', tone: 'good' },
  cancelled: { nhan: 'Đã huỷ', tone: 'bad' },
};

export function nhanTrangThai(tt: string): { nhan: string; tone: 'brand' | 'neutral' | 'good' | 'bad' } {
  return TRANG_THAI[tt] ?? { nhan: 'Chưa rõ trạng thái', tone: 'neutral' };
}

/**
 * Câu tóm tắt đối tượng nhận, cho DÒNG trong danh sách.
 *
 * Nhận `tenLop` là một bảng tra id → tên do máy chủ trả; thiếu tên thì nói "1 lớp" chứ
 * KHÔNG in `#7586` — một con số kỹ thuật trên màn học vụ là thứ không ai đọc được
 * (RULES §10). Bản đầu in id và trông hoàn toàn bình thường với người viết mã.
 */
export function moTaDoiTuong(
  aud: DoiTuong,
  tenLop: Map<number, string>,
  tenMon: Map<string, string>,
): string {
  const phan: string[] = [];
  const lop = aud.classIds ?? [];
  const mon = aud.courseIds ?? [];
  const nguoi = aud.userIds ?? [];
  if (lop.length) {
    const ten = lop.map((id) => tenLop.get(id)).filter(Boolean) as string[];
    phan.push(ten.length === lop.length ? ten.join(', ') : `${lop.length} lớp`);
  }
  if (mon.length) {
    const ten = mon.map((m) => tenMon.get(m) ?? m);
    phan.push(`môn ${ten.join(', ')}`);
  }
  if (nguoi.length) phan.push(aud.groupName || `${nguoi.length} người chọn riêng`);
  return phan.join(' · ') || 'Chưa chọn ai';
}

/**
 * Câu của ô XEM TRƯỚC: "sẽ báo cho N em, M em nhận email".
 *
 * Nói cả phần KHÔNG nhận được gì thêm, vì đó là thứ người gửi cần biết TRƯỚC khi bấm Gửi:
 * em tắt nhận thư, em thiếu địa chỉ, em dữ liệu mẫu. Bản chỉ nói "3 em" thì người gửi tin
 * là cả ba đều nhận được thư và không gọi điện cho ai.
 */
export function cauXemTruoc(d: XemTruoc, guiEmail: boolean): string {
  if (d.tong === 0) return 'Chưa em nào đang học trong phạm vi này — bấm Gửi thì không ai nhận được.';
  const cau = [`Sẽ báo cho ${d.tong} em qua chuông trong ứng dụng`];
  if (guiEmail) {
    cau.push(`${d.email} em nhận email`);
    if (d.tatEmail > 0) cau.push(`${d.tatEmail} em đã tắt nhận thư`);
    if (d.thieuEmail.length > 0) cau.push(`${d.thieuEmail.length} em chưa có địa chỉ thư`);
    if (d.mau > 0) cau.push(`${d.mau} em dữ liệu mẫu — không gửi thư`);
  } else {
    cau.push('không gửi email (ô "Gửi kèm email" đang tắt)');
  }
  return `${cau.join(', ')}.`;
}
