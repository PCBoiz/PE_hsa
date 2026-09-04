/**
 * Unit test — engine bài học phải NÓI LẠI câu của máy chủ, đừng đổ cho mạng.
 *
 * ── LỖI ĐANG CHẶN LẠI (04/09/2026) ────────────────────────────────────────
 *
 * `lesson_hsa.js::complete` chỉ phân biệt 404 với "mọi thứ khác", và "mọi thứ
 * khác" hiện ra là *"Chưa lưu được tiến độ — kiểm tra mạng rồi mở lại bài."*
 *
 * Nhưng máy chủ trả những câu rất cụ thể:
 *
 *     403  "Bạn chưa ghi danh khoá này."
 *     400  "Bài này có phần luyện tập — làm ít nhất một câu rồi mới…"
 *
 * Nói "kiểm tra mạng" ở đó là NÓI DỐI. Mạng vẫn tốt, máy chủ đã trả lời tử tế,
 * và học viên bị đẩy đi sửa nhầm chỗ: họ sẽ tắt wifi bật lại, đổi trình duyệt,
 * rồi kết luận là sản phẩm hỏng. Một thông báo lỗi sai chỗ đắt hơn không có
 * thông báo, vì nó tiêu thời gian của người dùng vào một hướng chắc chắn sai.
 *
 * Hàm được RÚT THẲNG từ `lesson_hsa.js` chứ không chép sang — bản chép sẽ được
 * vá còn tệp thật thì không.
 *
 * Chạy: node e2e/unit/loi-may-chu.test.mjs
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

const cau = rutHam(MA, 'cauLoiMayChu');
check('rút được `cauLoiMayChu` từ lesson_hsa.js', typeof cau === 'function');

if (typeof cau === 'function') {
  const CHUNG = 'Chưa lưu được tiến độ — kiểm tra mạng rồi mở lại bài.';

  // ── Câu THẬT của máy chủ phải được nói lại nguyên văn ────────────────────
  //
  // Hai chuỗi dưới đây lấy ĐÚNG từ `lessons/views.py`. Nếu ai đó đổi câu ở
  // backend thì phép kiểm này vẫn xanh (nó chỉ kiểm cơ chế), nhưng cơ chế mới
  // là thứ hỏng được — câu chữ thì hỏng cũng không ai mất tiến độ.
  for (const [ma_loi, thong_diep] of [
    [403, 'Bạn chưa ghi danh khoá này.'],
    [400, 'Bài này có phần luyện tập — làm ít nhất một câu rồi mới đánh dấu hoàn thành được.'],
    [409, 'Đề này đã có 5 lượt làm bài.'],
  ]) {
    check(`${ma_loi}: nói lại câu của máy chủ`,
      cau(ma_loi, { error: thong_diep }) === thong_diep, cau(ma_loi, { error: thong_diep }));
  }

  // ── Hình dạng object của bộ xử lý lỗi chung ──────────────────────────────
  check('đọc được `error` dạng object {status, message, detail}',
    cau(404, { error: { status: 404, message: 'Không tìm thấy tài nguyên', detail: '/x' } })
      === 'Không tìm thấy tài nguyên');

  // ── Không đọc được thân thì mới về câu chung ─────────────────────────────
  check('mất mạng (không có thân) → câu chung', cau(0, null) === CHUNG, cau(0, null));
  check('500 không kèm câu nào → câu chung', cau(500, {}) === CHUNG, cau(500, {}));
  check('404 không kèm câu nào → câu riêng của 404',
    cau(404, {}) === 'Không lưu được: máy chủ không tìm thấy bài này.', cau(404, {}));

  // ── Chuỗi rỗng / khoảng trắng KHÔNG được tính là một câu ─────────────────
  //
  // `{"error": ""}` mà nói lại nguyên văn thì học viên thấy một hộp thông báo
  // TRỐNG — tệ hơn cả câu chung.
  check('`error` rỗng → câu chung', cau(400, { error: '' }) === CHUNG, cau(400, { error: '' }));
  check('`error` toàn khoảng trắng → câu chung',
    cau(400, { error: '   ' }) === CHUNG, cau(400, { error: '   ' }));
  check('`error.message` rỗng → câu chung',
    cau(400, { error: { message: '' } }) === CHUNG, cau(400, { error: { message: '' } }));

  // ── Và chỗ GỌI phải thật sự dùng nó ─────────────────────────────────────
  //
  // Hàm đúng mà không ai gọi thì phép kiểm ở trên chỉ chứng nhận một hàm chết.
  const goi = /flashNote\(cauLoiMayChu\(r\.status,\s*d\)\)/.test(MA);
  check('nhánh `!r.ok` của complete() gọi `cauLoiMayChu`', goi);

  console.log(failures === 0 ? '\nOK — engine nói lại đúng câu của máy chủ' : `\n${failures} lỗi`);
}
process.exitCode = failures === 0 ? 0 : 1;
