'use client';

import { useState } from 'react';

import { BieuTuong } from '@/components/bieuTuong';
import ThemVaoLich from '@/components/ThemVaoLich';

import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';
import { lucVN } from '@/lib/gioVN';
import { tenMien } from '@/lib/hocLieu';
import { noiHoc } from '@/lib/noiHoc';
import { cauTienDoEm } from '@/lib/tienDoChu';

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

/** Bản ghi một buổi ĐÃ HỌC (§72). `daMo` = em đã bấm mở, không phải đã xem hết. */
type BanGhi = {
  sessionId: number;
  startsAt: string | null;
  topic: string | null;
  recordingUrl: string;
  daMo: boolean;
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
  /** Điểm danh TỪNG buổi đã diễn ra, mới nhất trước (V-d, 25/09/2026). `?`: máy chủ cũ không trả. */
  diemDanh?: DongDiemDanh[];
  /** % chương trình của em (E1). null: lớp chưa nhận khung; thiếu: máy chủ cũ. */
  chuongTrinh?: { pct: number | null; keHoachPct: number | null } | null;
  /** Buổi đã học có bản ghi để xem lại (§72). `?`: máy chủ cũ không trả. */
  banGhiGanDay?: BanGhi[];
  /** Tài liệu giảng viên đã mở cho em (§60). `?`: máy chủ cũ không trả. */
  hocLieuGanDay?: TaiLieuNgan[];
};

/** Một tài liệu trên thẻ lớp. Bản gọn của `lib/hocLieu.ts::TaiLieu` — thẻ lớp chỉ cần
    đủ để bấm mở, phần mô tả và người gắn nằm ở trang tài liệu của lớp. */
type TaiLieuNgan = {
  id: number;
  ten: string;
  url: string | null;
  /** 'link' = địa chỉ ngoài. 'r2' = tệp tải lên (chờ khoá R2 của anh Sơn, chưa dựng). */
  nguon: string;
  sessionId: number | null;
  luc: string | null;
};

type DongDiemDanh = {
  sessionId: number;
  startsAt: string | null;
  topic: string | null;
  /** false = giảng viên chưa mở sổ buổi ấy — KHÔNG phải em vắng. */
  daDiemDanh: boolean;
  trangThai: string | null;
};

/** Nhãn + màu chữ của trạng thái — cùng bốn trạng thái với sổ điểm danh của giảng viên. */
const TRANG_THAI_DD: Record<string, { nhan: string; mau: string }> = {
  present: { nhan: 'Có mặt', mau: 'text-success-ink' },
  late: { nhan: 'Muộn', mau: 'text-warning-ink' },
  absent: { nhan: 'Vắng', mau: 'text-danger-ink' },
  excused: { nhan: 'Có phép', mau: 'text-brand-ink' },
};

function nhanDiemDanh(b: DongDiemDanh) {
  if (!b.daDiemDanh) return { nhan: 'Chưa điểm danh', mau: 'text-ink-3' };
  return b.trangThai ? (TRANG_THAI_DD[b.trangThai] ?? { nhan: b.trangThai, mau: 'text-ink-2' })
    : { nhan: 'Không có trong sổ', mau: 'text-ink-3' };
}

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
 * "24/09" — ngày ngắn từ một MỐC THỜI GIAN đầy đủ.
 *
 * `ngay()` ở trên chỉ ăn được chuỗi `YYYY-MM-DD` (ngày thi). Đưa cho nó
 * `2026-09-24T19:30:00` thì nó cắt theo dấu `-` và nhả ra `24T19:30:00/09/2026`
 * — đúng thứ hiện trên màn thật lúc 10:5x ngày 26/09, trước khi có hàm này.
 */
