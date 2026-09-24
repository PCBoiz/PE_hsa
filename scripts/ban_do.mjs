#!/usr/bin/env node
/**
 * BẢN ĐỒ HỆ THỐNG pe_hsa — đồ thị các CHỖ NỐI giữa các tầng.
 *
 * ── VÌ SAO CÓ TỆP NÀY (23/09/2026) ────────────────────────────────────────
 *
 * Anh Sơn bảo nghiên cứu graphify (Graphify-Labs, ~120 nghìn sao) rồi áp về
 * đây. Chạy thật trên pe_hsa (`--code-only`, 461 tệp): 5.145 nút, 12.058 cạnh,
 * 241 cụm, 1.009 nút "lý do" từ docstring — nhưng ĐO RA đúng 0 cạnh ở bốn chỗ:
 *
 *     trang Next  ──fetch('/api/x')──▶  tuyến Django        (0 cạnh)
 *     React       ──goiLegacy('x')───▶  hàm JS cũ           (0 cạnh)
 *     view Django ──q1('… FROM t')──▶  bảng SQL            (0 cạnh)
 *     view Django ──permission_classes▶ lớp quyền           (không phải cạnh)
 *
 * Graphify đọc cú pháp từng ngôn ngữ, nên nó thấy lời gọi hàm TRONG một tầng.
 * Mà lỗi đắt nhất của pe_hsa sống ở chỗ HAI TẦNG nối nhau qua một CHUỖI:
 * RULES §1 — 45/45 phép kiểm xanh trong khi cả màn điểm danh chết, vì backend
 * trả `startsAt` còn frontend đọc `starts_at`. Tệp này dựng đúng các cạnh ấy.
 *
 * ── MƯỢN GÌ CỦA GRAPHIFY ─────────────────────────────────────────────────
 *
 *   · Đầu ra là `graph.json` máy đọc được + một báo cáo người đọc được.
 *   · Mỗi cạnh mang ĐỘ TIN CẬY: `EXTRACTED` (đọc thẳng từ mã: urls.py,
 *     permission_classes, REFERENCES) hay `INFERRED` (suy từ CHUỖI: URL trong
 *     fetch, tên bảng trong câu SQL). Người đọc biết cạnh nào là sự thật, cạnh
 *     nào là đoán — và đoán thì sai được (xem ghi chú "thước" bên dưới).
 *
 * ── KHÔNG MƯỢN GÌ ────────────────────────────────────────────────────────
 *
 *   · Không gọi mô hình nào. Lượt chạy graphify ngày 23/09 tự tìm lệnh `claude`
 *     trên máy để ĐẶT TÊN CỤM, tốn ~124 nghìn token mà không hỏi (cờ tắt:
 *     `--no-label`). Tệp này tất định, chạy 1 giây, không tốn gì.
 *   · Không hook vào trợ lý, không đổi cách ai đọc mã.
 *
 * ── THƯỚC DÒ CHUỖI THÌ SAI ĐƯỢC ─────────────────────────────────────────
 *
 * Bản thử đầu (cùng ngày) báo 9 lời gọi "mồ côi" và 0 tuyến "không ai gọi" —
 * sai cả hai: chuỗi `/api/*` trong CHÚ THÍCH khớp mọi tuyến, `path("api/chat")`
 * viết nháy kép bị bỏ sót, URL ghép chuỗi trong JS cũ (`'/api/quizzes/' + id`)
 * không được nhận. Mỗi quy tắc dưới đây sinh ra từ một lần báo oan như thế.
 * Kết quả vẫn là GỢI Ý có bằng chứng, không phải phán quyết.
 *
 * Chạy:   node scripts/ban_do.mjs            → ban_do/graph.json + ban_do/BAO_CAO.md
 *         node scripts/ban_do.mjs --kiem     → thoát 1 nếu có chỗ nối gãy (dùng trong CI)
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const RA = path.join(GOC, 'ban_do');
const doc = (p) => fs.readFileSync(p, 'utf8');
const rel = (p) => path.relative(GOC, p).split(path.sep).join('/');

function duyet(thuMuc, loc) {
  const ra = [];
  const di = (d) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      if (['node_modules', '.next', '.venv', '__pycache__', 'migrations', 'test-results'].includes(e.name)) continue;
      const p = path.join(d, e.name);
      if (e.isDirectory()) di(p);
      else if (loc(p)) ra.push(p);
    }
  };
  if (fs.existsSync(thuMuc)) di(thuMuc);
  return ra;
}

const nut = new Map();          // id → {id, loai, nhan, tep, dong}
const canh = [];                // {tu, toi, quanHe, tinCay, tep, dong}
function themNut(id, loai, nhan, tep, dong) {
  if (!nut.has(id)) nut.set(id, { id, loai, nhan, tep, dong });
  return id;
}
function themCanh(tu, toi, quanHe, tinCay, tep, dong) {
  canh.push({ tu, toi, quanHe, tinCay, tep, dong });
}

/* ── 1 · LƯỢC ĐỒ: bảng + khoá ngoại (EXTRACTED) ─────────────────────────── */
const BANG = new Set();
for (const tep of duyet(path.join(GOC, 'backend', 'sql'), (p) => p.endsWith('.sql'))) {
  const t = doc(tep);
  const re = /CREATE TABLE IF NOT EXISTS\s+"?(\w+)"?\s*\(([\s\S]*?)\n\);/g;
  let m;
  while ((m = re.exec(t))) {
    const bang = m[1].toLowerCase();
    BANG.add(bang);
    const dong = t.slice(0, m.index).split('\n').length;
    themNut(`bang:${bang}`, 'bang', bang, rel(tep), dong);
    for (const r of m[2].matchAll(/REFERENCES\s+"?(\w+)"?/gi)) {
      themCanh(`bang:${bang}`, `bang:${r[1].toLowerCase()}`, 'khoa_ngoai', 'EXTRACTED', rel(tep), dong);
    }
  }
  // Khoá ngoại thêm sau bằng ALTER TABLE … FOREIGN KEY … REFERENCES
  for (const a of t.matchAll(/ALTER TABLE\s+"?(\w+)"?[^;]*?FOREIGN KEY[^;]*?REFERENCES\s+"?(\w+)"?/gi)) {
    const dong = t.slice(0, a.index).split('\n').length;
    themCanh(`bang:${a[1].toLowerCase()}`, `bang:${a[2].toLowerCase()}`, 'khoa_ngoai', 'EXTRACTED', rel(tep), dong);
  }
}

