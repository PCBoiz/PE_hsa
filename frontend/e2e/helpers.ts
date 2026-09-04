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
import { Page, expect } from '@playwright/test';

export const E2E_EMAIL = process.env.E2E_EMAIL || 'audit@example.com';
export const E2E_PASSWORD = process.env.E2E_PASSWORD || 'AuditPass123';

/** Khoá mặc định để mở bài — phải là khoá CÓ THẬT trong CSDL. */
export const KHOA = process.env.E2E_COURSE || 'hsa_quantitative';

/** Câu giải thích khi bỏ qua — để người đọc log biết PHẢI LÀM GÌ. */
export const LY_DO_BO_QUA =
  `không đăng nhập được bằng ${E2E_EMAIL}. Tài khoản này không có sẵn trong `
  + 'CSDL, và tạo nó là một lượt GHI vào Neon production nên phải do chủ dự án '
  + 'quyết định. Có tài khoản rồi thì đặt E2E_EMAIL / E2E_PASSWORD.';

/**
 * Đăng nhập; trả `false` nếu KHÔNG vào được.
 *
 * Bản cũ nuốt lỗi bằng `.catch(() => {})` rồi đi tiếp, nên một tài khoản không
 * tồn tại hiện ra thành một `waitForFunction` hết giờ ở tận nơi khác — đúng
 * kiểu im lặng đã làm mất ba tuần của trợ lý chat. Nay nói thẳng, và phía gọi
 * quyết định BỎ QUA hay báo đỏ.
 */
export async function login(page: Page): Promise<boolean> {
  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#login-email', { timeout: 30_000 });
  await page.fill('#login-email', E2E_EMAIL);
  await page.fill('#login-password', E2E_PASSWORD);
  await page.click('#loginBtn');
  try {
    await page.waitForURL('**/dashboard**', { timeout: 20_000 });
    return true;
  } catch {
    // In ra, chứ không chỉ trả `false`. Một phép kiểm bị bỏ qua mà không ai
    // đọc lý do thì cũng là một im lặng — đúng thứ đang sửa ở khắp phiên này.
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
