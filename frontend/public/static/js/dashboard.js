/* ═══════════════════════════════════════════════════════
   dashboard.js — tất cả JS riêng cho dashboard.html
   ═══════════════════════════════════════════════════════ */

/* Lớp bảo vệ độc lập: đảm bảo trang Roadmap/Skills luôn được khởi tạo
   khi điều hướng tới, kể cả khi 1 đoạn code khác phía dưới trong file
   này lỗi (1 lỗi JS ở top-level sẽ chặn các IIFE phía sau không chạy). */
(function () {
  var _orig = window.navigate;
  window.navigate = function (page) {
    _orig(page);
    try {
      if (page === 'roadmap' && typeof window.initRoadmapPage === 'function') {
        window.initRoadmapPage();
      }
    } catch (e) { console.error('[roadmap] init error:', e); }
  };
})();

/* ── User avatar dropdown ── */
function toggleUserMenu() {
  var wrap = document.getElementById('user-chip-wrap');
  var btn = document.getElementById('user-chip-btn');
  var menu = document.getElementById('user-dropdown');
  var open = menu.classList.contains('open');
  if (open) {
    menu.classList.remove('open');
    btn.classList.remove('open');
    btn.setAttribute('aria-expanded', 'false');
  } else {
    menu.classList.add('open');
    btn.classList.add('open');
    btn.setAttribute('aria-expanded', 'true');
  }
}

function closeUserMenu() {
  var btn = document.getElementById('user-chip-btn');
  var menu = document.getElementById('user-dropdown');
  menu.classList.remove('open');
  btn.classList.remove('open');
  btn.setAttribute('aria-expanded', 'false');
}

document.addEventListener('click', function (e) {
  var wrap = document.getElementById('user-chip-wrap');
  if (wrap && !wrap.contains(e.target)) closeUserMenu();
});

document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') closeUserMenu();
});

/* Sync tên hiển thị trong dropdown header khi mở */
var _origToggleUserMenu = toggleUserMenu;
toggleUserMenu = function () {
  var n = document.getElementById('chip-name');
  var d = document.getElementById('udh-name');
  if (n && d) d.textContent = n.textContent;
  closeBellPanel();
  _origToggleUserMenu();
};

/* ── Bell notification panel — nối với /api/notifications/feed (DB thật) ── */
var _bellNotifs = [];
var _bellServerUnread = 0; // badge count từ server (COUNT(*) WHERE is_read=false)
var _BELL_ICON = { mention: '💬', comment_reply: '↩️', post_comment: '📝', system: '🔔' };

function _bellTimeAgo(iso) {
  if (!iso) return '';
  var s = /[Zz]|[+][0-9]/.test(iso) ? iso : String(iso).replace(' ', 'T') + 'Z';
  var diff = Math.floor((Date.now() - new Date(s).getTime()) / 1000);
  if (isNaN(diff)) return '';
  if (diff < 60) return 'vừa xong';
  if (diff < 3600) return Math.floor(diff / 60) + ' phút trước';
  if (diff < 86400) return Math.floor(diff / 3600) + ' giờ trước';
  return Math.floor(diff / 86400) + ' ngày trước';
}

function _escBell(s) {
  return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function loadBellNotifs() {
  return fetch('/api/notifications/feed')
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d) return;
      _bellNotifs = (d.items || []).map(function (n) {
        return {
          id: n.id, icon: _BELL_ICON[n.type] || '🔔',
          title: n.title || '', body: n.body || '',
          time: _bellTimeAgo(n.created_at), unread: !n.is_read,
          refType: n.ref_type || null, refId: n.ref_id || null
        };
      });
      _bellServerUnread = d.unread || 0;
      _renderBellItems();
      _updateBellDot();
    })
    .catch(function () {});
}

function _renderBellItems() {
  var body = document.getElementById('bell-panel-body');
  if (!body) return;
  if (!_bellNotifs.length) {
    body.innerHTML = '<div class="bell-empty"><div class="bell-empty-icon">🔕</div><div>Chưa có thông báo nào</div></div>';
    return;
  }
  body.innerHTML = _bellNotifs.map(function (n, i) {
    return '<div class="bell-item' + (n.unread ? ' unread' : '') + '" onclick="readBellItem(' + i + ')" role="menuitem" tabindex="0">'
      + '<div class="bell-item-icon">' + n.icon + '</div>'
      + '<div class="bell-item-body">'
      + '<div class="bell-item-text">' + _escBell(n.title) + (n.body ? ': ' + _escBell(n.body) : '') + '</div>'
      + '<div class="bell-item-time">' + _escBell(n.time) + '</div>'
      + '</div>'
      + (n.unread ? '<div class="bell-unread-dot"></div>' : '')
      + '</div>';
  }).join('');
}

function _updateBellDot() {
  var dot = document.getElementById('bell-dot');
  if (!dot) return;
  var count = _bellServerUnread;
  if (!count) count = _bellNotifs.filter(function (n) { return n.unread; }).length;
  if (count > 0) {
    dot.style.display = '';
    dot.classList.add('bell-dot-count');
    dot.textContent = count > 9 ? '9+' : String(count);
  } else {
    dot.style.display = 'none';
    dot.textContent = '';
  }
}

function toggleBellPanel() {
  var panel = document.getElementById('bell-panel');
  var btn = document.getElementById('bell-btn');
  var open = panel.classList.contains('open');
  if (open) {
    panel.classList.remove('open');
    btn.setAttribute('aria-expanded', 'false');
  } else {
    closeUserMenu();
    loadBellNotifs();   // tải mới mỗi lần mở
    _renderBellItems();
    panel.classList.add('open');
    btn.setAttribute('aria-expanded', 'true');
  }
}

function closeBellPanel() {
  var panel = document.getElementById('bell-panel');
  var btn = document.getElementById('bell-btn');
  if (panel) panel.classList.remove('open');
  if (btn) btn.setAttribute('aria-expanded', 'false');
}

// Điều hướng tới bài viết của thông báo và mở khung bình luận chứa @mention.
function _focusForumPost(postId) {
  closeBellPanel();
  if (typeof window.navigate === 'function') window.navigate('forum');
  // renderPosts chạy async (chờ API) -> thử tìm card nhiều lần rồi scroll + mở comment.
  var tries = 0;
  var timer = setInterval(function () {
    tries++;
    var card = document.getElementById('fpc-' + postId);
    if (card) {
      clearInterval(timer);
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Nhấp nháy nhẹ để user nhận ra bài
      card.style.transition = 'box-shadow .3s';
      card.style.boxShadow = '0 0 0 2px var(--blue, #3B82F6)';
      setTimeout(function () { card.style.boxShadow = ''; }, 1600);
      // Mở khung bình luận để thấy @mention
      if (typeof window.forumToggleComments === 'function') {
        var section = document.getElementById('fpc-cmt-' + postId);
        if (section && !section.classList.contains('open')) window.forumToggleComments(postId);
      }
    } else if (tries > 40) {  // ~10s (Neon cold-start) rồi bỏ cuộc
      clearInterval(timer);
    }
  }, 250);
}

function readBellItem(idx) {
  var n = _bellNotifs[idx];
  if (!n) return;
  if (n.unread) {
    n.unread = false;
    if (_bellServerUnread > 0) _bellServerUnread--;
    _renderBellItems();
    _updateBellDot();
    if (n.id) fetch('/api/notifications/feed/' + n.id + '/read', { method: 'POST' }).catch(function () {});
  }
  // Di chuyển tới bài viết có @mention
  if (n.refType === 'post' && n.refId) _focusForumPost(n.refId);
}

function markAllBellRead() {
  _bellNotifs.forEach(function (n) { n.unread = false; });
  _bellServerUnread = 0;
  _renderBellItems();
  _updateBellDot();
  fetch('/api/notifications/feed/read-all', { method: 'POST' }).catch(function () {});
}

/* ── Badge chuông: client poll /api/notifications/badge mỗi 45s ──
 * PERF 2026-07-19: thay SSE (/api/notifications/stream đã gỡ). SSE giữ 1
 * thread/user suốt ~1h phía server + poll DB 3s/kết nối → nhiều user online
 * là cạn worker. Poll 45s: trễ badge tối đa 45s (chấp nhận được cho chuông),
 * chỉ poll khi tab đang hiển thị. fetch('/api/...') đi qua pe-bridge nên tự
 * có Authorization + refresh token — không cần trò token-qua-query của SSE. */
var _badgeTimer = null;
var _badgeLastLatest = null;
var BADGE_POLL_MS = 45000;

function _pollBadge() {
  if (document.visibilityState !== 'visible') return;
  fetch('/api/notifications/badge')
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d) return;
      _bellServerUnread = d.unread || 0;
      _updateBellDot();
      // Có notification mới (latest tăng) → nạp lại danh sách nếu panel đang mở
      var panel = document.getElementById('bell-panel');
      if (_badgeLastLatest !== null && d.latest > _badgeLastLatest &&
          panel && panel.classList.contains('open')) {
        loadBellNotifs();
      }
      _badgeLastLatest = d.latest;
    })
    .catch(function () {}); // mạng lỗi → thử lại ở lần poll sau
}

function _startBadgePolling() {
  if (_badgeTimer) return;
  _badgeTimer = setInterval(_pollBadge, BADGE_POLL_MS);
}

// Quay lại tab sau khi máy ngủ/đổi tab lâu: đồng bộ badge ngay.
document.addEventListener('visibilitychange', function () {
  if (document.visibilityState === 'visible') {
    loadBellNotifs();
    _pollBadge();
  }
});

// Tải thông báo lúc vào trang để cập nhật badge trên chuông + bắt đầu poll
function _initBell() { loadBellNotifs(); _startBadgePolling(); }
if (document.readyState !== 'loading') _initBell();
else document.addEventListener('DOMContentLoaded', _initBell);

document.addEventListener('click', function (e) {
  var wrap = document.getElementById('bell-wrap');
  if (wrap && !wrap.contains(e.target)) closeBellPanel();
});
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') closeBellPanel();
});

/* ═══════════════════════════════════════════════════════
   Modal đổi mật khẩu
   ═══════════════════════════════════════════════════════ */
function openChangePasswordModal() {
  const modal = document.getElementById('changePasswordModal');
  modal.classList.add('active');
  document.body.classList.add('cp-modal-open');
  document.body.style.overflow = 'hidden';
  setTimeout(() => document.getElementById('cpCurrent').focus(), 300);
}

function closeChangePasswordModal() {
  const modal = document.getElementById('changePasswordModal');
  modal.classList.remove('active');
  document.body.classList.remove('cp-modal-open');
  document.body.style.overflow = '';
  setTimeout(() => {
    document.getElementById('cpForm').reset();
    resetCpUI();
  }, 300);
}

function resetCpUI() {
  document.getElementById('cpStrength').className = 'cp-strength';
  document.getElementById('cpStrengthLabel').textContent = '';
  document.getElementById('cpCurrentMsg').textContent = '';
  document.getElementById('cpConfirmMsg').textContent = '';
}

(function () {
  var cpModal = document.getElementById('changePasswordModal');
  if (cpModal) {
    cpModal.addEventListener('click', (e) => {
      if (e.target.id === 'changePasswordModal') closeChangePasswordModal();
    });
  }
})();

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    var cpModal = document.getElementById('changePasswordModal');
    var unModal = document.getElementById('unenrollModal');
    if (cpModal && cpModal.classList.contains('active'))
      closeChangePasswordModal();
    if (unModal && unModal.classList.contains('active'))
      closeUnenrollModal();
  }
});

function togglePassword(inputId, btn) {
  const input = document.getElementById(inputId);
  const isPassword = input.type === 'password';
  input.type = isPassword ? 'text' : 'password';

  btn.innerHTML = isPassword
    ? `<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
       <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"></path>
       <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"></path>
       <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"></path>
       <line x1="2" y1="2" x2="22" y2="22"></line>
     </svg>`
    : `<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
       <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"></path>
       <circle cx="12" cy="12" r="3"></circle>
     </svg>`;
}

function checkStrength(pwd) {
  const strength = document.getElementById('cpStrength');
  const label = document.getElementById('cpStrengthLabel');

  if (!pwd) {
    strength.className = 'cp-strength';
    label.textContent = '';
    return;
  }

  let score = 0;
  if (pwd.length >= 8) score++;
  if (/[A-Z]/.test(pwd) && /[a-z]/.test(pwd)) score++;
  if (/\d/.test(pwd)) score++;
  if (/[^A-Za-z0-9]/.test(pwd)) score++;

  const levels = ['', 'Yếu', 'Trung bình', 'Khá mạnh', 'Mạnh'];
  strength.className = 'cp-strength level-' + score;
  label.textContent = levels[score];

  checkMatch();
}

function checkMatch() {
  const newPwd = document.getElementById('cpNew').value;
  const confirm = document.getElementById('cpConfirm').value;
  const msg = document.getElementById('cpConfirmMsg');

  if (!confirm) {
    msg.textContent = '';
    msg.className = 'cp-msg';
    return;
  }

  if (newPwd === confirm) {
    msg.textContent = '✓ Mật khẩu khớp';
    msg.className = 'cp-msg success';
  } else {
    msg.textContent = '✗ Mật khẩu không khớp';
    msg.className = 'cp-msg';
  }
}

(function () {
  var cpSubmitBtn = document.getElementById('cpSubmitBtn');
  if (cpSubmitBtn) {
    cpSubmitBtn.addEventListener('click', function (e) {
      const rect = this.getBoundingClientRect();
      const ripple = document.createElement('span');
      ripple.className = 'cp-ripple';
      ripple.style.width = ripple.style.height = '20px';
      ripple.style.left = (e.clientX - rect.left - 10) + 'px';
      ripple.style.top = (e.clientY - rect.top - 10) + 'px';
      this.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  }
})();

(function () {
  var cpForm = document.getElementById('cpForm');
  if (!cpForm) return;
  cpForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const currentPwd = document.getElementById('cpCurrent').value;
  const newPwd = document.getElementById('cpNew').value;
  const confirmPwd = document.getElementById('cpConfirm').value;
  const submitBtn = document.getElementById('cpSubmitBtn');
  const currentMsg = document.getElementById('cpCurrentMsg');

  if (newPwd.length < 8) {
    alert('Mật khẩu mới phải có ít nhất 8 ký tự');
    return;
  }
  if (newPwd !== confirmPwd) {
    document.getElementById('cpConfirmMsg').textContent = '✗ Mật khẩu không khớp';
    return;
  }
  if (currentPwd === newPwd) {
    currentMsg.textContent = 'Mật khẩu mới phải khác mật khẩu hiện tại';
    return;
  }

  submitBtn.classList.add('loading');
  submitBtn.disabled = true;

  try {
    const response = await fetch('/api/user/password', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        current: currentPwd,
        new: newPwd
      })
    });

    const data = await response.json();

    if (response.ok) {
      alert('✓ Đổi mật khẩu thành công!');
      closeChangePasswordModal();
    } else {
      currentMsg.textContent = data.error || 'Mật khẩu hiện tại không đúng';
    }

  } catch (err) {
    console.error('Change password error:', err);
    currentMsg.textContent = 'Không kết nối được máy chủ. Vui lòng thử lại.';
  } finally {
    submitBtn.classList.remove('loading');
    submitBtn.disabled = false;
  }
  });
})();

/* ═══════════════════════════════════════════════════════
   Kỹ năng — toggle helpers
   ═══════════════════════════════════════════════════════ */
function skSetToggle(hd) {
  var body = hd.nextElementSibling;
  var open = body.style.display === 'block';
  body.style.display = open ? 'none' : 'block';
  var arrow = hd.querySelector('.sk-arrow');
  if (arrow) arrow.style.transform = open ? '' : 'rotate(90deg)';
}
function skSkillToggle(row) {
  var sub = row.nextElementSibling;
  sub.style.display = sub.style.display === 'block' ? 'none' : 'block';
}

/* ═══════════════════════════════════════════════════════
   Kỹ năng — load & render
   ═══════════════════════════════════════════════════════ */
(function () {
  var _skillsLoaded = false;

  function badge(pct) {
    if (pct === 0) return '<span class="sk-badge new">Chưa bắt đầu</span>';
    if (pct >= 70) return '<span class="sk-badge achieved">Đạt ✓</span>';
    return '<span class="sk-badge review">Cần ôn</span>';
  }

  function fillColor(pct) {
    if (pct === 0) return '#E5E7EB';
    if (pct >= 70) return 'linear-gradient(90deg,#10B981,#059669)';
    return 'linear-gradient(90deg,#F59E0B,#D97706)';
  }

  function donutChart(pct) {
    var color = pct >= 70 ? '#10B981' : (pct > 0 ? '#F59E0B' : '#D1D5DB');
    var bg = 'conic-gradient(' + color + ' ' + pct + '%, #E5E7EB ' + pct + '% 100%)';
    return '<div class="sk-donut" style="background:' + bg + '">' +
      '<div class="sk-donut-inner"><span class="sk-donut-pct">' + pct + '%</span></div>' +
      '</div>';
  }

  function renderSkills(data) {
    var sets = data.skill_sets || [];
    var total = 0, achieved = 0, review = 0, unstarted = 0;
    sets.forEach(function (bs) {
      bs.skills.forEach(function (sk) {
        total++;
        if (sk.progress === 0) unstarted++;
        else if (sk.progress >= 70) achieved++;
        else review++;
      });
    });

    var sum = document.getElementById('sk-summary');
    var filt = window._skFilter || 'all';
    function tab(key, val, label, color) {
      var active = filt === key;
      return '<button type="button" class="sk-tab' + (active ? ' active' : '') + '" data-filter="' + key + '" onclick="skSetFilter(\'' + key + '\')" style="' + (active && color ? 'border-color:' + color + '33;color:' + color : '') + '">' +
        '<div class="v"' + (color ? ' style="color:' + color + '"' : '') + '>' + val + '</div><div class="l">' + label + '</div></button>';
    }
    sum.innerHTML =
      tab('all', total, 'Tổng', null) +
      tab('achieved', achieved, 'Đã đạt ✓', '#10B981') +
      tab('review', review, 'Cần ôn', '#F59E0B') +
      tab('none', unstarted, 'Chưa bắt đầu', '#64748B');

    var grid = document.getElementById('sk-grid');
    if (!sets.length) { grid.innerHTML = '<div style="color:#9CA3AF;font-size:14px;padding:24px;">Chưa có dữ liệu kỹ năng.</div>'; return; }

    var defaultOpen = document.getElementById('page-skills').classList.contains('active');

    grid.innerHTML = sets.map(function (bs) {
      var setStatus = bs.progress >= 70 ? 'achieved' : (bs.progress > 0 ? 'review' : 'none');
      if (filt !== 'all' && filt !== setStatus) return '';
      var skillRows = bs.skills.map(function (sk) {
        var subItems = sk.sub_skills.map(function (sub) {
          var cls = sub.done ? 'done' : 'todo';
          return '<div class="sk-sub">' +
            '<span class="sk-sub-dot ' + cls + '"></span>' +
            '<span class="sk-sub-title ' + cls + '">' + sub.title + '</span>' +
            '</div>';
        }).join('');
        return '<div class="sk-skill">' +
          '<div class="sk-skill-row" onclick="skSkillToggle(this)">' +
          '<div class="sk-skill-top">' +
          '<span class="sk-skill-name">' + sk.title + '</span>' +
          '<span class="sk-skill-pct">' + sk.progress + '%</span>' +
          badge(sk.progress) +
          '</div>' +
          '<div class="sk-skill-bar-wrap">' +
          '<div class="sk-skill-bar"><div class="sk-skill-fill" style="width:' + sk.progress + '%;background:' + fillColor(sk.progress) + '"></div></div>' +
          '</div>' +
          '</div>' +
          '<div class="sk-sub-list" style="display:none">' + subItems + '</div>' +
          '</div>';
      }).join('');

      var setAchieved = bs.skills.filter(function (sk) { return sk.progress >= 70; }).length;
      var setTotal = bs.skills.length;
      return '<div class="sk-set">' +
        '<div class="sk-set-hd" onclick="skSetToggle(this)">' +
        '<span class="sk-set-icon">' + bs.icon + '</span>' +
        '<div class="sk-set-info">' +
        '<div class="sk-set-title">' + bs.title + '</div>' +
        '<div class="sk-set-meta">' + setAchieved + '/' + setTotal + ' kỹ năng đạt</div>' +
        '</div>' +
        badge(bs.progress) +
        donutChart(bs.progress) +
        '<span class="sk-arrow"' + (defaultOpen ? ' style="transform:rotate(90deg)"' : '') + '>▶</span>' +
        '</div>' +
        '<div class="sk-body" style="display:' + (defaultOpen ? 'block' : 'none') + '">' + skillRows + '</div>' +
        '</div>';
    }).join('');
  }

  var _skillsData = null;
  function loadSkills() {
    if (_skillsLoaded) return;
    _skillsLoaded = true;
    fetch('/api/skills')
      .then(function (r) { return r.json(); })
      .then(function (data) { _skillsData = data; renderSkills(data); })
      .catch(function () {
        document.getElementById('sk-grid').innerHTML =
          '<div style="color:#EF4444;font-size:14px;padding:24px;">Không tải được dữ liệu kỹ năng.</div>';
      });
  }
  window.skSetFilter = function (key) {
    window._skFilter = key;
    if (_skillsData) renderSkills(_skillsData);
  };

  var _origNavigate = window.navigate;
  window.navigate = function (page) {
    _origNavigate(page);
    if (page === 'skills') loadSkills();
    if (page === 'roadmap' && typeof window.initRoadmapPage === 'function') {
      window.initRoadmapPage();
    }
  };
  window._loadSkillsGlobal = loadSkills;
})();

/* ═══════════════════════════════════════════════════════
   Diễn đàn cộng đồng
   ═══════════════════════════════════════════════════════ */
