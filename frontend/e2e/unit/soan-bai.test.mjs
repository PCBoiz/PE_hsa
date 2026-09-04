/**
 * Unit test (Node thuần) — soạn nội dung bài KHÔNG được làm mất dữ liệu.
 *
 * BUG GỐC (đo 04/09/2026 trên cả 76 bài đang có). Bộ soạn cũ
 * `public/static/js/pages/admin.inline.js` dựng lại đối tượng bài TỪ ĐẦU mỗi
 * lần lưu, nên mọi trường nó không biết đều biến mất:
 *
 *   · `drill.time_seconds` — nó đọc/ghi `seconds`, engine đọc `time_seconds`;
 *   · `notes` `{tip, formula, key_points}` — nó xử lý `note` số ít, một trường
 *     KHÔNG bài nào có và engine không bao giờ đọc.
 *
 * Cái thứ nhất bị bộ kiểm phía máy chủ chặn nên không thành mất dữ liệu; cái
 * thứ hai thì không có hàng rào nào.
 *
 * Phép kiểm quan trọng nhất ở đây KHÔNG phải "trường tôi biết được lưu đúng" —
 * đó là thứ hiển nhiên và sẽ luôn xanh. Nó là **"trường tôi KHÔNG biết vẫn
 * còn"**, vì đó mới là thứ hỏng lặng lẽ và hỏng lần sau nữa, với một trường
 * chưa ai kịp nghĩ ra.
 *
 * Chạy: node e2e/unit/soan-bai.test.mjs   (exit 0 = pass, 1 = fail)
 */
import { register } from 'node:module';
import { pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
register('./hooks-nap-nguon.mjs', import.meta.url);

const { hopNhat, docRaBieuMau, truongLa } =
  await import(pathToFileURL(join(GOC, 'src', 'lib', 'soanBai.ts')).href);

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + JSON.stringify(them));
    failures++;
  }
}

/* Một bài THẬT, rút gọn từ dữ liệu đang có trong CSDL (04/09/2026). Giữ nguyên
   hình dạng `notes` và `drill.time_seconds` vì đó chính là thứ đang được canh. */
const BAI_THAT = {
  id: 'ql_12',
  index: 12,
  title: 'Xác suất cơ bản',
  subtitle: 'Biến cố và biến cố đối',
  topic_tag: 'Định lượng · Thống kê & Xác suất',
  xp_reward: 50,
  test: {
    intro: 'Ba câu định vị.',
    questions: [
      { id: 't1', type: 'mcq', question: 'P(A) là gì?', options: ['a', 'b'], answer: 'a', explain: 'x' },
    ],
  },
  assess: { strong_min: 3, ok_min: 2 },
  theory: {
    full: { title: 'Lý thuyết đầy đủ', cards: [{ icon: 'fa-book', title: 'Định nghĩa', body: '...' }] },
    condensed: { title: 'Tóm tắt', cards: [{ icon: 'fa-bolt', title: 'Nhanh', body: '...' }] },
  },
  notes: {
    tip: 'Tính "ít nhất một" thường dễ hơn qua biến cố đối.',
    formula: 'P(A) = (thuận lợi)/(tổng)',
    key_points: ['0 ≤ P(A) ≤ 1', 'P(A) + P(không A) = 1'],
  },
  drill: {
    intro: 'Tám câu, bấm giờ.',
    time_seconds: 80,
    questions: [{ id: 'd1', type: 'fill', question: '10% của 200?', answer: '20' }],
  },
  // Trường KHÔNG có trong biểu mẫu. Đại diện cho mọi trường sẽ được thêm sau
  // này mà màn hình soạn chưa biết tới.
  nguon_bien_soan: 'TopHSA · bản 2026-08',
  phien_ban: 3,
};

// ── 1) Đi một vòng nạp → lưu mà KHÔNG sửa gì: bài phải y nguyên ─────────────
{
  const m = docRaBieuMau(BAI_THAT, 12);
  const ra = hopNhat(BAI_THAT, m);

  check('vòng nạp→lưu giữ nguyên `drill.time_seconds`', ra.drill.time_seconds === 80, ra.drill);
  check('KHÔNG đẻ ra `drill.seconds`', !('seconds' in ra.drill), ra.drill);
  check('giữ nguyên cả khối `notes`',
    ra.notes && ra.notes.tip === BAI_THAT.notes.tip
      && ra.notes.formula === BAI_THAT.notes.formula
      && ra.notes.key_points.length === 2, ra.notes);
  check('GIỮ trường lạ `nguon_bien_soan`', ra.nguon_bien_soan === 'TopHSA · bản 2026-08');
  check('GIỮ trường lạ `phien_ban`', ra.phien_ban === 3);
  check('không đẻ ra `note` số ít (trường engine không đọc)', !('note' in ra));
  check('vòng tròn: JSON ra == JSON vào',
    JSON.stringify(ra) === JSON.stringify(BAI_THAT),
    { vao: Object.keys(BAI_THAT), ra: Object.keys(ra) });
}

