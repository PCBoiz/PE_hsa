/**
 * Unit test — tiến độ lộ trình KHÔNG được lem sang lộ trình khác.
 *
 * ── LỖI ĐANG CHẶN LẠI (đo 04/09/2026) ─────────────────────────────────────
 *
 * `roadmap.js::normalize` sinh id mục theo VỊ TRÍ:
 *
 *     main:  i + '-m'        left: i + '-l' + j       right: i + '-r' + j
 *
 * Tức `0-m` là id của chặng đầu trong **cả 26 lộ trình tĩnh**. Bản cũ của
 * `syncXuong` khớp tiến độ máy chủ theo ĐUÔI của khoá localStorage:
 *
 *     var it = k.slice(k.indexOf(':') + 1);
 *     if (d.doneItems.indexOf(it) > -1) o[k] = 'done';
 *
 * nên đánh dấu xong chặng đầu của "Tư duy Định lượng" làm chặng đầu của 25 lộ
 * trình còn lại cùng hiện ✓. Nhánh thứ hai còn gán mục lạ cho lộ trình ĐANG MỞ,
 * tức tiến độ của A hiện lên B chỉ vì B đang mở lúc tải trang.
 *
 * Bảng `roadmap_progress` LUÔN lưu `roadmap_id`; API nay trả kèm (`done` là
 * danh sách cặp). Lỗi này chưa cắn ai — bảng đang có 0 dòng (đã SELECT) — nhưng
 * nó cắn ngay ở học viên đầu tiên bấm "đã học".
 *
 * ── VÌ SAO RÚT HÀM RA KHỎI TỆP THẬT ───────────────────────────────────────
 *
 * Chép `gopTienDo` sang đây thì bản chép sẽ được vá còn tệp thật thì không.
 * Rút bằng cách ĐẾM NGOẶC, cùng kỹ thuật với `thoat-html.test.mjs`.
 *
 * Chạy: node e2e/unit/lo-trinh.test.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const MA = readFileSync(join(GOC, 'public', 'static', 'js', 'roadmap.js'), 'utf8');

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

/** Rút thân một hàm khỏi mã nguồn bằng cách ĐẾM NGOẶC. */
function rutHam(ma, ten) {
  const dau = new RegExp(`function\\s+${ten}\\s*\\(([^)]*)\\)\\s*\\{`);
  const m = dau.exec(ma);
  if (!m) return null;
  let sau = 1;
  let i = m.index + m[0].length;
  const batDau = i;
  while (i < ma.length && sau > 0) {
    if (ma[i] === '{') sau += 1;
    else if (ma[i] === '}') sau -= 1;
    i += 1;
  }
  if (sau !== 0) return null;
  return new Function(...m[1].split(',').map((s) => s.trim()), ma.slice(batDau, i - 1));
}

const _gop = rutHam(MA, 'gopTienDo');

/* Gọi qua vỏ bọc: hàm rút ra chạy trong phạm vi TOÀN CỤC, nên mọi biến tự do
   nó tham chiếu (`getActive`, `localStorage`…) đều ném `ReferenceError`.
 *
 * Đó không phải hạn chế của phép kiểm — đó là RÀNG BUỘC THIẾT KẾ nó đang canh:
 * `gopTienDo` phải THUẦN thì mới kiểm được. Bản cũ của phép gộp gọi
 * `getActive()` để đoán lộ trình cho những mục nó không nhận ra, và chính chỗ
 * đoán ấy là nửa thứ hai của lỗi lem.
 *
 * Bắt cú ném lại và tính là MỘT LỖI, thay vì để nó giết cả tệp: bản lùi thử
 * nghiệm đã làm đúng thế và che mất bốn khẳng định phía sau. */
function gop(cucBo, cap, nhan) {
  try {
    return _gop(cucBo, cap);
  } catch (e) {
    check(`${nhan} — gọi được mà không ném`, false,
      `${e.message} (hàm phải THUẦN: không dùng biến ngoài)`);
    return {};
  }
}

