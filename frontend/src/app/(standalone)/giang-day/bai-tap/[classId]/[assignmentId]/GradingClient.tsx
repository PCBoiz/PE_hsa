'use client';

import { useMemo, useState } from 'react';

import {
  Button,
  Card,
  CardHead,
  Chip,
  EmptyState,
  Tile,
  TileRow,
  ToastProvider,
  useToast,
} from '@/components/ui';
import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';

export type HocVien = {
  userId: number;
  name: string | null;
  email: string | null;
  submittedAt: string | null;
  content: string | null;
  fileUrl: string | null;
  score: number | null;
  scorePct: number | null;
  feedback: string | null;
  gradedAt: string | null;
  gradedByName: string | null;
};

function fmt(iso: string | null) {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const p = (n: number) => String(n).padStart(2, '0');
  return `${p(d.getDate())}/${p(d.getMonth() + 1)} · ${p(d.getHours())}:${p(d.getMinutes())}`;
}

/** Ô nhập của một em, trước khi bấm Lưu. Chuỗi rỗng = CHƯA chấm, không phải 0. */
type Nhap = { score: string; feedback: string };

/**
 * Bảng chấm cả lớp trên MỘT màn hình.
 *
 * Vì sao không mỗi em một trang: chấm hai chục bài tự luận là hai chục lần tải
 * trang, và giảng viên mất luôn khả năng so bài em này với em kia — thứ người
 * chấm tay nào cũng làm để giữ thang điểm nhất quán trong một lượt chấm.
 *
 * MỘT LƯỢT GHI cho cả lớp. Gọi API cho từng em là mỗi em một round-trip tới
 * Neon; đo trên đường điểm danh (T41) là 3 em = 9 lượt, một lớp 30 em = 90 lượt
 * cho một cú bấm. Ở đây tất cả đi trong một POST.
 *
 * CHỈ GỬI Ô ĐÃ SỬA. Backend từ chối `score` rỗng thay vì hiểu ngầm thành 0 —
 * xem `AssignmentGradingView.post` — nên "chưa chấm" phải được giữ nguyên là
 * chưa chấm, chứ không bị một lần bấm Lưu biến thành điểm không.
 */
export default function GradingClient({
  assignmentId,
  title,
  maxScore,
  topic,
  students,
  loiTai,
}: {
  assignmentId: number;
  title: string;
  maxScore: number;
  topic: string | null;
  students: HocVien[];
  loiTai?: string | null;
}) {
  return (
    <ToastProvider>
      <Bang
        assignmentId={assignmentId}
        title={title}
        maxScore={maxScore}
        topic={topic}
        students={students}
        loiTai={loiTai}
      />
    </ToastProvider>
  );
}

