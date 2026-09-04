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

import { type Form, type LopRow, formRong, formTuLop, thanForm } from './lop';

export type { LopRow };
export type ChonNguoi = { id: number; name: string | null; email: string };
export type ChonKhoa = { id: string; title: string };
type ChonDot = { id: number; name: string; code: string | null };

type HocVien = {
  userId: number;
  name: string;
  email: string;
  lessonsDone?: number;
  lessonsTotal?: number;
  left?: boolean;
};

const TRANG_THAI: Record<string, { nhan: string; tone: 'good' | 'neutral' | 'bad' }> = {
  draft: { nhan: 'Bản nháp', tone: 'neutral' },
  active: { nhan: 'Đang học', tone: 'good' },
  finished: { nhan: 'Đã kết thúc', tone: 'neutral' },
};

/**
 * Lý do rời lớp — `teaching/vocab.py::LEAVE_REASONS`.
 *
 * Bản cũ KHÔNG hỏi lý do, luôn gửi `DELETE ?user_id=` trần, nên mọi lượt rời
 * lớp vào CSDL với `leave_reason = NULL`. Backend nói rõ trong chú thích của nó
 * vì sao chuyện đó tệ: "học xong" và "bỏ giữa chừng" là HAI con số khác nhau khi
 * trung tâm báo tỉ lệ bỏ học của một đợt, và gộp lại thì mọi lớp kết thúc đều
 * trông như bỏ học 100%. Backend đã sẵn sàng nhận lý do từ 31/08; chỉ thiếu chỗ
 * để người dùng nói ra.
 */
const LY_DO: { ma: string; nhan: string }[] = [
  { ma: 'completed', nhan: 'Học xong' },
  { ma: 'dropped', nhan: 'Bỏ giữa chừng' },
  { ma: 'transferred', nhan: 'Chuyển lớp' },
];

