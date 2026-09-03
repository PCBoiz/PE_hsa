'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import { Button, Card, CardHead, Field } from '@/components/ui';
import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';
import {
  docRaBieuMau,
  hopNhat,
  truongLa,
  type BieuMau,
  type CauHoi,
  type NoiDungBai as TNoiDung,
  type The,
} from '@/lib/soanBai';

type Ban = {
  id: number;
  course_id: string;
  title: string;
  sort_order: number;
  content_json: TNoiDung | null;
};

const O = 'w-full rounded-md border border-line bg-surface px-3 py-2 text-body text-ink';

/**
 * Bộ soạn nội dung 5 bước của MỘT bài.
 *
 * ── LUẬT SỐNG CÒN: GỘP, KHÔNG DỰNG LẠI ────────────────────────────────────
 *
 * Mọi thay đổi đi qua `hopNhat` trong `@/lib/soanBai` — nó bắt đầu từ bản đã
 * nạp và chỉ đè lên những trường biểu mẫu này quản. Bản cũ dựng object mới từ
 * đầu, nên hai trường có ở CẢ 76 bài biến mất khi lưu: `drill.time_seconds`
 * (bị bộ kiểm máy chủ chặn nên thành "không lưu được") và `notes` (không ai
 * chặn, mất im lặng).
 *
 * Nếu sau này thêm một trường vào giáo trình mà quên thêm ô nhập ở đây, nó
 * KHÔNG mất — nó chỉ không sửa được, và màn hình nói thẳng ra ở cuối trang.
 *
 * ── KHÔNG DỰNG LẠI BỘ KIỂM Ở ĐÂY ──────────────────────────────────────────
 *
 * Luật hợp lệ nằm ở `backend/lessons/content.py` và chỉ ở đó. Màn hình này chỉ
 * HIỆN ĐẸP các lỗi máy chủ trả về. Chép luật sang đây là dựng nguồn sự thật thứ
 * hai cho cùng một câu hỏi, và hai bản sẽ trôi (`RULES §7`).
 */
