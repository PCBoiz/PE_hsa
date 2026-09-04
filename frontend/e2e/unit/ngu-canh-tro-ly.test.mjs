/**
 * Unit test — trợ lý phải BIẾT học viên đang mở bài nào.
 *
 * ── LỖI ĐANG CHẶN LẠI: một tính năng chết LẶNG ba tuần (05/09/2026) ────────
 *
 * `chatbot.js::collectLessonContext` đọc `window.LESSON_CONTENT_HSA` — biến do
 * `lesson_content_hsa.js` đặt ra. Ngày 19/08/2026, khi 76 bài chuyển vào CSDL,
 * `LessonHsa.tsx` bỏ tệp ấy khỏi danh sách script. Từ hôm đó hàm này rơi vào
 * nhánh `typeof … === 'undefined'` và trả `null` cho MỌI lần gọi.
 *
 * Không log, không màn hình đỏ, không ai báo hỏng. Trợ lý vẫn trả lời — chỉ là
 * trả lời chung chung hơn, thứ không ai quy được về một nguyên nhân. Và cái
 * guard `typeof … undefined`, viết ra để PHÒNG THỦ, chính là thứ biến sự cố
 * thành im lặng.
 *
 * ── VÌ SAO KIỂM THEO KIỂU NÀY ─────────────────────────────────────────────
 *
 * Một test chỉ gọi `collectLessonContext` với global đúng tên sẽ XANH cả trước
 * lẫn sau bản vá — nó kiểm cái tôi vừa viết, không kiểm cái đã hỏng. Thứ hỏng
 * là MỐI NỐI: chatbot đọc một tên mà không script nào ĐANG NẠP ghi ra.
 *
 * Nên phép kiểm 1 đi đúng đường thật: đọc danh sách script từ chính
 * `LessonHsa.tsx`, gom mọi global các script ấy GHI, rồi đòi mọi global
 * chatbot.js ĐỌC phải nằm trong đó. Bỏ một script khỏi danh sách mà quên người
 * đọc nó → đỏ ngay, kể cả với một tính năng khác trong tương lai.
 *
 * Chạy: node e2e/unit/ngu-canh-tro-ly.test.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const JS = (t) => readFileSync(join(GOC, 'public', 'static', 'js', t), 'utf8');

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

/* Bỏ chú thích TRƯỚC khi quét tên.
   Không bỏ thì đoạn văn giải thích "bản cũ đọc window.LESSON_CONTENT_HSA" ở
   ngay trong chatbot.js sẽ bị tính là một lần ĐỌC, và test báo đỏ cho một bản
   vá đã đúng. Đúng cái bẫy đã mắc một lần trong repo này: một biểu thức tìm
   `<script src>` khớp phải chữ trong chú thích rồi báo thiếu tệp. */
function boChuThich(ma) {
  return ma.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/(^|[^:])\/\/[^\n]*/g, '$1 ');
}

/* `window.X` THẬT — không phải `chatbotElements.window.classList`.
   Chặn ký tự đứng trước là chữ, số, `.` hay `$`. */
const DOC = /(?<![\w.$])window\.([A-Za-z_$][\w$]*)/g;
const GHI = /(?<![\w.$])window\.([A-Za-z_$][\w$]*)\s*=(?!=)/g;

function ten(ma, re) {
  const out = new Set();
  for (const m of boChuThich(ma).matchAll(re)) out.add(m[1]);
  return out;
}

/* Global của TRÌNH DUYỆT — không script nào trong repo ghi chúng.
   Danh sách CỐ TÌNH ngắn và tường minh: thêm một dòng vào đây là một hành động
   có ý thức, còn một danh sách dài thì che mất đúng thứ test này đi tìm. */
const CUA_TRINH_DUYET = new Set([
  'location', 'localStorage', 'sessionStorage', 'document', 'navigator',
  'innerWidth', 'innerHeight', 'matchMedia', 'scrollTo', 'addEventListener',
  'removeEventListener', 'setTimeout', 'clearTimeout', 'fetch', 'open',
  'URLSearchParams', 'getComputedStyle', 'requestAnimationFrame',
]);

/* ── 1. MỐI NỐI: chatbot đọc gì, các script ĐANG NẠP có ghi không ────────── */
const TSX = readFileSync(join(GOC, 'src', 'components', 'LessonHsa.tsx'), 'utf8');
const nap = [...boChuThich(TSX).matchAll(/'\/static\/js\/([\w./-]+\.js)'/g)].map((m) => m[1]);

