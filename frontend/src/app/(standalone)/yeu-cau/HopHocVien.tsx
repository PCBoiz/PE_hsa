'use client';

import Link from 'next/link';
import { useRef, useState } from 'react';

import { Button, Card, CardHead, Chip, EmptyState } from '@/components/ui';
import { ghiJson, layJson, loiBatDuoc } from '@/lib/api';
import { useDaGan } from '@/lib/daGan';
import { lucVN } from '@/lib/gioVN';
import {
  HD_DS,
  HD_YEU_CAU,
  NHOM_LOAI,
  O_CHON,
  O_CHU,
  toneTrangThai,
  type LuaChonHV,
  type YeuCau,
} from '@/lib/yeuCau';

/**
 * HỎI & YÊU CẦU của học viên (E3 — bảng TopHSA dòng 32 "gửi câu hỏi cho GV/TG, yêu cầu hỗ trợ
 * học tập", dòng 12 phía người xin).
 *
 * Luật (loại nào em gửi được, lớp nào hợp lệ, trần độ dài) ở `yeu_cau/dich_vu.py::tao` —
 * biểu mẫu chỉ dẫn đường: loại cần lớp thì hỏi lớp, loại cần buổi thì hỏi buổi. Em chỉ thấy
 * yêu cầu MÌNH GỬI (máy chủ lọc), không thấy ghi chú nội bộ của trung tâm.
 */
const TRAN_TIEU_DE = 200;
const TRAN_NOI_DUNG = 4000;

