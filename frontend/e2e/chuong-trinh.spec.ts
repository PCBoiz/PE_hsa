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
 * KHUNG CHƯƠNG TRÌNH + SỔ ĐẦU BÀI + TIẾN ĐỘ (E1, 25/09/2026) — đi bằng GIAO DIỆN.
 *
 * Backend có `chuong_trinh/tests_*.py` gọi thẳng view; tệp này canh phần view không
 * thấy: học vụ vào được màn soạn khung (giảng viên thì không), soạn → xuất bản bằng
 * nút thật, lớp nhận khung qua "Xem trước" → "Nhận khung", sổ đầu bài lưu được và làm
 * lớp rời khỏi "chưa ghi sổ", chip tiến độ hiện ở danh sách lớp, ô ở Tổng quan.
 *
 * ── GHI GÌ, DỌN GÌ ─────────────────────────────────────────────────────────
 *
 * Phần GHI mặc định TẮT (`E2E_GHI=1`): dựng MỘT lớp "E2E tự dọn khung …" (môn
 * hsa_verbal, một buổi hôm qua) và MỘT khung "E2E tự dọn khung …"; `afterAll` xoá lớp
 * (buổi, sổ đi theo) rồi xoá khung (xoá được vì không còn lớp dùng). Không chạm lớp
 * hay tài khoản thật nào. % của một em đo ở `tests_noi_vao.py` (cần điểm danh).
 */

test.describe.configure({ mode: 'serial' });

const BAT = process.env.E2E_GHI === '1';
const LY_DO_TAT = 'luồng có GHI — chỉ chạy khi E2E_GHI=1 (dựng một lớp + một khung tạm rồi xoá)';
const HOC_VU = 'Quản lý học vụ';
const GIANG_VIEN = 'Giảng viên';

let lop: number | null = null;
let khung: number | null = null;

test.afterAll(async ({ browser }) => {
  if (!BAT || (lop === null && khung === null)) return;
  const hv = await trangTheoVai(browser, HOC_VU);
  if (!hv) return;
  const hong: string[] = [];
  if (lop !== null) {
    const r = await goiApi(hv, 'DELETE', `/api/admin/classes/${lop}?confirm=1`);
    if (r.ma >= 300) hong.push(`dọn lớp ${lop}: ${r.ma} ${JSON.stringify(r.du)}`);
  }
  if (khung !== null) {
    const r = await goiApi(hv, 'DELETE', `/api/admin/syllabus/${khung}`);
    if (r.ma >= 300) hong.push(`dọn khung ${khung}: ${r.ma} ${JSON.stringify(r.du)}`);
  }
  await hv.close();
  expect(hong, 'dọn dẹp sau spec chương trình').toEqual([]);
});

// ── Chỉ đọc ────────────────────────────────────────────────────────────────

test('học vụ mở được màn soạn khung; giảng viên thấy lời chặn', async ({ page, browser }) => {
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  await chiDoc(page);
  await page.goto('/giao-trinh/khung-chuong-trinh', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { level: 1, name: 'Khung chương trình theo buổi' })).toBeVisible();
  await expect(page.getByRole('combobox', { name: 'Môn' })).toBeVisible();

  if (!taiKhoanCuaVai(GIANG_VIEN)) return;
  const gv = await trangTheoVai(browser, GIANG_VIEN);
  expect(gv).toBeTruthy();
  await gv!.goto('/giao-trinh/khung-chuong-trinh', { waitUntil: 'domcontentloaded' });
  await expect(gv!.locator('[data-chan="vai"]')).toBeVisible();
  await gv!.close();
});

// ── Có ghi ─────────────────────────────────────────────────────────────────

