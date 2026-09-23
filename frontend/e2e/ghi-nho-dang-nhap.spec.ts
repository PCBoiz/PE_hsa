import { expect, test, type Page } from '@playwright/test';

import { LY_DO_THIEU_VAI, taiKhoanCuaVai } from './helpers';

/**
 * GHI NHỚ ĐĂNG NHẬP — góp ý TopHSA #1 (24/09/2026), đi bằng GIAO DIỆN.
 *
 * Canh phần mà phép kiểm backend (`accounts/tests_ghi_nho.py`) và guard tầng Next
 * (`e2e/unit/ghi-nho-phien.test.mjs`) không thấy: ô tick có thật trên màn, giá
 * trị của nó đi tới máy chủ, và TRÌNH DUYỆT THẬT giữ cookie đúng thời hạn —
 *   · không tick → `pe_at`/`pe_rt` là cookie PHIÊN (expires = -1);
 *   · tick       → `pe_rt` sống ~30 ngày, `pe_at` 30 phút.
 * Đăng nhập tạo một dòng token trong bảng thu hồi — như mọi spec khác đăng nhập.
 */

const VAI = 'Giảng viên';

async function dangNhap(page: Page, nho: boolean) {
  const tk = taiKhoanCuaVai(VAI)!;
  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  await page.fill('#login-email', tk.email);
  await page.fill('#login-password', tk.matKhau);
  const o = page.getByRole('checkbox', { name: /Ghi nhớ đăng nhập/ });
  await expect(o).toBeVisible();
  await expect(o, 'mặc định KHÔNG tick — máy ở trung tâm là máy dùng chung').not.toBeChecked();
  if (nho) await o.check();
  await expect(page.locator('#loginBtn')).toBeEnabled({ timeout: 30_000 });
  await page.click('#loginBtn');
  await page.waitForURL((u) => !u.pathname.startsWith('/login'), { timeout: 60_000 });
  const cookies = await page.context().cookies();
  const han = (ten: string) => cookies.find((c) => c.name === ten)?.expires;
  return { at: han('pe_at'), rt: han('pe_rt') };
}

test('không tick "Ghi nhớ đăng nhập" → cookie phiên, đóng trình duyệt là hết', async ({ page }) => {
  test.skip(!taiKhoanCuaVai(VAI), LY_DO_THIEU_VAI);
  const { at, rt } = await dangNhap(page, false);
  expect(rt, 'refresh phải là cookie phiên').toBe(-1);
  expect(at, 'access phải là cookie phiên').toBe(-1);
});

test('tick "Ghi nhớ đăng nhập" → refresh sống ~30 ngày', async ({ page }) => {
  test.skip(!taiKhoanCuaVai(VAI), LY_DO_THIEU_VAI);
  const { at, rt } = await dangNhap(page, true);
  const bayGio = Date.now() / 1000;
  expect(rt! - bayGio, 'refresh ~30 ngày').toBeGreaterThan(29 * 86400);
  expect(at! - bayGio, 'access 30 phút').toBeLessThanOrEqual(30 * 60 + 5);
  expect(at! - bayGio).toBeGreaterThan(25 * 60);
});
