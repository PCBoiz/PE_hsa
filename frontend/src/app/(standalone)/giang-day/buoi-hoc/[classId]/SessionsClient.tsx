'use client';

import { useCallback, useEffect, useState } from 'react';

import { Button, Card, CardHead, Chip, EmptyState, Tile, TileRow } from '@/components/ui';
import { apiFetch } from '@/lib/api';

export type SessionRow = {
  id: number;
  starts_at: string;
  duration_minutes: number | null;
  topic: string | null;
  status: string;
  note: string | null;
  meeting_url?: string | null;
  counts?: { present: number; late: number; absent: number; excused: number; unmarked: number };
};

type Mark = 'present' | 'late' | 'absent' | 'excused';

type Student = {
  user_id: number;
  name: string | null;
  email: string | null;
  status: Mark | null;
  note?: string | null;
  absences?: number;
};

/** Bốn trạng thái điểm danh — nhãn tiếng Việt và tông màu dùng chung một chỗ. */
const MARKS: { key: Mark; label: string; tone: 'good' | 'warn' | 'bad' | 'brand' }[] = [
  { key: 'present', label: 'Có mặt', tone: 'good' },
  { key: 'late', label: 'Muộn', tone: 'warn' },
  { key: 'absent', label: 'Vắng', tone: 'bad' },
  { key: 'excused', label: 'Có phép', tone: 'brand' },
];

