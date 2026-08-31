/**
 * Phân tích THẬT mọi khối mermaid trong docs/ bằng chính mermaid.
 *
 *     node scripts/kiem_so_do.mjs
 *
 * VÌ SAO CẦN. Một sơ đồ sai cú pháp thì KHÔNG HIỆN RA — và một sơ đồ không hiện
 * còn tệ hơn không có sơ đồ, vì người đọc tưởng tài liệu có mà không đọc được,
 * rồi thôi không đi đọc mã nữa (RULES §20).
 *
 * Đếm dấu ``` không chứng minh gì: nó xanh cả khi bên trong là rác. Bản này gọi
 * `mermaid.parse` — đúng bộ phân tích mà trình duyệt dùng.
 *
 * Đã tự kiểm 01/09/2026: cố ý làm hỏng một sơ đồ → script báo ĐỎ đúng khối và
 * đúng số dòng; sửa lại → xanh. Một bộ kiểm không đỏ được là một bộ kiểm giả.
 *
 * Cần `mermaid` và `jsdom`. Chưa có thì:
 *     npm install --no-save mermaid@11 jsdom
 */
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..');
const THU_MUC = join(GOC, 'docs');

function timModule(ten) {
  // Tìm trong node_modules của repo, rồi của scripts/, rồi để Node tự phân giải.
  for (const goc of [GOC, join(GOC, 'scripts'), join(GOC, 'frontend')]) {
    const p = join(goc, 'node_modules', ten);
    if (existsSync(p)) return pathToFileURL(p).href;
  }
  return ten;
}

const { JSDOM } = await import(timModule('jsdom') + '/lib/api.js').catch(() => import('jsdom'));
const dom = new JSDOM('<!doctype html><html><body></body></html>');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
try {
  Object.defineProperty(globalThis, 'navigator',
    { value: dom.window.navigator, configurable: true });
} catch { /* Node mới đã có navigator — dùng luôn cái sẵn có */ }

const { default: mermaid } = await import(
  timModule('mermaid') + '/dist/mermaid.esm.mjs').catch(() => import('mermaid'));

function* tepMd(thu_muc) {
  for (const ten of readdirSync(thu_muc)) {
    const p = join(thu_muc, ten);
    if (statSync(p).isDirectory()) yield* tepMd(p);
    else if (ten.endsWith('.md')) yield p;
  }
}

let tong = 0;
const hong = [];
for (const tep of tepMd(THU_MUC)) {
  // `\r?` — tệp sinh trên Windows từng có CRLF và cả 8 khối lọt khỏi bộ kiểm
  // mà không ai biết. Nay `ve_erd` ghi LF, nhưng giữ `\r?` làm dây bảo hiểm.
  const noi_dung = readFileSync(tep, 'utf8');
  const khoi = [...noi_dung.matchAll(/```mermaid\r?\n([\s\S]*?)```/g)].map((m) => m[1]);
  for (let i = 0; i < khoi.length; i++) {
    tong++;
    const nhan = `${tep.slice(GOC.length + 1)} · khối ${i + 1}`;
    try {
      await mermaid.parse(khoi[i]);
    } catch (e) {
      hong.push(`${nhan}: ${String(e.message || e).split('\n')[0]}`);
    }
  }
}

console.log(`${tong} khối mermaid · ${hong.length} hỏng`);
for (const h of hong) console.log('  HỎNG ' + h);
if (!tong) {
  console.log('  ⚠ KHÔNG tìm thấy khối nào — kiểm lại biểu thức tìm hoặc đường dẫn.');
  process.exit(1);
}
process.exit(hong.length ? 1 : 0);
