import { expect, test } from '@playwright/test';

import { LY_DO_BO_QUA, login, vaoBangThe } from './helpers';

/**
 * Khu GIẢNG DẠY dùng chung khung — và đây là lần thứ BA cùng một lỗ.
 *
 * ── VÌ SAO CÓ TỆP NÀY (07/09/2026) ────────────────────────────────────────
 *
 *   06/09  màn Thi thử       không có Đăng xuất  → vá bằng `AppShell`
 *   07/09  khu Vận hành      không có Đăng xuất  → vá bằng `khu`/`muc`
 *   07/09  khu Giảng dạy     không có Đăng xuất  → tệp này
 *
 * Khu Giảng dạy có NĂM trang mà KHÔNG có `layout.tsx` nào — mỗi trang tự dựng
 * phần đầu của mình. Nên giảng viên đang ở trong lớp thì không có đường thoát,
 * và không chỗ nào cho biết đang đăng nhập bằng ai.
 *
 * Lỗ này lặp vì mỗi khu mới đều bắt đầu bằng "một trang thôi, chưa cần khung".
 * Phép kiểm ở đây không chặn được cái đó cho khu THỨ TƯ — nhưng nó chặn được
 * việc khu này trôi ngược lại.
 *
 * ĐO ĐƯỢC trước khi sửa: `.topbar` = 0 ở cả bốn trang.
 *
 * ── TAB LẤY TỪ ĐƯỜNG DẪN ─────────────────────────────────────────────────
 *
 * Cả năm trang đều nhận `classId`, nhưng `layout.tsx` của Next KHÔNG nhận
 * `params` của trang con — nên khung đọc `usePathname()`. Phép kiểm dưới đây
 * canh đúng chỗ ấy: tab phải trỏ vào ĐÚNG lớp đang mở, không phải một đường
 * dẫn `undefined`.
 */
const TRANG = [
  { url: '/giang-day/buoi-hoc/1', tab: 'Buổi học' },
  { url: '/giang-day/bai-tap/1', tab: 'Bài tập' },
  { url: '/giang-day/bao-cao/1', tab: 'Báo cáo phụ huynh' },
  { url: '/giang-day/bao-cao/1/9', tab: 'Báo cáo phụ huynh' },
];

test.describe('khu giảng dạy', () => {
  for (const t of TRANG) {
    test(`${t.url} dùng đúng khung chung`, async ({ page }) => {
      const vao = (await vaoBangThe(page)) || (await login(page));
      test.skip(!vao, LY_DO_BO_QUA);

      await page.goto(t.url, { waitUntil: 'networkidle' });
      expect(page.url(), 'không được rơi về màn đăng nhập').not.toContain('/login');
      test.skip(
        (await page.getByText(/không tìm thấy lớp|không có quyền/i).count()) > 0,
        'tài khoản kiểm thử không phụ trách lớp 1',
      );

      await expect(page.locator('.topbar')).toHaveCount(1);
      // ĐÚNG thứ đã thiếu trước 07/09/2026.
      await expect(page.locator('.user-dropdown-item.danger')).toHaveCount(1);
      await expect(page.locator('#theme-toggle')).toHaveCount(1);
      // Ô tìm kiếm nối thẳng `filterCourses` — nó tìm KHOÁ HỌC, ở đây vô nghĩa.
      await expect(page.locator('#search-input')).toHaveCount(0);

      await expect(page.locator('.topbar-nav .nav-btn')).toHaveCount(3);
      await expect(page.locator('.topbar-nav .nav-btn.active')).toHaveCount(1);
      await expect(page.locator('.topbar-nav .nav-btn.active')).toContainText(t.tab);

      /* Tab phải trỏ vào ĐÚNG lớp đang mở. `usePathname()` đọc sai một đoạn là
         cả ba tab dẫn tới `/giang-day/buoi-hoc/undefined` — trang vẫn dựng,
         thanh vẫn đẹp, và chỉ hỏng khi có người bấm. */
      const trongLop = await page.evaluate(() => [...document.querySelectorAll('.topbar-nav .nav-btn')]
        .every((b) => b.getAttribute('aria-label') !== null));
      expect(trongLop, 'mọi tab đều có aria-label').toBe(true);
      await page.locator('.topbar-nav .nav-btn', { hasText: 'Bài tập' }).first().click();
      await page.waitForURL(/\/giang-day\/bai-tap\/\d+/, { timeout: 15_000 });
      expect(page.url(), 'tab dẫn tới đúng lớp, không phải undefined')
        .toMatch(/\/giang-day\/bai-tap\/1(\?|$|\/)/);
    });
  }

  test('in ra giấy thì thanh biến mất', async ({ page }) => {
    const vao = (await vaoBangThe(page)) || (await login(page));
    test.skip(!vao, LY_DO_BO_QUA);

    await page.goto('/giang-day/bao-cao/1/9', { waitUntil: 'networkidle' });
    test.skip(page.url().includes('/login'), LY_DO_BO_QUA);
    test.skip(await page.locator('.topbar').count() === 0, 'không mở được lớp này');

    /* Tờ báo cáo IN RA GIẤY gửi phụ huynh. Một hàng nút bấm trên đầu tờ giấy
       vừa vô nghĩa vừa tốn mực — và `position: fixed` còn tệ hơn khi in: một
       số trình duyệt lặp lại nó ở MỌI trang giấy. */
    await page.emulateMedia({ media: 'print' });
    await expect(page.locator('.topbar')).toBeHidden();
    await page.emulateMedia({ media: 'screen' });
    await expect(page.locator('.topbar')).toBeVisible();
  });
});