check('đọc được danh sách script từ LessonHsa.tsx', nap.length >= 2, nap.join(', '));
check('chatbot.js nằm trong danh sách nạp', nap.includes('chatbot.js'), nap.join(', '));

const ghiBoi = new Map();
for (const t of nap) {
  for (const g of ten(JS(t), GHI)) if (!ghiBoi.has(g)) ghiBoi.set(g, t);
}

const thieu = [...ten(JS('chatbot.js'), DOC)]
  .filter((g) => !CUA_TRINH_DUYET.has(g) && !ghiBoi.has(g));

check('mọi global chatbot.js đọc đều do một script ĐANG NẠP ghi ra',
  thieu.length === 0,
  thieu.length ? `không ai ghi: ${thieu.join(', ')} (script đang nạp: ${nap.join(', ')})` : '');

check('`__PE_BAI_DANG_MO` do lesson_hsa.js công bố',
  ghiBoi.get('__PE_BAI_DANG_MO') === 'lesson_hsa.js',
  ghiBoi.get('__PE_BAI_DANG_MO') || 'không script nào ghi');

/* ── 2. Engine công bố ĐÚNG LÚC và ĐÚNG THỨ ──────────────────────────────── */
const ENGINE = boChuThich(JS('lesson_hsa.js'));

check('`lessonNo` có trong khai báo `state` (không phải trường bịa)',
  /var state = \{[^}]*lessonNo/.test(ENGINE),
  'công bố `state.lessonNo` mà state không có trường ấy → luôn là undefined');

check('`state.lessonNo` được GÁN từ tham số ?lesson',
  /state\.lessonNo = want;/.test(ENGINE));

check('nhánh RƠI VỀ bài 1 cập nhật lại `lessonNo`',
  /state\.lessonNo = 1;/.test(ENGINE),
  'không cập nhật → trợ lý nói số bài học viên yêu cầu, còn nội dung là bài 1');

check('công bố nằm CÙNG CHỖ với `state.lesson = lesson`',
  /state\.lesson = lesson;[\s\S]{0,400}window\.__PE_BAI_DANG_MO = \{/.test(ENGINE),
  'tách xa ra thì có đường vào bài mà không công bố');

/* ── 3. Hàm chạy thật với đúng hình dạng engine công bố ───────────────────── */
const than = /function collectLessonContext\(\)[\s\S]*?\n\}/.exec(JS('chatbot.js'));
check('rút được `collectLessonContext`', !!than);

if (than) {
  const goi = (w, d) => new Function('window', 'document',
    `${than[0]}\nreturn collectLessonContext();`)(w, d);

  const BAI = {
    id: 'tq_07', title: 'Tỉ lệ phần trăm', topic_tag: 'Số học',
    notes: { key_points: ['a', 'b'], formula: 'p = x/y' },
  };
  const buoc3 = { getAttribute: () => '3' };
  const docGia = { querySelector: () => buoc3, body: { getAttribute: () => 'hsa_tq' } };

  const ok = goi({ __PE_BAI_DANG_MO: { courseId: 'hsa_tq', index: 7, lesson: BAI } }, docGia);
  check('có bài đang mở → trả ngữ cảnh, KHÔNG null', ok !== null, String(ok));
  check('nói đúng số bài', ok && ok.lesson_index === 7, JSON.stringify(ok));
  check('nói đúng tên bài', ok && ok.lesson_title === 'Tỉ lệ phần trăm', JSON.stringify(ok));
  check('nói đúng bước đang xem', ok && ok.step === 'Lý thuyết', JSON.stringify(ok));
  check('gửi kèm ý chính + công thức',
    ok && ok.key_points.length === 2 && ok.formula === 'p = x/y', JSON.stringify(ok));

  // Không gửi `course_title` nữa: tên khoá không có ở client, máy chủ tự tra.
  check('KHÔNG gửi course_title từ client',
    ok && !('course_title' in ok), JSON.stringify(ok));

  check('trang không phải bài học → null', goi({}, docGia) === null);
  check('bài chưa tải xong → null',
    goi({ __PE_BAI_DANG_MO: { courseId: 'hsa_tq', index: 7, lesson: null } }, docGia) === null);
}

console.log(failures === 0 ? '\nOK — trợ lý biết bài đang mở' : `\n${failures} lỗi`);
process.exitCode = failures === 0 ? 0 : 1;
