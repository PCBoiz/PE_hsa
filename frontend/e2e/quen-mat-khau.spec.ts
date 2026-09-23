import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

import { expect, test } from '@playwright/test';

import { goiApi } from './helpers';

/**
 * QUÊN MẬT KHẨU QUA EMAIL (§52) — đi trọn bằng giao diện: màn đăng nhập → xin
 * đường dẫn → ĐỌC LÁ THƯ → mở đường dẫn → đặt mật khẩu → đăng nhập bằng mật
 * khẩu mới → đường dẫn cũ chết.
 *
 * ── ĐIỀU KIỆN CHẠY ───────────────────────────────────────────────────────
 *
 * Phần có ghi mặc định TẮT (`E2E_GHI=1`). Và máy chủ Django PHẢI chạy với
 * `EMAIL_CHE_DO_THU=1` + `FRONTEND_URL` trỏ về chính trang đang thử: thư được ghi
 * ra `.eml` (thư mục `EMAIL_THU_MUC_THU`, mặc định `<repo>/.thu_email/`), không
 * một byte nào rời máy. Không thấy lá thư mới trong thư mục ấy thì phép kiểm
 * DỪNG ĐỎ chứ không đoán — rất có thể máy chủ đang GỬI THẬT.
 *
 * ── CHỈ MỘT KHỔ CHO LUỒNG GHI ─────────────────────────────────────────────
 *
 * Mỗi tài khoản được xin tối đa 3 đường dẫn mỗi giờ (`TRAN_MOI_GIO`). Chạy luồng
 * ghi ở cả hai khổ là hai lượt; chạy lại thêm một lần trong giờ là chạm trần và
 * không có thư — đỏ oan. Nên luồng ghi chỉ chạy ở khổ máy tính; khổ điện thoại
 * kiểm hai trang và trạng thái "đường dẫn hỏng" (không xin chìa nào).
 *
 * Chỉ đụng `audit2009.hv3` — mật khẩu của em vốn được `ho-so-hoc-vien.spec.ts`
 * cấp lại mỗi lượt, không spec nào dựa vào nó. KHÔNG gửi gì cho ai.
 */

const BAT = process.env.E2E_GHI === '1';
const EM = 'audit2009.hv3@example.com';
const THU_MUC = process.env.EMAIL_THU_MUC_THU || join(process.cwd(), '..', '.thu_email');

/** Giải mã các phần base64 của một tệp `.eml`, trả về toàn bộ chữ đã giải. */
function chuTrongThu(tho: string): string {
  const dong = tho.split(/\r?\n/);
  let ra = '';
  for (let i = 0; i < dong.length; i++) {
    if (!/^Content-Transfer-Encoding:\s*base64/i.test(dong[i])) continue;
    let j = i + 1;
    while (j < dong.length && dong[j].trim() !== '') j++;          // hết phần đầu
    let b64 = '';
    for (j++; j < dong.length && dong[j].trim() && !dong[j].startsWith('--'); j++) b64 += dong[j].trim();
    ra += Buffer.from(b64, 'base64').toString('utf8') + '\n';
  }
  return ra;
}

