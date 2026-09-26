'use client';

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';

import YeuCauDongThoiGian from '@/components/YeuCauDongThoiGian';
import { Button, Card, CardHead, Chip } from '@/components/ui';
import { ghiJson, layJson, loiBatDuoc } from '@/lib/api';
import { useDaGan } from '@/lib/daGan';
import { lucVN } from '@/lib/gioVN';
import {
  HD_LOP_CHUYEN,
  HD_LUA_CHON_NS,
  HD_NGUOI_NHAN,
  HD_XEM_TRUOC,
  HD_YEU_CAU,
  NHAN_DU_LIEU,
  NHAN_NGUON,
  O_CHON,
  O_CHU,
  toneTrangThai,
  type XemTruoc,
  type YeuCau,
} from '@/lib/yeuCau';

/**
 * MỘT YÊU CẦU (E3). Nút nào hiện là do MÁY CHỦ nói (`coThe` — luật ở `yeu_cau/loai.py`,
 * `dich_vu.co_the`); trang không tự đoán ai được làm gì. Mọi lượt ghi trả về yêu cầu đã cập
 * nhật (cả lịch sử) — trang thay nguyên, không tự vá từng ô.
 *
 * Duyệt một lượt xin thay đổi: xem trước việc hệ thống SẼ làm (GET …/duyet, không ghi gì) rồi
 * mới bấm — duyệt là THỰC THI (chuyển lớp, bảo lưu…) trong một giao dịch ở máy chủ.
 */
type CheDo = null | 'xong' | 'tuChoi' | 'duyet' | 'giao' | 'phanLoai';

