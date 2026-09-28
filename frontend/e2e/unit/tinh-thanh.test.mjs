/**
 * Unit test — danh sách 34 tỉnh/thành ở trình duyệt và ở máy chủ phải GIỐNG HỆT.
 *
 * ── VÌ SAO (V-m, 25/09/2026) ─────────────────────────────────────────────
 *
 * Ô "Tỉnh/Thành phố" của hồ sơ học viên dựng từ `src/lib/tinhThanh.ts`; máy chủ
 * (`backend/teaching/ho_so.py`) chỉ nhận giá trị nằm trong `teaching/tinh_thanh.py`. Hai
 * bản lệch nhau một dấu ("Khánh Hoà" / "Khánh Hòa") thì ô chọn gửi đúng thứ nó hiện, còn
 * máy chủ trả "không có trong danh sách" — lỗi mà người dùng không có cách nào tự sửa.
 *
 * Chạy: node e2e/unit/tinh-thanh.test.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const TS = readFileSync(join(GOC, 'src', 'lib', 'tinhThanh.ts'), 'utf8');
const PY = readFileSync(join(GOC, '..', 'backend', 'teaching', 'tinh_thanh.py'), 'utf8');

let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${ten}${ok || !ct ? '' : `  → ${ct}`}`);
  if (!ok) loi += 1;
};

/** Các chuỗi '…' nằm giữa hai dấu mở/đóng của danh sách. */
function cat(van, mo, dong) {
  const i = van.indexOf(mo);
  const j = van.indexOf(dong, i + mo.length);
  if (i < 0 || j < 0) return [];
  return [...van.slice(i + mo.length, j).matchAll(/'([^']+)'/g)].map((m) => m[1]);
}

const trinhDuyet = cat(TS, 'TINH_THANH: readonly string[] = [', '] as const');
const mayChu = cat(PY, 'TINH_THANH = (', '\n)');

check('đọc được danh sách ở trình duyệt', trinhDuyet.length > 0, String(trinhDuyet.length));
check('đọc được danh sách ở máy chủ', mayChu.length > 0, String(mayChu.length));
check('đúng 34 đơn vị (sau sáp nhập 2025)', mayChu.length === 34, String(mayChu.length));
check('không tên nào lặp', new Set(mayChu).size === mayChu.length);
check('hai danh sách GIỐNG HỆT, cùng thứ tự', JSON.stringify(trinhDuyet) === JSON.stringify(mayChu),
  trinhDuyet.filter((t, i) => t !== mayChu[i]).join(', ') || `${trinhDuyet.length} ≠ ${mayChu.length}`);

console.log(loi === 0 ? '\nOK — danh sách tỉnh/thành khớp hai phía' : `\n${loi} lỗi`);
process.exitCode = loi === 0 ? 0 : 1;
