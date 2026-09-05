// Chạm vào topbar TRƯỚC khi `main.js` kịp nạp thì không được ném, và cú chạm
// ấy không được biến mất.
//
// ── LỖI ĐANG CHẶN LẠI (05/09/2026) ──────────────────────────────────────────
//
// React dựng `Topbar` và gắn handler NGAY; `LegacyScripts` nạp `main.js` SAU.
// Giữa hai mốc ấy, chạm vào ô tìm kiếm ném:
//
//     bấm  → W(...).showSearchSuggestions is not a function
//     gõ   → W(...).filterCourses is not a function
//
// Trên máy dev cửa sổ ấy ~200ms nên hiếm khi trúng — nên phép kiểm này KHÔNG
// trông chờ trúng thời điểm mà GIỮ CHẬM `main.js` để cửa sổ mở rộng ra. Một
// cuộc đua chỉ kiểm được khi mình cầm được nhịp.
//
// Dashboard nạp SÁU tệp thực thi nối tiếp (riêng `main.js` + `dashboard.js` đã
// 5.200 dòng), nên trên điện thoại mạng chậm cửa sổ này tính bằng giây.
//
// Phép kiểm đòi HAI điều, và điều thứ hai mới là điều đáng giá:
//   1. không ném;
//   2. việc người dùng yêu cầu VẪN ĐƯỢC LÀM sau khi script tới.
// Chỉ đòi điều 1 thì `?.` cũng qua — mà `?.` nuốt mất cú bấm, tức đổi một lỗi
// ồn lấy một lỗi câm.
import { expect, test } from '@playwright/test';

import { LY_DO_BO_QUA, login } from './helpers';

test('chạm topbar trước khi main.js tới: không ném, và không mất thao tác', async ({ page, context }) => {
  test.skip(!(await login(page)), LY_DO_BO_QUA);

  const loi: string[] = [];
  page.on('pageerror', (e) => loi.push(String(e.message)));

  // Giữ chậm ĐÚNG main.js. Mọi thứ khác chạy bình thường.
  await context.route('**/static/js/main.js', async (r) => {
    await new Promise((x) => setTimeout(x, 6000));
    return r.fallback();
  });

  await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1500);   // React đã hydrate, main.js còn đang bị giữ

  expect(await page.evaluate(() => typeof (window as unknown as
    { filterCourses?: unknown }).filterCourses),
  'cửa sổ đua phải đang MỞ, nếu không phép kiểm này không kiểm gì')
    .not.toBe('function');

  const o = page.locator('.topbar input').first();
  await o.click();
  await o.type('lượng', { delay: 40 });
  await page.waitForTimeout(600);

  expect(loi, 'chạm topbar khi script chưa tới KHÔNG được ném').toEqual([]);

  // Và thao tác phải được LÀM, không phải bị nuốt.
  await page.waitForFunction(() => typeof (window as unknown as
    { filterCourses?: unknown }).filterCourses === 'function', undefined, { timeout: 20_000 });
  await page.waitForTimeout(900);

  expect(await o.inputValue(), 'chữ người dùng gõ phải còn nguyên').toBe('lượng');
  const goiY = await page.evaluate(() => {
    const e = document.getElementById('search-suggestions')
      || document.querySelector('.search-suggestions');
    return e ? getComputedStyle(e).display : null;
  });
  expect(goiY, 'khối gợi ý phải mở ra — tức lời gọi bị hoãn đã được chạy').toBe('block');
});
