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
 *
 * ── SỐ ĐO 14/09/2026 (sau khi tệp này biết làm nóng + lấy trung vị) ───────
 *
 *     Trang của tôi        2464ms    0.007      432   2114   (2408/2464/2596)
 *     Thi thử              1580ms    0.002      271    280
 *     Vận hành             1880ms    0.006      222    260
 *     Báo cáo phụ huynh     992ms        0      222    213
 *     Ai làm được gì        992ms        0      222    976
 *     Hướng dẫn            1056ms        0      222    390
 *
 * "Trang của tôi" nay ỔN ĐỊNH quanh 2,4–2,6 s thay vì nhảy 0,6–4,7 s, và con
 * số ấy TRUNG THỰC hơn mọi số cũ: trước 14/09, những lượt "nhanh" chỉ nhanh vì
 * thẻ "Học tiếp" (phần tử LCP thật) chưa kịp vẽ trước lúc đọc.
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
 * CỘT `DOM` — ĐÃ TỰ ĐÚNG LẠI (14/09/2026). Cột này đọc `querySelectorAll('*')`
 * sau `networkidle` + 1200ms, và ghi chú 07/09 ở đây nói đúng rằng nó báo 1030
 * nút trong khi trang thật đứng lại ở 1922: lúc chụp, trang CHƯA dựng xong.
 * Từ khi `NapTruocDuLieu` bắn sẵn ba lượt GET (14/09), nội dung kịp về trước
 * mốc chụp và cột báo 2114 — con số thật, và nó VƯỢT ngưỡng 1500. Tức cảnh báo
 * "2114 nút DOM" hiện ra bây giờ KHÔNG phải hồi quy: nó là thứ ngưỡng ấy lẽ ra
 * phải nói từ 07/09. Nguồn: trang này dựng sẵn CẢ CHÍN "trang" của SPA cũ
 * (dashboard, khoá học, lộ trình, kỹ năng, diễn đàn, cài đặt, hồ sơ…) trong
 * một lượt, tám trong số đó `display:none`. Dựng lười từng trang là việc lớn
 * của tầng cũ — ghi ở TODO, không vá chen ngang.
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

// "JS(kB)" = byte GIẢI NÉN của mọi tệp JS trong lượt dựng trang (xem chú thích
// ở chỗ đếm) — lớn hơn số truyền qua mạng vì máy chủ nén gzip/brotli.
console.log('màn hình'.padEnd(20), 'LCP'.padStart(8), 'CLS'.padStart(7),
            'chặn'.padStart(7), 'JS(kB)'.padStart(8), 'req'.padStart(5), 'DOM'.padStart(6),
            '  JS = giải nén');
console.log('─'.repeat(66));
/* LÀM NÓNG trước khi đo (14/09/2026). `chromium.launch()` là một trình duyệt
   LẠNH HOÀN TOÀN — tiến trình GPU, bộ đệm phông, JIT đều chưa có gì — và màn
   ĐẦU TIÊN trong danh sách gánh trọn cái giá ấy: đo 5 lượt liền, "Trang của
   tôi" cho FCP 1,8 s ở lượt đầu và 0,4 s ở các lượt sau, CÙNG một bản dựng.
   Người dùng thật không mở trang trong trình duyệt vừa khởi động — Chrome của
   họ đã chạy sẵn. Nên mở một trang không cần thẻ trước để trình duyệt ấm lên,
   rồi mới đo. Không có bước này thì màn xếp đầu bảng LUÔN xấu nhất, và tôi đã
   đi tối ưu theo con số ấy suốt hai vòng. */
{
  const nong = await ctx.newPage();
  await nong.goto('http://localhost:3100/login', { waitUntil: 'networkidle' });
  await nong.close();
}

/* MỖI MÀN ĐO 3 LƯỢT, LẤY TRUNG VỊ. Một lượt là một mẫu; bảng 07/09 phải ghi
   tay "2740 / 2824 / 2972" vì tệp này chỉ chạy một lượt. Trung vị chứ không
   trung bình: một lượt trượt vì rác thu gom hay ổ đĩa thì không kéo cả số. */
