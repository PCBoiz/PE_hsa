import { expect, test } from '@playwright/test';

import { LY_DO_BO_QUA, login, vaoBangThe } from './helpers';

/**
 * Ô "Lộ trình của bạn" phải cao bằng NỘI DUNG của nó, và không được bóp méo.
 *
 * ── VÌ SAO CÓ TỆP NÀY (07/09/2026) ────────────────────────────────────────
 *
 * Anh Sơn: "phần lộ trình vẫn bị bóp méo nhỏ đi rất khó chịu".
 *
 * Bản cũ vẽ zigzag 6 nút đặt tuyệt đối theo phần trăm, đường nối là
 * `<svg preserveAspectRatio="none">` — nghĩa đen của thuộc tính ấy là "cho
 * phép bóp méo". Khung thì `height: 560px` cộng `flex: 1` trong một cột
 * `align-self: stretch`, nên nó bị kéo theo cột bên cạnh.
 *
 * ĐO ĐƯỢC trên tài khoản học viên thật (1 khoá), 07/09/2026:
 *
 *     mã cũ:  khung 2673px · các chặng 61px  →  2612px trống thừa
 *     mã mới: khung  108px · các chặng 71px  →     2px thừa (đệm đã trừ)
 *
 * HSA chỉ có BA khoá (hsa_quantitative, hsa_verbal, hsa_science) và học viên
 * ghi danh 1–2. Nên chỗ trống không phải trường hợp hiếm — nó là trường hợp
 * THƯỜNG.
 *
 * ── PHÉP KIỂM NÀY ĐÃ ĐƯỢC CHỨNG MINH LÀ ĐỎ ĐƯỢC ──────────────────────────
 *
 * Lùi `dashboard.js` + `dashboard.css` về bản trước rồi chạy lại: đỏ ở cả
 * "không còn khoảng trống thừa" (2612px) lẫn "không có preserveAspectRatio".
 *
 * ── VÀ THƯỚC ĐO NÀY TỪNG SAI, GHI LẠI ĐỂ KHÔNG AI DỰNG LẠI ────────────────
 *
 * Bản đầu của phép đo lấy `khung.firstElementChild` làm "nội dung". Trên mã
 * CŨ, con đầu tiên là chính cái `<svg>` phủ kín khung (`position:absolute;
 * inset:0`) — nên "nội dung" đo ra bằng đúng "khung", tỉ lệ ra 1.0, và phép
 * kiểm XANH trên đúng đoạn mã nó phải bắt. Nay nó đo hợp hình bao của các
 * `.mini-rm-node` thật. Một thước lặng lẽ đo nhầm vật thì tệ hơn không có
 * thước: nó tắt phản xạ kiểm tra của người đọc sau.
 */

test.describe('lộ trình rút gọn', () => {
  test('khung cao bằng nội dung, và không có gì để bóp méo', async ({ page }) => {
    const vao = (await vaoBangThe(page)) || (await login(page));
    test.skip(!vao, LY_DO_BO_QUA);

    await page.goto('/dashboard', { waitUntil: 'networkidle' });
    // Rơi về màn đăng nhập thì mọi khẳng định bên dưới đều vô nghĩa mà vẫn
    // có thể XANH — chặn ở đây trước.
    expect(page.url(), 'không được rơi về màn đăng nhập').not.toContain('/login');

    const khung = page.locator('#mini-rm-canvas');
    await expect(khung).toBeVisible();
    // Chờ dữ liệu về; còn chữ "Đang tải…" thì chưa có gì để đo.
    await expect(page.locator('.mini-rm-loading')).toHaveCount(0, { timeout: 15_000 });

    const d = await page.evaluate(() => {
      const k = document.getElementById('mini-rm-canvas')!;
      const cs = getComputedStyle(k);
      const oNut = [...k.querySelectorAll('.mini-rm-node')].map((n) => n.getBoundingClientRect());
      const trong = k.querySelector('.mini-rm-empty');
      const noiDung = oNut.length
        ? Math.max(...oNut.map((q) => q.bottom)) - Math.min(...oNut.map((q) => q.top))
        : (trong?.getBoundingClientRect().height ?? 0);
      return {
        khungCao: k.getBoundingClientRect().height,
        noiDung,
        dem: parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom),
        soNut: oNut.length,
        conNho: oNut.filter((q) => q.height < 44 || q.width < 44).length,
        meo: k.innerHTML.includes('preserveAspectRatio="none"'),
      };
    });

    // Chưa ghi danh khoá nào thì khối trống lo phần chiều cao — vẫn đo được,
    // vì `noiDung` khi ấy lấy theo `.mini-rm-empty`.
    expect(d.noiDung, 'có nội dung để đo').toBeGreaterThan(0);

    const thua = d.khungCao - d.noiDung - d.dem;
    expect(
      thua,
      `khoảng trống ngoài phần đệm đã khai: ${Math.round(d.khungCao)} − ${Math.round(d.noiDung)}`
        + ` − ${Math.round(d.dem)} = ${Math.round(thua)}px`,
    ).toBeLessThanOrEqual(8);

    expect(d.meo, 'preserveAspectRatio="none" cho phép kéo dãn lệch trục').toBe(false);
    expect(d.conNho, 'mọi chặng đủ vùng chạm 44px (Apple HIG)').toBe(0);
  });

  test('chặng là liên kết thật — bàn phím đi tới được', async ({ page }) => {
    const vao = (await vaoBangThe(page)) || (await login(page));
    test.skip(!vao, LY_DO_BO_QUA);

    await page.goto('/dashboard', { waitUntil: 'networkidle' });
    expect(page.url()).not.toContain('/login');
    await expect(page.locator('.mini-rm-loading')).toHaveCount(0, { timeout: 15_000 });

    const nut = page.locator('.mini-rm-node').first();
    test.skip(!(await nut.count()), 'tài khoản này chưa ghi danh khoá nào');

    /* Bản cũ dùng `<div onclick="location.href=…">`: chuột bấm được, bàn phím
       và trình đọc màn hình thì không — chúng không thấy `div` là thứ bấm
       được. Nay là `<a href>`, nên chỉ cần kiểm nó THẬT SỰ là liên kết. */
    expect(await nut.evaluate((e) => e.tagName)).toBe('A');
    expect(await nut.getAttribute('href')).toBeTruthy();
    await nut.focus();
    expect(await nut.evaluate((e) => e === document.activeElement),
      'nhận được tiêu điểm bàn phím').toBe(true);
  });
});