(function () {

  /* ── Forum API Layer — gọi thẳng Flask API thật (routes/forum.py) ──
     Trước đây là mock localStorage nên like/comment không lưu được. Giờ mọi
     thao tác đi thẳng Postgres. Cookie session tự gửi (same-origin), không cần
     thêm credentials. ─────────────────────────────────────────────────── */
  var forumApi = {
    getPosts: function (opts) {
      opts = opts || {};
      var qs = 'per_page=50';
      if (opts.mine) qs += '&mine=1';
      return fetch('/api/posts?' + qs).then(function (r) { return r.json(); });
    },
    createPost: function (payload) {
      return fetch('/api/posts', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }).then(function (r) { return r.json(); });
    },
    react: function (postId, reactionKey) {
      return fetch('/api/posts/' + postId + '/react', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reaction: reactionKey })
      }).then(function (r) { return r.json(); });
    },
    reactComment: function (commentId, reactionKey) {
      return fetch('/api/comments/' + commentId + '/react', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reaction: reactionKey })
      }).then(function (r) { return r.json(); });
    },
    getComments: function (postId) {
      return fetch('/api/posts/' + postId + '/comments?per_page=50').then(function (r) { return r.json(); });
    },
    addComment: function (postId, text, parentCommentId) {
      return fetch('/api/posts/' + postId + '/comments', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text, parent_comment_id: parentCommentId || null })
      }).then(function (r) { return r.json(); });
    },
    deletePost: function (postId) {
      return fetch('/api/posts/' + postId, { method: 'DELETE' }).then(function (r) { return r.json(); });
    }
  };

  /* Chuyển row API (category/content/author_name/created_at) -> model UI (cat/body/author/time). */
  function _apiTime(s) {
    if (!s) return Date.now();
    // created_at là TIMESTAMP không timezone -> append 'Z' để parse thành UTC,
    // nếu không new Date() coi là giờ local và timeAgo() sẽ lệch theo múi giờ.
    var iso = /[Zz]|[+][0-9]/.test(s) ? s : s.replace(' ', 'T') + 'Z';
    var t = new Date(iso).getTime();
    return isNaN(t) ? Date.now() : t;
  }
  function _emptyReactions() { return { like: 0, love: 0, haha: 0, wow: 0, sad: 0, angry: 0 }; }
  function _apiPostToUi(row) {
    return {
      id: row.id, cat: row.category, title: row.title || '', body: row.content || '',
      userId: row.user_id || null,
      author: row.author_name || 'Ẩn danh', avatar: '🙋', time: _apiTime(row.created_at),
      reactions: row.reactions || _emptyReactions(), myReaction: row.my_reaction || null,
      comments: row.comment_count || 0, commentList: null, media: [],
      // Thẻ bài học + cờ bài mồi (2026-08-14)
      courseId: row.course_id || null, lessonNo: row.lesson_no || null,
      isSample: Boolean(row.is_sample)
    };
  }

  //: id khoá → tên hợp phần, để nhãn "bài 12 · Định lượng" đọc được ngay
  var COURSE_SHORT = {
    hsa_quantitative: 'Định lượng',
    hsa_verbal: 'Định tính',
    hsa_science: 'Khoa học'
  };

  /* Nhãn bài học của một bài viết — bấm vào là mở thẳng bài đó. */
  function _lessonTagHtml(p) {
    if (!p.courseId || !p.lessonNo) return '';
    var name = COURSE_SHORT[p.courseId] || p.courseId;
    return '<a class="fpc-lesson-tag" href="/lesson/' + p.courseId + '?lesson=' + p.lessonNo + '"' +
      ' onclick="event.stopPropagation()" title="Mở bài học này">' +
      'Bài ' + p.lessonNo + ' · ' + name + '</a>';
  }

  /* Bài mồi PHẢI có nhãn: người xem không được nhầm là bài của học viên thật. */
  function _sampleTagHtml(p) {
    return p.isSample ? '<span class="fpc-sample-tag">Bài mẫu</span>' : '';
  }
  function _apiCommentToUi(row) {
    return {
      id: row.id, author: row.author_name || 'Ẩn danh', avatar: '🧑',
      time: _apiTime(row.created_at), text: row.content || '',
      reactions: row.reactions || _emptyReactions(), myReaction: row.my_reaction || null,
      parent_comment_id: row.parent_comment_id || null, replies: []
    };
  }
  /* Dựng cây 1 cấp từ mảng comment phẳng của API. */
  function _buildCommentTree(flat) {
    var byId = {}, roots = [];
    flat.forEach(function (row) { byId[row.id] = _apiCommentToUi(row); });
    flat.forEach(function (row) {
      var node = byId[row.id];
      if (row.parent_comment_id && byId[row.parent_comment_id]) {
        node.replyTo = byId[row.parent_comment_id].author;
        byId[row.parent_comment_id].replies.push(node);
      } else {
        roots.push(node);
      }
    });
    return roots;
  }
  function _isAdminUser() {
    return !!(window.__currentUser && window.__currentUser.role === 'admin');
  }
  /* Cache comment tree theo postId (lazy-load khi mở khung bình luận). */
  var _commentsCache = {};
  /* Mảng post vừa render — để reaction handler patch tại chỗ, không cần GET lại. */
  var _lastRenderedPosts = [];

  /* ═══════════════════════════════════════════════════════
     Predictive Comment Prefetch System
     — IntersectionObserver + hover + request queue —
     ═══════════════════════════════════════════════════════ */
  var _prefetchInFlight = {};   // postId -> Promise (đang fetch)
  var _prefetchQueue = [];      // [{postId, priority}] — chờ xử lý
  var _prefetchActive = 0;      // số request đang chạy
  var _PREFETCH_CONCURRENCY = 2; // tối đa 2 request song song
  var _commentObserver = null;  // IntersectionObserver instance

  // Prefetch chỉ fetch + cache, KHÔNG render. Trả Promise.
  function _prefetchComments(postId) {
    // Bỏ qua mock posts
    if (_isMockPost(postId)) return Promise.resolve();
    // Đã có cache → skip
    if (_commentsCache[postId]) return Promise.resolve();
    // Đang fetch → trả promise hiện tại
    if (_prefetchInFlight[postId]) return _prefetchInFlight[postId];

    var p = forumApi.getComments(postId).then(function (res) {
      var tree = _buildCommentTree((res && res.comments) || []);
      _commentsCache[postId] = tree;
      // Cập nhật badge nếu post đang hiển thị
      var post = _lastRenderedPosts.find(function (pp) { return String(pp.id) === String(postId); });
      if (post) {
        post.comments = tree.length;
        _setCommentBadge(postId, tree.length);
      }
      delete _prefetchInFlight[postId];
      _prefetchActive--;
      _drainPrefetchQueue();
    }).catch(function () {
      delete _prefetchInFlight[postId];
      _prefetchActive--;
      _drainPrefetchQueue();
    });
    _prefetchInFlight[postId] = p;
    _prefetchActive++;
    return p;
  }

  // Thêm postId vào hàng đợi prefetch (priority: 1=high, 2=medium, 3=low)
  function _enqueuePrefetch(postId, priority) {
    if (_isMockPost(postId)) return;
    if (_commentsCache[postId]) return;
    if (_prefetchInFlight[postId]) return;
    // Tránh duplicate trong queue
    for (var i = 0; i < _prefetchQueue.length; i++) {
      if (_prefetchQueue[i].postId === postId) {
        // Nâng priority nếu request mới ưu tiên hơn
        if (priority < _prefetchQueue[i].priority) _prefetchQueue[i].priority = priority;
        return;
      }
    }
    _prefetchQueue.push({ postId: postId, priority: priority || 3 });
    _drainPrefetchQueue();
  }

  // Xử lý queue: chạy tối đa _PREFETCH_CONCURRENCY request cùng lúc
  function _drainPrefetchQueue() {
    while (_prefetchActive < _PREFETCH_CONCURRENCY && _prefetchQueue.length > 0) {
      // Sort theo priority (thấp = ưu tiên hơn)
      _prefetchQueue.sort(function (a, b) { return a.priority - b.priority; });
      var next = _prefetchQueue.shift();
      // Double-check cache (có thể đã được fetch bởi request khác)
      if (_commentsCache[next.postId] || _prefetchInFlight[next.postId]) continue;
      _prefetchComments(next.postId);
    }
  }

  // IntersectionObserver: khi post card sắp vào viewport → enqueue prefetch
  function _setupCommentObserver() {
    // Hủy observer cũ nếu có
    if (_commentObserver) { _commentObserver.disconnect(); _commentObserver = null; }
    // Không hỗ trợ IntersectionObserver → fallback prefetch 3 post đầu
    if (typeof IntersectionObserver === 'undefined') {
      _lastRenderedPosts.slice(0, 3).forEach(function (p) {
        if (!_isMockPost(p.id)) _enqueuePrefetch(String(p.id), 3);
      });
      return;
    }

    _commentObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var card = entry.target;
        var postId = card.id.replace('fpc-', '');
        if (!postId) return;
        // Prefetch post này (medium priority)
        _enqueuePrefetch(postId, 2);
        // Dự đoán: prefetch post KẾ TIẾP trong danh sách (low priority)
        var nextCard = card.nextElementSibling;
        if (nextCard && nextCard.id && nextCard.id.startsWith('fpc-')) {
          var nextId = nextCard.id.replace('fpc-', '');
          _enqueuePrefetch(nextId, 3);
        }
        // Đã prefetch → ngừng theo dõi post này
        _commentObserver.unobserve(card);
      });
    }, {
      root: null,
      rootMargin: '300px 0px',  // Bắt đầu prefetch khi post còn cách 300px
      threshold: 0
    });

    // Observe tất cả post cards trong danh sách
    var list = document.getElementById('forum-list');
    if (!list) return;
    var cards = list.querySelectorAll('.forum-post-card[id^="fpc-"]');
    cards.forEach(function (card) {
      var postId = card.id.replace('fpc-', '');
      // Chỉ observe post thật chưa có cache
      if (!_isMockPost(postId) && !_commentsCache[postId]) {
        _commentObserver.observe(card);
      }
    });
  }

  // Hover prefetch: khi user di chuột vào nút comment → fetch ngay (high priority)
  function _setupHoverPrefetch() {
    var list = document.getElementById('forum-list');
    if (!list) return;
    // Dùng event delegation để tránh gắn listener lên từng nút
    list.addEventListener('mouseenter', function (e) {
      var btn = e.target.closest('.fpc-comment-btn');
      if (!btn) return;
      var postId = btn.id.replace('fpc-cmtbtn-', '');
      if (!postId || _isMockPost(postId)) return;
      if (_commentsCache[postId]) return;
      // High priority — user đang hướng tới bấm
      _enqueuePrefetch(postId, 1);
    }, true);
  }
  var _hoverPrefetchSetup = false;

  var CAT_LABELS = { question: '❓ Câu hỏi', share: '💡 Chia sẻ', discuss: '💬 Thảo luận' };
  var CAT_COLORS = { question: '#F87171', share: '#FCD34D', discuss: '#A78BFA' };
  var CAT_BG = { question: 'rgba(248,113,113,0.1)', share: 'rgba(252,211,77,0.1)', discuss: 'rgba(167,139,250,0.1)' };

  var REACT_EMOJIS = { like: '👍', love: '❤️', haha: '😂', wow: '😮', sad: '😢', angry: '😡' };
  var REACT_LABELS = { like: 'Thích', love: 'Yêu thích', haha: 'Haha', wow: 'Wow', sad: 'Buồn', angry: 'Phẫn nộ' };

  var _forumMediaFiles = [];

  var _currentCat = 'all';
  var _currentSort = 'newest';
  var _selectedCat = 'question';
  var _cmtSortMap = {};

  var MOCK_POSTS = [
    {
      id: 'm1', cat: 'question',
      title: 'Làm thế nào để hiểu rõ về con trỏ trong C/C++?',
      body: 'Mình đang học C++ nhưng phần con trỏ khá khó hiểu, đặc biệt là con trỏ đôi (double pointer). Mọi người có thể giải thích hoặc gợi ý tài liệu dễ hiểu không?',
      author: 'Trần Minh Tuấn', avatar: '🧑‍💻',
      time: Date.now() - 2 * 3600 * 1000,
      reactions: { like: 10, love: 2, haha: 0, wow: 2, sad: 0, angry: 0 }, myReaction: null,
      comments: 3,
      commentList: [
        { id: 'c1a', author: 'Nguyễn Văn An', avatar: '👨‍💻', time: Date.now() - 100 * 60 * 1000, text: 'Con trỏ đôi về bản chất là một con trỏ trỏ tới một con trỏ khác. Bạn thử hình dung bộ nhớ như một dãy ô, mỗi ô có địa chỉ riêng — con trỏ chỉ là biến lưu địa chỉ đó thôi!', reactions: { like: 4, love: 1, haha: 0, wow: 0, sad: 0, angry: 0 }, myReaction: null, replies: [{ id: 'r1a', author: 'Trần Minh Tuấn', avatar: '🧑‍💻', time: Date.now() - 85 * 60 * 1000, text: 'Cảm ơn bạn! Cách so sánh với dãy ô bộ nhớ dễ hình dung lắm, mình hiểu ngay rồi!', replyTo: 'Nguyễn Văn An' }] },
        { id: 'c1b', author: 'Lê Thị Hoa', avatar: '👩‍🏫', time: Date.now() - 60 * 60 * 1000, text: 'Mình học từ sách "C Programming Language" của Kernighan & Ritchie, phần con trỏ giải thích rất trực quan. Bạn nên thử debug từng bước để thấy giá trị thay đổi.', reactions: { like: 2, love: 0, haha: 0, wow: 1, sad: 0, angry: 0 }, myReaction: null, replies: [] },
        { id: 'c1c', author: 'Phạm Đức Huy', avatar: '🧑‍🎓', time: Date.now() - 20 * 60 * 1000, text: 'Series C++ của The Cherno trên YouTube giải thích con trỏ bằng hình ảnh rất dễ hiểu. Mình đã học từ đó và hiểu ngay sau 2 video!', reactions: { like: 6, love: 2, haha: 0, wow: 0, sad: 0, angry: 0 }, myReaction: null, replies: [] },
      ],
    },
    {
      id: 'm2', cat: 'share',
      title: 'Tổng hợp 10 extension VSCode hữu ích nhất cho lập trình viên Python',
      body: 'Sau một thời gian dùng VSCode để code Python, mình tổng hợp lại các extension mình thấy thực sự hữu ích. Hi vọng giúp ích cho mọi người: Pylance, Black Formatter, Python Debugger...',
      author: 'Nguyễn Hà Linh', avatar: '👩‍💻',
      time: Date.now() - 5 * 3600 * 1000,
      reactions: { like: 25, love: 7, haha: 0, wow: 0, sad: 0, angry: 0 }, myReaction: null,
      comments: 2,
      commentList: [
        { id: 'c2a', author: 'Trần Bình', avatar: '🧑‍💻', time: Date.now() - 3 * 3600 * 1000, text: 'Mình thêm GitLens vào danh sách nhé, siêu hữu ích khi làm việc nhóm, xem ai commit gì ngay trong editor.' },
        { id: 'c2b', author: 'Mai Anh', avatar: '👩‍🎓', time: Date.now() - 1 * 3600 * 1000, text: 'Docker extension cũng rất tiện nếu bạn hay dùng container. Quản lý image và container ngay trong VSCode luôn.' },
      ],
    },
    {
      id: 'm3', cat: 'discuss',
      title: 'Nên học Java hay Python trước khi học Machine Learning?',
      body: 'Mình đang phân vân giữa Java và Python để bắt đầu. Mình nghe nói Python phổ biến hơn trong ML, nhưng Java lại mạnh hơn về OOP. Mọi người nghĩ sao?',
      author: 'Lê Văn Đức', avatar: '🧑‍🎓',
      time: Date.now() - 24 * 3600 * 1000,
      reactions: { like: 14, love: 3, haha: 1, wow: 3, sad: 0, angry: 0 }, myReaction: null,
      comments: 3,
      commentList: [
        { id: 'c3a', author: 'Hoàng Nam', avatar: '👨‍💻', time: Date.now() - 20 * 3600 * 1000, text: 'Python chắc chắn rồi! Hầu hết thư viện ML như TensorFlow, PyTorch, scikit-learn đều Python-first. Java không có hệ sinh thái ML mạnh như vậy.' },
        { id: 'c3b', author: 'Thu Hương', avatar: '👩‍💻', time: Date.now() - 15 * 3600 * 1000, text: 'Mình cũng từng phân vân như bạn, cuối cùng chọn Python và không hối hận. NumPy + Pandas là bộ đôi không thể thiếu, học Python để dùng được 2 thư viện này.' },
        { id: 'c3c', author: 'Việt Anh', avatar: '🧑', time: Date.now() - 5 * 3600 * 1000, text: 'Java mạnh về enterprise và Android, nhưng cho ML thì Python win tuyệt đối. Bắt đầu Python đi bạn, 2-3 tháng là dùng được thư viện cơ bản rồi.' },
      ],
    },
    {
      id: 'm4', cat: 'share',
      title: 'Mình đã hoàn thành khóa học HTML/CSS sau 3 tuần — Chia sẻ kinh nghiệm',
      body: 'Sau 3 tuần học chăm chỉ, mình đã hoàn thành khóa HTML/CSS. Bí quyết của mình là học mỗi ngày ít nhất 1 tiếng và làm project nhỏ ngay sau khi học xong mỗi phần.',
      author: 'Phạm Thị Mai', avatar: '👩‍🎓',
      time: Date.now() - 2 * 24 * 3600 * 1000,
      reactions: { like: 30, love: 12, haha: 0, wow: 5, sad: 0, angry: 0 }, myReaction: null,
      comments: 2,
      commentList: [
        { id: 'c4a', author: 'Minh Khoa', avatar: '🧑‍💻', time: Date.now() - 40 * 3600 * 1000, text: 'Chúc mừng bạn! 3 tuần là rất nhanh đó. Bước tiếp theo bạn định học JavaScript hay framework nào không?' },
        { id: 'c4b', author: 'Ngọc Linh', avatar: '👩‍🎓', time: Date.now() - 30 * 3600 * 1000, text: 'Làm project nhỏ sau mỗi bài là cách hay nhất để nhớ kiến thức lâu dài. Mình cũng áp dụng phương pháp này và tiến bộ rất nhanh!' },
      ],
    },
    {
      id: 'm5', cat: 'question',
      title: 'Git merge vs Git rebase — khi nào nên dùng cái nào?',
      body: 'Mình hay bị nhầm lẫn giữa merge và rebase. Anh/chị nào có thể giải thích sự khác biệt và khi nào thì nên dùng từng loại không ạ?',
      author: 'Hoàng Quốc Bảo', avatar: '🧑',
      time: Date.now() - 3 * 24 * 3600 * 1000,
      reactions: { like: 7, love: 1, haha: 0, wow: 1, sad: 0, angry: 0 }, myReaction: null,
      comments: 2,
      commentList: [
        { id: 'c5a', author: 'Đức Thịnh', avatar: '👨‍💻', time: Date.now() - 60 * 3600 * 1000, text: 'Merge giữ lại lịch sử đầy đủ, thích hợp cho feature branch lớn. Rebase tạo lịch sử linear sạch hơn, hay dùng trước khi merge vào main để commit gọn gàng.' },
        { id: 'c5b', author: 'Khánh An', avatar: '👩‍💻', time: Date.now() - 48 * 3600 * 1000, text: 'Rule of thumb: không rebase nhánh public đã push lên remote vì sẽ thay đổi lịch sử ảnh hưởng người khác. Chỉ rebase nhánh local của mình thôi nhé!' },
      ],
    },
  ];

  // Lấy post thật từ API, đã map sang model UI. Trả Promise<Array>.
  function loadPosts() {
    return forumApi.getPosts().then(function (res) {
      return (res.posts || []).map(_apiPostToUi);
    });
  }

  /* ── Follow user (nút Theo dõi cạnh tên tác giả trong forum) ─────────── */
  var _followingIds = {};      // userId -> true (những người mình đang follow)
  var _followingLoaded = false;

  function _loadFollowing() {
    var me = window.__currentUser;
    if (!me || !me.id) return Promise.resolve();
    return fetch('/api/users/' + me.id + '/following')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        _followingIds = {};
        ((d && d.following) || []).forEach(function (u) { _followingIds[u.id] = true; });
        _followingLoaded = true;
      })
      .catch(function () { /* offline/lỗi: nút vẫn hoạt động, chỉ thiếu trạng thái đầu */ });
  }

  window.toggleFollow = function (userId, btn) {
    var isFollowing = !!_followingIds[userId];
    btn.disabled = true;
    fetch('/api/users/' + userId + '/follow', { method: isFollowing ? 'DELETE' : 'POST' })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.ok) {
          if (d.following) _followingIds[userId] = true;
          else delete _followingIds[userId];
          // Cập nhật MỌI nút follow của user này đang hiển thị
          document.querySelectorAll('.fpc-follow-btn[data-user-id="' + userId + '"]').forEach(function (b) {
            b.classList.toggle('following', !!d.following);
            b.textContent = d.following ? 'Đang theo dõi' : '+ Theo dõi';
          });
        }
      })
      .catch(function () {})
      .then(function () { btn.disabled = false; });
  };

  function _followBtnHtml(p) {
    var me = window.__currentUser || {};
    if (!p.userId || !me.id || p.userId === me.id) return '';
    var isF = !!_followingIds[p.userId];
    return '<button class="fpc-follow-btn' + (isF ? ' following' : '') + '"'
      + ' data-user-id="' + p.userId + '"'
      + ' style="margin-left:8px;font-size:11px;padding:2px 8px;border-radius:12px;border:1px solid var(--border,#d1d5db);background:transparent;cursor:pointer;color:inherit"'
      + ' onclick="event.stopPropagation();toggleFollow(' + p.userId + ', this)">'
      + (isF ? 'Đang theo dõi' : '+ Theo dõi') + '</button>';
  }

  // Async: post thật từ DB; admin thấy kèm 5 bài demo (MOCK_POSTS) ở đầu để
  // biết mà quản lý — user thường chỉ thấy bài thật.
  function getAllPostsAsync() {
    return loadPosts().then(function (realPosts) {
      return _isAdminUser() ? MOCK_POSTS.concat(realPosts) : realPosts;
    });
  }

  function filteredSorted(posts) {
    if (_currentCat !== 'all') posts = posts.filter(function (p) { return p.cat === _currentCat; });
    var q = (typeof _forumTextQ !== 'undefined' && _forumTextQ) ? _forumTextQ : '';
    if (q) posts = posts.filter(function (p) {
      return p.title.toLowerCase().includes(q) || p.body.toLowerCase().includes(q);
    });
    if (_currentSort === 'likes') posts.sort(function (a, b) { return (b.reactions?.like || 0) - (a.reactions?.like || 0); });
    else if (_currentSort === 'oldest') posts.sort(function (a, b) { return a.time - b.time; });
    else posts.sort(function (a, b) { return b.time - a.time; });
    return posts;
  }

  function timeAgo(ts) {
    var diff = Math.floor((Date.now() - ts) / 1000);
    if (diff < 60) return 'vừa xong';
    if (diff < 3600) return Math.floor(diff / 60) + ' phút trước';
    if (diff < 86400) return Math.floor(diff / 3600) + ' giờ trước';
    return Math.floor(diff / 86400) + ' ngày trước';
  }

  // Reload posts from API and re-render. Trả Promise để caller chờ được.
  function reloadPosts() {
    return getAllPostsAsync().then(function (allP) {
      var posts = filteredSorted(allP);
      _renderPosts(posts);
    });
  }

  function renderPosts() {
    // Show loading state
    var list = document.getElementById('forum-list');
    var empty = document.getElementById('forum-empty');
    if (list) list.innerHTML = '<div class="forum-loading">Đang tải...</div>';

    // Load from API (uses forumApi which can be swapped to real API)
    // Nạp danh sách following trước 1 lần để nút "Theo dõi" hiện đúng trạng thái
    var followReady = _followingLoaded ? Promise.resolve() : _loadFollowing();
    Promise.all([getAllPostsAsync(), followReady]).then(function (res) {
      var posts = filteredSorted(res[0]);
      _renderPosts(posts);
    });
  }

  function _renderPosts(posts) {
    _lastRenderedPosts = posts;
    var list = document.getElementById('forum-list');
    var empty = document.getElementById('forum-empty');
    if (!list) return;

    if (!posts.length) {
      list.innerHTML = '';
      empty && empty.classList.remove('hidden');
      return;
    }
    empty && empty.classList.add('hidden');

    list.innerHTML = posts.map(function (p, idx) {
      var catColor = CAT_COLORS[p.cat] || '#6B7280';
      var catBg = CAT_BG[p.cat] || '#F3F4F6';
      var catLabel = CAT_LABELS[p.cat] || p.cat;
      var excerpt = p.body.length > 160 ? p.body.slice(0, 157) + '...' : p.body;

      var reactions = p.reactions || { like: p.likes || 0 };
      var myReaction = p.myReaction || null;
      var totalR = Object.values(reactions).reduce(function (a, b) { return a + b; }, 0);
      var liked = !!myReaction;
      var reactClass = myReaction ? ('reacted-' + myReaction) : '';

      var pickerItems = Object.keys(REACT_EMOJIS).map(function (k) {
        return '<span class="reaction-item" onclick="forumSetReaction(\'' + p.id + '\',\'' + k + '\')" title="' + REACT_LABELS[k] + '">' + REACT_EMOJIS[k] + '</span>';
      }).join('');

      var mediaPart = '';
      if (p.media && p.media.length) {
        mediaPart = '<div class="fpc-media-row">' + p.media.map(function (m) {
          if (m.type === 'video') {
            return '<video src="' + m.url + '" class="fpc-media-item" controls muted></video>';
          }
          return '<img src="' + m.url + '" class="fpc-media-item" alt="ảnh" />';
        }).join('') + '</div>';
      }

      return (
        '<div class="forum-post-card fx-fade-up" id="fpc-' + p.id + '" style="animation-delay:' + Math.min(idx * 0.04, 0.3) + 's">' +
        '<div class="fpc-top">' +
        '<div class="fpc-avatar" style="background:' + avatarColor(p.author) + '">' + (p.author || '?').charAt(0).toUpperCase() + '</div>' +
        '<div class="fpc-meta">' +
        '<span class="fpc-author">' + escHtml(p.author) + _followBtnHtml(p) + '</span>' +
        '<span class="fpc-time">' + timeAgo(p.time) + '</span>' +
        '</div>' +
        '<span class="fpc-cat-tag" style="background:' + catBg + ';color:' + catColor + '">' + catLabel + '</span>' +
        '</div>' +
        '<div class="fpc-tags">' + _sampleTagHtml(p) + _lessonTagHtml(p) + '</div>' +
        '<div class="fpc-title">' + escHtml(p.title) + '</div>' +
        '<div class="fpc-excerpt">' + escHtml(excerpt) + '</div>' +
        mediaPart +
        '<div class="fpc-actions">' +
        '<div class="fpc-react-wrap">' +
        '<button class="fpc-react-btn' + (liked ? ' liked' : '') + ' ' + reactClass + '" onclick="forumSetReaction(\'' + p.id + '\',\'' + (myReaction || 'like') + '\')">' +
        '<span data-icon="thumbs-up" data-size="13"' + (liked ? ' data-color="#60A5FA"' : '') + '></span> Thích' +
        (totalR > 0 ? ' <span class="fpc-react-count">' + totalR + '</span>' : '') +
        '</button>' +
        '<div class="reaction-picker">' + pickerItems + '</div>' +
        '</div>' +
        '<button class="fpc-comment-btn" id="fpc-cmtbtn-' + p.id + '" onclick="forumToggleComments(\'' + p.id + '\')">' +
        '<span data-icon="message-circle" data-size="13"></span> ' + p.comments + ' bình luận' +
        '</button>' +
        '<button class="fpc-share-btn" onclick="event.stopPropagation()"><span data-icon="share2" data-size="13"></span> Chia sẻ</button>' +
        '</div>' +
        '<div class="fpc-comments" id="fpc-cmt-' + p.id + '">' +
        '<div class="fpc-cmt-sort-bar">' +
        '<span class="fpc-cmt-sort-label">Bình luận</span>' +
        '<div class="fpc-cmt-sort-btns">' +
        '<button class="fpc-cmt-sort-btn active" id="fpc-csort-newest-' + p.id + '" onclick="forumSetCmtSort(\'' + p.id + '\',\'newest\')">↓ Mới nhất</button>' +
        '<button class="fpc-cmt-sort-btn" id="fpc-csort-oldest-' + p.id + '" onclick="forumSetCmtSort(\'' + p.id + '\',\'oldest\')">↑ Cũ nhất</button>' +
        '</div>' +
        '</div>' +
        '<div class="fpc-cmt-list" id="fpc-cmt-list-' + p.id + '"></div>' +
        '<div class="fpc-cmt-input-row">' +
        '<div class="fpc-cmt-avatar-col">' +
        '<div class="fpc-cmt-avatar fpc-cmt-me">🧑</div>' +
        '</div>' +
        '<div class="fpc-cmt-compose">' +
        '<input class="fpc-cmt-input" id="fpc-cmt-inp-' + p.id + '" placeholder="Viết bình luận..." ' +
        'onkeydown="if(event.key===\'Enter\'&&!event.shiftKey){event.preventDefault();forumAddComment(\'' + p.id + '\');}" />' +
        '<button class="fpc-cmt-send" onclick="forumAddComment(\'' + p.id + '\')" title="Gửi (Enter)">↑</button>' +
        '</div>' +
        '</div>' +
        '</div>' +
        '</div>'
      );
    }).join('');
    if (window.mountIcons) mountIcons(list);

    // Kích hoạt prefetch system sau mỗi lần render posts
    // Dùng requestIdleCallback nếu có, để không chặn paint
    var _schedPrefetch = window.requestIdleCallback || function (cb) { setTimeout(cb, 100); };
    _schedPrefetch(function () {
      _setupCommentObserver();
      if (!_hoverPrefetchSetup) {
        _setupHoverPrefetch();
        _hoverPrefetchSetup = true;
      }
    });

    // Nếu vừa được điều hướng từ "Trang của tôi" tới 1 bài cụ thể → cuộn tới + highlight
    if (_pendingScrollPostId) {
      var targetCard = document.getElementById('fpc-' + _pendingScrollPostId);
      _pendingScrollPostId = null;
      if (targetCard) {
        requestAnimationFrame(function () {
          targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
          targetCard.style.transition = 'box-shadow .4s';
          targetCard.style.boxShadow = '0 0 0 3px rgba(59,130,246,.55)';
          setTimeout(function () { targetCard.style.boxShadow = ''; }, 2000);
        });
      }
    }
  }

  /* Mở diễn đàn và cuộn tới đúng bài — gọi từ "Bài đăng của tôi" trên Trang của tôi.
     Reset bộ lọc/tìm kiếm để bài chắc chắn nằm trong danh sách render. */
  var _pendingScrollPostId = null;
  window.forumOpenPost = function (postId) {
    _pendingScrollPostId = String(postId);
    _currentCat = 'all';
    _currentSort = 'newest';
    _forumTextQ = '';
    var si = document.getElementById('forum-search-input');
    if (si) si.value = '';
    document.querySelectorAll('#forum-tabs .filter-btn').forEach(function (b) {
      b.classList.toggle('active', b.dataset.cat === 'all');
    });
    window.navigate('forum');
  };

  function escHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  var _AVATAR_COLORS = ['#3B82F6', '#8B5CF6', '#F97316', '#10B981', '#EC4899', '#06B6D4', '#F59E0B', '#EF4444'];
  function avatarColor(name) {
    var s = String(name || '?');
    var h = 0;
    for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
    return _AVATAR_COLORS[h % _AVATAR_COLORS.length];
  }

  window.forumSetCat = function (btn, cat) {
    document.querySelectorAll('#forum-tabs .filter-btn').forEach(function (b) { b.classList.remove('active'); });
    btn.classList.add('active');
    _currentCat = cat;
    renderPosts();
  };

  window.forumSetSort = function (val) {
    _currentSort = val;
    renderPosts();
  };

  window.forumToggleLike = function (postId) {
    forumSetReaction(postId, 'like');
  };

  /* ── Patch DOM tại chỗ cho reaction post — không re-render toàn bộ ── */
  function _patchPostReactionDOM(postId, reactions, myReaction) {
    var card = document.getElementById('fpc-' + postId);
    if (!card) return;
    var wrap = card.querySelector('.fpc-react-wrap');
    if (!wrap) return;
    var btn = wrap.querySelector('.fpc-react-btn');
    if (!btn) return;

    var totalR = Object.values(reactions).reduce(function (a, b) { return a + b; }, 0);
    var liked = !!myReaction;

    // Update button classes
    btn.className = 'fpc-react-btn' + (liked ? ' liked' : '') + (myReaction ? ' reacted-' + myReaction : '');

    // Update onclick to toggle current reaction
    btn.setAttribute('onclick', "forumSetReaction('" + postId + "','" + (myReaction || 'like') + "')");

    // Update icon color
    var icon = btn.querySelector('[data-icon]');
    if (icon) {
      if (liked) { icon.setAttribute('data-color', '#60A5FA'); } else { icon.removeAttribute('data-color'); }
      if (window.mountIcons) mountIcons(btn);
    }

    // Update count
    var countEl = btn.querySelector('.fpc-react-count');
    if (totalR > 0) {
      if (countEl) {
        countEl.textContent = totalR;
      } else {
        var span = document.createElement('span');
        span.className = 'fpc-react-count';
        span.textContent = totalR;
        btn.appendChild(span);
      }
    } else if (countEl) {
      countEl.remove();
    }

    // Quick pop animation on the button
    btn.style.transform = 'scale(1.15)';
    setTimeout(function () { btn.style.transform = ''; }, 180);
  }

  window.forumSetReaction = function (postId, key) {
    function applyReaction(post) {
      if (!post.reactions) {
        post.reactions = { like: post.likes || 0, love: 0, haha: 0, wow: 0, sad: 0, angry: 0 };
        post.likes = 0;
      }
      var prev = post.myReaction || null;
      if (prev === key) {
        post.myReaction = null;
        if (post.reactions[key] > 0) post.reactions[key]--;
      } else {
        if (prev && post.reactions[prev] > 0) post.reactions[prev]--;
        post.myReaction = key;
        post.reactions[key] = (post.reactions[key] || 0) + 1;
      }
    }
    var mockIdx = MOCK_POSTS.findIndex(function (p) { return p.id === postId; });
    if (mockIdx !== -1) {
      // MOCK_POSTS (chỉ admin thấy) — thao tác cục bộ, patch DOM tại chỗ
      applyReaction(MOCK_POSTS[mockIdx]);
      _patchPostReactionDOM(postId, MOCK_POSTS[mockIdx].reactions, MOCK_POSTS[mockIdx].myReaction);
    } else {
      // Bài thật — optimistic update: patch DOM ngay, API chạy nền
      var post = _lastRenderedPosts.find(function (p) { return String(p.id) === String(postId); });
      if (post) {
        // Optimistic: update data ngay
        applyReaction(post);
        _patchPostReactionDOM(postId, post.reactions, post.myReaction);
      }
      // Gọi API nền — nếu server trả khác thì patch lại
      forumApi.react(postId, key).then(function (res) {
        if (!res || res.error) return;
        if (post) {
          post.reactions = res.reactions;
          post.myReaction = res.my_reaction;
          _patchPostReactionDOM(postId, res.reactions, res.my_reaction);
        }
      });
    }
  };

  /* ── Create box inline (giống Forum.tsx: 1 textarea, không modal) ── */
  window.forumInlinePickType = function (btn) {
    document.querySelectorAll('.fcb-type-btn').forEach(function (b) { b.classList.remove('active'); });
    btn.classList.add('active');
    _selectedCat = btn.dataset.val;
  };

  window.forumInlineInput = function (val) {
    var btn = document.getElementById('fcb-submit-btn');
    if (btn) btn.disabled = !val.trim();
  };

  window.forumSubmitInline = function () {
    var ta = document.getElementById('forum-inline-body');
    var body = (ta.value || '').trim();
    if (!body) return;
    var firstLine = body.split('\n')[0];
    var title = firstLine.length > 80 ? firstLine.slice(0, 77) + '…' : firstLine;

    forumApi.createPost({ category: _selectedCat, title: title, content: body }).then(function (res) {
      if (res && res.error) { alert(window.__PE_errMsg ? window.__PE_errMsg(res.error) : res.error); return; }
      ta.value = '';
      document.getElementById('fcb-submit-btn').disabled = true;
      _selectedCat = 'question';
      document.querySelectorAll('.fcb-type-btn').forEach(function (b) {
        b.classList.toggle('active', b.dataset.val === 'question');
      });
      _currentCat = 'all';
      _currentSort = 'newest';
      document.querySelectorAll('#forum-tabs .filter-btn').forEach(function (b) {
        b.classList.toggle('active', b.dataset.cat === 'all');
      });
      reloadPosts();
    });
  };

  function _isMockPost(postId) {
    return MOCK_POSTS.findIndex(function (p) { return p.id === postId; }) !== -1;
  }

  // Cập nhật số bình luận trên nút, giữ icon (không dùng getAllPostsAsync -> đỡ 1 request).
  function _setCommentBadge(postId, count) {
    var btn = document.getElementById('fpc-cmtbtn-' + postId);
    if (!btn) return;
    btn.innerHTML = '<span data-icon="message-circle" data-size="13"></span> ' + count + ' bình luận';
    if (window.mountIcons) mountIcons(btn);
  }

  // Tải lại comment 1 post từ API -> cache -> render + cập nhật badge.
  function _refreshComments(postId) {
    return forumApi.getComments(postId).then(function (res) {
      var tree = _buildCommentTree((res && res.comments) || []);
      _commentsCache[postId] = tree;
      forumRenderComments(postId);
      var post = _lastRenderedPosts.find(function (p) { return String(p.id) === String(postId); });
      if (post) post.comments = tree.length;
      _setCommentBadge(postId, tree.length);
    });
  }

  // Tìm 1 comment hoặc reply theo id trong cây (id API là int, onclick truyền string).
  function _findCommentNode(tree, id) {
    for (var i = 0; i < tree.length; i++) {
      if (String(tree[i].id) === String(id)) return tree[i];
      var reps = tree[i].replies || [];
      for (var j = 0; j < reps.length; j++) {
        if (String(reps[j].id) === String(id)) return reps[j];
      }
    }
    return null;
  }

  window.forumToggleComments = function (postId) {
    var section = document.getElementById('fpc-cmt-' + postId);
    var btn = document.getElementById('fpc-cmtbtn-' + postId);
    if (!section) return;
    var isOpen = section.classList.toggle('open');
    if (btn) btn.classList.toggle('active', isOpen);
    if (isOpen) {
      if (_isMockPost(postId)) {
        // Mock posts: render ngay từ MOCK_POSTS
        forumRenderComments(postId);
      } else if (_commentsCache[postId]) {
        // Đã prefetch xong → render ngay, không chờ API
        forumRenderComments(postId);
      } else if (_prefetchInFlight[postId]) {
        // Prefetch đang chạy → chờ nó xong rồi render (không tạo request mới)
        _prefetchInFlight[postId].then(function () {
          forumRenderComments(postId);
        });
      } else {
        // Chưa có gì → fetch + render (fallback)
        _refreshComments(postId);
      }
      setTimeout(function () {
        var inp = document.getElementById('fpc-cmt-inp-' + postId);
        if (inp) inp.focus();
      }, 80);
    }
  };

  window.forumRenderComments = function (postId) {
    var list = document.getElementById('fpc-cmt-list-' + postId);
    if (!list) return;
    var mockPost = MOCK_POSTS.find(function (p) { return p.id === postId; });
    var cmts = mockPost
      ? ((mockPost.commentList || []).slice())
      : ((_commentsCache[postId] || []).slice());
    var sortDir = _cmtSortMap[postId] || 'newest';
    cmts.sort(function (a, b) { return sortDir === 'oldest' ? a.time - b.time : b.time - a.time; });
    if (!cmts.length) {
      list.innerHTML = '<p class="fpc-cmt-empty">Chưa có bình luận nào. Hãy là người đầu tiên! 👋</p>';
      return;
    }
    list.innerHTML = cmts.map(function (c, i) {
      var isLast = (i === cmts.length - 1);
      var reactions = c.reactions || {};
      var myReaction = c.myReaction || null;
      var totalR = Object.values(reactions).reduce(function (a, b) { return a + b; }, 0);
      var reactEmoji = myReaction ? REACT_EMOJIS[myReaction] : '👍';
      var reactLabel = myReaction ? REACT_LABELS[myReaction] : 'Thích';
      var reactCls = myReaction ? 'cmt-reacted-' + myReaction : '';
      var replies = c.replies || [];

      var pickerHtml = Object.keys(REACT_EMOJIS).map(function (k) {
        return '<span class="fpc-cmt-react-item" onclick="forumSetCmtReaction(\'' + postId + '\',\'' + c.id + '\',\'' + k + '\')" title="' + REACT_LABELS[k] + '">' + REACT_EMOJIS[k] + '</span>';
      }).join('');

      var reactSummaryHtml = '';
      if (totalR > 0) {
        var topEmojis = Object.keys(reactions)
          .filter(function (k) { return reactions[k] > 0; })
          .sort(function (a, b) { return reactions[b] - reactions[a]; })
          .slice(0, 2).map(function (k) { return REACT_EMOJIS[k]; }).join('');
        reactSummaryHtml = '<span class="fpc-cmt-react-summary">' + topEmojis + ' ' + totalR + '</span>';
      }

      var repliesHtml = replies.map(function (r) {
        var rReactions = r.reactions || {};
        var rMyReaction = r.myReaction || null;
        var rTotalR = Object.values(rReactions).reduce(function (a, b) { return a + b; }, 0);
        var rReactEmoji = rMyReaction ? REACT_EMOJIS[rMyReaction] : '👍';
        var rReactLabel = rMyReaction ? REACT_LABELS[rMyReaction] : 'Thích';
        var rReactCls = rMyReaction ? 'cmt-reacted-' + rMyReaction : '';
        var rPickerHtml = Object.keys(REACT_EMOJIS).map(function (k) {
          return '<span class="fpc-cmt-react-item" onclick="forumSetReplyReaction(\'' + postId + '\',\'' + c.id + '\',\'' + r.id + '\',\'' + k + '\')" title="' + REACT_LABELS[k] + '">' + REACT_EMOJIS[k] + '</span>';
        }).join('');
        var rSummaryHtml = '';
        if (rTotalR > 0) {
          var rTopEmojis = Object.keys(rReactions)
            .filter(function (k) { return rReactions[k] > 0; })
            .sort(function (a, b) { return rReactions[b] - rReactions[a]; })
            .slice(0, 2).map(function (k) { return REACT_EMOJIS[k]; }).join('');
          rSummaryHtml = '<span class="fpc-cmt-react-summary">' + rTopEmojis + ' ' + rTotalR + '</span>';
        }
        return (
          '<div class="fpc-reply-item">' +
          '<div class="fpc-reply-avatar">' + (r.avatar || '🧑') + '</div>' +
          '<div class="fpc-reply-body">' +
          '<div class="fpc-cmt-bubble">' +
          '<span class="fpc-cmt-author">' + escHtml(r.author) + '</span>' +
          (r.replyTo ? '<span class="fpc-reply-to"> @' + escHtml(r.replyTo) + '</span> ' : '') +
          '<p class="fpc-cmt-text">' + escHtml(r.text) + '</p>' +
          '</div>' +
          '<div class="fpc-cmt-actions">' +
          '<span class="fpc-cmt-time-inline">' + timeAgo(r.time) + '</span>' +
          '<div class="fpc-cmt-react-wrap">' +
          '<button class="fpc-cmt-act-btn fpc-cmt-like-btn ' + rReactCls + '" onclick="forumSetReplyReaction(\'' + postId + '\',\'' + c.id + '\',\'' + r.id + '\',\'' + (rMyReaction || 'like') + '\')">' +
          rReactEmoji + ' ' + rReactLabel +
          '</button>' +
          '<div class="fpc-cmt-reaction-picker">' + rPickerHtml + '</div>' +
          '</div>' +
          rSummaryHtml +
          '<button class="fpc-cmt-act-btn fpc-cmt-reply-btn" onclick="forumToggleReply(\'' + postId + '\',\'' + c.id + '\',\'' + escHtml(r.author) + '\')">Trả lời</button>' +
          '</div>' +
          '</div>' +
          '</div>'
        );
      }).join('');

      return (
        '<div class="fpc-cmt-item" id="fpc-ci-' + postId + '-' + c.id + '">' +
        '<div class="fpc-cmt-avatar-col">' +
        '<div class="fpc-cmt-avatar">' + (c.avatar || '🧑') + '</div>' +
        '<div class="fpc-cmt-vline"></div>' +
        '</div>' +
        '<div class="fpc-cmt-body">' +
        '<div class="fpc-cmt-bubble">' +
        '<span class="fpc-cmt-author">' + escHtml(c.author) + '</span>' +
        '<p class="fpc-cmt-text">' + escHtml(c.text) + '</p>' +
        '</div>' +
        '<div class="fpc-cmt-actions">' +
        '<span class="fpc-cmt-time-inline">' + timeAgo(c.time) + '</span>' +
        '<div class="fpc-cmt-react-wrap">' +
        '<button class="fpc-cmt-act-btn fpc-cmt-like-btn ' + reactCls + '" onclick="forumSetCmtReaction(\'' + postId + '\',\'' + c.id + '\',\'' + (myReaction || 'like') + '\')">' +
        reactEmoji + ' ' + reactLabel +
        '</button>' +
        '<div class="fpc-cmt-reaction-picker">' + pickerHtml + '</div>' +
        '</div>' +
        reactSummaryHtml +
        '<button class="fpc-cmt-act-btn fpc-cmt-reply-btn" onclick="forumToggleReply(\'' + postId + '\',\'' + c.id + '\',\'' + escHtml(c.author) + '\')">Trả lời</button>' +
        '</div>' +
        (repliesHtml ? '<div class="fpc-replies-list">' + repliesHtml + '</div>' : '') +
        '<div class="fpc-reply-input-row" id="fpc-reply-row-' + postId + '-' + c.id + '" style="display:none">' +
        '<div class="fpc-reply-avatar">🧑</div>' +
        '<div class="fpc-cmt-compose">' +
        '<input class="fpc-cmt-input" id="fpc-reply-inp-' + postId + '-' + c.id + '" placeholder="Trả lời ' + escHtml(c.author) + '..." ' +
        'onkeydown="if(event.key===\'Enter\'&&!event.shiftKey){event.preventDefault();forumAddReply(\'' + postId + '\',\'' + c.id + '\');}" />' +
        '<button class="fpc-cmt-send" onclick="forumAddReply(\'' + postId + '\',\'' + c.id + '\')" title="Gửi">↑</button>' +
        '</div>' +
        '</div>' +
        '</div>' +
        '</div>'
      );
    }).join('');
  };

  window.forumAddComment = function (postId) {
    var inp = document.getElementById('fpc-cmt-inp-' + postId);
    if (!inp) return;
    var text = inp.value.trim();
    if (!text) return;
    var mockIdx = MOCK_POSTS.findIndex(function (p) { return p.id === postId; });

    if (mockIdx !== -1) {
      // MOCK_POSTS (chỉ admin) — thao tác cục bộ
      var nameEl = document.getElementById('chip-name');
      var comment = {
        id: 'c' + Date.now(),
        author: (nameEl && nameEl.textContent.trim() && nameEl.textContent.trim() !== '—') ? nameEl.textContent.trim() : 'Bạn',
        avatar: '🧑', time: Date.now(), text: text,
      };
      if (!MOCK_POSTS[mockIdx].commentList) MOCK_POSTS[mockIdx].commentList = [];
      MOCK_POSTS[mockIdx].commentList.push(comment);
      MOCK_POSTS[mockIdx].comments = MOCK_POSTS[mockIdx].commentList.length;
      inp.value = '';
      forumRenderComments(postId);
      _setCommentBadge(postId, MOCK_POSTS[mockIdx].comments);
      return;
    }
    // Bài thật — optimistic: hiển thị comment ngay, API chạy nền
    inp.value = '';
    var nameEl = document.getElementById('chip-name');
    var myName = (nameEl && nameEl.textContent.trim() && nameEl.textContent.trim() !== '—') ? nameEl.textContent.trim() : 'Bạn';
    var tempComment = {
      id: 'temp-' + Date.now(), author: myName, avatar: '🧑',
      time: Date.now(), text: text,
      reactions: { like: 0, love: 0, haha: 0, wow: 0, sad: 0, angry: 0 },
      myReaction: null, replies: []
    };
    // Thêm vào cache ngay
    if (!_commentsCache[postId]) _commentsCache[postId] = [];
    _commentsCache[postId].push(tempComment);
    forumRenderComments(postId);
    // Cập nhật badge số comment
    var post = _lastRenderedPosts.find(function (p) { return String(p.id) === String(postId); });
    if (post) { post.comments = _commentsCache[postId].length; }
    _setCommentBadge(postId, _commentsCache[postId].length);
    // Scroll tới comment mới
    var listEl = document.getElementById('fpc-cmt-list-' + postId);
    if (listEl && listEl.lastElementChild)
      listEl.lastElementChild.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    // API nền — refresh cache từ server (silent, không re-render nếu không cần)
    forumApi.addComment(postId, text, null).then(function (res) {
      if (res && res.error) { alert(window.__PE_errMsg ? window.__PE_errMsg(res.error) : res.error); return; }
      // Refresh cache từ server để có ID thật + dữ liệu chính xác
      _refreshComments(postId);
    });
  };

  window.forumSetCmtSort = function (postId, dir) {
    _cmtSortMap[postId] = dir;
    ['newest', 'oldest'].forEach(function (d) {
      var btn = document.getElementById('fpc-csort-' + d + '-' + postId);
      if (btn) btn.classList.toggle('active', d === dir);
    });
    forumRenderComments(postId);
  };

  // Toggle reaction cục bộ trên 1 node (dùng cho MOCK_POSTS).
  function _applyReactionLocal(node, key) {
    if (!node) return;
    if (!node.reactions) node.reactions = { like: 0, love: 0, haha: 0, wow: 0, sad: 0, angry: 0 };
    var prev = node.myReaction || null;
    if (prev === key) {
      node.myReaction = null;
      if (node.reactions[key] > 0) node.reactions[key]--;
    } else {
      if (prev && node.reactions[prev] > 0) node.reactions[prev]--;
      node.myReaction = key;
      node.reactions[key] = (node.reactions[key] || 0) + 1;
    }
  }

  /* ── Patch DOM tại chỗ cho reaction comment — không re-render toàn bộ comment list ── */
  function _patchCmtReactionDOM(postId, targetId, reactions, myReaction) {
    // Tìm comment item chứa reaction cần patch
    var commentEl = document.getElementById('fpc-ci-' + postId + '-' + targetId);
    // Nếu không tìm thấy (có thể là reply), tìm trong toàn bộ comment section
    if (!commentEl) {
      var section = document.getElementById('fpc-cmt-' + postId);
      if (!section) return;
      // Tìm bất kỳ phần tử nào có onclick chứa targetId
      var allBtns = section.querySelectorAll('.fpc-cmt-like-btn');
      for (var i = 0; i < allBtns.length; i++) {
        var onclick = allBtns[i].getAttribute('onclick') || '';
        if (onclick.indexOf("'" + targetId + "'") !== -1) {
          commentEl = allBtns[i].closest('.fpc-cmt-item, .fpc-reply-item');
          break;
        }
      }
    }
    if (!commentEl) return;

    var totalR = Object.values(reactions).reduce(function (a, b) { return a + b; }, 0);
    var reactEmoji = myReaction ? REACT_EMOJIS[myReaction] : '👍';
    var reactLabel = myReaction ? REACT_LABELS[myReaction] : 'Thích';
    var reactCls = myReaction ? 'cmt-reacted-' + myReaction : '';

    // Update the like button
    var likeBtn = commentEl.querySelector('.fpc-cmt-like-btn');
    if (likeBtn) {
      likeBtn.className = 'fpc-cmt-act-btn fpc-cmt-like-btn ' + reactCls;
      likeBtn.innerHTML = reactEmoji + ' ' + reactLabel;
      // Pop animation
      likeBtn.style.transform = 'scale(1.2)';
      setTimeout(function () { likeBtn.style.transform = ''; }, 180);
    }

    // Update reaction summary
    var actions = commentEl.querySelector('.fpc-cmt-actions');
    if (actions) {
      var summaryEl = actions.querySelector('.fpc-cmt-react-summary');
      if (totalR > 0) {
        var topEmojis = Object.keys(reactions)
          .filter(function (k) { return reactions[k] > 0; })
          .sort(function (a, b) { return reactions[b] - reactions[a]; })
          .slice(0, 2).map(function (k) { return REACT_EMOJIS[k]; }).join('');
        if (summaryEl) {
          summaryEl.innerHTML = topEmojis + ' ' + totalR;
        } else {
          var span = document.createElement('span');
          span.className = 'fpc-cmt-react-summary';
          span.innerHTML = topEmojis + ' ' + totalR;
          // Insert after the react-wrap
          var reactWrap = actions.querySelector('.fpc-cmt-react-wrap');
          if (reactWrap && reactWrap.nextSibling) {
            actions.insertBefore(span, reactWrap.nextSibling);
          } else {
            actions.appendChild(span);
          }
        }
      } else if (summaryEl) {
        summaryEl.remove();
      }
    }
  }

  // React trên 1 comment/reply bất kỳ (targetId là comment id thật). Dùng chung
  // cho cả comment gốc lẫn reply — backend cùng bảng comment_likes, cùng endpoint.
  function _reactOnComment(postId, targetId, key, findInMock) {
    var mockIdx = MOCK_POSTS.findIndex(function (p) { return p.id === postId; });
    if (mockIdx !== -1) {
      var mockNode = findInMock(MOCK_POSTS[mockIdx]);
      _applyReactionLocal(mockNode, key);
      if (mockNode) _patchCmtReactionDOM(postId, targetId, mockNode.reactions, mockNode.myReaction);
      return;
    }
    // Optimistic: update data + DOM ngay
    var node = _findCommentNode(_commentsCache[postId] || [], targetId);
    if (node) {
      _applyReactionLocal(node, key);
      _patchCmtReactionDOM(postId, targetId, node.reactions, node.myReaction);
    }
    // API chạy nền — reconcile nếu server trả khác
    forumApi.reactComment(targetId, key).then(function (res) {
      if (!res || res.error) return;
      if (node) {
        node.reactions = res.reactions;
        node.myReaction = res.my_reaction;
        _patchCmtReactionDOM(postId, targetId, res.reactions, res.my_reaction);
      }
    });
  }

  window.forumSetCmtReaction = function (postId, cmtId, key) {
    _reactOnComment(postId, cmtId, key, function (post) {
      return (post.commentList || []).find(function (c) { return c.id === cmtId; });
    });
  };

  window.forumSetReplyReaction = function (postId, cmtId, replyId, key) {
    _reactOnComment(postId, replyId, key, function (post) {
      var cmt = (post.commentList || []).find(function (c) { return c.id === cmtId; });
      return cmt && (cmt.replies || []).find(function (r) { return r.id === replyId; });
    });
  };

  window.forumToggleReply = function (postId, cmtId, mentionName) {
    var row = document.getElementById('fpc-reply-row-' + postId + '-' + cmtId);
    if (!row) return;
    var inp = document.getElementById('fpc-reply-inp-' + postId + '-' + cmtId);
    var alreadyOpen = row.style.display !== 'none';
    var prevMention = row.dataset.mention || '';
    if (alreadyOpen && prevMention === mentionName) {
      row.style.display = 'none';
      row.dataset.mention = '';
      return;
    }
    row.style.display = 'flex';
    row.dataset.mention = mentionName;
    if (inp) {
      inp.placeholder = 'Trả lời ' + mentionName + '...';
      setTimeout(function () { inp.focus(); }, 30);
    }
  };

  window.forumAddReply = function (postId, cmtId) {
    var inp = document.getElementById('fpc-reply-inp-' + postId + '-' + cmtId);
    if (!inp) return;
    var text = inp.value.trim();
    if (!text) return;
    var mockIdx = MOCK_POSTS.findIndex(function (p) { return p.id === postId; });

    if (mockIdx !== -1) {
      // MOCK_POSTS (chỉ admin) — thao tác cục bộ
      var nameEl = document.getElementById('chip-name');
      var myName = (nameEl && nameEl.textContent.trim() !== '—') ? nameEl.textContent.trim() : 'Bạn';
      var row = document.getElementById('fpc-reply-row-' + postId + '-' + cmtId);
      var replyTo = (row && row.dataset.mention) || '';
      var cmt = (MOCK_POSTS[mockIdx].commentList || []).find(function (c) { return c.id === cmtId; });
      if (cmt) {
        if (!cmt.replies) cmt.replies = [];
        cmt.replies.push({ id: 'r' + Date.now(), author: myName, avatar: '🧑', time: Date.now(), text: text, replyTo: replyTo || cmt.author });
      }
      inp.value = '';
      forumRenderComments(postId);
      return;
    }
    // Bài thật — optimistic: hiển thị reply ngay, API chạy nền
    inp.value = '';
    var nameEl2 = document.getElementById('chip-name');
    var myName2 = (nameEl2 && nameEl2.textContent.trim() !== '—') ? nameEl2.textContent.trim() : 'Bạn';
    var row = document.getElementById('fpc-reply-row-' + postId + '-' + cmtId);
    var replyTo = (row && row.dataset.mention) || '';
    // Thêm reply vào cache ngay
    var parentCmt = _findCommentNode(_commentsCache[postId] || [], cmtId);
    if (parentCmt) {
      if (!parentCmt.replies) parentCmt.replies = [];
      parentCmt.replies.push({
        id: 'temp-r-' + Date.now(), author: myName2, avatar: '🧑',
        time: Date.now(), text: text, replyTo: replyTo || parentCmt.author,
        reactions: { like: 0, love: 0, haha: 0, wow: 0, sad: 0, angry: 0 },
        myReaction: null
      });
    }
    forumRenderComments(postId);
    // Scroll tới comment cha
    setTimeout(function () {
      var item = document.getElementById('fpc-ci-' + postId + '-' + cmtId);
      if (item) item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 50);
    // API nền
    forumApi.addComment(postId, text, cmtId).then(function (res) {
      if (res && res.error) { alert(window.__PE_errMsg ? window.__PE_errMsg(res.error) : res.error); return; }
      _refreshComments(postId);
    });
  };

  var _origNavigateForum = window.navigate;
  window.navigate = function (page) {
    _origNavigateForum(page);
    if (page === 'forum') renderPosts();
  };

  /* Trang của tôi (IIFE khác) cần gọi lại API + helper của diễn đàn để render
     "Bài đăng của tôi" — expose qua window vì khác scope. */
  window.forumApi = forumApi;
  window.forumShared = {
    apiPostToUi: _apiPostToUi,
    timeAgo: timeAgo,
    escHtml: escHtml,
    CAT_LABELS: CAT_LABELS,
    CAT_COLORS: CAT_COLORS,
    CAT_BG: CAT_BG
  };

})();

