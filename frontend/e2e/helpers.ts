// Helper chung cho bộ e2e Playwright của pe_hsa.
//
// ── TỆP NÀY TỪNG TRỎ VÀO MỘT DỰ ÁN KHÁC (sửa 05/09/2026) ────────────────────
//
// Bản trước mở `/lesson/db_design` và chờ `window.LESSON_CONTENT.db_design` có
// ít nhất 20 bài. Khoá `db_design` KHÔNG TỒN TẠI trong CSDL này — chỉ có
// `hsa_quantitative`, `hsa_science`, `hsa_verbal`. Nó là khoá của PE_test, theo
// hai tệp spec được chép sang khi tách repo.
//
// Chạy thử để chắc chứ không suy: `pe-run-sql.spec.ts` chết đúng ở dòng
// `waitForFunction` ấy sau 30 giây. Hai spec DB Design đã xoá (không mã nào
// trong repo này cung cấp `PE_runSQL` hay `drag_game`); tệp này viết lại cho HSA.
//
// Yêu cầu chạy:
//   cd backend  && .venv/Scripts/python manage.py runserver 9000 --noreload
//   cd frontend && pnpm dev            (cổng 3100)
//   cd frontend && E2E_BASE_URL=http://localhost:3100 \
//                  pnpm exec playwright test --config e2e/playwright.config.ts
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

import { Page, expect } from '@playwright/test';

/* Tài khoản kiểm thử. Thứ tự lấy: biến môi trường → `.the/e2e.json` (do
   `python scripts/tai_khoan_e2e.py --that` sinh ra) → không có.

   KHÔNG có mật khẩu mặc định trong mã nguồn nữa. Bản trước ghi cứng
   `audit@example.com` / `AuditPass123` — một tài khoản không tồn tại, nên ba
   phép kiểm luôn bỏ qua; và nếu nó TỪNG tồn tại thì đó là một cánh cửa vào CSDL
   production nằm sẵn trong repo. */
function docTaiKhoan(): { email: string; password: string } | null {
  if (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) {
    return { email: process.env.E2E_EMAIL, password: process.env.E2E_PASSWORD };
  }
  for (const p of [join(process.cwd(), '..', '.the', 'e2e.json'),
                   join(process.cwd(), '.the', 'e2e.json')]) {
    try {
      const d = JSON.parse(readFileSync(p, 'utf8'));
      if (d.email && d.password) return d;
    } catch { /* thử đường sau */ }
  }
  return null;
}

const TAI_KHOAN = docTaiKhoan();
export const E2E_EMAIL = TAI_KHOAN?.email || '(chưa có tài khoản kiểm thử)';

/** Khoá mặc định để mở bài — phải là khoá CÓ THẬT trong CSDL. */
export const KHOA = process.env.E2E_COURSE || 'hsa_quantitative';

/** Câu giải thích khi bỏ qua — để người đọc log biết PHẢI LÀM GÌ. */
export const LY_DO_BO_QUA =
  'không vào được. Tạo tài khoản kiểm thử: `python scripts/tai_khoan_e2e.py --that` '
  + '(xem trước không cần cờ). Hoặc đặt E2E_EMAIL / E2E_PASSWORD. Đường thẻ JWT '
  + '(`python scripts/cap_the.py`) cũng dùng được nhưng thẻ chỉ sống 30 phút.';

/* Tệp thẻ do `scripts/cap_the.py` sinh ra.

   KHÔNG dùng `import.meta.url`: Playwright dịch tệp TS này sang CommonJS, và
   `import.meta` ở đó là `SyntaxError` — nó làm HỎNG CẢ BỘ, "No tests found",
   chứ không chỉ hỏng một phép kiểm. Cũng không dùng `__dirname`, vì nó sẽ vỡ
   theo chiều ngược lại nếu dự án chuyển sang ESM.

   Dò vài đường dẫn ứng viên rồi lấy cái CÓ THẬT: đúng cho cả hai dạng mô-đun,
   và không phụ thuộc vào việc lệnh được gõ từ thư mục nào. */
