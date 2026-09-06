import Link from 'next/link';

import { Card, CardHead, Chip, EmptyState, TableWrap, Tbody, Td, Th, Thead, Tr } from '@/components/ui';
import { serverJson } from '@/lib/server-api';

import { ViecCanLam, type Viec } from './ViecCanLam';

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
 * Suy ra VIỆC CÒN TỒN từ đúng payload đang có — không thêm chỉ số, không thêm
 * lượt gọi API. Mỗi việc phải kèm chỗ để LÀM nó; xem `ViecCanLam.tsx`.
 *
 * Thứ tự trong mảng là thứ tự người đọc thấy, nên nó phải là thứ tự ƯU TIÊN
 * thật: việc làm sai CON SỐ đứng trước việc chỉ gây bất tiện. Điểm danh thiếu
 * làm tỉ lệ chuyên cần sai; lý do rời lớp thiếu làm tỉ lệ giữ chân sai — hai
 * cái đó bóp méo chính những con số nằm ngay bên dưới, nên chúng lên đầu.
 */
function suyViec(
  s: Payload['summary'],
  lop: LopRow[],
  nguong: Payload['thresholds'],
): Viec[] {
  const ra: Viec[] = [];

  if (s.sessionsUnmarked > 0) {
    // Trỏ thẳng vào LỚP có buổi chưa điểm danh, không trỏ vào danh sách lớp:
    // một dòng nhắc mà còn bắt người ta đi tìm chỗ làm thì mới đi nửa đường.
    const o = lop.find((c) => c.sessionsUnmarked > 0);
    ra.push({
      nang: 'gap',
      icon: 'clock',
      chu: `${s.sessionsUnmarked} buổi đã dạy chưa ai điểm danh`,
      phu: 'Tỉ lệ chuyên cần bên dưới đang thiếu đúng ngần ấy buổi, nên nó thấp hơn sự thật.',
      href: o ? `/giang-day/buoi-hoc/${o.id}` : '/quan-tri/lop-hoc',
    });
  }

  if (s.leftUnknown > 0) {
    ra.push({
      nang: 'gap',
      icon: 'inbox',
      chu: `${s.leftUnknown} học viên rời lớp mà chưa ghi lý do`,
      phu: 'Chưa ghi thì hệ thống không đoán, nên các em đó không nằm trong tỉ lệ giữ chân.',
      href: '/quan-tri/lop-hoc',
    });
  }

  const chuaGV = lop.filter((c) => c.status === 'active' && !c.teacherName);
  if (chuaGV.length > 0) {
    ra.push({
      nang: 'gap',
      icon: 'users',
      chu: `${chuaGV.length} lớp đang chạy chưa phân công giảng viên`,
      phu: 'Không có giảng viên thì không ai điểm danh và không ai giao bài cho lớp đó.',
      href: '/quan-tri/lop-hoc',
    });
  }

  const quaTai = lop.filter((c) => c.capacity != null && c.active > c.capacity);
  if (quaTai.length > 0) {
    ra.push({
      nang: 'nhac',
      icon: 'graduation-cap',
      chu: `${quaTai.length} lớp đã vượt sĩ số`,
      phu: 'Xếp thêm học viên vào lớp đầy là lý do bỏ giữa chừng hay gặp nhất.',
      href: '/quan-tri/lop-hoc',
    });
  }

  /* `dropRate` là tỉ lệ BỎ, `nguong.alarm` là ngưỡng GIỮ CHÂN — hai chiều
     ngược nhau, nên phải lật: giữ chân dưới 70% tức bỏ từ 30% trở lên. Viết
     phép lật ra thay vì ghi thẳng 30: ngưỡng do máy chủ cấp, và một con số
     chép tay ở đây sẽ không đổi theo khi bên kia đổi. */
  const dangRoi = lop.filter(
    (c) => c.status === 'active' && c.dropRate !== null && c.dropRate >= 100 - nguong.alarm,
  );
  if (dangRoi.length > 0) {
    ra.push({
      nang: 'nhac',
      icon: 'bar-chart',
      chu: `${dangRoi.length} lớp có tỉ lệ bỏ giữa chừng đáng lo`,
      phu: `Giữ chân dưới ${nguong.alarm}% thường là dấu hiệu hỏng ở khâu đón học viên hoặc chất lượng dạy.`,
      href: '/quan-tri/lop-hoc',
    });
  }

  return ra;
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
  const viec = suyViec(s, lop, nguong);

  return (
    <div className="flex flex-col gap-5">
      {/* ── VIỆC TRƯỚC, SỐ SAU ─────────────────────────────────────────────
          Trang này từng mở đầu bằng bốn ô số. Với dữ liệu thật ngày
          07/09/2026 (1 lớp, 2 học viên đang học) màn hình đầu tiên của người
          quản lý là sáu dấu `—` và một ô `0%` — không dấu nào sai, nhưng đọc
          thì y hệt một trang hỏng.

          Người học vụ mở trang này lúc 8 giờ sáng không hỏi "mọi thứ thế nào",
          họ hỏi "hôm nay tôi phải làm gì". Câu ấy trang cũ CÓ trả lời, nhưng
          chôn dưới bảng dưới dạng hai dòng chữ vàng nhỏ. */}
      <Card>
        <CardHead
          title="Hôm nay cần làm gì"
          hint="Việc còn tồn, xếp theo thứ tự việc nào đang làm sai con số bên dưới."
        />

        {/* Mảng dữ liệu KHÔNG đọc được. Đứng trên cả danh sách việc: khi máy
            chủ không đọc nổi một mảng thì chính DANH SÁCH VIỆC cũng thiếu, và
            người đọc không có cách nào tự biết điều đó. */}
        {s.incomplete.length > 0 && (
          <p
            role="alert"
            className="mb-3 rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-small text-danger-ink"
          >
            Chưa đọc được: {s.incomplete.map((k) => THIEU_NHAN[k] ?? k).join(' · ')}. Những cột
            liên quan bên dưới đang KHÔNG đáng tin, và danh sách việc cũng có thể thiếu — tải
            lại trang, nếu vẫn vậy thì báo kỹ thuật.
          </p>
        )}

        <ViecCanLam viec={viec} />
      </Card>

      <Card>
        <CardHead
          title="Toàn trung tâm"
          hint="Cuộn số liệu của mọi lớp lên một chỗ. Cùng cách tính với báo cáo từng lớp — nếu hai bên lệch nhau thì đó là lỗi, không phải hai cách đo."
        />

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

        {/* Hai dòng chữ vàng từng nằm ở đây ("N buổi chưa điểm danh", "N học
            viên rời lớp chưa ghi lý do") đã LÊN khối "Hôm nay cần làm gì" —
            chúng là việc phải làm, không phải chú thích của một bảng số, và ở
            đây thì chúng bấm không được. Không lặp lại ở cả hai chỗ: một việc
            hiện hai lần là người ta làm xong một lần rồi tưởng còn sót. */}
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
                      /* `py-2` cho ra vùng chạm cao 36px — đo 04/09/2026 trên
                         khổ điện thoại, dưới ngưỡng 44px. `py-3.5` cho 48px,
                         và `-my-3.5` giữ nguyên chiều cao hàng bảng. Lấy dư
                         một chút thay vì đúng 44: làm tròn nửa điểm ảnh ở tỉ lệ
                         hiển thị khác là rơi lại xuống dưới ngưỡng. */
                      className="-my-3.5 inline-block py-3.5 font-semibold text-brand-ink underline"
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
