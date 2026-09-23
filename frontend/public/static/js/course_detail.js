function toggleModule(hd) {
  hd.classList.toggle('open');
  hd.nextElementSibling.classList.toggle('open');
}

function goLesson() {
  var el = document.getElementById('current-lesson');
  if (el) { el.click(); return; }
  window.location = LESSON_URL + '?lesson=' + (CURRENT_LESSON_IDX + 1);
}

// Scroll to the current lesson so user can see where they left off
(function () {
  var el = document.getElementById('current-lesson');
  if (el) setTimeout(function () { el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 500);
})();

/* Theme nào là mặc định: lựa chọn đã lưu > cài đặt hệ điều hành. */
function prefersDarkTheme() {
  var saved = null;
  try { saved = localStorage.getItem('theme'); } catch (e) {}
  if (saved) return saved === 'dark';
  return !!(window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches);
}

(function () {
  function applyTheme(isDark) {
    document.body.classList.toggle('dark', isDark);
    document.body.classList.toggle('light', !isDark);   // xem ghi chú ở main.js
    // Bản sao thứ hai của lỗi ghi-đè-emoji, đã gỡ — xem chú thích ở main.js.
    // `body.dark` ở trên là đủ; shell.css chọn hiện mặt trời hay mặt trăng.
  }
  window.toggleTheme = function () {
    var isDark = !document.body.classList.contains('dark');
    applyTheme(isDark);
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  };
  // Chọn tay thắng; chưa chọn thì theo hệ điều hành (khớp (base)/layout.tsx).
  // Trước đây dòng này mặc định SÁNG còn dashboard mặc định TỐI → lệch theme
  // giữa hai trang (audit 2026-08-13).
  applyTheme(prefersDarkTheme());
})();

/* ── User dropdown ──
   22/09/2026 (agent ban-phim-4): gộp ba bản chép tay của cùng phép "đóng menu"
   (nút, bấm-ra-ngoài, Esc) vào MỘT hàm `closeUserMenu`, cùng khuôn dashboard.js —
   để thêm được luật trả tiêu điểm (F9) ở một chỗ mà tầng này vẫn nhỏ đi. */
function toggleUserMenu() {
  var menu = document.getElementById('user-dropdown');
  closeBellPanel();
  if (menu.classList.contains('open')) return closeUserMenu();
  menu.classList.add('open');
  document.getElementById('user-chip-btn').classList.add('open');
  document.getElementById('user-chip-btn').setAttribute('aria-expanded', 'true');
}

function closeUserMenu() {
  var btn = document.getElementById('user-chip-btn'), menu = document.getElementById('user-dropdown');
  if (!menu || !btn) return;
  menu.classList.remove('open'); btn.classList.remove('open'); btn.setAttribute('aria-expanded', 'false');
  // Tiêu điểm trong menu vừa giấu → về nút đã mở nó; không thì rơi về <body> (agent tiếp cận F9).
  if (menu.contains(document.activeElement)) btn.focus();
}

document.addEventListener('click', function(e) {
  var userWrap = document.getElementById('user-chip-wrap'), bellWrap = document.getElementById('bell-wrap');
  if (userWrap && !userWrap.contains(e.target)) closeUserMenu();
  if (bellWrap && !bellWrap.contains(e.target)) closeBellPanel();
});

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') { closeUserMenu(); closeBellPanel(); }
});

/* ── Bell notification panel ── */
var _bellNotifs = [
  { icon: '✅', text: 'Bạn đã hoàn thành bài học đầu tiên trong khóa C++!', time: '5 phút trước', unread: true },
  { icon: '🔥', text: 'Streak 7 ngày liên tiếp! Tiếp tục phát huy nhé!', time: '2 giờ trước', unread: true },
  { icon: '📖', text: 'Khóa học Python vừa được cập nhật thêm nội dung mới.', time: 'Hôm qua', unread: true },
  { icon: '🏅', text: 'Bạn đã đạt huy hiệu "Người mới bắt đầu". Chúc mừng!', time: '3 ngày trước', unread: false },
];