function fmt(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const p = (n: number) => String(n).padStart(2, '0');
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()} · ${p(d.getHours())}:${p(d.getMinutes())}`;
}

/** `datetime-local` cần đúng dạng YYYY-MM-DDTHH:mm theo giờ MÁY, không phải UTC. */
function localInputValue(d: Date) {
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

export default function SessionsClient({
  classId,
  className,
  initial,
}: {
  classId: number;
  className: string;
  initial: SessionRow[];
}) {
  const [sessions, setSessions] = useState<SessionRow[]>(initial);
  const [openId, setOpenId] = useState<number | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const r = await apiFetch(`/api/teach/classes/${classId}/sessions`);
      if (r.ok) setSessions((await r.json()).sessions ?? []);
    } catch {
      /* giữ nguyên danh sách đang hiện — mất mạng chốc lát không nên xoá màn hình */
    }
  }, [classId]);

  return (
    <div className="flex flex-col gap-5">
      <NewSession classId={classId} onDone={() => void reload()} onError={setErr} />

      {err && (
        <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">
          {err}
        </p>
      )}

      <Card>
        <CardHead
          title="Các buổi đã lên lịch"
          hint={`${sessions.length} buổi của lớp ${className}. Bấm một buổi để điểm danh.`}
        />

        {sessions.length === 0 ? (
          <EmptyState
            title="Lớp chưa có buổi học nào"
            hint="Tạo buổi đầu tiên ở ô phía trên. Có buổi thì mới điểm danh được, và số buổi đi học mới vào được đường cong tiến bộ của từng em."
          />
        ) : (
          <ul className="flex flex-col gap-2">
            {sessions.map((s) => {
              const c = s.counts;
              return (
                <li key={s.id}>
                  <Card tone="sunken" padding="sm">
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-subhead text-ink">{s.topic || 'Buổi học'}</p>
                        <p className="mt-0.5 text-small text-ink-3">
                          {fmt(s.starts_at)}
                          {s.duration_minutes ? ` · ${s.duration_minutes} phút` : ''}
                        </p>
                      </div>

                      {/* Số CHƯA điểm danh là con số giảng viên cần nhất: nó trả
                          lời "buổi hôm qua tôi tick xong chưa". Chỉ tô cảnh báo
                          khi lớn hơn 0 — bảng lúc nào cũng đỏ thì mắt bỏ qua. */}
                      {c && (
                        <span className="flex flex-wrap gap-1.5">
                          {c.present > 0 && <Chip tone="good">{c.present} có mặt</Chip>}
                          {c.late > 0 && <Chip tone="warn">{c.late} muộn</Chip>}
                          {c.absent > 0 && <Chip tone="bad">{c.absent} vắng</Chip>}
                          {c.unmarked > 0 && <Chip tone="warn">{c.unmarked} chưa điểm danh</Chip>}
                        </span>
                      )}

                      <Button
                        size="sm"
                        variant={openId === s.id ? 'ghost' : 'primary'}
                        onClick={() => setOpenId(openId === s.id ? null : s.id)}
                      >
                        {openId === s.id ? 'Đóng' : 'Điểm danh'}
                      </Button>
                    </div>

                    {openId === s.id && (
                      <Attendance sessionId={s.id} onSaved={() => void reload()} onError={setErr} />
                    )}
                  </Card>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}

/** Tạo buổi mới. Gấp lại khi chưa dùng để không che mất danh sách buổi. */
function NewSession({
  classId,
  onDone,
  onError,
}: {
  classId: number;
  onDone: () => void;
  onError: (m: string | null) => void;
}) {
  const [open, setOpen] = useState(false);
  const [startsAt, setStartsAt] = useState('');
  const [topic, setTopic] = useState('');
  const [minutes, setMinutes] = useState('90');
  const [busy, setBusy] = useState(false);

  // Gợi ý sẵn 19:30 hôm nay: lớp online của trung tâm học buổi tối, và ô giờ
  // trống bắt giảng viên gõ đủ ngày-tháng-năm-giờ-phút mỗi lần tạo buổi.
  useEffect(() => {
    if (!open || startsAt) return;
    const d = new Date();
    d.setHours(19, 30, 0, 0);
    setStartsAt(localInputValue(d));
  }, [open, startsAt]);

  if (!open) {
    return (
      <Card tone="flat">
        <div className="flex flex-wrap items-center gap-3">
          <p className="min-w-0 flex-1 text-body text-ink-2">
            Thêm một buổi vào lịch lớp để điểm danh.
          </p>
          <Button onClick={() => setOpen(true)}>Tạo buổi học</Button>
        </div>
      </Card>
    );
  }

  async function save() {
    setBusy(true);
    onError(null);
    try {
      const r = await apiFetch(`/api/teach/classes/${classId}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          starts_at: startsAt,
          topic: topic.trim() || null,
          duration_minutes: Number(minutes) || null,
        }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.error || 'Không tạo được buổi học');
      if (d.warning) onError(d.warning);
      setTopic('');
      setOpen(false);
      onDone();
    } catch (e) {
      onError(e instanceof Error ? e.message : 'Không tạo được buổi học');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHead
        title="Buổi học mới"
        action={
          <Button variant="ghost" onClick={() => setOpen(false)}>
            Thu gọn
          </Button>
        }
      />
      <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,190px),1fr))]">
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Bắt đầu lúc</span>
          <input
            type="datetime-local"
            value={startsAt}
            onChange={(e) => setStartsAt(e.target.value)}
            className="min-h-11 w-full min-w-0 rounded-md border border-line bg-sunken px-3 text-input text-ink"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Chủ đề buổi</span>
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Tỉ lệ & phần trăm"
            className="min-h-11 w-full min-w-0 rounded-md border border-line bg-sunken px-3 text-input text-ink placeholder:text-ink-3/70"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Thời lượng (phút)</span>
          <input
            type="number"
            inputMode="numeric"
            min={15}
            value={minutes}
            onChange={(e) => setMinutes(e.target.value)}
            className="min-h-11 w-full min-w-0 rounded-md border border-line bg-sunken px-3 text-input text-ink"
          />
        </label>
      </div>
      <div className="mt-3">
        <Button loading={busy} disabled={!startsAt} onClick={() => void save()}>
          Tạo buổi
        </Button>
      </div>
    </Card>
  );
}

/**
 * Bảng tick điểm danh.
 *
 * Hiện TOÀN BỘ học viên đang trong lớp, kể cả em chưa có dòng điểm danh nào —
 * chứ không chỉ những em đã tick. Giảng viên mở ra phải thấy ngay cả lớp để
 * tick, không phải tự đối chiếu hai danh sách trong đầu.
 *
 * Nút bấm chứ không phải ô chọn: bốn trạng thái, và trên điện thoại thì bốn nút
 * to bấm nhanh hơn hẳn một ô chọn phải mở ra rồi cuộn. Giảng viên điểm danh
 * trong lúc đang dạy, mỗi giây đều tính.
 */
