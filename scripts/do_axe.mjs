/**
 * axe-core (Deque) trên 23 trang × 2 khổ — bộ luật NGOÀI, bổ cho `do_giao_dien.mjs`.
 *
 * Bộ đo nhà hỏi tương phản, cỡ chạm, tràn, che, chồng. axe hỏi thứ KHÁC: ARIA,
 * nhãn, MỐC TRANG (main/banner/nav), thứ tự tiêu đề, vùng cuộn có nhận bàn phím
 * không… Lượt đầu 20/09/2026: ~340 nút vi phạm (1 SERIOUS — vùng lý thuyết bài
 * học không nhận tiêu điểm bàn phím, WCAG 2.1.1; 10 trang không có `<main>`; 20
 * lượt trang không có h1; 9 trang nhảy cấp tiêu đề) → 0 sau khi sửa.
 *
 * axe nạp từ jsdelivr (CSP đã mở cho canvas-confetti), không thêm dependency.
 * Trang học viên đi thẻ học viên, trang khác thẻ quản trị — cùng lý do với bộ
 * đo nhà (nhân sự không thấy màn học viên). Bài học đi tới bước lý thuyết. Mọi
 * lời gọi ghi bị chặn. `/login` chờ `domcontentloaded`: trang ấy tự đánh thức
 * máy chủ theo chu kỳ nên không bao giờ `networkidle`.
 *
 * Chạy (cần Next 3100 + Django 9000 + hai thẻ):
 *   python scripts/cap_the.py && python scripts/cap_the.py --e2e --ra .the/tokens_hv.json
 *   node scripts/do_axe.mjs            # thoát 1 nếu còn vi phạm
 */
