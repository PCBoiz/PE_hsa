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
export type BaoCao = {
  student: { id: number; name: string | null; email?: string | null; phone?: string | null };
  /** Người NHẬN tờ này. Chuỗi rỗng = chưa ai điền. */
  parent: { name: string; phone?: string };
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

export function ToBaoCao({ bc }: { bc: BaoCao }) {
  const { attendance: cc, study: ht, topics: cd } = bc;
  const coMat = cc.present + cc.late;

  return (
      <article className="rounded-lg border border-line bg-surface p-6 print:border-0 print:p-0">
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
            {cc.noRecord > 0 && (
              <p className="mt-1 text-small text-warning-ink">
                {cc.noRecord} buổi đã điểm danh nhưng không có dòng nào cho em — giảng viên
                ghi sót. Những buổi đó không được tính vào tỉ lệ trên; đề nghị bổ sung để
                con số này đầy đủ.
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
  );
}
