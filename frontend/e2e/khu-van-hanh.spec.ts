import { expect, test } from '@playwright/test';

import { LY_DO_BO_QUA, login, vaoBangThe } from './helpers';

/**
 * Khu VẬN HÀNH dùng chung khung với mọi màn khác.
 *
 * ── VÌ SAO CÓ TỆP NÀY (07/09/2026) ────────────────────────────────────────
 *
 * Đợt gộp 06/09 hợp nhất BA bản dựng thanh điều hướng. Còn sót bản thứ TƯ:
 * `quan-tri/layout.tsx` tự dựng một header Tailwind riêng (`<header>` + `<h1>`
 * + `AdminNav`). Anh Sơn báo "phần vận hành vẫn còn xấu, lỗi".
 *
 * ĐO ĐƯỢC trên `/quan-tri/tong-quan` trước khi sửa, 07/09/2026:
 *
 *     .topbar                    = 0     (không dùng khung chung)
 *     .user-dropdown-item.danger = 0     ← KHÔNG CÓ ĐƯỜNG ĐĂNG XUẤT
 *     #theme-toggle              = 1     (bản riêng, không phải của khung)
 *
 * Đúng lỗ đã vá ở màn Thi thử hôm 06/09, lặp lại ở một khu khác: người trong
 * khu Vận hành muốn thoát phải quay về `/dashboard` trước. Và không chỗ nào
 * cho biết đang đăng nhập bằng ai — giữa một khu mà việc chính là quản lý
 * CON NGƯỜI.
 *
 * Phép kiểm này ĐỎ trên mã trước đó ở ba khẳng định đầu tiên (số đo ở trên).
 *
 * ── HAI THỨ KHÁC VỚI THANH HỌC VIÊN, CÓ CHỦ Ý ────────────────────────────
 *
 *   · Ô tìm kiếm bị GỠ. Nó nối thẳng vào `filterCourses` — nó tìm KHOÁ HỌC.
 *     Để lại trong khu Vận hành là một ô nhập nuốt chữ rồi vứt đi.
 *   · Hàng mục là tab của khu, đã LỌC THEO VAI ở máy chủ. Quản lý học vụ thấy
 *     2 tab, quản trị viên thấy 6 — nên phép kiểm dưới đây đếm "ít nhất 2" chứ
 *     không chốt cứng 6, và kiểm riêng rằng mọi tab đều mở được.
 */

const TRANG = [
  '/quan-tri/tong-quan',
  '/quan-tri/tai-khoan',
  '/quan-tri/lop-hoc',
  '/quan-tri/dot-hoc',
  '/quan-tri/nhat-ky',
  // Thêm 07/09/2026 cùng lúc với trang: mỗi trang mới trong khu phải vào danh
  // sách này, nếu không nó là trang DUY NHẤT không ai canh khung chung — và
  // khung chung đúng là thứ đã hỏng bốn lần ở bốn khu khác nhau.
  '/quan-tri/co-so-hoc-phi',
];

