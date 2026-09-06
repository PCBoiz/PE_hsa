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
 *     Trang của tôi        2740ms        0      329   1030    ← VƯỢT ngưỡng
 *     Thi thử              1612ms    0.002      237    244
 *     Vận hành             1956ms    0.005      222    248
 *     Báo cáo phụ huynh    1168ms        0      222    187
 *     Ai làm được gì       1036ms    0.006      222    783
 *     Hướng dẫn            1508ms        0      222    353
 *
 * Năm màn dưới đạt ngưỡng Core Web Vitals (LCP 2500ms, CLS 0.1). "Trang của
 * tôi" thì KHÔNG: ba lượt cho 2740 / 2824 / 2972ms. Ghi cả ba, không lấy lượt
 * đẹp nhất.
 *
 * ĐÍNH CHÍNH: bản đầu của bảng này ghi "Trang của tôi 2168ms · 222kB · 889
 * nút" và kết luận "sát ngưỡng nhưng chưa vượt". SAI — lúc ấy tệp này chưa có
 * chốt `/login` bên dưới, nên lượt đo rơi ra ngoài hạn thẻ đã đo MÀN ĐĂNG NHẬP
 * và in ra một bảng đẹp hơn sự thật. Giữ lại dòng này để số cũ nếu còn nằm
 * trong ghi chép nào đó thì tra ra được ngay là nó hỏng ở đâu.
 *
 * CẢNH BÁO VỀ CỘT `DOM` (đo 07/09): cột này đọc `querySelectorAll('*')` sau
 * `networkidle` + 1200ms. Trên "Trang của tôi" trang lúc ấy CHƯA dựng xong —
 * cột báo 1030 nút, còn trang thật đứng lại ở 1922 (DOM tăng gấp đôi trong
 * quãng 2,5s → 4s, tức sau cả mốc LCP). Nên ngưỡng `> 1500` bên dưới chưa bao
 * giờ nổ dù trang thật vượt. Cùng họ với bẫy `/login`: im lặng cho số đẹp hơn
 * sự thật. CHƯA vá — vá là đổi ngữ nghĩa cột, phải đo lại cả sáu màn.
 *
 * Vì sao riêng màn ấy: DOM lớn nhất trong sáu màn và
 * nó là màn DUY NHẤT còn nạp cả tầng JS cũ (main.js + dashboard.js +
 * icons.js…). Đó cũng đúng là màn học viên mở nhiều nhất. Đã gỡ Font Awesome
 * (-100kB CSS) và tải trước tầng JS cũ; phần còn lại là T31/T32.
 *
 * ── SỐ CHỈ TIN ĐƯỢC KHI TRANG THẬT SỰ MỞ ─────────────────────────────────
 *
 * Mỗi màn được kiểm là có rơi về `/login` không TRƯỚC khi lấy số. Màn đăng nhập
 * nhẹ (LCP thấp, DOM nhỏ, JS ít) nên một lượt đo trượt xác thực sẽ in ra một
 * bảng số ĐẸP HƠN sự thật — và không có gì trong bảng ấy nói rằng nó sai.
 * Thẻ access sống 30 phút, nên hãy cấp lại ngay trước mỗi lượt đo:
 *     python scripts/cap_the.py --id 7 --ra .the/tokens_ad.json
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

  /* Rơi về màn đăng nhập thì mọi số bên dưới đều VÔ NGHĨA mà vẫn in ra đẹp —
     màn đăng nhập nhẹ nên LCP thấp, DOM nhỏ, JS ít. Đúng cái bẫy đã sửa cho
     `do_giao_dien.mjs` hôm 05/09, và tôi dựng lại nó ở đây (07/09).
     Thẻ access sống 30 phút; một lượt đo dài là nó hết hạn giữa chừng. */
  if (p.url().includes('/login')) {
    console.log(ten.padEnd(20), 'BỎ QUA — rơi về /login (thẻ hết hạn?):', p.url());
    await p.close();
    continue;
  }

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
