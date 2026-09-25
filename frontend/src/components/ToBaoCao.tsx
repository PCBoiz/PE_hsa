/**
 * TỜ BÁO CÁO gửi phụ huynh — phần THÂN, dùng chung cho hai đường vào.
 *
 * ── VÌ SAO TÁCH RA (07/09/2026) ───────────────────────────────────────────
 *
 * Nay có HAI đường tới cùng tờ giấy này:
 *
 *   /giang-day/bao-cao/<lop>/<em>   giảng viên xem, sau cổng đăng nhập
 *   /bc/<chia>                      phụ huynh mở từ tin Zalo, không tài khoản
 *
 * Hai đường mà hai bản dựng thì chúng sẽ trôi khỏi nhau — và kiểu trôi tệ nhất
 * ở đây không phải lệch chữ, mà là một bên sửa cách tính chuyên cần còn bên
 * kia không, tức phụ huynh và giảng viên đọc hai con số khác nhau về cùng một
 * đứa trẻ, rồi cãi nhau về việc ai đúng.
 *
 * ── KIỂU DỮ LIỆU CỐ Ý NỚI Ở BA CHỖ ───────────────────────────────────────
 *
 * `student.email`, `student.phone`, `parent.phone` là `?` vì tờ đi qua chìa
 * KHÔNG mang chúng (`teaching/parent_report.py::rut_gon_cho_link`). Component
 * này không đọc tới chúng, nên nới kiểu là đúng — và nếu ai đó thêm một chỗ
 * hiển thị email vào đây, `tsc` sẽ bắt ngay vì kiểu nói rõ nó có thể vắng.
 */
import { cauTienDoEm } from '@/lib/tienDoChu';

export type BaoCao = {
  student: { id: number; name: string | null; email?: string | null; phone?: string | null };
  /** Người NHẬN tờ này. Chuỗi rỗng = chưa ai điền. `phone`/`email` vắng ở tờ đi qua chìa. */
  parent: { name: string; phone?: string; email?: string };
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
    /** Buổi CẢ LỚP đã tick nhưng em này KHÔNG có dòng nào — giảng viên sót. */
    noRecord: number;
    attendedPct: number | null;
  };
  study: {
    lessonsDone: number;
    mockCount: number;
    mockAvg: number | null;
    mockBest: number | null;
    mockTrend: 'up' | 'down' | 'flat' | null;
  };
  /**
   * TỪ 24/09/2026 KHÔNG VẼ (bỏ thi, pha A) — `study.mock*` cũng vậy. Kiểu giữ vì
   * máy chủ còn gửi; pha B bỏ khoá ở máy chủ SAU khi màn hình thôi đọc.
   *
   * Kỳ thi thử THẬT tại trung tâm, nhập từ tờ PDF của hệ thống khảo thí.
   * `null` khi chưa nhập tờ nào — giấu hẳn khối ấy đi, đừng hiện "chưa có dữ
   * liệu" cho một thứ phụ huynh còn không biết là có tồn tại.
   *
   * Thang điểm KHÁC `study.mockAvg` (phần trăm, luyện tập trong ứng dụng), nên
   * khối này tự nói ra thang của nó.
   */
  centerExam?: {
    date: string;
    round: string | null;
    score: number;
    max: number;
    sections: { phan: number; ten: string; diem: number; toiDa: number }[];
    weakUnits: { phan: number; ten: string; pct: number }[];
    unitsMeasured: number;
    previous: { date: string; round: string | null; score: number; delta: number } | null;
  } | null;
  /**
   * Nhịp học TỪNG TUẦN trong kỳ (17/09/2026) — `teaching/parent_report.py::_nhip_tuan`.
   * Mỗi hàng là một khối 7 ngày kết thúc ở ngày cuối kỳ (khối đầu có thể dài hơn,
   * `days` nói ra). `optional` vì một bản dựng cũ của máy chủ chưa gửi khoá này —
   * thiếu nó KHÔNG được làm hỏng tờ báo cáo phụ huynh đang mở trên điện thoại.
   */
  weekly?: {
    weeks: {
      from: string;
      to: string;
      days: number;
      /** Có mặt (kể cả muộn) / buổi có dòng điểm danh của em — cùng mẫu số với `attendedPct`. */
      attended: number;
      attendanceCounted: number;
      lessons: number;
      drills: number;
      /** Bài tập của lớp em NỘP trong tuần (theo ngày nộp, không theo ngày chấm). */
      submissions: number;
    }[];
    /** Số tuần cũ không in vì kỳ quá dài. */
    omitted: number;
  } | null;
  /**
   * Bài giảng viên giao cho lớp trong kỳ, kèm điểm + nhận xét (20/09/2026) —
   * `parent_report._bai_tap_lop`. `optional`: bản dựng cũ của máy chủ chưa gửi.
   */
  assignments?: {
    id: number;
    title: string;
    topic: string | null;
    dueAt: string | null;
    maxScore: number | null;
    submittedAt: string | null;
    score: number | null;
    feedback: string | null;
    gradedAt: string | null;
  }[];
  /** % chương trình em đã học tới hôm nay (E1). null: lớp chưa nhận khung; thiếu: máy chủ cũ. */
  chuongTrinh?: { pct: number | null; keHoachPct: number | null } | null;
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

