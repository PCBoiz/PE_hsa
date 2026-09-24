import { expect, test } from '@playwright/test';

import { LY_DO_THIEU_VAI, chiDoc, taiKhoanCuaVai, vaoTheoVai } from './helpers';

/**
 * KHU HƯỚNG DẪN — mọi vai mở được, mỗi vai thấy đúng phần việc của mình.
 *
 * ── VÌ SAO CÓ TỆP NÀY (23/09/2026) ────────────────────────────────────────
 *
 * Tới 22/09 hướng dẫn chỉ nằm ở `/quan-tri/huong-dan`, mà cổng khu ấy chỉ cho
 * quản trị viên và học vụ — tức các bài viết CHO giảng viên, trợ giảng, biên
 * tập nội dung nằm đó mà đúng người cần thì không mở được. Khu `/huong-dan`
 * sửa việc ấy. Tệp này canh để nó không trôi ngược.
 *
 * Canh BA thứ, vì hỏng thứ nào người mới cũng mắc kẹt:
 *   · mở được     — không bị chặn
 *   · lọc đúng    — thấy bài của vai mình, KHÔNG thấy bài chỉ dành vai khác
 *   · tìm thấy    — có mục "Hướng dẫn" trong menu tài khoản, bấm được, đưa tới
 *                   đúng chỗ. Một cuốn cẩm nang không ai tìm ra thì bằng không có.
 *
 * Chạy ở CẢ HAI khổ (xem `playwright.config.ts`). Ở điện thoại, menu tài khoản
 * là thứ người mới chạm vào đầu tiên khi bí — nên đây là chỗ đáng canh nhất.
 */

/* Số bài mong đợi cho từng vai — đo 22/09/2026 trên trình duyệt, rồi mới ghi.
   23/09/2026 (đo lại sau khi thêm): giảng viên 5 → 6 ("Ghi mục tiêu và nguyện vọng
   của em"), học vụ 6 → 8 ("Cấp tài khoản cho người mới" mở cho học vụ + "Cập nhật
   hồ sơ học viên").
   Thêm bài vào `lib/huongDan.ts` thì đổi số ở đây; con số lệch là tín hiệu có
   người thêm/bớt bài mà quên gắn vai. */
const MONG: Record<string, { bai: number; phaiCo: string; khongCo?: string }> = {
  'Giảng viên': { bai: 7, phaiCo: 'Mở đầu ngày dạy', khongCo: 'Cấp tài khoản cho người mới' },
  'Trợ giảng': { bai: 4, phaiCo: 'Điểm danh một buổi', khongCo: 'Gửi báo cáo cho phụ huynh' },
  'Quản lý học vụ': { bai: 9, phaiCo: 'Mở lớp và xếp học viên', khongCo: 'Khi cần biết ai đã làm gì' },
  // Tên bài đổi 24/09/2026 (bỏ thi, pha A): phần đề thi thử gỡ khỏi bài này.
  'Biên tập nội dung': { bai: 1, phaiCo: 'Soạn khoá học và bài học', khongCo: 'Điểm danh một buổi' },
};

/** Tiêu đề các bài đang hiện — đọc từ mục lục neo trong trang. */
async function mucLuc(page: import('@playwright/test').Page): Promise<string[]> {
  await page.waitForSelector('main', { timeout: 30_000 });
  return page.locator('main a[href^="#"]').allTextContents().then((ds) => ds.map((s) => s.trim()));
}

for (const [vai, mong] of Object.entries(MONG)) {
  test.describe(`hướng dẫn · ${vai}`, () => {
    test.beforeEach(async ({ page }) => {
      test.skip(!taiKhoanCuaVai(vai), LY_DO_THIEU_VAI);
      test.skip(!(await vaoTheoVai(page, vai)), `không đăng nhập được bằng vai ${vai}`);
      await chiDoc(page);
    });

    test('mở được và chỉ thấy bài của vai mình', async ({ page }) => {
      await page.goto('/huong-dan', { waitUntil: 'domcontentloaded' });
      await expect(page.locator('[data-chan]'), 'khu Hướng dẫn không được chặn ai').toHaveCount(0);

      const bai = await mucLuc(page);
      expect(bai, `${vai}: số bài`).toHaveLength(mong.bai);
      expect(bai, `${vai}: phải có bài của vai mình`).toContain(mong.phaiCo);
      if (mong.khongCo) {
        expect(bai, `${vai}: KHÔNG được thấy bài chỉ dành cho vai khác`).not.toContain(mong.khongCo);
      }
    });

    test('"xem tất cả" mở ra mọi bài — không ai rơi vào ngõ cụt', async ({ page }) => {
      await page.goto('/huong-dan', { waitUntil: 'domcontentloaded' });
      const loc = await mucLuc(page);
      await page.getByRole('link', { name: /xem tất cả|toàn bộ hướng dẫn/i }).first().click();
      await page.waitForURL(/tat-ca=1/, { timeout: 15_000 });
      const tatCa = await mucLuc(page);
      expect(tatCa.length, 'bản đầy đủ phải nhiều bài hơn bản đã lọc').toBeGreaterThan(loc.length);
    });

    test('tìm thấy từ menu tài khoản', async ({ page }) => {
      // Trang Giảng dạy / Vận hành / Soạn giáo trình đều dựng qua AppShell;
      // `/dashboard` là chỗ ai đăng nhập cũng rơi vào đầu tiên.
      await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
      const chip = page.locator('#user-chip-btn');
      await chip.waitFor({ state: 'visible', timeout: 30_000 });
      await chip.click();

      const muc = page.locator('.user-dropdown-item', { hasText: 'Hướng dẫn' });
      await expect(muc, 'menu tài khoản phải có mục "Hướng dẫn"').toBeVisible();

      /* Vùng chạm: ở khổ điện thoại (`pointer: coarse`) sàn là 44px. Menu là
         thứ bấm bằng ngón cái — mục nhỏ hơn là bấm trượt sang "Đăng xuất".

         CHỜ HOẠT ẢNH XONG rồi mới đo. `.user-dropdown` mở bằng `scale(0.97) →
         scale(1)` trong 0,15 s (`shell.css`). Bản đầu đo ngay khi mục "hiện" và
         đỏ ở cả bốn vai với 43,4px — tức 44 × 0,987, đúng một khung hình giữa
         chừng. Mục menu thật vẫn cao 44px; lỗi nằm ở thước. */
      await page.waitForFunction(() => {
        const t = getComputedStyle(document.getElementById('user-dropdown') as Element).transform;
        return t === 'none' || t === 'matrix(1, 0, 0, 1, 0, 0)';
      }, undefined, { timeout: 5_000 });
      const hop = await muc.boundingBox();
      const dienThoai = (page.viewportSize()?.width ?? 1440) < 500;
      if (dienThoai && hop) expect(hop.height, 'mục menu cao ≥ 44px trên điện thoại').toBeGreaterThanOrEqual(44);

      await muc.click();
      await page.waitForURL('**/huong-dan**', { timeout: 20_000 });
      await expect(page.locator('main a[href^="#"]').first()).toBeVisible();
    });
  });
}
