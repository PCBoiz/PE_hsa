/**
 * Đọc một ô chữ ra khỏi `FormData`.
 *
 * VÌ SAO KHÔNG DÙNG `String(f.get('x') || '')`. `FormData.get()` trả
 * `string | File | null`, và `String(mộtFile)` ra đúng chuỗi
 * **`"[object File]"`** — 15 ký tự, truthy, đi lọt mọi phép kiểm "có nhập chưa"
 * rồi vào thẳng máy chủ. Cùng họ với lỗi `[object Object]` đã hiện lên banner
 * đỏ trước mặt trợ giảng (T22).
 *
 * Chưa ai gặp: các biểu mẫu hiện tại chỉ có ô chữ. Nhưng hàng rào duy nhất đang
 * giữ chỗ đó là "không ai thêm một ô `type=file` trùng tên" — mà một hàng rào
 * phụ thuộc vào việc người sau không làm gì thì không phải hàng rào.
 *
 * Trả chuỗi RỖNG cho `File`: ô chữ nhận một tệp là chuyện không có nghĩa, và
 * "rỗng" đi qua đúng nhánh "chưa nhập" mà biểu mẫu đã có sẵn.
 */
export function oChu(f: FormData, ten: string): string {
  const v = f.get(ten);
  return typeof v === 'string' ? v : '';
}
