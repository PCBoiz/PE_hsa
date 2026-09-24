import { expect, test } from '@playwright/test';

import { LY_DO_THIEU_VAI, chiDoc, goiApi, openLesson, taiKhoanCuaVai, vaoTheoVai } from './helpers';

/**
 * MÔN MỞ QUA LỚP (mục 1.3, 24/09/2026 — góp ý TopHSA số 3) — đi bằng GIAO DIỆN, hai khổ.
 *
 * Khách: "mục Học không rõ để đăng ký hay để quản lý; giáo viên, trợ giảng cũng thấy nút
 * Đăng ký". Nay học viên học được môn của lớp em đang học, không có nút Đăng ký ở đâu;
 * nhân sự xem bài ở chế độ chỉ-đọc. Backend: `courses/tests_truy_cap.py`.
 *
 * CHỈ ĐỌC (`chiDoc`). Em rà soát `audit2009.hv*` học lớp AUDIT — môn của lớp đọc từ
 * máy chủ (`/api/courses`), không đoán tên môn trong phép kiểm.
 */

const HOC_VIEN = 'Học viên';
const GIANG_VIEN = 'Giảng viên';
/** Chữ của sản phẩm tự học cũ — không được còn ở trang khoá. */
const CHU_CU = /Đăng ký ngay|Hủy đăng ký|Huỷ đăng ký|Miễn phí|Chứng chỉ hoàn thành|Truy cập vĩnh viễn/;

async function monTheoQuyen(page: import('@playwright/test').Page) {
  const r = await goiApi(page, 'GET', '/api/courses');
  expect(r.ma, JSON.stringify(r.du)).toBe(200);
  const ds = r.du as { id: string; access?: string | null }[];
  return {
    mo: ds.filter((c) => c.access === 'hoc').map((c) => c.id),
    dong: ds.filter((c) => !c.access && c.id.startsWith('hsa_')).map((c) => c.id),
    xem: ds.filter((c) => c.access === 'xem').map((c) => c.id),
  };
}

test('học viên: môn của lớp mở, môn khác nói "chưa mở cho lớp của em" — không nút Đăng ký ở đâu', async ({ page }) => {
  test.skip(!taiKhoanCuaVai(HOC_VIEN), LY_DO_THIEU_VAI);
  test.skip(!(await vaoTheoVai(page, HOC_VIEN)), 'tài khoản học viên rà soát không đăng nhập được');
  await chiDoc(page);
  const { mo, dong } = await monTheoQuyen(page);
  test.skip(mo.length === 0, 'em rà soát chưa thuộc lớp nào có môn — xếp lớp cho audit2009.hv* trước');

  await page.goto(`/courses/${mo[0]}`, { waitUntil: 'domcontentloaded' });
  const main = page.getByRole('main');
  await expect(main.getByRole('button', { name: /Bắt đầu học|Tiếp tục học/ })).toBeVisible({ timeout: 20_000 });
  await expect(main).not.toContainText(CHU_CU);

  test.skip(dong.length === 0, 'lớp của em mở cả ba môn — không có môn đóng để kiểm');
  await page.goto(`/courses/${dong[0]}`, { waitUntil: 'domcontentloaded' });
  await expect(main.getByText('Môn này chưa mở cho lớp của em')).toBeVisible({ timeout: 20_000 });
  await expect(main.getByRole('button', { name: /Đăng ký|Bắt đầu học|Tiếp tục học/ })).toHaveCount(0);
  await expect(main).not.toContainText(CHU_CU);
});

test('giảng viên: mọi môn ở "Chế độ xem", mở bài đọc được, không nút Đăng ký', async ({ page }) => {
  test.skip(!taiKhoanCuaVai(GIANG_VIEN), LY_DO_THIEU_VAI);
  expect(await vaoTheoVai(page, GIANG_VIEN)).toBe(true);
  await chiDoc(page);
  const { mo, xem } = await monTheoQuyen(page);
  expect(mo, 'nhân sự không được ở chế độ học').toEqual([]);
  expect(xem.length, 'nhân sự phải xem được mọi môn').toBeGreaterThanOrEqual(3);

  await page.goto(`/courses/${xem[0]}`, { waitUntil: 'domcontentloaded' });
  const main = page.getByRole('main');
  await expect(main.getByText('Chế độ xem')).toBeVisible({ timeout: 20_000 });
  await expect(main.getByRole('button', { name: 'Xem bài' })).toBeVisible();
  await expect(main).not.toContainText(CHU_CU);

  // Bài học nạp được cho nhân sự (trước 1.3: 403 "chưa ghi danh").
  await openLesson(page, 1, xem[0]);
  await expect(page.getByText('Chưa mở được bài này.')).toHaveCount(0);
});

test('học viên: lưới "Môn học" ở Trang của tôi — môn của lớp "Vào học →", môn khác "Chưa mở", không nút Đăng ký', async ({ page }) => {
  // Tầng JS cũ (`main.js::renderCourses`) từng còn nút "Đăng ký" gọi tuyến đã trả 410 và
  // nút "Hủy đăng ký" ở "Khoá của tôi" — gỡ 25/09 (1.3 phần còn lại).
  test.skip(!taiKhoanCuaVai(HOC_VIEN), LY_DO_THIEU_VAI);
  test.skip(!(await vaoTheoVai(page, HOC_VIEN)), 'tài khoản học viên rà soát không đăng nhập được');
  await chiDoc(page);
  const { mo, dong } = await monTheoQuyen(page);

  await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
  await page.locator('.nav-nhom-nut').click();
  await page.locator('.nav-nhom-panel .nav-btn[data-page="courses"]').click();
  const luoi = page.locator('#courses-grid');
  await expect(luoi.locator('.course-card').first()).toBeVisible({ timeout: 20_000 });
  await expect(luoi.getByRole('button', { name: /^Đăng ký$|Hủy đăng ký|Học thử/ })).toHaveCount(0);
  await expect(page.locator('#unenrollModal')).toHaveCount(0);
  if (mo.length) await expect(luoi.getByRole('button', { name: 'Vào học →' }).first()).toBeVisible();
  if (dong.length) await expect(luoi.getByText('Chưa mở cho lớp của em').first()).toBeVisible();
});
