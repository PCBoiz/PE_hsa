'use client';

import { useState } from 'react';

import { BieuTuong } from '@/components/bieuTuong';

import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';
import { noiHoc } from '@/lib/noiHoc';

/**
 * LỚP CỦA BẠN — khối đầu tiên trên bảng điều khiển của học viên đang ở trong lớp.
 *
 * ── VÌ SAO CÓ (14/09/2026, anh Sơn chốt) ──────────────────────────────────
 *
 * Rà luồng học viên trên trình duyệt thật: lớp 1 học buổi đầu tối 15/09 với
 * link phòng, 16 buổi đã lên lịch — mà bảng điều khiển của em không có một chữ
 * nào về lớp. Người phải vào phòng lúc 19:30 là người duy nhất không thấy link.
 *
 * Ba việc: buổi tới + link phòng + hai buổi kế · chuyên cần của CHÍNH em (cùng
 * cách đếm với tờ báo cáo phụ huynh) · giảng viên, lịch, ngày thi của lớp. Và
 * khi ngày thi của lớp khác mục tiêu cá nhân: NÓI ra kèm một nút — không tự
 * đổi mục tiêu sau lưng em.
 *
 * Ở `src/` chứ không ở `dashboard.js` (tầng cũ bị chốt hãm), tự gọi API. Em
 * không ở lớp nào thì khối không dựng gì — học viên tự học vẫn có bảng điều
 * khiển sạch. Backend: `backend/teaching/lop_cua_toi.py`.
 */
type Buoi = {
  sessionId: number;
  startsAt: string | null;
  durationMinutes: number | null;
  topic: string | null;
  meetingUrl: string | null;
  /** Hình thức / phòng HIỆU LỰC của buổi (đã kế thừa lớp) — §53. */
  hinhThuc?: string | null;
  phong?: string | null;
  dangDienRa: boolean;
};

type Lop = {
  id: number;
  name: string;
  schedule: string | null;
  teacherName: string | null;
  examDate: string | null;
  mode?: string | null;
  room?: string | null;
  buoiToi: Buoi | null;
  sapToi: Buoi[];
  /** Buổi ĐÃ HUỶ trong tuần tới — nêu tên để em biết tối đó nghỉ. */
  daHuy: Buoi[];
  chuyenCan: {
    sessionsCounted: number;
    present: number;
    late: number;
    absent: number;
    excused: number;
    attendedPct: number | null;
  };
  ngayThiLech: boolean;
  /** Bài giảng viên giao mà em CHƯA nộp — xem `lop_cua_toi.py` vì sao nằm ở thẻ lớp. */
  baiTap: { chuaNop: number; hanSom: string | null };
};

export type DuLieu = { lop: Lop[]; mucTieu: { examDate: string | null } };

const THU = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];

