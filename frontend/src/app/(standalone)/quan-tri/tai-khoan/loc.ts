/**
 * BỘ LỌC màn Tài khoản — hàm THUẦN, tách khỏi React để trang máy chủ và màn trình
 * duyệt dùng CÙNG một bản (và để kiểm được bằng `e2e/unit/loc-tai-khoan.test.mjs`).
 *
 * Hai nơi đọc: `page.tsx` (máy chủ — đọc URL, dựng sẵn trang đầu) và
 * `AccountsClient.tsx` (trình duyệt — gõ tới đâu lọc tới đó, ghi lại lên URL). Không
 * được import từ tệp `'use client'`: trang máy chủ gọi hàm ở đó là lỗi lúc chạy.
 *
 * Tham số URL = tham số API (`q`, `role`, `status`, `class_id`, `chua_xep_lop`,
 * `khong_hoat_dong`) — một bảng tên, không dịch hai lần.
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
};

export const CHUA_XEP_LOP = 'chua-xep-lop';

export const LOC_RONG: LocTaiKhoan = { q: '', role: '', status: '', lop: '', khongHoatDong: '' };

/** Tham số URL → bộ lọc. `lay(k)` trả chuỗi đã cắt khoảng trắng, thiếu thì ''. */
export function docLoc(lay: (k: string) => string): LocTaiKhoan {
  return {
    q: lay('q'),
    role: lay('role'),
    status: lay('status'),
    lop: lay('chua_xep_lop') === '1' ? CHUA_XEP_LOP : lay('class_id'),
    khongHoatDong: lay('khong_hoat_dong'),
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
  return sp;
}

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
