/**
 * Unit test — mọi đường dẫn trong HƯỚNG DẪN phải là tuyến CÓ THẬT.
 *
 * ── VÌ SAO CANH ĐÚNG CHỖ NÀY (07/09/2026) ─────────────────────────────────
 *
 * Tài liệu hỏng theo một kiểu riêng: nó không đổ, không ném lỗi, không có ai
 * chạy nó. Nó chỉ dần dần nói sai — và người phát hiện ra là NGƯỜI MỚI, đúng
 * người ít có khả năng nhận ra rằng tài liệu sai chứ không phải mình làm sai.
 *
 * Anh Sơn chốt tài liệu đặt TRONG ứng dụng, nên nó có một chỗ bám vào sự thật
 * mà một tệp `.md` không có: các đường dẫn. Phép kiểm này đối chiếu từng
 * đường dẫn với thư mục `app/`, nên một tuyến bị đổi tên hay xoá sẽ làm bộ
 * kiểm đỏ thay vì làm người mới lạc.
 *
 * ── VÌ SAO KHÔNG CHỈ `fetch` THỬ TỪNG ĐƯỜNG ──────────────────────────────
 *
 * `fetch` cần máy chủ chạy và tài khoản đăng nhập; bộ unit chạy trong CI không
 * có cả hai. Đọc thư mục tuyến là thứ luôn làm được, và nó bắt đúng lỗi cần
 * bắt: đường dẫn trỏ vào chỗ không tồn tại.
 *
 * Nó KHÔNG bắt được: tuyến còn đó nhưng cái nút được nhắc tới đã bị đổi tên.
 * Chỗ ấy vẫn cần người đọc lại — nói rõ ở đây để không ai tưởng tệp này canh
 * cả nội dung.
 *
 * Chạy: node e2e/unit/huong-dan.test.mjs
 */
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const APP = join(GOC, 'src', 'app');
const DL = readFileSync(join(GOC, 'src', 'lib', 'huongDan.ts'), 'utf8');

let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${ten}${ok || !ct ? '' : `  → ${ct}`}`);
  if (!ok) loi += 1;
};

/** Mọi tuyến TĨNH của ứng dụng, quét từ thư mục `app/`. */
function quetTuyen(thuMuc, tienTo = '') {
  const ra = new Set();
  for (const e of readdirSync(thuMuc, { withFileTypes: true })) {
    if (!e.isDirectory()) {
      if (/^page\.tsx?$/.test(e.name)) ra.add(tienTo || '/');
      continue;
    }
    // `(nhom)` là nhóm tuyến của Next — không xuất hiện trong URL.
    const doan = /^\(.*\)$/.test(e.name) ? '' : `/${e.name}`;
    // Tuyến động `[x]` không so được với đường dẫn tĩnh; bỏ qua nhánh ấy.
    if (/^\[.*\]$/.test(e.name)) continue;
    for (const t of quetTuyen(join(thuMuc, e.name), tienTo + doan)) ra.add(t);
  }
  return ra;
}

const TUYEN = quetTuyen(APP);
check('quét được tuyến của ứng dụng', TUYEN.size >= 10, `${TUYEN.size} tuyến`);

// ── Mọi `o:` trong hướng dẫn phải là tuyến có thật ────────────────────────
/* KHÔNG neo vào đầu/cuối dòng. Bản đầu dùng `/^\s*o: '…',$/gm`, nên một
   bước viết gọn trên MỘT dòng — `{ lam: '…', o: '/admin' }` — bị bỏ qua
   IM LẶNG, và phép kiểm vẫn báo xanh trong khi không hề đo `/admin`.
   Đây là lần thứ năm trong phiên 07/09/2026 một cái thước bỏ sót một phần vật
   cần đo mà vẫn báo đạt. Hình dạng lỗi luôn giống nhau: lớp ký tự hoặc mỏ neo
   hẹp hơn dữ liệu thật. */
const DUONG = [...DL.matchAll(/(?:^|[^\w])o: '([^']+)'/gm)].map((m) => m[1]);
check('hướng dẫn có đường dẫn để đối chiếu', DUONG.length >= 5, String(DUONG.length));

for (const d of [...new Set(DUONG)]) {
  // Bỏ phần `#neo` — neo nằm trong trang, không phải tuyến.
  const chi = d.split('#')[0];
  check(`\`${d}\` là tuyến có thật`, TUYEN.has(chi),
    `không thấy trong app/ (${TUYEN.size} tuyến đã quét)`);
}

