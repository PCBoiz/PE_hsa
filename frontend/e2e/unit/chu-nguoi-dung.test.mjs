/**
 * Unit test — CHỮ NGƯỜI DÙNG NHÌN THẤY không được mang ghi chú lập trình viên.
 *
 * ── VÌ SAO CÓ TỆP NÀY (24/09/2026) ────────────────────────────────────────
 *
 * TopHSA dùng thử và chê "nhiều chữ, màn đầu rối". Đo trong mã: phần lớn chữ
 * thừa KHÔNG phải nội dung mà là ghi chú lập trình viên in thẳng ra màn —
 * ngày tháng, tên người, ký hiệu §, đường dẫn tệp `.py::View` — trái RULES §10.
 * Chúng lọt vì chỗ viết chú thích và chỗ viết câu cho người dùng nằm sát nhau
 * trong cùng một tệp, cùng một giọng, và không cửa kiểm nào phân biệt được hai
 * thứ ấy.
 *
 * ── VÌ SAO KHÔNG REGEX TRÊN CẢ TỆP ───────────────────────────────────────
 *
 * Chú thích mã ĐƯỢC PHÉP (và nên) mang ngày, §, tên tệp — đó là luật §9. Một
 * phép grep sẽ báo oan hàng trăm dòng chú thích; báo oan thì người ta thôi
 * đọc thước. Nên tệp này dùng bộ phân tích TypeScript trong `node_modules`
 * (tất định, không gọi mô hình) và chỉ đọc chuỗi CHẢY TỚI MÀN HÌNH:
 *
 *   · chữ JSX, và biểu thức con của JSX (trừ bên trong `<style>`/`<script>`);
 *   · thuộc tính hiển thị: `title`, `placeholder`, `aria-label`, `alt`,
 *     `label`, `hint`, `chiTiet`, `error` …;
 *   · prop mà component IN RA: `CardHead` viết `{hint}` → mọi `hint=` truyền
 *     cho `CardHead` (lần qua kiểu của props, không đoán theo tên);
 *   · thuộc tính dữ liệu được in: trang viết `{v.nguon}` → mọi `nguon:` gán
 *     cho kiểu ấy; thuộc tính KHÔNG ai in thì không bị đọc;
 *   · lời toast (`useToast()`), `confirm`/`alert`, `new Error(…)` (câu lỗi hiện
 *     qua `catch`), `setX(…)` của state được in, `metadata.title`.
 *
 * Từ mỗi chỗ ấy thước lần NGƯỢC theo giá trị: biến, hằng nhập từ tệp khác,
 * hàm trả chuỗi, `.map`/`.join`, `a ? b : c`, `&&`, `??`, `+`. Chuỗi đứng ở
 * vế SO SÁNH (`s === 'x'`) hay làm đối số cho hàm thư viện thì không hiện ra.
 *
 * KHÔNG bắt được (nói rõ để không ai tưởng thước canh cả): chuỗi đi qua
 * `{...props}`, qua `window`/tầng JS cũ, chữ đến từ API, và prop truyền qua
 * một hàm set không gọi thẳng (`onLoi={setLoi}`).
 *
 * ── THƯỚC PHẢI ĐỎ ĐƯỢC ───────────────────────────────────────────────────
 *
 * Mỗi lượt chạy dựng thêm một tệp ẢO (`src/__tu_kiem__/`, chỉ trong bộ nhớ)
 * gài sẵn vi phạm ở từng đường lần ngược kể trên, và vài chỗ KHÔNG được bắt
 * (chú thích, `className` Tailwind có `::`, CSS trong `<style>`, thuộc tính
 * không ai in, vế so sánh, `hint` đúng 90 ký tự). Thước mù hay thước báo oan
 * đều làm tệp này đỏ — cùng lượt với lượt đo thật, cùng một chương trình.
 *
 * Chạy: node e2e/unit/chu-nguoi-dung.test.mjs            (kiểm)
 *       node e2e/unit/chu-nguoi-dung.test.mjs --liet-ke  (in MỌI chuỗi hiện
 *       ra màn — để kiểm tay bộ quét, không phải để đọc hằng ngày)
 */
import { readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';

const FE = join(dirname(fileURLToPath(import.meta.url)), '..', '..').replace(/\\/g, '/');
const SRC = `${FE}/src/`;
const TEP_MAU = `${SRC}__tu_kiem__/MauViPham.tsx`;
const LIET_KE = process.argv.includes('--liet-ke');

/** Luật cấm trong chuỗi hiển thị. Mỗi luật một lớp ghi chú lập trình viên. */
const LUAT = [
  // Ngày đầy đủ gõ cứng: "Từ 27/08/2026 …", "(anh chốt 01/09/2026)". Ngày
  // do mã tính ra (`${ngay}/…`) không phải chữ gõ cứng nên không khớp.
  { ma: 'ngay', ten: 'ngày gõ cứng dd/mm/20xx', re: /(^|[^\d])\d{1,2}\/\d{1,2}\/20\d\d(?!\d)/ },
  { ma: 'muc', ten: 'ký hiệu §', re: /§/ },
  { ma: 'py', ten: 'tên tệp .py', re: /\.py(?![\p{L}\d_])/u },
  { ma: 'ts', ten: 'tên tệp .ts/.tsx', re: /\.tsx?(?![\p{L}\d_])/u },
  { ma: 'haicham', ten: '"::" (tệp::View)', re: /::/ },
  { ma: 'nguoi', ten: 'tên người "anh Sơn"', re: /(^|[^\p{L}])[Aa]nh Sơn(?![\p{L}])/u },
  { ma: 'quyen', ten: 'permission_classes', re: /permission_classes/ },
  { ma: 'so', ten: 'RULES / PROGRESS', re: /\b(RULES|PROGRESS)\b/ },
  { ma: 'ten_du_an', ten: 'ProgrammingEdu', re: /ProgrammingEdu/ },
  { ma: 'premium', ten: 'Premium', re: /Premium/ },
];

/* `hint` là MỘT dòng phụ dưới tiêu đề. 90 ký tự ≈ một dòng ở khổ máy tính của
   thẻ hẹp nhất; giải thích dài hơn thuộc về `chiTiet` (gập sau "Chi tiết") hay
   bài Hướng dẫn. Chuỗi mẫu `${…}` đếm mỗi chỗ nội suy là MỘT ký tự — tức con
   số là cận dưới của thứ người dùng thấy, thước không báo oan vì một tên lớp
   dài. */
const TRAN_HINT = 90;

/* Ngoại lệ TẠM, theo tệp chứa chuỗi. Mỗi dòng phải có lý do và phải HẾT HẠN:
   ngoại lệ nào không còn vi phạm nào để che thì tệp này đỏ, bắt gỡ nó đi. */
// Hai ngoại lệ tạm (màn Lớp học, huongDan.ts) đã gỡ 24/09/2026 sau khi lead sửa
// hết 5 vi phạm ở đó. Thêm ngoại lệ mới thì ghi lý do + người xử lý như cũ.
const NGOAI_LE_TAM = [];

/** Thuộc tính JSX mà chữ trong đó tới tay người dùng (mắt hoặc trình đọc màn hình). */
const THUOC_TINH_HIEN = new Set([
  'title', 'placeholder', 'aria-label', 'aria-description', 'aria-roledescription',
  'aria-valuetext', 'alt', 'label', 'hint', 'chiTiet', 'error',
]);

/* Phương thức mảng/chuỗi giữ nguyên chữ của đối tượng gọi: `.filter(…)`
   vẫn ra các phần tử ấy, `.trim()` vẫn ra chuỗi ấy. */
const GIU_CHU = new Set([
  'filter', 'slice', 'sort', 'toSorted', 'reverse', 'toReversed', 'find', 'at',
  'trim', 'trimStart', 'trimEnd', 'toUpperCase', 'toLowerCase', 'toLocaleUpperCase',
  'toLocaleLowerCase', 'padStart', 'padEnd', 'normalize', 'concat', 'replace', 'replaceAll',
]);

// ═══ Tệp ẢO tự kiểm ═══════════════════════════════════════════════════════
/* Mỗi chỗ gài mang một thẻ [Kn]. DUONG: phải bị bắt đúng luật. AM: không
   được bắt. Hint 90/91 ký tự dựng bằng mã để biên đúng tuyệt đối. */
const H91 = ('Câu nhắc dài quá ngưỡng một ký tự thì phải bị bắt [K8] ' + 'x'.repeat(200)).slice(0, TRAN_HINT + 1);
const H90 = ('Câu nhắc dài vừa khít ngưỡng thì không được báo [K16] ' + 'x'.repeat(200)).slice(0, TRAN_HINT);
const NOI_DUNG_MAU = `'use client';
import { useState } from 'react';
import { CardHead, useToast } from '@/components/ui';

type Dong = { nhan: string; nguon: string; ghiChu: string };
const DONG: readonly Dong[] = [
  { nhan: 'Việc', nguon: 'mau/views.py [K4]', ghiChu: 'mau/views.py [K12]' },
] as const;
const THE = [
  { nhan: 'Một §1 [K5]' },
  { nhan: 'Hai §2 [K6]', phu: 1 },
];
function nhanTrangThai(s: string) {
  if (s === 'x.py [K17]') return 'Theo RULES [K7]';
  return 'Bình thường';
}
function The({ goiY }: { goiY: string }) {
  return <p>{goiY}</p>;
}
export default function Mau({ s }: { s: string }) {
  // anh Sơn chốt 24/09/2026 — RULES §10, mau.py::X, Premium [K13]
  const [loi, setLoi] = useState<string | null>(null);
  const toast = useToast();
  return (
    <div title="Xem PROGRESS [K1]" className="[&::before]:content-[''] [K14]">
      Theo §12 thì vậy [K2]
      <style>{'a::before { content: "[K15]"; }'}</style>
      <CardHead title="Mẫu" hint=${JSON.stringify(H91)} />
      <CardHead title="Mẫu" hint=${JSON.stringify(H90)} />
      {DONG.map((d) => <span key={d.nhan}>{d.nguon}</span>)}
      {THE.map((t) => <b key={t.nhan}>{t.nhan}</b>)}
      <The goiY="Anh Sơn nói vậy [K3]" />
      <i>{nhanTrangThai(s)}</i>
      {loi && <p role="alert">{loi}</p>}
      <button type="button" onClick={() => { setLoi('Hỏng ở views.py [K9]'); toast('ProgrammingEdu [K10]'); }}>Bấm</button>
      <button type="button" onClick={() => { throw new Error('Lỗi ngày 24/09/2026 [K11]'); }}>Nữa</button>
    </div>
  );
}
`;
const MAU_DUONG = [
  ['K1', 'so', 'thuộc tính title của thẻ HTML'],
  ['K2', 'muc', 'chữ JSX'],
  ['K3', 'nguoi', 'prop mà component tự viết in ra'],
  ['K4', 'py', 'thuộc tính dữ liệu có khai kiểu, được in'],
  ['K5', 'muc', 'mảng KHÔNG khai kiểu — phần tử đầu'],
  ['K6', 'muc', 'mảng KHÔNG khai kiểu — phần tử sau'],
  ['K7', 'so', 'chuỗi hàm trả về'],
  ['K8', 'hint', `hint ${TRAN_HINT + 1} ký tự`],
  ['K9', 'py', 'setState của state được in'],
  ['K10', 'ten_du_an', 'lời toast'],
  ['K11', 'ngay', 'new Error(…) hiện qua catch'],
];
const MAU_AM = [
  ['K12', 'thuộc tính dữ liệu KHÔNG ai in'],
  ['K13', 'chú thích mã'],
  ['K14', '`::` trong className Tailwind'],
  ['K15', '`::` trong CSS của <style>'],
  ['K16', `hint đúng ${TRAN_HINT} ký tự`],
  ['K17', 'chuỗi ở vế so sánh'],
];

// ═══ Dựng chương trình TypeScript ═════════════════════════════════════════
function* tepMa(thuMuc) {
  for (const e of readdirSync(thuMuc, { withFileTypes: true })) {
    const p = `${thuMuc}/${e.name}`;
    if (e.isDirectory()) yield* tepMa(p);
    else if (/\.tsx?$/.test(e.name) && !/\.d\.ts$/.test(e.name)) yield p;
  }
}

const cfg = ts.readConfigFile(`${FE}/tsconfig.json`, ts.sys.readFile);
const phan = ts.parseJsonConfigFileContent(cfg.config, ts.sys, FE);
const opts = { ...phan.options, incremental: false, noEmit: true };
const host = ts.createCompilerHost(opts, true);
const goc = { gsf: host.getSourceFile, fe: host.fileExists, rf: host.readFile };
host.getSourceFile = (f, ...r) => (f === TEP_MAU
  ? ts.createSourceFile(f, NOI_DUNG_MAU, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX)
  : goc.gsf.call(host, f, ...r));
host.fileExists = (f) => f === TEP_MAU || goc.fe.call(host, f);
host.readFile = (f) => (f === TEP_MAU ? NOI_DUNG_MAU : goc.rf.call(host, f));

const TEP_THAT = [...tepMa(`${FE}/src`)];
const program = ts.createProgram({ rootNames: [...TEP_THAT, TEP_MAU], options: opts, host });
const checker = program.getTypeChecker();

const tuongDoi = (f) => f.replace(/\\/g, '/').slice(FE.length + 1);
/** Khai báo nằm trong mã CỦA DỰ ÁN (không phải node_modules hay lib.d.ts). */
const laDuAn = (node) => node.getSourceFile().fileName.replace(/\\/g, '/').toLowerCase()
  .startsWith(SRC.toLowerCase());
const cacTep = program.getSourceFiles().filter((sf) => laDuAn(sf));

// ═══ Chỉ mục: ai GÁN vào thuộc tính nào, ai GỌI hàm nào ═══════════════════
/* Hai tầng, vì hỏi bộ kiểm kiểu về MỌI thuộc tính và MỌI lời gọi của chương
   trình tốn 15 giây (đo 24/09/2026 — gần bằng một lượt `tsc` trọn). Tầng một
   chỉ đọc cú pháp: gom ứng viên theo TÊN. Tầng hai hỏi kiểu cho đúng những ứng
   viên cùng tên với khai báo đang lần tới — thường vài chục nút chứ không phải
   hàng nghìn. Tên chỉ để lọc; phán quyết vẫn là của bộ kiểm kiểu. */
/** tên thuộc tính → phép gán vào nó (thuộc tính đối tượng, thuộc tính JSX). */
const GAN_TEN = new Map();
/** tên hàm được gọi (định danh cuối của callee) → các lời gọi. */
const GOI_TEN = new Map();
const them = (m, k, v) => { if (!m.has(k)) m.set(k, []); m.get(k).push(v); };

const tenCua = (name) => (name && (ts.isIdentifier(name) || ts.isStringLiteral(name)
  || ts.isPrivateIdentifier(name)) ? name.text : undefined);

/** Tên của khai báo hàm/biến/thuộc tính/phần tử rã — để tra ứng viên. */
const tenKhaiBao = (d) => tenCua(d.name);

const NHO_GAN = new Map();
/** Khai báo thuộc tính mà một phép gán (ứng viên) nhắm vào — hỏi kiểu một lần. */
function dichCuaPhepGan(g) {
  if (!NHO_GAN.has(g)) {
    const khai = ts.isJsxAttribute(g)
      ? khaiBaoThuocTinh(checker.getContextualType(g.parent), g.name.getText())
      : khaiBaoThuocTinh(checker.getContextualType(g.parent), tenCua(g.name));
    NHO_GAN.set(g, new Set(khai.filter((d) => d !== g)));
  }
  return NHO_GAN.get(g);
}
/** Mọi phép gán vào khai báo thuộc tính `d`. */
function ganVao(d) {
  const ten = tenKhaiBao(d);
  return (GAN_TEN.get(ten) ?? []).filter((g) => dichCuaPhepGan(g).has(d));
}

const NHO_GOI = new Map();
/** Mọi lời gọi tới khai báo `k` (hàm, biến giữ hàm, hàm set của useState). */
function goiToi(k) {
  const ten = tenKhaiBao(k);
  return (GOI_TEN.get(ten) ?? []).filter((c) => {
    if (!NHO_GOI.has(c)) NHO_GOI.set(c, new Set(khaiBaoHam(c.expression)));
    return NHO_GOI.get(c).has(k);
  });
}

/** Khai báo của thuộc tính `ten` trên kiểu `kieu` (xé union, bỏ undefined). */
function khaiBaoThuocTinh(kieu, ten) {
  if (!kieu || !ten) return [];
  const t = checker.getNonNullableType(kieu);
  const ra = [];
  for (const c of t.isUnion() ? t.types : [t]) {
    for (const d of c.getProperty(ten)?.declarations ?? []) ra.push(d);
  }
  return ra;
}

function kyHieuGoc(s) {
  if (s && s.flags & ts.SymbolFlags.Alias) {
    try { return checker.getAliasedSymbol(s); } catch { return s; }
  }
  return s;
}

/** Khai báo của hàm được gọi ở `callee` — chỉ trong mã dự án. */
function khaiBaoHam(callee) {
  const ten = ts.isPropertyAccessExpression(callee) ? callee.name : callee;
  const s = kyHieuGoc(checker.getSymbolAtLocation(ten));
  return (s?.declarations ?? []).filter(laDuAn);
}

/** Khoá của một hàm khi tra lời gọi: chính khai báo, hoặc biến/thuộc tính giữ nó. */
function khoaHam(f) {
  if (ts.isFunctionDeclaration(f) || ts.isMethodDeclaration(f)) return f;
  if ((ts.isArrowFunction(f) || ts.isFunctionExpression(f))
    && (ts.isVariableDeclaration(f.parent) || ts.isPropertyAssignment(f.parent))) return f.parent;
  return undefined;
}

const laUseToast = (d) => ts.isVariableDeclaration(d) && d.initializer
  && ts.isCallExpression(d.initializer) && d.initializer.expression.getText() === 'useToast';

/** Thẻ JSX gần nhất bọc `n` có phải `<style>`/`<script>` (chữ ở đó là mã). */
function trongMa(n) {
  for (let p = n.parent; p; p = p.parent) {
    if (ts.isJsxElement(p)) return /^(style|script)$/.test(p.openingElement.tagName.getText());
    if (ts.isJsxFragment(p)) return false;
  }
  return false;
}

/** Chỗ chữ ĐI RA MÀN: { bt: nút, cach: mô tả } */
const GOC_HIEN = [];
/** Giá trị của mọi thuộc tính `hint=` — cho luật độ dài. */
const GOC_HINT = [];

function giaTriThuocTinh(attr) {
  const i = attr.initializer;
  if (!i) return undefined;
  if (ts.isStringLiteral(i)) return i;
  if (ts.isJsxExpression(i)) return i.expression;
  return undefined;
}

/** Tên các biến giữ `useToast()` — lời gọi tới chúng là lời toast. */
const TEN_TOAST = new Set();

function lapChiMuc(n) {
  if ((ts.isPropertyAssignment(n) || ts.isShorthandPropertyAssignment(n))
    && ts.isObjectLiteralExpression(n.parent)) {
    them(GAN_TEN, tenCua(n.name), n);
  } else if (ts.isJsxAttribute(n)) {
    const ten = n.name.getText();
    const bt = giaTriThuocTinh(n);
    if (bt) {
      them(GAN_TEN, ten, n);
      if (THUOC_TINH_HIEN.has(ten)) GOC_HIEN.push({ bt, cach: `thuộc tính ${ten}` });
      if (ten === 'hint') GOC_HINT.push(bt);
    }
  } else if (ts.isCallExpression(n)) {
    const c = n.expression;
    const ten = ts.isPropertyAccessExpression(c) ? c.name.text : ts.isIdentifier(c) ? c.text : undefined;
    if (ten) them(GOI_TEN, ten, n);
    if (/^(window\.)?(confirm|alert|prompt)$/.test(c.getText()) && n.arguments[0]) {
      GOC_HIEN.push({ bt: n.arguments[0], cach: c.getText() });
    }
  } else if (ts.isVariableDeclaration(n) && laUseToast(n) && ts.isIdentifier(n.name)) {
    TEN_TOAST.add(n.name.text);
  } else if (ts.isNewExpression(n)) {
    if (n.expression.getText() === 'Error' && n.arguments?.[0]) {
      GOC_HIEN.push({ bt: n.arguments[0], cach: 'new Error (hiện qua catch)' });
    }
  } else if (ts.isJsxText(n)) {
    if (!n.containsOnlyTriviaWhiteSpaces && !trongMa(n)) GOC_HIEN.push({ bt: n, cach: 'chữ JSX' });
  } else if (ts.isJsxExpression(n) && n.expression
    && (ts.isJsxElement(n.parent) || ts.isJsxFragment(n.parent))) {
    if (!trongMa(n)) GOC_HIEN.push({ bt: n.expression, cach: 'biểu thức JSX' });
  } else if (ts.isVariableDeclaration(n) && ts.isIdentifier(n.name) && n.name.text === 'metadata'
    && n.initializer && ts.isObjectLiteralExpression(n.initializer)) {
    for (const p of n.initializer.properties) {
      if (ts.isPropertyAssignment(p) && /^(title|description)$/.test(tenCua(p.name) ?? '')) {
        GOC_HIEN.push({ bt: p.initializer, cach: 'metadata' });
      }
    }
  } else if (ts.isBinaryExpression(n) && n.operatorToken.kind === ts.SyntaxKind.EqualsToken
    && n.left.getText() === 'document.title') {
    GOC_HIEN.push({ bt: n.right, cach: 'document.title' });
  }
  ts.forEachChild(n, lapChiMuc);
}
for (const sf of cacTep) lapChiMuc(sf);
// Lời toast: gọi đúng biến giữ `useToast()` (hỏi kiểu — tên `toast` chỉ để lọc).
for (const ten of TEN_TOAST) {
  for (const c of GOI_TEN.get(ten) ?? []) {
    if (c.arguments[0] && khaiBaoHam(c.expression).some(laUseToast)) {
      GOC_HIEN.push({ bt: c.arguments[0], cach: 'toast' });
    }
  }
}

// ═══ Lần ngược: một biểu thức có thể HIỆN RA những chuỗi nào ═════════════
/** Trả về các nút lá (chuỗi, chuỗi mẫu, chữ JSX) mà `n` có thể hiện ra. */
function laCua(goc) {
  const ra = [];
  const daQua = new Set();

  const traVe = (f) => {
    if (!f) return;
    if (ts.isArrowFunction(f) && !ts.isBlock(f.body)) { la(f.body); return; }
    if (!f.body) return;
    const duyet = (x) => {
      if (ts.isReturnStatement(x)) { if (x.expression) la(x.expression); return; }
      if (ts.isFunctionLike(x)) return; // lời return của hàm LỒNG không phải của f
      ts.forEachChild(x, duyet);
    };
    ts.forEachChild(f.body, duyet);
  };

  const hamCua = (d) => {
    if (ts.isFunctionDeclaration(d) || ts.isMethodDeclaration(d)) return d;
    const init = (ts.isVariableDeclaration(d) || ts.isPropertyAssignment(d)) ? d.initializer : undefined;
    if (init && (ts.isArrowFunction(init) || ts.isFunctionExpression(init))) return init;
    return undefined;
  };

  const theoKhaiBaoThuocTinh = (d) => {
    if (ts.isPropertyAssignment(d)) {
      la(d.initializer);
      // Mảng không khai kiểu: TS gộp phần tử, nhưng lần cả anh em cho chắc.
      const obj = d.parent;
      if (ts.isArrayLiteralExpression(obj.parent)) {
        for (const e of obj.parent.elements) {
          if (!ts.isObjectLiteralExpression(e)) continue;
          for (const p of e.properties) {
            if (ts.isPropertyAssignment(p) && tenCua(p.name) === tenCua(d.name)) la(p.initializer);
          }
        }
      }
    } else if (ts.isShorthandPropertyAssignment(d)) {
      theoKyHieu(checker.getShorthandAssignmentValueSymbol(d));
    } else if (ts.isPropertySignature(d) || ts.isPropertyDeclaration(d)) {
      if (d.initializer) la(d.initializer);
    } else if (ts.isGetAccessorDeclaration(d)) {
      traVe(d);
    }
    for (const g of ganVao(d)) {
      if (ts.isShorthandPropertyAssignment(g)) theoKyHieu(checker.getShorthandAssignmentValueSymbol(g));
      else if (ts.isPropertyAssignment(g)) la(g.initializer);
      else la(giaTriThuocTinh(g));
    }
  };

  const theoPhanTuRaHoa = (d) => {
    const mau = d.parent;
    if (ts.isObjectBindingPattern(mau)) {
      if (d.initializer) la(d.initializer); // giá trị mặc định
      const ten = tenCua(d.propertyName ?? d.name);
      for (const k of khaiBaoThuocTinh(checker.getTypeAtLocation(mau.parent), ten)) {
        if (laDuAn(k)) theoKhaiBaoThuocTinh(k);
      }
    } else if (ts.isArrayBindingPattern(mau)) {
      // const [loi, setLoi] = useState(…): chữ là giá trị đầu + mọi lời setLoi(…)
      const khai = mau.parent;
      const init = ts.isVariableDeclaration(khai) ? khai.initializer : undefined;
      if (init && ts.isCallExpression(init) && /(^|\.)useState$/.test(init.expression.getText())
        && mau.elements.indexOf(d) === 0) {
        if (init.arguments[0]) la(init.arguments[0]);
        const set = mau.elements[1];
        for (const goi of set ? goiToi(set) : []) {
          const a = goi.arguments[0];
          if (a && (ts.isArrowFunction(a) || ts.isFunctionExpression(a))) traVe(a);
          else if (a) la(a);
        }
      }
    }
  };

  /* Bảng tra khai kiểu chỉ mục (`Record<number, string>`) không có thuộc
     tính để lần theo — đọc thẳng các ô của khối khởi tạo. */
  const moiGiaTri = (e) => {
    const ten = ts.isPropertyAccessExpression(e) ? e.name : e;
    for (const d of kyHieuGoc(checker.getSymbolAtLocation(ten))?.declarations ?? []) {
      if (!laDuAn(d) || !ts.isVariableDeclaration(d) || !d.initializer) continue;
      let init = d.initializer;
      while (ts.isAsExpression(init) || ts.isSatisfiesExpression(init) || ts.isParenthesizedExpression(init)) {
        init = init.expression;
      }
      if (ts.isObjectLiteralExpression(init)) {
        for (const p of init.properties) if (ts.isPropertyAssignment(p)) la(p.initializer);
      } else if (ts.isArrayLiteralExpression(init)) {
        init.elements.forEach(la);
      }
    }
  };

  const theoThamSo = (p) => {
    const f = p.parent;
    const k = khoaHam(f);
    const i = f.parameters.indexOf(p);
    for (const goi of k ? goiToi(k) : []) if (goi.arguments[i]) la(goi.arguments[i]);
  };

  function theoKyHieu(s) {
    s = kyHieuGoc(s);
    for (const d of s?.declarations ?? []) {
      if (!laDuAn(d)) continue;
      if (ts.isVariableDeclaration(d)) {
        if (d.initializer) la(d.initializer);
      } else if (ts.isBindingElement(d)) {
        theoPhanTuRaHoa(d);
      } else if (ts.isParameter(d)) {
        theoThamSo(d);
      } else if (ts.isEnumMember(d)) {
        if (d.initializer) la(d.initializer);
      } else {
        theoKhaiBaoThuocTinh(d);
      }
    }
  }

  function goiHam(n) {
    const c = n.expression;
    if (ts.isPropertyAccessExpression(c)) {
      const ten = c.name.text;
      if (ten === 'join') { if (n.arguments[0]) la(n.arguments[0]); la(c.expression); return; }
      if (ten === 'map' || ten === 'flatMap') {
        const cb = n.arguments[0];
        if (cb && (ts.isArrowFunction(cb) || ts.isFunctionExpression(cb))) traVe(cb);
        else if (cb) for (const d of khaiBaoHam(cb)) traVe(hamCua(d));
        return;
      }
      if (GIU_CHU.has(ten)) {
        la(c.expression);
        if (ten === 'concat') n.arguments.forEach(la);
        if ((ten === 'replace' || ten === 'replaceAll') && n.arguments[1]) la(n.arguments[1]);
        return;
      }
    } else if (ts.isIdentifier(c) && c.text === 'String') {
      if (n.arguments[0]) la(n.arguments[0]);
      return;
    }
    for (const d of khaiBaoHam(c)) traVe(hamCua(d));
  }

  function la(n) {
    if (!n || daQua.has(n)) return;
    daQua.add(n);
    if (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n) || ts.isJsxText(n)) {
      ra.push(n);
    } else if (ts.isTemplateExpression(n)) {
      ra.push(n);
      for (const sp of n.templateSpans) la(sp.expression);
    } else if (ts.isParenthesizedExpression(n) || ts.isAsExpression(n) || ts.isNonNullExpression(n)
      || ts.isSatisfiesExpression(n) || ts.isTypeAssertionExpression(n) || ts.isAwaitExpression(n)
      || ts.isSpreadElement(n)) {
      la(n.expression);
    } else if (ts.isConditionalExpression(n)) {
      la(n.whenTrue); la(n.whenFalse);
    } else if (ts.isBinaryExpression(n)) {
      const op = n.operatorToken.kind;
      const K = ts.SyntaxKind;
      if (op === K.AmpersandAmpersandToken || op === K.EqualsToken) la(n.right);
      else if (op === K.BarBarToken || op === K.QuestionQuestionToken || op === K.PlusToken) {
        la(n.left); la(n.right);
      }
      // so sánh, số học khác: ra boolean/số, không ra chữ
    } else if (ts.isArrayLiteralExpression(n)) {
      n.elements.forEach(la);
    } else if (ts.isIdentifier(n)) {
      theoKyHieu(checker.getSymbolAtLocation(n));
    } else if (ts.isPropertyAccessExpression(n)) {
      theoKyHieu(checker.getSymbolAtLocation(n.name));
    } else if (ts.isElementAccessExpression(n)) {
      if (ts.isStringLiteralLike(n.argumentExpression)) {
        theoKyHieu(checker.getSymbolAtLocation(n.argumentExpression));
      } else {
        // BANG[khoa] với khoá động: không biết ô nào, nên mọi ô của BANG.
        for (const p of checker.getTypeAtLocation(n.expression).getProperties()) {
          for (const d of p.declarations ?? []) if (laDuAn(d)) theoKhaiBaoThuocTinh(d);
        }
        moiGiaTri(n.expression);
      }
    } else if (ts.isCallExpression(n)) {
      goiHam(n);
    }
    // JSX lồng, đối tượng, hàm, số: không phải chữ (JSX lồng có lượt quét riêng)
  }

  la(goc);
  return ra;
}

