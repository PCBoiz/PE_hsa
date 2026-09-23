/**
 * "Khu làm việc của bạn" (`src/lib/khuTheoVai.ts`) phải KHỚP cổng thật của từng khu.
 *
 * ── VÌ SAO (20/09/2026) ─────────────────────────────────────────────────────
 *
 * Nhân sự mở Trang của tôi thấy các thẻ dẫn tới khu của vai mình. Vai của mỗi
 * thẻ là bản chép tay từ lượt đi thử sáu vai — đúng hôm đó. Bản chép thì trôi:
 * nới `IsTeachingStaff` thêm một vai ở backend, hay đổi `VAI_VAO_KHU`, là thẻ
 * này im lặng lệch — hoặc dựng thẻ dẫn tới bức tường "Không đủ quyền", hoặc
 * giấu một khu người ta có quyền vào. Cả hai đều là đúng lỗi bảng này sinh ra
 * để tránh, và không có gì đỏ.
 *
 * Phép kiểm đọc THẲNG nguồn của từng cổng (không qua bản chép nào khác):
 *   IsTeachingStaff  → `lib/quyenVai.ts::VAI_CUA_LOP_QUYEN` (tệp ấy đã ràng với
 *                      `common/permissions.py` bởi `quyen-vai.test.mjs`)
 *   van-hanh         → `quan-tri/vai.ts`: `TABS[href].vai` nếu thẻ trỏ vào một
 *                      trang cụ thể, không thì `VAI_VAO_KHU`
 *   soan-giao-trinh  → `giao-trinh/page.tsx::DUOC_VAO`
 *   moi-nhan-su      → đủ năm vai nhân sự
 *
 * Đọc bằng regex trên mã nguồn TS, cùng lối với `quyen-vai.test.mjs`: nạp TS
 * bằng Node thuần thì phải dựng nửa bộ bundler chỉ để đọc mấy mảng hằng.
 *
 * Chứng minh đỏ 20/09: thêm `VAI_BIEN_TAP` vào `DAY` → 2 thẻ đỏ; đổi `cong` của
 * "Vận hành trung tâm" thành `moi-nhan-su` → đỏ; bỏ `cong` → đỏ "thiếu cổng".
 *
 * Chạy: node e2e/unit/khu-theo-vai.test.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const doc = (p) => readFileSync(join(GOC, 'src', ...p.split('/')), 'utf8');
const boChuThich = (s) => s.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/(^|[^:'"])\/\/[^\n]*/g, '$1 ');

