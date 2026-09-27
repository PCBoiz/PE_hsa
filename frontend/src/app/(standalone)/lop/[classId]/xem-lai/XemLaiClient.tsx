'use client';

import { useState } from 'react';

import { Button, Chip, EmptyState } from '@/components/ui';
import { apiFetch, layJson, loiBatDuoc } from '@/lib/api';
import { useDaGan } from '@/lib/daGan';
import {
  BAN_GHI,
  HD_TRANG_BAN_GHI,
  HD_TRANG_HOC_LIEU,
  HOC_LIEU,
  type BanGhi,
  type Chi,
  type Loai,
  type TaiLieu,
  type TrangBanGhi,
  type TrangHocLieu,
  buoiDay,
  duongTrang,
  ngayDay,
  tenMien,
} from '@/lib/xemDu';

/**
 * XEM LẠI BÀI — bản ghi buổi học và tài liệu của CẢ KHOÁ (bảng phân rã dòng 29, 30).
 *
 * ── VÌ SAO CÓ MÀN NÀY (27/09/2026) ────────────────────────────────────────
 *
 * Thẻ lớp ở bảng điều khiển chỉ giữ BỐN dòng gần nhất — đúng cho một thẻ, nhưng ngoài nó em
 * không có màn nào khác. Lớp 24 buổi thì từ buổi thứ năm trở về trước, bản ghi và tài liệu
 * coi như không tồn tại với em. Đây là chỗ xem đủ, và là chỗ TÌM.
 *
 * ── BỐN ĐIỀU ĐÁNG NÓI RÕ, mỗi điều là một cách hỏng đã thấy trong repo ─────
 *
 * ① MỌI Ô, MỌI NÚT KHOÁ TỚI KHI REACT GẮN XONG (`useDaGan`). Trang dựng sẵn ở máy chủ nên ô
 *   tìm HIỆN RA trước khi JavaScript gắn vào; bấm trong khoảng ấy là bấm vào hư không — không
 *   lời gọi mạng, không `aria-pressed` đổi, không một dấu hiệu nào. Bộ đo trang Thông báo gặp
 *   đúng chuyện đó ở bước lọc đầu tiên rồi những bước sau lại chạy tốt, nên nó KHÔNG tự lộ ra.
 *
 * ② ĐỔI TAB / ĐỔI LỌC / TÌM LẠI là tải lại từ đầu và DỌN SẠCH danh sách trước. Giữ dòng cũ
 *   trong lúc chờ thì có một nhịp màn hiện kết quả của bộ lọc TRƯỚC dưới nhãn của bộ lọc SAU.
 *
 * ③ "XEM THÊM" NỐI THÊM THEO KHOÁ (`truoc` = dòng cuối trang trước), không theo số trang:
 *   giảng viên gắn thêm một tài liệu giữa hai lần bấm thì phân trang theo số trang đẩy một
 *   dòng xuống và em đọc nó HAI lần.
 *
 * ④ GHI NHẬN "EM ĐÃ MỞ" đi qua đúng cửa §72 (`POST /api/sessions/<id>/ban-ghi/da-mo`) mà thẻ
 *   lớp đang dùng — không viết một đường đếm thứ hai. Con số "1/2 em đã mở" của trợ giảng
 *   phải đếm cùng một thứ dù em bấm ở thẻ lớp hay ở đây. Việc báo chạy NGẦM và không chặn
 *   đường đi: máy chủ lỗi thì em vẫn mở được bản ghi — thống kê hỏng còn hơn em không xem lại
 *   được bài.
 */
type Dong = { k: 'bg'; d: BanGhi } | { k: 'tl'; d: TaiLieu };

