/**
 * Unit test — mã chạy ở TRÌNH DUYỆT không được nhập `zod` bản đầy đủ.
 *
 * ── VÌ SAO CÓ TỆP NÀY (14/09/2026, tối) ──────────────────────────────────
 *
 * Sáng nay T18 mức 2 thêm hình dạng `zod` cho chiều GHI ở bốn component
 * `'use client'`. Bản `zod` đầy đủ không rung cây được (các phương thức móc vào
 * prototype), nên nhập nó ở phía trình duyệt là kéo cả thư viện vào gói của
 * trang: đo bằng `scripts/do_hieu_nang.mjs`, **Thi thử 271 → 398 kB**, **Trang
 * của tôi 431 → 587 kB** — nhiều hơn cả Font Awesome vừa gỡ cùng ngày. Không
 * bộ kiểm nào đỏ; chỉ thấy vì đọc cột JS(kB) của bảng hiệu năng.
 *
 * Luật: tệp bắt đầu bằng `'use client'` nhập `zod/mini` (API dạng hàm, cùng
 * `looseObject`/`safeParse`). Mã máy chủ dùng `zod` đầy đủ thoải mái — gói máy
 * chủ không ai tải.
 *
 * Chỉ bắt dòng `import … from 'zod'` THẬT (đầu dòng), không bắt chữ `zod`
 * trong chú thích — lần quét tay đầu tiên đã báo oan `LopCuaToiNguon.tsx`
 * (tệp máy chủ, chỉ NHẮC tới `'use client'` trong chú thích).
 *
 * Chạy: node e2e/unit/zod-phia-trinh-duyet.test.mjs
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');

let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${ten}${ok || !ct ? '' : `  → ${ct}`}`);
  if (!ok) loi += 1;
};

function* tep(d) {
  for (const t of readdirSync(d)) {
    const p = join(d, t);
    if (statSync(p).isDirectory()) yield* tep(p);
    else if (/\.tsx?$/.test(t)) yield p;
  }
}

/** Chỉ thị `'use client'` phải là câu lệnh ĐẦU TIÊN của tệp (luật của React). */
const laClient = (s) => /^\s*['"]use client['"]/.test(s);
const NHAP_DAY_DU = /^\s*import\s[^;]*\sfrom\s+['"]zod['"]/m;
const NHAP_MINI = /^\s*import\s[^;]*\sfrom\s+['"]zod\/mini['"]/m;

let soClient = 0;
let soMini = 0;
for (const p of tep(join(GOC, 'src'))) {
  const s = readFileSync(p, 'utf8');
  if (!laClient(s)) continue;
  soClient += 1;
  const ten = relative(GOC, p).split(sep).join('/');
  if (NHAP_MINI.test(s)) soMini += 1;
  check(`${ten} không nhập zod đầy đủ`, !NHAP_DAY_DU.test(s), "đổi sang `import * as z from 'zod/mini'`");
}
check('quét được component client (bộ quét còn sống)', soClient >= 20, `chỉ ${soClient}`);
check('có ít nhất 4 component client dùng zod/mini (luật đang được dùng thật)', soMini >= 4, `chỉ ${soMini}`);

// Hàng rào cho chính biểu thức: một chuỗi mẫu PHẢI khớp, một chú thích KHÔNG khớp.
check('thước bắt được `import { z } from \'zod\';`', NHAP_DAY_DU.test("'use client';\nimport { z } from 'zod';\n"));
check('thước KHÔNG bắt chữ zod trong chú thích', !NHAP_DAY_DU.test("// nhập { z } from 'zod' là sai\n"));
check('thước KHÔNG nhầm zod/mini là bản đầy đủ', !NHAP_DAY_DU.test("import * as z from 'zod/mini';\n"));

console.log(loi ? `\n${loi} lỗi` : `\nOK — ${soClient} component client, ${soMini} dùng zod/mini, không cái nào nhập zod đầy đủ`);
process.exit(loi ? 1 : 0);
