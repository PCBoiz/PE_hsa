'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import { Button, Card, CardHead, Chip, EmptyState, Modal, TableWrap, Td, Th, Tr } from '@/components/ui';
import { apiFetch, errorText } from '@/lib/api';

export type ClassLite = { id: number; name: string; code?: string | null };

export type UserRow = {
  id: number;
  name: string | null;
  email: string | null;
  phone: string | null;
  role: string;
  status: string;
  must_change_password?: boolean;
  password_changed_at?: string | null;
  created_at?: string | null;
  classes?: string[];
};

type Payload = {
  users: UserRow[];
  total: number;
  page: number;
  per_page: number;
  roles: string[];
};

/** Một dòng trong kết quả nhập hàng loạt. */
type BulkRow = {
  line: number;
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  status: 'created' | 'skipped';
  reason?: string | null;
  tempPassword?: string | null;
};

/** Kết quả một mẻ nhập, dùng chung cho cả bản xem trước và bản đã tạo. */
type BulkResultData = {
  created: number;
  skipped: number;
  rows: BulkRow[];
  warnings?: string[];
  tooMany?: boolean;
};

/** Trần một mẻ nhập. Phải khớp `MAX_CREATE_PER_BATCH` trong teaching/admin_users.py —
 *  con số đó tính từ chi phí băm mật khẩu (~126ms CPU mỗi mật khẩu, gunicorn cắt
 *  ở 30 giây), không phải một giới hạn tuỳ tiện. */
const MAX_BATCH = 50;

const STATUS_LABEL: Record<string, string> = {
  active: 'Đang hoạt động',
  suspended: 'Đã khoá',
};

/**
 * Màn hình tài khoản của trung tâm.
 *
 * Đây là hệ quả trực tiếp của chính sách bỏ tự đăng ký (27/08/2026): khi trung
 * tâm là đường DUY NHẤT để có tài khoản, màn hình này thành công cụ dùng hằng
 * ngày chứ không phải trang cấu hình. Ba việc nó phải làm thật nhanh:
 * cấp tài khoản cho cả một danh sách vừa đăng ký, tìm đúng một em trong vài
 * trăm em, và khoá tài khoản em đã nghỉ.
 */
