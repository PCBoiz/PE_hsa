/**
 * BẤM THỬ mọi nút của sản phẩm và thu lỗi JS.
 *
 *     node scripts/go_moi_nut.mjs            # bấm và in
 *     node scripts/go_moi_nut.mjs --tu-kiem  # nó có BẮT ĐƯỢC lỗi không
 *
 * ── VÌ SAO CẦN, DÙ ĐÃ CÓ do_giao_dien.mjs (05/09/2026) ──────────────────────
 *
 * `do_giao_dien.mjs` MỞ 16 trang và báo "lỗi JS: 0" trên tất cả. Con số ấy đúng
 * — và vô dụng cho một lớp lỗi: nó chỉ TẢI trang, không BẤM gì.
 *
 * Cùng ngày, `no-undef` tìm ra ô tìm kiếm diễn đàn ném
 * `ReferenceError: renderPosts is not defined` ở MỌI lần gõ. Trang tải sạch,
 * `lỗi JS: 0`, và tính năng thì hỏng hoàn toàn. Khoảng cách giữa "tải được" và
 * "dùng được" chính là chỗ này.
 *
 * ── CHỈ ĐỌC, CHẶN THEO PHƯƠNG THỨC ──────────────────────────────────────────
 *
 * Bấm nút thì sẽ đụng nút GHI. Nên mọi lời gọi không phải GET/HEAD bị chặn và
 * ĐẾM — cùng luật `do_giao_dien.mjs` dùng (RULES §22). Báo số lời gọi ghi lọt ra
 * ở cuối; khác 0 nghĩa là hàng rào thủng, không phải "chạy xong".
 *
 * Cũng KHÔNG bấm những nút mang chữ nguy hiểm (xoá, huỷ, đăng xuất…): chặn
 * mạng giữ CSDL an toàn, nhưng một nút `confirm()` rồi `location.href` vẫn kéo
 * lượt quét đi lạc và làm phần còn lại không được bấm.
 */
import { createRequire } from 'node:module';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const DAY = dirname(fileURLToPath(import.meta.url));
const _doi = createRequire(join(DAY, '..', 'frontend', 'package.json'));
let PW = null;
for (const ten of ['@playwright/test', 'playwright']) {
  try { PW = pathToFileURL(_doi.resolve(ten)).href; break; } catch { /* thử tên sau */ }
}
if (!PW) { console.error('Không tìm thấy Playwright. Cài ở frontend: pnpm install'); process.exit(1); }
const _pw = await import(PW);
const chromium = _pw.chromium || (_pw.default && _pw.default.chromium);

const GOC = process.env.PE_URL || 'http://localhost:3100';
const tu_kiem = process.argv.includes('--tu-kiem');

/** Tài khoản kiểm thử (`scripts/tai_khoan_e2e.py`). */
function taiKhoan() {
  if (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) {
    return { email: process.env.E2E_EMAIL, password: process.env.E2E_PASSWORD };
  }
  const p = join(DAY, '..', '.the', 'e2e.json');
  if (!existsSync(p)) return null;
  try { return JSON.parse(readFileSync(p, 'utf8')); } catch { return null; }
}

/* Nút KHÔNG bấm. Chặn mạng đã giữ CSDL an toàn; danh sách này giữ cho lượt quét
   không bị kéo ra khỏi trang đang xét. */
const TRANH = /đăng xuất|thoát|xoá|xóa|huỷ|hủy|gỡ|rời|khôi phục|tải lại|đổi mật khẩu/i;

/** Tab SPA của dashboard + các trang đứng riêng. */
const TRANG = [
  ['/dashboard', 'Dashboard (mọi tab SPA)', true],
  ['/courses/hsa_quantitative', 'Chi tiết khoá', false],
  ['/mock', 'Thi thử', false],
  ['/bai-tap', 'Bài tập của tôi', false],
  ['/quan-tri/tong-quan', 'Quản trị · tổng quan', false],
  ['/quan-tri/tai-khoan', 'Quản trị · tài khoản', false],
  ['/quan-tri/lop-hoc', 'Quản trị · lớp học', false],
  ['/admin', 'Soạn giáo trình', false],
  ['/giang-day/buoi-hoc/1', 'Giảng dạy · buổi học', false],
];

