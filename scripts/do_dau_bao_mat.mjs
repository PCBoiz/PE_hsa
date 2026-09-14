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
 *              Font Awesome từ cdnjs, `new Function` của đồ thị bài học.
 *   CHẶN     — thứ kẻ tấn công cần thì bị chặn: nhúng trang vào iframe miền lạ,
 *              fetch/ảnh gửi dữ liệu ra máy chủ lạ, `<base>` giả.
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
  dat(!coNoiDung, 'iframe từ miền lạ không hiển thị được trang (chống clickjacking)',
    coNoiDung ? 'trang VẪN dựng trong iframe' : (ds[0] || '').slice(0, 90));
  await p.close();
}
{
  const p = await c.newPage();
  const ds = loiCsp(p);
  await p.goto(GOC + '/login', { waitUntil: 'domcontentloaded' });
  const fetchRa = await p.evaluate(async () => {
    try { await fetch('https://example.com/ro-ri?d=1', { mode: 'no-cors' }); return 'đi được'; } catch { return 'bị chặn'; }
  });
  dat(fetchRa === 'bị chặn', 'fetch tới máy chủ lạ bị chặn (connect-src)', fetchRa);
  const truoc = ds.length;
  await p.evaluate(() => { const i = new Image(); i.src = 'https://example.com/ro-ri.png?d=1'; document.body.appendChild(i); });
  await p.waitForTimeout(1200);
  dat(ds.length > truoc, 'ảnh gửi ra máy chủ lạ bị chặn (img-src)', (ds[ds.length - 1] || 'không có dòng CSP nào').slice(0, 90));
  const truoc2 = ds.length;
  await p.evaluate(() => { const o = document.createElement('object'); o.data = '/favicon.ico'; document.body.appendChild(o); });
  await p.waitForTimeout(800);
  dat(ds.length > truoc2, '<object> bị chặn (object-src none)');
  await p.close();
}

/* ── 3. Trình duyệt: CHO PHÉP thứ sản phẩm dùng ── */
console.log('\n[3] CHO PHÉP');
{
  const p = await c.newPage();
  const ds = loiCsp(p);
  await p.goto(GOC + '/login', { waitUntil: 'domcontentloaded' });
  const kq = await p.evaluate(async () => {
    const eval_ = (() => { try { return new Function('x', 'return x * 2')(21) === 42; } catch { return false; } })();
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
    return { eval_, confetti, fa };
  });
  await p.waitForTimeout(1500);
  dat(kq.eval_, "new Function chạy được (đồ thị bài học cần 'unsafe-eval')");
  dat(kq.confetti, 'script confetti từ cdn.jsdelivr.net nạp được');
  dat(kq.fa, 'Font Awesome từ cdnjs.cloudflare.com nạp được');
  dat(ds.length === 0, 'trang đăng nhập + ba thao tác trên: 0 dòng CSP', (ds[0] || '').slice(0, 120));
  await p.close();
}

/* ── 4. Có thẻ: đi các trang cần đăng nhập, đếm dòng CSP ── */
if (TOKEN && existsSync(TOKEN)) {
  console.log('\n[4] Trang cần đăng nhập');
  const tok = JSON.parse(readFileSync(TOKEN, 'utf8'));
  const host = new URL(GOC).hostname;
  await c.addCookies([{ name: 'pe_at', value: tok.access, domain: host, path: '/', httpOnly: true, sameSite: 'Lax', secure: GOC.startsWith('https') }]);
  for (const duong of ['/dashboard', '/courses/hsa_quantitative', '/lesson/hsa_quantitative?lesson=1', '/mock', '/quan-tri/tong-quan', '/admin', '/giang-day/buoi-hoc/1']) {
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