/* ═══════════════════════════════════════════════════════
   Trang của tôi — profile page hook
   ═══════════════════════════════════════════════════════ */
(function () {
  var _origNavigateProfile = window.navigate;
  window.navigate = function (page) {
    _origNavigateProfile(page);
    if (page === 'profile') _loadProfile();
  };

  function _esc(s) {
    return window.forumShared ? window.forumShared.escHtml(String(s)) : String(s);
  }

  /* ── Mục tiêu HSA hiện trên hero ── */
  function _renderGoals(summary) {
    var box = document.getElementById('prof-goals');
    if (!box) return;
    var chips = [];
    if (summary.targetScore) chips.push(['target', 'Mục tiêu ' + summary.targetScore]);
    if (summary.daysToExam != null) chips.push(['clock', 'Còn ' + summary.daysToExam + ' ngày']);
    if (summary.streakDays) chips.push(['flame', summary.streakDays + ' ngày liên tiếp']);
    if (!chips.length) {
      box.innerHTML = '<a class="prof-goal-chip prof-goal-chip--cta" href="/questionaire">'
        + 'Đặt mục tiêu HSA của bạn →</a>';
      return;
    }
    box.innerHTML = chips.map(function (c) {
      return '<span class="prof-goal-chip"><i data-icon="' + c[0] + '" data-size="13"></i>'
        + _esc(c[1]) + '</span>';
    }).join('');
    if (window.mountIcons) mountIcons(box);
  }

  /* ── Vị trí trong cộng đồng ── */
  function _renderRanks(weekly, streak) {
    var box = document.getElementById('prof-ranks');
    if (!box) return;
    var rows = [];
    if (weekly && weekly.me) {
      rows.push(['XP tuần này', '#' + weekly.me.rank, (weekly.me.value || 0) + ' XP']);
    }
    if (streak && streak.me) {
      rows.push(['Chuỗi ngày học', '#' + streak.me.rank, (streak.me.value || 0) + ' ngày']);
    }
    if (!rows.length) {
      box.innerHTML = '<div class="prof-empty">Chưa có dữ liệu xếp hạng.</div>';
      return;
    }
    box.innerHTML = rows.map(function (r) {
      return '<div class="prof-rank">'
        + '<span class="prof-rank-lbl">' + r[0] + '</span>'
        + '<span class="prof-rank-pos">' + r[1] + '</span>'
        + '<span class="prof-rank-val">' + r[2] + '</span>'
        + '</div>';
    }).join('')
      + '<a class="prof-rank-link" href="#" onclick="window.navigate(\'dashboard\');return false;">'
      + 'Xem bảng xếp hạng đầy đủ →</a>';
  }

  window.navigateToSkills = function () {
    window.navigate('skills');
    var skillsPage = document.getElementById('page-skills');
    if (skillsPage && !skillsPage.classList.contains('active')) {
      document.querySelectorAll('.page').forEach(function (p) {
        p.classList.remove('active');
      });
      skillsPage.classList.add('active');
      if (typeof window._loadSkillsGlobal === 'function') window._loadSkillsGlobal();
    }
  };

  function _loadProfile() {
    // Tên & email: lấy từ data đã load sẵn trong settings.
    // Phải dùng settings-profile-name (họ tên ĐẦY ĐỦ) chứ không phải chip-name —
    // chip-name chỉ là tên gọi ở góc phải, đã cắt còn chữ cuối ("Quản trị viên"
    // → "viên"), nên hồ sơ hiện mỗi "viên".
    var name = (document.getElementById('settings-profile-name') || {}).textContent || '—';
    var email = (document.getElementById('settings-profile-email') || {}).textContent || '—';
    if (name === '—') name = (document.getElementById('chip-name') || {}).textContent || '—';
    _set('prof-name', name);
    _set('prof-email', email);

    // Số khóa đang học
    _set('prof-enrolled', enrolledCourses ? enrolledCourses.length : '—');

    // Một lượt /api/hsa/summary nuôi cả chuỗi ngày, số bài xong, mục tiêu và
    // dải năng lực — trước đây gọi /api/stats rồi lại cộng tay completedLessons
    // từ enrollments (đếm sai với người chưa ghi danh).
    var pSummary = fetch('/api/hsa/summary').then(function (r) { return r.ok ? r.json() : {}; })
      .catch(function () { return {}; });

    pSummary.then(function (s) {
      _set('prof-streak', s.streakDays != null ? s.streakDays : '—');
      _set('prof-done', s.lessonsDone != null ? s.lessonsDone : '—');
      _renderGoals(s);
    });
    // Hai khối cũ của cột này đã được thay: "Lịch sử thi thử" → Sổ điểm (liệt
    // kê cả bốn loại hoạt động được chấm), "Năng lực theo hợp phần" → nhập vào
    // đầu mỗi nhóm của Bản đồ năng lực. Nhờ đó trang bỏ luôn được một lượt gọi
    // /api/mock-attempts.
    Promise.all([
      fetch('/api/leaderboard?type=weekly').then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }),
      fetch('/api/leaderboard?type=streak').then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })
    ]).then(function (r) { _renderRanks(r[0], r[1]); });

    // Thành tích: đếm thật từ API /api/achievements
    fetch('/api/achievements')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && typeof d.unlockedCount === 'number') {
          _set('prof-achievements', d.unlockedCount + '/' + d.totalCount);
        }
      })
      .catch(function () { /* giữ nguyên '—' nếu lỗi */ });

    // Kỹ năng: đếm thật từ API /api/skills (trước đây scrape #sk-grid,
    // chỉ có sau khi user mở trang Kỹ năng nên thường trống)
    fetch('/api/skills')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var total = 0;
        ((d && d.skill_sets) || []).forEach(function (bs) {
          total += (bs.skills || []).length;
        });
        _set('prof-skills', total);
      })
      .catch(function () { /* giữ nguyên '—' nếu lỗi */ });

    // Bài đăng của user trên diễn đàn
    _renderProfPosts();

    if (window.mountIcons) mountIcons(document.getElementById('page-profile'));
  }

  function _set(id, val) {
    var el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  /* ── Forum posts của user trên profile ── */
  function _renderProfPosts() {
    var list = document.getElementById('prof-post-list');
    if (!list) return;
    list.innerHTML = '<div class="prof-empty">Đang tải...</div>';

    // Bài của chính user hiện tại, lấy từ DB (server tự lọc theo session).
    // Dùng window.forumApi/forumShared — forumApi gốc nằm ở IIFE diễn đàn,
    // gọi trực tiếp ở đây là ReferenceError khiến ô này kẹt "Đang tải...".
    var fs = window.forumShared;
    window.forumApi.getPosts({ mine: true }).then(function (res) {
      var myPosts = ((res && res.posts) || []).map(fs.apiPostToUi);
      if (!myPosts.length) {
        list.innerHTML = '<div class="prof-empty">Chưa có bài đăng nào.</div>';
        return;
      }
      list.innerHTML = myPosts.map(function (p) {
        var catColor = fs.CAT_COLORS[p.cat] || '#6B7280';
        var catBg = fs.CAT_BG[p.cat] || '#F3F4F6';
        var catLabel = fs.CAT_LABELS[p.cat] || p.cat;
        var excerpt = p.body.length > 120 ? p.body.slice(0, 117) + '...' : p.body;
        var totalR = Object.values(p.reactions || {}).reduce(function (a, b) { return a + b; }, 0);
        return (
          '<div class="prof-post-card" onclick="window.forumOpenPost && window.forumOpenPost(\'' + p.id + '\')" style="cursor:pointer;">' +
            '<div class="prof-post-top">' +
              '<span class="prof-post-cat" style="background:' + catBg + ';color:' + catColor + '">' + catLabel + '</span>' +
              '<span class="prof-post-time">' + fs.timeAgo(p.time) + '</span>' +
            '</div>' +
            '<div class="prof-post-title">' + fs.escHtml(p.title) + '</div>' +
            '<div class="prof-post-excerpt">' + fs.escHtml(excerpt) + '</div>' +
            '<div class="prof-post-stats">' +
              '<span>👍 ' + totalR + '</span>' +
              '<span>💬 ' + (p.comments || 0) + '</span>' +
            '</div>' +
          '</div>'
        );
      }).join('');
    }).catch(function () {
      list.innerHTML = '<div class="prof-empty">Không thể tải bài đăng.</div>';
    });
  }
})();