function timTepThe(): string {
  if (process.env.PE_TOKENS) return process.env.PE_TOKENS;
  const ungVien = [
    join(process.cwd(), '..', '.the', 'tokens_ad.json'),   // gõ từ frontend/
    join(process.cwd(), '.the', 'tokens_ad.json'),         // gõ từ gốc repo
  ];
  return ungVien.find((p) => existsSync(p)) || ungVien[0];
}

/**
 * Vào bằng THẺ thay vì mật khẩu.
 *
 * Đường mật khẩu cần một tài khoản có thật, mà tạo tài khoản là một lượt GHI vào
 * Neon production. Cấp thẻ ACCESS thì không: nó chỉ ký một chuỗi cho một
 * `user_id` đã tồn tại (`scripts/cap_the.py`) — cùng cơ chế
 * `scripts/do_giao_dien.mjs` dùng để đo 16 trang.
 *
 * (Cấp kèm REFRESH thì CÓ ghi một dòng `token_blacklist_outstandingtoken` —
 * `RefreshToken` của SimpleJWT mang `BlacklistMixin`. Đã đo. Nên `cap_the.py`
 * mặc định access-only, và `refresh` ở đây là TUỲ CHỌN.)
 *
 * Không có tệp thẻ → trả `false` lặng lẽ, phía gọi sẽ thử mật khẩu.
 */
export async function vaoBangThe(page: Page): Promise<boolean> {
  let the: { access?: string; refresh?: string };
  try {
    the = JSON.parse(readFileSync(timTepThe(), 'utf8'));
  } catch {
    return false;
  }
  if (!the.access) return false;

  const mien = new URL(page.url() === 'about:blank' ? 'http://localhost' : page.url()).hostname;
  const banh = [
    { name: 'pe_at', value: the.access, domain: mien, path: '/', httpOnly: true, sameSite: 'Lax' as const },
  ];
  if (the.refresh) {
    banh.push({ name: 'pe_rt', value: the.refresh, domain: mien, path: '/', httpOnly: true, sameSite: 'Lax' as const });
  }
  await page.context().addCookies(banh);

  const vaoDuoc = async () => {
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);
    return !/(dang-nhap|login)/.test(new URL(page.url()).pathname);
  };
  if (await vaoDuoc()) return true;

  /* Thẻ `access` sống 30 PHÚT, và một lượt chạy đầy đủ dài hơn thế: đo ngày
     05/09/2026, hai phép kiểm CUỐI bị bỏ qua chỉ vì thẻ hết hạn giữa chừng —
     mà câu bỏ qua lại nói "không có tài khoản", tức chẩn đoán sai hẳn nguyên
     nhân. Một câu giải thích SAI còn tệ hơn không có câu nào.

     Có `refresh` thì thử đường làm mới của chính sản phẩm: gọi một đường
     `/api/*`, lớp trung gian đổi refresh lấy access mới rồi ghi lại cookie
     (`src/lib/proxy.ts`). Không có refresh thì nói thẳng là thẻ hết hạn. */
  if (the.refresh) {
    await page.goto('/api/user', { waitUntil: 'domcontentloaded' }).catch(() => {});
    await page.waitForTimeout(800);
    if (await vaoDuoc()) return true;
  }
  console.warn('[e2e] Thẻ đã hết hạn (access sống 30 phút). Cấp lại:'
    + ' python scripts/cap_the.py');
  return false;
}

/**
 * Vào ứng dụng: THỬ THẺ TRƯỚC, rồi mới tới mật khẩu. Trả `false` nếu cả hai hỏng.
 *
 * Bản cũ nuốt lỗi bằng `.catch(() => {})` rồi đi tiếp, nên một tài khoản không
 * tồn tại hiện ra thành một `waitForFunction` hết giờ ở tận nơi khác — đúng kiểu
 * im lặng đã làm mất ba tuần của trợ lý chat. Nay nói thẳng, và phía gọi quyết
 * định BỎ QUA hay báo đỏ.
 */
