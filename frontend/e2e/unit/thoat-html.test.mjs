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
 * `roadmap.js` TỪNG có một hàm tên `esc` thoát gạch chéo ngược và nháy đơn —
 * thoát cho NGỮ CẢNH JS, không phải HTML. Phép quét dưới đây cố ý không soi nó,
 * vì nó không sai theo tiêu chí "đủ 5 ký tự". Nó sai theo một cách KHÁC, và
 * chuyện ấy sinh ra phần thứ hai của tệp này (xem cuối). Hàm đó đã bị xoá cùng
 * cả ba chỗ dùng nó, 04/09/2026.
 *
 * Nên chỉ soi hàm nào có MỘT THỰC THỂ HTML trong thân (`&amp;`, `&lt;`,
 * `&quot;`, `&#39;`…): đó là dấu hiệu tự khai "tôi là hàm thoát HTML".
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

/* ── HỌ LỖI THỨ HAI: thoát cho ngữ cảnh JS, đặt trong thuộc tính HTML ──────
 *
 * Phép quét ở trên hỏi "hàm thoát HTML có đủ 5 ký tự không". Nó bỏ lọt một họ
 * lỗi khác hẳn, và họ ấy đã cắn ba lần trong CÙNG MỘT NGÀY (04/09/2026):
 *
 *   dashboard.js  `escHtml(c.author)`  trong `onclick="forumToggleReply('…')"`
 *   roadmap.js    `esc(node.label)`    trong `onclick="roadmapOpenDrawer('…')"`
 *   main.js       `c.title.replace(/'/g,"\\'")` trong `onclick="unenroll('…')"`
 *
 * Ba chỗ, ba hàm thoát KHÁC NHAU, cùng một sai lầm: đặt một hàm thoát vào SAI
 * NGỮ CẢNH. Hàm thoát HTML bị trình duyệt hoàn tác trước khi JS chạy; hàm thoát
 * JS thì mù với dấu nháy KÉP đang bọc chính thuộc tính ấy.
 *
 * Không có phép kiểm nào bắt được cả ba, vì mỗi cái sai theo một kiểu. Cái
 * CHUNG duy nhất là hình dạng: **một chuỗi JS được dựng bên trong `onclick="`**.
 * Nên chặn ở hình dạng ấy — cấm hẳn `'` mở một chuỗi JS trong `onclick`. Cách
 * đúng đã dùng ở cả ba chỗ: dữ liệu qua `data-*`, trình xử lý đọc từ `this`.
 *
 * Bắt cả `.replace(/'/g, "\\'")` — một hàm thoát JS trong tầng này không còn
 * chỗ dùng đúng nào nữa sau khi ba chỗ trên đã chuyển sang `data-*`. */
/* Chỉ soi khi chuỗi JS đang được NỐI với dữ liệu — `\'' +` ở cuối.
 *
 * `onclick="navigate('courses')"` là hằng số viết thẳng trong mã, không phải
 * dữ liệu người dùng; báo nó là báo oan, và một phép kiểm báo oan sẽ bị tắt.
 * Đây đúng là lỗi tôi vừa phê bình ở `onclick-noi-suy.test.mjs` sáng nay và
 * suýt lặp lại ở đây: quét chuỗi thô rồi gọi mọi thứ trông giống là lỗi.
 *
 * Chú thích cũng phải bị loại: dòng chú thích kể lại mã CŨ (như ở `main.js`
 * ngay chỗ vừa vá) sẽ khớp y hệt mã thật. */
function boChuThich(ma) {
  return ma.replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '))
    .replace(/(^|[^:])\/\/[^\n]*/g, (m, p) => p + ' '.repeat(m.length - p.length));
}

/* `\\?'` — dấu nháy mở chuỗi JS có thể ĐÃ THOÁT hoặc TRẦN, tuỳ chuỗi JS bao
 * ngoài dùng nháy đơn hay nháy kép:
 *
 *     '…onclick="f(\'' + x + '\')">'      ← chuỗi ngoài nháy ĐƠN  → `\'`
 *     "…onclick=\"f('" + x + "','"        ← chuỗi ngoài nháy KÉP  → `'` trần
 *
 * Bản đầu chỉ bắt dạng thứ nhất, và dạng thứ hai là ĐÚNG chỗ `unenroll` vừa vá
 * ở `main.js` — tức phép kiểm sẽ mù với chính lỗi nó vừa được dựng để canh. Nó
 * chỉ bắt được chỗ ấy nhờ nhánh `THOAT_JS`, một dấu hiệu hẹp hơn nhiều (chỉ nổ
 * khi người viết dùng đúng cái hàm thoát ấy). */
const CHUOI_JS_NOI = /on(?:click|change|input|submit)=\\?["']([^"'\n]*?)\(\\?'\s*['"]\s*\+/g;
const THOAT_JS = /\.replace\(\s*\/'\/g\s*,\s*["']\\\\'["']\s*\)/g;

/* ── BÁNH CÓC: 12 chỗ CŨ, mỗi chỗ một lý do ĐÃ KIỂM ────────────────────────
 *
 * Ba chỗ nguy hiểm đã chuyển sang `data-*` hôm nay. Mười hai chỗ dưới đây an
 * toàn vì THỨ CHẢY VÀO, không vì hình dạng — nên chúng là NỢ, không phải đúng.
 * Ghi ra đây để (a) mọi chỗ MỚI mọc lên đều đỏ ngay, (b) lý do an toàn không
 * còn nằm trong đầu ai cả.
 *
 * Một danh sách miễn trừ mà không kèm lý do đã kiểm thì chỉ là một lời hứa;
 * mỗi dòng dưới đây đã được tra tận nguồn dữ liệu (04/09/2026).
 */
