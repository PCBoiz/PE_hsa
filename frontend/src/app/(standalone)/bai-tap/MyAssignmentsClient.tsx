'use client';

import { useState } from 'react';

import { Button, Card, CardHead, Chip, EmptyState, ToastProvider, useToast } from '@/components/ui';
import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';

export type BaiCuaToi = {
  id: number;
  title: string;
  description: string | null;
  topic: string | null;
  className: string;
  status: string;
  dueAt: string | null;
  maxScore: number | null;
  submittedAt: string | null;
  content: string | null;
  score: number | null;
  scorePct: number | null;
  feedback: string | null;
  gradedAt: string | null;
};

function fmt(iso: string | null) {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const p = (n: number) => String(n).padStart(2, '0');
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()} · ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function quaHan(iso: string | null) {
  if (!iso) return false;
  const d = new Date(iso);
  return !Number.isNaN(d.getTime()) && d.getTime() < Date.now();
}

/**
 * Bài tập của học viên — nửa còn lại của ERP §5.
 *
 * Không có màn hình này thì tính năng chấm bài chỉ chạy được một chiều: giảng
 * viên giao được, chấm được, nhưng em không có đường nào nộp. Cùng lỗi với
 * `/giang-day/*` hồi 30/08 — mã đầy đủ, không lối vào, bằng không có tính năng.
 */
export default function MyAssignmentsClient({
  initial,
  loiTai,
}: {
  initial: BaiCuaToi[];
  loiTai?: string | null;
}) {
  return (
    <ToastProvider>
      <DanhSach initial={initial} loiTai={loiTai} />
    </ToastProvider>
  );
}

