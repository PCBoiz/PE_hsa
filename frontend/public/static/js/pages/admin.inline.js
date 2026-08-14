    let editCourseId = null;   // null = đang tạo mới
    let editLessonId = null;
    let activeCourse = null;   // course_id đang xem bài giảng

    function toast(msg) {
      const t = document.getElementById('toast');
      t.textContent = msg; t.classList.add('show');
      setTimeout(() => t.classList.remove('show'), 2200);
    }

    async function api(url, opts) {
      const res = await fetch(url, opts);
      let data = {};
      try { data = await res.json(); } catch (e) {}
      if (!res.ok) {
        const err = new Error(data.error || 'Lỗi không xác định');
        // Máy chủ trả kèm `details` — danh sách lỗi có VỊ TRÍ ("bài thứ 2.test…").
        // Không mang theo thì người soạn chỉ thấy "Nội dung chưa hợp lệ".
        err.detailList = Array.isArray(data.details) ? data.details : null;
        throw err;
      }
      return data;
    }

    // ───── Khóa học ─────
    async function loadCourses() {
      const { courses } = await api('/api/admin/courses');
      const tb = document.getElementById('courseRows');
      tb.innerHTML = '';
      courses.forEach(c => {
        const tr = document.createElement('tr');
        tr.dataset.course = c.id;
        if (c.id === activeCourse) tr.classList.add('sel');
        tr.innerHTML = `
          <td>${esc(c.id)}</td>
          <td>${esc(c.title || '')}</td>
          <td>${c.lessons ?? 0}</td>
          <td style="white-space:nowrap">
            <button class="btn-ghost" onclick="editCourse(event, '${esc(c.id)}')">Sửa</button>
            <button class="btn-danger" onclick="delCourse(event, '${esc(c.id)}')">Xóa</button>
          </td>`;
        tr.onclick = () => selectCourse(c.id, c.title);
        tr.dataset.json = JSON.stringify(c);
        tb.appendChild(tr);
      });
    }

    async function saveCourse() {
      const body = {
        id: val('cId'), title: val('cTitle'), subtitle: val('cSubtitle'),
        description: val('cDescription'), level: val('cLevel'),
        duration: val('cDuration'), tag: val('cTag'), image: val('cImage'),
        color: val('cColor'), accent_color: val('cAccentColor'),
      };
      try {
        if (editCourseId) {
          await api('/api/admin/courses/' + encodeURIComponent(editCourseId), {
            method: 'PUT', headers: json(), body: JSON.stringify(body)
          });
          toast('Đã cập nhật khóa học');
        } else {
          await api('/api/admin/courses', {
            method: 'POST', headers: json(), body: JSON.stringify(body)
          });
          toast('Đã thêm khóa học');
        }
        resetCourseForm();
        loadCourses();
      } catch (e) { toast(e.message); }
    }

    function editCourse(ev, id) {
      ev.stopPropagation();
      const tr = document.querySelector(`tr[data-course="${id}"]`);
      const c = JSON.parse(tr.dataset.json);
      editCourseId = id;
      document.getElementById('courseFormTitle').textContent = 'Sửa khóa học: ' + id;
      set('cId', c.id); document.getElementById('cId').disabled = true;
      set('cTitle', c.title); set('cSubtitle', c.subtitle); set('cDescription', c.description);
      set('cLevel', c.level); set('cDuration', c.duration); set('cTag', c.tag);
      set('cImage', c.image); set('cColor', c.color); set('cAccentColor', c.accent_color);
    }

    async function delCourse(ev, id) {
      ev.stopPropagation();
      if (!confirm('Xóa khóa học "' + id + '"? Toàn bộ bài giảng của khóa cũng bị xóa.')) return;
      try {
        await api('/api/admin/courses/' + encodeURIComponent(id), { method: 'DELETE' });
        toast('Đã xóa khóa học');
        if (activeCourse === id) clearLessons();
        loadCourses();
      } catch (e) { toast(e.message); }
    }

    function resetCourseForm() {
      editCourseId = null;
      document.getElementById('courseFormTitle').textContent = 'Thêm khóa học';
      document.getElementById('cId').disabled = false;
      ['cId','cTitle','cSubtitle','cDescription','cLevel','cDuration','cTag','cImage','cColor','cAccentColor']
        .forEach(id => set(id, ''));
    }

    // ───── Bài giảng ─────
    function selectCourse(id, title) {
      activeCourse = id;
      document.querySelectorAll('tr[data-course]').forEach(tr =>
        tr.classList.toggle('sel', tr.dataset.course === id));
      document.getElementById('lessonTitle').textContent = 'Bài giảng — ' + (title || id);
      document.getElementById('lessonHint').style.display = 'none';
      document.getElementById('lessonFormBox').style.display = 'block';
      const ic = document.getElementById('importCourse');
      if (ic) ic.textContent = 'Nhập vào khoá: ' + (title || id);
      resetLessonForm();
      loadLessons();
    }

    function clearLessons() {
      activeCourse = null;
      document.getElementById('lessonRows').innerHTML = '';
      document.getElementById('lessonTitle').textContent = 'Bài giảng';
      document.getElementById('lessonHint').style.display = 'block';
      document.getElementById('lessonFormBox').style.display = 'none';
    }

    async function loadLessons() {
      const { lessons } = await api('/api/admin/courses/' + encodeURIComponent(activeCourse) + '/lessons');
      const tb = document.getElementById('lessonRows');
      tb.innerHTML = '';
      lessons.forEach(l => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${l.sort_order ?? 0}</td>
          <td>${esc(l.module || '')}</td>
          <td>${esc(l.title || '')}</td>
          <td style="white-space:nowrap">
            <button class="btn-primary" onclick="openContent(${l.id})">Soạn</button>
            <button class="btn-ghost" onclick="editLesson(${l.id})">Sửa</button>
            <button class="btn-danger" onclick="delLesson(${l.id})">Xóa</button>
          </td>`;
        tr.dataset.json = JSON.stringify(l);
        tb.appendChild(tr);
      });
    }

    async function saveLesson() {
      const body = {
        course_id: activeCourse, module: val('lModule'),
        title: val('lLessonTitle'), content: val('lContent'),
        sort_order: parseInt(val('lSort') || '0', 10),
      };
      try {
        if (editLessonId) {
          await api('/api/admin/lessons/' + editLessonId, {
            method: 'PUT', headers: json(), body: JSON.stringify(body)
          });
          toast('Đã cập nhật bài giảng');
        } else {
          await api('/api/admin/lessons', {
            method: 'POST', headers: json(), body: JSON.stringify(body)
          });
          toast('Đã thêm bài giảng');
        }
        resetLessonForm();
        loadLessons();
        loadCourses();
      } catch (e) { toast(e.message); }
    }

    function editLesson(id) {
      const tr = [...document.querySelectorAll('#lessonRows tr')]
        .find(t => JSON.parse(t.dataset.json).id === id);
      const l = JSON.parse(tr.dataset.json);
      editLessonId = id;
      document.getElementById('lessonFormTitle').textContent = 'Sửa bài giảng';
      set('lModule', l.module); set('lLessonTitle', l.title);
      set('lContent', l.content); set('lSort', l.sort_order ?? 0);
    }

    async function delLesson(id) {
      if (!confirm('Xóa bài giảng này?')) return;
      try {
        await api('/api/admin/lessons/' + id, { method: 'DELETE' });
        toast('Đã xóa bài giảng');
        loadLessons();
        loadCourses();
      } catch (e) { toast(e.message); }
    }

    function resetLessonForm() {
      editLessonId = null;
      document.getElementById('lessonFormTitle').textContent = 'Thêm bài giảng';
      ['lModule','lLessonTitle','lContent'].forEach(id => set(id, ''));
      set('lSort', '0');
    }


    /* ══════════════════════════════════════════════════════════════════════
       SOẠN NỘI DUNG BÀI HỌC — ghi vào lessons.content_json
       Trước 2026-08-14 trang này chỉ ghi được cột `content` (TEXT) mà engine
       không đọc, nên bài tạo ở đây học viên không bao giờ thấy.
       ══════════════════════════════════════════════════════════════════════ */
    let contentLessonId = null;

    /* ── Khối lặp: câu hỏi ── */
    function questionRow(q) {
      q = q || {};
      const isFill = (q.type || 'mcq') === 'fill';
      const div = document.createElement('div');
      div.className = 'rep-item';
      div.innerHTML =
        '<div class="rep-head">' +
          '<select class="q-type">' +
            '<option value="mcq"' + (isFill ? '' : ' selected') + '>Trắc nghiệm</option>' +
            '<option value="fill"' + (isFill ? ' selected' : '') + '>Điền đáp án</option>' +
          '</select>' +
          '<input class="q-id" placeholder="mã câu (t1)" value="' + esc(q.id || '') + '" />' +
          '<button class="btn-danger btn-sm" type="button">Xoá</button>' +
        '</div>' +
        '<textarea class="q-question" placeholder="Nội dung câu hỏi">' + esc(q.question || '') + '</textarea>' +
        '<label class="q-opts-wrap">Các lựa chọn — <span class="hint-inline">mỗi dòng một lựa chọn</span>' +
          '<textarea class="q-options" placeholder="375.000đ&#10;350.000đ&#10;300.000đ">' +
            esc((q.options || []).join('\n')) + '</textarea>' +
        '</label>' +
        '<input class="q-answer" placeholder="Đáp án đúng (phải trùng đúng một dòng ở trên)" value="' +
          esc(q.answer == null ? '' : q.answer) + '" />' +
        '<input class="q-explain" placeholder="Giải thích (hiện sau khi chấm)" value="' +
          esc(q.explain || '') + '" />';
      div.querySelector('.btn-danger').onclick = () => div.remove();
      const sel = div.querySelector('.q-type');
      const optsWrap = div.querySelector('.q-opts-wrap');
      const syncType = () => { optsWrap.style.display = sel.value === 'fill' ? 'none' : 'block'; };
      sel.onchange = syncType; syncType();
      return div;
    }

    function readQuestions(containerId) {
      return Array.from(document.getElementById(containerId).children).map((el, i) => {
        const type = el.querySelector('.q-type').value;
        const q = {
          id: el.querySelector('.q-id').value.trim() || ('q' + (i + 1)),
          type: type,
          question: el.querySelector('.q-question').value.trim(),
          answer: el.querySelector('.q-answer').value.trim(),
        };
        const ex = el.querySelector('.q-explain').value.trim();
        if (ex) q.explain = ex;
        if (type === 'mcq') {
          q.options = el.querySelector('.q-options').value
            .split('\n').map(x => x.trim()).filter(Boolean);
        }
        return q;
      });
    }

    /* ── Khối lặp: thẻ lý thuyết ── */
    function cardRow(c) {
      c = c || {};
      const div = document.createElement('div');
      div.className = 'rep-item';
      div.innerHTML =
        '<div class="rep-head">' +
          '<input class="c-icon" placeholder="fa-book" value="' + esc(c.icon || '') + '" />' +
          '<input class="c-title" placeholder="Tiêu đề thẻ" value="' + esc(c.title || '') + '" />' +
          '<button class="btn-danger btn-sm" type="button">Xoá</button>' +
        '</div>' +
        '<textarea class="c-body" placeholder="Nội dung thẻ (cho phép thẻ HTML nhẹ)">' +
          esc(c.body || '') + '</textarea>' +
        '<label>Minh hoạ — <span class="hint-inline">JSON, để trống nếu không có. 8 kiểu: ' +
          'bars · numline · curve · flow · table · pie · tree · timeline</span>' +
          '<textarea class="c-visual" placeholder=\'{"type":"bars","bars":[{"label":"A","value":10}]}\'>' +
            (c.visual ? esc(JSON.stringify(c.visual, null, 1)) : '') + '</textarea>' +
        '</label>';
      div.querySelector('.btn-danger').onclick = () => div.remove();
      return div;
    }

    /* Trả về {cards, errors} — JSON minh hoạ hỏng thì BÁO chứ không nuốt lặng,
       nếu không người soạn sẽ tưởng đã lưu mà đồ thị thì biến mất. */
    function readCards(containerId, nhan) {
      const cards = [], errors = [];
      Array.from(document.getElementById(containerId).children).forEach((el, i) => {
        const card = {
          icon: el.querySelector('.c-icon').value.trim() || 'fa-book',
          title: el.querySelector('.c-title').value.trim(),
          body: el.querySelector('.c-body').value.trim(),
        };
        const raw = el.querySelector('.c-visual').value.trim();
        if (raw) {
          try { card.visual = JSON.parse(raw); }
          catch (e) { errors.push(nhan + ' — thẻ ' + (i + 1) + ': minh hoạ không phải JSON hợp lệ (' + e.message + ')'); }
        }
        cards.push(card);
      });
      return { cards: cards, errors: errors };
    }

    window.addQuestion = id => document.getElementById(id).appendChild(questionRow());
    window.addCard = id => document.getElementById(id).appendChild(cardRow());

    window.switchVariant = (btn, variant) => {
      document.querySelectorAll('.tab').forEach(t => t.classList.toggle('is-on', t === btn));
      document.querySelectorAll('.variant-pane').forEach(p => {
        p.style.display = p.dataset.pane === variant ? 'block' : 'none';
      });
    };

    function fillRepeat(containerId, items, factory) {
      const box = document.getElementById(containerId);
      box.innerHTML = '';
      (items || []).forEach(it => box.appendChild(factory(it)));
    }

    function showErrors(list) {
      const box = document.getElementById('contentErrors');
      if (!list || !list.length) { box.style.display = 'none'; box.innerHTML = ''; return; }
      box.style.display = 'block';
      box.className = 'err-box';
      box.innerHTML = '<b>Chưa lưu được — cần sửa:</b><ul>' +
        list.map(e => '<li>' + esc(e) + '</li>').join('') + '</ul>';
      box.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    window.openContent = async function (lessonId) {
      try {
        const row = await api('/api/admin/lessons/' + lessonId + '/content');
        contentLessonId = lessonId;
        const c = row.content_json || {};
        document.getElementById('contentTitle').textContent =
          'Nội dung bài — ' + (row.title || ('#' + row.sort_order));
        document.getElementById('contentHint').style.display = 'none';
        document.getElementById('contentForm').style.display = 'block';
        document.getElementById('contentActions').style.display = 'flex';
        const idx = c.index || row.sort_order || 1;
        document.getElementById('btnPreview').href =
          '/lesson/' + encodeURIComponent(row.course_id) + '?lesson=' + idx;

        set('fId', c.id || ''); set('fIndex', idx);
        set('fTitle', c.title || row.title || ''); set('fSubtitle', c.subtitle || '');
        set('fTopic', c.topic_tag || ''); set('fXp', c.xp_reward == null ? 50 : c.xp_reward);

        const test = c.test || {};
        set('fTestIntro', test.intro || '');
        fillRepeat('testQs', test.questions, questionRow);
        const as = c.assess || {};
        set('fStrongMin', as.strong_min == null ? '' : as.strong_min);
        set('fOkMin', as.ok_min == null ? '' : as.ok_min);

        const th = c.theory || {};
        set('fFullTitle', (th.full || {}).title || '');
        fillRepeat('fullCards', (th.full || {}).cards, cardRow);
        set('fCondTitle', (th.condensed || {}).title || '');
        fillRepeat('condCards', (th.condensed || {}).cards, cardRow);

        const note = c.note || {};
        set('fNoteTitle', note.title || '');
        set('fNotePoints', (note.points || []).join('\n'));

        const drill = c.drill || {};
        set('fDrillIntro', drill.intro || '');
        set('fDrillSeconds', drill.seconds == null ? 60 : drill.seconds);
        fillRepeat('drillQs', drill.questions, questionRow);

        showErrors(null);
        document.getElementById('contentSection').scrollIntoView({ behavior: 'smooth' });
      } catch (e) { toast(e.message); }
    };

    function collectContent() {
      const full = readCards('fullCards', 'Bản đầy đủ');
      const cond = readCards('condCards', 'Bản tóm tắt');
      const errors = full.errors.concat(cond.errors);

      const obj = {
        id: val('fId'),
        index: parseInt(val('fIndex'), 10),
        title: val('fTitle'),
        topic_tag: val('fTopic'),
        xp_reward: parseInt(val('fXp'), 10) || 50,
        test: { intro: val('fTestIntro'), questions: readQuestions('testQs') },
        theory: {},
      };
      if (val('fSubtitle')) obj.subtitle = val('fSubtitle');

      const sm = parseInt(val('fStrongMin'), 10), om = parseInt(val('fOkMin'), 10);
      if (!isNaN(sm) || !isNaN(om)) {
        obj.assess = {};
        if (!isNaN(sm)) obj.assess.strong_min = sm;
        if (!isNaN(om)) obj.assess.ok_min = om;
      }
      if (full.cards.length) obj.theory.full = { title: val('fFullTitle'), cards: full.cards };
      if (cond.cards.length) obj.theory.condensed = { title: val('fCondTitle'), cards: cond.cards };

      const points = val('fNotePoints').split('\n').map(x => x.trim()).filter(Boolean);
      if (points.length) obj.note = { title: val('fNoteTitle') || 'Ghi nhớ', points: points };

      const dq = readQuestions('drillQs');
      if (dq.length) {
        obj.drill = {
          intro: val('fDrillIntro'),
          seconds: parseInt(val('fDrillSeconds'), 10) || 60,
          questions: dq,
        };
      }
      return { obj: obj, errors: errors };
    }

    window.saveLessonContent = async function () {
      if (!contentLessonId) return;
      const res = collectContent();
      if (res.errors.length) { showErrors(res.errors); return; }
      try {
        await api('/api/admin/lessons/' + contentLessonId + '/content', {
          method: 'PUT', headers: json(), body: JSON.stringify({ content_json: res.obj }),
        });
        showErrors(null);
        toast('Đã lưu nội dung bài học');
        loadLessons();
      } catch (e) {
        // Máy chủ kiểm lần nữa và trả danh sách lỗi có vị trí cụ thể.
        showErrors(e.detailList || [e.message]);
      }
    };

    window.clearLessonContent = async function () {
      if (!contentLessonId) return;
      if (!confirm('Xoá nội dung bài này? Bài sẽ quay về dùng nội dung mặc định trong mã nguồn.')) return;
      try {
        await api('/api/admin/lessons/' + contentLessonId + '/content', {
          method: 'PUT', headers: json(), body: JSON.stringify({ content_json: null }),
        });
        toast('Đã xoá nội dung — bài dùng lại bản mặc định');
        openContent(contentLessonId);
      } catch (e) { toast(e.message); }
    };

    /* ── Nhập cả khoá từ file JSON ── */
    function bindImportFile() {
      const fileInput = document.getElementById('importFile');
      if (!fileInput) return;
      fileInput.onchange = () => {
        const f = fileInput.files && fileInput.files[0];
        if (!f) return;
        const rd = new FileReader();
        rd.onload = () => { document.getElementById('importText').value = rd.result; };
        rd.readAsText(f, 'utf-8');
      };
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', bindImportFile);
    } else { bindImportFile(); }

    window.importCourse = async function () {
      const box = document.getElementById('importResult');
      if (!activeCourse) { toast('Chọn một khoá học trước'); return; }
      const raw = val('importText');
      if (!raw) { toast('Chưa có dữ liệu để nhập'); return; }

      let payload;
      try { payload = JSON.parse(raw); }
      catch (e) {
        box.style.display = 'block';
        box.className = 'err-box';
        box.innerHTML = '<b>File không phải JSON hợp lệ:</b><br>' + esc(e.message);
        return;
      }
      // Chấp nhận cả mảng bài trần lẫn object bọc {lessons:[…]}.
      if (Array.isArray(payload)) payload = { lessons: payload };
      const total = parseInt(val('importTotal'), 10);
      if (!isNaN(total) && total > 0) payload.total_lessons = total;

      try {
        const res = await api('/api/admin/courses/' + encodeURIComponent(activeCourse) + '/import', {
          method: 'POST', headers: json(), body: JSON.stringify(payload),
        });
        box.style.display = 'block';
        box.className = 'err-box is-ok';
        box.innerHTML = '<b>Nhập xong.</b> Tạo mới ' + res.created + ' bài · cập nhật ' + res.updated + ' bài.';
        toast('Đã nhập ' + res.total + ' bài');
        loadCourses(); loadLessons();
      } catch (e) {
        box.style.display = 'block';
        box.className = 'err-box';
        const list = e.detailList || [];
        box.innerHTML = '<b>' + esc(e.message) + '</b>' +
          (list.length ? '<ul>' + list.map(d => '<li>' + esc(d) + '</li>').join('') + '</ul>' : '');
      }
    };

    // ───── Helpers ─────
    function val(id) { return document.getElementById(id).value.trim(); }
    function set(id, v) { document.getElementById(id).value = v == null ? '' : v; }
    function json() { return { 'Content-Type': 'application/json' }; }
    function esc(s) {
      return String(s).replace(/[&<>"']/g, m =>
        ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m]));
    }

    loadCourses();
