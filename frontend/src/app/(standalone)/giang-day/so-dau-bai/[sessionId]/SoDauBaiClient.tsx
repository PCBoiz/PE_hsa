'use client';

import { useRef, useState } from 'react';

import { Button, Card, CardHead, Chip, EmptyState } from '@/components/ui';
import { apiFetch, errorText, ghiJson, loiBatDuoc } from '@/lib/api';
import { HD_SO_DAU_BAI, type MucSo, type SoDauBai } from '@/lib/chuongTrinh';
import { lucVN } from '@/lib/gioVN';

/**
 * Biểu mẫu sổ đầu bài. Một lượt Lưu ghi CẢ sổ (mục, mức tiếp thu, đề xuất, em cần hỗ
 * trợ) — máy chủ thay toàn bộ sổ cũ. `phien_ban` = mốc lưu lúc mở: người khác vừa lưu
 * thì máy chủ trả 409 thay vì đè (giảng viên + trợ giảng cùng mở một buổi).
 *
 * "Tình hình lớp" là cột sẵn có của buổi (`class_sessions.note`) — lưu qua cửa sửa buổi
 * cũ, chỉ khi đã đổi.
 */
const O_CHU =
  'w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 py-2 text-input text-ink placeholder:text-ink-3/70';
const O_CHON =
  'min-h-11 w-full rounded-md border border-line-input bg-sunken px-3 text-input text-ink focus:outline-2 focus:outline-brand';

type DongMuc = { itemId: number | null; label: string; soBuoi?: number | null; status: string; note: string };

function tuMuc(m: MucSo): DongMuc {
  return { itemId: m.itemId, label: m.label, soBuoi: m.soBuoi, status: m.status ?? '', note: m.note ?? '' };
}

const MUC_DO = [
  { ma: 1, nhan: 'Rất khó theo' },
  { ma: 2, nhan: 'Khó theo' },
  { ma: 3, nhan: 'Tạm được' },
  { ma: 4, nhan: 'Hiểu tốt' },
  { ma: 5, nhan: 'Rất tốt' },
];