export default function ChiTietYeuCau({ initial, laHocVien }: { initial: YeuCau; laHocVien: boolean }) {
  const [yc, setYc] = useState<YeuCau>(initial);
  const [err, setErr] = useState<string | null>(null);
  const [bao, setBao] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const dangGui = useRef(false);
  const coThe = yc.coThe;
  // URL viết TƯỜNG MINH (không ghép từ một biến gốc): `scripts/ban_do.mjs` đếm tuyến có người gọi
  // theo chuỗi `/api/…` trong mã — ghép `${goc}/tra-loi` là ba tuyến bị báo "không ai gọi".
  const duongTraLoi = laHocVien ? `/api/yeu-cau/${yc.id}/tra-loi` : `/api/teach/yeu-cau/${yc.id}/tra-loi`;

  /** Một lượt ghi: chặn bấm đúp, đổi mặt nút, thay yêu cầu bằng bản máy chủ trả. */
  async function ghi(ten: string, duong: string, than: object | null, xong?: string) {
    if (dangGui.current) return false;
    dangGui.current = true;
    setBusy(ten);
    setErr(null);
    try {
      const moi = await ghiJson(duong, { method: 'POST', body: JSON.stringify(than ?? {}) }, HD_YEU_CAU);
      setYc(moi);
      setBao(xong ?? null);
      return true;
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không lưu được.'));
      setBao(null);
      return false;
    } finally {
      dangGui.current = false;
      setBusy(null);
    }
  }

  const duLieu = Object.entries(yc.duLieu).filter(([k]) => k in NHAN_DU_LIEU);

  return (
    <div className="flex flex-col gap-5">
      <div>
        <Link href="/yeu-cau" className="-my-3 inline-flex min-h-11 items-center text-small text-ink-3 hover:text-brand-ink">
          ← {laHocVien ? 'Hỏi & yêu cầu' : 'Hộp yêu cầu'}
        </Link>
        <h1 className="mt-1 break-words text-section text-ink">{yc.tieuDe}</h1>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <Chip tone={toneTrangThai(yc.trangThai)}>{yc.trangThaiNhan}</Chip>
          <Chip tone={yc.canDuyet ? 'brand' : 'neutral'}>{yc.loaiNhan}</Chip>
          {yc.duLieu.khong_phan_hoi === true && <Chip tone="warn">Em không phản hồi</Chip>}
        </div>
        <dl className="mt-3 grid gap-x-6 gap-y-1 text-small sm:grid-cols-2">
          <Dong nhan="Gửi">{[yc.nguoiTao?.ten, lucVN(yc.createdAt)].filter(Boolean).join(' · ')}</Dong>
          {!laHocVien && <Dong nhan="Nguồn">{NHAN_NGUON[yc.nguon] ?? '—'}</Dong>}
          {!laHocVien && yc.hocVien && <Dong nhan="Học viên">{yc.hocVien.ten ?? '—'}</Dong>}
          {yc.lop && <Dong nhan="Lớp">{yc.lop.ten ?? '—'}</Dong>}
          {yc.buoi && <Dong nhan="Buổi học">{lucVN(yc.buoi.luc)}</Dong>}
          <Dong nhan="Người xử lý">{yc.nguoiXuLy?.ten ?? (laHocVien ? 'Trung tâm' : 'Học vụ (chưa giao)')}</Dong>
          {yc.nguoiDuyet && <Dong nhan="Người duyệt">{`${yc.nguoiDuyet.ten ?? '—'} · ${lucVN(yc.duyetLuc)}`}</Dong>}
        </dl>
      </div>

      {err && <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">{err}</p>}
      {bao && !err && <p role="status" className="rounded-md bg-success/10 px-3 py-2 text-small text-success-ink">{bao}</p>}

      {(yc.noiDung || duLieu.length > 0) && (
        <Card as="section">
          <CardHead title="Nội dung" />
          {yc.noiDung && <p className="whitespace-pre-wrap break-words text-body text-ink">{yc.noiDung}</p>}
          {duLieu.length > 0 && (
            <dl className="mt-3 grid gap-x-6 gap-y-1 text-small sm:grid-cols-2">
              {duLieu.map(([k, v]) => (
                <Dong key={k} nhan={NHAN_DU_LIEU[k]}>{v === true ? 'Có' : String(v)}</Dong>
              ))}
            </dl>
          )}
        </Card>
      )}

      {yc.ketQua && (
        <Card as="section">
          <CardHead title="Kết quả" />
          <p className="whitespace-pre-wrap break-words text-body text-ink">{yc.ketQua}</p>
        </Card>
      )}

      {!laHocVien && <XuLy yc={yc} busy={busy} ghi={ghi} />}

      <Card as="section">
        <CardHead title="Trao đổi và lịch sử" hint={laHocVien ? undefined : 'Dòng tô vàng là ghi chú nội bộ — học viên, phụ huynh không thấy.'} />
        <YeuCauDongThoiGian suKien={yc.suKien ?? []} />
        {coThe.traLoi || coThe.ghiChu ? (
          <TraLoi
            laNhanSu={!laHocVien}
            ghiChuDuoc={!!coThe.ghiChu}
            traLoiDuoc={!!coThe.traLoi}
            busy={busy === 'traLoi'}
            gui={(noiDung, noiBo) => ghi('traLoi', duongTraLoi, { noi_dung: noiDung, noi_bo: noiBo },
              noiBo ? 'Đã ghi chú nội bộ.' : 'Đã gửi trả lời.')}
          />
        ) : (
          <p className="mt-3 text-small text-ink-3">Yêu cầu đã đóng — không trả lời thêm được.</p>
        )}
        {laHocVien && coThe.huy && (
          <div className="mt-4">
            <Button variant="ghost-danger" size="sm" loading={busy === 'huy'}
              onClick={() => { if (confirm('Rút yêu cầu này? Trung tâm sẽ không xử lý nữa.')) void ghi('huy', `/api/yeu-cau/${yc.id}/huy`, null, 'Đã rút yêu cầu.'); }}>
              {busy === 'huy' ? 'Đang rút…' : 'Rút yêu cầu'}
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}

function Dong({ nhan, children }: { nhan: string; children: React.ReactNode }) {
  return (
    <div className="flex min-w-0 gap-2">
      <dt className="shrink-0 text-ink-3">{nhan}:</dt>
      <dd className="m-0 min-w-0 break-words text-ink-2">{children}</dd>
    </div>
  );
}

function TraLoi({
  laNhanSu, ghiChuDuoc, traLoiDuoc, busy, gui,
}: {
  laNhanSu: boolean; ghiChuDuoc: boolean; traLoiDuoc: boolean; busy: boolean;
  gui: (noiDung: string, noiBo: boolean) => Promise<boolean>;
}) {
  const [chu, setChu] = useState('');
  // Yêu cầu đã đóng: nhân sự vẫn ghi chú nội bộ được, nhưng không trả lời ra ngoài.
  const [noiBo, setNoiBo] = useState(!traLoiDuoc);
  const daGan = useDaGan();   // bấm trước khi hydrate = GET mặc định, mất chữ đã gõ
  return (
    <form className="mt-4 flex flex-col gap-2" onSubmit={(e) => {
      e.preventDefault();
      if (!chu.trim()) return;
      void gui(chu.trim(), noiBo).then((ok) => { if (ok) setChu(''); });
    }}>
      <label className="flex flex-col gap-1">
        <span className="text-label text-ink-3">{noiBo ? 'Ghi chú nội bộ' : 'Trả lời'}</span>
        <textarea rows={3} className={`${O_CHU} ${noiBo ? 'border-warning' : ''}`} value={chu} maxLength={4000}
          onChange={(e) => setChu(e.target.value)} />
      </label>
      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" size="sm" loading={busy} disabled={!daGan || !chu.trim()}>
          {busy ? 'Đang gửi…' : noiBo ? 'Lưu ghi chú' : 'Gửi trả lời'}
        </Button>
        {laNhanSu && ghiChuDuoc && traLoiDuoc && (
          <label className="flex min-h-11 items-center gap-2 text-small text-ink-2">
            <input type="checkbox" className="size-5" checked={noiBo} onChange={(e) => setNoiBo(e.target.checked)} />
            Ghi chú nội bộ (học viên, phụ huynh không thấy)
          </label>
        )}
      </div>
    </form>
  );
}

/* ── Xử lý (nhân sự) ──────────────────────────────────────────────────────── */

function XuLy({
  yc, busy, ghi,
}: {
  yc: YeuCau; busy: string | null;
  ghi: (ten: string, duong: string, than: object | null, xong?: string) => Promise<boolean>;
}) {
  const c = yc.coThe;
  const [cheDo, setCheDo] = useState<CheDo>(null);
  const coNut = c.nhan || c.xong || c.tuChoi || c.moLai || c.duyet || c.giao || c.chuyenTiep || c.phanLoai;
  if (!coNut) return null;
  const tt = `/api/teach/yeu-cau/${yc.id}/trang-thai`;
  const doi = (m: CheDo) => setCheDo((cu) => (cu === m ? null : m));

  return (
    <Card as="section">
      <CardHead title="Xử lý" hint={yc.canDuyet ? 'Duyệt xong hệ thống tự làm việc được xin.' : undefined} />
      <div className="flex flex-wrap gap-2">
        {c.duyet && <Button size="sm" onClick={() => doi('duyet')} aria-expanded={cheDo === 'duyet'}>Duyệt…</Button>}
        {c.nhan && (
          <Button size="sm" variant="ghost" loading={busy === 'nhan'}
            onClick={() => void ghi('nhan', tt, { den: 'dang_xu_ly' }, 'Đã nhận xử lý.')}>
            {busy === 'nhan' ? 'Đang lưu…' : 'Nhận xử lý'}
          </Button>
        )}
        {c.xong && <Button size="sm" variant="ghost" onClick={() => doi('xong')} aria-expanded={cheDo === 'xong'}>Đã xong…</Button>}
        {(c.giao || c.chuyenTiep) && (
          <Button size="sm" variant="ghost" onClick={() => doi('giao')} aria-expanded={cheDo === 'giao'}>
            {c.giao ? 'Giao người xử lý…' : 'Chuyển tiếp…'}
          </Button>
        )}
        {c.phanLoai && <Button size="sm" variant="ghost" onClick={() => doi('phanLoai')} aria-expanded={cheDo === 'phanLoai'}>Đổi loại…</Button>}
        {c.tuChoi && <Button size="sm" variant="ghost-danger" onClick={() => doi('tuChoi')} aria-expanded={cheDo === 'tuChoi'}>Từ chối…</Button>}
        {c.moLai && (
          <Button size="sm" variant="ghost" loading={busy === 'moLai'}
            onClick={() => void ghi('moLai', tt, { den: 'dang_xu_ly' }, 'Đã mở lại yêu cầu.')}>
            {busy === 'moLai' ? 'Đang lưu…' : 'Mở lại'}
          </Button>
        )}
      </div>

      {cheDo === 'xong' && (
        <KetQua nhan="Kết quả (người gửi đọc được)" nut="Đánh dấu đã xong" dangLam={busy === 'xong'}
          gui={(kq) => { void ghi('xong', tt, { den: 'da_xong', ket_qua: kq }, 'Đã đóng yêu cầu.').then((ok) => { if (ok) setCheDo(null); }); }} />
      )}
      {cheDo === 'tuChoi' && (
        <KetQua nhan="Lý do từ chối (người gửi đọc được)" nut="Từ chối" nguyHiem dangLam={busy === 'tuChoi'}
          gui={(kq) => {
            void ghi('tuChoi', yc.canDuyet ? `/api/admin/yeu-cau/${yc.id}/tu-choi` : tt,
              yc.canDuyet ? { ket_qua: kq } : { den: 'tu_choi', ket_qua: kq }, 'Đã từ chối.')
              .then((ok) => { if (ok) setCheDo(null); });
          }} />
      )}
      {cheDo === 'giao' && <Giao yc={yc} busy={busy === 'giao'} ghi={ghi} xong={() => setCheDo(null)} />}
      {cheDo === 'phanLoai' && <PhanLoai yc={yc} busy={busy === 'phanLoai'} ghi={ghi} xong={() => setCheDo(null)} />}
      {cheDo === 'duyet' && <Duyet yc={yc} busy={busy === 'duyet'} ghi={ghi} xong={() => setCheDo(null)} />}
    </Card>
  );
}

function KetQua({
  nhan, nut, nguyHiem = false, dangLam, gui,
}: { nhan: string; nut: string; nguyHiem?: boolean; dangLam: boolean; gui: (kq: string | null) => void }) {
  const [chu, setChu] = useState('');
  return (
    <form className="mt-4 flex flex-col gap-2 border-t border-line pt-4" onSubmit={(e) => { e.preventDefault(); gui(chu.trim() || null); }}>
      <label className="flex flex-col gap-1">
        <span className="text-label text-ink-3">{nhan}</span>
        <textarea rows={2} className={O_CHU} value={chu} maxLength={4000} onChange={(e) => setChu(e.target.value)} />
      </label>
      <div>
        <Button type="submit" size="sm" variant={nguyHiem ? 'danger' : 'primary'} loading={dangLam}>
          {dangLam ? 'Đang lưu…' : nut}
        </Button>
      </div>
    </form>
  );
}

type PhanHanhDong = {
  yc: YeuCau; busy: boolean; xong: () => void;
  ghi: (ten: string, duong: string, than: object | null, xong?: string) => Promise<boolean>;
};

function Giao({ yc, busy, ghi, xong }: PhanHanhDong) {
  const [ds, setDs] = useState<{ id: number; ten: string; vai: string }[] | null>(null);
  const [chon, setChon] = useState('');
  const [ghiChu, setGhiChu] = useState('');
  const [loi, setLoi] = useState<string | null>(null);
  useEffect(() => {
    layJson(`/api/teach/yeu-cau/${yc.id}/nguoi-nhan`, HD_NGUOI_NHAN)
      .then((d) => setDs(d.nguoi))
      .catch((e) => setLoi(loiBatDuoc(e, 'Không tải được danh sách người nhận.')));
  }, [yc.id]);
  const duong = yc.coThe.giao ? `/api/admin/yeu-cau/${yc.id}/giao` : `/api/teach/yeu-cau/${yc.id}/chuyen-tiep`;
  return (
    <form className="mt-4 flex flex-col gap-2 border-t border-line pt-4" onSubmit={(e) => {
      e.preventDefault();
      void ghi('giao', duong, { nguoi_xu_ly_id: chon === 'hoc-vu' ? null : Number(chon), ghi_chu: ghiChu.trim() || null },
        'Đã giao người xử lý.').then((ok) => { if (ok) xong(); });
    }}>
      {loi && <p role="alert" className="text-small text-danger-ink">{loi}</p>}
      <label className="flex flex-col gap-1">
        <span className="text-label text-ink-3">Giao cho</span>
        <select className={O_CHON} value={chon} onChange={(e) => setChon(e.target.value)} required>
          <option value="">{ds ? '— Chọn người —' : 'Đang tải…'}</option>
          <option value="hoc-vu">Trả về học vụ (chưa giao ai)</option>
          {(ds ?? []).map((n) => <option key={n.id} value={String(n.id)}>{n.ten} · {n.vai}</option>)}
        </select>
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-label text-ink-3">Ghi chú cho người nhận (nội bộ)</span>
        <input className={`min-h-11 ${O_CHU}`} value={ghiChu} maxLength={4000} onChange={(e) => setGhiChu(e.target.value)} />
      </label>
      <div><Button type="submit" size="sm" loading={busy} disabled={!chon}>{busy ? 'Đang giao…' : 'Giao'}</Button></div>
    </form>
  );
}

function PhanLoai({ yc, busy, ghi, xong }: PhanHanhDong) {
  const [ds, setDs] = useState<{ code: string; nhan: string }[] | null>(null);
  const [chon, setChon] = useState(yc.loai);
  const [loi, setLoi] = useState<string | null>(null);
  useEffect(() => {
    layJson('/api/teach/yeu-cau/lua-chon', HD_LUA_CHON_NS)
      .then((d) => setDs(d.tatCaLoai.filter((l) => l.phanLoai)))
      .catch((e) => setLoi(loiBatDuoc(e, 'Không tải được danh sách loại.')));
  }, []);
  return (
    <form className="mt-4 flex flex-col gap-2 border-t border-line pt-4" onSubmit={(e) => {
      e.preventDefault();
      void ghi('phanLoai', `/api/admin/yeu-cau/${yc.id}/phan-loai`, { loai: chon }, 'Đã đổi loại.')
        .then((ok) => { if (ok) xong(); });
    }}>
      {loi && <p role="alert" className="text-small text-danger-ink">{loi}</p>}
      <label className="flex flex-col gap-1">
        <span className="text-label text-ink-3">Loại đúng của yêu cầu</span>
        <select className={O_CHON} value={chon} onChange={(e) => setChon(e.target.value)}>
          {(ds ?? [{ code: yc.loai, nhan: yc.loaiNhan }]).map((l) => <option key={l.code} value={l.code}>{l.nhan}</option>)}
        </select>
      </label>
      <p className="text-small text-ink-3">Đổi sang “Hỗ trợ tài khoản” thì giảng viên, trợ giảng thôi thấy yêu cầu này.</p>
      <div><Button type="submit" size="sm" loading={busy} disabled={chon === yc.loai}>{busy ? 'Đang lưu…' : 'Đổi loại'}</Button></div>
    </form>
  );
}

function Duyet({ yc, busy, ghi, xong }: PhanHanhDong) {
  const canLop = yc.loai === 'tt_chuyen_lop' || yc.loai === 'tt_chuyen_mon';
  const canNgay = yc.loai === 'tt_bao_luu';
  const [lopDs, setLopDs] = useState<{ id: number; ten: string; giaSu: boolean; mon: string | null }[] | null>(null);
  const [denLop, setDenLop] = useState(typeof yc.duLieu.den_lop_id === 'number' ? String(yc.duLieu.den_lop_id) : '');
  const [denNgay, setDenNgay] = useState(typeof yc.duLieu.den_ngay === 'string' ? yc.duLieu.den_ngay : '');
  const [ketQua, setKetQua] = useState('');
  const [xt, setXt] = useState<XemTruoc | null>(null);
  const [loi, setLoi] = useState<string | null>(null);

  useEffect(() => {
    if (!canLop) return;
    layJson(`/api/admin/yeu-cau/${yc.id}/lop`, HD_LOP_CHUYEN)
      .then((d) => setLopDs(d.lop.filter((l) => l.id !== yc.lop?.id)))
      .catch((e) => setLoi(loiBatDuoc(e, 'Không tải được danh sách lớp.')));
  }, [canLop, yc.id, yc.lop?.id]);

  // Xem trước mỗi lần đổi tham số — GET, máy chủ không ghi gì.
  const choLop = canLop && !denLop;
  useEffect(() => {
    if (choLop) return;
    const p = new URLSearchParams();
    if (denLop) p.set('den_lop_id', denLop);
    if (denNgay) p.set('den_ngay', denNgay);
    let bo = false;
    layJson(`/api/admin/yeu-cau/${yc.id}/duyet?${p}`, HD_XEM_TRUOC)
      .then((d) => { if (!bo) setXt(d); })
      .catch((e) => { if (!bo) setLoi(loiBatDuoc(e, 'Không xem trước được.')); });
    return () => { bo = true; };
  }, [choLop, denLop, denNgay, yc.id]);

  return (
    <form className="mt-4 flex flex-col gap-3 border-t border-line pt-4" onSubmit={(e) => {
      e.preventDefault();
      void ghi('duyet', `/api/admin/yeu-cau/${yc.id}/duyet`, {
        den_lop_id: denLop ? Number(denLop) : null, den_ngay: denNgay || null, ket_qua: ketQua.trim() || null,
      }, 'Đã duyệt.').then((ok) => { if (ok) xong(); });
    }}>
      {loi && <p role="alert" className="text-small text-danger-ink">{loi}</p>}
      {canLop && (
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Chuyển tới lớp</span>
          <select className={O_CHON} value={denLop} onChange={(e) => setDenLop(e.target.value)} required>
            <option value="">{lopDs ? '— Chọn lớp —' : 'Đang tải…'}</option>
            {(lopDs ?? []).map((l) => (
              <option key={l.id} value={String(l.id)}>{l.ten}{l.mon ? ` · ${l.mon}` : ''}{l.giaSu ? ' · gia sư' : ''}</option>
            ))}
          </select>
        </label>
      )}
      {canNgay && (
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Bảo lưu tới ngày (không bắt buộc)</span>
          <input type="date" className={`min-h-11 ${O_CHU}`} value={denNgay} onChange={(e) => setDenNgay(e.target.value)} />
        </label>
      )}
      {xt && !choLop && (
        <div className="rounded-md bg-sunken px-3 py-2 text-small" aria-live="polite">
          <p className="text-ink">{xt.cach === 'tay' ? '' : 'Hệ thống sẽ: '}{xt.moTa ?? 'Chưa làm được — xem cảnh báo bên dưới.'}</p>
          {xt.canhBao.map((c) => <p key={c} className="mt-1 text-warning-ink">{c}</p>)}
        </div>
      )}
      <label className="flex flex-col gap-1">
        <span className="text-label text-ink-3">Lời nhắn cho người gửi (không bắt buộc)</span>
        <input className={`min-h-11 ${O_CHU}`} value={ketQua} maxLength={4000} onChange={(e) => setKetQua(e.target.value)} />
      </label>
      <div>
        <Button type="submit" size="sm" loading={busy} disabled={canLop && !denLop}>
          {busy ? 'Đang duyệt…' : 'Duyệt và thực hiện'}
        </Button>
      </div>
    </form>
  );
}
