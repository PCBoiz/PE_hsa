/**
 * Unit test — mỗi ô hồ sơ phải đi THÔNG cả ba tầng: React → main.js → API.
 *
 * ── VÌ SAO CÓ TỆP NÀY (07/09/2026) ────────────────────────────────────────
 *
 * Trước hôm nay `main.js::saveSettings` gọi TÊN từng ô:
 *
 *     name:     document.getElementById("field-name").value,
 *     email:    document.getElementById("field-email").value,
 *     phone:    document.getElementById("field-phone").value,
 *     birthday: document.getElementById("field-birthday").value,
 *
 * Thêm một trường hồ sơ là phải sửa BA chỗ (thẻ input, hàm lưu, hàm nạp) ở HAI
 * tầng. Quên một chỗ thì ô ấy hiện ra bình thường, gõ vào được, bấm Lưu xong
 * báo thành công — và không lưu gì cả. Không lỗi, không cảnh báo.
 *
 * Nay cả hai hàm đọc theo nhãn `data-ho-so`, nên thêm trường chỉ là thêm một
 * <input>. Nhưng cách ấy DỜI rủi ro chứ không xoá: nhãn gõ sai chính tả, hoặc
 * API không nhận khoá đó, thì vẫn im lặng đúng như cũ. Đây là chỗ phép kiểm
 * này đứng — nó đọc CẢ BA tầng và bắt chúng khớp nhau. Chỉ đọc một tầng thì
 * ba tầng lệch nhau vẫn xanh.
 *
 * ── VÀ PHÉP KIỂM NÀY TỪNG ĐO NHẦM VẬT ─────────────────────────────────────
 *
 * Bản đầu quét cả thân `UserView.get` để tìm cột cấm, rồi báo đỏ `status_note`
 * và `password` — nhưng gọi HTTP thật thì chúng KHÔNG hề có trong phản hồi.
 * Nó đang khớp phải chính CHÚ THÍCH giải thích vì sao hai cột ấy bị loại. Đo
 * văn xuôi chứ không đo mã, và cách "sửa" hiển nhiên sẽ là xoá chú thích — tức
 * làm mã tệ đi để cái thước xanh. Nay nó cắt đúng danh sách cột giữa SELECT
 * và FROM.
 *
 * Chạy: node e2e/unit/ho-so-truong.test.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const BE = join(GOC, '..', 'backend');

const doc = (p) => readFileSync(p, 'utf8');
const TRANG = doc(join(GOC, 'src', 'app', '(base)', 'dashboard', 'page.tsx'));
const MAIN = doc(join(GOC, 'public', 'static', 'js', 'main.js'));
const VIEWS = doc(join(BE, 'accounts', 'views.py'));

let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${ten}${ok || !ct ? '' : `  → ${ct}`}`);
  if (!ok) loi += 1;
};

// ── Tầng 1: các nhãn khai trong React ────────────────────────────────────
const NHAN = [...TRANG.matchAll(/data-ho-so="([a-z_]+)"/g)].map((m) => m[1]);
console.log(`\nÔ hồ sơ khai ở dashboard/page.tsx: ${NHAN.join(', ')}\n`);
check('có ít nhất bốn ô hồ sơ', NHAN.length >= 4, String(NHAN.length));
check('không nhãn nào trùng', new Set(NHAN).size === NHAN.length, NHAN.join(','));

// ── Tầng 2: main.js phải đọc theo nhãn ở CẢ HAI chiều ────────────────────
// Lưu và nạp là hai hàm khác nhau; sửa một chiều mà quên chiều kia là ô hiện
// đúng giá trị cũ nhưng không lưu được (hoặc lưu được mà mở lại thì trống).
const soChoDoc = (MAIN.match(/querySelectorAll\("\[data-ho-so\]"\)/g) || []).length;
check('main.js đọc `[data-ho-so]` ở CẢ hai chiều (lưu + nạp)',
  soChoDoc >= 2, `${soChoDoc} chỗ`);

// Không được sót lối cũ: một `getElementById("field-…")` còn lại nghĩa là ô đó
// đi đường riêng, và đường riêng ấy không ai canh.
const conGoiTen = [...MAIN.matchAll(/getElementById\("(field-[a-z-]+)"\)/g)].map((m) => m[1]);
check('main.js không còn gọi tên từng ô hồ sơ', conGoiTen.length === 0, conGoiTen.join(','));

// ── Tầng 3: API phải NHẬN và TRẢ đúng ngần ấy khoá ───────────────────────
// Cắt lấy đúng thân `UserView`: `views.py` có nhiều view, và một khoá trùng
// tên ở view khác sẽ làm phép kiểm xanh oan.
const iUser = VIEWS.indexOf('class UserView');
const iSau = VIEWS.indexOf('\nclass ', iUser + 1);
const USERVIEW = VIEWS.slice(iUser, iSau === -1 ? undefined : iSau);
check('tìm được thân UserView', USERVIEW.length > 200, String(USERVIEW.length));

const iPut = USERVIEW.indexOf('def put');
const GET = USERVIEW.slice(0, iPut);
const PUT = USERVIEW.slice(iPut);

// Danh sách cột THẬT của câu SELECT — xem chú thích đầu tệp về lần đo nhầm.
// Neo vào chính lời gọi `q1('''SELECT`, KHÔNG bắt chữ `SELECT` trần: ngay
// phía trên câu truy vấn có một CHÚ THÍCH viết `SELECT *` (nó giải thích vì
// sao không dùng `SELECT *`), và regex trần khớp từ đó — nuốt cả chú thích
// vào "danh sách cột". Phát hiện lúc chạy phép đỏ-trước 07/09/2026: ngữ
// cảnh in ra ``*`.`` thay vì tên cột.
const mSel = GET.match(/q1\(\s*'''SELECT\s+([\s\S]*?)\s+FROM users/);
const COT = (mSel ? mSel[1] : '').split(',').map((c) => c.trim());
check('đọc được danh sách cột của SELECT (không thì mọi kiểm dưới đều vô nghĩa)',
  COT.length > 5, `${COT.length} cột`);

for (const n of NHAN) {
  check(`PUT /api/user đọc \`${n}\``, new RegExp(`data\\.get\\('${n}'\\)`).test(PUT));
  check(`PUT /api/user ghi cột \`${n}\``, new RegExp(`${n}\\s*=%s`).test(PUT));
  // Không trả về thì mở lại trang là ô trống, dù đã lưu đúng.
  check(`GET /api/user trả \`${n}\``, COT.includes(n), COT.join(','));
}

// ── Ranh giới: cột NỘI BỘ không được lọt vào danh sách trắng ─────────────
// `UserView.get` từng `SELECT *` rồi chỉ `pop('password')`, nên `status_note`
// — ghi chú của quản trị viên VỀ học viên, ví dụ lý do khoá tài khoản — rò ra
// cho chính em ấy đọc. Danh sách trắng vá điều đó; phép kiểm này giữ nó không
// bị nới lại khi có người thêm cột mới cho tiện.
for (const cam of ['status_note', 'password', 'tokens_valid_from', 'status_changed_at']) {
  check(`GET /api/user KHÔNG trả \`${cam}\``, !COT.includes(cam), COT.join(','));
}

// ── Số phụ huynh: KHÔNG được kiểm trùng như số học viên ──────────────────
// Hai anh em cùng học thì dùng chung số của mẹ — chuyện bình thường, không
// phải xung đột danh tính. `users.phone` phải duy nhất vì nó là một cách ĐĂNG
// NHẬP; số phụ huynh chỉ là một địa chỉ để gửi tới. Kiểm trùng ở đây sẽ chặn
// đúng người thứ hai trong nhà, và thông báo lỗi sẽ vô nghĩa với họ.
check('không kiểm trùng `parent_phone`',
  !/WHERE parent_phone=%s AND id<>%s/.test(PUT));
check('vẫn kiểm trùng `phone` của chính học viên',
  /WHERE phone=%s AND id<>%s/.test(PUT));

// Sai dạng phải bị chặn TRƯỚC khi tới CSDL: một số sai là một tin ZNS gửi vào
// hư không, mất phí, và không ai biết cho tới khi phụ huynh hỏi vì sao chưa
// nhận được gì.
check('`parent_phone` có qua validator', /validate_phone_field\(parent_phone\)/.test(PUT));

console.log(loi === 0 ? '\nOK — ô hồ sơ thông cả ba tầng' : `\n${loi} lỗi`);
process.exitCode = loi === 0 ? 0 : 1;
