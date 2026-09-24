import { expect, test, type Page } from '@playwright/test';

import { LY_DO_THIEU_VAI, chiDoc, taiKhoanCuaVai, vaoTheoVai } from './helpers';

/**
 * MA TRẬN QUYỀN LÚC CHẠY — bốn vai × mọi khu, ở cả hai tầng.
 *
 * ── VÌ SAO CÓ TỆP NÀY (23/09/2026) ────────────────────────────────────────
 *
 * Hôm qua tôi viết cẩm nang cho bốn vai bằng cách ĐỌC `permissions.py` rồi suy,
 * và sai ba việc liền về Quản lý học vụ (tưởng họ cấp được tài khoản, xem được
 * nhật ký và cơ sở học phí — cả ba đều chỉ quản trị viên; từ 23/09 học vụ cấp
 * được tài khoản HỌC VIÊN, xem bảng TRANG bên dưới). Thứ bắt được lỗi ấy
 * là mở trình duyệt bằng CHÍNH tài khoản vai đó. Tệp này là việc ấy, giao cho máy.
 *
 * `tests_ma_tran_quyen.py` ở backend đã canh 6 vai × mọi view — nhưng nó canh
 * VIEW, không canh TRANG. Một trang Next có thể tự cổng khác với API phía sau
 * nó (khu Vận hành từng chặn học vụ khỏi đúng hai trang backend đã mở cho họ).
 *
 * ── HAI TẦNG, VÌ HAI CÂU HỎI KHÁC NHAU ─────────────────────────────────────
 *
 *   API   · an ninh THẬT. Mã 200/403/404 không mơ hồ. Hở ở đây là hở dữ liệu.
 *   TRANG · người dùng có được BÁO đúng không. Hở ở đây là người dùng tưởng
 *           hệ thống hỏng, hoặc thấy một trang trống không lời giải thích.
 *
 * ── ĐỌC TRẠNG THÁI, KHÔNG DÒ CHỮ ──────────────────────────────────────────
 *
 * Tầng trang đọc móc `data-chan` (`vai` / `khong-thay` / `loi`). Bản đo đầu tiên
 * dò ba cụm chữ và bỏ sót BA màn chặn thật: `/admin` nói "Khu này dành cho
 * người soạn giáo trình", `/bai-tap` nói "Trang này dành cho học viên", Buổi học
 * nói "Không mở được LỚP này" (khác đúng một chữ với "…TRANG này"). Câu chữ là
 * thứ người ta sửa thường xuyên nhất cho dễ hiểu — phép kiểm không được mù theo.
 *
 * ── KHÔNG ĐỤNG LỚP CỦA NGƯỜI DÙNG THỬ ──────────────────────────────────────
 *
 * Cả tệp CHỈ ĐỌC (`chiDoc` chặn mọi lời gọi ghi). Ngày 23/09 lớp 7586 đã được
 * quản trị viên giao cho một tài khoản dùng thử thật; một phép kiểm ghi vào đó
 * là người dùng thử mở ra thấy điểm danh do máy bịa.
 */

type Vai = 'Giảng viên' | 'Trợ giảng' | 'Quản lý học vụ' | 'Biên tập nội dung';
const BON_VAI: Vai[] = ['Giảng viên', 'Trợ giảng', 'Quản lý học vụ', 'Biên tập nội dung'];

/** `true` = vào được. `false` = phải gặp màn chặn `data-chan="vai"`. */
type Bang = Record<Vai, boolean>;
const tatCa = (v: boolean): Bang =>
  ({ 'Giảng viên': v, 'Trợ giảng': v, 'Quản lý học vụ': v, 'Biên tập nội dung': v });
const chiHocVu: Bang = { 'Giảng viên': false, 'Trợ giảng': false, 'Quản lý học vụ': true, 'Biên tập nội dung': false };

/* Đo 23/09/2026 bằng tài khoản thật của từng vai (1440 px), rồi mới ghi vào đây.
   Muốn đổi một ô: đổi QUYỀN trước, đo lại, rồi mới đổi bảng — đừng làm ngược. */
const TRANG: Record<string, Bang> = {
  '/giang-day': { 'Giảng viên': true, 'Trợ giảng': true, 'Quản lý học vụ': true, 'Biên tập nội dung': false },
  '/quan-tri/tong-quan': chiHocVu,
  '/quan-tri/lop-hoc': chiHocVu,
  '/quan-tri/dot-hoc': chiHocVu,
  '/quan-tri/vai-tro': chiHocVu,
  '/quan-tri/huong-dan': chiHocVu,
  // Học vụ vào được từ 23/09/2026 (tạo tài khoản + sửa hồ sơ HỌC VIÊN — máy chủ
  // chỉ trả tài khoản vai Học viên cho họ, xem `ho-so-hoc-vien.spec.ts`). Đo lại
  // bằng tài khoản học vụ thật trước khi đổi ô này.
  '/quan-tri/tai-khoan': chiHocVu,
  // Hai trang CHỈ quản trị viên — hai trong ba thứ cẩm nang bản đầu viết sai.
  '/quan-tri/nhat-ky': tatCa(false),
  '/quan-tri/co-so-hoc-phi': tatCa(false),
  '/giao-trinh': { 'Giảng viên': false, 'Trợ giảng': false, 'Quản lý học vụ': false, 'Biên tập nội dung': true },
  // Khu tài liệu mở cho MỌI vai (22/09/2026) — lọc chứ không chặn.
  '/huong-dan': tatCa(true),
  // Trang học viên: nhân sự được chỉ đường sang khu Giảng dạy.
  '/bai-tap': tatCa(false),
};