// ═══ Đo ═══════════════════════════════════════════════════════════════════
/** Chữ người dùng thấy của một nút lá; `${…}` thành "…". */
function chuCua(n) {
  if (ts.isJsxText(n)) return n.text.replace(/\s+/g, ' ').trim();
  if (ts.isTemplateExpression(n)) {
    return n.head.text + n.templateSpans.map((s) => `…${s.literal.text}`).join('');
  }
  return n.text;
}
function viTri(n) {
  const sf = n.getSourceFile();
  return { tep: tuongDoi(sf.fileName), dong: sf.getLineAndCharacterOfPosition(n.getStart(sf)).line + 1 };
}

/** lá → { n, cach } (một lá có thể tới từ nhiều gốc — giữ gốc đầu). */
const LA_HIEN = new Map();
for (const { bt, cach } of GOC_HIEN) {
  for (const n of laCua(bt)) if (!LA_HIEN.has(n)) LA_HIEN.set(n, cach);
}
const LA_HINT = new Set();
for (const bt of GOC_HINT) for (const n of laCua(bt)) LA_HINT.add(n);

const viPham = []; // { ma, tep, dong, chu, cach }
for (const [n, cach] of LA_HIEN) {
  const chu = chuCua(n);
  if (!chu) continue;
  for (const l of LUAT) {
    if (l.re.test(chu)) viPham.push({ ma: l.ma, ...viTri(n), chu, cach });
  }
}
let tongHint = 0;
let soHint = 0;
let hintNgoaiLe = 0;
for (const n of LA_HINT) {
  const { tep } = viTri(n);
  if (tep.startsWith('src/__tu_kiem__/')) continue;
  const dai = [...chuCua(n)].length;
  soHint += 1;
  tongHint += dai;
  if (NGOAI_LE_TAM.some((e) => tep.startsWith(e.tienTo))) hintNgoaiLe += dai;
}
for (const n of LA_HINT) {
  const chu = chuCua(n);
  const dai = [...chu].length;
  if (dai > TRAN_HINT) viPham.push({ ma: 'hint', ...viTri(n), chu, cach: `hint ${dai} ký tự` });
}

