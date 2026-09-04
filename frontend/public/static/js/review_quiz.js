/* review_quiz.js — FE-06: Quiz ôn tập cấp khóa học (block #review-quiz-block
   trong course_detail.html). Backend: routes/quizzes.py.
   Đáp án đúng chỉ backend biết — FE chỉ nhận {id, text} cho từng option.

   PHẦN XEM LẠI in CHỮ, không in mã lựa chọn (L13, 31/08/2026). Bản cũ in
   thẳng `your_answer`/`correct_answer` — vốn là `o1`/`o2` — nên màn hình
   hiện "Bạn chọn: o1 — Đáp án đúng: o2", thứ không ai đọc được, kể cả
   người vừa làm bài xong. Vẫn giữ đường lùi về mã: một quiz sinh TRƯỚC bản
   vá không có `*_text` trong phản hồi. */

let currentQuiz = null;

function _csrfHeader() {
  const meta = document.querySelector('meta[name=csrf-token]');
  return meta ? { 'X-CSRFToken': meta.content } : {};
}

/* Dữ liệu câu hỏi/option đến từ content_json — escape trước khi đưa vào innerHTML */
function _esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, ch => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[ch]));
}

async function startReviewQuiz(courseId) {
  const btn = document.querySelector('#quiz-idle .quiz-btn');
  if (btn) { btn.disabled = true; btn.textContent = 'Đang tạo quiz…'; }
  try {
    const res = await fetch(`/api/courses/${courseId}/quiz/generate`, {
      method: 'POST',
      headers: _csrfHeader()
    });
    const data = await res.json();
    if (!res.ok) {
      alert((window.__PE_errMsg ? window.__PE_errMsg(data.error) : data.error) || 'Không thể tạo quiz');
      return;
    }
    currentQuiz = { id: data.quiz_id, total: data.total, answers: {} };
    renderQuizRunner(data.questions);
  } catch (e) {
    alert('Lỗi mạng, thử lại sau.');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Bắt đầu ôn tập'; }
  }
}

function renderQuizRunner(questions) {
  document.getElementById('quiz-idle').style.display = 'none';
  const runner = document.getElementById('quiz-runner');
  runner.style.display = 'block';
  runner.innerHTML = questions.map(q => `
    <div class="quiz-q" data-no="${q.question_no}">
      <p class="quiz-q-text">${q.question_no}. ${_esc(q.question)}</p>
      ${q.options.map(o => `
        <label class="quiz-opt">
          <input type="radio" name="q${q.question_no}" value="${_esc(o.id)}"
                 onchange="setAnswer(${q.question_no}, this.value)"> ${_esc(o.text)}
        </label>`).join('')}
    </div>`).join('') +
    `<button type="button" class="quiz-btn primary" id="quiz-submit-btn" onclick="submitReviewQuiz()">Nộp bài</button>`;
  runner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function setAnswer(qno, selected) { currentQuiz.answers[qno] = selected; }

async function submitReviewQuiz() {
  const answered = Object.keys(currentQuiz.answers).length;
  if (answered < currentQuiz.total &&
      !confirm(`Bạn mới trả lời ${answered}/${currentQuiz.total} câu. Nộp luôn?`)) {
    return;
  }
  const btn = document.getElementById('quiz-submit-btn');
  if (btn) { btn.disabled = true; btn.textContent = 'Đang chấm…'; }
  const answers = Object.entries(currentQuiz.answers)
    .map(([question_no, selected]) => ({ question_no: Number(question_no), selected }));
  try {
    const res = await fetch(`/api/quizzes/${currentQuiz.id}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ..._csrfHeader() },
      body: JSON.stringify({ answers })
    });
    const data = await res.json();
    if (!res.ok) {
      alert((window.__PE_errMsg ? window.__PE_errMsg(data.error) : data.error) || 'Nộp bài thất bại');
      if (btn) { btn.disabled = false; btn.textContent = 'Nộp bài'; }
      return;
    }
    renderQuizResult(data);
  } catch (e) {
    alert('Lỗi mạng, thử lại sau.');
    if (btn) { btn.disabled = false; btn.textContent = 'Nộp bài'; }
  }
}

function renderQuizResult(result) {
  const runner = document.getElementById('quiz-runner');

  /* XP LẤY TỪ MÁY CHỦ, và nói rõ khi nó bằng 0 (05/09/2026).

     Trước hôm nay quiz ôn tập không cộng XP nào, và màn hình cũng không nói gì —
     em làm xong mười lượt rồi tự hỏi vì sao chỉ số không nhúc nhích.

     Nay có XP, kèm trần 3 lượt/ngày. Trần ấy BẮT BUỘC: `GenerateQuizView` không
     giới hạn số quiz, nên không có trần thì bảng xếp hạng thành cuộc thi bấm
     nút. Nhưng một lượt 0 XP mà IM LẶNG thì trông y hệt một lỗi — nên nói ra,
     và nói cả lý do. Lượt quá trần vẫn được chấm, vẫn vào bản đồ năng lực, vẫn
     tính chuỗi ngày. */
  const xp = typeof result.xpGained === 'number' ? result.xpGained : null;
  const soMoiNgay = Number(result.xpMoiNgay) || 3;
  const dongXp = xp === null ? ''
    : (xp > 0
      ? `<p class="quiz-xp">+${xp} XP</p>`
      : `<p class="quiz-xp quiz-xp--het">Hôm nay đã đủ ${soMoiNgay} lượt tính XP.`
        + ' Lượt này vẫn được chấm và vẫn tính vào bản đồ năng lực.</p>');

  runner.innerHTML = `
    <p class="quiz-score">Điểm: ${result.score}/${result.total} (${result.percentage}%)</p>
    ${dongXp}
    ${result.review.map(r => `
      <div class="quiz-review-item ${r.is_correct ? 'correct' : 'wrong'}">
        <p class="quiz-q-text">${r.question_no}. ${_esc(r.question)}</p>
        <p>Bạn chọn: <b>${r.your_answer_text != null ? _esc(r.your_answer_text)
                          : (r.your_answer != null ? _esc(r.your_answer) : '(bỏ trống)')}</b>
           — Đáp án đúng: <b>${_esc(r.correct_answer_text != null ? r.correct_answer_text
                                    : r.correct_answer)}</b></p>
        ${r.explanation ? `<p class="quiz-explain">${_esc(r.explanation)}</p>` : ''}
      </div>`).join('')}
    <button type="button" class="quiz-btn secondary" onclick="location.reload()">Làm lại từ đầu</button>`;
}
