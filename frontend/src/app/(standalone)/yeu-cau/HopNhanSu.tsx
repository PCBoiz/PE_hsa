'use client';

import Link from 'next/link';
import { useRef, useState } from 'react';

import { Button, Card, CardHead, Chip, EmptyState, Modal } from '@/components/ui';
import { ghiJson, layJson, loiBatDuoc } from '@/lib/api';
import { lucVN } from '@/lib/gioVN';
import {
  HD_DS,
  HD_LUA_CHON_NS,
  HD_YEU_CAU,
  NHAN_NGUON,
  O_CHON,
  O_CHU,
  toneTrangThai,
  type LuaChonNS,
  type YeuCau,
} from '@/lib/yeuCau';

/**
 * HỘP YÊU CẦU của nhân sự (E3 — bảng TopHSA dòng 11, 12, 20, 21).
 *
 * Học vụ / quản trị thấy mọi yêu cầu; giảng viên, trợ giảng thấy yêu cầu của lớp mình + việc
 * giao cho mình, KHÔNG thấy hỗ trợ tài khoản (máy chủ lọc — `pham_vi_yeu_cau`). Trang chỉ đổi
 * bộ lọc rồi hỏi lại máy chủ; không lọc phạm vi ở trình duyệt.
 *
 * "Tạo yêu cầu": trợ giảng / giảng viên BÁO LÊN về một em (kể cả "em không phản hồi"), báo lỗi
 * bản ghi một buổi, hoặc xin thay đổi cho em; học vụ tạo thay em / phụ huynh gọi điện tới.
 */
type Loc = { trangThai: string; loai: string; lop: string; cuaToi: boolean };

function duongLoc(l: Loc) {
  const p = new URLSearchParams();
  if (l.trangThai === 'mo') p.set('mo', '1');
  else if (l.trangThai) p.set('trang_thai', l.trangThai);
  if (l.loai) p.set('loai', l.loai);
  if (l.lop) p.set('class_id', l.lop);
  if (l.cuaToi) p.set('cua_toi', '1');
  const s = p.toString();
  return `/api/teach/yeu-cau${s ? `?${s}` : ''}`;
}

