/**
 * Unit test — `apiFetch` phải khai `Content-Type: application/json` cho thân
 * là chuỗi.
 *
 * ── VÌ SAO CÓ TỆP NÀY (14/09/2026) ────────────────────────────────────────
 *
 * Rà luồng học viên đầu-cuối: em bấm "Nộp bài" → "Yêu cầu không hợp lệ", máy
 * chủ trả **415**. Nguyên nhân: `apiFetch(path, {method:'POST', body:
 * JSON.stringify(...)})` không khai kiểu nội dung, trình duyệt gắn
 * `text/plain;charset=UTF-8`, DRF từ chối. Bốn nơi cùng lỗi: em nộp bài, giảng
 * viên giao bài, sửa bài đã giao, chấm bài — tức cả tính năng bài tập chết
 * qua giao diện, trong khi mọi phép kiểm backend vẫn xanh vì chúng gọi thẳng
 * view với `format='json'`.
 *
 * Hai phần: gọi `apiFetch` THẬT với `fetch` giả (đọc header nó gửi), và quét
 * tĩnh mọi nơi gọi để không ai đặt tay một kiểu nội dung sai cho thân chuỗi.
 *
 * Chạy: node e2e/unit/kieu-noi-dung.test.mjs
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { register } from 'node:module';
import { dirname, join, relative, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
register('./hooks-nap-nguon.mjs', import.meta.url);
const { apiFetch } = await import(pathToFileURL(join(GOC, 'src', 'lib', 'api.ts')).href);

let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${ten}${ok || !ct ? '' : `  → ${ct}`}`);
  if (!ok) loi += 1;
};

// ── 1. Hành vi thật ─────────────────────────────────────────────────────────
const goc = globalThis.fetch;
const daGoi = [];
globalThis.fetch = async (url, opts) => {
  daGoi.push({ url, opts });
  return { ok: true, status: 200, clone: () => ({ json: async () => ({}) }) };
};
try {
  await apiFetch('/api/assignments', { method: 'POST', body: JSON.stringify({ a: 1 }) });
  const h1 = new Headers(daGoi[0].opts.headers);
  check('thân chuỗi → Content-Type: application/json',
    h1.get('content-type') === 'application/json', String(h1.get('content-type')));
  check('vẫn gửi kèm cookie', daGoi[0].opts.credentials === 'same-origin');
  check('không đụng method/body', daGoi[0].opts.method === 'POST' && daGoi[0].opts.body === '{"a":1}');

  await apiFetch('/api/x', { method: 'POST', body: JSON.stringify({}), headers: { 'Content-Type': 'application/merge-patch+json' } });
  check('nơi gọi tự khai kiểu thì GIỮ NGUYÊN',
    new Headers(daGoi[1].opts.headers).get('content-type') === 'application/merge-patch+json');

  // FormData: trình duyệt phải tự đặt `multipart/form-data; boundary=…`.
  // Đặt tay `application/json` ở đây là phá đường tải tệp (nhập đề thi thử).
  const fd = new FormData();
  fd.append('file', new Blob(['x']), 'de.json');
  await apiFetch('/api/admin/mock-exams/import', { method: 'POST', body: fd });
  const h3 = new Headers(daGoi[2].opts.headers);
  check('FormData → KHÔNG tự đặt kiểu nội dung', !h3.has('content-type'), String(h3.get('content-type')));

  await apiFetch('/api/assignments');
  check('GET không thân → không thêm gì', !new Headers(daGoi[3].opts.headers).has('content-type'));
} finally {
  globalThis.fetch = goc;
}

// ── 2. Quét tĩnh: không nơi gọi nào khai kiểu SAI cho thân chuỗi ────────────
console.log('mọi nơi gọi apiFetch:');
function* tep(d) {
  for (const t of readdirSync(d)) {
    const p = join(d, t);
    if (statSync(p).isDirectory()) yield* tep(p);
    else if (/\.tsx?$/.test(t)) yield p;
  }
}
let tong = 0;
for (const p of tep(join(GOC, 'src'))) {
  const s = readFileSync(p, 'utf8');
  for (const m of s.matchAll(/apiFetch\(/g)) {
    const dauDong = s.lastIndexOf('\n', m.index) + 1;
    if (/^\s*(\*|\/\/)/.test(s.slice(dauDong, m.index))) continue;
    let i = s.indexOf('(', m.index);
    let d = 0;
    let j = i;
    for (; j < s.length; j += 1) {
      if (s[j] === '(') d += 1;
      else if (s[j] === ')') { d -= 1; if (d === 0) break; }
    }
    const goi = s.slice(m.index, j + 1);
    if (!/body:/.test(goi)) continue;
    tong += 1;
    const chuoi = /body:\s*JSON\.stringify/.test(goi);
    const kieu = /'Content-Type':\s*'([^']+)'/.exec(goi)?.[1];
    const dong = s.slice(0, m.index).split('\n').length;
    const ten = `${relative(GOC, p).split(sep).join('/')}:${dong}`;
    // Thân chuỗi: khai gì cũng được MIỄN LÀ json; không khai thì `apiFetch` lo.
    check(ten, !chuoi || !kieu || /json/.test(kieu), `thân JSON nhưng khai '${kieu}'`);
  }
}
check('có quét được nơi gọi có thân (bộ quét còn sống)', tong >= 15, `chỉ ${tong}`);

console.log(loi ? `\n${loi} lỗi` : '\nOK — mọi lời gọi có thân đều khai đúng kiểu');
process.exit(loi ? 1 : 0);
