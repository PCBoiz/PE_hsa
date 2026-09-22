import Link from 'next/link';

import { Card, CardHead, Chip, EmptyState, Tile, TileRow } from '@/components/ui';
import { ngayDayDuVN } from '@/lib/gioVN';
import { serverJson, type HinhDang } from '@/lib/server-api';
import { z } from 'zod';

/**
 * VIỆC HÔM NAY — trang đầu của khu Giảng dạy, gom mọi lớp của người đang đăng nhập.
 *
 * ── VÌ SAO CÓ (14/09/2026, anh Sơn chốt) ──────────────────────────────────
 *
 * Mọi màn giảng dạy trước đó đều gắn với MỘT lớp. Câu "tối qua tôi điểm danh
 * xong chưa, còn bài nào chưa chấm" bắt giảng viên ba lớp mở ba trang. Từ 15/09
 * lớp 1 học thật, nên đây là màn mở mỗi tối.
 *
 * Trang KHÔNG tính gì: mọi con số và mọi ngưỡng (đỏ khi chờ chấm quá N ngày,
 * vắng liền từ N buổi) đến từ `backend/teaching/viec_hom_nay.py`, và cảnh báo
 * "cần chú ý ngay" là CÙNG luật với báo cáo lớp. Trang chỉ xếp và dẫn đường.
 *
 * Mỗi dòng là một việc kèm LỐI VÀO đúng chỗ làm việc ấy: buổi chưa điểm danh
 * mở thẳng sổ điểm danh buổi đó (`?diem-danh=<id>`), bài chưa chấm mở đúng bài.
 */
export const dynamic = 'force-dynamic';
export const metadata = { title: 'Việc hôm nay | TopHSA' };

type Buoi = {
  sessionId: number;
  classId: number;
  className: string;
  startsAt: string | null;
  topic: string | null;
};

type ViecHomNay = {
  troGiang: boolean;
  lop: { id: number; name: string }[];
  nguong: { chamQuaNgay: number; vangLien: number };
  sapToi: (Buoi & { durationMinutes: number | null; thieuLink: boolean })[];
  chuaDiemDanh: { tong: number; ds: (Buoi & { dangDienRa: boolean; conThieu?: number | null })[] };
  chuaCham: {
    assignmentId: number;
    classId: number;
    className: string;
    title: string;
    soBai: number;
    choNgay: number;
    quaHan: boolean;
  }[];
  /** Vắng mặt với trợ giảng — không phải rỗng, mà KHÔNG CÓ. */
  vangLien?: { userId: number; name: string | null; classId: number; className: string; soBuoi: number }[];
  canChuY?: { userId: number; name: string | null; classId: number; className: string; lyDo: string }[];
};

/* Hình dạng `/api/teach/viec-hom-nay` (T18 mức 2). Hai khoá về từng em là
   `optional` đúng nghĩa: trợ giảng KHÔNG có chúng — không phải rỗng. */
const BUOI = {
  sessionId: z.number(), classId: z.number(), className: z.string(),
  startsAt: z.string().nullable(), topic: z.string().nullable(),
};
const EM = { userId: z.number(), name: z.string().nullable(), classId: z.number(), className: z.string() };
const HINH_DANG = z.looseObject({
  troGiang: z.boolean(),
  lop: z.array(z.looseObject({ id: z.number(), name: z.string() })),
  nguong: z.looseObject({ chamQuaNgay: z.number(), vangLien: z.number() }),
  sapToi: z.array(z.looseObject({ ...BUOI, durationMinutes: z.number().nullable(), thieuLink: z.boolean() })),
  chuaDiemDanh: z.looseObject({
    tong: z.number(),
    ds: z.array(z.looseObject({ ...BUOI, dangDienRa: z.boolean(), conThieu: z.number().nullable().optional() })),
  }),
  chuaCham: z.array(z.looseObject({
    assignmentId: z.number(), classId: z.number(), className: z.string(), title: z.string(),
    soBai: z.number(), choNgay: z.number(), quaHan: z.boolean(),
  })),
  vangLien: z.array(z.looseObject({ ...EM, soBuoi: z.number() })).optional(),
  canChuY: z.array(z.looseObject({ ...EM, lyDo: z.string() })).optional(),
}) satisfies HinhDang<ViecHomNay>;

function gio(iso: string | null) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const p = (n: number) => String(n).padStart(2, '0');
  return `${p(d.getDate())}/${p(d.getMonth() + 1)} · ${p(d.getHours())}:${p(d.getMinutes())}`;
}

