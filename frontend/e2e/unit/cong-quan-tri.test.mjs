/**
 * Unit test — cổng vai trò ở frontend phải KHỚP `permission_classes` ở backend.
 *
 * ── LỖI ĐANG CHẶN LẠI (đo 04/09/2026) ─────────────────────────────────────
 *
 * Có BỐN bảng trả lời cùng một câu hỏi "ai vào được trang nào", và chúng lệch:
 *
 *   `quan-tri/layout.tsx`  · `role !== 'admin'` → chặn tất cả trừ quản trị viên
 *   `AdminNav`             · hiện ĐỦ mọi tab cho ai qua được cổng trên
 *   `admin/page.tsx`       · `new Set(['admin', 'Biên tập nội dung'])` gõ tay
 *   backend                · `/api/admin/classes`, `/api/admin/terms` mở cho
 *                            `Quản lý học vụ` (`IsAdminOrAcademic`)
 *
 * Tức cổng chặn `Quản lý học vụ` khỏi ĐÚNG hai trang backend đã mở cho họ —
 * trong khi vai ấy sinh ra để KHÔNG phải cấp quyền quản trị cho người xếp lớp.
 *
 * ── VÌ SAO KIỂM BẰNG CÁCH ĐỌC MÃ PYTHON ───────────────────────────────────
 *
 * Kiểm `tabsCho('Quản lý học vụ')` trả về đúng hai href thì chỉ chứng minh bảng
 * ở frontend NHẤT QUÁN VỚI CHÍNH NÓ — bốn bảng lệch nhau vẫn xanh, vì phép kiểm
 * cũng chỉ đọc một bảng. Thứ cần chặn là hai bên TRÔI KHỎI NHAU, nên phép kiểm
 * phải đọc CẢ HAI: bảng ở `vai.ts` và `permission_classes` trong .py.
 *
 * Cách này KHÔNG thay được việc mở bằng trình duyệt với một tài khoản
 * `Quản lý học vụ` thật. CSDL không có tài khoản nào mang vai đó (đo 04/09:
 * admin ×1, Giảng viên ×1, Học viên ×3), và tạo một tài khoản là GHI vào Neon
 * production — chưa được phép. Phần đã lái thật là đường ADMIN.
 *
 * Chạy: node e2e/unit/cong-quan-tri.test.mjs
 */
import { readFileSync } from 'node:fs';
import { register } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const BE = join(GOC, '..', 'backend');
const KHU = join(GOC, 'src', 'app', '(standalone)', 'quan-tri');

// `vai.ts` nhập `@/lib/vaiTro` — alias của tsconfig, Node không tự phân giải.
register('./hooks-nap-nguon.mjs', import.meta.url);

const { TABS, VAI_HOC_VU, VAI_QUAN_TRI, VAI_VAO_KHU, tabsCho } = await import(
  'file://' + join(KHU, 'vai.ts').replace(/\\/g, '/')
);

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

const doc = (...p) => {
  try {
    return readFileSync(join(...p), 'utf8');
  } catch {
    return '';
  }
};

/**
 * Mỗi trang của khu, kèm lớp quyền mà API CỦA NÓ khai ở backend.
 *
 * Cột `lop` là thứ phải đi tra lại trong .py — không phải một niềm tin chép
 * sang đây. Cột `tep` nói tra ở đâu.
 */
const TRANG = [
  { href: '/quan-tri/tong-quan', lop: 'IsAdminRole', tep: 'teaching/overview.py',
    view: 'AdminOverviewView' },
  { href: '/quan-tri/tai-khoan', lop: 'IsAdminRole', tep: 'teaching/admin_users.py',
    view: 'AdminUsersView' },
  { href: '/quan-tri/lop-hoc', lop: 'IsAdminOrAcademic', tep: 'teaching/views.py',
    view: 'AdminClassesView' },
  { href: '/quan-tri/dot-hoc', lop: 'IsAdminOrAcademic', tep: 'teaching/terms.py',
    view: 'AdminTermsView' },
  { href: '/quan-tri/nhat-ky', lop: 'IsAdminRole', tep: 'teaching/admin_users.py',
    view: 'AdminAuditView' },
];

const PERM = readFileSync(join(BE, 'common', 'permissions.py'), 'utf8');
const VAI_CUA_LOP = {
  IsAdminRole: [VAI_QUAN_TRI],
  IsAdminOrAcademic: [VAI_QUAN_TRI, VAI_HOC_VU],
};

/**
 * Thân của MỘT lớp/hàm Python: từ dòng khai báo tới khai báo cấp 0 kế tiếp.
 *
 * Bản đầu dùng cửa sổ ký tự cố định — `class IsAdminOrAcademic[\s\S]{0,600}` —
 * và đo được: thân lớp ấy dài **269** ký tự, nên cửa sổ tràn 331 ký tự và với
 * sang một `is_academic` khác nằm trong hàm `can_see_class` phía dưới.
 *
 * Hậu quả: siết `IsAdminOrAcademic` về chỉ-quản-trị thì regex VẪN khớp và cả bộ
 * kiểm vẫn xanh — nó hằng đúng ĐÚNG ở chỗ nó tuyên bố đang canh. Một cửa sổ đếm
 * bằng ký tự là một phỏng đoán về bố cục tệp, mà bố cục tệp thì đổi.
 */
function thanPython(ma, khaiBao) {
  const i = ma.indexOf(khaiBao);
  if (i < 0) return '';
  const sau = ma.slice(i + khaiBao.length);
  const m = /\n(?:class |def |@)/.exec(sau);
  return m ? ma.slice(i, i + khaiBao.length + m.index) : ma.slice(i);
}