function Bang({
  assignmentId,
  title,
  maxScore,
  topic,
  students,
  loiTai,
}: {
  assignmentId: number;
  title: string;
  maxScore: number;
  topic: string | null;
  students: HocVien[];
  loiTai?: string | null;
}) {
  const [ds, setDs] = useState<HocVien[]>(students);
  const [nhap, setNhap] = useState<Record<number, Nhap>>({});
  const [err, setErr] = useState<string | null>(loiTai ?? null);
  const [dangLuu, setDangLuu] = useState(false);
  const [mo, setMo] = useState<number | null>(null);
  const toast = useToast();

  const daNop = ds.filter((s) => s.submittedAt).length;
  const daCham = ds.filter((s) => s.gradedAt).length;

  /**
   * Những ô giảng viên THỰC SỰ vừa gõ, và giá trị của chúng hợp lệ.
   *
   * Lọc ở đây chứ không lọc lúc gửi: nút Lưu phải nói được nó sắp lưu bao nhiêu
   * bài TRƯỚC khi bấm. Một nút "Lưu" không cho biết nó động vào gì là nút người
   * ta ngại bấm.
   */
  const sapLuu = useMemo(() => {
    const ra: { user_id: number; score: number; feedback: string }[] = [];
    for (const [uid, v] of Object.entries(nhap)) {
      const s = v.score.trim();
      if (s === '') continue;
      const n = Number(s);
      if (!Number.isFinite(n) || n < 0 || n > maxScore) continue;
      ra.push({ user_id: Number(uid), score: n, feedback: v.feedback.trim() });
    }
    return ra;
  }, [nhap, maxScore]);

  /** Ô đã gõ nhưng SAI — phải đếm riêng, nếu không nút Lưu im lặng bỏ qua chúng. */
  const oHong = useMemo(
    () =>
      Object.entries(nhap).filter(([, v]) => {
        const s = v.score.trim();
        if (s === '') return false;
        const n = Number(s);
        return !Number.isFinite(n) || n < 0 || n > maxScore;
      }).length,
    [nhap, maxScore],
  );

  async function luu() {
    if (sapLuu.length === 0) return;
    setErr(null);
    setDangLuu(true);
    try {
      const r = await apiFetch(`/api/teach/assignments/${assignmentId}/submissions`, {
        method: 'POST',
        body: JSON.stringify({ grades: sapLuu }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));

      // Nạp lại từ máy chủ chứ không tự vá trạng thái tại chỗ: `gradedAt`,
      // `gradedByName` và `scorePct` đều do backend tính, và một bản sao tự
      // dựng ở đây sớm muộn sẽ lệch với thứ đang nằm trong CSDL.
      const r2 = await apiFetch(`/api/teach/assignments/${assignmentId}/submissions`);
      if (r2.ok) setDs((await r2.json()).students ?? []);
      setNhap({});

      // Nhắc lại CON SỐ, không chỉ nói "Đã lưu": giảng viên vừa gõ hai chục ô
      // và thứ họ cần yên tâm là máy đếm đúng bằng số mình gõ.
      const bo = Array.isArray(d.skipped) && d.skipped.length > 0
        ? ` (${d.skipped.length} em không còn học lớp này nên bỏ qua)`
        : '';
      toast(`Đã chấm ${d.graded} bài${bo}.`);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không lưu được điểm'));
    } finally {
      setDangLuu(false);
    }
  }

  function sua(uid: number, patch: Partial<Nhap>) {
    setNhap((cu) => {
      // Dựng tường minh thay vì `{score:'', feedback:'', ...cu[uid], ...patch}`.
      // Thứ tự spread ở bản đầu CHẠY ĐÚNG nhưng `tsc` từ chối (TS2783: khoá khai
      // hai lần), và một biểu thức mà trình biên dịch phải đoán ý là biểu thức
      // người đọc cũng phải đoán.
      const truoc = cu[uid] ?? { score: '', feedback: '' };
      return { ...cu, [uid]: { ...truoc, ...patch } };
    });
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
          title={title}
          hint={
            topic
              ? `Chủ đề "${topic}" — điểm chấm ở đây vào thẳng ô đó trên bản đồ năng lực của từng em.`
              : 'Bài này CHƯA gắn chủ đề: điểm vẫn vào sổ nhưng không vào được ô nào trên bản đồ năng lực. Sửa bài để gắn chủ đề.'
          }
        />
        <TileRow>
          <Tile value={`${daNop}/${ds.length}`} label="Đã nộp" />
          <Tile
            value={`${daCham}/${ds.length}`}
            label="Đã chấm"
            tone={daCham < daNop ? 'warn' : 'good'}
          />
          <Tile value={maxScore} label="Thang điểm" />
        </TileRow>
      </Card>

      {ds.length === 0 ? (
        <EmptyState
          title="Lớp chưa có học viên nào đang học"
          hint="Xếp học viên vào lớp ở khu Quản trị, rồi quay lại đây."
        />
      ) : (
        <>
          <ul className="flex flex-col gap-2">
            {ds.map((s) => {
              const v = nhap[s.userId];
              const nop = fmt(s.submittedAt);
              const dangMo = mo === s.userId;
              const sai =
                v && v.score.trim() !== '' &&
                (!Number.isFinite(Number(v.score)) ||
                  Number(v.score) < 0 ||
                  Number(v.score) > maxScore);
              return (
                <li key={s.userId} className="rounded-md border border-line bg-surface px-4 py-3">
                  <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                    <span className="text-subhead text-ink">{s.name || s.email}</span>
                    {nop ? (
                      <Chip tone="good">Nộp {nop}</Chip>
                    ) : (
                      <Chip tone="neutral">Chưa nộp</Chip>
                    )}
                    {s.gradedAt && (
                      <Chip tone="brand">
                        {s.score}/{maxScore}
                        {s.scorePct !== null ? ` · ${Math.round(s.scorePct)}%` : ''}
                      </Chip>
                    )}
                  </div>

                  {s.content && (
                    <div className="mt-2">
                      <button
                        type="button"
                        onClick={() => setMo(dangMo ? null : s.userId)}
                        aria-expanded={dangMo}
                        className="min-h-11 text-small text-brand-ink underline"
                      >
                        {dangMo ? 'Thu gọn bài làm' : 'Xem bài làm'}
                      </button>
                      {dangMo && (
                        // `whitespace-pre-wrap`: bài tự luận có xuống dòng, và
                        // gộp mất chúng là đọc một bài khác với bài em viết.
                        <p className="mt-1 max-h-96 overflow-y-auto rounded-md bg-sunken px-3 py-2 text-body whitespace-pre-wrap text-ink">
                          {s.content}
                        </p>
                      )}
                    </div>
                  )}

                  <div className="mt-3 flex flex-wrap items-end gap-3">
                    <div>
                      <label
                        htmlFor={`d-${s.userId}`}
                        className="block text-label text-ink-3"
                      >
                        Điểm (0–{maxScore})
                      </label>
                      <input
                        id={`d-${s.userId}`}
                        type="number"
                        min={0}
                        max={maxScore}
                        step="0.25"
                        inputMode="decimal"
                        value={v?.score ?? ''}
                        placeholder={s.score !== null ? String(s.score) : '—'}
                        onChange={(e) => sua(s.userId, { score: e.target.value })}
                        aria-invalid={sai || undefined}
                        className={[
                          'mt-1 min-h-11 w-28 rounded-md border bg-sunken px-3 text-input text-ink tabular-nums',
                          sai ? 'border-danger' : 'border-line-input',
                        ].join(' ')}
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <label
                        htmlFor={`nx-${s.userId}`}
                        className="block text-label text-ink-3"
                      >
                        Nhận xét
                      </label>
                      <input
                        id={`nx-${s.userId}`}
                        maxLength={4000}
                        value={v?.feedback ?? ''}
                        placeholder={s.feedback ?? 'không bắt buộc'}
                        onChange={(e) => sua(s.userId, { feedback: e.target.value })}
                        className="mt-1 min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink placeholder:text-ink-3/70"
                      />
                    </div>
                  </div>

                  {sai && (
                    <p role="alert" className="mt-1 text-small text-danger-ink">
                      Điểm phải là số trong khoảng 0–{maxScore}. Ô này sẽ KHÔNG được lưu.
                    </p>
                  )}
                  {s.gradedAt && s.gradedByName && (
                    <p className="mt-1 text-small text-ink-3">
                      {s.gradedByName} chấm lúc {fmt(s.gradedAt)}
                      {s.feedback ? ` — “${s.feedback}”` : ''}
                    </p>
                  )}
                </li>
              );
            })}
          </ul>

          {/* Neo đáy màn hình: bảng chấm dài hơn một khung nhìn, và một nút Lưu
              nằm dưới cùng danh sách là nút phải cuộn tới mới bấm được. Cùng lý
              do đã ghi ở màn hình điểm danh. */}
          <div className="sticky bottom-0 -mx-4 border-t border-line bg-surface px-4 py-3">
            <div className="flex flex-wrap items-center gap-3">
              <Button onClick={() => void luu()} loading={dangLuu} disabled={sapLuu.length === 0}>
                {sapLuu.length > 0 ? `Lưu ${sapLuu.length} bài chấm` : 'Chưa gõ điểm nào'}
              </Button>
              {oHong > 0 && (
                <span className="text-small text-danger-ink">
                  {oHong} ô điểm không hợp lệ, sẽ không được lưu.
                </span>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
