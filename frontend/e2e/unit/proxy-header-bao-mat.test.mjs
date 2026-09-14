/**
 * Unit test — proxy `/api/*` KHÔNG chép header an ninh trang của Django.
 *
 * ── LỖI ĐANG CHẶN LẠI (14/09/2026) ────────────────────────────────────────
 *
 * `next.config.ts` gửi CSP `frame-ancestors 'none'` + `X-Frame-Options: DENY`…
 * cho mọi phản hồi của miền Vercel. Đo trên production sau deploy: `/api/user`
 * lại mang CSP `frame-ancestors 'self'` và `X-Frame-Options: SAMEORIGIN` — của
 * DJANGO, do `passThrough` chép nguyên header backend, và trên Vercel header do
 * hàm đặt thắng header cấu hình. `next start` ở máy làm ngược lại nên
 * `scripts/do_dau_bao_mat.mjs` chạy trên máy báo ĐẠT; chỉ production thấy.
 *
 * Phép kiểm này không cần Vercel: nó hỏi thẳng hàm có bỏ các header ấy không.
 *
 * Chạy: node e2e/unit/proxy-header-bao-mat.test.mjs
 */
import { register } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
register('./hooks-nap-nguon.mjs', import.meta.url);

const { passThrough, HEADER_AN_NINH_TRANG } = await import(
  'file://' + join(GOC, 'src', 'lib', 'proxy.ts').replace(/\\/g, '/')
);

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

check('rút được `passThrough`', typeof passThrough === 'function');

// Đúng bộ header Django thật gửi (đọc từ production 14/09/2026), cộng hai thứ
// phải GIỮ: kiểu nội dung và một header nghiệp vụ.
const upstream = new Response('{"detail":"x"}', {
  status: 401,
  headers: {
    'Content-Type': 'application/json',
    'Content-Security-Policy': "default-src 'self'; frame-ancestors 'self'",
    'X-Frame-Options': 'SAMEORIGIN',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'same-origin',
    'Cache-Control': 'private, no-store',
    'Set-Cookie': 'csrftoken=abc',
  },
});
const body = await upstream.clone().arrayBuffer();
const ra = passThrough(upstream, body);

for (const ten of ['content-security-policy', 'x-frame-options', 'x-content-type-options', 'referrer-policy']) {
  check(`bỏ \`${ten}\` của Django`, !ra.headers.has(ten), ra.headers.get(ten));
}
check('bộ bỏ khớp sáu header `next.config.ts` gửi',
  ['content-security-policy', 'x-frame-options', 'x-content-type-options',
    'referrer-policy', 'permissions-policy', 'cross-origin-opener-policy'].every((h) => HEADER_AN_NINH_TRANG.has(h)));

// Không được bỏ nhầm thứ nghiệp vụ cần.
check('giữ `content-type`', ra.headers.get('content-type') === 'application/json');
check('giữ `cache-control` (dữ liệu học viên không vào bộ đệm)', ra.headers.get('cache-control') === 'private, no-store');
check('vẫn bỏ `set-cookie` như trước', !ra.headers.has('set-cookie'));
check('giữ mã trạng thái', ra.status === 401);
check('giữ thân', (await ra.text()) === '{"detail":"x"}');

if (failures) {
  console.error(`\n${failures} phép kiểm HỎNG`);
  process.exit(1);
}
console.log('\nTất cả xanh');
