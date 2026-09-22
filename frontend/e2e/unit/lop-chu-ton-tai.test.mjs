/**
 * Unit test — mọi lớp `text-*` trong `src/` phải là thứ Tailwind SINH RA ĐƯỢC.
 *
 * ── VÌ SAO CÓ TỆP NÀY (22/09/2026) ────────────────────────────────────────
 *
 * Agent rà giảng viên → phụ huynh đo `document.styleSheets`: lớp `text-caption`
 * có 25 chỗ dùng trong 5 tệp (tờ phụ huynh, bảng chấm, nhập kết quả thi, khu
 * Soạn) mà KHÔNG có một luật CSS nào — thang cỡ chữ trong `app/tailwind.css`
 * chưa từng khai `--text-caption`. Tailwind gặp tên lạ thì im lặng không sinh
 * gì; `tsc`, `eslint`, bản dựng đều xanh. Hệ quả: đoạn "chú thích" trên tờ phụ
 * huynh ra 15px — to hơn cả cái bảng 13px mà nó chú thích.
 *
 * Quét cùng lúc lòi ra lỗi thứ hai cùng họ: `text-ok-ink` (4 chỗ ở khu Soạn) —
 * token thật tên `success-ink`, nên câu "Đã lưu" hiện màu chữ thường thay vì
 * xanh.
 *
 * ── LUẬT ──────────────────────────────────────────────────────────────────
 *
 * `text-TÊN` hợp lệ khi TÊN là: cỡ chữ khai trong `@theme` (`--text-TÊN:`),
 * màu khai trong `@theme` (`--color-TÊN:`), tiện ích có sẵn của Tailwind
 * (canh lề, gói dòng, cỡ mặc định xs…9xl), hoặc màu bảng mặc định (red-600…)
 * — `tailwind.css` vẫn nạp `tailwindcss/theme.css` nên bảng mặc định còn.
 * Bỏ qua giá trị tuỳ ý (`text-[13px]`) và thuộc tính tuỳ ý
 * (`[text-orientation:mixed]` — đứng sau dấu `[`).
 *
 * Chạy: node e2e/unit/lop-chu-ton-tai.test.mjs
 */
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const FE = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const SRC = join(FE, 'src');
const TW = readFileSync(join(SRC, 'app', 'tailwind.css'), 'utf8');

// `--text-body:` là cỡ; `--text-body--line-height:` là thuộc tính phụ của cỡ ấy.
const CO = new Set([...TW.matchAll(/--text-([a-z0-9]+(?:-[a-z0-9]+)*)\s*:/g)].map((m) => m[1]));
const MAU = new Set([...TW.matchAll(/--color-([a-z0-9]+(?:-[a-z0-9]+)*)\s*:/g)].map((m) => m[1]));
const SAN = new Set(['left', 'center', 'right', 'justify', 'start', 'end', 'wrap', 'nowrap', 'balance', 'pretty',
  'ellipsis', 'clip', 'transparent', 'current', 'inherit', 'white', 'black',
  'xs', 'sm', 'base', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl', '6xl', '7xl', '8xl', '9xl']);
const BANG = /^(slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(50|[1-9]00|950)$/;

let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${ten}${ok || !ct ? '' : `  → ${ct}`}`);
  if (!ok) loi += 1;
};

function* tep(d) {
  for (const e of readdirSync(d, { withFileTypes: true })) {
    const p = join(d, e.name);
    if (e.isDirectory()) yield* tep(p);
    else if (/\.(tsx|ts)$/.test(e.name)) yield p;
  }
}

check('đọc được thang cỡ chữ (đường dẫn đúng chưa?)', CO.has('body') && CO.has('label'), [...CO].join(','));
check('đọc được bảng màu', MAU.has('ink') && MAU.has('success-ink'), [...MAU].slice(0, 8).join(','));

const la = [];
let dem = 0;
for (const p of tep(SRC)) {
  const dong = readFileSync(p, 'utf8').split('\n');
  dong.forEach((s, i) => {
    // Tiền tố biến thể (`hover:`, `md:`, `dark:`…) được phép; hậu tố độ mờ `/70` cũng vậy.
    for (const m of s.matchAll(/(?<![\w\-[])(?:[a-z0-9-]+:)*text-([a-z0-9]+(?:-[a-z0-9]+)*)(?:\/\d+)?(?![\w-])/g)) {
      dem += 1;
      const ten = m[1];
      if (CO.has(ten) || MAU.has(ten) || SAN.has(ten) || BANG.test(ten)) continue;
      la.push(`${relative(FE, p)}:${i + 1} · text-${ten}`);
    }
  });
}
check(`có lớp text-* để quét (${dem})`, dem > 200, String(dem));
check('không lớp text-* nào Tailwind không sinh được', la.length === 0, `\n      ${la.join('\n      ')}`);

console.log(loi ? `\n${loi} kiểm tra ĐỎ\n` : '\nOK — mọi lớp text-* đều có CSS\n');
process.exit(loi ? 1 : 0);
