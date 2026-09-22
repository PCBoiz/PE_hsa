// Cấu hình Playwright cho bộ e2e của pe_hsa.
//
// Bản trước mô tả nó là "bộ e2e regression engine chấm SQL, port từ test_e2.py
// bản Flask" và trỏ `baseURL` vào cổng **3000** — cả hai đều của PE_test, chép
// sang khi tách repo. pe_hsa chạy Next ở **3100**, và engine chấm SQL không tồn
// tại ở đây. Hai spec DB Design đã xoá 05/09/2026.
//
// Yêu cầu chạy: Django cổng 9000 + Next cổng 3100.
//   cd backend  && .venv/Scripts/python manage.py runserver 9000 --noreload
//   cd frontend && pnpm dev
//   cd frontend && pnpm e2e
//
// Phép kiểm cần đăng nhập sẽ TỰ BỎ QUA kèm lý do khi chưa có tài khoản
// (E2E_EMAIL/E2E_PASSWORD) — bỏ qua có tiếng, không phải đỏ khó hiểu.
//
// ── HAI KHỔ MÁY, KHÔNG PHẢI MỘT (22/09/2026) ────────────────────────────────
//
// Đến hôm nay bộ này chạy ĐÚNG MỘT khổ: 1600×1000. Khổ điện thoại chỉ có trong
// `mobile-responsive.spec.ts`, tệp tự ghim `viewport` của riêng nó — tức 26
// trong 27 phép kiểm chưa từng chạy ở khổ điện thoại lần nào, trong khi học
// viên và giảng viên mở hệ thống bằng điện thoại là chuyện thường ngày.
//
// Nay hai `project`. Cùng một spec chạy hai lượt, tên lượt hiện trong báo cáo
// nên đỏ ở khổ nào là biết ngay khổ ấy.
//
//   · 1440×900 — khổ laptop phổ biến, KHÔNG giữ 1600 nữa: 1600 rộng hơn màn
//     hình thật của phần lớn người dùng nên nó giấu đúng loại lỗi bó hẹp mà bộ
//     đo giao diện vẫn bắt được ở 1366.
//   · 390×844 — iPhone 14/15. `isMobile` + `hasTouch` để `@media (pointer:
//     coarse)` trong `a11y.css` THẬT SỰ áp; thiếu hai cờ ấy thì sàn vùng chạm
//     44px không bật và phép kiểm đo nhầm một giao diện không ai nhìn thấy.
//
// `mobile-responsive.spec.ts` không chạy ở lượt điện thoại: nó tự ghim 375×812
// nên lượt hai chỉ lặp y hệt lượt một — tốn thời gian mà không thêm tin.
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  // CHỈ `*.spec.ts`. Mặc định của Playwright cũng khớp `*.test.mjs`, nên
  // `testDir: '.'` nuốt luôn `e2e/unit/` — vốn là script node thuần, CI chạy
  // bằng `node <tệp>`. Chạy chúng dưới Playwright thì mỗi tệp thành một "test"
  // không có `test()` nào, và kết quả không nói lên điều gì.
  testMatch: /\.spec\.ts$/,
  timeout: 120_000,
  retries: 0,
  workers: 1, // các test dùng chung tài khoản — chạy tuần tự
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3100',
    headless: true,
  },
  projects: [
    {
      name: 'may-tinh',
      use: { viewport: { width: 1440, height: 900 } },
    },
    {
      name: 'dien-thoai',
      use: {
        viewport: { width: 390, height: 844 },
        isMobile: true,
        hasTouch: true,
        deviceScaleFactor: 3,
      },
      testIgnore: /mobile-responsive\.spec\.ts$/,
    },
  ],
});
