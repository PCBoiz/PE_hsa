/**
 * Unit test — ô "Ghi nhớ đăng nhập" (góp ý TopHSA #1, 24/09/2026) ở tầng Next.
 *
 * Backend đặt claim `nho` vào refresh token (và access — SimpleJWT chép sang):
 * `backend/accounts/ghi_nho.py`. Tầng Next quyết THỜI HẠN COOKIE theo claim ấy:
 *   · có `nho`  → cookie có Max-Age: access 30 phút, refresh = thời gian còn lại
 *                 tới `exp` (≤ 30 ngày) — máy riêng, mở lại trình duyệt vẫn vào;
 *   · không     → cookie PHIÊN (không Max-Age): đóng trình duyệt là hết — máy
 *                 dùng chung ở trung tâm.
 *
 * Hai nơi ghi cookie token, phải cùng một luật — lệch một nơi là phiên "không ghi
 * nhớ" bị lén thành cookie sống lâu ở lần làm mới đầu tiên:
 *   1. `setTokenCookies` (`lib/auth.ts`) — đăng nhập, làm mới trong `/api/*`;
 *   2. `proxy` (`src/proxy.ts`) — làm mới trước khi dựng trang.
 * Nạp CHÍNH hai tệp ấy, chỉ giả lập câu trả lời mạng.
 *
 * Chạy: node e2e/unit/ghi-nho-phien.test.mjs   (exit 0 = pass, 1 = fail)
 */
import { register } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const GOC = join(__dirname, '..', '..');
register('./hooks-nap-nguon.mjs', import.meta.url);

const { NextRequest } = await import('next/server.js');
const { proxy } = await import(pathToFileURL(join(GOC, 'src', 'proxy.ts')).href);
const { AT, RT, setTokenCookies } = await import(pathToFileURL(join(GOC, 'src', 'lib', 'auth.ts')).href);

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

const NGAY = 86400;
const bayGio = () => Math.floor(Date.now() / 1000);
/** JWT giả — tầng Next chỉ ĐỌC claim, không xác minh chữ ký (Django làm việc ấy). */
function jwt(claims) {
  const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
  return `${b64({ alg: 'HS256', typ: 'JWT' })}.${b64(claims)}.chu-ky-gia`;
}
const AT_NHO = jwt({ exp: bayGio() + 1800, nho: true });
const RT_NHO = jwt({ exp: bayGio() + 30 * NGAY, nho: true });
const AT_THUONG = jwt({ exp: bayGio() + 1800 });
const RT_THUONG = jwt({ exp: bayGio() + 8 * 3600 });

/** Max-Age của cookie `ten` trong các Set-Cookie; null = cookie phiên; undefined = không đặt. */
function maxAge(setCookies, ten) {
  const c = setCookies.find((s) => s.startsWith(ten + '=') && !/max-age=0\b/i.test(s));
  if (!c) return undefined;
  const m = /max-age=(\d+)/i.exec(c);
  return m ? Number(m[1]) : null;
}

// ── 1) setTokenCookies: đăng nhập KHÔNG tick → hai cookie phiên ──────────────
{
  const res = new Response('{}');
  setTokenCookies(res, AT_THUONG, RT_THUONG);
  const sc = res.headers.getSetCookie();
  check('không ghi nhớ: access là cookie phiên', maxAge(sc, AT) === null, maxAge(sc, AT));
  check('không ghi nhớ: refresh là cookie phiên', maxAge(sc, RT) === null, maxAge(sc, RT));
}

// ── 2) setTokenCookies: có tick → access 30 phút, refresh ~30 ngày ──────────
{
  const res = new Response('{}');
  setTokenCookies(res, AT_NHO, RT_NHO);
  const sc = res.headers.getSetCookie();
  check('ghi nhớ: access sống 30 phút', maxAge(sc, AT) === 1800, maxAge(sc, AT));
  const rt = maxAge(sc, RT);
  check('ghi nhớ: refresh sống ~30 ngày (theo exp của token)', rt > 29 * NGAY && rt <= 30 * NGAY, rt);
}

// ── 3) Token hỏng / không phải JWT → cookie phiên, không ném ────────────────
{
  const res = new Response('{}');
  setTokenCookies(res, 'khong-phai-jwt', 'a.b.c');
  const sc = res.headers.getSetCookie();
  check('token lạ: vẫn ghi, là cookie phiên', maxAge(sc, AT) === null && maxAge(sc, RT) === null);
}

// ── 4) proxy (làm mới trước khi dựng trang) theo đúng luật ──────────────────
async function lamMoi(moi) {
  const that = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(JSON.stringify(moi), { status: 200, headers: { 'content-type': 'application/json' } });
  try {
    const r = new NextRequest('https://pe.test/giang-day');
    r.cookies.set(AT, jwt({ exp: bayGio() - 60 }));     // hết hạn → buộc làm mới
    r.cookies.set(RT, 'refresh-cu');
    return (await proxy(r)).headers.getSetCookie();
  } finally {
    globalThis.fetch = that;
  }
}
{
  const sc = await lamMoi({ access: AT_THUONG, refresh: RT_THUONG });
  check('proxy, không ghi nhớ: refresh mới là cookie phiên', maxAge(sc, RT) === null, maxAge(sc, RT));
  check('proxy, không ghi nhớ: access mới là cookie phiên', maxAge(sc, AT) === null, maxAge(sc, AT));
}
{
  const sc = await lamMoi({ access: AT_NHO, refresh: RT_NHO });
  const rt = maxAge(sc, RT);
  check('proxy, ghi nhớ: refresh mới sống ~30 ngày', rt > 29 * NGAY && rt <= 30 * NGAY, rt);
  check('proxy, ghi nhớ: access mới sống 30 phút', maxAge(sc, AT) === 1800, maxAge(sc, AT));
}

console.log(failures ? `\n${failures} phép kiểm HỎNG` : '\nOK — thời hạn cookie theo đúng ô ghi nhớ ở cả hai nơi ghi');
process.exit(failures ? 1 : 0);
