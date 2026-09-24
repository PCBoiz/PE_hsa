/**
 * BỎ THI, PHA A (1.5A, 24/09/2026) — không còn lối nào dẫn tới tính năng thi.
 *
 * ── VÌ SAO ──────────────────────────────────────────────────────────────────
 *
 * Anh Sơn chốt 24/09: "Bỏ mọi thứ về thi, giữ ngày thi HSA" — thi thử online
 * (`/mock`), nhập kết quả kỳ thi tại trung tâm (`/giang-day/ket-qua-thi`), khối
 * điểm thi. Pha A chỉ GIẤU và THÁO TUYẾN (đảo ngược được): bảng giữ nguyên, mã
 * backend của app thi còn đó tới pha C.
 *
 * Tháo một tính năng mà còn sót một lối vào thì người dùng gặp đúng thứ tệ nhất:
 * một nút bấm vào ra trang khác, hoặc một trang gọi API đã tháo và hiện "không
 * tải được". Phép kiểm này canh bốn chỗ lối vào hay sót:
 *
 *   ① thanh điều hướng (mọi vai — học viên lẫn nhân sự);
 *   ② link cũ (thư, dấu trang, cẩm nang in) vẫn mở được — chuyển hướng ở
 *     `next.config.ts`, và KHÔNG còn trang nào nằm dưới đường bị chuyển hướng
 *     (trang ấy không bao giờ tới được, ai sửa nó là sửa vào khoảng không);
 *   ③ không tệp nào trong `src/` hay tầng JS cũ còn trỏ link tới hai đường ấy;
 *   ④ chữ "thi thử" không còn trên các màn pha A đã dọn.
 *
 * GIỮ: ngày thi HSA (`exam_date` của lớp, đếm ngược "ngày nữa tới kỳ thi") — đó
 * là mốc của học viên, không phải tính năng thi. Phép kiểm này không đụng tới nó.
 *
 * Còn lại cho pha B (đã biết, cố ý chưa canh ở ④): chữ thi thử trong
 * `dashboard.js` (năng lực, đường tiến bộ, chỉ tiêu tuần), `tong-quan/page.tsx`,
 * PDF/thư báo cáo phía máy chủ — pha B thay chúng bằng tiến trình học tập.
 *
 * Chứng minh đỏ 24/09: chạy trên mã trước pha A → ① ② ③ ④ đều đỏ.
 *
 * Chạy: node e2e/unit/bo-thi.test.mjs
 */
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const SRC = join(GOC, 'src');
const TANG_CU = join(GOC, 'public', 'static', 'js');
const APP = join(SRC, 'app');

