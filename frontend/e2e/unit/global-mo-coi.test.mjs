/**
 * MỌI TRANG — không script nào được đọc một global không ai ghi.
 *
 * ── LỚP LỖI NÀY VỪA LÀM MẤT BA TUẦN (05/09/2026) ──────────────────────────
 *
 * `chatbot.js` đọc `window.LESSON_CONTENT_HSA`; tệp đặt ra biến ấy bị bỏ khỏi
 * danh sách script ngày 19/08/2026. Hàm rơi vào nhánh `typeof … undefined` và
 * trả `null` cho mọi lần gọi — trợ lý mất khả năng biết học viên đang ở bài
 * nào, suốt ba tuần, không một lỗi nào hiện ra.
 *
 * `ngu-canh-tro-ly.test.mjs` giữ riêng mối nối ấy. Tệp này tổng quát hoá cho
 * MỌI trang, theo HAI chiều ghép nối:
 *
 *   JS → JS   một script cũ đọc `window.X` mà không script nào trên trang ghi.
 *   TSX → JS  mã React gọi `W().X` (tức `(window as any).X`) — 55 tên như thế
 *             trong repo, gồm `startReviewQuiz`, `enroll`, `goLesson`.
 *
 * Chiều TSX→JS được thêm SAU KHI phép chứng minh đỏ THẤT BẠI: tôi bỏ
 * `review_quiz.js` khỏi trang khoá học — đúng thao tác đã gây ra sự cố ngày
 * 19/08 — và bản chỉ-JS→JS vẫn XANH. Lý do: `review_quiz.js` được gọi từ
 * `onClick` phía React, không qua một `window.X` nào trong mã JS. Tức phần lớn
 * mặt ghép nối thật của tầng này khi ấy VÔ HÌNH với thước.
 *
 * Trang phải gom theo CÂY IMPORT, không theo từng tệp rời: `Topbar.tsx`,
 * `RoadmapSection.tsx`, `Chatbot.tsx` gọi `W().X` nhưng không tự nạp script —
 * chúng dựa vào trang cha. Xét từng tệp rời là báo đỏ giả cho cả ba.
 *
 * ── THƯỚC PHẢI ĐÚNG TRƯỚC ĐÃ ──────────────────────────────────────────────
 *
 * Bản thăm dò đầu tiên báo **12 global mồ côi**. Bảy trong số đó là lỗi của
 * chính thước, không phải của mã:
 *
 *   · `mountIcons` — `icons.js` xuất bằng `global.mountIcons = …` trong IIFE
 *     `(function (global) { … })(window)`. Thước chỉ tìm `window.X =`.
 *   · `COURSE_URLS`, `_rmPersonalLoaded` — `var` ở cột 0 của một script cổ
 *     điển CHÍNH LÀ thuộc tính của `window`.
 *   · `confetti` — nạp từ CDN, không nằm trong `/static/js/`.
 *   · `requestIdleCallback` — global của trình duyệt, thước thiếu trong danh
 *     sách.
 *
 * Đúng cái đã xảy ra với bộ đo tương phản: 106/108 "vi phạm" là lỗi của bộ đo.
 * Một phép kiểm mới phải bị nghi ngờ như mã mới — nên ba dạng GHI dưới đây được
 * viết ra vì đã ĐO thấy chúng tồn tại trong repo này, không phải vì suy đoán.
 *
 * Năm cái còn lại đã soi từng cái: `__PE_BAI_DANG_MO` vắng mặt trên trang không
 * phải bài học là ĐÚNG THIẾT KẾ (hàm trả `null`, xem `chatbot.js`), còn
 * `bayTieuDiem`/`__saveHsaGoals` là thoái lui CÓ CHỦ Ý và đã ghi lý do ngay tại
 * chỗ gọi (`main.js:1152`). Cả ba nằm trong `CHAP_NHAN` kèm lý do.
 *
 * Chạy: node e2e/unit/global-mo-coi.test.mjs
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const JSDIR = join(GOC, 'public', 'static', 'js');

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

function boChuThich(ma) {
  return ma.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/(^|[^:])\/\/[^\n]*/g, '$1 ');
}