const tk = taiKhoan();
if (!tk) {
  console.error('Chưa có tài khoản kiểm thử. Tạo:  python scripts/tai_khoan_e2e.py --that');
  process.exit(1);
}

const b = await chromium.launch();
const c = await b.newContext({ viewport: { width: 1440, height: 900 } });
let ghiLen = 0;
await c.route('**/api/**', (r, req) => {
  const m = req.method();
  if (m === 'GET' || m === 'HEAD') return r.fallback();
  ghiLen += 1;
  return r.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
});

const p = await c.newPage();
const loi = [];
p.on('pageerror', (e) => loi.push(String(e.message || e).slice(0, 120)));

await p.goto(GOC + '/login', { waitUntil: 'domcontentloaded' });
await p.waitForSelector('#login-email', { timeout: 30000 });
await p.fill('#login-email', tk.email);
await p.fill('#login-password', tk.password);
await p.click('#loginBtn');
await p.waitForURL('**/dashboard**', { timeout: 30000 });

/* Cùng tập với `do_giao_dien.mjs` (hằng `CHAM`), trừ liên kết rời trang.
   Bản đầu chỉ lấy `button` và ra ĐÚNG 7 nút trên mọi tab dashboard — một trang
   có 260 vùng chạm. Phần lớn điều khiển ở đây là `<a>`, `<label>` hoặc
   `[role=button]`; đếm 7 rồi tin là đã quét xong thì tệ hơn không quét. */
const CHON = ['button', '[role="button"]', 'a[href^="#"]', 'a:not([href])',
  'label', '[tabindex]:not([tabindex="-1"])'].map((s) => `${s}:visible`).join(', ');

/** Trần mỗi màn — giữ một lượt quét trong khoảng chờ được. */
const TRAN_MOI_MAN = 45;

/**
 * Bấm mọi điều khiển NHÌN THẤY được trên màn hình hiện tại.
 *
 * TRUY VẤN LẠI sau mỗi lần bấm, thay vì giữ một mảng handle từ đầu. Bản đầu giữ
 * mảng: cú bấm đầu tiên đổi tab, toàn bộ handle còn lại thành ẩn, mọi lần bấm
 * sau đó hết giờ rồi bị `catch` nuốt — và lượt quét báo "7 nút" trên MỌI tab,
 * một con số đều đặn đến mức đáng ra phải làm tôi dừng lại sớm hơn.
 *
 * `veCho` đưa màn hình về đúng chỗ sau mỗi lần bấm; không có nó thì lượt quét
 * đo tab khác với tab nó đang ghi tên.
 */