/* ═══════════════════════════════════════════════════════
   Search bars — Dashboard, Roadmap, Skills, Forum
   ═══════════════════════════════════════════════════════ */
function _sbToggleClear(clearId, val) {
  var btn = document.getElementById(clearId);
  if (btn) btn.style.display = val ? 'flex' : 'none';
}

function dashSearch(val) {
  _sbToggleClear('dash-search-clear', val);
  var q = val.trim().toLowerCase();
  var cards = document.querySelectorAll('#enrolled-list .enrolled-card');
  var hasVisible = false;
  cards.forEach(function (card) {
    var title = (card.querySelector('h3') || {}).textContent || '';
    var sub = (card.querySelector('.subtitle') || {}).textContent || '';
    var match = !q || title.toLowerCase().includes(q) || sub.toLowerCase().includes(q);
    card.style.display = match ? '' : 'none';
    if (match) hasVisible = true;
  });
  var empty = document.getElementById('dash-search-empty');
  if (empty) empty.style.display = (q && !hasVisible) ? 'block' : 'none';
}

function dashClearSearch() {
  var el = document.getElementById('dash-search-input');
  if (el) { el.value = ''; dashSearch(''); el.focus(); }
}

function roadmapSearch(val) {
  _sbToggleClear('roadmap-search-clear', val);
  var q = val.trim().toLowerCase();
  if (!q) return;
  var tabs = document.querySelectorAll('#roadmap-tabs .filter-btn');
  var matched = null;
  tabs.forEach(function (tab) {
    if (!matched && tab.textContent.toLowerCase().includes(q)) matched = tab;
  });
  if (matched) matched.click();
}

function roadmapClearSearch() {
  var el = document.getElementById('roadmap-search-input');
  if (el) { el.value = ''; _sbToggleClear('roadmap-search-clear', ''); el.focus(); }
}

function skillsSearch(val) {
  _sbToggleClear('skills-search-clear', val);
  var q = val.trim().toLowerCase();
  var sets = document.querySelectorAll('#sk-grid .sk-set');
  var hasVisible = false;
  sets.forEach(function (set) {
    var setTitle = (set.querySelector('.sk-set-title') || {}).textContent || '';
    var skills = set.querySelectorAll('.sk-skill-name');
    var skillMatch = false;
    skills.forEach(function (sk) {
      if (sk.textContent.toLowerCase().includes(q)) skillMatch = true;
    });
    var match = !q || setTitle.toLowerCase().includes(q) || skillMatch;
    set.style.display = match ? '' : 'none';
    if (match) hasVisible = true;
  });
  var empty = document.getElementById('skills-search-empty');
  if (empty) empty.style.display = (q && !hasVisible) ? 'block' : 'none';
}

function skillsClearSearch() {
  var el = document.getElementById('skills-search-input');
  if (el) { el.value = ''; skillsSearch(''); el.focus(); }
}

var _forumTextQ = '';

function forumSearch(val) {
  _sbToggleClear('forum-search-clear', val);
  _forumTextQ = val.trim().toLowerCase();
  renderPosts();
}

function forumClearSearch() {
  var el = document.getElementById('forum-search-input');
  if (el) { el.value = ''; forumSearch(''); el.focus(); }
}

/* ═══════════════════════════════════════════════════════
   Popup nhắc giữ chuỗi học
   ═══════════════════════════════════════════════════════ */
