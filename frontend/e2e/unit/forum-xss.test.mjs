/**
 * Unit test (Node thuần, không cần runner) — chống hồi quy XSS ở forum feed.
 *
 * Bug gốc: dashboard.js render TÊN TÁC GIẢ bài viết (`p.author`, nguồn là
 * users.name — do người dùng tự đặt) bằng cách nối chuỗi THÔ vào innerHTML,
 * KHÔNG escape → stored XSS: đặt tên = <img src=x onerror=...> là chạy JS trong
 * feed của mọi người xem. (Tên tác giả bình luận thì đã escHtml — chỉ post sót.)
 *
 * Test gồm 2 phần:
 *  1) Trích hàm escHtml THẬT trong dashboard.js và chứng minh nó trung hòa payload.
 *  2) Khẳng định dòng render `fpc-author` có bọc escHtml quanh author.
 *
 * Chạy: node e2e/unit/forum-xss.test.mjs   (exit 0 = pass, 1 = fail)
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SRC = join(__dirname, '..', '..', 'public', 'static', 'js', 'dashboard.js');
const code = readFileSync(SRC, 'utf8');

let failures = 0;
function check(name, cond, them) {
  if (cond) { console.log('  ✓', name); }
  else { console.error('  ✗', name, them === undefined ? '' : '→ ' + them); failures++; }
}

// ── 1) MỌI escHtml trong file phải trung hòa payload + null-safe ──────────
// dashboard.js có nhiều IIFE, mỗi IIFE có escHtml riêng. Bài viết forum dùng
// bản trong IIFE của nó, nên ta kiểm TẤT CẢ để không phụ thuộc bản nào đang scope.
const escBodies = [...code.matchAll(/function\s+escHtml\s*\(s\)\s*\{([\s\S]*?)\n\s{2}\}/g)];
if (escBodies.length === 0) throw new Error('Không tìm thấy escHtml trong dashboard.js');
const payload = '<img src=x onerror=alert(1)>';
escBodies.forEach((m, i) => {
   
  const escHtml = new Function('s', m[1]);
  const escaped = escHtml(payload);
  check(`escHtml#${i + 1} chuyển < thành &lt;`, !escaped.includes('<img'));
  check(`escHtml#${i + 1} chuyển > thành &gt;`, !escaped.includes('>'));
  check(`escHtml#${i + 1} giữ nguyên chuỗi thường`, escHtml('An') === 'An');
  check(`escHtml#${i + 1} null-safe (không ném lỗi với null/undefined)`, (() => {
    try { escHtml(null); escHtml(undefined); return true; } catch { return false; }
  })());
});

// ── 2) Dòng render tên tác giả bài viết PHẢI escape ──────────────────────
// Tìm dòng gán class "fpc-author" — phải bọc escHtml quanh author, không nối thô.
const authorLine = code.split('\n').find((l) => l.includes('class="fpc-author"'));
check('tìm thấy dòng render fpc-author', !!authorLine);
check(
  'tên tác giả bài viết được escape (escHtml(p.author))',
  !!authorLine && /escHtml\(\s*p\.author\s*\)/.test(authorLine),
);
check(
  'KHÔNG còn nối thô "+ p.author +" chưa escape ở dòng author',
  !!authorLine && !/\+\s*p\.author\s*\+/.test(authorLine),
);

// ── 3) Nhãn bài học: CHẠY THẬT hàm dựng HTML với payload ─────────────────
//
// Phần 2 ở trên chỉ khẳng định một DÒNG MÃ có chứa `escHtml`. Kiểu kiểm ấy xanh
// cả khi hàm bị đổi nghĩa — và nó KHÔNG bắt được lỗ thứ hai nằm trong CÙNG tệp,
// cách đó 500 dòng, suốt từ lúc bộ kiểm này ra đời. Phần này rút chính
// `_lessonTagHtml` ra rồi GỌI nó, nên nó đo hành vi chứ không đo hình dạng.
//
// LỖ GỐC (đo 04/09/2026): `p.courseId` là chuỗi người dùng gửi lên
// (`forum/views.py` nhận tự do, cắt 60 ký tự) và được nối THÔ vào `href` lẫn
// vào chữ hiển thị. Payload thoát khỏi thuộc tính vừa đúng 60 ký tự, và mã chạy
// trên miền Vercel — nơi cookie phiên sống, nên không cần đọc token, chỉ cần
// dùng nó qua lớp trung gian cùng origin.
const mTag = code.match(/function\s+_lessonTagHtml\s*\(p\)\s*\{([\s\S]*?)\n\s{2}\}/);
check('tìm thấy _lessonTagHtml', !!mTag);

if (mTag) {
  const escHtml = new Function('s', escBodies[0][1]);
  const COURSE_SHORT = { hsa_quantitative: 'Định lượng' };
  const lessonTag = new Function('escHtml', 'COURSE_SHORT', 'p', mTag[1]);
  const doc = (courseId) => lessonTag(escHtml, COURSE_SHORT, { courseId, lessonNo: 1 });

  const ra = doc('"><img src=x onerror=alert(1)>');

  /* KIỂM TÍNH CHẤT, KHÔNG KIỂM CHUỖI CON. Bản đầu của phép kiểm này đòi chuỗi
     `onerror` không được xuất hiện — và nó ĐỎ trên bản vá ĐÚNG, vì `onerror`
     vẫn còn đó dưới dạng văn bản chết (`&lt;img … onerror=…&gt;` trong nội dung,
     `onerror%3D` trong URL). Cả hai đều không chạy được.
     Hai tính chất dưới đây mới là thứ quyết định an toàn:
       · payload không tạo thêm được MỘT dấu `<` nào → không dựng nổi thẻ mới;
       · giá trị `href` không chứa dấu nháy kép → không thoát ra khỏi thuộc tính
         để gắn `onerror` vào chính thẻ `<a>`. */
  const soThe = (ra.match(/</g) || []).length;
  check('payload không tạo thêm thẻ nào (chỉ còn <a> và </a>)', soThe === 2, `${soThe} dấu < — ${ra}`);
  /* ĐẾM DẤU NHÁY, đừng bóc `href` bằng regex. Bản đầu dùng
     `/href="([^"]*)"/` rồi kiểm giá trị bóc ra có dấu nháy không — nhưng chính
     dấu nháy do payload chèn vào làm regex DỪNG SỚM, nên nó bóc ra `/lesson/`
     sạch sẽ và báo XANH trên mã hỏng. Phép kiểm tự cắt mất bằng chứng của nó.
     Khuôn mẫu có đúng 4 thuộc tính (class, href, onclick, title) = 8 dấu nháy;
     payload thoát ra được thì con số ấy lẻ ra ngay. */
  const soNhay = (ra.match(/"/g) || []).length;
  check('payload không thoát ra khỏi thuộc tính (đúng 8 dấu nháy của khuôn mẫu)',
    soNhay === 8, `${soNhay} dấu nháy — ${ra}`);

  // `javascript:` trong href — `escHtml` KHÔNG chặn được (không ký tự nào phải
  // thoát), `encodeURIComponent` thì có. Hai chỗ cần hai cách thoát khác nhau.
  check('href không trở thành javascript:', !/href="javascript:/i.test(doc('javascript:alert(1)')));

  // Và đường bình thường phải KHÔNG vỡ.
  const ok = doc('hsa_quantitative');
  check('khoá hợp lệ vẫn ra đúng đường dẫn',
    ok.includes('href="/lesson/hsa_quantitative?lesson=1"'), ok);
  check('khoá hợp lệ vẫn hiện tên hợp phần', ok.includes('Định lượng'), ok);
}

console.log(failures === 0 ? '\nPASS forum-xss' : `\nFAIL forum-xss (${failures})`);
process.exit(failures === 0 ? 0 : 1);
