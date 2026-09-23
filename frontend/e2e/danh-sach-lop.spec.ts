import { expect, test } from '@playwright/test';

import { LY_DO_THIEU_VAI, chiDoc, goiApi, taiKhoanCuaVai, trangTheoVai, vaoTheoVai } from './helpers';

/**
 * DANH SÁCH LỚP LỌC ĐƯỢC (§54, 24/09/2026) — đi bằng GIAO DIỆN, hai khổ máy.
 *
 * TopHSA có ~400 lớp gia sư bên cạnh lớp nhóm; ghi chú họp: "quản lý lớp là
 * priority số 1". `teaching/tests_danh_sach_lop.py` gọi thẳng view (lọc, tổng
 * giữ khi trang rỗng, trần 3 em, danh sách gọn). Tệp này canh phần view không
 * thấy: chip đếm có bấm được không, bộ lọc có nằm trên URL (gửi link cho đồng
 * nghiệp), câu rỗng nói "không khớp bộ lọc" chứ không "chưa có lớp nào", và góp ý
 * câu chữ của khách ("Tất cả" thay "Mọi …", "Môn học" thay "Hợp phần").
 *
 * Phần GHI (`E2E_GHI=1`): dựng MỘT lớp "E2E tự dọn gia sư …" bằng biểu mẫu thật,
 * xếp ba em rà soát + trợ giảng rà soát vào, rồi xoá lớp ở `afterAll`.
 */

test.describe.configure({ mode: 'serial' });

const BAT = process.env.E2E_GHI === '1';
const LY_DO_TAT = 'luồng có GHI — chỉ chạy khi E2E_GHI=1 (dựng một lớp tạm rồi xoá)';
const HOC_VU = 'Quản lý học vụ';
const DUONG = '/quan-tri/lop-hoc';
const EM = ['audit2009.hv1@example.com', 'audit2009.hv2@example.com', 'audit2009.hv3@example.com'];
const TG = 'audit2009.tg@example.com';

let lopTam: number | null = null;
let lopGiaSu: number | null = null;

test.afterAll(async ({ browser }) => {
  if (!BAT || (lopTam === null && lopGiaSu === null)) return;
  const hv = await trangTheoVai(browser, HOC_VU);
  if (!hv) return;
  const hong: string[] = [];
  for (const id of [lopTam, lopGiaSu]) {
    if (id === null) continue;
    // Buổi học + ghi danh đi theo lớp (xoá có xác nhận).
    const r = await goiApi(hv, 'DELETE', `/api/admin/classes/${id}?confirm=1`);
    if (r.ma >= 300) hong.push(`dọn lớp ${id}: ${r.ma} ${JSON.stringify(r.du)}`);
  }
  await hv.close();
  expect(hong, 'dọn dẹp sau spec danh sách lớp').toEqual([]);
});

// ── Chỉ đọc ────────────────────────────────────────────────────────────────

test('học vụ: chip loại lớp bấm là lọc, bấm lại là bỏ; tổng dưới bảng khớp số trên chip', async ({ page }) => {
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  await chiDoc(page);

  await page.goto(DUONG, { waitUntil: 'domcontentloaded' });
  const chip = page.getByRole('navigation', { name: 'Lọc nhanh theo loại lớp' });
  await expect(chip.getByRole('link')).toHaveCount(2);
  const giaSu = chip.getByRole('link', { name: /^Gia sư \d+$/ });
  await expect(chip.getByRole('link', { name: /^Lớp nhóm \d+$/ })).toBeVisible();
  const n = Number((await giaSu.innerText()).match(/\d+/)![0]);

  await giaSu.click();
  await page.waitForURL((u) => u.searchParams.get('loai') === 'gia_su');
  await expect(giaSu).toHaveAttribute('aria-current', 'true');
  const main = page.getByRole('main');
  // Tổng dưới bảng đếm ĐÚNG tập đang lọc — cùng con số trên chip. 0 lớp thì chỉ
  // ô trống nói (không lặp "0 lớp" bên dưới).
  if (n === 0) {
    await expect(main.getByText('Không có lớp khớp bộ lọc')).toBeVisible();
    await expect(main.getByText(/^0 lớp$/)).toHaveCount(0);
  } else {
    await expect(main.getByText(new RegExp(`(^|· )${n} lớp$`))).toBeVisible();
  }

  await giaSu.click();
  await page.waitForURL((u) => !u.searchParams.has('loai'));
});

