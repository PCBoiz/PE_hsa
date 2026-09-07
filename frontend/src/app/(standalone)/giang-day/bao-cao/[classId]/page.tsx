import Link from 'next/link';

import { Card, CardHead, Chip, EmptyState, TableWrap, Tbody, Td, Th, Thead, Tr } from '@/components/ui';
import { serverJson } from '@/lib/server-api';

import GuiCaLop from './GuiCaLop';

/**
 * Báo cáo phụ huynh CẤP LỚP — soạn sẵn cho cả lớp, gửi bằng một cú bấm.
 *
 * Trước 07/09/2026 khu `bao-cao/` chỉ có cấp học viên, nên gửi báo cáo cho 25
 * em là mở 25 trang, bấm 25 lần, chép 25 đường dẫn. Đó là lý do tính năng ấy
 * chưa từng được dùng cho một lớp thật.
 *
 * Trang này KHÔNG gửi ngay khi mở. Nó hiện bản SOẠN SẴN — ai nhận được, ai
 * thiếu số — rồi chờ một cú bấm (anh Sơn chốt: hệ thống soạn sẵn, NGƯỜI bấm
 * gửi). Xem `backend/teaching/parent_send.py`.
 */
export const dynamic = 'force-dynamic';
export const metadata = { title: 'Báo cáo phụ huynh cả lớp | TopHSA' };

type Em = {
  id: number;
  name: string | null;
  parentName: string;
  parentPhone: string;
  parentEmail: string;
  /** Em này có số hoặc email phụ huynh chưa — GIẢNG VIÊN sửa nếu thiếu. */
  coLienLac: boolean;
  /** Kênh gửi được NGAY BÂY GIỜ, hoặc null nếu chưa cấu hình kênh nào hợp. */
  kenh: 'email' | 'zns' | null;
  guiDuoc: boolean;
};

type SoanSan = {
  period: { from: string; to: string };
  znsSanSang: boolean;
  znsThieu: string[];
  emailSanSang: boolean;
  emailThieu: string[];
  students: Em[];
};

function ngay(iso: string) {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

export default async function BaoCaoCaLopPage({
  params,
}: {
  params: Promise<{ classId: string }>;
}) {
  const { classId } = await params;
  const kq = await serverJson<SoanSan>(
    `/api/teach/classes/${classId}/parent-report/send-all`,
    { requireAuth: true },
  );

  if (!kq.ok) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-16">
        <h1 className="text-title text-ink">Không mở được trang này</h1>
        <p className="mt-2 text-body text-ink-2">{kq.message}</p>
        <Link
          href={`/giang-day/buoi-hoc/${classId}`}
          className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline"
        >
          ← Về lớp
        </Link>
      </main>
    );
  }

  const d = kq.data;
  // HAI danh sách khác nhau, vì hai người khác nhau đi sửa:
  //   · thiếu liên lạc  → giảng viên đi hỏi phụ huynh số hoặc email;
  //   · có liên lạc mà chưa gửi được → người quản trị chưa nối kênh.
  // Gộp lại thành một câu "N em sẽ không nhận được tin" thì người đọc màn hình
  // không biết phải làm gì tiếp.
  const thieu = d.students.filter((e) => !e.coLienLac);
  const ketNoiThieu = d.students.filter((e) => e.coLienLac && !e.guiDuoc);

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-5 px-4 py-6">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <Link
          href={`/giang-day/buoi-hoc/${classId}`}
          className="-my-3 inline-block py-3 text-small text-ink-3 hover:text-brand-ink"
        >
          ← Về lớp
        </Link>
        <h1 className="flex-1 text-section text-ink">Báo cáo gửi phụ huynh</h1>
      </div>

      <Card>
        <CardHead
          title={`Kỳ ${ngay(d.period.from)} – ${ngay(d.period.to)}`}
          hint="Hệ thống soạn sẵn cho từng em. Không có gì được gửi đi cho tới khi bạn bấm nút."
        />

        {/* Nói TRƯỚC ai sẽ bị bỏ qua. Để người ta bấm Gửi rồi mới đọc trong
            kết quả là bắt họ đối chiếu ngược một danh sách. */}
        {thieu.length > 0 && (
          <p className="mb-3 rounded-md border border-warning/30 bg-warning/5 px-3 py-2 text-small text-warning-ink">
            {thieu.length} em chưa có email hoặc số Zalo của phụ huynh nên sẽ không
            nhận được báo cáo: {thieu.map((e) => e.name || `#${e.id}`).join(' · ')}. Các
            em tự điền được ở Cài đặt → Liên hệ phụ huynh.
          </p>
        )}

        {ketNoiThieu.length > 0 && (
          <p className="mb-3 rounded-md border border-line bg-sunken px-3 py-2 text-small text-ink-2">
            {ketNoiThieu.length} em CÓ liên lạc phụ huynh nhưng hệ thống chưa nối được
            kênh tương ứng, nên lượt này chỉ cấp đường dẫn để gửi tay.
            {d.emailThieu.length > 0 && (
              <> Còn thiếu cấu hình email: <code className="font-mono">{d.emailThieu.join(', ')}</code>.</>
            )}
          </p>
        )}

        <GuiCaLop
          classId={classId}
          soEm={d.students.filter((e) => e.guiDuoc).length}
          znsSanSang={d.znsSanSang}
          znsThieu={d.znsThieu}
          emailSanSang={d.emailSanSang}
          emailThieu={d.emailThieu}
        />
      </Card>

      <Card>
        <CardHead title={`Học viên đang học (${d.students.length})`} />
        {d.students.length === 0 ? (
          <EmptyState
            title="Lớp chưa có học viên nào đang học"
            hint="Xếp học viên vào lớp ở khu Vận hành, rồi quay lại đây."
          />
        ) : (
          <TableWrap caption="Học viên của lớp và người nhận báo cáo tương ứng">
            <Thead>
              <tr>
                <Th>Học viên</Th>
                <Th>Người nhận</Th>
                <Th>Số Zalo</Th>
                <Th>Báo cáo</Th>
              </tr>
            </Thead>
            <Tbody>
              {d.students.map((e) => (
                <Tr key={e.id}>
                  <Td label="Học viên">
                    <span className="font-semibold text-ink">{e.name || `#${e.id}`}</span>
                  </Td>
                  <Td label="Người nhận" muted>
                    {e.parentName || (e.guiDuoc ? 'chưa khai tên' : '—')}
                  </Td>
                  <Td label="Số Zalo">
                    {e.guiDuoc ? (
                      <span className="font-mono tabular-nums">{e.parentPhone}</span>
                    ) : (
                      <Chip tone="warn">chưa có</Chip>
                    )}
                  </Td>
                  <Td label="Báo cáo">
                    <Link
                      href={`/giang-day/bao-cao/${classId}/${e.id}`}
                      /* `-my-3.5 py-3.5` cho vùng chạm 48px mà không kéo cao
                         hàng bảng — cùng lối với bảng ở /quan-tri/tong-quan. */
                      className="-my-3.5 inline-block py-3.5 font-semibold text-brand-ink underline"
                    >
                      Xem tờ của em này
                    </Link>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </TableWrap>
        )}
      </Card>
    </main>
  );
}
