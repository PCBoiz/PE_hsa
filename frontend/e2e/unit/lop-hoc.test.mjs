/**
 * Unit test — biểu mẫu SỬA LỚP không được xoá trắng trường nó không hiển thị.
 *
 * ── LỖI ĐANG CHẶN LẠI ─────────────────────────────────────────────────────
 *
 * Bản cũ (`public/static/js/pages/admin.inline.js`, đã xoá) đổ **7 trong 11**
 * trường vào biểu mẫu sửa, rồi `PUT` gửi cả 11. Bốn trường không được đổ —
 * `meeting_url`, `starts_on`, `ends_on`, `note` — đi lên máy chủ dưới dạng
 * chuỗi rỗng, và `_clean_class_payload` hiểu chuỗi rỗng là `NULL`.
 *
 * Tức **sửa tên lớp là xoá trắng link họp và ghi chú của lớp đó.** Không hỏi,
 * không báo. Cùng một họ với lỗi "dựng lại thay vì đè lên" của bộ soạn bài học,
 * và cùng một cách chặn: một phép kiểm hỏi vòng đi–về có giữ nguyên không.
 *
 * ── VÌ SAO KIỂM THEO BẢNG CHỨ KHÔNG LIỆT KÊ TAY ───────────────────────────
 *
 * Phép kiểm duyệt `TRUONG` — bảng trường trong chính mã nguồn — chứ không chép
 * một danh sách 13 tên sang đây. Chép sang thì trường thứ 14 thêm tháng sau sẽ
 * KHÔNG được kiểm, và phép kiểm vẫn xanh: nó chỉ xanh về 13 trường nó biết.
 * Đúng cái bẫy mà bản đầu của `thoat-html.test.mjs` đã rơi vào.
 *
 * Chạy: node e2e/unit/lop-hoc.test.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const THU_MUC = join(GOC, 'src', 'app', '(standalone)', 'quan-tri', 'lop-hoc');

const { TRUONG, formRong, formTuLop, thanForm } = await import(
  'file://' + join(THU_MUC, 'lop.ts').replace(/\\/g, '/')
);

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

/* Một lớp NHƯ `teaching/reports.py::class_list` trả về, mọi trường CÓ giá trị.
   Trường nào cũng khác rỗng là cố ý: một trường để `null` ở đây sẽ khiến vòng
   đi–về đúng một cách tình cờ (null → '' → null) và giấu mất lỗi. */
const LOP = {
  id: 7,
  code: 'HSA-01',
  name: 'Luyện HSA đợt 1/2027 — Ca tối',
  course: 'hsa_quantitative',
  courseTitle: 'Tư duy Định lượng',
  teacherId: 42,
  teacherName: 'Cô Lan',
  schedule: 'T3–T5 19:30',
  status: 'active',
  capacity: 30,
  members: 12,
  startsOn: '2026-09-10',
  endsOn: '2027-02-28',
  examDate: '2027-03-15',
  meetingUrl: 'https://meet.google.com/abc-defg-hij',
  note: 'Lớp có 3 em thi lại',
  termId: 3,
  termName: 'Đợt 1/2027',
  termCode: 'D1-2027',
};

console.log(`Bảng trường có ${TRUONG.length} dòng.\n`);

// ── ① Vòng đi–về: nạp lớp → biểu mẫu → thân request, KHÔNG mất trường nào ───
const than = thanForm(formTuLop(LOP));
for (const t of TRUONG) {
  const goc = LOP[t.row];
  const ve = than[t.than];
  const mong = t.kieu === 'so' ? goc : goc === null ? null : String(goc);
  check(
    `"${t.than}" đi–về nguyên vẹn`,
    ve === mong,
    `gốc ${JSON.stringify(goc)} → gửi lên ${JSON.stringify(ve)}`,
  );
}

// ── ② Bảng trường phải PHỦ HẾT thân request, không thừa không thiếu ─────────
check(
  'thân request có đúng số khoá bằng số dòng bảng trường',
  Object.keys(than).length === TRUONG.length,
  `${Object.keys(than).length} khoá / ${TRUONG.length} dòng`,
);

// ── ③ Mọi trường trong bảng PHẢI có một ô trên màn hình ─────────────────────
//
// Đây là nửa còn lại của lỗi. Vòng đi–về ở trên chỉ chứng minh hàm thuần đúng;
// nếu biểu mẫu quên vẽ ô cho `note` thì `form.note` luôn là chuỗi rỗng và trường
// ấy vẫn bị xoá trắng — hàm thuần không có cách nào biết.
const MA_CLIENT = readFileSync(join(THU_MUC, 'LopHocClient.tsx'), 'utf8');
for (const t of TRUONG) {
  const co = new RegExp(`o(?:Chu|Ngay|Chon)\\(\\s*'${t.form}'`).test(MA_CLIENT);
  check(`"${t.form}" có ô nhập trên màn hình`, co);
}

// ── ④ Biểu mẫu rỗng không được gửi rác lên ──────────────────────────────────
const thanRong = thanForm(formRong());
check(
  'biểu mẫu rỗng gửi null cho mọi trường trừ status',
  Object.entries(thanRong).every(([k, v]) => (k === 'status' ? v === 'draft' : v === null)),
  JSON.stringify(thanRong),
);

// ── ⑤ Số về đúng KIỂU SỐ, không phải chuỗi ─────────────────────────────────
//
// `capacity: "30"` qua được `int(body['capacity'])` của backend nên lỗi này im
// lặng — cho tới khi ai đó so sánh `capacity > members` ở phía JS.
for (const t of TRUONG.filter((x) => x.kieu === 'so')) {
  check(`"${t.than}" gửi lên là số, không phải chuỗi`, typeof than[t.than] === 'number',
    typeof than[t.than]);
}

console.log(failures === 0 ? '\nOK — sửa lớp không xoá trắng trường nào' : `\n${failures} lỗi`);
process.exitCode = failures === 0 ? 0 : 1;