(function () {
  /* Nhắc giữ chuỗi ngày học.
     Bản cũ là POPUP PHỦ KÍN màn hình (nền đen 55%, z-index 9999, khoá cuộn
     trang) bật ngay sau mỗi lần đăng nhập — thứ đầu tiên học viên gặp là một
     bức tường phải bấm bỏ. Nay là thẻ nhỏ trượt vào góc, tự tắt, không chặn
     thao tác nào (audit 2026-08-19). */
  function shouldShow() {
    return new URLSearchParams(window.location.search).get('streak') === '1';
  }

  function cleanUrl() {
    var url = new URL(window.location.href);
    url.searchParams.delete('streak');
    history.replaceState(null, '', url.toString());
  }

  function dismiss(el) {
    if (!el || el.__di) return;
    el.__di = true;
    el.classList.remove('show');
    setTimeout(function () { el.remove(); }, 400);
  }

  function show(streak) {
    var el = document.createElement('div');
    el.className = 'streak-toast';
    el.setAttribute('role', 'status');
    var dong = streak > 0
      ? 'Bạn đang có <b>' + streak + ' ngày</b> liên tiếp — học một chút hôm nay để giữ chuỗi nhé.'
      : 'Học một bài hôm nay để bắt đầu chuỗi ngày học của bạn.';
    el.innerHTML =
      '<span class="streak-toast-ic">🔥</span>' +
      '<span class="streak-toast-body">' +
        '<b>Giữ chuỗi hôm nay</b>' +
        '<span>' + dong + '</span>' +
        '<button type="button" class="streak-toast-go">Học tiếp →</button>' +
      '</span>' +
      '<button type="button" class="streak-toast-x" aria-label="Đóng">×</button>';
    document.body.appendChild(el);
    requestAnimationFrame(function () { el.classList.add('show'); });

    el.querySelector('.streak-toast-x').onclick = function () { dismiss(el); };
    el.querySelector('.streak-toast-go').onclick = function () {
      dismiss(el);
      var link = document.querySelector('#hsa-continue .hsa-cont-link');
      if (link) { window.location.href = link.getAttribute('href'); return; }
      if (typeof navigate === 'function') navigate('courses');
    };
    setTimeout(function () { dismiss(el); }, 9000);
  }

  function init() {
    if (!shouldShow()) return;
    cleanUrl();
    // Đợi hàng thẻ đổ số xong để nói ĐÚNG số ngày, thay vì câu chung chung.
    setTimeout(function () {
      var n = parseInt((document.getElementById('tile-streak') || {}).textContent, 10);
      show(isNaN(n) ? 0 : n);
    }, 1400);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();

/* ═══════════════════════════════════════════════════════
   Dashboard redesign — Leaderboard + Mini Roadmap Canvas
   (Thêm bởi patch ngày 2026-06-17, KHÔNG xoá các block phía trên)
   ═══════════════════════════════════════════════════════ */
(function () {
  var _currentLbType = 'weekly';
  var _lbLoaded = { weekly: false, streak: false, friends: false };
  var _lbData = { weekly: null, streak: null, friends: null };
  var _miniRmLoaded = false;

  /* ─── Leaderboard ─── */
  function escHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function renderLeaderboard(data) {
    var meta = document.getElementById('lb-meta');
    var list = document.getElementById('lb-list');
    var me = document.getElementById('lb-me');
    if (!list) return;

    if (!data || !data.entries) {
      meta.textContent = 'Không tải được bảng xếp hạng.';
      list.innerHTML = '<li class="lb-skel">Vui lòng thử lại sau.</li>';
      if (me) me.hidden = true;
      return;
    }

    var unit = data.unit || 'XP';
    var label = data.label || '';
    var meInfo = data.me;

    var inTop = false;
    if (meInfo) {
      for (var i = 0; i < data.entries.length; i++) {
        if (data.entries[i].id && meInfo.id && data.entries[i].id === meInfo.id) {
          inTop = true; break;
        }
        // mock friends không có id thật, fallback so sánh name + value
        if (data.type === 'friends' && data.entries[i].name === meInfo.name
          && data.entries[i].value === meInfo.value) {
          inTop = true; break;
        }
      }
    }

    meta.textContent = label + ' · Top ' + data.entries.length + ' học viên';

    list.innerHTML = data.entries.map(function (e) {
      var rankCls = '';
      if (e.rank === 1) rankCls = 'lb-top1';
      else if (e.rank === 2) rankCls = 'lb-top2';
      else if (e.rank === 3) rankCls = 'lb-top3';
      var isMe = false;
      if (meInfo) {
        if (e.id && meInfo.id && e.id === meInfo.id) isMe = true;
        else if (e.name === meInfo.name && e.value === meInfo.value) isMe = true;
      }
      var medal = e.medal || '';
      return (
        '<li class="lb-row ' + rankCls + (isMe ? ' lb-row-me' : '') + '">' +
        '<div class="lb-rank">' +
        '<span class="lb-rank-text">' + escHtml(medal) + '</span>' +
        '<span class="lb-rank-num">#' + e.rank + '</span>' +
        '</div>' +
        '<div class="lb-avatar">' + escHtml(e.avatar || '🧑') + '</div>' +
        '<div class="lb-info">' +
        '<div class="lb-name">' + escHtml(e.name) + (isMe ? ' (Bạn)' : '') + '</div>' +
        '</div>' +
        '<div class="lb-value">' + formatValue(e.value, unit) + '</div>' +
        '</li>'
      );
    }).join('');

    if (meInfo && !inTop) {
      me.hidden = false;
      me.innerHTML =
        '<div class="lb-me-label">Vị trí của bạn</div>' +
        '<li class="lb-row lb-row-me">' +
        '<div class="lb-rank"><span class="lb-rank-num">#' + meInfo.rank + '</span></div>' +
        '<div class="lb-avatar">' + escHtml(meInfo.avatar || '🧑') + '</div>' +
        '<div class="lb-info">' +
        '<div class="lb-name">' + escHtml(meInfo.name) + ' (Bạn)</div>' +
        '</div>' +
        '<div class="lb-value">' + formatValue(meInfo.value, unit) + '</div>' +
        '</li>';
    } else if (me) {
      me.hidden = true;
    }
  }

  function formatValue(v, unit) {
    if (v == null) return '—';
    if (unit === 'ngày') return v + ' ngày';
    return Number(v).toLocaleString('vi-VN') + ' XP';
  }

  function loadLeaderboard(type) {
    type = type || _currentLbType;
    _currentLbType = type;
    var list = document.getElementById('lb-list');
    var meta = document.getElementById('lb-meta');
    var me = document.getElementById('lb-me');
    if (!list) return;
    if (meta) meta.textContent = 'Đang tải…';
    list.innerHTML = '<li class="lb-skel">Đang tải bảng xếp hạng…</li>';
    if (me) me.hidden = true;

    // Cache hit
    if (_lbLoaded[type] && _lbData[type]) {
      renderLeaderboard(_lbData[type]);
      return;
    }

    fetch(API + '/leaderboard?type=' + encodeURIComponent(type))
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (data) {
        _lbLoaded[type] = true;
        _lbData[type] = data;
        if (_currentLbType === type) renderLeaderboard(data);
      })
      .catch(function () {
        if (meta) meta.textContent = 'Lỗi tải bảng xếp hạng.';
        list.innerHTML = '<li class="lb-skel">Không tải được dữ liệu.</li>';
      });
  }

  // Expose to window for inline onclick
  window.setLbTab = function (type, btn) {
    var tabs = document.querySelectorAll('.lb-tab');
    tabs.forEach(function (t) {
      var active = t === btn;
      t.classList.toggle('active', active);
      t.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    loadLeaderboard(type);
  };

  // Khởi tạo listener cho các nút tab (dùng delegation để tránh phải gọi lại)
  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('.lb-tab');
    if (!btn) return;
    var type = btn.getAttribute('data-type');
    if (!type) return;
    window.setLbTab(type, btn);
  });

  /* ─── Mini roadmap canvas ─── */
  // Vẽ zigzag 6 node trong 1 canvas cố định (height 420, width theo container)
  var POSITIONS = [
    { x: 28, y: 14 },
    { x: 72, y: 28 },
    { x: 28, y: 44 },
    { x: 72, y: 60 },
    { x: 28, y: 76 },
    { x: 72, y: 90 },
  ];

  function classifyNode(c) {
    if (!c) return 'locked';
    var p = Number(c.progress || 0);
    if (p >= 100) return 'done';
    if (p > 0) return 'current';
    return 'locked';
  }

  function renderMiniCanvas(courses) {
    var canvas = document.getElementById('mini-rm-canvas');
    if (!canvas) return;

    if (!courses || !courses.length) {
      // Khối trống: icon SVG (không emoji), một câu nói rõ việc cần làm, một
      // nút hành động. Class is-empty cho khối TỰ CO thay vì giữ chiều cao
      // 360px — chính chỗ này tạo mảng trống lớn giữa dashboard (audit
      // 2026-08-13). Nội dung cũ còn sót chữ "học lập trình" của pe_test.
      canvas.classList.add('is-empty');
      canvas.innerHTML =
        '<div class="mini-rm-empty">' +
        '<div class="mini-rm-empty-icon" data-icon="map" data-size="30"></div>' +
        '<div>Bạn chưa đăng ký khoá nào.<br>Chọn một hợp phần HSA để bắt đầu lộ trình của bạn.</div>' +
        '<a class="mini-rm-empty-cta" href="#" onclick="navigate(\'courses\');return false;">Khám phá khoá học</a>' +
        '</div>';
      if (window.mountIcons) mountIcons(canvas);
      return;
    }

    // Pad thêm "khoá học tiếp theo" nếu có enrolled ít hơn 6
    var nodes = courses.slice(0, 6);
    var svgW = canvas.clientWidth || 320;
    var svgH = canvas.clientHeight || 420;

    var svgPaths = '';
    for (var i = 0; i < nodes.length - 1; i++) {
      var a = POSITIONS[i], b = POSITIONS[i + 1];
      var x1 = (a.x / 100) * svgW, y1 = (a.y / 100) * svgH;
      var x2 = (b.x / 100) * svgW, y2 = (b.y / 100) * svgH;
      // Đường cong Bezier đơn giản
      var midX = (x1 + x2) / 2;
      var path = 'M ' + x1 + ' ' + y1 + ' C ' + midX + ' ' + y1 + ', ' + midX + ' ' + y2 + ', ' + x2 + ' ' + y2;
      var isActive = classifyNode(nodes[i]) === 'done' || classifyNode(nodes[i]) === 'current';
      svgPaths += '<path id="mini-rm-path-' + i + '" class="mini-rm-arrow ' + (isActive ? 'mini-rm-arrow--solid' : '') + '" d="' + path + '"></path>';
    }

    // Truck animation: chạy từ current node đến next node. Tìm index current.
    var currentIdx = -1;
    nodes.forEach(function (c, i) {
      if (classifyNode(c) === 'current') currentIdx = i;
    });

    var html = '<svg class="mini-rm-arrows" viewBox="0 0 ' + svgW + ' ' + svgH + '" preserveAspectRatio="none">' + svgPaths;
    if (currentIdx >= 0 && currentIdx < nodes.length - 1) {
      html += '<g class="mini-rm-truck">' +
              '<circle r="11" fill="#FCD34D" stroke="#F59E0B" stroke-width="2"/>' +
              '<text x="0" y="5" text-anchor="middle" font-size="14">🚚</text>' +
              '<animateMotion dur="6s" repeatCount="indefinite" rotate="auto">' +
              '<mpath href="#mini-rm-path-' + currentIdx + '"/>' +
              '</animateMotion>' +
              '</g>';
    }
    html += '</svg>';
    nodes.forEach(function (c, i) {
      var pos = POSITIONS[i];
      var status = classifyNode(c);
      var lessons = (c.completedLessons != null ? c.completedLessons : 0) + '/' + (c.totalLessons || 0);
      var sub = status === 'done' ? '✓ Hoàn thành'
        : status === 'current' ? (c.progress || 0) + '% · ' + lessons
          : 'Bấm để bắt đầu';
      var onClick = "window.location.href='" + (window.COURSE_URLS && window.COURSE_URLS[c.id]
        ? window.COURSE_URLS[c.id]
        : '/lesson/' + c.id) + "'";
      html +=
        '<div class="mini-rm-node mini-rm-node--' + status + '"' +
        ' style="left:' + pos.x + '%; top:' + pos.y + '%;"' +
        ' onclick="' + onClick + '"' +
        ' title="' + escHtml(c.title || '') + '">' +
        '<div class="mini-rm-node-icon">' + escHtml(c.icon || '📘') + '</div>' +
        '<div class="mini-rm-node-body">' +
        '<div class="mini-rm-node-title">' + escHtml(c.title || 'Khóa học') + '</div>' +
        '<div class="mini-rm-node-sub">' + escHtml(sub) + '</div>' +
        '</div>' +
        '</div>';
    });

    canvas.innerHTML = html;
  }

  function loadMiniRoadmap() {
    // Nếu main.js đã load enrolledCourses → render luôn
    if (window.enrolledCourses && window.enrolledCourses.length) {
      renderMiniCanvas(window.enrolledCourses);
      _miniRmLoaded = true;
      return;
    }
    if (_miniRmLoaded) return;
    _miniRmLoaded = true;

    // 1) Ưu tiên dùng cache enrolledCourses của main.js
    if (window.enrolledCourses && window.enrolledCourses.length) {
      renderMiniCanvas(window.enrolledCourses);
      return;
    }

    // 2) Fallback fetch /api/enrolled
    fetch(API + '/enrolled')
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (data) {
        renderMiniCanvas(data || []);
        // Watch: main.js may load enrolledCourses sau → re-render khi có
        var tries = 0;
        var iv = setInterval(function () {
          tries++;
          if (window.enrolledCourses && window.enrolledCourses.length) {
            renderMiniCanvas(window.enrolledCourses);
            clearInterval(iv);
          } else if (tries > 20) {
            clearInterval(iv);
          }
        }, 500);
      })
      .catch(function () {
        renderMiniCanvas([]);
      });
  }

  /* ─── Hook vào navigate() để re-render khi quay lại dashboard ─── */
  // Lưu navigate gốc (nếu có) rồi bọc
  document.addEventListener('DOMContentLoaded', function () {
    // Bỏ qua nếu không có hàm navigate (không phải trang dashboard)
    if (typeof window.navigate !== 'function') return;

    var _origNav = window.navigate;
    if (_origNav.__hookedDashboard) return; // tránh hook 2 lần
    window.navigate = function (page) {
      _origNav(page);
      if (page === 'dashboard') {
        loadLeaderboard('weekly');
        // Vẽ lại canvas với kích thước mới (nếu main.js đã load enrolledCourses)
        if (window.enrolledCourses && window.enrolledCourses.length) {
          // Defer để DOM ổn định
          setTimeout(function () { loadMiniRoadmap(); }, 50);
        }
      }
    };
    window.navigate.__hookedDashboard = true;

    // Lần đầu load
    setTimeout(function () {
      loadLeaderboard('weekly');
      loadMiniRoadmap();
    }, 200);
  });
})();

/* ══════════════════════════════════════════════════════════════════════════
   DASHBOARD KIỂU DỮ LIỆU (audit 2026-08-14)
   Đổ số vào hàng 4 thẻ + dải 7 ngày + "Học tiếp" + tiến độ 3 hợp phần.
   Một lượt gọi /api/hsa/summary thay vì ghép từ 4 endpoint rời.
   Thiếu dữ liệu → hiện dấu gạch kèm nút hành động, KHÔNG bịa số.
   ══════════════════════════════════════════════════════════════════════════ */
(function () {
  var SECTIONS = [
    { key: 'ql', id: 'hsa_quantitative', name: 'Tư duy Định lượng', total: 27 },
    { key: 'vb', id: 'hsa_verbal', name: 'Tư duy Định tính', total: 23 },
    { key: 'kh', id: 'hsa_science', name: 'Khoa học', total: 26 }
  ];
  var DAYS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];
  //: /api/hsa/summary và /api/courses-enrolled chạy song song — giữ kết quả
  //  summary lại để bên nào về sau cũng vẽ được bằng dữ liệu đầy đủ.
  var lastSummary = null, lastEnrolled = null;

  function el(id) { return document.getElementById(id); }

  function renderWeek(streak) {
    var box = el('tile-week');
    if (!box) return;
    // Thứ trong tuần: JS trả CN=0 → quy về T2=0 cho khớp lịch Việt Nam.
    var todayIdx = (new Date().getDay() + 6) % 7;
    box.innerHTML = DAYS.map(function (d, i) {
      // streak ĐÃ tính cả hôm nay → số ngày trước đó được tô là streak - 1.
      var cls = i === todayIdx ? ' class="is-today"'
        : (i < todayIdx && streak > (todayIdx - i) ? ' class="is-done"' : '');
      return '<span' + cls + '>' + d + '</span>';
    }).join('');
  }

  function renderTiles(s) {
    if (el('tile-streak')) el('tile-streak').textContent = s.streakDays || 0;
    renderWeek(s.streakDays || 0);

    var done = s.lessonsDone || 0, total = s.lessonsTotal || 76;
    if (el('tile-done')) el('tile-done').textContent = done;
    if (el('tile-done-bar')) el('tile-done-bar').style.width = Math.round(done / total * 100) + '%';

    // Đếm ngược: không suy ra được thì để dấu gạch + nút dẫn tới nơi sửa được.
    // Đã khảo sát nhưng mốc đã trôi qua → dẫn thẳng vào Cài đặt, không bắt
    // học viên làm lại toàn bộ khảo sát chỉ để đổi một dòng.
    var days = s.daysToExam;
    if (el('tile-days')) el('tile-days').textContent = (days == null ? '—' : days);
    var dCta = el('tile-days-cta');
    if (dCta) {
      dCta.classList.toggle('hidden', days != null);
      var surveyed = Boolean(s.examTiming || s.targetScore);
      dCta.textContent = surveyed ? 'Cập nhật mốc thi' : 'Làm khảo sát để đặt mốc thi';
      dCta.setAttribute('href', surveyed ? '#hsa-goals' : '/questionaire');
      if (surveyed) {
        dCta.onclick = function (e) {
          e.preventDefault();
          if (typeof window.navigate === 'function') window.navigate('settings');
          var box = el('hsa-goals');
          if (box) box.scrollIntoView({ behavior: 'smooth', block: 'center' });
        };
      } else {
        dCta.onclick = null;
      }
    }

    // Điểm thi thử: có mục tiêu thì hiện "điểm / mục tiêu".
    var sc = s.lastMockScore, tot = s.lastMockTotal;
    if (el('tile-score')) {
      el('tile-score').textContent = (sc == null || tot == null) ? '—' : (sc + '/' + tot);
    }
    if (el('tile-score-lbl')) {
      el('tile-score-lbl').textContent = s.targetScore
        ? ('điểm thi thử · mục tiêu ' + s.targetScore)
        : 'điểm thi thử gần nhất';
    }
    var sCta = el('tile-score-cta');
    if (sCta) sCta.classList.toggle('hidden', sc != null && tot != null);
  }

  function renderSections(enrolled) {
    var box = el('hsa-sections');
    if (!box) return;
    var byId = {};
    (enrolled || []).forEach(function (c) { byId[c.id] = c; });
    var counted = (lastSummary && lastSummary.byCourse) || {};
    box.innerHTML = SECTIONS.map(function (s) {
      var c = byId[s.id] || {};
      // Số bài đã xong đếm thẳng từ lesson_progress; enrollments.progress chỉ
      // là bộ nhớ đệm và bằng 0 với người chưa ghi danh.
      var doneN = counted[s.id];
      var pct = (doneN != null)
        ? Math.max(0, Math.min(100, Math.round(doneN / s.total * 100)))
        : Math.max(0, Math.min(100, Math.round(c.progress || 0)));
      if (doneN == null) doneN = Math.round(pct / 100 * s.total);
      return '<div class="hsa-sec-row" data-sec="' + s.key + '">' +
        '<span class="hsa-sec-name">' + s.name + '</span>' +
        '<span class="hsa-sec-num">' + doneN + '/' + s.total + ' bài · ' + pct + '%</span>' +
        '<span class="hsa-sec-track"><i style="width:' + pct + '%"></i></span>' +
        '</div>';
    }).join('');
  }

  function renderContinue(enrolled) {
    var box = el('hsa-continue');
    if (!box) return;
    var counted = (lastSummary && lastSummary.byCourse) || {};
    // Số bài đã xong của từng khoá, ưu tiên số đếm thật.
    function doneOf(c) {
      var sec = SECTIONS.filter(function (s) { return s.id === c.id; })[0];
      if (counted[c.id] != null) return counted[c.id];
      return Math.round((c.progress || 0) / 100 * ((sec && sec.total) || 27));
    }
    // Khoá đang học dở dang nhất; chưa động vào khoá nào thì lấy khoá đầu tiên.
    var list = (enrolled || []).slice().sort(function (a, b) { return doneOf(b) - doneOf(a); });
    var c = list.filter(function (x) {
      var sec = SECTIONS.filter(function (s) { return s.id === x.id; })[0];
      return doneOf(x) < ((sec && sec.total) || 27);
    })[0] || list[0];
    if (!c) return;   // chưa có khoá nào → giữ nguyên khối rỗng có sẵn
    var sec = SECTIONS.filter(function (s) { return s.id === c.id; })[0] || { total: 27 };
    var doneN = doneOf(c);
    var nextNum = Math.min(sec.total, doneN + 1);
    var pct = Math.round(doneN / sec.total * 100);
    box.innerHTML =
      '<a class="hsa-cont-link" href="/lesson/' + c.id + '?lesson=' + nextNum + '">' +
        '<span class="hsa-cont-badge">' + nextNum + '</span>' +
        '<span class="hsa-cont-txt">' +
          '<span class="hsa-cont-eyebrow">Học tiếp</span>' +
          '<div class="hsa-cont-title">' + (c.title || 'Khoá học') + ' — Bài ' + nextNum + '</div>' +
          '<span class="hsa-cont-meta">' + pct + '% hoàn thành · ' + sec.total + ' bài</span>' +
        '</span>' +
        '<span class="hsa-cont-go">Vào học →</span>' +
      '</a>';
  }

  /* ── Nhiệm vụ hôm nay ──────────────────────────────────────────────────
     Tiến độ tính từ số liệu THẬT trong ngày; nút "Nhận" chỉ sáng khi đã đạt,
     và mỗi ngày nhận được đúng một lần (máy chủ chặn bằng khoá chính). */
  function renderMissions(data) {
    var box = el('hsa-missions');
    if (!box) return;
    var list = (data && data.missions) || [];
    if (!list.length) {
      box.innerHTML = '<div class="hsa-mis-empty">Chưa có nhiệm vụ nào cho hôm nay.</div>';
      return;
    }
    box.innerHTML = list.map(function (m) {
      var pct = Math.min(100, Math.round(m.progress / (m.target || 1) * 100));
      var state = m.claimed ? 'is-claimed' : (m.done ? 'is-done' : '');
      var btn = m.claimed
        ? '<span class="hsa-mis-got">Đã nhận</span>'
        : (m.done
          ? '<button class="hsa-mis-claim" data-code="' + m.code + '">Nhận +' + m.xpReward + '</button>'
          : '<span class="hsa-mis-xp">+' + m.xpReward + ' XP</span>');
      return '<div class="hsa-mis ' + state + '">'
        + '<div class="hsa-mis-top">'
        + '<span class="hsa-mis-title">' + m.title + '</span>'
        + btn
        + '</div>'
        + '<div class="hsa-mis-track"><i style="width:' + pct + '%"></i></div>'
        + '<div class="hsa-mis-meta">' + m.progress + '/' + m.target + ' · ' + m.description + '</div>'
        + '</div>';
    }).join('');

    Array.prototype.forEach.call(box.querySelectorAll('.hsa-mis-claim'), function (b) {
      b.addEventListener('click', function () {
        b.disabled = true;
        b.textContent = 'Đang nhận…';
        fetch('/api/missions/claim', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code: b.getAttribute('data-code') })
        })
          .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
          .then(function (res) {
            if (!res.ok) { b.disabled = false; b.textContent = 'Thử lại'; return; }
            renderMissions({ missions: res.d.missions });
            (res.d.newAchievements || []).forEach(showAchievement);
            // XP vừa cộng có thể làm xong luôn nhiệm vụ "kiếm 100 XP".
            if (window.__refreshHsaTiles) window.__refreshHsaTiles();
          })
          .catch(function () { b.disabled = false; b.textContent = 'Thử lại'; });
      });
    });
  }

  /* Thành tích vừa mở khoá — báo một lần, tự tắt. */
  function showAchievement(a) {
    var t = document.createElement('div');
    t.className = 'hsa-ach-toast';
    t.setAttribute('role', 'status');
    t.innerHTML = '<span class="hsa-ach-ic">' + (a.icon || '🏅') + '</span>'
      + '<span><b>Mở khoá thành tích</b><br>' + (a.name || '') + '</span>';
    document.body.appendChild(t);
    requestAnimationFrame(function () { t.classList.add('show'); });
    setTimeout(function () {
      t.classList.remove('show');
      setTimeout(function () { t.remove(); }, 400);
    }, 4200);
  }
  window.__showAchievement = showAchievement;

  function loadMissions() {
    if (!el('hsa-missions')) return;
    fetch('/api/missions/today')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { if (d) renderMissions(d); })
      .catch(function () { /* giữ khối rỗng */ });
  }

  /* Vẽ lại phần phụ thuộc CẢ HAI lượt gọi, gọi được nhiều lần vô hại. */
  function renderProgressBlocks() {
    if (lastEnrolled) { renderSections(lastEnrolled); renderContinue(lastEnrolled); }
  }

  /* Nạp lại riêng hàng thẻ — gọi sau khi học viên sửa mục tiêu ở Cài đặt. */
  window.__refreshHsaTiles = function () {
    if (!el('tile-streak')) return;
    fetch('/api/hsa/summary')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { if (d) { lastSummary = d; renderTiles(d); renderProgressBlocks(); } })
      .catch(function () { /* giữ nguyên giá trị đang hiện */ });
  };

  function initHsaDashboard() {
    if (!el('tile-streak')) return;   // không phải trang dashboard
    fetch('/api/hsa/summary')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { if (d) { lastSummary = d; renderTiles(d); renderProgressBlocks(); } })
      .catch(function () { /* thẻ giữ giá trị mặc định */ });
    // Dùng chung lượt gọi với main.js — trước đây mỗi bên tự fetch nên
    // /api/courses-enrolled bị gọi hai lần mỗi lần mở Bảng điều khiển.
    window.__apiGet('/api/courses-enrolled')
      .then(function (list) {
        lastEnrolled = Array.isArray(list) ? list : (list && list.courses) || [];
        renderProgressBlocks();
      })
      .catch(function () { lastEnrolled = []; renderProgressBlocks(); });
    loadMissions();
    if (window.mountIcons) mountIcons(document.querySelector('.hsa-tiles'));
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHsaDashboard);
  } else {
    initHsaDashboard();
  }
})();

/* ══════════════════════════════════════════════════════════════════════════
   MỤC TIÊU HSA trong Cài đặt (audit 2026-08-15)
   Khảo sát đầu vào chỉ chạy MỘT LẦN, nhưng điểm mục tiêu / mốc thi / hợp phần
   thứ 3 lại nuôi thẻ đếm ngược + lộ trình cá nhân hoá. Mục này cho sửa lại.
   Lưu chung nút "Lưu thay đổi" của trang, qua hook window.__saveHsaGoals.
   ══════════════════════════════════════════════════════════════════════════ */