test('học vụ: câu chữ theo góp ý TopHSA — "Tất cả" không "Mọi …", "Môn học" không "Hợp phần"', async ({ page }) => {
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  await chiDoc(page);

  await page.goto(DUONG, { waitUntil: 'domcontentloaded' });
  const loc = page.getByRole('search', { name: 'Lọc danh sách lớp' });
  await expect(loc).toBeVisible();
  const tuyChon = await loc.locator('option').allTextContents();
  expect(tuyChon.filter((t) => /^\s*Mọi\b/.test(t)), 'ô lọc còn chữ "Mọi …"').toEqual([]);
  expect(tuyChon.filter((t) => t.trim() === 'Tất cả').length).toBeGreaterThanOrEqual(2);
  // Điều kiện phụ gập lại khi chưa dùng (màn đầu điện thoại) — và TỰ MỞ khi đang dùng.
  await expect(loc.getByRole('combobox', { name: 'Trạng thái', exact: true })).toBeHidden();
  await page.goto(`${DUONG}?tt=active`, { waitUntil: 'domcontentloaded' });
  await expect(loc.getByRole('combobox', { name: 'Trạng thái', exact: true })).toHaveValue('active');
  await expect(loc.locator('summary')).toHaveText(/Lọc thêm · 1 đang chọn$/);

  const main = page.getByRole('main');
  await expect(main).not.toContainText('Hợp phần');
  await page.getByRole('button', { name: 'Thêm lớp' }).click();
  const form = page.getByRole('group', { name: 'Thêm lớp' });
  await expect(form.getByRole('combobox', { name: 'Môn học', exact: true })).toBeVisible();
  await expect(form.getByRole('combobox', { name: 'Loại lớp', exact: true })).toHaveValue('nhom');
});

test('học vụ: tìm ra rỗng nói "không khớp bộ lọc" + Bỏ lọc; trang quá xa có đường về', async ({ page }) => {
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  await chiDoc(page);

  await page.goto(DUONG, { waitUntil: 'domcontentloaded' });
  const loc = page.getByRole('search', { name: 'Lọc danh sách lớp' });
  await loc.getByRole('textbox', { name: 'Tìm' }).fill('zzz-khong-co-lop-nao-e2e');
  await loc.getByRole('button', { name: 'Lọc', exact: true }).click();
  await page.waitForURL((u) => u.searchParams.get('q') === 'zzz-khong-co-lop-nao-e2e');
  const main = page.getByRole('main');
  await expect(main.getByText('Không có lớp khớp bộ lọc')).toBeVisible();
  await expect(main.getByText('Chưa có lớp nào')).toHaveCount(0);
  await loc.getByRole('link', { name: 'Bỏ lọc' }).click();
  await page.waitForURL((u) => u.pathname === DUONG && u.search === '');

  // Trang vượt quá số trang (link cũ sau khi lớp bị xoá bớt) — không được trắng trơn.
  await page.goto(`${DUONG}?trang=9999`, { waitUntil: 'domcontentloaded' });
  const ve = main.getByRole('link', { name: 'Về trang 1' });
  const coLop = await page.getByRole('navigation', { name: 'Phân trang danh sách lớp' }).count();
  test.skip(!coLop, 'học vụ không thấy lớp nào — không có trang nào để vượt');
  await ve.click();
  await page.waitForURL((u) => !u.searchParams.has('trang'));
});

// ── Có ghi ─────────────────────────────────────────────────────────────────