function Attendance({
  sessionId,
  onSaved,
  onError,
}: {
  sessionId: number;
  onSaved: () => void;
  onError: (m: string | null) => void;
}) {
  const [rows, setRows] = useState<Student[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    let alive = true;
    void (async () => {
      try {
        const r = await apiFetch(`/api/teach/sessions/${sessionId}/attendance`);
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.error || 'Không tải được danh sách lớp');
        if (alive) setRows(d.students ?? []);
      } catch (e) {
        onError(e instanceof Error ? e.message : 'Không tải được danh sách lớp');
        if (alive) setRows([]);
      }
    })();
    return () => {
      alive = false;
    };
  }, [sessionId, onError]);

  function set(userId: number, mark: Mark) {
    setRows((prev) => prev?.map((s) => (s.user_id === userId ? { ...s, status: mark } : s)) ?? prev);
    setDirty(true);
  }

  /** Tick cả lớp có mặt rồi sửa lại vài em vắng — nhanh hơn tick từng em. */
  function allPresent() {
    setRows((prev) => prev?.map((s) => ({ ...s, status: s.status ?? 'present' })) ?? prev);
    setDirty(true);
  }

  async function save() {
    if (!rows) return;
    setBusy(true);
    onError(null);
    try {
      const marks = rows
        .filter((s) => s.status)
        .map((s) => ({ user_id: s.user_id, status: s.status }));
      const r = await apiFetch(`/api/teach/sessions/${sessionId}/attendance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ marks }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.error || 'Không lưu được điểm danh');
      setDirty(false);
      onSaved();
    } catch (e) {
      onError(e instanceof Error ? e.message : 'Không lưu được điểm danh');
    } finally {
      setBusy(false);
    }
  }

  if (rows === null) {
    return <p className="mt-3 text-small text-ink-3">Đang tải danh sách lớp…</p>;
  }
  if (rows.length === 0) {
    return (
      <div className="mt-3">
        <EmptyState
          title="Lớp chưa có học viên"
          hint="Thêm học viên vào lớp ở trang Quản trị trước, rồi quay lại đây điểm danh."
        />
      </div>
    );
  }

  const done = rows.filter((s) => s.status).length;

  return (
    <div className="mt-4 border-t border-line pt-4">
      <TileRow>
        <Tile value={rows.length} label="Sĩ số" />
        <Tile value={done} label="Đã tick" tone={done === rows.length ? 'good' : 'neutral'} />
        <Tile
          value={rows.length - done}
          label="Chưa tick"
          tone={rows.length - done > 0 ? 'warn' : 'neutral'}
        />
      </TileRow>

      <ul className="mt-4 flex flex-col gap-2">
        {rows.map((s) => (
          <li
            key={s.user_id}
            className="flex flex-wrap items-center gap-x-3 gap-y-2 rounded-md bg-surface px-3 py-2"
          >
            <span className="min-w-0 flex-1">
              <span className="block truncate text-body font-semibold text-ink">
                {s.name || s.email || `#${s.user_id}`}
              </span>
              {typeof s.absences === 'number' && s.absences > 0 && (
                <span className="block text-small text-warning-ink">
                  đã nghỉ {s.absences} buổi
                </span>
              )}
            </span>
            <span className="flex flex-wrap gap-1">
              {MARKS.map((m) => {
                const on = s.status === m.key;
                return (
                  <button
                    key={m.key}
                    type="button"
                    aria-pressed={on}
                    onClick={() => set(s.user_id, m.key)}
                    className={[
                      'min-h-11 rounded-md px-3 text-small font-semibold',
                      'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand',
                      on
                        ? 'bg-brand-fill text-white'
                        : 'border border-line text-ink-2 hover:border-brand hover:text-brand-ink',
                    ].join(' ')}
                  >
                    {m.label}
                  </button>
                );
              })}
            </span>
          </li>
        ))}
      </ul>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Button loading={busy} disabled={!dirty} onClick={() => void save()}>
          Lưu điểm danh
        </Button>
        <Button variant="ghost" onClick={allPresent}>
          Đánh dấu cả lớp có mặt
        </Button>
        {dirty && <span className="text-small text-warning-ink">Chưa lưu</span>}
      </div>
    </div>
  );
}
