import Link from 'next/link';

import { LOAI_LOP, TRANG_THAI } from './lop';

/**
 * BỘ LỌC + PHÂN TRANG danh sách lớp (§54, 24/09/2026) — dựng ở MÁY CHỦ.
 *
 * TopHSA có ~400 lớp gia sư bên cạnh lớp nhóm: danh sách phải lọc + chia trang ở
 * máy chủ (`reports.class_page`). Bộ lọc là `<form method="get">` và liên kết
 * thường — không một dòng JS phía trình duyệt, mọi trạng thái nằm trên URL (gửi
 * link "lớp gia sư của cô Lan" cho đồng nghiệp là họ thấy đúng thứ mình thấy).
 * Truyền vào `LopHocClient` như một khối giao diện, cùng khuôn Trang của tôi.
 *
 * Tham số URL (tiếng Việt, ngắn): `q`, `loai`, `tt`, `dot`, `gv`, `trang`.
 * Ô chọn nói "Tất cả" chứ không "Mọi …" (góp ý TopHSA 24/09). Chỉ ô Tìm luôn hiện;
 * loại lớp là chip, điều kiện phụ gập trong "Lọc thêm" (màn đầu điện thoại từng
 * chỉ thấy năm ô lọc, danh sách lớp nằm dưới nếp gấp).
 */
export type LocLop = { q: string; loai: string; tt: string; dot: string; gv: string; trang: string };
type Chon = { id: number; ten: string };

const DUONG = '/quan-tri/lop-hoc';
const O = 'min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink';
const LINK = 'inline-flex min-h-11 items-center text-small text-brand-ink underline';

/** URL với bộ lọc hiện tại, đè vài khoá; khoá rỗng thì bỏ khỏi URL. */
export function urlLoc(loc: LocLop, de: Partial<LocLop> = {}) {
  const n = new URLSearchParams();
  for (const [k, v] of Object.entries({ ...loc, ...de })) if (v) n.set(k, v);
  const s = n.toString();
  return s ? `${DUONG}?${s}` : DUONG;
}

