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

export const E2E_EMAIL = process.env.E2E_EMAIL || 'audit@example.com';
export const E2E_PASSWORD = process.env.E2E_PASSWORD || 'AuditPass123';

/** Khoá mặc định để mở bài — phải là khoá CÓ THẬT trong CSDL. */
export const KHOA = process.env.E2E_COURSE || 'hsa_quantitative';

/** Câu giải thích khi bỏ qua — để người đọc log biết PHẢI LÀM GÌ. */
export const LY_DO_BO_QUA =
  'không vào được bằng thẻ lẫn bằng mật khẩu. Thẻ access sống 30 PHÚT — hết hạn '
  + 'thì cấp lại: `python scripts/cap_the.py`. Hoặc đặt E2E_EMAIL / E2E_PASSWORD cho một tài '
  + `khoản có thật — ${E2E_EMAIL} không có trong CSDL này, và tạo nó là một lượt `
  + 'GHI vào Neon production.';

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
  if (await vaoBangThe(page)) return true;

  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#login-email', { timeout: 30_000 });
  await page.fill('#login-email', E2E_EMAIL);
  await page.fill('#login-password', E2E_PASSWORD);
  await page.click('#loginBtn');
  try {
    await page.waitForURL('**/dashboard**', { timeout: 20_000 });
    return true;
  } catch {
    // In ra, chứ không chỉ trả `false`. Một phép kiểm bị bỏ qua mà không ai đọc
    // lý do thì cũng là một im lặng — đúng thứ đang sửa ở khắp phiên này.
    console.warn(`[e2e] BỎ QUA phép kiểm cần đăng nhập — ${LY_DO_BO_QUA}`);
    return false;
  }
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

/** Trợ lý chat có BIẾT học viên đang mở bài nào không. */
export async function expectChatbotBietBai(page: Page, soBai: number) {
  const ctx = await page.evaluate(
    () => (window as unknown as { collectLessonContext?: () => unknown })
      .collectLessonContext?.() ?? null,
  );
  expect(ctx, 'collectLessonContext() trả null — trợ lý mất ngữ cảnh bài học')
    .not.toBeNull();
  expect((ctx as { lesson_index?: number }).lesson_index).toBe(soBai);
}
