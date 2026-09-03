/**
 * Unit test (Node thuần, không cần runner) — middleware KHÔNG được giết phiên
 * khi backend chỉ đang không với tới được.
 *
 * BUG GỐC (đo 01/09/2026). `src/middleware.ts` tự viết lại lời gọi
 * `/auth/refresh` thay vì gọi `refreshTokens` của `lib/auth.ts`, và bắt lỗi thế
 * này:
 *
 *     try { if (r.ok) moi = await r.json(); } catch { return next(); }
 *     if (!moi?.access) { res.cookies.delete(AT); res.cookies.delete(RT); }
 *
 * `catch` CHỈ chạy khi `fetch` NÉM — mất mạng, DNS hỏng. Một phản hồi **502/503**
 * thì `fetch` thành công, `r.ok` là false, `moi` ở nguyên `null`, và luồng rơi
 * thẳng xuống nhánh xoá cả hai cookie — dưới một chú thích nói "phiên hết thật".
 *
 * Không phải giả thiết: Render gói free ngủ sau ~15 phút, nên 502 lúc máy chủ
 * tỉnh dậy là chuyện thường ngày. Hậu quả: giảng viên đang giữa buổi dạy bị văng
 * ra màn đăng nhập trong khi refresh token còn sống bảy tiếng rưỡi.
 *
 * VÌ SAO KHÔNG KIỂM BẰNG `grep`. Phần 2 của `forum-xss.test.mjs` khẳng định một
 * DÒNG MÃ có chứa `escHtml` — kiểu kiểm ấy xanh cả khi hàm bị đổi nghĩa. Ở đây
 * ta nạp CHÍNH `src/middleware.ts` rồi GỌI nó với một `NextRequest` thật, và chỉ
 * giả lập đúng một thứ: câu trả lời của mạng. Đường đi qua mã là đường thật.
 *
 * Chạy: node e2e/unit/middleware-phien.test.mjs   (exit 0 = pass, 1 = fail)
 */
import { register } from 'node:module';
import { pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const GOC = join(__dirname, '..', '..'); // frontend/

/* Hook phân giải `@/...` và `next/...` — xem `hooks-nap-nguon.mjs`. Phải đăng
   ký TRƯỚC khi nạp `middleware.ts`, nên nạp bằng `await import()` ở dưới chứ
   không bằng `import` tĩnh (lệnh `import` tĩnh chạy trước mọi mã trong tệp). */
register('./hooks-nap-nguon.mjs', import.meta.url);

const { NextRequest } = await import('next/server.js');
const { middleware } = await import(pathToFileURL(join(GOC, 'src', 'middleware.ts')).href);
const { AT, RT } = await import(pathToFileURL(join(GOC, 'src', 'lib', 'auth.ts')).href);

let failures = 0;
function check(name, cond) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name);
    failures++;
  }
}

/** JWT giả, chỉ cần đọc được claim `exp` — middleware KHÔNG xác minh chữ ký. */
function jwt(expLech) {
  const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
  return `${b64({ alg: 'HS256', typ: 'JWT' })}.${b64({
    exp: Math.floor(Date.now() / 1000) + expLech,
  })}.chu-ky-gia`;
}

const AT_HET = jwt(-60); // đã hết hạn → middleware buộc phải đi làm mới
const RT_CON = 'refresh-token-con-song';

function req() {
  const r = new NextRequest('https://pe.test/quan-tri/tong-quan');
  r.cookies.set(AT, AT_HET);
  r.cookies.set(RT, RT_CON);
  return r;
}

/** Cookie nào bị XOÁ trong phản hồi (đặt rỗng + Max-Age=0). */
function biXoa(res) {
  return res.headers
    .getSetCookie()
    .filter((c) => /(^|;)\s*(max-age=0|expires=thu, 01 jan 1970)/i.test(c))
    .map((c) => c.slice(0, c.indexOf('=')));
}

