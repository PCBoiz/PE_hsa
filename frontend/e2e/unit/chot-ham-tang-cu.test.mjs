/**
 * CHỐT HÃM cho tầng frontend CŨ — `public/static/js/` chỉ được nhỏ đi.
 *
 * ── VÌ SAO CẦN (A7, 05/09/2026) ───────────────────────────────────────────
 *
 * Sản phẩm có HAI tầng frontend chồng nhau: `src/` (Next/React, có bundler,
 * lint, typecheck) và `public/static/js/` (JS thuần, không bundler, CI chỉ chạy
 * `node --check` — tức chỉ kiểm cú pháp). Tầng cũ là nơi hai lỗ stored-XSS đã
 * nằm, và là nơi một tính năng chết lặng ba tuần mà không ai biết.
 *
 * Kế hoạch là dời dần sang `src/`. Nhưng "dời dần" không có số đo thì trôi:
 * TODO ghi 14.855 dòng, đo lại 05/09 thấy **15.134** — tầng đáng lẽ teo đi thì
 * đã LỚN THÊM, và không ai nhận ra vì không ai đo.
 *
 * ── CHỐT HÃM, KHÔNG PHẢI HẠN CHÓT ─────────────────────────────────────────
 *
 * Một hạn chót ("xoá xong trước 01/10") hoặc là trượt, hoặc ép làm ẩu. Chốt hãm
 * chỉ nói MỘT điều: hôm nay tầng này lớn thế này, và không được lớn hơn. Dời
 * được bao nhiêu thì hạ số xuống bấy nhiêu — việc hạ số là một dòng diff, và
 * nó biến tiến độ thành thứ nhìn thấy được trong lịch sử git.
 *
 * ── ĐẾM DÒNG MÃ, KHÔNG ĐẾM DÒNG CHÚ THÍCH ─────────────────────────────────
 *
 * Trần theo TỔNG số dòng sẽ phạt đúng việc viết giải thích tử tế — chính bản đo
 * 05/09 cho thấy phần lớn mức tăng 279 dòng là chú thích tôi viết thêm khi vá
 * lỗi. Một luật khiến người ta xoá lời giải thích để lọt CI là một luật tệ.
 * Nên trần đặt trên DÒNG MÃ: thêm lời giải thích thì miễn phí, thêm logic thì
 * không.
 *
 * Chạy: node e2e/unit/chot-ham-tang-cu.test.mjs
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const TANG_CU = join(GOC, 'public', 'static', 'js');

/* ── TRẦN HIỆN TẠI ─────────────────────────────────────────────────────────
   Đo 05/09/2026, ngay sau khi xoá `lesson_content_hsa.js` (5.847 dòng, 44% cả
   tầng — nó cung cấp đúng một global `window.LESSON_CONTENT_HSA` mà từ
   19/08/2026 không script nào đang nạp còn đọc).

   Dời thêm được tệp nào thì HẠ hai số này xuống.

   ── MỘT NGOẠI LỆ, VÀ CHỈ MỘT (ghi ngay trong ngày viết luật) ─────────────

   Luật đầu tiên tôi viết ở đây là "CHỈ ĐƯỢC HẠ". Vài giờ sau nó chặn đúng một
   thứ đáng làm: `#hsa-flash` — kênh phản hồi DUY NHẤT của trang bài học — không
   có `role`/`aria-live`, nên người dùng trình đọc màn hình không nghe được câu
   nào trong bốn câu giải thích VÌ SAO màn hình không nhúc nhích khi bấm nút.
   Bản vá tốn 17 dòng mã, và nó thuộc về engine, tức thuộc về tầng này.

   Viết mã tệ hơn để lọt một bộ đếm dòng là đúng thứ luật này sinh ra để chống.
   Nên ngoại lệ là: **VÁ LỖI trong tệp ĐÃ CÓ thì được nâng trần**, kèm lý do ở
   commit. Thêm màn hình mới hay tính năng mới thì KHÔNG — chúng thuộc `src/`.
   Ranh giới ấy nhìn thấy được trong một diff, và chốt hãm vẫn giữ giá trị của
   nó: nó BUỘC dừng lại và nói ra lý do. Lần này nó đã làm đúng việc.

       7353 → 7370   (+17)   vùng sống aria-live cho `flashNote`, 05/09/2026
       7370 → 7369   (-1)    vá tìm-kiếm-diễn-đàn (T60), 05/09/2026 — hạ trần
                             theo đúng luật ngay trên: dời được thì HẠ.
       7369 → 7383   (+14)  hai bản vá do lượt quét BẤM THỬ tìm ra, 05/09/2026:
                             · nhật ký báo "Đã lưu ✓" cho một phản hồi thiếu
                               dữ liệu, rồi nhét một bản ghi ma vào danh sách;
                             · khối phản ứng diễn đàn ghi đè state bằng undefined.
                             Cả hai là VÁ LỖI trong tệp đã có — ngoại lệ ghi ở trên.

   Con số là của BỘ ĐẾM DƯỚI ĐÂY, không phải của một câu grep. Ước lượng thô
   bằng `grep -vE '^\s*($|//|/\*|\*)'` cho ra 7.832 vì nó không hiểu khối
   `/* … *⁄` nhiều dòng — chênh 479. Trần phải là con số do chính bộ đếm này
   sinh ra, nếu không lần đo sau sẽ so hai thước khác nhau. */