test('tạo lớp GIA SƯ bằng biểu mẫu → xếp 3 em + trợ giảng → hàng hiện chip, tên em, TG; lọc theo trợ giảng ra lớp ấy', async ({ page, browser }) => {
  test.skip(!BAT, LY_DO_TAT);
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  lopTam = null;
  const ten = `E2E tự dọn gia sư ${test.info().project.name} ${new Date().toISOString().slice(0, 16)}`;

  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  await page.goto(DUONG, { waitUntil: 'domcontentloaded' });
  await expect(async () => {
    await page.getByRole('button', { name: 'Thêm lớp' }).click();
    await expect(page.getByRole('group', { name: 'Thêm lớp' })).toBeVisible({ timeout: 2_000 });
  }).toPass({ timeout: 20_000 });
  const form = page.getByRole('group', { name: 'Thêm lớp' });
  await form.getByRole('textbox', { name: 'Tên lớp' }).fill(ten);
  await form.getByRole('combobox', { name: 'Loại lớp', exact: true }).selectOption('gia_su');
  await form.getByRole('button', { name: 'Tạo lớp' }).click();
  await expect(page.getByText(`Đã tạo lớp "${ten}".`)).toBeVisible({ timeout: 20_000 });

  const hv = await trangTheoVai(browser, HOC_VU);
  expect(hv, 'không đăng nhập được học vụ').toBeTruthy();
  const tim = await goiApi(hv!, 'GET', `/api/admin/classes?q=${encodeURIComponent(ten)}`);
  const lop = (tim.du as { classes: { id: number; classType: string }[] }).classes;
  expect(lop.length, JSON.stringify(tim.du)).toBe(1);
  lopTam = lop[0].id;
  expect(lop[0].classType, 'ô "Loại lớp" chọn Gia sư mà máy chủ lưu khác').toBe('gia_su');

  const xep = await goiApi(hv!, 'POST', `/api/admin/classes/${lopTam}/members`, { emails: [...EM, TG] });
  expect(xep.ma, JSON.stringify(xep.du)).toBeLessThan(300);
  const kq = xep.du as { added: unknown[]; full?: unknown[] };
  // Trợ giảng KHÔNG chiếm chỗ của em: ba em + một TG đều vào, không ai bị "đầy".
  expect(kq.added.length, JSON.stringify(xep.du)).toBe(4);
  expect(kq.full ?? []).toEqual([]);
  // Id trợ giảng lấy từ `assistants` của chính danh sách lớp — `/api/admin/users`
  // của học vụ CHỈ trả học viên (đúng luật phân quyền, không phải lỗi).
  const tgId = (tim.du as { assistants: { id: number; email: string }[] }).assistants
    .find((u) => u.email === TG)?.id;
  expect(tgId, 'danh sách lớp không trả trợ giảng rà soát trong `assistants`').toBeTruthy();
  await hv!.close();

  await page.goto(`${DUONG}?q=${encodeURIComponent(ten)}`, { waitUntil: 'domcontentloaded' });
  const main = page.getByRole('main');
  const hang = main.getByRole('row').filter({ hasText: ten });
  await expect(hang).toHaveCount(1);
  await expect(hang).toContainText('Gia sư');
  await expect(hang).toContainText(/Em: .+, .+, .+/);
  await expect(hang).toContainText('TG: ');

  // Lọc theo NGƯỜI: mở "Lọc thêm", chọn trợ giảng → lớp vẫn ra, ô Tìm giữ nguyên.
  const loc = page.getByRole('search', { name: 'Lọc danh sách lớp' });
  await loc.locator('summary').click();
  await loc.getByRole('combobox', { name: 'Giáo viên / trợ giảng' }).selectOption(String(tgId));
  await loc.getByRole('button', { name: 'Lọc', exact: true }).click();
  await page.waitForURL((u) => u.searchParams.get('gv') === String(tgId));
  expect(new URL(page.url()).searchParams.get('q'), 'lọc người làm rơi ô tìm').toBe(ten);
  await expect(main.getByRole('row').filter({ hasText: ten })).toHaveCount(1);
});

