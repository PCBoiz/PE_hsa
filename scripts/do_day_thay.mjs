/**
 * ĐO "AI DẠY BUỔI NÀY" (§58, bảng TopHSA dòng 10) — bấm chuột trên màn thật.
 *
 *     node scripts/do_day_thay.mjs [--anh <thư mục>]
 *
 * Thẻ giảng viên đọc từ `.the/tokens_gv.json`. Gọi `chay()` của `lib/phien_do.mjs`.
 */
import { chay } from './lib/phien_do.mjs';

const WEB = process.env.PE_WEB || 'http://localhost:3100';
const LOP = process.env.PE_LOP || '1';
const anh = process.argv.includes('--anh') ? process.argv[process.argv.indexOf('--anh') + 1] : null;

const buoc = [];
function ghi(ten, dat, chiTiet) {
  buoc.push({ dat });
  console.log(`${dat ? 'ĐẠT ' : 'HỎNG'} ${ten}${chiTiet ? ` — ${chiTiet}` : ''}`);
}

await chay({ goc: WEB, anh }, async (phien) => {
  const page = await phien.man(`/giang-day/buoi-hoc/${LOP}`, 'gv');
  if (!page.url().includes('/buoi-hoc')) {
    console.log(`\nKHÔNG ĐO ĐƯỢC — bị đẩy sang ${page.url()}`);
    process.exitCode = 2;
    return;
  }

  /**
   * Mở form sửa của buổi đầu tiên.
   *
   * Bấm MỘT lần rồi chờ là không đủ: nút "Sửa" nằm trong HTML máy chủ dựng, nhưng nó chỉ
   * làm được việc sau khi React gắn vào — bấm giữa hai mốc ấy thì cú bấm rơi vào hư
   * không, không dấu hiệu nào báo, và bộ đo kết luận "màn không có ô chọn" cho một màn
   * hoàn toàn đúng. Bấm lại tới khi form thật sự mở, có trần.
   */
  async function moForm() {
    const nut = page.locator('button', { hasText: /^Sửa$/ }).first();
    await nut.waitFor({ state: 'visible', timeout: 12000 }).catch(() => {});
    const o = page.locator('select[data-o="gv-buoi"]').first();
    for (let i = 0; i < 6; i++) {
      if (await o.count()) return true;
      await nut.click().catch(() => {});
      await o.waitFor({ state: 'visible', timeout: 2500 }).catch(() => {});
    }
    return (await o.count()) > 0;
  }

  ghi('mở được form sửa buổi', await moForm());

  const oGv = page.locator('select[data-o="gv-buoi"]').first();
  const oTg = page.locator('select[data-o="tg-buoi"]').first();
  ghi('có ô "Giảng viên buổi này"', (await oGv.count()) > 0);
  ghi('có ô "Trợ giảng buổi này"', (await oTg.count()) > 0);

  const chonGv = await oGv.locator('option').allInnerTexts();
  ghi('ô mặc định là "Theo lớp"', (chonGv[0] || '').trim() === 'Theo lớp', chonGv[0]);
  ghi('danh sách người do máy chủ trả', chonGv.length > 1, `${chonGv.length - 1} giảng viên`);

  // Chữ trên màn phải là tiếng Việt, không phải mã hay email trần.
  const chu = chonGv.join(' ');
  ghi('không mã kỹ thuật nào lọt lên ô chọn',
      !/teacher_id|assistant_id|ROLE_/.test(chu));

  // Chọn một người rồi lưu; đọc lại để chắc máy chủ đã nhận.
  const ten = (chonGv[1] || '').trim();
  await oGv.selectOption({ label: ten });
  const nutLuu = page.locator('button', { hasText: /Lưu/ }).first();
  await nutLuu.click();
  await page.waitForTimeout(2500);

  await page.reload({ waitUntil: 'domcontentloaded' });
  await moForm();
  const oGv2 = page.locator('select[data-o="gv-buoi"]').first();
  const daChon = await oGv2.locator('option:checked').innerText().catch(() => '');
  ghi('lưu xong, mở lại vẫn thấy người vừa chọn', daChon.trim() === ten,
      `${daChon.trim()} (mong ${ten})`);

  await phien.chup(page, 'day-thay-form', { toanTrang: false, toi: 'select[data-o="gv-buoi"]' });

  // Trả về "Theo lớp" để lượt đo sau bắt đầu từ trạng thái sạch.
  await oGv2.selectOption({ label: 'Theo lớp' });
  await page.locator('button', { hasText: /Lưu/ }).first().click();
  await page.waitForTimeout(2000);

  const dat = buoc.filter((b) => b.dat).length;
  console.log(`\n${dat}/${buoc.length} bước ĐẠT`);
  if (dat < buoc.length) process.exitCode = 1;
});
