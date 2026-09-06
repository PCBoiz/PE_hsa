/**
 * Unit test — bảng "ai làm được gì" phải KHÔNG TRÔI ĐƯỢC khỏi backend.
 *
 * ── VÌ SAO ĐỌC THẲNG TỆP PYTHON ───────────────────────────────────────────
 *
 * Kiểm `vaiLamDuoc()` trả về đúng ba vai thì chỉ chứng minh bảng ở frontend
 * NHẤT QUÁN VỚI CHÍNH NÓ. Thứ cần chặn là hai bên trôi khỏi nhau — nên phép
 * kiểm phải đọc CẢ HAI: bảng ở `quyenVai.ts` và `common/permissions.py`.
 *
 * Đây đúng cách mà `cong-quan-tri.test.mjs` canh bảng tab, áp cho bảng quyền.
 *
 * ── HAI CHIỀU, KHÔNG PHẢI MỘT ─────────────────────────────────────────────
 *
 *   → mỗi lớp quyền khai ở frontend phải TỒN TẠI ở backend và cho ĐÚNG ngần
 *     ấy vai (không thiếu, không thừa);
 *   ← mỗi `nguon` phải là một view CÓ THẬT, và view ấy phải khai ĐÚNG lớp
 *     quyền mà bảng nói.
 *
 * Chỉ kiểm chiều đầu thì một dòng bịa trong `VIEC` — "Trợ giảng xem được báo
 * cáo phụ huynh, nguồn: parent_report.py" — vẫn xanh, vì `IsSeniorTeachingStaff`
 * tồn tại và đúng vai. Chiều thứ hai mới bắt được là view ấy KHÔNG dùng lớp
 * quyền được khai.
 *
 * Chạy: node e2e/unit/quyen-vai.test.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const BE = join(GOC, '..', 'backend');

const doc = (p) => readFileSync(p, 'utf8');
const PERM = doc(join(BE, 'common', 'permissions.py'));
const BANG = doc(join(GOC, 'src', 'lib', 'quyenVai.ts'));

let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${ten}${ok || !ct ? '' : `  → ${ct}`}`);
  if (!ok) loi += 1;
};

// ── Hằng số vai trò, đọc từ chính `permissions.py` ────────────────────────
const VAI = Object.fromEntries(
  [...PERM.matchAll(/^(ROLE_[A-Z]+)\s*=\s*'([^']+)'/gm)].map((m) => [m[1], m[2]]),
);
check('đọc được sáu hằng số vai từ permissions.py',
  Object.keys(VAI).length === 6, Object.keys(VAI).join(','));

/** Hàm `is_*` nào ứng với vai nào — đọc từ định nghĩa, không gõ tay. */
const HAM_VAI = Object.fromEntries(
  [...PERM.matchAll(/def (is_\w+)\(user\)[\s\S]*?user\.role == (ROLE_[A-Z]+)/g)]
    .map((m) => [m[1], VAI[m[2]]]),
);
check('đọc được ánh xạ hàm is_* → vai',
  Object.keys(HAM_VAI).length >= 5, JSON.stringify(HAM_VAI));

/** Đầu của khối định nghĩa kế tiếp — `class` hoặc `def` ở cột 0. */
const MOC = /\n(?:class |def )/g;

/** Lớp quyền → vai nó cho qua, suy từ các `is_*` mà `has_permission` gọi. */
function vaiCuaLop(ten) {
  const i = PERM.indexOf(`class ${ten}(BasePermission)`);
  if (i === -1) return null;

  /* Cắt tới định nghĩa kế tiếp, `class` HOẶC `def`.
   *
   * Bản đầu chỉ cắt tới `class` kế tiếp. `IsAdminOrAcademic` là lớp CUỐI
   * trong tệp, nên lát cắt chạy tới hết tệp và nuốt luôn `can_see_class` với
   * `visible_class_ids` nằm dưới — hai hàm ấy gọi `is_teacher`/`is_assistant`,
   * nên lớp quyền bị đọc thành "cho cả bốn vai" và phép kiểm báo đỏ trong khi
   * mã hoàn toàn đúng.
   *
   * Chính phép kiểm này bắt được lỗi của CHÍNH NÓ (07/09/2026). Nhắc lại điều
   * đã trả giá nhiều lần trong phiên: đọc kỹ một dòng ĐỎ trước khi tin rằng mã
   * sai — thước hỏng và mã hỏng trông giống hệt nhau. */
  MOC.lastIndex = i + 1;
  const m = MOC.exec(PERM);
  const than = PERM.slice(i, m ? m.index : undefined);

  const ra = new Set();
  for (const k of than.matchAll(/is_(\w+)\((?:request\.)?u(?:ser)?\)/g)) {
    const v = HAM_VAI[`is_${k[1]}`];
    if (v) ra.add(v);
  }
  return [...ra];
}