// ── 2) Sửa một trường: chỉ trường ấy đổi ───────────────────────────────────
{
  const m = docRaBieuMau(BAI_THAT, 12);
  m.drillSeconds = 45;
  m.notesTip = 'Mẹo mới';
  const ra = hopNhat(BAI_THAT, m);

  check('đổi được đồng hồ phòng luyện', ra.drill.time_seconds === 45);
  check('đổi được mẹo', ra.notes.tip === 'Mẹo mới');
  check('công thức KHÔNG bị đụng', ra.notes.formula === BAI_THAT.notes.formula);
  check('trường lạ vẫn còn sau khi sửa', ra.phien_ban === 3);
  check('câu hỏi test không bị đụng',
    JSON.stringify(ra.test.questions) === JSON.stringify(BAI_THAT.test.questions));
}

// ── 3) Bản do bộ soạn CŨ ghi (`seconds`) phải được chữa lành ───────────────
{
  const cu = { ...BAI_THAT, drill: { intro: 'x', seconds: 33, questions: [] } };
  const m = docRaBieuMau(cu, 12);
  check('đọc được con số từ `seconds` của bản cũ', m.drillSeconds === 33);
  const ra = hopNhat(cu, m);
  check('ghi ra `time_seconds`', ra.drill.time_seconds === 33);
  check('và XOÁ `seconds` — để bộ kiểm máy chủ không từ chối cả bài',
    !('seconds' in ra.drill), ra.drill);
}

// ── 4) Làm rỗng hẳn một khối thì khối ấy biến mất ──────────────────────────
{
  const m = docRaBieuMau(BAI_THAT, 12);
  m.notesTip = ''; m.notesFormula = ''; m.notesKeyPoints = [];
  m.drillIntro = ''; m.drillQuestions = [];
  const ra = hopNhat(BAI_THAT, m);
  check('xoá hết ghi nhớ → bỏ khoá `notes`', !('notes' in ra));
  check('xoá hết phòng luyện → bỏ khoá `drill`', !('drill' in ra));
  check('nhưng trường lạ vẫn còn', ra.nguon_bien_soan !== undefined);
}

// ── 5) Rỗng MỘT PHẦN thì giữ khối lại ──────────────────────────────────────
{
  const m = docRaBieuMau(BAI_THAT, 12);
  m.notesKeyPoints = [];                     // xoá tạm các ý, còn mẹo
  m.drillQuestions = [];                     // xoá tạm câu, còn lời dẫn
  const ra = hopNhat(BAI_THAT, m);
  check('còn mẹo → `notes` vẫn còn', !!ra.notes && ra.notes.tip);
  check('bỏ `key_points` khi rỗng', !('key_points' in ra.notes));
  check('còn lời dẫn → `drill` vẫn còn', !!ra.drill && ra.drill.time_seconds === 80);
}

// ── 6) Bài chưa có nội dung: dựng mới không nổ ─────────────────────────────
{
  const m = docRaBieuMau(null, 7);
  check('bài trống → index lấy theo sort_order', m.index === 7);
  check('bài trống → đồng hồ mặc định 60', m.drillSeconds === 60);
  const ra = hopNhat(null, m);
  check('dựng mới ra object hợp lệ', !!ra.test && !!ra.theory);
  check('không đẻ ra khối rỗng thừa', !('notes' in ra) && !('drill' in ra), Object.keys(ra));
}

// ── 7) `truongLa` phải kể ĐÚNG những gì biểu mẫu không hiện ────────────────
{
  const la = truongLa(BAI_THAT);
  check('kể đúng hai trường lạ', JSON.stringify(la) === '["nguon_bien_soan","phien_ban"]', la);
  check('bài không có trường lạ → mảng rỗng', truongLa({ id: 'x', test: {} }).length === 0);
}

// ── 8) KHÔNG được sửa đối tượng gốc ────────────────────────────────────────
{
  const truoc = JSON.stringify(BAI_THAT);
  const m = docRaBieuMau(BAI_THAT, 12);
  m.title = 'Đổi tên';
  m.notesKeyPoints = [];
  hopNhat(BAI_THAT, m);
  check('`hopNhat` không sửa bản gốc', JSON.stringify(BAI_THAT) === truoc);
}