check('rút được `gopTienDo` từ roadmap.js', typeof _gop === 'function');
if (typeof _gop !== 'function') {
  console.error('\nKhông rút được hàm — dừng.');
  process.exitCode = 1;
} else {
  // ── ① Tiến độ của lộ trình A KHÔNG được hiện ở lộ trình B ────────────────
  //
  // Cùng `itemId` `0-m`, khác lộ trình. Đây là ca mà bản cũ hỏng.
  const cucBo = {
    'Tư duy Định lượng:0-m': 'locked',
    'Tư duy Định tính:0-m': 'locked',
    'Khoa học:0-m': 'locked',
    'Lộ trình tổng HSA:1-l0': 'locked',
  };
  const capDaXong = [{ roadmapId: 'Tư duy Định lượng', itemId: '0-m' }];
  const ra = gop(cucBo, capDaXong, 'gộp một mục của một lộ trình');

  check('lộ trình ĐÃ đánh dấu thì thành done',
    ra['Tư duy Định lượng:0-m'] === 'done', ra['Tư duy Định lượng:0-m']);
  for (const k of ['Tư duy Định tính:0-m', 'Khoa học:0-m']) {
    check(`"${k}" KHÔNG bị lem (cùng itemId, khác lộ trình)`, ra[k] === 'locked', ra[k]);
  }
  check('mục không liên quan giữ nguyên',
    ra['Lộ trình tổng HSA:1-l0'] === 'locked', ra['Lộ trình tổng HSA:1-l0']);

  // ── ② Mục máy chủ có mà máy này CHƯA có thì thêm ĐÚNG lộ trình của nó ────
  //
  // Bản cũ gán cho lộ trình ĐANG MỞ — tiến độ của A hiện lên B chỉ vì B đang mở.
  const ra2 = gop({}, [{ roadmapId: 'Khoa học', itemId: '2-r1' }], 'mục máy chủ chưa có ở máy này');
  check('mục mới vào đúng khoá của lộ trình nó thuộc về',
    ra2['Khoa học:2-r1'] === 'done', JSON.stringify(ra2));
  check('và KHÔNG tạo khoá nào khác', Object.keys(ra2).length === 1, JSON.stringify(ra2));

  // ── ③ Không được sửa object gốc ─────────────────────────────────────────
  const goc = { 'A:0-m': 'locked' };
  gop(goc, [{ roadmapId: 'A', itemId: '0-m' }], 'không sửa object gốc');
  check('không ghi đè lên object truyền vào', goc['A:0-m'] === 'locked', goc['A:0-m']);

  // ── ④ Dữ liệu rác không làm hỏng ────────────────────────────────────────
  const ra4 = gop({ 'A:1': 'done' },
    [null, {}, { roadmapId: 'B' }, { itemId: '0-m' }, { roadmapId: 'B', itemId: '0-m' }],
    'dữ liệu rác');
  check('bỏ qua cặp thiếu trường, giữ phần hợp lệ',
    ra4['B:0-m'] === 'done' && ra4['A:1'] === 'done' && Object.keys(ra4).length === 2,
    JSON.stringify(ra4));

  // ── ⑤ `syncXuong` phải đọc `done`, KHÔNG đọc `doneItems` ────────────────
  //
  // Máy chủ vẫn trả `doneItems` cho bản client đang mở dở. Nếu client mới lỡ
  // đọc lại khoá cũ thì bản vá này vô hiệu mà không ai thấy.
  /* Bỏ chú thích TRƯỚC khi soi. Chú thích kể lại mã CŨ khớp y hệt mã thật —
     phép kiểm này báo đỏ ngay lần chạy đầu vì đúng cái comment giải thích bản
     vá. Một phép kiểm báo oan sẽ bị tắt, nên nó phải soi MÃ, không soi chữ. */
  const boChuThich = (s) => s
    .replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '))
    .replace(/(^|[^:])\/\/[^\n]*/g, (m, p) => p + ' '.repeat(m.length - p.length));

  const than = /function syncXuong[\s\S]*?\n  \}/.exec(MA);
  check('rút được `syncXuong`', than !== null);
  if (than) {
    const ma = boChuThich(than[0]);
    check('`syncXuong` đọc `d.done` (danh sách cặp)', /d\.done\b/.test(ma));
    check('`syncXuong` KHÔNG còn đọc `doneItems`', !/doneItems/.test(ma),
      'còn tham chiếu doneItems trong MÃ (không tính chú thích)');
    check('`syncXuong` KHÔNG còn đoán bằng `getActive()`', !/getActive\(\)/.test(ma));
  }

  console.log(failures === 0 ? '\nOK — tiến độ không lem giữa các lộ trình' : `\n${failures} lỗi`);
  process.exitCode = failures === 0 ? 0 : 1;
}
