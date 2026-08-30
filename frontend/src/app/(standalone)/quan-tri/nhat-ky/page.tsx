import Link from 'next/link';

import { Card, CardHead, Chip, EmptyState, TableWrap, Tbody, Td, Th, Thead, Tr } from '@/components/ui';
import { serverJson } from '@/lib/server-api';

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
  'class.create': 'Tạo lớp',
  'class.update': 'Sửa lớp',
  'class.delete': 'Xoá lớp',
  'class.member.add': 'Thêm vào lớp',
  'class.member.remove': 'Cho rời lớp',
  'session.create': 'Tạo buổi học',
  'session.update': 'Sửa buổi học',
  'session.delete': 'Xoá buổi học',
  'attendance.mark': 'Điểm danh',
};

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

  const kq = await serverJson<Payload>(`/api/admin/audit?${qs}`, { requireAuth: true });
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
            ? `${data.total} hành động đã ghi. Chỉ ghi việc SỬA — tạo và khoá tài khoản, đổi vai trò, đặt lại mật khẩu, thêm bớt học viên khỏi lớp, điểm danh.`
            : kq.ok
              ? 'Không đọc được nhật ký. Thử tải lại trang.'
              : kq.message
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
            className="min-h-11 w-full max-w-full min-w-0 rounded-md border border-line bg-sunken px-3 text-input text-ink"
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
            className="min-h-11 w-full min-w-0 rounded-md border border-line bg-sunken px-3 text-input text-ink"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Đến ngày</span>
          <input
            type="date"
            name="to"
            defaultValue={one('to')}
            className="min-h-11 w-full min-w-0 rounded-md border border-line bg-sunken px-3 text-input text-ink"
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
          hint="Nhật ký bắt đầu ghi từ 30/08/2026. Mọi việc trước mốc đó không có ở đây — đó chính là lý do đặc tả khuyên làm phần này sớm."
        />
      ) : (
        <TableWrap>
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
                  <span className="block text-ink-3">{e.actor_role || ''}</span>
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
        <div className="mt-4 flex flex-wrap items-center gap-3 text-small">
          {page > 1 && (
            <Link href={pageHref(page - 1)} className="text-brand-ink underline">
              ← Trang trước
            </Link>
          )}
          <span className="text-ink-3">
            Trang {page} / {pages}
          </span>
          {page < pages && (
            <Link href={pageHref(page + 1)} className="text-brand-ink underline">
              Trang sau →
            </Link>
          )}
        </div>
      )}
    </Card>
  );
}
