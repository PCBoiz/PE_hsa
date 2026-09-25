import Link from 'next/link';

import { Card, CardHead, Chip, EmptyState, TableWrap, Tbody, Td, Th, Thead, Tr } from '@/components/ui';
import { serverJson } from '@/lib/server-api';
import { z } from 'zod';

import {
  CHUONG_TRINH,
  GIANG_VIEN,
  KyXem,
  LOP_THEO_LOAI,
  ROI_LOP,
  TAI_KHOAN_NGU,
  TheChuongTrinh,
  TheDiemDanh,
  TheLop,
  TheRoiLop,
  TheTaiKhoanNgu,
  gioCapNhat,
  type GiangVien,
  type TaiKhoanNgu,
} from './TheTongQuan';
import { ViecCanLam, type Viec } from './ViecCanLam';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Toàn trung tâm | TopHSA' };

/* HÌNH DẠNG phản hồi `/api/admin/overview` (`teaching/overview.py::tong_quan`).
   Kiểu TS suy ra từ đây — một nguồn, không phải một kiểu tay cạnh một hình dạng.
   `looseObject`: máy chủ thêm khoá thì màn hình không hỏng; thiếu khoá màn hình
   ĐỌC mới là lỗi (T18 mức 2, 14/09/2026).
   Khoá của 1.4a (24/09/2026) đều `.optional()`: Vercel và Render deploy riêng, trang
   mới gặp máy chủ cũ thì thẻ mới không vẽ, phần cũ vẫn chạy. Cột thi thử nay cũng
   tuỳ chọn và KHÔNG vẽ nữa (bỏ thi, kế hoạch 1.5) — máy chủ gỡ chúng thì trang này
   không vỡ. */
const so = z.number();
const soHoacTrong = z.number().nullable();
const LOP_ROW = z.looseObject({
  id: so,
  code: z.string().nullable(),
  name: z.string(),
  status: z.string(),
  termName: z.string().nullable(),
  teacherName: z.string().nullable(),
  capacity: soHoacTrong,
  active: so,
  enrolledEver: so,
  completed: so,
  dropped: so,
  leftUnknown: so,
  dropRate: soHoacTrong,
  sessionsHeld: so,
  sessionsMarked: so,
  sessionsUnmarked: so,
  attendedPct: soHoacTrong,
  /* `null` khi máy chủ không đọc được học tập (`overview.py` trả None, không 0) —
     khai `so` như trước thì CẢ TRANG báo lỗi hình dạng đúng lúc một câu tra hỏng. */
  lessonsDone: soHoacTrong,
  progressPct: soHoacTrong,
  mockCount: soHoacTrong.optional(),
  mockAvg: soHoacTrong.optional(),
  classType: z.string().nullable().optional(),
  teacherId: soHoacTrong.optional(),
  activeLearners7d: soHoacTrong.optional(),
});
const DOT_ROW = z.looseObject({
  termId: soHoacTrong,
  termName: z.string(),
  classes: so,
  active: so,
  enrolledEver: so,
  completed: so,
  dropped: so,
  leftUnknown: so,
  attendedPct: soHoacTrong,
  dropRate: soHoacTrong,
  retentionPct: soHoacTrong,
  mockAvg: soHoacTrong.optional(),
});
const HINH_DANG = z.looseObject({
  classes: z.array(LOP_ROW),
  terms: z.array(DOT_ROW),
  summary: z.looseObject({
    classCount: so,
    activeClasses: so,
    active: so,
    enrolledEver: so,
    completed: so,
    dropped: so,
    leftUnknown: so,
    dropRate: soHoacTrong,
    retentionPct: soHoacTrong,
    attendedPct: soHoacTrong,
    sessionsUnmarked: so,
    classesByType: LOP_THEO_LOAI.optional(),
    activeNoTeacher: so.optional(),
    overCapacity: so.optional(),
    dropAlarm: so.optional(),
    incomplete: z.array(z.string()),
  }),
  thresholds: z.looseObject({ good: so, alarm: so, lateHours: so.optional() }),
  classesTotal: so.optional(),
  /* `null` = máy chủ không đọc được khối ấy (tên nó nằm trong `incomplete`). */
  roiLop: ROI_LOP.nullable().optional(),
  giangVien: GIANG_VIEN.nullable().optional(),
  taiKhoanNgu: TAI_KHOAN_NGU.nullable().optional(),
  /* Tiến độ chương trình (E1) — tuỳ chọn: máy chủ trước 25/09/2026 không trả. */
  chuongTrinh: CHUONG_TRINH,
  generatedAt: z.string().optional(),
});
type LopRow = z.infer<typeof LOP_ROW>;
type Payload = z.infer<typeof HINH_DANG>;

