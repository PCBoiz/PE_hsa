import Link from 'next/link';

import { Card, CardHead, Chip, EmptyState, TableWrap, Tbody, Td, Th, Thead, Tr } from '@/components/ui';
import { serverJson, type HinhDang } from '@/lib/server-api';
import { z } from 'zod';

export const metadata = { title: 'Nhật ký kiểm toán | TopHSA' };
export const dynamic = 'force-dynamic';

type Entry = {
  id: number;
  actor_name: string | null;
  actor_role: string | null;
  action: string;
  target_type: string | null;
  target_label: string | null;
  summary: string | null;
  ip: string | null;
  occurred_at: string;
};

type Payload = { entries: Entry[]; total: number; page: number; per_page: number; actions: string[] };
/* Hình dạng `/api/admin/audit` (`teaching/admin_users.py::AdminAuditView`) — T18 mức 2. */
const HINH_DANG = z.looseObject({
  entries: z.array(z.looseObject({
    id: z.number(),
    actor_name: z.string().nullable(),
    actor_role: z.string().nullable(),
    action: z.string(),
    target_type: z.string().nullable(),
    target_label: z.string().nullable(),
    summary: z.string().nullable(),
    ip: z.string().nullable(),
    occurred_at: z.string(),
  })),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
  actions: z.array(z.string()),
}) satisfies HinhDang<Payload>;

/** Nhóm hành động → tông màu. Việc chạm tới mật khẩu hay quyền phải nổi lên. */
/**
 * Tên việc, bằng tiếng Việt.
 *
 * Cột `admin_audit.action` lưu mã máy (`attendance.mark`, `user.password_reset`)
 * — đúng cho CSDL, nhưng nhật ký này là thứ trợ giảng và quản lý trung tâm đọc
 * khi có chuyện xảy ra. Hiện mã trần lên màn hình là bắt người đọc tự dịch đúng
 * lúc họ đang cần đọc nhanh nhất (RULES §10).
 *
 * Khoá ở đây phải khớp hằng số trong `backend/common/audit.py`. Mã lạ thì hiện
 * nguyên mã chứ KHÔNG giấu đi: một dòng nhật ký không đọc được vẫn hơn một dòng
 * nhật ký biến mất.
 */
const VIEC: Record<string, string> = {
  'user.create': 'Cấp tài khoản',
  'user.role': 'Đổi vai trò',
  'user.status': 'Khoá / mở tài khoản',
  'user.password_reset': 'Đặt lại mật khẩu',
  // 23/09/2026 (§51): học vụ sửa hồ sơ, giảng viên sửa mục tiêu/nguyện vọng.
  // Cột "Nội dung" nêu các ô đã đổi; giá trị cũ nằm trong `detail.cu`.
  'user.profile': 'Sửa hồ sơ học viên',
  // §52: chủ tài khoản tự đặt lại qua đường dẫn trong email (người làm = người bị đổi).
  'user.password_self_reset': 'Tự đặt lại mật khẩu qua email',
  'class.create': 'Tạo lớp',
  'class.update': 'Sửa lớp',
  'class.delete': 'Xoá lớp',
  'class.member.add': 'Thêm vào lớp',
  'class.member.remove': 'Cho rời lớp',
  'class.member.transfer': 'Chuyển lớp',
  'class.parent_contacts': 'Nhập liên hệ phụ huynh',
  'session.create': 'Tạo buổi học',
  'session.update': 'Sửa buổi học',
  'session.delete': 'Xoá buổi học',
  'session.generate': 'Sinh buổi học hàng loạt',
  'attendance.mark': 'Điểm danh',
  // Báo cáo phụ huynh (14/09/2026): đường công khai tới tờ báo cáo một em là
  // dữ liệu của một đứa trẻ đi ra ngoài cửa — phải thấy ở đây, không phải ở SQL.
  'parent_link.create': 'Phát hành link báo cáo phụ huynh',
  'parent_link.revoke': 'Thu hồi link báo cáo phụ huynh',
  'parent_report.send_all': 'Gửi báo cáo cả lớp',
  // 16/09/2026: điểm kỳ thi thử đọc từ PDF đi thẳng vào tờ gửi về nhà.
  'exam.external_import': 'Nhập kết quả thi thử từ PDF',
  // Nhóm `term.*` thêm 31/08/2026 cùng tính năng đợt học. Đây đúng là cách
  // bảng nhãn này trôi khỏi backend: thêm hành động mới ở `common/audit.py` mà
  // quên chỗ này, và mã máy lại lọt ra màn hình — đúng thứ chú thích trên vừa
  // nói là không được để xảy ra.
  'term.create': 'Tạo đợt học',
  'term.update': 'Sửa đợt học',
  'term.delete': 'Xoá đợt học',
  'term.holiday.add': 'Khai ngày nghỉ của đợt',
  'term.holiday.delete': 'Xoá ngày nghỉ của đợt',
  // Bốn nhóm dưới đây thêm ở backend từ 31/08 tới 04/09 và lọt ra màn hình
  // dưới dạng mã máy suốt hai tuần — dù chú thích ngay trên đã dặn. Lời dặn
  // nằm ở tệp mà người thêm hằng số không mở; nay `e2e/unit/nhan-nhat-ky`
  // đọc cả hai tệp và đỏ ở CI của chính người ấy.
  'assignment.create': 'Giao bài',
  'assignment.update': 'Sửa bài đã giao',
  'assignment.delete': 'Xoá bài đã giao',
  'assignment.grade': 'Chấm bài',
  'course.create': 'Tạo khoá học',
  'course.update': 'Sửa khoá học',
  'course.delete': 'Xoá khoá học',
  'course.import': 'Nhập giáo trình',
  'lesson.create': 'Thêm bài học',
  'lesson.update': 'Sửa thông tin bài',
  'lesson.delete': 'Xoá bài học',
  'lesson.content': 'Sửa nội dung bài',
  'mock_exam.create': 'Tạo đề thi thử',
  'mock_exam.update': 'Sửa đề thi thử',
  // Một mã cho cả hai chiều (xem `mockexam/quan_tri.py`) — cột "Nội dung" nói
  // rõ là xuất bản hay ẩn.
  'mock_exam.publish': 'Xuất bản / ẩn đề thi thử',
  // Khung chương trình theo buổi + sổ đầu bài (25/09/2026).
  'syllabus.create': 'Tạo khung chương trình',
  'syllabus.update': 'Sửa khung chương trình',
  'syllabus.delete': 'Xoá khung chương trình',
  'syllabus.version.create': 'Tạo bản mới của khung',
  'syllabus.version.edit': 'Sửa bản nháp của khung',
  'syllabus.version.publish': 'Xuất bản khung chương trình',
  'syllabus.version.delete': 'Xoá một bản của khung',
  'class.syllabus': 'Lớp nhận khung chương trình',
  'session.syllabus': 'Gắn buổi học với buổi khung',
  'session.log': 'Ghi sổ đầu bài',
};

