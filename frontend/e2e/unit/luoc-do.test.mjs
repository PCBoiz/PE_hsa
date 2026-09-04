/**
 * Unit test — LƯỢC ĐỒ nội dung bài: một bảng, hai bên dùng.
 *
 * ── LỖI ĐANG CHẶN LẠI (04/09/2026) ────────────────────────────────────────
 *
 * Ba khoảng số của nội dung bài được viết ở HAI NƠI, bằng HAI NGÔN NGỮ:
 *
 *     backend/lessons/content.py   `not 0 <= xp <= 500`
 *     admin/NoiDungBai.tsx         `min={0} max={500}`
 *
 * Hôm nay chúng khớp. Không có gì giữ cho chúng khớp: đổi trần XP ở Python là
 * biểu mẫu vẫn cho gõ 500, người soạn bấm Lưu và nhận một lỗi máy chủ cho con
 * số mà chính màn hình vừa bảo là hợp lệ.
 *
 * Nay bản gốc nằm ở `backend/lessons/luoc_do.py` — bên CƯỠNG CHẾ — và đi kèm
 * phản hồi của endpoint mà biểu mẫu vốn đã gọi. Biểu mẫu giữ một bảng DỰ PHÒNG
 * để không chết khi lược đồ không tới; phép kiểm này canh đúng bảng dự phòng ấy,
 * vì nó là bản chép DUY NHẤT còn lại.
 *
 * ── VÌ SAO ĐỌC THẲNG TỆP PYTHON ───────────────────────────────────────────
 *
 * Chép ba khoảng số sang đây là dựng bản chép THỨ BA. Phép kiểm phải đọc chính
 * tệp mà máy chủ đọc.
 *
 * Chạy: node e2e/unit/luoc-do.test.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const BE = join(GOC, '..', 'backend');
const PY = readFileSync(join(BE, 'lessons', 'luoc_do.py'), 'utf8');
const FORM = readFileSync(
  join(GOC, 'src', 'app', '(standalone)', 'admin', 'NoiDungBai.tsx'), 'utf8');

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

/** Đọc bảng `SO` từ tệp Python — khoá, min, max. */
function docSO(ma) {
  const khoi = /^SO = \{([\s\S]*?)^\}/m.exec(ma);
  if (!khoi) return null;
  const ra = {};
  const mau = /'([a-z_.]+)':\s*\{\s*'min':\s*(-?\d+),\s*'max':\s*(None|\d+)/g;
  for (const m of khoi[1].matchAll(mau)) {
    ra[m[1]] = { min: Number(m[2]), max: m[3] === 'None' ? null : Number(m[3]) };
  }
  return ra;
}

/** Đọc bảng `DU_PHONG` từ biểu mẫu TypeScript. */
function docDuPhong(ma) {
  const khoi = /const DU_PHONG: Record<string, RangBuocSo> = \{([\s\S]*?)^\};/m.exec(ma);
  if (!khoi) return null;
  const ra = {};
  const mau = /'?([a-zA-Z_.]+)'?:\s*\{\s*min:\s*(-?\d+),\s*max:\s*(null|\d+)/g;
  for (const m of khoi[1].matchAll(mau)) {
    ra[m[1]] = { min: Number(m[2]), max: m[3] === 'null' ? null : Number(m[3]) };
  }
  return ra;
}

const so = docSO(PY);
const du = docDuPhong(FORM);

check('đọc được bảng `SO` từ luoc_do.py', so !== null && Object.keys(so).length > 0,
  JSON.stringify(so));
check('đọc được bảng `DU_PHONG` từ NoiDungBai.tsx', du !== null && Object.keys(du).length > 0,
  JSON.stringify(du));

if (so && du) {
  // ── Cùng tập khoá, cùng giá trị ────────────────────────────────────────
  const kPy = Object.keys(so).sort();
  const kTs = Object.keys(du).sort();
  check('hai bảng có ĐÚNG cùng tập trường', kPy.join(',') === kTs.join(','),
    `python: ${kPy} · form: ${kTs}`);

  for (const k of kPy) {
    if (!du[k]) continue;
    check(`"${k}" khớp min/max`,
      so[k].min === du[k].min && so[k].max === du[k].max,
      `python ${JSON.stringify(so[k])} · form ${JSON.stringify(du[k])}`);
  }

  // ── Và bộ kiểm ở máy chủ phải THẬT SỰ đọc bảng, không còn số viết cứng ──
  //
  // Bảng khớp mà `content.py` vẫn kiểm bằng số viết cứng thì phép kiểm trên chỉ
  // chứng nhận hai bản chép giống nhau, còn thứ CƯỠNG CHẾ là bản thứ ba.
  const CONTENT = readFileSync(join(BE, 'lessons', 'content.py'), 'utf8');
  check('content.py kiểm số QUA bảng (`_kiem_so`), không viết cứng',
    /_kiem_so\(/.test(CONTENT)
      && !/not 0 <= xp <= 500/.test(CONTENT)
      && !/not 5 <= ts <= 3600/.test(CONTENT),
    'còn khoảng số viết cứng trong content.py');

  // ── Biểu mẫu phải DÙNG lược đồ máy chủ, không chỉ mang bảng dự phòng ────
  check('biểu mẫu đọc ràng buộc qua `rb(ban?.schema, …)`',
    (FORM.match(/rb\(ban\?\.schema,/g) || []).length >= 3,
    `${(FORM.match(/rb\(ban\?\.schema,/g) || []).length} chỗ`);
  check('biểu mẫu không còn `min={0} max={500}` viết cứng',
    !/max=\{500\}/.test(FORM) && !/max=\{3600\}/.test(FORM));

  // ── Hai luật chỉ-có-ở-máy-chủ nay có cảnh báo tại chỗ ───────────────────
  check('luoc_do.py khai hai luật ngoài khoảng số',
    /dap_an_trong_lua_chon/.test(PY) && /ma_cau_drill_bat_buoc/.test(PY));
  check('biểu mẫu cảnh báo đáp án không nằm trong lựa chọn',
    /không trùng ĐÚNG một dòng nào/.test(FORM));
  check('biểu mẫu cảnh báo thiếu mã / trùng mã câu phòng luyện',
    /Thiếu mã câu/.test(FORM) && /trùng với một câu khác/.test(FORM));
  check('khối phòng luyện bật `maBatBuoc`', /maBatBuoc\s*\n\s*\/>/.test(FORM));
}

console.log(failures === 0 ? '\nOK — một lược đồ, hai bên dùng' : `\n${failures} lỗi`);
process.exitCode = failures === 0 ? 0 : 1;
