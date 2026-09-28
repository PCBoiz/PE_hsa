/**
 * 34 đơn vị hành chính cấp tỉnh sau sáp nhập 2025 — ô "Tỉnh/Thành phố" của hồ sơ học viên.
 *
 * BẢN CHÉP của `backend/teaching/tinh_thanh.py` (nguồn và lý do ở đó). Hai danh sách phải
 * GIỐNG HỆT, cùng thứ tự — `e2e/unit/tinh-thanh.test.mjs` đọc cả hai tệp và so từng tên.
 * Sửa một bên mà quên bên kia thì máy chủ từ chối đúng giá trị ô chọn vừa gửi.
 */
export const TINH_THANH: readonly string[] = [
  'Hà Nội',
  'Thành phố Hồ Chí Minh',
  'Hải Phòng',
  'Đà Nẵng',
  'Cần Thơ',
  'Huế',
  'An Giang',
  'Bắc Ninh',
  'Cà Mau',
  'Cao Bằng',
  'Đắk Lắk',
  'Điện Biên',
  'Đồng Nai',
  'Đồng Tháp',
  'Gia Lai',
  'Hà Tĩnh',
  'Hưng Yên',
  'Khánh Hòa',
  'Lai Châu',
  'Lạng Sơn',
  'Lào Cai',
  'Lâm Đồng',
  'Nghệ An',
  'Ninh Bình',
  'Phú Thọ',
  'Quảng Ngãi',
  'Quảng Ninh',
  'Quảng Trị',
  'Sơn La',
  'Tây Ninh',
  'Thái Nguyên',
  'Thanh Hóa',
  'Tuyên Quang',
  'Vĩnh Long',
] as const;

/** Giá trị đang lưu có nằm trong danh sách không — ngoài danh sách là ô chữ tự do CŨ. */
export function laTinhThanh(v: string | null | undefined): boolean {
  return !!v && TINH_THANH.includes(v);
}
