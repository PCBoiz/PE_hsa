import { expect, test } from '@playwright/test';

import { LY_DO_THIEU_VAI, goiApi as goi, taiKhoanCuaVai, trangTheoVai, vaoTheoVai } from './helpers';

/**
 * LUỒNG GIẢNG DẠY — điểm danh và đường dẫn phụ huynh, đi trọn bằng GIAO DIỆN,
 * ở cả hai khổ máy.
 *
 * ── VÌ SAO CÓ TỆP NÀY (23/09/2026) ────────────────────────────────────────
 *
 * Tới hôm nay bộ e2e chỉ canh CẤU TRÚC (khung, tràn ngang, điều hướng). Không
 * phép kiểm nào bấm "Điểm danh" rồi đọc lại xem nó có lưu thật không — trong khi
 * đây là việc giảng viên làm nhiều nhất, và `Việc hôm nay` gọi nó là "lỗi hay
 * gặp nhất và khó thấy nhất" (buổi chưa tick thì không vào chuyên cần, tờ phụ
 * huynh báo thiếu). Backend có `tests_luong_erp.py` đi cùng luồng — nhưng gọi
 * thẳng view, nên nút bấm, trạng thái "Chưa lưu", và bố cục ở 390px không ai canh.
 *
 * ── TỰ DỰNG LỚP, TỰ DỌN — VÀ MẶC ĐỊNH TẮT ─────────────────────────────────
 *
 * Tệp này GHI: tạo một lớp, xếp học viên, tạo buổi, điểm danh. Nó không được
 * đụng lớp của ai — ngày 23/09 lớp 7586 đã được giao cho tài khoản dùng thử thật.
 * Nên nó dựng lớp riêng tên "E2E tự dọn …" và XOÁ lớp ấy ở `afterAll` (kéo theo
 * buổi và điểm danh qua `ON DELETE CASCADE`).
 *
 * Mặc định TẮT (`E2E_GHI=1` mới chạy): trong vài chục giây lớp ấy tồn tại, học vụ
 * nào đang mở "Lớp học" cũng thấy nó. Lúc có người dùng thử thật trên hệ thống thì
 * đó là thứ họ không nên phải thấy.
 *
 * KHÔNG gửi gì cho phụ huynh ở bất cứ bước nào.
 */

test.describe.configure({ mode: 'serial' });

const BAT = process.env.E2E_GHI === '1';
const LY_DO_TAT = 'luồng có GHI — chỉ chạy khi E2E_GHI=1 (tạo rồi xoá một lớp riêng)';

type NguoiHoc = { id: number; ten: string };

let lopId: number | null = null;
let buoiId: number | null = null;
let hocVien: NguoiHoc[] = [];

test.beforeAll(async ({ browser }) => {
  if (!BAT) return;
  if (!taiKhoanCuaVai('Quản lý học vụ') || !taiKhoanCuaVai('Giảng viên') || !taiKhoanCuaVai('Học viên')) return;

  // Ba học viên rà soát — lấy id thật bằng cách đăng nhập, không đoán.
  const hvTk = ['audit2009.hv1@example.com', 'audit2009.hv2@example.com'];
  const gv = await trangTheoVai(browser, 'Giảng viên');
  const hv = await trangTheoVai(browser, 'Quản lý học vụ');
  if (!gv || !hv) return;
  const gvId = ((await goi(gv, 'GET', '/api/user')).du as { id: number }).id;

  // ── Lớp riêng ──
  const tao = await goi(hv, 'POST', '/api/admin/classes', {
    name: `E2E tự dọn ${new Date().toISOString().slice(0, 16)}`,
    course_id: 'hsa_quantitative', teacher_id: gvId, capacity: 10, status: 'active',
  });
  expect(tao.ma, `tạo lớp: ${JSON.stringify(tao.du)}`).toBe(201);
  lopId = (tao.du as { id: number }).id;

  /* Ngày vào lớp LÙI 14 ngày: buổi học tạo ở "hôm qua" phải nằm SAU ngày vào,
     không thì tờ phụ huynh tính em vào lớp sau buổi ấy và bỏ nó ra — đúng cái
     bẫy `tests_luong_erp.py` ghi là đã sập hai lần. */
  const vao = new Date(Date.now() - 14 * 864e5).toISOString().slice(0, 10);
  const xep = await goi(hv, 'POST', `/api/admin/classes/${lopId}/members`, { emails: hvTk, joined_at: vao });
  expect(xep.ma, `xếp học viên: ${JSON.stringify(xep.du)}`).toBeLessThan(300);

  // ── Buổi học đã diễn ra ──
  const buoi = await goi(gv, 'POST', `/api/teach/classes/${lopId}/sessions`, {
    starts_at: new Date(Date.now() - 864e5).toISOString(), duration_minutes: 90,
  });
  expect(buoi.ma, `tạo buổi: ${JSON.stringify(buoi.du)}`).toBeLessThan(300);
  const b = buoi.du as { id?: number; session?: { id: number } };
  buoiId = b.id ?? b.session?.id ?? null;

  /* Tên + id học viên, đọc lại từ chính sổ điểm danh của buổi.
     Khoá là `students` (`teaching/sessions.py::SessionAttendanceView.get`), và
     `name` đã là `name || email` — CÙNG chuỗi nút bấm dùng trong `aria-label`. */
  const so = await goi(gv, 'GET', `/api/teach/sessions/${buoiId}/attendance`);
  const dong = (so.du as { students?: { userId: number; name: string }[] })?.students ?? [];
  hocVien = dong.map((r) => ({ id: r.userId, ten: r.name }));

  await gv.close();
  await hv.close();
});