const SO_LUOT = 3;
const ra = [];
for (const [ten, url] of MAN) {
  const cacLuot = [];
  for (let luot = 0; luot < SO_LUOT; luot += 1) {
  const p = await ctx.newPage();
  const cdp = await p.context().newCDPSession(p);
  await cdp.send('Network.enable');
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });   // máy yếu
  /* TẮT BỘ ĐỆM cho từng lượt đo. Ba lượt dùng CHUNG một `context`, nên lượt 2
     và 3 sẽ đọc JS/CSS/phông từ bộ đệm — cột `JS(kB)` tụt từ 432 xuống 222 và
     LCP đẹp lên, nhưng đó là số của LẦN GHÉ THỨ HAI, không phải của người mở
     lần đầu. Ấm trình duyệt thì được (người dùng thật có Chrome đang chạy);
     ấm bộ đệm của chính trang thì không. */
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });

  /* ĐỌC THÂN PHẢN HỒI PHẢI ĐƯỢC CHỜ XONG (14/09/2026, tối).
     Bản cũ `try { byteJs += (await r.body()).length } catch {}` (nuốt lỗi)
     rồi đóng trang ngay sau khi đo — lượt đọc nào chưa xong lúc ấy ném lỗi và
     bị BỎ QUA IM LẶNG — và KHÔNG chỉ khi máy nặng. Mổ xẻ từng tệp 14/09 tối:
     `/quan-tri/huong-dan` thật tải 9 tệp = 529 kB giải nén, trong đó khối khung
     React một mình 222 kB — đúng bằng con số "222 kB" thước cũ báo đều đặn nhiều
     ngày. Tức thước cũ chỉ kịp đếm khoảng MỘT tệp mỗi trang; cột JS(kB) đã báo
     thấp từ lâu, theo hướng đẹp hơn thật, mà ổn định nên không ai ngờ. Nay giữ
     mọi lời hứa, chờ hết trước khi đóng trang, ĐẾM lượt đọc hỏng để in ra.

     Đơn vị: byte GIẢI NÉN (`r.body()`), không phải byte truyền qua mạng. Mọi
     số JS(kB) ghi trong PROGRESS trước 14/09 tối đo bằng thước cũ — chỉ dùng để
     so tương đối trong cùng một lượt, không dùng làm độ lớn. */
  let byteJs = 0, soReq = 0, docHong = 0;
  const choDoc = [];
  p.on('response', (r) => {
    soReq += 1;
    const ct = r.headers()['content-type'] || '';
    if (/javascript/.test(ct)) {
      choDoc.push(r.body().then((b) => { byteJs += b.length; }, () => { docHong += 1; }));
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
    break;
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

  await Promise.allSettled(choDoc);
  if (docHong > 0) {
    console.log(`  ⚠ ${ten} lượt ${luot + 1}: ${docHong} tệp JS không đọc được thân — cột JS(kB) THIẾU, đừng tin số này`);
  }
  cacLuot.push({ ...d, js: Math.round(byteJs / 1024), req: soReq, docHong });
  await p.close();
  }
  if (!cacLuot.length) continue;
  // Trung vị theo LCP; các cột khác lấy của đúng lượt ấy để bảng là MỘT lượt thật.
  cacLuot.sort((a, b) => a.lcp - b.lcp);
  const d = cacLuot[Math.floor(cacLuot.length / 2)];
  ra.push({ ten, url, ...d, cacLcp: cacLuot.map((x) => x.lcp) });
  console.log(ten.padEnd(20), (d.lcp + 'ms').padStart(8), String(d.cls).padStart(7),
              (d.chan + 'ms').padStart(7), String(d.js).padStart(8),
              String(d.req).padStart(5), String(d.dom).padStart(6),
              '  (' + cacLuot.map((x) => x.lcp).join(' / ') + ')');
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
