import { expect, test, type Page } from '@playwright/test';

import { LY_DO_THIEU_VAI, chiDoc, goiApi, taiKhoanCuaVai, trangTheoVai, vaoBangThe, vaoTheoVai } from './helpers';

/**
 * VẬN HÀNH LỚP, luồng A2 (kế hoạch v2, 25/09/2026) — đi bằng GIAO DIỆN, hai khổ máy.
 *
 *   · V-o "Chấm công" (bảng TopHSA dòng 6.3) — học vụ mở trang, chọn tháng, tải Excel. Chỉ đọc.
 *   · V-n "Lịch sử thay đổi của lớp" (dòng 4 + 10) — học vụ mở trong Học viên của lớp. Chỉ đọc.
 *   · V-j "Nhập học viên từ tệp mẫu" (dòng 4) — CÓ GHI: tạo lớp tạm, nhập `audit2009.hv1`
 *     (tài khoản CÓ SẴN — không cấp tài khoản mới nào: tài khoản không xoá được), xoá lớp ở cuối.
 *   · V-i "Đang mở / Nháp" (dòng 5) — CÓ GHI: khoá TẠM do quản trị viên tạo, xoá ở cuối.
 *     Không bao giờ bấm trên ba khoá thật (mọi học viên mất bài ngay).
 *
 * Phần ghi chỉ chạy khi `E2E_GHI=1`. Không gửi gì cho phụ huynh.
 */
test.describe.configure({ mode: 'serial' });

const BAT = process.env.E2E_GHI === '1';
const LY_DO_TAT = 'luồng có GHI — chỉ chạy khi E2E_GHI=1 (lớp / khoá tạm, dọn ở afterAll)';
const HOC_VU = 'Quản lý học vụ';
const EM_CO_SAN = 'audit2009.hv1@example.com';
const DAU = `${Date.now().toString(36)}`;

let lopTam: number | null = null;
let khoaTam: string | null = null;

test.afterAll(async ({ browser }) => {
  const hong: string[] = [];
  if (lopTam !== null) {
    const hv = await trangTheoVai(browser, HOC_VU);
    if (hv) {
      const r = await goiApi(hv, 'DELETE', `/api/admin/classes/${lopTam}?confirm=1`);
      if (r.ma >= 300) hong.push(`xoá lớp ${lopTam}: ${r.ma}`);
      await hv.close();
    }
  }
  if (khoaTam !== null) {
    const ad = await browser.newPage();
    if (await vaoBangThe(ad)) {
      const r = await goiApi(ad, 'DELETE', `/api/admin/courses/${khoaTam}`);
      if (r.ma >= 300) hong.push(`xoá khoá ${khoaTam}: ${r.ma}`);
    }
    await ad.close();
  }
  expect(hong, 'dọn dẹp sau spec vận hành A2').toEqual([]);
});

type ChamCong = { thang: string; nguoi: { id: number; soBuoi: number }[] };

test('học vụ: Chấm công theo tháng — bảng khớp máy chủ, chọn tháng lên URL, Excel mang đúng tháng', async ({ page }) => {
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  await chiDoc(page);

  await page.goto('/quan-tri/cham-cong', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('[data-chan]')).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Chấm công giảng viên và trợ giảng' })).toBeVisible({ timeout: 30_000 });
  const api = (await goiApi(page, 'GET', '/api/admin/cham-cong')).du as ChamCong;
  const bang = page.getByRole('table');
  if (api.nguoi.length) {
    await expect(bang.locator('tbody tr')).toHaveCount(api.nguoi.length);
  }
  await expect(page.getByRole('link', { name: 'Tải Excel' })).toHaveAttribute('href', `/api/admin/cham-cong?thang=${api.thang}&dinh_dang=xlsx`);

  // Tháng trước: biểu mẫu GET thường → URL mang ?thang=, Excel theo đúng tháng ấy.
  const [y, m] = api.thang.split('-').map(Number);
  const truoc = m === 1 ? `${y - 1}-12` : `${y}-${String(m - 1).padStart(2, '0')}`;
  await page.getByLabel('Tháng').fill(truoc);
  await page.getByRole('button', { name: 'Xem' }).click();
  await page.waitForURL((u) => u.searchParams.get('thang') === truoc);
  await expect(page.getByRole('link', { name: 'Tải Excel' })).toHaveAttribute('href', new RegExp(`thang=${truoc}&dinh_dang=xlsx`));
});

test('học vụ: "Lịch sử thay đổi của lớp" mở trong Học viên, số thay đổi khớp máy chủ', async ({ page }) => {
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  await chiDoc(page);

  await page.goto('/quan-tri/lop-hoc', { waitUntil: 'domcontentloaded' });
  const nut = page.getByRole('button', { name: 'Học viên', exact: true }).first();
  await expect(nut).toBeVisible({ timeout: 30_000 });
  await nut.click();
  const khoi = page.locator('details', { hasText: 'Lịch sử thay đổi của lớp' });
  await expect(khoi).toBeVisible({ timeout: 30_000 });
  await khoi.locator('summary').click();
  await expect(khoi.getByText(/thay đổi — mới nhất ở trên|Lớp chưa có thay đổi nào được ghi/)).toBeVisible({ timeout: 30_000 });
  const tong = await khoi.getByText(/\d+ thay đổi — mới nhất ở trên/).count();
  if (tong) {
    await expect(khoi.getByRole('list', { name: 'Các thay đổi của lớp, mới nhất trước' }).locator('li').first()).toBeVisible();
  }
});

