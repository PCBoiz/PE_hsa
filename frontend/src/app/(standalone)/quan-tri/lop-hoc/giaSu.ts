/**
 * TẠO NHANH LỚP GIA SƯ (mục 1.2b, 24/09/2026) — phần THUẦN: kiểm biểu mẫu, dựng thân
 * request cho `POST /api/admin/classes/gia-su`. Tách khỏi `TaoLopGiaSu.tsx` để
 * `e2e/unit/lop-gia-su.test.mjs` chạy được bằng Node trần.
 *
 * Kiểm ở đây chỉ để nói lỗi SỚM, đúng ô; máy chủ vẫn kiểm lại đủ (`lop_gia_su.py`,
 * `sinh_buoi._doc_than`) — câu lỗi hai bên giữ cùng ý để người dùng không thấy hai
 * cách nói cho một chuyện.
 */

export type FormGiaSu = {
  /** Em đã chọn trong ô tìm — `null` là chưa chọn. */
  emId: number | null;
  /** '' = chưa chọn. */
  giangVienId: string;
  /** '' = cả ba môn. */
  monHoc: string;
  /** '' = chưa thuộc đợt nào. */
  dotHoc: string;
  /** Để trống → máy chủ đặt "Gia sư · {em} · {giảng viên}". */
  ten: string;
  sinhBuoi: boolean;
  /** Thứ theo ISO: 1 = Thứ 2 … 7 = Chủ nhật — cùng quy ước với sinh lịch. */
  thu: number[];
  gio: string;
  phut: string;
  tu: string;
  den: string;
};

export const THU: { so: number; nhan: string }[] = [
  { so: 1, nhan: 'T2' }, { so: 2, nhan: 'T3' }, { so: 3, nhan: 'T4' }, { so: 4, nhan: 'T5' },
  { so: 5, nhan: 'T6' }, { so: 6, nhan: 'T7' }, { so: 7, nhan: 'CN' },
];

/** Cùng trần với `teaching/sessions.py::MAX_SESSION_MINUTES`. */
export const TRAN_PHUT = 600;

/** Ngày `YYYY-MM-DD` cộng thêm `n` ngày (theo lịch, không theo múi giờ). */
export function congNgay(ngay: string, n: number): string {
  const d = new Date(`${ngay}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

/** Biểu mẫu trống: lịch sinh từ hôm nay, 12 tuần — một đợt gia sư điển hình. */
export function formGiaSuRong(homNay: string): FormGiaSu {
  return {
    emId: null, giangVienId: '', monHoc: '', dotHoc: '', ten: '',
    sinhBuoi: true, thu: [], gio: '19:30', phut: '90', tu: homNay, den: congNgay(homNay, 83),
  };
}

export function thanGiaSu(
  f: FormGiaSu,
  dryRun: boolean,
): { body: Record<string, unknown> | null; loi: string | null } {
  const hong = (loi: string) => ({ body: null, loi });
  if (!f.emId) return hong('Chọn học viên cho lớp gia sư.');
  if (!f.giangVienId) return hong('Chọn giảng viên dạy lớp gia sư.');
  const body: Record<string, unknown> = {
    student_id: f.emId,
    teacher_id: Number(f.giangVienId),
    course_id: f.monHoc || null,
    term_id: f.dotHoc ? Number(f.dotHoc) : null,
    name: f.ten.trim() || null,
    dry_run: dryRun,
  };
  if (!f.sinhBuoi) return { body, loi: null };

  if (f.thu.length === 0) return hong('Chọn ít nhất một thứ trong tuần.');
  if (!/^([01]?\d|2[0-3]):[0-5]\d$/.test(f.gio.trim())) return hong('Giờ bắt đầu phải có dạng HH:MM, ví dụ 19:30.');
  const phut = Number(f.phut);
  // `Number.isInteger`, không `typeof`: `Number('90 phút')` là NaN — xem `lop-hoc.test.mjs`.
  if (!Number.isInteger(phut) || phut <= 0 || phut > TRAN_PHUT) {
    return hong(`Độ dài buổi học phải là số phút nguyên, 1–${TRAN_PHUT}.`);
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(f.tu) || !/^\d{4}-\d{2}-\d{2}$/.test(f.den)) {
    return hong('Chọn ngày bắt đầu và ngày kết thúc lịch.');
  }
  if (f.tu > f.den) return hong('Ngày kết thúc phải sau ngày bắt đầu.');
  Object.assign(body, {
    generate: true,
    weekdays: [...new Set(f.thu)].sort((a, b) => a - b),
    start_time: f.gio.trim(),
    duration_minutes: phut,
    from: f.tu,
    to: f.den,
    // Ngày khai giảng của lớp = buổi đầu của lịch; ngày kết thúc để trống — lớp gia sư
    // thường học tiếp sau đợt lịch đầu, sinh thêm buổi ở màn Buổi học.
    starts_on: f.tu,
  });
  return { body, loi: null };
}