export default function XemLaiClient({
  lopId, tabDau, dauBanGhi, dauTaiLieu, loiTai,
}: {
  lopId: number;
  /** Tab mở sẵn — thẻ lớp có hai đường "Xem tất cả", mỗi đường mở đúng danh sách của nó. */
  tabDau: Loai;
  dauBanGhi: TrangBanGhi | null;
  dauTaiLieu: TrangHocLieu | null;
  loiTai: string | null;
}) {
  const [loai, setLoai] = useState<Loai>(tabDau);
  const [ds, setDs] = useState<Dong[]>(tabDau === BAN_GHI
    ? (dauBanGhi?.items ?? []).map((d): Dong => ({ k: 'bg', d }))
    : (dauTaiLieu?.items ?? []).map((d): Dong => ({ k: 'tl', d })));
  const [tiep, setTiep] = useState<number | null>(
    (tabDau === BAN_GHI ? dauBanGhi?.tiep : dauTaiLieu?.tiep) ?? null);
  // Chữ TRONG ô tìm, và chữ ĐÃ GỬI đi — hai thứ khác nhau. Gõ mà chưa bấm Tìm thì danh sách
  // đang hiện vẫn là kết quả của chữ cũ, và nhãn trên đầu phải nói theo chữ cũ ấy.
  const [oTim, setOTim] = useState('');
  const [tim, setTim] = useState('');
  const [chuaMo, setChuaMo] = useState(false);
  const [chi, setChi] = useState<Chi>(null);
  const [dangTai, setDangTai] = useState(false);
  const [err, setErr] = useState<string | null>(loiTai);
  const daGan = useDaGan();

  async function tai(l: Loai, truoc: number | null, t: string, cm: boolean, c: Chi) {
    setDangTai(true);
    setErr(null);
    try {
      const duong = duongTrang(lopId, l, { truoc, tim: t, chuaMo: cm, chi: c });
      let moi: Dong[];
      let sau: number | null;
      if (l === BAN_GHI) {
        const d = await layJson<TrangBanGhi>(duong, HD_TRANG_BAN_GHI);
        moi = d.items.map((x): Dong => ({ k: 'bg', d: x }));
        sau = d.tiep;
      } else {
        const d = await layJson<TrangHocLieu>(duong, HD_TRANG_HOC_LIEU);
        moi = d.items.map((x): Dong => ({ k: 'tl', d: x }));
        sau = d.tiep;
      }
      setDs((cu) => (truoc === null ? moi : [...cu, ...moi]));
      setTiep(sau);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không tải được danh sách. Thử lại sau ít phút.'));
    } finally {
      setDangTai(false);
    }
  }

  /** Đổi tab: dọn cả danh sách LẪN ô lọc riêng của tab kia — "chưa xem lại" không có nghĩa gì
      với tài liệu, và để nó bật ngầm là một bộ lọc không ai thấy. */
  function doiTab(l: Loai) {
    if (l === loai) return;
    setLoai(l);
    setDs([]);
    setTiep(null);
    setChuaMo(false);
    setChi(null);
    void tai(l, null, tim, false, null);
  }

  function doiLoc(cm: boolean, c: Chi) {
    setChuaMo(cm);
    setChi(c);
    setDs([]);
    setTiep(null);
    void tai(loai, null, tim, cm, c);
  }

  function guiTim(e: React.FormEvent) {
    e.preventDefault();
    const t = oTim.trim();
    setTim(t);
    setDs([]);
    setTiep(null);
    void tai(loai, null, t, chuaMo, chi);
  }

  /** Em bấm mở một bản ghi: báo cho máy chủ (§72) và đánh dấu ngay trên màn. */
  function ghiDaMo(sessionId: number) {
    setDs((cu) => cu.map((r) => (r.k === 'bg' && r.d.sessionId === sessionId
      ? { k: 'bg', d: { ...r.d, daMo: true, lanMo: r.d.lanMo + 1 } }
      : r)));
    void apiFetch(`/api/sessions/${sessionId}/ban-ghi/da-mo`, { method: 'POST' }).catch(() => {});
  }

  const rong = ds.length === 0 && !dangTai;
  const dangTim = tim.length > 0;

  return (
    <div data-khu="xem-lai">
      {/* Hai danh sách của cùng một lớp — tab chứ không hai trang: em vào đây để "xem lại bài",
          và bản ghi với tài liệu của một buổi là hai nửa của cùng việc ấy. */}
      <div className="mb-4 flex flex-wrap gap-2" role="group" aria-label="Chọn danh sách">
        <button type="button" onClick={() => doiTab(BAN_GHI)} aria-pressed={loai === BAN_GHI}
                disabled={!daGan} className={o(loai === BAN_GHI)}>
          Bản ghi buổi học
        </button>
        <button type="button" onClick={() => doiTab(HOC_LIEU)} aria-pressed={loai === HOC_LIEU}
                disabled={!daGan} className={o(loai === HOC_LIEU)}>
          Tài liệu
        </button>
      </div>

      <form onSubmit={guiTim} className="mb-3 flex flex-wrap items-center gap-2">
        <label htmlFor="xl-tim" className="sr-only">
          {loai === BAN_GHI ? 'Tìm buổi học' : 'Tìm tài liệu'}
        </label>
        <input
          id="xl-tim"
          type="search"
          value={oTim}
          onChange={(e) => setOTim(e.target.value)}
          disabled={!daGan}
          placeholder={loai === BAN_GHI
            ? 'Tìm theo chủ đề buổi, hoặc theo ngày học'
            : 'Tìm theo tên hoặc mô tả tài liệu'}
          /* `basis-64` + `min-w-0` + `flex-1`: ô tìm chiếm cả dòng ở khổ điện thoại và chia
             dòng với hai nút ở khổ rộng — không con số px nào, không tràn ngang. */
          className="min-h-11 min-w-0 flex-1 basis-64 rounded-xl border border-line bg-surface px-3 text-body text-ink placeholder:text-ink-3 disabled:opacity-60"
        />
        <Button type="submit" size="sm" disabled={!daGan || dangTai}>Tìm</Button>
        {(dangTim || oTim.length > 0) && (
          <Button type="button" variant="ghost" size="sm" disabled={!daGan || dangTai}
                  onClick={() => { setOTim(''); setTim(''); setDs([]); setTiep(null); void tai(loai, null, '', chuaMo, chi); }}>
            Xoá ô tìm
          </Button>
        )}
      </form>

      <div className="mb-4 flex flex-wrap gap-2" role="group" aria-label="Lọc danh sách">
        {loai === BAN_GHI ? (
          <>
            <button type="button" onClick={() => doiLoc(false, null)} aria-pressed={!chuaMo}
                    disabled={!daGan} className={o(!chuaMo)}>Tất cả buổi</button>
            <button type="button" onClick={() => doiLoc(true, null)} aria-pressed={chuaMo}
                    disabled={!daGan} className={o(chuaMo)}>Chưa xem lại</button>
          </>
        ) : (
          <>
            <button type="button" onClick={() => doiLoc(false, null)} aria-pressed={chi === null}
                    disabled={!daGan} className={o(chi === null)}>Tất cả tài liệu</button>
            <button type="button" onClick={() => doiLoc(false, 'chung')} aria-pressed={chi === 'chung'}
                    disabled={!daGan} className={o(chi === 'chung')}>Dùng cho cả khoá</button>
            <button type="button" onClick={() => doiLoc(false, 'buoi')} aria-pressed={chi === 'buoi'}
                    disabled={!daGan} className={o(chi === 'buoi')}>Theo từng buổi</button>
          </>
        )}
      </div>

      {err && (
        <p role="alert" className="mb-3 rounded-xl bg-danger/10 px-4 py-3 text-small text-danger-ink">
          {err}
        </p>
      )}

      {rong ? (
        <EmptyState
          title={trong(loai, dangTim).title}
          hint={trong(loai, dangTim).hint}
        />
      ) : (
        <ul className="flex flex-col gap-2">
          {ds.map((r) => (r.k === 'bg'
            ? <DongBanGhi key={`bg-${r.d.sessionId}`} b={r.d} onMo={() => ghiDaMo(r.d.sessionId)} />
            : <DongTaiLieu key={`tl-${r.d.id}`} t={r.d} />))}
        </ul>
      )}

      {tiep !== null && (
        <div className="mt-4 flex justify-center">
          <Button variant="ghost" disabled={dangTai || !daGan}
                  onClick={() => void tai(loai, tiep, tim, chuaMo, chi)}>
            {dangTai ? 'Đang tải…' : 'Xem thêm'}
          </Button>
        </div>
      )}
    </div>
  );
}