test.afterAll(async ({ browser }) => {
  if (!BAT || lopId === null) return;
  const hv = await trangTheoVai(browser, 'Quản lý học vụ');
  if (!hv) return;
  const xoa = await goi(hv, 'DELETE', `/api/admin/classes/${lopId}?confirm=1`);
  // Dọn KHÔNG được im lặng thất bại: một lớp "E2E" nằm lại là thứ học vụ thử thấy.
  expect(xoa.ma, `dọn lớp ${lopId}: ${JSON.stringify(xoa.du)}`).toBeLessThan(300);
  await hv.close();
});

test('giảng viên điểm danh bằng giao diện, và nó LƯU thật', async ({ page }) => {
  test.skip(!BAT, LY_DO_TAT);
  test.skip(!taiKhoanCuaVai('Giảng viên'), LY_DO_THIEU_VAI);
  expect(lopId, 'không dựng được lớp riêng — xem lỗi ở beforeAll').not.toBeNull();
  expect(hocVien.length, 'sổ điểm danh không có học viên nào').toBeGreaterThanOrEqual(2);

  expect(await vaoTheoVai(page, 'Giảng viên')).toBe(true);
  await page.goto(`/giang-day/buoi-hoc/${lopId}`, { waitUntil: 'domcontentloaded' });

  // Mở sổ của buổi (buổi duy nhất trong lớp riêng này).
  await page.getByRole('button', { name: 'Điểm danh', exact: true }).first().click();

  const [co, vang] = hocVien;
  await page.getByRole('button', { name: `Có mặt — ${co.ten}` }).click();
  await page.getByRole('button', { name: `Vắng — ${vang.ten}` }).click();

  // Trạng thái chưa lưu phải hiện — người dùng cần biết mình chưa bấm Lưu.
  await expect(page.getByText('Chưa lưu')).toBeVisible();

  const luu = page.getByRole('button', { name: 'Lưu điểm danh' });
  /* Ở 390px nút Lưu từng nằm ngoài khung nhìn (`SessionsClient.tsx`, 21/09).
     `click()` của Playwright tự cuộn tới nên không bắt được việc ấy — kiểm riêng
     rằng sau khi cuộn nó THẬT SỰ nằm trong khung. */
  await luu.scrollIntoViewIfNeeded();
  await expect(luu).toBeInViewport();
  await luu.click();
  await expect(page.getByText('Chưa lưu')).toHaveCount(0, { timeout: 15_000 });

  // Đọc lại từ MÁY CHỦ, không tin giao diện.
  const so = await goi(page, 'GET', `/api/teach/sessions/${buoiId}/attendance`);
  const dong = (so.du as { students?: { userId: number; status: string | null }[] })?.students ?? [];
  const trangThai = (id: number) => dong.find((r) => r.userId === id)?.status;
  expect(trangThai(co.id), `${co.ten}`).toBe('present');
  expect(trangThai(vang.id), `${vang.ten}`).toBe('absent');
});

test('buổi đã điểm danh biến khỏi "Việc hôm nay"', async ({ page }) => {
  test.skip(!BAT, LY_DO_TAT);
  expect(await vaoTheoVai(page, 'Giảng viên')).toBe(true);
  const vn = await goi(page, 'GET', '/api/teach/viec-hom-nay');
  expect(vn.ma).toBe(200);
  // Buổi của lớp riêng không được nằm trong danh sách "chưa điểm danh xong".
  expect(JSON.stringify(vn.du), 'buổi vừa điểm danh vẫn bị báo là chưa xong')
    .not.toContain(`"sessionId":${buoiId},`);
});

