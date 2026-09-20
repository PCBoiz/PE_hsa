// Bấm Enter ở màn đăng nhập TRƯỚC KHI React hydrate xong → mật khẩu KHÔNG được
// lọt vào URL.
//
// Đo trên production 20/09/2026 (điện thoại 390, Vercel + Render lạnh): kịch bản
// điền email/mật khẩu rồi bấm Đăng nhập ngay khi DOM có, và trình duyệt đi tới
//   /login?email=…&password=Audit2009%21hv2
// — biểu mẫu chưa có `onSubmit` của React nên trình duyệt gửi kiểu MẶC ĐỊNH:
// GET, mọi ô thành tham số. Mật khẩu nằm trong lịch sử trình duyệt, trong log
// của Vercel, trong `Referer` của mọi tài nguyên trang kế. Người dùng thật gặp
// đúng cảnh này trên mạng chậm: gõ xong, Enter, chưa kịp có JS.
//
// Cách dựng lại: giữ chậm MỌI chunk JS của Next (không phải chỉ main.js), nên
// HTML về, ô nhập dùng được, nhưng React chưa hydrate.
import { expect, test } from '@playwright/test';

test('Enter trước khi hydrate: không gửi GET mang mật khẩu', async ({ page, context }) => {
  await context.route('**/_next/static/chunks/**', async (r) => {
    await new Promise((x) => setTimeout(x, 8000));
    return r.fallback();
  });
  await page.goto('/login', { waitUntil: 'domcontentloaded' });

  const email = page.locator('input[type="email"], input[name="email"]').first();
  const mk = page.locator('input[type="password"]').first();
  await email.fill('ai-do@example.com');
  await mk.fill('MatKhauBiMat!1');
  await mk.press('Enter');
  await page.waitForTimeout(1500);

  expect(page.url(), 'URL không được mang password').not.toMatch(/password=/);
  expect(page.url(), 'URL không được mang email').not.toMatch(/email=/);
  // Ô nhập vẫn còn chữ — không tải lại trang, không mất thứ người dùng gõ.
  expect(await mk.inputValue()).toBe('MatKhauBiMat!1');
});