/**
 * Một buổi có bản ghi.
 *
 * Mở ra TAB MỚI kèm `rel="noopener noreferrer"`: đường dẫn do trợ giảng dán vào, trỏ ra ngoài
 * TopHSA (Zoom, Drive). Thiếu `noopener` thì trang đích với tới được `window.opener` và đổi
 * được địa chỉ tab gốc — cách dựng một màn đăng nhập giả mà người dùng không thấy gì lạ.
 */
function DongBanGhi({ b, onMo }: { b: BanGhi; onMo: () => void }) {
  return (
    <li data-id={b.sessionId} data-mo={b.daMo ? 'roi' : 'chua'}
        className="rounded-xl border border-line bg-surface p-4">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <b className="text-body text-ink">{buoiDay(b.startsAt)}</b>
        {b.daMo
          ? <Chip tone="neutral">Bạn đã mở{b.lanMo > 1 ? ` ${b.lanMo} lần` : ''}</Chip>
          : <Chip tone="brand">Chưa xem lại</Chip>}
      </div>
      {b.topic && <p className="mt-1 text-small text-ink-2">{b.topic}</p>}
      <p className="mt-2">
        <a href={b.recordingUrl} target="_blank" rel="noopener noreferrer" onClick={onMo}
           className="text-small font-semibold text-brand-ink underline underline-offset-2">
          Mở bản ghi{tenMien(b.recordingUrl) ? ` (${tenMien(b.recordingUrl)})` : ''} →
        </a>
      </p>
    </li>
  );
}