export function BoLocLop({
  loc, dem, dotHoc, nguoi, trangThai,
}: {
  loc: LocLop;
  dem: { byType: Record<string, number>; byStatus: Record<string, number> } | null;
  dotHoc: Chon[];
  /** Giảng viên + trợ giảng: lọc "lớp của một người" gồm cả lớp người ấy trợ giảng. */
  nguoi: Chon[];
  trangThai: string[];
}) {
  const dangLoc = Boolean(loc.q || loc.loai || loc.tt || loc.dot || loc.gv);
  const soPhu = [loc.gv, loc.tt, loc.dot].filter(Boolean).length;
  return (
    <div className="mb-4 flex flex-col gap-3">
      {/* Chip đếm theo loại — bấm là lọc ngay (trang về 1). */}
      {dem && (
        <nav aria-label="Lọc nhanh theo loại lớp" className="flex flex-wrap gap-2">
          {Object.keys(LOAI_LOP).map((k) => {
            const dangChon = loc.loai === k;
            return (
              <Link
                key={k}
                href={urlLoc(loc, { loai: dangChon ? '' : k, trang: '' })}
                aria-current={dangChon ? 'true' : undefined}
                className={`inline-flex min-h-11 items-center gap-2 rounded-full border px-4 text-small ${
                  dangChon ? 'border-brand bg-brand/10 text-brand-ink' : 'border-line text-ink-2 hover:border-brand'
                }`}
              >
                {LOAI_LOP[k]} <b className="tabular-nums">{dem.byType[k] ?? 0}</b>
              </Link>
            );
          })}
        </nav>
      )}

      {/* `role="search"` + tên: biểu mẫu Thêm/Sửa lớp cũng có ô "Trạng thái", "Đợt
          học" — hai vùng có tên riêng thì trình đọc màn hình (và phép kiểm) phân biệt
          được ô nào lọc, ô nào ghi. */}
      <form method="get" action={DUONG} role="search" aria-label="Lọc danh sách lớp" className="flex flex-col gap-1">
        {/* Loại lớp chọn bằng CHIP ở trên — ô ẩn giữ nó khi bấm Lọc (form GET chỉ gửi ô của nó). */}
        {loc.loai && <input type="hidden" name="loai" value={loc.loai} />}
        <div className="flex flex-wrap items-end gap-x-3 gap-y-2">
          <label className="flex min-w-0 flex-[1_1_12rem] flex-col gap-1">
            <span className="text-label text-ink-3">Tìm</span>
            <input name="q" defaultValue={loc.q} className={O} placeholder="Tên lớp, giáo viên, học viên, mã HSA" />
          </label>
          <span className="flex flex-wrap items-center gap-x-4">
            <button type="submit"
              className="min-h-11 rounded-md bg-brand-fill px-4 text-body font-semibold text-white hover:brightness-110">
              Lọc
            </button>
            {dangLoc && <Link href={DUONG} className={LINK}>Bỏ lọc</Link>}
          </span>
        </div>
        {/* Điều kiện phụ GẬP lại (góp ý TopHSA: màn đầu rối) — tự mở khi đang dùng,
            để người mở link "lớp của cô Lan" thấy ngay vì sao danh sách ngắn. */}
        <details open={soPhu > 0} className="group">
          {/* `inline-flex` xoá mũi tên mặc định của <summary> — vẽ lại để thấy bấm được. */}
          <summary className="inline-flex min-h-11 cursor-pointer items-center gap-1 text-small text-brand-ink">
            <span aria-hidden="true" className="inline-block transition-transform group-open:rotate-90 motion-reduce:transition-none">›</span>
            Lọc thêm{soPhu > 0 ? ` · ${soPhu} đang chọn` : ''}
          </summary>
          <div className="grid gap-2 pb-1 [grid-template-columns:repeat(auto-fit,minmax(min(100%,13rem),1fr))]">
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Giáo viên / trợ giảng</span>
              <select name="gv" defaultValue={loc.gv} className={O}>
                <option value="">Tất cả</option>
                {nguoi.map((g) => <option key={g.id} value={g.id}>{g.ten}</option>)}
              </select>
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Trạng thái</span>
              <select name="tt" defaultValue={loc.tt} className={O}>
                <option value="">Tất cả</option>
                {trangThai.map((s) => <option key={s} value={s}>{TRANG_THAI[s]?.nhan ?? s}</option>)}
              </select>
            </label>
            {dotHoc.length > 0 && (
              <label className="flex flex-col gap-1">
                <span className="text-label text-ink-3">Đợt học</span>
                <select name="dot" defaultValue={loc.dot} className={O}>
                  <option value="">Tất cả</option>
                  {dotHoc.map((d) => <option key={d.id} value={d.id}>{d.ten}</option>)}
                </select>
              </label>
            )}
          </div>
        </details>
      </form>
    </div>
  );
}

export function PhanTrangLop({ loc, tong, trang, moiTrang }: {
  loc: LocLop; tong: number; trang: number; moiTrang: number;
}) {
  const soTrang = Math.max(1, Math.ceil(tong / moiTrang));
  // 0 lớp: ô trống ở trên đã nói — thêm "0 lớp" là thêm chữ, không thêm tin.
  if (tong === 0 && trang <= 1) return null;
  if (tong <= moiTrang && trang <= 1) {
    return <p className="mt-3 text-small text-ink-3">{tong} lớp</p>;
  }
  return (
    <nav aria-label="Phân trang danh sách lớp" className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1">
      <span className="text-small text-ink-3 tabular-nums">
        Trang {Math.min(trang, soTrang)}/{soTrang} · {tong} lớp
      </span>
      {trang > 1 && <Link href={urlLoc(loc, { trang: String(trang - 1) })} className={LINK}>← Trang trước</Link>}
      {trang < soTrang && <Link href={urlLoc(loc, { trang: String(trang + 1) })} className={LINK}>Trang sau →</Link>}
      {trang > soTrang && <Link href={urlLoc(loc, { trang: '' })} className={LINK}>Về trang 1</Link>}
    </nav>
  );
}
