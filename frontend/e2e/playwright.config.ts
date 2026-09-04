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
    viewport: { width: 1600, height: 1000 },
    headless: true,
  },
});
