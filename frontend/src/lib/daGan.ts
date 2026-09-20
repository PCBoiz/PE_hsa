import { useSyncExternalStore } from 'react';

const khongDoi = () => () => {};

/**
 * `false` trong HTML máy chủ dựng và trong lượt hydrate đầu, `true` ngay sau đó.
 *
 * Dùng để KHOÁ nút gửi của biểu mẫu có mật khẩu cho tới khi React gắn xong:
 * theo đặc tả HTML, biểu mẫu có nút mặc định bị `disabled` thì Enter không gửi
 * ngầm — không có hàng rào này, Enter trước khi hydrate là trình duyệt gửi GET
 * kiểu mặc định, mọi ô thành tham số URL. Đo trên production 20/09/2026
 * (điện thoại, Render lạnh): `/login?email=…&password=…`.
 *
 * `useSyncExternalStore` chứ không phải `useEffect(() => setState(true))`: cùng
 * kết quả, nhưng không phải một lượt dựng lại do effect (luật
 * `react-hooks/set-state-in-effect`), và React tự lo hai bản chụp máy chủ/máy khách.
 */
export function useDaGan(): boolean {
  return useSyncExternalStore(khongDoi, () => true, () => false);
}
