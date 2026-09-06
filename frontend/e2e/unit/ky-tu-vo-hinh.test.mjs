/**
 * Unit test — không tệp mã nào được chứa KÝ TỰ VÔ HÌNH.
 *
 * ── VÌ SAO CÓ TỆP NÀY (07/09/2026) ────────────────────────────────────────
 *
 * Một lượt sửa bằng script đã ghi ký tự `0x08` (backspace) vào giữa một biểu
 * thức chính quy:
 *
 *     const DUONG = [...DL.matchAll(/^<0x08>o: '([^']+)'/g)]
 *                                    ↑ đây là 0x08, không phải chữ H
 *
 * Tệp mở ra trông bình thường. `node` chạy không ném. `eslint` không kêu.
 * `tsc` không thấy (tệp `.mjs`). Phép kiểm ấy chỉ lặng lẽ khớp 0 dòng và báo
 * "đường dẫn để đối chiếu: 0" — mà con số 0 thì trông y như "chưa có gì để
 * đo", không như "cái thước đã hỏng".
 *
 * Mất khá lâu mới lần ra, và chỉ vì `cat -A` hiện `^H`. Đó là lý do tệp này
 * tồn tại: một byte vô hình có thể ngồi trong mã rất lâu, và mọi cửa kiểm hiện
 * có đều đi qua nó.
 *
 * ── QUÉT GÌ ──────────────────────────────────────────────────────────────
 *
 *   · ký tự điều khiển C0 (trừ tab, xuống dòng, về đầu dòng);
 *   · khoảng trắng bề rộng 0 và các dấu định hướng hai chiều (U+200B–200F,
 *     U+2028/2029, U+202A–202E, U+2066–2069) — chúng có thể làm mã HIỆN ra
 *     khác hẳn thứ trình biên dịch đọc;
 *   · BOM ở giữa tệp.
 *
 * KHÔNG quét thư mục `node_modules` và `.next` (không phải mã của dự án), và
 * không quét ảnh hay tệp nhị phân.
 *
 * Chạy: node e2e/unit/ky-tu-vo-hinh.test.mjs
 */
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const FE = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const GOC = join(FE, '..');

/** Thư mục quét, và phần mở rộng được coi là MÃ. */
const QUET = [
  join(FE, 'src'),
  join(FE, 'e2e'),
  join(FE, 'public', 'static', 'js'),
  join(FE, 'public', 'static', 'css'),
  join(GOC, 'backend'),
  join(GOC, 'scripts'),
];
const DUOI = /\.(ts|tsx|js|mjs|cjs|css|py|sql|json)$/;
const BO_QUA = /(^|[\\/])(node_modules|\.next|\.venv|__pycache__|staticfiles|test-results)([\\/]|$)/;

/* CHỈ những ký tự KHÔNG BAO GIỜ hợp lệ trong mã:
     · điều khiển C0, trừ tab (09), xuống dòng (0A), về đầu dòng (0D);
     · U+200B khoảng trắng bề rộng 0;
     · U+2028/2029 dấu ngắt dòng Unicode — JS coi chúng là xuống dòng THẬT;
     · U+202A-202E, U+2066-2069 dấu đảo chiều hai chiều ("Trojan Source":
       mã HIỆN ra khác hẳn thứ trình biên dịch đọc).

   CỐ Ý KHÔNG bắt U+200C-200F và BOM đầu tệp. Bản đầu có bắt, và nó báo đỏ ba
   chỗ HOÀN TOÀN HỢP LỆ: `👩‍💻` và `🧑‍💻` là emoji ghép bằng ZWJ (U+200D), còn
   `lesson_db_design.css` mở đầu bằng BOM — một dấu vết mã hoá, không phải mã
   hỏng.

   Đây là mặt kia của cùng một sai lầm đã gặp năm lần hôm nay: thước quá HẸP
   thì bỏ sót im lặng, thước quá RỘNG thì báo oan — và báo oan còn tệ hơn ở
   chỗ nó dạy người ta bỏ qua chính cái thước ấy. */
const XAU = new RegExp('[\u0000-\u0008\u000B\u000C\u000E-\u001F' + '\u200B\u2028\u2029\u202A-\u202E\u2066-\u2069]');

/* BOM chỉ sai khi nằm GIỮA tệp. Ở byte đầu nó là dấu mã hoá, khó chịu
   nhưng không làm mã chạy sai. */
const bomLac = (s) => s.indexOf(String.fromCharCode(0xFEFF), 1) !== -1;

let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${ten}${ok || !ct ? '' : `  → ${ct}`}`);
  if (!ok) loi += 1;
};

function* tepMa(thuMuc) {
  let ds;
  try {
    ds = readdirSync(thuMuc, { withFileTypes: true });
  } catch {
    return; // thư mục không có ở máy này — không phải lỗi
  }
  for (const e of ds) {
    const p = join(thuMuc, e.name);
    if (BO_QUA.test(p)) continue;
    if (e.isDirectory()) yield* tepMa(p);
    else if (DUOI.test(e.name)) yield p;
  }
}

const ds = [...new Set(QUET.flatMap((d) => [...tepMa(d)]))];
console.log(`\nQuét ${ds.length} tệp mã.\n`);
check('có tệp để quét (đường dẫn đúng chưa?)', ds.length > 100, String(ds.length));

const dinh = [];
for (const p of ds) {
  let s;
  try {
    s = readFileSync(p, 'utf8');
  } catch {
    continue; // không đọc được dạng chữ → không phải mã
  }
  if (bomLac(s)) {
    dinh.push(`${relative(GOC, p)} · BOM (U+FEFF) nằm GIỮA tệp`);
  }
  if (!XAU.test(s)) continue;
  // Nói ĐÚNG dòng và ĐÚNG mã ký tự: "có ký tự lạ trong tệp X" thì người sửa
  // vẫn phải tự đi tìm, mà thứ họ tìm thì vô hình.
  const dong = s.split('\n');
  for (let i = 0; i < dong.length; i += 1) {
    const m = XAU.exec(dong[i]);
    if (!m) continue;
    dinh.push(`${relative(GOC, p)}:${i + 1} · U+${m[0].codePointAt(0)
      .toString(16).toUpperCase().padStart(4, '0')} ở cột ${m.index + 1}`);
  }
}

check('không tệp nào chứa ký tự vô hình', dinh.length === 0,
  '\n      ' + dinh.slice(0, 20).join('\n      '));

/* Phép kiểm này phải ĐỎ ĐƯỢC — nếu không thì nó chỉ là một dòng xanh trang
   trí. Tự dựng một chuỗi có backspace và xác nhận bộ dò bắt được. */
check('bộ dò thật sự bắt được 0x08', XAU.test('matchAll(/^' + String.fromCharCode(8) + "o: '/g)"));
check('bộ dò KHÔNG bắt nhầm tab và xuống dòng', !XAU.test('\t\n\r  chữ thường'));
check('bộ dò KHÔNG bắt nhầm emoji ghép ZWJ',
  !XAU.test('avatar: ' + String.fromCharCode(0x1F469, 0x200D, 0x1F4BB)));
check('bộ dò bắt được khoảng trắng bề rộng 0', XAU.test('const a' + String.fromCharCode(0x200B) + ' = 1;'));

console.log(loi === 0 ? '\nOK — không có ký tự vô hình trong mã' : `\n${loi} lỗi`);
process.exitCode = loi === 0 ? 0 : 1;