(function () {
  //: khoá API → tên nhóm radio trong DOM
  var RADIOS = {
    target_score: 'goal-target-score',
    exam_timing: 'goal-exam-timing',
    section3_choice: 'goal-section3'
  };
  var loaded = false;

  function setRadio(name, value) {
    var list = document.querySelectorAll('input[name="' + name + '"]');
    Array.prototype.forEach.call(list, function (i) { i.checked = (i.value === value); });
  }

  function getRadio(name) {
    var el = document.querySelector('input[name="' + name + '"]:checked');
    return el ? el.value : '';
  }

  function status(msg, cls) {
    var el = document.getElementById('goal-status');
    if (!el) return;
    el.textContent = msg || '';
    el.className = 'goal-status' + (cls ? ' ' + cls : '');
  }

  function loadGoals() {
    if (loaded || !document.getElementById('hsa-goals')) return;
    fetch('/api/hsa/goals')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d) return;
        Object.keys(RADIOS).forEach(function (k) {
          if (d[k]) setRadio(RADIOS[k], d[k]);
        });
        var dt = document.getElementById('goal-exam-date');
        // Backend có thể trả ISO đầy đủ; <input type="date"> chỉ nhận YYYY-MM-DD.
        if (dt) dt.value = String(d.exam_date || '').slice(0, 10);
        loaded = true;
      })
      .catch(function () { status('Không tải được mục tiêu hiện tại.', 'is-err'); });
  }

  /* Trả Promise để nút "Lưu thay đổi" của trang gộp chung một lượt lưu. */
  window.__saveHsaGoals = function () {
    if (!document.getElementById('hsa-goals')) return Promise.resolve();
    var body = {};
    Object.keys(RADIOS).forEach(function (k) {
      var v = getRadio(RADIOS[k]);
      if (v) body[k] = v;
    });
    var dt = document.getElementById('goal-exam-date');
    // Gửi cả khi rỗng: đó là cách học viên XOÁ ngày thi đã nhập.
    if (dt) body.exam_date = dt.value || '';
    if (!Object.keys(body).length) return Promise.resolve();

    status('Đang lưu…', '');
    return fetch('/api/hsa/goals', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
      .then(function (r) {
        if (r.ok) return r.json();
        return r.json().then(function (e) { throw new Error(e && e.error || 'Lưu thất bại.'); });
      })
      .then(function () {
        status('Đã lưu mục tiêu HSA.', 'is-ok');
        // Thẻ đếm ngược ở Bảng điều khiển phải khớp ngay, không đợi tải lại trang.
        if (typeof window.__refreshHsaTiles === 'function') window.__refreshHsaTiles();
      })
      .catch(function (err) {
        status(err.message || 'Lưu thất bại.', 'is-err');
        throw err;
      });
  };

  document.addEventListener('DOMContentLoaded', function () {
    if (typeof window.navigate !== 'function') return;
    var _orig = window.navigate;
    if (_orig.__hookedGoals) return;
    window.navigate = function (page) {
      _orig(page);
      if (page === 'settings') loadGoals();
    };
    window.navigate.__hookedGoals = true;
    // Vào thẳng /dashboard#settings thì navigate không chạy → nạp luôn.
    if (location.hash.indexOf('settings') > -1 || location.hash.indexOf('hsa-goals') > -1) loadGoals();
  });
})();


/* ═══════════════════════════════════════════════════════
   BẢN ĐỒ NĂNG LỰC THEO CHỦ ĐỀ  (/api/hsa/competency)
   ═══════════════════════════════════════════════════════
   Cả 76 bài HSA đã gắn sẵn chương mục từ lâu — Số học, Hình học, Đọc hiểu,
   Vật lý… — nhưng chưa lần nào dùng để chấm mạnh–yếu. Khối này biến
   "bạn được 62%" thành "Hình học 45% — yếu nhất, ôn tiếp Bài 12".

   HAI QUY TẮC KHÔNG ĐƯỢC PHÁ:
   · Ô chưa đủ dữ liệu để TRỐNG (gạch chéo), không hiện 0%. Một con số dựng từ
     đúng một bài không phải là phép đo, và hiện nó ra còn tệ hơn để trống.
   · Học viên tự đánh dấu "đã nắm" KHÔNG làm đổi điểm thành thạo. Tự đánh giá là
     đầu vào để xếp lịch ôn, không phải bằng chứng năng lực — lẫn hai thứ này là
     cách nhanh nhất khiến số liệu mất giá trị.
   ═══════════════════════════════════════════════════════ */
(function () {
  var API = '/api/hsa/competency';
  var cache = null;

  function esc(s) {
    return window.forumShared ? window.forumShared.escHtml(String(s)) : String(s == null ? '' : s);
  }

  /* Bậc thành thạo → lớp CSS. Bốn bậc là đủ để nhìn ra chỗ yếu; chia nhỏ hơn
     chỉ tạo cảm giác chính xác giả. */
  function level(m) {
    if (m == null) return 'none';
    if (m >= 80) return 'l4';
    if (m >= 60) return 'l3';
    if (m >= 40) return 'l2';
    return 'l1';
  }

  function lessonHref(course, idx) {
    return '/lesson/' + encodeURIComponent(course) + '?lesson=' + idx;
  }

  function tile(t) {
    var data0 = cache || {};
    var lv = level(t.mastery);
    var num = t.mastery == null ? '—' : t.mastery;
    var bar = t.mastery == null
      ? '<div class="cmp-bar cmp-bar--empty" aria-hidden="true"></div>'
      : '<div class="cmp-bar"><i style="width:' + t.mastery + '%"></i></div>';
    // Ô chưa đo phải nói CẦN GÌ để mở đánh giá. "chưa đủ dữ liệu" đúng nhưng
    // là ngõ cụt: người đọc không biết phải làm gì tiếp.
    var thieu = (data0.minActivities || 2) - (t.confidence || 0);
    var meta = t.mastery == null
      ? (t.confidence ? ('cần thêm ' + thieu + ' bài nữa') : ('cần ' + thieu + ' bài để đánh giá'))
      : (t.confidence + ' hoạt động đã đo');
    var next = t.suggestion
      ? '<a class="cmp-go" href="' + lessonHref(t.course, t.suggestion.lessonIndex) + '">Bài '
        + t.suggestion.lessonIndex + ' →</a>'
      : '<span class="cmp-go is-done">xong chủ đề</span>';

    return '<div class="cmp-tile is-' + lv + (t.selfMarked ? ' is-self' : '') + '">'
      + '<div class="cmp-hd">'
        + '<span class="cmp-name" title="' + esc(t.topic) + '">' + esc(t.topic) + '</span>'
        + '<button type="button" class="cmp-self" aria-pressed="' + (t.selfMarked ? 'true' : 'false')
          + '" data-course="' + esc(t.course) + '" data-topic="' + esc(t.topic) + '"'
          // aria-label chứ không phải <span> ẩn: a11y.css nâng sàn vùng chạm
          // 44×44 theo bộ chọn `button[aria-label]`, và trình đọc màn hình đọc
          // được ngay mà không cần thêm phần tử.
          + ' aria-label="' + (t.selfMarked ? 'Bỏ đánh dấu đã nắm ' : 'Tự đánh dấu đã nắm ') + esc(t.topic) + '"'
          + ' title="' + (t.selfMarked ? 'Bỏ đánh dấu đã nắm' : 'Tự đánh dấu đã nắm chủ đề này') + '">✓'
        + '</button>'
      + '</div>'
      + '<div class="cmp-num">' + num + (t.mastery == null ? '' : '<i>%</i>') + '</div>'
      + bar
      + '<div class="cmp-meta"><span>' + t.lessonsDone + '/' + t.lessonsTotal + ' bài</span>' + next + '</div>'
      + '<div class="cmp-sub">' + meta + '</div>'
      + (t.conflict
        ? '<div class="cmp-warn">Bạn đánh dấu đã nắm, nhưng bài làm gần đây mới ' + t.mastery + '%.</div>'
        : '')
      + '</div>';
  }

  function renderMap(data) {
    var box = document.getElementById('cmp-map');
    if (!box) return;
    var topics = (data && data.topics) || [];
    if (!topics.length) {
      box.innerHTML = '<div class="prof-empty">Chưa có chương mục nào trong giáo trình.</div>';
      return;
    }
    // Gom theo hợp phần, giữ nguyên thứ tự máy chủ trả về.
    var groups = [], byId = {};
    topics.forEach(function (t) {
      if (!byId[t.course]) {
        byId[t.course] = { id: t.course, title: t.courseTitle, items: [] };
        groups.push(byId[t.course]);
      }
      byId[t.course].items.push(t);
    });
    // Tóm tắt hợp phần nhập vào ĐẦU NHÓM. Trước đây nó là một khối riêng ngay
    // phía trên bản đồ, nói đúng cùng một chuyện bằng ba thanh thô hơn — hai
    // khối cạnh nhau cùng nội dung là thứ người dùng đã phản ánh một lần rồi.
    var sums = {};
    (data && data.courses || []).forEach(function (c) { sums[c.id] = c; });
    box.innerHTML = groups.map(function (g) {
      var c = sums[g.id] || {};
      var acc = (c.mockPct != null && c.mockCount)
        ? '<span class="cmp-group-acc">thi thử ' + c.mockPct + '% đúng</span>'
        : '<span class="cmp-group-acc is-muted">chưa thi thử</span>';
      var bar = c.lessonsTotal
        ? '<span class="cmp-group-num">' + c.lessonsDone + '/' + c.lessonsTotal + ' bài</span>'
          + '<span class="cmp-group-track"><i style="width:' + (c.pct || 0) + '%"></i></span>'
        : '';
      return '<div class="cmp-group">'
        + '<div class="cmp-group-hd">'
          + '<span class="cmp-group-name">' + esc(g.title) + '</span>' + bar + acc
        + '</div>'
        + '<div class="cmp-grid">' + g.items.map(tile).join('') + '</div>'
        + '</div>';
    }).join('');

    var note = document.getElementById('cmp-note');
    if (note) {
      note.textContent = data.hint || ('Điểm thành thạo gộp bốn nguồn: kiểm tra đầu vào, '
        + 'phòng luyện tốc độ, quiz ôn tập và thi thử — kết quả gần đây tính nặng hơn. '
        + 'Ô gạch chéo là chưa đủ dữ liệu để đánh giá, không phải điểm 0. Dấu ✓ là bạn tự '
        + 'đánh dấu đã nắm: nó chỉ đổi thứ tự gợi ý ôn, không đổi điểm.');
    }
    bindSelf(box);
  }

  function bindSelf(box) {
    Array.prototype.forEach.call(box.querySelectorAll('.cmp-self'), function (b) {
      b.addEventListener('click', function () {
        var known = b.getAttribute('aria-pressed') !== 'true';
        b.disabled = true;
        fetch('/api/hsa/competency/self', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            courseId: b.getAttribute('data-course'),
            topic: b.getAttribute('data-topic'),
            known: known
          })
        })
          .then(function (r) { return r.ok ? r.json() : null; })
          .then(function (d) {
            b.disabled = false;
            if (d) window.__refreshCompetency();
          })
          .catch(function () { b.disabled = false; });
      });
    });
  }

  /* ── Ba chủ đề yếu nhất, đẩy lên Bảng điều khiển ──
     Mỗi chủ đề đúng MỘT nút: biết mình yếu ở đâu mà không có đường đi tiếp thì
     thông tin đó chưa dùng được. */
  function renderWeak(data) {
    var box = document.getElementById('hsa-weak');
    if (!box) return;
    var weak = (data && data.weakest) || [];
    if (!weak.length) {
      box.innerHTML = '<div class="hsa-mis-empty">'
        + esc((data && data.hint) || 'Học thêm vài bài để hệ thống chấm được chủ đề nào cần ôn.')
        + '</div>';
      return;
    }
    box.innerHTML = weak.map(function (t) {
      var go = t.suggestion
        ? '<a class="hsa-weak-btn" href="' + lessonHref(t.course, t.suggestion.lessonIndex)
          + '">Ôn Bài ' + t.suggestion.lessonIndex + ' →</a>'
        : '<a class="hsa-weak-btn is-ghost" href="/mock">Luyện đề →</a>';
      return '<div class="hsa-weak-row is-' + level(t.mastery) + '">'
        + '<span class="hsa-weak-pct">' + t.mastery + '<i>%</i></span>'
        + '<span class="hsa-weak-body">'
          + '<span class="hsa-weak-name">' + esc(t.topic) + '</span>'
          + '<span class="hsa-weak-sub">' + esc(t.courseTitle) + ' · '
            + t.lessonsDone + '/' + t.lessonsTotal + ' bài</span>'
        + '</span>' + go
        + '</div>';
    }).join('');
  }

  function load(force) {
    if (!document.getElementById('cmp-map') && !document.getElementById('hsa-weak')) return;
    if (cache && !force) { renderMap(cache); renderWeak(cache); return; }
    var p = window.__apiGet ? window.__apiGet(API, force ? 0 : 30000)
      : fetch(API).then(function (r) { return r.ok ? r.json() : null; });
    p.then(function (d) {
      if (!d) return;
      cache = d;
      renderMap(d);
      renderWeak(d);
    }).catch(function () { /* giữ khối "đang tải" thay vì hiện số sai */ });
  }

  // Bản đồ nằm ở Trang của tôi → nạp khi mở trang đó. Khối yếu nhất nằm ở Bảng
  // điều khiển → nạp ngay lúc vào.
  var _origNavigateCmp = window.navigate;
  window.navigate = function (page) {
    _origNavigateCmp(page);
    if (page === 'profile') load(false);
  };
  window.__refreshCompetency = function () {
    cache = null;
    if (window.__apiGetBust) window.__apiGetBust(API);
    load(true);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { load(false); });
  } else {
    load(false);
  }
})();


/* ═══════════════════════════════════════════════════════
   ĐƯỜNG TIẾN BỘ + SỔ ĐIỂM  (/api/hsa/progress-curve, /api/hsa/gradebook)
   ═══════════════════════════════════════════════════════
   Trả lời câu hỏi thứ hai của thí sinh, sau "tôi yếu ở đâu":
   "mấy tuần qua tôi có khá lên không, và còn cách đích bao xa?"

   BA QUY TẮC VỀ MẶT SỐ LIỆU:
   · Điểm và thời lượng KHÔNG chung một trục. "Học 300 phút" và "đúng 62%" là
     hai đơn vị; ép chung một thang là vẽ ra tương quan không có thật. Cột thời
     lượng nằm nền, thang riêng, chỉ chiếm nửa dưới khung.
   · Đường xu hướng chỉ vẽ khi đã có từ 3 lượt thi. Nối hai điểm rồi gọi là xu
     hướng là trò lừa thị giác: hai điểm thì luôn thẳng hàng.
   · Tuần không học là một cột TRỐNG nhìn thấy được, không phải khoảng trắng bị
     bỏ qua — nghỉ một tuần cũng là thông tin.

   Vẽ bằng SVG dựng tay theo bề rộng THẬT của khung (giống mini roadmap), không
   dùng viewBox co giãn: co giãn sẽ kéo cỡ chữ xuống còn 5px trên màn 390.
   ═══════════════════════════════════════════════════════ */
