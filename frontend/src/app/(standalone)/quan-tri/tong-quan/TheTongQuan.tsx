import Link from 'next/link';
import { z } from 'zod';

import { Button, Card, CardHead, Chip, TableWrap, Tbody, Td, Th, Thead, Tr } from '@/components/ui';

import { LOAI_LOP, NHAN_LY_DO_ROI } from '../lop-hoc/lop';

/**
 * BỐN THẺ của Tổng quan v2 (1.4a, 24/09/2026) — trả lời đúng bốn câu trong ghi
 * chú họp TopHSA: bao nhiêu lớp, bao nhiêu em rời lớp, giảng viên điểm danh ra
 * sao, bao nhiêu tài khoản lâu không vào. Số do `teaching/overview.py` tính; ở
 * đây chỉ VẼ, không đếm lại (mảng `classes` đã bị cắt còn 50 dòng — đếm trên nó
 * là hụt lặng lẽ).
 *
 * Gọn chữ là yêu cầu của khách ("nhiều chữ, màn rối"): mỗi thẻ một tiêu đề, số
 * to, nhãn ngắn; danh sách từng em gập trong `<details>` — không JS, bàn phím và
 * trình đọc màn hình mở được sẵn.
 *
 * Hình dạng khai ở đây, trang ghép vào HINH_DANG dưới dạng TUỲ CHỌN: Vercel và
 * Render deploy lệch nhau, nên trang mới gặp máy chủ cũ là chuyện sẽ xảy ra —
 * thiếu khối nào thì thẻ ấy không vẽ, phần còn lại của trang vẫn chạy.
 */
const so = z.number();
const soHoacTrong = z.number().nullable();
const chu = z.string().nullable();

export const LOP_THEO_LOAI = z.record(z.string(), z.looseObject({ total: so, active: so }));
export const ROI_LOP = z.looseObject({
  tu: z.string(),
  den: z.string(),
  tong: so,
  theoLyDo: z.record(z.string(), so),
  theoLoai: z.record(z.string(), so),
  theoThang: z.array(z.looseObject({ thang: z.string(), tong: so })),
  ds: z.array(
    z.looseObject({
      id: so,
      userId: so,
      name: chu,
      className: chu,
      classType: chu,
      leftOn: z.string(),
      reason: chu,
    }),
  ),
});
export const GIANG_VIEN = z.array(
  z.looseObject({
    teacherId: soHoacTrong,
    name: chu,
    soLop: so,
    buoiDaDay: so,
    daDiemDanh: so,
    chuaDiemDanh: so,
    diemDanhMuon: so,
    tiLe: soHoacTrong,
  }),
);
export const TAI_KHOAN_NGU = z.looseObject({
  nguong: z.array(so),
  /* `{tong, d7, d14, d30, chuaTungVao}` — khoá `d<n>` theo `nguong`, nên đọc bằng bản ghi. */
  hocVien: z.record(z.string(), so),
  nhanSu: z.record(z.string(), so),
  doTu: chu,
  ds: z.array(
    z.looseObject({ id: so, name: chu, lop: chu, ngay: so, lanCuoi: chu }),
  ),
});
export type LopTheoLoai = z.infer<typeof LOP_THEO_LOAI>;
export type RoiLop = z.infer<typeof ROI_LOP>;
export type GiangVien = z.infer<typeof GIANG_VIEN>;
export type TaiKhoanNgu = z.infer<typeof TAI_KHOAN_NGU>;

/* Giờ trong phản hồi là giờ VN dạng chuỗi (`local_now()` của máy chủ). Tách chuỗi
   chứ KHÔNG qua `Date`: máy chủ Next chạy UTC, `new Date(...)` sẽ quy đổi và lệch
   7 tiếng — cùng bẫy `lib/gioVN.ts` đã vá cho lịch tuần. */
const NGAY = /^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}))?/;

/** 'YYYY-MM-DD…' → 'dd/mm'. Chuỗi lạ trả nguyên, không đoán. */
export function ngayNgan(iso: string | null | undefined) {
  const m = NGAY.exec(iso ?? '');
  return m ? `${m[3]}/${m[2]}` : (iso ?? '');
}

/** 'YYYY-MM-DDTHH:MM:SS' → 'HH:MM dd/mm'. */
export function gioCapNhat(iso: string) {
  const m = NGAY.exec(iso);
  return m && m[4] ? `${m[4]}:${m[5]} ${m[3]}/${m[2]}` : iso;
}