export default function AccountsClient({
  initial,
  classes,
  offline,
}: {
  initial: Payload;
  classes: ClassLite[];
  offline: boolean;
}) {
  const [data, setData] = useState<Payload>(initial);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(
    offline ? 'Không gọi được máy chủ. Thử tải lại trang; nếu vẫn vậy thì báo kỹ thuật.' : null,
  );

  const [q, setQ] = useState('');
  const [role, setRole] = useState('');
  const [status, setStatus] = useState('');
  const [classId, setClassId] = useState('');
  const [page, setPage] = useState(1);

  // Hộp thoại hiện mật khẩu tạm. KHÔNG dùng toast: toast tự biến mất sau vài
  // giây, mà trợ giảng cần thời gian đọc chuỗi này qua điện thoại cho học viên.
  const [temp, setTemp] = useState<{ title: string; password: string; note?: string } | null>(null);

  const query = useCallback(
    (p = page) => {
      const sp = new URLSearchParams({ page: String(p), per_page: String(data.per_page || 25) });
      if (q.trim()) sp.set('q', q.trim());
      if (role) sp.set('role', role);
      if (status) sp.set('status', status);
      if (classId) sp.set('class_id', classId);
      return sp.toString();
    },
    [q, role, status, classId, page, data.per_page],
  );

  const load = useCallback(
    async (p = page) => {
      setLoading(true);
      setErr(null);
      try {
        const r = await apiFetch(`/api/admin/users?${query(p)}`);
        if (!r.ok) throw new Error(errorText(r.status, await r.json().catch(() => null)));
        setData(await r.json());
        setPage(p);
      } catch (e) {
        setErr(e instanceof Error ? e.message : 'Không tải được danh sách');
      } finally {
        setLoading(false);
      }
    },
    [page, query],
  );

  // Gõ tới đâu tìm tới đó, nhưng chờ 350ms sau phím cuối. Gọi mỗi phím một lần
  // là mỗi phím một vòng 245ms tới Neon — máy chủ đuối mà kết quả vẫn nhảy loạn.
  const first = useRef(true);
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    const t = setTimeout(() => void load(1), 350);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, role, status, classId]);

  async function act(path: string, body: unknown, ok: (d: never) => void) {
    setErr(null);
    try {
      const r = await apiFetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      ok(d as never);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Thao tác không thành công');
    }
  }

  function resetPassword(u: UserRow) {
    const who = u.name || u.email || u.phone || `#${u.id}`;
    if (
      !confirm(
        `Đặt lại mật khẩu cho "${who}"?\n\n` +
          'Mật khẩu cũ của học viên ngừng hoạt động ngay lập tức.',
      )
    )
      return;
    void act(`/api/admin/users/${u.id}/reset-password`, undefined, (d: { tempPassword: string }) => {
      setTemp({
        title: `Mật khẩu tạm của ${who}`,
        password: d.tempPassword,
        note: 'Đọc chuỗi này cho học viên. Hệ thống sẽ bắt em đổi ngay lần đăng nhập đầu tiên.',
      });
      void load();
    });
  }

  function toggleStatus(u: UserRow) {
    const locking = u.status === 'active';
    const who = u.name || u.email || `#${u.id}`;
    const note = locking
      ? prompt(`Khoá tài khoản "${who}" vì lý do gì?\n(Ghi lại để sau này còn biết vì sao)`, '')
      : '';
    if (locking && note === null) return; // bấm Huỷ
    void act(
      `/api/admin/users/${u.id}/status`,
      { status: locking ? 'suspended' : 'active', note },
      () => void load(),
    );
  }

  function changeRole(u: UserRow, next: string) {
    setErr(null);
    void (async () => {
      try {
        const r = await apiFetch(`/api/admin/users/${u.id}/role`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role: next }),
        });
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(errorText(r.status, d));
        void load();
      } catch (e) {
        setErr(e instanceof Error ? e.message : 'Không đổi được vai trò');
      }
    })();
  }

  const pages = Math.max(1, Math.ceil(data.total / (data.per_page || 25)));
  const exportHref = `/api/admin/export/users.csv?${query(1)}`;

  return (
    <div className="flex flex-col gap-5">
      <BulkImport classes={classes} roles={data.roles} onDone={() => void load(1)} />

      <Card>
        <CardHead
          title="Tài khoản"
          hint={
            loading
              ? 'Đang tải…'
              : `${data.total} tài khoản khớp bộ lọc hiện tại · trang ${data.page}/${pages}`
          }
          action={
            /* Thẻ neo thường, KHÔNG phải fetch rồi tự dựng file: cookie đăng
               nhập đi kèm sẵn, và trình duyệt lo phần tải xuống — tự dựng thì
               phải giữ cả tệp trong bộ nhớ trước khi lưu. */
            <a
              href={exportHref}
              className="inline-flex min-h-11 items-center rounded-md border border-line px-4 text-small font-semibold text-ink-2 hover:border-brand hover:text-brand-ink"
            >
              Tải Excel (CSV)
            </a>
          }
        />

        <div className="mb-4 grid gap-2 [grid-template-columns:repeat(auto-fit,minmax(min(100%,180px),1fr))]">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Tìm theo tên, email, số điện thoại"
            aria-label="Tìm tài khoản"
            className="min-h-11 min-w-0 rounded-md border border-line bg-sunken px-3 text-input text-ink placeholder:text-ink-3/70 focus:outline-2 focus:outline-brand"
          />
          <Select value={role} onChange={setRole} label="Vai trò">
            <option value="">Mọi vai trò</option>
            {data.roles.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </Select>
          <Select value={status} onChange={setStatus} label="Trạng thái">
            <option value="">Mọi trạng thái</option>
            <option value="active">Đang hoạt động</option>
            <option value="suspended">Đã khoá</option>
          </Select>
          <Select value={classId} onChange={setClassId} label="Lớp">
            <option value="">Mọi lớp</option>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </div>

        {err && (
          <p role="alert" className="mb-3 rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">
            {err}
          </p>
        )}

        {data.users.length === 0 ? (
          <EmptyState
            title="Không có tài khoản nào khớp"
            hint="Thử bỏ bớt bộ lọc, hoặc dán danh sách học viên vừa đăng ký vào ô nhập hàng loạt ở trên."
          />
        ) : (
          <TableWrap>
            <thead>
              <tr>
                <Th>Học viên</Th>
                <Th>Liên hệ</Th>
                <Th>Vai trò</Th>
                <Th>Lớp</Th>
                <Th>Mật khẩu</Th>
                <Th>Trạng thái</Th>
                <Th align="right">Thao tác</Th>
              </tr>
            </thead>
            <tbody>
              {data.users.map((u) => (
                <Tr key={u.id} dim={u.status !== 'active'}>
                  <Td>
                    <span className="font-semibold text-ink">{u.name || '(chưa có tên)'}</span>
                  </Td>
                  <Td muted>
                    <span className="block break-all">{u.email || '—'}</span>
                    <span className="block">{u.phone || ''}</span>
                  </Td>
                  <Td>
                    <select
                      value={u.role}
                      onChange={(e) => changeRole(u, e.target.value)}
                      aria-label={`Vai trò của ${u.name || u.id}`}
                      className="min-h-11 max-w-full min-w-0 rounded-md border border-line bg-sunken px-2 text-small text-ink"
                    >
                      {(data.roles.length ? data.roles : [u.role]).map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </Td>
                  <Td muted>{u.classes?.length ? u.classes.join(', ') : '—'}</Td>
                  <Td>
                    {/* Đọc `must_change_password`, KHÔNG đọc `password_changed_at`.
                        Cột thời gian kia chỉ được ghi ở đúng một chỗ — luồng học
                        viên tự đổi mật khẩu, thêm về sau — nên mọi tài khoản có
                        trước cột đó vĩnh viễn NULL. Đo ngày 30/08/2026: chip cam
                        "Còn mật khẩu tạm" hiện cho CẢ 5/5 tài khoản thật, kể cả
                        tài khoản quản trị đang đăng nhập, trong khi cả 5 đều có
                        `must_change_password = FALSE`.
                        Cột này sinh ra để trả lời "phải gọi nhắc em nào", và nó
                        đang trả lời "gọi tất cả" — đúng loại báo cáo RULES §8 cấm.
                        `must_change_password` mới là cờ thật sự bắt đổi mật khẩu. */}
                    {u.must_change_password ? (
                      <Chip tone="warn">Còn mật khẩu tạm</Chip>
                    ) : u.password_changed_at ? (
                      <Chip tone="good">Đã tự đổi</Chip>
                    ) : (
                      <Chip tone="neutral">—</Chip>
                    )}
                  </Td>
                  <Td>
                    <Chip tone={u.status === 'active' ? 'neutral' : 'bad'}>
                      {STATUS_LABEL[u.status] || u.status}
                    </Chip>
                  </Td>
                  <Td>
                    <span className="flex flex-wrap justify-end gap-2">
                      <Button size="sm" variant="ghost" onClick={() => resetPassword(u)}>
                        Đặt lại mật khẩu
                      </Button>
                      <Button
                        size="sm"
                        variant={u.status === 'active' ? 'danger' : 'ghost'}
                        onClick={() => toggleStatus(u)}
                      >
                        {u.status === 'active' ? 'Khoá' : 'Mở lại'}
                      </Button>
                    </span>
                  </Td>
                </Tr>
              ))}
            </tbody>
          </TableWrap>
        )}

        {pages > 1 && (
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Button size="sm" variant="ghost" disabled={data.page <= 1} onClick={() => void load(data.page - 1)}>
              ← Trang trước
            </Button>
            <span className="text-small text-ink-3">
              Trang {data.page} / {pages}
            </span>
            <Button size="sm" variant="ghost" disabled={data.page >= pages} onClick={() => void load(data.page + 1)}>
              Trang sau →
            </Button>
          </div>
        )}
      </Card>

      <Modal
        open={temp !== null}
        onClose={() => setTemp(null)}
        title={temp?.title || ''}
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => {
                if (temp) void navigator.clipboard?.writeText(temp.password);
              }}
            >
              Chép
            </Button>
            <Button onClick={() => setTemp(null)}>Đã đọc xong</Button>
          </>
        }
      >
        <p className="mb-3 text-body text-ink-2">{temp?.note}</p>
        <p className="rounded-md bg-sunken px-4 py-3 text-center font-mono text-title tracking-wide text-ink select-all">
          {temp?.password}
        </p>
        <p className="mt-3 text-small text-ink-3">
          Chuỗi này chỉ hiện đúng một lần — hệ thống không lưu lại dạng đọc được. Cần xem lại thì
          phải đặt lại mật khẩu lần nữa.
        </p>
      </Modal>
    </div>
  );
}

