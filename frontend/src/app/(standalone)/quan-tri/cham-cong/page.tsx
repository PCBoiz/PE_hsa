import { Card, CardHead, EmptyState, TableWrap, Tbody, Td, Th, Thead, Tr } from '@/components/ui';
import { serverJson, type HinhDang } from '@/lib/server-api';
import { z } from 'zod';

/**
 * CHẤM CÔNG theo tháng — giảng viên VÀ trợ giảng (V-o, bảng TopHSA dòng 6.3). CHỈ ĐỌC.
 *
 * Số liệu và định nghĩa ở `backend/teaching/cham_cong.py`: buổi đã dạy (không huỷ, đã diễn
 * ra theo sổ), tổng phút, buổi mình điểm danh, điểm danh muộn. Chọn tháng bằng biểu mẫu GET
 * thường — mỗi tháng có đường dẫn riêng, gửi được cho kế toán. Khoá tháng và chỉnh tay chưa
 * có (đợt sau).
 */
export const dynamic = 'force-dynamic';
export const metadata = { title: 'Chấm công | TopHSA' };

type Nguoi = {
  id: number;
  name: string | null;
  email: string | null;
  vai: string;
  soBuoi: number;
  soPhut: number;
  daDiemDanh: number;
  diemDanhMuon: number;
  lop: string[];
};
type Payload = { thang: string; tu: string; den: string; lateHours: number; nguoi: Nguoi[] };

const HINH_DANG = z.looseObject({
  thang: z.string(),
  tu: z.string(),
  den: z.string(),
  lateHours: z.number(),
  nguoi: z.array(z.looseObject({
    id: z.number(), name: z.string().nullable(), email: z.string().nullable(), vai: z.string(),
    soBuoi: z.number(), soPhut: z.number(), daDiemDanh: z.number(), diemDanhMuon: z.number(),
    lop: z.array(z.string()),
  })),
}) satisfies HinhDang<Payload>;

function ngayVN(iso: string) {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

function gio(phut: number) {
  if (!phut) return '0';
  const g = Math.floor(phut / 60);
  const p = phut % 60;
  return p ? `${g} giờ ${p} phút` : `${g} giờ`;
}

export default async function ChamCongPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const thangUrl = ((Array.isArray(sp.thang) ? sp.thang[0] : sp.thang) ?? '').trim();
  const qs = thangUrl ? `?thang=${encodeURIComponent(thangUrl)}` : '';
  const kq = await serverJson<Payload>(`/api/admin/cham-cong${qs}`, { requireAuth: true }, HINH_DANG);
  const d = kq.ok ? kq.data : null;
  const coBuoi = (d?.nguoi ?? []).some((n) => n.soBuoi > 0);

  return (
    <Card>
      <CardHead
        title="Chấm công giảng viên và trợ giảng"
        hint={d ? `Tháng ${d.thang.split('-').reverse().join('/')}: từ ${ngayVN(d.tu)} đến ${ngayVN(d.den)}.` : undefined}
        chiTiet={
          d
            ? `Buổi đã dạy = buổi không huỷ, đã điểm danh hoặc đã đánh dấu xong. Trợ giảng được tính buổi của lớp mình đang được gán lúc buổi diễn ra. Điểm danh muộn = quá ${d.lateHours} giờ sau khi buổi kết thúc.`
            : undefined
        }
        action={
          d ? (
            <a
              href={`/api/admin/cham-cong?thang=${d.thang}&dinh_dang=xlsx`}
              className="inline-flex min-h-11 items-center rounded-md border border-line px-4 text-small font-semibold text-ink-2 hover:border-brand hover:text-brand-ink"
            >
              Tải Excel
            </a>
          ) : undefined
        }
      />

      <form method="get" className="mb-4 flex flex-wrap items-end gap-2">
        <label className="flex min-w-0 flex-col gap-1">
          <span className="text-label text-ink-3">Tháng</span>
          <input
            type="month"
            name="thang"
            defaultValue={d?.thang ?? thangUrl}
            className="min-h-11 min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink"
          />
        </label>
        <button
          type="submit"
          className="min-h-11 rounded-md bg-brand-fill px-4 text-body font-semibold text-white hover:brightness-110"
        >
          Xem
        </button>
      </form>

      {!kq.ok ? (
        <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">
          {kq.message}
        </p>
      ) : !d || d.nguoi.length === 0 ? (
        <EmptyState title="Chưa có giảng viên hay trợ giảng nào" hint="Quản trị viên cấp tài khoản ở trang Tài khoản." />
      ) : (
        <>
          {!coBuoi && (
            <p className="mb-3 rounded-md bg-sunken px-3 py-2 text-small text-ink-2">
              Tháng này chưa có buổi nào được tính: buổi chỉ được tính khi đã điểm danh hoặc đã đánh dấu xong.
            </p>
          )}
          <TableWrap caption={`Chấm công tháng ${d.thang.split('-').reverse().join('/')}, từng giảng viên và trợ giảng`}>
            <Thead>
              <tr>
                <Th>Người dạy</Th>
                <Th align="right">Buổi đã dạy</Th>
                <Th align="right">Thời lượng</Th>
                <Th align="right">Tự điểm danh</Th>
                <Th align="right">Điểm danh muộn</Th>
                <Th>Lớp</Th>
              </tr>
            </Thead>
            <Tbody>
              {d.nguoi.map((n) => (
                <Tr key={n.id} dim={n.soBuoi === 0}>
                  <Td label="Người dạy">
                    <span className="block font-semibold text-ink">{n.name || n.email || `#${n.id}`}</span>
                    <span className="block text-small text-ink-3">{n.vai}</span>
                  </Td>
                  <Td label="Buổi đã dạy" num>
                    {n.soBuoi}
                  </Td>
                  <Td label="Thời lượng" num>
                    {gio(n.soPhut)}
                  </Td>
                  <Td label="Tự điểm danh" num>
                    {n.daDiemDanh}
                  </Td>
                  <Td label="Điểm danh muộn" num>
                    {n.diemDanhMuon}
                  </Td>
                  <Td label="Lớp" muted>
                    {n.lop.length ? n.lop.join(', ') : '—'}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </TableWrap>
        </>
      )}
    </Card>
  );
}