let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${ten}${ok || !ct ? '' : `  → ${ct}`}`);
  if (!ok) loi += 1;
};

/* ── Hằng số vai → chuỗi thật, từ `vaiTro.ts` ─────────────────────────────── */
const VAI = Object.fromEntries(
  [...doc('lib/vaiTro.ts').matchAll(/^export const (VAI_[A-Z_]+) = '([^']+)';/gm)].map((m) => [m[1], m[2]]),
);
check('đọc được sáu vai từ vaiTro.ts', Object.keys(VAI).length === 6, Object.keys(VAI).join(','));
const NHAN_SU = Object.values(VAI).filter((v) => v !== VAI.VAI_HOC_VIEN).sort();

/** `[VAI_A, VAI_B, ...]` hoặc `[...DAY, VAI_X]` → mảng chuỗi, đã sắp. */
const mang = (chuoi, hang = {}) => {
  const ra = new Set();
  for (const m of chuoi.matchAll(/\.\.\.([A-Z_]+)|(VAI_[A-Z_]+)/g)) {
    if (m[1]) for (const v of hang[m[1]] || []) ra.add(v);
    else ra.add(VAI[m[2]]);
  }
  return [...ra].sort();
};
const bang = (a, b) => JSON.stringify(a) === JSON.stringify(b);

/* ── Bảng thẻ, từ `khuTheoVai.ts` ─────────────────────────────────────────── */
const KHU = boChuThich(doc('lib/khuTheoVai.ts'));
const HANG = {};
for (const m of KHU.matchAll(/^const ([A-Z_]+) = \[([^\]]*)\];/gm)) HANG[m[1]] = mang(m[2], HANG);
const the = [...KHU.matchAll(/\{\s*nhan: '([^']+)'([\s\S]*?)moTa:/g)].map((m) => {
  const than = m[2];
  const url = /url: '([^']+)'/.exec(than)?.[1];
  const tab = /tab: '([^']+)'/.exec(than)?.[1];
  const cong = /cong: '([^']+)'/.exec(than)?.[1];
  const vaiRaw = /vai: (\[[^\]]*\]|[A-Z_]+)/.exec(than)?.[1] ?? '';
  const vai = vaiRaw.startsWith('[') ? mang(vaiRaw, HANG) : (HANG[vaiRaw] || []);
  return { nhan: m[1], url, tab, cong, vai };
});
check('đọc được các thẻ', the.length >= 5, String(the.length));

/* ── Cổng thật ────────────────────────────────────────────────────────────── */
const QUYEN = boChuThich(doc('lib/quyenVai.ts'));
const lopQuyen = (ten) => mang(new RegExp(`${ten}: (\\[[^\\]]*\\])`).exec(QUYEN)?.[1] ?? '');

const VAN_HANH = boChuThich(doc('app/(standalone)/quan-tri/vai.ts'));
const VAO_KHU = mang(/VAI_VAO_KHU: readonly string\[\] = (\[[^\]]*\])/.exec(VAN_HANH)?.[1] ?? '');
const TAB_VH = Object.fromEntries(
  [...VAN_HANH.matchAll(/href: '([^']+)'[^}]*?vai: (\[[^\]]*\])/g)].map((m) => [m[1], mang(m[2])]),
);
const ADMIN = boChuThich(doc('app/(standalone)/giao-trinh/page.tsx'));
const SOAN = mang(/DUOC_VAO = new Set\((\[[^\]]*\])\)/.exec(ADMIN)?.[1] ?? '');

check('đọc được VAI_VAO_KHU', VAO_KHU.length >= 1, JSON.stringify(VAO_KHU));
check('đọc được DUOC_VAO của /giao-trinh', SOAN.length >= 1, JSON.stringify(SOAN));
check('đọc được IsTeachingStaff', lopQuyen('IsTeachingStaff').length >= 1);

/* ── Đối chiếu từng thẻ ───────────────────────────────────────────────────── */
for (const t of the) {
  if (!t.cong) { check(`${t.nhan}: có cổng`, false, 'thiếu `cong` — không biết đối chiếu với gì'); continue; }
  let mong;
  let nguon;
  if (t.cong === 'IsTeachingStaff') { mong = lopQuyen('IsTeachingStaff'); nguon = 'quyenVai.ts::IsTeachingStaff'; }
  else if (t.cong === 'van-hanh') {
    mong = (t.url && TAB_VH[t.url]) || VAO_KHU;
    nguon = t.url && TAB_VH[t.url] ? `quan-tri/vai.ts::TABS[${t.url}]` : 'quan-tri/vai.ts::VAI_VAO_KHU';
  }
  else if (t.cong === 'soan-giao-trinh') { mong = SOAN; nguon = 'giao-trinh/page.tsx::DUOC_VAO'; }
  else if (t.cong === 'moi-nhan-su') { mong = NHAN_SU; nguon = 'năm vai nhân sự'; }
  else { check(`${t.nhan}: cổng hợp lệ`, false, `cổng lạ ${t.cong}`); continue; }
  check(`${t.nhan}: vai khớp ${nguon}`, bang(t.vai, mong),
    `thẻ ghi ${JSON.stringify(t.vai)} — cổng cho ${JSON.stringify(mong)}`);
  check(`${t.nhan}: không có vai học viên`, !t.vai.includes(VAI.VAI_HOC_VIEN));
}

/* ── Trang ĐẦU sau đăng nhập theo vai (24/09/2026, góp ý TopHSA #3/#4) ─────
   Mỗi vai nhân sự vào thẳng khu làm việc của mình. Trang đích mà cổng thật từ
   chối vai ấy = đăng nhập xong rơi vào màn "không có quyền". */
const TRANG_DAU = Object.fromEntries(
  [...KHU.matchAll(/\[(VAI_[A-Z_]+)\]: '([^']+)'/g)].map((m) => [VAI[m[1]], m[2]]),
);
check('đọc được TRANG_DAU', Object.keys(TRANG_DAU).length >= 1, JSON.stringify(TRANG_DAU));
const CONG_TRANG = {
  '/giang-day': [lopQuyen('IsTeachingStaff'), 'quyenVai.ts::IsTeachingStaff'],
  '/quan-tri/tong-quan': [VAO_KHU, 'quan-tri/vai.ts::VAI_VAO_KHU'],
  '/giao-trinh': [SOAN, 'giao-trinh/page.tsx::DUOC_VAO'],
};
for (const vai of NHAN_SU) {
  const dich = TRANG_DAU[vai];
  if (!dich) { check(`trang đầu của ${vai}`, false, 'thiếu — vai này đăng nhập xong rơi về trang thẻ'); continue; }
  const [cho, nguon] = CONG_TRANG[dich] ?? [null, null];
  check(`trang đầu của ${vai} (${dich}) mở cho vai ấy theo ${nguon}`, !!cho && cho.includes(vai),
    cho ? `cổng chỉ cho ${JSON.stringify(cho)}` : 'trang đích lạ — thêm cổng của nó vào CONG_TRANG');
}
check('học viên KHÔNG có trang đầu riêng (vẫn /dashboard)', !(VAI.VAI_HOC_VIEN in TRANG_DAU));

console.log(loi ? `\n${loi} lỗi` : '\nOK — bảng khu làm việc khớp cổng thật');
process.exit(loi ? 1 : 0);