/** `permission_classes` mà một view THẬT SỰ khai. */
function quyenCuaView(tep, view) {
  const than = thanPython(readFileSync(join(BE, ...tep.split('/')), 'utf8'), `class ${view}(`);
  const m = /permission_classes\s*=\s*\[([^\]]*)\]/.exec(than);
  return m ? m[1].replace(/[()\s]/g, '') : null;
}

for (const lop of Object.keys(VAI_CUA_LOP)) {
  check(`backend còn lớp quyền \`${lop}\``, new RegExp(`class ${lop}\\b`).test(PERM));
}

const THAN_IAOA = thanPython(PERM, 'class IsAdminOrAcademic');
check('đọc được đúng THÂN lớp IsAdminOrAcademic (không tràn sang hàm kế tiếp)',
  THAN_IAOA.length > 0 && THAN_IAOA.length < 1200, `${THAN_IAOA.length} ký tự`);
check('`IsAdminOrAcademic` vẫn nhận vai học vụ', /is_academic/.test(THAN_IAOA),
  'không thấy `is_academic` TRONG THÂN LỚP (chỉ thấy ở chỗ khác trong tệp)');

console.log('');
for (const t of TRANG) {
  const that = quyenCuaView(t.tep, t.view);
  check(`${t.view} (${t.tep}) vẫn dùng ${t.lop}`, that === t.lop,
    `đang là ${JSON.stringify(that)}`);

  const tab = TABS.find((x) => x.href === t.href);
  if (!tab) {
    check(`có tab cho ${t.href}`, false);
    continue;
  }
  const mong = VAI_CUA_LOP[t.lop];
  check(`tab ${t.href} khai đúng vai của ${t.lop}`,
    [...tab.vai].sort().join(',') === [...mong].sort().join(','),
    `frontend: ${JSON.stringify(tab.vai)} · backend: ${JSON.stringify(mong)}`);
}

console.log('');
const cuaQT = tabsCho(VAI_QUAN_TRI).map((t) => t.href);
const cuaHV = tabsCho(VAI_HOC_VU).map((t) => t.href);
check('quản trị viên thấy mọi trang của khu', TRANG.every((t) => cuaQT.includes(t.href)),
  JSON.stringify(cuaQT));
check('học vụ thấy Lớp học và Đợt học',
  cuaHV.includes('/quan-tri/lop-hoc') && cuaHV.includes('/quan-tri/dot-hoc'),
  JSON.stringify(cuaHV));
check('học vụ KHÔNG thấy Tài khoản / Nhật ký / Toàn trung tâm',
  !cuaHV.includes('/quan-tri/tai-khoan') && !cuaHV.includes('/quan-tri/nhat-ky')
    && !cuaHV.includes('/quan-tri/tong-quan'),
  JSON.stringify(cuaHV));

console.log('');
// ── Cổng KHU: hằng số vừa được NỚI hôm nay, và là hằng số duy nhất chưa ai
//    canh. Nới thêm một vai vào đây là cho vai ấy vào khung khu. ────────────
const HOP = [...new Set(TRANG.flatMap((t) => VAI_CUA_LOP[t.lop]))].sort();
check('`VAI_VAO_KHU` đúng bằng HỢP các vai vào được ít nhất một trang',
  [...VAI_VAO_KHU].sort().join(',') === HOP.join(','),
  `${JSON.stringify([...VAI_VAO_KHU])} vs ${JSON.stringify(HOP)}`);

const LAYOUT_KHU = doc(KHU, 'layout.tsx');
check('layout khu dùng `VAI_VAO_KHU` làm cổng',
  /duocVao\(kq\.vai,\s*VAI_VAO_KHU\)/.test(LAYOUT_KHU));
check('layout khu chỉ hiện tab người ấy vào được', /tabsCho\(kq\.vai\)/.test(LAYOUT_KHU));

// MỌI trang phải có cổng RIÊNG, kể cả trang mở cho học vụ: cổng khu chỉ hỏi
// "vào được ÍT NHẤT MỘT trang", nên nó không thay được cổng của từng trang.
// Nới cổng khu mà quên dựng cổng trang là nới QUYỀN, không phải sửa lỗi.
for (const t of TRANG) {
  const ten = t.href.split('/').pop();
  const ma = doc(KHU, ten, 'layout.tsx') + '\n' + doc(KHU, ten, 'page.tsx');
  check(`${ten}/ có cổng riêng`, /duocVao\(kq\.vai,\s*\[/.test(ma));
}

// `admin/page.tsx` từng là bảng THỨ TƯ trả lời cùng câu hỏi, với hai chuỗi vai
// gõ tay. Hôm nay hai bên trùng nhau nên chưa hỏng — cơ chế trôi thì y hệt.
const TRANG_ADMIN = doc(GOC, 'src', 'app', '(standalone)', 'admin', 'page.tsx');
check('admin/page.tsx lấy vai từ bảng chung, không gõ lại chuỗi',
  /from '@\/lib\/vaiTro'/.test(TRANG_ADMIN) && !/'Biên tập nội dung'/.test(TRANG_ADMIN),
  'còn chuỗi vai gõ tay trong admin/page.tsx');

console.log(failures === 0 ? '\nOK — cổng frontend khớp permission_classes' : `\n${failures} lỗi`);
process.exitCode = failures === 0 ? 0 : 1;