const laMau = (v) => v.tep.startsWith('src/__tu_kiem__/');
const ngoaiLeCua = (v) => NGOAI_LE_TAM.find((e) => v.tep.startsWith(e.tienTo));
const THAT = viPham.filter((v) => !laMau(v));
const CHAN = THAT.filter((v) => !ngoaiLeCua(v));
const CHE = THAT.filter((v) => ngoaiLeCua(v));
const MAU = viPham.filter(laMau);

// ═══ In ═══════════════════════════════════════════════════════════════════
let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${ten}${ok || !ct ? '' : `\n${ct}`}`);
  if (!ok) loi += 1;
};

const laThat = [...LA_HIEN.keys()].filter((n) => !viTri(n).tep.startsWith('src/__tu_kiem__/'));
console.log(`\nQuét ${TEP_THAT.length} tệp · ${GOC_HIEN.length} chỗ chữ ra màn · ${laThat.length} chuỗi hiển thị`
  + ` · ${soHint} chuỗi hint, tổng ${tongHint.toLocaleString('vi-VN')} ký tự`
  + ` (${hintNgoaiLe.toLocaleString('vi-VN')} ở tệp ngoại lệ tạm).\n`);

if (LIET_KE) {
  const ds = laThat.map((n) => ({ ...viTri(n), chu: chuCua(n), cach: LA_HIEN.get(n) }))
    .sort((a, b) => a.tep.localeCompare(b.tep) || a.dong - b.dong);
  for (const d of ds) console.log(`${d.tep}:${d.dong}  [${d.cach}]  ${d.chu.slice(0, 140)}`);
  console.log('');
}

const bang = [...LUAT, { ma: 'hint', ten: `hint > ${TRAN_HINT} ký tự` }];
console.log('  luật                           vi phạm   ngoại lệ tạm');
for (const l of bang) {
  const a = CHAN.filter((v) => v.ma === l.ma).length;
  const b = CHE.filter((v) => v.ma === l.ma).length;
  console.log(`  ${l.ten.padEnd(30)} ${String(a).padStart(7)}   ${String(b).padStart(12)}`);
}
console.log(`  ${'TỔNG'.padEnd(30)} ${String(CHAN.length).padStart(7)}   ${String(CHE.length).padStart(12)}\n`);

// Thước không mù: đủ tệp, đủ chữ.
check('quét đủ tệp (đường dẫn đúng chưa?)', TEP_THAT.length >= 100, String(TEP_THAT.length));
check('thấy đủ chữ trên màn (bộ lần ngược không chết)', laThat.length >= 1000, String(laThat.length));

// Thước đỏ được — và không báo oan.
for (const [the, ma, moTa] of MAU_DUONG) {
  check(`thước bắt được: ${moTa} [${the}]`,
    MAU.some((v) => v.ma === ma && v.chu.includes(`[${the}]`)),
    `      không thấy vi phạm "${ma}" mang [${the}] trong tệp mẫu`);
}
for (const [the, moTa] of MAU_AM) {
  const oan = MAU.filter((v) => v.chu.includes(`[${the}]`));
  check(`thước không bắt oan: ${moTa} [${the}]`, oan.length === 0,
    oan.map((v) => `      ${v.ma}: ${v.chu.slice(0, 100)}`).join('\n'));
}

// Hiện trạng.
const theoLuat = (ma) => CHAN.filter((v) => v.ma === ma);
for (const l of bang) {
  const ds = theoLuat(l.ma);
  check(`không chuỗi hiển thị nào vi phạm: ${l.ten}`, ds.length === 0,
    ds.map((v) => `      ${v.tep}:${v.dong}  [${v.cach}]  ${v.chu.slice(0, 120)}`).join('\n'));
}

// Ngoại lệ phải hết hạn. In ra những gì đang được che — người giữ tệp ấy cần
// danh sách để sửa, và che im lặng thì không ai biết còn nợ bao nhiêu.
for (const e of NGOAI_LE_TAM) {
  const ds = CHE.filter((v) => v.tep.startsWith(e.tienTo));
  check(`ngoại lệ tạm "${e.tienTo}" còn che ${ds.length} vi phạm (${e.lyDo})`, ds.length > 0,
    '      không còn vi phạm nào ở đây — GỠ dòng này khỏi NGOAI_LE_TAM');
  for (const v of ds) console.log(`      · ${v.tep}:${v.dong}  ${v.ma}  ${v.chu.slice(0, 100)}`);
}

console.log(loi === 0
  ? '\nOK — chữ trên màn không mang ghi chú lập trình viên, và thước còn nhạy'
  : `\n${loi} lỗi`);
process.exitCode = loi === 0 ? 0 : 1;
