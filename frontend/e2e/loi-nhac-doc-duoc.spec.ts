// Lời nhắc của trang bài học phải ĐỌC ĐƯỢC bằng trình đọc màn hình.
//
// ── VÌ SAO (audit 05/09/2026) ───────────────────────────────────────────────
//
// `#hsa-flash` là kênh phản hồi DUY NHẤT của cả trang bài học, và bản trước là
// một `<div>` trơn — không `role`, không `aria-live`. Bảy câu đi qua đó, trong
// đó BỐN câu là lý do màn hình không nhúc nhích khi bấm nút:
//
//   "Hãy trả lời đủ N câu trước khi xem đánh giá."
//   "Chưa chấm được — kiểm tra mạng rồi bấm lại."
//   "Hãy hoàn thành bài kiểm tra ở Bước 1 trước."
//   cauLoiMayChu(...)  ← chính những câu được viết lại cho chính xác hôm 04/09
//
// Không nghe được chúng thì trải nghiệm đúng bằng "bấm mãi mà chẳng có gì xảy
// ra" — cùng một họ với A13: hỏng mà không có gì báo là hỏng.
//
// Kiểm trong TRÌNH DUYỆT THẬT chứ không quét mã: `role`/`aria-live` chỉ có
// nghĩa khi phần tử thật sự nằm trong DOM lúc chữ xuất hiện, và đó là thứ chỉ
// đo được lúc chạy.
import { expect, test } from '@playwright/test';

import { KHOA } from './helpers';

const BAI = {
  id: 'e2e_a11y',
  index: 3,
  title: 'Tỉ lệ phần trăm',
  topic_tag: 'Số học',
  test: {
    intro: '',
    questions: [
      { id: 'q1', type: 'mcq', question: '10% của 200?', options: ['10', '20'] },
      { id: 'q2', type: 'fill', question: 'Một nửa = ? %' },
    ],
  },
  theory: { full: { cards: [] }, condensed: { cards: [] } },
  notes: { key_points: [], formula: '' },
};

test('câu nhắc CHẶN nằm trong vùng sống assertive', async ({ page }) => {
  await page.route('**/api/courses/*/content*', (r) =>
    r.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ lesson: BAI, total: 27 }),
    }));

  await page.goto(`/lesson/${KHOA}?lesson=3`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(
    () => !!(window as unknown as { __PE_BAI_DANG_MO?: unknown }).__PE_BAI_DANG_MO,
    undefined,
    { timeout: 30_000 },
  );

  // Nộp khi chưa trả lời gì: engine chặn, và PHẢI nói ra.
  await page.click('#nav-next');

  const vung = page.locator('#hsa-flash-alert');
  await expect(vung, 'không có vùng nhắc nào → học viên bấm nút mà không thấy gì')
    .toHaveCount(1);
  await expect(vung).toHaveAttribute('role', 'alert');
  await expect(vung).toHaveAttribute('aria-live', 'assertive');
  // Không có `aria-atomic` thì trình đọc màn hình chỉ đọc phần chữ THAY ĐỔI,
  // nên câu thứ hai dùng chung vùng có thể ra một mẩu vô nghĩa.
  await expect(vung).toHaveAttribute('aria-atomic', 'true');

  await expect(vung).toHaveText(/Hãy trả lời đủ 2 câu/);

  // Và phải NHÌN thấy được nữa — vùng sống đúng mà ẩn thì người sáng mắt mất
  // phản hồi. Hai đối tượng, một kênh, cùng phải hoạt động.
  await expect(vung).toHaveCSS('opacity', '1');

  // Vẫn ở bước 1: câu nhắc phải khớp với việc thật sự bị chặn.
  const buoc = await page.evaluate(
    () => document.querySelector('.progress-step.active')?.getAttribute('data-step'));
  expect(buoc).toBe('1');
});