test('soạn → xuất bản → lớp nhận khung → ghi sổ → tiến độ hiện ở danh sách lớp và Tổng quan', async ({ browser }) => {
  test.skip(!BAT, LY_DO_TAT);
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  lop = khung = null;
  const p = await browser.newPage();
  expect(await vaoTheoVai(p, HOC_VU)).toBe(true);
  p.on('dialog', (d) => void d.accept());
  const tem = `E2E tự dọn khung ${test.info().project.name} ${new Date().toISOString().slice(0, 16)}`;

  // 1. Soạn khung bằng giao diện: 2 buổi, buổi 1 có một nội dung.
  await p.goto('/giao-trinh/khung-chuong-trinh', { waitUntil: 'networkidle' });
  await p.getByRole('combobox', { name: 'Môn' }).selectOption('hsa_verbal');
  await p.getByLabel('Tên khung mới').fill(tem);
  await p.getByRole('button', { name: 'Tạo khung' }).click();
  await expect(p.getByText('Đã tạo bản nháp')).toBeVisible();
  for (const ten of ['Đọc hiểu cơ bản', 'Văn học']) {
    await p.locator('#buoi-moi-ten').fill(ten);
    await p.getByRole('button', { name: 'Thêm buổi' }).click();
    await expect(p.locator('h3', { hasText: ten })).toBeVisible();
  }
  const b1 = p.locator('li', { has: p.locator('h3', { hasText: 'Đọc hiểu cơ bản' }) });
  await b1.locator('summary').click();
  await b1.locator('input[id$="-muc"]').fill('Tìm ý chính');
  await b1.getByRole('button', { name: 'Thêm', exact: true }).click();
  await expect(p.getByText('Tìm ý chính')).toBeVisible();
  await p.locator('tr', { hasText: tem }).getByRole('button', { name: 'Xuất bản' }).click();
  await expect(p.getByText('Đã xuất bản')).toBeVisible();
  const ml = await goiApi(p, 'GET', '/api/admin/chuong-trinh/khung');
  khung = ((ml.du as { mon: { id: string; versions: { id: number; name: string }[] }[] }).mon
    .find((m) => m.id === 'hsa_verbal')?.versions.find((v) => v.name === tem)?.id) ?? null;
  expect(khung, 'khung vừa tạo có trong mục lục').not.toBeNull();

  // 2. Lớp tạm, một buổi HÔM QUA (đã dạy, chưa ghi sổ).
  const r = await goiApi(p, 'POST', '/api/admin/classes', { name: tem, course_id: 'hsa_verbal', capacity: 5, status: 'active' });
  expect(r.ma, JSON.stringify(r.du)).toBe(201);
  lop = (r.du as { id: number }).id;
  const hq = new Date(Date.now() - 86_400_000);
  const pad = (n: number) => String(n).padStart(2, '0');
  const gio = `${hq.getFullYear()}-${pad(hq.getMonth() + 1)}-${pad(hq.getDate())}T18:00`;
  const s = await goiApi(p, 'POST', `/api/teach/classes/${lop}/sessions`, { starts_at: gio, duration_minutes: 90 });
  expect(s.ma, JSON.stringify(s.du)).toBe(201);

  // 3. Nhận khung: xem trước rồi lưu.
  await p.goto(`/giang-day/chuong-trinh/${lop}`, { waitUntil: 'networkidle' });
  await p.getByRole('combobox', { name: 'Khung đang dùng' }).selectOption(String(khung));
  await p.getByRole('button', { name: 'Xem trước' }).click();
  await expect(p.getByText(/Sẽ gắn 1 buổi học/)).toBeVisible();
  await p.getByRole('button', { name: 'Nhận khung' }).click();
  await expect(p.getByText('Đã nhận khung')).toBeVisible();
  await expect(p.getByText('Chưa ghi — ghi ngay')).toBeVisible();

  // 4. Sổ đầu bài.
  await p.getByText('Chưa ghi — ghi ngay').click();
  await expect(p.getByRole('heading', { name: /Nội dung buổi 1/ })).toBeVisible();
  await p.locator('fieldset').first().getByText('Đã dạy', { exact: true }).click();
  await p.getByText('4 · Hiểu tốt').click();
  await p.getByRole('button', { name: 'Lưu sổ đầu bài' }).click();
  await expect(p.getByText('Đã lưu sổ đầu bài')).toBeVisible();

  // 5. Danh sách lớp có chip, Tổng quan có ô.
  await p.goto(`/quan-tri/lop-hoc?q=${encodeURIComponent(tem)}`, { waitUntil: 'networkidle' });
  await expect(p.locator(`a[href="/giang-day/chuong-trinh/${lop}"]`).first()).toBeVisible();
  await p.goto('/quan-tri/tong-quan', { waitUntil: 'networkidle' });
  await expect(p.getByRole('heading', { name: 'Tiến độ chương trình' })).toBeVisible();
  await p.close();
});
