/**
 * Đo trang PHỤ HUYNH `/bc/<chìa>` trên PRODUCTION, trong vai một điện thoại.
 *
 * ── VÌ SAO KHÁC `do_hieu_nang.mjs` (17/09/2026) ─────────────────────────────
 *
 * `do_hieu_nang.mjs` đo sáu màn đã đăng nhập, khổ MÁY TÍNH, trên bản dựng CHẠY
 * Ở MÁY NÀY. Với trang phụ huynh cả ba điều ấy đều sai chỗ:
 *
 *   · Người mở là PHỤ HUYNH, trên ĐIỆN THOẠI, từ một tin nhắn.
 *   · Bản dựng ở máy này gọi Django ở máy này, Django gọi Neon ở Mỹ — mỗi truy
 *     vấn ~250 ms từ Việt Nam. Trên production thì Vercel → Render → Neon nằm
 *     cùng một vùng. Đo ở máy này là đo đường truyền Việt Nam–Mỹ của MÁY CHỦ,
 *     không phải thứ phụ huynh chờ.
 *   · Nên đo thẳng production: đúng đường phụ huynh đi (điện thoại → Vercel).
 *
 * ── HAI CHẾ ĐỘ ──────────────────────────────────────────────────────────────
 *
 *   nhanh  mạng thật của máy đang chạy lệnh (thường tốt hơn 4G của phụ huynh).
 *   4g     chồng thêm hạn chế kiểu Lighthouse di động: 150 ms, 1,6 Mbps xuống.
 *          ĐÂY LÀ GIẢ LẬP. DevTools không mô phỏng đúng ưu tiên của HTTP/2, nên
 *          số tuyệt đối có thể xấu hơn thật; dùng để SO SÁNH hai bản dựng, đừng
 *          dùng làm lời hứa về tốc độ.
 *
 * Cả hai: khổ 390×844, CPU chậm 4×, TẮT bộ đệm mỗi lượt (đo lần mở ĐẦU của phụ
 * huynh, không phải lần ghé thứ hai), 5 lượt lấy TRUNG VỊ theo LCP, in cả 5 số.
 *
 * ── SỐ ĐO LẦN ĐẦU, 17/09/2026 22:2x (5 lượt mỗi chế độ) ────────────────────
 *
 *   nhanh: LCP 860 / 1.044 / 1.136 / 1.780 / 2.640 ms · CLS 0 · 323 kB · DOM 167
 *   4g   : LCP 1.896 / 2.248 / 2.332 / 2.460 / 3.320 ms · FCP = LCP
 *
 *   Phông chữ ≈ MỘT NỬA số byte của trang (16 tệp woff2, 18 thẻ preload), trong
 *   khi trang chỉ dùng 9 tệp (Be Vietnam Pro 400/600/700 × 3 dải ký tự). A/B xen
 *   kẽ 6+6 lượt, chế độ 4g: chặn MỌI tệp woff2 → FCP trung vị 2.560 → 1.888 ms,
 *   CSS chặn-vẽ xong 1.621 → 857 ms. Tức preload phông tranh băng thông với CSS.
 *   Chưa sửa — xem TODO "phông trang phụ huynh": muốn bớt tệp thì hoặc bỏ trọng
 *   lượng 500/800 (tầng CSS cũ dùng 158 chỗ), hoặc tách layout theo nhóm tuyến.
 *   Cả hai là đánh đổi, không phải vá.
 *
 * ── MỖI LƯỢT ĐO LÀ MỘT LƯỢT "MỞ" ────────────────────────────────────────────
 *
 * Trang dựng ở máy chủ, nên mỗi lần tải tăng `opened_count` của chìa. 5 lượt đo
 * = "đã mở 5 lần". Vì vậy chỉ đo bằng chìa của LỚP MẪU, cấp bằng
 * `scripts/cap_chia_mau.py` (tệp ấy ghi rõ nó ghi gì).
 *
 * Chạy:
 *   backend/.venv/Scripts/python.exe scripts/cap_chia_mau.py     # một lần
 *   curl https://pe-hsa-backend.onrender.com/health              # đánh thức Render trước!
 *   node scripts/do_trang_phu_huynh.mjs nhanh
 *   node scripts/do_trang_phu_huynh.mjs 4g
 */
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { baoHiem } from './lib/phien_do.mjs';

const _doi = createRequire('D:/pe_hsa/frontend/package.json');
let chromium = null;
for (const t of ['@playwright/test', 'playwright']) { try { ({ chromium } = _doi(t)); break; } catch { /* thử gói sau */ } }

const CHE_DO = process.argv[2] || 'nhanh';
if (!['nhanh', '4g'].includes(CHE_DO)) {
  console.error('Chế độ phải là "nhanh" hoặc "4g".');
  process.exit(2);
}
const { token } = JSON.parse(readFileSync('D:/pe_hsa/.the/chia_mau.json', 'utf8'));
const GOC = process.env.PE_GOC || 'https://pe-hsa.vercel.app';
const SO_LUOT = 5;