const THIEU_NHAN: Record<string, string> = {
  attendance: 'chuyên cần',
  sessions: 'buổi học',
  study: 'bài học',
  lessons: 'tổng số bài của khoá',
  leavers: 'rời lớp',
  teachers: 'điểm danh của giảng viên',
  accounts: 'tài khoản lâu không vào',
  chuongTrinh: 'tiến độ chương trình',
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
  ngu: TaiKhoanNgu | null | undefined,
  gv: GiangVien | null | undefined,
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

  /* Ba số đếm lớp dưới đây lấy từ `summary` khi máy chủ có (1.4a): mảng `lop` nay
     bị cắt còn 50 dòng, đếm trên nó là HỤT đúng lúc trung tâm đông lớp nhất. Máy
     chủ cũ không trả thì đếm trên mảng như trước — lúc ấy mảng còn đủ. */
  const soChuaGV =
    s.activeNoTeacher ?? lop.filter((c) => c.status === 'active' && !c.teacherName).length;
  if (soChuaGV > 0) {
    ra.push({
      nang: 'gap',
      icon: 'users',
      chu: `${soChuaGV} lớp đang chạy chưa phân công giảng viên`,
      phu: 'Không có giảng viên thì không ai điểm danh và không ai giao bài cho lớp đó.',
      href: '/quan-tri/lop-hoc',
    });
  }

  const soQuaTai = s.overCapacity ?? lop.filter((c) => c.capacity != null && c.active > c.capacity).length;
  if (soQuaTai > 0) {
    ra.push({
      nang: 'nhac',
      icon: 'graduation-cap',
      chu: `${soQuaTai} lớp đã vượt sĩ số`,
      phu: 'Xếp thêm học viên vào lớp đầy là lý do bỏ giữa chừng hay gặp nhất.',
      href: '/quan-tri/lop-hoc',
    });
  }

  /* `dropRate` là tỉ lệ BỎ, `nguong.alarm` là ngưỡng GIỮ CHÂN — hai chiều
     ngược nhau, nên phải lật: giữ chân dưới 70% tức bỏ từ 30% trở lên. Viết
     phép lật ra thay vì ghi thẳng 30: ngưỡng do máy chủ cấp, và một con số
     chép tay ở đây sẽ không đổi theo khi bên kia đổi. */
  const soDangRoi =
    s.dropAlarm ??
    lop.filter((c) => c.status === 'active' && c.dropRate !== null && c.dropRate >= 100 - nguong.alarm)
      .length;
  if (soDangRoi > 0) {
    ra.push({
      nang: 'nhac',
      icon: 'bar-chart',
      chu: `${soDangRoi} lớp có tỉ lệ bỏ giữa chừng đáng lo`,
      phu: `Giữ chân dưới ${nguong.alarm}% thường là dấu hiệu hỏng ở khâu đón học viên hoặc chất lượng dạy.`,
      href: '/quan-tri/lop-hoc',
    });
  }

  /* Học viên lâu không vào (1.4a). Mốc lấy từ mảng `nguong` máy chủ gửi (mốc
     GIỮA — 14 ngày theo `NGUONG_NGU`), không gõ lại số: 7 ngày là quá sớm để gọi
     điện (nghỉ một tuần thi học kỳ là thường), 30 ngày thì thường đã muộn. */
  const mocNgu = ngu ? (ngu.nguong[1] ?? ngu.nguong[0]) : undefined;
  const soNgu = ngu && mocNgu !== undefined ? (ngu.hocVien[`d${mocNgu}`] ?? 0) : 0;
  if (soNgu > 0) {
    ra.push({
      nang: 'nhac',
      icon: 'user',
      chu: `${soNgu} học viên ≥${mocNgu} ngày không vào`,
      phu: 'Nghỉ càng lâu càng khó quay lại — nên gọi hỏi thăm sớm.',
      href: '#tai-khoan-ngu',
    });
  }

  /* Điểm danh MUỘN trong kỳ xem (1.4a) — số đã xảy ra, không sửa lại được, nên chỉ
     là "nên làm": nhắc giảng viên. Cộng trên mảng `giangVien` là cộng ĐỦ — máy
     chủ không cắt mảng ấy. Chuyên cần trong báo cáo phụ huynh chỉ đếm buổi ĐÃ
     điểm danh (`parent_report._chuyen_can`), nên báo cáo lập trước lúc tick là
     thiếu đúng buổi ấy. */
  const soMuon = (gv ?? []).reduce((a, g) => a + g.diemDanhMuon, 0);
  if (soMuon > 0) {
    ra.push({
      nang: 'nhac',
      icon: 'clock',
      chu: `${soMuon} buổi điểm danh muộn trong kỳ`,
      phu: 'Nhắc giảng viên điểm danh ngay sau buổi — báo cáo gửi phụ huynh lấy số từ đây.',
      href: '#diem-danh-gv',
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
 * Trang này KHÔNG phát minh chỉ số mới: nó cuộn những thứ mà báo cáo lớp đã
 * đo cho từng em — chuyên cần, tiến độ bài — lên cấp lớp rồi cấp đợt (điểm thi
 * thử thôi vẽ từ 24/09/2026: trung tâm bỏ thi thử). Nhờ vậy con số quản lý nhìn
 * thấy và con số giảng viên nhìn thấy luôn truy được về cùng một gốc; nếu hai bên
 * lệch nhau thì đó là lỗi chứ không phải "hai cách tính".
 *
 * 1.4a (24/09/2026) thêm bốn thẻ cho bốn câu của ghi chú họp TopHSA — xem
 * `TheTongQuan.tsx`.
 */
export default async function TongQuanPage({
  searchParams,
}: {
  searchParams: Promise<{ term_id?: string; tu?: string; den?: string }>;
}) {
  const { term_id, tu, den } = await searchParams;
  /* `tu`/`den` = kỳ xem của "Rời lớp" và "Điểm danh" (form GET ở `KyXem`). Chuyển
     nguyên cho máy chủ — nó kiểm dạng ngày và trả câu lỗi tiếng Việt khi sai. */
  const qs = new URLSearchParams();
  for (const [k, v] of [['term_id', term_id], ['tu', tu], ['den', den]] as const) {
    if (v) qs.set(k, v);
  }
  const chuoi = qs.toString();
  const kq = await serverJson<Payload>(
    `/api/admin/overview${chuoi ? `?${chuoi}` : ''}`,
    { requireAuth: true },
    HINH_DANG,
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
  const { roiLop, giangVien, taiKhoanNgu, chuongTrinh, generatedAt } = kq.data;
  const tongLop = kq.data.classesTotal ?? lop.length;
  const viec = suyViec(s, lop, nguong, taiKhoanNgu, giangVien);

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
          action={
            /* "Báo cáo realtime" của khách: trang không bộ đệm (force-dynamic +
               no-store), mốc này là giờ MÁY CHỦ tính số — tải lại là số mới. */
            generatedAt ? (
              <p className="text-small text-ink-3">Cập nhật lúc {gioCapNhat(generatedAt)}</p>
            ) : undefined
          }
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
          hint="Số liệu mọi lớp gộp một chỗ, cùng cách tính với báo cáo từng lớp."
          chiTiet="Số ở đây lệch với báo cáo của một lớp là lỗi, không phải hai cách đo — báo kỹ thuật."
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

      {/* ── BỐN CÂU CỦA GHI CHÚ HỌP (1.4a) ─────────────────────────────────────
          Hàng trên là HIỆN TRẠNG (lớp, tài khoản); hàng dưới theo KỲ XEM (rời lớp,
          điểm danh) nên form kỳ xem nằm ngay trên nó. Thẻ nào máy chủ không trả
          (máy chủ cũ, hoặc khối ấy hỏng — tên đã nằm trong dòng "Chưa đọc được"
          ở trên) thì không vẽ. */}
      {/* Hàng RIÊNG, không chen vào hàng dưới: ba thẻ một hàng làm bảng "Tài khoản lâu
          không vào" hẹp lại thành vùng cuộn ngang (axe scrollable-region-focusable, đo
          25/09/2026 khi thêm thẻ này). */}
      {chuongTrinh && <TheChuongTrinh c={chuongTrinh} termId={term_id} />}

      {(s.classesByType || taiKhoanNgu) && (
        <div className="grid items-start gap-5 [grid-template-columns:repeat(auto-fit,minmax(min(100%,22rem),1fr))]">
          {s.classesByType && <TheLop theoLoai={s.classesByType} termId={term_id} />}
          {taiKhoanNgu && (
            <TheTaiKhoanNgu t={taiKhoanNgu} homNay={(generatedAt ?? '').slice(0, 10)} />
          )}
        </div>
      )}

      {(roiLop || giangVien) && (
        <div className="flex flex-col gap-3">
          {roiLop && <KyXem tu={roiLop.tu} den={roiLop.den} termId={term_id} />}
          <div className="grid items-start gap-5 [grid-template-columns:repeat(auto-fit,minmax(min(100%,22rem),1fr))]">
            {roiLop && <TheRoiLop r={roiLop} />}
            {giangVien && <TheDiemDanh gv={giangVien} gioMuon={nguong.lateHours} />}
          </div>
        </div>
      )}

      {dot.length > 1 && (
        <Card>
          <CardHead
            title="So sánh theo đợt"
            hint={`Giữ chân từ ${nguong.good}% trở lên là khoẻ; dưới ${nguong.alarm}% là cần xem lại.`}
            chiTiet="Giữ chân thấp thường do khâu đón học viên, chất lượng dạy hoặc học phí."
          />
          <TableWrap caption="So sánh các đợt học: giữ chân và chuyên cần">
            <Thead>
              <tr>
                <Th>Đợt</Th>
                <Th align="right">Lớp</Th>
                <Th align="right">Đang học</Th>
                <Th align="right">Giữ chân</Th>
                <Th align="right">Chuyên cần</Th>
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
                </Tr>
              ))}
            </Tbody>
          </TableWrap>
        </Card>
      )}

      <Card>
        <CardHead
          title={tongLop > lop.length ? `Từng lớp (${lop.length}/${tongLop})` : `Từng lớp (${lop.length})`}
          /* Máy chủ cắt còn 50 lớp, xếp lớp CẦN NHÌN lên đầu (`overview._xep_van_de`). */
          hint={tongLop > lop.length ? 'Lớp cần xem lên đầu. Đủ danh sách ở mục Lớp học.' : undefined}
        />
        {lop.length === 0 ? (
          <EmptyState
            title="Chưa có lớp nào"
            hint="Tạo lớp ở mục Lớp học rồi xếp học viên vào. Số liệu tự có khi lớp bắt đầu học."
          />
        ) : (
          <TableWrap caption="Từng lớp của trung tâm: sĩ số, buổi đã dạy, chuyên cần, tiến độ, số em học trong 7 ngày">
            <Thead>
              <tr>
                <Th>Lớp</Th>
                <Th>Giảng viên</Th>
                <Th align="right">Đang học</Th>
                <Th align="right">Buổi đã dạy</Th>
                <Th align="right">Chuyên cần</Th>
                <Th align="right">Tiến độ</Th>
                <Th align="right">Học 7 ngày</Th>
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
                  <Td label="Học 7 ngày" num>
                    {/* Số em đang học có hoạt động học trong 7 ngày / sĩ số đang học.
                        Máy chủ cũ không trả → dấu gạch, không đoán 0. */}
                    {c.activeLearners7d == null ? '—' : `${c.activeLearners7d}/${c.active}`}
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