export async function login(page: Page): Promise<boolean> {
  /* TÀI KHOẢN TRƯỚC, THẺ SAU — ngược với bản hôm qua.
     Thẻ access sống 30 phút; một lượt chạy đầy đủ dài hơn thế, và hai phép kiểm
     cuối đã bỏ qua chỉ vì lý do ấy. Phiên đăng nhập thật không có hạn đó. */
  if (TAI_KHOAN) {
    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#login-email', { timeout: 30_000 });
    await page.fill('#login-email', TAI_KHOAN.email);
    await page.fill('#login-password', TAI_KHOAN.password);
    await page.click('#loginBtn');
    try {
      await page.waitForURL('**/dashboard**', { timeout: 20_000 });
      return true;
    } catch { /* rơi xuống đường thẻ */ }
  }

  // Đường lùi: thẻ JWT. Và nếu cả hai hỏng thì IN RA lý do — một phép kiểm bị
  // bỏ qua mà không ai đọc lý do thì cũng là một im lặng.
  {
    if (await vaoBangThe(page)) return true;
    console.warn(`[e2e] BỎ QUA phép kiểm cần đăng nhập — ${LY_DO_BO_QUA}`);
    return false;
  }
}

/**
 * Vào bằng một tài khoản HỌC VIÊN — cho phép kiểm đo MÀN HỌC VIÊN.
 *
 * Từ 20/09/2026 nhân sự không thấy phần luyện thi (`src/lib/nhomVai.ts`). Trước
 * đó các phép kiểm dashboard gọi `vaoBangThe()` trước — thẻ QUẢN TRỊ — và vẫn
 * xanh, vì quản trị viên thấy nguyên màn học viên. Đo 20/09: tài khoản e2e đã
 * biến khỏi CSDL, nên CẢ đường mật khẩu cũng rơi về thẻ quản trị; bốn tệp kiểm
 * "màn học viên" thật ra đang đo màn của admin. Hàm này hỏi `/api/user` sau khi
 * vào và BỎ QUA kèm lý do nếu vai không phải học viên — không để một thước
 * lệch vai báo xanh hay đỏ oan.
 */
export async function vaoLaHocVien(page: Page): Promise<string | null> {
  if (!(await login(page))) return LY_DO_BO_QUA;
  const vai = await page.evaluate(async () => {
    const r = await fetch('/api/user', { credentials: 'same-origin' });
    return r.ok ? ((await r.json()) as { role?: string }).role ?? null : null;
  });
  if (vai !== 'Học viên') {
    return `phép kiểm này đo MÀN HỌC VIÊN nhưng đang vào bằng vai ${JSON.stringify(vai)}`
      + ' — tạo tài khoản kiểm thử học viên: python scripts/tai_khoan_e2e.py --that';
  }
  return null;
}

/**
 * Mở một bài HSA và chờ engine công bố bài đang mở.
 *
 * Mốc chờ là `window.__PE_BAI_DANG_MO` — biến `lesson_hsa.js` đặt NGAY SAU khi
 * gán `state.lesson`. Chờ đúng nó thay vì một biến nội dung nào đó: nó là thứ
 * trợ lý chat đọc, nên chờ ở đây là kiểm luôn cả mối nối ấy (bản vá A13,
 * 05/09/2026 — xem `e2e/unit/ngu-canh-tro-ly.test.mjs`).
 */
export async function openLesson(page: Page, lesson = 1, khoa = KHOA) {
  await page.goto(`/lesson/${khoa}?lesson=${lesson}`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(
    () => !!(window as unknown as { __PE_BAI_DANG_MO?: unknown }).__PE_BAI_DANG_MO,
    undefined,
    { timeout: 30_000 },
  );
}

/**
 * Trợ lý chat có BIẾT học viên đang mở bài nào không — đo ở THÂN REQUEST.
 *
 * Bản trước gọi `window.collectLessonContext()` của `chatbot.js`. Từ 20/09/2026
 * trợ lý là React và không để lại global nào; cách đo đúng hơn cũng là cách
 * duy nhất còn lại: bấm nút "Giảng lại" như học viên, chặn `/api/chat`, đọc
 * `page_context` trong thân request. Trả ngữ cảnh ấy cho phép kiểm soi tiếp.
 */
export async function expectChatbotBietBai(page: Page, soBai: number): Promise<Record<string, unknown>> {
  let than: { page_context?: Record<string, unknown> } | null = null;
  await page.route('**/api/chat', (r) => {
    than = r.request().postDataJSON();
    return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ reply: 'ok' }) });
  });
  await page.click('#chatbot-toggle');
  await page.getByRole('button', { name: 'Giảng lại' }).click();
  await expect.poll(() => than, { timeout: 15_000 }).not.toBeNull();
  await page.unroute('**/api/chat');
  const ctx = than!.page_context ?? null;
  expect(ctx, 'page_context trống — trợ lý mất ngữ cảnh bài học').not.toBeNull();
  expect((ctx as { lesson_index?: number }).lesson_index).toBe(soBai);
  return ctx as Record<string, unknown>;
}

