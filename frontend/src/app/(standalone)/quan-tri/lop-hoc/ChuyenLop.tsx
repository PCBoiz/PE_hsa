'use client';

import { useState } from 'react';
import * as z from 'zod/mini';

import { Button, Modal } from '@/components/ui';
import { apiFetch, errorText, ghiJson, loiBatDuoc } from '@/lib/api';
import { ngayVN } from '@/lib/gioVN';

import { LOAI_LOP, TRANG_THAI } from './lop';

/**
 * CHUYỂN LỚP MỘT THAO TÁC (§55, mục 1.2c — 24/09/2026).
 *
 * Trước đây "Chuyển lớp" chỉ là một LÝ DO rời lớp: cho em rời lớp A, rồi tự sang lớp B
 * xếp lại — hai thao tác rời tay, làm dở là em rơi khỏi mọi lớp. Hộp này gọi
 * `POST …/members/<em>/transfer`: rời A + vào B + nối hai lượt trong một giao dịch.
 */

type Lop = { id: number; name: string; code: string | null; classType?: string | null; status: string; termName: string | null };

const HD_LOP = z.looseObject({
  classes: z.array(z.looseObject({
    id: z.number(), name: z.string(), code: z.nullable(z.string()),
    classType: z.optional(z.nullable(z.string())), status: z.string(), termName: z.nullable(z.string()),
  })),
});
const HD_CHUYEN = z.looseObject({ ok: z.boolean(), toClassId: z.number(), warnings: z.array(z.string()) });

const O = 'min-h-11 w-full min-w-0 rounded-md border border-line bg-surface px-3 text-input text-ink placeholder:text-ink-3/70';

export default function ChuyenLop({
  em, tuLop, onDong, onXong,
}: {
  em: { userId: number; name: string };
  tuLop: { id: number; name: string };
  onDong: () => void;
  onXong: (cau: string) => void;
}) {
  const homNay = ngayVN();
  const [tu, setTu] = useState('');
  const [ds, setDs] = useState<Lop[] | null>(null);
  const [chon, setChon] = useState<Lop | null>(null);
  const [ngay, setNgay] = useState(homNay);
  const [ghiChu, setGhiChu] = useState('');
  const [loi, setLoi] = useState<string | null>(null);
  const [ban, setBan] = useState(false);

  async function tim() {
    setLoi(null);
    try {
      const r = await apiFetch(`/api/admin/classes/options?q=${encodeURIComponent(tu.trim())}`);
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      const kq = HD_LOP.safeParse(d);
      // Lớp đã huỷ không nhận em; lớp đang ở thì không phải "chuyển".
      setDs(kq.success ? kq.data.classes.filter((c) => c.id !== tuLop.id && c.status !== 'cancelled').slice(0, 12) : []);
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Không tìm được lớp'));
    }
  }

  async function chuyen() {
    if (!chon) { setLoi('Chọn lớp chuyển tới.'); return; }
    setBan(true);
    setLoi(null);
    try {
      const d = await ghiJson(
        `/api/admin/classes/${tuLop.id}/members/${em.userId}/transfer`,
        { method: 'POST', body: JSON.stringify({ to_class_id: chon.id, effective_date: ngay || null, note: ghiChu.trim() || null }) },
        HD_CHUYEN,
      );
      onXong([`Đã chuyển ${em.name} sang lớp "${chon.name}".`, ...d.warnings].join(' '));
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Không chuyển được lớp'));
    } finally {
      setBan(false);
    }
  }

  return (
    <Modal
      open
      onClose={onDong}
      title={`Chuyển ${em.name} sang lớp khác`}
      footer={
        <>
          <Button variant="ghost" onClick={onDong}>Huỷ</Button>
          <Button loading={ban} disabled={!chon} onClick={() => void chuyen()}>Chuyển lớp</Button>
        </>
      }
    >
      <div className="flex flex-col gap-3">
        <p className="text-body text-ink-2">Đang học: <b className="text-ink">{tuLop.name}</b></p>
        {chon ? (
          <p className="flex flex-wrap items-center gap-x-3 text-body text-ink">
            <span>Sang lớp: <b>{chon.name}</b></span>
            <button type="button" className="inline-flex min-h-11 items-center text-small text-brand-ink underline"
              onClick={() => setChon(null)}>Chọn lớp khác</button>
          </p>
        ) : (
          <>
            <form className="flex flex-wrap items-end gap-2" onSubmit={(e) => { e.preventDefault(); void tim(); }}>
              <label className="flex min-w-0 flex-[1_1_12rem] flex-col gap-1">
                <span className="text-label text-ink-3">Tìm lớp chuyển tới</span>
                <input value={tu} onChange={(e) => setTu(e.target.value)} className={O} placeholder="Tên hoặc mã lớp" />
              </label>
              <Button type="submit" variant="ghost">Tìm</Button>
            </form>
            {ds !== null && (ds.length === 0 ? (
              <p className="text-small text-ink-3">Không thấy lớp nào khớp.</p>
            ) : (
              <ul aria-label="Lớp tìm được" className="flex max-h-[40vh] flex-col gap-1 overflow-y-auto">
                {ds.map((c) => (
                  <li key={c.id}>
                    <button type="button" onClick={() => setChon(c)}
                      className="flex min-h-11 w-full flex-wrap items-center justify-between gap-x-3 rounded-md border border-line bg-surface px-3 py-1 text-left text-body text-ink hover:border-brand">
                      <span>{c.name}</span>
                      <span className="text-small text-ink-3">
                        {[c.classType ? LOAI_LOP[c.classType] : null, c.termName,
                          c.status !== 'active' ? (TRANG_THAI[c.status]?.nhan ?? c.status).toLowerCase() : null]
                          .filter(Boolean).join(' · ')}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            ))}
          </>
        )}
        <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,12rem),1fr))]">
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Ngày chuyển</span>
            <input type="date" value={ngay} max={homNay} onChange={(e) => setNgay(e.target.value)} className={O} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Ghi chú (không bắt buộc)</span>
            <input value={ghiChu} maxLength={500} onChange={(e) => setGhiChu(e.target.value)} className={O}
              placeholder="Ví dụ: xin đổi sang ca tối" />
          </label>
        </div>
        {loi && <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">{loi}</p>}
      </div>
    </Modal>
  );
}
