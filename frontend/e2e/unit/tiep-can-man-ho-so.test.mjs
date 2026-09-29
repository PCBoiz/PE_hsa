/**
 * Unit test — hai lỗi TIẾP CẬN của màn Hồ sơ, axe bắt trên production 30/09/2026.
 *
 * ── VÌ SAO HAI LỖI NÀY SỐNG ĐƯỢC LÂU ─────────────────────────────────────
 *
 * ① **Tương phản 4,40.** Chip "xong chủ đề" (`.cmp-go.is-done`) gán cứng `#0E7C6B`. Mã ấy
 *   đạt 4,62 trên nền ô mặc định `#F4F3F8` và trên ba trong bốn bậc năng lực — chỉ **thiếu
 *   ở bậc 3** (`#EFECFD`, 4,40 so với chuẩn AA 4,5). Một lỗi chỉ hiện ở một phần tư số ô thì
 *   soi bằng mắt gần như không bao giờ thấy.
 *
 *   Đau hơn: dòng NGAY TRÊN nó trong `pages.css` mang chú thích kể lại rằng `.cmp-go` đã
 *   phải bỏ mã cứng vì lý do y hệt (22/09/2026, thiếu 0,03). Bài học có sẵn, cách đúng một
 *   dòng, và vẫn không ai sửa theo.
 *
 * ② **Vùng cuộn không vào được bằng bàn phím.** Sổ điểm nằm trong khung cao 420px với
 *   `overflow-y: auto`, mà từng dòng bên trong không có gì nhận được tiêu điểm — nên người
 *   không dùng chuột không cuộn nổi tới dòng thứ mười. WCAG 2.1.1.
 *
 * ── VÌ SAO KIỂM BẰNG NGUỒN ───────────────────────────────────────────────
 *
 * `do_axe.mjs` là thước thật và nó đã bắt được cả hai. Nhưng nó cần một bản đang chạy cùng
 * sáu thẻ vai, tốn mươi phút và ~1,5 GB RAM; phép kiểm này chạy trong một giây và nằm trong
 * cổng `pre-push`, nên nó canh phần KHÔNG ĐƯỢC QUAY LẠI giữa hai lượt đo thật.
 *
 * Chạy: node e2e/unit/tiep-can-man-ho-so.test.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const CSS = readFileSync(join(GOC, 'public', 'static', 'css', 'pages.css'), 'utf8');
const MAN = readFileSync(
  join(GOC, 'src', 'app', '(base)', 'dashboard', 'DashboardClient.tsx'), 'utf8');

let hong = 0;
function kiem(ten, dung, them) {
  if (dung) console.log('  ✓', ten);
  else {
    console.error('  ✗', ten, them === undefined ? '' : '→ ' + them);
    hong++;
  }
}

console.log('Màn Hồ sơ — hai lỗi tiếp cận axe bắt được 30/09');

// ① Chip "xong chủ đề" phải lấy màu từ TOKEN chữ, không gán cứng.
const dongChip = (CSS.match(/^\.cmp-go\.is-done\s*\{[^}]*\}/m) || [''])[0];
kiem('`.cmp-go.is-done` lấy màu từ `--success-ink`',
     /var\(\s*--success-ink/.test(dongChip),
     'đang gán cứng: ' + dongChip.replace(/\s+/g, ' ').slice(0, 80));
kiem('`.cmp-go.is-done` KHÔNG còn mã màu gán cứng',
     !/#[0-9a-fA-F]{3,8}/.test(dongChip),
     'mã cứng chỉ đúng với MỘT nền, mà ô năng lực có bốn nền khác nhau');

// ② Sổ điểm cuộn được bằng bàn phím, và thấy được mình đang ở đâu.
const khung = (MAN.match(/<div className="bk-rows"[\s\S]{0,260}?>/) || [''])[0];
kiem('khung sổ điểm nhận tiêu điểm (`tabIndex={0}`)',
     /tabIndex=\{0\}/.test(khung),
     'không có tiêu điểm thì bàn phím không cuộn được — WCAG 2.1.1');
kiem('khung sổ điểm có nhãn cho bộ đọc màn hình',
     /aria-label="[^"]{8,}"/.test(khung),
     'một vùng nhận tiêu điểm mà không tên thì người nghe không biết vừa vào đâu');
kiem('có viền tiêu điểm cho khung ấy',
     /\.bk-rows:focus-visible\s*\{[^}]*outline/.test(CSS),
     'nhận tiêu điểm mà không thấy viền thì mất dấu con trỏ — hại hơn cả không cuộn được');

if (hong) {
  console.error(`\n${hong} phép kiểm ĐỎ.`);
  process.exit(1);
}
console.log('\nTất cả xanh.');
