'use client';

import { useRef, useState } from 'react';

import {
  Button,
  Card,
  CardHead,
  Chip,
  EmptyState,
  TableWrap,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
} from '@/components/ui';
import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';

export type TermRow = {
  id: number;
  code: string | null;
  name: string;
  startsOn: string | null;
  endsOn: string | null;
  examDate: string | null;
  status: string;
  note: string | null;
  classes?: number;
  students?: number;
};

const TRANG_THAI: Record<string, { nhan: string; tone: 'good' | 'neutral' | 'bad' }> = {
  active: { nhan: 'Đang chạy', tone: 'good' },
  finished: { nhan: 'Đã kết thúc', tone: 'neutral' },
  cancelled: { nhan: 'Đã huỷ', tone: 'bad' },
};

function ngay(iso: string | null) {
  if (!iso) return '—';
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

/**
 * Quản lý ĐỢT HỌC — schema §36, API `teaching/terms.py`.
 *
 * Vì sao màn hình này tồn tại: không có đợt thì "đợt 1/2027 so với đợt 2/2027"
 * phải suy từ ngày khai giảng và ĐỌC TÊN LỚP. Thông tin nghiệp vụ nằm trong một
 * chuỗi tự do thì mọi báo cáo về sau đều phải đoán lại nó, và đoán sai thì
 * không ai biết.
 *
 * Hai con số "lớp" và "học viên" nằm ngay trong bảng, vì đó là hai câu hỏi đầu
 * tiên ai mở màn hình này cũng hỏi — "đợt vừa rồi có bao nhiêu em".
 */
export default function TermsClient({
  initial,
  statuses,
  loi,
}: {
  initial: TermRow[];
  statuses: string[];
  loi: string | null;
}) {
  const [terms, setTerms] = useState<TermRow[]>(initial);
  const [err, setErr] = useState<string | null>(loi);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [startsOn, setStartsOn] = useState('');
  const [endsOn, setEndsOn] = useState('');
  const [examDate, setExamDate] = useState('');

  // Cùng lý do với ô nhập hàng loạt: `setBusy` của React không có tác dụng ngay
  // nên hai cú bấm liền nhau đều lọt, và ở đây nó tạo ra hai đợt trùng tên.
  const dangGui = useRef(false);

  async function nap() {
    try {
      const r = await apiFetch('/api/admin/terms');
      if (r.ok) setTerms((await r.json()).terms ?? []);
    } catch {
      /* giữ nguyên danh sách đang hiện */
    }
  }

  async function tao() {
    if (dangGui.current) return;
    dangGui.current = true;
    setBusy(true);
    setErr(null);
    try {
      const r = await apiFetch('/api/admin/terms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: code.trim() || null,
          name: name.trim(),
          starts_on: startsOn || null,
          ends_on: endsOn || null,
          exam_date: examDate || null,
        }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      setCode('');
      setName('');
      setStartsOn('');
      setEndsOn('');
      setExamDate('');
      setOpen(false);
      await nap();
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không tạo được đợt học'));
    } finally {
      dangGui.current = false;
      setBusy(false);
    }
  }

  async function doiTrangThai(t: TermRow, next: string) {
    setErr(null);
    try {
      const r = await apiFetch(`/api/admin/terms/${t.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: next }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      await nap();
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không đổi được trạng thái'));
    }
  }

  /**
   * Xoá đợt — hai bước khi đợt còn gắn lớp.
   *
   * Backend trả 409 kèm số lớp sẽ mất nhãn. Câu hỏi phải nói rõ **lớp không
   * mất**: người đang đọc câu này sợ mất dữ liệu, và câu trả lời đúng là "không
   * mất, chỉ mất nhãn đợt" — nếu không họ sẽ không dám bấm và đợt sai cứ nằm đó.
   */
  async function xoa(t: TermRow) {
    // Hỏi TRƯỚC khi gửi. Bản trước gửi DELETE rồi mới hỏi khi backend trả 409,
    // nên một đợt CHƯA gắn lớp nào bị xoá ngay ở cú bấm đầu tiên — không 409,
    // không hộp thoại. Mà nút "Xoá" nằm sát ô chọn trạng thái trong cùng một
    // dòng bảng, tức đúng chỗ dễ bấm nhầm nhất.
    //
    // Khác với buổi học (ở đó buổi chưa điểm danh xoá luôn là hợp lý — nó chỉ
    // chứa đúng thứ vừa gõ vào): một đợt mang tên, mã và ba mốc ngày do người
    // dùng nhập, và nó là cái nhãn mà mọi báo cáo so sánh giữa các mùa thi dựa
    // vào. Gõ lại không đắt, nhưng mất mà không kịp biết thì đắt.
    if (!confirm(`Xoá đợt "${t.name}"?`)) return;
    setErr(null);
    try {
      const r = await apiFetch(`/api/admin/terms/${t.id}`, { method: 'DELETE' });
      const d = await r.json().catch(() => ({}));
      if (r.status === 409 && d.needsConfirm) {
        if (
          !confirm(
            `Đợt "${t.name}" đang gắn ${d.classes} lớp.\n\n` +
              'Xoá đợt KHÔNG xoá lớp nào — các lớp đó chỉ mất nhãn đợt và phải gán lại bằng tay.',
          )
        )
          return;
        const r2 = await apiFetch(`/api/admin/terms/${t.id}?confirm=1`, { method: 'DELETE' });
        const d2 = await r2.json().catch(() => ({}));
        if (!r2.ok) throw new Error(errorText(r2.status, d2));
      } else if (!r.ok) {
        throw new Error(errorText(r.status, d));
      }
      await nap();
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không xoá được đợt học'));
    }
  }

  const oNgay = (nhan: string, gt: string, dat: (v: string) => void) => (
    <label className="flex flex-col gap-1">
      <span className="text-label text-ink-3">{nhan}</span>
      <input
        type="date"
        value={gt}
        onChange={(e) => dat(e.target.value)}
        className="min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink"
      />
    </label>
  );

  return (
    <Card>
      <CardHead
        title="Đợt học"
        hint="Mỗi mùa thi là một đợt. Gán lớp vào đợt thì báo cáo so được đợt này với đợt trước, thay vì phải đọc tên lớp mà đoán."
        action={!open && <Button onClick={() => setOpen(true)}>Tạo đợt</Button>}
      />

      {err && (
        <p role="alert" className="mb-3 rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">
          {err}
        </p>
      )}

      {open && (
        <div className="mb-4 rounded-md border border-line bg-sunken p-4">
          <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr))]">
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Tên đợt</span>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Đợt 1/2027"
                className="min-h-11 w-full min-w-0 rounded-md border border-line bg-surface px-3 text-input text-ink placeholder:text-ink-3/70"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Mã đợt (không bắt buộc)</span>
              <input
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="D1-2027"
                className="min-h-11 w-full min-w-0 rounded-md border border-line bg-surface px-3 text-input text-ink placeholder:text-ink-3/70"
              />
            </label>
            {oNgay('Bắt đầu', startsOn, setStartsOn)}
            {oNgay('Kết thúc', endsOn, setEndsOn)}
            {oNgay('Ngày thi', examDate, setExamDate)}
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button loading={busy} disabled={!name.trim()} onClick={() => void tao()}>
              Tạo đợt
            </Button>
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Huỷ
            </Button>
          </div>
        </div>
      )}

      {terms.length === 0 ? (
        <EmptyState
          title="Chưa có đợt học nào"
          hint="Tạo đợt đầu tiên rồi gán lớp vào đó. Lớp chưa thuộc đợt nào vẫn chạy bình thường — nhãn đợt chỉ để báo cáo so sánh được giữa các mùa thi."
        />
      ) : (
        <TableWrap caption="Các đợt học của trung tâm, kèm số lớp và số học viên mỗi đợt">
          <Thead>
            <tr>
              <Th>Đợt</Th>
              <Th>Thời gian</Th>
              <Th>Ngày thi</Th>
              <Th align="right">Lớp</Th>
              <Th align="right">Học viên</Th>
              <Th>Trạng thái</Th>
              <Th align="right">Thao tác</Th>
            </tr>
          </Thead>
          <Tbody>
            {terms.map((t) => (
              <Tr key={t.id} dim={t.status === 'cancelled'}>
                <Td label="Đợt">
                  <span className="font-semibold text-ink">{t.name}</span>
                  {t.code && <span className="block text-ink-3">{t.code}</span>}
                </Td>
                <Td label="Thời gian" muted>
                  {ngay(t.startsOn)} – {ngay(t.endsOn)}
                </Td>
                <Td label="Ngày thi" muted>
                  {ngay(t.examDate)}
                </Td>
                <Td label="Lớp" num>
                  {t.classes ?? 0}
                </Td>
                <Td label="Học viên" num>
                  {t.students ?? 0}
                </Td>
                <Td label="Trạng thái">
                  <select
                    value={t.status}
                    onChange={(e) => void doiTrangThai(t, e.target.value)}
                    aria-label={`Trạng thái đợt ${t.name}`}
                    className="min-h-11 max-w-full min-w-0 rounded-md border border-line-input bg-sunken px-2 text-small text-ink"
                  >
                    {statuses.map((s) => (
                      <option key={s} value={s}>
                        {TRANG_THAI[s]?.nhan ?? s}
                      </option>
                    ))}
                  </select>
                </Td>
                <Td label="Thao tác">
                  <span className="flex flex-wrap justify-end gap-2">
                    <Chip tone={TRANG_THAI[t.status]?.tone ?? 'neutral'}>
                      {TRANG_THAI[t.status]?.nhan ?? t.status}
                    </Chip>
                    <Button size="sm" variant="ghost" onClick={() => void xoa(t)}>
                      Xoá
                    </Button>
                  </span>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </TableWrap>
      )}
    </Card>
  );
}
