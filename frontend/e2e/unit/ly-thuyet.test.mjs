/**
 * Unit test — nhãn "Bản đầy đủ / Bản tóm tắt" phải nói đúng bản ĐANG HIỆN.
 *
 * ── LỖI ĐANG CHẶN LẠI (04/09/2026) ────────────────────────────────────────
 *
 * `renderTheory` tính hai thứ từ HAI nguồn khác nhau:
 *
 *     pick  = th[mucDo] || th.full || th.condensed || {}      ← CÓ đường lùi
 *     badge = (mucDo === 'full') ? 'Bản đầy đủ' : 'Bản tóm tắt'   ← KHÔNG
 *
 * Nhãn bám vào bản được YÊU CẦU (suy từ kết quả bài kiểm tra đầu vào), nội dung
 * bám vào bản THẬT SỰ CÓ. Hai thứ lệch nhau ngay khi một bài thiếu một bản: em
 * "Cần ôn 📘" mở một bài không có `full` sẽ đọc bản TÓM TẮT dưới nhãn
 * *"Bản đầy đủ — theo kết quả kiểm tra"*.
 *
 * ── ĐÂY LÀ MỘT LỖ CHƯA CẮN, VÀ NÓI THẲNG THẾ ─────────────────────────────
 *
 * Đo trên CSDL thật: cả 76 bài đều có ĐỦ hai bản, nên nhãn chưa nói dối lần
 * nào. Thứ giữ nó đúng là một sự trùng hợp về DỮ LIỆU, không phải một luật của
 * MÃ — và giáo trình thì sắp được nhập từ bảng tính, bởi người khác.
 *
 * Chạy: node e2e/unit/ly-thuyet.test.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const MA = readFileSync(join(GOC, 'public', 'static', 'js', 'lesson_hsa.js'), 'utf8');

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

function rutHam(ma, ten) {
  const m = new RegExp(`function\\s+${ten}\\s*\\(([^)]*)\\)\\s*\\{`).exec(ma);
  if (!m) return null;
  let sau = 1;
  let i = m.index + m[0].length;
  const dau = i;
  while (i < ma.length && sau > 0) {
    if (ma[i] === '{') sau += 1;
    else if (ma[i] === '}') sau -= 1;
    i += 1;
  }
  return sau === 0
    ? new Function(...m[1].split(',').map((s) => s.trim()), ma.slice(dau, i - 1))
    : null;
}

const chon = rutHam(MA, 'chonLyThuyet');
check('rút được `chonLyThuyet` từ lesson_hsa.js', typeof chon === 'function');

if (typeof chon === 'function') {
  const DAY_DU = { cards: [{ title: 'đầy đủ' }] };
  const TOM_TAT = { cards: [{ title: 'tóm tắt' }] };

  // ── Đủ cả hai bản: lấy đúng bản được yêu cầu, nhãn khớp ─────────────────
  {
    const a = chon({ full: DAY_DU, condensed: TOM_TAT }, 'full');
    check('yêu cầu `full`, có `full` → lấy full + nhãn "đầy đủ"',
      a.ban === DAY_DU && a.la_day_du === true, JSON.stringify(a));
    const b = chon({ full: DAY_DU, condensed: TOM_TAT }, 'condensed');
    check('yêu cầu `condensed`, có → lấy condensed + nhãn "tóm tắt"',
      b.ban === TOM_TAT && b.la_day_du === false, JSON.stringify(b));
  }

  // ── ĐÂY LÀ CA HỎNG: thiếu bản được yêu cầu → nhãn phải theo bản ĐƯỢC LẤY ─
  {
    const a = chon({ condensed: TOM_TAT }, 'full');
    check('bài THIẾU `full`, em "Cần ôn" → lấy tóm tắt và nhãn nói TÓM TẮT',
      a.ban === TOM_TAT && a.la_day_du === false,
      `${a.la_day_du ? 'nhãn nói ĐẦY ĐỦ' : ''} ${JSON.stringify(a.ban)}`);

    const b = chon({ full: DAY_DU }, 'condensed');
    check('bài THIẾU `condensed`, em "Vững" → lấy đầy đủ và nhãn nói ĐẦY ĐỦ',
      b.ban === DAY_DU && b.la_day_du === true, JSON.stringify(b));
  }

  // ── Không có bản nào: đừng khẳng định gì về thứ không hiện ra ────────────
  {
    const a = chon({}, 'full');
    check('không có bản nào → không nhận là "đầy đủ"',
      a.la_day_du === false && a.ban && !a.ban.cards, JSON.stringify(a));
    const b = chon(null, 'condensed');
    check('`theory` là null → không ném', b && b.la_day_du === false, JSON.stringify(b));
  }

  // ── Và chỗ GỌI phải dùng nó, nếu không đây chỉ là một hàm chết ───────────
  check('renderTheory dùng `chonLyThuyet` cho CẢ nội dung lẫn nhãn',
    /var chon = chonLyThuyet\(/.test(MA) && /chon\.la_day_du/.test(MA)
      && !/LEVELS\[state\.level\]\.theory === 'full'/.test(MA),
    'còn chỗ tính nhãn từ mức độ được YÊU CẦU');

  console.log(failures === 0 ? '\nOK — nhãn nói đúng bản đang hiện' : `\n${failures} lỗi`);
}
process.exitCode = failures === 0 ? 0 : 1;
