/**
 * Unit test — T18 mức 2: máy chủ trả dữ liệu lệch hình dạng thì màn hình phải
 * nói RA, chứ không hiện như "chưa có dữ liệu".
 *
 * ── VÌ SAO CÓ TỆP NÀY (14/09/2026) ────────────────────────────────────────
 *
 * `serverJson<T>` chỉ ÉP KIỂU: `T` là lời hứa của người viết trang, không phải
 * điều máy chủ làm. Hai lần nó đã im lặng: khoá `klass` → `class` (30/08) làm
 * trang buổi học luôn nói "không mở được lớp"; `class_list` thiếu 5 cột (04/09)
 * làm biểu mẫu sửa lớp xoá trắng link họp. Cả hai đều KHÔNG có dòng lỗi nào.
 *
 * Hai phần:
 *   1. Gọi `kiemHinhDang` THẬT (qua hook nạp nguồn, không chép mã) — lệch khoá
 *      là `ok: false` và câu lỗi nêu đúng đường tới ô lệch; khớp là `ok: true`;
 *      máy chủ THÊM khoá thì vẫn qua (`looseObject`).
 *   2. Quét tĩnh: MỌI lời gọi `serverJson<…>(` trong `src/app` phải truyền hình
 *      dạng làm tham số thứ ba. Không có phần này thì trang viết sau quên là
 *      quên im lặng — đúng cái lỗi tệp này sinh ra để chặn.
 *
 * Chạy: node e2e/unit/hinh-dang.test.mjs
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { register } from 'node:module';
import { dirname, join, relative, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
register('./hooks-nap-nguon.mjs', import.meta.url);

const { kiemHinhDang } = await import(pathToFileURL(join(GOC, 'src', 'lib', 'server-api.ts')).href);
const { z } = await import('zod');

let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${ten}${ok || !ct ? '' : `  → ${ct}`}`);
  if (!ok) loi += 1;
};

// ── 1. Hành vi thật ─────────────────────────────────────────────────────────
console.log('kiemHinhDang:');
const HD = z.looseObject({
  class: z.looseObject({ id: z.number(), name: z.string() }).optional(),
  sessions: z.array(z.looseObject({ id: z.number(), startsAt: z.string().nullable() })),
});

// Bịt console.error trong lúc thử — lỗi cố ý không phải lỗi của bộ kiểm.
const errCu = console.error;
const daGhi = [];
console.error = (...a) => daGhi.push(a.join(' '));
try {
  const khop = kiemHinhDang('/x', { class: { id: 1, name: 'A' }, sessions: [{ id: 2, startsAt: null }] }, 200, HD);
  check('khớp → ok:true, giữ nguyên dữ liệu', khop.ok && khop.data.sessions[0].id === 2);

  const them = kiemHinhDang('/x', { class: { id: 1, name: 'A', them: 1 }, sessions: [], laKhoaMoi: true }, 200, HD);
  check('máy chủ THÊM khoá → vẫn qua (looseObject)', them.ok);

  const doiTen = kiemHinhDang('/x', { klass: { id: 1, name: 'A' }, sessions: [] }, 200, HD);
  // `class` là optional nên `klass` thay `class` KHÔNG lệch — đúng là lỗi 30/08
  // cũ không bắt được bằng optional; vì thế `HD_CHI_TIET_LOP` để trang tự xử
  // "không có class" thành lỗi. Ở đây chỉ ghi nhận hành vi để người sau đọc.
  check('khoá optional đổi tên → không phải lỗi hình dạng (trang phải tự xử)', doiTen.ok);

  const lechSau = kiemHinhDang('/x', { sessions: [{ id: 2, startsAt: null }, { id: 3, starts_at: null }] }, 200, HD);
  check('lệch ở phần tử [1] → ok:false', !lechSau.ok);
  check('  câu lỗi nêu đúng đường `sessions[1].startsAt`',
    !lechSau.ok && lechSau.message.includes('sessions[1].startsAt'), lechSau.ok ? '' : lechSau.message);
  check('  giữ mã trạng thái của máy chủ (200)', !lechSau.ok && lechSau.status === 200);

  const saiKieu = kiemHinhDang('/x', { sessions: [{ id: '2', startsAt: null }] }, 200, HD);
  check('sai KIỂU (chuỗi thay số) → ok:false', !saiKieu.ok);

  const goc = kiemHinhDang('/x', { classes: [] }, 200, HD);
  check('thiếu khoá gốc → câu lỗi nêu `sessions`', !goc.ok && goc.message.includes('sessions'));

  // Ba lần lệch (phần tử [1], sai kiểu, thiếu khoá gốc) — mỗi lần một dòng, để
  // nhật ký máy chủ (Render) thấy được ngay cả khi không ai báo.
  check('mỗi lần lệch có một dòng console.error [hinh-dang]',
    daGhi.length === 3 && daGhi.every((d) => d.includes('[hinh-dang]')), `ghi ${daGhi.length} dòng`);
} finally {
  console.error = errCu;
}

// ── 2. Quét tĩnh: mọi lời gọi serverJson trong src/app phải có hình dạng ───
console.log('mọi serverJson< trong src/app có tham số hình dạng:');

function* tep(d) {
  for (const t of readdirSync(d)) {
    const p = join(d, t);
    if (statSync(p).isDirectory()) yield* tep(p);
    else if (/\.tsx?$/.test(t)) yield p;
  }
}

/** Đếm tham số ở tầng ngoặc ngoài cùng của `serverJson<…>(…)` bắt đầu tại `i`. */
function soThamSo(s, i) {
  // Nhảy qua tham số kiểu `<…>` (có thể lồng).
  let j = s.indexOf('<', i);
  let sau = 0;
  for (; j < s.length; j += 1) {
    if (s[j] === '<') sau += 1;
    else if (s[j] === '>') { sau -= 1; if (sau === 0) break; }
  }
  j = s.indexOf('(', j);
  let ngoac = 0;
  let dem = 0;
  let coGi = false;
  let chuoi = null;
  for (let k = j; k < s.length; k += 1) {
    const c = s[k];
    if (chuoi) { if (c === chuoi && s[k - 1] !== '\\') chuoi = null; continue; }
    if (c === "'" || c === '"' || c === '`') { chuoi = c; coGi = true; continue; }
    if ('([{'.includes(c)) { ngoac += 1; continue; }
    if (')]}'.includes(c)) {
      ngoac -= 1;
      if (ngoac === 0) return dem + (coGi ? 1 : 0);
      continue;
    }
    if (c === ',' && ngoac === 1) { dem += 1; coGi = false; continue; }
    if (!/\s/.test(c)) coGi = true;
  }
  return dem;
}

let tong = 0;
for (const p of tep(join(GOC, 'src', 'app'))) {
  const s = readFileSync(p, 'utf8');
  const re = /serverJson</g;
  let m;
  while ((m = re.exec(s))) {
    // Bỏ qua chữ `serverJson<T>` trong CHÚ THÍCH (dòng mở đầu bằng `*` hay `//`)
    // — ba trang nhắc tới nó trong lời cảnh báo cũ về chính lỗi này.
    const dauDong = s.lastIndexOf('\n', m.index) + 1;
    if (/^\s*(\*|\/\/)/.test(s.slice(dauDong, m.index))) continue;
    tong += 1;
    const n = soThamSo(s, m.index);
    const dong = s.slice(0, m.index).split('\n').length;
    check(`${relative(GOC, p).split(sep).join('/')}:${dong}`, n >= 3, `${n} tham số — thiếu hình dạng`);
  }
}
check('có ít nhất 20 lời gọi được quét (bộ quét còn sống)', tong >= 20, `quét ${tong}`);

console.log(loi ? `\n${loi} lỗi` : '\nTất cả đạt');
process.exit(loi ? 1 : 0);