export default function HopHocVien({
  initial, luaChon, loiTai,
}: { initial: YeuCau[]; luaChon: LuaChonHV | null; loiTai: string | null }) {
  const [ds, setDs] = useState<YeuCau[]>(initial);
  const [loai, setLoai] = useState('');
  const [lop, setLop] = useState<number | ''>('');
  const [buoi, setBuoi] = useState<number | ''>('');
  const [tieuDe, setTieuDe] = useState('');
  const [noiDung, setNoiDung] = useState('');
  const [mongMuon, setMongMuon] = useState('');
  const [denNgay, setDenNgay] = useState('');
  const [err, setErr] = useState<string | null>(loiTai);
  const [bao, setBao] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const dangGui = useRef(false);
  // Khoá nút gửi tới khi React gắn xong: bấm sớm hơn là trình duyệt gửi GET mặc định, mất chữ đã gõ
  // (cùng lý do với `LoginForm` — đo được ở e2e 26/09/2026 trên máy dev).
  const daGan = useDaGan();

  const dsLoai = luaChon?.loai ?? [];
  const chon = dsLoai.find((l) => l.code === loai);
  const lopDangHoc = (luaChon?.lop ?? []).filter((l) => l.dangHoc || loai === 'tt_hoc_lai');
  const buoiCuaLop = (luaChon?.buoi ?? []).filter((b) => !lop || b.classId === lop);
  const nhom = NHOM_LOAI
    .map((n) => ({ ...n, loai: dsLoai.filter((l) => l.nhom === n.ma) }))
    .filter((n) => n.loai.length > 0);

  function doiLoai(ma: string) {
    setLoai(ma);
    setBuoi('');
    // Em học đúng một lớp → chọn sẵn lớp ấy (máy chủ cũng tự gắn khi chỉ có một lớp).
    const dang = (luaChon?.lop ?? []).filter((l) => l.dangHoc);
    if (lop === '' && dang.length === 1) setLop(dang[0].id);
  }

  async function gui() {
    if (dangGui.current) return;
    if (!chon) { setErr('Chọn bạn cần gì.'); return; }
    if (!tieuDe.trim()) { setErr('Viết một dòng tóm tắt điều bạn cần.'); return; }
    if (chon.canLop && lop === '' && !chon.canBuoi) { setErr('Chọn lớp.'); return; }
    if (chon.canBuoi && buoi === '') { setErr('Chọn buổi học có bản ghi bị lỗi.'); return; }
    dangGui.current = true;
    setBusy(true);
    setErr(null);
    try {
      const duLieu: Record<string, string> = {};
      if (mongMuon.trim()) duLieu[loai === 'tt_chuyen_lop' || loai === 'tt_chuyen_mon' ? 'lop_mong_muon' : 'ngay_mong_muon'] = mongMuon.trim();
      if (denNgay) duLieu.den_ngay = denNgay;
      const moi = await ghiJson('/api/yeu-cau', {
        method: 'POST',
        body: JSON.stringify({
          loai, tieu_de: tieuDe.trim(), noi_dung: noiDung.trim() || null,
          class_id: lop === '' ? null : lop, session_id: buoi === '' ? null : buoi, du_lieu: duLieu,
        }),
      }, HD_YEU_CAU);
      setDs((cu) => [moi, ...cu.filter((y) => y.id !== moi.id)]);
      setLoai(''); setBuoi(''); setTieuDe(''); setNoiDung(''); setMongMuon(''); setDenNgay('');
      setBao(`Đã gửi “${moi.tieuDe}”. Trả lời sẽ hiện ở danh sách bên dưới và trên chuông thông báo.`);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không gửi được yêu cầu.'));
      setBao(null);
    } finally {
      dangGui.current = false;
      setBusy(false);
    }
  }

  async function taiLai() {
    try {
      setDs((await layJson('/api/yeu-cau', HD_DS)).yeuCau);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không tải lại được danh sách.'));
    }
  }

  const mo = ds.filter((y) => ['moi', 'dang_xu_ly', 'da_duyet'].includes(y.trangThai)).length;

  return (
    <div className="flex flex-col gap-5">
      {err && <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">{err}</p>}
      {bao && !err && <p role="status" className="rounded-md bg-success/10 px-3 py-2 text-small text-success-ink">{bao}</p>}

      <Card as="section">
        <CardHead title="Gửi câu hỏi hoặc yêu cầu" hint="Câu hỏi bài học tới giảng viên, trợ giảng lớp bạn. Việc khác tới học vụ." />
        {!luaChon ? (
          <p className="text-body text-ink-3">Chưa đọc được danh sách loại yêu cầu. Tải lại trang sau ít phút.</p>
        ) : (
          <form className="flex flex-col gap-4" onSubmit={(e) => { e.preventDefault(); void gui(); }}>
            <label className="flex flex-col gap-2">
              <span className="text-label text-ink-3">Bạn cần gì?</span>
              <select className={O_CHON} value={loai} onChange={(e) => doiLoai(e.target.value)} required>
                <option value="">— Chọn —</option>
                {nhom.map((n) => (
                  <optgroup key={n.ma} label={n.nhan}>
                    {n.loai.map((l) => <option key={l.code} value={l.code}>{l.nhan}</option>)}
                  </optgroup>
                ))}
              </select>
            </label>

            {chon?.canDuyet && (
              <p className="rounded-md bg-brand-soft px-3 py-2 text-small text-brand-ink">
                Học vụ xem xét và duyệt. Duyệt xong hệ thống tự làm (ví dụ chuyển bạn sang lớp mới) và báo lại cho bạn.
              </p>
            )}

            {chon && (lopDangHoc.length > 0) && (
              <label className="flex flex-col gap-2">
                <span className="text-label text-ink-3">{chon.canLop ? 'Lớp' : 'Lớp (không bắt buộc)'}</span>
                <select className={O_CHON} value={lop} onChange={(e) => { setLop(e.target.value ? Number(e.target.value) : ''); setBuoi(''); }}>
                  <option value="">{chon.canLop ? '— Chọn lớp —' : 'Không gắn lớp'}</option>
                  {lopDangHoc.map((l) => <option key={l.id} value={l.id}>{l.ten}{l.dangHoc ? '' : ' (đã học xong)'}</option>)}
                </select>
              </label>
            )}

            {chon?.canBuoi && (
              <label className="flex flex-col gap-2">
                <span className="text-label text-ink-3">Buổi học có bản ghi bị lỗi</span>
                <select className={O_CHON} value={buoi} onChange={(e) => setBuoi(e.target.value ? Number(e.target.value) : '')}>
                  <option value="">— Chọn buổi —</option>
                  {buoiCuaLop.map((b) => (
                    <option key={b.id} value={b.id}>
                      {lucVN(b.luc)}{b.chuDe ? ` · ${b.chuDe}` : ''}{b.coBanGhi ? '' : ' · chưa có bản ghi'}
                    </option>
                  ))}
                </select>
              </label>
            )}

            {(loai === 'tt_chuyen_lop' || loai === 'tt_chuyen_mon') && (
              <label className="flex flex-col gap-2">
                <span className="text-label text-ink-3">Lớp hoặc lịch bạn muốn chuyển sang</span>
                <input className={`min-h-11 ${O_CHU}`} value={mongMuon} maxLength={200} onChange={(e) => setMongMuon(e.target.value)} />
              </label>
            )}
            {(loai === 'tt_chuyen_lich' || loai === 'tt_hoc_bu' || loai === 'tt_nghi_hoc') && (
              <label className="flex flex-col gap-2">
                <span className="text-label text-ink-3">Ngày hoặc buổi mong muốn</span>
                <input className={`min-h-11 ${O_CHU}`} value={mongMuon} maxLength={100} onChange={(e) => setMongMuon(e.target.value)} />
              </label>
            )}
            {loai === 'tt_bao_luu' && (
              <label className="flex flex-col gap-2">
                <span className="text-label text-ink-3">Bảo lưu tới ngày (không bắt buộc)</span>
                <input type="date" className={`min-h-11 ${O_CHU}`} value={denNgay} onChange={(e) => setDenNgay(e.target.value)} />
              </label>
            )}

            <label className="flex flex-col gap-2">
              <span className="text-label text-ink-3">Tóm tắt một dòng</span>
              <input className={`min-h-11 ${O_CHU}`} value={tieuDe} maxLength={TRAN_TIEU_DE} required
                onChange={(e) => setTieuDe(e.target.value)} />
            </label>
            <label className="flex flex-col gap-2">
              <span className="text-label text-ink-3">Nội dung (không bắt buộc)</span>
              <textarea rows={4} className={O_CHU} value={noiDung} maxLength={TRAN_NOI_DUNG}
                onChange={(e) => setNoiDung(e.target.value)} />
            </label>
            <div>
              <Button type="submit" loading={busy} disabled={!daGan}>{busy ? 'Đang gửi…' : 'Gửi yêu cầu'}</Button>
            </div>
          </form>
        )}
      </Card>

      <Card as="section">
        <CardHead
          title="Yêu cầu bạn đã gửi"
          hint={ds.length === 0 ? undefined : mo > 0 ? `${mo} yêu cầu đang chờ trung tâm.` : 'Mọi yêu cầu đã được trả lời.'}
          action={<Button size="sm" variant="ghost" onClick={() => void taiLai()}>Tải lại</Button>}
        />
        {ds.length === 0 ? (
          <EmptyState title="Chưa có yêu cầu nào" hint="Gửi câu hỏi ở trên — trả lời của trung tâm sẽ hiện ở đây." />
        ) : (
          <ul className="flex flex-col gap-2">
            {ds.map((y) => (
              <li key={y.id}>
                <Link href={`/yeu-cau/${y.id}`}
                  className="block rounded-md border border-line bg-surface px-4 py-3 hover:border-brand focus-visible:outline-2 focus-visible:outline-brand">
                  <span className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                    <span className="text-subhead text-ink">{y.tieuDe}</span>
                    <Chip tone={toneTrangThai(y.trangThai)}>{y.trangThaiNhan}</Chip>
                    <Chip tone="neutral">{y.loaiNhan}</Chip>
                  </span>
                  <span className="mt-1 block text-small text-ink-3">
                    {y.lop?.ten ? `${y.lop.ten} · ` : ''}cập nhật {lucVN(y.updatedAt)}
                    {y.nguoiXuLy?.ten ? ` · ${y.nguoiXuLy.ten} đang xử lý` : ''}
                  </span>
                  {y.ketQua && <span className="mt-1 block text-small text-ink-2">Kết quả: {y.ketQua}</span>}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