/* ── BA DẠNG GHI, cả ba đều ĐO được trong repo này ───────────────────────── */

//  1. `window.X = …`
const GHI_WINDOW = /(?<![\w.$])window\.([A-Za-z_$][\w$]*)\s*=(?!=)/g;

//  2. `var X = …` / `function X(…)` / `async function X(…)` ở CỘT 0 của một
//     script cổ điển. Cột 0 làm đại diện cho "phạm vi script": mọi tệp trong
//     tầng này hoặc bọc toàn bộ trong IIFE (thụt lề), hoặc viết phẳng.
//     `let`/`const` KHÔNG tính — chúng ở phạm vi script nhưng không thành
//     thuộc tính của `window`.
//
//     `async` là lần thứ BA thước này sai theo cùng một kiểu: bỏ sót một cách
//     viết có thật trong repo rồi báo đỏ cho mã đang đúng. Bỏ nó thì
//     `quickChatbotAsk` (chatbot.js:108) và `startReviewQuiz` (review_quiz.js:25)
//     — cả hai đều `async function` cột 0 — bị kết luận là mồ côi.
const GHI_COT0 =
  /^(?:var\s+([A-Za-z_$][\w$]*)|(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)\s*\()/gm;

//  3. `global.X = …` trong `(function (global) { … })(window)`.
function ghiQuaBiDanh(ma) {
  const ra = new Set();
  // Tên tham số của IIFE được gọi với `window`.
  for (const m of ma.matchAll(
    /\(\s*function\s*\(\s*([A-Za-z_$][\w$]*)\s*\)[\s\S]*?\}\s*\)?\s*\(\s*window\s*\)/g)) {
    const bd = m[1];
    const re = new RegExp(`(?<![\\w.$])${bd}\\.([A-Za-z_$][\\w$]*)\\s*=(?!=)`, 'g');
    for (const g of m[0].matchAll(re)) ra.add(g[1]);
  }
  return ra;
}

function ghiBoiTep(ma) {
  const sach = boChuThich(ma);
  const ra = new Set();
  for (const m of sach.matchAll(GHI_WINDOW)) ra.add(m[1]);
  for (const m of sach.matchAll(GHI_COT0)) ra.add(m[1] || m[2]);
  for (const g of ghiQuaBiDanh(sach)) ra.add(g);
  return ra;
}

const DOC = /(?<![\w.$])window\.([A-Za-z_$][\w$]*)/g;
function docBoiTep(ma) {
  const ra = new Set();
  for (const m of boChuThich(ma).matchAll(DOC)) ra.add(m[1]);
  return ra;
}

/* ── Global của TRÌNH DUYỆT — không script nào trong repo ghi chúng ──────── */
const CUA_TRINH_DUYET = new Set([
  'location', 'localStorage', 'sessionStorage', 'document', 'navigator',
  'innerWidth', 'innerHeight', 'matchMedia', 'scrollTo', 'scrollX', 'scrollY',
  'addEventListener', 'removeEventListener', 'setTimeout', 'clearTimeout',
  'setInterval', 'clearInterval', 'fetch', 'open', 'close', 'alert', 'confirm',
  'prompt', 'print', 'focus', 'blur', 'history', 'origin', 'parent', 'top',
  'self', 'crypto', 'performance', 'devicePixelRatio', 'getComputedStyle',
  'requestAnimationFrame', 'cancelAnimationFrame', 'requestIdleCallback',
  'URL', 'URLSearchParams', 'FormData', 'Blob', 'Image', 'CSS',
  'IntersectionObserver', 'ResizeObserver', 'MutationObserver', 'Notification',
  'speechSynthesis', 'SpeechSynthesisUtterance', 'AudioContext',
]);

