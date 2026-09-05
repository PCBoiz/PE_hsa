// Lưu nhật ký mà máy chủ trả 200 THIẾU `log` thì KHÔNG được báo "Đã lưu".
//
// ── LỖI ĐANG CHẶN LẠI (05/09/2026) ──────────────────────────────────────────
//
// `dashboard.js::saveToday` chỉ kiểm `r.ok` rồi dùng thẳng `res.d.log.date`.
// Cho máy chủ trả 200 với thân `{}` và bấm Lưu:
//
//   · màn hình báo "Đã lưu ✓"                        ← NÓI DỐI
//   · `unshift(undefined)` nhét một bản ghi MA vào danh sách
//   · nhãn đổi thành "Xem nhật ký 1 ngày gần đây"
//   · mở nhật ký ra → Cannot read properties of undefined (reading 'date')
//
// Dòng `.filter()` ngay trên KHÔNG chặn được, vì với học viên MỚI thì `recent`
// rỗng nên callback không chạy lần nào — chính người mới là người trúng.
//
// Tìm ra bằng `scripts/go_moi_nut.mjs`: `do_giao_dien.mjs` mở trang này và báo
// "lỗi JS: 0" vì nó chỉ TẢI, không BẤM.
import { expect, test } from '@playwright/test';

import { LY_DO_BO_QUA, login } from './helpers';

/** Chặn ĐÚNG lời gọi PUT nhật ký; mọi thứ khác đi thật. */
async function gia(page: import('@playwright/test').Page, than: string) {
  await page.route('**/api/hsa/journal*', (r) =>
    (r.request().method() === 'PUT'
      ? r.fulfill({ status: 200, contentType: 'application/json', body: than })
      : r.fallback()));
}

async function moDashboard(page: import('@playwright/test').Page) {
  await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(
    () => typeof (window as unknown as { navigate?: unknown }).navigate === 'function',
    undefined, { timeout: 30_000 });
  await page.waitForTimeout(2500);
}

test('máy chủ trả 200 thiếu `log` → nói thật, không tạo bản ghi ma', async ({ page }) => {
  test.skip(!(await login(page)), LY_DO_BO_QUA);
  const loi: string[] = [];
  page.on('pageerror', (e) => loi.push(String(e.message)));

  await gia(page, '{}');
  await moDashboard(page);

  await page.fill('#jr-minutes', '30');
  await page.click('#jr-save');
  await page.waitForTimeout(1200);

  await expect(page.locator('#jr-msg'), 'không được báo đã lưu khi chưa chắc')
    .not.toHaveText(/Đã lưu/);
  await expect(page.locator('#jr-msg')).toHaveText(/chưa chắc đã lưu/);

  // Không có bản ghi MA: nhãn vẫn phải là 0 ngày.
  await expect(page.locator('#jr-toggle')).toHaveText(/0 ngày/);

  await page.click('#jr-toggle').catch(() => {});
  await page.waitForTimeout(700);
  expect(loi, 'mở nhật ký sau đó KHÔNG được ném').toEqual([]);
});

test('phản hồi đúng hình dạng → vẫn lưu và hiện đúng một dòng', async ({ page }) => {
  test.skip(!(await login(page)), LY_DO_BO_QUA);
  const loi: string[] = [];
  page.on('pageerror', (e) => loi.push(String(e.message)));

  // Hình dạng LẤY TỪ máy chủ thật (`stats/views.py:451`), không tự bịa.
  const ngay = new Date().toISOString().slice(0, 10);
  await gia(page, JSON.stringify({
    ok: true,
    log: { date: ngay, minutes: 30, topic: 'Số học', what: 'Ôn tập', note: '', difficultyLabel: 'Vừa' },
    week: {
      weekStart: ngay, done: { lessons: 0, mocks: 0, minutes: 30 },
      systemMinutes: 0, selfMinutes: 30, events: 1, target: null, met: null,
    },
  }));
  await moDashboard(page);

  await page.fill('#jr-minutes', '30');
  await page.click('#jr-save');
  await page.waitForTimeout(1200);

  await expect(page.locator('#jr-msg')).toHaveText(/Đã lưu/);
  await expect(page.locator('#jr-toggle')).toHaveText(/1 ngày/);

  await page.click('#jr-toggle');
  await page.waitForTimeout(700);
  await expect(page.locator('#jr-history .jr-item')).toHaveCount(1);
  await expect(page.locator('#jr-history .jr-item').first()).toContainText('Ôn tập');
  expect(loi).toEqual([]);
});