/** API → mã mong đợi theo vai. */
const API: Record<string, Record<Vai, number>> = {
  '/api/teach/classes': { 'Giảng viên': 200, 'Trợ giảng': 200, 'Quản lý học vụ': 200, 'Biên tập nội dung': 403 },
  '/api/admin/classes': { 'Giảng viên': 403, 'Trợ giảng': 403, 'Quản lý học vụ': 200, 'Biên tập nội dung': 403 },
  '/api/admin/terms': { 'Giảng viên': 403, 'Trợ giảng': 403, 'Quản lý học vụ': 200, 'Biên tập nội dung': 403 },
  '/api/admin/users': { 'Giảng viên': 403, 'Trợ giảng': 403, 'Quản lý học vụ': 200, 'Biên tập nội dung': 403 },
  '/api/admin/audit': { 'Giảng viên': 403, 'Trợ giảng': 403, 'Quản lý học vụ': 403, 'Biên tập nội dung': 403 },
  '/api/admin/co-so-hoc-phi': { 'Giảng viên': 403, 'Trợ giảng': 403, 'Quản lý học vụ': 403, 'Biên tập nội dung': 403 },
};

/** Đọc móc chặn sau khi trang dựng xong. `null` = không có màn chặn. */
async function docChan(page: Page): Promise<string | null> {
  // Chờ trang dựng: hoặc có `<main>` có nội dung, hoặc có móc chặn.
  await page.waitForFunction(
    () => document.querySelector('[data-chan]') || (document.querySelector('main')?.textContent || '').trim().length > 20,
    undefined, { timeout: 30_000 },
  ).catch(() => { /* để khẳng định bên dưới nói lý do */ });
  return page.locator('[data-chan]').first().getAttribute('data-chan', { timeout: 1000 }).catch(() => null);
}

async function maApi(page: Page, url: string): Promise<number> {
  return page.evaluate(async (u) => (await fetch(u, { credentials: 'include' })).status, url);
}

for (const vai of BON_VAI) {
  test.describe(`vai ${vai}`, () => {
    test.beforeEach(async ({ page }) => {
      test.skip(!taiKhoanCuaVai(vai), LY_DO_THIEU_VAI);
      const vao = await vaoTheoVai(page, vai);
      test.skip(!vao, `không đăng nhập được bằng tài khoản vai ${vai}`);
      await chiDoc(page);
    });

    test('tầng API: mỗi cổng trả đúng mã', async ({ page }) => {
      for (const [url, mong] of Object.entries(API)) {
        const ma = await maApi(page, url);
        expect.soft(ma, `${vai} · GET ${url}`).toBe(mong[vai]);
      }
    });

    test('tầng trang: vào được đúng chỗ, bị chặn thì được BÁO', async ({ page }) => {
      for (const [url, bang] of Object.entries(TRANG)) {
        await page.goto(url, { waitUntil: 'domcontentloaded' });
        expect.soft(page.url(), `${vai} · ${url}: không được rơi về màn đăng nhập`).not.toContain('/login');
        const chan = await docChan(page);
        if (bang[vai]) {
          expect.soft(chan, `${vai} · ${url}: phải VÀO ĐƯỢC, nhưng gặp màn chặn "${chan}"`).toBeNull();
        } else {
          // Chặn theo VAI — không phải "không tìm thấy", không phải "máy chủ lỗi".
          // Ba câu trả lời ấy đẩy người dùng đi hỏi ba chỗ khác nhau.
          expect.soft(chan, `${vai} · ${url}: phải gặp màn chặn theo vai`).toBe('vai');
        }
      }
    });
  });
}

/* ── CÁCH LY GIỮA CÁC LỚP ────────────────────────────────────────────────────
   Giảng viên chỉ thấy lớp mình phụ trách. Lấy một lớp mà HỌC VỤ thấy nhưng
   GIẢNG VIÊN KHÔNG, rồi đòi giảng viên nhận 404 — không phải 403, vì 403 lộ ra
   rằng lớp ấy có tồn tại. */
