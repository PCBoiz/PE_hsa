// Trợ lý chat phải BIẾT học viên đang mở bài nào — kiểm trong TRÌNH DUYỆT THẬT.
//
// ── VÌ SAO CẦN CẢ BẢN TRÌNH DUYỆT (A13, 05/09/2026) ─────────────────────────
//
// `e2e/unit/ngu-canh-tro-ly.test.mjs` rút hàm ra khỏi tệp rồi gọi bằng `window`
// giả. Nó bắt được mối nối, nhưng KHÔNG chứng minh được rằng trên trang thật
// engine có chạy tới chỗ công bố, đúng thứ tự, trước khi trợ lý hỏi tới.
//
// Ngày 05/09 tôi đã đo tay điều đó bằng Playwright và ghi lại con số ở đây để
// nó không phải là một lần đo rồi thôi:
//
//     hàm CŨ  (bản 19/08–05/09)  →  null
//     hàm MỚI (sau bản vá)       →  bài 3: "Tỉ lệ phần trăm"
//
// Chặn ĐÚNG MỘT lời gọi (`/api/courses/*/content`) để khỏi phụ thuộc nội dung
// CSDL. Mọi thứ khác là thật: trang Next thật, `lesson_hsa.js` thật,
// `chatbot.js` thật, DOM thật, thứ tự nạp script thật.
//
// KHÔNG cần đăng nhập: trang bài học render được cho khách (đã đo: HTTP 200),
// chỉ các lời gọi API khác trả 401 — không cản phép kiểm này.
import { expect, test } from '@playwright/test';

import { KHOA, expectChatbotBietBai } from './helpers';

const SO_BAI = 3;

const BAI = {
  id: 'e2e_03',
  title: 'Tỉ lệ phần trăm',
  topic_tag: 'Số học',
  test: {
    intro: 'Kiểm tra nhanh',
    questions: [{ id: 'q1', type: 'mcq', question: '10% của 200 là?', options: ['10', '20'] }],
  },
  theory: { full: { cards: [] }, condensed: { cards: [] } },
  notes: { key_points: ['phần trăm là phần của 100'], formula: 'p% của x = x·p/100' },
};

test('engine công bố bài đang mở và trợ lý đọc được', async ({ page }) => {
  const loiJs: string[] = [];
  page.on('pageerror', (e) => loiJs.push(String(e)));

  await page.route('**/api/courses/*/content*', (r) =>
    r.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ lesson: BAI, total: 27 }),
    }));

  await page.goto(`/lesson/${KHOA}?lesson=${SO_BAI}`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(
    () => !!(window as unknown as { __PE_BAI_DANG_MO?: unknown }).__PE_BAI_DANG_MO,
    undefined,
    { timeout: 30_000 },
  );

  // Công bố đúng khoá và đúng SỐ BÀI trên URL. Số bài trước bản vá chỉ tồn tại
  // như biến cục bộ của `init()` — không ai ngoài hàm ấy đọc được.
  const mo = await page.evaluate(
    () => (window as unknown as {
      __PE_BAI_DANG_MO: { courseId: string; index: number; lesson: { title: string } };
    }).__PE_BAI_DANG_MO,
  );
  expect(mo.courseId).toBe(KHOA);
  expect(mo.index).toBe(SO_BAI);
  expect(mo.lesson.title).toBe(BAI.title);

  await expectChatbotBietBai(page, SO_BAI);

  // Tên khoá KHÔNG đi từ client nữa — máy chủ tra từ bảng `courses`.
  const ctx = await page.evaluate(
    () => (window as unknown as { collectLessonContext: () => Record<string, unknown> })
      .collectLessonContext(),
  );
  expect(Object.keys(ctx)).not.toContain('course_title');
  expect(ctx.lesson_title).toBe(BAI.title);

  expect(loiJs, 'trang không được ném lỗi JS').toEqual([]);
});
