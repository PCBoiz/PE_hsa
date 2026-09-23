import { serverJson, type HinhDang } from '@/lib/server-api';
import { z } from 'zod';

import { KhongDocDuoc, KhongDuQuyen } from '../ChanVai';
import { layVai } from '../layVai';
import { VAI_HOC_VU, VAI_QUAN_TRI, duocVao } from '../vai';

import { BoLocLop, PhanTrangLop, type LocLop } from './BoLocLop';
import LopHocClient, { type ChonKhoa, type ChonNguoi, type LopRow } from './LopHocClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Lớp học | TopHSA' };

type DsLop = {
  classes: LopRow[]; teachers: ChonNguoi[]; assistants: ChonNguoi[]; statuses: string[];
  /* §54 (24/09/2026): lọc + phân trang ở máy chủ. Tuỳ chọn — backend cũ không trả. */
  total?: number; page?: number; per_page?: number;
  counts?: { byType: Record<string, number>; byStatus: Record<string, number> };
};
type DsDot = { terms: { id: number; name: string; code: string | null }[] };
type DsKhoa = { courses: ChonKhoa[] };

/* Hình dạng ba phản hồi (T18 mức 2). `LopRow` là thứ biểu mẫu SỬA đổ vào —
   thiếu một khoá ở đây là sửa tên lớp xoá trắng link họp (lỗi 04/09), nên khai
   ĐỦ mọi khoá của `LopRow`; tsc bắt qua `satisfies`. */
const chu = z.string().nullable();
const HD_LOP = z.looseObject({
  classes: z.array(z.looseObject({
    id: z.number(), code: chu, name: z.string(), course: chu, courseTitle: chu,
    teacherId: z.number().nullable(), teacherName: chu, schedule: chu, status: z.string(),
    capacity: z.number().nullable(), members: z.number(), startsOn: chu, endsOn: chu,
    examDate: chu, meetingUrl: chu, note: chu, termId: z.number().nullable(),
    mode: chu.optional(), room: chu.optional(),
    classType: chu.optional(),
    studentNames: z.array(z.string()).optional(),
    assistantNames: z.array(z.string()).optional(),
    termName: chu, termCode: chu,
  })),
  total: z.number().optional(), page: z.number().optional(), per_page: z.number().optional(),
  counts: z.looseObject({
    byType: z.record(z.string(), z.number()), byStatus: z.record(z.string(), z.number()),
  }).optional(),
  teachers: z.array(z.looseObject({ id: z.number(), name: chu, email: z.string() })),
  assistants: z.array(z.looseObject({ id: z.number(), name: chu, email: z.string() })),
  statuses: z.array(z.string()),
}) satisfies HinhDang<DsLop>;
const HD_DOT = z.looseObject({
  terms: z.array(z.looseObject({ id: z.number(), name: z.string(), code: chu })),
}) satisfies HinhDang<DsDot>;
const HD_KHOA = z.looseObject({
  courses: z.array(z.looseObject({ id: z.string(), title: z.string() })),
}) satisfies HinhDang<DsKhoa>;

/**
 * Quản lý LỚP HỌC — tạo, sửa, xếp học viên vào lớp.
 *
 * ── VÌ SAO TRANG NÀY CÓ MẶT TRỞ LẠI (04/09/2026) ────────────────────────────
 *
 * Nó từng nằm trong `public/static/js/pages/admin.inline.js`, và tôi XOÁ NHẦM
 * cả tệp ấy khi chuyển khu Soạn giáo trình sang React (0af1c26). Tôi có grep
 * cả repo trước khi xoá — nhưng chỉ grep xem có ai THAM CHIẾU tới tệp không,
 * chứ không hỏi tệp ấy CUNG CẤP chức năng gì. Không ai tham chiếu tới nó là
 * đúng: nó là một trang tự chạy. Tám chỗ gọi biến mất theo, và chỗ này là
 * đường DUY NHẤT để xếp một học viên vào lớp — không có nó thì cả khu Giảng
 * dạy không có gì để hiện.
 *
 * ── DỰNG LẠI, KHÔNG CHÉP LẠI ────────────────────────────────────────────────
 *
 * Bản cũ có một lỗi thật, và chép nguyên là chép cả lỗi: biểu mẫu SỬA chỉ đổ
 * 7 trong 11 trường (thiếu `meeting_url`, `starts_on`, `ends_on`, `note`, và
 * giảng viên), rồi `PUT` gửi cả 11 — nên sửa tên lớp là XOÁ TRẮNG link họp và
 * ghi chú của lớp đó. Đúng lớp lỗi vừa vá ở bộ soạn bài học sáng nay: biểu mẫu
 * DỰNG LẠI từ đầu thay vì ĐÈ LÊN bản đã có.
 *
 * Vì thế `class_list` đã được bổ sung năm cột ấy (`teaching/reports.py`), và
 * biểu mẫu ở đây đổ ĐỦ. Có phép kiểm khẳng định điều đó:
 * `e2e/unit/lop-hoc.test.mjs`.
 *
 * ── BA NGUỒN, BA MỨC QUYỀN KHÁC NHAU ────────────────────────────────────────
 *
 * Danh sách khoá lấy từ `/api/public/courses` chứ KHÔNG từ `/api/admin/courses`:
 * đường admin đòi `IsContentEditor`, mà trang này mở cho `Quản lý học vụ` — họ
 * sẽ nhận 403 và ô chọn khoá hiện rỗng, không báo gì. Chọn nguồn theo QUYỀN của
 * người dùng trang, không theo tên nghe cho oai.
 */
