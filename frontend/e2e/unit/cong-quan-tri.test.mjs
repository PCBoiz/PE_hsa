/**
 * Unit test — cổng vai trò ở frontend phải KHỚP `permission_classes` ở backend.
 *
 * ── LỖI ĐANG CHẶN LẠI (đo 04/09/2026) ─────────────────────────────────────
 *
 * Có BA bảng trả lời cùng một câu hỏi "ai vào được trang nào", và chúng lệch:
 *
 *   `quan-tri/layout.tsx`  · `role !== 'admin'` → chặn tất cả trừ quản trị viên
 *   `AdminNav`             · hiện ĐỦ mọi tab cho ai qua được cổng trên
 *   backend                · `/api/admin/classes` và `/api/admin/terms` dùng
 *                            `IsAdminOrAcademic` — `Quản lý học vụ` ĐƯỢC làm
 *
 * Tức cổng chặn `Quản lý học vụ` khỏi ĐÚNG hai trang backend vừa mở cho họ.
 * Xếp lớp và mở đợt học là việc hằng ngày của vai ấy; vai sinh ra để KHÔNG phải
 * cấp quyền quản trị cho người làm hai việc đó, rồi lại phải cấp quyền quản trị
 * cho họ mới dùng được.
 *
 * ── VÌ SAO KIỂM BẰNG CÁCH ĐỌC MÃ PYTHON ───────────────────────────────────
 *
 * Kiểm `tabsCho('Quản lý học vụ')` trả về đúng hai href thì chỉ chứng minh bảng
 * ở frontend NHẤT QUÁN VỚI CHÍNH NÓ — cả ba bảng lệch nhau vẫn xanh, vì phép
 * kiểm cũng chỉ đọc một bảng. Thứ cần chặn là hai bên TRÔI KHỎI NHAU, nên phép
 * kiểm phải đọc CẢ HAI: bảng ở `vai.ts` và `permission_classes` trong .py.
 *
 * Cách này KHÔNG thay được việc mở bằng trình duyệt với một tài khoản
 * `Quản lý học vụ` thật. CSDL hiện không có tài khoản nào mang vai đó (đo
 * 04/09/2026: chỉ có admin ×1, Giảng viên ×1, Học viên ×3), và tạo một tài
 * khoản là GHI vào Neon production — chưa được phép. Nên phần đã lái thật trong
 * trình duyệt là đường ADMIN; phần này chặn đúng cái đã hỏng.
 *
 * Chạy: node e2e/unit/cong-quan-tri.test.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const BE = join(GOC, '..', 'backend');

const { TABS, VAI_HOC_VU, VAI_QUAN_TRI, tabsCho } = await import(
  'file://' + join(GOC, 'src', 'app', '(standalone)', 'quan-tri', 'vai.ts').replace(/\\/g, '/')
);

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

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

/** Lớp quyền nào cho vai nào — đọc từ `common/permissions.py`, không chép. */
const PERM = readFileSync(join(BE, 'common', 'permissions.py'), 'utf8');
const VAI_CUA_LOP = {
  IsAdminRole: [VAI_QUAN_TRI],
  IsAdminOrAcademic: [VAI_QUAN_TRI, VAI_HOC_VU],
};

for (const lop of Object.keys(VAI_CUA_LOP)) {
  check(`backend còn lớp quyền \`${lop}\``, new RegExp(`class ${lop}\\b`).test(PERM));
}
// `IsAdminOrAcademic` phải THẬT SỰ cho học vụ vào — nếu ai đó siết nó lại thì
// bảng ở frontend thành quá rộng, và phép kiểm này phải đỏ.
check(
  '`IsAdminOrAcademic` vẫn nhận vai học vụ',
  /class IsAdminOrAcademic[\s\S]{0,600}?is_academic/.test(PERM),
  'không thấy `is_academic` trong thân lớp',
);

/** Lấy `permission_classes` mà một view thật sự khai. */
function quyenCuaView(tep, view) {
  const ma = readFileSync(join(BE, ...tep.split('/')), 'utf8');
  const i = ma.indexOf(`class ${view}(`);
  if (i < 0) return null;
  // Cắt tới `class` kế tiếp để không nhặt nhầm `permission_classes` của view sau.
  const j = ma.indexOf('\nclass ', i + 1);
  const than = ma.slice(i, j < 0 ? ma.length : j);
  const m = /permission_classes\s*=\s*\[([^\]]*)\]/.exec(than);
  return m ? m[1].replace(/[()\s]/g, '') : null;
}

console.log('');
for (const t of TRANG) {
  const that = quyenCuaView(t.tep, t.view);
  check(
    `${t.view} (${t.tep}) vẫn dùng ${t.lop}`,
    that === t.lop,
    `đang là ${JSON.stringify(that)}`,
  );

  const tab = TABS.find((x) => x.href === t.href);
  if (!tab) {
    check(`có tab cho ${t.href}`, false);
    continue;
  }
  const mong = VAI_CUA_LOP[t.lop];
  const bang = [...tab.vai].sort().join(',') === [...mong].sort().join(',');
  check(
    `tab ${t.href} khai đúng vai của ${t.lop}`,
    bang,
    `frontend: ${JSON.stringify(tab.vai)} · backend: ${JSON.stringify(mong)}`,
  );
}

console.log('');
// ── Cổng phải KHÁC NHAU giữa hai vai, nếu không nó không phải là cổng ───────
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

// ── Ba trang chỉ-quản-trị phải CÓ layout riêng làm cổng ─────────────────────
//
// Nới cổng khu mà quên dựng cổng trang là NỚI QUYỀN. Backend vẫn trả 403 nên
// dữ liệu không rò, nhưng người dùng thấy một trang tải xong rồi mọi ô báo lỗi
// — đúng thứ mà cổng phía trên sinh ra để tránh.
for (const t of TRANG.filter((x) => x.lop === 'IsAdminRole')) {
  const ten = t.href.split('/').pop();
  const p = join(GOC, 'src', 'app', '(standalone)', 'quan-tri', ten, 'layout.tsx');
  let ma = '';
  try {
    ma = readFileSync(p, 'utf8');
  } catch {
    /* không có tệp */
  }
  check(`${ten}/ có cổng riêng chỉ cho quản trị viên`,
    /duocVao\(kq\.vai,\s*\[VAI_QUAN_TRI\]\)/.test(ma), ma ? 'có tệp nhưng không thấy cổng' : 'không có layout.tsx');
}

console.log(failures === 0 ? '\nOK — cổng frontend khớp permission_classes' : `\n${failures} lỗi`);
process.exitCode = failures === 0 ? 0 : 1;
