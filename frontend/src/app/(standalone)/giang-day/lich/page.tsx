import Link from 'next/link';

import ThemVaoLich from '@/components/ThemVaoLich';
import { Chip, EmptyState } from '@/components/ui';
import { chanTu } from '@/lib/chanTu';
import { ngayVN } from '@/lib/gioVN';
import { noiHoc } from '@/lib/noiHoc';
import { serverJson, type HinhDang } from '@/lib/server-api';
import { z } from 'zod';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Lịch học | TopHSA' };

/**
 * LỊCH HỌC GỘP — mọi buổi của mọi lớp người xem thấy, theo tuần (bảng yêu cầu
 * TopHSA tab "Nhi" #4, 23/09/2026). `GET /api/teach/lich` — xem `teaching/lich.py`.
 *
 * ── VÌ SAO MỘT TRANG RIÊNG ─────────────────────────────────────────────────
 *
 * Sổ buổi học (`buoi-hoc/<lớp>`) trả lời "lớp NÀY học khi nào". Người xếp lịch
 * hỏi câu khác: "tối thứ Năm này trung tâm có những lớp nào, giảng viên nào kín
 * giờ, phòng nào trống" — câu ấy cần nhìn XUYÊN lớp. Học vụ lọc thêm theo giảng
 * viên hoặc theo một em (lối vào từ hồ sơ học viên: `?hoc_vien=<id>`).
 *
 * ── DỰNG Ở MÁY CHỦ, LỌC BẰNG FORM GET ─────────────────────────────────────
 *
 * Không một dòng JS phía trình duyệt: bộ lọc là `<form method="get">`, chuyển
 * tuần là liên kết. Nhờ vậy mọi trạng thái nằm trên URL — gửi link "lịch tuần
 * sau của cô Lan" cho đồng nghiệp là họ thấy đúng thứ mình thấy.
 *
 * Ngày giờ đọc bằng CẮT CHUỖI, không dựng `Date`: máy chủ trả giờ Việt Nam
 * không múi, còn máy dựng trang (Vercel) chạy UTC.
 */
type Buoi = {
  id: number;
  lopId: number;
  lop: string;
  maLop: string | null;
  giangVien: string | null;
  batDau: string;
  phut: number;
  chuDe: string | null;
  trangThai: string;
  hinhThuc: string | null;
  phong: string | null;
  linkPhong: string | null;
  trungGiangVien: boolean;
};
type Chon = { id: number; ten: string | null };
type Lich = {
  tu: string;
  den: string;
  buoi: Buoi[];
  lopChon: Chon[];
  giangVienChon?: Chon[];
  hocVien?: { id: number; ten: string | null; ma: string | null } | null;
};

const chu = z.string().nullable();
const HD_LICH = z.looseObject({
  tu: z.string(),
  den: z.string(),
  buoi: z.array(z.looseObject({
    id: z.number(), lopId: z.number(), lop: z.string(), maLop: chu, giangVien: chu,
    batDau: z.string(), phut: z.number(), chuDe: chu, trangThai: z.string(),
    hinhThuc: chu, phong: chu, linkPhong: chu, trungGiangVien: z.boolean(),
  })),
  lopChon: z.array(z.looseObject({ id: z.number(), ten: chu })),
  giangVienChon: z.array(z.looseObject({ id: z.number(), ten: chu })).optional(),
  hocVien: z.looseObject({ id: z.number(), ten: chu, ma: chu }).nullable().optional(),
}) satisfies HinhDang<Lich>;

