/**
 * Unit test — mọi bộ đo tự mở trình duyệt phải ĐÓNG nó lại, kể cả khi lỗi.
 *
 * ── LUẬT NÀY ĐÃ TỪNG ĐƯỢC ÉP, VÀ BẢN ÉP RƠI VÀO CHÚ THÍCH ────────────────
 *
 * 26/09/2026, commit `5f452f3` mang đúng cái tên *"Bảy bộ đo vẫn bỏ lại Chromium — một luật
 * không ai canh chỉ là một câu trong tài liệu"*. Nó thêm `import { baoHiem }` vào bảy tệp.
 * Ở `scripts/do_hieu_nang.mjs`, câu nhập ấy rơi **vào trong khối chú thích mở ở dòng 1**:
 *
 *     /* ĐO HIỆU NĂNG bằng chính giao thức DevTools (CDP), qua Playwright.
 *     import { baoHiem } from './lib/phien_do.mjs';        ← nằm trong chú thích
 *
 * Nên bản ép luật ấy, ở đúng tệp ấy, TỰ NÓ thành một câu trong tài liệu. Tệp chết ngay ở
 * `baoHiem(b)` với `ReferenceError`, và bốn ngày không ai chạy bộ đo hiệu năng nên không ai
 * biết — mãi tới 30/09, khi lần đầu có người trỏ nó ra production.
 *
 * ── VÌ SAO PHÉP KIỂM NÀY BÓC CHÚ THÍCH TRƯỚC ────────────────────────────
 *
 * `grep "import { baoHiem }"` sẽ XANH trên chính tệp hỏng — chuỗi ấy có mặt, chỉ là không
 * chạy. Muốn bắt được thì phải đọc như máy đọc, tức bỏ chú thích đi rồi mới tìm. Đây là lý do
 * phép kiểm này tồn tại thay vì một dòng dặn trong tài liệu.
 *
 * Chạy: node e2e/unit/bo-do-dong-trinh-duyet.test.mjs
 */
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SCRIPTS = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..', 'scripts');

/** Bỏ chú thích — đọc tệp như máy đọc, không như mắt đọc. */
function boChuThich(ma) {
  return ma.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/^\s*\/\/.*$/gm, '');
}

let hong = 0;
function kiem(ten, dung, them) {
  if (dung) console.log('  ✓', ten);
  else {
    console.error('  ✗', ten, them === undefined ? '' : '→ ' + them);
    hong++;
  }
}

console.log('Bộ đo tự mở trình duyệt thì phải tự đóng');

const tep = readdirSync(SCRIPTS).filter((f) => f.endsWith('.mjs'));
let soMo = 0;
for (const f of tep) {
  const ma = boChuThich(readFileSync(join(SCRIPTS, f), 'utf8'));
  if (!ma.includes('chromium.launch(')) continue;
  soMo += 1;
  kiem(`${f} — nhập \`baoHiem\` THẬT (không nằm trong chú thích)`,
       /import\s*\{[^}]*\bbaoHiem\b[^}]*\}\s*from/.test(ma),
       'tệp tự gọi `chromium.launch()` mà không có `baoHiem` — lỗi giữa chừng là bỏ lại một '
       + 'bộ Chromium trên máy người khác');
  kiem(`${f} — có GỌI \`baoHiem(...)\``, /\bbaoHiem\s*\(/.test(ma),
       'nhập mà không gọi thì cũng như không');
}

kiem('có tìm thấy bộ đo nào tự mở trình duyệt', soMo > 0,
     'phép kiểm không tìm thấy tệp nào để canh — nhiều khả năng đường dẫn `scripts/` sai, '
     + 'và một phép kiểm không canh gì thì luôn XANH');

if (hong) {
  console.error(`\n${hong} phép kiểm ĐỎ.`);
  process.exit(1);
}
console.log(`\nTất cả xanh (${soMo} bộ đo tự mở trình duyệt).`);
