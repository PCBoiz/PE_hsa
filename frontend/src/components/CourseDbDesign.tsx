'use client';

// Port course_db_design.html — trang chi tiết 3 khóa DB Design (db_design /
// db_design_tc / db_design_nc dùng CHUNG markup; course_db_design.js đọc
// data-course trên <body> để render roadmap đúng khóa — giữ nguyên cơ chế).
// Jinja server bơm (user_name, enrollment, streak, pct) → fetch API client-side.
import { useEffect, useState } from 'react';

import Chatbot from '@/components/Chatbot';
import LegacyScripts from '@/components/LegacyScripts';
import { apiFetch } from '@/lib/api';

/* eslint-disable @typescript-eslint/no-explicit-any, @next/next/no-img-element */
const W = () => window as any;

export default function CourseDbDesign({ courseId }: { courseId: string }) {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    // body class/data-attr y hệt template gốc: <body class="dark" data-course="...">
    document.body.classList.add('dark');
    document.body.setAttribute('data-course', courseId);
    return () => {
      document.body.removeAttribute('data-course');
    };
  }, [courseId]);

  useEffect(() => {
    (async () => {
      try {
        // apiFetch (không phải fetch tương đối): pe-bridge chưa nạp ở thời điểm này
        const [enrolled, stats, user]: any[] = await Promise.all([
          apiFetch('/api/enrolled').then((r) => (r.ok ? r.json() : [])),
          apiFetch('/api/stats').then((r) => (r.ok ? r.json() : {})),
          apiFetch('/api/user').then((r) => (r.ok ? r.json() : {})),
        ]);
        const enrollment = Array.isArray(enrolled) ? enrolled.find((e: any) => e.id === courseId) : null;
        setData({ enrollment, streak: stats.streakDays || 0, userName: user.name || '—' });
      } catch {
        setData({ enrollment: null, streak: 0, userName: '—' });
      }
    })();
  }, [courseId]);

  if (!data) return null;

  const { enrollment, streak, userName } = data;
  // Jinja: done = min(completed_lessons, 20); pct = round(done*100/20, 1)
  const done = enrollment ? Math.min(enrollment.completedLessons || 0, 20) : 0;
  const pct = done > 0 ? Math.round((done * 100) / 20 * 10) / 10 : 0;

  return (
    <>
      <title>Database Design – Programming EDU</title>
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />

      <div id="main">
        {/* Topbar */}
        <div className="topbar">
          <div className="topbar-left">
            <div className="brand brand-always">
              <div className="brand-title">Programming EDU</div>
            </div>
          </div>
          <nav className="topbar-nav" role="navigation" aria-label="Main navigation">
            <button className="nav-btn" onClick={() => { window.location.href = '/dashboard'; }} aria-label="Dashboard">
              <span className="nav-icon">🏠</span><span>Dashboard</span>
            </button>
            <button className="nav-btn active" aria-label="Khóa học">
              <span className="nav-icon">📖</span><span>Khóa học</span>
            </button>
            <button className="nav-btn" onClick={() => { window.location.href = '/dashboard#roadmap'; }} aria-label="Lộ trình">
              <span className="nav-icon">🗺️</span><span>Lộ trình</span>
            </button>
            <button className="nav-btn" onClick={() => { window.location.href = '/dashboard#skills'; }} aria-label="Kỹ năng">
              <span className="nav-icon">🏅</span><span>Kỹ năng</span>
            </button>
            <button className="nav-btn" onClick={() => { window.location.href = '/dashboard#forum'; }} aria-label="Diễn đàn">
              <span className="nav-icon">💬</span><span>Diễn đàn</span>
            </button>
          </nav>
          <div className="topbar-right">
            <div className="search-wrap">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                placeholder="Tìm kiếm khóa học..."
                onKeyDown={(e) => {
                  const v = e.currentTarget.value.trim();
                  if (e.key === 'Enter' && v) window.location.href = '/dashboard?q=' + encodeURIComponent(v);
                }}
              />
            </div>
            <button className="theme-toggle-btn" id="theme-toggle" onClick={() => W().toggleTheme()} title="Đổi giao diện">🌙</button>
            <div className="bell-wrap" id="bell-wrap">
              <button className="bell-btn" id="bell-btn" onClick={() => W().toggleBellPanel()} aria-haspopup="true" aria-expanded="false" aria-label="Thông báo">
                🔔<span className="bell-dot" id="bell-dot"></span>
              </button>
              <div className="bell-panel" id="bell-panel" role="dialog" aria-label="Thông báo">
                <div className="bell-panel-header">
                  <span className="bell-panel-title">🔔 Thông báo</span>
                  <button className="bell-mark-all" onClick={() => W().markAllBellRead()}>Đánh dấu đã đọc</button>
                </div>
                <div className="bell-panel-body" id="bell-panel-body"></div>
              </div>
            </div>
            <div className="user-chip-wrap" id="user-chip-wrap">
              <div className="user-chip" id="user-chip-btn" onClick={() => W().toggleUserMenu()} aria-haspopup="true" aria-expanded="false">
                <img src="/static/images/avatar.svg" alt="avatar" />
                <span className="chip-name">{userName}</span>
                <span className="dropdown-icon" id="chip-arrow">▾</span>
              </div>
              <div className="user-dropdown" id="user-dropdown" role="menu">
                <div className="user-dropdown-header">
                  <img src="/static/images/avatar.svg" alt="avatar" className="udh-avatar" />
                  <div>
                    <div className="udh-name">{userName}</div>
                    <div className="udh-role">Học viên</div>
                  </div>
                </div>
                <div className="user-dropdown-divider"></div>
                <button className="user-dropdown-item" onClick={() => { window.location.href = '/dashboard'; }} role="menuitem">
                  <span className="udi-icon">🙋</span> Trang của tôi
                </button>
                <button className="user-dropdown-item" onClick={() => { window.location.href = '/dashboard#settings'; }} role="menuitem">
                  <span className="udi-icon">⚙️</span> Cài đặt
                </button>
                <div className="user-dropdown-divider"></div>
                <button className="user-dropdown-item danger" onClick={() => { window.location.href = '/auth/logout'; }} role="menuitem">
                  <span className="udi-icon">🚪</span> Đăng xuất
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <div className="page active" style={{ padding: 0 }}>
          {/* Hero */}
          <div className="cd-hero">
            <div className="cd-hero-content">
              <span className="cd-tag">DATABASE</span>
              <h1 className="cd-hero-title">Database Design</h1>
              <p className="cd-hero-subtitle">ER Mapping, Phụ thuộc hàm &amp; Chuẩn hóa dữ liệu — theo giáo trình Silberschatz</p>
              <div className="cd-meta">
                <div className="cd-meta-item">🕐 <span className="val" id="cd-hero-time">~5 giờ</span></div>
                <div className="cd-meta-item">📖 <span className="val">20</span> bài học</div>
                <div className="cd-meta-item">🎯 <span className="val cd-difficulty-gradient">Cơ bản → Nâng cao</span></div>
              </div>
            </div>
            <div className="cd-hero-visual">🗄️</div>
          </div>

          {/* Body */}
          <div className="cd-body">
            {/* Cột trái */}
            <div className="cd-main-col">
              {/* Block 1: Tổng quan */}
              <div className="cd-block">
                <div className="cd-block-hd">
                  <div className="cd-block-icon">📋</div>
                  <h3>Tổng quan khóa học</h3>
                </div>
                <div className="cd-block-body">
                  <p className="cd-desc">
                    Bạn có ý tưởng một <strong>game shop</strong>, một <strong>mạng xã hội cho gamer</strong>, hay một <strong>app đặt đồ ăn</strong> — nhưng chưa biết <em>&quot;cơ sở dữ liệu&quot; thì thiết kế từ đâu</em>? Khóa học này dành cho bạn.
                    <br /><br />
                    Trong <strong>20 bài</strong> (3 module), bạn sẽ đi từ <em>không biết gì</em> đến <em>tự tin thiết kế</em> một database hoàn chỉnh chạy thật trong dự án của mình. Mỗi bài là một <strong>bài toán thực tế</strong> (game shop, mạng xã hội, app giao đồ ăn) chứ không phải lý thuyết khô khan.
                  </p>
                  <p className="cd-desc" style={{ marginTop: 14 }}>
                    <strong>Sau khóa học, bạn sẽ làm được:</strong>
                  </p>
                  <ul className="cd-outcomes">
                    <li>📐 <strong>Vẽ được sơ đồ ER</strong> cho bất kỳ bài toán nào (game, web, app) chỉ trong vài phút</li>
                    <li>🗄️ <strong>Thiết kế bảng SQL</strong> không thừa không thiếu — không bao giờ bị lỗi <em>&quot;duplicate dữ liệu&quot;</em> hay <em>&quot;mất thông tin khi update&quot;</em></li>
                    <li>🧠 <strong>Giải thích được vì sao</strong> cần tách bảng, thêm khóa ngoại — để tự tin bảo vệ thiết kế trước team/lead</li>
                    <li>📊 <strong>Chuẩn hóa dữ liệu</strong> qua 1NF → BCNF → 3NF với thuật toán tách bảng chuẩn</li>
                    <li>🛡️ <strong>Biết cách đánh đổi</strong> giữa BCNF (chuẩn tuyệt đối) và 3NF (thực tế, performance tốt hơn)</li>
                    <li>🏆 <strong>Hoàn thành Boss Battle</strong> — thiết kế database cho Mạng Xã Hội Gamers từ A-Z (capstone project)</li>
                  </ul>
                  <p className="cd-desc" style={{ marginTop: 14, fontSize: 13, color: '#9CA3AF' }}>
                    💡 <strong>Cách học:</strong> Mỗi bài 4 bước — đọc lý thuyết ngắn gọn → trắc nghiệm kiểm tra hiểu → kéo thả xếp câu SQL → tự code với gợi ý 4 cấp độ. Thực hành ngay trên trình duyệt, không cần cài database.
                  </p>
                </div>
              </div>

              {/* Block 2: Giáo trình */}
              <div className="cd-block">
                <div className="cd-block-hd">
                  <div className="cd-block-icon">📚</div>
                  <h3>Giáo trình</h3>
                  <span style={{ marginLeft: 'auto', fontSize: 12, color: '#9CA3AF' }}>Khóa Cơ bản: 20 bài · 3 module</span>
                </div>
                <div style={{ padding: 0 }}>
                  {/* C2: Course Roadmap Visual — course_db_design.js render vào đây */}
                  <div className="cd-roadmap" id="cd-roadmap" aria-label="Lộ trình khóa học"></div>

                  {/* OLD LIST FALLBACK (ẩn bằng CSS) */}
                  <div className="cd-roadmap-fallback">
                    <div className="cd-module">
                      <div className="cd-module-hd open" onClick={(e) => W().toggleModule(e.currentTarget)}>
                        <div className="cd-module-arrow">▶</div>
                        <div className="cd-module-name">Module 1: ER Model &amp; Mapping</div>
                        <div className="cd-module-meta">7 bài</div>
                      </div>
                      <div className="cd-module-body open">
                        <div className="cd-lesson-list">
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Entity &amp; Primary Key (Bài 1)</div><div className="cd-lesson-num">1</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Composite + Multivalued + Derived (Bài 2)</div><div className="cd-lesson-num">2</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Foreign Key &amp; JOIN (Bài 3)</div><div className="cd-lesson-num">3</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Foreign Key &amp; 1:N (Bài 4)</div><div className="cd-lesson-num">4</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">M:N &amp; Bảng trung gian (Bài 5)</div><div className="cd-lesson-num">5</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Weak Entity &amp; Khóa chính tổng hợp (Bài 6)</div><div className="cd-lesson-num">6</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Mapping ER → Bảng quan hệ (Bài 7)</div><div className="cd-lesson-num">7</div></div>
                        </div>
                      </div>
                    </div>

                    <div className="cd-module">
                      <div className="cd-module-hd" onClick={(e) => W().toggleModule(e.currentTarget)}>
                        <div className="cd-module-arrow">▶</div>
                        <div className="cd-module-name">Module 2: Phụ thuộc hàm &amp; Chuẩn hóa (FD &amp; Normal Forms)</div>
                        <div className="cd-module-meta">7 bài</div>
                      </div>
                      <div className="cd-module-body">
                        <div className="cd-lesson-list">
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Redundancy &amp; Phụ thuộc hàm (FD) (Bài 8)</div><div className="cd-lesson-num">8</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Dạng chuẩn 1 (1NF) — Nguyên tử hóa (Bài 9)</div><div className="cd-lesson-num">9</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Dạng chuẩn 2 (2NF) — Phụ thuộc đầy đủ (Bài 10)</div><div className="cd-lesson-num">10</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Dạng chuẩn 3 (3NF) — Phụ thuộc bắc cầu (Bài 11)</div><div className="cd-lesson-num">11</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Dạng chuẩn BCNF &amp; Phân rã Phi tổn thất (Bài 12)</div><div className="cd-lesson-num">12</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Dạng chuẩn 4 (4NF) — Phụ thuộc đa trị (Bài 13)</div><div className="cd-lesson-num">13</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Boss Battle — Mạng Xã Hội Gamers (Bài 14)</div><div className="cd-lesson-num">14</div></div>
                        </div>
                      </div>
                    </div>

                    <div className="cd-module">
                      <div className="cd-module-hd" onClick={(e) => W().toggleModule(e.currentTarget)}>
                        <div className="cd-module-arrow">▶</div>
                        <div className="cd-module-name">Module 3: Application Design</div>
                        <div className="cd-module-meta">6 bài</div>
                      </div>
                      <div className="cd-module-body">
                        <div className="cd-lesson-list">
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">JSON trong Relational DB (Bài 15)</div><div className="cd-lesson-num">15</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Spatial Data &amp; Truy vấn tọa độ (Bài 16)</div><div className="cd-lesson-num">16</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">ORM (Django) — Ánh xạ Lớp ↔ Bảng (Bài 17)</div><div className="cd-lesson-num">17</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Web Services — REST/AJAX (Bài 18)</div><div className="cd-lesson-num">18</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">SQL Injection — Lỗ hổng chết người (Bài 19)</div><div className="cd-lesson-num">19</div></div>
                          <div className="cd-lesson locked"><div className="cd-lesson-icon">○</div><div className="cd-lesson-title">Password Security — Salt &amp; Hashing (Bài 20)</div><div className="cd-lesson-num">20</div></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Block 3: Yêu cầu */}
              <div className="cd-block">
                <div className="cd-block-hd">
                  <div className="cd-block-icon">📌</div>
                  <h3>Yêu cầu</h3>
                </div>
                <div className="cd-block-body">
                  <ul className="cd-req-list">
                    <li data-prereq="sql">
                      <span className="cd-req-text">Biết SQL cơ bản: SELECT, FROM, WHERE (tương đương PART 1 — đã học ở &quot;SQL cơ bản&quot;)</span>
                      <span className="cd-req-status" aria-label="Trạng thái"><i className="fas fa-lock"></i></span>
                    </li>
                    <li data-prereq="static">
                      <span className="cd-req-text">Hiểu khái niệm bảng, cột, dòng, khóa chính/khóa ngoại</span>
                      <span className="cd-req-status is-info" aria-label="Khuyến nghị"><i className="fas fa-lightbulb"></i></span>
                    </li>
                    <li data-prereq="static">
                      <span className="cd-req-text">Có khả năng đọc ER Diagram cơ bản</span>
                      <span className="cd-req-status is-info" aria-label="Khuyến nghị"><i className="fas fa-lightbulb"></i></span>
                    </li>
                    <li data-prereq="static">
                      <span className="cd-req-text">Trình duyệt web hiện đại (Chrome / Edge / Firefox mới nhất) — không cần cài DB</span>
                      <span className="cd-req-status is-info" aria-label="Khuyến nghị"><i className="fas fa-lightbulb"></i></span>
                    </li>
                  </ul>
                </div>
              </div>

              {/* Block 4: Thành tựu */}
              <div className="cd-block">
                <div className="cd-block-hd">
                  <div className="cd-block-icon">🏅</div>
                  <h3>Thành tựu</h3>
                </div>
                <div className="cd-block-body">
                  <div className="cd-skills">
                    <div className="cd-skill-item" data-module="1">
                      <div className="cd-skill-icon"><i className="fas fa-key"></i></div>
                      <div className="cd-skill-body">
                        <div className="cd-skill-title">Phân biệt các loại Key</div>
                        <div className="cd-skill-desc">Primary, Composite, Foreign Key</div>
                      </div>
                    </div>
                    <div className="cd-skill-item" data-module="1">
                      <div className="cd-skill-icon"><i className="fas fa-link"></i></div>
                      <div className="cd-skill-body">
                        <div className="cd-skill-title">Thiết kế FK 1:1 &amp; 1:N</div>
                        <div className="cd-skill-desc">Quan hệ một-một &amp; một-nhiều qua khóa ngoại</div>
                      </div>
                    </div>
                    <div className="cd-skill-item" data-module="1">
                      <div className="cd-skill-icon"><i className="fas fa-project-diagram"></i></div>
                      <div className="cd-skill-body">
                        <div className="cd-skill-title">Junction Table cho M:N</div>
                        <div className="cd-skill-desc">Quan hệ nhiều-nhiều qua bảng trung gian</div>
                      </div>
                    </div>
                    <div className="cd-skill-item" data-module="1">
                      <div className="cd-skill-icon"><i className="fas fa-cubes"></i></div>
                      <div className="cd-skill-body">
                        <div className="cd-skill-title">Composite Key &amp; Weak Entity</div>
                        <div className="cd-skill-desc">Thực thể yếu &amp; khóa phức hợp đúng chuẩn</div>
                      </div>
                    </div>

                    <div className="cd-skill-item" data-module="2">
                      <div className="cd-skill-icon"><i className="fas fa-broom"></i></div>
                      <div className="cd-skill-body">
                        <div className="cd-skill-title">Loại bỏ Redundancy &amp; FD dư thừa</div>
                        <div className="cd-skill-desc">Phát hiện &amp; xử lý phụ thuộc hàm thừa</div>
                      </div>
                    </div>
                    <div className="cd-skill-item" data-module="2">
                      <div className="cd-skill-icon"><i className="fas fa-layer-group"></i></div>
                      <div className="cd-skill-body">
                        <div className="cd-skill-title">Chuẩn hóa 1NF → BCNF → 3NF</div>
                        <div className="cd-skill-desc">Thuật toán tách bảch chuẩn &amp; phi tổn thất</div>
                      </div>
                    </div>
                    <div className="cd-skill-item" data-module="2">
                      <div className="cd-skill-icon"><i className="fas fa-balance-scale"></i></div>
                      <div className="cd-skill-body">
                        <div className="cd-skill-title">BCNF vs 3NF trade-off</div>
                        <div className="cd-skill-desc">Giải thích thỏa hiệp chuẩn vs thực tế</div>
                      </div>
                    </div>
                    <div className="cd-skill-item" data-module="2">
                      <div className="cd-skill-icon"><i className="fas fa-crown"></i></div>
                      <div className="cd-skill-body">
                        <div className="cd-skill-title">Boss Battle — Mạng Xã Hội Gamers</div>
                        <div className="cd-skill-desc">Thiết kế schema A-Z từ yêu cầu thực tế</div>
                      </div>
                    </div>

                    <div className="cd-skill-item" data-module="3">
                      <div className="cd-skill-icon"><i className="fas fa-code"></i></div>
                      <div className="cd-skill-body">
                        <div className="cd-skill-title">JSONB trong Postgres</div>
                        <div className="cd-skill-desc">Toán tử <code>-&gt;</code>, <code>-&gt;&gt;</code>, GROUP BY theo key lồng</div>
                      </div>
                    </div>
                    <div className="cd-skill-item" data-module="3">
                      <div className="cd-skill-icon"><i className="fas fa-map-marker-alt"></i></div>
                      <div className="cd-skill-body">
                        <div className="cd-skill-title">Spatial Query PostGIS</div>
                        <div className="cd-skill-desc"><code>ST_MakePoint</code>, <code>ST_Distance</code>, <code>ST_DWithin</code>, GiST index</div>
                      </div>
                    </div>
                    <div className="cd-skill-item" data-module="3">
                      <div className="cd-skill-icon"><i className="fab fa-python"></i></div>
                      <div className="cd-skill-body">
                        <div className="cd-skill-title">ORM Django</div>
                        <div className="cd-skill-desc"><code>select_related</code>, <code>values/annotate</code>, ánh xạ Class ↔ Table</div>
                      </div>
                    </div>
                    <div className="cd-skill-item" data-module="3">
                      <div className="cd-skill-icon"><i className="fas fa-shield-alt"></i></div>
                      <div className="cd-skill-body">
                        <div className="cd-skill-title">Phòng chống SQL Injection</div>
                        <div className="cd-skill-desc">Prepared Statement, validate input, least privilege</div>
                      </div>
                    </div>
                    <div className="cd-skill-item" data-module="3">
                      <div className="cd-skill-icon"><i className="fas fa-user-shield"></i></div>
                      <div className="cd-skill-body">
                        <div className="cd-skill-title">Password Security</div>
                        <div className="cd-skill-desc">bcrypt + salt, audit <code>CASE WHEN</code> phát hiện hash yếu</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Block 5: Đánh giá */}
              <div className="cd-block">
                <div className="cd-block-hd">
                  <div className="cd-block-icon">⭐</div>
                  <h3>Đánh giá của học viên</h3>
                </div>
                <div className="cd-block-body">
                  <div className="cd-reviews-stub">
                    <div className="star-avg-wrap">
                      <div className="star-avg">
                        <div className="star-avg-bg">★★★★★</div>
                        <div className="star-avg-fill" data-fill="96">★★★★★</div>
                      </div>
                    </div>
                    <div className="score">4.8</div>
                    <div className="avg-label">Đánh giá trung bình</div>

                    <div className="user-rate-section">
                      <div className="user-rate-label">Đánh giá của bạn:</div>
                      <div className="star-interactive" id="starInteractive">
                        {[1, 2, 3, 4, 5].map((i) => (
                          <div className="si-star" data-star={i} key={i}>★</div>
                        ))}
                      </div>
                      <div className="user-rate-val" id="userRateVal">—</div>
                    </div>

                    <div className="coming-soon-note">Tính năng lưu đánh giá đang được phát triển. Hãy quay lại sau!</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <div className="cd-side-col">
              <div className="cd-card">
                <div className="cd-card-image">🗄️</div>
                <div className="cd-card-body">
                  <div className="cd-card-price">Miễn phí</div>
                  <div className="cd-card-free">🎉 Hoàn toàn không mất phí</div>

                  <div id="cd-cta-area">
                    {enrollment ? (
                      <>
                        <div className="cd-progress-row" style={{ marginTop: 14 }}>
                          <div className="cd-progress-label">
                            <span>Tiến độ</span>
                            <span className="pct">{pct}%</span>
                          </div>
                          <div className="cd-prog-bar">
                            <div className="cd-prog-fill" id="prog-fill" style={{ width: `${pct}%` }}></div>
                          </div>
                        </div>

                        <div className="cd-card-stats">
                          <div className="cd-cs">
                            <div className="v">{done}</div>
                            <div className="l">Bài đã học</div>
                          </div>
                          <div className="cd-cs">
                            <div className="v">{Math.max(20 - (enrollment.completedLessons || 0), 0)}</div>
                            <div className="l">Còn lại</div>
                          </div>
                          <div className="cd-cs">
                            <div className="v">{enrollment.timeSpent || '0h'}</div>
                            <div className="l">Đã học</div>
                          </div>
                          <div className="cd-cs">
                            <div className="v">{streak}</div>
                            <div className="l">🔥 Streak</div>
                          </div>
                        </div>

                        <button className="cd-enroll-btn continue" onClick={() => W().goLesson()}>▶ Tiếp tục học</button>
                        <button className="cd-enroll-btn unenroll" id="unenroll-btn" onClick={() => W().unenroll()}>Hủy đăng ký</button>
                      </>
                    ) : (
                      <button className="cd-enroll-btn primary" style={{ marginTop: 14 }} id="enroll-btn" onClick={() => W().enroll()}>
                        Đăng ký ngay – Miễn phí
                      </button>
                    )}
                  </div>
                  <div id="cd-cta-error" role="alert" aria-live="polite" style={{ display: 'none', marginTop: 8, color: '#EF4444', fontSize: '0.8rem' }}></div>

                  <div className="cd-includes">
                    <div className="cd-includes-title">KHÓA HỌC BAO GỒM</div>
                    <div className="cd-inc-item"><i className="fas fa-book-open"></i> 20 bài học (Khóa Cơ bản)</div>
                    <div className="cd-inc-item"><i className="fas fa-project-diagram"></i> 3 module (ER / Normalization / Application)</div>
                    <div className="cd-inc-item"><i className="fas fa-clock"></i> ~14 giờ học</div>
                    <div className="cd-inc-item"><i className="fas fa-database"></i> Thực hành trên trình duyệt (không cần cài DB)</div>
                    <div className="cd-inc-item"><i className="fas fa-infinity"></i> Truy cập vĩnh viễn</div>
                    <div className="cd-inc-item"><i className="fas fa-certificate"></i> Chứng chỉ hoàn thành</div>
                    <div className="cd-inc-item"><i className="fas fa-mobile-alt"></i> Học trên mọi thiết bị</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Chatbot />
      {/* Globals cho course_db_design.js (thay inline script Jinja gốc):
          <script> trong JSX không bao giờ được React thực thi, nên phải gán
          qua LegacyScripts trước khi nạp file legacy. */}
      <LegacyScripts
        srcs={['/static/js/course_db_design.js', '/static/js/chatbot.js']}
        globals={{
          COURSE_ID: courseId,
          USER_STREAK: streak,
          CURRENT_LESSON_IDX: enrollment ? enrollment.completedLessons || 0 : 0,
          LESSON_URL: `/lesson/${courseId}`,
        }}
      />
    </>
  );
}
