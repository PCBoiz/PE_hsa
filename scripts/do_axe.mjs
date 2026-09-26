/**
 * axe-core (Deque) trên 23 trang × 2 khổ — bộ luật NGOÀI, bổ cho `do_giao_dien.mjs`.
 * + (22/09/2026) 7 view SPA × {sáng, tối} và 4 trạng thái MỞ × {sáng, tối} — xem `LUOT_THEM`.
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
 *   node scripts/do_axe.mjs            # thoát 1 nếu còn vi phạm HOẶC có lượt không đo được
 *   node scripts/do_axe.mjs --chi-them # chỉ các lượt view/tối/trạng thái mở (nhanh hơn)
 */
import { createRequire } from 'node:module';
import fs from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const DAY = dirname(fileURLToPath(import.meta.url));
const { chromium } = createRequire(join(DAY, '..', 'frontend', 'package.json'))('@playwright/test');
import { baoHiem } from './lib/phien_do.mjs';
const doc = (t) => JSON.parse(fs.readFileSync(process.env[t] || join(DAY, '..', '.the', t === 'PE_TOKENS' ? 'tokens_ad.json' : 'tokens_hv.json'), 'utf8')).access;
const AD = doc('PE_TOKENS');
const HV = doc('PE_TOKENS_HV');
const GOC = process.env.PE_GOC || 'http://localhost:3100';
const TRANG = [
  // `/` bỏ 24/09/2026: chỉ còn chuyển hướng (trang quảng cáo đã gỡ).
  ['/login', 'Đăng nhập', null],
  // Quên mật khẩu (§52, 23/09/2026): hai trang KHÔNG cần đăng nhập. Trang đặt lại mở
  // không kèm chìa → đúng trạng thái 'đường dẫn hỏng' mà người bấm thư cũ sẽ thấy.
  ['/quen-mat-khau', 'Quên mật khẩu', null], ['/dat-lai-mat-khau', 'Đặt lại (đường dẫn hỏng)', null],
  ['/dashboard', 'Dashboard', HV], ['/courses/hsa_quantitative', 'Chi tiết khoá', HV],
  // `/mock` (Thi thử) và `/giang-day/ket-qua-thi/…` (nhập PDF) ra khỏi danh sách
  // 24/09/2026 — bỏ thi, pha A: hai đường nay chỉ chuyển hướng (next.config.ts).
  ['/lesson/hsa_quantitative?lesson=1', 'Bài học', HV],
  ['/bai-tap', 'Bài tập của tôi', HV], ['/questionaire', 'Khảo sát', HV], ['/doi-mat-khau', 'Đổi mật khẩu', HV],
  ['/quan-tri/tong-quan', 'QT tổng quan', AD], ['/quan-tri/tai-khoan', 'QT tài khoản', AD],
  ['/quan-tri/lop-hoc', 'QT lớp học', AD], ['/quan-tri/dot-hoc', 'QT đợt học', AD],
  ['/quan-tri/nhat-ky', 'QT nhật ký', AD], ['/quan-tri/co-so-hoc-phi', 'QT học phí', AD],
  ['/quan-tri/vai-tro', 'QT vai trò', AD], ['/quan-tri/huong-dan', 'QT hướng dẫn', AD],
  ['/giao-trinh', 'Giáo trình', AD], ['/giang-day', 'GD việc hôm nay', AD],
  ['/giang-day/buoi-hoc/7322', 'GD buổi học', AD], ['/giang-day/bai-tap/7322', 'GD bài tập', AD],
  ['/giang-day/bao-cao/7322', 'GD báo cáo', AD],
  // Hai màn thêm 23/09/2026 (hồ sơ học viên §51): form hồ sơ đầy đủ, và tờ báo cáo
  // một em — nay có ô mục tiêu/nguyện vọng của giảng viên. 35695 là em mẫu của lớp 7322.
  ['/quan-tri/tai-khoan/35695', 'QT hồ sơ học viên', AD], ['/giang-day/bao-cao/7322/35695', 'GD tờ một em', AD],
  // Thêm 24/09/2026 (§53): lịch gộp theo tuần.
  ['/giang-day/lich', 'GD lịch học', AD],
  // Gộp A2 + E1 (26/09/2026): chấm công theo tháng, soạn khung, chương trình một lớp, sổ đầu
  // bài một buổi. 8004 là buổi đã dạy của lớp 7322 trên Neon dev.
  ['/quan-tri/cham-cong', 'QT chấm công', AD], ['/giao-trinh/khung-chuong-trinh', 'Khung chương trình', AD],
  ['/giang-day/chuong-trinh/7322', 'GD chương trình lớp', AD], ['/giang-day/so-dau-bai/8004', 'GD sổ đầu bài', AD],
  // Hộp Yêu cầu (E3, 26/09/2026): học viên (gửi + một yêu cầu của mình) và nhân sự (hộp + một lượt
  // xin chuyển lớp chưa duyệt). 176 / 177 = yêu cầu của tài khoản e2e ở lớp mẫu 7322 (Neon dev).
  ['/yeu-cau', 'Hỏi & yêu cầu', HV], ['/yeu-cau/176', 'Một yêu cầu (HV)', HV],
  ['/yeu-cau', 'Hộp yêu cầu (nhân sự)', AD], ['/yeu-cau/177', 'Xin chuyển lớp (nhân sự)', AD],
  // Màn soạn thông báo (§61, E2-GD 26/09/2026): biểu mẫu có ô tick nhóm (`fieldset`/`legend`)
  // và nút khoá tới khi React gắn — hai thứ axe hay bắt nhất ở một màn nhập liệu mới.
  ['/giang-day/thong-bao/7322', 'GD soạn thông báo lớp', AD], ['/quan-tri/thong-bao', 'QT thông báo trung tâm', AD],
  // Tờ phụ huynh — nay có khối gửi yêu cầu. Cần chìa lớp mẫu (`scripts/cap_chia_mau.py`); thiếu tệp
  // thì bỏ trang này (xem sau mảng) — cùng quy ước với `do_giao_dien.mjs`.
].map(([url, ten, the]) => ({ url, ten, the, cheDo: 'light' }));

