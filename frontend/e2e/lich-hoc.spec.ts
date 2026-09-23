import { existsSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

import { expect, test } from '@playwright/test';

import {
  LY_DO_THIEU_VAI,
  chiDoc,
  goiApi,
  taiKhoanCuaVai,
  trangTheoVai,
  vaoTheoVai,
} from './helpers';

/**
 * LỊCH HỌC NÂNG CẤP (§53, 24/09/2026) — đi bằng GIAO DIỆN, ở cả hai khổ máy.
 *
 * Bảng yêu cầu TopHSA tab "Nhi" #4; anh Sơn chốt 23/09: báo đổi lịch bằng chuông
 * + email cho HỌC VIÊN (không phụ huynh), phòng là chữ tự do, hình thức đặt theo
 * buổi và mặc định theo lớp. Backend có `teaching/tests_lich.py` gọi thẳng view
 * (18 đột biến đều đỏ) — tệp này canh phần view không thấy: tab có trên thanh
 * không, bộ lọc giữ qua chuyển tuần, cảnh báo trùng hiện VÀNG chứ không đỏ, ô
 * phòng tắt khi chọn trực tuyến, câu "đã báo N học viên", và thư thật sự ra đĩa.
 *
 * ── GHI GÌ, DỌN GÌ ─────────────────────────────────────────────────────────
 *
 * Phần chỉ đọc chạy luôn (`chiDoc`). Phần GHI mặc định TẮT (`E2E_GHI=1`): dựng
 * hai lớp "E2E tự dọn lịch …" cùng một phòng giả, xếp `audit2009.hv3` vào lớp B,
 * rồi xoá cả hai lớp ở `afterAll` (buổi học và ghi danh đi theo lớp). Dấu vết
 * còn lại: MỘT chuông "đổi lịch" trong hộp của em rà soát ấy, và một `.eml` ở
 * `.thu_email/` — Django dev PHẢI chạy với `EMAIL_CHE_DO_THU=1`, spec tự kiểm
 * điều đó bằng cách đòi tệp `.eml` xuất hiện. KHÔNG gửi phụ huynh ở bước nào.
 */

test.describe.configure({ mode: 'serial' });

const BAT = process.env.E2E_GHI === '1';
const LY_DO_TAT = 'luồng có GHI — chỉ chạy khi E2E_GHI=1 (dựng hai lớp tạm rồi xoá)';
const HOC_VU = 'Quản lý học vụ';
const EM = 'audit2009.hv3@example.com';
const PHONG = 'E2E-P9';
const THU_MUC_THU = join(process.cwd(), '..', '.thu_email');

let lopA: number | null = null;
let lopB: number | null = null;

test.afterAll(async ({ browser }) => {
  if (!BAT || (lopA === null && lopB === null)) return;
  const hv = await trangTheoVai(browser, HOC_VU);
  if (!hv) return;
  const hong: string[] = [];
  for (const id of [lopA, lopB]) {
    if (id === null) continue;
    const r = await goiApi(hv, 'DELETE', `/api/admin/classes/${id}?confirm=1`);
    if (r.ma >= 300) hong.push(`dọn lớp ${id}: ${r.ma} ${JSON.stringify(r.du)}`);
  }
  await hv.close();
  expect(hong, 'dọn dẹp sau spec lịch học').toEqual([]);
});

/** YYYY-MM-DD theo giờ MÁY (máy chạy e2e ở giờ Việt Nam). */
function ngay(d: Date) {
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

// ── Chỉ đọc ────────────────────────────────────────────────────────────────

test('học vụ: lịch tuần đủ bảy ngày, có lọc giảng viên, chuyển tuần giữ bộ lọc', async ({ page }) => {
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  await chiDoc(page);

  await page.goto('/giang-day/lich', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { level: 1, name: 'Lịch học' })).toBeVisible();
  await expect(page.locator('main ol > li')).toHaveCount(7);
  await expect(page.getByRole('combobox', { name: 'Giảng viên', exact: true })).toBeVisible();
  if (test.info().project.name === 'may-tinh') {
    // Thanh khu chỉ hiện đủ mục ở khổ rộng; điện thoại gập vào trình đơn.
    await expect(page.getByRole('link', { name: 'Lịch học', exact: true }).first()).toBeVisible();
  }

  const oLop = page.getByRole('combobox', { name: 'Lớp', exact: true });
  const lop = await oLop.locator('option').nth(1).getAttribute('value');
  test.skip(!lop, 'học vụ không thấy lớp nào để lọc');
  await oLop.selectOption(lop!);
  await page.getByRole('button', { name: 'Lọc', exact: true }).click();
  await page.waitForURL((u) => u.searchParams.get('lop') === lop);
  const tu = new URL(page.url()).searchParams.get('tu');

  await page.getByRole('link', { name: 'Tuần sau →' }).click();
  await page.waitForURL((u) => u.searchParams.get('tu') !== tu);
  const sau = new URL(page.url()).searchParams;
  expect(sau.get('lop'), 'chuyển tuần làm rơi bộ lọc lớp').toBe(lop);
  const cach = (Date.parse(`${sau.get('tu')}T00:00:00Z`) - Date.parse(`${tu}T00:00:00Z`)) / 86_400_000;
  expect(cach).toBe(7);

  await page.getByRole('link', { name: 'Bỏ lọc' }).click();
  await page.waitForURL((u) => !u.searchParams.has('lop'));
  expect(new URL(page.url()).searchParams.get('tu'), 'bỏ lọc phải GIỮ tuần đang xem').toBe(sau.get('tu'));
});

test('giảng viên: không có ô lọc giảng viên; ngày gõ sai trên URL có đường về', async ({ page }) => {
  test.skip(!taiKhoanCuaVai('Giảng viên'), LY_DO_THIEU_VAI);
  expect(await vaoTheoVai(page, 'Giảng viên')).toBe(true);
  await chiDoc(page);

  await page.goto('/giang-day/lich', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { level: 1, name: 'Lịch học' })).toBeVisible();
  await expect(page.getByRole('combobox', { name: 'Lớp', exact: true })).toBeVisible();
  await expect(page.getByRole('combobox', { name: 'Giảng viên', exact: true })).toHaveCount(0);

  await page.goto('/giang-day/lich?tu=2026-13-45', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('[data-chan="loi"]')).toBeVisible();
  await page.getByRole('link', { name: 'Xem lịch tuần này' }).click();
  await expect(page.getByRole('heading', { level: 1, name: 'Lịch học' })).toBeVisible();
});

