'use client';

import { useState } from 'react';
import * as z from 'zod/mini';

import { Button } from '@/components/ui';
import { apiFetch, errorText, ghiJson, loiBatDuoc } from '@/lib/api';
import { ngayVN } from '@/lib/gioVN';

import { THU, formGiaSuRong, thanGiaSu, type FormGiaSu } from './giaSu';

/**
 * TẠO NHANH LỚP GIA SƯ (mục 1.2b, 24/09/2026) — một em + một giảng viên + lịch tuần →
 * lớp + em vào lớp + buổi, MỘT lượt (`POST /api/admin/classes/gia-su`, một giao dịch).
 *
 * Luôn "Xem trước" rồi mới "Tạo": bản xem trước chạy đúng đường ghi rồi cuộn lại, nên
 * cảnh báo trùng giờ (giảng viên / em / phòng) và ngày nghỉ là cảnh báo THẬT. Sửa bất
 * kỳ ô nào là bản xem trước hết hiệu lực — tạo theo một bản xem trước cũ là tạo thứ
 * người dùng chưa nhìn thấy.
 */

type ChonNguoi = { id: number; name: string | null; email: string };
type ChonKhoa = { id: string; title: string };
type ChonDot = { id: number; name: string; code: string | null };
type Em = { id: number; name: string | null; email: string };

const O = 'min-h-11 w-full min-w-0 rounded-md border border-line bg-surface px-3 text-input text-ink placeholder:text-ink-3/70';

const HD_BUOI = z.nullable(z.looseObject({
  dem: z.looseObject({ tao: z.number(), nghi_le: z.number(), trung: z.number() }),
  buoi: z.array(z.looseObject({ ngay: z.string(), canhBao: z.nullable(z.string()), trangThai: z.string() })),
  canhBao: z.array(z.string()),
}));
const HD_XEM = z.looseObject({ name: z.string(), schedule: z.nullable(z.string()), sessions: HD_BUOI });
const HD_TAO = z.looseObject({ classId: z.number(), name: z.string(), sessions: HD_BUOI });
const HD_TIM = z.looseObject({
  users: z.array(z.looseObject({ id: z.number(), name: z.nullable(z.string()), email: z.string() })),
});

type XemTruoc = z.infer<typeof HD_XEM>;

