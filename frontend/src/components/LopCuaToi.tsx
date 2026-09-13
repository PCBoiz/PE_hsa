'use client';

import { useEffect, useState } from 'react';

import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';

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
  dangDienRa: boolean;
};

type Lop = {
  id: number;
  name: string;
  schedule: string | null;
  teacherName: string | null;
  examDate: string | null;
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
};

type DuLieu = { lop: Lop[]; mucTieu: { examDate: string | null } };

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

export default function LopCuaToi() {
  const [d, setD] = useState<DuLieu | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [dangDoi, setDangDoi] = useState(false);

  useEffect(() => {
    let huy = false;
    // Lượt GET này đã được bắn sẵn từ HTML máy chủ trả về (`NapTruocDuLieu`),
    // trước cả khi React hydrate — lấy lại lời hứa ấy chứ không gọi lần hai.
    // Lấy MỘT lần rồi xoá, để lượt điều hướng sau đọc dữ liệu mới.
    const san = (window as unknown as { __napTruoc?: Record<string, Promise<DuLieu | null>> }).__napTruoc;
    const nguon = san?.['/api/lop-cua-toi'];
    if (nguon) delete san['/api/lop-cua-toi'];
    (nguon ?? fetch('/api/lop-cua-toi', { credentials: 'same-origin' })
      .then(async (r) => (r.ok ? ((await r.json()) as DuLieu) : null)))
      .then((kq) => { if (!huy && kq) setD(kq); })
      .catch(() => { /* khối phụ: thiếu nó thì bảng điều khiển vẫn dùng được */ });
    return () => { huy = true; };
  }, []);

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
        return (
          <section key={l.id} className="section-card fx-fade-up lct" aria-label={`Lớp ${l.name}`}>
            <div className="section-title" style={{ marginBottom: 6 }}>
              <span className="title-icon-blue" data-icon="users" data-size="16"></span>
              <span>Lớp của bạn · {l.name}</span>
            </div>
            <p className="lct-meta">
              {l.teacherName && <>GV {l.teacherName} · </>}
              {l.schedule && <>{l.schedule} · </>}
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
                  </span>
                </div>
                {l.buoiToi.meetingUrl ? (
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
                Sau đó: {l.sapToi.slice(1).map((b) => gio(b.startsAt)).join(' · ')}
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
