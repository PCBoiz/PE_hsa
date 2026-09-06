import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { expect, test } from '@playwright/test';

import { LY_DO_BO_QUA, login, vaoBangThe } from './helpers';

/**
 * Sơ đồ phân quyền phải VẼ ĐÚNG CHIỀU, và không được bỏ sót lớp quyền nào.
 *
 * ── VÌ SAO CÓ TỆP NÀY (07/09/2026) ────────────────────────────────────────
 *
 * Bản dựng đầu của `SoDoVaiTro.tsx` lồng NGƯỢC: hộp ngoài cùng là
 * `IsAdminOrAcademic` (2 vai) còn `IsTeachingStaff` (4 vai) nằm bên trong —
 * tức hình nói ngược hẳn cái nhãn "càng ra ngoài càng nhiều vai" in ngay bên
 * trên nó.
 *
 * Không thứ gì bắt được: TypeScript nhận cả `reduce` lẫn `reduceRight`, cả hai
 * đều dựng ra đúng bốn hộp lồng nhau, và bản sai trông không kém thuyết phục
 * chút nào. Tôi chỉ phát hiện vì mở ảnh chụp ra nhìn. Một hình vẽ SAI mà TRÔNG
 * ĐÚNG là thứ tệ nhất trong cả trang này — nó sẽ được mang vào buổi họp với cô
 * Hương và không ai trong phòng có cách nào kiểm lại.
 *
 * ── HAI KHẲNG ĐỊNH, VÀ VÌ SAO CHÚNG KHÔNG CHÉP LẠI THUẬT TOÁN ────────────
 *
 * Cách dễ nhất là chép `soDoVai()` sang đây rồi so hai kết quả. Làm thế thì
 * phép kiểm chỉ chứng minh tôi chép đúng chính mình: cùng một lỗi tư duy sẽ
 * nằm ở cả hai bên và cả hai cùng xanh.
 *
 * Nên phép kiểm này chỉ đọc DỮ LIỆU (`VAI_CUA_LOP_QUYEN` — lớp quyền nào cho
 * mấy vai) rồi kiểm hai TÍNH CHẤT mà mọi bản vẽ đúng đều phải có:
 *
 *   1. LỒNG ĐÚNG CHIỀU — hộp nào chứa hộp nào thì số vai của hộp ngoài phải
 *      LỚN HƠN hộp trong. Đây là khẳng định đỏ trên bản `reduceRight`.
 *   2. KHÔNG SÓT — mọi lớp quyền đã khai đều phải xuất hiện trên trang, dù ở
 *      chuỗi chính hay ở nhánh. Một lớp bị thuật toán đánh rơi sẽ biến mất
 *      lặng lẽ, và trang vẫn trông đầy đủ.
 */

/* `process.cwd()`, KHÔNG phải `import.meta.url`: bộ chạy Playwright nạp tệp
   spec ở chế độ CommonJS, nên `import.meta` là lỗi cú pháp và cả tệp bị bỏ
   qua — Playwright báo "No tests found" chứ không báo lỗi, tức phép kiểm biến
   mất im lặng. Playwright luôn chạy từ thư mục chứa `playwright.config`. */
const GOC = process.cwd();

/** Lớp quyền → số vai, đọc THẲNG từ nguồn. Không gõ tay, không chép thuật toán. */
function soVaiCuaLopQuyen(): Record<string, number> {
  const src = readFileSync(join(GOC, 'src', 'lib', 'quyenVai.ts'), 'utf8');
  const khoi = src.slice(
    src.indexOf('export const VAI_CUA_LOP_QUYEN'),
    src.indexOf('export type Viec'),
  );
  return Object.fromEntries(
    [...khoi.matchAll(/(\w+):\s*\[([^\]]*)\]/g)].map((m) => [
      m[1],
      m[2].split(',').filter((x) => x.trim()).length,
    ]),
  );
}

test.describe('sơ đồ phân quyền', () => {
  test('lồng đúng chiều: hộp ngoài luôn nhiều vai hơn hộp trong', async ({ page }) => {
    const vao = (await vaoBangThe(page)) || (await login(page));
    test.skip(!vao, LY_DO_BO_QUA);
    await page.goto('/quan-tri/vai-tro', { waitUntil: 'networkidle' });
    test.skip(
      await page.getByText(/không có quyền/i).count() > 0,
      'tài khoản kiểm thử không vào được khu Vận hành',
    );

    const hop = page.locator('[data-lop-quyen]:not([data-nhanh])');
    // `count()` KHÔNG tự chờ (bài học 06/09) — chờ hộp đầu hiện ra trước đã.
    await expect(hop.first()).toBeVisible();
    const n = await hop.count();
    expect(n, 'phải có ít nhất hai vòng để nói tới chuyện lồng nhau').toBeGreaterThan(1);

    /* Với MỌI cặp lồng nhau (A chứa B) thì số vai của A phải lớn hơn B.
       Duyệt mọi cặp chứ không chỉ cặp liền kề: một hoán vị ở giữa vẫn giữ
       nguyên quan hệ của các cặp liền kề nếu chỉ nhìn hai hộp một. */
    const cap = await page.evaluate(() => {
      const hs = [...document.querySelectorAll('[data-lop-quyen]:not([data-nhanh])')];
      const ra: { ngoai: string; trong: string; sn: number; st: number }[] = [];
      for (const a of hs) {
        for (const b of hs) {
          if (a !== b && a.contains(b)) {
            ra.push({
              ngoai: a.getAttribute('data-lop-quyen') ?? '',
              trong: b.getAttribute('data-lop-quyen') ?? '',
              sn: Number(a.getAttribute('data-so-vai')),
              st: Number(b.getAttribute('data-so-vai')),
            });
          }
        }
      }
      return ra;
    });

    expect(cap.length, 'không cặp lồng nhau nào — hình không phải hình lồng').toBeGreaterThan(0);
    for (const c of cap) {
      expect(
        c.sn,
        `"${c.ngoai}" (${c.sn} vai) bọc ngoài "${c.trong}" (${c.st} vai) — hộp ngoài phải RỘNG hơn`,
      ).toBeGreaterThan(c.st);
    }
  });

  test('không lớp quyền nào bị đánh rơi khỏi hình', async ({ page }) => {
    const vao = (await vaoBangThe(page)) || (await login(page));
    test.skip(!vao, LY_DO_BO_QUA);
    await page.goto('/quan-tri/vai-tro', { waitUntil: 'networkidle' });
    test.skip(
      await page.getByText(/không có quyền/i).count() > 0,
      'tài khoản kiểm thử không vào được khu Vận hành',
    );
    await expect(page.locator('[data-lop-quyen]').first()).toBeVisible();

    const tren = await page.evaluate(() =>
      [...document.querySelectorAll('[data-lop-quyen]')]
        // Lõi gộp nhãn hai lớp cùng tập vai (`A · B`) — tách ra để đối chiếu.
        .flatMap((e) => (e.getAttribute('data-lop-quyen') ?? '').split(' · ')),
    );

    const khai = soVaiCuaLopQuyen();
    expect(Object.keys(khai).length, 'đọc được bảng lớp quyền từ nguồn').toBeGreaterThan(3);
    for (const lop of Object.keys(khai)) {
      expect(tren, `lớp quyền "${lop}" có khai nhưng KHÔNG hiện trên sơ đồ`).toContain(lop);
    }
  });
});
