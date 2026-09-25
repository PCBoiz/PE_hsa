/**
 * BỘ LỌC màn Tài khoản — hàm THUẦN, tách khỏi React để trang máy chủ và màn trình
 * duyệt dùng CÙNG một bản (và để kiểm được bằng `e2e/unit/loc-tai-khoan.test.mjs`).
 *
 * Hai nơi đọc: `page.tsx` (máy chủ — đọc URL, dựng sẵn trang đầu) và
 * `AccountsClient.tsx` (trình duyệt — gõ tới đâu lọc tới đó, ghi lại lên URL). Không
 * được import từ tệp `'use client'`: trang máy chủ gọi hàm ở đó là lỗi lúc chạy.
 *
 * Tham số URL = tham số API (`q`, `role`, `status`, `class_id`, `chua_xep_lop`,
 * `khong_hoat_dong`, `tinh_trang_hoc`, `hoc_phi`) — một bảng tên, không dịch hai lần.
 *
 * "Chưa xếp lớp" (1.4b) là một lựa chọn của ô Lớp chứ không phải ô riêng: nó và "lớp X"
 * loại trừ nhau, và ít ô lọc hơn là ít chữ hơn (góp ý TopHSA: màn đầu rối).
 */
export type LocTaiKhoan = {
  q: string;
  role: string;
  status: string;
  /** '' = tất cả · `CHUA_XEP_LOP` · hoặc id lớp. */
  lop: string;
  /** '' = tất cả · số ngày (một mốc trong `nguongNgu` của máy chủ). */
  khongHoatDong: string;
  /** V-m: '' = tất cả · mã tình trạng học tập (`tinhTrangHocOptions` của máy chủ). */
  tinhTrangHoc: string;
  /** V-m: '' = tất cả · mã học phí · `HOC_PHI_CHUA_DAT` (ô trống). */
  hocPhi: string;
};

/** Giá trị ô lọc "Học phí" = chưa đặt — khớp `admin_users.HOC_PHI_CHUA_DAT`. */
export const HOC_PHI_CHUA_DAT = 'chua_dat';

export const CHUA_XEP_LOP = 'chua-xep-lop';

export const LOC_RONG: LocTaiKhoan = {
  q: '', role: '', status: '', lop: '', khongHoatDong: '', tinhTrangHoc: '', hocPhi: '',
};

/** Tham số URL → bộ lọc. `lay(k)` trả chuỗi đã cắt khoảng trắng, thiếu thì ''. */
export function docLoc(lay: (k: string) => string): LocTaiKhoan {
  return {
    q: lay('q'),
    role: lay('role'),
    status: lay('status'),
    lop: lay('chua_xep_lop') === '1' ? CHUA_XEP_LOP : lay('class_id'),
    khongHoatDong: lay('khong_hoat_dong'),
    tinhTrangHoc: lay('tinh_trang_hoc'),
    hocPhi: lay('hoc_phi'),
  };
}

/** Bộ lọc → tham số API (cũng là tham số URL). Ô trống thì không gửi. */
export function thamSoLoc(loc: LocTaiKhoan): URLSearchParams {
  const sp = new URLSearchParams();
  if (loc.q.trim()) sp.set('q', loc.q.trim());
  if (loc.role) sp.set('role', loc.role);
  if (loc.status) sp.set('status', loc.status);
  if (loc.lop === CHUA_XEP_LOP) sp.set('chua_xep_lop', '1');
  else if (loc.lop) sp.set('class_id', loc.lop);
  if (loc.khongHoatDong) sp.set('khong_hoat_dong', loc.khongHoatDong);
  if (loc.tinhTrangHoc) sp.set('tinh_trang_hoc', loc.tinhTrangHoc);
  if (loc.hocPhi) sp.set('hoc_phi', loc.hocPhi);
  return sp;
}

/** Nhãn tình trạng học tập / học phí khi máy chủ chưa gửi danh sách (backend cũ) — ĐƯỜNG LÙI;
 *  nguồn là `backend/teaching/tinh_trang.py`, máy chủ gửi `tinhTrangHocOptions`/`hocPhiOptions`. */
export const TINH_TRANG_HOC_DUONG_LUI: { ma: string; nhan: string }[] = [
  { ma: 'dang_hoc', nhan: 'Đang học' },
  { ma: 'tam_dung', nhan: 'Tạm dừng' },
  { ma: 'da_hoc_xong', nhan: 'Đã học xong' },
  { ma: 'bao_luu', nhan: 'Bảo lưu' },
  { ma: 'da_nghi', nhan: 'Đã nghỉ' },
  { ma: 'chua_xep_lop', nhan: 'Chưa xếp lớp' },
];
export const HOC_PHI_DUONG_LUI: { ma: string; nhan: string }[] = [
  { ma: 'da_dong', nhan: 'Đã đóng' },
  { ma: 'sap_het', nhan: 'Sắp hết' },
  { ma: 'het', nhan: 'Hết' },
  { ma: 'bao_luu', nhan: 'Bảo lưu' },
];

/** Mốc "lâu không vào" khi máy chủ chưa gửi `nguongNgu` (backend cũ). ĐƯỜNG LÙI, không
 *  phải nguồn sự thật — nguồn là `NGUONG_NGU` ở `teaching/overview.py`, cùng mốc thẻ
 *  "Tài khoản lâu không vào" của Tổng quan. */
export const NGUONG_NGU_DUONG_LUI = [7, 14, 30];

/**
 * Số ngày từ lần hoạt động cuối → chữ ngắn cho cột "Hoạt động cuối".
 *  · `undefined` — máy chủ không gửi khoá (backend cũ): "—", KHÔNG phải "chưa vào";
 *  · `null` — chưa thấy vào lần nào (không đăng nhập, không làm bài): "chưa vào".
 */
export function nhanHoatDong(ngay: number | null | undefined): string {
  if (ngay === undefined) return '—';
  if (ngay === null) return 'chưa vào';
  if (ngay <= 0) return 'hôm nay';
  if (ngay === 1) return 'hôm qua';
  return `${ngay} ngày trước`;
}