function ngayNgan(iso: string | null) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const p = (n: number) => String(n).padStart(2, '0');
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}`;
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
/**
 * Một bản ghi để em bấm mở. Mở link ở tab mới, đồng thời báo cho máy chủ là em
 * đã mở — để trợ giảng biết ai chưa xem lại mà nhắc (§72).
 *
 * Việc báo chạy NGẦM và không chặn đường đi: máy chủ lỗi thì em vẫn mở được
 * bản ghi. Thống kê hỏng còn hơn em không xem lại được bài.
 */
function NutBanGhi({ b, onMo }: { b: BanGhi; onMo: () => void }) {
  const [daMo, setDaMo] = useState(b.daMo);
  return (
    <a
      className={`lct-link lct-bg-nut${daMo ? ' lct-bg-da' : ''}`}
      href={b.recordingUrl}
      target="_blank"
      rel="noopener noreferrer"
      title={b.topic ?? undefined}
      onClick={() => {
        setDaMo(true);
        onMo();
        void apiFetch(`/api/sessions/${b.sessionId}/ban-ghi/da-mo`, { method: 'POST' })
          .catch(() => {});
      }}
    >
      {ngayNgan(b.startsAt)}
      {daMo && <span className="lct-bg-dau" aria-label="bạn đã mở"> ✓</span>}
    </a>
  );
}

/**
 * Một tài liệu trên thẻ lớp (§60).
 *
 * Mở ra TAB MỚI kèm `rel="noopener noreferrer"`: đường dẫn do giảng viên dán vào, trỏ ra
 * ngoài TopHSA. Thiếu `noopener` thì trang đích với tới được `window.opener` và đổi được
 * địa chỉ tab gốc — cách dựng một màn đăng nhập giả mà người dùng không thấy gì bất thường.
 *
 * Tên miền hiện cạnh tên tài liệu vì người bấm nên biết mình sắp đi đâu TRƯỚC khi bấm.
 */
function NutTaiLieu({ t }: { t: TaiLieuNgan }) {
  const mien = tenMien(t.url);
  return (
    <a
      className="lct-link lct-hl-nut"
      href={t.url ?? undefined}
      target="_blank"
      rel="noopener noreferrer"
      title={mien ? `${t.ten} — mở ở ${mien}` : t.ten}
    >
      {t.ten}
      {/* `&nbsp;` chứ không phải dấu cách thường: dấu cách ở ĐẦU một phần tử JSX bị gộp mất
          khi dựng, nên trên màn thật tên miền dính liền tên tài liệu — "…định lượng(drive.google.com)"
          (đo 27/09, đã soi ảnh). */}
      {mien && <span className="lct-hl-mien">&nbsp;({mien})</span>}
    </a>
  );
}

/**
 * Báo link bản ghi hỏng (§72 · bảng phân rã dòng 22 "Báo lỗi record").
 *
 * Chỉ hiện SAU khi em vừa bấm mở một bản ghi: người chưa thử mở thì chưa biết
 * nó hỏng, và một nút cho mọi buổi lúc nào cũng nằm đó chỉ làm màn dài thêm.
 */
function BaoLoiBanGhi({ sessionId }: { sessionId: number }) {
  const [trangThai, setTrangThai] = useState<'chua' | 'dang' | 'xong' | 'loi'>('chua');
  if (trangThai === 'xong') return <span className="lct-bg-da">Đã báo, cảm ơn em.</span>;
  return (
    <button
      type="button"
      className="lct-link lct-bg-bao"
      disabled={trangThai === 'dang'}
      onClick={() => {
        // CHỜ máy chủ trả lời rồi mới nói "đã báo". Bản đầu đặt cờ trước rồi
        // `.catch(() => {})` — nên 400, 403 hay mạng rớt cũng ra "Đã báo, cảm ơn
        // em." trong khi người dạy chẳng nhận được gì (agent soát 26/09).
        setTrangThai('dang');
        void apiFetch(`/api/sessions/${sessionId}/ban-ghi/bao-loi`, { method: 'POST' })
          .then((r) => setTrangThai(r.ok ? 'xong' : 'loi'))
          .catch(() => setTrangThai('loi'));
      }}
    >
      {trangThai === 'dang' ? 'Đang báo…' : trangThai === 'loi' ? 'Chưa báo được — thử lại?' : 'Không mở được?'}
    </button>
  );
}

export default function LopCuaToi({ dl }: { dl: DuLieu | null }) {
  const [loi, setLoi] = useState<string | null>(null);
  const [dangDoi, setDangDoi] = useState(false);
  // Buổi em vừa bấm mở — để nút báo link hỏng gắn đúng buổi ấy (§72).
  const [vuaMo, setVuaMo] = useState<number | null>(null);
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

            {/* Điểm danh TỪNG buổi (bảng TopHSA dòng 28): gấp sẵn — con số tổng ở
                dòng trên là thứ em nhìn hằng ngày, danh sách là để đối chiếu. */}
            {l.diemDanh && l.diemDanh.length > 0 && (
              <details className="group mt-2">
                <summary className="inline-flex min-h-11 cursor-pointer items-center gap-1 text-small font-semibold text-brand-ink">
                  <span aria-hidden="true" className="inline-block transition-transform group-open:rotate-90 motion-reduce:transition-none">›</span>
                  Điểm danh từng buổi ({l.diemDanh.length})
                </summary>
                <ol className="flex flex-col">
                  {l.diemDanh.map((b) => {
                    const t = nhanDiemDanh(b);
                    return (
                      <li key={b.sessionId} className="flex flex-wrap items-baseline justify-between gap-x-3 border-t border-line/50 py-1.5 text-small first:border-t-0">
                        <span className="min-w-0 text-ink-2">
                          <span className="tabular-nums">{lucVN(b.startsAt)}</span>
                          {b.topic && <> · {b.topic}</>}
                        </span>
                        <b className={t.mau}>{t.nhan}</b>
                      </li>
                    );
                  })}
                </ol>
              </details>
            )}
            {l.chuongTrinh && <p className="lct-cc">{cauTienDoEm(l.chuongTrinh)}</p>}

            {/* Bản ghi buổi đã học (§72, 26/09/2026). Trợ giảng dán link từ lâu
                nhưng chưa màn nào của em hiện nó ra — link nằm đó, không ai mở. */}
            {(l.banGhiGanDay?.length ?? 0) > 0 && (
              <p className="lct-cc lct-bg">
                Xem lại:{' '}
                {l.banGhiGanDay!.map((b) => (
                  <NutBanGhi key={b.sessionId} b={b} onMo={() => setVuaMo(b.sessionId)} />
                ))}
                {/* `key` là bắt buộc: không có nó, React giữ nguyên instance khi
                    em mở sang bản ghi khác, nên cờ "đã báo" của buổi trước còn
                    nguyên và em không báo được link thứ hai — màn vẫn nói "Đã
                    báo, cảm ơn em." mà chẳng gửi gì (agent soát 26/09). */}
                {vuaMo !== null && <BaoLoiBanGhi key={vuaMo} sessionId={vuaMo} />}
              </p>
            )}

            {/* Học liệu (§60, 26/09/2026). Cùng lý do với bản ghi ở trên: giảng viên
                gắn tài liệu vào lớp mà không màn nào của em hiện ra thì tài liệu ấy
                coi như không tồn tại. Chỉ hiện thứ giảng viên ĐÃ MỞ (`an = FALSE`) và
                của buổi em THUỘC — máy chủ đã lọc, màn không lọc lại. */}
            {(l.hocLieuGanDay?.length ?? 0) > 0 && (
              <p className="lct-cc lct-hl">
                Tài liệu:{' '}
                {l.hocLieuGanDay!.map((t) => (
                  <NutTaiLieu key={t.id} t={t} />
                ))}
              </p>
            )}

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
      {/* Lịch học sang điện thoại (§71). Đặt SAU các thẻ lớp: em vào đây trước hết
          để xem buổi tới và bài phải làm; việc thêm lịch chỉ làm một lần. */}
      <ThemVaoLich />
    </>
  );
}
