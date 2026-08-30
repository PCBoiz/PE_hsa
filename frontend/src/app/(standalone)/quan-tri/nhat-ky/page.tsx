import Link from 'next/link';

import { Card, CardHead, Chip, EmptyState, TableWrap, Td, Th, Tr } from '@/components/ui';
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

  const data = await serverJson<Payload>(`/api/admin/audit?${qs}`, { requireAuth: true });
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
            : 'Không đọc được nhật ký. Thử tải lại trang.'
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
            {(data?.actions ?? []).map((a) => (
              <option key={a} value={a}>
                {a}
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

      {entries.length === 0 ? (
        <EmptyState
          title="Chưa có hành động nào được ghi"
          hint="Nhật ký bắt đầu ghi từ 30/08/2026. Mọi việc trước mốc đó không có ở đây — đó chính là lý do đặc tả khuyên làm phần này sớm."
        />
      ) : (
        <TableWrap>
          <thead>
            <tr>
              <Th>Lúc</Th>
              <Th>Người làm</Th>
              <Th>Việc</Th>
              <Th>Nội dung</Th>
              <Th>IP</Th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <Tr key={e.id}>
                <Td num>{when(e.occurred_at)}</Td>
                <Td>
                  <span className="block font-semibold text-ink">{e.actor_name || '(đã xoá)'}</span>
                  <span className="block text-ink-3">{e.actor_role || ''}</span>
                </Td>
                <Td>
                  <Chip tone={tone(e.action)}>{e.action}</Chip>
                </Td>
                <Td>{e.summary || `${e.target_type || ''} ${e.target_label || ''}`.trim() || '—'}</Td>
                <Td muted>{e.ip || '—'}</Td>
              </Tr>
            ))}
          </tbody>
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