// ── Chiều 1: mỗi lớp quyền khai ở frontend phải khớp backend ─────────────
const KHAI = [...BANG.matchAll(/^ {2}(Is\w+): \[([^\]]*)\],$/gm)].map((m) => ({
  ten: m[1],
  // Giá trị là các hằng số `VAI_*` của TypeScript; đổi sang chuỗi thật bằng
  // chính `vaiTro.ts` để không chép lần thứ ba.
  bien: m[2].split(',').map((s) => s.trim()).filter(Boolean),
}));
check('đọc được bảng lớp quyền ở quyenVai.ts', KHAI.length === 6, String(KHAI.length));

const TEN_VAI = Object.fromEntries(
  [...doc(join(GOC, 'src', 'lib', 'vaiTro.ts'))
    .matchAll(/export const (VAI_\w+) = '([^']+)'/g)].map((m) => [m[1], m[2]]),
);
check('đọc được hằng số vai ở vaiTro.ts', Object.keys(TEN_VAI).length === 6,
  Object.keys(TEN_VAI).join(','));

for (const k of KHAI) {
  const mongDoi = vaiCuaLop(k.ten);
  if (mongDoi === null) {
    check(`lớp quyền \`${k.ten}\` tồn tại ở backend`, false, 'không thấy trong permissions.py');
    continue;
  }
  const a = k.bien.map((b) => TEN_VAI[b]).filter(Boolean).sort().join(' | ');
  const b = [...mongDoi].sort().join(' | ');
  check(`\`${k.ten}\` cho đúng ngần ấy vai`, a === b, `frontend [${a}] ≠ backend [${b}]`);
}

// ── Chiều 2: mỗi `nguon` phải là view có thật, khai ĐÚNG lớp quyền ────────
const MUC = [...BANG.matchAll(
  /lopQuyen: '(\w+)',\s*\n\s*nguon: '([^']+)'/g,
)].map((m) => ({ lopQuyen: m[1], nguon: m[2] }));
check('đọc được danh sách việc', MUC.length >= 15, String(MUC.length));

for (const v of MUC) {
  const [tep, view] = v.nguon.split('::');
  let py;
  try {
    py = doc(join(BE, ...tep.split('/')));
  } catch {
    check(`\`${v.nguon}\` — tệp tồn tại`, false, 'không mở được ' + tep);
    continue;
  }
  if (!view) {
    // Nguồn cấp TỆP (ví dụ `mockexam/quan_tri.py`): chỉ đòi tệp ấy có khai lớp
    // quyền được nói tới, không đòi tên view.
    check(`\`${v.nguon}\` khai ${v.lopQuyen}`,
      py.includes(`permission_classes = [${v.lopQuyen}]`));
    continue;
  }
  const i = py.indexOf(`class ${view}(`);
  if (i === -1) {
    check(`\`${v.nguon}\` — view tồn tại`, false, `không thấy class ${view}`);
    continue;
  }
  const sau = py.indexOf('\nclass ', i + 1);
  const than = py.slice(i, sau === -1 ? undefined : sau);
  check(`\`${view}\` khai đúng \`${v.lopQuyen}\``,
    than.includes(`permission_classes = [${v.lopQuyen}]`),
    (than.match(/permission_classes = \[[^\]]*\]/) || ['(không khai)'])[0]);
}

// ── Ranh giới đắt nhất, canh riêng ───────────────────────────────────────
// Trợ giảng KHÔNG được xem tờ báo cáo phụ huynh: tờ ấy in email và số điện
// thoại của học viên. Đây là quyết định của anh Sơn (01/09/2026, §8 đặc tả),
// và nó dễ bị nới im lặng bằng cách đổi một chữ `Senior`.
const vaiBaoCao = vaiCuaLop('IsSeniorTeachingStaff') || [];
check('Trợ giảng KHÔNG xem được tờ báo cáo phụ huynh',
  !vaiBaoCao.includes(VAI.ROLE_ASSISTANT), vaiBaoCao.join(' | '));
check('Trợ giảng VẪN điểm danh được',
  (vaiCuaLop('IsTeachingStaff') || []).includes(VAI.ROLE_ASSISTANT));

console.log(loi === 0 ? '\nOK — bảng quyền khớp permissions.py' : `\n${loi} lỗi`);
process.exitCode = loi === 0 ? 0 : 1;
