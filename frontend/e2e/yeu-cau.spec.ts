import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

import { expect, test, type Page } from '@playwright/test';

import { LY_DO_BO_QUA, LY_DO_THIEU_VAI, goiApi, login, taiKhoanCuaVai, trangTheoVai } from './helpers';

/**
 * HỘP YÊU CẦU (E3) — đi bằng GIAO DIỆN, hai khổ máy. Bảng TopHSA dòng 11, 12, 25, 32.
 *
 *   1. Học viên (tài khoản e2e, lớp mẫu) gửi câu hỏi → thấy trong "Yêu cầu bạn đã gửi".
 *   2. Học vụ (tài khoản vai, KHÔNG gắn lớp thử nghiệm của TopHSA) mở cùng yêu cầu: ghi chú nội
 *      bộ + trả lời.
 *   3. Học viên mở lại: thấy trả lời, KHÔNG thấy ghi chú nội bộ.
 *   4. Học vụ đóng "Đã xong" kèm kết quả (dọn luôn — hộp không phình theo số lượt chạy).
 *   5. Phụ huynh (chìa lớp mẫu `.the/chia_mau.json`) gửi qua tờ báo cáo → thấy trong danh sách;
 *      học vụ đóng lại (trần 5 yêu cầu mở mỗi link — không đóng thì lượt chạy thứ ba đỏ oan).
 *
 * Mọi lượt chờ sau một lần GHI: `timeout: 20_000` (Neon từ máy dev ~5 s một lượt ghi). CÓ GHI
 * → chỉ chạy khi `E2E_GHI=1`. Không gửi gì ra ngoài (thông báo chỉ vào chuông, không thư).
 */
test.describe.configure({ mode: 'serial' });

const BAT = process.env.E2E_GHI === '1';
const LY_DO_TAT = 'luồng có GHI — chỉ chạy khi E2E_GHI=1 (yêu cầu tạo ra được đóng ở cuối)';
const HOC_VU = 'Quản lý học vụ';
const DAU = `${Date.now().toString(36)}`;
const CHO = { timeout: 20_000 };

function chiaMau(): string | null {
  for (const p of [join(process.cwd(), '..', '.the', 'chia_mau.json'), join(process.cwd(), '.the', 'chia_mau.json')]) {
    try {
      if (existsSync(p)) return (JSON.parse(readFileSync(p, 'utf8')) as { token?: string }).token ?? null;
    } catch { /* thử đường sau */ }
  }
  return null;
}

/** Mở trang rồi CHỜ React gắn xong (lưới im) — gõ / bấm sớm hơn thì trình duyệt gửi biểu mẫu kiểu
 *  mặc định (GET) và mất chữ; nút gửi của các màn này khoá tới khi gắn xong (`useDaGan`). */
async function mo(page: Page, url: string) {
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded' });
  } catch (e) {
    /* Ngay sau đăng nhập, trang đích của vai (`TRANG_DAU`) còn đang chuyển hướng → lượt `goto`
       mới bị huỷ ngang (`ERR_ABORTED`, đo 26/09/2026 ở khổ máy tính). Chờ yên rồi đi lại MỘT lần. */
    if (!String(e).includes('ERR_ABORTED')) throw e;
    await page.waitForLoadState('networkidle', { timeout: 30_000 }).catch(() => {});
    await page.goto(url, { waitUntil: 'domcontentloaded' });
  }
  await page.waitForLoadState('networkidle', { timeout: 60_000 }).catch(() => {});
}

async function idTuLienKet(page: Page, tieuDe: string): Promise<number> {
  const href = await page.getByRole('link', { name: new RegExp(tieuDe) }).first().getAttribute('href');
  const m = /\/yeu-cau\/(\d+)/.exec(href ?? '');
  expect(m, `liên kết của "${tieuDe}"`).not.toBeNull();
  return Number(m![1]);
}