/* ── 2 · BACKEND: tuyến → view (EXTRACTED), view → quyền (EXTRACTED),
         mô-đun → bảng (INFERRED, từ chuỗi SQL) ──────────────────────────── */
const BE = path.join(GOC, 'backend');

/* CHỈ tính `urls.py` được GẮN vào cây tuyến thật: đi từ `ROOT_URLCONF` theo
   `include('x.urls')` (24/09/2026). Bản trước đọc MỌI tệp `urls.py` trên đĩa —
   ngày bỏ thi (pha A) tháo `include('mockexam.urls')` mà thước vẫn thấy đủ 9
   tuyến thi, tức một lời gọi frontend tới tuyến đã tháo sẽ được báo là "khớp":
   đúng loại mù mà tệp này sinh ra để chữa. Include nằm trong chú thích `#` hay
   docstring không được tính. Gói ngoài (`allauth.urls`) không có tệp trong
   `backend/` nên tự rơi ra. */
function cacInclude(t) {
  const sach = t.replace(/("""|''')[\s\S]*?\1/g, ' ').replace(/#[^\n]*/g, ' ');
  return [...sach.matchAll(/include\(\s*(['"])([\w.]+)\1/g)].map((m) => m[2]);
}
const ROOT_URLCONF = /^ROOT_URLCONF\s*=\s*['"]([\w.]+)['"]/m
  .exec(doc(path.join(BE, 'config', 'settings.py')))?.[1] ?? 'config.urls';
const DA_GAN = new Set([ROOT_URLCONF]);
for (const hang = [ROOT_URLCONF]; hang.length;) {
  const tepMod = path.join(BE, ...hang.shift().split('.')) + '.py';
  if (!fs.existsSync(tepMod)) continue;
  for (const con of cacInclude(doc(tepMod))) if (!DA_GAN.has(con)) { DA_GAN.add(con); hang.push(con); }
}
const urlsKhongGan = [];        // tệp urls.py có trên đĩa mà không ai gắn — ghi vào báo cáo

const tuyen = [];               // {mau, view, app, tep, dong}
for (const tep of duyet(BE, (p) => p.endsWith(`${path.sep}urls.py`))) {
  const mod = path.relative(BE, tep).replace(/\.py$/, '').split(path.sep).join('.');
  if (!DA_GAN.has(mod)) { urlsKhongGan.push(rel(tep)); continue; }
  const app = path.basename(path.dirname(tep));
  const t = doc(tep);
  // Nháy ĐƠN hoặc KÉP — bản đầu chỉ bắt nháy đơn và bỏ sót `path("api/chat", …)`.
  // `config/urls.py` cũng khai tuyến thật (`api/health`); chỉ bỏ dòng `include(…)`.
  for (const m of t.matchAll(/path\(\s*(['"])([^'"]*)\1\s*,\s*(?!include\()([\w.]+)/g)) {
    const dong = t.slice(0, m.index).split('\n').length;
    const dich = m[3].replace(/\.as_view$/, '');
    const view = dich.split('.').pop();
    const mau = '/' + m[2].replace(/<[^>]+>/g, '*').replace(/\/$/, '');
    tuyen.push({ mau, view, app, tep: rel(tep), dong, modGoi: dich.split('.').slice(0, -1).join('.') });
    themNut(`tuyen:${mau}`, 'tuyen', mau, rel(tep), dong);
    themNut(`view:${app}.${view}`, 'view', `${app}.${view}`, rel(tep), dong);
    themCanh(`tuyen:${mau}`, `view:${app}.${view}`, 'goi_view', 'EXTRACTED', rel(tep), dong);
  }
}

// Tuyến do chính NEXT phục vụ (`src/app/**/route.ts`), ví dụ `/auth/session`.
// BỎ tuyến bắt-tất-cả (`[...path]`): chúng là proxy chuyển tiếp sang Django và
// khớp MỌI URL — đưa vào là mọi lời gọi đều "có đích", phép so mù hoàn toàn.
const APP = path.join(GOC, 'frontend', 'src', 'app');
for (const tep of duyet(APP, (p) => /route\.ts$/.test(p))) {
  const doanDuong = path.relative(APP, path.dirname(tep)).split(path.sep)
    .filter((s) => !/^\(.*\)$/.test(s));               // bỏ nhóm `(standalone)`
  if (doanDuong.some((s) => s.startsWith('[...'))) continue;
  const mau = '/' + doanDuong.map((s) => (/^\[.*\]$/.test(s) ? '*' : s)).join('/');
  tuyen.push({ mau, view: 'route.ts', app: 'next', tep: rel(tep), dong: 1 });
  themNut(`tuyen:${mau}`, 'tuyen', mau, rel(tep), 1);
}

// view → lớp quyền, và view → tệp định nghĩa (để nối tới bảng qua mô-đun)
const viewTep = new Map();       // "app.View" → tệp .py định nghĩa
for (const tep of duyet(BE, (p) => p.endsWith('.py') && !/tests?_?[^/\\]*\.py$/.test(path.basename(p)) && !p.includes(`${path.sep}sql${path.sep}`))) {
  const app = path.relative(BE, tep).split(path.sep)[0];
  const t = doc(tep);
  const lop = [...t.matchAll(/^class (\w+)\(([^)]*)\):/gm)];
  lop.forEach((m, i) => {
    const than = t.slice(m.index, i + 1 < lop.length ? lop[i + 1].index : t.length);
    const id = `view:${app}.${m[1]}`;
    if (!nut.has(id)) return;                 // chỉ những lớp được tuyến trỏ tới
    viewTep.set(`${app}.${m[1]}`, tep);
    const dong = t.slice(0, m.index).split('\n').length;
    const q = than.match(/permission_classes\s*=\s*\[([^\]]*)\]/);
    const ds = q ? q[1].split(',').map((s) => s.trim()).filter(Boolean) : [];
    if (!ds.length) themCanh(id, 'quyen:(mặc định)', 'can_quyen', 'EXTRACTED', rel(tep), dong);
    for (const p of ds) {
      themNut(`quyen:${p}`, 'quyen', p, rel(tep), dong);
      themCanh(id, `quyen:${p}`, 'can_quyen', 'EXTRACTED', rel(tep), dong);
    }
  });
}
themNut('quyen:(mặc định)', 'quyen', '(mặc định: IsAuthenticated)', 'backend/config/settings.py', 0);

// mô-đun → bảng: tên bảng CÓ THẬT trong lược đồ đứng sau FROM/JOIN/INTO/UPDATE.
// INFERRED: một chuỗi SQL dựng động hay một chú thích nhắc tên bảng đều lọt vào.
const modBang = new Map();
for (const tep of new Set(viewTep.values())) {
  const t = doc(tep);
  const s = new Set();
  for (const m of t.matchAll(/\b(?:FROM|JOIN|INTO|UPDATE)\s+"?([a-z_][a-z0-9_]*)"?/gi)) {
    const b = m[1].toLowerCase();
    if (BANG.has(b)) s.add(b);
  }
  modBang.set(tep, s);
}
for (const [v, tep] of viewTep) {
  for (const b of modBang.get(tep) || []) themCanh(`view:${v}`, `bang:${b}`, 'cham_bang', 'INFERRED', rel(tep), 0);
}

/* ── 3 · FRONTEND: tệp → tuyến (INFERRED, từ chuỗi URL) ─────────────────── */
const FE_TEP = [
  ...duyet(path.join(GOC, 'frontend', 'src'), (p) => /\.(tsx?|mjs)$/.test(p)),
  ...duyet(path.join(GOC, 'frontend', 'public', 'static', 'js'), (p) => p.endsWith('.js')),
];

/* ── Đọc CHUỖI GHÉP, không đọc chuỗi đơn lẻ ───────────────────────────────
   JS cũ dựng URL kiểu `'/api/courses/' + encodeURIComponent(id) + '/content?x='
   + n`, và `dashboard.js` khai `var API = '/api/hsa/…'` LẠI nhiều lần trong các
   khối IIFE nối tiếp rồi viết `API + '/items/' + id`. Dò từng chuỗi riêng thì
   một URL thành ba mảnh vô nghĩa. Nên: đọc cả chuỗi `a + b + c`, literal lấy
   nguyên văn, hằng URL lấy giá trị khai GẦN NHẤT phía trên trong cùng tệp,
   biểu thức khác thành một chỗ trống `\0`. */
const TRONG = '\u0000';

/** Đọc một literal JS tại `i`. Trả `{val, end}` hoặc null. `${…}` → chỗ trống. */
function docLiteral(t, i, hang = () => null) {
  const q = t[i];
  if (q !== "'" && q !== '"' && q !== '`') return null;
  let j = i + 1, val = '';
  while (j < t.length && t[j] !== q) {
    if (t[j] === '\\') { val += t[j + 1] ?? ''; j += 2; continue; }
    if (q === '`' && t[j] === '$' && t[j + 1] === '{') {
      let sau = 1; const dau = j + 2; j += 2;
      while (j < t.length && sau) { if (t[j] === '{') sau++; else if (t[j] === '}') sau--; j++; }
      // `${goc}` mà `goc` là một hằng URL đã khai → lấy giá trị hằng.
      const ben = t.slice(dau, j - 1).trim();
      val += (/^[A-Za-z_$][\w$]*$/.test(ben) && hang(ben)) || TRONG; continue;
    }
    if (q !== '`' && t[j] === '\n') return null;
    val += t[j++];
  }
  return { val, end: j + 1 };
}

/** Đọc một biểu thức tới dấu `+` / kết thúc ở độ sâu 0. */
function docBieuThuc(t, i) {
  let j = i, sau = 0;
  while (j < t.length) {
    const c = t[j];
    if ('([{'.includes(c)) sau++;
    else if (')]}'.includes(c)) { if (!sau) break; sau--; }
    else if (!sau && '+,;\n?:'.includes(c)) break;
    else if (c === "'" || c === '"' || c === '`') { const l = docLiteral(t, j); if (l) { j = l.end; continue; } }
    j++;
  }
  return { expr: t.slice(i, j).trim(), end: j };
}

/** Đọc cả chuỗi ghép bắt đầu tại `i`. `hang(ten)` trả giá trị hằng URL hoặc null. */
function docChuoiGhep(t, i, hang) {
  let j = i, ra = '';
  for (;;) {
    while (/[ \t]/.test(t[j] ?? '')) j++;
    const l = docLiteral(t, j, hang);
    if (l) { ra += l.val; j = l.end; }
    else {
      const b = docBieuThuc(t, j);
      if (!b.expr) break;
      const h = /^[A-Za-z_$][\w$]*$/.test(b.expr) ? hang(b.expr) : null;
      ra += h ?? TRONG; j = b.end;
    }
    let k = j; while (/[ \t\r\n]/.test(t[k] ?? '')) k++;
    if (t[k] !== '+') break;
    j = k + 1;
    while (/[ \t\r\n]/.test(t[j] ?? '')) j++;
  }
  return { url: ra, end: j };
}

/** URL thô (có chỗ trống) → mẫu so được với tuyến backend. */
function mauFE(url) {
  let u = url.split('?')[0].split('#')[0];
  let duoiDinh = false;
  const doan = u.split('/').map((s, i, a) => {
    if (!s.includes(TRONG)) return s;
    /* Chỗ trống DÍNH đuôi một đoạn tĩnh: `parent-report${qs}` là chuỗi truy vấn,
       nhưng `holidays${duong}` (với `duong = '/' + id`) lại là THÊM một đoạn
       đường dẫn. Không biết là cái nào — nên giữ phần tĩnh và đánh cờ để bên so
       thử cả hai (khớp đúng → INFERRED; thêm một đoạn → AMBIGUOUS). */
    const tinh = s.replace(new RegExp(TRONG, 'g'), '');
    if (tinh && s.endsWith(TRONG) && i === a.length - 1) { duoiDinh = true; return tinh; }
    return '*';
  });
  u = doan.join('/').replace(/\/+$/, '');
  // `'/api/quizzes/' + id` — đuôi '/' bị nối tiếp đã thành `/*` ở trên.
  return { mau: u, duoiDinh };
}

/* ── VÙNG CHÚ THÍCH, đọc bằng máy quét hiểu chuỗi ─────────────────────────
   Bản trước chỉ bỏ dòng MỞ ĐẦU bằng `//`, `*`, `/*`. Dòng tiếp nối của một khối
   `/* … *\/` không mở đầu bằng `*` thì lọt — và 23/09/2026 một câu ví dụ tấn
   công XSS trong chú thích `dashboard.js` ("`fetch('/api/admin/users/create')`
   cùng origin…") được đếm là NGƯỜI GỌI của tuyến ấy, trong khi thực tế không
   màn hình nào gọi nó. Quét từng ký tự, nhớ đang ở trong chuỗi nào (', ", `
   kèm `${…}` lồng nhau) và regex literal, thì `//` trong 'https://…' không bị
   tưởng là chú thích. */
function vungChuThich(t) {
  const vung = [];
  const ngoac = [];               // độ sâu `{` của từng tầng `${` đang mở
  let i = 0, trongMau = false;    // đang ở phần CHỮ của một template
  let truoc = '';                 // ký tự có nghĩa gần nhất — để đoán regex
  while (i < t.length) {
    const c = t[i];
    if (trongMau) {
      if (c === '\\') { i += 2; continue; }
      if (c === '`') { trongMau = false; i++; truoc = '`'; continue; }
      if (c === '$' && t[i + 1] === '{') { ngoac.push(0); trongMau = false; i += 2; truoc = '{'; continue; }
      i++; continue;
    }
    if (c === '/' && t[i + 1] === '/') {
      const het = t.indexOf('\n', i); const cuoi = het < 0 ? t.length : het;
      vung.push([i, cuoi]); i = cuoi; continue;
    }
    if (c === '/' && t[i + 1] === '*') {
      const het = t.indexOf('*/', i + 2); const cuoi = het < 0 ? t.length : het + 2;
      vung.push([i, cuoi]); i = cuoi; continue;
    }
    if (c === "'" || c === '"') {
      // Chuỗi thường không qua được dòng mới — dấu nháy lẻ trong chữ JSX
      // ("Em's") không được nuốt cả phần còn lại của tệp.
      let j = i + 1;
      while (j < t.length && t[j] !== c && t[j] !== '\n') j += t[j] === '\\' ? 2 : 1;
      i = j + 1; truoc = c; continue;
    }
    if (c === '`') { trongMau = true; i++; continue; }
    if (c === '/' && (!truoc || '(,=:[!&|?{};+-*%<>~^'.includes(truoc))) {
      // Regex literal: `/\/\//` không được mở một chú thích dòng.
      let j = i + 1, lop = false;
      while (j < t.length && t[j] !== '\n') {
        if (t[j] === '\\') { j += 2; continue; }
        if (t[j] === '[') lop = true; else if (t[j] === ']') lop = false;
        else if (t[j] === '/' && !lop) break;
        j++;
      }
      i = j + 1; truoc = '/'; continue;
    }
    if (ngoac.length) {
      if (c === '{') ngoac[ngoac.length - 1]++;
      else if (c === '}') {
        if (ngoac[ngoac.length - 1] === 0) { ngoac.pop(); trongMau = true; i++; continue; }
        ngoac[ngoac.length - 1]--;
      }
    }
    if (!/\s/.test(c)) truoc = /[\w$)\]]/.test(c) ? 'x' : c;
    i++;
  }
  return vung;
}

/** Mọi lời gọi `/api…` `/auth…` trong MỘT tệp nguồn. Tách thành hàm để
    `--tu-kiem` chạy đúng máy quét này trên một đoạn mã cài sẵn. */
function quetTep(t, tenTep) {
  const ra = [];
  const chuThich = vungChuThich(t);
  const trongChuThich = (vi) => chuThich.some(([a, b]) => vi >= a && vi < b);
  // Hằng URL trong tệp: `var|const|let TEN = <chuỗi ghép bắt đầu /api|/auth>`.
  const hangTep = [];
  for (const m of t.matchAll(/\b(?:var|const|let)\s+([A-Za-z_$][\w$]*)\s*=\s*(?=['"`]\/(?:api|auth))/g)) {
    const { url } = docChuoiGhep(t, m.index + m[0].length, () => null);
    hangTep.push({ ten: m[1], vi: m.index, url });
  }
  const hangTai = (vi) => (ten) => {
    let tot = null;
    for (const h of hangTep) if (h.ten === ten && h.vi < vi) tot = h;
    if (tot) return tot.url;
    // `main.js` khai `var API = "/api"` ở tầm TOÀN CỤC — tệp khác dùng `API` mà
    // không khai riêng thì là hằng ấy.
    return ten === 'API' ? '/api' : null;
  };
  // Điểm bắt đầu: literal '/api…' '/auth…', hoặc một hằng URL đứng đầu chuỗi ghép.
  const tenHang = [...new Set(hangTep.map((h) => h.ten))];
  // Điểm bắt đầu: literal '/api…'; hằng URL đứng đầu chuỗi ghép (`API + …`,
  // `fetch(API)`); hoặc template mở đầu bằng hằng (`\`${goc}/doc\``).
  const hoac = tenHang.join('|');
  const re = new RegExp(`(['"\`])\\/(?:api|auth)[/'"\`?]${tenHang.length
    ? `|\\b(?:${hoac})\\b(?=\\s*(?:\\+|\\)))|\`\\$\\{(?:${hoac})\\}` : ''}`, 'g');
  let m;
  while ((m = re.exec(t))) {
    // Bỏ chuỗi nằm trong CHÚ THÍCH và ví dụ minh hoạ — nguồn báo oan lớn nhất.
    if (trongChuThich(m.index)) continue;
    const dong = t.slice(0, m.index).split('\n').length;
    /* KHÔNG bỏ dòng khai hằng (`const goc = \`/api/…/ket-qua-thi\``). Bản trước bỏ
       để khỏi đếm trùng — và làm 3 tuyến thành "không ai gọi" oan: một hằng URL
       dùng làm `href` hay ghép tiếp ở chỗ khác CŨNG là tham chiếu tới tuyến ấy. */
    const { url, end } = docChuoiGhep(t, m.index, hangTai(m.index));
    re.lastIndex = Math.max(re.lastIndex, end);
    if (/\.\.\.|…|%2f/i.test(url) || /path\.join/.test(url)) continue;
    const { mau, duoiDinh } = mauFE(url);
    if (['/api', '/api/*', '/auth', '/auth/*'].includes(mau)) continue;
    ra.push({ mau, duoiDinh, tep: tenTep, dong, tho: url.replace(new RegExp(TRONG, 'g'), '…') });
  }
  return ra;
}

const goiFE = [];                // {mau, tep, dong, tho}
for (const tep of FE_TEP) goiFE.push(...quetTep(doc(tep), rel(tep)));

const seg = (u) => u.split('/').filter(Boolean);
/** Mẫu FE khớp mẫu BE: từng đoạn bằng nhau, hoặc một bên là `*`. */
function khop(fe, be) {
  const a = seg(fe), b = seg(be);
  if (a.length !== b.length) return false;
  return a.every((x, i) => x === '*' || b[i] === '*' || x === b[i]);
}

/** Mẫu FE là TIỀN TỐ của mẫu BE (URL dựng dở, ghép tiếp ở chỗ khác). */
function tienTo(fe, be) {
  const a = seg(fe), b = seg(be);
  if (a.length >= b.length) return false;
  return a.every((x, i) => x === '*' || b[i] === '*' || x === b[i]);
}

/* Mức tin cậy thứ ba, mượn nguyên của graphify: `AMBIGUOUS`. Khớp tiền tố thì
   có thể đúng (`goc = …/ket-qua-thi`, rồi `${goc}/doc`) mà cũng có thể chỉ là
   một phép so `url.startsWith('/api/teach')`. Chỉ tính là "có người gọi" khi
   tiền tố thiếu ĐÚNG MỘT đoạn và dài ≥ 3 đoạn — `'/api/teach'` trơ trọi không
   được phép tự đánh dấu hai chục tuyến giảng dạy là đã có người gọi. */
/* TỰ KIỂM: cài hai lỗi GIẢ rồi đòi thước bắt được — cùng quy ước với
   `do_giao_dien.mjs --tu-kiem`. Một cái thước báo 0 lần đầu chưa chứng minh gì:
   bản thử đầu tiên của chính tệp này báo "0 tuyến không ai gọi" chỉ vì một chuỗi
   `/api/*` trong chú thích khớp MỌI tuyến. */
const TU_KIEM = process.argv.includes('--tu-kiem');
const GIA_GOI = '/api/__tu_kiem__/khong-ton-tai';
const GIA_TUYEN = '/api/__tu_kiem__/khong-ai-goi';
if (TU_KIEM) {
  goiFE.push({ mau: GIA_GOI, duoiDinh: false, tep: '(tự kiểm)', dong: 0, tho: GIA_GOI });
  tuyen.push({ mau: GIA_TUYEN, view: 'TuKiemView', app: 'tu_kiem', tep: '(tự kiểm)', dong: 0 });
  themNut(`tuyen:${GIA_TUYEN}`, 'tuyen', GIA_TUYEN, '(tự kiểm)', 0);
}

const khongKhop = [];
for (const g of goiFE) {
  const idTep = themNut(`tep:${g.tep}`, 'tep_fe', g.tep, g.tep, 0);
  const trung = tuyen.filter((r) => khop(g.mau, r.mau));
  // Đuôi dính (`holidays${duong}`): thử thêm tuyến dài hơn ĐÚNG một đoạn.
  if (g.duoiDinh) {
    for (const r of tuyen.filter((x) => tienTo(g.mau, x.mau) && seg(x.mau).length - seg(g.mau).length === 1)) {
      themCanh(idTep, `tuyen:${r.mau}`, 'goi_api', 'AMBIGUOUS', g.tep, g.dong);
    }
  }
  if (trung.length) {
    for (const r of trung) themCanh(idTep, `tuyen:${r.mau}`, 'goi_api', 'INFERRED', g.tep, g.dong);
    continue;
  }
  const gan = tuyen.filter((r) => tienTo(g.mau, r.mau));
  if (!gan.length) { khongKhop.push(g); continue; }
  for (const r of gan) {
    const du = seg(g.mau).length >= 3 && seg(r.mau).length - seg(g.mau).length === 1;
    themCanh(idTep, `tuyen:${r.mau}`, du ? 'goi_api' : 'goi_api_tien_to', 'AMBIGUOUS', g.tep, g.dong);
  }
}

/* ── 4 · CẦU REACT → JS CŨ (EXTRACTED) ───────────────────────────────────── */
const hamCu = new Map();         // tên → tệp
for (const tep of duyet(path.join(GOC, 'frontend', 'public', 'static', 'js'), (p) => p.endsWith('.js'))) {
  const t = doc(tep);
  for (const m of t.matchAll(/^\s*(?:async\s+)?function\s+(\w+)\s*\(|window\.(\w+)\s*=(?!=)/gm)) {
    const ten = m[1] || m[2];
    if (!hamCu.has(ten)) hamCu.set(ten, rel(tep));
  }
}
const cauGay = [];
for (const tep of duyet(path.join(GOC, 'frontend', 'src'), (p) => /\.tsx?$/.test(p))) {
  const t = doc(tep);
  for (const m of t.matchAll(/goiLegacy\(\s*'(\w+)'|W\(\)\??\.(\w+)\s*\(/g)) {
    const ten = m[1] || m[2];
    const dong = t.slice(0, m.index).split('\n').length;
    const idTep = themNut(`tep:${rel(tep)}`, 'tep_fe', rel(tep), rel(tep), 0);
    if (!hamCu.has(ten)) { cauGay.push({ ten, tep: rel(tep), dong }); continue; }
    themNut(`hamcu:${ten}`, 'ham_cu', ten, hamCu.get(ten), 0);
    themCanh(idTep, `hamcu:${ten}`, 'goi_js_cu', 'EXTRACTED', rel(tep), dong);
  }
}

/* ── 5 · SUY RA: chỗ nối gãy / thừa ──────────────────────────────────────── */
const coNguoiGoi = new Set(canh.filter((c) => c.quanHe === 'goi_api').map((c) => c.toi));

/* Tuyến CỐ Ý không có người gọi phía frontend — mỗi dòng phải có lý do. Tuyến
   mới mà không ai gọi sẽ làm `--kiem` đỏ: hoặc nối nó vào giao diện, hoặc ghi
   vào đây kèm lý do. */
const KHONG_CAN_NGUOI_GOI = {
  '/api/admin/do-proxy': 'tuyến chẩn đoán proxy, chỉ kịch bản vận hành gọi',
  '/api/health': 'kiểm sức khoẻ cho Render / giữ ấm',
  '/auth/oauth-complete': 'nhà cung cấp OAuth chuyển hướng về, không phải fetch',
  '/auth/refresh': 'proxy Next tự gọi phía máy chủ khi thẻ hết hạn',
  '/auth/register': 'màn đăng ký đã gỡ — tài khoản do trung tâm cấp',
  '/health': 'Render gọi để kiểm sức khoẻ dịch vụ',
};

/* ỨNG VIÊN GỠ — soi TAY từng tuyến ngày 23/09/2026: không nơi nào trong
   frontend gọi (chỉ phép kiểm backend, hoặc chỉ một dòng chú thích). KHÔNG giấu
   vào danh sách trên: chúng là nợ cần anh Sơn quyết gỡ hay nối lại, không phải
   tuyến có chủ ý. Nằm ở đây để `--kiem` chỉ đỏ với tuyến MỚI không ai gọi. */
const UNG_VIEN_GO = {
  '/api/course/rating': 'đánh giá khoá: sao trên trang là số seed 5.0, bảng course_ratings rỗng',
  '/api/course/*/rating': 'như trên',
  '/api/comments/*': 'sửa/xoá bình luận: frontend chỉ gọi …/react',
  // `/api/mock-attempts` ra khỏi danh sách 24/09/2026: tuyến đã THÁO (bỏ thi, pha A).
  '/api/courses/*/quiz/history': 'không nơi nào gọi',
  '/api/quizzes/*': 'frontend chỉ gọi …/submit, không lấy đề qua tuyến này',
  '/api/roadmaps': 'không nơi nào gọi',
  '/api/streak/review-quiz-status': 'chỉ phép kiểm backend gọi',
  '/api/teach/terms': 'frontend dùng /api/admin/terms',
  // Lộ ra 23/09/2026 khi máy quét thôi đếm chuỗi trong chú thích: "người gọi"
  // duy nhất là câu ví dụ tấn công XSS ở dashboard.js:757. Cấp lẻ một em đi qua
  // ô nhập hàng loạt (một dòng). View vẫn giữ đúng luật mới (học vụ chỉ tạo Học
  // viên, cấp mã HSA ngay) — `teaching/tests_ho_so_hoc_vien.py` canh.
  '/api/admin/users/create': 'không màn hình nào gọi — cấp lẻ đi qua ô nhập hàng loạt',
};
const khongAiGoi = tuyen
  .filter((r) => !coNguoiGoi.has(`tuyen:${r.mau}`))
  .map((r) => ({
    ...r,
    lyDo: KHONG_CAN_NGUOI_GOI[r.mau] || (UNG_VIEN_GO[r.mau] ? `ỨNG VIÊN GỠ — ${UNG_VIEN_GO[r.mau]}` : null),
  }));

/* Lý do trỏ vào tuyến KHÔNG còn gắn (24/09/2026): tháo tuyến mà quên dòng lý do
   thì dòng ấy nằm chờ — ngày ai đó gắn lại một tuyến cùng khuôn, nó được miễn
   kiểm sẵn bằng một câu viết cho tuyến cũ. Đỏ ở `--kiem` để dọn cùng lượt tháo. */
const coTuyen = new Set(tuyen.map((r) => r.mau));
const GIA_LY_DO = '/api/__tu_kiem__/da-thao';
if (TU_KIEM) UNG_VIEN_GO[GIA_LY_DO] = 'lý do giả của tự kiểm';
const lyDoMoCoi = [...Object.keys(KHONG_CAN_NGUOI_GOI), ...Object.keys(UNG_VIEN_GO)]
  .filter((mau) => !coTuyen.has(mau));

const bangCham = new Set(canh.filter((c) => c.quanHe === 'cham_bang').map((c) => c.toi.slice(5)));
const bangKhongAiCham = [...BANG].filter((b) => !bangCham.has(b)).sort();

if (TU_KIEM) {
  const batGoi = khongKhop.some((g) => g.mau === GIA_GOI);
  const batTuyen = khongAiGoi.some((r) => r.mau === GIA_TUYEN && !r.lyDo);
  /* Lỗi giả thứ ba — đúng ca đã báo oan 23/09/2026: lời gọi nằm ở dòng TIẾP NỐI
     của một khối chú thích (không mở đầu bằng `*`). Cùng đoạn cài thêm hai bẫy
     cho chiều ngược lại: `//` trong một URL và trong regex literal không được
     nuốt lời gọi THẬT đứng sau trên cùng dòng. */
  const mauGia = [
    '/* ví dụ tấn công, KHÔNG phải lời gọi:',
    "   DÙNG nó: `fetch('/api/__tu_kiem__/trong-chu-thich')` cùng origin",
    '*/',
    "const re = /^(\\/\\/|x)/; const u = 'https://a.vn//b'; fetch('/api/__tu_kiem__/sau-url');",
    "const tpl = `${a}//${b}`; fetch(`/api/__tu_kiem__/sau-mau/${id}`);",
  ].join('\n');
  const thay = quetTep(mauGia, '(tự kiểm)').map((g) => g.mau);
  const boChuThich = !thay.includes('/api/__tu_kiem__/trong-chu-thich');
  const giuGoiThat = thay.includes('/api/__tu_kiem__/sau-url') && thay.includes('/api/__tu_kiem__/sau-mau/*');
  /* Hai ca thêm 24/09/2026 (bỏ thi, pha A): include bị chú thích / nằm trong
     docstring KHÔNG được gắn tuyến; lý do trỏ vào tuyến đã tháo phải bị bắt. */
  const gan = cacInclude([
    "    path('', include('a.urls')),",
    "    # path('', include('b.urls')),",
    '"""Ví dụ: path(\'\', include(\'c.urls\'))"""',
  ].join('\n'));
  const chiGanThat = JSON.stringify(gan) === JSON.stringify(['a.urls']);
  const batLyDo = lyDoMoCoi.includes(GIA_LY_DO);
  console.log(`tự kiểm: lời gọi tới tuyến không tồn tại → ${batGoi ? 'BẮT ĐƯỢC' : 'BỎ SÓT'}`);
  console.log(`tự kiểm: tuyến không ai gọi               → ${batTuyen ? 'BẮT ĐƯỢC' : 'BỎ SÓT'}`);
  console.log(`tự kiểm: chuỗi trong dòng tiếp nối chú thích → ${boChuThich ? 'BỎ ĐÚNG' : 'ĐẾM OAN'}`);
  console.log(`tự kiểm: lời gọi sau '//' trong URL/regex  → ${giuGoiThat ? 'GIỮ ĐÚNG' : 'NUỐT MẤT'} ${JSON.stringify(thay)}`);
  console.log(`tự kiểm: include trong chú thích/docstring → ${chiGanThat ? 'BỎ ĐÚNG' : 'GẮN OAN'} ${JSON.stringify(gan)}`);
  console.log(`tự kiểm: lý do cho tuyến đã tháo           → ${batLyDo ? 'BẮT ĐƯỢC' : 'BỎ SÓT'}`);
  process.exit(batGoi && batTuyen && boChuThich && giuGoiThat && chiGanThat && batLyDo ? 0 : 1);
}

/* ── 6 · GHI ─────────────────────────────────────────────────────────────── */
fs.mkdirSync(RA, { recursive: true });
fs.writeFileSync(path.join(RA, 'graph.json'), JSON.stringify({
  sinhLuc: new Date().toISOString(),
  nguon: 'scripts/ban_do.mjs',
  nodes: [...nut.values()],
  edges: canh,
}, null, 1));

const dem = (q) => canh.filter((c) => c.quanHe === q).length;
const L = [];
L.push('# Bản đồ hệ thống pe_hsa');
L.push('');
L.push(`Sinh bởi \`scripts/ban_do.mjs\` — tất định, không gọi mô hình. ${nut.size} nút · ${canh.length} cạnh.`);
L.push('');
L.push('| Loại cạnh | Số | Độ tin cậy |');
L.push('|---|---|---|');
L.push(`| trang/tệp frontend → tuyến API | ${dem('goi_api')} | INFERRED (từ chuỗi URL) |`);
L.push(`| tuyến → view Django | ${dem('goi_view')} | EXTRACTED |`);
L.push(`| view → lớp quyền | ${dem('can_quyen')} | EXTRACTED |`);
L.push(`| view → bảng SQL | ${dem('cham_bang')} | INFERRED (từ chuỗi SQL, theo mô-đun) |`);
L.push(`| bảng → bảng (khoá ngoại) | ${dem('khoa_ngoai')} | EXTRACTED |`);
L.push(`| React → hàm JS cũ | ${dem('goi_js_cu')} | EXTRACTED |`);
L.push('');
L.push(`## Frontend gọi mà không khớp tuyến nào (${khongKhop.length})`);
L.push('');
for (const g of khongKhop) L.push(`- \`${g.tho}\` → mẫu \`${g.mau}\` — ${g.tep}:${g.dong}`);
L.push('');
const chuaGiaiThich = khongAiGoi.filter((r) => !r.lyDo);
L.push(`## Tuyến không thấy lời gọi nào phía frontend (${khongAiGoi.length}; ${chuaGiaiThich.length} chưa có lý do)`);
L.push('');
for (const r of khongAiGoi) L.push(`- \`${r.mau}\` → ${r.app}.${r.view}${r.lyDo ? ` — *${r.lyDo}*` : ' — **chưa có lý do**'}`);
L.push('');
L.push(`## Lý do trỏ vào tuyến không còn gắn (${lyDoMoCoi.length})`);
L.push('');
for (const m of lyDoMoCoi) L.push(`- \`${m}\` — xoá dòng ấy khỏi \`KHONG_CAN_NGUOI_GOI\`/\`UNG_VIEN_GO\``);
L.push('');
L.push(`## Tệp urls.py có trên đĩa mà không được gắn từ ${ROOT_URLCONF} (${urlsKhongGan.length})`);
L.push('');
L.push('Tuyến trong các tệp này KHÔNG phục vụ gì — không tính vào bản đồ.');
L.push('');
for (const t of urlsKhongGan) L.push(`- \`${t}\``);
L.push('');
L.push(`## Cầu React → JS cũ gãy (${cauGay.length})`);
L.push('');
for (const c of cauGay) L.push(`- \`${c.ten}\` — ${c.tep}:${c.dong} (không thấy \`function ${c.ten}\` hay \`window.${c.ten} =\` trong static/js)`);
L.push('');
L.push(`## Bảng không view nào chạm tới (${bangKhongAiCham.length})`);
L.push('');
L.push('Không nhất thiết là thừa: bảng có thể chỉ được lệnh quản trị, tín hiệu Django, hay mã ngoài view dùng.');
L.push('');
L.push(bangKhongAiCham.map((b) => `\`${b}\``).join(' · ') || '(không có)');
L.push('');
fs.writeFileSync(path.join(RA, 'BAO_CAO.md'), L.join('\n'));

console.log(`bản đồ: ${nut.size} nút, ${canh.length} cạnh → ${rel(RA)}/graph.json, BAO_CAO.md`);
console.log(`  frontend→API ${dem('goi_api')} · tuyến→view ${dem('goi_view')} · view→quyền ${dem('can_quyen')} · view→bảng ${dem('cham_bang')} · khoá ngoại ${dem('khoa_ngoai')} · React→JS cũ ${dem('goi_js_cu')}`);
console.log(`  gãy: ${khongKhop.length} lời gọi không khớp · ${chuaGiaiThich.length} tuyến không ai gọi chưa có lý do · ${cauGay.length} cầu JS cũ gãy · ${lyDoMoCoi.length} lý do cho tuyến đã tháo`);
if (urlsKhongGan.length) console.log(`  bỏ qua ${urlsKhongGan.length} urls.py không được gắn: ${urlsKhongGan.join(', ')}`);

if (process.argv.includes('--kiem')) {
  const loi = khongKhop.length + chuaGiaiThich.length + cauGay.length + lyDoMoCoi.length;
  process.exitCode = loi ? 1 : 0;
}
