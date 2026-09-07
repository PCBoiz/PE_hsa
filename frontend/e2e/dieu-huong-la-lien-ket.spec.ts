import { expect, test } from '@playwright/test';

import { LY_DO_BO_QUA, login, vaoBangThe } from './helpers';

/**
 * Trong KHU, mục điều hướng phải là LIÊN KẾT — và vẫn phải đi phía client.
 *
 * ── VÌ SAO CÓ TỆP NÀY (07/09/2026) ────────────────────────────────────────
 *
 * Audit luồng đo thanh điều hướng trên `/giang-day/buoi-hoc/1` và
 * `/quan-tri/tong-quan`: MỌI mục đều là `BUTTON`, không mục nào có `href`.
 * Nhưng bấm chúng thì URL đổi thật (`router.push`). Một thứ chuyển trang mà
 * không phải liên kết thì mất hết những gì trình duyệt cho không:
 *
 *   · Ctrl/⌘ + bấm để mở tab mới          · bấm chuột giữa
 *   · chuột phải → "Mở trong tab mới"     · chép địa chỉ
 *   · trình đọc màn hình đọc đúng "liên kết" thay vì "nút"
 *
 * Không nhỏ với người dùng thật: giảng viên so hai em thì mở hai tab báo cáo
 * cạnh nhau; quản trị viên đang đọc nhật ký muốn mở lớp học ra bên cạnh chứ
 * không muốn rời trang đang đọc.
 *
 * ── HAI KHẲNG ĐỊNH PHẢI ĐI CÙNG NHAU ─────────────────────────────────────
 *
 * Đổi `<button>` thành `<a href>` mà quên `preventDefault` thì mỗi lần bấm tab
 * là NẠP LẠI CẢ TRANG — một hồi quy tốc độ đội lốt sửa a11y, và nó sẽ không ai
 * nhận ra vì màn hình vẫn hiện đúng nội dung. Nên phép kiểm đòi CẢ HAI: có
 * `href` thật, VÀ bấm thường vẫn đi phía client.
 *
 * Cách đo "đi phía client": đặt một dấu vết lên `window` rồi bấm. Nạp lại
 * trang thì dấu vết mất; điều hướng phía client thì nó còn.
 *
 * ── NGOÀI KHU THÌ NGƯỢC LẠI ──────────────────────────────────────────────
 *
 * Trên `/dashboard` và `/mock`, bấm mục chỉ đổi TAB trong cùng một trang qua
 * `goiLegacy('navigate')` — URL đứng yên. Gắn `href` ở đó còn tệ hơn: Ctrl-bấm
 * sẽ mở một tab mới nạp lại cả trang rồi rơi về tab mặc định, tức lời hứa của
 * `href` là lời hứa hão. Phép kiểm cuối canh đúng điều đó.
 */

test.describe('điều hướng trong khu là liên kết thật', () => {
  test('có href, và bấm thường vẫn đi phía client', async ({ page }) => {
    const vao = (await vaoBangThe(page)) || (await login(page));
    test.skip(!vao, LY_DO_BO_QUA);

    await page.goto('/quan-tri/tong-quan', { waitUntil: 'networkidle' });
    test.skip(
      (await page.getByText(/không có quyền/i).count()) > 0,
      'tài khoản kiểm thử không vào được khu Vận hành',
    );

    const muc = page.locator('.topbar-nav a.nav-btn');
    await expect(muc.first()).toBeVisible();
    expect(await muc.count(), 'mục điều hướng trong khu phải là thẻ <a>').toBeGreaterThan(1);

    for (const el of await muc.all()) {
      const href = await el.getAttribute('href');
      expect(href, 'mỗi mục phải mang địa chỉ thật để Ctrl-bấm được').toMatch(/^\//);
    }

    // Dấu vết chỉ sống sót nếu KHÔNG nạp lại cả trang.
    await page.evaluate(() => {
      (window as unknown as { __dau?: string }).__dau = 'con';
    });
    await page.locator('.topbar-nav a.nav-btn', { hasText: 'Lớp học' }).first().click();
    await page.waitForURL('**/quan-tri/lop-hoc');
    const con = await page.evaluate(
      () => (window as unknown as { __dau?: string }).__dau,
    );
    expect(con, 'bấm tab không được nạp lại cả trang').toBe('con');
  });

  test('ngoài khu, mục điều hướng KHÔNG mang href', async ({ page }) => {
    const vao = (await vaoBangThe(page)) || (await login(page));
    test.skip(!vao, LY_DO_BO_QUA);

    await page.goto('/dashboard', { waitUntil: 'networkidle' });
    await expect(page.locator('.topbar-nav .nav-btn').first()).toBeVisible();

    /* Ở đây bấm chỉ đổi tab trong cùng trang, URL đứng yên — nên `href` sẽ là
       một lời hứa sai. Đếm phải bằng 0. */
    expect(
      await page.locator('.topbar-nav a.nav-btn').count(),
      'trên trang SPA, mục điều hướng không đổi URL nên không được mang href',
    ).toBe(0);
  });
});