async function voi(fetchGia, than) {
  const that = globalThis.fetch;
  globalThis.fetch = fetchGia;
  try {
    return await than();
  } finally {
    globalThis.fetch = that;
  }
}

const json = (o, status) =>
  new Response(JSON.stringify(o), { status, headers: { 'content-type': 'application/json' } });

// ── 1) 503 — Render đang tỉnh dậy. Phiên PHẢI còn nguyên. ────────────────────
{
  const res = await voi(async () => new Response('bad gateway', { status: 503 }), () =>
    middleware(req()),
  );
  const xoa = biXoa(res);
  check('503: KHÔNG xoá refresh token', !xoa.includes(RT));
  check('503: KHÔNG xoá access token', !xoa.includes(AT));
}

// ── 2) 502 — cùng chuyện, mã khác. ──────────────────────────────────────────
{
  const res = await voi(async () => new Response('', { status: 502 }), () => middleware(req()));
  check('502: KHÔNG xoá refresh token', !biXoa(res).includes(RT));
}

// ── 3) `fetch` NÉM (mất mạng) — phiên PHẢI còn nguyên. ──────────────────────
{
  const res = await voi(
    async () => {
      throw new TypeError('fetch failed');
    },
    () => middleware(req()),
  );
  check('mất mạng: KHÔNG xoá refresh token', !biXoa(res).includes(RT));
}

// ── 4) 401 — máy chủ ĐÃ xem token và từ chối. Phiên hết THẬT. ───────────────
{
  const res = await voi(async () => json({ detail: 'token_not_valid' }, 401), () =>
    middleware(req()),
  );
  const xoa = biXoa(res);
  check('401: CÓ xoá refresh token', xoa.includes(RT));
  check('401: CÓ xoá access token', xoa.includes(AT));
}

// ── 5) 200 — đường hạnh phúc: cookie mới phải được ghi ra. ──────────────────
{
  let goi = null;
  const res = await voi(
    async (url, init) => {
      goi = { url: String(url), body: JSON.parse(init.body) };
      return json({ access: jwt(1800), refresh: 'refresh-moi' }, 200);
    },
    () => middleware(req()),
  );
  const set = res.headers.getSetCookie();
  check('200: gọi đúng /auth/refresh', !!goi && goi.url.endsWith('/auth/refresh'));
  check('200: gửi đúng refresh token đang có', !!goi && goi.body.refresh === RT_CON);
  check(
    '200: ghi access token mới',
    set.some((c) => c.startsWith(`${AT}=`) && !/max-age=0/i.test(c)),
  );
  check(
    '200: ghi refresh token mới (ROTATE_REFRESH_TOKENS)',
    set.some((c) => c.startsWith(`${RT}=refresh-moi`)),
  );
}

// ── 6) Access còn hạn → KHÔNG được gọi mạng lần nào. ────────────────────────
{
  let dem = 0;
  const r = new NextRequest('https://pe.test/dashboard');
  r.cookies.set(AT, jwt(1800));
  r.cookies.set(RT, RT_CON);
  await voi(
    async () => {
      dem++;
      return json({}, 200);
    },
    () => middleware(r),
  );
  check('access còn hạn: không gọi /auth/refresh lần nào', dem === 0);
}

console.log(failures === 0 ? '\nOK — middleware giữ phiên đúng cách' : `\n${failures} lỗi`);
/* `process.exitCode` chứ KHÔNG `process.exit()`. Tệp này đăng ký một loader
   hook, tức có một worker chạy nền; cắt ngang tiến trình trong lúc worker còn
   sống làm libuv nổ assertion trên Windows và trả mã thoát 127 — một lần hỏng
   GIẢ, và hỏng giả trong CI đắt hơn hỏng thật vì nó dạy người ta chạy lại cho
   qua. Đặt mã thoát rồi để Node tự kết thúc thì không có cuộc đua nào.
   (Đo 04/09: chỉ nổ khi stdout có ống dẫn, nên chạy trần thì không thấy.) */
process.exitCode = failures === 0 ? 0 : 1;
