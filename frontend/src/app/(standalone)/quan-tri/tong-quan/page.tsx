import Link from 'next/link';

import { Card, CardHead, Chip, EmptyState, TableWrap, Tbody, Td, Th, Thead, Tr } from '@/components/ui';
import { serverJson } from '@/lib/server-api';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Toàn trung tâm | TopHSA' };

type LopRow = {
  id: number;
  code: string | null;
  name: string;
  status: string;
  termName: string | null;
  teacherName: string | null;
  capacity: number | null;
  active: number;
  enrolledEver: number;
  completed: number;
  dropped: number;
  leftUnknown: number;
  dropRate: number | null;
  sessionsHeld: number;
  sessionsMarked: number;
  sessionsUnmarked: number;
  attendedPct: number | null;
  lessonsDone: number;
  progressPct: number | null;
  mockCount: number;
  mockAvg: number | null;
};

type DotRow = {
  termId: number | null;
  termName: string;
  classes: number;
  active: number;
  enrolledEver: number;
  completed: number;
  dropped: number;
  leftUnknown: number;
  attendedPct: number | null;
  dropRate: number | null;
  retentionPct: number | null;
  mockAvg: number | null;
};

type Payload = {
  classes: LopRow[];
  terms: DotRow[];
  summary: {
    classCount: number;
    activeClasses: number;
    active: number;
    enrolledEver: number;
    completed: number;
    dropped: number;
    leftUnknown: number;
    dropRate: number | null;
    retentionPct: number | null;
    attendedPct: number | null;
    sessionsUnmarked: number;
    incomplete: string[];
  };
  thresholds: { good: number; alarm: number };
};

const THIEU_NHAN: Record<string, string> = {
  attendance: 'chuyên cần',
  sessions: 'buổi học',
  study: 'bài học và điểm thi thử',
  lessons: 'tổng số bài của khoá',
};

/** `null` = chưa tính được. Hiện dấu gạch chứ KHÔNG hiện 0 — xem `overview.py`. */
function pct(v: number | null) {
  return v === null ? '—' : `${v}%`;
}

/**
 * Tông màu cho tỉ lệ giữ chân, theo ngưỡng máy chủ gửi xuống.
 *
 * Ngưỡng do backend cấp chứ không viết cứng ở đây: nó là một GIẢ ĐỊNH về mô
 * hình kinh doanh (≥80% khoẻ, <70% báo động — chuẩn ngành dạy thêm), và giả
 * định thì phải nằm một chỗ để còn bàn lại được.
 */
function toneGiuChan(v: number | null, t: { good: number; alarm: number }) {
  if (v === null) return 'neutral' as const;
  if (v >= t.good) return 'good' as const;
  if (v < t.alarm) return 'bad' as const;
  return 'warn' as const;
}

/** Một ô số lớn. Con số luôn kèm chú thích nói nó là gì so với cái gì. */
function O({ nhan, so, phu }: { nhan: string; so: string; phu?: string }) {
  return (
    <div className="rounded-md border border-line bg-surface px-4 py-3">
      <p className="text-label text-ink-3">{nhan}</p>
      <p className="mt-1 text-title text-ink tabular-nums">{so}</p>
      {phu && <p className="mt-0.5 text-small text-ink-3">{phu}</p>}
    </div>
  );
}

/**
 * Bảng điều khiển TOÀN TRUNG TÂM — nửa "Trung tâm" của đặc tả ERP §6.
 *
 * Mọi báo cáo trước hôm nay dừng ở cấp lớp. Quản lý học vụ muốn biết lớp nào
 * đang rơi thì phải mở từng lớp rồi tự cộng trong đầu.
 *
 * Trang này KHÔNG phát minh chỉ số mới: nó cuộn đúng ba thứ mà báo cáo lớp đã
 * đo cho từng em — chuyên cần, tiến độ bài, điểm thi thử — lên cấp lớp rồi cấp
 * đợt. Nhờ vậy con số quản lý nhìn thấy và con số giảng viên nhìn thấy luôn
 * truy được về cùng một gốc; nếu hai bên lệch nhau thì đó là lỗi chứ không phải
 * "hai cách tính".
 */