/* ── Mồ côi ĐƯỢC CHẤP NHẬN — mỗi dòng là một quyết định, kèm lý do ───────── */
const CHAP_NHAN = new Map([
  ['confetti',
   'nạp từ CDN (canvas-confetti) trong LessonHsa.tsx, không nằm ở /static/js/'],
  ['__PE_BAI_DANG_MO',
   'ĐÚNG THIẾT KẾ: chỉ trang bài học công bố nó; nơi khác chatbot trả null'],
  ['bayTieuDiem',
   'thoái lui CÓ CHỦ Ý, ghi rõ tại main.js:1152 — thiếu bẫy thì hộp vẫn dùng '
   + 'được, chỉ kém tiếp cận'],
  ['__saveHsaGoals',
   'cùng lối: mục "Mục tiêu HSA" chỉ có ở dashboard; nơi khác rơi về '
   + 'Promise.resolve()'],
  ['mountIcons',
   '/questionaire nạp main.js (vì nó vá window.fetch: CSRF + chặn mật khẩu '
   + 'tạm) nhưng không nạp icons.js. Chỗ đọc duy nhất là renderCourses, và hàm '
   + 'ấy THOÁT SỚM khi không có #courses-grid — đã đọc main.js:760. Trang này '
   + 'cũng có ĐÚNG 0 phần tử [data-icon]. Đo, không đoán.'],
]);

/* ── Trang = CÂY IMPORT, đọc từ CHÍNH mã React ───────────────────────────── */
const SRC = join(GOC, 'src');

function moiNguon(d) {
  const out = [];
  for (const t of readdirSync(d)) {
    const p = join(d, t);
    if (statSync(p).isDirectory()) out.push(...moiNguon(p));
    else if (t.endsWith('.tsx') || t.endsWith('.ts')) out.push(p);
  }
  return out;
}

/** `@/components/Topbar` → đường dẫn thật; thử cả `.tsx`/`.ts`/`/index`. */
function giaiTen(spec) {
  if (!spec.startsWith('@/')) return null;
  const goc = join(SRC, spec.slice(2));
  for (const hau of ['.tsx', '.ts', '/index.tsx', '/index.ts']) {
    const p = goc + hau;
    try { if (statSync(p).isFile()) return p; } catch { /* thử hậu tố sau */ }
  }
  return null;
}

/** Mọi tệp nguồn một trang KÉO THEO, đi hết chiều sâu. */
function cayImport(dau) {
  const tham = new Set([dau]);
  const hang = [dau];
  while (hang.length) {
    const p = hang.pop();
    let ma;
    try { ma = boChuThich(readFileSync(p, 'utf8')); } catch { continue; }
    for (const m of ma.matchAll(/from\s+'(@\/[\w./-]+)'/g)) {
      const con = giaiTen(m[1]);
      if (con && !tham.has(con)) { tham.add(con); hang.push(con); }
    }
  }
  return [...tham];
}

// `LegacyScripts` chèn `pe-bridge.js` cho MỌI trang dùng nó.
const LUON = ['pe-bridge.js'];

// `W().X` / `(window as any).X` — mã React gọi thẳng vào tầng cũ.
const DOC_TSX = /(?:W\(\)[?.]*|\(window as any\))\.([A-Za-z_$][\w$]*)/g;

const trang = new Map();   // trang → { srcs, goi }
for (const p of moiNguon(join(SRC, 'app'))) {
  if (!/[\\/]page\.tsx$/.test(p)) continue;
  const srcs = [];
  const goi = new Map();
  for (const q of cayImport(p)) {
    const ma = boChuThich(readFileSync(q, 'utf8'));
    for (const m of ma.matchAll(/'\/static\/js\/([\w./-]+\.js)'/g)) srcs.push(m[1]);
    for (const m of ma.matchAll(DOC_TSX)) {
      if (!goi.has(m[1])) goi.set(m[1], relative(GOC, q).replace(/\\/g, '/'));
    }
  }
  if (srcs.length) {
    trang.set(relative(GOC, p).replace(/\\/g, '/'), { srcs: [...new Set(srcs)], goi });
  }
}

