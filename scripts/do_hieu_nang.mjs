/* ĐO HIỆU NĂNG bằng chính giao thức DevTools (CDP), qua Playwright.
 *
 * ── VÌ SAO CÓ TỆP NÀY (07/09/2026) ────────────────────────────────────────
 *
 * Anh Sơn chỉ ra rằng `chrome-devtools-mcp` sẽ giúp audit luồng người dùng
 * thoải mái hơn. Đúng, và nó chỉ ra một lỗ thật: cả phiên ấy tôi đo bố cục,
 * vùng chạm, tương phản, lỗi JS — nhưng CHƯA đo hiệu năng lần nào.
 *
 * MCP ấy chưa được nối vào phiên. Nhưng Playwright mở được ĐÚNG giao thức nằm
 * dưới nó (`newCDPSession`), nên đo được ngay mà không cần cài thêm gì. Nếu
 * sau này nối MCP thật thì tệp này vẫn có ích: nó chạy được trong CI, còn MCP
 * thì cần một phiên trò chuyện.
 *
 * ── HAI ĐIỀU KIỆN ĐO, CẢ HAI ĐỀU BẮT BUỘC ────────────────────────────────
 *
 * 1. **Phải đo bản PRODUCTION** (`next build && next start`), không đo dev.
 *    Đo lần đầu trên dev cho `Ai làm được gì` = 5480ms; đo lại trên production
 *    = **1036ms**. Chênh gấp năm, và toàn bộ phần chênh là chi phí biên dịch
 *    theo yêu cầu của dev server. Một con số đo trên dev rồi gọi là hiệu năng
 *    thì tệ hơn không đo: nó làm người ta đi tối ưu nhầm chỗ.
 *
 * 2. **Phải đo trên máy YẾU** (`Emulation.setCPUThrottlingRate: 4`). Học sinh
 *    cấp 3 không dùng máy như máy dev. Đo trên máy khoẻ là tự khen mình.
 *
 * ── SỐ ĐO 07/09/2026 (production, CPU chậm 4×) ───────────────────────────
 *
 *     màn hình               LCP      CLS    JS(kB)   DOM
 *     Trang của tôi        2168ms        0      222    889
 *     Thi thử              1612ms    0.002      237    244
 *     Vận hành             1956ms    0.005      222    248
 *     Báo cáo phụ huynh    1168ms        0      222    187
 *     Ai làm được gì       1036ms    0.006      222    783
 *     Hướng dẫn            1508ms        0      222    353
 *
 * Không màn nào vượt ngưỡng Core Web Vitals (LCP 2500ms, CLS 0.1) — NHƯNG
 * "Trang của tôi" nằm NGAY SÁT: ba lượt đo cho 2168 / 2528 / 2400ms, tức nó
 * vượt ở một trong ba lượt. Ghi cả ba chứ không lấy lượt đẹp nhất.
 *
 * Vì sao riêng màn ấy: 889 nút DOM (gấp 3-4 lần các màn khác) và nó là màn
 * DUY NHẤT còn nạp cả tầng JS cũ (main.js + dashboard.js + icons.js…). Đó
 * cũng đúng là màn học viên mở nhiều nhất. Chưa tối ưu ở đây — ghi lại để
 * lần sau có chỗ bắt đầu, và để ai đó đừng đi tối ưu một màn đang 1036ms.
 *
 * Chạy:
 *     cd frontend && npx next build && npx next start -p 3100
 *     node scripts/do_hieu_nang.mjs
 */
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
const _doi = createRequire('D:/pe_hsa/frontend/package.json');
let chromium=null; for (const t of ['@playwright/test','playwright']) { try { ({chromium}=_doi(t)); break; } catch {} }
const the = JSON.parse(readFileSync('D:/pe_hsa/.the/tokens_ad.json','utf8'));

const MAN = [
  ['Trang của tôi',      '/dashboard'],
  ['Thi thử',            '/mock'],
  ['Vận hành',           '/quan-tri/tong-quan'],
  ['Báo cáo phụ huynh',  '/giang-day/bao-cao/1'],
  ['Ai làm được gì',     '/quan-tri/vai-tro'],
  ['Hướng dẫn',          '/quan-tri/huong-dan'],
];

const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1366, height: 768 } });
await ctx.addCookies([{name:'pe_at',value:the.access,domain:'localhost',path:'/',httpOnly:true,sameSite:'Lax'}]);

console.log('màn hình'.padEnd(20), 'LCP'.padStart(8), 'CLS'.padStart(7),
            'chặn'.padStart(7), 'JS(kB)'.padStart(8), 'req'.padStart(5), 'DOM'.padStart(6));
console.log('─'.repeat(66));
const ra = [];
for (const [ten, url] of MAN) {
  const p = await ctx.newPage();
  const cdp = await p.context().newCDPSession(p);
  await cdp.send('Network.enable');
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });   // máy yếu

  let byteJs = 0, soReq = 0;
  p.on('response', async (r) => {
    soReq += 1;
    const ct = r.headers()['content-type'] || '';
    if (/javascript/.test(ct)) {
      try { byteJs += (await r.body()).length; } catch { /* bị huỷ */ }
    }
  });

  await p.goto('http://localhost:3100' + url, { waitUntil: 'networkidle' });
  await p.waitForTimeout(1200);

  const d = await p.evaluate(() => new Promise((res) => {
    let lcp = 0, cls = 0;
    new PerformanceObserver((l) => { for (const e of l.getEntries()) lcp = e.startTime; })
      .observe({ type: 'largest-contentful-paint', buffered: true });
    new PerformanceObserver((l) => {
      for (const e of l.getEntries()) if (!e.hadRecentInput) cls += e.value;
    }).observe({ type: 'layout-shift', buffered: true });
    const chan = performance.getEntriesByType('longtask')
      .reduce((s, t) => s + t.duration, 0);
    setTimeout(() => res({
      lcp: Math.round(lcp), cls: Math.round(cls * 1000) / 1000,
      chan: Math.round(chan), dom: document.querySelectorAll('*').length,
    }), 400);
  }));

  ra.push({ ten, url, ...d, js: Math.round(byteJs / 1024), req: soReq });
  console.log(ten.padEnd(20), (d.lcp + 'ms').padStart(8), String(d.cls).padStart(7),
              (d.chan + 'ms').padStart(7), String(Math.round(byteJs/1024)).padStart(8),
              String(soReq).padStart(5), String(d.dom).padStart(6));
  await p.close();
}
await b.close();

console.log('\n── Ngưỡng Core Web Vitals (máy CPU chậm 4×) ──');
const xau = [];
for (const r of ra) {
  if (r.lcp > 2500) xau.push(`${r.ten}: LCP ${r.lcp}ms > 2500ms`);
  if (r.cls > 0.1) xau.push(`${r.ten}: CLS ${r.cls} > 0.1`);
  if (r.dom > 1500) xau.push(`${r.ten}: ${r.dom} nút DOM (>1500)`);
}
console.log(xau.length ? xau.map(s => '  ⚠ ' + s).join('\n') : '  không màn nào vượt ngưỡng');
