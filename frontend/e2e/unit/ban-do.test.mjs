/**
 * Unit test — BẢN ĐỒ HỆ THỐNG: mọi chỗ nối giữa các tầng phải còn nối.
 *
 * Chạy `scripts/ban_do.mjs` hai lượt:
 *
 *   --kiem      hiện trạng phải SẠCH: không lời gọi frontend nào trỏ vào tuyến
 *               không tồn tại, không tuyến MỚI nào mà không ai gọi, không cầu
 *               React → JS cũ nào gãy.
 *   --tu-kiem   cái thước phải ĐỎ ĐƯỢC: cài một lời gọi tới tuyến giả và một
 *               tuyến giả không ai gọi, rồi đòi bản đồ bắt được cả hai.
 *
 * Vì sao cần lượt hai: bản thử đầu tiên của bản đồ (23/09/2026) báo "0 tuyến
 * không ai gọi" — sai, do một chuỗi `/api/*` trong chú thích khớp MỌI tuyến.
 * Một phép kiểm chỉ chạy lượt một sẽ xanh mãi với cái thước mù ấy.
 *
 * Tuyến mới thêm mà chưa có giao diện gọi: hoặc nối nó vào giao diện, hoặc ghi
 * vào `KHONG_CAN_NGUOI_GOI` trong `scripts/ban_do.mjs` KÈM LÝ DO.
 */
import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const BAN_DO = join(GOC, 'scripts', 'ban_do.mjs');

let loi = 0;
function chay(co) {
  const r = spawnSync(process.execPath, [BAN_DO, co], { cwd: GOC, encoding: 'utf8' });
  return { ma: r.status, ra: `${r.stdout || ''}${r.stderr || ''}`.trim() };
}
function check(ten, dung, chiTiet = '') {
  console.log(`  ${dung ? '✓' : '✗'} ${ten}`);
  if (!dung) {
    loi++;
    if (chiTiet) console.log(chiTiet.split('\n').map((d) => `      ${d}`).join('\n'));
  }
}

const kiem = chay('--kiem');
check('hiện trạng: mọi chỗ nối frontend ↔ backend ↔ JS cũ còn nguyên', kiem.ma === 0,
  `${kiem.ra}\n(xem ban_do/BAO_CAO.md)`);

const tuKiem = chay('--tu-kiem');
check('thước đỏ được: bắt lời gọi tới tuyến không tồn tại', /không tồn tại → BẮT ĐƯỢC/.test(tuKiem.ra), tuKiem.ra);
check('thước đỏ được: bắt tuyến không ai gọi', /không ai gọi\s+→ BẮT ĐƯỢC/.test(tuKiem.ra), tuKiem.ra);
// Hai ca thêm 23/09/2026, khi câu ví dụ tấn công trong một khối chú thích của
// dashboard.js được đếm là "người gọi" của /api/admin/users/create.
check('thước không đếm chuỗi trong dòng tiếp nối của chú thích',
  /tiếp nối chú thích → BỎ ĐÚNG/.test(tuKiem.ra), tuKiem.ra);
check("thước không nuốt lời gọi đứng sau '//' của URL hay regex",
  /URL\/regex\s+→ GIỮ ĐÚNG/.test(tuKiem.ra), tuKiem.ra);
check('lượt tự kiểm thoát 0', tuKiem.ma === 0, tuKiem.ra);

console.log(loi === 0 ? '\nOK — bản đồ còn nối và thước còn nhạy' : `\n${loi} lỗi`);
process.exitCode = loi === 0 ? 0 : 1;