check('tìm được các trang có nạp script cũ', trang.size >= 5, `${trang.size} trang`);

const moCoi = [];
const thieuTep = [];
for (const [tsx, { srcs, goi }] of [...trang].sort()) {
  const tap = [...new Set([...srcs, ...LUON])];
  const nguon = new Map();
  for (const t of tap) {
    try { nguon.set(t, readFileSync(join(JSDIR, t), 'utf8')); }
    catch { thieuTep.push(`${tsx} nạp ${t} — KHÔNG CÓ TỆP`); }
  }
  const ghi = new Set();
  for (const ma of nguon.values()) for (const g of ghiBoiTep(ma)) ghi.add(g);

  // JS → JS
  for (const [t, ma] of nguon) {
    for (const g of docBoiTep(ma)) {
      if (CUA_TRINH_DUYET.has(g) || CHAP_NHAN.has(g) || ghi.has(g)) continue;
      moCoi.push(`${tsx} · ${t} đọc window.${g} — không script nào trên trang ghi`);
    }
  }
  // TSX → JS
  for (const [g, oDau] of goi) {
    if (CUA_TRINH_DUYET.has(g) || CHAP_NHAN.has(g) || ghi.has(g)) continue;
    moCoi.push(`${tsx} · ${oDau} gọi W().${g} — không script nào trên trang ghi`);
  }
}

check('mọi script được nạp đều TỒN TẠI', thieuTep.length === 0, thieuTep.join('\n      '));

check('không có global mồ côi trên trang nào', moCoi.length === 0,
  moCoi.length
    ? '\n      ' + moCoi.join('\n      ')
      + '\n\n      Sửa: cho một script ĐANG NẠP ghi nó ra, hoặc thôi đọc nó.'
      + '\n      Nếu vắng mặt là ĐÚNG (nạp từ CDN, chỉ có ở một trang…), thêm vào'
      + '\n      `CHAP_NHAN` KÈM LÝ DO — một dòng ở đó là một quyết định có ý thức.'
    : '');

/* Thước không được nới đến mức không bắt gì. Kiểm nó trên mã giả có sẵn đáp án. */
{
  const mau = `
window.A = 1;
var B = 2;
function C() {}
let D = 3;
(function (global) { global.E = 4; })(window);
async function F() {}
function* G() {}
const H = 5;
  function I() {}
`;
  const g = ghiBoiTep(mau);
  check('thước thấy `window.A =`', g.has('A'));
  check('thước thấy `var B` ở cột 0', g.has('B'));
  check('thước thấy `function C()` ở cột 0', g.has('C'));
  check('thước thấy `global.E =` trong IIFE(window)', g.has('E'));
  check('thước thấy `async function F()` ở cột 0', g.has('F'),
    'bỏ sót async → báo đỏ giả cho quickChatbotAsk và startReviewQuiz');
  check('thước thấy `function* G()` ở cột 0', g.has('G'));
  check('thước KHÔNG nhận `let D` (không thành thuộc tính window)', !g.has('D'),
    'nhận nhầm → sẽ bỏ sót một global mồ côi thật');
  check('thước KHÔNG nhận `const H`', !g.has('H'));
  check('thước KHÔNG nhận hàm THỤT LỀ (nằm trong IIFE, không ra window)',
    !g.has('I'), 'nhận nhầm → bỏ sót global mồ côi thật');
}

console.log(failures === 0 ? '\nOK — không trang nào đọc global mồ côi'
  : `\n${failures} lỗi`);
process.exitCode = failures === 0 ? 0 : 1;
