/**
 * HÌNH DẠNG dùng chung cho nhiều trang — T18 mức 2 (14/09/2026).
 *
 * Mỗi trang tự khai hình dạng của phản hồi nó đọc, ngay cạnh lời gọi
 * `serverJson`. Tệp này chỉ giữ những hình dạng mà HAI trang trở lên cùng đọc
 * (tờ báo cáo phụ huynh có đường giảng viên và đường công khai; "chi tiết lớp"
 * có trang buổi học và trang bài tập). Chép mỗi nơi một bản là hai bản sẽ trôi.
 *
 * `looseObject` ở mọi tầng: máy chủ THÊM khoá thì màn hình không hỏng; chỉ khoá
 * màn hình ĐỌC mà thiếu hoặc sai kiểu mới là lỗi — và lỗi ấy hiện thành một
 * câu nêu đúng ô, thay vì một trang trông như "chưa có dữ liệu".
 */
import { z } from 'zod';

import type { HinhDang } from '@/lib/server-api';
import type { BaoCao } from '@/components/ToBaoCao';

const so = z.number();
const soHoacTrong = z.number().nullable();
const chu = z.string().nullable();

const CHU_DE = z.looseObject({
  course: z.string(),
  courseTitle: chu,
  topic: z.string(),
  mastery: so,
});

/** Tờ báo cáo phụ huynh — `teaching/parent_report.py::dung_bao_cao` (+ bản rút gọn cho link). */
export const HD_BAO_CAO = z.looseObject({
  student: z.looseObject({
    id: so, name: chu, email: chu.optional(), phone: chu.optional(),
  }),
  parent: z.looseObject({
    name: z.string(), phone: z.string().optional(), email: z.string().optional(),
  }),
  class: z.looseObject({ id: so, name: z.string(), code: chu, teacher: chu }),
  membership: z.looseObject({
    joinedAt: chu, leftAt: chu, status: z.string(), teacherNote: chu,
  }),
  period: z.looseObject({ from: z.string(), to: z.string(), weeks: so }),
  attendance: z.looseObject({
    sessionsTotal: so, sessionsCounted: so, sessionsUnmarked: so,
    present: so, late: so, absent: so, excused: so, noRecord: so,
    attendedPct: soHoacTrong,
  }),
  study: z.looseObject({
    lessonsDone: so, mockCount: so, mockAvg: soHoacTrong, mockBest: soHoacTrong,
    mockTrend: z.enum(['up', 'down', 'flat']).nullable(),
  }),
  // Kỳ thi thử tại trung tâm — `null` khi chưa nhập tờ kết quả nào, và `optional`
  // vì một bản dựng cũ của máy chủ chưa gửi khoá này. Thiếu nó KHÔNG được làm
  // hỏng cả tờ báo cáo: phụ huynh đang mở link trên điện thoại.
  centerExam: z.looseObject({
    date: z.string(),
    round: chu,
    score: so,
    max: so,
    sections: z.array(z.looseObject({ phan: so, ten: z.string(), diem: so, toiDa: so })),
    weakUnits: z.array(z.looseObject({ phan: so, ten: z.string(), pct: so })),
    unitsMeasured: so,
    previous: z.looseObject({
      date: z.string(), round: chu, score: so, delta: so,
    }).nullable(),
  }).nullable().optional(),
  // Nhịp từng tuần — `nullable().optional()` cùng lý do với `centerExam`.
  weekly: z.looseObject({
    weeks: z.array(z.looseObject({
      from: z.string(), to: z.string(), days: so, attended: so, attendanceCounted: so,
      lessons: so, drills: so, submissions: so,
    })),
    omitted: so,
  }).nullable().optional(),
  assignments: z.array(z.looseObject({
    id: so, title: z.string(), topic: chu, dueAt: chu, maxScore: z.number().nullable(),
    submittedAt: chu, score: z.number().nullable(), feedback: chu, gradedAt: chu,
  })).optional(),
  kiemTra: z.array(z.looseObject({
    id: so, title: z.string(), topic: chu, heldOn: z.string(), maxScore: z.number().nullable(),
    score: z.number().nullable(), absent: z.boolean(), feedback: chu,
  })).optional(),
  topics: z.looseObject({
    weak: z.array(CHU_DE),
    strong: z.array(CHU_DE),
    measured: so,
    total: so,
    courses: z.array(z.looseObject({
      id: z.string(), title: z.string(), lessonsDone: so, lessonsTotal: so, pct: so,
    })),
  }),
  warnings: z.array(z.string()),
}) satisfies HinhDang<BaoCao>;

/**
 * Chi tiết lớp — `teaching/reports.py::class_report`. Trang chỉ đọc `class`;
 * khoá ấy là `class`, KHÔNG phải `klass` — chính lỗi 30/08/2026 khiến trang
 * buổi học LUÔN nói "không mở được lớp". Nay lệch tên là một câu lỗi rõ ràng.
 */
export const HD_CHI_TIET_LOP = z.looseObject({
  class: z.looseObject({
    id: so,
    name: z.string(),
    schedule: chu.optional(),
    courseTitle: chu.optional(),
  }).optional(),
});
export type ChiTietLop = z.infer<typeof HD_CHI_TIET_LOP>;

/**
 * Tài khoản đang đăng nhập — `accounts/views.py::UserView.get`. Hai cổng vai
 * (`/admin`, `/quan-tri`) đọc `role` để quyết cho vào hay không; `role` đổi tên
 * là mọi người bị chặn với câu "không đủ quyền" — sai chỗ để đi hỏi. Cột
 * `users.role` là TEXT có thể null, nên vẫn `nullable`; thiếu hẳn khoá mới là lỗi.
 */
export const HD_TOI = z.looseObject({
  role: chu,
  name: chu.optional(),
});
export type Toi = z.infer<typeof HD_TOI>;