test.describe('khu vận hành', () => {
  for (const url of TRANG) {
    test(`${url} dùng đúng khung chung`, async ({ page }) => {
      const vao = (await vaoBangThe(page)) || (await login(page));
      test.skip(!vao, LY_DO_BO_QUA);

      await page.goto(url, { waitUntil: 'networkidle' });
      expect(page.url(), 'không được rơi về màn đăng nhập').not.toContain('/login');
      // Tài khoản kiểm thử không đủ quyền thì trang trả về màn "không có
      // quyền" — bỏ qua có tiếng, chứ không đỏ khó hiểu.
      test.skip(
        await page.getByText(/không có quyền/i).count() > 0,
        'tài khoản kiểm thử không vào được khu Vận hành',
      );

      await expect(page.locator('.topbar')).toHaveCount(1);
      // ĐÚNG thứ đã mất trước 07/09/2026.
      await expect(page.locator('.user-dropdown-item.danger')).toHaveCount(1);
      await expect(page.locator('#theme-toggle')).toHaveCount(1);

      const soTab = await page.locator('.topbar-nav .nav-btn').count();
      expect(soTab, 'có tab của khu').toBeGreaterThanOrEqual(2);

      // Ô tìm kiếm phải VẮNG: nó tìm khoá học, ở đây không có khoá học nào.
      await expect(page.locator('#search-input')).toHaveCount(0);

      // Đúng MỘT tab sáng, và nó là tab của trang đang mở.
      await expect(page.locator('.topbar-nav .nav-btn.active')).toHaveCount(1);

      // Mọi tab có tên cho trình đọc màn hình: dưới 70rem `shell.css` đặt
      // `display:none` cho nhãn chữ, mà phần tử display:none thì trình đọc
      // màn hình cũng bỏ qua.
      const thieuTen = await page.evaluate(() => [...document.querySelectorAll('.topbar-nav .nav-btn')]
        .filter((b) => !b.getAttribute('aria-label')).length);
      expect(thieuTen, 'mọi tab đều có aria-label').toBe(0);

      /* Nội dung KHÔNG được nằm dưới thanh. `.topbar` là `position: fixed`,
         nên thiếu phần bù chiều cao là tiêu đề trang bị cắt ngang (đo
         07/09/2026: chữ "Toàn trung tâm" nằm dưới thanh).

         Đo mép NỘI DUNG chứ không mép hộp: `padding-top` nằm BÊN TRONG hộp,
         nên `rect.top` của <main> vẫn là 0 dù nội dung đã được đẩy xuống. Bản
         đầu của phép kiểm này đo hộp và báo đỏ oan trên đúng đoạn mã đã sửa. */
      const biChe = await page.evaluate(() => {
        const m = document.querySelector('main');
        const tb = document.querySelector('.topbar');
        if (!m || !tb) return true;
        const con = m.firstElementChild;
        const dinh = con
          ? con.getBoundingClientRect().top
          : m.getBoundingClientRect().top + parseFloat(getComputedStyle(m).paddingTop);
        return dinh < tb.getBoundingClientRect().bottom - 1;
      });
      expect(biChe, 'nội dung không bị thanh cố định che').toBe(false);
    });
  }

  test('bảng một dòng KHÔNG mọc thanh cuộn dọc', async ({ page }) => {
    const vao = (await vaoBangThe(page)) || (await login(page));
    test.skip(!vao, LY_DO_BO_QUA);

    await page.goto('/quan-tri/tong-quan', { waitUntil: 'networkidle' });
    expect(page.url()).not.toContain('/login');
    test.skip(await page.locator('table').count() === 0, 'chưa có bảng nào để đo');

    /* `overflow-x: auto` làm `overflow-y` TÍNH THÀNH `auto` theo đặc tả. Bảng
       cao 77.296875px (phân số) cho `clientHeight` 77 nhưng `scrollHeight` 79
       — 2px ma ấy đủ để trình duyệt vẽ một thanh cuộn dọc đầy đủ mũi tên trên
       một bảng MỘT DÒNG. Đó là thanh cuộn trong ảnh anh Sơn gửi 07/09/2026.

       Phép kiểm ĐỎ được: bỏ `overflow-y-hidden` khỏi `TableWrap` rồi chạy lại. */
    const maCuon = await page.evaluate(() => [...document.querySelectorAll('*')]
      .filter((e) => {
        const cs = getComputedStyle(e);
        return /auto|scroll/.test(cs.overflowY) && e.scrollHeight > e.clientHeight + 1;
      })
      .map((e) => `${String(e.className).slice(0, 40)} ${e.scrollHeight}>${e.clientHeight}`));
    expect(maCuon, 'không vùng nào cuộn dọc vì vài điểm ảnh làm tròn').toEqual([]);
  });

  test('khổ điện thoại: không tràn ngang, tab vẫn tới được', async ({ page }) => {
    const vao = (await vaoBangThe(page)) || (await login(page));
    test.skip(!vao, LY_DO_BO_QUA);

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/quan-tri/tong-quan', { waitUntil: 'networkidle' });
    expect(page.url()).not.toContain('/login');

    const tran = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(tran, 'trang không được trượt ngang').toBeLessThanOrEqual(1);

    /* Hàng tab CUỘN NGANG được — ở khổ này nó không vừa, và cuộn trong vùng
       của nó là đúng cách (trang thì không được trượt). Kiểm rằng vùng ấy
       THẬT SỰ cuộn được, chứ không phải các tab bị cắt mất im lặng. */
    const nav = page.locator('#topbar-nav');
    const cuonDuoc = await nav.evaluate((e) => e.scrollWidth > e.clientWidth
      || getComputedStyle(e).overflowX === 'auto');
    expect(cuonDuoc, 'hàng tab cuộn ngang được thay vì bị cắt').toBe(true);
  });
});