function Select({
  value,
  onChange,
  label,
  children,
}: {
  value: string;
  onChange: (v: string) => void;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      aria-label={label}
      /* `min-w-0` bắt buộc: ô chọn tự co giãn theo lựa chọn DÀI NHẤT, và trong
         lưới thì nó đẩy cả hàng rộng ra khiến trang trượt ngang trên điện
         thoại — đúng lỗi đã phải vá ở trang /admin ngày 27/08/2026. */
      className="min-h-11 w-full max-w-full min-w-0 rounded-md border border-line bg-sunken px-3 text-input text-ink focus:outline-2 focus:outline-brand"
    >
      {children}
    </select>
  );
}

/**
 * Nhập hàng loạt từ danh sách đăng ký.
 *
 * Lý do tồn tại: học viên đăng ký học ở TopHSA để lại email/số điện thoại, trợ
 * giảng có sẵn một bảng vài chục dòng. Cấp từng tài khoản một cho ba lớp mới
 * khai giảng là công việc cả buổi chiều.
 *
 * Bắt buộc KIỂM TRA TRƯỚC rồi mới cho tạo. Không có bước đó thì một danh sách
 * dán nhầm cột sẽ tạo ra bốn chục tài khoản rác, mà hệ thống không có nút hoàn
 * tác — phải khoá tay từng cái.
 */