export default async function LopHocPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const mot = (k: string) => {
    const v = sp[k];
    return ((Array.isArray(v) ? v[0] : v) ?? '').trim();
  };
  const loc: LocLop = { q: mot('q'), loai: mot('loai'), tt: mot('tt'), dot: mot('dot'), gv: mot('gv'), trang: mot('trang') };
  // Tên tham số URL (tiếng Việt, ngắn) → tên tham số API.
  const qs = new URLSearchParams({ page: loc.trang || '1', per_page: '25' });
  for (const [ta, api] of [['q', 'q'], ['loai', 'type'], ['tt', 'status'], ['dot', 'term_id'], ['gv', 'teacher_id']] as const) {
    if (loc[ta]) qs.set(api, loc[ta]);
  }

  const kq = await layVai();
  if (!kq.ok) return <KhongDocDuoc loi={kq.loi} />;
  if (!duocVao(kq.vai, [VAI_QUAN_TRI, VAI_HOC_VU])) {
    return <KhongDuQuyen can="quản trị viên và quản lý học vụ" />;
  }

  const [lop, dot, khoa] = await Promise.all([
    serverJson<DsLop>(`/api/admin/classes?${qs}`, { requireAuth: true }, HD_LOP),
    serverJson<DsDot>('/api/admin/terms', { requireAuth: true }, HD_DOT),
    serverJson<DsKhoa>('/api/public/courses', {}, HD_KHOA),
  ]);

  const d = lop.ok ? lop.data : null;
  const dotHoc = dot.ok ? dot.data.terms.map((t) => ({ id: t.id, ten: t.code ? `${t.name} (${t.code})` : t.name })) : [];
  const nguoi = [
    ...(d?.teachers ?? []).map((g) => ({ id: g.id, ten: g.name || g.email })),
    ...(d?.assistants ?? []).map((g) => ({ id: g.id, ten: `${g.name || g.email} (trợ giảng)` })),
  ];
  return (
    <LopHocClient
      initial={d ? d.classes : []}
      dangLoc={Boolean(loc.q || loc.loai || loc.tt || loc.dot || loc.gv)}
      boLoc={
        <BoLocLop loc={loc} dem={d?.counts ?? null} dotHoc={dotHoc} nguoi={nguoi}
          trangThai={d?.statuses ?? ['active', 'finished', 'cancelled']} />
      }
      phanTrang={
        d && typeof d.total === 'number'
          ? <PhanTrangLop loc={loc} tong={d.total} trang={d.page ?? 1} moiTrang={d.per_page ?? 25} />
          : null
      }
      giangVien={lop.ok ? lop.data.teachers : []}
      troGiang={lop.ok ? lop.data.assistants : []}
      trangThai={lop.ok ? lop.data.statuses : ['active', 'finished', 'cancelled']}
      // Đợt và khoá chỉ là ô CHỌN. Không đọc được thì trang vẫn phải dùng được
      // để tạo lớp — nên không cho hỏng cả trang vì một danh sách phụ.
      dotHoc={dot.ok ? dot.data.terms : []}
      khoaHoc={khoa.ok ? khoa.data.courses : []}
      loi={lop.ok ? null : lop.message}
    />
  );
}