function ngay(iso: string | null) {
  if (!iso) return '—';
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

const O_CHUNG =
  'min-h-11 w-full min-w-0 rounded-md border border-line bg-surface px-3 text-input text-ink placeholder:text-ink-3/70';

export default function LopHocClient({
  initial,
  giangVien,
  trangThai,
  dotHoc,
  khoaHoc,
  loi,
}: {
  initial: LopRow[];
  giangVien: ChonNguoi[];
  trangThai: string[];
  dotHoc: ChonDot[];
  khoaHoc: ChonKhoa[];
  loi: string | null;
}) {
  const [lop, setLop] = useState<LopRow[]>(initial);
  const [err, setErr] = useState<string | null>(loi);
  const [busy, setBusy] = useState(false);

  /** `null` = biểu mẫu đóng; `0` = thêm mới; `>0` = đang sửa lớp id ấy. */
  const [dangSua, setDangSua] = useState<number | null>(null);
  const [form, setForm] = useState<Form>(formRong);

  const [lopMoRong, setLopMoRong] = useState<LopRow | null>(null);
  const [hocVien, setHocVien] = useState<HocVien[] | null>(null);
  const [emailMoi, setEmailMoi] = useState('');

  // `setBusy` của React không có tác dụng NGAY, nên hai cú bấm liền nhau đều
  // lọt qua `if (busy) return`. Với nút "Lưu" của một biểu mẫu tạo lớp thì đó
  // là hai lớp trùng tên trong CSDL. `useRef` đổi giá trị đồng bộ nên chặn thật.
  const dangGui = useRef(false);

  const dat = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  async function nap() {
    try {
      const r = await apiFetch('/api/admin/classes');
      if (r.ok) setLop(((await r.json()).classes as LopRow[]) ?? []);
    } catch {
      /* giữ nguyên danh sách đang hiện */
    }
  }

  async function luu() {
    if (dangGui.current) return;
    dangGui.current = true;
    setBusy(true);
    setErr(null);
    try {
      const moi = dangSua === 0;
      const r = await apiFetch(moi ? '/api/admin/classes' : `/api/admin/classes/${dangSua}`, {
        method: moi ? 'POST' : 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(thanForm(form)),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      setDangSua(null);
      setForm(formRong());
      await nap();
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không lưu được lớp'));
    } finally {
      dangGui.current = false;
      setBusy(false);
    }
  }

  async function xoa(c: LopRow) {
    // Hỏi TRƯỚC khi gửi, và nói rõ cái gì mất cái gì không: người đang đọc câu
    // này sợ mất dữ liệu học tập của học viên. Dữ liệu ấy KHÔNG mất — nó nằm ở
    // `learning_events`/`lesson_progress`, gắn với tài khoản chứ không gắn với
    // lớp. Cái mất là danh sách lớp và điểm danh của lớp.
    if (
      !confirm(
        `Xoá lớp "${c.name}"?\n\n` +
          `Danh sách ${c.members} học viên của lớp và toàn bộ điểm danh của lớp này sẽ mất.\n` +
          'Tiến độ học của từng em thì KHÔNG mất — nó gắn với tài khoản, không gắn với lớp.',
      )
    )
      return;
    setErr(null);
    try {
      const r = await apiFetch(`/api/admin/classes/${c.id}`, { method: 'DELETE' });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      if (lopMoRong?.id === c.id) {
        setLopMoRong(null);
        setHocVien(null);
      }
      await nap();
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không xoá được lớp'));
    }
  }

  async function moHocVien(c: LopRow) {
    setLopMoRong(c);
    // `null` = đang tải. Báo cáo lớp tính tiến độ từng em nên mất vài giây;
    // không có dòng chờ thì người dùng tưởng nút hỏng và bấm lại.
    setHocVien(null);
    setErr(null);
    try {
      const r = await apiFetch(`/api/teach/classes/${c.id}`);
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      setHocVien((d.students as HocVien[]) ?? []);
    } catch (e) {
      setHocVien([]);
      setErr(loiBatDuoc(e, 'Không tải được danh sách học viên'));
    }
  }

  async function themHocVien() {
    if (!lopMoRong || dangGui.current) return;
    const email = emailMoi.trim();
    if (!email) return;
    dangGui.current = true;
    setErr(null);
    try {
      const r = await apiFetch(`/api/admin/classes/${lopMoRong.id}/members`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      setEmailMoi('');
      await Promise.all([moHocVien(lopMoRong), nap()]);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không thêm được học viên'));
    } finally {
      dangGui.current = false;
    }
  }

  async function choRoiLop(s: HocVien, lyDo: string) {
    if (!lopMoRong) return;
    setErr(null);
    try {
      const r = await apiFetch(
        `/api/admin/classes/${lopMoRong.id}/members?user_id=${s.userId}&leave_reason=${lyDo}`,
        { method: 'DELETE' },
      );
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      await Promise.all([moHocVien(lopMoRong), nap()]);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không cập nhật được'));
    }
  }

  const oChu = (k: string, nhan: string, goi?: string) => (
    <label className="flex flex-col gap-1">
      <span className="text-label text-ink-3">{nhan}</span>
      <input
        value={form[k] ?? ''}
        onChange={(e) => dat(k, e.target.value)}
        placeholder={goi}
        className={O_CHUNG}
      />
    </label>
  );

  const oNgay = (k: string, nhan: string) => (
    <label className="flex flex-col gap-1">
      <span className="text-label text-ink-3">{nhan}</span>
      <input
        type="date"
        value={form[k] ?? ''}
        onChange={(e) => dat(k, e.target.value)}
        className={O_CHUNG}
      />
    </label>
  );

  const oChon = (k: string, nhan: string, muc: { gt: string; nhan: string }[]) => (
    <label className="flex flex-col gap-1">
      <span className="text-label text-ink-3">{nhan}</span>
      <select
        value={form[k] ?? ''}
        onChange={(e) => dat(k, e.target.value)}
        className={O_CHUNG}
      >
        {muc.map((m) => (
          <option key={m.gt} value={m.gt}>
            {m.nhan}
          </option>
        ))}
      </select>
    </label>
  );

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHead
          title="Lớp học"
          hint="Xếp học viên vào lớp. Không có bước này thì khu Giảng dạy — điểm danh, giao bài, báo cáo phụ huynh — không có gì để hiện."
          action={
            dangSua === null && (
              <Button
                onClick={() => {
                  setForm(formRong());
                  setDangSua(0);
                }}
              >
                Thêm lớp
              </Button>
            )
          }
        />

        {err && (
          <p
            role="alert"
            className="mb-3 rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink"
          >
            {err}
          </p>
        )}

        {dangSua !== null && (
          <div className="mb-4 rounded-md border border-line bg-sunken p-4">
            <h3 className="mb-3 text-label text-ink">
              {dangSua === 0 ? 'Thêm lớp' : `Sửa lớp: ${form.name || '(chưa đặt tên)'}`}
            </h3>
            <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr))]">
              {oChu('name', 'Tên lớp', 'Luyện HSA đợt 1/2027 — Ca tối')}
              {oChu('code', 'Mã lớp (không bắt buộc)', 'HSA-01')}
              {oChon('course', 'Hợp phần', [
                { gt: '', nhan: '(cả ba hợp phần)' },
                ...khoaHoc.map((k) => ({ gt: k.id, nhan: k.title })),
              ])}
              {oChon('teacherId', 'Giảng viên', [
                { gt: '', nhan: '(chưa gán)' },
                ...giangVien.map((g) => ({ gt: String(g.id), nhan: g.name || g.email })),
              ])}
              {oChon('termId', 'Đợt học', [
                { gt: '', nhan: '(chưa thuộc đợt nào)' },
                ...dotHoc.map((d) => ({
                  gt: String(d.id),
                  nhan: d.code ? `${d.name} (${d.code})` : d.name,
                })),
              ])}
              {oChon(
                'status',
                'Trạng thái',
                trangThai.map((s) => ({ gt: s, nhan: TRANG_THAI[s]?.nhan ?? s })),
              )}
              {oChu('schedule', 'Lịch học', 'T3–T5 19:30')}
              {oChu('capacity', 'Sĩ số tối đa', '30')}
              {oNgay('startsOn', 'Khai giảng')}
              {oNgay('endsOn', 'Kết thúc')}
              {oNgay('examDate', 'Ngày thi')}
              {oChu('meetingUrl', 'Link họp', 'https://meet.google.com/...')}
              {oChu('note', 'Ghi chú')}
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button loading={busy} disabled={!(form.name ?? '').trim()} onClick={() => void luu()}>
                {dangSua === 0 ? 'Tạo lớp' : 'Lưu thay đổi'}
              </Button>
              <Button variant="ghost" onClick={() => setDangSua(null)}>
                Huỷ
              </Button>
            </div>
          </div>
        )}

        {lop.length === 0 ? (
          <EmptyState
            title="Chưa có lớp nào"
            hint="Tạo lớp đầu tiên, rồi bấm “Học viên” để xếp các em vào."
          />
        ) : (
          <TableWrap caption="Các lớp của trung tâm, kèm giảng viên phụ trách và sĩ số hiện tại">
            <Thead>
              <tr>
                <Th>Lớp</Th>
                <Th>Hợp phần</Th>
                <Th>Giảng viên</Th>
                <Th>Lịch</Th>
                <Th align="right">Sĩ số</Th>
                <Th>Trạng thái</Th>
                <Th align="right">Thao tác</Th>
              </tr>
            </Thead>
            <Tbody>
              {lop.map((c) => (
                <Tr key={c.id} dim={c.status === 'finished'}>
                  <Td label="Lớp">
                    <span className="font-semibold text-ink">{c.name}</span>
                    <span className="block text-ink-3">
                      {[c.code, c.termName].filter(Boolean).join(' · ') || '—'}
                    </span>
                  </Td>
                  <Td label="Hợp phần" muted>
                    {c.courseTitle ?? 'Cả ba'}
                  </Td>
                  <Td label="Giảng viên" muted>
                    {c.teacherName ?? '(chưa gán)'}
                  </Td>
                  <Td label="Lịch" muted>
                    {c.schedule || '—'}
                    {c.startsOn && <span className="block text-ink-3">từ {ngay(c.startsOn)}</span>}
                  </Td>
                  <Td label="Sĩ số" num>
                    {c.members}
                    {c.capacity ? `/${c.capacity}` : ''}
                  </Td>
                  <Td label="Trạng thái">
                    <Chip tone={TRANG_THAI[c.status]?.tone ?? 'neutral'}>
                      {TRANG_THAI[c.status]?.nhan ?? c.status}
                    </Chip>
                  </Td>
                  <Td label="Thao tác">
                    <span className="flex flex-wrap justify-end gap-2">
                      <Button size="sm" variant="ghost" onClick={() => void moHocVien(c)}>
                        Học viên
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          // Đổ ĐỦ mọi trường. Bản cũ đổ 7/11 rồi gửi cả 11, nên
                          // sửa tên lớp là xoá trắng link họp và ghi chú.
                          setForm(formTuLop(c));
                          setDangSua(c.id);
                        }}
                      >
                        Sửa
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => void xoa(c)}>
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

      {lopMoRong && (
        <Card>
          <CardHead
            title={`Học viên lớp: ${lopMoRong.name}`}
            hint="Rời lớp KHÔNG xoá dữ liệu học tập — em vẫn còn trong báo cáo của đợt đó, kèm lý do rời."
            action={
              <Button
                variant="ghost"
                onClick={() => {
                  setLopMoRong(null);
                  setHocVien(null);
                }}
              >
                Đóng
              </Button>
            }
          />

          <div className="mb-4 flex flex-wrap items-end gap-2">
            <label className="flex min-w-60 flex-1 flex-col gap-1">
              <span className="text-label text-ink-3">Email học viên</span>
              <input
                value={emailMoi}
                type="email"
                autoComplete="off"
                onChange={(e) => setEmailMoi(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') void themHocVien();
                }}
                placeholder="hocvien@example.com"
                className={O_CHUNG}
              />
            </label>
            <Button disabled={!emailMoi.trim()} onClick={() => void themHocVien()}>
              Thêm vào lớp
            </Button>
          </div>

          {hocVien === null ? (
            <p className="text-small text-ink-3">Đang tải danh sách học viên…</p>
          ) : hocVien.length === 0 ? (
            <EmptyState
              title="Lớp chưa có học viên"
              hint="Nhập email của em rồi bấm “Thêm vào lớp”. Tài khoản phải có sẵn — trang Tài khoản là nơi tạo."
            />
          ) : (
            <TableWrap caption={`Học viên của lớp ${lopMoRong.name}`}>
              <Thead>
                <tr>
                  <Th>Học viên</Th>
                  <Th>Email</Th>
                  <Th align="right">Bài đã học</Th>
                  <Th>Tình trạng</Th>
                  <Th align="right">Cho rời lớp</Th>
                </tr>
              </Thead>
              <Tbody>
                {hocVien.map((s) => (
                  <Tr key={s.userId} dim={s.left}>
                    <Td label="Học viên">{s.name}</Td>
                    <Td label="Email" muted>
                      {s.email}
                    </Td>
                    <Td label="Bài đã học" num>
                      {s.lessonsDone ?? 0}/{s.lessonsTotal ?? 0}
                    </Td>
                    <Td label="Tình trạng">
                      <Chip tone={s.left ? 'neutral' : 'good'}>
                        {s.left ? 'đã rời lớp' : 'đang học'}
                      </Chip>
                    </Td>
                    <Td label="Cho rời lớp">
                      {/* Bắt CHỌN LÝ DO chứ không có nút "rời lớp" trần: xem
                          chú thích ở `LY_DO`. Ô về lại "—" sau mỗi lần chọn nên
                          nó không bao giờ trông như một trạng thái đang lưu. */}
                      <select
                        value=""
                        disabled={s.left}
                        aria-label={`Cho ${s.name} rời lớp, kèm lý do`}
                        onChange={(e) => {
                          const ly = e.target.value;
                          e.currentTarget.value = '';
                          if (!ly) return;
                          const nhan = LY_DO.find((l) => l.ma === ly)?.nhan ?? ly;
                          if (
                            !confirm(
                              `Cho "${s.name}" rời lớp với lý do "${nhan}"?\n\n` +
                                'Dữ liệu học tập của em vẫn giữ nguyên.',
                            )
                          )
                            return;
                          void choRoiLop(s, ly);
                        }}
                        className="min-h-11 max-w-full min-w-0 rounded-md border border-line-input bg-sunken px-2 text-small text-ink"
                      >
                        <option value="">— chọn lý do —</option>
                        {LY_DO.map((l) => (
                          <option key={l.ma} value={l.ma}>
                            {l.nhan}
                          </option>
                        ))}
                      </select>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </TableWrap>
          )}
        </Card>
      )}
    </div>
  );
}