/**
 * Nhãn vai trò. Cột `users.role` chứa lẫn hai thứ tiếng (`admin` cạnh
 * `Giảng viên`/`Học viên`), nên nhật ký hiện "Giảng viên" cho người này và
 * `admin` cho người kia — trong cùng một cột.
 */
const VAI: Record<string, string> = { admin: 'Quản trị viên' };

function tone(action: string): 'neutral' | 'brand' | 'warn' | 'bad' {
  if (action.startsWith('user.password') || action === 'user.status') return 'bad';
  if (action === 'user.role') return 'warn';
  if (action.startsWith('attendance')) return 'brand';
  return 'neutral';
}

function when(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const p = (n: number) => String(n).padStart(2, '0');
  return `${p(d.getDate())}/${p(d.getMonth() + 1)} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

/**
 * Nhật ký kiểm toán — ai đã sửa gì, lúc nào.
 *
 * Đặc tả ERP §9 xếp việc này thứ 5 nhưng ghi rõ nên chen lên sớm: rẻ khi làm
 * trước, đắt khi làm sau — vì làm muộn thì mọi hành động đã xảy ra trước đó
 * mất trắng, không dựng lại được từ đâu.
 *
 * Không có JavaScript nào ở trang này. Bộ lọc là một biểu mẫu GET thường, và
 * nhờ vậy mỗi bộ lọc có URL riêng — quản lý học vụ gửi được đường dẫn "mọi lần
 * đặt lại mật khẩu tháng này" cho người khác, thay vì bảo họ tự bấm lại.
 */
export default async function NhatKyPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const one = (k: string) => (Array.isArray(sp[k]) ? sp[k][0] : sp[k]) || '';

  const qs = new URLSearchParams({ page: one('page') || '1', per_page: '50' });
  for (const k of ['action', 'from', 'to']) if (one(k)) qs.set(k, one(k));

  const kq = await serverJson<Payload>(`/api/admin/audit?${qs}`, { requireAuth: true }, HINH_DANG);
  const data = kq.ok ? kq.data : null;
  const entries = data?.entries ?? [];
  const pages = Math.max(1, Math.ceil((data?.total ?? 0) / (data?.per_page || 50)));
  const page = data?.page ?? 1;

  const pageHref = (p: number) => {
    const n = new URLSearchParams(qs);
    n.set('page', String(p));
    return `/quan-tri/nhat-ky?${n}`;
  };

  return (
    <Card>
      <CardHead
        title="Nhật ký kiểm toán"
        hint={
          data
            ? `${data.total} hành động sửa dữ liệu đã ghi.`
            : kq.ok
              ? 'Không đọc được nhật ký. Thử tải lại trang.'
              : kq.message
        }
        chiTiet={
          data
            ? 'Chỉ ghi việc SỬA: tạo và khoá tài khoản, đổi vai trò, đặt lại mật khẩu, thêm bớt học viên khỏi lớp, điểm danh. Việc chỉ xem không được ghi.'
            : undefined
        }
      />

      <form
        method="get"
        className="mb-4 grid items-end gap-2 [grid-template-columns:repeat(auto-fit,minmax(min(100%,170px),1fr))]"
      >
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Hành động</span>
          <select
            name="action"
            defaultValue={one('action')}
            className="min-h-11 w-full max-w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink"
          >
            <option value="">Mọi hành động</option>
            {/* Ô LỌC cũng phải dịch, không chỉ chip trong bảng. Chip đọc được
                tiếng Việt mà ô lọc bên trên vẫn liệt kê `attendance.mark` thì
                người dùng không nối được hai thứ đó với nhau — và ô lọc mới là
                chỗ họ chạm vào trước. */}
            {(data?.actions ?? []).map((a) => (
              <option key={a} value={a}>
                {VIEC[a] || a}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Từ ngày</span>
          <input
            type="date"
            name="from"
            defaultValue={one('from')}
            className="min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Đến ngày</span>
          <input
            type="date"
            name="to"
            defaultValue={one('to')}
            className="min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink"
          />
        </label>
        <button
          type="submit"
          className="min-h-11 rounded-md bg-brand-fill px-4 text-body font-semibold text-white hover:brightness-110"
        >
          Lọc
        </button>
      </form>

      {!kq.ok ? (
        /* Lời gọi HỎNG khác hẳn "không có dòng nào". Bản trước gộp cả hai vào
           một nhánh, nên `?from=abc` hiện đồng thời "Không đọc được nhật ký" ở
           tiêu đề và "Chưa có hành động nào được ghi" ở thân — hai câu mâu
           thuẫn, mà không câu nào nói ngày gõ sai ở đâu.

           "Xoá bộ lọc" là ĐƯỜNG THOÁT. Khi lời gọi hỏng thì ô chọn Hành động
           cũng rỗng theo (danh sách đó do chính phản hồi này cấp), nên không
           còn nút nào bấm được — người dùng phải tự sửa URL. */
        <div className="rounded-md border border-danger/30 bg-danger/5 px-4 py-6" role="alert">
          <p className="text-subhead text-ink">Không đọc được nhật ký</p>
          <p className="mt-1 text-body text-ink-2">{kq.message}</p>
          <Link
            href="/quan-tri/nhat-ky"
            className="mt-4 inline-block text-body text-brand-ink underline"
          >
            Xoá bộ lọc và xem lại từ đầu
          </Link>
        </div>
      ) : entries.length === 0 ? (
        <EmptyState
          title="Chưa có hành động nào được ghi"
          // Nhật ký ghi từ 30/08/2026 — ngày ấy từng in ở đây; gỡ 24/09/2026
          // (ngày gõ cứng + "đặc tả khuyên" là ghi chú lập trình viên).
          hint="Việc sửa dữ liệu (tạo tài khoản, xếp lớp, điểm danh…) sẽ hiện ở đây."
        />
      ) : (
        <TableWrap caption="Nhật ký các hành động sửa dữ liệu, mới nhất trước">
          <Thead>
            <tr>
              <Th>Lúc</Th>
              <Th>Người làm</Th>
              <Th>Việc</Th>
              <Th>Nội dung</Th>
              <Th>IP</Th>
            </tr>
          </Thead>
          <Tbody>
            {entries.map((e) => (
              <Tr key={e.id}>
                <Td label="Lúc" num>
                  {when(e.occurred_at)}
                </Td>
                <Td label="Người làm">
                  <span className="block font-semibold text-ink">{e.actor_name || '(đã xoá)'}</span>
                  <span className="block text-ink-3">{VAI[e.actor_role || ''] || e.actor_role || ''}</span>
                </Td>
                <Td label="Việc">
                  <Chip tone={tone(e.action)}>{VIEC[e.action] || e.action}</Chip>
                </Td>
                <Td label="Nội dung">
                  {e.summary || `${e.target_type || ''} ${e.target_label || ''}`.trim() || '—'}
                </Td>
                <Td label="IP" muted>
                  {e.ip || '—'}
                </Td>
              </Tr>
            ))}
          </Tbody>
        </TableWrap>
      )}

      {pages > 1 && (
        /* `min-h-11` (44px) cho hai lối chuyển trang: chữ chỉ cao 20px, mà đây
           là đích duy nhất để đi tiếp trong một bảng dài. Bộ đo giao diện bắt
           được nó ngày 14/09 — trước đó nhật ký chưa bao giờ quá MỘT trang nên
           khối này không hiện, và không thước nào chạm tới. */
        <div className="mt-4 flex flex-wrap items-center gap-3 text-small">
          {page > 1 && (
            <Link href={pageHref(page - 1)} className="inline-flex min-h-11 items-center text-brand-ink underline">
              ← Trang trước
            </Link>
          )}
          <span className="text-ink-3">
            Trang {page} / {pages}
          </span>
          {page < pages && (
            <Link href={pageHref(page + 1)} className="inline-flex min-h-11 items-center text-brand-ink underline">
              Trang sau →
            </Link>
          )}
        </div>
      )}
    </Card>
  );
}