test('học viên mở lịch gộp: bị chặn theo vai, không phải lỗi máy chủ', async ({ page }) => {
  test.skip(!taiKhoanCuaVai('Học viên'), LY_DO_THIEU_VAI);
  test.skip(!(await vaoTheoVai(page, 'Học viên')), 'tài khoản học viên rà soát không đăng nhập được');
  await chiDoc(page);
  await page.goto('/giang-day/lich', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('[data-chan="vai"]')).toBeVisible();
});

// ── Có ghi ─────────────────────────────────────────────────────────────────

test('tạo buổi trùng phòng lớp khác → dải VÀNG; đổi sang trực tuyến → báo em (chuông + thư); lịch gộp thấy đúng', async ({ page, browser }) => {
  test.skip(!BAT, LY_DO_TAT);
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  // Hai khổ máy chạy nối nhau trên CÙNG dữ liệu — lớp của khổ trước đã dọn ở
  // afterAll của khổ ấy, khổ này dựng lại từ đầu.
  lopA = lopB = null;

  const hv = await trangTheoVai(browser, HOC_VU);
  expect(hv, 'không đăng nhập được học vụ').toBeTruthy();
  const tem = `${test.info().project.name} ${new Date().toISOString().slice(0, 16)}`;
  const taoLop = async (ten: string) => {
    const r = await goiApi(hv!, 'POST', '/api/admin/classes', {
      name: ten, course_id: 'hsa_quantitative', capacity: 5, status: 'active', mode: 'offline', room: PHONG,
    });
    expect(r.ma, `tạo lớp: ${JSON.stringify(r.du)}`).toBe(201);
    return (r.du as { id: number }).id;
  };
  const tenA = `E2E tự dọn lịch A ${tem}`;
  const tenB = `E2E tự dọn lịch B ${tem}`;
  lopA = await taoLop(tenA);
  lopB = await taoLop(tenB);

  // Giờ học: 20 ngày nữa, 19:00 — xa mọi lớp thật, và là buổi SẮP TỚI (mới báo).
  const luc = new Date(Date.now() + 20 * 86_400_000);
  const ngayHoc = ngay(luc);
  const gio = `${ngayHoc}T19:00`;
  const a1 = await goiApi(hv!, 'POST', `/api/teach/classes/${lopA}/sessions`, { starts_at: gio, duration_minutes: 90 });
  expect(a1.ma, JSON.stringify(a1.du)).toBe(201);
  const xep = await goiApi(hv!, 'POST', `/api/admin/classes/${lopB}/members`, { emails: [EM] });
  expect(xep.ma, JSON.stringify(xep.du)).toBeLessThan(300);
  const tim = await goiApi(hv!, 'GET', `/api/admin/users?q=${encodeURIComponent(EM)}`);
  const emId = ((tim.du as { users: { id: number; email: string }[] }).users.find((u) => u.email === EM))?.id;
  expect(emId, 'không tìm được id của em rà soát').toBeTruthy();
  await hv!.close();

  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);

  // ① Tạo buổi ở lớp B đúng giờ buổi của lớp A, cùng phòng (theo lớp).
  await page.goto(`/giang-day/buoi-hoc/${lopB}`, { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: 'Tạo buổi học' }).click();
  await page.getByLabel('Bắt đầu lúc').fill(gio);
  await expect(page.getByRole('combobox', { name: 'Hình thức', exact: true }).locator('option').first()).toHaveText(`Theo lớp (Phòng ${PHONG})`);
  await page.getByRole('button', { name: 'Tạo buổi', exact: true }).click();

  const vang = page.getByRole('status').filter({ hasText: 'Trùng lịch' });
  await expect(vang).toBeVisible({ timeout: 20_000 });
  await expect(vang).toContainText(`phòng ${PHONG} đã có lớp ${tenA}`);
  // Vàng, không đỏ: buổi ĐÃ lưu — dải lỗi đỏ không được xuất hiện. Trong `main`:
  // Next luôn có một `role="alert"` rỗng NGOÀI main (bộ đọc chuyển trang).
  await expect(page.getByRole('main').getByRole('alert')).toHaveCount(0);
  await expect(page.getByText(`Phòng ${PHONG}`).first()).toBeVisible();

  // ② Sửa buổi ấy sang trực tuyến: ô phòng tắt, lưu xong báo đúng một em.
  const batDau = Date.now();
  await page.getByRole('button', { name: 'Sửa', exact: true }).click();
  await page.getByRole('combobox', { name: 'Hình thức', exact: true }).selectOption('online');
  await expect(page.getByLabel('Phòng', { exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Lưu buổi học' }).click();
  const tin = page.getByRole('status').filter({ hasText: 'Đã báo đổi lịch cho 1 học viên' });
  await expect(tin).toBeVisible({ timeout: 20_000 });
  // Hết trùng PHÒNG (buổi đã trực tuyến). KHÔNG đòi hết "Trùng lịch": em rà soát còn
  // học lớp AUDIT tối thứ 2/4 lúc 19:30 — ngày thử rơi vào thứ 4 thì cảnh báo trùng
  // HỌC VIÊN là đúng (đo 24/09: 14/10 là thứ 4). Phép kiểm không được phụ thuộc thứ.
  await expect(tin).not.toContainText(`phòng ${PHONG}`);

  // Thư ra đĩa (chế độ thử) — gửi trên luồng riêng nên chờ tối đa 15 giây.
  await expect.poll(() => {
    if (!existsSync(THU_MUC_THU)) return 0;
    return readdirSync(THU_MUC_THU)
      .filter((t) => t.startsWith('audit2009_hv3-') && statSync(join(THU_MUC_THU, t)).mtimeMs >= batDau - 1000)
      .length;
  }, { timeout: 15_000, message: 'không thấy .eml báo đổi lịch — Django có chạy với EMAIL_CHE_DO_THU=1 không?' })
    .toBeGreaterThan(0);

  // ③ Lịch gộp tuần ấy: thấy cả hai lớp, buổi B đã là "Trực tuyến".
  const tu = ngayHoc;
  const den = ngay(new Date(luc.getTime() + 6 * 86_400_000));
  await page.goto(`/giang-day/lich?tu=${tu}&den=${den}&lop=${lopB}`, { waitUntil: 'domcontentloaded' });
  const theB = page.locator('main ol li li').filter({ hasText: tenB });
  await expect(theB).toHaveCount(1);
  await expect(theB).toContainText('Trực tuyến');
  await expect(theB).toContainText('19:00–20:30');

  // ④ Lịch của RIÊNG em: có lớp B, không có lớp A (em không học A).
  await page.goto(`/giang-day/lich?tu=${tu}&den=${den}&hoc_vien=${emId}`, { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('status').filter({ hasText: 'Đang xem lịch của' })).toBeVisible();
  await expect(page.locator('main ol li li').filter({ hasText: tenB })).toHaveCount(1);
  await expect(page.locator('main ol li li').filter({ hasText: tenA })).toHaveCount(0);

  // ⑤ Biểu mẫu lớp đổ lại ĐÚNG hình thức + phòng (vòng đi–về ở giao diện thật).
  await page.goto('/quan-tri/lop-hoc', { waitUntil: 'domcontentloaded' });
  // Bấm lại tới khi form mở: ở khổ máy tính trang về nhanh hơn lúc React gắn xong,
  // cú bấm đầu rơi vào nút chưa có trình xử lý (đo 24/09 — khổ điện thoại không bị).
  await expect(async () => {
    await page.getByRole('row').filter({ hasText: tenA }).getByRole('button', { name: 'Sửa' }).click();
    await expect(page.getByRole('heading', { name: /^Sửa lớp:/ })).toBeVisible({ timeout: 1_000 });
  }).toPass({ timeout: 20_000 });
  await expect(page.getByRole('combobox', { name: 'Hình thức', exact: true })).toHaveValue('offline');
  await expect(page.getByLabel('Phòng (lớp tại trung tâm)')).toHaveValue(PHONG);
  await page.getByRole('button', { name: 'Huỷ', exact: true }).click();
});
