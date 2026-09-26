/**
 * MỌI BỘ ĐO PHẢI ĐÓNG TRÌNH DUYỆT — kể cả khi nó chết giữa chừng.
 *
 * ── VÌ SAO (26–27/09/2026) ────────────────────────────────────────────────
 *
 * Anh Sơn hai lần báo máy không thở được. Lần đầu: 11 tiến trình Chromium giữ 788 MB cho
 * MỘT tab trống, cộng 22 tiến trình Node/Python mồ côi. Lần sau, một tuần chưa qua, máy
 * còn 1,5 GB trống trên 15,9 GB. Cả hai lần cùng một gốc: bộ đo gọi `chromium.launch()` ở
 * thân tệp và `browser.close()` ở dòng cuối, KHÔNG có gì lo phần ở giữa. Bộ đo ném lỗi —
 * trang trả 500, thẻ `pe_at` hết hạn, chờ quá giờ, người bấm Ctrl-C vì nó chạy lâu quá —
 * là Chromium sống tiếp tới khi tắt máy. Mỗi lượt chạy lại cộng thêm một bộ.
 *
 * `CLAUDE.md` đã ghi luật "bộ đo KHÔNG tự gọi `chromium.launch()`" từ 26/09. Sáng 27/09 đo
 * lại: **BẢY** bộ đo vẫn tự gọi. Một luật không có ai canh thì chỉ là một câu trong tài liệu.
 *
 * ── LUẬT Ở ĐÂY ────────────────────────────────────────────────────────────
 *
 * Bộ đo tự `chromium.launch()` thì PHẢI gọi `baoHiem(b)` — hàm ấy đóng trình duyệt trên
 * bốn đường mà `finally` không chạy. Chuyển hẳn sang `chay()` vẫn là đích đến, nhưng mỗi
 * bộ đo là một cổng của RULES §4: đổi cách nó mở trình duyệt thì phải đo lại cả bộ mới
 * biết con số còn nghĩa cũ không. Trong lúc chưa làm xong, thứ phải canh là "có đóng
 * không", chứ không phải "mở kiểu nào".
 *
 * Chạy: node e2e/unit/bo-do-phai-dong-trinh-duyet.test.mjs
 */
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const SCRIPTS = join(GOC, 'scripts');

/**
 * Có DÒNG THỰC THI nào chứa `can`? Chú thích không tính.
 *
 * Phải là một hàm chung cho cả hai phía. Bản đầu lọc chú thích cho `chromium.launch(`
 * nhưng lại kiểm `baoHiem(` bằng `ma.includes()` — nên khi thử ngược (chú thích dòng
 * `baoHiem(b);` đi rồi chạy lại), phép kiểm vẫn XANH: `// baoHiem(b);` vẫn chứa chuỗi ấy.
 * Một cái thước chỉ nghiêm ở nửa nó đang nhìn thì nửa kia là chỗ lỗi sẽ chui qua.
 */
function coDongThucThi(ma, can) {
  return ma.split('\n').some((d) => {
    const t = d.trim();
    if (t.startsWith('*') || t.startsWith('//')) return false;
    return t.includes(can);
  });
}

const loi = [];
let soTuLaunch = 0;
let soDungChay = 0;

for (const ten of readdirSync(SCRIPTS)) {
  if (!ten.endsWith('.mjs')) continue;
  const ma = readFileSync(join(SCRIPTS, ten), 'utf8');
  if (!coDongThucThi(ma, 'chromium.launch(')) {
    if (ma.includes("from './lib/phien_do.mjs'") && coDongThucThi(ma, 'chay(')) soDungChay++;
    continue;
  }
  soTuLaunch++;
  if (!coDongThucThi(ma, 'baoHiem(')) {
    loi.push(`${ten}: tự gọi chromium.launch() mà KHÔNG gọi baoHiem() — `
      + `Chromium sẽ sống tiếp nếu bộ đo chết giữa chừng`);
  }
}

// Bộ quét tự kiểm: nếu nó không thấy bộ đo nào tự launch thì hoặc mọi thứ đã chuyển sang
// `chay()` (tin mừng, hạ dòng dưới xuống 0), hoặc phép kiểm đã hỏng và đang xanh oan.
if (soTuLaunch === 0 && soDungChay === 0) {
  loi.push('bộ quét không thấy bộ đo nào — nó đang tìm sai chỗ, không phải scripts/ đã sạch');
}

if (loi.length) {
  console.error('✗ bộ đo không đóng trình duyệt:');
  for (const d of loi) console.error(`  · ${d}`);
  console.error('\n  Sửa: thêm `import { baoHiem } from \'./lib/phien_do.mjs\';` rồi `baoHiem(b);`');
  console.error('  ngay sau dòng launch. Tốt hơn nữa: chuyển hẳn sang `chay()`.');
  process.exit(1);
}

console.log(`  ✓ ${soTuLaunch} bộ đo tự launch — tất cả có baoHiem()`);
console.log(`  ✓ ${soDungChay} bộ đo đã dùng chay() của phien_do.mjs`);
console.log('\nOK — không bộ đo nào bỏ lại Chromium');