export default function NoiDungBai({
  baiId,
  onDong,
  onLuuXong,
}: {
  baiId: number;
  onDong: () => void;
  onLuuXong: () => void;
}) {
  const [ban, setBan] = useState<Ban | null>(null);
  const [m, setM] = useState<BieuMau | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [chiTiet, setChiTiet] = useState<string[]>([]);
  const [xong, setXong] = useState<string | null>(null);
  const dangGui = useRef(false);

  useEffect(() => {
    let huy = false;
    void (async () => {
      setErr(null);
      setXong(null);
      setChiTiet([]);
      try {
        const r = await apiFetch(`/api/admin/lessons/${baiId}/content`);
        const d: unknown = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(errorText(r.status, d));
        if (huy) return;
        const row = d as Ban;
        setBan(row);
        setM(docRaBieuMau(row.content_json, row.sort_order));
      } catch (e) {
        if (!huy) setErr(loiBatDuoc(e, 'Không mở được nội dung bài.'));
      }
    })();
    return () => {
      huy = true;
    };
  }, [baiId]);

  const dat = useCallback(<K extends keyof BieuMau>(k: K, v: BieuMau[K]) => {
    setM((cu) => (cu ? { ...cu, [k]: v } : cu));
  }, []);

  async function luu() {
    if (!ban || !m || dangGui.current) return;
    dangGui.current = true;
    setErr(null);
    setChiTiet([]);
    setXong(null);
    try {
      const moi = hopNhat(ban.content_json, m);
      const r = await apiFetch(`/api/admin/lessons/${ban.id}/content`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content_json: moi }),
      });
      const d = (await r.json().catch(() => ({}))) as { details?: string[] };
      if (!r.ok) {
        setChiTiet(Array.isArray(d.details) ? d.details : []);
        throw new Error(errorText(r.status, d));
      }
      // Nạp lại BẢN VỪA GHI làm gốc mới. Không làm thì lần lưu thứ hai vẫn gộp
      // vào bản cũ, và một trường vừa xoá sẽ sống lại.
      setBan({ ...ban, content_json: moi });
      setXong('Đã lưu.');
      onLuuXong();
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không lưu được nội dung.'));
    } finally {
      dangGui.current = false;
    }
  }

  if (err && !m) {
    return (
      <Card as="section">
        <CardHead title="Nội dung bài" />
        <p role="alert" className="text-body text-danger-ink">
          {err}
        </p>
      </Card>
    );
  }
  if (!ban || !m) {
    return (
      <Card as="section">
        <CardHead title="Nội dung bài" />
        <p className="text-body text-ink-3">Đang mở…</p>
      </Card>
    );
  }

  const la = truongLa(ban.content_json);

  return (
    <Card as="section">
      <CardHead
        title={`Nội dung — ${ban.title}`}
        hint={`Bài số ${ban.sort_order} của khoá ${ban.course_id}`}
        action={
          <div className="flex flex-wrap gap-2">
            <a
              className="inline-flex items-center rounded-md border border-line px-3 py-1.5 text-label text-ink-2"
              href={`/lesson/${encodeURIComponent(ban.course_id)}?lesson=${m.index}`}
              target="_blank"
              rel="noreferrer"
            >
              Xem thử ↗
            </a>
            <Button size="sm" variant="ghost" onClick={onDong}>
              Đóng
            </Button>
            <Button
              size="sm"
              onClick={() => {
                void luu();
              }}
            >
              Lưu nội dung
            </Button>
          </div>
        }
      />

      {err && (
        <div
          role="alert"
          className="mb-4 rounded-md border border-danger bg-danger-soft px-4 py-3 text-body text-danger-ink"
        >
          {err}
          {chiTiet.length > 0 && (
            <ul className="mt-2 flex flex-col gap-1">
              {chiTiet.map((c, i) => (
                <li key={i} className="font-mono text-caption">
                  {c}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
      {xong && <p className="mb-4 text-body text-ok-ink">{xong}</p>}

      <div className="flex flex-col gap-8">
        {/* ── Thông tin bài ── */}
        <Khoi ten="Thông tin bài">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field
              id="nd-id"
              label="Mã bài"
              hint="Dùng trong file giáo trình, ví dụ ql_01."
              value={m.id}
              onChange={(e) => dat('id', e.target.value)}
            />
            <Field
              id="nd-index"
              label="Số thứ tự (index)"
              hint="PHẢI bằng số bài ở cột # — máy chủ từ chối nếu lệch."
              type="number"
              min={1}
              value={m.index}
              onChange={(e) => dat('index', Number(e.target.value))}
            />
            <Field
              id="nd-title"
              label="Tiêu đề"
              value={m.title}
              onChange={(e) => dat('title', e.target.value)}
            />
            <Field
              id="nd-sub"
              label="Tiêu đề phụ"
              value={m.subtitle}
              onChange={(e) => dat('subtitle', e.target.value)}
            />
            <Field
              id="nd-topic"
              label="Chủ đề"
              hint="Ví dụ: Định lượng · Số học"
              value={m.topic_tag}
              onChange={(e) => dat('topic_tag', e.target.value)}
            />
            <Field
              id="nd-xp"
              label="XP thưởng"
              type="number"
              min={0}
              max={500}
              value={m.xp_reward}
              onChange={(e) => dat('xp_reward', Number(e.target.value))}
            />
          </div>
        </Khoi>

        {/* ── Bước 1: định vị ── */}
        <Khoi
          ten="Bước 1 — Câu hỏi định vị"
          ghi="Kết quả ở đây quyết định học viên nhận bản lý thuyết tóm tắt hay đầy đủ."
        >
          <label className="flex flex-col gap-2">
            <span className="text-label text-ink-3">Lời dẫn</span>
            <input
              className={O}
              value={m.testIntro}
              onChange={(e) => dat('testIntro', e.target.value)}
            />
          </label>
          <DsCauHoi
            ten="định vị"
            ds={m.testQuestions}
            onDoi={(v) => dat('testQuestions', v)}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <Field
              id="nd-strong"
              label="Đúng từ mấy câu thì cho bản TÓM TẮT"
              hint="Bỏ trống = dùng mặc định của engine."
              type="number"
              min={0}
              value={m.strongMin}
              onChange={(e) => dat('strongMin', e.target.value)}
            />
            <Field
              id="nd-ok"
              label="Ngưỡng “tạm ổn”"
              type="number"
              min={0}
              value={m.okMin}
              onChange={(e) => dat('okMin', e.target.value)}
            />
          </div>
        </Khoi>

        {/* ── Bước 2–3: lý thuyết ── */}
        <Khoi
          ten="Bước 2–3 — Lý thuyết"
          gap
          ghi="Minh hoạ đặt trong bản nào thì CHỈ bản đó có. Chỉ đặt ở bản đầy đủ thì học viên giỏi không bao giờ nhìn thấy đồ thị."
        >
          <BanLyThuyet
            nhan="Bản đầy đủ"
            tieuDe={m.fullTitle}
            the={m.fullCards}
            onTieuDe={(v) => dat('fullTitle', v)}
            onThe={(v) => dat('fullCards', v)}
          />
          <BanLyThuyet
            nhan="Bản tóm tắt"
            tieuDe={m.condTitle}
            the={m.condCards}
            onTieuDe={(v) => dat('condTitle', v)}
            onThe={(v) => dat('condCards', v)}
          />
        </Khoi>

        {/* ── Ghi nhớ ── */}
        <Khoi
          ten="Bước 4 — Ghi nhớ"
          ghi="Khối này engine đọc từ trường `notes`. Bộ soạn cũ ghi vào `note` số ít — một trường không bài nào có và engine không bao giờ đọc."
        >
          <label className="flex flex-col gap-2">
            <span className="text-label text-ink-3">Mẹo</span>
            <textarea
              className={O}
              rows={2}
              value={m.notesTip}
              onChange={(e) => dat('notesTip', e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-2">
            <span className="text-label text-ink-3">Công thức</span>
            <input
              className={`${O} font-mono`}
              value={m.notesFormula}
              onChange={(e) => dat('notesFormula', e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-2">
            <span className="text-label text-ink-3">Ý chính — mỗi dòng một ý</span>
            <textarea
              className={O}
              rows={4}
              value={m.notesKeyPoints.join('\n')}
              onChange={(e) => dat('notesKeyPoints', e.target.value.split('\n'))}
            />
          </label>
        </Khoi>

        {/* ── Bước 5: phòng luyện ── */}
        <Khoi
          ten="Bước 5 — Phòng luyện tốc độ"
          gap
          ghi="Xoá hết câu VÀ xoá lời dẫn thì cả phòng luyện bị bỏ khỏi bài."
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <Field
              id="nd-dintro"
              label="Lời dẫn"
              value={m.drillIntro}
              onChange={(e) => dat('drillIntro', e.target.value)}
            />
            <Field
              id="nd-dsec"
              label="Thời gian (giây)"
              hint="Ghi ra trường time_seconds — đúng tên engine đọc."
              type="number"
              min={5}
              max={3600}
              value={m.drillSeconds}
              onChange={(e) => dat('drillSeconds', Number(e.target.value))}
            />
          </div>
          <DsCauHoi
            ten="luyện"
            ds={m.drillQuestions}
            onDoi={(v) => dat('drillQuestions', v)}
          />
        </Khoi>

        {/* Thanh dính đáy: nút Lưu phải với tới được từ MỌI chỗ trong biểu mẫu
            dài 9.600px, không chỉ từ đỉnh. */}
        <div className="sticky bottom-0 -mx-4 flex items-center justify-end gap-2 border-t border-line bg-surface/95 px-4 py-3 backdrop-blur">
          {xong && <span className="mr-auto text-body text-ok-ink">{xong}</span>}
          <Button variant="ghost" onClick={onDong}>
            Đóng
          </Button>
          <Button
            onClick={() => {
              void luu();
            }}
          >
            Lưu nội dung
          </Button>
        </div>

        {la.length > 0 && (
          <p className="rounded-md border border-line bg-sunken px-4 py-3 text-caption text-ink-2">
            Bài này còn <b>{la.length}</b> trường màn hình chưa hiện ra:{' '}
            <code>{la.join(', ')}</code>. Chúng được <b>giữ nguyên</b> khi lưu — chỉ là chưa
            sửa được từ đây.
          </p>
        )}
      </div>
    </Card>
  );
}

/* ── Mảnh dùng lại ───────────────────────────────────────────────────────── */

/**
 * Một khối của biểu mẫu. `gap` = gập được.
 *
 * Đo 04/09: cả bộ soạn cao **9.615px** với một bài thật — người soạn cuộn hết
 * trang rồi phải cuộn ngược lên mới thấy nút Lưu. Hai khối dài nhất (lý thuyết
 * và phòng luyện) nay gập lại được, và thanh Lưu dính đáy màn hình.
 *
 * Dùng `<details>` của HTML chứ không tự dựng bằng state: nó gập/mở được bằng
 * bàn phím sẵn, trình đọc màn hình đọc đúng trạng thái, và Ctrl+F của trình
 * duyệt vẫn tìm được chữ bên trong ở các trình duyệt mới.
 */
function Khoi({
  ten,
  ghi,
  gap = false,
  children,
}: {
  ten: string;
  ghi?: string;
  gap?: boolean;
  children: React.ReactNode;
}) {
  const dau = (
    <div>
      <h3 className="text-section text-ink">{ten}</h3>
      {ghi && <p className="mt-1 text-small text-ink-3">{ghi}</p>}
    </div>
  );
  const than = <div className="flex flex-col gap-4">{children}</div>;

  if (!gap) {
    return (
      <section className="flex flex-col gap-4 border-t border-line pt-6 first:border-t-0 first:pt-0">
        {dau}
        {than}
      </section>
    );
  }
  return (
    <details open className="border-t border-line pt-6 first:border-t-0 first:pt-0">
      <summary className="cursor-pointer list-none">{dau}</summary>
      <div className="mt-4">{than}</div>
    </details>
  );
}

function DsCauHoi({
  ten,
  ds,
  onDoi,
}: {
  ten: string;
  ds: CauHoi[];
  onDoi: (v: CauHoi[]) => void;
}) {
  const sua = (i: number, p: Partial<CauHoi>) =>
    onDoi(ds.map((c, j) => (i === j ? { ...c, ...p } : c)));

  return (
    <div className="flex flex-col gap-3">
      {ds.map((c, i) => (
        <div key={i} className="flex flex-col gap-3 rounded-md border border-line p-3">
          <div className="flex flex-wrap items-center gap-2">
            <select
              aria-label={`Kiểu câu ${i + 1}`}
              className="rounded-md border border-line bg-surface px-2 py-1.5 text-body text-ink"
              value={c.type || 'mcq'}
              onChange={(e) => sua(i, { type: e.target.value as CauHoi['type'] })}
            >
              <option value="mcq">Trắc nghiệm</option>
              <option value="fill">Điền đáp án</option>
            </select>
            <input
              aria-label={`Mã câu ${i + 1}`}
              className="w-32 rounded-md border border-line bg-surface px-2 py-1.5 text-body text-ink"
              placeholder="mã (t1)"
              value={c.id || ''}
              onChange={(e) => sua(i, { id: e.target.value })}
            />
            <Button
              size="sm"
              variant="ghost"
              className="ml-auto"
              onClick={() => onDoi(ds.filter((_, j) => j !== i))}
            >
              Xoá câu
            </Button>
          </div>
          <textarea
            aria-label={`Nội dung câu ${i + 1}`}
            className={O}
            rows={2}
            placeholder="Nội dung câu hỏi"
            value={c.question || ''}
            onChange={(e) => sua(i, { question: e.target.value })}
          />
          {(c.type || 'mcq') === 'mcq' && (
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Lựa chọn — mỗi dòng một</span>
              <textarea
                className={O}
                rows={3}
                value={(c.options || []).join('\n')}
                onChange={(e) => sua(i, { options: e.target.value.split('\n') })}
              />
            </label>
          )}
          <input
            aria-label={`Đáp án câu ${i + 1}`}
            className={O}
            placeholder="Đáp án đúng — với trắc nghiệm phải trùng ĐÚNG một dòng ở trên"
            value={c.answer ?? ''}
            onChange={(e) => sua(i, { answer: e.target.value })}
          />
          <input
            aria-label={`Giải thích câu ${i + 1}`}
            className={O}
            placeholder="Giải thích (hiện sau khi chấm)"
            value={c.explain || ''}
            onChange={(e) => sua(i, { explain: e.target.value })}
          />
        </div>
      ))}
      <div>
        <Button
          size="sm"
          variant="ghost"
          onClick={() =>
            onDoi([...ds, { id: '', type: 'mcq', question: '', options: [], answer: '' }])
          }
        >
          + Thêm câu {ten}
        </Button>
      </div>
    </div>
  );
}

function BanLyThuyet({
  nhan,
  tieuDe,
  the,
  onTieuDe,
  onThe,
}: {
  nhan: string;
  tieuDe: string;
  the: The[];
  onTieuDe: (v: string) => void;
  onThe: (v: The[]) => void;
}) {
  const sua = (i: number, p: Partial<The>) =>
    onThe(the.map((t, j) => (i === j ? { ...t, ...p } : t)));

  return (
    <div className="flex flex-col gap-3 rounded-md border border-line p-3">
      <div className="flex flex-wrap items-center gap-3">
        <h4 className="text-label text-ink">{nhan}</h4>
        <input
          aria-label={`Tiêu đề ${nhan}`}
          className="min-w-48 flex-1 rounded-md border border-line bg-surface px-2 py-1.5 text-body text-ink"
          placeholder="Tiêu đề khối"
          value={tieuDe}
          onChange={(e) => onTieuDe(e.target.value)}
        />
        <span className="text-caption text-ink-3">{the.length} thẻ</span>
      </div>

      {the.map((t, i) => (
        <div key={i} className="flex flex-col gap-2 rounded-md border border-line/60 p-3">
          <div className="flex flex-wrap items-center gap-2">
            <input
              aria-label={`Biểu tượng thẻ ${i + 1} — ${nhan}`}
              className="w-32 rounded-md border border-line bg-surface px-2 py-1.5 text-body text-ink"
              placeholder="fa-book"
              value={t.icon || ''}
              onChange={(e) => sua(i, { icon: e.target.value })}
            />
            <input
              aria-label={`Tiêu đề thẻ ${i + 1} — ${nhan}`}
              className="min-w-48 flex-1 rounded-md border border-line bg-surface px-2 py-1.5 text-body text-ink"
              placeholder="Tiêu đề thẻ"
              value={t.title || ''}
              onChange={(e) => sua(i, { title: e.target.value })}
            />
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onThe(the.filter((_, j) => j !== i))}
            >
              Xoá thẻ
            </Button>
          </div>
          <textarea
            aria-label={`Nội dung thẻ ${i + 1} — ${nhan}`}
            className={O}
            rows={3}
            placeholder="Nội dung thẻ (cho phép thẻ HTML nhẹ)"
            value={t.body || ''}
            onChange={(e) => sua(i, { body: e.target.value })}
          />
          <MinhHoa
            nhan={`Minh hoạ thẻ ${i + 1} — ${nhan}`}
            gia={t.visual}
            onDoi={(v) => sua(i, { visual: v })}
          />
        </div>
      ))}

      <div>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => onThe([...the, { icon: 'fa-book', title: '', body: '' }])}
        >
          + Thêm thẻ
        </Button>
      </div>
    </div>
  );
}

/**
 * Ô minh hoạ — vẫn là JSON thô, nhưng KHÔNG nuốt lỗi.
 *
 * Tám kiểu (bars/numline/curve/flow/table/pie/tree/timeline) có hình dạng khác
 * nhau hẳn, nên một bộ soạn có ô riêng cho từng kiểu là một màn hình khác và
 * đáng làm riêng. Ở đây điều quan trọng là: gõ sai JSON thì BÁO ngay tại chỗ,
 * chứ không để người soạn bấm Lưu rồi tưởng đồ thị đã vào.
 */
function MinhHoa({
  nhan,
  gia,
  onDoi,
}: {
  nhan: string;
  gia: unknown;
  onDoi: (v: unknown) => void;
}) {
  const [tho, setTho] = useState(() => (gia == null ? '' : JSON.stringify(gia, null, 1)));
  const [loi, setLoi] = useState<string | null>(null);

  return (
    <label className="flex flex-col gap-1">
      <span className="text-label text-ink-3">
        Minh hoạ — JSON, để trống nếu không có. 8 kiểu: bars · numline · curve · flow · table ·
        pie · tree · timeline
      </span>
      <textarea
        aria-label={nhan}
        className={`${O} font-mono text-caption`}
        /* 8 dòng chứ không 3: JSON in đẹp của một minh hoạ nhỏ nhất cũng đã 6
           dòng, nên 3 dòng cho ra đúng `{ "max": 25, "bars": [` rồi cắt —
           người soạn không đọc nổi thứ mình đang sửa. (Đo trên bài 1 khoá Định
           lượng, 04/09.) */
        rows={8}
        spellCheck={false}
        placeholder={'{"type":"bars","bars":[{"label":"A","value":10}]}'}
        value={tho}
        onChange={(e) => {
          const v = e.target.value;
          setTho(v);
          if (!v.trim()) {
            setLoi(null);
            onDoi(undefined);
            return;
          }
          try {
            onDoi(JSON.parse(v));
            setLoi(null);
          } catch (er) {
            setLoi(er instanceof Error ? er.message : 'JSON không hợp lệ');
          }
        }}
      />
      {loi && (
        <span role="alert" className="text-caption text-danger-ink">
          {loi} — phần minh hoạ này chưa được ghi nhận.
        </span>
      )}
    </label>
  );
}