test('TẠO NHANH lớp gia sư (1.2b): tìm em → chọn giảng viên + T3/T5 → xem trước → tạo → lớp có em và buổi', async ({ page, browser }) => {
  test.skip(!BAT, LY_DO_TAT);
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  lopGiaSu = null;
  const ten = `E2E tự dọn gia sư nhanh ${test.info().project.name} ${new Date().toISOString().slice(0, 16)}`;

  const hv = await trangTheoVai(browser, HOC_VU);
  expect(hv, 'không đăng nhập được học vụ').toBeTruthy();
  const ds = await goiApi(hv!, 'GET', '/api/admin/classes?per_page=1');
  const gv = (ds.du as { teachers: { id: number; email: string }[] }).teachers.find((t) => t.email === 'audit2009.gv@example.com');
  expect(gv, 'danh sách giảng viên thiếu giảng viên rà soát').toBeTruthy();

  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  await page.goto(DUONG, { waitUntil: 'domcontentloaded' });
  await expect(async () => {
    await page.getByRole('button', { name: 'Tạo lớp gia sư' }).click();
    await expect(page.getByRole('group', { name: 'Tạo lớp gia sư' })).toBeVisible({ timeout: 2_000 });
  }).toPass({ timeout: 20_000 });
  const khung = page.getByRole('group', { name: 'Tạo lớp gia sư' });

  // Bấm "Xem trước" khi chưa chọn em → câu lỗi nói đúng ô, KHÔNG gọi máy chủ.
  await khung.getByRole('button', { name: 'Xem trước' }).click();
  await expect(khung.getByRole('alert')).toHaveText('Chọn học viên cho lớp gia sư.');

  await khung.getByRole('textbox', { name: 'Tìm học viên' }).fill(EM[0]);
  await khung.getByRole('button', { name: 'Tìm', exact: true }).click();
  await khung.getByRole('list', { name: 'Kết quả tìm học viên' }).getByRole('button').first().click();
  await expect(khung.getByText(EM[0])).toBeVisible();

  await khung.getByRole('combobox', { name: 'Giảng viên', exact: true }).selectOption(String(gv!.id));
  await khung.getByRole('textbox', { name: 'Tên lớp (không bắt buộc)' }).fill(ten);
  await khung.getByText('T3', { exact: true }).click();
  await khung.getByText('T5', { exact: true }).click();
  await khung.getByRole('button', { name: 'Xem trước' }).click();
  const xem = khung.getByRole('status');
  await expect(xem).toContainText(ten, { timeout: 20_000 });
  await expect(xem).toContainText('T3, T5 · 19:30–21:00');
  const so = Number((await xem.getByText(/\d+ buổi sẽ tạo/).innerText()).match(/\d+/)![0]);
  expect(so, 'lịch 12 tuần T3/T5 phải ra ~24 buổi').toBeGreaterThanOrEqual(20);

  // Sửa một ô → bản xem trước hết hiệu lực, nút lại là "Xem trước" (không tạo theo bản cũ).
  await khung.getByText('T3', { exact: true }).click();
  await expect(khung.getByRole('button', { name: 'Xem trước' })).toBeVisible();
  await khung.getByText('T3', { exact: true }).click();
  await khung.getByRole('button', { name: 'Xem trước' }).click();
  await expect(khung.getByRole('status')).toContainText(`${so} buổi sẽ tạo`, { timeout: 20_000 });

  await khung.getByRole('button', { name: 'Tạo lớp gia sư' }).click();
  await expect(page.getByText(`Đã tạo lớp "${ten}" · ${so} buổi.`)).toBeVisible({ timeout: 20_000 });

  const tim = await goiApi(hv!, 'GET', `/api/admin/classes?q=${encodeURIComponent(ten)}`);
  const lop = (tim.du as { classes: { id: number; classType: string; members: number; teacherId: number }[] }).classes;
  expect(lop.length, JSON.stringify(tim.du)).toBe(1);
  lopGiaSu = lop[0].id;
  expect([lop[0].classType, lop[0].members, lop[0].teacherId]).toEqual(['gia_su', 1, gv!.id]);
  const buoi = await goiApi(hv!, 'GET', `/api/teach/classes/${lopGiaSu}/sessions`);
  expect(buoi.ma, JSON.stringify(buoi.du)).toBe(200);
  await hv!.close();

  // Hàng mới trong danh sách: chip Gia sư + tên em.
  await page.goto(`${DUONG}?q=${encodeURIComponent(ten)}`, { waitUntil: 'domcontentloaded' });
  const hang = page.getByRole('main').getByRole('row').filter({ hasText: ten });
  await expect(hang).toContainText('Gia sư');
  await expect(hang).toContainText('Em: ');
});