/* ── LƯỢT THÊM (22/09/2026, agent thuoc-4, theo phát hiện F1 của agent tiếp cận) ──
   Tới hôm nay cổng này chỉ đi view MẶC ĐỊNH của /dashboard, bản SÁNG, mọi menu
   ĐÓNG — và báo 0. Nhưng sáu view SPA (Khoá học, Lộ trình, Kỹ năng, Diễn đàn,
   Cài đặt, Hồ sơ) là sáu màn học viên mở hằng ngày; chế độ tối là một bảng màu
   khác hẳn; và menu "Học", chuông, menu tài khoản, ngăn chi tiết Lộ trình chỉ
   có trong cây DOM đọc được khi MỞ (lúc đóng chúng `visibility: hidden`, axe bỏ
   qua). Agent tiếp cận chạy tay `v37_axe_views.mjs` (5 view × sáng/tối) và
   thấy lỗi thật mà cổng này không bao giờ thấy.

   Mỗi lượt đều KIỂM đã tới đúng trạng thái trước khi chạy axe: view phải
   `#page-<v>.active`, chủ đề phải khớp `body.dark`, trạng thái mở phải thấy bộ
   chọn của nó. Không khớp → lượt ấy "không đo được" và cổng thoát 1 — không
   bao giờ chạy axe trên trạng thái sai rồi in 0 dưới tên trạng thái kia. */
{
  const TEP_CHIA = join(DAY, '..', '.the', 'chia_mau.json');
  if (fs.existsSync(TEP_CHIA)) {
    TRANG.push({ url: `/bc/${JSON.parse(fs.readFileSync(TEP_CHIA, 'utf8')).token}`, ten: 'Phụ huynh · tờ báo cáo', the: null, cheDo: 'light' });
  } else {
    console.log('⚠ Không có .the/chia_mau.json → BỎ QUA trang phụ huynh /bc/<chìa> (cấp: scripts/cap_chia_mau.py).');
  }
}
const VIEW = ['courses', 'plan', 'roadmap', 'skills', 'forum', 'settings', 'profile'];
const MO = [
  // [tên, view chứa nó, bộ chọn để bấm, bộ chọn chứng minh đã mở]
  ['menu "Học" mở', 'dashboard', '.nav-nhom-nut', '.nav-nhom.mo'],
  ['chuông mở', 'dashboard', '#bell-btn', '#bell-panel.open'],
  ['menu tài khoản mở', 'dashboard', '#user-chip-btn', '#user-dropdown.open'],
  /* `#rm-drawer`, KHÔNG phải `#sidebar-detail`: bộ chọn cũ chưa bao giờ có mặt
     trong `roadmap.js`, nên 4 lượt (2 khổ × 2 chế độ) luôn hết giờ. Cổng báo
     "KHÔNG ĐO ĐƯỢC" và thoát 1 thay vì in 0 dưới tên một trạng thái nó không
     hề tới được — đúng như thiết kế; chỗ hỏng là cái thước. (22/09/2026) */
  ['ngăn chi tiết Lộ trình', 'roadmap', '[data-rm-node]', '#rm-drawer.open'],
];
const LUOT_THEM = [];
for (const cheDo of ['light', 'dark']) {
  if (cheDo === 'dark') LUOT_THEM.push({ url: '/dashboard', ten: 'Dashboard', the: HV, cheDo, view: 'dashboard' });
  for (const v of VIEW) LUOT_THEM.push({ url: '/' + v, ten: 'View ' + v, the: HV, cheDo, view: v });
  for (const [ten, v, bam, cho] of MO) {
    LUOT_THEM.push({ url: v === 'dashboard' ? '/dashboard' : '/' + v, ten, the: HV, cheDo, view: v, bam, cho });
  }
}
const chiThem = process.argv.includes('--chi-them');
/* `--chi <chuỗi>` — chỉ chạy những lượt có TÊN chứa chuỗi ấy (không phân biệt hoa thường).
   Thêm 26/09/2026: một lượt đầy đủ là ~60 lần tải trang và vượt 10 phút trên máy dev, nên
   sau khi thêm MỘT màn mới người ta hoặc chạy cả bộ (rồi Ctrl-C giữa chừng — một trong bốn
   đường mà `finally` KHÔNG chạy, xem `lib/phien_do.mjs`), hoặc không đo gì cả. Cờ này để
   đo đúng màn vừa dựng. Nó KHÔNG thay lượt đầy đủ: cổng RULES §4 vẫn chạy không cờ. */
