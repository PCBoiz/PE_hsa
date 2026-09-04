/* ============================================================================
 * lesson_hsa.js — engine bài học HSA luồng ĐẢO NGƯỢC (cô Hương):
 *   1 KIỂM TRA đầu vào → 2 ĐÁNH GIÁ năng lực → 3 LÝ THUYẾT (thích ứng) → 4 GHI CHÚ.
 * Tái dùng chrome/CSS của lesson_db_design (header, .progress-track, .step-pane,
 * .lesson-nav-footer, .next-btn, #success-modal).
 * Data: CSDL, qua /api/courses/<id>/content?lesson=N — ĐÚNG một bài mỗi lần.
 * (Trước 19/08/2026 là `window.LESSON_CONTENT_HSA`, cả 76 bài trong một tệp JS
 *  5.847 dòng; tệp ấy xoá hẳn 05/09/2026 sau khi đối chiếu đủ 76 mã bài với
 *  CSDL — không thiếu, không thừa bài nào.)
 * KHÔNG đụng lesson_db_design.js (9219 dòng DB) — engine riêng, tối giản.
 * ============================================================================ */
(function () {
  'use strict';

  var state = { courseId: null, lesson: null, lessonNo: 1, step: 1, answers: {},
              results: {}, score: 0, total: 0, level: 'ok', graded: false };

  /* Thoát ĐỦ NĂM ký tự, kể cả hai dấu nháy.
     
     BẢN CŨ CHỈ THOÁT `& < >`, mà hàm này được dùng NGAY TRONG THUỘC TÍNH:
     `data-val="' + esc(op) + '"`, `data-qid="…"`, `aria-label="…"`,
     `class="fa-solid ' + esc(c.icon) + '"`. Một phương án trả lời chứa dấu nháy
     kép là thoát ra khỏi thuộc tính và gắn được `onmouseover=` vào chính nút
     đáp án — thứ học viên buộc phải bấm để làm bài.
     
     Và nó đi VÒNG QUA bộ lọc HTML thêm cùng ngày (`lessons/content.py`): payload
     thoát-thuộc-tính không chứa một ký tự `<` nào, nên biểu thức tìm thẻ của bộ
     lọc không thấy gì. Hai hàng rào, cùng một ngày, và khe nằm ĐÚNG giữa chúng.
     
     `'` dùng `&#39;` chứ không `&apos;`: `&apos;` không có trong HTML4 và một
     số bộ phân tích cũ để nguyên nó. */
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function $(id) { return document.getElementById(id); }

  /* Câu báo lỗi khi lưu tiến độ thất bại — hàm THUẦN để kiểm được
     (`e2e/unit/loi-may-chu.test.mjs`).

     ── LỖI ĐANG CHẶN (vá 04/09/2026) ────────────────────────────────────────
     Bản cũ chỉ phân biệt 404 với "mọi thứ khác", và "mọi thứ khác" hiện ra là
     *"kiểm tra mạng rồi mở lại bài"*. Nhưng máy chủ trả về những câu RẤT cụ thể:

         403  "Bạn chưa ghi danh khoá này."
         400  "Bài này có phần luyện tập — làm ít nhất một câu rồi mới…"

     Nói "kiểm tra mạng" ở đó là NÓI DỐI: mạng vẫn tốt, máy chủ đã trả lời tử tế,
     và học viên bị đẩy đi sửa nhầm chỗ — họ sẽ tắt wifi bật lại, đổi trình
     duyệt, rồi kết luận là sản phẩm hỏng.

     `error` có HAI hình dạng trong repo: chuỗi (view tự trả) và object
     `{status, message, detail}` (bộ xử lý lỗi chung). Đọc cả hai. */
  /* Chọn bản lý thuyết + NÓI ĐÚNG bản nào đang hiện — hàm THUẦN, có bộ kiểm
     riêng (`e2e/unit/ly-thuyet.test.mjs`).

     ── VÌ SAO TÁCH RA (04/09/2026) ──────────────────────────────────────────
     Bản cũ tính hai thứ từ HAI nguồn khác nhau:

         pick  = th[mucDo] || th.full || th.condensed || {}     ← có đường lùi
         badge = (mucDo === 'full') ? 'Bản đầy đủ' : 'Bản tóm tắt'  ← KHÔNG

     Nhãn bám vào bản được YÊU CẦU, nội dung bám vào bản THẬT SỰ CÓ. Hai thứ ấy
     lệch nhau ngay khi một bài thiếu một bản: em "Cần ôn" mở một bài không có
     `full` sẽ đọc bản tóm tắt dưới nhãn "Bản đầy đủ — theo kết quả kiểm tra".

     Đo trên dữ liệu thật 04/09: cả 76 bài đều có ĐỦ hai bản, nên nhãn hiện chưa
     nói dối lần nào. Đây là vá một lỗ CHƯA cắn — sửa lúc nó rẻ, vì thứ giữ nó
     đúng là một sự trùng hợp về dữ liệu, không phải một luật của mã.

     Một màn hình nói sai về CHÍNH NÓ thì mọi thứ khác nó nói cũng mất giá. */
  function chonLyThuyet(theory, mucDo) {
    var th = theory || {};
    var thu = [mucDo, 'full', 'condensed'];
    for (var i = 0; i < thu.length; i++) {
      var k = thu[i];
      if (k && th[k]) return { ban: th[k], la_day_du: k === 'full' };
    }
    // Không có bản nào: đừng khẳng định gì về thứ không hiện ra.
    return { ban: {}, la_day_du: false };
  }

  function cauLoiMayChu(status, d) {
    var e = d && d.error;
    if (typeof e === 'string' && e.trim()) return e;
    if (e && typeof e.message === 'string' && e.message.trim()) return e.message;
    if (status === 404) return 'Không lưu được: máy chủ không tìm thấy bài này.';
    return 'Chưa lưu được tiến độ — kiểm tra mạng rồi mở lại bài.';
  }
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

  /* Chấm Ở MÁY CHỦ.
     Trước 31/08/2026 hàm này so `state.answers[q.id]` với `q.answer` — mà
     `q.answer` đi kèm nội dung bài xuống trình duyệt TRƯỚC khi học viên trả
     lời. Đo được: một request lấy 297 đáp án của cả khoá, và
     `POST complete {"quizScore": 999999}` được nhận. Nay `answer` không còn
     trong nội dung nữa (`lessons/grading.bo_dap_an`), nên hàm này BUỘC phải
     hỏi máy chủ — và đó chính là điều kiện khiến điểm trở thành bằng chứng.

     Bất đồng bộ: nút gọi phải `await` nó. `state.results` giữ kết quả để bước
     ĐÁNH GIÁ vẽ lại, thay cho `q.answer` đã biến mất. */
  async function gradeTest() {
    var qs = (state.lesson.test && state.lesson.test.questions) || [];
    var missing = qs.filter(function (q) { var a = state.answers[q.id]; return a == null || String(a).trim() === ''; });
    if (missing.length) { flashNote('Hãy trả lời đủ ' + qs.length + ' câu trước khi xem đánh giá.', true); return false; }

    var d = await checkOnServer('test', state.answers);
    if (!d) {
      /* Mất mạng giữa chừng: KHÔNG chấm bừa 0 điểm và KHÔNG cho đi tiếp — bài
         này quyết định nhánh lý thuyết và điểm vào sổ. Thà bảo họ thử lại. */
      flashNote('Chưa chấm được — kiểm tra mạng rồi bấm lại.', true);
      return false;
    }
    state.results = d.results || {};
    state.score = d.correct || 0;
    var a = state.lesson.assess || { strong_min: qs.length, ok_min: Math.ceil(qs.length / 2) };
    state.level = state.score >= (a.strong_min || qs.length) ? 'strong'
                : (state.score >= (a.ok_min || 1) ? 'ok' : 'weak');
    state.graded = true;
    renderAssess();
    return true;
  }

  /* Gọi đường chấm. Trả `null` khi không gọi được — nơi gọi tự quyết định nói
     gì, chứ hàm này không bịa ra một kết quả nào. */
  async function checkOnServer(phan, answers, reset) {
    try {
      var r = await fetch('/api/courses/' + encodeURIComponent(state.courseId) +
                          '/lessons/' + encodeURIComponent(state.lesson.index) + '/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ phan: phan, answers: answers, reset: !!reset }),
      });
      if (!r.ok) return null;
      return await r.json();
    } catch (e) {
      return null;
    }
  }

  /* ── Bước 2: ĐÁNH GIÁ ─────────────────────────────────────────── */
  function renderAssess() {
    var lv = LEVELS[state.level];
    var qs = (state.lesson.test && state.lesson.test.questions) || [];
    /* Đáp án và lời giải nay đến TỪ MÁY CHỦ, sau khi đã nhận câu trả lời —
       chúng không còn nằm trong `state.lesson`. */
    var rows = qs.map(function (q, i) {
      var kq = (state.results || {})[q.id] || {};
      var ok = !!kq.correct;
      return '<li class="hsa-rev ' + (ok ? 'ok' : 'no') + '">' +
        '<span class="hsa-rev-ic">' + (ok ? '✓' : '✕') + '</span>' +
        '<span class="hsa-rev-q">Câu ' + (i + 1) + '</span>' +
        '<span class="hsa-rev-ans">Đáp án: <b>' + esc(kq.answer == null ? '—' : kq.answer) + '</b>' +
        (kq.explain ? ' — ' + esc(kq.explain) : '') + '</span></li>';
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
  /* TRỤC SỐ — dạy khoảng nghiệm, bất phương trình, miền giá trị.
     v = {type:'numline', min, max, ticks:[số…], marks:[{at,label,kind}],
          ranges:[{from,to,label,open?,color?}], caption?} */
  function renderNumline(v) {
    var min = v.min, max = v.max, span = (max - min) || 1;
    var pos = function (x) { return ((x - min) / span * 100); };
    var ticks = (v.ticks || []).map(function (t) {
      return '<span class="hsa-nl-tick" style="left:' + pos(t) + '%">' +
             '<i></i><b>' + esc(t) + '</b></span>';
    }).join('');
    var ranges = (v.ranges || []).map(function (r) {
      var a = Math.max(0, pos(r.from)), b = Math.min(100, pos(r.to));
      var color = VIZ_COLORS[r.color] ? r.color : 'violet';
      return '<span class="hsa-nl-range hsa-nl-range--' + color + (r.open ? ' is-open' : '') + '" ' +
             'style="left:' + a + '%;width:' + (b - a) + '%">' +
             (r.label ? '<b>' + esc(r.label) + '</b>' : '') + '</span>';
    }).join('');
    var marks = (v.marks || []).map(function (m) {
      return '<span class="hsa-nl-mark hsa-nl-mark--' + (m.kind || 'solid') + '" style="left:' + pos(m.at) + '%">' +
             (m.label ? '<b>' + esc(m.label) + '</b>' : '') + '</span>';
    }).join('');
    return '<div class="hsa-viz hsa-viz--nl">' +
      (v.badge ? '<span class="hsa-viz-badge">' + esc(v.badge) + '</span>' : '') +
      '<div class="hsa-nl"><div class="hsa-nl-axis"></div>' + ranges + ticks + marks + '</div>' +
      (v.caption ? '<div class="hsa-viz-cap">' + v.caption + '</div>' : '') + '</div>';
  }

  /* ĐỒ THỊ HÀM — vẽ y=f(x) bằng SVG polyline, tự lấy mẫu.
     v = {type:'curve', fn:'x*x-2*x', from, to, points?, marks?, caption?}
     `fn` chỉ nhận biểu thức toán an toàn (số, x, + - * / ( ) . , ^ và Math.*). */
  var FN_SAFE = /^[-+*/(). 0-9xeE^,<>=?:|&%\s]*(?:(?:Math\.[a-z0-9]+|abs|sqrt|sin|cos|tan|log|exp|pow|PI)[-+*/(). 0-9xeE^,\s]*)*$/i;
  function compileFn(src) {
    if (!FN_SAFE.test(String(src))) return null;
    var body = String(src).replace(/\^/g, '**')
      .replace(/\b(abs|sqrt|sin|cos|tan|log|exp|pow)\(/g, 'Math.$1(')
      .replace(/\bPI\b/g, 'Math.PI');
    try {   return new Function('x', 'return (' + body + ');'); }
    catch (e) { return null; }
  }
  function renderCurve(v) {
    var f = compileFn(v.fn);
    if (!f) return '';
    var from = v.from, to = v.to, n = v.points || 60;
    var xs = [], ys = [];
    for (var i = 0; i <= n; i++) {
      var x = from + (to - from) * i / n, y;
      try { y = f(x); } catch (e) { y = NaN; }
      if (isFinite(y)) { xs.push(x); ys.push(y); }
    }
    if (!ys.length) return '';
    var yMin = v.yMin != null ? v.yMin : Math.min.apply(null, ys);
    var yMax = v.yMax != null ? v.yMax : Math.max.apply(null, ys);
    if (yMax === yMin) { yMax += 1; yMin -= 1; }
    var W = 320, H = 170, pad = 6;
    var sx = function (x) { return pad + (x - from) / ((to - from) || 1) * (W - pad * 2); };
    var sy = function (y) { return H - pad - (y - yMin) / ((yMax - yMin) || 1) * (H - pad * 2); };
    var pts = xs.map(function (x, k) { return sx(x).toFixed(1) + ',' + sy(ys[k]).toFixed(1); }).join(' ');
    var axisY = (yMin <= 0 && yMax >= 0) ? '<line class="hsa-cv-axis" x1="' + pad + '" y1="' + sy(0) + '" x2="' + (W - pad) + '" y2="' + sy(0) + '"/>' : '';
    var axisX = (from <= 0 && to >= 0) ? '<line class="hsa-cv-axis" x1="' + sx(0) + '" y1="' + pad + '" x2="' + sx(0) + '" y2="' + (H - pad) + '"/>' : '';
    var dots = (v.marks || []).map(function (m) {
      var my; try { my = m.y != null ? m.y : f(m.at); } catch (e) { return ''; }
      if (!isFinite(my)) return '';
      return '<g class="hsa-cv-mark"><circle cx="' + sx(m.at) + '" cy="' + sy(my) + '" r="4.5"/>' +
        (m.label ? '<text x="' + (sx(m.at) + 7) + '" y="' + (sy(my) - 7) + '">' + esc(m.label) + '</text>' : '') + '</g>';
    }).join('');
    return '<div class="hsa-viz hsa-viz--cv">' +
      (v.badge ? '<span class="hsa-viz-badge">' + esc(v.badge) + '</span>' : '') +
      '<svg class="hsa-cv" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Đồ thị hàm ' + esc(v.fn) + '">' +
        axisY + axisX + '<polyline class="hsa-cv-line" points="' + pts + '"/>' + dots +
      '</svg>' +
      (v.caption ? '<div class="hsa-viz-cap">' + v.caption + '</div>' : '') + '</div>';
  }

  /* SƠ ĐỒ KHỐI — chuỗi bước / quan hệ (hợp cho Văn, Khoa học).
     v = {type:'flow', steps:[{label, note?, color?}], caption?} */
  function renderFlow(v) {
    var steps = (v.steps || []);
    if (!steps.length) return '';
    var html = steps.map(function (s, i) {
      var color = VIZ_COLORS[s.color] ? s.color : 'violet';
      return (i ? '<span class="hsa-fl-arrow" aria-hidden="true">→</span>' : '') +
        '<span class="hsa-fl-step hsa-fl-step--' + color + '">' +
          '<b>' + esc(s.label) + '</b>' +
          (s.note ? '<i>' + esc(s.note) + '</i>' : '') +
        '</span>';
    }).join('');
    return '<div class="hsa-viz hsa-viz--fl">' +
      (v.badge ? '<span class="hsa-viz-badge">' + esc(v.badge) + '</span>' : '') +
      '<div class="hsa-fl">' + html + '</div>' +
      (v.caption ? '<div class="hsa-viz-cap">' + v.caption + '</div>' : '') + '</div>';
  }

  /* BẢNG SỐ LIỆU — dạng câu hỏi phổ biến NHẤT của hợp phần Định lượng là đọc
     bảng, mà bộ máy cũ lại không vẽ được bảng (audit 2026-08-14).
     v = {type:'table', head:[…], rows:[[…]], highlight?:[chỉ số cột], foot?:[…],
          align?:['left'|'right'…], badge?, caption?} */
  function renderTable(v) {
    var head = v.head || [], rows = v.rows || [];
    if (!head.length || !rows.length) return '';
    var hi = {};
    (v.highlight || []).forEach(function (i) { hi[i] = 1; });
    var align = v.align || [];
    // Cột không chỉ định thì: cột đầu căn trái (nhãn), còn lại căn phải (số).
    var cls = function (i) {
      return ' class="' + (align[i] || (i === 0 ? 'left' : 'right')) + (hi[i] ? ' is-hi' : '') + '"';
    };
    var th = head.map(function (h, i) { return '<th' + cls(i) + ' scope="col">' + esc(h) + '</th>'; }).join('');
    var tb = rows.map(function (r) {
      return '<tr>' + r.map(function (c, i) {
        return i === 0
          ? '<th' + cls(i) + ' scope="row">' + esc(c) + '</th>'
          : '<td' + cls(i) + '>' + esc(c) + '</td>';
      }).join('') + '</tr>';
    }).join('');
    var tf = (v.foot && v.foot.length)
      ? '<tfoot><tr>' + v.foot.map(function (c, i) { return '<td' + cls(i) + '>' + esc(c) + '</td>'; }).join('') + '</tr></tfoot>'
      : '';
    return '<div class="hsa-viz hsa-viz--tb">' +
      (v.badge ? '<span class="hsa-viz-badge">' + esc(v.badge) + '</span>' : '') +
      // Bảng rộng phải tự cuộn NGANG trong khung của nó, không đẩy cả trang trượt.
      '<div class="hsa-tb-wrap"><table class="hsa-tb">' +
        '<thead><tr>' + th + '</tr></thead><tbody>' + tb + '</tbody>' + tf +
      '</table></div>' +
      (v.caption ? '<div class="hsa-viz-cap">' + v.caption + '</div>' : '') + '</div>';
  }

  /* BIỂU ĐỒ TRÒN — cơ cấu, tỉ trọng (Địa lí, đọc số liệu).
     v = {type:'pie', slices:[{label, value, color?}], unit?, badge?, caption?}
     Vẽ bằng conic-gradient: không cần thư viện, không cần SVG dài dòng. */
  var PIE_HEX = { violet: '#6D5AE6', teal: '#0E7C6B', amber: '#A45B08', slate: '#64748B', rose: '#BE2A46' };
  var PIE_ORDER = ['violet', 'teal', 'amber', 'slate', 'rose'];
  function renderPie(v) {
    var slices = (v.slices || []).filter(function (s) { return Number(s.value) > 0; });
    if (!slices.length) return '';
    var total = slices.reduce(function (a, s) { return a + Number(s.value); }, 0) || 1;
    var acc = 0, stops = [], legend = [];
    slices.forEach(function (s, i) {
      var hex = PIE_HEX[s.color] || PIE_HEX[PIE_ORDER[i % PIE_ORDER.length]];
      var pct = Number(s.value) / total * 100;
      stops.push(hex + ' ' + acc.toFixed(2) + '% ' + (acc + pct).toFixed(2) + '%');
      acc += pct;
      legend.push('<li><i style="background:' + hex + '"></i>' +
        '<span class="hsa-pie-lb">' + esc(s.label) + '</span>' +
        '<b>' + (Math.round(pct * 10) / 10) + '%</b>' +
        '<em>' + esc(s.value) + (v.unit ? ' ' + esc(v.unit) : '') + '</em></li>');
    });
    return '<div class="hsa-viz hsa-viz--pie">' +
      (v.badge ? '<span class="hsa-viz-badge">' + esc(v.badge) + '</span>' : '') +
      '<div class="hsa-pie-body">' +
        '<div class="hsa-pie-disc" style="background:conic-gradient(' + stops.join(',') + ')" ' +
          'role="img" aria-label="Biểu đồ tròn: ' + esc(slices.map(function (s) { return s.label; }).join(', ')) + '"></div>' +
        '<ul class="hsa-pie-legend">' + legend.join('') + '</ul>' +
      '</div>' +
      (v.caption ? '<div class="hsa-viz-cap">' + v.caption + '</div>' : '') + '</div>';
  }

  /* SƠ ĐỒ CÂY — phân loại (từ loại trong Ngữ văn, phân loại sinh vật, hoá vô cơ).
     v = {type:'tree', root:{label, note?}, branches:[{label, note?, color?,
          children?:[{label, note?}]}], badge?, caption?} */
  function renderTree(v) {
    var root = v.root || {}, branches = v.branches || [];
    if (!branches.length) return '';
    var cols = branches.map(function (b, i) {
      var color = VIZ_COLORS[b.color] ? b.color : PIE_ORDER[i % 4];
      var kids = (b.children || []).map(function (c) {
        return '<li><b>' + esc(c.label) + '</b>' + (c.note ? '<i>' + esc(c.note) + '</i>' : '') + '</li>';
      }).join('');
      return '<div class="hsa-tree-branch hsa-tree-branch--' + (VIZ_COLORS[color] ? color : 'violet') + '">' +
        '<div class="hsa-tree-node"><b>' + esc(b.label) + '</b>' +
          (b.note ? '<i>' + esc(b.note) + '</i>' : '') + '</div>' +
        (kids ? '<ul class="hsa-tree-kids">' + kids + '</ul>' : '') +
      '</div>';
    }).join('');
    return '<div class="hsa-viz hsa-viz--tree">' +
      (v.badge ? '<span class="hsa-viz-badge">' + esc(v.badge) + '</span>' : '') +
      (root.label ? '<div class="hsa-tree-root"><b>' + esc(root.label) + '</b>' +
        (root.note ? '<i>' + esc(root.note) + '</i>' : '') + '</div>' : '') +
      '<div class="hsa-tree-row">' + cols + '</div>' +
      (v.caption ? '<div class="hsa-viz-cap">' + v.caption + '</div>' : '') + '</div>';
  }

  /* TRỤC THỜI GIAN — mốc lịch sử, chuỗi sự kiện.
     v = {type:'timeline', events:[{when, label, note?, color?}], badge?, caption?} */
  function renderTimeline(v) {
    var evs = v.events || [];
    if (!evs.length) return '';
    var items = evs.map(function (e, i) {
      var color = VIZ_COLORS[e.color] ? e.color : PIE_ORDER[i % 4];
      return '<li class="hsa-tl-item hsa-tl-item--' + (VIZ_COLORS[color] ? color : 'violet') + '">' +
        '<span class="hsa-tl-dot" aria-hidden="true"></span>' +
        '<span class="hsa-tl-when">' + esc(e.when) + '</span>' +
        '<span class="hsa-tl-body"><b>' + esc(e.label) + '</b>' +
          (e.note ? '<i>' + esc(e.note) + '</i>' : '') + '</span>' +
      '</li>';
    }).join('');
    return '<div class="hsa-viz hsa-viz--tl">' +
      (v.badge ? '<span class="hsa-viz-badge">' + esc(v.badge) + '</span>' : '') +
      '<ol class="hsa-tl">' + items + '</ol>' +
      (v.caption ? '<div class="hsa-viz-cap">' + v.caption + '</div>' : '') + '</div>';
  }

  var VIZ_RENDERERS = {
    bars: renderBars,
    numline: renderNumline,
    curve: renderCurve,
    flow: renderFlow,
    table: renderTable,
    pie: renderPie,
    tree: renderTree,
    timeline: renderTimeline
  };

  function renderVisual(v) {
    if (!v || !v.type) return '';
    var fn = VIZ_RENDERERS[v.type];
    return fn ? fn(v) : '';
  }

  /* ── Bước 3: LÝ THUYẾT (thích ứng) ────────────────────────────── */
  function renderTheory() {
    var chon = chonLyThuyet(state.lesson.theory, LEVELS[state.level].theory);
    var pick = chon.ban;
    var badge = chon.la_day_du
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
    /* Xin máy chủ xoá câu trả lời phòng luyện đã ghi nhận. Nút này là nút LÀM
       LẠI; không xoá thì lần luyện thứ hai tô màu theo câu trả lời lần trước
       (đo được: 5/8 thay vì 6/8 vì một câu bị khoá bằng đáp án sai của lần bỏ
       dở). Không `await`: xoá xong hay chưa thì câu đầu cũng phải mất ~2 giây
       nữa mới tới, và hỏng thì cũng chỉ mất đúng lần luyện này. */
    checkOnServer('drill', {}, true);
    drill = { idx: 0, correct: 0, answered: 0, combo: 0, maxCombo: 0, times: [], xp: 0,
      /* `answers` là thứ DUY NHẤT được gửi lên lúc hoàn thành. Các con số
         `correct`/`maxCombo` dưới đây chỉ để vẽ HUD tại chỗ; máy chủ dựng lại
         chúng từ chính các câu trả lời này (`lessons/grading.cham_phong_luyen`). */
      answers: {},
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

  /* Chấm Ở MÁY CHỦ, từng câu một.

     `q.answer` KHÔNG còn đi xuống trình duyệt (`lessons/grading.bo_dap_an` cắt
     nó ở tầng đọc), nên `norm(val) === norm(q.answer)` của bản cũ so với
     `undefined` — mọi câu đều sai. Phòng luyện lại là một nguồn của bản đồ năng
     lực (`KIND_DRILL` trong `stats/competency.KIND_TO_SOURCE`), nên đáp án của
     nó phải bí mật y như bài kiểm tra đầu vào; việc phải chuyển là chỗ CHẤM.

     Lời gọi nằm gọn trong 470ms hiển thị phản hồi vốn đã có, nên phần lớn độ
     trễ bị che. Đường chấm có đệm 60 giây cho bảng đáp án và cho phép kiểm ghi
     danh (đo: 270ms → 1ms từ lần thứ hai). */
  async function answerDrill(val, btn) {
    if (drill.locked) return;
    drill.locked = true;
    var q = state.lesson.drill.questions[drill.idx];
    var qEl = $('hsa-drill-q');
    drill.answers[q.id] = val;
    drill.times.push((Date.now() - drill.qStart) / 1000);

    var d = await checkOnServer('drill', drill.answers);
    var kq = d && d.results && d.results[q.id];
    if (!kq) {
      /* Mất mạng giữa chừng: KHÔNG tô đỏ như thể em làm sai. Câu vẫn nằm trong
         `drill.answers` nên lúc hoàn thành máy chủ vẫn chấm được nó. */
      flashNote('Chưa chấm được câu này — vẫn tính khi bạn hoàn thành bài.');
    } else {
      var ok = !!kq.correct;
      drill.answered++;
      if (ok) { drill.correct++; drill.combo++; if (drill.combo > drill.maxCombo) drill.maxCombo = drill.combo; }
      else { drill.combo = 0; }
      updateCombo();
      if (btn) btn.classList.add(ok ? 'correct' : 'wrong');
      if (qEl) qEl.classList.add(ok ? 'flash-ok' : 'flash-no');
    }
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
    if (n >= 2 && !state.graded) { flashNote('Hãy hoàn thành bài kiểm tra ở Bước 1 trước.', true); return; }
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

  var dangCham = false;
  async function navNext() {
    if (state.step === 1) {
      /* `gradeTest` nay BẤT ĐỒNG BỘ (chấm ở máy chủ). Không `await` thì nó trả
         về một Promise — thứ luôn truthy — nên `&& goToStep(2)` sẽ nhảy sang
         bước ĐÁNH GIÁ trước khi có kết quả, và màn hình vẽ 0/3 cho một bài làm
         đúng hết. Đúng loại lỗi "màn hình xanh, số sai" mà cả dự án đang truy.
         `dangCham` chặn bấm hai lần: một lượt chấm là một lượt ghi. */
      if (dangCham) return;
      dangCham = true;
      try { if (await gradeTest()) goToStep(2); }
      finally { dangCham = false; }
    } else if (state.step === LAST_STEP) { complete(); }
    else { goToStep(state.step + 1); }
  }
  function navBack() { if (state.step > 1) goToStep(state.step - 1); }

  /* Ghi tiến độ về máy chủ.
     Trước audit 2026-08-15, complete() chỉ hiện modal chúc mừng — KHÔNG có chỗ
     nào trong ứng dụng gọi /api/lessons/<n>/complete. Hệ quả: lesson_progress
     luôn rỗng, nên chuỗi ngày học, số bài đã xong, tiến độ khoá và "Học tiếp"
     trên Bảng điều khiển đứng yên ở 0 với mọi học viên. */
  /* Kết quả phòng luyện tốc độ, gửi kèm để bản đồ năng lực chấm được TỐC ĐỘ —
     thứ mà bài kiểm tra đầu vào không đo được và cũng là thứ kỳ thi HSA chấm.
     Trước đây con số này chỉ hiện lên màn hình rồi biến mất.

     Chấm trên `total` chứ không phải `answered`: hết giờ mà chưa làm xong CŨNG
     là một kết quả trong bài thi tính giờ. Số câu kịp làm vẫn gửi kèm để phân
     biệt "làm chậm" với "làm sai".
     Chưa bấm Bắt đầu thì trả null — không có gì để chấm. */
  function drillResult() {
    if (!drill || !drill.total) return null;
    var elapsed = (drill.timeTotal != null && drill.remaining != null)
      ? Math.round(drill.timeTotal - Math.max(0, drill.remaining)) : 0;
    /* Chỉ gửi CÂU TRẢ LỜI và thời lượng. `correct` / `maxCombo` / `total` do
       máy chủ dựng lại — con số tự đếm ở đây đáng 10 XP mỗi câu đúng và 5 XP
       mỗi nấc combo, tức là một cái cần gạt. */
    return { answers: drill.answers || {}, seconds: Math.max(0, elapsed) };
  }

  function saveProgress() {
    var no = state.lesson && state.lesson.index;
    if (!no) return;
    // GỠ 01/09/2026: hai dòng tách `module` từ `topic_tag` được tính rồi VỨT
    // ĐI — chú thích ngay dưới đã nói `module` thôi gửi từ L5 (31/08/2026),
    // nhưng phép tính thì ở lại. Máy chủ tự suy chương từ `lessons.module`.
    fetch('/api/lessons/' + no + '/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        courseId: state.courseId,
        /* GỬI CÂU TRẢ LỜI, KHÔNG GỬI ĐIỂM. Máy chủ chấm lại từ đáp án trong
           CSDL — xem `lessons/grading.py`. `quizScore` cũ đã bị máy chủ BỎ QUA
           (ghi bài xong nhưng không ghi điểm), nên gửi nó lên chỉ để lại một
           dòng nhật ký; thôi gửi hẳn cho khỏi ai tưởng nó còn tác dụng.

           `lessonTitle`, `module`, `xpEarned` cũng thôi gửi (L5, 31/08/2026):
           cả ba nay lấy từ dòng `lessons` ở máy chủ. Tiêu đề và chủ đề do thân
           request quyết định là cách một học viên đẻ ra bài học giả trong bảng
           dùng chung; XP do thân request quyết định là cách cộng 500 thay vì
           50 cho mỗi bài. */
        answers: state.answers,
        drill: drillResult()
      })
    })
      .then(function (r) {
        /* `/complete` NAY 404 ĐƯỢC (L5, 31/08/2026): bài không có trong khoá thì
           máy chủ nói thẳng thay vì đẻ ra nó. Nuốt im lặng thì học viên thấy màn
           chúc mừng, thấy "+50 XP", thấy pháo hoa — mà `lesson_progress` trống,
           chuỗi ngày không tăng, "Học tiếp" đứng yên. Phải nói ra. */
        if (!r.ok) {
          /* ĐỌC CÂU CỦA MÁY CHỦ TRƯỚC (vá 04/09/2026).

             Bản cũ chỉ phân biệt 404 với "mọi thứ khác", và "mọi thứ khác" hiện
             ra là *"kiểm tra mạng rồi mở lại bài"*. Với 403 ("Bạn chưa ghi danh
             khoá này") hay 400 ("làm ít nhất một câu rồi mới đánh dấu hoàn thành
             được") thì câu ấy là NÓI DỐI: mạng vẫn tốt, máy chủ đã trả lời tử
             tế, và học viên bị đẩy đi sửa nhầm chỗ.

             `error` có HAI hình dạng trong repo: chuỗi (view tự trả) và object
             `{status, message, detail}` (bộ xử lý lỗi chung). Đọc cả hai; không
             đọc được thì mới về câu chung. */
          var rx = $('reward-xp'); if (rx) rx.textContent = '—';
          return r.json().catch(function () { return null; }).then(function (d) {
            flashNote(cauLoiMayChu(r.status, d), true);
            return null;
          });
        }
        return r.json();
      })
      .then(function (d) {
        if (!d) return;
        /* XP hiện trên màn chúc mừng lấy TỪ MÁY CHỦ. Con số ước lượng ở dưới
           chỉ để modal không trống trong lúc chờ; máy chủ mới là nơi biết bài
           này thưởng bao nhiêu và phòng luyện được mấy câu. */
        if ($('reward-xp') && typeof d.xpGained === 'number') {
          $('reward-xp').textContent = '+' + d.xpGained;
        }
        // Thành tích vừa mở khoá phải được báo NGAY tại đây; học viên hiếm khi
        // tự mở trang Thành tích để phát hiện ra.
        (d.newAchievements || []).forEach(function (a, i) {
          setTimeout(function () {
            flashNote('🏅 Mở khoá thành tích: ' + (a.name || ''));
          }, 900 + i * 3000);
        });
        if (d.usedStreakFreeze) {
          setTimeout(function () {
            flashNote('❄️ Đã dùng 1 vé bảo hiểm chuỗi — chuỗi của bạn vẫn tiếp tục!');
          }, 500);
        }
      })
      .catch(function () { /* mất mạng thì thôi — không chặn màn chúc mừng */ });
  }

  function complete() {
    stopDrill();
    var m = $('success-modal');
    var xp = (state.lesson.xp_reward || 50) + (drill && drill.xp ? drill.xp : 0);
    saveProgress();
    if ($('success-lesson-title')) $('success-lesson-title').textContent = state.lesson.title || '';
    if ($('success-message')) $('success-message').textContent =
      'Bạn đã hoàn thành bài "' + (state.lesson.title || '') + '" với ' + state.score + '/' + state.total + ' câu kiểm tra đúng.';
    if ($('reward-xp')) $('reward-xp').textContent = '+' + xp;
    if (m) { m.classList.remove('hidden'); if (window.confetti) try { window.confetti({ particleCount: 90, spread: 70, origin: { y: 0.6 } }); } catch (e) {} }
  }

  /* Lời nhắc nổi — KÊNH PHẢN HỒI DUY NHẤT của cả trang bài học.
   *
   * ── VÙNG SỐNG, THÊM 05/09/2026 ────────────────────────────────────────────
   *
   * Bản cũ chỉ là một `<div>` trơn: không `role`, không `aria-live`. Người dùng
   * trình đọc màn hình KHÔNG nghe được câu nào trong bảy câu đi qua đây:
   *
   *   "Hãy trả lời đủ N câu trước khi xem đánh giá."   ← CHẶN, không đi tiếp được
   *   "Chưa chấm được — kiểm tra mạng rồi bấm lại."    ← CHẶN
   *   "Hãy hoàn thành bài kiểm tra ở Bước 1 trước."    ← CHẶN
   *   cauLoiMayChu(...)                                 ← CHẶN
   *   "🏅 Mở khoá thành tích…" / "❄️ Đã dùng 1 vé…"     ← tin vui
   *
   * Bốn câu đầu chính là LÝ DO màn hình không nhúc nhích khi bấm nút. Không
   * nghe được chúng thì trải nghiệm đúng bằng "bấm mãi mà chẳng có gì xảy ra".
   * Và mấy câu lỗi máy chủ vừa được viết lại cho chính xác hôm 04/09 — công sức
   * ấy vô hình với họ.
   *
   * HAI vùng chứ không một, và KHÔNG đổi `role` trên cùng phần tử: nhiều trình
   * đọc màn hình gắn kiểu vùng sống lúc phần tử vào DOM rồi bỏ qua thay đổi sau
   * đó. Hai vùng cố định thì không phụ thuộc vào điều ấy.
   *   · `role="alert"`  (assertive) — việc bị CHẶN, phải nghe ngay.
   *   · `role="status"` (polite)    — tin vui, chờ đọc xong câu đang đọc.
   */
  function _vungNhac(khan) {
    var id = khan ? 'hsa-flash-alert' : 'hsa-flash';
    var el = $(id);
    if (!el) {
      el = document.createElement('div');
      el.id = id;
      el.className = 'hsa-flash';
      el.setAttribute('role', khan ? 'alert' : 'status');
      el.setAttribute('aria-live', khan ? 'assertive' : 'polite');
      el.setAttribute('aria-atomic', 'true');
      document.body.appendChild(el);
    }
    return el;
  }

  function flashNote(msg, khan) {
    var el = _vungNhac(!!khan);
    /* Tách một nhịp: vùng sống phải NẰM SẴN trong DOM trước khi có chữ. Chèn
       một phần tử đã mang sẵn chữ thì phần lớn trình đọc màn hình không đọc gì
       — không có thay đổi nào để chúng bám vào. */
    setTimeout(function () {
      el.textContent = msg;
      el.classList.add('show');
      clearTimeout(el._t);
      el._t = setTimeout(function () { el.classList.remove('show'); }, 2600);
    }, 0);
  }

  /* ── API cho chrome (buttons React gọi qua window) ────────────── */
  window.HSALesson = {
    goToStep: goToStep, next: navNext, back: navBack, complete: complete,
    exit: function () { window.location.href = '/dashboard'; }
  };

  function start(lesson) {
    if (!lesson) {
      var stage = document.querySelector('.lesson-stage');
      if (stage) stage.innerHTML = '<div class="hsa-empty">' +
        '<b>Chưa tải được nội dung bài học.</b>' +
        '<p>Máy chủ nội dung đang không phản hồi. Thử tải lại trang sau giây lát.</p>' +
        '<button onclick="location.reload()">Tải lại</button></div>';
      return;
    }
    state.lesson = lesson;

    /* CÔNG BỐ BÀI ĐANG MỞ cho trợ lý chat (vá 05/09/2026).
     *
     * `chatbot.js::collectLessonContext` đọc `window.LESSON_CONTENT_HSA` — biến
     * do `lesson_content_hsa.js` đặt ra. Tệp ấy THÔI ĐƯỢC NẠP từ 19/08/2026 khi
     * 76 bài chuyển vào CSDL, nên hàm ấy rơi vào nhánh `typeof … undefined` và
     * lặng lẽ trả `null` suốt ba tuần: trợ lý mất hẳn khả năng biết học viên
     * đang ở bài nào, mà không một lỗi nào hiện ra.
     *
     * Đây là kiểu hỏng tệ nhất của một tính năng phụ: nó "vẫn chạy", chỉ là
     * chạy rỗng. Không log, không màn hình đỏ, chỉ có câu trả lời chung chung
     * hơn — thứ không ai quy được về một nguyên nhân.
     *
     * Engine ĐÃ có đúng bài ấy trong tay; nó chỉ chưa nói ra. Một biến toàn cục
     * là đủ, và nó KHÔNG dựng lại tệp 5.847 dòng: chỉ đúng bài đang mở. */
    window.__PE_BAI_DANG_MO = {
      courseId: state.courseId,
      index: state.lessonNo || null,
      lesson: lesson,
    };

    if ($('lesson-title')) $('lesson-title').textContent = lesson.title || '';
    if ($('hsa-topic-tag')) $('hsa-topic-tag').textContent = lesson.topic_tag || '';
    goToStep(1);
  }

  function init() {
    var courseId = (document.body && document.body.dataset.course) || 'hsa_quantitative';
    state.courseId = courseId;

    // ?lesson=N là SỐ BÀI. Chỉ tải ĐÚNG bài đó: trước đây trang nạp cả 76 bài
    // (440 kB gốc / 87 kB nén) chỉ để hiển thị một bài.
    var want = parseInt(new URLSearchParams(window.location.search).get('lesson'), 10);
    if (isNaN(want) || want < 1) want = 1;
    // Lưu vào `state`: trợ lý chat cần SỐ BÀI, và trước đây con số ấy chỉ tồn
    // tại như một biến cục bộ của `init()` — tức không ai ngoài hàm này đọc được.
    state.lessonNo = want;

    fetch('/api/courses/' + encodeURIComponent(courseId) + '/content?lesson=' + want)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (d && d.lesson) { state.total = d.total; start(d.lesson); return; }
        // Bài yêu cầu chưa có trong CSDL → thử bài 1 trước khi báo lỗi.
        if (want === 1) { start(null); return; }
        return fetch('/api/courses/' + encodeURIComponent(courseId) + '/content?lesson=1')
          .then(function (r2) { return r2.ok ? r2.json() : null; })
          .then(function (d2) {
            // Đã RƠI VỀ bài 1 — cập nhật số bài, nếu không trợ lý sẽ nói tên
            // bài 1 kèm số bài mà học viên vừa yêu cầu và không có.
            state.lessonNo = 1;
            start(d2 && d2.lesson);
          });
      })
      .catch(function () { start(null); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
