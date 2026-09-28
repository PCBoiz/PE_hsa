/**
 * Unit test — §66 · tờ báo cáo phụ huynh "sống" phải NÓI RA là nó sống, và mục "Lịch học có
 * thay đổi" phải phân biệt được "không có gì đổi" với "máy chủ chưa trả mục này".
 *
 * ── HAI CHỖ SAI KHÔNG KÊU LÊN ────────────────────────────────────────────
 *
 * ① **Im lặng về việc tờ sống.** Từ 28/09 chìa mở ra số liệu TỚI HÔM NAY chứ không đứng yên ở
 *   ngày cấp. Phụ huynh mở lại cùng một đường link sau ba tuần sẽ thấy số khác. Không nói gì
 *   thì đó trông như trung tâm sửa số cũ — và người đi giải thích sẽ là giảng viên, không
 *   phải tờ giấy. Hai mốc `song.toiNgay` và `song.kyCap` có đúng để nói chuyện ấy.
 *
 * ② **`bc.thayDoi && length > 0` hay chỉ `bc.thayDoi`.** Mảng RỖNG trong JavaScript là giá
 *   trị THẬT, nên `{bc.thayDoi && <h3>…}` sẽ dựng cả tiêu đề "Lịch học có thay đổi" lẫn một
 *   danh sách trống cho mọi lớp không đổi gì — tức phần lớn các lớp. Một tiêu đề báo động
 *   xuất hiện trên mọi tờ là một tiêu đề thôi được đọc.
 *
 * Kiểm bằng chữ trong nguồn: hai nhánh này chỉ hiện với dữ liệu thật của một chìa thật, và
 * dựng lại chúng trên máy thì tốn hơn thứ chúng canh.
 *
 * Chạy: node e2e/unit/to-bao-cao-song.test.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const TO = join(GOC, 'src', 'components', 'ToBaoCao.tsx');
const HINH = join(GOC, 'src', 'lib', 'hinhDang.ts');

/** Bỏ chú thích trước khi đo — câu trong chú thích không phải câu người đọc thấy, và đếm cả
 *  chúng thì viết một dòng giải thích là làm đỏ phép kiểm của chính mình. */
function boChuThich(ma) {
  return ma.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
}
const MA = boChuThich(readFileSync(TO, 'utf8'));
const MA_HINH = boChuThich(readFileSync(HINH, 'utf8'));

let hong = 0;
function kiem(ten, dung, them) {
  if (dung) console.log('  ✓', ten);
  else {
    console.error('  ✗', ten, them === undefined ? '' : '→ ' + them);
    hong++;
  }
}

console.log('Tờ báo cáo phụ huynh — §66 link sống + thay đổi lịch');

// 1 · Mảng rỗng KHÔNG được dựng tiêu đề.
kiem('mục "Lịch học có thay đổi" chỉ dựng khi mảng CÓ phần tử',
     /bc\.thayDoi\s*&&\s*bc\.thayDoi\.length\s*>\s*0/.test(MA),
     'thiếu phép so `.length > 0` — mảng rỗng là giá trị thật, tiêu đề sẽ hiện trên mọi tờ');

// 2 · Nhãn lấy từ máy chủ, không dịch lại ở màn (RULES §7).
kiem('nhãn từng dòng lấy từ máy chủ (`t.nhan`), không so mã ở màn',
     /\{t\.nhan\}/.test(MA) && !/['"]cancelled['"]/.test(MA),
     'màn đang tự dịch mã trạng thái — tờ này còn có bản PDF và bản thư, ba nơi dịch là ba bản lệch');

// 3 · Nói ra rằng tờ sống, và nêu cả hai mốc.
const dauSong = MA.search(/bc\.song\s*&&/);
kiem('có nhánh riêng cho tờ mở bằng chìa (`bc.song`)', dauSong >= 0,
     'không thấy nhánh nào đọc `bc.song`');
const khoiSong = dauSong >= 0 ? MA.slice(dauSong, dauSong + 900) : '';
kiem('nêu mốc SỐ LIỆU tính tới ngày nào', /song\.toiNgay/.test(khoiSong),
     'thiếu `song.toiNgay` — phụ huynh không biết số này mới tới đâu');
kiem('nêu cả KỲ trung tâm đã cấp, để đối chiếu tờ cũ',
     /song\.kyCap\.from/.test(khoiSong) && /song\.kyCap\.to/.test(khoiSong),
     'thiếu `song.kyCap` — mở lại thấy số khác mà không có mốc nào giải thích');

// 4 · Hai khoá phải là TUỲ CHỌN ở lớp kiểm hình dạng: tờ của giảng viên không đi qua chìa nào,
//     bắt buộc chúng là làm màn ấy ném ngay ở bước kiểm hình dạng.
kiem('`song` khai optional trong hinhDang.ts',
     /song:\s*z\.optional\(/.test(MA_HINH),
     'bắt buộc `song` sẽ làm tờ của giảng viên (không qua chìa) hỏng ở bước kiểm hình dạng');
kiem('`thayDoi` khai optional trong hinhDang.ts',
     /thayDoi:\s*z\.optional\(/.test(MA_HINH),
     'như trên');

// 5 · Cắt bớt thì phải NÓI RA. Máy chủ chỉ trả `TRAN` dòng; im lặng thì phụ huynh đếm được
//     12 và tưởng đó là tất cả, trong khi buổi ảnh hưởng tới con có thể nằm ở dòng 13.
kiem('nói ra khi danh sách bị cắt (`thayDoiConNua`)',
     /bc\.thayDoiConNua/.test(MA),
     'màn đang bỏ qua cờ cắt bớt — tờ in 12 dòng rồi im lặng');
kiem('`thayDoiConNua` khai optional trong hinhDang.ts',
     /thayDoiConNua:\s*z\.optional\(/.test(MA_HINH));

if (hong) {
  console.error(`\n${hong} phép kiểm ĐỎ.`);
  process.exit(1);
}
console.log('\nTất cả xanh.');
