import Link from 'next/link';

import { serverJson } from '@/lib/server-api';

import PrintButton from './PrintButton';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Báo cáo gửi phụ huynh | TopHSA' };

/**
 * Hình dạng do `teaching/parent_report.py:ParentReportView` trả về.
 *
 * CẢNH BÁO đã trả giá một lần ở màn hình buổi học: `serverJson<T>` chỉ ÉP KIỂU,
 * không kiểm gì lúc chạy — kiểu ở đây là lời tự khai về thứ người viết TƯỞNG
 * backend trả. Đổi tên khoá thì phải mở trang thật xem lại.
 */
type BaoCao = {
  student: { id: number; name: string | null; email: string | null; phone: string | null };
  class: { id: number; name: string; code: string | null; teacher: string | null };
  membership: { joinedAt: string | null; leftAt: string | null; status: string; teacherNote: string | null };
  period: { from: string; to: string; weeks: number };
  attendance: {
    sessionsTotal: number;
    sessionsCounted: number;
    sessionsUnmarked: number;
    present: number;
    late: number;
    absent: number;
    excused: number;
    attendedPct: number | null;
  };
  study: {
    lessonsDone: number;
    mockCount: number;
    mockAvg: number | null;
    mockBest: number | null;
    mockTrend: 'up' | 'down' | 'flat' | null;
  };
  topics: {
    weak: { course: string; courseTitle: string | null; topic: string; mastery: number }[];
    strong: { course: string; courseTitle: string | null; topic: string; mastery: number }[];
    measured: number;
    total: number;
    courses: { id: string; title: string; lessonsDone: number; lessonsTotal: number; pct: number }[];
  };
  warnings: string[];
};