// ── KHÔNG được dùng tuyến ĐỘNG làm đường dẫn ─────────────────────────────
// Một đường dẫn dựng sẵn với mã lớp bất kỳ sẽ dẫn người đọc vào lớp của người
// khác — hoặc vào một 404, tuỳ họ có quyền hay không.
check('không đường dẫn nào chứa tham số động',
  !DUONG.some((d) => /\[|<|:\w/.test(d)),
  DUONG.filter((d) => /\[|<|:\w/.test(d)).join(', '));

// ── Mỗi bài phải có đủ phần ───────────────────────────────────────────────
/* `
?
`, KHÔNG phải `
`.
 *
 * Bản cũ đòi dấu phẩy đứng LIỀN NGAY TRƯỚC `
`. Trên bản checkout
 * Windows, `huongDan.ts` có kết thúc dòng CRLF (đo: 262 CRLF, 0 LF đơn),
 * nên giữa `,` và `
` còn một `
` — regex không khớp gì cả và phép
 * kiểm báo "đọc được 0 bài" trong khi tệp có 9.
 *
 * CI chạy trên Linux nên nó XANH ở đó suốt. Tức phép kiểm này đỏ đúng ở
 * chỗ người viết mã ngồi, và xanh ở chỗ không ai nhìn — kiểu hỏng dạy
 * người ta bỏ qua màu đỏ. Sửa 07/09/2026. */
const BAI = [...DL.matchAll(/^\s*ma: '([a-z-]+)',\r?\n\s*tieu_de: '([^']+)',/gm)]
  .map((m) => ({ ma: m[1], tieu_de: m[2] }));
check('đọc được danh sách bài', BAI.length >= 6, String(BAI.length));
check('không mã bài nào trùng',
  new Set(BAI.map((b) => b.ma)).size === BAI.length, BAI.map((b) => b.ma).join(','));

// ── Vai nhắc tới phải là vai CÓ THẬT ─────────────────────────────────────
// Một bài dành cho `VAI_QUAN_LY` (vai chưa tồn tại) sẽ hiện ra cho không ai cả,
// và không có gì báo — đúng kiểu hỏng im lặng mà tệp này sinh ra để chặn.
const VAI_HOP_LE = new Set(
  [...readFileSync(join(GOC, 'src', 'lib', 'vaiTro.ts'), 'utf8')
    .matchAll(/export const (VAI_\w+) = '/g)].map((m) => m[1]),
);
const VAI_DUNG = [...new Set(
  [...DL.matchAll(/vai: \[([^\]]+)\]/g)]
    .flatMap((m) => m[1].split(',').map((s) => s.trim()))
    .filter(Boolean),
)];
for (const v of VAI_DUNG) {
  check(`vai \`${v}\` có thật trong vaiTro.ts`, VAI_HOP_LE.has(v));
}

// ── Trang hiển thị phải THẬT SỰ đọc dữ liệu này ──────────────────────────
// Không có câu này thì ai đó chép nội dung vào JSX cho tiện, và bộ kiểm vẫn
// xanh trong khi trang hiện một bản khác hẳn.
const TRANG = readFileSync(
  join(GOC, 'src', 'app', '(standalone)', 'quan-tri', 'huong-dan', 'page.tsx'), 'utf8');
check('trang Hướng dẫn dựng từ `lib/huongDan.ts`',
  /from '@\/lib\/huongDan'/.test(TRANG) && /HUONG_DAN\.map/.test(TRANG));

console.log(loi === 0 ? '\nOK — hướng dẫn trỏ vào tuyến thật' : `\n${loi} lỗi`);
process.exitCode = loi === 0 ? 0 : 1;
