/**
 * Unit test — biểu mẫu TẠO NHANH LỚP GIA SƯ (`lop-hoc/giaSu.ts`, mục 1.2b 24/09/2026).
 *
 * Canh ba chuyện hàm thuần phải giữ: (1) thiếu em / thiếu giảng viên / lịch hỏng bị
 * chặn TRƯỚC khi gửi, câu lỗi nói đúng ô; (2) thân request đúng tên khoá máy chủ đọc
 * (`student_id`, `teacher_id`, `weekdays`, `start_time`, `duration_minutes`, `from`,
 * `to`, `generate`) — đổi tên một khoá là máy chủ lặng lẽ không sinh lịch; (3) bỏ tick
 * "sinh buổi" thì KHÔNG gửi khoá lịch nào (máy chủ thấy `generate` là sinh).
 *
 * Chạy: node e2e/unit/lop-gia-su.test.mjs
 */
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const { THU, congNgay, formGiaSuRong, thanGiaSu } = await import(
  'file://' + join(GOC, 'src', 'app', '(standalone)', 'quan-tri', 'lop-hoc', 'giaSu.ts').replace(/\\/g, '/')
);

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

const du = { ...formGiaSuRong('2026-10-05'), emId: 42, giangVienId: '7', thu: [4, 2, 2] };

// ── Thân request đúng khoá máy chủ đọc ─────────────────────────────────────
{
  const { body, loi } = thanGiaSu(du, true);
  check('biểu mẫu đủ thì không lỗi', loi === null, loi);
  check('student_id / teacher_id là SỐ', body.student_id === 42 && body.teacher_id === 7, JSON.stringify(body));
  check('thứ bỏ trùng + sắp tăng dần', JSON.stringify(body.weekdays) === '[2,4]', JSON.stringify(body.weekdays));
  check('có generate + đủ khoá lịch', body.generate === true && body.start_time === '19:30'
    && body.duration_minutes === 90 && body.from === '2026-10-05' && body.to === '2026-12-27', JSON.stringify(body));
  check('dry_run đi theo tham số', body.dry_run === true && thanGiaSu(du, false).body.dry_run === false);
  check('tên để trống → null (máy chủ tự đặt)', body.name === null);
  check('môn trống → null = cả ba môn', body.course_id === null);
}

// ── Bỏ tick "sinh buổi" → không một khoá lịch nào ──────────────────────────
{
  const { body, loi } = thanGiaSu({ ...du, sinhBuoi: false, thu: [] }, false);
  const khoaLich = ['generate', 'weekdays', 'start_time', 'duration_minutes', 'from', 'to'].filter((k) => k in body);
  check('không sinh buổi thì không gửi khoá lịch', loi === null && khoaLich.length === 0, khoaLich.join(','));
}

// ── Chặn trước khi gửi, câu lỗi đúng ô ──────────────────────────────────────
const CA = [
  ['thiếu em', { emId: null }, 'học viên'],
  ['thiếu giảng viên', { giangVienId: '' }, 'giảng viên'],
  ['chưa chọn thứ', { thu: [] }, 'thứ trong tuần'],
  ['giờ sai dạng', { gio: '7h30' }, 'HH:MM'],
  ['giờ 24:00', { gio: '24:00' }, 'HH:MM'],
  ['số phút có chữ', { phut: '90 phút' }, 'số phút'],
  ['số phút 0', { phut: '0' }, 'số phút'],
  ['số phút vượt trần', { phut: '601' }, 'số phút'],
  ['số phút lẻ', { phut: '90.5' }, 'số phút'],
  ['thiếu ngày', { den: '' }, 'ngày'],
  ['kết thúc trước bắt đầu', { tu: '2026-10-10', den: '2026-10-01' }, 'sau ngày bắt đầu'],
];
for (const [ten, sua, can] of CA) {
  const { body, loi } = thanGiaSu({ ...du, ...sua }, false);
  check(`${ten} → chặn, nói "${can}"`, body === null && typeof loi === 'string' && loi.includes(can), loi);
}

// ── Hằng + tiện ích ────────────────────────────────────────────────────────
check('bảy thứ, ISO 1..7, CN cuối', THU.length === 7 && THU[0].so === 1 && THU[6].nhan === 'CN');
check('cộng ngày qua tháng', congNgay('2026-10-30', 3) === '2026-11-02', congNgay('2026-10-30', 3));
check('lịch mặc định 12 tuần', formGiaSuRong('2026-10-05').den === '2026-12-27');

console.log(failures === 0 ? '\nOK — biểu mẫu lớp gia sư' : `\n${failures} lỗi`);
process.exitCode = failures === 0 ? 0 : 1;
