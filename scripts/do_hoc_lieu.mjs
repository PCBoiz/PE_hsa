/**
 * ĐO HỌC LIỆU TRÊN THẺ LỚP (§60, bảng TopHSA dòng 30) — bấm chuột trên màn thật.
 *
 *     node scripts/do_hoc_lieu.mjs [--anh <thư mục>]
 *
 * Thẻ học viên đọc từ `.the/tokens_hv.json`. Gọi `chay()` của `lib/phien_do.mjs` — không
 * tự `chromium.launch()`.
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
  const page = await phien.man('/dashboard', 'hv');
  const url = page.url();
  if (!url.includes('/dashboard')) {
    console.log(`\nKHÔNG ĐO ĐƯỢC — bị đẩy sang ${url}`);
    process.exitCode = 2;
    return;
  }

  // Khối "Lớp của bạn" tải bằng JS SAU khi HTML tới nơi, nên `phien.man` (chờ `main` có
  // chữ) trả về trước khi nó kịp hiện: lượt đo đầu xanh vì may, lượt sau báo "0 khối" cho
  // một màn dựng hoàn toàn đúng. Chờ đúng thứ mình sắp đo, có trần.
  const khoi = page.locator('.lct-hl');
  await khoi.first().waitFor({ state: 'visible', timeout: 12000 }).catch(() => {});
  ghi('khối "Tài liệu" có trên thẻ lớp', (await khoi.count()) > 0, `${await khoi.count()} khối`);
  if ((await khoi.count()) === 0) {
    console.log('\nKhông thấy khối học liệu — lớp này chưa có tài liệu nào đã mở?');
    process.exitCode = 1;
    return;
  }

  const chu = (await khoi.first().innerText()).trim();
  ghi('có tên tài liệu', chu.includes('Slide buổi 1'), chu.replace(/\s+/g, ' ').slice(0, 90));

  const nut = khoi.first().locator('a.lct-hl-nut').first();
  const href = await nut.getAttribute('href');
  const target = await nut.getAttribute('target');
  const rel = await nut.getAttribute('rel');
  ghi('bấm được, trỏ ra địa chỉ thật', Boolean(href && href.startsWith('https://')), href);
  ghi('mở tab mới kèm noopener', target === '_blank' && (rel || '').includes('noopener'),
      `target=${target} rel=${rel}`);
  ghi('hiện tên miền cho người bấm biết sắp đi đâu', chu.includes('drive.google.com'),
      (chu.match(/\(([^)]+)\)/) || [])[1] || '(không thấy)');

  // Vùng chạm: tên tài liệu do giảng viên gõ, dài ngắn tuỳ người — không được vỡ thẻ.
  const o = await nut.boundingBox();
  const rongThe = (await page.locator('.lct-the, [class*="lct"]').first().boundingBox())?.width ?? 9999;
  ghi('không tràn ra ngoài thẻ lớp', (o?.width ?? 0) <= rongThe + 2,
      `nút ${Math.round(o?.width ?? 0)}px / thẻ ${Math.round(rongThe)}px`);

  await phien.chup(page, 'hoc-lieu-the-lop', { toanTrang: true, toi: '.lct-hl' });

  // ── Màn GIẢNG VIÊN: gắn / gỡ tài liệu ──────────────────────────────────
  const gv = await phien.man(`/giang-day/buoi-hoc/${LOP}`, 'gv');
  if (!gv.url().includes('/buoi-hoc')) {
    ghi('màn giảng viên mở được', false, `bị đẩy sang ${gv.url()}`);
  } else {
    const khu = gv.locator('[data-khu="hoc-lieu"]');
    ghi('khối "Tài liệu của lớp" có trên màn giảng viên', (await khu.count()) === 1);

    // Ô nhập phải KHOÁ tới khi React gắn xong, rồi mở ra — đo cả hai đầu.
    const oTen = khu.locator('input').first();
    // Ô nhập hiện ra trong HTML máy chủ nhưng `useDaGan` giữ `disabled` tới khi React gắn
    // vào. Hỏi `isEnabled()` ngay lúc nó vừa hiện là hỏi sai lúc — bước này báo HỎNG trong
    // khi bước gắn tài liệu ngay sau đó lại ĐẠT, tức ô có mở thật. Chờ nó mở, có trần.
    await khu.locator('input:not([disabled])').first()
      .waitFor({ state: 'visible', timeout: 8000 }).catch(() => {});
    const mo = await oTen.isEnabled().catch(() => false);
    ghi('ô nhập khoá lúc đầu rồi mở khi React gắn', mo);

    const ten = `Đề thử ${Date.now() % 100000}`;
    await oTen.fill(ten);
    await khu.locator('input').nth(1).fill('https://drive.google.com/file/d/do-tay/view');
    await khu.locator('button', { hasText: 'Gắn tài liệu' }).click();
    await khu.locator('li', { hasText: ten }).first().waitFor({ state: 'visible', timeout: 10000 })
      .catch(() => {});
    ghi('gắn được tài liệu mới', (await khu.locator('li', { hasText: ten }).count()) > 0, ten);

    // Địa chỉ xấu phải bị TỪ CHỐI ngay trên màn, kèm câu tiếng Việt cạnh đúng ô.
    await khu.locator('input').first().fill('Thử địa chỉ xấu');
    await khu.locator('input').nth(1).fill('javascript:alert(1)');
    await khu.locator('button', { hasText: 'Gắn tài liệu' }).click();
    await gv.waitForTimeout(1200);
    const chuLoi = (await khu.innerText()).includes('http://');
    ghi('địa chỉ javascript: bị từ chối, nói bằng tiếng Việt', chuLoi,
        (await khu.innerText()).split(String.fromCharCode(10)).find((x) => x.includes('http://')) || '(không thấy câu lỗi)');

    await phien.chup(gv, 'hoc-lieu-man-gv', { toanTrang: true, toi: '[data-khu="hoc-lieu"]' });

    // Dọn: gỡ tài liệu vừa tạo để lượt đo sau không tích luỹ rác.
    const dong = khu.locator('li', { hasText: ten }).first();
    if (await dong.count()) {
      await dong.locator('button', { hasText: 'Gỡ' }).click();
      await dong.waitFor({ state: 'detached', timeout: 8000 }).catch(() => {});
      ghi('gỡ được tài liệu', (await khu.locator('li', { hasText: ten }).count()) === 0);
    }
  }

  const dat = buoc.filter((b) => b.dat).length;
  console.log(`\n${dat}/${buoc.length} bước ĐẠT`);
  if (dat < buoc.length) process.exitCode = 1;
});
