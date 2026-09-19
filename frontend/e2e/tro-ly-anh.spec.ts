// Ảnh đính kèm của trợ lý phải ĐI TỚI máy chủ — kiểm trong TRÌNH DUYỆT THẬT.
//
// ── VÌ SAO (20/09/2026) ─────────────────────────────────────────────────────
//
// Nút kẹp giấy của trợ lý có từ bản Gemini đầu tiên. Người dùng chọn ảnh, thấy
// ô xem trước, bấm gửi, thấy ảnh mình hiện trong khung chat — và mô hình chưa
// từng nhận nó: `sendChatbotMessage` xoá ảnh khỏi state trước khi đọc nó để
// gửi, còn `callChatbotGemini` không gửi trường ảnh nào. Hai lỗi chồng nhau,
// không lỗi nào kêu, vì màn hình vẫn "đúng".
//
// Phép kiểm này đi đúng đường người dùng đi: chọn tệp qua `<input type=file>`,
// bấm gửi, rồi ĐỌC thân request tới `/api/chat`. Ảnh nguồn 2400×1600 để chứng
// minh phần co về ≤1280px có chạy (ảnh điện thoại 3–8 MB gửi nguyên thì vượt
// trần thân request của Django). Chặn `/api/chat` để không tốn tiền DeepSeek.
import { expect, test } from '@playwright/test';

import { KHOA } from './helpers';

const BAI = {
  id: 'e2e_03',
  title: 'Tỉ lệ phần trăm',
  topic_tag: 'Số học',
  test: { intro: 'x', questions: [{ id: 'q1', type: 'mcq', question: '?', options: ['1', '2'] }] },
  theory: { full: { cards: [] }, condensed: { cards: [] } },
  notes: { key_points: [], formula: '' },
};

/** PNG 2400×1600 nền trắng có một vệt đen — dựng bằng canvas ngay trong trang. */
async function anhLon(page: import('@playwright/test').Page): Promise<Buffer> {
  const dataUrl = await page.evaluate(() => {
    const c = document.createElement('canvas');
    c.width = 2400; c.height = 1600;
    const g = c.getContext('2d')!;
    g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height);
    g.fillStyle = '#000'; g.font = '120px sans-serif'; g.fillText('Câu 7. 2x + 3 = 11', 100, 400);
    return c.toDataURL('image/png');
  });
  return Buffer.from(dataUrl.split(',')[1], 'base64');
}

test('ảnh đính kèm được co nhỏ và gửi trong trường `image` của /api/chat', async ({ page }) => {
  const loiJs: string[] = [];
  page.on('pageerror', (e) => loiJs.push(String(e)));

  await page.route('**/api/courses/*/content*', (r) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ lesson: BAI, total: 27 }) }));

  let than: { messages: { role: string; content: string }[]; image?: string } | null = null;
  await page.route('**/api/chat', (r) => {
    than = r.request().postDataJSON();
    return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ reply: 'đã nhận ảnh' }) });
  });

  await page.goto(`/lesson/${KHOA}?lesson=3`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => typeof (window as unknown as { sendChatbotMessage?: unknown }).sendChatbotMessage === 'function');

  await page.click('#chatbot-toggle');
  await page.setInputFiles('#chatbot-image-upload', {
    name: 'de.png', mimeType: 'image/png', buffer: await anhLon(page),
  });
  // Ô xem trước hiện ảnh ĐÃ CO (data URL JPEG), không phải tệp gốc.
  await expect(page.locator('#chatbot-image-preview')).not.toHaveClass(/chatbot-hidden/);
  await expect.poll(() => page.locator('#chatbot-preview-img').getAttribute('src')).toMatch(/^data:image\/jpeg;base64,/);

  await page.fill('#chatbot-input', 'đọc đề trong ảnh giúp mình');
  await page.click('#chatbot-send-btn');
  await expect.poll(() => than, { timeout: 15_000 }).not.toBeNull();

  const b = than!;
  expect(b.image, 'thân request KHÔNG có ảnh — nút đính kèm lại là nút giả').toMatch(/^data:image\/jpeg;base64,/);
  expect(b.messages.at(-1)).toEqual({ role: 'user', content: 'đọc đề trong ảnh giúp mình' });

  // Kích thước thật của ảnh gửi đi: cạnh dài đúng 1280 (từ 2400), tỉ lệ giữ nguyên.
  const kich = await page.evaluate((src) => new Promise<[number, number]>((ok) => {
    const im = new Image();
    im.onload = () => ok([im.naturalWidth, im.naturalHeight]);
    im.src = src;
  }), b.image!);
  expect(kich).toEqual([1280, 853]);
  expect(b.image!.length).toBeLessThan(1_600_000);

  // Ảnh KHÔNG bị nhân vào lịch sử: lượt sau không có ảnh, và lượt trước giữ dạng chữ.
  than = null;
  await page.fill('#chatbot-input', 'còn câu 8?');
  await page.click('#chatbot-send-btn');
  await expect.poll(() => than, { timeout: 15_000 }).not.toBeNull();
  expect(than!.image).toBeUndefined();
  expect(than!.messages.map((m) => typeof m.content)).not.toContain('object');

  expect(loiJs, 'trang không được ném lỗi JS').toEqual([]);
});
