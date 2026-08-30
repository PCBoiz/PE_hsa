document.addEventListener("DOMContentLoaded", function() {
    /* Hiệu ứng hiện dần khi cuộn. `.reveal-on-scroll` để opacity:0 nên NẾU
       phần này không chạy thì cả trang dưới hero biến mất — phải có đường lùi. */
    function revealAll() {
      document.querySelectorAll('.reveal-on-scroll').forEach(el => el.classList.add('visible'));
    }

    if (!('IntersectionObserver' in window)) {
      revealAll();
    } else {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) entry.target.classList.add('visible');
        });
      }, { threshold: 0.1 });
      document.querySelectorAll('.reveal-on-scroll').forEach(el => observer.observe(el));

      // Lưới an toàn: observer lỡ nhịp (ảnh chụp toàn trang, khôi phục vị trí
      // cuộn, tab nền…) thì hiện hết, không để trang trống trơn. Để ngắn vì
      // script này nạp SAU khi React hydrate — đo được là mốc 1s vẫn còn ẩn cả
      // 8 mục, tức khách nhìn thấy khoảng trống thật trong khoảng đó.
      setTimeout(revealAll, 1200);
    }

    /* ── Số liệu hero + lưới khoá học ──────────────────────────────────────
       Trước 2026-08-14 trang này gọi /api/courses — endpoint YÊU CẦU ĐĂNG NHẬP.
       Khách vãng lai (kể cả đối tác mở link) nhận 401, lưới khoá học không
       render và để lại một khoảng TRỐNG khổng lồ giữa trang. Nay gọi
       /api/public/courses, ai cũng xem được. ── */
    function setHeroStats(courses) {
      const el = document.getElementById('stat-courses');
      if (el) el.textContent = courses.length || '3';
      const hoursEl = document.getElementById('stat-hours');
      if (!hoursEl) return;
      // "Bài" là con số CHẮC CHẮN của mình (đếm từ CSDL), khác với các con số
      // về cấu trúc đề — thứ phải chờ TopHSA xác nhận.
      const lessons = courses.reduce((n, c) => n + (c.lessons || 0), 0);
      if (lessons > 0) hoursEl.textContent = lessons;
    }

    function renderCourses(courses) {
      const grid = document.getElementById('course-preview-grid');
      const loading = document.getElementById('course-preview-loading');
      if (!grid) return;
      if (loading) loading.style.display = 'none';
      grid.innerHTML = '';
      courses.slice(0, 4).forEach(c => {
        const card = document.createElement('a');
        card.href = '/login';
        card.className = 'section-card neon-card course-preview-card';
        card.innerHTML =
          '<div class="card-icon neon-icon" style="color:' + (c.accent_color || c.color || '#8B7CF6') + '">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
            '<path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 ' +
            '7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 ' +
            '14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>' +
            '</svg></div>' +
          '<strong>' + (c.title || 'Khoá học') + '</strong>' +
          '<p>' + (c.subtitle || c.description || '') + '</p>' +
          '<span class="course-preview-meta">' +
            (c.lessons ? c.lessons + ' bài' : '') +
            (c.duration ? ' · ' + c.duration : '') +
          '</span>';
        grid.appendChild(card);
      });
    }

    function courseFallback() {
      // Máy chủ ngủ đông (Render gói free) hoặc mất mạng → vẫn phải thấy 3 hợp
      // phần, tuyệt đối không để lại khoảng trống giữa trang.
      return [
        { id: 'hsa_quantitative', title: 'Tư duy Định lượng', accent_color: '#A78BFA',
          subtitle: 'Toán học – xử lý số liệu' },
        { id: 'hsa_verbal', title: 'Tư duy Định tính', accent_color: '#F472B6',
          subtitle: 'Ngữ văn – ngôn ngữ' },
        { id: 'hsa_science', title: 'Khoa học & Tiếng Anh', accent_color: '#34D399',
          subtitle: 'Lý – Hoá – Sinh – Sử – Địa hoặc Tiếng Anh' },
      ];
    }

    fetch('/api/public/courses')
      .then(r => (r.ok ? r.json() : null))
      .then(d => {
        const courses = (d && d.courses && d.courses.length) ? d.courses : courseFallback();
        setHeroStats(courses);
        renderCourses(courses);
      })
      .catch(() => {
        const courses = courseFallback();
        setHeroStats(courses);
        renderCourses(courses);
      });
  });