export default function SoDauBaiClient({ initial }: { initial: SoDauBai }) {
  const [d, setD] = useState<SoDauBai>(initial);
  const [muc, setMuc] = useState<DongMuc[]>(() => [
    ...initial.mucKeHoach.map(tuMuc),
    ...initial.mucNgoaiKeHoach.filter((m) => !m.ngoaiBan).map(tuMuc),
    ...initial.mucTuThem.map((m) => ({ itemId: null, label: m.label, status: m.status, note: m.note ?? '' })),
  ]);
  const [mucDo, setMucDo] = useState<number | null>(initial.soDauBai?.comprehension ?? null);
  const [deXuat, setDeXuat] = useState(initial.soDauBai?.deXuat ?? '');
  const [hoTro, setHoTro] = useState<Record<number, string | null>>(() => Object.fromEntries(
    initial.hocVien.filter((h) => h.canHoTro).map((h) => [h.userId, h.ghiChu ?? ''])));
  const [tinhHinh, setTinhHinh] = useState(initial.session.note ?? '');
  const [themKhac, setThemKhac] = useState<number | ''>('');
  const [tuThem, setTuThem] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const [bao, setBao] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const dangGui = useRef(false);

  const nhanTT = d.trangThaiMuc;
  const daCo = new Set(muc.map((m) => m.itemId).filter((x) => x != null));
  const conKhac = d.mucKhac.filter((m) => !daCo.has(m.itemId));
  const mocoi = d.mucNgoaiKeHoach.filter((m) => m.ngoaiBan);
  const thieu = muc.filter((m) => !m.status).length;

  function doiMuc(i: number, doi: Partial<DongMuc>) {
    setMuc((ds) => ds.map((m, j) => (j === i ? { ...m, ...doi } : m)));
  }

  async function luu() {
    if (dangGui.current) return;
    dangGui.current = true;
    setBusy(true);
    try {
      const moi = await ghiJson(`/api/teach/sessions/${d.session.id}/so-dau-bai`, {
        method: 'PUT',
        body: JSON.stringify({
          phien_ban: d.soDauBai?.loggedAt ?? null,
          items: muc.filter((m) => m.status).map((m) => ({
            item_id: m.itemId, label: m.label, status: m.status, note: m.note.trim() || null,
          })),
          comprehension: mucDo,
          de_xuat: deXuat.trim() || null,
          support: Object.entries(hoTro).map(([uid, note]) => ({ user_id: Number(uid), note: note?.trim() || null })),
        }),
      }, HD_SO_DAU_BAI);
      if (tinhHinh.trim() !== (d.session.note ?? '').trim()) {
        const r = await apiFetch(`/api/teach/sessions/${d.session.id}`, {
          method: 'PATCH', body: JSON.stringify({ note: tinhHinh.trim() || null }),
        });
        if (!r.ok) throw new Error(errorText(r.status, await r.json().catch(() => ({}))));
        moi.session.note = tinhHinh.trim() || null;
      }
      setD(moi);
      setErr(null);
      setBao(`Đã lưu sổ đầu bài lúc ${lucVN(moi.soDauBai?.loggedAt).slice(-5)}.`);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không lưu được sổ đầu bài.'));
      setBao(null);
    } finally {
      dangGui.current = false;
      setBusy(false);
    }
  }

  if (!d.ghiDuoc && !d.soDauBai) {
    return (
      <EmptyState
        title={d.session.status === 'cancelled' ? 'Buổi này đã huỷ' : 'Buổi này chưa diễn ra'}
        hint="Sổ đầu bài ghi sau khi dạy xong buổi."
      />
    );
  }

  return (
    <form className="space-y-6" onSubmit={(e) => { e.preventDefault(); void luu(); }}>
      {err && <div role="alert" className="rounded-md border border-danger bg-danger-soft px-4 py-3 text-body text-danger-ink">{err}</div>}
      {bao && !err && <p role="status" className="rounded-md bg-success/10 px-4 py-3 text-body text-success-ink">{bao}</p>}

      <Card>
        <CardHead
          title={d.buoiKhung ? `Nội dung buổi ${d.buoiKhung.soBuoi ?? ''}: ${d.buoiKhung.name}` : 'Nội dung đã dạy'}
          hint={d.lopCoKhung
            ? (d.buBuoiGoc ? `Buổi học bù cho buổi ${lucVN(d.buBuoiGoc)}.` : 'Đánh dấu từng nội dung: đã dạy, dạy một phần hay chưa dạy.')
            : 'Lớp chưa nhận khung chương trình — ghi các nội dung đã dạy ở ô bên dưới.'}
        />
        {d.buoiKhung?.homework && <p className="mb-3 text-small text-ink-2">Bài về nhà theo khung: {d.buoiKhung.homework}</p>}
        {d.lopCoKhung && !d.buoiKhung && (
          <p className="mb-3 text-small text-warning-ink">Buổi này chưa gắn với buổi nào của khung — gắn ở màn Chương trình lớp, hoặc chọn nội dung bên dưới.</p>
        )}

        {muc.length === 0 ? (
          <p className="text-body text-ink-3">Chưa có nội dung nào.</p>
        ) : (
          <ul className="space-y-3">
            {muc.map((m, i) => (
              <li key={`${m.itemId ?? 'tu'}-${i}`} className="rounded-md border border-line p-3">
                <fieldset className="m-0 min-w-0 border-0 p-0">
                  <legend className="p-0 text-body font-medium text-ink">
                    {m.label}
                    {m.soBuoi && d.buoiKhung?.soBuoi !== m.soBuoi && (
                      <span className="ml-2 text-small font-normal text-ink-3">(buổi {m.soBuoi} của khung)</span>
                    )}
                    {m.itemId == null && <span className="ml-2 text-small font-normal text-ink-3">(ngoài khung)</span>}
                  </legend>
                  <div className="mt-2 flex flex-wrap gap-2" role="radiogroup">
                    {nhanTT.map((t) => (
                      <label key={t.ma}
                        className={`inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-md border px-3 text-small ${m.status === t.ma ? 'border-brand bg-brand-soft text-brand-ink' : 'border-line text-ink-2'}`}>
                        <input type="radio" className="sr-only" name={`muc-${i}`} value={t.ma}
                          checked={m.status === t.ma} onChange={() => doiMuc(i, { status: t.ma })} />
                        {t.nhan}
                      </label>
                    ))}
                    {m.itemId == null && (
                      <Button type="button" size="sm" variant="ghost-danger" onClick={() => setMuc((ds) => ds.filter((_, j) => j !== i))}>
                        Bỏ
                      </Button>
                    )}
                  </div>
                  <label className="mt-2 block">
                    <span className="sr-only">Ghi chú cho {m.label}</span>
                    <input className={`min-h-11 ${O_CHU}`} value={m.note} maxLength={500}
                      placeholder="Ghi chú (không bắt buộc)" onChange={(e) => doiMuc(i, { note: e.target.value })} />
                  </label>
                </fieldset>
              </li>
            ))}
          </ul>
        )}

        {mocoi.length > 0 && (
          <p className="mt-3 text-small text-ink-3">
            Đã ghi trước khi lớp đổi khung: {mocoi.map((m) => m.label).join(', ')}.
          </p>
        )}

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {conKhac.length > 0 && (
            <div className="flex items-end gap-2">
              <div className="min-w-0 flex-1">
                <label htmlFor="them-khac" className="text-label text-ink-3">Thêm nội dung buổi khác (dạy bù, dạy vượt)</label>
                <select id="them-khac" className={`mt-2 ${O_CHON}`} value={themKhac}
                  onChange={(e) => setThemKhac(e.target.value ? Number(e.target.value) : '')}>
                  <option value="">— Chọn —</option>
                  {conKhac.map((m) => <option key={m.itemId} value={m.itemId}>Buổi {m.soBuoi}: {m.label}</option>)}
                </select>
              </div>
              <Button type="button" variant="ghost" disabled={!themKhac} onClick={() => {
                const m = conKhac.find((x) => x.itemId === themKhac);
                if (m) setMuc((ds) => [...ds, { itemId: m.itemId, label: m.label, soBuoi: m.soBuoi, status: '', note: '' }]);
                setThemKhac('');
              }}>Thêm</Button>
            </div>
          )}
          <div className="flex items-end gap-2">
            <div className="min-w-0 flex-1">
              <label htmlFor="tu-them" className="text-label text-ink-3">Nội dung ngoài khung</label>
              <input id="tu-them" className={`mt-2 min-h-11 ${O_CHU}`} value={tuThem} maxLength={300}
                onChange={(e) => setTuThem(e.target.value)} />
            </div>
            <Button type="button" variant="ghost" disabled={!tuThem.trim()} onClick={() => {
              setMuc((ds) => [...ds, { itemId: null, label: tuThem.trim(), status: 'done', note: '' }]);
              setTuThem('');
            }}>Thêm</Button>
          </div>
        </div>
      </Card>

      <Card>
        <CardHead title="Lớp tiếp thu thế nào" />
        <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Mức tiếp thu của lớp">
          {MUC_DO.map((m) => (
            <label key={m.ma}
              className={`inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-md border px-3 text-small ${mucDo === m.ma ? 'border-brand bg-brand-soft text-brand-ink' : 'border-line text-ink-2'}`}>
              <input type="radio" className="sr-only" name="muc-do" value={m.ma} checked={mucDo === m.ma}
                onChange={() => setMucDo(m.ma)} />
              {m.ma} · {m.nhan}
            </label>
          ))}
        </div>
        <label className="mt-4 flex flex-col gap-1">
          <span className="text-label text-ink-3">Tình hình lớp</span>
          <textarea rows={3} className={O_CHU} value={tinhHinh} maxLength={2000}
            placeholder="Lớp gặp khó ở chỗ nào, em nào vắng, việc cần nhớ…" onChange={(e) => setTinhHinh(e.target.value)} />
        </label>
        <label className="mt-4 flex flex-col gap-1">
          <span className="text-label text-ink-3">Đề xuất (học bù, điều chỉnh nội dung…)</span>
          <textarea rows={2} className={O_CHU} value={deXuat} maxLength={2000} onChange={(e) => setDeXuat(e.target.value)} />
        </label>
      </Card>

      <Card>
        <CardHead title="Em cần hỗ trợ sau buổi" hint="Chỉ người dạy lớp thấy — không in lên tờ phụ huynh." />
        {d.hocVien.length === 0 ? (
          <p className="text-body text-ink-3">Lớp chưa có học viên.</p>
        ) : (
          <ul className="space-y-2">
            {d.hocVien.map((h) => {
              const chon = h.userId in hoTro;
              return (
                <li key={h.userId} className="flex flex-wrap items-center gap-3">
                  <label className="inline-flex min-h-11 min-w-0 flex-1 basis-48 cursor-pointer items-center gap-2 text-body text-ink">
                    <input type="checkbox" className="size-5" checked={chon} onChange={() => setHoTro((o) => {
                      const n = { ...o };
                      if (chon) delete n[h.userId]; else n[h.userId] = '';
                      return n;
                    })} />
                    {h.name}
                    {h.diemDanh === 'absent' && <Chip tone="bad">vắng</Chip>}
                  </label>
                  {chon && (
                    <label className="min-w-0 flex-1 basis-64">
                      <span className="sr-only">Cần hỗ trợ gì — {h.name}</span>
                      <input className={`min-h-11 ${O_CHU}`} value={hoTro[h.userId] ?? ''} maxLength={500}
                        placeholder="Cần hỗ trợ gì" onChange={(e) => setHoTro((o) => ({ ...o, [h.userId]: e.target.value }))} />
                    </label>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </Card>

      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" loading={busy} disabled={!d.ghiDuoc}>Lưu sổ đầu bài</Button>
        {thieu > 0 && <span className="text-small text-ink-3">{thieu} nội dung chưa đánh dấu sẽ không được lưu.</span>}
        {d.soDauBai && (
          <span className="text-small text-ink-3">
            Lưu lần cuối {lucVN(d.soDauBai.loggedAt)}{d.soDauBai.loggedBy ? ` · ${d.soDauBai.loggedBy}` : ''}
          </span>
        )}
      </div>
    </form>
  );
}