test('học viên gửi câu hỏi → học vụ trả lời + ghi chú nội bộ → học viên chỉ thấy trả lời', async ({ page, browser }, info) => {
  test.skip(!BAT, LY_DO_TAT);
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  test.skip(!(await login(page)), LY_DO_BO_QUA);
  const tieuDe = `E2E hỏi ${DAU} ${info.project.name}`;

  await mo(page, '/yeu-cau');
  await expect(page.getByRole('heading', { name: 'Hỏi & yêu cầu', level: 1 })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByRole('button', { name: 'Gửi yêu cầu' })).toBeEnabled({ timeout: 30_000 });
  await page.getByLabel('Bạn cần gì?').selectOption('ht_hoc_tap');
  await page.getByLabel('Tóm tắt một dòng').fill(tieuDe);
  await page.getByLabel('Nội dung (không bắt buộc)').fill('Em chưa hiểu cách đổi đơn vị ở câu 5.');
  const nut = page.getByRole('button', { name: 'Gửi yêu cầu' });
  await nut.click();
  await expect(page.getByRole('status')).toContainText('Đã gửi', CHO);
  await expect(page.getByRole('link', { name: new RegExp(tieuDe) })).toBeVisible(CHO);
  const id = await idTuLienKet(page, tieuDe);

  // Học vụ: ghi chú nội bộ, rồi trả lời.
  const hv = await trangTheoVai(browser, HOC_VU);
  expect(hv, 'đăng nhập vai học vụ').not.toBeNull();
  await mo(hv!, `/yeu-cau/${id}`);
  await expect(hv!.getByRole('heading', { name: tieuDe })).toBeVisible({ timeout: 30_000 });
  await hv!.getByLabel('Ghi chú nội bộ (học viên, phụ huynh không thấy)').check();
  await hv!.getByLabel('Ghi chú nội bộ', { exact: true }).fill(`Nội bộ ${DAU}: em hỏi lần thứ hai`);
  await hv!.getByRole('button', { name: 'Lưu ghi chú' }).click();
  await expect(hv!.getByText(`Nội bộ ${DAU}: em hỏi lần thứ hai`)).toBeVisible(CHO);
  await hv!.getByLabel('Ghi chú nội bộ (học viên, phụ huynh không thấy)').uncheck();
  await hv!.getByLabel('Trả lời', { exact: true }).fill(`Trả lời ${DAU}: xem lại ví dụ 2 trong bài 3.`);
  await hv!.getByRole('button', { name: 'Gửi trả lời' }).click();
  await expect(hv!.getByText(`Trả lời ${DAU}: xem lại ví dụ 2 trong bài 3.`)).toBeVisible(CHO);
  // Nhân sự trả lời = đã nhận việc.
  await expect(hv!.getByText('Đang xử lý').first()).toBeVisible(CHO);

  // Học viên: thấy trả lời, không thấy nội bộ (máy chủ không gửi xuống — đọc cả thân API).
  await mo(page, `/yeu-cau/${id}`);
  await expect(page.getByText(`Trả lời ${DAU}: xem lại ví dụ 2 trong bài 3.`)).toBeVisible(CHO);
  await expect(page.getByText(`Nội bộ ${DAU}`)).toHaveCount(0);
  const api = await goiApi(page, 'GET', `/api/yeu-cau/${id}`);
  expect(JSON.stringify(api.du)).not.toContain(`Nội bộ ${DAU}`);

  // Học vụ đóng kèm kết quả.
  await hv!.getByRole('button', { name: 'Đã xong…' }).click();
  await hv!.getByLabel('Kết quả (người gửi đọc được)').fill('Đã hướng dẫn em qua trả lời.');
  await hv!.getByRole('button', { name: 'Đánh dấu đã xong' }).click();
  await expect(hv!.getByText('Đã hướng dẫn em qua trả lời.').first()).toBeVisible(CHO);
  await hv!.close();
});

test('phụ huynh gửi yêu cầu qua tờ báo cáo → thấy trong danh sách; học vụ thấy trong hộp', async ({ page, browser }, info) => {
  test.skip(!BAT, LY_DO_TAT);
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  const chia = chiaMau();
  test.skip(!chia, 'chưa có .the/chia_mau.json — cấp bằng scripts/cap_chia_mau.py');
  const tieuDe = `E2E phụ huynh ${DAU} ${info.project.name}`;

  await mo(page, `/bc/${chia}`);
  const khoi = page.getByRole('region', { name: 'Gửi yêu cầu cho trung tâm' });
  test.skip(!(await khoi.isVisible({ timeout: 30_000 }).catch(() => false)), 'chìa mẫu đã hết hạn — cấp lại bằng scripts/cap_chia_mau.py');
  await expect(khoi.getByRole('button', { name: 'Gửi yêu cầu' })).toBeEnabled({ timeout: 30_000 });
  await khoi.getByLabel('Anh / chị cần gì?').selectOption('ht_lich_hoc');
  await khoi.getByLabel('Tóm tắt một dòng').fill(tieuDe);
  await khoi.getByRole('button', { name: 'Gửi yêu cầu' }).click();
  await expect(khoi.getByRole('status')).toContainText('Trung tâm đã nhận', CHO);
  await expect(khoi.getByText(tieuDe)).toBeVisible(CHO);

  const hv = await trangTheoVai(browser, HOC_VU);
  expect(hv, 'đăng nhập vai học vụ').not.toBeNull();
  await mo(hv!, '/yeu-cau');
  await expect(hv!.getByRole('link', { name: new RegExp(tieuDe) })).toBeVisible({ timeout: 30_000 });
  const id = await idTuLienKet(hv!, tieuDe);
  // Dọn: đóng lại — trần 5 yêu cầu đang mở mỗi link.
  const r = await goiApi(hv!, 'POST', `/api/teach/yeu-cau/${id}/trang-thai`, { den: 'da_xong', ket_qua: 'Kiểm thử tự động.' });
  expect(r.ma).toBe(200);
  await hv!.close();

  // Phụ huynh tải lại: thấy "Đã xong" + kết quả, không thấy gì nội bộ.
  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(khoi.getByText('Kết quả: Kiểm thử tự động.').first()).toBeVisible(CHO);
});