const TRAN_TEP = 13;
const TRAN_DONG_MA = 7383;

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

function moiTep(thuMuc) {
  const out = [];
  for (const t of readdirSync(thuMuc)) {
    const p = join(thuMuc, t);
    if (statSync(p).isDirectory()) out.push(...moiTep(p));
    else if (t.endsWith('.js')) out.push(p);
  }
  return out.sort();
}

/* Dòng MÃ: bỏ dòng trống, `//`, và thân khối `/* … *␘/`.
   Đếm thô bằng regex từng dòng thay vì phân tích cú pháp: con số này để so với
   CHÍNH NÓ qua thời gian, nên nhất quán quan trọng hơn chính xác tuyệt đối. */
function dongMa(ma) {
  let trongKhoi = false;
  let n = 0;
  for (const raw of ma.split('\n')) {
    const d = raw.trim();
    if (trongKhoi) {
      if (d.includes('*/')) trongKhoi = false;
      continue;
    }
    if (!d) continue;
    if (d.startsWith('//')) continue;
    if (d.startsWith('/*')) {
      if (!d.includes('*/')) trongKhoi = true;
      continue;
    }
    n += 1;
  }
  return n;
}

const tep = moiTep(TANG_CU);
let tong = 0;
const bang = [];
for (const p of tep) {
  const n = dongMa(readFileSync(p, 'utf8'));
  tong += n;
  bang.push([relative(TANG_CU, p).replace(/\\/g, '/'), n]);
}

bang.sort((a, b) => b[1] - a[1]);
console.log('  Tầng cũ (public/static/js), dòng mã:');
for (const [t, n] of bang) console.log('   ', String(n).padStart(5), t);
console.log('   ', String(tong).padStart(5), `TỔNG (${tep.length} tệp)`);
console.log('');

check(`số tệp ≤ ${TRAN_TEP}`, tep.length <= TRAN_TEP,
  `đang là ${tep.length}. Tầng này chỉ được TEO đi — mã mới thuộc về src/, `
  + 'nơi có bundler, lint và typecheck.');

check(`dòng mã ≤ ${TRAN_DONG_MA}`, tong <= TRAN_DONG_MA,
  `đang là ${tong} (+${tong - TRAN_DONG_MA}). Chú thích KHÔNG bị tính, nên đây `
  + 'là logic mới. Viết nó ở src/ thay vì ở đây.');

/* Dời xong thì phải HẠ trần, nếu không nó chỉ là một con số cũ nằm đó.
   Cảnh báo chứ không đỏ: bỏ được nhiều là chuyện tốt, đừng biến nó thành lỗi. */
if (tep.length < TRAN_TEP || tong < TRAN_DONG_MA) {
  console.log(`  ⓘ Tầng cũ đã nhỏ hơn trần (${tep.length} tệp / ${tong} dòng mã).`);
  console.log('    Hạ TRAN_TEP và TRAN_DONG_MA trong tệp này xuống để chốt lại.');
}

console.log(failures === 0 ? '\nOK — tầng cũ không phình' : `\n${failures} lỗi`);
process.exitCode = failures === 0 ? 0 : 1;