/* ── ĐĂNG NHẬP THEO VAI (22/09/2026) ────────────────────────────────────────

   Bộ helper cho tới nay chỉ biết MỘT tài khoản. Nhưng phần lớn thứ đáng kiểm
   trong một ERP là "vai nào thấy gì" — và câu ấy không kiểm được bằng một tài
   khoản duy nhất.

   Hôm nay tôi đã trả giá cho đúng chỗ này: viết cẩm nang cho bốn vai bằng cách
   đọc `permissions.py` rồi suy, và sai ba việc liền về vai Quản lý học vụ. Thứ
   sửa được tôi là mở trình duyệt bằng chính tài khoản vai ấy. Phép kiểm dưới
   đây biến việc đó thành việc của máy.

   Tài khoản đọc từ `.the/audit_tk.json` — tệp do phiên rà soát sinh ra, nằm
   trong `.gitignore` như mọi thứ khác dưới `.the/`. Không có tệp thì BỎ QUA kèm
   lý do, không đỏ oan. */

export type TaiKhoanVai = { email: string; matKhau: string; vai: string };

function docBangVai(): Record<string, TaiKhoanVai> {
  for (const p of [join(process.cwd(), '..', '.the', 'audit_tk.json'),
                   join(process.cwd(), '.the', 'audit_tk.json')]) {
    try {
      if (!existsSync(p)) continue;
      return JSON.parse(readFileSync(p, 'utf8')) as Record<string, TaiKhoanVai>;
    } catch { /* thử đường sau */ }
  }
  return {};
}

const BANG_VAI = docBangVai();

/** Tài khoản đầu tiên mang đúng vai này, hoặc `null`. */
export function taiKhoanCuaVai(vai: string): (TaiKhoanVai & { email: string }) | null {
  for (const [email, t] of Object.entries(BANG_VAI)) {
    if (t && t.vai === vai && t.matKhau) return { ...t, email };
  }
  return null;
}

export const LY_DO_THIEU_VAI =
  'chưa có `.the/audit_tk.json` (bảng tài khoản bốn vai). Sinh bằng kịch bản rà '
  + 'soát, hoặc bỏ qua nhóm phép kiểm theo vai.';

/**
 * Đăng nhập bằng tài khoản mang ĐÚNG vai này.
 *
 * Trả `true` khi vào được VÀ `/api/user` xác nhận đúng vai — hai vế, vì vế sau
 * mới là thứ phép kiểm dựa vào. Một tài khoản bị đổi vai mà bảng chưa cập nhật
 * sẽ làm mọi khẳng định phía sau nói về một vai khác hẳn.
 */
export async function vaoTheoVai(page: Page, vai: string): Promise<boolean> {
  const tk = taiKhoanCuaVai(vai);
  if (!tk) return false;
  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#login-email', { timeout: 30_000 });
  await page.fill('#login-email', tk.email);
  await page.fill('#login-password', tk.matKhau);
  await page.click('#loginBtn');
  try {
    await page.waitForURL('**/dashboard**', { timeout: 25_000 });
  } catch {
    return false;
  }
  const that = await page.evaluate(async () => {
    const r = await fetch('/api/user', { credentials: 'include' });
    return r.ok ? ((await r.json()) as { role?: string }).role ?? null : null;
  });
  if (that !== vai) {
    console.warn(`[e2e] tài khoản ${tk.email} mang vai "${that}", không phải "${vai}"`);
    return false;
  }
  return true;
}

/** Chặn MỌI lời gọi ghi — dùng cho phép kiểm chỉ đọc. */
export async function chiDoc(page: Page) {
  await page.route('**/api/**', (r) => (
    ['GET', 'HEAD', 'OPTIONS'].includes(r.request().method())
      ? r.continue()
      : r.fulfill({ status: 200, contentType: 'application/json', body: '{}' })));
}
