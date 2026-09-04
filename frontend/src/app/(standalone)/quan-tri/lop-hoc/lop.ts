/**
 * Biểu mẫu lớp học ↔ thân request — hàm THUẦN, tách khỏi React để kiểm được.
 *
 * ── VÌ SAO TÁCH RA (04/09/2026) ─────────────────────────────────────────────
 *
 * Bản cũ (`admin.inline.js`, đã xoá) đổ **7 trong 11** trường vào biểu mẫu sửa,
 * rồi `PUT` gửi cả 11. Bốn trường không được đổ — `meeting_url`, `starts_on`,
 * `ends_on`, `note` — đi lên máy chủ dưới dạng chuỗi rỗng, và `_clean_class_payload`
 * hiểu chuỗi rỗng là `NULL`. Tức **sửa tên lớp là xoá trắng link họp và ghi chú
 * của lớp đó**, không hỏi gì, không báo gì.
 *
 * Lỗi ấy không nhìn thấy được khi đọc mã: chỗ đổ dữ liệu và chỗ gửi dữ liệu
 * nằm cách nhau 60 dòng, mỗi chỗ đọc riêng đều hợp lý. Nó chỉ lộ ra khi đặt hai
 * hàm CẠNH NHAU và hỏi "vòng đi–về có giữ nguyên không". Nên hai hàm ấy nằm ở
 * đây, cạnh nhau, và có một phép kiểm hỏi đúng câu đó với MỌI trường —
 * `e2e/unit/lop-hoc.test.mjs`.
 *
 * Trường thứ 12 thêm tháng sau sẽ được bảo vệ mà không ai phải nhớ, vì phép kiểm
 * duyệt theo `TRUONG` chứ không liệt kê tay.
 */

/** Một lớp như `teaching/reports.py::class_list` trả về. */
export type LopRow = {
  id: number;
  code: string | null;
  name: string;
  /** `class_list` gọi cột `course_id` là `course`. */
  course: string | null;
  courseTitle: string | null;
  teacherId: number | null;
  teacherName: string | null;
  schedule: string | null;
  status: string;
  capacity: number | null;
  members: number;
  startsOn: string | null;
  endsOn: string | null;
  examDate: string | null;
  meetingUrl: string | null;
  note: string | null;
  termId: number | null;
  termName: string | null;
  termCode: string | null;
};

export type Form = Record<string, string>;

/**
 * Bảng trường DUY NHẤT: khoá trong biểu mẫu ↔ khoá trong `LopRow` ↔ khoá trong
 * thân request. Ba tên khác nhau cho cùng một thứ là chuyện có thật ở đây
 * (`course` / `courseTitle` / `course_id`), nên chúng phải nằm cùng một dòng.
 */
export const TRUONG = [
  { form: 'code', row: 'code', than: 'code', kieu: 'chu' },
  { form: 'name', row: 'name', than: 'name', kieu: 'chu' },
  { form: 'schedule', row: 'schedule', than: 'schedule', kieu: 'chu' },
  { form: 'meetingUrl', row: 'meetingUrl', than: 'meeting_url', kieu: 'chu' },
  { form: 'note', row: 'note', than: 'note', kieu: 'chu' },
  { form: 'startsOn', row: 'startsOn', than: 'starts_on', kieu: 'chu' },
  { form: 'endsOn', row: 'endsOn', than: 'ends_on', kieu: 'chu' },
  { form: 'examDate', row: 'examDate', than: 'exam_date', kieu: 'chu' },
  { form: 'course', row: 'course', than: 'course_id', kieu: 'chu' },
  { form: 'status', row: 'status', than: 'status', kieu: 'chu' },
  { form: 'teacherId', row: 'teacherId', than: 'teacher_id', kieu: 'so' },
  { form: 'termId', row: 'termId', than: 'term_id', kieu: 'so' },
  { form: 'capacity', row: 'capacity', than: 'capacity', kieu: 'so' },
] as const;

/** Biểu mẫu rỗng — dùng cho "Thêm lớp". `status` mặc định là bản nháp. */
export function formRong(): Form {
  const f: Form = {};
  for (const t of TRUONG) f[t.form] = '';
  f.status = 'draft';
  return f;
}

/** Đổ MỘT lớp vào biểu mẫu. Mọi trường trong `TRUONG`, không sót cái nào. */
export function formTuLop(row: Partial<LopRow>): Form {
  const f: Form = {};
  for (const t of TRUONG) {
    // Thu hẹp kiểu thay vì `String(v)` trên `unknown`: một object lọt vào đây
    // sẽ thành chuỗi "[object Object]" rồi đi thẳng lên máy chủ dưới dạng tên
    // lớp. eslint chặn đúng chỗ ấy (`no-base-to-string`).
    const v: unknown = (row as Record<string, unknown>)[t.row];
    f[t.form] = typeof v === 'string' ? v : typeof v === 'number' ? String(v) : '';
  }
  return f;
}

/**
 * Biểu mẫu → thân request.
 *
 * Ô để trống thành `null`, KHÔNG thành chuỗi rỗng: `_clean_class_payload` coi
 * chuỗi rỗng là `NULL` nên hai đằng cùng nghĩa, nhưng gửi `null` thì ý định
 * hiện rõ ngay trên đường truyền khi ai đó soi request.
 */
export function thanForm(f: Form): Record<string, string | number | null> {
  const body: Record<string, string | number | null> = {};
  for (const t of TRUONG) {
    const v = (f[t.form] ?? '').trim();
    if (t.kieu === 'so') {
      body[t.than] = v === '' ? null : Number(v);
    } else {
      body[t.than] = v === '' ? null : v;
    }
  }
  return body;
}