/** Đợi lá thư đặt lại MỚI (sửa sau `tuLuc`) cho `EM`, trả `{duongDan, chia}`. */
async function doiThu(tuLuc: number): Promise<{ duongDan: string; chia: string }> {
  const han = Date.now() + 20_000;
  while (Date.now() < han) {
    if (existsSync(THU_MUC)) {
      for (const ten of readdirSync(THU_MUC)) {
        if (!ten.startsWith('audit2009_hv3-') || !ten.endsWith('.eml')) continue;
        const p = join(THU_MUC, ten);
        if (statSync(p).mtimeMs < tuLuc) continue;
        const m = /(\S+\/dat-lai-mat-khau)#chia=([A-Za-z0-9_-]+)/.exec(chuTrongThu(readFileSync(p, 'utf8')));
        if (m) return { duongDan: m[1], chia: m[2] };
      }
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`Không thấy lá thư mới trong ${THU_MUC}. Máy chủ có chạy EMAIL_CHE_DO_THU=1 không? `
    + '(Hoặc em đã chạm trần 3 đường dẫn/giờ.)');
}

test.describe.configure({ mode: 'serial' });

test('màn đăng nhập dẫn tới "Quên mật khẩu"; trang nói rõ lối cho tài khoản không có email', async ({ page }) => {
  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  await page.getByRole('link', { name: 'Đặt lại qua email' }).click();
  await page.waitForURL('**/quen-mat-khau');
  await expect(page.getByRole('heading', { name: 'Quên mật khẩu' })).toBeVisible();
  await expect(page.getByText('Tài khoản không có email?')).toBeVisible();
  // Sai dạng: báo ngay dưới ô, con trỏ về ô ấy — không gọi máy chủ.
  await page.getByLabel('Email của tài khoản').fill('0912345678');
  await page.getByRole('button', { name: 'Gửi đường dẫn đặt lại' }).click();
  await expect(page.locator('#qmk-email-error')).toBeVisible();
  await expect(page.locator('#qmk-email')).toBeFocused();
});

test('đường dẫn hỏng: báo ngay, chỉ lối xin đường dẫn mới, và xoá chìa khỏi thanh địa chỉ', async ({ page }) => {
  await page.goto('/dat-lai-mat-khau#chia=khong-phai-chia-that-0000000000000000000000', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('[data-chan="khong-thay"]')).toBeVisible({ timeout: 20_000 });
  await expect(page.getByRole('link', { name: 'Xin đường dẫn mới' })).toBeVisible();
  expect(new URL(page.url()).hash, 'chìa phải bị xoá khỏi thanh địa chỉ').toBe('');
});

test('email không có tài khoản: cùng MỘT câu trả lời', async ({ page }) => {
  await page.goto('/quen-mat-khau', { waitUntil: 'domcontentloaded' });
  const co = await goiApi(page, 'POST', '/auth/quen-mat-khau', { email: `khong-ai-${Date.now()}@example.com` });
  expect(co.ma).toBe(200);
  expect((co.du as { message: string }).message).toMatch(/^Nếu email này thuộc một tài khoản/);
});

test('trọn luồng: xin → đọc thư → đặt mật khẩu mới → đăng nhập → đường dẫn cũ chết', async ({ page, browser }, info) => {
  test.skip(!BAT, 'luồng có GHI — chỉ chạy khi E2E_GHI=1 (máy chủ chạy EMAIL_CHE_DO_THU=1)');
  test.skip(info.project.name !== 'may-tinh', 'luồng ghi chỉ chạy một khổ — trần 3 đường dẫn/giờ, xem đầu tệp');

  const tuLuc = Date.now() - 1000;
  await page.goto('/quen-mat-khau', { waitUntil: 'domcontentloaded' });
  await page.getByLabel('Email của tài khoản').fill(EM.toUpperCase());
  await page.getByRole('button', { name: 'Gửi đường dẫn đặt lại' }).click();
  await expect(page.getByRole('status')).toContainText('Nếu email này thuộc một tài khoản');

  const { duongDan, chia } = await doiThu(tuLuc);
  const goc = new URL(page.url()).origin;
  expect(duongDan, 'gốc đường dẫn trong thư phải là trang đang thử (FRONTEND_URL)').toBe(`${goc}/dat-lai-mat-khau`);

  const moi = `E2E-qmk-${Date.now().toString(36)}`;
  await page.goto(`/dat-lai-mat-khau#chia=${chia}`, { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Tài khoản a***@example.com')).toBeVisible({ timeout: 20_000 });
  expect(new URL(page.url()).hash, 'chìa phải bị xoá khỏi thanh địa chỉ ngay khi đọc').toBe('');

  // Mật khẩu yếu KHÔNG được đốt mất đường dẫn.
  await page.getByLabel('Mật khẩu mới', { exact: true }).fill('ngan');
  await page.getByLabel('Nhập lại mật khẩu mới').fill('ngan');
  await page.getByRole('button', { name: 'Đặt mật khẩu mới' }).click();
  await expect(page.locator('#dl-next-error')).toBeVisible();

  await page.getByLabel('Mật khẩu mới', { exact: true }).fill(moi);
  await page.getByLabel('Nhập lại mật khẩu mới').fill(moi);
  await page.getByRole('button', { name: 'Đặt mật khẩu mới' }).click();
  await page.waitForURL('**/login?vua-doi-mat-khau=1', { timeout: 20_000 });
  await expect(page.getByText('Đăng nhập lại bằng')).toBeVisible();

  // Đăng nhập bằng mật khẩu mới, ở một phiên sạch.
  const ctx = await browser.newContext();
  const p = await ctx.newPage();
  await p.goto(`${goc}/login`, { waitUntil: 'domcontentloaded' });
  await p.fill('#login-email', EM);
  await p.fill('#login-password', moi);
  await p.click('#loginBtn');
  await p.waitForURL('**/dashboard**', { timeout: 25_000 });
  await ctx.close();

  // Cùng đường dẫn, lần hai: đã chết.
  await page.goto(`/dat-lai-mat-khau#chia=${chia}`, { waitUntil: 'domcontentloaded' });
  await expect(page.locator('[data-chan="khong-thay"]')).toBeVisible({ timeout: 20_000 });
});
