/**
 * Unit test (Node thuần) — MỌI hàm thoát HTML trong tầng JS cũ phải thoát ĐỦ.
 *
 * ── VÌ SAO CÓ TỆP NÀY (04/09/2026) ────────────────────────────────────────
 *
 * Tầng `public/static/js` có **14** hàm thoát viết tay, mỗi IIFE một bản. Một
 * hàm ba dòng nhân bản 14 lần thì sẽ trôi — và nó đã trôi:
 *
 *   `lesson_hsa.js::esc` chỉ thoát `& < >`, KHÔNG thoát hai dấu nháy, trong khi
 *   nó được dùng ngay trong thuộc tính: `data-val="' + esc(op) + '"`. Một
 *   phương án trả lời chứa dấu nháy kép thoát ra khỏi thuộc tính và gắn được
 *   `onmouseover=` vào chính nút đáp án — thứ học viên buộc phải bấm.
 *
 * Tệ hơn: payload ấy KHÔNG chứa ký tự `<` nào, nên bộ lọc HTML thêm cùng ngày ở
 * `backend/lessons/content.py` không thấy gì. Hai hàng rào dựng trong một ngày,
 * và khe nằm đúng giữa chúng.
 *
 * Phép kiểm này quét CẢ tầng thay vì kiểm từng hàm: thêm một IIFE mới với một
 * bản `esc` thiếu sót thì nó đỏ ngay, không cần ai nhớ.
 *
 * ── PHÂN BIỆT HÀM THOÁT HTML VỚI HÀM THOÁT JS ─────────────────────────────
 *
 * `roadmap.js:99` có một hàm tên `esc` thoát dấu gạch chéo ngược và dấu nháy
 * đơn — đó là thoát cho NGỮ CẢNH JS, không phải HTML, và nó ĐÚNG khi không đụng
 * tới `&<>`. Nên chỉ soi hàm nào có MỘT THỰC THỂ HTML trong thân (`&amp;`,
 * `&lt;`, `&quot;`, `&#39;`…): đó là dấu hiệu tự khai "tôi là hàm thoát HTML".
 *
 * Bản đầu chỉ tìm `&amp;`, và như thế nó bỏ qua đúng loại tệ nhất — một hàm
 * quên thoát `&` hoàn toàn. Lọc theo triệu chứng nhẹ nhất là cách chắc chắn để
 * bỏ sót ca nặng nhất.
 *
 * Chạy: node e2e/unit/thoat-html.test.mjs
 */
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..', 'public', 'static', 'js');

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

/** Mọi tệp .js của tầng cũ, kể cả trong `pages/`. */
function tepJs(thumuc) {
  const ra = [];
  for (const m of readdirSync(thumuc, { withFileTypes: true })) {
    if (m.isDirectory()) ra.push(...tepJs(join(thumuc, m.name)));
    else if (m.name.endsWith('.js')) ra.push(join(thumuc, m.name));
  }
  return ra;
}

/* Rút thân hàm bằng cách ĐẾM NGOẶC, không bằng biểu thức chính quy.
 *
 * Bản đầu dùng `\{([\s\S]*?)\n?\s*\}` — nó dừng ở dấu `}` ĐẦU TIÊN, nên mọi hàm
 * có khối `{}` bên trong bị cắt cụt. Đo: nó tìm được 7 hàm trong khi `grep` thấy
 * 14, và một hàm bị cắt tới mức không dựng lại chạy được.
 *
 * Một phép kiểm quét cả tầng mà bỏ sót một nửa còn tệ hơn không có: nó phát ra
 * một tờ giấy chứng nhận sạch cho phần nó chưa hề nhìn tới. */
const DAU_HAM = /function\s+([A-Za-z_$][\w$]*)\s*\(\s*([A-Za-z_$][\w$]*)\s*\)\s*\{/g;

function* rutHam(ma) {
  for (const m of ma.matchAll(DAU_HAM)) {
    let sau = 1;
    let i = m.index + m[0].length;
    const dau = i;
    while (i < ma.length && sau > 0) {
      const c = ma[i];
      if (c === '{') sau += 1;
      else if (c === '}') sau -= 1;
      i += 1;
    }
    if (sau === 0) yield { ten: m[1], thamSo: m[2], than: ma.slice(dau, i - 1) };
  }
}

const CAN_THOAT = [
  ['&', '&amp;'],
  ['<', '&lt;'],
  ['>', '&gt;'],
  ['"', '&quot; hoặc &#34;'],
  ["'", '&#39; hoặc &apos;'],
];

let soHam = 0;
const daSoi = [];
const thieu = [];

for (const tep of tepJs(GOC)) {
  const ma = readFileSync(tep, 'utf8');
  const ten = tep.slice(GOC.length + 1).replace(/\\/g, '/');
  for (const { ten: tenHam, thamSo, than } of rutHam(ma)) {
    /* Nhận diện hàm thoát HTML bằng BẤT KỲ thực thể HTML nào trong thân, không
       chỉ `&amp;`. Bản đầu chỉ tìm `&amp;`, tức nó bỏ qua đúng loại tệ nhất —
       một hàm quên thoát `&` hoàn toàn. Lọc theo triệu chứng nhẹ nhất là cách
       bỏ sót ca nặng nhất. */
    if (!/&(amp|lt|gt|quot|apos|#\d+);/.test(than)) continue;
    soHam += 1;
    daSoi.push(`${ten}::${tenHam}`);

    let f;
    try {
      f = new Function(thamSo, than);
    } catch {
      thieu.push(`${ten}::${tenHam} — không dựng lại được để chạy`);
      continue;
    }

    const ra = String(f(`&<>"'`));
    for (const [ky, mong] of CAN_THOAT) {
      if (ra.includes(ky) && !(ky === '&' && ra.includes('&amp;'))) {
        thieu.push(`${ten}::${tenHam} — để lọt ${JSON.stringify(ky)} (cần ${mong}); trả về ${JSON.stringify(ra)}`);
        break;
      }
    }
    // Null-safe: gọi với null/undefined không được ném.
    try {
      f(null);
      f(undefined);
    } catch (e) {
      thieu.push(`${ten}::${tenHam} — ném lỗi với null/undefined: ${e.message}`);
    }
  }
}

console.log(`Quét tầng JS cũ — soi ${soHam} hàm thoát HTML:`);
for (const t of daSoi) console.log('   ·', t);
console.log('');
check(`tất cả ${soHam} hàm thoát đủ 5 ký tự & < > " '`, thieu.length === 0);
for (const t of thieu) console.error('      ·', t);
/* Sàn 7 = số hàm thoát HTML thật, đo được 04/09/2026. Bảy hàm tên `esc` khác
   trong `dashboard.js` là thoát cho NGỮ CẢNH JS (gạch chéo ngược + nháy đơn),
   đúng khi không đụng tới `&<>`, nên không tính vào đây.

   Sàn này tồn tại vì một lý do cụ thể: khâu rút thân hàm ĐÃ TỪNG hỏng trong
   chính phiên viết ra nó (biểu thức cắt cụt ở dấu `}` đầu tiên, soi 7/14 hàm
   rồi báo xanh). Không có sàn thì một lần hỏng như thế biến phép kiểm thành
   một tờ giấy chứng nhận sạch cấp cho zero hàm. */
check('vẫn soi được ít nhất 7 hàm (phép kiểm không tự rỗng đi)', soHam >= 7, `${soHam} hàm`);

console.log(failures === 0 ? '\nOK — không hàm thoát nào thủng' : `\n${failures} lỗi`);
process.exitCode = failures === 0 ? 0 : 1;