let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${ten}${ok || !ct ? '' : `  → ${ct}`}`);
  if (!ok) loi += 1;
};

/* Bỏ chú thích: lịch sử "vì sao" trong chú thích được phép nhắc thi thử — cái
   bị cấm là chữ và link NGƯỜI DÙNG thấy. `[^:'"]` trước `//` để giữ `https://`. */
const boChuThich = (s) => s.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/(^|[^:'"])\/\/[^\n]*/g, '$1 ');
const doc = (p) => readFileSync(p, 'utf8');

function moiTep(thuMuc, loc) {
  const ra = [];
  for (const t of readdirSync(thuMuc)) {
    const p = join(thuMuc, t);
    if (statSync(p).isDirectory()) ra.push(...moiTep(p, loc));
    else if (loc(p)) ra.push(p);
  }
  return ra;
}

/* KHÔNG bắt "đề thi" trơn: "Ba hợp phần của đề thi" (lộ trình) nói về cấu trúc kỳ
   thi HSA mà em sẽ thi thật — thứ được GIỮ, không phải tính năng thi của hệ thống. */
const CHU_THI = /thi thử|luyện đề tổng/i;

/* ── ① Thanh điều hướng ───────────────────────────────────────────────────── */
// `navMuc.ts` không import gì — Node 24 tự bóc kiểu, nạp thẳng được.
const { MUC_NAV, NHOM_NAV } = await import(pathToFileURL(join(SRC, 'components', 'navMuc.ts')).href);
check('đọc được MUC_NAV', Array.isArray(MUC_NAV) && MUC_NAV.length >= 5, String(MUC_NAV?.length));
for (const [nhom, laHocVien] of [['học viên', true], ['nhân sự', false]]) {
  const thay = MUC_NAV.filter((m) => laHocVien || !m.chiHocVien);
  const sai = thay.filter((m) => CHU_THI.test(m.nhan) || /^\/mock\b/.test(m.url) || /ket-qua-thi/.test(m.url));
  check(`thanh của ${nhom} không còn mục thi`, sai.length === 0, sai.map((m) => `${m.nhan} → ${m.url}`).join(', '));
}
check('nhóm trên thanh không mang chữ thi',
  !Object.values(NHOM_NAV).some((n) => CHU_THI.test(n.nhan)));
// Ba thanh riêng của ba khu (Giảng dạy, Vận hành, Giáo trình) — đọc bằng chữ.
for (const tep of [
  'app/(standalone)/giang-day/KhungGiangDay.tsx',
  'app/(standalone)/quan-tri/vai.ts',
  'app/(standalone)/giao-trinh/page.tsx',
]) {
  const t = boChuThich(doc(join(SRC, ...tep.split('/'))));
  check(`${tep}: không mục/tab thi`, !CHU_THI.test(t) && !/ket-qua-thi|['"`]\/mock\b/.test(t));
}
// Khối "Đề thi thử" ở khu Giáo trình: tên chữ nằm trong `DeThi.tsx`, nên dò theo
// chỗ DÙNG nó (component + API) chứ không theo chữ.
for (const tep of ['app/(standalone)/giao-trinh/page.tsx', 'app/(standalone)/giao-trinh/SoanClient.tsx']) {
  const t = boChuThich(doc(join(SRC, ...tep.split('/'))));
  check(`${tep}: không còn khối Đề thi thử`, !/\bDeThi\b|mock-exams/.test(t));
}

/* ── ② Link cũ vẫn mở được, và không trang nào nằm dưới đường bị chuyển ──── */
// `next.config.ts` chỉ `import type` — bóc kiểu xong là JS thuần.
const cfg = (await import(pathToFileURL(join(GOC, 'next.config.ts')).href)).default;
const chuyen = await cfg.redirects();
const MONG_CHUYEN = [
  { source: '/mock', destination: '/dashboard', trang: ['(standalone)', 'mock'] },
  {
    source: '/giang-day/ket-qua-thi/:classId',
    destination: '/giang-day/buoi-hoc/:classId',
    trang: ['(standalone)', 'giang-day', 'ket-qua-thi'],
  },
];
for (const m of MONG_CHUYEN) {
  const r = chuyen.find((x) => x.source === m.source);
  check(`${m.source} chuyển về ${m.destination}`, r?.destination === m.destination,
    r ? `đang về ${r.destination}` : 'thiếu — link cũ sẽ ra "Không có trang này"');
  // Tạm thời (307) như các chuyển hướng khác của tệp ấy: pha A đảo ngược được,
  // mà 308 thì trình duyệt nhớ mãi, bật lại tính năng cũng không ai vào được.
  check(`${m.source} là chuyển hướng TẠM (307)`, r ? r.permanent === false : false);
  check(`không còn trang dưới ${m.source}`, !existsSync(join(APP, ...m.trang)),
    'next.config chuyển hướng TRƯỚC khi tìm trang — trang này không bao giờ tới được');
}

/* ── ③ Không còn link nào trỏ tới hai đường đã chuyển hướng ─────────────── */
const nguon = [
  ...moiTep(SRC, (p) => /\.(tsx?|mjs)$/.test(p)),
  ...moiTep(TANG_CU, (p) => p.endsWith('.js')),
];
const LINK = [/['"`]\/mock(?:['"`?#/]|$)/m, /\/giang-day\/ket-qua-thi/];
const conLink = nguon.filter((p) => LINK.some((re) => re.test(boChuThich(doc(p)))))
  .map((p) => relative(GOC, p).split('\\').join('/'));
check(`không tệp nào còn link tới /mock hay /giang-day/ket-qua-thi (${nguon.length} tệp)`,
  conLink.length === 0, conLink.join(', '));

/* ── ④ Chữ thi thử trên các màn pha A đã dọn ─────────────────────────────── */
const DA_DON = [
  'src/components/navMuc.ts',
  'src/components/TheSoHsaClient.tsx',
  'src/components/ToBaoCao.tsx',
  'src/components/KhuNhanSu.tsx',
  'src/lib/quyenVai.ts',
  'src/lib/huongDan.ts',
  'src/app/(base)/dashboard/DashboardClient.tsx',
  'src/app/(standalone)/giao-trinh/SoanClient.tsx',
  'src/app/(standalone)/giao-trinh/page.tsx',
  'src/app/(standalone)/giang-day/bao-cao/[classId]/page.tsx',
  'src/app/(standalone)/thiet-ke/page.tsx',
  'public/static/js/main.js',
  'public/static/js/roadmapData.js',
];
for (const tep of DA_DON) {
  const t = boChuThich(doc(join(GOC, ...tep.split('/'))));
  const m = CHU_THI.exec(t);
  check(`${tep}: không còn chữ thi`, !m,
    m ? `…${t.slice(Math.max(0, m.index - 40), m.index + 40).replace(/\s+/g, ' ')}…` : '');
}

console.log(loi ? `\n${loi} lỗi` : '\nOK — không còn lối vào tính năng thi (pha A)');
process.exit(loi ? 1 : 0);