test('giảng viên không mở được lớp của giảng viên khác (404, không lộ lớp)', async ({ browser }) => {
  test.skip(!taiKhoanCuaVai('Quản lý học vụ') || !taiKhoanCuaVai('Giảng viên'), LY_DO_THIEU_VAI);

  const hv = await browser.newPage();
  test.skip(!(await vaoTheoVai(hv, 'Quản lý học vụ')), 'không vào được bằng vai Quản lý học vụ');
  const lopHv: number[] = await hv.evaluate(async () =>
    ((await (await fetch('/api/teach/classes', { credentials: 'include' })).json()).classes || [])
      .map((c: { id: number }) => c.id));
  await hv.close();

  const gv = await browser.newPage();
  test.skip(!(await vaoTheoVai(gv, 'Giảng viên')), 'không vào được bằng vai Giảng viên');
  await chiDoc(gv);
  const lopGv: number[] = await gv.evaluate(async () =>
    ((await (await fetch('/api/teach/classes', { credentials: 'include' })).json()).classes || [])
      .map((c: { id: number }) => c.id));

  const la = lopHv.find((id) => !lopGv.includes(id));
  test.skip(la === undefined, 'không có lớp nào học vụ thấy mà giảng viên không thấy');

  for (const duoi of ['', '/sessions', '/parent-report/send-all']) {
    const ma = await maApi(gv, `/api/teach/classes/${la}${duoi}`);
    expect.soft(ma, `GET /api/teach/classes/${la}${duoi}`).toBe(404);
  }
  for (const trang of [`/giang-day/buoi-hoc/${la}`, `/giang-day/bai-tap/${la}`, `/giang-day/bao-cao/${la}`]) {
    await gv.goto(trang, { waitUntil: 'domcontentloaded' });
    expect.soft(await docChan(gv), `${trang}: phải báo "không tìm thấy"`).toBe('khong-thay');
  }
  await gv.close();
});

/* ── TRỢ GIẢNG TRONG CHÍNH LỚP CỦA MÌNH ──────────────────────────────────────
   Được gán vào lớp thì điểm danh và chấm bài được — nhưng báo cáo phụ huynh vẫn
   bị cắt, vì nó mang dữ liệu liên lạc của em ra ngoài. Đây là ranh giới "nhìn được
   khi làm việc, không mang ra ngoài được". (Màn nhập kết quả thi từng nằm trong
   vòng này — gỡ 24/09/2026, bỏ thi pha A; đường cũ nay chuyển về sổ buổi học.) */
test('trợ giảng: trong lớp được gán vẫn bị cắt báo cáo phụ huynh', async ({ page }) => {
  test.skip(!taiKhoanCuaVai('Trợ giảng'), LY_DO_THIEU_VAI);
  test.skip(!(await vaoTheoVai(page, 'Trợ giảng')), 'không vào được bằng vai Trợ giảng');
  await chiDoc(page);

  const lop: number[] = await page.evaluate(async () =>
    ((await (await fetch('/api/teach/classes', { credentials: 'include' })).json()).classes || [])
      .map((c: { id: number }) => c.id));
  test.skip(lop.length === 0, 'tài khoản trợ giảng chưa được gán vào lớp nào');
  const id = lop[0];

  expect.soft(await maApi(page, `/api/teach/classes/${id}/sessions`), 'buổi học: phải mở được').toBe(200);
  expect.soft(await maApi(page, `/api/teach/classes/${id}/parent-report/send-all`), 'báo cáo phụ huynh: phải 403').toBe(403);

  await page.goto(`/giang-day/buoi-hoc/${id}`, { waitUntil: 'domcontentloaded' });
  expect.soft(await docChan(page), 'buổi học: phải vào được').toBeNull();
  // Tờ TỪNG EM (25/09/2026): lớp quyền chặn trước khi hỏi em nào, nên id em bất kỳ cũng 403.
  for (const trang of [`/giang-day/bao-cao/${id}`, `/giang-day/bao-cao/${id}/1`]) {
    await page.goto(trang, { waitUntil: 'domcontentloaded' });
    expect.soft(await docChan(page), `${trang}: phải chặn theo vai`).toBe('vai');
  }
});

/* Biên tập nội dung gõ thẳng đường bảng chấm (25/09/2026): lớp quyền `IsTeachingStaff` chặn
   trước khi tìm bài, nên id bất kỳ cũng 403 — trang phải BÁO chặn theo vai, không phải lỗi chung. */
test('biên tập nội dung: bảng chấm báo chặn theo vai', async ({ page }) => {
  test.skip(!taiKhoanCuaVai('Biên tập nội dung'), LY_DO_THIEU_VAI);
  test.skip(!(await vaoTheoVai(page, 'Biên tập nội dung')), 'không vào được bằng vai Biên tập nội dung');
  await chiDoc(page);
  await page.goto('/giang-day/bai-tap/1/1', { waitUntil: 'domcontentloaded' });
  expect(await docChan(page), 'bảng chấm: phải chặn theo vai').toBe('vai');
});