/**
 * Một tài liệu.
 *
 * `nguon` nói thành LỜI, không bao giờ in ra mã: hôm nay mọi tài liệu là liên kết ngoài
 * (`'link'` — anh Sơn chốt 26/09) nên nhãn là "Mở tài liệu"; chỗ chừa sẵn cho tệp tải thẳng
 * lên (`'r2'`, chờ khoá Cloudflare R2) đọc thành "Tải tệp về". Ngày thêm R2 chỉ là thêm dữ
 * liệu, không phải sửa màn — và không đời nào để chữ `r2` lọt lên màn của em (RULES §10).
 */
function DongTaiLieu({ t }: { t: TaiLieu }) {
  const mien = tenMien(t.url);
  const nhanMo = t.nguon === 'link' ? 'Mở tài liệu' : 'Tải tệp về';
  return (
    <li data-id={t.id} className="rounded-xl border border-line bg-surface p-4">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <b className="text-body text-ink">{t.ten}</b>
        {t.sessionId === null
          ? <Chip tone="neutral">Dùng cho cả khoá</Chip>
          : <Chip tone="brand">Buổi {ngayDay(t.buoiLuc)}</Chip>}
      </div>
      {t.buoiChuDe && t.sessionId !== null && (
        <p className="mt-1 text-small text-ink-3">{t.buoiChuDe}</p>
      )}
      {t.moTa && <p className="mt-1 text-small text-ink-2">{t.moTa}</p>}
      <p className="mt-2 flex flex-wrap items-baseline gap-x-3 text-small">
        {t.url ? (
          <a href={t.url} target="_blank" rel="noopener noreferrer"
             className="font-semibold text-brand-ink underline underline-offset-2">
            {nhanMo}{mien ? ` (${mien})` : ''} →
          </a>
        ) : (
          <span className="text-ink-3">Tài liệu này chưa có đường mở — nhắn giảng viên giúp em nhé.</span>
        )}
        {t.luc && <span className="text-ink-3">Gắn ngày {ngayDay(t.luc)}</span>}
      </p>
    </li>
  );
}

/** Danh sách rỗng vì CHƯA CÓ GÌ và rỗng vì Ô TÌM không khớp là hai câu khác nhau. */
function trong(loai: Loai, dangTim: boolean): { title: string; hint: string } {
  if (loai === BAN_GHI) {
    return dangTim
      ? { title: 'Không có buổi nào khớp',
          hint: 'Thử bớt chữ trong ô tìm, hoặc gõ ngày buổi học theo dạng ngày/tháng/năm.' }
      : { title: 'Chưa có bản ghi nào',
          hint: 'Sau mỗi buổi, trợ giảng dán đường xem lại vào buổi đó. Khi có, buổi ấy sẽ hiện ở đây.' };
  }
  return dangTim
    ? { title: 'Không có tài liệu nào khớp', hint: 'Thử bớt chữ trong ô tìm.' }
    : { title: 'Chưa có tài liệu nào',
        hint: 'Giảng viên mở dần tài liệu theo tiến độ lớp. Khi có, tài liệu sẽ hiện ở đây.' };
}

/** Ô lọc: cùng chiều cao chạm với nút thường, khác nhau ở nền khi đang bật. */
function o(dangBat: boolean): string {
  return `min-h-11 rounded-full border px-4 text-small disabled:opacity-60 ${
    dangBat
      ? 'border-brand bg-brand-soft text-brand-ink'
      : 'border-line bg-surface text-ink-2 hover:border-brand hover:text-brand-ink'
  }`;
}
