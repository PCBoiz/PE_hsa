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
 * HỒ SƠ HỌC VIÊN MỞ RỘNG — đi bằng GIAO DIỆN, ở cả hai khổ máy (23/09/2026).
 *
 * Sinh từ bảng yêu cầu TopHSA (dòng 3, 14 + tab "Nhi" #1) và các quyết định anh
 * Sơn chốt cùng ngày: học vụ vào được Tài khoản nhưng CHỈ thấy học viên; mã
 * HSA-xxxxx tự sinh; người tư vấn + nguồn chọn từ danh sách; tên đăng nhập tuỳ
 * chọn do học vụ đặt; giảng viên chỉ sửa mục tiêu + nguyện vọng của em lớp mình.
 * Backend có `teaching/tests_ho_so_hoc_vien.py` gọi thẳng view — tệp này canh
 * phần view không thấy: nút nào hiện, lỗi nằm ở đâu, con trỏ đi đâu, form có
 * lấy lại bản đã chuẩn hoá không, và đăng nhập bằng tên đăng nhập qua ô thật.
 *
 * ── GHI GÌ, TRẢ LẠI GÌ ─────────────────────────────────────────────────────
 *
 * Phần chỉ đọc chạy luôn (có `chiDoc`). Phần GHI mặc định TẮT (`E2E_GHI=1`), và
 * chỉ đụng `audit2009.hv3` — em rà soát không spec nào khác dùng — rồi TRẢ LẠI
 * mọi ô đã sửa ở `afterAll`. Còn sót hai dấu vết: cờ "trung tâm đã nhập liên hệ
 * phụ huynh" (§47) mang mốc thời gian của lượt chạy (em vốn đã bị khoá từ một
 * lượt dán cả lớp trước đó); và mật khẩu tạm của em được cấp lại mỗi lượt — mật
 * khẩu trong bảng rà soát vốn đã sai (đo 23/09: đăng nhập bằng email cũng 401).
 * Lớp riêng "E2E tự dọn hồ sơ …" bị xoá ở cuối.
 *
 * Cấp tài khoản MỚI chỉ đi tới bước "Kiểm tra trước": tạo thật thì để lại một
 * tài khoản không xoá được, mà học vụ dùng thử sẽ thấy nó trong danh sách. Phần
 * tạo thật + cấp mã ngay có phép kiểm backend canh.
 *
 * KHÔNG gửi gì cho phụ huynh ở bất cứ bước nào.
 */

test.describe.configure({ mode: 'serial' });

const BAT = process.env.E2E_GHI === '1';
const LY_DO_TAT = 'luồng có GHI — chỉ chạy khi E2E_GHI=1 (sửa hồ sơ một em rà soát rồi trả lại)';
const HOC_VU = 'Quản lý học vụ';
const EM = 'audit2009.hv3@example.com';

/** Ô spec này có thể đổi — đọc lúc đầu, trả lại ở cuối. */
const O_TRA_LAI = [
  'username', 'school', 'schoolGrade', 'region', 'studyGoal', 'aspiration',
  'enrollSource', 'consultantId', 'parentName', 'parentPhone', 'parentEmail',
] as const;

let emId: number | null = null;
let banGoc: Record<string, unknown> | null = null;
let lopId: number | null = null;

