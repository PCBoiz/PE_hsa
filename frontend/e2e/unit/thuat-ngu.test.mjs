/**
 * Unit test — MỘT KHÁI NIỆM MỘT TÊN trong chữ người dùng đọc.
 *
 * ── VÌ SAO CÓ TỆP NÀY (26/09/2026) ────────────────────────────────────────
 *
 * Chị phụ trách bên TopHSA dùng thử và nhắn 23/09: sản phẩm gọi cùng một thứ
 * bằng ba tên. Đề HSA có ba phần, và trong mã chúng được gọi là "hợp phần"
 * (dashboard, tờ phụ huynh), "tổ hợp" (lộ trình), "khoá học" (trang khoá).
 * Chị chốt MỘT tên: **Môn học**. Kèm theo: bỏ chữ "Mọi …" đứng đầu lựa chọn
 * trong ô lọc ("Mọi lớp" → "Tất cả lớp") — "có thể bỏ chữ *mọi* cho gọn".
 *
 * Đổi một lượt thì dễ; giữ cho nó không bò về mới khó. Chuỗi "hợp phần" đã bò
 * về một lần: 24/09 lead sửa ô lọc ở màn Tài khoản, mà màn Nhật ký vẫn còn
 * "Mọi hành động" vì không ai grep lại. Nên luật ấy phải là một cửa kiểm.
 *
 * ── CHỈ ĐỌC CHUỖI, KHÔNG ĐỌC CHÚ THÍCH ───────────────────────────────────
 *
 * Chú thích mã ĐƯỢC PHÉP nói "hợp phần": nó kể lịch sử ("khối này từng gọi là
 * hợp phần"), và cấm chú thích thì thước báo oan hàng chục dòng — báo oan thì
 * người ta thôi đọc thước. Nên tệp này dựng cây cú pháp bằng bộ phân tích
 * TypeScript trong `node_modules` (tất định, không gọi mô hình) và chỉ soi:
 *
 *   · chuỗi (`'…'`, `"…"`), phần chữ của chuỗi mẫu (`` `…${x}…` ``);
 *   · chữ JSX (`<p>Chọn một môn học</p>`).
 *
 * Chú thích `//`, `/* *\/` và `{/* *\/}` KHÔNG phải nút nào trong cây, nên
 * chúng không bao giờ bị đọc. Đường dẫn `import`/`require` bị bỏ (nó là tên
 * tệp, không phải câu cho người dùng) — `BaHopPhan.tsx` là tên component.
 *
 * Thước này KHÔNG canh: chữ đến từ CSDL hoặc từ API (tên khoá học nằm trong
 * bảng `courses` — đổi nó là một mục lược đồ, xem §72), và chữ trong tệp `.py`.
 *
 * ── HAI LUẬT ──────────────────────────────────────────────────────────────
 *
 *   1. `hop_phan` — chuỗi hiển thị không được chứa "hợp phần" (không phân biệt
 *      hoa thường, dấu cách nào cũng tính).
 *   2. `moi_lua_chon` — chữ trong `<option>` không được bắt đầu bằng "Mọi ".
 *      Chỉ `<option>`: câu văn "Mọi buổi đã dạy đều được điểm danh" là tiếng
 *      Việt bình thường, không phải nhãn lọc.
 *
 * "Tổ hợp" KHÔNG thành luật máy: trong Toán nó là thuật ngữ đúng ("tổ hợp –
 * chỉnh hợp", `lessons/minh_hoa/hsa_quantitative.py`), cấm cả chuỗi thì thước
 * bắt oan nội dung bài học. Chỗ "tổ hợp" nghĩa là ba phần của đề đã sửa tay
 * 26/09 và ghi trong `docs/agent/BAO_CAO_GOP_Y.md`.
 *
 * ── THƯỚC PHẢI ĐỎ ĐƯỢC ───────────────────────────────────────────────────
 *
 * Mỗi lượt chạy đọc thêm hai tệp ẢO (chỉ trong bộ nhớ): một tệp gài sẵn vi
 * phạm ở từng đường (chuỗi thường, chuỗi mẫu, chữ JSX, `<option>`, tệp `.js`
 * tầng cũ) và các chỗ KHÔNG được bắt (chú thích, đường dẫn import, câu văn có
 * chữ "Mọi" ngoài `<option>`). Thước mù hay thước báo oan đều làm tệp này đỏ,
 * trong cùng lượt với lượt đo thật.
 *
 * Chạy: node e2e/unit/thuat-ngu.test.mjs
 */
import { readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';

const FE = join(dirname(fileURLToPath(import.meta.url)), '..', '..').replace(/\\/g, '/');

/** Hai luật. `re` chạy trên chữ người dùng thấy; `chiOption` = chỉ soi `<option>`. */
const LUAT = [
  { ma: 'hop_phan', ten: '"hợp phần" (phải là "môn học")', re: /hợp\s+phần/iu, chiOption: false },
  { ma: 'moi_lua_chon', ten: 'lựa chọn mở đầu "Mọi " (phải là "Tất cả")', re: /^Mọi\s/u, chiOption: true },
];

/* Thư mục quét. Tầng JS cũ vào luôn: màn Lộ trình và Trang của tôi cũ vẫn in
   "Hợp phần HSA" ra màn, và tầng ấy chỉ được CO nên không ai dời nó sớm. */
const THU_MUC = [`${FE}/src`, `${FE}/public/static/js`];
const DUOI = /\.(tsx?|mjs|js)$/;
/* Tệp mẫu tự kiểm của thước khác — chúng CỐ Ý mang chuỗi xấu. */
const BO_QUA = /\/__tu_kiem__\//;

function* tepMa(thuMuc) {
  for (const e of readdirSync(thuMuc, { withFileTypes: true })) {
    const p = `${thuMuc}/${e.name}`;
    if (e.isDirectory()) yield* tepMa(p);
    else if (DUOI.test(e.name) && !BO_QUA.test(p)) yield p;
  }
}

const kieuTep = (ten) => (ten.endsWith('.tsx') ? ts.ScriptKind.TSX
  : ten.endsWith('.ts') ? ts.ScriptKind.TS : ts.ScriptKind.JS);

/** Đường dẫn module (`import x from './y'`) — tên tệp, không phải câu cho người đọc. */
function laDuongDanModule(n) {
  const c = n.parent;
  if (!c) return false;
  if (ts.isImportDeclaration(c) || ts.isExportDeclaration(c)) return c.moduleSpecifier === n;
  if (ts.isExternalModuleReference(c) || ts.isImportTypeNode(c)) return true;
  if (ts.isCallExpression(c) && c.arguments[0] === n) {
    const f = c.expression.getText(n.getSourceFile());
    return f === 'require' || f === 'import';
  }
  return false;
}

/** Thẻ JSX bọc `n` gần nhất có tên `ten` (so chữ thường). */
function trongThe(n, ten) {
  for (let p = n.parent; p; p = p.parent) {
    if (ts.isJsxElement(p)) {
      const t = p.openingElement.tagName.getText(p.getSourceFile()).toLowerCase();
      if (t === ten) return true;
    }
  }
  return false;
}

/**
 * Mọi chuỗi hiển thị của một tệp: { chu, dong, trongOption }.
 * `nguon` là `ts.SourceFile` đã dựng (thật hay ảo, cùng một đường đi).
 */
function chuoiHienThi(nguon) {
  const ra = [];
  const themChu = (n, chu, trongOption) => {
    if (!chu.trim()) return;
    const { line } = nguon.getLineAndCharacterOfPosition(n.getStart(nguon));
    ra.push({ chu, dong: line + 1, trongOption });
  };
  const di = (n) => {
    if (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n)) {
      if (!laDuongDanModule(n)) themChu(n, n.text, trongThe(n, 'option'));
    } else if (ts.isTemplateExpression(n)) {
      /* Chuỗi mẫu: chỉ phần CHỮ (head + mỗi middle/tail). Chỗ `${…}` bỏ —
         giá trị của nó do mã tính ra, không phải chữ gõ cứng ở đây. */
      const op = trongThe(n, 'option');
      themChu(n, n.head.text, op);
      for (const s of n.templateSpans) themChu(s.literal, s.literal.text, op);
    } else if (ts.isJsxText(n)) {
      themChu(n, n.text, trongThe(n, 'option'));
    }
    ts.forEachChild(n, di);
  };
  di(nguon);
  return ra;
}

/** Vi phạm của một tệp: { ma, tep, dong, chu }. */
function viPhamCua(tep, ma, ten) {
  const nguon = ts.createSourceFile(tep, ma, ts.ScriptTarget.Latest, true, kieuTep(ten ?? tep));
  const ra = [];
  for (const c of chuoiHienThi(nguon)) {
    for (const l of LUAT) {
      if (l.chiOption && !c.trongOption) continue;
      /* Chữ JSX hay chuỗi mẫu có thể mang dấu cách/xuống dòng ở đầu — luật
         "Mọi " nhắm vào chữ NGƯỜI ĐỌC thấy, nên so trên bản đã cắt lề. */
      if (l.re.test(c.chu.trim())) ra.push({ ma: l.ma, tep, dong: c.dong, chu: c.chu.trim().slice(0, 100) });
    }
  }
  return ra;
}