(function () {
  var CURVE_API = '/api/hsa/progress-curve';
  var BOOK_API = '/api/hsa/gradebook';
  var weeks = 12;
  var lastCurve = null;

  function esc(s) {
    return window.forumShared ? window.forumShared.escHtml(String(s)) : String(s == null ? '' : s);
  }
  function el(id) { return document.getElementById(id); }

  /* ── Biểu đồ ───────────────────────────────────────────────────────── */
  function drawCurve(d) {
    var box = el('curve-chart');
    if (!box) return;
    var W = Math.max(280, box.clientWidth || 640);
    var H = W < 460 ? 200 : 240;
    var PAD = { l: 32, r: 10, t: 12, b: 24 };
    var pw = W - PAD.l - PAD.r;
    var ph = H - PAD.t - PAD.b;
    var wk = d.weeks || [];
    var span = d.spanDays || (wk.length * 7);

    function X(day) { return PAD.l + (span ? day / span * pw : 0); }
    function Y(pct) { return PAD.t + (100 - Math.max(0, Math.min(100, pct))) / 100 * ph; }

    var parts = [];

    // Dải mục tiêu — chỉ khi học viên ĐÃ đặt mục tiêu. Không có thì bỏ trống,
    // tuyệt đối không vẽ một đích mặc định do hệ thống nghĩ ra.
    var tg = d.target;
    if (tg && (tg.minPct != null || tg.maxPct != null)) {
      var top = Y(tg.maxPct == null ? 100 : tg.maxPct);
      var bot = Y(tg.minPct == null ? 0 : tg.minPct);
      parts.push('<rect class="cv-target" x="' + PAD.l + '" y="' + top.toFixed(1)
        + '" width="' + pw + '" height="' + Math.max(2, bot - top).toFixed(1) + '"/>');
    }

    // Lưới ngang + nhãn %
    [0, 25, 50, 75, 100].forEach(function (p) {
      var y = Y(p);
      parts.push('<line class="cv-grid" x1="' + PAD.l + '" y1="' + y.toFixed(1)
        + '" x2="' + (W - PAD.r) + '" y2="' + y.toFixed(1) + '"/>');
      parts.push('<text class="cv-ylbl" x="' + (PAD.l - 6) + '" y="' + (y + 3.5).toFixed(1)
        + '" text-anchor="end">' + p + '%</text>');
    });

    // Cột thời lượng học — THANG RIÊNG, chỉ dùng nửa dưới khung để không ai
    // nhầm chiều cao cột với phần trăm điểm.
    var maxMin = 0;
    wk.forEach(function (w) { maxMin = Math.max(maxMin, (w.minutes || 0) + (w.selfMinutes || 0)); });
    d._maxMinutes = maxMin;
    var barArea = ph * 0.45;
    var bw = Math.max(3, Math.min(22, pw / Math.max(1, wk.length) * 0.55));
    wk.forEach(function (w, i) {
      var sys = w.minutes || 0, self = w.selfMinutes || 0;
      var total = sys + self;
      if (!total || !maxMin) return;
      var cx = X(i * 7 + 3.5);
      var base = PAD.t + ph;
      // Cột XẾP CHỒNG: đoạn dưới là phút hệ thống bấm giờ, đoạn trên là phút
      // học viên tự khai. Gộp thành một cột đặc là trộn số đo được với số tự
      // nhận — đúng cái ranh giới không được xoá nhoà.
      var hSys = sys / maxMin * barArea;
      var hSelf = self / maxMin * barArea;
      var tip = '<title>Tuần ' + esc(w.label) + ': ' + total + ' phút'
        + (self ? ' (' + sys + ' hệ thống đo, ' + self + ' tự ghi)' : '') + '</title>';
      if (hSys > 0) {
        parts.push('<rect class="cv-bar" x="' + (cx - bw / 2).toFixed(1) + '" y="'
          + (base - hSys).toFixed(1) + '" width="' + bw.toFixed(1) + '" height="'
          + hSys.toFixed(1) + '" rx="2">' + tip + '</rect>');
      }
      if (hSelf > 0) {
        parts.push('<rect class="cv-bar cv-bar--self" x="' + (cx - bw / 2).toFixed(1) + '" y="'
          + (base - hSys - hSelf).toFixed(1) + '" width="' + bw.toFixed(1) + '" height="'
          + hSelf.toFixed(1) + '" rx="2">' + tip + '</rect>');
      }
    });
    d._hasSelf = wk.some(function (w) { return (w.selfMinutes || 0) > 0; });

    // Đường xu hướng (nét đứt) — chỉ khi đủ số lượt thi.
    if (d.trend) {
      parts.push('<line class="cv-trend" x1="' + X(d.trend.x0).toFixed(1) + '" y1="'
        + Y(d.trend.fromPct).toFixed(1) + '" x2="' + X(d.trend.x1).toFixed(1) + '" y2="'
        + Y(d.trend.toPct).toFixed(1) + '"/>');
    }

    // Đường điểm thi thử + từng lượt một chấm.
    var ms = d.mocks || [];
    if (ms.length > 1) {
      parts.push('<polyline class="cv-line" points="' + ms.map(function (m) {
        return X(m.x).toFixed(1) + ',' + Y(m.pct).toFixed(1);
      }).join(' ') + '"/>');
    }
    ms.forEach(function (m) {
      parts.push('<circle class="cv-dot" cx="' + X(m.x).toFixed(1) + '" cy="'
        + Y(m.pct).toFixed(1) + '" r="4"><title>' + esc(_viDate(m.date)) + ': '
        + m.pct + '% (' + m.score + '/' + m.max + ')</title></circle>');
    });

    // Nhãn tuần — thưa ra để không chồng chữ trên màn hẹp.
    var step = Math.max(1, Math.ceil(wk.length / (W < 460 ? 4 : 7)));
    wk.forEach(function (w, i) {
      if (i % step) return;
      parts.push('<text class="cv-xlbl" x="' + X(i * 7 + 3.5).toFixed(1) + '" y="'
        + (H - 7) + '" text-anchor="middle">' + esc(w.label) + '</text>');
    });

    var alt = ms.length
      ? ('Biểu đồ ' + wk.length + ' tuần: ' + ms.length + ' lượt thi thử, từ '
        + ms[0].pct + '% đến ' + ms[ms.length - 1].pct + '% số câu đúng.')
      : ('Biểu đồ ' + wk.length + ' tuần, chưa có lượt thi thử nào.');

    box.innerHTML = '<svg class="cv-svg" width="' + W + '" height="' + H
      + '" role="img" aria-label="' + esc(alt) + '">' + parts.join('') + '</svg>';
  }

  function _viDate(iso) {
    if (!iso) return '';
    var p = String(iso).slice(0, 10).split('-');
    return p.length === 3 ? (p[2] + '/' + p[1] + '/' + p[0]) : iso;
  }

  /* ── Dòng tóm tắt dưới biểu đồ: nói thẳng đang lên hay đang xuống ── */
  function renderCurveMeta(d) {
    var box = el('curve-meta');
    if (!box) return;
    var bits = [];
    var ms = d.mocks || [];

    if (d.trend) {
      var per = d.trend.perWeek;
      var cls = per > 0.3 ? 'is-up' : (per < -0.3 ? 'is-down' : 'is-flat');
      var txt = per > 0.3 ? ('đang lên ' + per.toFixed(1).replace('.', ',') + ' điểm %/tuần')
        : (per < -0.3 ? ('đang xuống ' + Math.abs(per).toFixed(1).replace('.', ',') + ' điểm %/tuần')
          : 'đang đi ngang');
      bits.push('<span class="cv-chip ' + cls + '">Xu hướng: ' + txt + '</span>');
    } else if (ms.length) {
      bits.push('<span class="cv-chip is-flat">Cần ' + (d.minPointsForTrend - ms.length)
        + ' lượt thi nữa mới đủ để nói về xu hướng</span>');
    }

    if (d.target) {
      var need = d.target.minPct != null ? d.target.minPct : d.target.maxPct;
      var now = ms.length ? ms[ms.length - 1].pct : null;
      var reached = (now != null && need != null && now >= need);
      bits.push('<span class="cv-chip' + (reached ? ' is-up' : '') + '">Mục tiêu '
        + esc(d.target.raw) + '/' + d.target.maxScoreScale + ' ≈ ' + need + '% đúng'
        + (now != null ? ' · lượt gần nhất ' + now + '%' : '')
        + (reached ? ' · đã đạt' : '') + '</span>');
    }
    if (d.daysToExam != null) {
      bits.push('<span class="cv-chip">Còn ' + d.daysToExam + ' ngày tới kỳ thi</span>');
    }

    box.innerHTML = bits.join('')
      + '<span class="cv-legend">'
      + '<i class="cv-key cv-key--dot"></i> điểm thi thử'
      + '<i class="cv-key cv-key--bar"></i> thời lượng hệ thống đo/tuần'
      + (d._maxMinutes ? ' (cao nhất ' + d._maxMinutes + ' phút)' : '')
      + (d._hasSelf ? '<i class="cv-key cv-key--self"></i> phút bạn tự ghi trong nhật ký' : '')
      + (d.target ? '<i class="cv-key cv-key--band"></i> dải mục tiêu' : '')
      + '</span>';

    var note = el('curve-note');
    if (note) note.textContent = d.scaleNote || '';
  }

  function renderCurve(d) {
    lastCurve = d;
    var empty = el('curve-empty');
    if (empty) {
      var has = (d.mocks || []).length > 0;
      empty.hidden = has;
      if (!has) {
        empty.innerHTML = '<p>Chưa có lượt thi thử nào — đường tiến bộ cần ít nhất '
          + 'một lượt để bắt đầu.</p><a class="cv-cta" href="/mock">Làm đề thi thử →</a>';
      }
    }
    drawCurve(d);
    renderCurveMeta(d);
  }

  /* ── Sổ điểm ──────────────────────────────────────────────────────────
     Thay cho khối "Lịch sử thi thử" cũ: thi thử chỉ là MỘT loại hoạt động,
     hiện riêng nó thì bài học, phòng luyện và quiz ôn tập không có chỗ nào
     nhìn lại được. */
  function renderBook(d) {
    var sum = el('book-sum');
    if (sum) {
      var kinds = d.byKind || [];
      sum.innerHTML = kinds.length ? kinds.map(function (k) {
        return '<div class="bk-sum">'
          + '<span class="bk-sum-pct">' + k.avgPct + '<i>%</i></span>'
          + '<span class="bk-sum-lbl">' + esc(k.label) + '</span>'
          + '<span class="bk-sum-n">' + k.n + ' lượt</span>'
          + '</div>';
      }).join('') : '';
    }
    var box = el('book-rows');
    if (!box) return;
    var rows = d.rows || [];
    if (!rows.length) {
      box.innerHTML = '<div class="prof-empty">' + esc(d.hint || 'Chưa có hoạt động nào.')
        + ' <a href="/mock">Thi thử ngay →</a></div>';
      return;
    }
    box.innerHTML = rows.map(function (r) {
      return '<div class="bk-row" data-kind="' + esc(r.kind) + '">'
        + '<span class="bk-kind">' + esc(r.kindLabel) + '</span>'
        + '<span class="bk-body">'
          + '<span class="bk-label">' + esc(r.label) + '</span>'
          + '<span class="bk-meta">' + esc(_viDate(r.at))
            + (r.topic ? ' · ' + esc(r.topic) : '')
            + (r.selfReported ? ' · <b>tự ghi nhận</b>' : '') + '</span>'
        + '</span>'
        + '<span class="bk-score">' + (r.score % 1 === 0 ? r.score : r.score.toFixed(1))
          + '<i>/' + (r.max % 1 === 0 ? r.max : r.max.toFixed(1)) + '</i></span>'
        + '<span class="bk-pct">' + r.pct + '%</span>'
        + '</div>';
    }).join('');
  }

  /* ── Nạp ──────────────────────────────────────────────────────────── */
  /* Trang của tôi nằm sẵn trong DOM (ẩn) ngay từ lúc mở Bảng điều khiển, nên
     "phần tử có tồn tại không" KHÔNG dùng làm điều kiện nạp được: nó khiến hai
     endpoint chỉ phục vụ Trang của tôi bị gọi trên mọi lượt vào Bảng điều
     khiển. Chỉ nạp khi trang đó thực sự đang hiển thị. */
  function onProfile() {
    var pg = el('page-profile');
    return !!(pg && pg.classList.contains('active'));
  }

  function load(force) {
    if (!el('curve-chart') || !onProfile()) return;
    var cu = CURVE_API + '?weeks=' + weeks;
    var g1 = window.__apiGet ? window.__apiGet(cu, force ? 0 : 30000)
      : fetch(cu).then(function (r) { return r.ok ? r.json() : null; });
    g1.then(function (d) { if (d) renderCurve(d); }).catch(function () {});

    var g2 = window.__apiGet ? window.__apiGet(BOOK_API, force ? 0 : 30000)
      : fetch(BOOK_API).then(function (r) { return r.ok ? r.json() : null; });
    g2.then(function (d) { if (d) renderBook(d); }).catch(function () {});
  }

  function bindRange() {
    var box = el('curve-range');
    if (!box) return;
    box.addEventListener('click', function (e) {
      var b = e.target.closest && e.target.closest('button[data-weeks]');
      if (!b) return;
      weeks = parseInt(b.getAttribute('data-weeks'), 10) || 12;
      Array.prototype.forEach.call(box.querySelectorAll('button'), function (x) {
        var on = x === b;
        x.classList.toggle('active', on);
        x.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
      load(false);
    });
  }

  // Vẽ lại khi đổi bề rộng khung: SVG dựng theo pixel thật nên không tự co.
  var rt = null;
  window.addEventListener('resize', function () {
    if (!lastCurve) return;
    clearTimeout(rt);
    rt = setTimeout(function () { drawCurve(lastCurve); }, 180);
  });

  var _origNavigateCurve = window.navigate;
  window.navigate = function (page) {
    _origNavigateCurve(page);
    // Khung có bề rộng 0 khi trang còn ẩn → phải vẽ lại sau khi hiện ra.
    if (page === 'profile') { load(false); if (lastCurve) setTimeout(function () { drawCurve(lastCurve); }, 60); }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { bindRange(); load(false); });
  } else {
    bindRange(); load(false);
  }
})();


/* ═══════════════════════════════════════════════════════
   TUẦN NÀY + NHẬT KÝ HỌC  (/api/hsa/journal, /api/hsa/weekly-target)
   ═══════════════════════════════════════════════════════
   Đặt ở Bảng điều khiển chứ không phải Trang của tôi: ghi nhật ký và bám mục
   tiêu tuần là việc làm HẰNG NGÀY, còn Trang của tôi là nơi nhìn lại. Một việc
   hằng ngày nằm dưới đáy một trang dài thì không ai dùng.

   BA ĐIỀU KHÔNG ĐƯỢC LÀM SAI:
   · Phút TỰ KHAI phải nhìn ra được là tự khai. Thanh thời gian tách hai đoạn,
     chú thích ghi rõ đâu là hệ thống bấm giờ, đâu là học viên tự ghi.
   · Mục tiêu do hệ thống đề xuất phải kèm LÝ DO. Một con số áp xuống không nói
     vì sao thì người học không có cơ sở nào để tin, và bỏ ngay tuần đầu.
   · Không đủ thời gian thì NÓI THẲNG. Lặng lẽ hạ mục tiêu cho vừa sức là cách
     chắc chắn để học viên tưởng mình đang kịp, tới sát ngày thi mới biết là không.
   ═══════════════════════════════════════════════════════ */
(function () {
  var API = '/api/hsa/journal';
  var data = null;
  var editingTarget = false;
  var showHistory = false;

  function esc(s) {
    return window.forumShared ? window.forumShared.escHtml(String(s)) : String(s == null ? '' : s);
  }
  function el(id) { return document.getElementById(id); }
  function viDate(iso) {
    if (!iso) return '';
    var p = String(iso).slice(0, 10).split('-');
    return p.length === 3 ? (p[2] + '/' + p[1]) : iso;
  }

  /* ── Tiến độ tuần ─────────────────────────────────────────────────── */
  /* Ba trạng thái khác nhau, đừng gộp:
       · chưa đặt mục tiêu cho mục này (undefined) → chỉ hiện số đã làm
       · đặt bằng 0                                → coi như đã đạt
       · đặt > 0                                   → thanh theo tỉ lệ
     Bản đầu dùng `target ?` nên mục tiêu 0 rơi vào nhánh "chưa đặt" và vẽ ra
     một thanh rỗng trông như hỏng. */
  function bar(label, done, target, extra, split) {
    var hasTarget = (target !== undefined && target !== null);
    var met = hasTarget && done >= target;
    var pct = !hasTarget ? 0 : (target > 0 ? Math.min(100, Math.round(done / target * 100)) : 100);
    // Thanh thời gian XẾP CHỒNG hai đoạn: hệ thống bấm giờ và học viên tự ghi.
    // Chú thích chữ ở dưới đã nói, nhưng chính cái thanh cũng phải nói — người
    // ta đọc hình trước khi đọc chữ.
    var fill = '<i style="width:' + pct + '%"></i>';
    if (split && done > 0 && pct > 0) {
      var sysPct = Math.round(split.system / done * pct);
      fill = '<i style="width:' + sysPct + '%"></i>'
           + '<i class="is-self" style="width:' + Math.max(0, pct - sysPct) + '%"></i>';
    }
    return '<div class="jr-bar' + (met ? ' is-met' : '') + (hasTarget ? '' : ' is-noaim') + '">'
      + '<span class="jr-bar-lbl">' + esc(label) + '</span>'
      + '<span class="jr-bar-track">' + fill + '</span>'
      + '<span class="jr-bar-num">' + done + (hasTarget ? '/' + target : '')
        + (met ? ' ✓' : '') + '</span>'
      + (extra ? '<span class="jr-bar-sub">' + extra + '</span>' : '')
      + '</div>';
  }

  function renderWeek() {
    var box = el('jr-week');
    if (!box || !data) return;
    var w = data.week || {};
    var done = w.done || {};
    var t = data.target;

    if (!t) {
      var s = data.suggestion || {};
      box.innerHTML = '<div class="jr-noplan">'
        + '<p class="jr-noplan-h">Bạn chưa đặt mục tiêu tuần.</p>'
        + '<p class="jr-noplan-s">Hệ thống đề xuất <b>' + s.lessons + ' bài · '
          + s.mocks + ' đề · ' + s.minutes + ' phút</b> mỗi tuần'
          + (s.why ? ' — ' + esc(s.why) : '') + '.</p>'
        + '<div class="jr-actions">'
          + '<button type="button" class="jr-btn" id="jr-use">Dùng đề xuất này</button>'
          + '<button type="button" class="jr-btn is-ghost" id="jr-edit">Tự đặt</button>'
        + '</div>'
        + (s.warning ? '<p class="jr-warn">' + esc(s.warning) + '</p>' : '')
        + '</div>';
      bindTargetButtons();
      return;
    }

    // Thời lượng: TÁCH đoạn hệ thống đo và đoạn tự khai, không cộng thành một
    // con số rồi thôi — người xem phải biết bao nhiêu là đo được.
    var sysM = w.systemMinutes || 0, selfM = w.selfMinutes || 0;
    var extra = (sysM || selfM)
      ? ('<i class="jr-key jr-key--sys"></i>' + sysM + ' phút hệ thống đo'
         + ' <i class="jr-key jr-key--self"></i>' + selfM + ' phút bạn tự ghi')
      : '';
    box.innerHTML =
      bar('Bài học', done.lessons || 0, t.lessons)
      + bar('Đề thi thử', done.mocks || 0, t.mocks)
      + bar('Thời gian', done.minutes || 0, t.minutes, extra,
            { system: sysM, self: selfM })
      + '<div class="jr-actions">'
        + '<button type="button" class="jr-btn is-ghost" id="jr-edit">Sửa mục tiêu</button>'
      + '</div>'
      + (data.targetGap ? '<p class="jr-warn">' + esc(data.targetGap) + '</p>' : '')
      + ((data.suggestion && data.suggestion.warning)
          ? '<p class="jr-warn">' + esc(data.suggestion.warning) + '</p>' : '');
    bindTargetButtons();
  }

  function renderTargetForm() {
    var box = el('jr-week');
    if (!box) return;
    var t = data.target || data.suggestion || {};
    box.innerHTML = '<div class="jr-form jr-form--target">'
      + '<label class="jr-f"><span>Bài/tuần</span>'
        + '<input type="number" id="jr-t-lessons" min="0" max="100" value="' + (t.lessons || 0) + '"></label>'
      + '<label class="jr-f"><span>Đề/tuần</span>'
        + '<input type="number" id="jr-t-mocks" min="0" max="20" value="' + (t.mocks || 0) + '"></label>'
      + '<label class="jr-f"><span>Phút/tuần</span>'
        + '<input type="number" id="jr-t-minutes" min="0" max="5000" step="30" value="' + (t.minutes || 0) + '"></label>'
      + '<div class="jr-actions">'
        + '<button type="button" class="jr-btn" id="jr-t-save">Lưu mục tiêu</button>'
        + '<button type="button" class="jr-btn is-ghost" id="jr-t-cancel">Huỷ</button>'
      + '</div></div>';
    el('jr-t-save').addEventListener('click', function () {
      saveTarget({
        lessons: el('jr-t-lessons').value,
        mocks: el('jr-t-mocks').value,
        minutes: el('jr-t-minutes').value
      });
    });
    el('jr-t-cancel').addEventListener('click', function () {
      editingTarget = false; renderWeek();
    });
  }

  function bindTargetButtons() {
    var e = el('jr-edit');
    if (e) e.addEventListener('click', function () { editingTarget = true; renderTargetForm(); });
    var u = el('jr-use');
    if (u) u.addEventListener('click', function () {
      var s = data.suggestion || {};
      saveTarget({ lessons: s.lessons, mocks: s.mocks, minutes: s.minutes });
    });
  }

  function saveTarget(body) {
    fetch('/api/hsa/weekly-target', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
      .then(function (res) {
        if (!res.ok) { alert(res.d.error || 'Không lưu được mục tiêu.'); return; }
        data.target = res.d.target;
        data.week = res.d.week;
        editingTarget = false;
        if (window.__apiGetBust) window.__apiGetBust(API + '?days=30');
        renderWeek();
      })
      .catch(function () { alert('Mất kết nối, thử lại nhé.'); });
  }

  /* ── Nhật ký hôm nay ──────────────────────────────────────────────── */
  function renderToday() {
    var box = el('jr-today');
    if (!box || !data) return;
    var t = data.today || {};
    var diffs = data.difficulties || [];
    box.innerHTML = '<div class="jr-form">'
      + '<div class="jr-row">'
        + '<label class="jr-f jr-f--sm"><span>Số phút</span>'
          + '<input type="number" id="jr-minutes" min="0" max="960" placeholder="45" value="'
          + (t.minutes != null ? t.minutes : '') + '"></label>'
        + '<label class="jr-f"><span>Chủ đề</span>'
          + '<input type="text" id="jr-topic" list="jr-topics" placeholder="Hình học" value="'
          + esc(t.topic || '') + '"></label>'
      + '</div>'
      + '<label class="jr-f"><span>Hôm nay học gì</span>'
        + '<input type="text" id="jr-what" maxlength="200" placeholder="Ôn hệ thức lượng trong tam giác" value="'
        + esc(t.what || '') + '"></label>'
      + '<div class="jr-f"><span>Thấy thế nào</span><div class="jr-diffs" id="jr-diffs">'
        + diffs.map(function (d) {
          return '<button type="button" class="jr-diff' + (t.difficulty === d.value ? ' active' : '')
            + '" data-v="' + d.value + '" aria-pressed="' + (t.difficulty === d.value) + '">'
            + esc(d.label) + '</button>';
        }).join('') + '</div></div>'
      + '<label class="jr-f"><span>Vướng ở đâu (trợ lý AI đọc phần này để tư vấn sát hơn)</span>'
        + '<textarea id="jr-note" rows="2" maxlength="500" placeholder="Vẫn nhầm khi nào dùng sin, khi nào dùng cos">'
        + esc(t.note || '') + '</textarea></label>'
      + '<div class="jr-actions">'
        + '<button type="button" class="jr-btn" id="jr-save">'
          + (data.today ? 'Cập nhật nhật ký' : 'Lưu nhật ký hôm nay') + '</button>'
        + '<span class="jr-msg" id="jr-msg" role="status"></span>'
      + '</div></div>';

    var diffBox = el('jr-diffs');
    if (diffBox) {
      diffBox.addEventListener('click', function (e) {
        var b = e.target.closest && e.target.closest('.jr-diff');
        if (!b) return;
        var on = b.getAttribute('aria-pressed') !== 'true';
        Array.prototype.forEach.call(diffBox.querySelectorAll('.jr-diff'), function (x) {
          x.classList.remove('active'); x.setAttribute('aria-pressed', 'false');
        });
        if (on) { b.classList.add('active'); b.setAttribute('aria-pressed', 'true'); }
      });
    }
    el('jr-save').addEventListener('click', saveToday);
  }

  function saveToday() {
    var picked = document.querySelector('#jr-diffs .jr-diff.active');
    var body = {
      minutes: el('jr-minutes').value,
      topic: el('jr-topic').value,
      what: el('jr-what').value,
      note: el('jr-note').value,
      difficulty: picked ? picked.getAttribute('data-v') : ''
    };
    var btn = el('jr-save'), msg = el('jr-msg');
    btn.disabled = true;
    fetch(API, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
      .then(function (res) {
        btn.disabled = false;
        if (!res.ok) { msg.textContent = res.d.error || 'Không lưu được.'; msg.className = 'jr-msg is-err'; return; }
        msg.textContent = 'Đã lưu ✓'; msg.className = 'jr-msg is-ok';
        data.today = res.d.log;
        data.week = res.d.week;
        // Thay bản ghi hôm nay trong danh sách, hoặc chèn lên đầu nếu mới.
        data.recent = (data.recent || []).filter(function (l) { return l.date !== res.d.log.date; });
        data.recent.unshift(res.d.log);
        if (window.__apiGetBust) window.__apiGetBust(API + '?days=30');
        renderWeek();
        renderHistory();
        setTimeout(function () { msg.textContent = ''; }, 2600);
      })
      .catch(function () {
        btn.disabled = false;
        msg.textContent = 'Mất kết nối, thử lại nhé.'; msg.className = 'jr-msg is-err';
      });
  }

  /* ── Nhật ký 30 ngày ──────────────────────────────────────────────── */
  function renderHistory() {
    var box = el('jr-history');
    var tgl = el('jr-toggle');
    if (!box || !data) return;
    var list = data.recent || [];
    if (tgl) {
      tgl.textContent = showHistory
        ? 'Ẩn nhật ký'
        : ('Xem nhật ký ' + list.length + ' ngày gần đây');
      tgl.setAttribute('aria-expanded', showHistory ? 'true' : 'false');
      tgl.hidden = !list.length;
    }
    box.hidden = !showHistory;
    if (!showHistory) return;
    box.innerHTML = list.map(function (l) {
      return '<div class="jr-item">'
        + '<span class="jr-item-d">' + viDate(l.date) + '</span>'
        + '<span class="jr-item-b">'
          + '<span class="jr-item-t">' + esc(l.what || l.topic || 'Có học') + '</span>'
          + '<span class="jr-item-m">'
            + (l.minutes != null ? l.minutes + ' phút' : '')
            + (l.topic && l.what ? ' · ' + esc(l.topic) : '')
            + (l.difficultyLabel ? ' · ' + esc(l.difficultyLabel) : '')
          + '</span>'
          + (l.note ? '<span class="jr-item-n">' + esc(l.note) + '</span>' : '')
        + '</span></div>';
    }).join('');
  }

  /* ── Nạp ──────────────────────────────────────────────────────────── */
  function render() {
    if (editingTarget) renderTargetForm(); else renderWeek();
    renderToday();
    renderHistory();
  }

  function load() {
    if (!el('jr-week')) return;
    var url = API + '?days=30';
    var p = window.__apiGet ? window.__apiGet(url, 30000)
      : fetch(url).then(function (r) { return r.ok ? r.json() : null; });
    p.then(function (d) { if (d) { data = d; render(); } })
      .catch(function () { /* giữ khối "đang tải" thay vì hiện số sai */ });
  }

  function init() {
    if (!el('jr-week')) return;
    var tgl = el('jr-toggle');
    if (tgl) tgl.addEventListener('click', function () {
      showHistory = !showHistory; renderHistory();
    });
    // Danh sách chủ đề cho ô gợi ý — lấy từ chính bản đồ năng lực, khỏi cứng hoá.
    if (window.__apiGet) {
      window.__apiGet('/api/hsa/competency', 60000).then(function (c) {
        var dl = el('jr-topics');
        if (!dl || !c || !c.topics) return;
        var seen = {};
        dl.innerHTML = c.topics.filter(function (t) {
          if (seen[t.topic]) return false; seen[t.topic] = 1; return true;
        }).map(function (t) { return '<option value="' + esc(t.topic) + '">'; }).join('');
      }).catch(function () {});
    }
    load();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();


/* ═══════════════════════════════════════════════════════
   KẾ HOẠCH HỌC CÓ LỊCH  (/api/hsa/study-plan)
   ═══════════════════════════════════════════════════════
   Vế System-Guided: học viên tư duy và làm bài, còn lịch thì hệ thống lo.
   Hiện ở hai nơi, cùng một nguồn dữ liệu:
     · Bảng điều khiển — VIỆC CỦA TUẦN NÀY, ngay trên mục tiêu tuần
     · Trang Kế hoạch  — toàn bộ lịch tới ngày thi

   BA ĐIỀU KHÔNG ĐƯỢC LÀM SAI:
   · "Đang chậm N việc" phải hiện, không được giấu. Lịch tự dồn nên nhìn lúc
     nào cũng đúng hạn; con số chậm là thứ duy nhất nói thật.
   · Mục nào cũng phải nói được VÌ SAO nó ở đây khi hệ thống có lý do.
   · Không đủ thời gian thì nói rõ bỏ bao nhiêu bài và bỏ bài nào.
   ═══════════════════════════════════════════════════════ */
(function () {
  var API = '/api/hsa/study-plan';
  var data = null;
  var busy = false;
  //: Số tuần mở sẵn ở trang Kế hoạch. Trải hết 29 tuần × 5 việc ra một trang
  //  dài 7500px thì không ai đọc; những tuần xa rút thành một dòng, bấm mới mở.
  var EXPAND_WEEKS = 6;
  var expanded = {};

  function esc(s) {
    return window.forumShared ? window.forumShared.escHtml(String(s)) : String(s == null ? '' : s);
  }
  function el(id) { return document.getElementById(id); }
  function viWeek(iso) {
    var p = String(iso).split('-');
    return p.length === 3 ? (p[2] + '/' + p[1]) : iso;
  }

  // Dùng bộ icon SVG của dự án (icons.js) chứ không dùng emoji: emoji lệ thuộc
  // font hệ điều hành — trên máy thiếu font nó ra ô vuông, và cỡ/màu không theo
  // được phần còn lại của giao diện.
  var KIND_ICON = { lesson: 'book-open', mock: 'target', review: 'rotate-ccw' };
  var KIND_NAME = { lesson: 'Bài học', mock: 'Thi thử', review: 'Ôn tập' };

  function itemHtml(it) {
    var href = null;
    if (it.kind === 'lesson' && it.course && it.lessonNo) {
      href = '/lesson/' + encodeURIComponent(it.course) + '?lesson=' + it.lessonNo;
    } else if (it.kind === 'mock') {
      href = '/mock';
    }
    var body = '<span class="pl-ic" aria-hidden="true" data-icon="'
      + (KIND_ICON[it.kind] || 'check') + '" data-size="15"></span>'
      + '<span class="pl-body">'
        + '<span class="pl-title">' + esc(it.title || KIND_NAME[it.kind]) + '</span>'
        + '<span class="pl-meta">' + esc(KIND_NAME[it.kind] || it.kind)
          + (it.topic ? ' · ' + esc(it.topic) : '')
          + (it.lessonNo ? ' · Bài ' + it.lessonNo : '') + '</span>'
        + (it.reason ? '<span class="pl-why">' + esc(it.reason) + '</span>' : '')
      + '</span>';

    var main = href
      ? '<a class="pl-go" href="' + href + '">' + body + '</a>'
      : '<span class="pl-go is-flat">' + body + '</span>';

    var act = it.state === 'done'
      ? '<span class="pl-state is-done">Xong ✓</span>'
      : (it.state === 'skipped'
        ? '<button type="button" class="pl-skip" data-id="' + it.id + '" data-to="todo">Bỏ qua ✕ · hoàn lại</button>'
        : '<button type="button" class="pl-skip" data-id="' + it.id + '" data-to="skipped"'
          + ' aria-label="Bỏ qua mục này">Bỏ qua</button>');

    return '<div class="pl-item is-' + esc(it.state) + '">' + main + act + '</div>';
  }

  function weekHtml(w, showHead) {
    return (showHead
      ? '<div class="pl-week-hd">'
        + '<span class="pl-week-t">' + (w.isThisWeek ? 'Tuần này' : 'Tuần ' + viWeek(w.weekStart)) + '</span>'
        + '<span class="pl-week-n">' + w.done + '/' + w.total + '</span>'
        + '</div>'
      : '')
      + '<div class="pl-items">' + w.items.map(itemHtml).join('') + '</div>';
  }

  /* ── Khối trên Bảng điều khiển: chỉ tuần này ── */
  function renderThisWeek() {
    var box = el('pl-thisweek');
    if (!box || !data) return;
    if (!data.hasPlan) {
      box.innerHTML = '<div class="pl-empty">'
        + '<p>' + esc(data.hint || '') + '</p>'
        + '<button type="button" class="jr-btn" id="pl-gen">Lập kế hoạch</button>'
        + '</div>';
      bindGen();
      return;
    }
    var w = (data.weeks || [])[0];
    box.innerHTML = lagHtml()
      + (w ? weekHtml(w, false) : '<div class="pl-empty"><p>Tuần này chưa có việc nào.</p></div>')
      + '<div class="pl-foot">'
        + '<a class="pl-more" href="#" id="pl-open">Xem cả lịch tới ngày thi →</a>'
        + '<button type="button" class="pl-regen" id="pl-gen">Xếp lại lịch</button>'
      + '</div>';
    bindItems(box);
    bindGen();
    if (window.mountIcons) mountIcons(box);
    var open = el('pl-open');
    if (open) open.addEventListener('click', function (e) {
      e.preventDefault();
      if (typeof window.navigate === 'function') window.navigate('plan');
    });
  }

  function lagHtml() {
    if (!data.lag) return '';
    // Lịch tự dồn nên nhìn lúc nào cũng đúng hạn — con số này là thứ duy nhất
    // nói thật rằng học viên đang chậm.
    return '<div class="pl-lag">Đang chậm <b>' + data.lag + ' việc</b> so với lịch. '
      + 'Những việc đó đã được dồn vào tuần này.</div>';
  }

  /* ── Trang Kế hoạch: toàn bộ lịch ── */
  function renderPage() {
    var box = el('pl-all');
    if (!box || !data) return;
    if (!data.hasPlan) {
      box.innerHTML = '<div class="pl-empty"><p>' + esc(data.hint || '') + '</p>'
        + '<button type="button" class="jr-btn" id="pl-gen2">Lập kế hoạch</button></div>';
      var g = el('pl-gen2');
      if (g) g.addEventListener('click', regenerate);
      return;
    }
    var b = data.basis || {};
    var weakTxt = (b.weakTopics && b.weakTopics.length)
      ? ', và chen thêm buổi ôn cho chủ đề bạn đang yếu (' + b.weakTopics.map(esc).join(', ') + ')'
      // Chưa đo được chủ đề nào thì ĐỪNG hứa chen buổi ôn — lịch sẽ không có
      // mục nào như vậy, và câu chữ hứa suông là thứ phá tin cậy nhanh nhất.
      : '. Chưa đủ dữ liệu để chấm chủ đề nào, nên chưa chen buổi ôn — học thêm '
        + 'vài bài là hệ thống tự thêm vào lịch';
    var head = '<div class="pl-sum">'
      + '<div class="pl-sum-i"><b>' + (b.perWeek || '—') + '</b><span>bài/tuần</span></div>'
      + '<div class="pl-sum-i"><b>' + (b.weeksTotal || '—') + '</b><span>tuần tới kỳ thi</span></div>'
      + '<div class="pl-sum-i"><b>' + (data.totals ? data.totals.done : 0) + '/'
        + (data.totals ? data.totals.all : 0) + '</b><span>việc đã xong</span></div>'
      + '</div>'
      + '<p class="pl-note">'
        + 'Lịch xếp theo thứ tự giáo trình, ba hợp phần xen kẽ nhau' + weakTxt
        + '. Hai tuần cuối chỉ luyện đề, không nạp bài mới.'
        + (b.usedTarget ? ' Số bài/tuần lấy theo mục tiêu bạn tự đặt.'
                        : ' Số bài/tuần do hệ thống tính từ ngày thi và sức học bạn khai.')
      + '</p>';

    if (b.lessonsDropped) {
      // Không đủ thời gian thì NÓI THẲNG, và nói bỏ bài nào — im lặng cắt bớt
      // là để học viên tưởng mình đang kịp cho tới sát ngày thi.
      head += '<div class="pl-lag is-cut">Lịch này <b>bỏ qua ' + b.lessonsDropped + ' bài</b> '
        + 'vì không đủ thời gian tới ngày thi. Ưu tiên bỏ bài của chủ đề bạn đang mạnh'
        + ((b.droppedSample && b.droppedSample.length)
            ? ', ví dụ: ' + b.droppedSample.map(esc).join(', ') + '…' : '.')
        + ' Muốn học đủ thì tăng số phút mỗi ngày ở khảo sát rồi xếp lại lịch.</div>';
    }

    box.innerHTML = head + lagHtml()
      + (data.weeks || []).map(function (w, i) {
        var open = i < EXPAND_WEEKS || expanded[w.weekStart];
        if (open) {
          return '<div class="pl-week' + (w.isThisWeek ? ' is-now' : '') + '">'
            + weekHtml(w, true) + '</div>';
        }
        var kinds = {};
        w.items.forEach(function (it) { kinds[it.kind] = (kinds[it.kind] || 0) + 1; });
        var sum = [];
        if (kinds.lesson) sum.push(kinds.lesson + ' bài');
        if (kinds.review) sum.push(kinds.review + ' buổi ôn');
        if (kinds.mock) sum.push(kinds.mock + ' đề');
        return '<button type="button" class="pl-week-mini" data-week="' + esc(w.weekStart) + '">'
          + '<span class="pl-week-t">Tuần ' + viWeek(w.weekStart) + '</span>'
          + '<span class="pl-week-sum">' + sum.join(' · ') + '</span>'
          + '<span class="pl-week-x">Mở</span>'
          + '</button>';
      }).join('')
      + '<div class="pl-foot"><button type="button" class="pl-regen" id="pl-gen2">Xếp lại lịch</button></div>';
    bindItems(box);
    Array.prototype.forEach.call(box.querySelectorAll('.pl-week-mini'), function (b) {
      b.addEventListener('click', function () {
        expanded[b.getAttribute('data-week')] = true;
        renderPage();
      });
    });
    if (window.mountIcons) mountIcons(box);
    var g2 = el('pl-gen2');
    if (g2) g2.addEventListener('click', regenerate);
  }

  /* ── Thao tác ── */
  function bindGen() {
    var g = el('pl-gen');
    if (g) g.addEventListener('click', regenerate);
  }

  function regenerate() {
    if (busy) return;
    busy = true;
    document.querySelectorAll('#pl-gen, #pl-gen2').forEach(function (b) {
      b.disabled = true; b.textContent = 'Đang xếp lịch…';
    });
    fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
      .then(function (res) {
        busy = false;
        if (!res.ok) { alert(res.d.error || 'Không xếp được lịch.'); render(); return; }
        data = res.d.plan;
        if (window.__apiGetBust) { window.__apiGetBust(API); window.__apiGetBust(API + '?all=1'); }
        render();
      })
      .catch(function () { busy = false; render(); });
  }

  function bindItems(box) {
    Array.prototype.forEach.call(box.querySelectorAll('.pl-skip'), function (b) {
      b.addEventListener('click', function () {
        b.disabled = true;
        fetch(API + '/items/' + b.getAttribute('data-id'), {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: b.getAttribute('data-to') })
        })
          .then(function (r) { return r.ok ? r.json() : null; })
          .then(function (d) {
            if (!d) { b.disabled = false; return; }
            data = d.plan;
            if (window.__apiGetBust) { window.__apiGetBust(API); window.__apiGetBust(API + '?all=1'); }
            render();
          })
          .catch(function () { b.disabled = false; });
      });
    });
  }

  function render() { renderThisWeek(); renderPage(); }

  function load(force) {
    if (!el('pl-thisweek') && !el('pl-all')) return;
    // Trang Kế hoạch cần cả lịch; Bảng điều khiển chỉ cần tuần này. Gọi bản đầy
    // đủ một lần rồi dùng chung, đỡ một lượt tới máy chủ (mỗi lượt ~245ms).
    var url = API + '?all=1';
    var p = window.__apiGet ? window.__apiGet(url, force ? 0 : 30000)
      : fetch(url).then(function (r) { return r.ok ? r.json() : null; });
    p.then(function (d) { if (d) { data = d; render(); } }).catch(function () {});
  }

  var _origNavigatePlan = window.navigate;
  window.navigate = function (page) {
    _origNavigatePlan(page);
    if (page === 'plan') load(false);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { load(false); });
  } else {
    load(false);
  }
})();


/* ═══════════════════════════════════════════════════════
   KHU GIẢNG DẠY  (/api/teach/*)
   ═══════════════════════════════════════════════════════
   Bảng điều khiển lớp cho giảng viên. Đây là chỗ năm trụ cột đã dựng trả công:
   mọi con số per-học-viên đã có sẵn, ở đây chỉ gom theo lớp.

   BA ĐIỀU CỐ Ý:
   · KHÔNG xếp hạng học viên trong lớp. Bảng sắp theo "cần chú ý trước", nhưng
     không có cột hạng — bảng xếp hạng nội bộ làm hỏng động lực của đúng những
     em cần giữ lại nhất, mà giảng viên vẫn đọc được thứ tự từ số liệu.
   · Mỗi cảnh báo là một câu NÓI ĐƯỢC LÀM GÌ TIẾP. "Nam đang yếu" thì không làm
     gì được; "Nam 9 ngày không mở bài, chưa làm đề nào" thì gọi điện được.
   · Hồ sơ một học viên dùng lại ĐÚNG những con số học viên tự thấy. Giảng viên
     và học viên nhìn hai số khác nhau cho cùng một chủ đề là hỏng buổi tư vấn.
   ═══════════════════════════════════════════════════════ */
(function () {
  var API = '/api/teach';
  var classes = null;
  var report = null;
  var openStudent = null;

  function esc(s) {
    return window.forumShared ? window.forumShared.escHtml(String(s)) : String(s == null ? '' : s);
  }
  function el(id) { return document.getElementById(id); }
  function viDate(iso) {
    if (!iso) return '—';
    var p = String(iso).slice(0, 10).split('-');
    return p.length === 3 ? (p[2] + '/' + p[1]) : iso;
  }
  function lvl(m) {
    if (m == null) return 'none';
    if (m >= 80) return 'l4'; if (m >= 60) return 'l3';
    if (m >= 40) return 'l2'; return 'l1';
  }

  /* ── Danh sách lớp ── */
  function renderClasses() {
    var box = el('tc-classes');
    if (!box) return;
    var list = (classes && classes.classes) || [];
    if (!list.length) {
      box.innerHTML = '<div class="tc-empty">Bạn chưa phụ trách lớp nào. '
        + 'Quản trị viên tạo lớp và gán giảng viên ở trang Quản trị.</div>';
      return;
    }
    box.innerHTML = list.map(function (c) {
      return '<button type="button" class="tc-class' + (report && report.class.id === c.id ? ' active' : '')
        + '" data-id="' + c.id + '">'
        + '<span class="tc-class-hd">'
          + (c.code ? '<span class="tc-code">' + esc(c.code) + '</span>' : '')
          + '<span class="tc-class-n">' + esc(c.name) + '</span>'
        + '</span>'
        + '<span class="tc-class-m">' + (c.schedule ? esc(c.schedule) + ' · ' : '')
          + c.members + (c.capacity ? '/' + c.capacity : '') + ' học viên'
          + (c.examDate ? ' · thi ' + viDate(c.examDate) : '') + '</span>'
        + '</button>';
    }).join('');
    Array.prototype.forEach.call(box.querySelectorAll('.tc-class'), function (b) {
      b.addEventListener('click', function () { loadClass(b.getAttribute('data-id')); });
    });
  }

  /* ── Báo cáo lớp ── */
  function tile(num, label, warn) {
    return '<div class="tc-tile' + (warn && num > 0 ? ' is-warn' : '') + '">'
      + '<b>' + num + '</b><span>' + esc(label) + '</span></div>';
  }

  function renderReport() {
    var box = el('tc-report');
    if (!box) return;
    if (!report) {
      box.innerHTML = '<div class="tc-empty">Chọn một lớp để xem báo cáo.</div>';
      return;
    }
    var s = report.summary, c = report.class;

    var alerts = report.students.filter(function (st) { return st.alerts.length; });
    var alertHtml = alerts.length
      ? alerts.map(function (st) {
        return '<div class="tc-alert">'
          + '<button type="button" class="tc-alert-n" data-uid="' + st.userId + '">'
            + esc(st.name) + '</button>'
          + '<span class="tc-alert-t">' + st.alerts.map(function (a) {
              return '<i class="tc-dot is-' + a.level + '"></i>' + esc(a.text);
            }).join(' ') + '</span></div>';
      }).join('')
      : '<div class="tc-ok">Không có học viên nào cần chú ý ngay lúc này.</div>';

    var weak = (s.weakestTopics || []).length
      ? s.weakestTopics.map(function (t) {
        return '<span class="tc-weak is-' + lvl(t.avg) + '">' + esc(t.topic)
          + ' <b>' + t.avg + '</b>'
          + '<i>' + t.measuredStudents + '/' + t.ofStudents + ' học viên đã đo</i></span>';
      }).join('')
      : '<span class="tc-muted">Chưa đủ dữ liệu để chấm chủ đề nào của lớp.</span>';

    box.innerHTML =
      '<div class="tc-hd">'
        + '<div><h3>' + esc(c.name) + '</h3>'
        + '<p class="tc-sub">' + (c.code ? esc(c.code) + ' · ' : '')
          + (c.courseTitle ? esc(c.courseTitle) + ' · ' : '')
          + (c.schedule ? esc(c.schedule) : 'chưa đặt lịch')
          + (c.examDate ? ' · kỳ thi ' + viDate(c.examDate) : '') + '</p></div>'
        + (c.meetingUrl ? '<a class="tc-link" href="' + esc(c.meetingUrl)
            + '" target="_blank" rel="noopener">Vào phòng học →</a>' : '')
        /* Lối vào sổ buổi học & điểm danh (30/08/2026). Trước dòng này màn hình
           điểm danh KHÔNG được liên kết từ bất kỳ đâu — giảng viên chỉ tới được
           nếu gõ tay đường dẫn kèm đúng id lớp. Một tính năng không có lối vào
           thì bằng không có tính năng, mà mã vẫn phải bảo trì.
           Đặt ở đây chứ không phải ở danh sách lớp bên trái vì mỗi lớp bên đó
           là một <button>, mà lồng <a> trong <button> là HTML không hợp lệ. */
        + '<a class="tc-link" href="/giang-day/buoi-hoc/' + c.id + '">'
          + 'Sổ buổi học &amp; điểm danh →</a>'
      + '</div>'
      + '<div class="tc-tiles">'
        + tile(s.students, 'học viên')
        + tile(s.avgProgress + '%', 'tiến độ trung bình')
        + tile(s.atRisk, 'cần chú ý ngay', true)
        + tile(s.noMock, 'chưa làm đề nào', true)
        + tile(s.idle, 'nghỉ từ ' + s.idleDays + ' ngày', true)
        + tile(s.behind, 'chậm từ ' + s.lagItems + ' bài', true)
      + '</div>'
      + '<div class="tc-sec"><div class="tc-sec-t">Cần chú ý</div>' + alertHtml + '</div>'
      + '<div class="tc-sec"><div class="tc-sec-t">Chủ đề cả lớp đang yếu</div>'
        + '<div class="tc-weaks">' + weak + '</div></div>'
      + '<div class="tc-sec"><div class="tc-sec-t">Học viên ('
        + report.students.length + ')</div>' + tableHtml() + '</div>';

    Array.prototype.forEach.call(box.querySelectorAll('[data-uid]'), function (b) {
      b.addEventListener('click', function () { loadStudent(b.getAttribute('data-uid')); });
    });
  }

  function tableHtml() {
    // Sắp "cần chú ý trước" rồi tới tiến độ thấp. KHÔNG có cột hạng.
    var rows = report.students.slice().sort(function (a, b) {
      var wa = a.alerts.filter(function (x) { return x.level === 'high'; }).length;
      var wb = b.alerts.filter(function (x) { return x.level === 'high'; }).length;
      if (wa !== wb) return wb - wa;
      if (a.alerts.length !== b.alerts.length) return b.alerts.length - a.alerts.length;
      return a.progressPct - b.progressPct;
    });
    return '<div class="tc-tbl-wrap"><table class="tc-tbl">'
      + '<thead><tr><th>Học viên</th><th>Tiến độ</th><th>Chuỗi</th>'
      + '<th>Hoạt động</th><th>Thi thử</th><th>Chậm</th><th>Chủ đề yếu nhất</th><th></th></tr></thead>'
      + '<tbody>' + rows.map(function (st) {
        var idle = st.idleDays == null ? 'chưa học'
          : (st.idleDays === 0 ? 'hôm nay' : st.idleDays + ' ngày trước');
        var mock = st.mockCount
          ? st.lastMockPct + '%' + (st.mockTrend != null
              ? ' <i class="tc-trend is-' + (st.mockTrend >= 0 ? 'up' : 'down') + '">'
                + (st.mockTrend >= 0 ? '+' : '') + st.mockTrend + '</i>' : '')
          : '<span class="tc-muted">chưa thi</span>';
        var weak = st.weakest.length
          ? st.weakest.map(function (w) {
              return '<span class="tc-chip is-' + lvl(w.mastery) + '">' + esc(w.topic)
                + ' ' + w.mastery + '</span>';
            }).join('')
          : '<span class="tc-muted">chưa đủ dữ liệu</span>';
        return '<tr' + (st.left ? ' class="is-left"' : '') + '>'
          + '<td><b>' + esc(st.name) + '</b>' + (st.left ? ' <i>(đã rời lớp)</i>' : '') + '</td>'
          + '<td class="tc-num">' + st.lessonsDone + '/' + st.lessonsTotal
            + ' <i>' + st.progressPct + '%</i></td>'
          + '<td class="tc-num">' + st.streak + '</td>'
          + '<td class="' + (st.idleDays == null || st.idleDays >= 7 ? 'tc-bad' : '') + '">'
            + idle + '</td>'
          + '<td class="tc-num">' + mock + '</td>'
          + '<td class="tc-num' + (st.lag >= 5 ? ' tc-bad' : '') + '">' + st.lag + '</td>'
          + '<td>' + weak + '</td>'
          + '<td><button type="button" class="tc-view" data-uid="' + st.userId + '">Xem</button></td>'
          + '</tr>';
      }).join('') + '</tbody></table></div>';
  }

  /* ── Hồ sơ một học viên ── */
  function renderStudent(d) {
    var box = el('tc-student');
    if (!box) return;
    if (!d) { box.hidden = true; box.innerHTML = ''; return; }
    box.hidden = false;
    var u = d.user, g = d.goals || {};
    var measured = (d.competency.topics || []).filter(function (t) { return t.mastery != null; });
    var map = measured.length
      ? measured.sort(function (a, b) { return a.mastery - b.mastery; }).map(function (t) {
          return '<span class="tc-chip is-' + lvl(t.mastery) + '">' + esc(t.topic)
            + ' <b>' + t.mastery + '</b></span>';
        }).join('')
      : '<span class="tc-muted">Chưa đủ dữ liệu để chấm chủ đề nào ('
        + d.competency.minActivities + ' hoạt động/chủ đề mới đủ).</span>';

    var book = (d.gradebook.rows || []).slice(0, 8).map(function (r) {
      return '<div class="tc-row"><span>' + esc(r.kindLabel) + '</span>'
        + '<span class="tc-row-t">' + esc(r.label) + '</span>'
        + '<span class="tc-num">' + r.pct + '%</span>'
        + '<span class="tc-muted">' + viDate(r.at) + '</span></div>';
    }).join('') || '<span class="tc-muted">Chưa có hoạt động nào được chấm.</span>';

    var jr = (d.journal || []).slice(0, 5).map(function (l) {
      return '<div class="tc-row"><span>' + viDate(l.date) + '</span>'
        + '<span class="tc-row-t">' + esc(l.what || l.topic || 'Có học') + '</span>'
        + '<span class="tc-muted">' + (l.minutes != null ? l.minutes + ph() : '')
          + (l.difficultyLabel ? ' · ' + esc(l.difficultyLabel) : '') + '</span>'
        + (l.note ? '<span class="tc-note">' + esc(l.note) + '</span>' : '') + '</div>';
    }).join('') || '<span class="tc-muted">Học viên chưa ghi nhật ký ngày nào.</span>';

    var wk = (d.plan.weeks || [])[0];
    // Cắt còn 6 dòng: học viên chưa bắt đầu thì cả tuần bị dồn 14 việc, đọc hết
    // trong một khung hẹp là vô ích — giảng viên chỉ cần biết đang có gì và bao nhiêu.
    var PLAN_SHOWN = 6;
    var plan = wk
      ? wk.items.slice(0, PLAN_SHOWN).map(function (i) {
          return '<div class="tc-row is-' + esc(i.state) + '">'
            + '<span>' + (i.state === 'done' ? 'Xong' : (i.state === 'skipped' ? 'Bỏ qua' : 'Chưa')) + '</span>'
            + '<span class="tc-row-t">' + esc(i.title) + '</span></div>';
        }).join('')
        + (wk.items.length > PLAN_SHOWN
            ? '<span class="tc-muted">…và ' + (wk.items.length - PLAN_SHOWN)
              + ' việc nữa trong tuần này.</span>' : '')
      : '<span class="tc-muted">Học viên chưa lập kế hoạch.</span>';

    box.innerHTML = '<div class="tc-st-hd">'
      + '<div><h4>' + esc(u.name) + '</h4>'
      + '<p class="tc-sub">' + esc(u.email) + (u.phone ? ' · ' + esc(u.phone) : '')
        + ' · mục tiêu ' + esc(g.targetScore || 'chưa đặt')
        + (g.daysToExam != null ? ' · còn ' + g.daysToExam + ' ngày' : '') + '</p></div>'
      + '<button type="button" class="tc-close" id="tc-close" aria-label="Đóng hồ sơ">Đóng</button>'
      + '</div>'
      + '<div class="tc-st-grid">'
        + '<div class="tc-st-b"><div class="tc-sec-t">Chủ đề đã đo được ('
          + measured.length + '/' + d.competency.topics.length + ')</div>'
          + '<div class="tc-weaks">' + map + '</div></div>'
        + '<div class="tc-st-b"><div class="tc-sec-t">Kế hoạch tuần này'
          + (d.plan.lag ? ' — chậm ' + d.plan.lag + ' việc' : '') + '</div>' + plan + '</div>'
        + '<div class="tc-st-b"><div class="tc-sec-t">Hoạt động gần đây</div>' + book + '</div>'
        + '<div class="tc-st-b"><div class="tc-sec-t">Nhật ký học viên tự ghi</div>' + jr
          + '<p class="tc-priv">Đây là phần học viên tự viết cho mình. Dùng để tư vấn, '
          + 'đừng đọc lại trước lớp.</p></div>'
      + '</div>';
    var cl = el('tc-close');
    if (cl) cl.addEventListener('click', function () { openStudent = null; renderStudent(null); });
    box.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function ph() { return ' phút'; }

  /* ── Nạp ── */
  function loadClasses() {
    fetch(API + '/classes')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d) return;
        classes = d;
        renderClasses();
        var list = d.classes || [];
        if (list.length === 1 && !report) loadClass(list[0].id);
      })
      .catch(function () {});
  }

  function loadClass(id) {
    var box = el('tc-report');
    if (box) box.innerHTML = '<div class="tc-empty">Đang tính báo cáo lớp…</div>';
    renderStudent(null);
    fetch(API + '/classes/' + id)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d) { if (box) box.innerHTML = '<div class="tc-empty">Không tải được lớp này.</div>'; return; }
        report = d;
        renderClasses();
        renderReport();
      })
      .catch(function () {});
  }

  function loadStudent(uid) {
    if (!report) return;
    var box = el('tc-student');
    if (box) { box.hidden = false; box.innerHTML = '<div class="tc-empty">Đang mở hồ sơ học viên…</div>'; }
    openStudent = uid;
    fetch(API + '/classes/' + report.class.id + '/students/' + uid)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (openStudent !== uid) return;      // người dùng đã bấm sang em khác
        if (!d) { renderStudent(null); return; }
        renderStudent(d);
      })
      .catch(function () { renderStudent(null); });
  }

  var _origNavigateTeach = window.navigate;
  window.navigate = function (page) {
    _origNavigateTeach(page);
    if (page === 'teach' && !classes) loadClasses();
  };

  // Nút điều hướng chỉ hiện với giảng viên/quản trị viên. main.js đã nạp
  // /api/user và đặt window.__currentUser; chờ nó rồi mới quyết định.
  function gate() {
    var u = window.__currentUser;
    if (!u) return false;
    var btn = el('nav-teach');
    var ok = (u.role === 'Giảng viên' || u.role === 'admin');
    if (btn) btn.style.display = ok ? '' : 'none';
    if (ok && !classes) loadClasses();
    return true;
  }
  var tries = 0;
  var timer = setInterval(function () {
    if (gate() || ++tries > 40) clearInterval(timer);
  }, 250);
})();