test.afterAll(async ({ browser }) => {
  if (!BAT || (banGoc === null && lopId === null)) return;
  const hv = await trangTheoVai(browser, HOC_VU);
  if (!hv) return;
  /* Làm CẢ HAI việc dọn rồi mới kêu. Bản đầu `expect` ngay sau bước trả hồ sơ:
     bước ấy hỏng (500) là lớp tạm không bao giờ được xoá — lớp 9494 nằm lại. */
  const hong: string[] = [];
  if (lopId !== null) {
    const xoa = await goiApi(hv, 'DELETE', `/api/admin/classes/${lopId}?confirm=1`);
    if (xoa.ma >= 300) hong.push(`dọn lớp ${lopId}: ${xoa.ma} ${JSON.stringify(xoa.du)}`);
  }
  if (banGoc && emId !== null) {
    const tra: Record<string, unknown> = {};
    for (const k of O_TRA_LAI) tra[k] = banGoc[k] ?? '';
    tra.consultantId = banGoc.consultantId ?? null;
    const r = await goiApi(hv, 'PATCH', `/api/admin/users/${emId}/profile`, tra);
    if (r.ma !== 200) hong.push(`trả lại hồ sơ ${EM}: ${r.ma} ${JSON.stringify(r.du)}`);
  }
  await hv.close();
  // Dọn KHÔNG được im lặng hỏng: thứ nằm lại là thứ người dùng thử nhìn thấy.
  expect(hong, 'dọn dẹp sau spec hồ sơ').toEqual([]);
});

// ── Chỉ đọc ────────────────────────────────────────────────────────────────

test('học vụ vào Tài khoản: chỉ học viên, không đổi vai, không khoá, không xuất CSV', async ({ page }) => {
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  await chiDoc(page);

  // Máy chủ là chốt thật — kiểm nó trước, rồi mới kiểm màn hình.
  const api = await goiApi(page, 'GET', '/api/admin/users?page=1&per_page=100');
  expect(api.ma).toBe(200);
  const du = api.du as {
    users: { role: string; studentCode: string | null }[];
    chiHocVien: boolean;
    roles: string[];
  };
  expect(du.chiHocVien).toBe(true);
  expect(du.roles).toEqual(['Học viên']);
  expect(du.users.length).toBeGreaterThan(0);
  expect(du.users.filter((u) => u.role !== 'Học viên'), 'học vụ thấy tài khoản không phải học viên').toEqual([]);
  expect(du.users.filter((u) => !/^HSA-\d{5}$/.test(u.studentCode ?? '')), 'học viên chưa có mã').toEqual([]);

  await page.goto('/quan-tri/tai-khoan', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('[data-chan]')).toHaveCount(0);
  await expect(page.getByRole('link', { name: /^Hồ sơ của / }).first()).toBeVisible({ timeout: 30_000 });
  // Ba thứ còn `IsAdminRole` phải VẮNG MẶT — không phải hiện rồi bấm ra 403.
  await expect(page.locator('select[aria-label^="Vai trò của"]')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Khoá', exact: true })).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Tải Excel (CSV)' })).toHaveCount(0);
  await expect(page.getByText(/HSA-\d{5}/).first()).toBeVisible();

  // Ô cấp hàng loạt chỉ cho chọn đúng một vai.
  await page.getByRole('button', { name: 'Mở ô nhập' }).click();
  await expect(page.getByLabel('Vai trò cấp cho cả danh sách').locator('option')).toHaveText(['Học viên']);
});