test('tờ phụ huynh đọc đúng buổi vừa điểm danh', async ({ page }) => {
  test.skip(!BAT, LY_DO_TAT);
  expect(await vaoTheoVai(page, 'Giảng viên')).toBe(true);
  const [co, vang] = hocVien;
  await page.goto(`/giang-day/bao-cao/${lopId}/${co.id}`, { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Con có tiến bộ không')).toBeVisible({ timeout: 60_000 });
  await expect(page.locator('[data-chan]')).toHaveCount(0);

  /* Đọc chuyên cần từ API tờ — CÙNG nguồn trang dựng (`parent_report.py::
     _chuyen_can`, dưới khoá `attendance`). Một buổi đã diễn ra, đã tick:
     em có mặt → present 1, em vắng → absent 1; và không buổi nào "chưa tick". */
  type ChuyenCan = { present: number; absent: number; sessionsCounted: number; sessionsUnmarked: number };
  for (const [em, coMat, vangMat] of [[co, 1, 0], [vang, 0, 1]] as const) {
    const to = await goi(page, 'GET', `/api/teach/classes/${lopId}/students/${em.id}/parent-report`);
    expect(to.ma).toBe(200);
    const cc = (to.du as { attendance?: ChuyenCan }).attendance;
    expect(cc, `${em.ten}: tờ không có khối chuyên cần`).toBeTruthy();
    expect(cc!.sessionsCounted, `${em.ten}: số buổi được tính`).toBe(1);
    expect(cc!.sessionsUnmarked, `${em.ten}: không được còn buổi chưa tick`).toBe(0);
    expect(cc!.present, `${em.ten}: có mặt`).toBe(coMat);
    expect(cc!.absent, `${em.ten}: vắng`).toBe(vangMat);
  }
});

/* ── VÒNG ĐỜI ĐƯỜNG DẪN PHỤ HUYNH ────────────────────────────────────────────
   Đúng việc giảng viên dùng thử sẽ làm: tạo đường dẫn → phụ huynh mở KHÔNG cần
   đăng nhập → gửi nhầm thì thu hồi → đường dẫn chết NGAY.

   Vế cuối là vế đáng canh nhất. Đường dẫn này ai cầm cũng đọc được học bạ của
   một đứa trẻ; "thu hồi" mà không thật sự chết thì nút ấy là một lời hứa suông.
   Ngày 22/09 tôi đã phải thu hồi tay một chìa rà soát còn sống, đã bị mở 15 lượt.

   KHÔNG gửi gì: chỉ tạo, mở, thu hồi. Chìa không bao giờ được in ra log. */
test('đường dẫn phụ huynh: mở được không cần đăng nhập, thu hồi là chết ngay', async ({ page, browser }) => {
  test.skip(!BAT, LY_DO_TAT);
  expect(await vaoTheoVai(page, 'Giảng viên')).toBe(true);
  const [co] = hocVien;

  await page.goto(`/giang-day/bao-cao/${lopId}/${co.id}`, { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Con có tiến bộ không')).toBeVisible({ timeout: 60_000 });

  await page.getByRole('button', { name: 'Tạo đường dẫn gửi phụ huynh' }).click();
  const o = page.getByRole('textbox', { name: 'Đường dẫn báo cáo gửi phụ huynh' }).first();
  await expect(o).toBeVisible({ timeout: 20_000 });
  const diaChi = await o.inputValue();
  expect(diaChi, 'đường dẫn phải trỏ vào /bc/…').toMatch(/\/bc\/[^/?#\s]{16,}$/);
  const duong = new URL(diaChi).pathname;           // chỉ giữ đường dẫn, không in ra

  /* Phụ huynh: một trình duyệt KHÔNG cookie, cùng khổ máy với lượt đang chạy. */
  const moAnDanh = async () => {
    const ctx = await browser.newContext({ viewport: page.viewportSize() ?? undefined });
    const p = await ctx.newPage();
    const r = await p.goto(duong, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(2500);
    const thay = await p.getByText('Con có tiến bộ không').count();
    await ctx.close();
    return { ma: r?.status() ?? 0, thay };
  };

  const truoc = await moAnDanh();
  expect(truoc.thay, 'phụ huynh phải đọc được tờ mà không cần đăng nhập').toBeGreaterThan(0);

  // ── Thu hồi, bằng giao diện, qua đúng bước xác nhận tại chỗ ──
  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Con có tiến bộ không')).toBeVisible({ timeout: 60_000 });
  await page.getByRole('button', { name: 'Thu hồi', exact: true }).first().click();
  await expect(page.getByText('Thu hồi? Phụ huynh sẽ không mở được nữa.')).toBeVisible();
  await page.getByRole('button', { name: 'Thu hồi', exact: true }).first().click();
  await expect(page.getByText('Thu hồi? Phụ huynh sẽ không mở được nữa.')).toHaveCount(0, { timeout: 15_000 });

  const sau = await moAnDanh();
  expect(sau.thay, 'đường dẫn ĐÃ THU HỒI mà phụ huynh vẫn đọc được tờ').toBe(0);
});
