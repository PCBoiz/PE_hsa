'use client';

import Link from 'next/link';
import { useCallback, useState } from 'react';

import { Button, Card, CardHead, Chip, EmptyState } from '@/components/ui';
import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';

/**
 * Hình dạng do `teaching/assignments.py:_dict()` trả về.
 *
 * camelCase ở phản hồi, snake_case ở thân request — đúng quy ước của cả khu
 * `teaching/`, và đúng cái bẫy đã làm chết cả màn hình buổi học ngày
 * 30/08/2026. `serverJson<T>` chỉ ép kiểu chứ không kiểm gì lúc chạy, nên gõ
 * sai một khoá ở đây là `undefined` im lặng, không phải lỗi biên dịch.
 */
export type Assignment = {
  id: number;
  classId: number;
  title: string;
  description: string | null;
  topic: string | null;
  courseId: string | null;
  status: string;
  dueAt: string | null;
  maxScore: number | null;
  attachmentUrl: string | null;
  createdAt: string | null;
  submitted?: number;
  graded?: number;
  ungraded?: number;
  members?: number;
};

const TRANG_THAI: Record<string, { nhan: string; tone: 'neutral' | 'good' | 'warn' }> = {
  draft: { nhan: 'Đang soạn', tone: 'neutral' },
  open: { nhan: 'Đang nhận bài', tone: 'good' },
  closed: { nhan: 'Đã đóng', tone: 'warn' },
};