test('học vụ tìm một em theo email rồi mở Hồ sơ: đủ năm mục, nút Lưu tắt khi chưa đổi', async ({ page }) => {
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  await chiDoc(page);

  await page.goto('/quan-tri/tai-khoan', { waitUntil: 'domcontentloaded' });
  await page.getByLabel('Tìm tài khoản').fill(EM);
  // Tìm chạy sau 350 ms kể từ phím cuối — chờ tới khi còn đúng một hàng.
  await expect(page.getByRole('link', { name: /^Hồ sơ của / })).toHaveCount(1, { timeout: 20_000 });
  await expect(page.getByText(EM)).toBeVisible();
  await page.getByRole('link', { name: /^Hồ sơ của / }).click();
  await page.waitForURL(/\/quan-tri\/tai-khoan\/\d+$/);
  emId = Number(new URL(page.url()).pathname.split('/').pop());

  for (const tieuDe of ['Thông tin cá nhân', 'Tên đăng nhập', 'Học tập', 'Tuyển sinh', 'Phụ huynh']) {
    await expect(page.getByRole('heading', { name: tieuDe, exact: true })).toBeVisible();
  }
  await expect(page.getByText(/^HSA-\d{5}$/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Lưu hồ sơ' })).toBeDisabled();
  // Tám nguồn của `NGUON_TUYEN_SINH` + "Chưa chọn".
  await expect(page.locator('#hs-enrollSource option')).toHaveCount(9);
  // Email/SĐT chỉ đọc: không có ô nhập nào cho chúng.
  await expect(page.locator('#hs-email, #hs-phone')).toHaveCount(0);

  // Dòng thời gian (23/09/2026): cuối trang, mới nhất ở trên — mốc CŨ NHẤT của mọi
  // em là "Được cấp tài khoản", nên nó phải nằm ở dòng cuối.
  await expect(page.getByRole('heading', { name: 'Dòng thời gian', exact: true })).toBeVisible();
  const moc = page.locator('ol li');
  await expect(moc.last()).toContainText('Được cấp tài khoản');
  expect(await moc.count()).toBeGreaterThan(0);
});

test('học vụ mở hồ sơ NHÂN SỰ → bị chặn, nói rõ vì sao', async ({ page, browser }) => {
  test.skip(!taiKhoanCuaVai(HOC_VU) || !taiKhoanCuaVai('Giảng viên'), LY_DO_THIEU_VAI);
  const gv = await trangTheoVai(browser, 'Giảng viên');
  expect(gv, 'không đăng nhập được giảng viên').not.toBeNull();
  const gvId = ((await goiApi(gv!, 'GET', '/api/user')).du as { id: number }).id;
  await gv!.close();

  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  await chiDoc(page);
  await page.goto(`/quan-tri/tai-khoan/${gvId}`, { waitUntil: 'domcontentloaded' });
  await expect(page.locator('[data-chan="vai"]')).toBeVisible();
  await expect(page.getByText('Quản lý học vụ chỉ xem và sửa hồ sơ HỌC VIÊN', { exact: false })).toBeVisible();
});

// ── Có ghi ─────────────────────────────────────────────────────────────────

test('học vụ sửa hồ sơ bằng giao diện: lưu thật, form lấy lại bản đã chuẩn hoá', async ({ page }) => {
  test.skip(!BAT, LY_DO_TAT);
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  expect(emId, 'bước tìm em ở trên không chạy được').not.toBeNull();
  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);

  const goc = await goiApi(page, 'GET', `/api/admin/users/${emId}/profile`);
  expect(goc.ma).toBe(200);
  banGoc = (goc.du as { profile: Record<string, unknown> }).profile;

  await page.goto(`/quan-tri/tai-khoan/${emId}`, { waitUntil: 'domcontentloaded' });
  const dau = Date.now().toString(36);
  await page.fill('#hs-school', `THPT E2E ${dau}`);
  await page.fill('#hs-schoolGrade', '12A1');
  await page.fill('#hs-region', 'Hà Nội');
  await page.fill('#hs-studyGoal', `Mục tiêu E2E ${dau}`);
  await page.fill('#hs-aspiration', 'ĐH Bách khoa — CNTT');
  await page.selectOption('#hs-enrollSource', 'gioi_thieu');
  await page.selectOption('#hs-consultantId', { index: 1 });
  await page.fill('#hs-parentName', 'Phụ huynh E2E');
  await page.fill('#hs-parentPhone', '0912 345 678');
  await page.fill('#hs-parentEmail', 'PH.E2E@Example.com');
  await expect(page.getByText(/^\d+ ô chưa lưu$/)).toBeVisible();

  // Thanh Lưu dính đáy: phải nằm TRONG khung nhìn mà không cần cuộn (390px).
  const luu = page.getByRole('button', { name: 'Lưu hồ sơ' });
  await expect(luu).toBeInViewport();
  await luu.click();
  await expect(page.getByText(/^Đã lưu lúc/)).toBeVisible({ timeout: 20_000 });
  await expect(page.locator('#hs-parentPhone')).toHaveValue('0912345678');
  await expect(page.locator('#hs-parentEmail')).toHaveValue('ph.e2e@example.com');

  // Tải lại: đọc từ máy chủ, không phải từ state của form.
  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(page.locator('#hs-school')).toHaveValue(`THPT E2E ${dau}`);
  await expect(page.locator('#hs-enrollSource')).toHaveValue('gioi_thieu');
  await expect(page.locator('#hs-studyGoal')).toHaveValue(`Mục tiêu E2E ${dau}`);
  await expect(page.getByRole('button', { name: 'Lưu hồ sơ' })).toBeDisabled();
});

test('tên đăng nhập sai dạng: lỗi ngay dưới ô, con trỏ nhảy tới đó, không ô nào được lưu', async ({ page }) => {
  test.skip(!BAT, LY_DO_TAT);
  expect(emId).not.toBeNull();
  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  await page.goto(`/quan-tri/tai-khoan/${emId}`, { waitUntil: 'domcontentloaded' });

  await page.fill('#hs-username', 'ab');
  await page.fill('#hs-region', 'Huế');           // con trỏ đang ở ô KHÁC khi bấm Lưu
  await page.getByRole('button', { name: 'Lưu hồ sơ' }).click();
  await expect(page.locator('#hs-username-error')).toBeVisible();
  await expect(page.locator('#hs-username')).toBeFocused();
  await expect(page.locator('#hs-username')).toHaveAttribute('aria-invalid', 'true');

  // Máy chủ từ chối CẢ LƯỢT — khu vực không được lén đổi thành "Huế".
  const sau = await goiApi(page, 'GET', `/api/admin/users/${emId}/profile`);
  expect((sau.du as { profile: { region: string | null } }).profile.region).toBe('Hà Nội');
});

test('học vụ đặt tên đăng nhập + cấp lại mật khẩu → em vào được bằng tên ấy, gõ hoa cũng được', async ({ page, browser }) => {
  test.skip(!BAT, LY_DO_TAT);
  expect(emId).not.toBeNull();
  const ten = `e2e.hv3.${Date.now().toString(36)}`;

  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  await page.goto(`/quan-tri/tai-khoan/${emId}`, { waitUntil: 'domcontentloaded' });
  await page.fill('#hs-username', ten);
  await page.getByRole('button', { name: 'Lưu hồ sơ' }).click();
  await expect(page.getByText(/^Đã lưu lúc/)).toBeVisible({ timeout: 20_000 });

  /* Mật khẩu: KHÔNG tin bảng rà soát. Đo 23/09/2026: `hv3` đăng nhập bằng EMAIL
     cũng 401 — mật khẩu trong `.the/audit_tk.json` đã cũ. Học vụ cấp lại mật
     khẩu tạm bằng đúng nút của họ (mở cho học viên từ 20/09), rồi đọc chuỗi từ
     hộp thoại — cùng đường một học vụ thật đi khi em quên cả email lẫn mật khẩu. */
  await page.getByRole('link', { name: '← Danh sách tài khoản' }).click();
  await page.getByLabel('Tìm tài khoản').fill(EM);
  await expect(page.getByRole('link', { name: /^Hồ sơ của / })).toHaveCount(1, { timeout: 20_000 });
  page.once('dialog', (d) => void d.accept());
  await page.getByRole('button', { name: 'Đặt lại mật khẩu' }).click();
  const hop = page.getByRole('dialog');
  await expect(hop.locator('.font-mono')).not.toBeEmpty({ timeout: 20_000 });
  const mkTam = ((await hop.locator('.font-mono').textContent()) ?? '').trim();
  await hop.getByRole('button', { name: 'Đã đọc xong' }).click();

  // Phiên MỚI, chưa đăng nhập — gõ vào đúng ô thật của trang đăng nhập.
  const goc = new URL(page.url()).origin;
  const moi = await browser.newContext();
  const p = await moi.newPage();
  await p.goto(`${goc}/login`, { waitUntil: 'domcontentloaded' });
  await p.fill('#login-email', ten.toUpperCase());
  await p.fill('#login-password', mkTam);
  await p.click('#loginBtn');
  // Mật khẩu tạm → hệ thống bắt đổi trước khi vào: tới được trang ấy nghĩa là
  // máy chủ ĐÃ nhận ra em qua tên đăng nhập (sai tên thì ở lại /login, báo 401).
  await p.waitForURL('**/doi-mat-khau**', { timeout: 25_000 });
  await moi.close();
});

test('giảng viên sửa mục tiêu của em ngay trên tờ báo cáo; không in ra giấy', async ({ page, browser }) => {
  test.skip(!BAT, LY_DO_TAT);
  test.skip(!taiKhoanCuaVai('Giảng viên'), LY_DO_THIEU_VAI);
  expect(emId).not.toBeNull();

  // Lớp riêng: học vụ dựng, giảng viên dạy, xếp em vào. Không đụng lớp của ai.
  const hv = await trangTheoVai(browser, HOC_VU);
  const gv = await trangTheoVai(browser, 'Giảng viên');
  expect(hv && gv, 'không đăng nhập được học vụ / giảng viên').toBeTruthy();
  const gvId = ((await goiApi(gv!, 'GET', '/api/user')).du as { id: number }).id;
  const tao = await goiApi(hv!, 'POST', '/api/admin/classes', {
    name: `E2E tự dọn hồ sơ ${new Date().toISOString().slice(0, 16)}`,
    course_id: 'hsa_quantitative', teacher_id: gvId, capacity: 5, status: 'active',
  });
  expect(tao.ma, `tạo lớp: ${JSON.stringify(tao.du)}`).toBe(201);
  lopId = (tao.du as { id: number }).id;
  const xep = await goiApi(hv!, 'POST', `/api/admin/classes/${lopId}/members`, { emails: [EM] });
  expect(xep.ma, `xếp em: ${JSON.stringify(xep.du)}`).toBeLessThan(300);
  await hv!.close();
  await gv!.close();

  expect(await vaoTheoVai(page, 'Giảng viên')).toBe(true);
  await page.goto(`/giang-day/bao-cao/${lopId}/${emId}`, { waitUntil: 'domcontentloaded' });
  const khoi = page.locator('section[aria-labelledby="muc-tieu-em"]');
  await expect(khoi).toBeVisible({ timeout: 60_000 });
  // Đọc được điều HỌC VỤ vừa ghi ở bước trước — ô trống ở đây là mời xoá trắng.
  await expect(khoi.getByLabel('Mục tiêu học tập')).toHaveValue(/^Mục tiêu E2E /);

  const moi = `GV đặt mục tiêu ${Date.now().toString(36)}`;
  await khoi.getByLabel('Mục tiêu học tập').fill(moi);
  await khoi.getByRole('button', { name: 'Lưu', exact: true }).click();
  await expect(khoi.getByText('Đã lưu', { exact: true })).toBeVisible({ timeout: 20_000 });
  const doc = await goiApi(page, 'GET', `/api/teach/classes/${lopId}/students/${emId}/profile`);
  expect((doc.du as { studyGoal: string }).studyGoal).toBe(moi);

  // Ghi chú NỘI BỘ: bản in gửi phụ huynh không được có khối này.
  await page.emulateMedia({ media: 'print' });
  await expect(khoi).toBeHidden();
  await page.emulateMedia({ media: 'screen' });
});

test('trợ giảng không sửa được mục tiêu của em', async ({ page }) => {
  test.skip(!BAT, LY_DO_TAT);
  test.skip(!taiKhoanCuaVai('Trợ giảng'), LY_DO_THIEU_VAI);
  expect(lopId).not.toBeNull();
  expect(await vaoTheoVai(page, 'Trợ giảng')).toBe(true);
  const r = await goiApi(page, 'PATCH', `/api/teach/classes/${lopId}/students/${emId}/profile`,
    { studyGoal: 'trợ giảng ghi' });
  expect(r.ma).toBe(403);
});