export default async function TongQuanPage({
  searchParams,
}: {
  searchParams: Promise<{ term_id?: string }>;
}) {
  const { term_id } = await searchParams;
  const kq = await serverJson<Payload>(
    `/api/admin/overview${term_id ? `?term_id=${encodeURIComponent(term_id)}` : ''}`,
    { requireAuth: true },
  );

  if (!kq.ok) {
    return (
      <Card>
        <CardHead title="Toàn trung tâm" />
        <div className="rounded-md border border-danger/30 bg-danger/5 px-4 py-6" role="alert">
          <p className="text-subhead text-ink">Chưa mở được bảng điều khiển</p>
          <p className="mt-1 text-body text-ink-2">{kq.message}</p>
        </div>
      </Card>
    );
  }

  const { classes: lop, terms: dot, summary: s, thresholds: nguong } = kq.data;

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHead
          title="Toàn trung tâm"
          hint="Cuộn số liệu của mọi lớp lên một chỗ. Cùng cách tính với báo cáo từng lớp — nếu hai bên lệch nhau thì đó là lỗi, không phải hai cách đo."
        />

        {/* Mảng dữ liệu KHÔNG đọc được. Phải nói ngay trên đầu: con số bên dưới
            trông vẫn bình thường, nên người đọc không có cách nào tự biết. */}
        {s.incomplete.length > 0 && (
          <p
            role="alert"
            className="mb-4 rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-small text-danger-ink"
          >
            Chưa đọc được: {s.incomplete.map((k) => THIEU_NHAN[k] ?? k).join(' · ')}. Những cột
            liên quan bên dưới đang KHÔNG đáng tin — tải lại trang, nếu vẫn vậy thì báo kỹ thuật.
          </p>
        )}

        <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,190px),1fr))]">
          <O
            nhan="Lớp đang chạy"
            so={String(s.activeClasses)}
            phu={s.classCount !== s.activeClasses ? `trên tổng ${s.classCount} lớp` : 'tất cả'}
          />
          <O nhan="Học viên đang học" so={String(s.active)} phu={`${s.enrolledEver} lượt ghi danh`} />
          <O
            nhan="Giữ chân"
            so={pct(s.retentionPct)}
            phu={
              s.retentionPct === null
                ? 'chưa ai rời lớp có ghi lý do'
                : `${s.completed} học xong / ${s.completed + s.dropped} đã rời lớp`
            }
          />
          <O
            nhan="Chuyên cần"
            so={pct(s.attendedPct)}
            phu={s.attendedPct === null ? 'chưa buổi nào được điểm danh' : 'trên số lượt đã tick'}
          />
        </div>

        {/* Hai con số này là VIỆC CÒN TỒN, không phải thành tích — tách khỏi
            hàng ô trên để mắt không đọc nhầm chúng thành chỉ số. */}
        {(s.sessionsUnmarked > 0 || s.leftUnknown > 0) && (
          <ul className="mt-3 flex flex-col gap-1">
            {s.sessionsUnmarked > 0 && (
              <li className="text-small text-warning-ink">
                {s.sessionsUnmarked} buổi đã dạy nhưng chưa ai điểm danh — chuyên cần ở trên
                đang thiếu đúng ngần ấy buổi.
              </li>
            )}
            {s.leftUnknown > 0 && (
              <li className="text-small text-warning-ink">
                {s.leftUnknown} học viên đã rời lớp mà chưa ghi lý do. Chưa ghi thì hệ thống
                không đoán, nên các em đó không nằm trong tỉ lệ giữ chân.
              </li>
            )}
          </ul>
        )}
      </Card>

      {dot.length > 1 && (
        <Card>
          <CardHead
            title="So sánh theo đợt"
            hint={`Giữ chân từ ${nguong.good}% trở lên là khoẻ; dưới ${nguong.alarm}% là dấu hiệu hỏng ở khâu đón học viên, chất lượng dạy hoặc học phí.`}
          />
          <TableWrap caption="So sánh các đợt học: giữ chân, chuyên cần và điểm thi thử">
            <Thead>
              <tr>
                <Th>Đợt</Th>
                <Th align="right">Lớp</Th>
                <Th align="right">Đang học</Th>
                <Th align="right">Giữ chân</Th>
                <Th align="right">Chuyên cần</Th>
                <Th align="right">Điểm thi thử TB</Th>
              </tr>
            </Thead>
            <Tbody>
              {dot.map((d) => (
                <Tr key={String(d.termId)}>
                  <Td label="Đợt">
                    <span className="font-semibold text-ink">{d.termName}</span>
                  </Td>
                  <Td label="Lớp" num>
                    {d.classes}
                  </Td>
                  <Td label="Đang học" num>
                    {d.active}
                  </Td>
                  <Td label="Giữ chân">
                    <span className="flex justify-end">
                      <Chip tone={toneGiuChan(d.retentionPct, nguong)}>{pct(d.retentionPct)}</Chip>
                    </span>
                  </Td>
                  <Td label="Chuyên cần" num>
                    {pct(d.attendedPct)}
                  </Td>
                  <Td label="Điểm thi thử TB" num>
                    {pct(d.mockAvg)}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </TableWrap>
        </Card>
      )}

      <Card>
        <CardHead title={`Từng lớp (${lop.length})`} />
        {lop.length === 0 ? (
          <EmptyState
            title="Chưa có lớp nào"
            hint="Tạo lớp ở khu Nội dung & lớp, rồi xếp học viên vào. Số liệu ở đây tự có khi lớp bắt đầu học."
          />
        ) : (
          <TableWrap caption="Từng lớp của trung tâm: sĩ số, buổi đã dạy, chuyên cần, tiến độ, điểm thi thử">
            <Thead>
              <tr>
                <Th>Lớp</Th>
                <Th>Giảng viên</Th>
                <Th align="right">Đang học</Th>
                <Th align="right">Buổi đã dạy</Th>
                <Th align="right">Chuyên cần</Th>
                <Th align="right">Tiến độ</Th>
                <Th align="right">Điểm thi thử</Th>
                <Th align="right">Bỏ giữa chừng</Th>
              </tr>
            </Thead>
            <Tbody>
              {lop.map((c) => (
                <Tr key={c.id} dim={c.status !== 'active'}>
                  <Td label="Lớp">
                    <Link
                      href={`/giang-day/buoi-hoc/${c.id}`}
                      className="-my-2 inline-block py-2 font-semibold text-brand-ink underline"
                    >
                      {c.name}
                    </Link>
                    {c.termName && <span className="block text-ink-3">{c.termName}</span>}
                  </Td>
                  <Td label="Giảng viên" muted>
                    {c.teacherName || 'chưa phân công'}
                  </Td>
                  <Td label="Đang học" num>
                    {c.active}
                    {c.capacity ? <span className="text-ink-3">/{c.capacity}</span> : null}
                  </Td>
                  <Td label="Buổi đã dạy" num>
                    {c.sessionsMarked}/{c.sessionsHeld}
                  </Td>
                  <Td label="Chuyên cần" num>
                    {pct(c.attendedPct)}
                  </Td>
                  <Td label="Tiến độ" num>
                    {pct(c.progressPct)}
                  </Td>
                  <Td label="Điểm thi thử" num>
                    {pct(c.mockAvg)}
                  </Td>
                  <Td label="Bỏ giữa chừng" num>
                    {pct(c.dropRate)}
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