function ngayVn(iso: string) {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

export default function TaoLopGiaSu({
  giangVien, khoaHoc, dotHoc, onDong, onXong,
}: {
  giangVien: ChonNguoi[];
  khoaHoc: ChonKhoa[];
  dotHoc: ChonDot[];
  onDong: () => void;
  onXong: (cau: string) => void;
}) {
  // Hôm nay theo giờ VN (`ngayVN`), không theo múi giờ máy — lịch mặc định bắt đầu từ đây.
  const [f, setF] = useState<FormGiaSu>(() => formGiaSuRong(ngayVN()));
  const [em, setEm] = useState<Em | null>(null);
  const [tu, setTu] = useState('');
  const [timThay, setTimThay] = useState<Em[] | null>(null);
  const [xem, setXem] = useState<XemTruoc | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [ban, setBan] = useState(false);

  // Mọi thay đổi làm bản xem trước hết hiệu lực.
  const dat = (sua: Partial<FormGiaSu>) => { setF((c) => ({ ...c, ...sua })); setXem(null); };

  async function tim() {
    const t = tu.trim();
    if (!t) return;
    setLoi(null);
    try {
      const r = await apiFetch(`/api/admin/users?role=${encodeURIComponent('Học viên')}&per_page=8&q=${encodeURIComponent(t)}`);
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      const kq = HD_TIM.safeParse(d);
      setTimThay(kq.success ? kq.data.users : []);
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Không tìm được học viên'));
    }
  }

  async function gui(dryRun: boolean) {
    const { body, loi: loiForm } = thanGiaSu(f, dryRun);
    if (loiForm) { setLoi(loiForm); return; }
    setBan(true);
    setLoi(null);
    try {
      const opts = { method: 'POST', body: JSON.stringify(body) };
      if (dryRun) {
        setXem(await ghiJson('/api/admin/classes/gia-su', opts, HD_XEM));
      } else {
        const d = await ghiJson('/api/admin/classes/gia-su', opts, HD_TAO);
        const so = d.sessions?.dem.tao ?? 0;
        onXong(`Đã tạo lớp "${d.name}"${so ? ` · ${so} buổi` : ''}.`);
      }
    } catch (e) {
      setLoi(loiBatDuoc(e, dryRun ? 'Không xem trước được' : 'Không tạo được lớp gia sư'));
    } finally {
      setBan(false);
    }
  }

  const buoiCanhBao = (xem?.sessions?.buoi ?? []).filter((b) => b.canhBao);

  return (
    <div role="group" aria-labelledby="gia-su-tieu-de" className="mb-4 rounded-md border border-line bg-sunken p-4">
      <h3 id="gia-su-tieu-de" className="mb-3 text-label text-ink">Tạo lớp gia sư</h3>

      {/* ── Học viên ───────────────────────────────────────────────── */}
      {em ? (
        <p className="mb-3 flex flex-wrap items-center gap-x-3 text-body text-ink">
          <span>Học viên: <b>{em.name || em.email}</b> <span className="text-ink-3">{em.email}</span></span>
          <button type="button" className="inline-flex min-h-11 items-center text-small text-brand-ink underline"
            onClick={() => { setEm(null); dat({ emId: null }); }}>Đổi em khác</button>
        </p>
      ) : (
        <div className="mb-3 flex flex-col gap-2">
          <form className="flex flex-wrap items-end gap-2" onSubmit={(e) => { e.preventDefault(); void tim(); }}>
            <label className="flex min-w-0 flex-[1_1_12rem] flex-col gap-1">
              <span className="text-label text-ink-3">Tìm học viên</span>
              <input value={tu} onChange={(e) => setTu(e.target.value)} className={O}
                placeholder="Tên, email hoặc số điện thoại" />
            </label>
            <Button type="submit" variant="ghost">Tìm</Button>
          </form>
          {timThay !== null && (timThay.length === 0 ? (
            <p className="text-small text-ink-3">Không thấy học viên nào khớp.</p>
          ) : (
            <ul aria-label="Kết quả tìm học viên" className="flex flex-col gap-1">
              {timThay.map((u) => (
                <li key={u.id}>
                  <button type="button"
                    className="flex min-h-11 w-full items-center justify-between gap-3 rounded-md border border-line bg-surface px-3 text-left text-body text-ink hover:border-brand"
                    onClick={() => { setEm(u); dat({ emId: u.id }); setTimThay(null); }}>
                    <span>{u.name || u.email}</span>
                    <span className="text-small text-ink-3">{u.email}</span>
                  </button>
                </li>
              ))}
            </ul>
          ))}
        </div>
      )}

      {/* ── Lớp ─────────────────────────────────────────────────────── */}
      <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,13rem),1fr))]">
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Giảng viên</span>
          <select value={f.giangVienId} onChange={(e) => dat({ giangVienId: e.target.value })} className={O}>
            <option value="">(chọn giảng viên)</option>
            {giangVien.map((g) => <option key={g.id} value={g.id}>{g.name || g.email}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Môn học</span>
          <select value={f.monHoc} onChange={(e) => dat({ monHoc: e.target.value })} className={O}>
            <option value="">(cả ba môn)</option>
            {khoaHoc.map((k) => <option key={k.id} value={k.id}>{k.title}</option>)}
          </select>
        </label>
        {dotHoc.length > 0 && (
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Đợt học</span>
            <select value={f.dotHoc} onChange={(e) => dat({ dotHoc: e.target.value })} className={O}>
              <option value="">(chưa thuộc đợt nào)</option>
              {dotHoc.map((d) => <option key={d.id} value={d.id}>{d.code ? `${d.name} (${d.code})` : d.name}</option>)}
            </select>
          </label>
        )}
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Tên lớp (không bắt buộc)</span>
          <input value={f.ten} onChange={(e) => dat({ ten: e.target.value })} className={O}
            placeholder="Tự đặt: Gia sư · tên em · giảng viên" />
        </label>
      </div>

      {/* ── Lịch tuần ───────────────────────────────────────────────── */}
      <label className="mt-3 inline-flex min-h-11 items-center gap-2 text-body text-ink">
        <input type="checkbox" checked={f.sinhBuoi} onChange={(e) => dat({ sinhBuoi: e.target.checked })}
          className="size-5 accent-brand" />
        Sinh buổi học ngay
      </label>
      {f.sinhBuoi && (
        <div className="flex flex-col gap-3">
          {/* Bỏ khung mặc định của <fieldset> (viền xám + lề trong) — ở 390 px nó bóp hàng
              thứ xuống ba dòng. Giữ fieldset/legend cho trình đọc màn hình. */}
          <fieldset className="m-0 flex min-w-0 flex-col gap-1 border-0 p-0">
            <legend className="mb-1 p-0 text-label text-ink-3">Học vào</legend>
            <div className="flex flex-wrap gap-2">
              {THU.map((t) => {
                const co = f.thu.includes(t.so);
                return (
                  <label key={t.so}
                    className={`inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center rounded-md border px-3 text-body ${
                      co ? 'border-brand bg-brand/10 text-brand-ink' : 'border-line bg-surface text-ink-2'}`}>
                    <input type="checkbox" className="sr-only" checked={co}
                      onChange={() => dat({ thu: co ? f.thu.filter((x) => x !== t.so) : [...f.thu, t.so] })} />
                    {t.nhan}
                  </label>
                );
              })}
            </div>
          </fieldset>
          <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,9rem),1fr))]">
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Giờ bắt đầu</span>
              <input type="time" value={f.gio} onChange={(e) => dat({ gio: e.target.value })} className={O} />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Số phút mỗi buổi</span>
              <input type="number" inputMode="numeric" min={1} value={f.phut}
                onChange={(e) => dat({ phut: e.target.value })} className={O} />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Từ ngày</span>
              <input type="date" value={f.tu} onChange={(e) => dat({ tu: e.target.value })} className={O} />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Đến ngày</span>
              <input type="date" value={f.den} onChange={(e) => dat({ den: e.target.value })} className={O} />
            </label>
          </div>
        </div>
      )}

      {loi && (
        <p role="alert" className="mt-3 rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">{loi}</p>
      )}

      {/* ── Xem trước ───────────────────────────────────────────────── */}
      {xem && (
        <div role="status" className="mt-3 flex flex-col gap-1 rounded-md border border-line bg-surface p-3 text-body text-ink">
          <p><b>{xem.name}</b>{xem.schedule ? ` · ${xem.schedule}` : ''}</p>
          {xem.sessions && (
            <p className="text-ink-2">
              {xem.sessions.dem.tao} buổi sẽ tạo
              {xem.sessions.dem.nghi_le ? ` · bỏ ${xem.sessions.dem.nghi_le} ngày nghỉ` : ''}
            </p>
          )}
          {(xem.sessions?.canhBao ?? []).map((c) => (
            <p key={c} className="rounded-md bg-warning/10 px-2 py-1 text-small text-warning-ink">{c}</p>
          ))}
          {buoiCanhBao.length > 0 && (
            <ul className="text-small text-ink-2">
              {buoiCanhBao.slice(0, 6).map((b) => <li key={b.ngay}>{ngayVn(b.ngay)}: {b.canhBao}</li>)}
              {buoiCanhBao.length > 6 && <li>… và {buoiCanhBao.length - 6} ngày nữa</li>}
            </ul>
          )}
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-2">
        {xem ? (
          <Button loading={ban} onClick={() => void gui(false)}>Tạo lớp gia sư</Button>
        ) : (
          <Button loading={ban} onClick={() => void gui(true)}>Xem trước</Button>
        )}
        <Button variant="ghost" onClick={onDong}>Huỷ</Button>
      </div>
    </div>
  );
}
