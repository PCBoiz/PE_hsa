'use client';

// Khảo sát đầu vào HSA (ProgrammingEdu × TopHSA): 6 câu hồ sơ + 6 câu mini-test
// chẩn đoán (2/hợp phần). Backend chấm mini-test + sinh lộ trình cá nhân hoá.
// Logic step/validate/submit ở questionaire.js.

import PageStyles from '@/components/PageStyles';
import LegacyScripts from '@/components/LegacyScripts';

const SCRIPTS = ['/static/js/main.js', '/static/js/questionaire.js'];

export default function QuestionairePage() {
  return (
    <>
      <PageStyles hrefs={["/static/css/questionaire.css","/static/css/a11y.css"]} />
      <title>Khảo sát đầu vào — ProgrammingEdu × TopHSA</title>

      <div className="survey-container">
        <div className="tech-logo">
          <span className="logo-text">ProgrammingEdu × TopHSA</span>
        </div>

        <div className="progress-container">
          <div className="progress-bar" id="progressBar"></div>
        </div>

        <form id="surveyForm">
          {/* ══════ PHẦN 1: HỒ SƠ & MỤC TIÊU ══════ */}

          {/* Q1 — Mục tiêu điểm */}
          <div className="step active">
            <div className="question-block">
              <p className="question">1. Mục tiêu điểm HSA của bạn là bao nhiêu?</p>
              <label className="option"><input type="radio" name="target_score" value="Dưới 75" /> Dưới 75 điểm</label>
              <label className="option"><input type="radio" name="target_score" value="75–90" /> 75 – 90 điểm</label>
              <label className="option"><input type="radio" name="target_score" value="90–105" /> 90 – 105 điểm</label>
              <label className="option"><input type="radio" name="target_score" value="Trên 105" /> Trên 105 điểm</label>
            </div>
            <div className="btn-group">
              <button type="button" className="next-btn">Tiếp tục</button>
            </div>
          </div>

          {/* Q2 — Khối ngành xét tuyển */}
          <div className="step">
            <div className="question-block">
              <p className="question">2. Bạn dùng kết quả HSA để xét tuyển khối ngành nào?</p>
              <label className="option"><input type="radio" name="target_major" value="Kinh tế – Quản lý" /> Kinh tế – Quản lý</label>
              <label className="option"><input type="radio" name="target_major" value="Kỹ thuật – Công nghệ" /> Kỹ thuật – Công nghệ</label>
              <label className="option"><input type="radio" name="target_major" value="Khoa học tự nhiên" /> Khoa học tự nhiên</label>
              <label className="option"><input type="radio" name="target_major" value="Khoa học xã hội – Nhân văn" /> Khoa học xã hội – Nhân văn</label>
              <label className="option"><input type="radio" name="target_major" value="Y – Dược" /> Y – Dược</label>
              <label className="option"><input type="radio" name="target_major" value="Chưa xác định" /> Chưa xác định</label>
            </div>
            <div className="btn-group">
              <button type="button" className="prev-btn">Quay lại</button>
              <button type="button" className="next-btn">Tiếp tục</button>
            </div>
          </div>

          {/* Q3 — Thời điểm thi */}
          <div className="step">
            <div className="question-block">
              <p className="question">3. Bạn dự định thi HSA khi nào?</p>
              <label className="option"><input type="radio" name="exam_timing" value="Trong 1 tháng" /> Trong 1 tháng</label>
              <label className="option"><input type="radio" name="exam_timing" value="1–3 tháng" /> 1 – 3 tháng</label>
              <label className="option"><input type="radio" name="exam_timing" value="3–6 tháng" /> 3 – 6 tháng</label>
              <label className="option"><input type="radio" name="exam_timing" value="Trên 6 tháng" /> Trên 6 tháng</label>
            </div>
            <div className="btn-group">
              <button type="button" className="prev-btn">Quay lại</button>
              <button type="button" className="next-btn">Tiếp tục</button>
            </div>
          </div>

          {/* Q4 — Chọn hợp phần 3 */}
          <div className="step">
            <div className="question-block">
              <p className="question">4. Hợp phần thứ 3 bạn chọn làm bài là gì?</p>
              <label className="option"><input type="radio" name="section3_choice" value="Khoa học" /> Khoa học (Tự nhiên – Xã hội)</label>
              <label className="option"><input type="radio" name="section3_choice" value="Tiếng Anh" /> Tiếng Anh</label>
              <label className="option"><input type="radio" name="section3_choice" value="Chưa quyết định" /> Chưa quyết định</label>
            </div>
            <div className="btn-group">
              <button type="button" className="prev-btn">Quay lại</button>
              <button type="button" className="next-btn">Tiếp tục</button>
            </div>
          </div>

          {/* Q5 — Thời gian ôn mỗi ngày */}
          <div className="step">
            <div className="question-block">
              <p className="question">5. Bạn có thể dành bao nhiêu thời gian ôn mỗi ngày?</p>
              <label className="option"><input type="radio" name="study_time" value="Dưới 1 giờ" /> Dưới 1 giờ</label>
              <label className="option"><input type="radio" name="study_time" value="1–2 giờ" /> 1 – 2 giờ</label>
              <label className="option"><input type="radio" name="study_time" value="2–3 giờ" /> 2 – 3 giờ</label>
              <label className="option"><input type="radio" name="study_time" value="Trên 3 giờ" /> Trên 3 giờ</label>
            </div>
            <div className="btn-group">
              <button type="button" className="prev-btn">Quay lại</button>
              <button type="button" className="next-btn">Tiếp tục</button>
            </div>
          </div>

          {/* Q6 — Tự đánh giá hợp phần yếu */}
          <div className="step">
            <div className="question-block">
              <p className="question">6. Bạn tự thấy mình yếu nhất ở hợp phần nào?
                <span className="note">(Chọn tối đa 2)</span>
              </p>
              <label className="option"><input type="checkbox" name="self_weak" value="Định lượng" /> Tư duy Định lượng (Toán)</label>
              <label className="option"><input type="checkbox" name="self_weak" value="Định tính" /> Tư duy Định tính (Ngữ văn – Ngôn ngữ)</label>
              <label className="option"><input type="checkbox" name="self_weak" value="Khoa học" /> Khoa học / Tiếng Anh</label>
            </div>
            <div className="btn-group">
              <button type="button" className="prev-btn">Quay lại</button>
              <button type="button" className="next-btn">Tiếp tục</button>
            </div>
          </div>

          {/* ══════ PHẦN 2: MINI-TEST CHẨN ĐOÁN ══════ */}

          {/* Q7 — Định lượng 1 */}
          <div className="step">
            <div className="question-block">
              <p className="question"><span className="note">🧪 Mini-test · Định lượng</span><br />
                7. Giá trị của biểu thức 2³ + 3² bằng bao nhiêu?</p>
              <label className="option"><input type="radio" name="dq_ql_1" value="A" /> 15</label>
              <label className="option"><input type="radio" name="dq_ql_1" value="B" /> 16</label>
              <label className="option"><input type="radio" name="dq_ql_1" value="C" /> 17</label>
              <label className="option"><input type="radio" name="dq_ql_1" value="D" /> 18</label>
            </div>
            <div className="btn-group">
              <button type="button" className="prev-btn">Quay lại</button>
              <button type="button" className="next-btn">Tiếp tục</button>
            </div>
          </div>

          {/* Q8 — Định lượng 2 */}
          <div className="step">
            <div className="question-block">
              <p className="question"><span className="note">🧪 Mini-test · Định lượng</span><br />
                8. Một số tăng 20% rồi lại giảm 20%. So với ban đầu, số mới:</p>
              <label className="option"><input type="radio" name="dq_ql_2" value="A" /> Không đổi</label>
              <label className="option"><input type="radio" name="dq_ql_2" value="B" /> Tăng 4%</label>
              <label className="option"><input type="radio" name="dq_ql_2" value="C" /> Giảm 4%</label>
              <label className="option"><input type="radio" name="dq_ql_2" value="D" /> Giảm 40%</label>
            </div>
            <div className="btn-group">
              <button type="button" className="prev-btn">Quay lại</button>
              <button type="button" className="next-btn">Tiếp tục</button>
            </div>
          </div>

          {/* Q9 — Định tính 1 */}
          <div className="step">
            <div className="question-block">
              <p className="question"><span className="note">🧪 Mini-test · Định tính</span><br />
                9. Từ nào KHÁC loại với các từ còn lại?</p>
              <label className="option"><input type="radio" name="dq_qt_1" value="A" /> Bàn</label>
              <label className="option"><input type="radio" name="dq_qt_1" value="B" /> Ghế</label>
              <label className="option"><input type="radio" name="dq_qt_1" value="C" /> Tủ</label>
              <label className="option"><input type="radio" name="dq_qt_1" value="D" /> Chạy</label>
            </div>
            <div className="btn-group">
              <button type="button" className="prev-btn">Quay lại</button>
              <button type="button" className="next-btn">Tiếp tục</button>
            </div>
          </div>

          {/* Q10 — Định tính 2 */}
          <div className="step">
            <div className="question-block">
              <p className="question"><span className="note">🧪 Mini-test · Định tính</span><br />
                10. Từ nào TRÁI nghĩa với &quot;lạc quan&quot;?</p>
              <label className="option"><input type="radio" name="dq_qt_2" value="A" /> Vui vẻ</label>
              <label className="option"><input type="radio" name="dq_qt_2" value="B" /> Bi quan</label>
              <label className="option"><input type="radio" name="dq_qt_2" value="C" /> Tự tin</label>
              <label className="option"><input type="radio" name="dq_qt_2" value="D" /> Hạnh phúc</label>
            </div>
            <div className="btn-group">
              <button type="button" className="prev-btn">Quay lại</button>
              <button type="button" className="next-btn">Tiếp tục</button>
            </div>
          </div>

          {/* Q11 — Khoa học 1 */}
          <div className="step">
            <div className="question-block">
              <p className="question"><span className="note">🧪 Mini-test · Khoa học</span><br />
                11. Ở áp suất thường, nước sôi ở nhiệt độ nào?</p>
              <label className="option"><input type="radio" name="dq_kh_1" value="A" /> 90°C</label>
              <label className="option"><input type="radio" name="dq_kh_1" value="B" /> 100°C</label>
              <label className="option"><input type="radio" name="dq_kh_1" value="C" /> 110°C</label>
              <label className="option"><input type="radio" name="dq_kh_1" value="D" /> 120°C</label>
            </div>
            <div className="btn-group">
              <button type="button" className="prev-btn">Quay lại</button>
              <button type="button" className="next-btn">Tiếp tục</button>
            </div>
          </div>

          {/* Q12 — Khoa học 2 */}
          <div className="step">
            <div className="question-block">
              <p className="question"><span className="note">🧪 Mini-test · Khoa học</span><br />
                12. Hành tinh nào gần Mặt Trời nhất?</p>
              <label className="option"><input type="radio" name="dq_kh_2" value="A" /> Kim Tinh</label>
              <label className="option"><input type="radio" name="dq_kh_2" value="B" /> Trái Đất</label>
              <label className="option"><input type="radio" name="dq_kh_2" value="C" /> Thủy Tinh</label>
              <label className="option"><input type="radio" name="dq_kh_2" value="D" /> Hỏa Tinh</label>
            </div>
            <div className="btn-group">
              <button type="button" className="prev-btn">Quay lại</button>
              <button type="button" className="next-btn">Tiếp tục</button>
            </div>
          </div>

          {/* ══════ PHẦN 3: THÁI ĐỘ & THÓI QUEN HỌC ══════ */}

          {/* Q13 — Kiên trì khi gặp khó */}
          <div className="step">
            <div className="question-block">
              <p className="question"><span className="note">🧭 Thái độ · hành vi</span><br />
                13. Khi gặp câu khó trong lúc ôn, bạn thường làm gì?</p>
              <label className="option"><input type="radio" name="att_persistence" value="Bỏ qua ngay" /> Bỏ qua ngay, làm câu khác</label>
              <label className="option"><input type="radio" name="att_persistence" value="Thử rồi bỏ" /> Thử vài phút rồi bỏ nếu chưa ra</label>
              <label className="option"><input type="radio" name="att_persistence" value="Kiên trì" /> Kiên trì đến khi hiểu bằng được</label>
              <label className="option"><input type="radio" name="att_persistence" value="Hỏi ngay" /> Hỏi thầy cô / bạn bè ngay</label>
            </div>
            <div className="btn-group">
              <button type="button" className="prev-btn">Quay lại</button>
              <button type="button" className="next-btn">Tiếp tục</button>
            </div>
          </div>

          {/* Q14 — Thói quen ôn tập */}
          <div className="step">
            <div className="question-block">
              <p className="question"><span className="note">🧭 Thái độ · hành vi</span><br />
                14. Thói quen ôn tập của bạn gần nhất với mô tả nào?</p>
              <label className="option"><input type="radio" name="att_schedule" value="Đều đặn" /> Học đều đặn mỗi ngày</label>
              <label className="option"><input type="radio" name="att_schedule" value="Học dồn" /> Học dồn khi gần thi</label>
              <label className="option"><input type="radio" name="att_schedule" value="Tuỳ hứng" /> Tuỳ hứng, không cố định</label>
              <label className="option"><input type="radio" name="att_schedule" value="Chưa có" /> Chưa có thói quen rõ ràng</label>
            </div>
            <div className="btn-group">
              <button type="button" className="prev-btn">Quay lại</button>
              <button type="button" className="next-btn">Tiếp tục</button>
            </div>
          </div>

          {/* Q15 — Tâm lý áp lực */}
          <div className="step">
            <div className="question-block">
              <p className="question"><span className="note">🧭 Thái độ · hành vi</span><br />
                15. Áp lực thi cử ảnh hưởng đến bạn thế nào?</p>
              <label className="option"><input type="radio" name="att_stress" value="Kiểm soát tốt" /> Bình tĩnh, kiểm soát tốt</label>
              <label className="option"><input type="radio" name="att_stress" value="Hơi lo" /> Hơi lo nhưng vẫn ổn</label>
              <label className="option"><input type="radio" name="att_stress" value="Dễ căng thẳng" /> Dễ căng thẳng, mất tập trung</label>
              <label className="option"><input type="radio" name="att_stress" value="Rất áp lực" /> Rất áp lực, hay nản</label>
            </div>
            <div className="btn-group">
              <button type="button" className="prev-btn">Quay lại</button>
              <button type="button" className="next-btn">Tiếp tục</button>
            </div>
          </div>

          {/* Q16 — Động lực & mục tiêu */}
          <div className="step">
            <div className="question-block">
              <p className="question"><span className="note">🧭 Thái độ · hành vi</span><br />
                16. Mức độ quyết tâm và rõ ràng mục tiêu HSA của bạn?</p>
              <label className="option"><input type="radio" name="att_motivation" value="Rất quyết tâm" /> Rất rõ ràng, quyết tâm cao</label>
              <label className="option"><input type="radio" name="att_motivation" value="Khá rõ" /> Khá rõ ràng</label>
              <label className="option"><input type="radio" name="att_motivation" value="Còn mơ hồ" /> Còn mơ hồ</label>
              <label className="option"><input type="radio" name="att_motivation" value="Chưa có động lực" /> Chưa có động lực rõ</label>
            </div>
            <div className="btn-group">
              <button type="button" className="prev-btn">Quay lại</button>
              <button type="submit" className="submit-btn">Hoàn thành &amp; nhận lộ trình</button>
            </div>
          </div>
        </form>
      </div>

      <div className="thanks-overlay" id="thanksOverlay" aria-hidden="true">
        <div className="thanks-modal" role="dialog" aria-modal="true" aria-labelledby="thanksTitle">
          <div className="thanks-badge">✓</div>
          <h3 id="thanksTitle" className="thanks-title">Đã có lộ trình cho bạn!</h3>
          <p className="thanks-sub">
            Chúng tôi đã chẩn đoán năng lực và cá nhân hoá lộ trình luyện thi HSA theo điểm mạnh – yếu của bạn.
          </p>
          <button className="thanks-btn" id="thanksOkBtn" type="button">Xem lộ trình →</button>
        </div>
      </div>

      <LegacyScripts srcs={SCRIPTS} />
    </>
  );
}
