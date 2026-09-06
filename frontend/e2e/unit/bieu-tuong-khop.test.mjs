/**
 * `bieuTuong.tsx` phải khớp TỪNG KÝ TỰ với `icons.js`.
 *
 * ── VÌ SAO CÓ BẢN SAO, VÀ VÌ SAO NÓ AN TOÀN (06/09/2026) ──────────────────
 *
 * `icons.js` là script THUẦN: quét `[data-icon]` đúng một lần lúc
 * `DOMContentLoaded` rồi thôi. React dựng sau mốc ấy, nên ô biểu tượng do React
 * tạo ra sẽ RỖNG. Đó chính là lý do trước đây `Topbar.tsx` để ô trống chờ script
 * điền còn `courses/[courseId]` bỏ cuộc dùng emoji — hai thanh điều hướng của
 * cùng một sản phẩm không tài nào trông giống nhau.
 *
 * Nên bản React có đường vẽ của riêng nó. Bản sao thì sẽ trôi — trừ khi có ai
 * canh. Tệp này là người canh: đọc CẢ HAI nguồn, so từng đường path.
 *
 * ── PHÉP KIỂM NÀY ĐÃ ĐƯỢC CHỨNG MINH LÀ ĐỎ ĐƯỢC ──────────────────────────
 *
 * Đổi một ký tự trong `DUONG_VE.home` của bieuTuong.tsx → tệp này đỏ, và nói
 * đúng tên biểu tượng lệch. Một phép kiểm hằng đúng là một phép kiểm giả, nên
 * chỗ này phải nói rõ nó đã được thử theo chiều ngược lại.
 *
 * Muốn đổi biểu tượng: sửa `icons.js` rồi chạy
 *     python scripts/sinh_bieu_tuong.py
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const JS = join(GOC, 'public', 'static', 'js', 'icons.js');
const TSX = join(GOC, 'src', 'components', 'bieuTuong.tsx');

let loi = 0;
const check = (ten, ok, chiTiet = '') => {
  console.log(`${ok ? '  ok' : 'LỖI'}  ${ten}${ok || !chiTiet ? '' : `  → ${chiTiet}`}`);
  if (!ok) loi += 1;
};

/* Đọc `ten: '<path …>'` ở cả hai tệp bằng CÙNG một biểu thức. Dùng hai biểu
   thức khác nhau là mở đường cho "khớp giả": một bên bắt hụt thì phần bắt hụt
   không bao giờ bị đem ra so.
   `['"]?` chứ không `'?`: khoá có dấu gạch nối được sinh ra dưới dạng
   `"chevron-down"` (nháy KÉP, vì JSON), còn khoá thường thì trần. Bản đầu của
   tệp này chỉ chờ nháy đơn nên **bỏ sót đúng hai biểu tượng** — và vẫn báo
   XANH. Một thước đo lặng lẽ bỏ qua một phần vật cần đo thì tệ hơn không có
   thước, vì nó còn phát ra một lời trấn an. */
const doc = (duong) => {
  const s = readFileSync(duong, 'utf8');
  const ra = new Map();
  for (const m of s.matchAll(/^\s*['"]?([a-z-]+)['"]?:\s*'(.*?)',?\s*$/gm)) ra.set(m[1], m[2]);
  return ra;
};

const js = doc(JS);
const tsx = doc(TSX);

check('icons.js đọc được', js.size > 20, `chỉ thấy ${js.size} biểu tượng`);
check('bieuTuong.tsx đọc được', tsx.size > 0, `chỉ thấy ${tsx.size} biểu tượng`);

/* HÀNG RÀO CHỐNG CHÍNH BIỂU THỨC TRÊN. Đếm số dòng trong thân `DUONG_VE` bằng
   một cách KHÁC hẳn (đếm dòng, không khớp mẫu) rồi bắt hai con số bằng nhau.
   Nếu biểu thức lại bắt hụt một dạng khoá nào đó, chỗ này đỏ ngay — chứ không
   để cả tệp báo xanh trên một tập con. */
const than = /export const DUONG_VE[^{]*\{([\s\S]*?)\n\};/.exec(readFileSync(TSX, 'utf8'));
const soDong = than ? than[1].split('\n').filter((d) => d.trim()).length : -1;
check('so đủ MỌI biểu tượng trong tệp, không phải một tập con',
  soDong === tsx.size, `thân có ${soDong} dòng nhưng chỉ đọc ra ${tsx.size}`);

/* Chiều duy nhất đáng kiểm: mọi biểu tượng CÓ trong bản React phải có mặt và
   giống hệt ở nguồn. Chiều ngược lại không phải lỗi — bản React cố tình chỉ lấy
   phần khung chung cần, vì mỗi đường path thừa là byte gửi cho trình duyệt mà
   không ai vẽ. */
for (const [ten, duongTsx] of tsx) {
  const duongJs = js.get(ten);
  if (duongJs === undefined) {
    check(`${ten} có ở icons.js`, false, 'chỉ có ở bieuTuong.tsx — sinh lại từ nguồn');
    continue;
  }
  check(`${ten} khớp từng ký tự`, duongJs === duongTsx,
    `icons.js dài ${duongJs.length}, tsx dài ${duongTsx.length}`);
}

/* `BieuTuong` trả `null` khi tên sai — chứ không vẽ một ô trống. Ô trống trông
   y hệt "đang tải", nên một tên gõ nhầm sẽ im lặng mãi mãi. */
const nguon = readFileSync(TSX, 'utf8');
check('tên sai thì trả null, không vẽ ô trống', /if \(!d\) return null;/.test(nguon));
check('dùng currentColor, không màu ghi cứng', /stroke="currentColor"/.test(nguon));

console.log(loi === 0
  ? `\nOK — ${tsx.size} biểu tượng khớp nguồn icons.js`
  : `\n${loi} lỗi`);
process.exitCode = loi === 0 ? 0 : 1;
