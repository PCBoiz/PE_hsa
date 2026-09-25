'use client';

import { useEffect, useId, useRef, useState } from 'react';
import * as z from 'zod/mini';

import { Button } from '@/components/ui';
import { ghiJson, layJson, loiBatDuoc } from '@/lib/api';

/* Danh sách của buổi gốc — cùng đường với sổ điểm danh (`SessionAttendanceView.get`). */
const HD_SO = z.looseObject({
  students: z.array(z.looseObject({
    userId: z.number(), name: z.nullable(z.string()), status: z.nullable(z.string()),
  })),
});
/* Phản hồi tạo buổi bù (`teaching/buoi_bu.py`). */
const HD_TAO = z.looseObject({ ok: z.boolean(), id: z.number(), warning: z.optional(z.string()) });

type Em = { userId: number; name: string | null; status: string | null };

/** `datetime-local` cần giờ MÁY dạng YYYY-MM-DDTHH:mm. */
function giaTriGio(d: Date) {
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

/**
 * "Tạo buổi bù cho buổi này" (kế hoạch v2 V-g — bảng TopHSA dòng 10).
 *
 * Chọn em học bù từ danh sách của buổi gốc: em VẮNG hoặc CÓ PHÉP được tick sẵn — đó là
 * lý do buổi bù tồn tại; người sắp lịch bỏ bớt / thêm tay. Buổi bù chỉ hiện với các em
 * ấy (lịch, sổ điểm danh, chuyên cần) và máy chủ báo chuông + thư cho đúng các em ấy.
 */
export default function TaoBuoiBu({ sessionId, tenBuoi, phutMacDinh, onXong, onHuy }: {
  sessionId: number;
  tenBuoi: string;
  phutMacDinh: number | null;
  onXong: (d: { soEm: number; warning?: string }) => void;
  onHuy: () => void;
}) {
  const id = useId();
  const [ds, setDs] = useState<Em[] | null>(null);
  const [chon, setChon] = useState<number[]>([]);
  const [batDau, setBatDau] = useState('');
  const [phut, setPhut] = useState(String(phutMacDinh ?? 90));
  const [chuDe, setChuDe] = useState('');
  const [loi, setLoi] = useState<string | null>(null);
  const [dangGui, setDangGui] = useState(false);
  const khoa = useRef(false);

  useEffect(() => {
    let song = true;
    layJson(`/api/teach/sessions/${sessionId}/attendance`, HD_SO)
      .then((d) => {
        if (!song) return;
        setDs(d.students);
        // Tick sẵn em vắng / có phép ở buổi gốc — đặt TRONG lời hứa, không phải thân effect.
        setChon(d.students.filter((s) => s.status === 'absent' || s.status === 'excused').map((s) => s.userId));
      })
      .catch((e: unknown) => { if (song) setLoi(loiBatDuoc(e, 'Không tải được danh sách lớp')); });
    return () => { song = false; };
  }, [sessionId]);

  async function tao() {
    if (khoa.current) return;
    khoa.current = true;
    setDangGui(true);
    setLoi(null);
    try {
      const d = await ghiJson(`/api/teach/sessions/${sessionId}/buoi-bu`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          starts_at: batDau,
          duration_minutes: Number(phut) || null,
          topic: chuDe.trim() || null,
          user_ids: chon,
        }),
      }, HD_TAO);
      onXong({ soEm: chon.length, warning: d.warning });
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Không tạo được buổi bù'));
    } finally {
      khoa.current = false;
      setDangGui(false);
    }
  }

  const o = 'min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink placeholder:text-ink-3/70';

  return (
    <form
      className="mt-3 flex flex-col gap-3 border-t border-line pt-3"
      onSubmit={(e) => { e.preventDefault(); void tao(); }}
    >
      <p className="text-subhead text-ink">Buổi bù cho “{tenBuoi}”</p>
      <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,12rem),1fr))]">
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Bắt đầu lúc</span>
          <input type="datetime-local" required value={batDau} className={o}
            onFocus={() => { if (!batDau) { const d = new Date(); d.setDate(d.getDate() + 1); d.setHours(19, 30, 0, 0); setBatDau(giaTriGio(d)); } }}
            onChange={(e) => setBatDau(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Thời lượng (phút)</span>
          <input type="number" inputMode="numeric" min={15} value={phut} className={o}
            onChange={(e) => setPhut(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Chủ đề (tuỳ chọn)</span>
          <input value={chuDe} maxLength={200} placeholder={`Học bù: ${tenBuoi}`} className={o}
            onChange={(e) => setChuDe(e.target.value)} />
        </label>
      </div>

      <fieldset className="flex flex-col gap-1">
        <legend className="text-label text-ink-3">Em học bù</legend>
        {ds === null && !loi && <p className="text-small text-ink-3">Đang tải danh sách lớp…</p>}
        {ds && ds.length === 0 && <p className="text-small text-ink-3">Lớp chưa có học viên nào đang học.</p>}
        {ds && ds.length > 0 && (
          <div className="grid gap-x-4 [grid-template-columns:repeat(auto-fit,minmax(min(100%,14rem),1fr))]">
            {ds.map((s) => (
              <label key={s.userId} htmlFor={`${id}-${s.userId}`} className="flex min-h-11 items-center gap-2 text-body text-ink-2">
                <input id={`${id}-${s.userId}`} type="checkbox" className="size-5 accent-brand"
                  checked={chon.includes(s.userId)}
                  onChange={(e) => setChon((c) => (e.target.checked ? [...c, s.userId] : c.filter((x) => x !== s.userId)))} />
                <span className="min-w-0 truncate">{s.name || `#${s.userId}`}</span>
                {(s.status === 'absent' || s.status === 'excused') && (
                  <span className="text-small text-warning-ink">{s.status === 'absent' ? 'vắng' : 'có phép'}</span>
                )}
              </label>
            ))}
          </div>
        )}
        <p className="text-small text-ink-3">
          Đã chọn {chon.length} em. Chỉ các em này thấy buổi bù và nhận thông báo; em khác không bị tính buổi này.
        </p>
      </fieldset>

      {loi && <p role="alert" className="text-small text-danger-ink">{loi}</p>}
      <div className="flex flex-wrap gap-2">
        <Button type="submit" loading={dangGui} disabled={!batDau || chon.length === 0}>Tạo buổi bù</Button>
        <Button type="button" variant="ghost" onClick={onHuy}>Huỷ</Button>
      </div>
    </form>
  );
}
