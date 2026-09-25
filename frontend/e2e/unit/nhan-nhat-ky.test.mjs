/**
 * Unit test — mọi mã hành động trong `common/audit.py` phải có tên tiếng Việt
 * ở màn hình Nhật ký.
 *
 * ── VÌ SAO CÓ TỆP NÀY (13/09/2026) ────────────────────────────────────────
 *
 * Bảng `VIEC` ở `quan-tri/nhat-ky/page.tsx` có sẵn một chú thích cảnh báo đúng
 * chuyện này: "thêm hành động mới ở `common/audit.py` mà quên chỗ này, và mã máy
 * lại lọt ra màn hình". Chú thích viết 31/08. Đo 13/09: **15 mã** vẫn lọt —
 * cả nhóm giao bài/chấm điểm, giáo trình và đề thi thử, thêm từ 31/08 tới 04/09.
 *
 * Tức lời dặn trong chú thích KHÔNG giữ được gì. Người thêm hằng số ở backend
 * không mở tệp frontend, nên không bao giờ đọc thấy lời dặn. Phép kiểm này đọc
 * CẢ HAI tệp và đỏ đúng ở CI của người thêm hằng số — chỗ duy nhất họ nhìn.
 *
 * Chạy: node e2e/unit/nhan-nhat-ky.test.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const AUDIT = readFileSync(join(GOC, '..', 'backend', 'common', 'audit.py'), 'utf8');
// Bảng nhãn dời sang `src/lib/viecNhatKy.ts` (V-n, 25/09/2026) — Nhật ký VÀ lịch sử lớp cùng đọc.
const TRANG = readFileSync(join(GOC, 'src', 'lib', 'viecNhatKy.ts'), 'utf8');

let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${ten}${ok || !ct ? '' : `  → ${ct}`}`);
  if (!ok) loi += 1;
};

// Hằng số ở ĐẦU DÒNG, dạng `TEN = 'doi_tuong.viec'`. Neo `^` để không khớp
// một ví dụ nằm trong chú thích.
const MA = [...AUDIT.matchAll(/^[A-Z][A-Z_]+ = '([a-z_]+(?:\.[a-z_]+)+)'/gm)].map((m) => m[1]);

// Cắt đúng thân `const VIEC … };` — tệp còn bảng `VAI` cũng dạng khoá: giá trị.
const iDau = TRANG.indexOf('export const VIEC');
const iCuoi = TRANG.indexOf('\n};', iDau);
const THAN = iDau === -1 ? '' : TRANG.slice(iDau, iCuoi);
const NHAN = new Set([...THAN.matchAll(/^\s*'([a-z_.]+)':\s*'[^']+'/gm)].map((m) => m[1]));

// Hai phép kiểm chống hằng đúng: đọc hỏng một trong hai tệp thì vòng dưới
// không có gì để so, và "0 mã thiếu nhãn" xanh oan.
check('đọc được mã hành động từ audit.py', MA.length >= 20, `${MA.length} mã`);
check('đọc được bảng VIEC', NHAN.size >= 10, `${NHAN.size} nhãn`);

const thieu = MA.filter((m) => !NHAN.has(m));
check('mọi mã hành động đều có tên tiếng Việt', thieu.length === 0, thieu.join(', '));

// Chiều ngược: nhãn cho một mã không còn tồn tại là rác, và nó che mất việc
// một mã đã bị đổi tên (màn hình vẫn "có nhãn" — cho cái tên cũ).
const thua = [...NHAN].filter((m) => !MA.includes(m));
check('không có nhãn cho mã không còn tồn tại', thua.length === 0, thua.join(', '));

console.log(loi === 0 ? '\nOK — nhật ký không lọt mã máy' : `\n${loi} lỗi`);
process.exitCode = loi === 0 ? 0 : 1;