const CHO_PHEP = {
  // `posts.id` / `comments.id` là cột INTEGER (đã SELECT information_schema).
  'dashboard.js::forumSetReplyReaction': 'id số của CSDL + khoá cảm xúc hằng',
  'dashboard.js::forumToggleReply': 'id số của CSDL; TÊN người dùng đã chuyển sang data-mention',
  'dashboard.js::forumSetCmtReaction': 'id số của CSDL + khoá cảm xúc hằng',
  'dashboard.js::forumAddReply': 'id số của CSDL',
  'dashboard.js::window.forumOpenPost && window.forumOpenPost': 'p.id — cột INTEGER',
  // `courses.id` bị ép slug ở đường ghi (`courseadmin/views.py::_MA_KHOA`).
  'main.js::toggleEnroll': 'c.id — ép slug ở đường ghi',
  // `searchSuggestions` là mảng hằng khai ở main.js:47.
  'main.js::chooseSearchSuggestion': 'mảng hằng `searchSuggestions` (main.js:47)',
  // `levelSuggestions` khai `[]` ở main.js:48 và KHÔNG dòng nào nạp vào.
  'main.js::toggleSearchLevel': 'mảng `levelSuggestions` rỗng, không ai nạp',
  // Thoát HAI TẦNG đúng thứ tự (JS trước, HTML sau) — cách chữa hợp lệ.
  'main.js::cshPick': 'thoát hai tầng đúng thứ tự (JS rồi HTML)',
  // `chip.label` chỉ nhận hằng: `levelFilter` từ 4 chuỗi viết thẳng trong mã,
  // `languageFilters` từ 3 chuỗi ở `dashboard/page.tsx`. Đã grep hết chỗ gán.
  'main.js::removeCourseFilter': 'nhãn bộ lọc — chỉ nhận hằng viết thẳng trong mã',
  // `tab()` chỉ được gọi với bốn khoá viết thẳng: all/achieved/review/none.
  'dashboard.js::skSetFilter': 'bốn khoá viết thẳng ở dashboard.js:557-560',
  // `k` duyệt `Object.keys(REACT_EMOJIS)` — bảng hằng khai ở dashboard.js:924.
  'dashboard.js::forumSetReaction': 'p.id số + khoá của bảng hằng REACT_EMOJIS',
  'dashboard.js::forumToggleComments': 'p.id — cột INTEGER',
  'dashboard.js::forumSetCmtSort': "p.id số + hằng 'newest'/'oldest'",
  'dashboard.js::forumAddComment': 'p.id — cột INTEGER',
  // Danh sách `items` khai ngay trên chỗ dùng, ba khoá cứng.
  'roadmap.js::window.roadmapSetStatus': 'ba khoá trạng thái hằng khai tại chỗ',
};

const nghi = [];
const daDung = new Set();
for (const tep of tepJs(GOC)) {
  const goc = readFileSync(tep, 'utf8');
  const ma = boChuThich(goc);
  const ten = tep.slice(GOC.length + 1).replace(/\\/g, '/');
  const soDong = (i) => ma.slice(0, i).split('\n').length;

  for (const m of ma.matchAll(CHUOI_JS_NOI)) {
    const khoa = `${ten}::${m[1].trim()}`;
    if (khoa in CHO_PHEP) {
      daDung.add(khoa);
      continue;
    }
    nghi.push(`${ten}:${soDong(m.index)} — nối dữ liệu vào một chuỗi JS bên trong `
      + `onclick: ${JSON.stringify(m[0].slice(0, 46))}`
      + '\n         Cách chữa: đưa dữ liệu qua `data-*` rồi đọc `this.dataset.…`.'
      + '\n         Nếu thứ chảy vào CHẮC CHẮN là hằng hoặc số, thêm vào `CHO_PHEP`'
      + ' KÈM LÝ DO đã tra tận nguồn.');
  }
  for (const m of ma.matchAll(THOAT_JS)) {
    const dong = soDong(m.index);
    // Hai tầng ĐÚNG THỨ TỰ (JS trước, HTML sau) là cách chữa hợp lệ duy nhất
    // còn lại, và nó luôn có một hàm thoát HTML bọc NGOÀI trên cùng dòng.
    const dongMa = (ma.split('\n')[dong - 1] || '').replace(/\.replace\([^)]*\)/g, '');
    if (/esc/i.test(dongMa)) continue;
    nghi.push(`${ten}:${dong} — thoát cho ngữ cảnh JS mà không có tầng HTML bọc ngoài`);
  }
}

check('không chỗ nào MỚI nối dữ liệu vào chuỗi JS trong thuộc tính onclick',
  nghi.length === 0);
for (const t of nghi) console.error('      ·', t);

/* Danh sách miễn trừ phải CO LẠI, không phình ra. Một dòng không còn khớp chỗ
   nào là chỗ ấy đã được chữa (hoặc đổi tên) — xoá dòng ấy đi, đừng để nó nằm
   lại làm một lỗ mở sẵn cho hàm cùng tên mọc lên sau này. */
const thua = Object.keys(CHO_PHEP).filter((k) => !daDung.has(k));
check(`${Object.keys(CHO_PHEP).length} dòng miễn trừ đều còn khớp một chỗ thật`,
  thua.length === 0, thua.join(', '));
console.log(`   (nợ đang mang: ${daDung.size} chỗ dựng chuỗi JS trong onclick, `
  + 'an toàn vì thứ chảy vào — xem `CHO_PHEP`)');

console.log(failures === 0 ? '\nOK — không hàm thoát nào thủng' : `\n${failures} lỗi`);
process.exitCode = failures === 0 ? 0 : 1;
