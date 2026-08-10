/* ============================================================================
 * lesson_hsa.js — engine bài học HSA luồng ĐẢO NGƯỢC (cô Hương):
 *   1 KIỂM TRA đầu vào → 2 ĐÁNH GIÁ năng lực → 3 LÝ THUYẾT (thích ứng) → 4 GHI CHÚ.
 * Tái dùng chrome/CSS của lesson_db_design (header, .progress-track, .step-pane,
 * .lesson-nav-footer, .next-btn, #success-modal). Data: window.LESSON_CONTENT_HSA.
 * KHÔNG đụng lesson_db_design.js (9219 dòng DB) — engine riêng, tối giản.
 * ============================================================================ */
(function () {
  'use strict';

  var state = { courseId: null, lesson: null, step: 1, answers: {}, score: 0, total: 0, level: 'ok', graded: false };

  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function $(id) { return document.getElementById(id); }
  function norm(s) { return String(s == null ? '' : s).trim().toLowerCase().replace(/\s/g, '').replace(/%/g, ''); }

  var LEVELS = {
    strong: { label: 'Vững 💪', cls: 'strong', theory: 'condensed',
      msg: 'Bạn nắm khá chắc chủ đề này. Chúng tôi rút gọn lý thuyết để bạn không mất thời gian ôn lại phần đã vững.' },
    ok: { label: 'Khá 🙂', cls: 'ok', theory: 'condensed',
      msg: 'Bạn đã có nền tảng. Đây là bản tóm tắt nhanh để chốt lại những điểm quan trọng.' },
    weak: { label: 'Cần ôn 📘', cls: 'weak', theory: 'full',
      msg: 'Chủ đề này còn vài chỗ chưa chắc. Chúng tôi đưa lý thuyết ĐẦY ĐỦ kèm ví dụ để bạn nắm vững.' }
  };

  /* ── Bước 1: KIỂM TRA ─────────────────────────────────────────── */
  function renderTest() {
    var t = state.lesson.test || {};
    var intro = $('hsa-test-intro');
    if (intro) intro.innerHTML = t.intro || '';
    var qs = t.questions || [];
    state.total = qs.length;
    var html = qs.map(function (q, i) {
      var body;
      if (q.type === 'fill') {
        body = '<input class="hsa-fill" type="text" data-qid="' + esc(q.id) + '" ' +
               'placeholder="Nhập đáp án…" autocomplete="off" />';
      } else {
        body = '<div class="hsa-opts">' + (q.options || []).map(function (op) {
          return '<button type="button" class="hsa-opt" data-qid="' + esc(q.id) + '" data-val="' + esc(op) + '">' +
                 esc(op) + '</button>';
        }).join('') + '</div>';
      }
      return '<div class="hsa-q" data-qid="' + esc(q.id) + '">' +
        '<div class="hsa-q-head"><span class="hsa-q-num">Câu ' + (i + 1) + '</span>' +
        '<span class="hsa-q-type">' + (q.type === 'fill' ? 'Điền đáp án' : 'Trắc nghiệm') + '</span></div>' +
        '<p class="hsa-q-text">' + esc(q.question) + '</p>' + body + '</div>';
    }).join('');
    $('hsa-test-questions').innerHTML = html;

    // chọn đáp án MCQ
    $('hsa-test-questions').querySelectorAll('.hsa-opt').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var qid = btn.getAttribute('data-qid');
        btn.parentNode.querySelectorAll('.hsa-opt').forEach(function (b) { b.classList.remove('selected'); });
        btn.classList.add('selected');
        state.answers[qid] = btn.getAttribute('data-val');
      });
    });
    $('hsa-test-questions').querySelectorAll('.hsa-fill').forEach(function (inp) {
      inp.addEventListener('input', function () { state.answers[inp.getAttribute('data-qid')] = inp.value; });
    });
  }

  function gradeTest() {
    var qs = (state.lesson.test && state.lesson.test.questions) || [];
    var missing = qs.filter(function (q) { var a = state.answers[q.id]; return a == null || String(a).trim() === ''; });
    if (missing.length) { flashNote('Hãy trả lời đủ ' + qs.length + ' câu trước khi xem đánh giá.'); return false; }
    var score = 0;
    qs.forEach(function (q) { if (norm(state.answers[q.id]) === norm(q.answer)) score++; });
    state.score = score;
    var a = state.lesson.assess || { strong_min: qs.length, ok_min: Math.ceil(qs.length / 2) };
    state.level = score >= (a.strong_min || qs.length) ? 'strong' : (score >= (a.ok_min || 1) ? 'ok' : 'weak');
    state.graded = true;
    renderAssess();
    return true;
  }

  /* ── Bước 2: ĐÁNH GIÁ ─────────────────────────────────────────── */
  function renderAssess() {
    var lv = LEVELS[state.level];
    var qs = (state.lesson.test && state.lesson.test.questions) || [];
    var rows = qs.map(function (q, i) {
      var ok = norm(state.answers[q.id]) === norm(q.answer);
      return '<li class="hsa-rev ' + (ok ? 'ok' : 'no') + '">' +
        '<span class="hsa-rev-ic">' + (ok ? '✓' : '✕') + '</span>' +
        '<span class="hsa-rev-q">Câu ' + (i + 1) + '</span>' +
        '<span class="hsa-rev-ans">Đáp án: <b>' + esc(q.answer) + '</b>' +
        (q.explain ? ' — ' + esc(q.explain) : '') + '</span></li>';
    }).join('');
    $('hsa-assess').innerHTML =
      '<div class="hsa-score-card ' + lv.cls + '">' +
        '<div class="hsa-score-num">' + state.score + '<span>/' + state.total + '</span></div>' +
        '<div class="hsa-score-body">' +
          '<div class="hsa-score-level">Năng lực chủ đề: <b>' + lv.label + '</b></div>' +
          '<p class="hsa-score-msg">' + esc(lv.msg) + '</p>' +
        '</div>' +
      '</div>' +
      '<div class="hsa-rev-label">Xem lại từng câu</div>' +
      '<ul class="hsa-rev-list">' + rows + '</ul>';
  }

  /* ── Minh hoạ trực quan cho lý thuyết (đồ thị thanh so sánh) ──────
     Mỗi card có thể kèm visual:{type:'bars', badge?, caption?, max?,
     bars:[{label,value,display?,note?,color:'violet|teal|slate|amber'}]}.
     Engine tự scale theo giá trị lớn nhất → thanh ngang trực quan, không
     cần ảnh ngoài. Mở rộng type khác sau (number-line, curve…). */
  var VIZ_COLORS = { violet: 1, teal: 1, slate: 1, amber: 1 };
  function renderBars(v) {
    var bars = v.bars || [];
    if (!bars.length) return '';
    var max = v.max || Math.max.apply(null, bars.map(function (b) { return Number(b.value) || 0; })) || 1;
    var rows = bars.map(function (b) {
      var pct = Math.max(6, Math.min(100, Math.round((Number(b.value) || 0) / max * 100)));
      var color = VIZ_COLORS[b.color] ? b.color : 'violet';
      return '<div class="hsa-viz-row">' +
        '<span class="hsa-viz-blabel">' + esc(b.label) + '</span>' +
        '<div class="hsa-viz-track">' +
          '<div class="hsa-viz-bar hsa-viz-bar--' + color + '" style="width:' + pct + '%">' +
            '<span class="hsa-viz-val">' + esc(b.display != null ? b.display : b.value) + '</span>' +
          '</div>' +
          (b.note ? '<span class="hsa-viz-note">' + esc(b.note) + '</span>' : '') +
        '</div>' +
      '</div>';
    }).join('');
    return '<div class="hsa-viz">' +
      (v.badge ? '<span class="hsa-viz-badge">' + esc(v.badge) + '</span>' : '') +
      '<div class="hsa-viz-rows">' + rows + '</div>' +
      (v.caption ? '<div class="hsa-viz-cap">' + v.caption + '</div>' : '') +
    '</div>';
  }
  function renderVisual(v) {
    if (!v || !v.type) return '';
    if (v.type === 'bars') return renderBars(v);
    return '';
  }

  /* ── Bước 3: LÝ THUYẾT (thích ứng) ────────────────────────────── */
  function renderTheory() {
    var th = state.lesson.theory || {};
    var pick = th[LEVELS[state.level].theory] || th.full || th.condensed || {};
    var badge = LEVELS[state.level].theory === 'full'
      ? '<span class="hsa-th-badge full">Bản đầy đủ — theo kết quả kiểm tra</span>'
      : '<span class="hsa-th-badge cond">Bản tóm tắt — bạn đã khá vững</span>';
    var cards = (pick.cards || []).map(function (c) {
      return '<div class="hsa-card"><div class="hsa-card-ic"><i class="fa-solid ' + esc(c.icon || 'fa-book') + '"></i></div>' +
        '<div class="hsa-card-body"><h4>' + esc(c.title) + '</h4><p>' + c.body + '</p>' +
        (c.visual ? renderVisual(c.visual) : '') + '</div></div>';
    }).join('');
    var ex = (pick.examples || []).length
      ? '<div class="hsa-ex"><div class="hsa-ex-label"><i class="fa-solid fa-lightbulb"></i> Ví dụ minh hoạ</div>' +
        pick.examples.map(function (e) {
          return '<div class="hsa-ex-item"><div class="hsa-ex-q">' + esc(e.q) + '</div>' +
                 '<div class="hsa-ex-sol">→ ' + esc(e.sol) + '</div></div>';
        }).join('') + '</div>'
      : '';
    $('hsa-theory').innerHTML =
      '<div class="hsa-th-head">' + badge + '<h3>' + esc(pick.title || 'Lý thuyết') + '</h3></div>' +
      '<div class="hsa-cards">' + cards + '</div>' + ex;
  }

  /* ── Bước 4: GHI CHÚ ──────────────────────────────────────────── */
  function renderNotes() {
    var n = state.lesson.notes || {};
    var pts = (n.key_points || []).map(function (p) { return '<li>' + esc(p) + '</li>'; }).join('');
    $('hsa-notes').innerHTML =
      '<div class="hsa-notes-card">' +
        '<div class="hsa-notes-head"><i class="fa-solid fa-bookmark"></i> Ghi chú — chốt lại để nhớ</div>' +
        '<ul class="hsa-notes-list">' + pts + '</ul>' +
        (n.formula ? '<div class="hsa-formula"><span>Công thức</span><code>' + esc(n.formula) + '</code></div>' : '') +
        (n.tip ? '<div class="hsa-tip"><i class="fa-solid fa-wand-magic-sparkles"></i> ' + esc(n.tip) + '</div>' : '') +
      '</div>';
  }

  /* ── Bước 5: PHÒNG LUYỆN BẤM GIỜ (gamified) ───────────────────── */
  var drill = { timerId: null };

  function renderDrill() {
    var d = state.lesson.drill;
    if (!d || !(d.questions || []).length) {
      $('hsa-drill').innerHTML = '<p class="hsa-intro">Bài này chưa có phòng luyện.</p>';
      return;
    }
    $('hsa-drill').innerHTML =
      '<div class="hsa-drill-intro">' +
        '<div class="hsa-drill-badge">⚡ Phòng luyện tốc độ</div>' +
        '<h3 class="hsa-drill-h">' + d.questions.length + ' câu · ' + d.time_seconds + ' giây — nhanh &amp; chính xác!</h3>' +
        '<p class="hsa-intro">HSA ăn nhau ở <b>TỐC ĐỘ</b>. Trả lời đúng liên tiếp để nhân <b>COMBO 🔥</b>. Hết giờ là dừng — thử phá kỷ lục của chính mình!</p>' +
        '<button class="next-btn primary" id="hsa-drill-start"><i class="fa-solid fa-bolt"></i> Bắt đầu</button>' +
      '</div>';
    var b = $('hsa-drill-start'); if (b) b.addEventListener('click', startDrill);
  }

  function startDrill() {
    var d = state.lesson.drill;
    drill = { idx: 0, correct: 0, answered: 0, combo: 0, maxCombo: 0, times: [], xp: 0,
      total: d.questions.length, remaining: d.time_seconds, timeTotal: d.time_seconds,
      qStart: Date.now(), locked: false, timerId: null };
    $('hsa-drill').innerHTML =
      '<div class="hsa-drill-run">' +
        '<div class="hsa-drill-hud">' +
          '<div class="hsa-drill-prog" id="hsa-drill-prog"></div>' +
          '<div class="hsa-drill-combo" id="hsa-drill-combo"></div>' +
        '</div>' +
        '<div class="hsa-drill-timer"><div class="hsa-drill-timer-bar" id="hsa-timer-bar"></div></div>' +
        '<div class="hsa-drill-q" id="hsa-drill-q"></div>' +
      '</div>';
    showDrillQuestion();
    drill.timerId = setInterval(tick, 100);
  }

  function showDrillQuestion() {
    var q = state.lesson.drill.questions[drill.idx];
    drill.qStart = Date.now();
    drill.locked = false;
    var prog = $('hsa-drill-prog'); if (prog) prog.textContent = 'Câu ' + (drill.idx + 1) + '/' + drill.total;
    updateCombo();
    var body;
    if (q.type === 'fill') {
      body = '<input class="hsa-fill hsa-drill-fill" id="hsa-drill-fill" type="text" placeholder="Nhập rồi Enter…" autocomplete="off" />';
    } else {
      body = '<div class="hsa-opts">' + (q.options || []).map(function (op) {
        return '<button type="button" class="hsa-opt hsa-drill-opt" data-val="' + esc(op) + '">' + esc(op) + '</button>';
      }).join('') + '</div>';
    }
    $('hsa-drill-q').innerHTML = '<p class="hsa-q-text">' + esc(q.question) + '</p>' + body;
    if (q.type === 'fill') {
      var inp = $('hsa-drill-fill');
      inp.focus();
      inp.addEventListener('keydown', function (e) { if (e.key === 'Enter') answerDrill(inp.value, null); });
    } else {
      $('hsa-drill-q').querySelectorAll('.hsa-drill-opt').forEach(function (btn) {
        btn.addEventListener('click', function () { answerDrill(btn.getAttribute('data-val'), btn); });
      });
    }
  }

  function updateCombo() {
    var el = $('hsa-drill-combo'); if (!el) return;
    el.innerHTML = drill.combo >= 2 ? '🔥 Combo ×' + drill.combo : '';
    el.className = 'hsa-drill-combo' + (drill.combo >= 2 ? ' on' : '');
  }

  function answerDrill(val, btn) {
    if (drill.locked) return;
    drill.locked = true;
    var q = state.lesson.drill.questions[drill.idx];
    var ok = norm(val) === norm(q.answer);
    drill.answered++;
    drill.times.push((Date.now() - drill.qStart) / 1000);
    if (ok) { drill.correct++; drill.combo++; if (drill.combo > drill.maxCombo) drill.maxCombo = drill.combo; }
    else { drill.combo = 0; }
    updateCombo();
    if (btn) btn.classList.add(ok ? 'correct' : 'wrong');
    var qEl = $('hsa-drill-q'); if (qEl) qEl.classList.add(ok ? 'flash-ok' : 'flash-no');
    setTimeout(function () {
      if (qEl) qEl.classList.remove('flash-ok', 'flash-no');
      drill.idx++;
      if (drill.idx >= drill.total) endDrill();
      else showDrillQuestion();
    }, 470);
  }

  function tick() {
    drill.remaining -= 0.1;
    var bar = $('hsa-timer-bar');
    if (bar) {
      bar.style.width = Math.max(0, drill.remaining / drill.timeTotal * 100) + '%';
      bar.className = 'hsa-drill-timer-bar' + (drill.remaining <= drill.timeTotal * 0.25 ? ' low' : '');
    }
    if (drill.remaining <= 0) endDrill();
  }

  function statBox(v, l) { return '<div class="hsa-stat"><b>' + esc(v) + '</b><span>' + esc(l) + '</span></div>'; }

  function endDrill() {
    if (drill.timerId) { clearInterval(drill.timerId); drill.timerId = null; }
    var acc = drill.answered ? Math.round(drill.correct / drill.answered * 100) : 0;
    var avg = drill.times.length ? drill.times.reduce(function (a, b) { return a + b; }, 0) / drill.times.length : 0;
    drill.xp = drill.correct * 10 + drill.maxCombo * 5;
    var msg = acc >= 80 ? 'Xuất sắc! Tốc độ và độ chính xác đều tốt. 🎯'
      : (acc >= 50 ? 'Khá ổn — luyện thêm để vừa nhanh vừa chắc.' : 'Cứ luyện lại, tốc độ sẽ lên nhanh thôi!');
    $('hsa-drill').innerHTML =
      '<div class="hsa-drill-result">' +
        '<div class="hsa-drill-badge">⚡ Kết quả luyện tốc độ</div>' +
        '<div class="hsa-drill-stats">' +
          statBox(drill.correct + '/' + drill.total, 'Đúng') +
          statBox(acc + '%', 'Chính xác') +
          statBox(avg.toFixed(1) + 's', 'TB mỗi câu') +
          statBox('×' + drill.maxCombo, 'Combo cao nhất') +
        '</div>' +
        '<div class="hsa-drill-xp">+' + drill.xp + ' XP ⚡</div>' +
        '<p class="hsa-intro" style="text-align:center">' + msg + '</p>' +
        '<button class="next-btn ghost small" id="hsa-drill-retry"><i class="fa-solid fa-rotate-left"></i> Luyện lại</button>' +
      '</div>';
    var r = $('hsa-drill-retry'); if (r) r.addEventListener('click', renderDrill);
    if (window.confetti && acc >= 50) try { window.confetti({ particleCount: 70, spread: 65, origin: { y: 0.6 } }); } catch (e) {}
  }

  function stopDrill() { if (drill.timerId) { clearInterval(drill.timerId); drill.timerId = null; } }

  /* ── Điều hướng bước ──────────────────────────────────────────── */
  var STEP_RENDER = { 1: renderTest, 2: renderAssess, 3: renderTheory, 4: renderNotes, 5: renderDrill };
  var LAST_STEP = 5;

  function goToStep(n) {
    if (n < 1 || n > LAST_STEP) return;
    if (n >= 2 && !state.graded) { flashNote('Hãy hoàn thành bài kiểm tra ở Bước 1 trước.'); return; }
    if (state.step === 5 && n !== 5) stopDrill();   // rời phòng luyện → dừng đồng hồ
    state.step = n;
    if (STEP_RENDER[n]) STEP_RENDER[n]();
    document.querySelectorAll('.step-pane').forEach(function (p) {
      p.classList.toggle('active', p.getAttribute('data-step') === String(n));
    });
    document.querySelectorAll('.progress-step').forEach(function (p) {
      var s = parseInt(p.getAttribute('data-step'), 10);
      p.classList.toggle('active', s === n);
      p.classList.toggle('done', s < n);
    });
    var back = $('nav-back'); if (back) back.disabled = (n === 1);
    var next = $('nav-next');
    if (next) {
      var lbl = next.querySelector('.nav-btn-label');
      var txt = n === 1 ? 'Nộp & xem đánh giá' : (n === LAST_STEP ? 'Hoàn thành bài học' : 'Tiếp tục');
      if (lbl) lbl.textContent = txt; else next.textContent = txt;
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function navNext() {
    if (state.step === 1) { gradeTest() && goToStep(2); }
    else if (state.step === LAST_STEP) { complete(); }
    else { goToStep(state.step + 1); }
  }
  function navBack() { if (state.step > 1) goToStep(state.step - 1); }

  function complete() {
    stopDrill();
    var m = $('success-modal');
    var xp = (state.lesson.xp_reward || 50) + (drill && drill.xp ? drill.xp : 0);
    if ($('success-lesson-title')) $('success-lesson-title').textContent = state.lesson.title || '';
    if ($('success-message')) $('success-message').textContent =
      'Bạn đã hoàn thành bài "' + (state.lesson.title || '') + '" với ' + state.score + '/' + state.total + ' câu kiểm tra đúng.';
    if ($('reward-xp')) $('reward-xp').textContent = '+' + xp;
    if (m) { m.classList.remove('hidden'); if (window.confetti) try { window.confetti({ particleCount: 90, spread: 70, origin: { y: 0.6 } }); } catch (e) {} }
  }

  function flashNote(msg) {
    var el = $('hsa-flash');
    if (!el) { el = document.createElement('div'); el.id = 'hsa-flash'; el.className = 'hsa-flash'; document.body.appendChild(el); }
    el.textContent = msg; el.classList.add('show');
    clearTimeout(el._t); el._t = setTimeout(function () { el.classList.remove('show'); }, 2600);
  }

  /* ── API cho chrome (buttons React gọi qua window) ────────────── */
  window.HSALesson = {
    goToStep: goToStep, next: navNext, back: navBack, complete: complete,
    exit: function () { window.location.href = '/dashboard'; }
  };

  function init() {
    var courseId = (document.body && document.body.dataset.course) || 'hsa_quantitative';
    state.courseId = courseId;
    var data = window.LESSON_CONTENT_HSA && window.LESSON_CONTENT_HSA[courseId];
    if (!data || !data.lessons || !data.lessons.length) {
      var stage = document.querySelector('.lesson-stage');
      if (stage) stage.innerHTML = '<div style="padding:48px;text-align:center;color:#94A3B8">' +
        'Chưa có nội dung bài học cho khoá này. Nội dung HSA đầy đủ sẽ được cập nhật.</div>';
      return;
    }
    var params = new URLSearchParams(window.location.search);
    var idx = parseInt(params.get('lesson'), 10) - 1;
    if (isNaN(idx) || idx < 0 || idx >= data.lessons.length) idx = 0;
    state.lesson = data.lessons[idx];

    if ($('lesson-title')) $('lesson-title').textContent = state.lesson.title || '';
    if ($('hsa-topic-tag')) $('hsa-topic-tag').textContent = state.lesson.topic_tag || '';
    goToStep(1);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
