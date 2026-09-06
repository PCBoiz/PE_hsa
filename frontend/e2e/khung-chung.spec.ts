import { expect, test } from '@playwright/test';

import { LY_DO_BO_QUA, login, vaoBangThe } from './helpers';

/**
 * KHUNG CHUNG phải GIỐNG NHAU ở mọi màn — và phải CHẠY.
 *
 * ── VÌ SAO CÓ TỆP NÀY (06/09/2026) ────────────────────────────────────────
 *
 * Anh Sơn báo: "nav của mục thi thử khác hẳn nav của các mục khác". Đo lại thì
 * thanh điều hướng có BA bản dựng riêng, chỉ dùng chung mỗi danh sách mục:
 *
 *   Topbar.tsx           `.topbar`    · biểu tượng SVG
 *   courses/[courseId]   `.topbar`    · biểu tượng EMOJI 🔍🌙🔔▾
 *   MockExam.tsx         `.mk-topbar` · chữ trần, KHÔNG có chip người dùng
 *
 * Hậu quả nặng nhất không phải thẩm mỹ: vào màn Thi thử là học viên **mất
 * đường Đăng xuất và nút đổi sáng/tối**. Nay cả ba dùng chung `AppShell`.
 *
 * ── PHÉP KIỂM NÀY ĐÃ ĐƯỢC CHỨNG MINH LÀ ĐỎ ĐƯỢC ──────────────────────────
 *
 * Lùi `MockExam.tsx` về bản trước khi gộp rồi chạy lại: màn Thi thử đỏ ở
 * "có .topbar", "có 8 mục điều hướng", "biểu tượng là SVG", "có Đăng xuất",
 * "có nút đổi chủ đề". Một phép kiểm hằng đúng là một phép kiểm giả, nên chỗ
 * này ghi rõ nó đã được thử theo chiều ngược lại.
 *
 * `go_moi_nut.mjs` KHÔNG thay được tệp này: bộ ấy chỉ bấm trong thân trang
 * (nó báo "Thi thử: 1 nút"), tức chưa từng chạm vào thanh.
 */

/** Ba cấu hình khác nhau của CÙNG một component — phải ra cùng một thanh. */
const MAN = [
  { ten: 'Thi thử (React giữ menu)', url: '/mock' },
  { ten: 'Dashboard (JS cũ giữ menu)', url: '/dashboard' },
  { ten: 'Chi tiết khoá (JS cũ, không SPA)', url: '/courses/hsa_quantitative' },
];

test.describe('khung chung', () => {
  for (const man of MAN) {
    test(`${man.ten} dùng đúng khung chung`, async ({ page }) => {
      const vao = (await vaoBangThe(page)) || (await login(page));
      test.skip(!vao, LY_DO_BO_QUA);

      await page.goto(man.url, { waitUntil: 'networkidle' });
      // Rơi về màn đăng nhập thì mọi khẳng định bên dưới đều vô nghĩa mà vẫn
      // có thể XANH — nên chặn ở đây trước.
      expect(page.url(), 'không được rơi về màn đăng nhập').not.toContain('/login');

      await expect(page.locator('.topbar')).toHaveCount(1);
      expect(await page.locator('.topbar-nav .nav-btn').count(),
        'đủ 8 mục điều hướng của navMuc.ts').toBeGreaterThanOrEqual(8);

      // Biểu tượng phải là SVG. Emoji do phông màu của HỆ ĐIỀU HÀNH vẽ nên
      // không nhận `currentColor` và mỗi máy một kiểu.
      expect(await page.locator('.topbar .nav-btn svg').count()).toBeGreaterThanOrEqual(8);
      const emoji = await page.evaluate(() => {
        const t = (document.querySelector('.topbar') as HTMLElement | null)?.innerText || '';
        return [...t].filter((c) => (c.codePointAt(0) as number) > 0x2190).join('');
      });
      expect(emoji, 'không còn emoji trong thanh').toBe('');

      // Đúng thứ đã MẤT ở màn Thi thử trước 06/09/2026.
      await expect(page.locator('.user-dropdown-item.danger')).toHaveCount(1);
      await expect(page.locator('#theme-toggle')).toHaveCount(1);

      // Mỗi nút điều hướng phải có TÊN cho trình đọc màn hình: dưới 96rem
      // `shell.css` đặt `display:none` cho nhãn chữ, mà phần tử display:none
      // thì trình đọc màn hình cũng bỏ qua.
      const thieuTen = await page.evaluate(() => [...document.querySelectorAll('.topbar-nav .nav-btn')]
        .filter((b) => !b.getAttribute('aria-label')).length);
      expect(thieuTen, 'mọi nút điều hướng đều có aria-label').toBe(0);

      // Đổi chủ đề phải THẬT SỰ đổi, và biểu tượng phải đi theo.
      const truoc = await page.evaluate(() => document.body.classList.contains('dark'));
      await page.locator('#theme-toggle').click();
      await expect
        .poll(() => page.evaluate(() => document.body.classList.contains('dark')))
        .not.toBe(truoc);
      const sau = await page.evaluate(() => document.body.classList.contains('dark'));
      const hienTroi = await page.evaluate(() => {
        const e = document.querySelector('.theme-toggle-btn .shell-ic-troi');
        return e ? getComputedStyle(e).display !== 'none' : null;
      });
      expect(hienTroi, 'đang tối thì hiện mặt trời').toBe(sau);
      await page.locator('#theme-toggle').click();   // trả lại

      // Menu người dùng mở được và ĐÓNG được bằng Escape.
      await page.locator('#user-chip-btn').click();
      await expect(page.locator('#user-dropdown')).toBeVisible();
      await page.keyboard.press('Escape');
      await expect(page.locator('#user-dropdown')).toBeHidden();
    });
  }

  test('đang làm bài thì thanh bị tước, và đồng hồ không cuộn mất', async ({ page }) => {
    const vao = (await vaoBangThe(page)) || (await login(page));
    test.skip(!vao, LY_DO_BO_QUA);

    await page.goto('/mock', { waitUntil: 'networkidle' });
    const batDau = page.locator('.mk-exam-card button').first();
    test.skip(!(await batDau.count()), 'CSDL chưa có đề thi thử nào');
    await batDau.click();
    await expect(page.locator('.mk-take')).toBeVisible({ timeout: 15_000 });

    // Điều hướng bị GỠ HẲN: một cú bấm nhầm giữa lúc thi là mất bài đang làm.
    await expect(page.locator('.topbar.shell-lam-bai')).toHaveCount(1);
    await expect(page.locator('.topbar .nav-btn')).toHaveCount(0);
    await expect(page.locator('.topbar #search-input')).toHaveCount(0);

    // Đồng hồ lên thanh cố định — trước đây nó nằm trong thân trang, nên cuộn
    // xuống câu 5 là mất, đúng lúc thí sinh cần nhìn nó nhất.
    await expect(page.locator('.topbar .mk-timer')).toBeVisible();
    await page.evaluate(() => window.scrollTo(0, 600));
    await expect(page.locator('.topbar .mk-timer')).toBeVisible();
  });
});