const b = await chromium.launch({ channel: 'chrome' });
baoHiem(b);   // đóng trình duyệt cả khi Ctrl-C / lỗi không ai bắt
const ctx = await b.newContext({
  viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
});
// Làm nóng TRÌNH DUYỆT bằng một trang không cần chìa (không tăng opened_count).
{ const p = await ctx.newPage(); await p.goto(GOC + '/login', { waitUntil: 'load' }); await p.close(); }

const LOAI = (ct, url) => (/font|woff2?/.test(ct) || /\.woff2?$/.test(url) ? 'phông'
  : /javascript/.test(ct) ? 'JS' : /css/.test(ct) ? 'CSS' : /html/.test(ct) ? 'HTML' : 'khác');

const luot = [];
for (let i = 0; i < SO_LUOT; i += 1) {
  const p = await ctx.newPage();
  const cdp = await ctx.newCDPSession(p);
  await cdp.send('Network.enable');
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  if (CHE_DO === '4g') {
    await cdp.send('Network.emulateNetworkConditions', {
      offline: false, latency: 150,
      downloadThroughput: (1.6 * 1024 * 1024) / 8, uploadThroughput: (750 * 1024) / 8,
    });
  }
  // Byte QUA MẠNG (đã nén) theo loại — `content-length` thường vắng khi nén
  // luồng, nên đọc `encodedDataLength` của CDP thay vì tiêu đề phản hồi.
  const loai = new Map(); const byte = {};
  cdp.on('Network.responseReceived', (e) => loai.set(e.requestId, LOAI(e.response.mimeType, e.response.url)));
  cdp.on('Network.loadingFinished', (e) => {
    const k = loai.get(e.requestId) || 'khác';
    byte[k] = (byte[k] || 0) + e.encodedDataLength;
  });

  const res = await p.goto(`${GOC}/bc/${token}`, { waitUntil: 'load' });
  await p.waitForTimeout(1500);
  const d = await p.evaluate(() => new Promise((ok) => {
    let lcp = 0; let cls = 0;
    new PerformanceObserver((l) => { for (const e of l.getEntries()) lcp = e.startTime; })
      .observe({ type: 'largest-contentful-paint', buffered: true });
    new PerformanceObserver((l) => { for (const e of l.getEntries()) if (!e.hadRecentInput) cls += e.value; })
      .observe({ type: 'layout-shift', buffered: true });
    const fcp = performance.getEntriesByName('first-contentful-paint')[0];
    setTimeout(() => ok({
      fcp: Math.round(fcp ? fcp.startTime : -1), lcp: Math.round(lcp),
      cls: Math.round(cls * 1000) / 1000, dom: document.querySelectorAll('*').length,
      cuonNgang: document.documentElement.scrollWidth > window.innerWidth,
      // Trang lỗi ("Không mở được báo cáo này") cũng nhẹ và nhanh — một lượt đo
      // trên chìa chết sẽ in số ĐẸP mà vô nghĩa. Bắt buộc thấy nội dung báo cáo.
      laBaoCao: document.body.innerText.includes('Con có đi học không'),
    }), 300);
  }));
  await p.close();
  if (res.status() !== 200 || !d.laBaoCao) {
    console.error(`Lượt ${i + 1}: KHÔNG phải tờ báo cáo (HTTP ${res.status()}) — chìa hết hạn/thu hồi? Dừng, không in số.`);
    await b.close();
    process.exit(1);
  }
  luot.push({ ...d, byte });
}
await b.close();

luot.sort((a, x) => a.lcp - x.lcp);
const g = luot[Math.floor(luot.length / 2)];
const kb = (n) => Math.round((n || 0) / 1024);
const tong = Object.values(g.byte).reduce((s, n) => s + n, 0);
console.log(`/bc/<chìa> · production · điện thoại 390px · CPU 4× · mạng=${CHE_DO} · ${SO_LUOT} lượt, trung vị theo LCP`);
console.log(`  LCP các lượt : ${luot.map((x) => x.lcp).join(' / ')} ms`);
console.log(`  trung vị     : FCP ${g.fcp} ms · LCP ${g.lcp} ms · CLS ${g.cls} · DOM ${g.dom} · cuộn ngang: ${g.cuonNgang ? 'CÓ' : 'không'}`);
console.log(`  byte qua mạng: ${kb(tong)} kB = ${Object.entries(g.byte).sort((a, x) => x[1] - a[1]).map(([k, n]) => `${k} ${kb(n)}`).join(' · ')}`);
if (g.lcp > 2500) console.log('  ⚠ LCP trung vị > 2.500 ms (ngưỡng "tốt" của Core Web Vitals)');
