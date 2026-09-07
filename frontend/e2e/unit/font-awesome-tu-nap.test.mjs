/**
 * Tệp nào DÙNG biểu tượng Font Awesome thì phải TỰ NẠP Font Awesome.
 *
 * ── VÌ SAO CÓ TỆP NÀY (07/09/2026) ────────────────────────────────────────
 *
 * Sáng 07/09 tôi gỡ Font Awesome khỏi `(base)/layout.tsx` để tiết kiệm 100kB,
 * sau khi grep và kết luận "0 lần dùng class `fa-`". Kết luận ấy SAI —
 * `Chatbot.tsx` dùng 10 biểu tượng và `chatbot.js` dùng thêm 4. Đo lại sau đó
 * trên `/dashboard`: 12 thẻ `<i class="fa-*">` hiện ở 0×0px, `::before` rỗng.
 * Trợ lý AI mất sạch biểu tượng, và bản ấy đã lên production.
 *
 * Không gì chặn tôi lại, vì "biểu tượng biến mất" KHÔNG làm hỏng gì cả: không
 * lỗi JS, không lỗi build, không phép kiểm nào đỏ. Trang vẫn chạy, chỉ là chỗ
 * đáng ra có hình thì trống.
 *
 * ── VÌ SAO CANH BẰNG LUẬT "TỰ NẠP" CHỨ KHÔNG PHẢI ĐẾM BIỂU TƯỢNG ─────────
 *
 * Đếm biểu tượng hiện ra trên màn thì phải mở trình duyệt, phải đăng nhập, và
 * chỉ đúng với những trang phép kiểm nghĩ tới. Luật ở đây mạnh hơn mà rẻ hơn:
 * **đặt lời nạp cạnh chỗ dùng**. Ai thêm một nơi gắn thứ năm cũng không hỏng
 * được, vì component mang theo phụ thuộc của chính nó.
 *
 * Chạy: node e2e/unit/font-awesome-tu-nap.test.mjs
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, sep } from 'node:path';

const GOC = process.cwd();
const SRC = join(GOC, 'src');

/** Mọi tệp .tsx dưới `src/`. */
function cacTsx(thu_muc) {
  const ra = [];
  for (const ten of readdirSync(thu_muc)) {
    const p = join(thu_muc, ten);
    if (statSync(p).isDirectory()) ra.push(...cacTsx(p));
    else if (ten.endsWith('.tsx')) ra.push(p);
  }
  return ra;
}

let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${ten}${ok || !ct ? '' : `  → ${ct}`}`);
  if (!ok) loi += 1;
};

/* Font Awesome có HAI cú pháp và dự án dùng cả hai:
     ·  cũ  `fas fa-robot`, `far fa-clock`      (Chatbot, courses/[courseId])
     ·  FA6 `fa-solid fa-check`, `fa-regular …` (LessonHsa, MockExam)

   Bản đầu của regex này chỉ bắt cú pháp CŨ, nên nó báo "2 tệp dùng Font
   Awesome" trong khi thật ra có 4 — một phép kiểm sinh ra để canh chuyện bỏ
   sót, mà bản thân nó bỏ sót một nửa. Bắt được vì con số 2 không khớp với
   grep tay ra 4.

   Vẫn đòi có TIỀN TỐ họ biểu tượng chứ không bắt trần `fa-`: nới tới mức ấy
   sẽ khớp cả chú thích nói VỀ Font Awesome, và một phép kiểm báo oan thì
   người sau sẽ tắt nó đi. */
const DUNG = /class(?:Name)?=(?:\"|')[^\"']*(?:\bfa[bsrl]\s+fa-|\bfa-(?:solid|regular|brands|light|thin|duotone|sharp)\b)/;
const NAP = /cdnjs\.cloudflare\.com[^"']*font-awesome/;

const tsx = cacTsx(SRC);
check(`đọc được ${tsx.length} tệp .tsx`, tsx.length > 20, String(tsx.length));

const dung = [];
for (const p of tsx) {
  const s = readFileSync(p, 'utf8');
  // `split/join` chứ không phải regex: dấu gạch chéo ngược trong một regex
  // viết qua heredoc của shell bị nuốt mất, và tệp gãy cú pháp ngay.
  // `split(sep)` chứ không viết dấu gạch chéo ngược thẳng vào mã: một
  // ký tự thoát viết qua heredoc của shell bị nuốt mất, và tệp gãy cú
  // pháp ngay. Đã trả giá hai lượt cho đúng một dòng này.
  if (DUNG.test(s)) dung.push([p.replace(GOC, '').split(sep).join('/'), NAP.test(s)]);
}

check(`có ${dung.length} tệp dùng biểu tượng Font Awesome`, dung.length > 0,
  dung.map((d) => d[0]).join(', '));

for (const [p, tu_nap] of dung) {
  check(`${p} tự nạp Font Awesome`, tu_nap,
    'dùng class `fa-` nhưng KHÔNG có thẻ <link> Font Awesome — biểu tượng sẽ '
    + 'hiện ở 0×0px mà không có lỗi nào cả');
}

console.log(loi ? `\n${loi} lỗi` : '\nTất cả đạt');
process.exit(loi ? 1 : 0);