async function moHocVienCuaLop(page: Page, ten: string) {
  await page.goto(`/quan-tri/lop-hoc?q=${encodeURIComponent(ten)}`, { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: 'Học viên', exact: true }).first().click();
  await expect(page.getByRole('heading', { name: 'Nhập học viên từ tệp mẫu' })).toBeVisible({ timeout: 30_000 });
}

test('học vụ nhập học viên từ tệp: kiểm tra từng dòng rồi nhập, em có sẵn vào lớp, lịch sử lớp ghi lại', async ({ page }) => {
  test.skip(!BAT, LY_DO_TAT);
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);

  const ten = `E2E A2 nhập tệp ${DAU}`;
  const tao = await goiApi(page, 'POST', '/api/admin/classes', { name: ten, status: 'active' });
  expect(tao.ma).toBe(201);
  lopTam = (tao.du as { id: number }).id;

  await moHocVienCuaLop(page, ten);
  // Tệp mẫu tải được (liên kết thật, cookie đi kèm).
  const mau = await goiApi(page, 'GET', `/api/admin/classes/${lopTam}/nhap-hoc-vien/mau`);
  expect(mau.ma).toBe(200);

  const csv = 'Họ và tên,Email,Số điện thoại,Mã học viên\r\n'
    + `AUDIT2009 Nguyễn An,${EM_CO_SAN},,\r\n`
    + '=HYPERLINK("http://x"),,,\r\n';
  await page.locator('input[type="file"]').setInputFiles({ name: 'ds.csv', mimeType: 'text/csv', buffer: Buffer.from(csv, 'utf8') });
  await page.getByRole('button', { name: 'Kiểm tra tệp' }).click();
  const bang = page.getByRole('table', { name: 'Từng dòng của tệp danh sách' });
  await expect(bang).toBeVisible({ timeout: 30_000 });
  await expect(bang.getByText('Thêm vào lớp')).toBeVisible();
  await expect(bang.getByText('Lỗi', { exact: true })).toBeVisible();
  await expect(page.getByText(/Kết quả kiểm tra \(chưa ghi gì\)/)).toBeVisible();

  await page.getByRole('button', { name: 'Nhập 1 em vào lớp' }).click();
  await expect(page.getByText(/Đã nhập 1 học viên vào lớp/)).toBeVisible({ timeout: 30_000 });
  await expect(page.getByRole('table', { name: `Học viên của lớp ${ten}` }).getByText(EM_CO_SAN)).toBeVisible({ timeout: 30_000 });

  // Lịch sử lớp (V-n) có dòng "Nhập học viên từ tệp" và "Tạo lớp".
  const khoi = page.locator('details', { hasText: 'Lịch sử thay đổi của lớp' });
  await khoi.locator('summary').click();
  await expect(khoi.getByText('Nhập học viên từ tệp').first()).toBeVisible({ timeout: 30_000 });
  await expect(khoi.getByText('Tạo lớp').first()).toBeVisible();
});

test('quản trị viên chuyển khoá tạm về nháp rồi mở lại ở Giáo trình', async ({ page }) => {
  test.skip(!BAT, LY_DO_TAT);
  const vao = await vaoBangThe(page);
  test.skip(!vao, 'không có thẻ quản trị viên (scripts/cap_the.py)');
  const toi = (await goiApi(page, 'GET', '/api/user')).du as { role?: string };
  test.skip(toi.role !== 'admin', 'thẻ không phải quản trị viên');

  khoaTam = `e2e_a2_${DAU}`;
  const tao = await goiApi(page, 'POST', '/api/admin/courses', { id: khoaTam, title: `E2E A2 khoá ${DAU}` });
  expect(tao.ma).toBe(200);

  await page.goto('/giao-trinh', { waitUntil: 'domcontentloaded' });
  const hang = page.getByRole('row', { name: new RegExp(`E2E A2 khoá ${DAU}`) });
  await expect(hang.getByText('Đang mở')).toBeVisible({ timeout: 30_000 });
  page.once('dialog', (d) => void d.accept());
  await hang.getByRole('button', { name: `Chuyển khoá E2E A2 khoá ${DAU} về nháp` }).click();
  await expect(hang.getByText('Nháp', { exact: true })).toBeVisible({ timeout: 30_000 });
  const ds = (await goiApi(page, 'GET', '/api/admin/courses')).du as { courses: { id: string; is_published: boolean | null }[] };
  expect(ds.courses.find((c) => c.id === khoaTam)?.is_published).toBe(false);

  await hang.getByRole('button', { name: `Mở khoá E2E A2 khoá ${DAU} cho học viên` }).click();
  await expect(hang.getByText('Đang mở')).toBeVisible({ timeout: 30_000 });
});