// ═══ Tệp ẢO tự kiểm ════════════════════════════════════════════════════════
/* Mỗi chỗ gài mang một thẻ [Kn]: DUONG phải bị bắt, AM không được bắt. */
const MAU_TSX = `
// Chú thích nói "hợp phần" thì KHÔNG bị bắt [K10].
/* Khối này từng tên "Hợp phần HSA" [K11]. */
import { Ba } from './BaHopPhan';
const T = 'Tiến độ theo hợp phần [K1]';
const M = \`Ba hợp phần [K2] của \${ten}\`;
const SO_SANH = 'hợp phần';
export default function Mau({ ten }: { ten: string }) {
  return (
    <div>
      {/* Chú thích JSX: hợp phần [K12] */}
      <p>Chọn một hợp phần [K3] để mở bài học.</p>
      <p>Mọi buổi đã dạy đều được điểm danh [K13].</p>
      <select>
        <option value="">Mọi hành động [K4]</option>
        <option value="">Tất cả [K14]</option>
        <option value="">{\`Mọi lớp [K5]\`}</option>
      </select>
      <span title="Hợp Phần [K6] thứ 3">{T}{M}{SO_SANH}</span>
    </div>
  );
}
`;
const MAU_JS = `
// Tầng cũ: chú thích nói hợp phần [K15] thì bỏ qua.
var L = [{ group: "Hợp phần HSA [K7]" }];
var H = '<option value="">Mọi lớp [K16]</option>';
function ve() { return '<div>Chọn một hợp phần [K8] HSA</div>' + \`ba hợp phần [K9]\`; }
`;
/* [K16] nằm trong CHUỖI HTML của tầng cũ: cây cú pháp không thấy `<option>`
   nào, nên luật "Mọi " không bắt — nói rõ ra để không ai tưởng thước canh cả.
   Tầng cũ chỉ được CO, và ô lọc duy nhất của nó không có chữ "Mọi". */
const DUONG = ['K1', 'K2', 'K3', 'K4', 'K5', 'K6', 'K7', 'K8', 'K9'];
const AM = ['K10', 'K11', 'K12', 'K13', 'K14', 'K15', 'K16'];

const viPhamMau = [
  ...viPhamCua('ao/MauViPham.tsx', MAU_TSX, 'ao/MauViPham.tsx'),
  ...viPhamCua('ao/mau_tang_cu.js', MAU_JS, 'ao/mau_tang_cu.js'),
];
const theMau = new Set(viPhamMau.flatMap((v) => [...v.chu.matchAll(/\[(K\d+)\]/g)].map((m) => m[1])));

// ═══ Đo trên mã thật ══════════════════════════════════════════════════════
const viPham = [];
for (const thuMuc of THU_MUC) {
  for (const tep of tepMa(thuMuc)) {
    const ma = ts.sys.readFile(tep) ?? '';
    for (const v of viPhamCua(tep, ma)) viPham.push({ ...v, tep: v.tep.slice(FE.length + 1) });
  }
}

// ═══ In ════════════════════════════════════════════════════════════════════
let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`${ok ? '✓' : '✗'} ${ten}${ct && !ok ? ` — ${ct}` : ''}`);
  if (!ok) loi++;
};

console.log('THUẬT NGỮ — "Môn học" một tên, ô lọc nói "Tất cả"\n');

const thieu = DUONG.filter((k) => !theMau.has(k));
const oan = AM.filter((k) => theMau.has(k));
check(`tự kiểm: bắt đủ ${DUONG.length} chỗ gài`, thieu.length === 0, `không bắt được ${thieu.join(', ')}`);
check(`tự kiểm: không báo oan ${AM.length} chỗ hợp lệ`, oan.length === 0, `báo oan ${oan.join(', ')}`);

for (const l of LUAT) {
  const ds = viPham.filter((v) => v.ma === l.ma);
  check(`0 chỗ ${l.ten}`, ds.length === 0, `${ds.length} chỗ`);
  for (const v of ds.slice(0, 30)) console.log(`    ${v.tep}:${v.dong}  "${v.chu}"`);
  if (ds.length > 30) console.log(`    … và ${ds.length - 30} chỗ nữa`);
}

console.log(`\n${loi === 0 ? 'ĐẠT' : `KHÔNG ĐẠT — ${loi} luật`}`);
process.exit(loi === 0 ? 0 : 1);