// ── 9) XOÁ một phần tử KHÔNG được làm phần tử khác đổi nội dung ────────────
//
// Đây là thao tác mà tám khối kiểm đầu tiên bỏ sót hoàn toàn — chúng chỉ thử
// SỬA. Bản gộp đầu khớp theo VỊ TRÍ, nên xoá phần tử thứ i làm mọi phần tử sau
// tụt lên một chỗ và thừa hưởng khoá lạ của người khác.
//
// Đo trên 76 bài thật: 8/456 lượt xoá thẻ và 227/836 lượt xoá câu làm một phần
// tử KHÁC đổi nội dung. Với thẻ, thứ rò là `visual` — đồ thị mà engine VẼ RA,
// tức hiển thị sai cho học viên chứ không phải rác ẩn.
{
  const bai = {
    id: 'x', index: 1, title: 'T',
    test: { intro: '', questions: [
      { id: 't1', type: 'mcq', question: 'A?', options: ['1', '2'], answer: '1' },
      { id: 't2', type: 'fill', question: 'B?', answer: '9' },
    ] },
    theory: { full: { title: 'LT', cards: [
      { icon: 'i1', title: 'Có đồ thị', body: 'x', visual: { type: 'curve', fn: 'x*x' } },
      { icon: 'i2', title: 'Không đồ thị', body: 'y' },
    ] } },
  };

  // Xoá THẺ ĐẦU (thẻ mang đồ thị). Thẻ còn lại vốn không có `visual`.
  const m1 = docRaBieuMau(bai, 1);
  m1.fullCards = m1.fullCards.slice(1);
  const the = hopNhat(bai, m1).theory.full.cards;
  check('xoá thẻ: còn đúng 1 thẻ', the.length === 1, the);
  check('xoá thẻ: thẻ còn lại giữ đúng tiêu đề của NÓ', the[0].title === 'Không đồ thị', the[0]);
  check('xoá thẻ: KHÔNG thừa hưởng đồ thị của thẻ bị xoá', !('visual' in the[0]), the[0]);
  check('xoá thẻ: không rò khoá nội bộ `_k` xuống CSDL', !('_k' in the[0]), the[0]);

  // Xoá CÂU ĐẦU (câu trắc nghiệm có `options`). Câu còn lại là dạng điền.
  const m2 = docRaBieuMau(bai, 1);
  m2.testQuestions = m2.testQuestions.slice(1);
  const cau = hopNhat(bai, m2).test.questions;
  check('xoá câu: còn đúng 1 câu', cau.length === 1, cau);
  check('xoá câu: câu còn lại vẫn là dạng điền', cau[0].type === 'fill', cau[0]);
  check('xoá câu: KHÔNG nhiễm `options` của câu bị xoá', !('options' in cau[0]), cau[0]);
  check('xoá câu: không rò `_k`', !('_k' in cau[0]), cau[0]);
}

// ── 10) Đảo thứ tự: khoá lạ phải đi THEO PHẦN TỬ ──────────────────────────
{
  const bai = {
    id: 'x', index: 1, title: 'T',
    test: { intro: '', questions: [
      { id: 'a', type: 'fill', question: 'A?', answer: '1', ghi_chu_la: 'của A' },
      { id: 'b', type: 'fill', question: 'B?', answer: '2', ghi_chu_la: 'của B' },
    ] },
    theory: { full: { title: 'LT', cards: [{ title: 'c', body: 'd' }] } },
  };
  const m = docRaBieuMau(bai, 1);
  m.testQuestions = [m.testQuestions[1], m.testQuestions[0]];
  const q = hopNhat(bai, m).test.questions;
  check('đảo thứ tự: khoá lạ đi theo CÂU, không theo vị trí',
    q[0].ghi_chu_la === 'của B' && q[1].ghi_chu_la === 'của A', q);
}

// ── 11) Phần tử MỚI không được gộp nhầm vào phần tử cũ ────────────────────
{
  const bai = {
    id: 'x', index: 1, title: 'T',
    test: { intro: '', questions: [
      { id: 'a', type: 'mcq', question: 'A?', options: ['1', '2'], answer: '1', rieng: 1 },
    ] },
    theory: { full: { title: 'LT', cards: [{ title: 'c', body: 'd' }] } },
  };
  const m = docRaBieuMau(bai, 1);
  m.testQuestions = [...m.testQuestions,
    { id: 'moi', type: 'fill', question: 'Mới?', answer: '5' }];
  const q = hopNhat(bai, m).test.questions;
  check('câu mới KHÔNG thừa hưởng gì của câu cũ',
    !('rieng' in q[1]) && !('options' in q[1]), q[1]);
  check('câu cũ vẫn giữ khoá lạ của nó', q[0].rieng === 1, q[0]);
}

console.log(failures === 0 ? '\nOK — soạn bài không làm mất dữ liệu' : `\n${failures} lỗi`);
/* `process.exitCode` chứ KHÔNG `process.exit()`. Tệp này đăng ký một loader
   hook, tức có một worker chạy nền; cắt ngang tiến trình trong lúc worker còn
   sống làm libuv nổ assertion trên Windows và trả mã thoát 127 — một lần hỏng
   GIẢ, và hỏng giả trong CI đắt hơn hỏng thật vì nó dạy người ta chạy lại cho
   qua. Đặt mã thoát rồi để Node tự kết thúc thì không có cuộc đua nào.
   (Đo 04/09: chỉ nổ khi stdout có ống dẫn, nên chạy trần thì không thấy.) */
process.exitCode = failures === 0 ? 0 : 1;