function gio(iso: string | null) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const p = (n: number) => String(n).padStart(2, '0');
  return `${THU[d.getDay()]} ${p(d.getDate())}/${p(d.getMonth() + 1)} · ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function ngay(iso: string | null) {
  if (!iso) return '—';
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

/**
 * DỮ LIỆU NAY DO MÁY CHỦ ĐƯA XUỐNG (14/09/2026), không tự gọi trong `useEffect`.
 *
 * Trước đó khối này chỉ hiện sau khi React hydrate rồi chờ thêm một lượt mạng —
 * đo được **2,4 s**, và vì nó cao 333 px (390 px: 465) nằm TRÊN thẻ "Học tiếp"
 * nên lúc hiện ra nó đẩy cả cột xuống: CLS **0,177**, quá ngưỡng 0,1. Nhận dữ
 * liệu qua prop thì khối nằm sẵn trong HTML đầu tiên — không còn cú nhảy nào,
 * và em thấy buổi tới ngay lượt sơn đầu.
 */
export default function LopCuaToi({ dl }: { dl: DuLieu | null }) {
  const [loi, setLoi] = useState<string | null>(null);
  const [dangDoi, setDangDoi] = useState(false);
  const d = dl;

  if (!d || d.lop.length === 0) return null;

  /**
   * "Dùng ngày thi của lớp": ghi mục tiêu (em tự ghi cho mình) rồi xếp lại kế
   * hoạch — cùng hai việc nút "Xếp lại lịch" ở tab Kế hoạch làm, chỉ là em
   * không phải đi hai nơi. Xong thì tải lại trang: thẻ đếm ngược và tab Kế
   * hoạch do tầng cũ vẽ, không có cách nào bảo chúng vẽ lại từ đây.
   */
  async function dungNgayThiLop(examDate: string) {
    setDangDoi(true);
    setLoi(null);
    try {
      const r = await apiFetch('/api/hsa/goals', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exam_date: examDate }),
      });
      if (!r.ok) throw new Error(errorText(r.status, await r.json().catch(() => null)));
      const r2 = await apiFetch('/api/hsa/study-plan', { method: 'POST' });
      if (!r2.ok) throw new Error(errorText(r2.status, await r2.json().catch(() => null)));
      window.location.reload();
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Chưa đổi được ngày thi. Thử lại sau ít phút.'));
      setDangDoi(false);
    }
  }

  return (
    <>
      {d.lop.map((l) => {
        const cc = l.chuyenCan;
        const coMat = cc.present + cc.late;
        const noiLop = noiHoc(l.mode, l.room);
        /* Nơi của MỘT buổi chỉ nói ra khi KHÁC nơi của lớp — "buổi thứ Năm học
           online", "buổi này mượn phòng 305". Lặp lại "Phòng P201" ở mọi dòng là
           chữ thừa làm chìm đúng cái dòng khác thường. */
        const noiKhac = (b: Buoi) => {
          const n = noiHoc(b.hinhThuc, b.phong);
          return n && n !== noiLop ? n : null;
        };
        return (
          <section key={l.id} className="section-card fx-fade-up lct" aria-label={`Lớp ${l.name}`}>
            <div className="section-title" style={{ marginBottom: 6 }}>
              {/* `BieuTuong` chứ KHÔNG `data-icon` — xem chú thích ở
                  `HocTiepRong`: khối chảy tới sau thì tầng cũ kịp điền ô trống
                  và React phải dựng lại cả nhánh. */}
              <span className="title-icon-blue"><BieuTuong ten="users" co={16} /></span>
              <span>Lớp của bạn · {l.name}</span>
            </div>
            <p className="lct-meta">
              {l.teacherName && <>GV {l.teacherName} · </>}
              {l.schedule && <>{l.schedule} · </>}
              {noiLop && <>{noiLop} · </>}
              {l.examDate ? <>thi {ngay(l.examDate)}</> : 'chưa có ngày thi'}
            </p>

            {l.buoiToi ? (
              <div className="lct-next">
                <div className="lct-next-text">
                  <span className="lct-next-lbl">{l.buoiToi.dangDienRa ? 'Đang diễn ra' : 'Buổi tới'}</span>
                  <b className="lct-next-time">{gio(l.buoiToi.startsAt)}</b>
                  <span className="lct-next-sub">
                    {l.buoiToi.topic || 'Buổi học'}
                    {l.buoiToi.durationMinutes ? ` · ${l.buoiToi.durationMinutes} phút` : ''}
                    {noiKhac(l.buoiToi) && <b>{` · ${noiKhac(l.buoiToi)}`}</b>}
                  </span>
                </div>
                {/* Buổi TẠI TRUNG TÂM: em cần số phòng, không cần nút vào phòng
                    trực tuyến — link chung của lớp vẫn có thể nằm đó từ trước. */}
                {l.buoiToi.hinhThuc === 'offline' ? (
                  <span className="lct-nolink">
                    Học tại trung tâm{l.buoiToi.phong ? <> — phòng <b>{l.buoiToi.phong}</b></> : ''}.
                  </span>
                ) : l.buoiToi.meetingUrl ? (
                  <a className="hsa-cont-btn lct-go" href={l.buoiToi.meetingUrl} target="_blank" rel="noopener noreferrer">
                    Vào phòng học →
                  </a>
                ) : (
                  <span className="lct-nolink">Chưa có link phòng — hỏi giảng viên.</span>
                )}
              </div>
            ) : (
              <p className="hsa-mis-empty">Lớp chưa lên lịch buổi nào.</p>
            )}

            {l.sapToi.length > 1 && (
              <p className="lct-more">
                Sau đó:{' '}
                {l.sapToi
                  .slice(1)
                  .map((b) => (noiKhac(b) ? `${gio(b.startsAt)} (${noiKhac(b)})` : gio(b.startsAt)))
                  .join(' · ')}
              </p>
            )}
            {l.daHuy.length > 0 && (
              <p className="lct-more lct-huy">
                Nghỉ: {l.daHuy.map((b) => gio(b.startsAt)).join(' · ')} — buổi đã huỷ.
              </p>
            )}

            {/* Chuyên cần: cùng con số với tờ báo cáo phụ huynh. Chưa buổi nào
                được điểm danh thì nói thế, không hiện 0%. */}
            <p className="lct-cc">
              {cc.sessionsCounted === 0 ? (
                'Chưa có buổi nào được điểm danh.'
              ) : (
                <>
                  Chuyên cần: có mặt <b>{coMat}/{cc.sessionsCounted}</b> buổi
                  {cc.attendedPct != null && <> ({cc.attendedPct}%)</>}
                  {cc.absent > 0 && <> · {cc.absent} vắng</>}
                  {cc.excused > 0 && <> · {cc.excused} có phép</>}
                  {cc.late > 0 && <> · {cc.late} muộn</>}
                </>
              )}
            </p>

            {/* Bài tập chưa nộp. Ở điện thoại thanh trên không có mục Bài tập,
                nên không có dòng này thì em không biết thầy vừa giao bài. */}
            {l.baiTap?.chuaNop > 0 && (
              <p className="lct-cc lct-bt">
                <b>{l.baiTap.chuaNop}</b> bài tập chưa nộp
                {l.baiTap.hanSom && <> · hạn sớm nhất {gio(l.baiTap.hanSom)}</>}
                {' '}
                <a className="lct-link" href="/bai-tap">Làm bài →</a>
              </p>
            )}

            {l.ngayThiLech && l.examDate && (
              <div className="lct-lech" role="note">
                <span>
                  Lớp thi ngày <b>{ngay(l.examDate)}</b>, còn mục tiêu của bạn đang là{' '}
                  <b>{ngay(d.mucTieu.examDate)}</b> — thẻ đếm ngược và kế hoạch đang xếp theo ngày đó.
                </span>
                <button type="button" className="hsa-cont-btn lct-go" disabled={dangDoi} onClick={() => void dungNgayThiLop(l.examDate!)}>
                  {dangDoi ? 'Đang xếp lại…' : 'Dùng ngày thi của lớp'}
                </button>
              </div>
            )}
            {loi && <p role="alert" className="lct-loi">{loi}</p>}
          </section>
        );
      })}
    </>
  );
}