async function bamHet(veCho, gaiLoi) {
  const truoc = loi.length;
  const daBam = new Set();
  let bam = 0;

  /* TỰ KIỂM: bấm THẲNG nút gài, không chờ nó tới lượt.
     Bản trước để nó xếp hàng theo thứ tự tài liệu — mà nút gài nằm CUỐI `body`,
     còn vòng lặp có trần 45 lượt. Ba màn nhiều nút (dashboard, roadmap) chạm
     trần trước khi tới nó, và phép tự kiểm báo "KHÔNG đỏ nổi" cho một lượt quét
     đang chạy tốt. Thứ cần chứng minh là "bấm ra lỗi thì THU được", không phải
     "tìm thấy nút ở vị trí thứ mấy". */
  if (gaiLoi) {
    await gaiLoi();
    await p.click('#nut-tu-kiem', { timeout: 1500, noWaitAfter: true }).catch(() => {});
    await p.waitForTimeout(150);
    daBam.add('nut-thu-nghiem|');
  }

  for (let vong = 0; vong < TRAN_MOI_MAN; vong++) {
    /* `p.$$` cũng ném `Execution context was destroyed` khi cú bấm trước đang
       kéo một điều hướng. Bản trước để nó thoát ra ngoài và GIẾT cả lượt quét
       giữa chừng — mất luôn phần chưa quét, vì một chuyện bình thường. */
    let nut = [];
    try { nut = await p.$$(CHON); }
    catch {
      await p.waitForLoadState('domcontentloaded').catch(() => {});
      await veCho();
      try { nut = await p.$$(CHON); } catch { break; }
    }
    let tiep = null;
    for (const el of nut) {
      let chu = '';
      try { chu = ((await el.innerText()) || (await el.getAttribute('aria-label')) || '').trim(); }
      catch { continue; }
      const khoa = chu + '|' + (await el.evaluate((e) => e.className || '').catch(() => ''));
      if (daBam.has(khoa) || TRANH.test(chu)) continue;
      daBam.add(khoa);
      tiep = el;
      break;
    }
    if (!tiep) break;            // hết nút chưa bấm
    try {
      await tiep.click({ timeout: 1200, noWaitAfter: true });
      bam += 1;
      await p.waitForTimeout(120);
      await p.keyboard.press('Escape').catch(() => {});
    } catch { /* bị che hoặc rời DOM giữa chừng — không phải lỗi sản phẩm */ }
    await veCho();
    // `veCho` có thể đã TẢI LẠI trang, cuốn theo nút tự kiểm. Gài lại, nếu
    // không phép tự kiểm báo "không đỏ nổi" cho một lượt quét đang chạy tốt.
    if (gaiLoi) await gaiLoi();
  }

  // Ô nhập: gõ vào. Đây chính là chỗ lỗi tìm-kiếm-diễn-đàn nằm.
  for (const o of await p.$$('input[type="text"]:visible, input[type="search"]:visible')) {
    try { await o.fill('zzz', { timeout: 900 }); await p.waitForTimeout(240); await o.fill(''); }
    catch { /* ô chỉ đọc hoặc bị che */ }
  }
  return { bam, moi: loi.slice(truoc) };
}

