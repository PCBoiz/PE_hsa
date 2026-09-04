/**
 * Unit test — IP khách gửi xuống Django phải do NỀN TẢNG tính, và chỉ gửi khi
 * có bí mật.
 *
 * ── LỖI ĐANG CHẶN LẠI (05/09/2026) ────────────────────────────────────────
 *
 * `proxy.ts` gỡ `x-forwarded-for` của khách — ĐÚNG, vì để nguyên thì trình
 * duyệt tự đặt được khoá giới hạn tần suất (đo 30/08: 300 lần đăng nhập kèm
 * XFF ngẫu nhiên thì **300 lần đều lọt**, trong khi cùng 300 lần với IP cố định
 * bị chặn 200 lần).
 *
 * Nhưng `fetch` của Node không thêm lại, nên Django chỉ thấy IP egress của
 * Vercel: **mọi người dùng thật chung MỘT xô**. Với trần 5 lượt đăng nhập/phút,
 * người thứ sáu bị chặn dù ngồi ở đầu kia đất nước — hàng rào chống vét cạn
 * biến thành máy sinh sự cố cho một lớp 30 em vào học cùng giờ.
 *
 * Chạy: node e2e/unit/ip-khach.test.mjs
 */
import { readFileSync } from 'node:fs';
import { register } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
register('./hooks-nap-nguon.mjs', import.meta.url);

const { ipKhach } = await import('file://' + join(GOC, 'src', 'lib', 'proxy.ts').replace(/\\/g, '/'));

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

const req = (h) => new Request('https://x/api/y', { headers: h });

check('rút được `ipKhach`', typeof ipKhach === 'function');

// ── `x-real-ip` là thứ Vercel đặt: ưu tiên nó ──────────────────────────────
check('ưu tiên `x-real-ip`',
  ipKhach(req({ 'x-real-ip': '203.0.113.9', 'x-forwarded-for': '9.9.9.9' })) === '203.0.113.9');

// ── Không có `x-real-ip` → phần tử CUỐI của `x-forwarded-for` ─────────────
//
// Mỗi chặng NỐI THÊM VÀO CUỐI, nên phần đầu là thứ khách tự viết. Lấy phần đầu
// là lấy đúng con số kẻ tấn công gửi lên — và khi ấy bản vá này TỆ HƠN hiện
// trạng, vì nó phát con số giả đi kèm một bí mật nói "hãy tin tôi".
check('lấy phần tử CUỐI của `x-forwarded-for`',
  ipKhach(req({ 'x-forwarded-for': '9.9.9.9, 203.0.113.9' })) === '203.0.113.9',
  ipKhach(req({ 'x-forwarded-for': '9.9.9.9, 203.0.113.9' })));
check('một chặng duy nhất vẫn đúng',
  ipKhach(req({ 'x-forwarded-for': '203.0.113.9' })) === '203.0.113.9');
check('bỏ khoảng trắng thừa',
  ipKhach(req({ 'x-forwarded-for': ' 9.9.9.9 ,  203.0.113.9  ' })) === '203.0.113.9');
check('không có header nào → null', ipKhach(req({})) === null);
check('header rỗng → null', ipKhach(req({ 'x-forwarded-for': '  ' })) === null);

// ── Chỉ gửi khi CÓ bí mật, và bí mật phải đủ dài ──────────────────────────
//
// Kiểm trên mã nguồn: `forwardHeaders` không xuất ra được (nó đọc cookie và
// gọi mạng), nhưng điều kiện gác thì soi được — và đó mới là thứ hỏng được.
const MA = readFileSync(join(GOC, 'src', 'lib', 'proxy.ts'), 'utf8');
const boChuThich = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '))
  .replace(/(^|[^:])\/\/[^\n]*/g, (m, p) => p + ' '.repeat(m.length - p.length));
const ma = boChuThich(MA);

check('chỉ gửi header khi bí mật ĐỦ DÀI và có IP',
  /if\s*\(\s*biMat\.length\s*>=\s*16\s*&&\s*ip\s*\)/.test(ma),
  'không thấy cửa gác `biMat.length >= 16 && ip`');
check('gửi cả hai header, không chỉ IP',
  /X-PE-Client-IP/.test(ma) && /X-PE-Proxy-Secret/.test(ma));

// Bí mật KHÔNG được mang tiền tố `NEXT_PUBLIC_` — Next nhúng mọi biến như thế
// vào gói JavaScript gửi cho MỌI trình duyệt, tức phát bí mật cho cả kẻ tấn công.
check('bí mật đọc từ biến SERVER-SIDE, không `NEXT_PUBLIC_`',
  /process\.env\.PE_PROXY_SECRET/.test(ma) && !/NEXT_PUBLIC_[A-Z_]*SECRET/.test(ma));

// Và `x-forwarded-for` của khách vẫn phải bị GỠ — bản vá này không được lặng lẽ
// mở lại đường cũ.
check('vẫn gỡ `x-forwarded-for` của khách',
  /'x-forwarded-for'/.test(ma) && /const STRIP = new Set\(\[/.test(ma));

console.log(failures === 0 ? '\nOK — IP khách do nền tảng tính, và chỉ gửi khi có bí mật'
  : `\n${failures} lỗi`);
process.exitCode = failures === 0 ? 0 : 1;