function BulkImport({
  classes,
  roles,
  onDone,
}: {
  classes: ClassLite[];
  roles: string[];
  onDone: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState('');
  const [role, setRole] = useState('Học viên');
  const [classId, setClassId] = useState('');
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<BulkResultData | null>(null);
  const [done, setDone] = useState<BulkResultData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  // Số dòng đếm ở máy: chỉ để hiện cho người dùng biết mình vừa dán bao nhiêu.
  // KHÔNG dùng nó để chặn — máy chủ mới biết dòng nào hợp lệ, và trần đếm theo
  // dòng HỢP LỆ chứ không theo dòng đã dán.
  const lines = text.split(/\r?\n/).filter((l) => l.trim()).length;

  async function send(dryRun: boolean) {
    setBusy(true);
    setErr(null);
    try {
      const r = await apiFetch('/api/admin/users/bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, role, class_id: classId || null, dry_run: dryRun }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      if (dryRun) setPreview(d);
      else {
        setDone(d);
        setPreview(null);
        setText('');
        onDone();
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Không gửi được danh sách');
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <Card tone="flat">
        <div className="flex flex-wrap items-center gap-3">
          <div className="min-w-0 flex-1">
            <h2 className="text-section text-ink">Cấp tài khoản hàng loạt</h2>
            <p className="mt-1 text-small text-ink-3">
              Dán thẳng danh sách học viên vừa đăng ký từ Excel hoặc Google Sheets.
            </p>
          </div>
          <Button onClick={() => setOpen(true)}>Mở ô nhập</Button>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <CardHead
        title="Cấp tài khoản hàng loạt"
        hint={`Mỗi dòng một học viên: họ tên, email, số điện thoại. Ngăn cách bằng dấu phẩy hoặc tab (dán từ Excel là ra tab). Cần ít nhất email hoặc số điện thoại. Tối đa ${MAX_BATCH} tài khoản mỗi mẻ.`}
        action={
          <Button variant="ghost" onClick={() => setOpen(false)}>
            Thu gọn
          </Button>
        }
      />

      <textarea
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setPreview(null);
          setDone(null);
        }}
        rows={7}
        aria-label="Danh sách học viên"
        placeholder={'Nguyễn Văn An, an.nguyen@gmail.com, 0912345678\nTrần Thị Bình, binh.tran@gmail.com, 0987654321'}
        className="w-full rounded-md border border-line bg-sunken p-3 font-mono text-small leading-relaxed text-ink placeholder:text-ink-3/70 focus:outline-2 focus:outline-brand"
      />

      {lines > 0 && <p className="mt-2 text-small text-ink-3">{lines} dòng đã dán</p>}

      <div className="mt-3 grid gap-2 [grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr))]">
        <Select value={role} onChange={setRole} label="Vai trò cấp cho cả danh sách">
          {(roles.length ? roles : ['Học viên']).map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </Select>
        <Select value={classId} onChange={setClassId} label="Xếp vào lớp">
          <option value="">Chưa xếp lớp</option>
          {classes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </Select>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {/* Xem trước KHÔNG bao giờ bị chặn: kể cả khi danh sách vượt trần, đó
            vẫn là cách duy nhất để thấy dòng nào hỏng và phải cắt ở đâu. */}
        <Button variant="ghost" loading={busy} disabled={!text.trim()} onClick={() => void send(true)}>
          Kiểm tra trước
        </Button>
        <Button
          loading={busy}
          disabled={!preview || preview.created === 0 || !!preview.tooMany}
          onClick={() => void send(false)}
        >
          {preview ? `Tạo ${preview.created} tài khoản` : 'Tạo tài khoản'}
        </Button>
      </div>

      {/* Cảnh báo của máy chủ — vượt trần, danh sách bị cắt vì quá dài… Đây là
          chỗ DUY NHẤT nói cho trợ giảng biết phải làm gì tiếp, nên không được
          nuốt mất như một chi tiết kỹ thuật. */}
      {preview?.warnings?.map((w) => (
        <p key={w} className="mt-3 rounded-md bg-warning/10 px-3 py-2 text-small text-warning-ink">
          {w}
        </p>
      ))}

      {err && (
        <p role="alert" className="mt-3 rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">
          {err}
        </p>
      )}

      {preview && <BulkResult data={preview} dryRun />}
      {done && <BulkResult data={done} />}
    </Card>
  );
}

function BulkResult({ data, dryRun = false }: { data: BulkResultData; dryRun?: boolean }) {
  const created = data.rows.filter((r) => r.status === 'created');
  return (
    <div className="mt-4">
      <p className="mb-2 text-body text-ink">
        {dryRun
          ? `Sẽ tạo ${data.created} tài khoản, bỏ qua ${data.skipped} dòng.`
          : `Đã tạo ${data.created} tài khoản, bỏ qua ${data.skipped} dòng.`}
      </p>

      {!dryRun && created.length > 0 && (
        <p className="mb-3 rounded-md bg-warning/10 px-3 py-2 text-small text-warning-ink">
          Chép bảng mật khẩu tạm dưới đây ra ngay bây giờ. Hệ thống không lưu lại dạng đọc được —
          rời khỏi trang là mất, và phải đặt lại từng cái một.
        </p>
      )}

      <TableWrap>
        <thead>
          <tr>
            <Th align="right">Dòng</Th>
            <Th>Họ tên</Th>
            <Th>Liên hệ</Th>
            <Th>Kết quả</Th>
            {!dryRun && <Th>Mật khẩu tạm</Th>}
          </tr>
        </thead>
        <tbody>
          {data.rows.map((r) => (
            <Tr key={r.line} dim={r.status === 'skipped'}>
              <Td num>{r.line}</Td>
              <Td>{r.name || '—'}</Td>
              <Td muted>
                <span className="block break-all">{r.email || ''}</span>
                <span className="block">{r.phone || ''}</span>
              </Td>
              <Td>
                {r.status === 'created' ? (
                  <Chip tone="good">{dryRun ? 'Sẽ tạo' : 'Đã tạo'}</Chip>
                ) : (
                  <span className="flex flex-col gap-1">
                    <Chip tone="bad">Bỏ qua</Chip>
                    <span className="text-small text-ink-3">{r.reason}</span>
                  </span>
                )}
              </Td>
              {!dryRun && (
                <Td>
                  {r.tempPassword ? (
                    <code className="font-mono text-small text-ink select-all">{r.tempPassword}</code>
                  ) : (
                    '—'
                  )}
                </Td>
              )}
            </Tr>
          ))}
        </tbody>
      </TableWrap>
    </div>
  );
}