import { createRequire } from 'node:module';
import fs from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const DAY = dirname(fileURLToPath(import.meta.url));
const { chromium } = createRequire(join(DAY, '..', 'frontend', 'package.json'))('@playwright/test');
const doc = (t) => JSON.parse(fs.readFileSync(process.env[t] || join(DAY, '..', '.the', t === 'PE_TOKENS' ? 'tokens_ad.json' : 'tokens_hv.json'), 'utf8')).access;
const AD = doc('PE_TOKENS');
const HV = doc('PE_TOKENS_HV');
const GOC = process.env.PE_GOC || 'http://localhost:3100';
const TRANG = [
  ['/', 'Trang chủ', HV], ['/login', 'Đăng nhập', null],
  ['/dashboard', 'Dashboard', HV], ['/courses/hsa_quantitative', 'Chi tiết khoá', HV],
  ['/lesson/hsa_quantitative?lesson=1', 'Bài học', HV], ['/mock', 'Thi thử', HV],
  ['/bai-tap', 'Bài tập của tôi', HV], ['/questionaire', 'Khảo sát', HV], ['/doi-mat-khau', 'Đổi mật khẩu', HV],
  ['/quan-tri/tong-quan', 'QT tổng quan', AD], ['/quan-tri/tai-khoan', 'QT tài khoản', AD],
  ['/quan-tri/lop-hoc', 'QT lớp học', AD], ['/quan-tri/dot-hoc', 'QT đợt học', AD],
  ['/quan-tri/nhat-ky', 'QT nhật ký', AD], ['/quan-tri/co-so-hoc-phi', 'QT học phí', AD],
  ['/quan-tri/vai-tro', 'QT vai trò', AD], ['/quan-tri/huong-dan', 'QT hướng dẫn', AD],
  ['/admin', 'Soạn giáo trình', AD], ['/giang-day', 'GD việc hôm nay', AD],
  ['/giang-day/buoi-hoc/7322', 'GD buổi học', AD], ['/giang-day/bai-tap/7322', 'GD bài tập', AD],
  ['/giang-day/bao-cao/7322', 'GD báo cáo', AD], ['/giang-day/ket-qua-thi/7322', 'GD nhập PDF', AD],
];
const AXE = 'https://cdn.jsdelivr.net/npm/axe-core@4.10.3/axe.min.js';
const b = await chromium.launch();
const tong = new Map(); // rule → { impact, help, trang: Set, mau }
const theoTrang = [];
for (const w of [390, 1366]) {
  for (const [url, ten, the] of TRANG) {
    const ctx = await b.newContext({ viewport: { width: w, height: w === 390 ? 844 : 900 }, hasTouch: w === 390 });
    if (the) await ctx.addCookies([{ name: 'pe_at', value: the, domain: 'localhost', path: '/', httpOnly: true, sameSite: 'Lax' }]);
    await ctx.route('**/api/**', (r) => (['GET', 'HEAD'].includes(r.request().method()) ? r.continue() : r.fulfill({ status: 200, contentType: 'application/json', body: '{}' })));
    const p = await ctx.newPage();
    try {
      await p.goto(GOC + url, { waitUntil: url === '/login' ? 'domcontentloaded' : 'networkidle', timeout: 60000 });
      if (url.startsWith('/lesson/')) {
        try {
          await p.waitForSelector('.hsa-q', { timeout: 15000 });
          for (const q of await p.locator('.hsa-q').all()) { const o = q.locator('.hsa-opt'); if (await o.count()) await o.first().click(); else await q.locator('.hsa-fill').fill('1'); }
          await p.click('#nav-next'); await p.waitForSelector('.step-pane[data-step="2"].active', { timeout: 15000 });
          await p.click('#nav-next'); await p.waitForSelector('.step-pane[data-step="3"].active .hsa-cards', { timeout: 15000 });
        } catch { /* đo ở bước đang có */ }
      }
      await p.waitForTimeout(600);
      await p.addScriptTag({ url: AXE });
      const kq = await p.evaluate(async () => {
        // eslint-disable-next-line no-undef
        const r = await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'] } });
        return r.violations.map((v) => ({ id: v.id, impact: v.impact, help: v.help, tags: v.tags.filter((t) => /wcag|best/.test(t)),
          nodes: v.nodes.slice(0, 3).map((n) => ({ target: n.target.join(' '), html: n.html.slice(0, 120), msg: (n.failureSummary || '').split('\n')[1] || '' })), so: v.nodes.length }));
      });
      theoTrang.push({ kho: w, ten, so: kq.reduce((a, v) => a + v.so, 0), luat: kq.map((v) => `${v.id}×${v.so}`) });
      for (const v of kq) {
        const t = tong.get(v.id) || { impact: v.impact, help: v.help, tags: v.tags, trang: new Set(), mau: v.nodes, soNut: 0 };
        t.trang.add(`${ten}@${w}`); t.soNut += v.so; tong.set(v.id, t);
      }
    } catch (e) {
      theoTrang.push({ kho: w, ten, loi: String(e.message).slice(0, 80) });
    }
    await ctx.close();
  }
}
await b.close();
for (const r of theoTrang) console.log(`[${r.kho}] ${r.ten.padEnd(18)} ${r.loi ? 'LỖI ' + r.loi : String(r.so).padStart(3) + '  ' + r.luat.join(' ')}`);
console.log('\n══ THEO LUẬT (mọi trang, mọi khổ) ══');
for (const [id, t] of [...tong].sort((a, b) => ({ critical: 0, serious: 1, moderate: 2, minor: 3 }[a[1].impact] ?? 9) - ({ critical: 0, serious: 1, moderate: 2, minor: 3 }[b[1].impact] ?? 9))) {
  console.log(`\n${t.impact.toUpperCase().padEnd(9)} ${id} — ${t.help} [${t.tags.join(',')}]  · ${t.trang.size} lượt trang · ${t.soNut} nút`);
  for (const n of t.mau) console.log(`   ${n.target.slice(0, 70)} | ${n.html.slice(0, 90)} | ${n.msg.slice(0, 90)}`);
}
const i = process.argv.indexOf('--json');
if (i >= 0) fs.writeFileSync(process.argv[i + 1], JSON.stringify({ theoTrang, tong: [...tong].map(([id, t]) => ({ id, ...t, trang: [...t.trang] })) }, null, 1));
const tongNut = theoTrang.reduce((a, r) => a + (r.so || 0), 0);
const loiTai = theoTrang.filter((r) => r.loi).length;
console.log(`
TỔNG: ${tongNut} nút vi phạm / ${theoTrang.length} lượt · ${loiTai} lượt không tải được`);
process.exit(tongNut || loiTai ? 1 : 0);
