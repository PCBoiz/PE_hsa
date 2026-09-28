'use client';

import { useRef, useState } from 'react';

import YeuCauDongThoiGian from '@/components/YeuCauDongThoiGian';
import { Button, Card, CardHead, Chip } from '@/components/ui';
import { ghiJson, loiBatDuoc } from '@/lib/api';
import { useDaGan } from '@/lib/daGan';
import { lucVN } from '@/lib/gioVN';
import { HD_PHU_HUYNH, HD_YEU_CAU, NHOM_LOAI, O_CHON, O_CHU, toneTrangThai, type PhuHuynhDS, type YeuCau } from '@/lib/yeuCau';

/**
 * PHỤ HUYNH GỬI YÊU CẦU qua chính link tờ báo cáo (E3 — bảng TopHSA dòng 25; anh Sơn chốt
 * 25/09: phụ huynh không có tài khoản).
 *
 * Máy chủ lấy em + lớp TỪ CHÌA, không từ biểu mẫu; danh sách chỉ gồm yêu cầu gửi qua link này,
 * kèm trả lời của trung tâm — không có ghi chú nội bộ. Trần 5 yêu cầu đang chờ mỗi link + giới
 * hạn tốc độ theo máy (`yeu_cau/views.py::PhuHuynhYeuCauView`). Không in ra giấy.
 */
export default function YeuCauPhuHuynh({ token, initial }: { token: string; initial: PhuHuynhDS }) {
  const [ds, setDs] = useState<YeuCau[]>(initial.yeuCau);
  const [loai, setLoai] = useState('');
  const [tieuDe, setTieuDe] = useState('');
  const [noiDung, setNoiDung] = useState('');
  const [sdt, setSdt] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const [bao, setBao] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const dangGui = useRef(false);
  // Khoá nút gửi tới khi React gắn xong (điện thoại phụ huynh, 4G): bấm sớm là GET mặc định.
  const daGan = useDaGan();
  const duong = `/api/public/phu-huynh/${encodeURIComponent(token)}/yeu-cau`;

  const mo = ds.filter((y) => ['moi', 'dang_xu_ly', 'da_duyet'].includes(y.trangThai)).length;
  const het = mo >= initial.tranMo;
  const nhom = NHOM_LOAI.map((n) => ({ ...n, loai: initial.loai.filter((l) => l.nhom === n.ma) }))
    .filter((n) => n.loai.length > 0);

  async function gui() {
    if (dangGui.current) return;
    if (!loai) { setErr('Chọn loại yêu cầu.'); return; }
    if (!tieuDe.trim()) { setErr('Viết một dòng tóm tắt điều anh / chị cần.'); return; }
    dangGui.current = true;
    setBusy(true);
    setErr(null);
    try {
      await ghiJson(duong, {
        method: 'POST',
        body: JSON.stringify({ loai, tieu_de: tieuDe.trim(), noi_dung: noiDung.trim() || null, du_lieu: sdt.trim() ? { sdt: sdt.trim() } : {} }),
      }, HD_YEU_CAU);
      // Tải lại cả danh sách: bản trả về của lượt tạo không kèm lịch sử.
      const moi = await ghiJson(duong, { method: 'GET' }, HD_PHU_HUYNH);
      setDs(moi.yeuCau);
      setLoai(''); setTieuDe(''); setNoiDung(''); setSdt('');
      setBao('Trung tâm đã nhận yêu cầu. Mở lại đường dẫn này để xem trả lời.');
    } catch (e) {
      setErr(loiBatDuoc(e, 'Chưa gửi được yêu cầu. Thử lại sau ít phút.'));
      setBao(null);
    } finally {
      dangGui.current = false;
      setBusy(false);
    }
  }

  return (
    <section className="mt-6 flex flex-col gap-4 print:hidden" aria-labelledby="ph-yc">
      <h2 id="ph-yc" className="text-section text-ink">Gửi yêu cầu cho trung tâm</h2>
      {err && <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">{err}</p>}
      {bao && !err && <p role="status" className="rounded-md bg-success/10 px-3 py-2 text-small text-success-ink">{bao}</p>}

      <Card>
        {het ? (
          <p className="text-body text-ink-2">
            Anh / chị đang có {mo} yêu cầu chờ trung tâm xử lý. Vui lòng đợi trung tâm trả lời trước khi gửi thêm.
          </p>
        ) : (
          <form className="flex flex-col gap-3" onSubmit={(e) => { e.preventDefault(); void gui(); }}>
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Anh / chị cần gì?</span>
              <select className={O_CHON} value={loai} onChange={(e) => setLoai(e.target.value)} required>
                <option value="">— Chọn —</option>
                {nhom.map((n) => (
                  <optgroup key={n.ma} label={n.nhan}>
                    {n.loai.map((l) => <option key={l.code} value={l.code}>{l.nhan}</option>)}
                  </optgroup>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Tóm tắt một dòng</span>
              <input className={`min-h-11 ${O_CHU}`} value={tieuDe} maxLength={200} required onChange={(e) => setTieuDe(e.target.value)} />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Nội dung (không bắt buộc)</span>
              <textarea rows={3} className={O_CHU} value={noiDung} maxLength={4000} onChange={(e) => setNoiDung(e.target.value)} />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Số điện thoại để trung tâm gọi lại (không bắt buộc)</span>
              <input type="tel" inputMode="tel" className={`min-h-11 ${O_CHU}`} value={sdt} maxLength={20} onChange={(e) => setSdt(e.target.value)} />
            </label>
            <div><Button type="submit" loading={busy} disabled={!daGan}>{busy ? 'Đang gửi…' : 'Gửi yêu cầu'}</Button></div>
          </form>
        )}
      </Card>

      {ds.length > 0 && (
        <Card>
          <CardHead title="Yêu cầu đã gửi qua đường dẫn này" hint={mo > 0 ? `${mo} yêu cầu đang chờ trung tâm.` : undefined} />
          <ul className="flex flex-col gap-4">
            {ds.map((y) => (
              <li key={y.id} className="rounded-md border border-line p-3">
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <span className="text-subhead text-ink">{y.tieuDe}</span>
                  <Chip tone={toneTrangThai(y.trangThai)}>{y.trangThaiNhan}</Chip>
                  <Chip tone="neutral">{y.loaiNhan}</Chip>
                </div>
                <p className="mt-1 text-small text-ink-3">Gửi {lucVN(y.createdAt)}</p>
                {y.ketQua && <p className="mt-2 whitespace-pre-wrap text-body text-ink">Kết quả: {y.ketQua}</p>}
                <div className="mt-3">
                  <YeuCauDongThoiGian suKien={y.suKien ?? []} />
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </section>
  );
}