/** "11/09" — cột tuần hẹp, năm đã có ở dòng kỳ báo cáo phía trên. */
function ngayNgan(iso: string) {
  // `slice(0, 10)`: hạn nộp và ngày nộp là DATETIME ("2026-09-25T23:59:00"),
  // tách thẳng bằng '-' thì ra "25T23:59:00/09".
  const [, m, d] = iso.slice(0, 10).split('-');
  return `${d}/${m}`;
}

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

/**
 * `choPhuHuynh`: tờ đang mở ở đường dẫn CÔNG KHAI gửi phụ huynh (`/bc/<chìa>`).
 * Cùng một tờ phục vụ ba nơi (màn giảng viên, tờ phụ huynh, bản mẫu trang chủ),
 * nhưng có câu chỉ dành cho người trong trung tâm — xem khối "chưa có dòng".
 */
export function ToBaoCao({ bc, choPhuHuynh = false }: { bc: BaoCao; choPhuHuynh?: boolean }) {
  const { attendance: cc, study: ht, topics: cd } = bc;
  const coMat = cc.present + cc.late;
  const tuan = bc.weekly?.weeks ?? [];
  // Cả kỳ không một buổi được điểm danh, không một bài, một lượt luyện, một bài nộp:
  // một bảng toàn "—" và "0" chỉ bắt phụ huynh đọc bốn hàng để ra một câu.
  const tuanTrong = tuan.every(
    (w) => !w.attendanceCounted && !w.lessons && !w.drills && !w.submissions,
  );

  /* `print:[&_h3]:break-after-avoid`: khi IN, tiêu đề mục không được ở lại cuối trang một
     mình. Soi bản in 17/09/2026: "Con có học đều không" nằm cuối trang 1 còn bảng nhịp
     từng tuần sang trang 2 — người đọc phải lật trang mới biết bảng ấy thuộc về đâu.
     `print:[&_h3]:mt-3` (22/09/2026, agent GV→PH F15): in A4, tờ tràn sang trang 2 chỉ
     để chứa mục "Con cần giúp chỗ nào" (3 dòng) + chân trang. Khoảng cách trước mỗi
     mục ở màn hình (1,5rem) là thứ rẻ nhất để bớt khi in. */
  return (
      <article className="rounded-lg border border-line bg-surface p-6 print:border-0 print:p-0 print:[&_h3]:break-after-avoid print:[&_h3]:mt-3">
        <h2 className="text-title text-ink">{bc.student.name || `Học viên #${bc.student.id}`}</h2>
        <p className="mt-1 text-body text-ink-2">
          Lớp {bc.class.name}
          {bc.class.teacher && ` · Giảng viên ${bc.class.teacher}`}
        </p>
        {/* Lời chào trên tờ IN. Chỉ hiện khi đã biết tên: "Kính gửi quý phụ
            huynh" thì thừa — người nhận biết tờ này gửi cho mình. */}
        {bc.parent.name && (
          <p className="mt-2 text-body text-ink-2">Kính gửi ông/bà {bc.parent.name},</p>
        )}
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
              {/* Mẫu số PHẢI là số buổi em ấy có dòng, khớp với `attendedPct`
                  (công thức ở `attendance.ti_le`). Ghi `sessionsCounted` ở đây
                  trong khi phần trăm tính trên một mẫu số khác là hai con số
                  cạnh nhau không chia ra nhau được — người đọc tự nhân chia
                  rồi kết luận tờ giấy sai. */}
              <O
                nhan="Có mặt"
                so={`${coMat}/${cc.sessionsCounted - cc.noRecord}`}
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
            {/* Khoảng trống KHÁC hẳn ở trên: buổi đó lớp ĐÃ được điểm danh,
                chỉ riêng em này bị sót. Không nói ra thì bốn ô cộng lại không
                bằng số buổi, và người đọc tưởng tờ giấy tính sai — trong khi
                cái sai nằm ở sổ điểm danh. */}
            {/* HAI CÂU CHO HAI NGƯỜI ĐỌC (21/09/2026). Câu "giảng viên ghi sót…
                đề nghị bổ sung" là lời nhắc việc NỘI BỘ — agent rà giảng viên thấy
                nó nằm ngay màn đầu tờ công khai gửi phụ huynh ở 390, thành chữ vàng
                sáng ở chế độ tối, và cả trên bản in: trung tâm tự tố mình với
                người trả tiền. Phụ huynh vẫn cần biết con số chưa đủ (im lặng là
                nói dối), nhưng bằng câu trung tính, không đổ lỗi, không giao việc. */}
            {cc.noRecord > 0 && (choPhuHuynh ? (
              <p className="mt-1 text-small text-ink-3">
                Có {cc.noRecord} buổi trung tâm đang cập nhật điểm danh cho em; những buổi này
                chưa tính vào tỉ lệ trên.
              </p>
            ) : (
              <p className="mt-1 text-small text-warning-ink">
                {cc.noRecord} buổi đã điểm danh nhưng không có dòng nào cho em — giảng viên
                ghi sót. Những buổi đó không được tính vào tỉ lệ trên; đề nghị bổ sung để
                con số này đầy đủ.
              </p>
            ))}
          </>
        )}

        {/* ── Tiến độ chương trình (E1, 25/09/2026) — tính tới hôm nay, chỉ buổi em có
            mặt hoặc đi muộn (`chuong_trinh/tien_do.py`). Lớp chưa có khung: không vẽ. */}
        {bc.chuongTrinh && (
          <>
            <h3 className="mt-6 text-subhead text-ink">Tiến độ chương trình</h3>
            <p className="mt-2 text-body text-ink-2">{cauTienDoEm(bc.chuongTrinh)}</p>
          </>
        )}

        {/* ── Thi thử: GỠ 24/09/2026 (bỏ thi, pha A) ─────────────────────
            Anh Sơn chốt "bỏ mọi thứ về thi, giữ ngày thi HSA". Tờ này thôi vẽ khối
            "Kỳ thi thử tại trung tâm" (`centerExam`, điểm nhập từ PDF khảo thí) và
            hai ô "Đề thi thử đã làm" / "Điểm thi thử trung bình" cùng câu xu hướng.
            Khoá dữ liệu vẫn nằm trong `BaoCao` vì máy chủ còn gửi; pha B thay khối
            này bằng tiến trình học tập (phút học, số ngày có hoạt động…) rồi mới
            bỏ khoá ở máy chủ. */}

        {/* ── Học tập ────────────────────────────────────────────────── */}
        <h3 className="mt-6 text-subhead text-ink">Con có tiến bộ không</h3>
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
          <O nhan="Bài đã học trong kỳ" so={String(ht.lessonsDone)} phu="bài" />
        </div>

        {cd.courses.length > 0 && (
          <ul className="mt-3 flex flex-col gap-1">
            {cd.courses.map((c) => (
              <li key={c.id} className="text-small text-ink-2">
                {c.title}: đã học {c.lessonsDone}/{c.lessonsTotal} bài ({c.pct}%)
              </li>
            ))}
          </ul>
        )}

        {/* ── Nhịp từng tuần ─────────────────────────────────────────────
            Tổng cả kỳ không phân biệt "mỗi tuần 3 bài" với "11 bài dồn vào tuần
            cuối" — mà với phụ huynh đó là hai chuyện khác hẳn. Bảng thật chứ
            không phải thẻ: bốn tuần × bốn cột đọc theo HÀNG để so tuần này với
            tuần trước, và in ra giấy vẫn thẳng cột. */}
        {tuan.length > 0 && (
          <>
            <h3 className="mt-6 text-subhead text-ink">Con có học đều không</h3>
            {tuanTrong ? (
              <p className="mt-2 text-body text-ink-2">
                Trong kỳ này chưa có buổi học nào được điểm danh, và con chưa học bài hay làm bài
                tập nào trên hệ thống.
              </p>
            ) : (
              <>
                <div className="mt-3 overflow-x-auto">
                  <table className="w-full border-collapse text-small tabular-nums">
                    <caption className="sr-only">
                      Hoạt động học tập của con theo từng tuần trong kỳ báo cáo
                    </caption>
                    <thead>
                      {/* Tiêu đề hai chữ, căn ĐÁY: khổ điện thoại cột số hẹp nên chữ
                          xuống dòng — hai chữ thì mọi cột cùng gãy đúng một chỗ, thay
                          vì "Bài tập nộp" ba dòng cạnh "Tuần" một dòng (soi ảnh 17/09). */}
                      <tr className="border-b border-line align-bottom text-ink-3">
                        <th scope="col" className="py-2 pr-2 text-left font-semibold">Tuần</th>
                        <th scope="col" className="px-1.5 py-2 text-right font-semibold">Đi học</th>
                        <th scope="col" className="px-1.5 py-2 text-right font-semibold">Bài học</th>
                        <th scope="col" className="px-1.5 py-2 text-right font-semibold">Luyện tập</th>
                        <th scope="col" className="py-2 pl-1.5 text-right font-semibold">Bài tập</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tuan.map((w) => (
                        <tr key={w.from} className="border-b border-line last:border-0">
                          <th scope="row" className="py-2 pr-2 text-left font-normal text-ink-2">
                            <span className="whitespace-nowrap">
                              {ngayNgan(w.from)}–{ngayNgan(w.to)}
                            </span>
                            {w.days !== 7 && (
                              <span className="block text-caption text-ink-3">{w.days} ngày</span>
                            )}
                          </th>
                          <td className="px-1.5 py-2 text-right text-ink">
                            {w.attendanceCounted ? `${w.attended}/${w.attendanceCounted}` : '—'}
                          </td>
                          {[w.lessons, w.drills].map((n, i) => (
                            <td
                              key={i}
                              className={`px-1.5 py-2 text-right ${n ? 'text-ink' : 'text-ink-3'}`}
                            >
                              {n}
                            </td>
                          ))}
                          <td className={`py-2 pl-1.5 text-right ${w.submissions ? 'text-ink' : 'text-ink-3'}`}>
                            {w.submissions}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="mt-2 text-caption text-ink-3">
                  Mỗi hàng là 7 ngày liền, hàng cuối kết thúc ở ngày cuối kỳ. Đi học: số buổi có
                  mặt trên số buổi đã điểm danh (“—” là tuần chưa có buổi nào được điểm danh).
                  Luyện tập: số lượt vào phòng luyện bấm giờ. Bài tập: bài tập của lớp con đã nộp.
                  {bc.weekly && bc.weekly.omitted > 0 &&
                    ` Kỳ dài nên chỉ in ${tuan.length} tuần gần nhất, bỏ ${bc.weekly.omitted} tuần đầu.`}
                </p>
              </>
            )}
          </>
        )}

        {/* ── Bài tập giảng viên giao ────────────────────────────────── */}
        {/* Thứ duy nhất trên tờ này do một con người đọc và chấm. Không có
            bài trong kỳ thì giấu hẳn — không in "chưa có" cho một mục phụ
            huynh chưa biết là có. */}
        {bc.assignments && bc.assignments.length > 0 && (
          <>
            <h3 className="mt-6 text-subhead text-ink">Bài tập giảng viên giao</h3>
            <div className="mt-2 overflow-x-auto">
              <table className="w-full text-small">
                <thead>
                  <tr className="text-left text-label text-ink-3">
                    <th className="py-1 pr-3 font-medium">Bài</th>
                    <th className="py-1 pr-3 font-medium">Hạn nộp</th>
                    <th className="py-1 pr-3 font-medium">Nộp</th>
                    <th className="py-1 pr-3 text-right font-medium">Điểm</th>
                  </tr>
                </thead>
                <tbody>
                  {bc.assignments.map((b) => (
                    <tr key={b.id} className="border-t border-line align-top">
                      <td className="py-1.5 pr-3 text-ink">
                        {b.title}
                        {b.feedback && (
                          <span className="block text-ink-2">
                            Nhận xét: {b.feedback}
                          </span>
                        )}
                      </td>
                      <td className="py-1.5 pr-3 text-ink-2 whitespace-nowrap">
                        {b.dueAt ? ngayNgan(b.dueAt) : '—'}
                      </td>
                      <td className="py-1.5 pr-3 text-ink-2 whitespace-nowrap">
                        {b.submittedAt ? ngayNgan(b.submittedAt) : 'chưa nộp'}
                      </td>
                      <td className="py-1.5 text-right tabular-nums text-ink whitespace-nowrap">
                        {b.score !== null
                          ? `${b.score}/${b.maxScore ?? 10}`
                          : b.submittedAt
                            ? 'chờ chấm'
                            : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {/* ── Chủ đề ─────────────────────────────────────────────────── */}
        <h3 className="mt-6 text-subhead text-ink">Con cần giúp chỗ nào</h3>
        {cd.measured === 0 ? (
          <p className="mt-2 text-body text-ink-2">
            Chưa đủ bài làm để đánh giá từng chủ đề. Con cần học và luyện tập thêm trên hệ
            thống thì phần này mới có số liệu.
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
  );
}