function fmt(iso: string | null) {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const p = (n: number) => String(n).padStart(2, '0');
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()} · ${p(d.getHours())}:${p(d.getMinutes())}`;
}

/** Hạn nộp đã qua chưa — dùng để đổi tông chữ, KHÔNG dùng để chặn gì. */
function quaHan(iso: string | null) {
  if (!iso) return false;
  const d = new Date(iso);
  return !Number.isNaN(d.getTime()) && d.getTime() < Date.now();
}

export default function AssignmentsClient({
  classId,
  className,
  initial,
  loiTai,
}: {
  classId: number;
  className: string;
  initial: Assignment[];
  /**
   * Lỗi khi máy chủ dựng trang, nếu có.
   *
   * Truyền xuống thay vì để trang cha nuốt bằng `initial={ok ? … : []}`: danh
   * sách rỗng vì lớp chưa có bài, và danh sách rỗng vì không đọc được, trông
   * y hệt nhau trên màn hình — và cái thứ hai thì giảng viên sẽ giao lại bài.
   */
  loiTai?: string | null;
}) {
  const [ds, setDs] = useState<Assignment[]>(initial);
  const [err, setErr] = useState<string | null>(loiTai ?? null);
  const [moForm, setMoForm] = useState(false);

  const reload = useCallback(async () => {
    try {
      const r = await apiFetch(`/api/teach/classes/${classId}/assignments`);
      if (r.ok) setDs((await r.json()).assignments ?? []);
    } catch {
      /* giữ nguyên danh sách đang hiện — mất mạng chốc lát không nên xoá màn hình */
    }
  }, [classId]);

  /**
   * Xoá một bài. HAI bước khi đã có người nộp — giống hệt đường xoá buổi học.
   *
   * Không gửi sẵn `confirm=1`: hàng rào ấy sinh ra để chặn một cú bấm nhầm, gửi
   * kèm sẵn là tự tháo nó ra. Bài chưa ai nộp thì xoá luôn không hỏi.
   */
  async function xoa(a: Assignment) {
    setErr(null);
    try {
      const r = await apiFetch(`/api/teach/assignments/${a.id}`, { method: 'DELETE' });
      const d = await r.json().catch(() => ({}));
      if (r.status === 409 && d.needsConfirm) {
        if (
          !confirm(
            `Bài "${a.title}" đã có ${d.submissions} học viên nộp.\n\n` +
              'Xoá là mất luôn bài làm và điểm của các em, không khôi phục được.\n' +
              'Muốn dừng nhận bài thì bấm Đóng bài thay vì xoá.',
          )
        )
          return;
        const r2 = await apiFetch(`/api/teach/assignments/${a.id}?confirm=1`, {
          method: 'DELETE',
        });
        if (!r2.ok) throw new Error(errorText(r2.status, await r2.json().catch(() => ({}))));
      } else if (!r.ok) {
        throw new Error(errorText(r.status, d));
      }
      await reload();
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không xoá được bài tập'));
    }
  }

  async function doiTrangThai(a: Assignment, status: string) {
    setErr(null);
    try {
      const r = await apiFetch(`/api/teach/assignments/${a.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      await reload();
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không đổi được trạng thái'));
    }
  }

  return (
    <div className="flex flex-col gap-5">
      {err && (
        <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">
          {err}
        </p>
      )}

      {moForm ? (
        <FormBai
          classId={classId}
          onXong={() => {
            setMoForm(false);
            void reload();
          }}
          onHuy={() => setMoForm(false)}
          onLoi={setErr}
        />
      ) : (
        <div>
          <Button onClick={() => setMoForm(true)}>+ Giao bài mới</Button>
        </div>
      )}

      <Card>
        <CardHead
          title={`Bài đã giao (${ds.length})`}
          hint={`Lớp ${className}. Bấm "Chấm bài" để mở bảng chấm cả lớp trên một màn hình.`}
        />

        {ds.length === 0 ? (
          <EmptyState
            title="Lớp chưa có bài tập nào"
            hint="Giao bài đầu tiên ở nút phía trên. Điểm bài tự luận đi thẳng vào bản đồ năng lực của từng em — đó là chỗ duy nhất đo được phần một con người phải đọc mới chấm nổi."
          />
        ) : (
          <ul className="flex flex-col gap-2">
            {ds.map((a) => {
              const tt = TRANG_THAI[a.status] ?? { nhan: a.status, tone: 'neutral' as const };
              const han = fmt(a.dueAt);
              const tre = a.status === 'open' && quaHan(a.dueAt);
              return (
                <li
                  key={a.id}
                  className="rounded-md border border-line bg-surface px-4 py-3"
                >
                  <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                    <span className="text-subhead text-ink">{a.title}</span>
                    <Chip tone={tt.tone}>{tt.nhan}</Chip>
                    {a.topic && <Chip tone="brand">{a.topic}</Chip>}
                  </div>

                  <p className="mt-1 text-small text-ink-3">
                    Thang {a.maxScore ?? '—'} điểm
                    {han && (
                      <>
                        {' · hạn '}
                        <span className={tre ? 'text-warning-ink' : undefined}>
                          {han}
                          {tre && ' (đã qua)'}
                        </span>
                      </>
                    )}
                  </p>

                  {/* Ba con số này là VIỆC, không phải thành tích: còn bao nhiêu
                      bài phải chấm, và bao nhiêu em chưa nộp. Đó là hai câu hỏi
                      giảng viên mở màn hình này để hỏi. */}
                  <p className="mt-1 text-small text-ink-2 tabular-nums">
                    {a.submitted ?? 0}/{a.members ?? 0} đã nộp
                    {(a.ungraded ?? 0) > 0 ? (
                      <span className="text-warning-ink"> · còn {a.ungraded} bài chưa chấm</span>
                    ) : (a.submitted ?? 0) > 0 ? (
                      <span className="text-success-ink"> · đã chấm hết</span>
                    ) : null}
                  </p>

                  <div className="mt-3 flex flex-wrap gap-2">
                    <Link href={`/giang-day/bai-tap/${classId}/${a.id}`}>
                      <Button size="sm">Chấm bài</Button>
                    </Link>
                    {a.status !== 'open' && (
                      <Button size="sm" variant="ghost" onClick={() => void doiTrangThai(a, 'open')}>
                        Mở nhận bài
                      </Button>
                    )}
                    {a.status === 'open' && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => void doiTrangThai(a, 'closed')}
                      >
                        Đóng bài
                      </Button>
                    )}
                    <Button size="sm" variant="danger" onClick={() => void xoa(a)}>
                      Xoá
                    </Button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}

/**
 * Ô giao bài mới.
 *
 * Trạng thái mặc định là "Đang nhận bài" chứ không phải "Đang soạn": việc
 * thường gặp là giao bài ngay, và bắt bấm thêm một bước để phát hành thứ vừa
 * soạn xong là thêm một chỗ để quên. "Đang soạn" vẫn có, cho lúc soạn đề dài.
 */
function FormBai({
  classId,
  onXong,
  onHuy,
  onLoi,
}: {
  classId: number;
  onXong: () => void;
  onHuy: () => void;
  onLoi: (s: string | null) => void;
}) {
  const [dangGui, setDangGui] = useState(false);

  async function gui(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const lay = (k: string) => String(fd.get(k) ?? '').trim();
    onLoi(null);
    setDangGui(true);
    try {
      const r = await apiFetch(`/api/teach/classes/${classId}/assignments`, {
        method: 'POST',
        // snake_case ở THÂN REQUEST — xem `_clean()` trong assignments.py.
        // Trường trống gửi `null` chứ không gửi chuỗi rỗng: cột để trống và
        // cột chứa "" là hai chuyện khác nhau khi đọc lại.
        body: JSON.stringify({
          title: lay('title'),
          topic: lay('topic') || null,
          description: lay('description') || null,
          max_score: lay('max_score') || 10,
          due_at: lay('due_at') || null,
          status: lay('status') || 'open',
        }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      onXong();
    } catch (err) {
      onLoi(loiBatDuoc(err, 'Không giao được bài'));
    } finally {
      setDangGui(false);
    }
  }

  return (
    <Card>
      <CardHead title="Giao bài mới" />
      <form onSubmit={gui} className="flex flex-col gap-3">
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Tiêu đề</span>
          <input
            name="title"
            required
            maxLength={200}
            placeholder="Bài luận: Phân tích đoạn trích"
            className="min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink placeholder:text-ink-3/70"
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Đề bài</span>
          <textarea
            name="description"
            rows={4}
            maxLength={4000}
            placeholder="Dán nguyên đề vào đây. Học viên đọc và gõ bài làm ngay dưới."
            className="w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 py-2 text-input text-ink placeholder:text-ink-3/70"
          />
        </label>

        <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,190px),1fr))]">
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Chủ đề</span>
            <input
              name="topic"
              maxLength={120}
              placeholder="Đọc hiểu"
              className="min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink placeholder:text-ink-3/70"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Thang điểm</span>
            <input
              name="max_score"
              type="number"
              inputMode="decimal"
              min={1}
              step="0.5"
              defaultValue={10}
              className="min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink tabular-nums"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Hạn nộp</span>
            <input name="due_at" type="datetime-local" className="min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink" />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Trạng thái</span>
            <select name="status" defaultValue="open" className="min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink">
              {/* Nhãn NGẮN. Bản đầu ghi cả lời giải thích vào trong <option>, và ở
                  1280px ô này nằm trong lưới bốn cột nên chữ bị cắt giữa chừng:
                  "Đang nhận bài — học viên t✂". Một lựa chọn không đọc hết được thì
                  lời giải thích ấy bằng không có. Giải thích chuyển xuống dòng chú
                  thích ngay dưới, nơi chữ được xuống dòng. */}
              <option value="open">Đang nhận bài</option>
              <option value="draft">Đang soạn</option>
            </select>
          </label>
        </div>

        {/* Chủ đề KHÔNG bắt buộc, nhưng nói rõ cái giá của việc bỏ trống ngay
            tại chỗ điền — nói ở nơi khác thì người điền không đọc. */}
        <p className="text-small text-ink-3">
          <strong className="font-semibold">Đang nhận bài</strong> = học viên thấy và nộp được ngay;{' '}
          <strong className="font-semibold">Đang soạn</strong> = chỉ mình bạn thấy, dùng khi đề còn viết dở.
        </p>
        <p className="text-small text-ink-3">
          Không gắn chủ đề thì điểm vẫn vào sổ, nhưng KHÔNG vào được ô nào trên bản đồ năng lực
          của em.
        </p>

        <div className="flex flex-wrap gap-2">
          <Button type="submit" loading={dangGui}>
            Giao bài
          </Button>
          <Button type="button" variant="ghost" onClick={onHuy}>
            Huỷ
          </Button>
        </div>
      </form>
    </Card>
  );
}