console.log('BẤM THỬ — mọi lời gọi không phải GET đều bị chặn\n');
let tongBam = 0;
const manCam = [];   // màn KHÔNG đỏ nổi dù đã bị gài lỗi
for (const [duong, ten, laSpa] of TRANG) {
  await p.goto(GOC + duong, { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(2200);
  if (/(dang-nhap|login)/.test(new URL(p.url()).pathname)) {
    console.log(`  ${ten.padEnd(26)} BỊ ĐẨY VỀ ĐĂNG NHẬP — bỏ qua`);
    continue;
  }

  const tabs = laSpa
    ? await p.evaluate(() => [...document.querySelectorAll('.page[id^="page-"]')]
      .map((e) => e.id.replace(/^page-/, '')))
    : [null];

  for (const tab of tabs) {
    if (tab) {
      await p.evaluate((t) => window.navigate && window.navigate(t), tab);
      await p.waitForTimeout(1400);
    }
    /* TỰ KIỂM gài lại SAU MỖI lần đổi tab, và xét TỪNG MÀN.
       Bản đầu gài một lần cho cả trang rồi lấy TỔNG làm tiêu chí: nó "ĐẠT" nhờ
       7 màn, trong khi 9 màn còn lại không bắt được lần nào — đúng cái bẫy
       "xanh gộp che số 0 từng mục" vừa phải vá ở `do_giao_dien.mjs`. */
    const gaiLoi = async () => {
      try {
        await p.evaluate(() => {
          if (document.getElementById('nut-tu-kiem')) return;
          const t = document.createElement('button');
          t.id = 'nut-tu-kiem';
          t.textContent = 'nut-thu-nghiem';
          t.onclick = () => { throw new Error('LOI-TU-KIEM'); };
          /* GHIM CỐ ĐỊNH trong khung nhìn. Bản trước chỉ `appendChild` vào cuối
             `body`: trên ba màn có bố cục chiều cao cố định, nút rơi ra ngoài
             khung, thành không-`:visible`, không bao giờ được bấm — và phép tự
             kiểm báo "KHÔNG đỏ nổi" cho một lượt quét đang chạy tốt. Một phép
             tự kiểm báo oan cũng làm người ta thôi tin nó, y như báo sót. */
          t.style.cssText = 'position:fixed;top:0;left:0;z-index:2147483647;'
            + 'width:120px;height:28px;opacity:.01';
          document.body.appendChild(t);
        });
      } catch { /* đang điều hướng — vòng sau gài lại */ }
    };
    if (tu_kiem) await gaiLoi();

    /* Đưa màn hình VỀ ĐÚNG CHỖ sau mỗi cú bấm: lạc trang thì tải lại, còn
       trong SPA thì gọi lại `navigate(tab)`. Thiếu bước này, lượt quét đo một
       tab khác với tab nó đang ghi tên. */
    const veCho = async () => {
      /* Mọi `evaluate` ở đây phải bọc: cú bấm vừa rồi có thể đang kéo một
         điều hướng, và `Execution context was destroyed` sẽ giết cả lượt quét
         vì một chuyện hoàn toàn bình thường. */
      try {
        if (!p.url().includes(duong)) {
          await p.goto(GOC + duong, { waitUntil: 'domcontentloaded' });
          await p.waitForTimeout(900);
        }
        if (!tab) return;
        const dung = await p.evaluate((t) =>
          document.querySelector('.page.active')?.id === 'page-' + t, tab);
        if (!dung) {
          await p.evaluate((t) => window.navigate && window.navigate(t), tab);
          await p.waitForTimeout(500);
        }
      } catch {
        // Đang điều hướng — chờ nó xong rồi thử lại đúng một lần.
        await p.waitForLoadState('domcontentloaded').catch(() => {});
        await p.waitForTimeout(600);
        try {
          if (!p.url().includes(duong)) {
            await p.goto(GOC + duong, { waitUntil: 'domcontentloaded' });
            await p.waitForTimeout(900);
          }
          if (tab) {
            await p.evaluate((t) => window.navigate && window.navigate(t), tab);
            await p.waitForTimeout(500);
          }
        } catch { /* chịu — vòng sau `p.$$` sẽ tự đọc lại trạng thái thật */ }
      }
    };

    const r = await bamHet(veCho, tu_kiem ? gaiLoi : null);
    tongBam += r.bam;
    const nhan = tab ? `${ten} → ${tab}` : ten;
    const gai = r.moi.filter((x) => /LOI-TU-KIEM/.test(x)).length;
    const that_ = r.moi.filter((x) => !/LOI-TU-KIEM/.test(x));
    if (tu_kiem && !gai) manCam.push(nhan);
    console.log(`  ${nhan.padEnd(34)} bấm ${String(r.bam).padStart(3)} nút`
      + (tu_kiem ? (gai ? '  ✓ đỏ được' : '  ✗ KHÔNG đỏ nổi') : '')
      + (that_.length ? `  ✗ ${that_.length} LỖI` : (tu_kiem ? '' : '  ✓')));
    for (const x of [...new Set(that_)]) console.log(`        ${x}`);
  }
}

console.log(`\nTỔNG: bấm ${tongBam} nút · ${loi.length} lỗi JS · ${ghiLen} lời gọi GHI bị chặn`);
const that = loi.filter((x) => !/LOI-TU-KIEM/.test(x));
if (tu_kiem) {
  console.log('\n── TỰ KIỂM ──');
  if (manCam.length) {
    console.log(`  HỎNG: ${manCam.length} màn KHÔNG đỏ nổi dù đã gài lỗi vào —`
      + ' con số "0 lỗi" của chúng không chứng minh điều gì:');
    for (const m of manCam) console.log(`      ${m}`);
    await b.close();
    process.exit(1);
  }
  console.log('  ĐẠT: mọi màn đều bắt được lỗi tự gài.');
  await b.close();
  process.exit(0);
}
await b.close();
process.exit(that.length ? 1 : 0);