function _renderBellItems() {
  var body = document.getElementById('bell-panel-body');
  if (!body) return;
  if (!_bellNotifs.length) {
    body.innerHTML = '<div class="bell-empty"><div class="bell-empty-icon">🔕</div><div>Chưa có thông báo nào</div></div>';
    return;
  }
  // Mục là <button> thật, giữ tiêu điểm qua lượt dựng lại — lý do đầy đủ ở
  // `dashboard.js::_renderBellItems` (agent tiếp cận F8, 22/09/2026).
  var dangO = Array.prototype.indexOf.call(body.children, document.activeElement);
  body.innerHTML = _bellNotifs.map(function(n, i) {
    return '<button type="button" class="bell-item' + (n.unread ? ' unread' : '') + '" onclick="readBellItem(' + i + ')">'
      + '<span class="bell-item-icon" aria-hidden="true">' + n.icon + '</span>'
      + '<span class="bell-item-body">'
      + '<span class="bell-item-text">' + n.text + '</span>'
      + '<span class="bell-item-time">' + n.time + '</span>'
      + '</span>'
      + (n.unread ? '<span class="bell-unread-dot"><span class="sr-only">(chưa đọc)</span></span>' : '')
      + '</button>';
  }).join('');
  if (body.children[dangO]) body.children[dangO].focus();
}

function _updateBellDot() {
  var dot = document.getElementById('bell-dot');
  if (!dot) return;
  var hasUnread = _bellNotifs.some(function(n) { return n.unread; });
  dot.style.display = hasUnread ? '' : 'none';
}

function toggleBellPanel() {
  var panel = document.getElementById('bell-panel');
  if (panel.classList.contains('open')) return closeBellPanel();
  closeUserMenu();
  _renderBellItems();
  panel.classList.add('open');
  document.getElementById('bell-btn').setAttribute('aria-expanded', 'true');
}

function closeBellPanel() {
  var panel = document.getElementById('bell-panel');
  var btn   = document.getElementById('bell-btn');
  if (panel) panel.classList.remove('open');
  if (btn)   btn.setAttribute('aria-expanded', 'false');
  if (panel && btn && panel.contains(document.activeElement)) btn.focus();   // F9, như closeUserMenu
}

function readBellItem(idx) {
  if (_bellNotifs[idx]) {
    _bellNotifs[idx].unread = false;
    _renderBellItems();
    _updateBellDot();
  }
}

function markAllBellRead() {
  _bellNotifs.forEach(function(n) { n.unread = false; });
  _renderBellItems();
  _updateBellDot();
}

/* ── Interactive Star Rating ── */
(function () {
  var fillEl = document.querySelector('.star-avg-fill');
  if (fillEl) fillEl.style.width = (fillEl.dataset.fill || 0) + '%';

  var container = document.getElementById('starInteractive');
  var rateVal   = document.getElementById('userRateVal');
  if (!container || !rateVal) return;

  var stars = container.querySelectorAll('.si-star');
  var selectedRating = 0;

  var LABELS = {
    0.5: 'Quá tệ', 1: 'Rất tệ', 1.5: 'Tệ', 2: 'Không tốt',
    2.5: 'Tạm được', 3: 'Bình thường', 3.5: 'Khá ổn',
    4: 'Tốt', 4.5: 'Rất tốt', 5: 'Xuất sắc! 🎉'
  };

  function paintStars(val) {
    stars.forEach(function (star, i) {
      var n = i + 1;
      star.classList.remove('star-full', 'star-half');
      if (val >= n)            star.classList.add('star-full');
      else if (val >= n - 0.5) star.classList.add('star-half');
    });
  }

  function updateLabel(val) {
    rateVal.textContent = val ? val + ' ★  ' + (LABELS[val] || '') : '—';
  }

  stars.forEach(function (star) {
    star.addEventListener('mousemove', function (e) {
      var rect = star.getBoundingClientRect();
      var isLeft = (e.clientX - rect.left) < rect.width / 2;
      var n = parseInt(star.dataset.star);
      paintStars(isLeft ? n - 0.5 : n);
      updateLabel(isLeft ? n - 0.5 : n);
    });
    star.addEventListener('click', function (e) {
      var rect = star.getBoundingClientRect();
      var isLeft = (e.clientX - rect.left) < rect.width / 2;
      var n = parseInt(star.dataset.star);
      selectedRating = isLeft ? n - 0.5 : n;
      paintStars(selectedRating);
      updateLabel(selectedRating);
    });
  });

  container.addEventListener('mouseleave', function () {
    paintStars(selectedRating);
    updateLabel(selectedRating);
  });

  paintStars(0);
})();
