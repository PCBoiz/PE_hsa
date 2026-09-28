/**
 * ĐO "HỌC VỤ PHỤ TRÁCH LỚP" (bảng TopHSA dòng 4) — bấm chuột trên màn thật.
 *
 *     node scripts/do_hoc_vu_phu_trach.mjs [--anh <thư mục>]
 *
 * Thẻ học vụ đọc từ `.the/tokens_hvu.json`. Gọi `chay()` của `lib/phien_do.mjs`.
 */
import { chay } from './lib/phien_do.mjs';

const WEB = process.env.PE_WEB || 'http://localhost:3100';
const anh = process.argv.includes('--anh') ? process.argv[process.argv.indexOf('--anh') + 1] : null;

const buoc = [];
function ghi(ten, dat, chiTiet) {
  buoc.push({ dat });
  console.log(`${dat ? 'ĐẠT ' : 'HỎNG'} ${ten}${chiTiet ? ` — ${chiTiet}` : ''}`);
}

await chay({ goc: WEB, anh }, async (phien) => {
  const page = await phien.man('/quan-tri/lop-hoc', 'hvu');
  if (!page.url().includes('/lop-hoc')) {
    console.log(`\nKHÔNG ĐO ĐƯỢC — bị đẩy sang ${page.url()}`);
    process.exitCode = 2;
    return;
  }

  // Mở một lớp. Nút hiện trong HTML máy chủ nhưng chỉ sống sau khi React gắn —
  // bấm lại tới khi khối nhân sự hiện ra, có trần.
  const khoi = page.locator('[data-khu="nhan-su-Học vụ phụ trách"]');
  const nutMo = page.locator('button', { hasText: /Học viên|Mở lớp|Xem/ }).first();
  for (let i = 0; i < 6 && !(await khoi.count()); i++) {
    await nutMo.click().catch(() => {});
    await khoi.waitFor({ state: 'visible', timeout: 3000 }).catch(() => {});
  }
  ghi('mở được một lớp, thấy khối nhân sự', (await khoi.count()) > 0);
  if (!(await khoi.count())) { process.exitCode = 1; return; }

  const chu = (await khoi.innerText()).trim();
  ghi('khối nói bằng tiếng Việt', chu.includes('Học vụ phụ trách'), chu.split('\n')[0]);

  const o = khoi.locator('select').first();
  const muc = await o.locator('option').allInnerTexts();
  ghi('có danh sách học vụ để chọn', muc.length > 1, `${muc.length - 1} người`);
  ghi('không mã kỹ thuật nào lọt lên màn',
      !/ROLE_|class_members|academics/.test(chu + muc.join(' ')));

  // Khối trợ giảng phải còn nguyên — hai khối dùng chung một component.
  const khoiTg = page.locator('[data-khu="nhan-su-Trợ giảng của lớp"]');
  ghi('khối trợ giảng cũ vẫn còn', (await khoiTg.count()) > 0);

  if (muc.length > 1) {
    const ten = (muc[1] || '').trim();
    await o.selectOption({ label: ten });
    await khoi.locator('button', { hasText: /^Gán$/ }).click();
    await khoi.locator('span', { hasText: ten }).first()
      .waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
    ghi('gán được người phụ trách', (await khoi.locator(`text=${ten}`).count()) > 0, ten);
    await phien.chup(page, 'hoc-vu-phu-trach', { toi: '[data-khu="nhan-su-Học vụ phụ trách"]' });

    // Dọn: gỡ ra để lượt đo sau bắt đầu sạch. Hộp xác nhận của trình duyệt phải nhận trước.
    page.once('dialog', (d) => void d.accept());
    await khoi.locator('button[aria-label^="Gỡ"]').first().click().catch(() => {});
    await page.waitForTimeout(2000);
  }

  const dat = buoc.filter((b) => b.dat).length;
  console.log(`\n${dat}/${buoc.length} bước ĐẠT`);
  if (dat < buoc.length) process.exitCode = 1;
});