/** Số ngày giữa hai chuỗi 'YYYY-MM-DD' (b − a), tính trên lịch — không múi giờ nào xen vào. */
function soNgay(a: string, b: string) {
  const ma = NGAY.exec(a);
  const mb = NGAY.exec(b);
  if (!ma || !mb) return null;
  const t = (m: RegExpExecArray) => Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return Math.round((t(mb) - t(ma)) / 86_400_000);
}

const DONG_LINK =
  'flex min-h-11 items-center justify-between gap-3 rounded-md border border-line px-4 py-2 hover:border-brand';

/** Tông chip theo lý do: bỏ giữa chừng là tin xấu, chưa ghi là việc còn tồn. */
const TONE_LY_DO: Record<string, 'good' | 'bad' | 'neutral' | 'warn'> = {
  completed: 'good',
  dropped: 'bad',
  transferred: 'neutral',
  chuaGhi: 'warn',
};

// ── 1. Lớp học theo loại ────────────────────────────────────────────────────

export function TheLop({ theoLoai, termId }: { theoLoai: LopTheoLoai; termId?: string }) {
  return (
    <Card>
      <CardHead title="Lớp học" />
      <ul className="flex flex-col gap-2">
        {Object.keys(LOAI_LOP).map((k) => {
          const o = theoLoai[k];
          /* Bấm là tới danh sách lớp đã lọc đúng loại (và đúng đợt nếu đang xem một
             đợt) — chỗ để LÀM việc với các lớp ấy. Tham số là của `lop-hoc/page.tsx`. */
          const qs = new URLSearchParams({ loai: k, ...(termId ? { dot: termId } : {}) });
          return (
            <li key={k}>
              <Link href={`/quan-tri/lop-hoc?${qs}`} className={DONG_LINK}>
                <span className="text-body text-ink">{LOAI_LOP[k]}</span>
                <span className="text-right">
                  <b className="text-title text-ink tabular-nums">{o?.active ?? 0}</b>{' '}
                  <span className="text-small text-ink-3">
                    đang chạy{o && o.total !== o.active ? ` / ${o.total}` : ''}
                  </span>
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

// ── 2. Tài khoản lâu không vào ──────────────────────────────────────────────

export function TheTaiKhoanNgu({ t, homNay }: { t: TaiKhoanNgu; homNay: string }) {
  const nhom = [
    { ten: 'Học viên', g: t.hocVien },
    { ten: 'Nhân sự', g: t.nhanSu },
  ];
  /* Lần vào (§56) chỉ được ghi từ ngày cột ấy có. Trước đó người vào xem mà không
     làm bài không để lại dấu, nên số của những tuần đầu CAO hơn thật — nói ra,
     đừng để người đọc tưởng cả phòng giáo vụ bỏ hệ thống. */
  const doDuoc = t.doTu ? soNgay(t.doTu, homNay) : null;
  const ghiChu =
    t.doTu === null
      ? 'Chưa ghi được lần vào nào — tạm tính theo bài học và ngày cấp tài khoản.'
      : doDuoc !== null && doDuoc < (t.nguong[t.nguong.length - 1] ?? 30)
        ? `Lần vào ghi từ ${ngayNgan(t.doTu)}; trước đó tính theo bài học và ngày cấp tài khoản.`
        : null;
  return (
    /* `id` là đích của việc "N học viên lâu không vào" ở khối Hôm nay cần làm gì. */
    <div id="tai-khoan-ngu" className="scroll-mt-20">
      <Card>
        <CardHead title="Tài khoản lâu không vào" />
        <TableWrap caption="Tài khoản đang mở lâu không vào, theo số ngày">
          <Thead>
            <tr>
              <Th>Tài khoản</Th>
              {t.nguong.map((n) => (
                <Th key={n} align="right">
                  ≥{n} ngày
                </Th>
              ))}
              <Th align="right">Chưa vào</Th>
            </tr>
          </Thead>
          <Tbody>
            {nhom.map(({ ten, g }) => (
              <Tr key={ten}>
                <Td label="Tài khoản">
                  <span className="font-semibold text-ink">{ten}</span>
                  <span className="block text-ink-3">{g.tong ?? 0} tài khoản</span>
                </Td>
                {t.nguong.map((n) => (
                  <Td key={n} label={`≥${n} ngày`} num>
                    {g[`d${n}`] ?? 0}
                  </Td>
                ))}
                <Td label="Chưa vào" num>
                  {g.chuaTungVao ?? 0}
                </Td>
              </Tr>
            ))}
          </Tbody>
        </TableWrap>
        {ghiChu && <p className="mt-2 text-small text-ink-3">{ghiChu}</p>}

        {t.ds.length > 0 && (
          <details className="group mt-3">
            <summary className="inline-flex min-h-11 cursor-pointer items-center gap-1 text-small text-brand-ink">
              <span
                aria-hidden="true"
                className="inline-block transition-transform group-open:rotate-90 motion-reduce:transition-none"
              >
                ›
              </span>
              Học viên lâu không vào nhất ({t.ds.length})
            </summary>
            <ul className="mt-2 flex flex-col gap-1">
              {t.ds.map((d) => (
                <li key={d.id}>
                  <Link href={`/quan-tri/tai-khoan/${d.id}`} className={DONG_LINK}>
                    <span className="min-w-0">
                      <span className="block text-body text-ink">{d.name || `Tài khoản #${d.id}`}</span>
                      <span className="block text-small text-ink-3">{d.lop || 'Chưa xếp lớp'}</span>
                    </span>
                    <span className="shrink-0 text-small text-ink-2 tabular-nums">{d.ngay} ngày</span>
                  </Link>
                </li>
              ))}
            </ul>
          </details>
        )}
      </Card>
    </div>
  );
}

// ── Kỳ xem (dùng chung cho hai thẻ dưới) ────────────────────────────────────

export function KyXem({ tu, den, termId }: { tu: string; den: string; termId?: string }) {
  const O = 'min-h-11 min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink';
  return (
    /* `<form method="get">` — kỳ xem nằm trên URL (gửi link cho đồng nghiệp là họ
       thấy đúng kỳ ấy), không một dòng JS phía trình duyệt. Cùng khuôn bộ lọc Lớp học. */
    <form
      method="get"
      action="/quan-tri/tong-quan"
      role="search"
      aria-label="Kỳ xem rời lớp và điểm danh"
      className="flex flex-wrap items-end gap-x-3 gap-y-2"
    >
      {termId && <input type="hidden" name="term_id" value={termId} />}
      <label className="flex flex-col gap-1">
        <span className="text-label text-ink-3">Từ ngày</span>
        <input type="date" name="tu" defaultValue={tu} className={O} />
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-label text-ink-3">Đến ngày</span>
        <input type="date" name="den" defaultValue={den} className={O} />
      </label>
      <Button type="submit" variant="ghost">
        Xem
      </Button>
    </form>
  );
}

// ── 3. Rời lớp trong kỳ ─────────────────────────────────────────────────────

/** 'YYYY-MM' → 'T9'. */
const nhanThang = (t: string) => `T${Number(t.slice(5, 7))}`;

export function TheRoiLop({ r }: { r: RoiLop }) {
  const cao = Math.max(1, ...r.theoThang.map((t) => t.tong));
  const lyDo = Object.keys(NHAN_LY_DO_ROI).filter((k) => (r.theoLyDo[k] ?? 0) > 0);
  const loai = Object.keys(LOAI_LOP).filter((k) => (r.theoLoai[k] ?? 0) > 0);
  return (
    <Card>
      <CardHead title="Rời lớp" hint={`${ngayNgan(r.tu)} – ${ngayNgan(r.den)}`} />
      <p className="flex items-baseline gap-2">
        <b className="text-title text-ink tabular-nums">{r.tong}</b>
        <span className="text-small text-ink-3">học viên rời lớp</span>
      </p>
      {lyDo.length > 0 && (
        <p className="mt-2 flex flex-wrap gap-2">
          {lyDo.map((k) => (
            <Chip key={k} tone={TONE_LY_DO[k]}>
              {NHAN_LY_DO_ROI[k]} {r.theoLyDo[k]}
            </Chip>
          ))}
        </p>
      )}
      {loai.length > 0 && (
        <p className="mt-2 text-small text-ink-3">
          {loai.map((k) => `${LOAI_LOP[k]} ${r.theoLoai[k]}`).join(' · ')}
        </p>
      )}

      {/* Sáu tháng gần nhất: MỘT chuỗi số nên một màu, không chú giải — tiêu đề nói
          nó là gì; số in ngay dưới cột (sáu cột, không JS để hiện chú thích khi rê
          chuột) và một dòng chữ ẩn đọc đủ từng tháng cho trình đọc màn hình. Cột neo đáy, 0 thì chỉ còn vạch. */}
      <figure className="mt-4">
        <figcaption className="text-label text-ink-3">Rời lớp theo tháng</figcaption>
        <ol className="mt-2 grid grid-cols-6 items-end gap-2">
          {r.theoThang.map((t, i) => (
            <li key={t.thang} className="flex flex-col items-center gap-1">
              <span className="sr-only">{`Tháng ${Number(t.thang.slice(5, 7))}/${t.thang.slice(0, 4)}: ${t.tong} em`}</span>
              <span aria-hidden="true" className="flex h-16 w-full items-end border-b border-line">
                <span
                  className={`w-full rounded-t-sm ${i === r.theoThang.length - 1 ? 'bg-brand' : 'bg-brand/60'}`}
                  style={{ height: `${Math.round((t.tong / cao) * 100)}%` }}
                />
              </span>
              <span aria-hidden="true" className="text-small text-ink-2 tabular-nums">
                {t.tong}
              </span>
              <span aria-hidden="true" className="text-label text-ink-3">
                {nhanThang(t.thang)}
              </span>
            </li>
          ))}
        </ol>
      </figure>

      {r.ds.length > 0 && (
        <details className="group mt-3">
          <summary className="inline-flex min-h-11 cursor-pointer items-center gap-1 text-small text-brand-ink">
            <span
              aria-hidden="true"
              className="inline-block transition-transform group-open:rotate-90 motion-reduce:transition-none"
            >
              ›
            </span>
            Danh sách ({r.ds.length})
          </summary>
          <ul className="mt-2 flex flex-col gap-1">
            {r.ds.map((d) => (
              <li key={d.id}>
                <Link href={`/quan-tri/tai-khoan/${d.userId}`} className={DONG_LINK}>
                  <span className="min-w-0">
                    <span className="block text-body text-ink">{d.name || `Tài khoản #${d.userId}`}</span>
                    <span className="block text-small text-ink-3">
                      {d.className} · {NHAN_LY_DO_ROI[d.reason ?? 'chuaGhi'] ?? d.reason}
                    </span>
                  </span>
                  <span className="shrink-0 text-small text-ink-2 tabular-nums">{ngayNgan(d.leftOn)}</span>
                </Link>
              </li>
            ))}
          </ul>
        </details>
      )}
    </Card>
  );
}

// ── 4. Điểm danh của giảng viên trong kỳ ────────────────────────────────────

export function TheDiemDanh({ gv, gioMuon }: { gv: GiangVien; gioMuon?: number }) {
  return (
    /* `id` là đích của việc "N buổi điểm danh muộn" ở khối Hôm nay cần làm gì. */
    <div id="diem-danh-gv" className="scroll-mt-20">
      <Card>
        {/* Ngưỡng "muộn" do máy chủ cấp (`TRE_DIEM_DANH_GIO`) — không gõ lại số ở đây. */}
        <CardHead
          title="Điểm danh của giảng viên"
          hint={gioMuon ? `Muộn = ghi sau khi buổi kết thúc quá ${gioMuon} giờ.` : undefined}
        />
        {gv.length === 0 ? (
          <p className="text-small text-ink-3">Chưa có buổi nào trong kỳ.</p>
        ) : (
          <TableWrap caption="Điểm danh của từng giảng viên trong kỳ xem">
            <Thead>
              <tr>
                <Th>Giảng viên</Th>
                <Th align="right">Đã dạy</Th>
                <Th align="right">Đã điểm danh</Th>
                <Th align="right">Chưa</Th>
                <Th align="right">Muộn</Th>
              </tr>
            </Thead>
            <Tbody>
              {gv.map((g) => (
                <Tr key={String(g.teacherId)}>
                  <Td label="Giảng viên">
                    <span className="font-semibold text-ink">
                      {g.teacherId === null ? 'Lớp chưa phân công' : g.name || `Tài khoản #${g.teacherId}`}
                    </span>
                    {g.soLop > 0 && <span className="block text-ink-3">{g.soLop} lớp</span>}
                  </Td>
                  <Td label="Đã dạy" num>
                    {g.buoiDaDay}
                  </Td>
                  <Td label="Đã điểm danh" num>
                    {g.daDiemDanh}
                    {g.tiLe !== null && <span className="text-ink-3"> · {g.tiLe}%</span>}
                  </Td>
                  <Td label="Chưa" num>
                    {g.chuaDiemDanh > 0 ? <Chip tone="warn">{g.chuaDiemDanh}</Chip> : 0}
                  </Td>
                  <Td label="Muộn" num>
                    {g.diemDanhMuon > 0 ? <Chip tone="warn">{g.diemDanhMuon}</Chip> : 0}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </TableWrap>
        )}
      </Card>
    </div>
  );
}
