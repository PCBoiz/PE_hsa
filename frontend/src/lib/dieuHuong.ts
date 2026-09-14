/**
 * Điều hướng TẢI LẠI CẢ TRANG — có chủ đích, không phải quên dùng `useRouter`.
 *
 * Từ `eslint-config-next` 16.3, luật `no-location-assign-relative-destination`
 * báo mọi `location.href = '/…'`: nó bỏ qua điều hướng mềm của Next. Ở sản phẩm
 * này có ba lý do CẦN tải lại thật, và mỗi chỗ gọi hàm này thuộc một trong ba:
 *
 * 1. Trang đích chạy tầng JS cũ (`public/static/js`): các tệp ấy khởi động đúng
 *    một lần mỗi lượt tải trang. Điều hướng mềm vào `/dashboard` hay `/lesson`
 *    để lại cái vỏ không ai đổ dữ liệu.
 * 2. Đích là route handler chứ không phải trang (`/auth/logout`).
 * 3. Cố ý vứt trạng thái trong bộ nhớ: vừa đổi mật khẩu, phiên hết (401), bị buộc
 *    đổi mật khẩu lần đầu.
 *
 * Luật vẫn BẬT cho phần còn lại của `src`: mã React mới đi giữa hai trang React
 * thì dùng `<Link>` / `useRouter().push()`, còn cần tải lại thì gọi hàm này —
 * và chỗ gọi tự nói lên ý định.
 */
export function taiTrang(duongDan: string): void {
  window.location.assign(duongDan);
}