const THU = ['Chủ nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];
const LINK = 'inline-flex min-h-11 items-center text-small text-brand-ink underline';
const O = 'min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink';

/** Cộng ngày trên chuỗi YYYY-MM-DD — tính theo UTC để không lệch múi. */
function cong(ngay: string, soNgay: number) {
  const d = new Date(`${ngay}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + soNgay);
  return d.toISOString().slice(0, 10);
}
const thuCua = (ngay: string) => THU[new Date(`${ngay}T00:00:00Z`).getUTCDay()];
const dm = (ngay: string) => `${ngay.slice(8, 10)}/${ngay.slice(5, 7)}`;

/** "19:00–20:30" từ giờ bắt đầu (chuỗi máy chủ) và số phút. */
function khungGio(batDau: string, phut: number) {
  const [h, m] = batDau.slice(11, 16).split(':').map(Number);
  const het = h * 60 + m + phut;
  const p = (n: number) => String(n).padStart(2, '0');
  return `${batDau.slice(11, 16)}–${p(Math.floor(het / 60) % 24)}:${p(het % 60)}`;
}

export default async function LichHocPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const one = (k: string) => {
    const v = sp[k];
    return (Array.isArray(v) ? v[0] : v) ?? '';
  };
  const qs = new URLSearchParams();
  for (const k of ['tu', 'den', 'lop', 'giang_vien', 'hoc_vien']) if (one(k)) qs.set(k, one(k));

  const kq = await serverJson<Lich>(`/api/teach/lich?${qs}`, { requireAuth: true }, HD_LICH);

  if (!kq.ok) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-16" data-chan={chanTu(kq.status)}>
        <h1 className="text-title text-ink">Không mở được lịch học</h1>
        <p className="mt-2 text-body text-ink-2">
          {kq.status === 403 ? 'Lịch học gộp dành cho giảng viên, trợ giảng và học vụ.' : kq.message}
        </p>
        {/* Khoảng ngày gõ sai trên URL (400) thì phải có đường về — ô lọc do
            chính phản hồi hỏng này cấp nên cũng không còn. */}
        <Link href="/giang-day/lich" className={`mt-6 ${LINK}`}>
          Xem lịch tuần này
        </Link>
      </main>
    );
  }

  const d = kq.data;
  const homNay = ngayVN();
  const soNgay = Math.round(
    (Date.parse(`${d.den}T00:00:00Z`) - Date.parse(`${d.tu}T00:00:00Z`)) / 86_400_000,
  ) + 1;
  const ngay = Array.from({ length: soNgay }, (_, i) => cong(d.tu, i));
  const theoNgay = new Map<string, Buoi[]>();
  for (const b of d.buoi) {
    const k = b.batDau.slice(0, 10);
    theoNgay.set(k, [...(theoNgay.get(k) ?? []), b]);
  }

  /** Đổi khoảng ngày, GIỮ bộ lọc — "tuần sau của cô Lan" vẫn là của cô Lan. */
  const den = (tu: string, denNgay: string) => {
    const n = new URLSearchParams(qs);
    n.set('tu', tu);
    n.set('den', denNgay);
    return `/giang-day/lich?${n}`;
  };
  const boLoc = (khoa: string) => {
    const n = new URLSearchParams(qs);
    n.delete(khoa);
    return `/giang-day/lich?${n}`;
  };

  // Thứ Hai của tuần chứa hôm nay (thứ Hai = 0 … Chủ nhật = 6, lịch Việt).
  const thuHomNay = (new Date(`${homNay}T00:00:00Z`).getUTCDay() + 6) % 7;
  const dauTuanNay = cong(homNay, -thuHomNay);
  // Bỏ lọc = giữ đúng khoảng ngày đang xem, bỏ mọi thứ khác.
  const khongLoc = `/giang-day/lich?${new URLSearchParams({ tu: d.tu, den: d.den })}`;

  const conBuoi = d.buoi.filter((b) => b.trangThai !== 'cancelled');
  const soTrung = conBuoi.filter((b) => b.trungGiangVien).length;
  const soHuy = d.buoi.length - conBuoi.length;
  const dangLoc = Boolean(one('lop') || one('giang_vien') || one('hoc_vien'));

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-5 px-4 py-6">
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2">
        <div>
          <h1 className="text-section text-ink">Lịch học</h1>
          <p className="mt-1 text-small text-ink-3">
            <span className="text-ink-2">
              {dm(d.tu)} – {dm(d.den)}/{d.den.slice(0, 4)}
            </span>
            {' · '}
            {conBuoi.length} buổi
            {soHuy > 0 && ` · ${soHuy} đã huỷ`}
            {soTrung > 0 && (
              <span className="text-warning-ink"> · {soTrung} buổi trùng giờ giảng viên</span>
            )}
          </p>
        </div>
        <nav aria-label="Chuyển tuần" className="flex flex-wrap gap-x-4">
          <Link href={den(cong(d.tu, -7), cong(d.den, -7))} className={LINK}>
            ← Tuần trước
          </Link>
          <Link href={den(dauTuanNay, cong(dauTuanNay, 6))} className={LINK}>
            Tuần này
          </Link>
          <Link href={den(cong(d.tu, 7), cong(d.den, 7))} className={LINK}>
            Tuần sau →
          </Link>
        </nav>
      </div>

      {/* Lịch dạy đưa sang điện thoại (§71): giảng viên và trợ giảng là nhóm hỏi
          "tuần này tôi dạy buổi nào" nhiều nhất, mà câu trả lời lại nằm sau một
          lần đăng nhập. */}
      <ThemVaoLich nhan="Thêm lịch dạy vào điện thoại" />

      {d.hocVien && (
        <p role="status" className="rounded-md bg-brand/5 px-3 py-2 text-small text-ink-2">
          Đang xem lịch của <b className="text-ink">{d.hocVien.ten ?? 'học viên'}</b>
          {d.hocVien.ma ? ` (${d.hocVien.ma})` : ''} — tính theo lớp em đang học tại giờ từng buổi.{' '}
          <Link href={boLoc('hoc_vien')} className="text-brand-ink underline">
            Xem lịch chung
          </Link>
        </p>
      )}

      <form
        method="get"
        className="grid items-end gap-2 [grid-template-columns:repeat(auto-fit,minmax(min(100%,12rem),1fr))]"
      >
        <input type="hidden" name="tu" value={d.tu} />
        <input type="hidden" name="den" value={d.den} />
        {one('hoc_vien') && <input type="hidden" name="hoc_vien" value={one('hoc_vien')} />}
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Lớp</span>
          <select name="lop" defaultValue={one('lop')} className={O}>
            <option value="">Tất cả</option>
            {d.lopChon.map((l) => (
              <option key={l.id} value={l.id}>
                {l.ten ?? `Lớp #${l.id}`}
              </option>
            ))}
          </select>
        </label>
        {/* Chỉ quản trị viên và học vụ nhận danh sách giảng viên — giảng viên
            chỉ thấy lớp mình, lọc theo người khác là vô nghĩa. */}
        {d.giangVienChon && (
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Giảng viên</span>
            <select name="giang_vien" defaultValue={one('giang_vien')} className={O}>
              <option value="">Tất cả</option>
              {d.giangVienChon.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.ten ?? `#${g.id}`}
                </option>
              ))}
            </select>
          </label>
        )}
        <span className="flex flex-wrap items-center gap-x-4">
          <button
            type="submit"
            className="min-h-11 rounded-md bg-brand-fill px-4 text-body font-semibold text-white hover:brightness-110"
          >
            Lọc
          </button>
          {dangLoc && (
            <Link href={khongLoc} className={LINK}>
              Bỏ lọc
            </Link>
          )}
        </span>
      </form>

      {d.buoi.length === 0 ? (
        <EmptyState
          title="Không có buổi học nào trong khoảng này"
          hint={
            dangLoc
              ? 'Thử bỏ bộ lọc, hoặc chuyển sang tuần khác.'
              : 'Lịch lớp tạo ở “Buổi học” của từng lớp — có ô sinh lịch cả kỳ theo thứ trong tuần.'
          }
        />
      ) : (
        <ol className="flex flex-col divide-y divide-line rounded-lg border border-line bg-surface">
          {ngay.map((n) => {
            const ds = theoNgay.get(n) ?? [];
            const laHomNay = n === homNay;
            return (
              <li
                key={n}
                aria-current={laHomNay ? 'date' : undefined}
                className={`flex flex-wrap gap-x-4 gap-y-2 px-4 py-3 ${laHomNay ? 'bg-brand/5' : ''}`}
              >
                <p className="w-28 shrink-0 max-sm:w-full">
                  <span className={`block text-subhead ${laHomNay ? 'text-brand-ink' : 'text-ink'}`}>
                    {thuCua(n)}
                  </span>
                  <span className="text-small text-ink-3 tabular-nums">
                    {dm(n)}
                    {laHomNay && ' · hôm nay'}
                  </span>
                </p>
                {ds.length === 0 ? (
                  <p className="self-center text-small text-ink-3">Không có buổi</p>
                ) : (
                  <ul className="grid min-w-0 flex-1 gap-2 [grid-template-columns:repeat(auto-fill,minmax(min(100%,15rem),1fr))]">
                    {ds.map((b) => {
                      const huy = b.trangThai === 'cancelled';
                      const noi = noiHoc(b.hinhThuc, b.phong);
                      return (
                        <li
                          key={b.id}
                          className={`flex flex-col gap-1 rounded-md border px-3 py-2 ${
                            b.trungGiangVien && !huy ? 'border-warning/60' : 'border-line'
                          } ${huy ? 'bg-ground' : 'bg-surface'}`}
                        >
                          <span className="flex flex-wrap items-center gap-2">
                            <span className={`text-subhead tabular-nums ${huy ? 'text-ink-3 line-through' : 'text-ink'}`}>
                              {khungGio(b.batDau, b.phut)}
                            </span>
                            {huy && <Chip tone="bad">Đã huỷ</Chip>}
                            {b.trungGiangVien && !huy && <Chip tone="warn">Trùng giờ giảng viên</Chip>}
                          </span>
                          <Link
                            href={`/giang-day/buoi-hoc/${b.lopId}`}
                            className="inline-flex min-h-11 items-center text-body font-semibold text-ink underline decoration-line underline-offset-2 hover:text-brand-ink"
                          >
                            {b.lop}
                          </Link>
                          <span className="text-small text-ink-3">
                            {[b.giangVien ?? 'Chưa gán giảng viên', noi, b.chuDe].filter(Boolean).join(' · ')}
                          </span>
                          {b.linkPhong && !huy && b.hinhThuc !== 'offline' && (
                            <a
                              href={b.linkPhong}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex min-h-11 items-center text-small text-brand-ink underline"
                            >
                              Link phòng học
                            </a>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </li>
            );
          })}
        </ol>
      )}
    </main>
  );
}