function ngay(iso: string) {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

const XU_HUONG = {
  up: 'Điểm thi thử đang đi lên.',
  down: 'Điểm thi thử đang đi xuống — nên xem lại cách ôn.',
  flat: 'Điểm thi thử đang giữ nguyên.',
} as const;

/**
 * Một ô số liệu. Con số luôn đi kèm MẪU SỐ hoặc đơn vị, không đứng một mình:
 * "6/7 buổi" tự giải thích, còn "86%" thì phụ huynh phải đoán 86% của cái gì.
 */
function O({ nhan, so, phu }: { nhan: string; so: string; phu?: string }) {
  return (
    <div className="rounded-md border border-line bg-surface px-4 py-3 print:border-slate-300">
      <p className="text-label text-ink-3">{nhan}</p>
      <p className="mt-1 text-title text-ink tabular-nums">{so}</p>
      {phu && <p className="mt-0.5 text-small text-ink-3">{phu}</p>}
    </div>
  );
}

export default async function BaoCaoPhuHuynhPage({
  params,
  searchParams,
}: {
  params: Promise<{ classId: string; userId: string }>;
  searchParams: Promise<{ from?: string; to?: string }>;
}) {
  const { classId, userId } = await params;
  const { from, to } = await searchParams;
  const qs = new URLSearchParams();
  if (from) qs.set('from', from);
  if (to) qs.set('to', to);

  const bc = await serverJson<BaoCao>(
    `/api/teach/classes/${classId}/students/${userId}/parent-report${qs.size ? `?${qs}` : ''}`,
    { requireAuth: true },
  );

  if (!bc) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="text-title text-ink">Không mở được báo cáo này</h1>
        <p className="mt-2 text-body text-ink-2">
          Học viên không thuộc lớp này, hoặc bạn không phải giảng viên phụ trách lớp đó.
        </p>
        <Link
          href={`/giang-day/buoi-hoc/${classId}`}
          className="mt-6 inline-block text-body text-brand-ink underline"
        >
          ← Về lớp
        </Link>
      </main>
    );
  }

  const { attendance: cc, study: ht, topics: cd } = bc;
  const coMat = cc.present + cc.late;

  return (
    <div className="min-h-dvh bg-ground print:bg-white">
      {/* Thanh điều hướng KHÔNG in ra giấy: tờ gửi phụ huynh không nên có nút
          bấm và đường dẫn quay lại — nó chỉ làm rối và tốn mực. */}
      <header className="border-b border-line bg-surface print:hidden">
        <div className="mx-auto flex max-w-3xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-4">
          <Link
            href={`/giang-day/buoi-hoc/${classId}`}
            className="text-small text-ink-3 hover:text-brand-ink"
          >
            ← Về lớp
          </Link>
          <h1 className="flex-1 text-section text-ink">Báo cáo gửi phụ huynh</h1>
          <PrintButton />
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-6 print:max-w-none print:px-0 print:py-0">
        {bc.warnings.length > 0 && (
          <p
            role="alert"
            className="mb-4 rounded-md bg-warning/10 px-3 py-2 text-small text-warning-ink print:hidden"
          >
            {bc.warnings.join(' ')}
          </p>
        )}

        <article className="rounded-lg border border-line bg-surface p-6 print:border-0 print:p-0">
          <h2 className="text-title text-ink">{bc.student.name || `Học viên #${bc.student.id}`}</h2>
          <p className="mt-1 text-body text-ink-2">
            Lớp {bc.class.name}
            {bc.class.teacher && ` · Giảng viên ${bc.class.teacher}`}
          </p>
          <p className="mt-0.5 text-small text-ink-3">
            Kỳ báo cáo {ngay(bc.period.from)} – {ngay(bc.period.to)} · {bc.membership.status}
          </p>

          {/* ── Chuyên cần ─────────────────────────────────────────────── */}
          <h3 className="mt-6 text-subhead text-ink">Con có đi học không</h3>
          {cc.sessionsCounted === 0 ? (
            <p className="mt-2 text-body text-ink-2">
              {cc.sessionsTotal === 0
                ? 'Kỳ này lớp chưa có buổi học nào.'
                : `Lớp có ${cc.sessionsTotal} buổi trong kỳ nhưng chưa buổi nào được điểm danh, nên chưa có số liệu chuyên cần.`}
            </p>
          ) : (
            <>
              <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
                <O
                  nhan="Có mặt"
                  so={`${coMat}/${cc.sessionsCounted}`}
                  phu={cc.attendedPct !== null ? `${cc.attendedPct}% số buổi` : undefined}
                />
                <O nhan="Đi muộn" so={String(cc.late)} phu="đã tính vào có mặt" />
                <O nhan="Vắng" so={String(cc.absent)} />
                <O nhan="Vắng có phép" so={String(cc.excused)} />
              </div>
              {/* Nói thẳng phần còn thiếu. Im lặng chia cho một mẫu số nhỏ hơn
                  thực tế là cách êm ái nhất để một tờ báo cáo nói dối. */}
              {cc.sessionsUnmarked > 0 && (
                <p className="mt-2 text-small text-ink-3">
                  Còn {cc.sessionsUnmarked} buổi trong kỳ chưa được điểm danh nên không tính vào
                  các con số trên.
                </p>
              )}
            </>
          )}

          {/* ── Học tập ────────────────────────────────────────────────── */}
          <h3 className="mt-6 text-subhead text-ink">Con có tiến bộ không</h3>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
            <O nhan="Bài đã học trong kỳ" so={String(ht.lessonsDone)} phu="bài" />
            <O
              nhan="Đề thi thử đã làm"
              so={String(ht.mockCount)}
              phu={ht.mockCount === 0 ? 'chưa làm đề nào' : 'lượt'}
            />
            <O
              nhan="Điểm trung bình"
              so={ht.mockAvg !== null ? `${ht.mockAvg}%` : '—'}
              phu={
                ht.mockCount === 0
                  ? 'chưa có dữ liệu'
                  : ht.mockCount === 1
                    ? 'của một lượt duy nhất'
                    : `cao nhất ${ht.mockBest}%`
              }
            />
          </div>
          {/* Một lượt thi KHÔNG phải một xu hướng. Nếu để con số đứng trần, một
              em mới thi lần đầu và làm chưa tốt sẽ hiện lên tờ giấy gửi về nhà
              thành "điểm trung bình 0%" in đậm — đúng về số học, nhưng đọc như
              một kết luận về năng lực, mà nó chưa phải. */}
          {ht.mockCount === 1 && (
            <p className="mt-2 text-body text-ink-2">
              Con mới làm một đề nên chưa đủ để nói đang lên hay xuống. Làm thêm vài đề nữa thì
              phần này mới có ý nghĩa.
            </p>
          )}
          {ht.mockTrend && <p className="mt-2 text-body text-ink-2">{XU_HUONG[ht.mockTrend]}</p>}

          {cd.courses.length > 0 && (
            <ul className="mt-3 flex flex-col gap-1">
              {cd.courses.map((c) => (
                <li key={c.id} className="text-small text-ink-2">
                  {c.title}: đã học {c.lessonsDone}/{c.lessonsTotal} bài ({c.pct}%)
                </li>
              ))}
            </ul>
          )}

          {/* ── Chủ đề ─────────────────────────────────────────────────── */}
          <h3 className="mt-6 text-subhead text-ink">Con cần giúp chỗ nào</h3>
          {cd.measured === 0 ? (
            <p className="mt-2 text-body text-ink-2">
              Chưa đủ bài làm để đánh giá từng chủ đề. Con cần làm thêm bài tập và đề thi thử thì
              phần này mới có số liệu.
            </p>
          ) : (
            <div className="mt-3 flex flex-col gap-4">
              {cd.weak.length > 0 && (
                <div>
                  <p className="text-label text-ink-3">Nên tập trung</p>
                  <ul className="mt-1 flex flex-col gap-1">
                    {cd.weak.map((t) => (
                      <li key={`${t.course}-${t.topic}`} className="text-body text-ink-2">
                        {t.topic}
                        {t.courseTitle && ` (${t.courseTitle})`} — đang ở mức {t.mastery}/100
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {/* Điểm mạnh đứng cùng chỗ với điểm yếu, có chủ đích: một tờ giấy
                  chỉ toàn phần kém đọc như bản kiểm điểm, và phụ huynh đọc xong
                  thường quay sang trách con thay vì giúp con. */}
              {cd.strong.length > 0 && (
                <div>
                  <p className="text-label text-ink-3">Con đang làm tốt</p>
                  <ul className="mt-1 flex flex-col gap-1">
                    {cd.strong.map((t) => (
                      <li key={`${t.course}-${t.topic}`} className="text-body text-ink-2">
                        {t.topic}
                        {t.courseTitle && ` (${t.courseTitle})`} — {t.mastery}/100
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {cd.weak.length === 0 && cd.strong.length === 0 && (
                <p className="text-body text-ink-2">
                  Các chủ đề đo được đều ở mức trung bình, chưa có chủ đề nào nổi bật theo hướng
                  nào.
                </p>
              )}
              <p className="text-small text-ink-3">
                Đánh giá dựa trên {cd.measured}/{cd.total} chủ đề đã có bài làm.
              </p>
            </div>
          )}

          {bc.membership.teacherNote && (
            <>
              <h3 className="mt-6 text-subhead text-ink">Nhận xét của giảng viên</h3>
              <p className="mt-2 whitespace-pre-line text-body text-ink-2">
                {bc.membership.teacherNote}
              </p>
            </>
          )}

          <p className="mt-8 border-t border-line pt-3 text-small text-ink-3">
            Báo cáo lập tự động từ dữ liệu học tập trên hệ thống TopHSA. Có chỗ nào chưa rõ, phụ
            huynh liên hệ trực tiếp giảng viên phụ trách lớp.
          </p>
        </article>
      </main>
    </div>
  );
}
