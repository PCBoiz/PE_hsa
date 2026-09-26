/**
 * ĐO "DUYỆT = TỰ LÀM" cho xin học bù (bảng TopHSA dòng 12) — bấm chuột trên màn thật.
 *
 *     PE_YC=<id yêu cầu> node scripts/do_duyet_hoc_bu.mjs [--anh <thư mục>]
 *
 * Thẻ học vụ ở `.the/tokens_hvu.json`. Gọi `chay()` của `lib/phien_do.mjs`.
 */
import { chay } from './lib/phien_do.mjs';

const WEB = process.env.PE_WEB || 'http://localhost:3100';
const YC = process.env.PE_YC;
const anh = process.argv.includes('--anh') ? process.argv[process.argv.indexOf('--anh') + 1] : null;

const buoc = [];
function ghi(ten, dat, chiTiet) {
  buoc.push({ dat });
  console.log(`${dat ? 'ĐẠT ' : 'HỎNG'} ${ten}${chiTiet ? ` — ${chiTiet}` : ''}`);
}

await chay({ goc: WEB, anh }, async (phien) => {
  const page = await phien.man(`/yeu-cau/${YC}`, 'hvu');
  if (!page.url().includes('/yeu-cau')) {
    console.log(`\nKHÔNG ĐO ĐƯỢC — bị đẩy sang ${page.url()}`);
    process.exitCode = 2;
    return;
  }

  // Mở khối Duyệt. Nút nằm trong HTML máy chủ nhưng chỉ sống sau khi React gắn.
  // Nút mở khối là "Duyệt…" (có dấu ba chấm) — `/^Duyệt$/` không khớp, và bộ đo bản đầu
  // báo "màn không có ô chọn buổi" cho một màn hoàn toàn đúng. Soi màn mới thấy.
  const oBuoi = page.locator('select').first();
  const nutDuyet = page.locator('button', { hasText: /^Duyệt…?$/ }).first();
  for (let i = 0; i < 6 && !(await oBuoi.count()); i++) {
    await nutDuyet.click().catch(() => {});
    await oBuoi.waitFor({ state: 'visible', timeout: 3000 }).catch(() => {});
  }
  ghi('màn duyệt có ô "Xếp vào buổi bù"', (await oBuoi.count()) > 0);
  if (!(await oBuoi.count())) { process.exitCode = 1; return; }

  // Danh sách buổi tải bằng JS SAU khi khối mở ra — đọc ngay là đọc lúc mới có mỗi dòng
  // "— Chọn buổi bù —", và bộ đo báo "0 buổi" cho một ô hoàn toàn đúng.
  await oBuoi.locator('option').nth(1).waitFor({ state: 'attached', timeout: 10000 }).catch(() => {});
  const muc = await oBuoi.locator('option').allInnerTexts();
  ghi('ô liệt kê buổi bù của lớp', muc.length > 1, `${muc.length - 1} buổi: ${(muc[1] || '').trim()}`);
  ghi('không mã kỹ thuật nào lọt lên màn',
      !/session_id|makeup_for|tt_hoc_bu/.test(muc.join(' ')));

  await oBuoi.selectOption({ index: 1 });
  // Xem trước phải nói hệ thống SẼ làm gì, trước khi bấm.
  const xt = page.locator('text=/Hệ thống sẽ/i').first();
  await xt.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
  const cauXt = (await xt.innerText().catch(() => '')).trim();
  ghi('xem trước nói rõ hệ thống sẽ làm gì', /xếp|buổi bù/i.test(cauXt), cauXt.slice(0, 80));

  await page.locator('button', { hasText: /Duyệt và thực hiện/ }).first().click();
  await page.locator('text=/Đã xong|Đã duyệt/i').first()
    .waitFor({ state: 'visible', timeout: 12000 }).catch(() => {});
  const chu = (await page.locator('main, body').first().innerText()).replace(/\s+/g, ' ');
  ghi('duyệt xong, yêu cầu ĐÓNG', /Đã xong/i.test(chu), (chu.match(/Đã xong[^.]*/) || [''])[0].slice(0, 60));
  ghi('lịch sử nói hệ thống đã xếp em vào buổi bù', /xếp .* vào buổi bù/i.test(chu),
      (chu.match(/Đã xếp[^.]*/) || ['(không thấy)'])[0].slice(0, 70));

  await phien.chup(page, 'duyet-hoc-bu', { toanTrang: true });

  const dat = buoc.filter((b) => b.dat).length;
  console.log(`\n${dat}/${buoc.length} bước ĐẠT`);
  if (dat < buoc.length) process.exitCode = 1;
});