const LINK = 'inline-flex min-h-11 items-center font-semibold text-brand-ink underline';

/** Một dòng việc: chữ bên trái, lối vào bên phải; xuống hàng ở khổ hẹp. */
function Dong({ children, den, nhan }: { children: React.ReactNode; den: string; nhan: string }) {
  return (
    // Khổ hẹp: lối vào xuống DƯỚI câu việc. Để cạnh nhau thì câu bị ép vào
    // nửa bên trái và gãy làm bốn dòng (ảnh chụp 390px, 14/09/2026).
    <li className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 border-b border-line/50 py-2 last:border-b-0 max-sm:flex-col max-sm:items-start">
      <div className="min-w-0 flex-1 text-body text-ink-2">{children}</div>
      <Link href={den} className={LINK}>
        {nhan} →
      </Link>
    </li>
  );
}

export default async function ViecHomNayPage() {
  const kq = await serverJson<ViecHomNay>('/api/teach/viec-hom-nay', { requireAuth: true }, HINH_DANG);

  if (!kq.ok) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-16">
        <h1 className="text-title text-ink">Không mở được trang này</h1>
        <p className="mt-2 text-body text-ink-2">
          {kq.status === 403 ? 'Khu Giảng dạy dành cho giảng viên, trợ giảng và học vụ.' : kq.message}
        </p>
        <Link href="/dashboard" className={`mt-6 -mx-2 px-2 ${LINK}`}>
          ← Về bảng điều khiển
        </Link>
      </main>
    );
  }

  const d = kq.data;
  const soViec =
    d.chuaDiemDanh.tong + d.chuaCham.length + (d.vangLien?.length ?? 0) + (d.canChuY?.length ?? 0);

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-5 px-4 py-6">
      <div>
        <h1 className="text-section text-ink">Việc hôm nay</h1>
        <p className="mt-1 text-small text-ink-3">
          {/* Ngày HÔM NAY theo giờ VN, dựng ở máy chủ (22/09/2026, agent GV→PH F14). */}
          <span className="text-ink-2">{ngayDayDuVN()}</span>
          {' · '}
          {d.lop.length === 0
            ? 'Bạn chưa phụ trách lớp nào.'
            : `${d.lop.length} lớp: ${d.lop.map((l) => l.name).join(' · ')}`}
        </p>
      </div>

      {/* Tô cảnh báo CHỈ khi lớn hơn 0 — bảng lúc nào cũng đỏ thì mắt bỏ qua. */}
      <TileRow>
        <Tile value={d.sapToi.length} label="buổi trong 24 giờ tới" />
        <Tile value={d.chuaDiemDanh.tong} label="buổi chưa điểm danh" tone={d.chuaDiemDanh.tong > 0 ? 'warn' : 'neutral'} />
        <Tile value={d.chuaCham.length} label="bài chưa chấm" tone={d.chuaCham.length > 0 ? 'warn' : 'neutral'} />
        {d.vangLien && (
          <Tile value={d.vangLien.length} label={`em vắng liền ≥ ${d.nguong.vangLien} buổi`} tone={d.vangLien.length > 0 ? 'warn' : 'neutral'} />
        )}
        {d.canChuY && (
          <Tile value={d.canChuY.length} label="em cần chú ý ngay" tone={d.canChuY.length > 0 ? 'warn' : 'neutral'} />
        )}
      </TileRow>

      {soViec === 0 && d.sapToi.length === 0 && (
        <Card>
          <EmptyState
            title="Không có việc nào đang chờ"
            hint={
              d.lop.length === 0
                ? 'Học vụ gán bạn vào lớp thì việc của lớp ấy sẽ hiện ở đây.'
                : 'Không có buổi nào trong 24 giờ tới, mọi buổi đã qua đều đã điểm danh, không còn bài chờ chấm.'
            }
          />
        </Card>
      )}

      {d.sapToi.length > 0 && (
        <Card>
          <CardHead title="Sắp tới trong 24 giờ" />
          <ul className="flex flex-col">
            {d.sapToi.map((b) => (
              <Dong key={b.sessionId} den={`/giang-day/buoi-hoc/${b.classId}`} nhan="Mở lớp">
                <span className="font-mono tabular-nums text-ink">{gio(b.startsAt)}</span>
                {' · '}
                <span className="text-ink">{b.className}</span>
                {b.topic && ` · ${b.topic}`}
                {b.durationMinutes ? ` · ${b.durationMinutes} phút` : ''}
                {b.thieuLink && (
                  <>
                    {' '}
                    <Chip tone="warn">chưa có link phòng học</Chip>
                  </>
                )}
              </Dong>
            ))}
          </ul>
        </Card>
      )}

      {d.chuaDiemDanh.tong > 0 && (
        <Card>
          <CardHead
            title={`Chưa điểm danh xong (${d.chuaDiemDanh.tong})`}
            hint="Buổi đã bắt đầu mà chưa lưu điểm danh, hoặc đã lưu nhưng còn em chưa được tick. Em chưa tick thì buổi đó không vào chuyên cần của em — và tờ gửi phụ huynh sẽ báo thiếu."
          />
          <ul className="flex flex-col">
            {d.chuaDiemDanh.ds.map((b) => (
              <Dong
                key={b.sessionId}
                den={`/giang-day/buoi-hoc/${b.classId}?diem-danh=${b.sessionId}`}
                nhan="Điểm danh"
              >
                <span className="font-mono tabular-nums text-ink">{gio(b.startsAt)}</span>
                {' · '}
                <span className="text-ink">{b.className}</span>
                {b.topic && ` · ${b.topic}`}
                {b.dangDienRa && (
                  <>
                    {' '}
                    <Chip tone="brand">đang diễn ra</Chip>
                  </>
                )}
                {/* Đã lưu một phần (21/09/2026) — trước đây buổi này không hiện ở
                    đây, trong khi màn Buổi học báo "còn 2 chưa tick". */}
                {b.conThieu ? (
                  <>
                    {' '}
                    <Chip tone="warn">còn {b.conThieu} em chưa tick</Chip>
                  </>
                ) : null}
              </Dong>
            ))}
          </ul>
          {d.chuaDiemDanh.ds.length < d.chuaDiemDanh.tong && (
            <p className="mt-2 text-small text-ink-3">
              Hiện {d.chuaDiemDanh.ds.length} buổi gần nhất trong {d.chuaDiemDanh.tong}.
            </p>
          )}
        </Card>
      )}

      {d.chuaCham.length > 0 && (
        <Card>
          <CardHead
            title={`Bài chưa chấm (${d.chuaCham.length})`}
            hint={`Chờ lâu nhất lên đầu. Đỏ khi bài đã chờ quá ${d.nguong.chamQuaNgay} ngày.`}
          />
          <ul className="flex flex-col">
            {d.chuaCham.map((b) => (
              <Dong key={b.assignmentId} den={`/giang-day/bai-tap/${b.classId}/${b.assignmentId}`} nhan="Chấm">
                <span className="text-ink">{b.title}</span>
                {' · '}
                {b.className} · {b.soBai} bài{' '}
                <Chip tone={b.quaHan ? 'bad' : 'neutral'}>
                  {b.choNgay === 0 ? 'nộp hôm nay' : `chờ ${b.choNgay} ngày`}
                </Chip>
              </Dong>
            ))}
          </ul>
        </Card>
      )}

      {d.vangLien && d.vangLien.length > 0 && (
        <Card>
          <CardHead
            title={`Vắng liền từ ${d.nguong.vangLien} buổi (${d.vangLien.length})`}
            hint="Vắng không phép ở mọi buổi đã điểm danh gần đây. Đây là lúc gọi phụ huynh, trước khi em rơi hẳn."
          />
          <ul className="flex flex-col">
            {d.vangLien.map((e) => (
              <Dong key={`${e.classId}-${e.userId}`} den={`/giang-day/bao-cao/${e.classId}/${e.userId}`} nhan="Xem tờ báo cáo">
                <span className="font-semibold text-ink">{e.name || `#${e.userId}`}</span>
                {' · '}
                {e.className} · <Chip tone="bad">vắng {e.soBuoi} buổi liền</Chip>
              </Dong>
            ))}
          </ul>
        </Card>
      )}

      {d.canChuY && d.canChuY.length > 0 && (
        <Card>
          <CardHead
            title={`Cần chú ý ngay (${d.canChuY.length})`}
            hint="Cùng cảnh báo với báo cáo lớp — không phải một luật riêng của trang này."
          />
          <ul className="flex flex-col">
            {d.canChuY.map((e) => (
              <Dong key={`${e.classId}-${e.userId}`} den={`/giang-day/bao-cao/${e.classId}/${e.userId}`} nhan="Xem tờ báo cáo">
                <span className="font-semibold text-ink">{e.name || `#${e.userId}`}</span>
                {' · '}
                {e.className} · {e.lyDo}
              </Dong>
            ))}
          </ul>
        </Card>
      )}
    </main>
  );
}
