import { expect, test } from '@playwright/test';

import { chiDoc, vaoLaHocVien } from './helpers';

/**
 * BỎ THI, PHA A (1.5A, 24/09/2026) — đi ĐÚNG đường người dùng đi.
 *
 * Anh Sơn chốt 24/09: "Bỏ mọi thứ về thi, giữ ngày thi HSA". `e2e/unit/bo-thi.test.mjs`
 * đọc mã nguồn (thanh điều hướng, bảng chuyển hướng); tệp này đi qua MÁY CHỦ Next
 * thật — chuyển hướng khai sai khuôn (`:classId` gõ nhầm) thì mã nguồn vẫn đúng
 * chữ mà trình duyệt vẫn ra "Không có trang này".
 *
 * Phần một KHÔNG cần đăng nhập: `next.config.ts` chuyển hướng trước cả proxy
 * phiên, nên chạy được ở mọi máy có Next đang chạy.
 */

test.describe('bỏ thi — link cũ', () => {
  for (const [cu, moi] of [
    ['/mock', '/dashboard'],
    ['/giang-day/ket-qua-thi/7322', '/giang-day/buoi-hoc/7322'],
  ] as const) {
    test(`${cu} chuyển hướng TẠM về ${moi}`, async ({ request }) => {
      const r = await request.get(cu, { maxRedirects: 0 });
      // 307 chứ không 308: pha A đảo ngược được, trình duyệt không được nhớ mãi.
      expect(r.status(), `${cu} phải là chuyển hướng tạm`).toBe(307);
      expect(new URL(r.headers().location ?? '', 'http://x').pathname).toBe(moi);
    });
  }
});

test('bỏ thi — thanh của học viên không còn mục Thi thử', async ({ page }) => {
  const boQua = await vaoLaHocVien(page);
  test.skip(boQua !== null, boQua ?? '');
  await chiDoc(page);

  await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
  const thanh = page.locator('.topbar');
  await expect(thanh).toHaveCount(1);
  await expect(thanh.locator('.nav-btn').first()).toBeAttached();
  // Chữ trên thanh KỂ CẢ mục ẩn trong nhóm "Học" (textContent, không innerText).
  const chu = await thanh.evaluate((el) => el.textContent ?? '');
  expect(chu, 'thanh còn chữ Thi thử').not.toMatch(/thi thử/i);
  await expect(thanh.locator('a[href^="/mock"]')).toHaveCount(0);
  // GIỮ: đếm ngược tới ngày thi HSA là mốc của em, không phải tính năng thi.
  await expect(page.locator('#tile-days')).toBeAttached();
});