export default function HopNhanSu({
  initial, coTheDuyet, luaChon, loiTai,
}: { initial: YeuCau[]; coTheDuyet: boolean; luaChon: LuaChonNS | null; loiTai: string | null }) {
  const [ds, setDs] = useState<YeuCau[]>(initial);
  const [loc, setLoc] = useState<Loc>({ trangThai: 'mo', loai: '', lop: '', cuaToi: false });
  const [err, setErr] = useState<string | null>(loiTai);
  const [dangTai, setDangTai] = useState(false);
  const [moTao, setMoTao] = useState(false);

  async function doiLoc(moi: Loc) {
    setLoc(moi);
    setDangTai(true);
    try {
      setDs((await layJson(duongLoc(moi), HD_DS)).yeuCau);
      setErr(null);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không tải được danh sách yêu cầu.'));
    } finally {
      setDangTai(false);
    }
  }

  const choDuyet = ds.filter((y) => y.canDuyet && (y.trangThai === 'moi' || y.trangThai === 'dang_xu_ly')).length;

  return (
    <div className="flex flex-col gap-5">
      {err && <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">{err}</p>}

      <Card as="section">
        <CardHead
          title={dangTai ? 'Đang tải…' : `${ds.length} yêu cầu`}
          hint={coTheDuyet && choDuyet > 0 ? `${choDuyet} yêu cầu thay đổi đang chờ bạn duyệt.` : undefined}
          action={luaChon && luaChon.loai.length > 0
            ? <Button size="sm" onClick={() => setMoTao(true)}>Tạo yêu cầu</Button>
            : undefined}
        />
        <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4" aria-busy={dangTai || undefined}>
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Trạng thái</span>
            <select className={O_CHON} value={loc.trangThai} onChange={(e) => void doiLoc({ ...loc, trangThai: e.target.value })}>
              <option value="mo">Đang mở</option>
              <option value="">Tất cả</option>
              {(luaChon?.trangThai ?? []).map((t) => <option key={t.code} value={t.code}>{t.nhan}</option>)}
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Loại</span>
            <select className={O_CHON} value={loc.loai} onChange={(e) => void doiLoc({ ...loc, loai: e.target.value })}>
              <option value="">Tất cả loại</option>
              {(luaChon?.tatCaLoai ?? []).map((t) => <option key={t.code} value={t.code}>{t.nhan}</option>)}
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Lớp</span>
            <select className={O_CHON} value={loc.lop} onChange={(e) => void doiLoc({ ...loc, lop: e.target.value })}>
              <option value="">Tất cả lớp</option>
              {(luaChon?.lop ?? []).map((l) => <option key={l.id} value={String(l.id)}>{l.ten}</option>)}
            </select>
          </label>
          <label className="flex min-h-11 items-center gap-2 self-end text-body text-ink-2">
            <input type="checkbox" className="size-5" checked={loc.cuaToi}
              onChange={(e) => void doiLoc({ ...loc, cuaToi: e.target.checked })} />
            Chỉ việc giao cho tôi
          </label>
        </div>

        {ds.length === 0 ? (
          <EmptyState
            title={dangTai ? 'Đang tải…' : 'Không có yêu cầu nào khớp bộ lọc'}
            hint="Học viên, phụ huynh và trợ giảng gửi yêu cầu thì chúng hiện ở đây."
          />
        ) : (
          <ul className="flex flex-col gap-2">
            {ds.map((y) => (
              <li key={y.id}>
                <Link href={`/yeu-cau/${y.id}`}
                  className="block rounded-md border border-line bg-surface px-4 py-3 hover:border-brand focus-visible:outline-2 focus-visible:outline-brand">
                  <span className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                    <span className="text-subhead text-ink">{y.tieuDe}</span>
                    <Chip tone={toneTrangThai(y.trangThai)}>{y.trangThaiNhan}</Chip>
                    <Chip tone={y.canDuyet ? 'brand' : 'neutral'}>{y.loaiNhan}</Chip>
                    {y.duLieu.khong_phan_hoi === true && <Chip tone="warn">Em không phản hồi</Chip>}
                  </span>
                  <span className="mt-1 block text-small text-ink-3">
                    {[
                      NHAN_NGUON[y.nguon] ?? null,
                      y.hocVien?.ten ?? null,
                      y.lop?.ten ?? null,
                      y.nguoiXuLy?.ten ? `xử lý: ${y.nguoiXuLy.ten}` : null,
                      `cập nhật ${lucVN(y.updatedAt)}`,
                    ].filter(Boolean).join(' · ')}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {luaChon && (
        <TaoYeuCau
          mo={moTao}
          dong={() => setMoTao(false)}
          luaChon={luaChon}
          xong={(y) => { setMoTao(false); setDs((cu) => [y, ...cu.filter((x) => x.id !== y.id)]); }}
        />
      )}
    </div>
  );
}

/** Biểu mẫu tạo — trong hộp thoại. Em + buổi của lớp tải khi chọn lớp (chỉ tên, không liên lạc). */
function TaoYeuCau({
  mo, dong, luaChon, xong,
}: { mo: boolean; dong: () => void; luaChon: LuaChonNS; xong: (y: YeuCau) => void }) {
  const [loai, setLoai] = useState(luaChon.loai[0]?.code ?? '');
  const [lop, setLop] = useState('');
  const [em, setEm] = useState('');
  const [buoi, setBuoi] = useState('');
  const [tieuDe, setTieuDe] = useState('');
  const [noiDung, setNoiDung] = useState('');
  const [khongPhanHoi, setKhongPhanHoi] = useState(false);
  const [cuaLop, setCuaLop] = useState<{ hocVien: { id: number; ten: string }[]; buoi: { id: number; luc: string; chuDe: string | null }[] }>({ hocVien: [], buoi: [] });
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const dangGui = useRef(false);
  const chon = luaChon.loai.find((l) => l.code === loai);

  async function chonLop(id: string) {
    setLop(id); setEm(''); setBuoi('');
    if (!id) { setCuaLop({ hocVien: [], buoi: [] }); return; }
    try {
      const d = await layJson(`/api/teach/yeu-cau/lua-chon?class_id=${id}`, HD_LUA_CHON_NS);
      setCuaLop({ hocVien: d.hocVien ?? [], buoi: d.buoi ?? [] });
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không tải được danh sách em của lớp.'));
    }
  }

  async function gui() {
    if (dangGui.current) return;
    if (!tieuDe.trim()) { setErr('Viết một dòng tóm tắt.'); return; }
    dangGui.current = true;
    setBusy(true);
    setErr(null);
    try {
      const y = await ghiJson('/api/teach/yeu-cau', {
        method: 'POST',
        body: JSON.stringify({
          loai, tieu_de: tieuDe.trim(), noi_dung: noiDung.trim() || null,
          class_id: lop ? Number(lop) : null, hoc_vien_id: em ? Number(em) : null,
          session_id: buoi ? Number(buoi) : null,
          du_lieu: loai === 'bao_cao_len' && khongPhanHoi ? { khong_phan_hoi: true } : {},
        }),
      }, HD_YEU_CAU);
      setTieuDe(''); setNoiDung(''); setKhongPhanHoi(false);
      xong(y);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không tạo được yêu cầu.'));
    } finally {
      dangGui.current = false;
      setBusy(false);
    }
  }

  return (
    <Modal open={mo} onClose={dong} title="Tạo yêu cầu"
      footer={(
        <>
          <Button variant="ghost" onClick={dong}>Huỷ</Button>
          <Button type="submit" form="tao-yeu-cau" loading={busy}>{busy ? 'Đang gửi…' : 'Gửi'}</Button>
        </>
      )}>
      <form id="tao-yeu-cau" className="flex flex-col gap-3" onSubmit={(e) => { e.preventDefault(); void gui(); }}>
        {err && <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">{err}</p>}
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Loại</span>
          <select className={O_CHON} value={loai} onChange={(e) => setLoai(e.target.value)}>
            {luaChon.loai.map((l) => <option key={l.code} value={l.code}>{l.nhan}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">{chon?.canLop ? 'Lớp' : 'Lớp (không bắt buộc)'}</span>
          <select className={O_CHON} value={lop} onChange={(e) => void chonLop(e.target.value)}>
            <option value="">— Chọn lớp —</option>
            {luaChon.lop.map((l) => <option key={l.id} value={String(l.id)}>{l.ten}</option>)}
          </select>
        </label>
        {lop && (
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">{chon?.canDuyet ? 'Học viên' : 'Học viên (không bắt buộc)'}</span>
            <select className={O_CHON} value={em} onChange={(e) => setEm(e.target.value)}>
              <option value="">— Chọn em —</option>
              {cuaLop.hocVien.map((h) => <option key={h.id} value={String(h.id)}>{h.ten}</option>)}
            </select>
          </label>
        )}
        {chon?.canBuoi && lop && (
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Buổi học</span>
            <select className={O_CHON} value={buoi} onChange={(e) => setBuoi(e.target.value)}>
              <option value="">— Chọn buổi —</option>
              {cuaLop.buoi.map((b) => <option key={b.id} value={String(b.id)}>{lucVN(b.luc)}{b.chuDe ? ` · ${b.chuDe}` : ''}</option>)}
            </select>
          </label>
        )}
        {loai === 'bao_cao_len' && (
          <label className="flex min-h-11 items-center gap-2 text-body text-ink-2">
            <input type="checkbox" className="size-5" checked={khongPhanHoi} onChange={(e) => setKhongPhanHoi(e.target.checked)} />
            Em không phản hồi tin nhắn / cuộc gọi
          </label>
        )}
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Tóm tắt một dòng</span>
          <input className={`min-h-11 ${O_CHU}`} value={tieuDe} maxLength={200} onChange={(e) => setTieuDe(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Nội dung</span>
          <textarea rows={4} className={O_CHU} value={noiDung} maxLength={4000} onChange={(e) => setNoiDung(e.target.value)} />
        </label>
      </form>
    </Modal>
  );
}