function DanhSach({ initial, loiTai }: { initial: BaiCuaToi[]; loiTai?: string | null }) {
  const [ds, setDs] = useState<BaiCuaToi[]>(initial);
  const [err, setErr] = useState<string | null>(loiTai ?? null);
  const [mo, setMo] = useState<number | null>(null);
  const [nhap, setNhap] = useState<Record<number, string>>({});
  const [dangGui, setDangGui] = useState<number | null>(null);
  const toast = useToast();

  const chuaNop = ds.filter((a) => a.status === 'open' && !a.submittedAt).length;

  async function nop(a: BaiCuaToi) {
    const noi_dung = (nhap[a.id] ?? '').trim();
    if (!noi_dung) {
      setErr('Bài nộp không được để trống.');
      return;
    }
    // Nộp lại XOÁ điểm đã chấm — backend làm vậy có chủ đích (một điểm chấm cho
    // bản cũ mà treo trên bản mới là con số nói dối). Phải hỏi TRƯỚC, vì em
    // không có cách nào đoán ra điều đó từ nút "Nộp bài".
    if (a.gradedAt && !confirm(
      `Bài này đã được chấm ${a.score}/${a.maxScore}.\n\n` +
        'Nộp lại sẽ XOÁ điểm đó và giảng viên phải chấm lại từ đầu. Vẫn nộp?',
    )) return;

    setErr(null);
    setDangGui(a.id);
    try {
      const r = await apiFetch('/api/assignments', {
        method: 'POST',
        body: JSON.stringify({ assignment_id: a.id, content: noi_dung }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));

      const r2 = await apiFetch('/api/assignments');
      if (r2.ok) setDs((await r2.json()).assignments ?? []);
      setNhap((cu) => {
        const kt = { ...cu };
        delete kt[a.id];
        return kt;
      });
      setMo(null);
      toast(`Đã nộp "${a.title}".`);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không nộp được bài'));
    } finally {
      setDangGui(null);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      {err && (
        <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">
          {err}
        </p>
      )}

      <Card>
        <CardHead
          title="Bài tập của bạn"
          hint={
            chuaNop > 0
              ? `Còn ${chuaNop} bài chưa nộp.`
              : 'Bài giảng viên giao cho lớp bạn đang học. Nộp xong, giảng viên đọc rồi mới cho điểm.'
          }
        />

        {ds.length === 0 ? (
          <EmptyState
            title="Chưa có bài tập nào"
            hint="Khi giảng viên giao bài cho lớp bạn, bài sẽ hiện ở đây kèm hạn nộp."
          />
        ) : (
          <ul className="flex flex-col gap-2">
            {ds.map((a) => {
              const han = fmt(a.dueAt);
              const tre = a.status === 'open' && !a.submittedAt && quaHan(a.dueAt);
              const dangMo = mo === a.id;
              const thang = a.maxScore ?? 10;
              return (
                <li key={a.id} className="rounded-md border border-line bg-surface px-4 py-3">
                  <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                    <span className="text-subhead text-ink">{a.title}</span>
                    {a.gradedAt ? (
                      <Chip tone="good">
                        {a.score}/{thang}
                        {a.scorePct !== null ? ` · ${Math.round(a.scorePct)}%` : ''}
                      </Chip>
                    ) : a.submittedAt ? (
                      <Chip tone="brand">Đã nộp — chờ chấm</Chip>
                    ) : a.status === 'closed' ? (
                      <Chip tone="warn">Đã đóng, không nộp được</Chip>
                    ) : (
                      <Chip tone="neutral">Chưa nộp</Chip>
                    )}
                    {a.topic && <Chip tone="brand">{a.topic}</Chip>}
                  </div>

                  <p className="mt-1 text-small text-ink-3">
                    {a.className}
                    {han && (
                      <>
                        {' · hạn '}
                        <span className={tre ? 'text-warning-ink' : undefined}>
                          {han}
                          {tre && ' (đã quá hạn)'}
                        </span>
                      </>
                    )}
                  </p>

                  {a.description && (
                    // `whitespace-pre-wrap`: đề bài có xuống dòng, gộp mất chúng
                    // là đọc một đề khác với đề giảng viên viết.
                    <p className="mt-2 rounded-md bg-sunken px-3 py-2 text-body whitespace-pre-wrap text-ink-2">
                      {a.description}
                    </p>
                  )}

                  {a.gradedAt && a.feedback && (
                    <p className="mt-2 rounded-md border border-line bg-sunken px-3 py-2 text-body text-ink">
                      <span className="text-label text-ink-3">Nhận xét của giảng viên</span>
                      <br />
                      {a.feedback}
                    </p>
                  )}

                  {a.submittedAt && (
                    <p className="mt-2 text-small text-ink-3">
                      Bạn nộp lúc {fmt(a.submittedAt)}.
                    </p>
                  )}

                  {a.status === 'open' ? (
                    <div className="mt-3">
                      {dangMo ? (
                        <>
                          <label htmlFor={`nop-${a.id}`} className="text-label text-ink-3">
                            Bài làm của bạn
                          </label>
                          <textarea
                            id={`nop-${a.id}`}
                            rows={8}
                            maxLength={20000}
                            defaultValue={nhap[a.id] ?? a.content ?? ''}
                            onChange={(e) =>
                              setNhap((cu) => ({ ...cu, [a.id]: e.target.value }))
                            }
                            className="mt-1 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 py-2 text-input text-ink"
                          />
                          <div className="mt-2 flex flex-wrap items-center gap-2">
                            <Button onClick={() => void nop(a)} loading={dangGui === a.id}>
                              {a.submittedAt ? 'Nộp lại' : 'Nộp bài'}
                            </Button>
                            <Button variant="ghost" onClick={() => setMo(null)}>
                              Đóng
                            </Button>
                            {a.gradedAt && (
                              <span className="text-small text-warning-ink">
                                Nộp lại sẽ xoá điểm {a.score}/{thang} và giảng viên phải chấm
                                lại từ đầu.
                              </span>
                            )}
                          </div>
                        </>
                      ) : (
                        <Button
                          size="sm"
                          variant={a.submittedAt ? 'ghost' : 'primary'}
                          onClick={() => setMo(a.id)}
                        >
                          {a.submittedAt ? 'Xem / sửa bài đã nộp' : 'Làm bài'}
                        </Button>
                      )}
                    </div>
                  ) : (
                    <p className="mt-3 text-small text-ink-3">
                      Bài đã đóng, không nộp thêm được. Nếu bạn nộp muộn có lý do, liên hệ giảng
                      viên.
                    </p>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}