const chi = process.argv.includes('--chi')
  ? String(process.argv[process.argv.indexOf('--chi') + 1] || '').toLowerCase()
  : null;
const LUOT = (chiThem ? LUOT_THEM : [...TRANG, ...LUOT_THEM])
  .filter((l) => !chi || l.ten.toLowerCase().includes(chi));
if (chi && LUOT.length === 0) {
  // Lọc không khớp gì mà vẫn in "0 vi phạm" là cách chắc chắn nhất để tin rằng đã đo.
  console.error(`--chi "${chi}" không khớp lượt nào. Xem tên lượt trong mảng TRANG / LUOT_THEM.`);
  process.exit(2);
}

const AXE = 'https://cdn.jsdelivr.net/npm/axe-core@4.10.3/axe.min.js';
const b = await chromium.launch();
baoHiem(b);   // đóng trình duyệt cả khi Ctrl-C / lỗi không ai bắt
const tong = new Map(); // rule → { impact, help, trang: Set, mau }
const theoTrang = [];
for (const w of [390, 1366]) {
  for (const l of LUOT) {
    const { url, the, cheDo } = l;
    const ten = l.cheDo === 'dark' ? `${l.ten} (tối)` : l.ten;
    const ctx = await b.newContext({ viewport: { width: w, height: w === 390 ? 844 : 900 }, hasTouch: w === 390 });
    if (the) await ctx.addCookies([{ name: 'pe_at', value: the, domain: 'localhost', path: '/', httpOnly: true, sameSite: 'Lax' }]);
    // Chủ đề đọc từ `localStorage.theme` lúc nạp — đặt TRƯỚC khi trang chạy.
    await ctx.addInitScript((m) => { try { localStorage.setItem('theme', m); } catch { /* riêng tư */ } }, cheDo);
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
      if (l.view) {
        const daMo = () => p.evaluate((v) => !!document.querySelector(`#page-${v}.active`), l.view);
        if (!(await daMo())) {
          await p.evaluate((v) => { if (typeof window.navigate === 'function') window.navigate(v); }, l.view);
          await p.waitForTimeout(1500);
        }
        if (!(await daMo())) throw new Error(`view "${l.view}" KHÔNG mở`);
        await p.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});
      }
      const toi = await p.evaluate(() => document.body.classList.contains('dark'));
      if (toi !== (cheDo === 'dark')) throw new Error(`chủ đề: xin ${cheDo} nhưng body.dark=${toi}`);
      if (l.bam) {
        /* KHÔNG CÓ nút để mở ở khổ này (ví dụ một điều khiển chỉ có ở máy tính)
           thì đó không phải lỗi — ghi "bỏ qua" và nói rõ, chứ không nhuộm đỏ cổng
           bằng một trạng thái vốn không tồn tại ở đây. Có nút mà không mở được
           mới là lỗi. */
        if (!(await p.locator(l.bam).count())) {
          theoTrang.push({ kho: w, ten, bo_qua: `không có ${l.bam} ở khổ này` });
          console.log(`[${w}] ${ten.padEnd(30)} BỎ QUA: không có ${l.bam} ở khổ này`);
          await ctx.close();
          continue;
        }
        const nut = p.locator(l.bam).filter({ visible: true }).first();
        await nut.waitFor({ state: 'visible', timeout: 10000 });
        await nut.click();
        await p.waitForSelector(l.cho, { timeout: 8000 });
      }
      /* Chờ hết chuyển tiếp (panel mở trượt/mờ dần ~.2s): đọc giữa chừng là
         đọc màu pha dở — bẫy agent hồi quy mắc ngày 21/09. */
      await p.waitForTimeout(700);
      await p.addScriptTag({ url: AXE });
      const kq = await p.evaluate(async () => {
        // eslint-disable-next-line no-undef
        const r = await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'] } });
        return r.violations.map((v) => ({ id: v.id, impact: v.impact, help: v.help, tags: v.tags.filter((t) => /wcag|best/.test(t)),
          nodes: v.nodes.slice(0, 3).map((n) => ({ target: n.target.join(' '), html: n.html.slice(0, 120), msg: (n.failureSummary || '').split('\n')[1] || '' })), so: v.nodes.length }));
      });
      theoTrang.push({ kho: w, ten, so: kq.reduce((a, v) => a + v.so, 0), luat: kq.map((v) => `${v.id}×${v.so}`), mau: kq.map((v) => ({ id: v.id, nodes: v.nodes })) });
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
for (const r of theoTrang) {
  console.log(`[${r.kho}] ${r.ten.padEnd(30)} `
    + (r.loi ? 'KHÔNG ĐO ĐƯỢC: ' + r.loi
      : r.bo_qua ? 'BỎ QUA: ' + r.bo_qua
        : String(r.so).padStart(3) + '  ' + r.luat.join(' ')));
}
console.log('\n══ THEO LUẬT (mọi trang, mọi khổ) ══');
for (const [id, t] of [...tong].sort((a, b) => ({ critical: 0, serious: 1, moderate: 2, minor: 3 }[a[1].impact] ?? 9) - ({ critical: 0, serious: 1, moderate: 2, minor: 3 }[b[1].impact] ?? 9))) {
  console.log(`\n${t.impact.toUpperCase().padEnd(9)} ${id} — ${t.help} [${t.tags.join(',')}]  · ${t.trang.size} lượt trang · ${t.soNut} nút`);
  console.log(`   ở: ${[...t.trang].join(', ').slice(0, 300)}`);
  for (const n of t.mau) console.log(`   ${n.target.slice(0, 70)} | ${n.html.slice(0, 90)} | ${n.msg.slice(0, 90)}`);
}
const i = process.argv.indexOf('--json');
if (i >= 0) fs.writeFileSync(process.argv[i + 1], JSON.stringify({ theoTrang, tong: [...tong].map(([id, t]) => ({ id, ...t, trang: [...t.trang] })) }, null, 1));
const tongNut = theoTrang.reduce((a, r) => a + (r.so || 0), 0);
const loiTai = theoTrang.filter((r) => r.loi).length;
console.log(`
TỔNG: ${tongNut} nút vi phạm / ${theoTrang.length} lượt · ${loiTai} lượt không đo được`);
process.exit(tongNut || loiTai ? 1 : 0);
