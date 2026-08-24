'use client';

// Port dashboard.html (extends base.html) — SPA-hub: các "trang" Dashboard/
// Khóa học/Lộ trình/Kỹ năng/Diễn đàn/Cài đặt/Trang của tôi chuyển client-side
// bằng main.js navigate() trong CÙNG route này (không tách route Next — giữ UX cũ).
// CSS đúng tổ hợp gốc (dashboard.html block extra_head, thứ tự giữ nguyên).

import PageStyles from '@/components/PageStyles';
import Chatbot from '@/components/Chatbot';
import LegacyScripts from '@/components/LegacyScripts';
import RoadmapSection from '@/components/RoadmapSection';
import Topbar from '@/components/Topbar';

/* eslint-disable @typescript-eslint/no-explicit-any, @next/next/no-img-element */
const W = () => window as any;

// Thứ tự script y hệt cuối dashboard.html (mermaid → svg-pan-zoom → roadmapData
// → roadmap → main → chatbot → dashboard); icons.js vốn nằm ở <head> base.html.
const SCRIPTS = [
  '/static/js/icons.js',
  'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js',
  'https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js',
  '/static/js/roadmapData.js',
  '/static/js/roadmap.js',
  '/static/js/main.js',
  '/static/js/chatbot.js',
  '/static/js/dashboard.js',
];

export default function DashboardPage() {
  return (
    <>
      <PageStyles hrefs={["/static/css/style.css","/static/css/dashboard.css","/static/css/pages.css","/static/css/ChangePassword.css","/static/css/skeleton.css","/static/css/dark-mode.css","/static/css/roadmap.css","/static/css/a11y.css"]} />
      <title>ProgrammingEdu × TopHSA</title>
      {/* PERF 2026-07-19: mermaid + svg-pan-zoom tải từ jsdelivr — preconnect
          cắt DNS+TLS handshake khỏi đường găng nạp script */}
      <link rel="preconnect" href="https://cdn.jsdelivr.net" />
      <Topbar />

      <div id="main">
        {/* ── Dashboard ── */}
        <div className="page active" id="page-dashboard">
          {/* Hero banner */}
          <div className="dash-hero fx-fade-up">
            <div className="dash-hero-overlay"></div>
            <div className="dash-hero-text">
              <span className="dash-hero-greeting" id="banner-greeting">Chào mừng trở lại 👋</span>
              <h2 id="banner-name">—</h2>
              <p>Hôm nay luyện phần nào? Tiếp tục hành trình chinh phục kỳ thi Đánh giá năng lực HSA.</p>
            </div>
            <button className="dash-hero-btn" onClick={() => W().navigate('courses')}>
              Khám phá khóa học <span data-icon="arrow-right" data-size="13"></span>
            </button>
          </div>

          {/* ── Hàng thẻ số liệu (audit 2026-08-14) ──
              Trước đây màn hình đầu bị "Lịch học tuần này" chiếm trọn một hàng
              ngang còn lộ trình thì teo lại. Nay 4 chỉ số quan trọng nhất lên
              trên cùng, lịch học thu thành dải 7 chấm ngay trong thẻ streak.
              dashboard.js đổ số vào qua /api/hsa/summary. */}
          <div className="hsa-tiles fx-fade-up" style={{ animationDelay: '.04s' }}>
            <div className="hsa-tile">
              <div className="hsa-tile-ic" data-icon="flame" data-size="18"></div>
              <div className="hsa-tile-body">
                <div className="hsa-tile-num" id="tile-streak">0</div>
                <div className="hsa-tile-lbl">ngày học liên tiếp</div>
                <div className="hsa-week" id="tile-week" aria-label="Lịch học tuần này"></div>
              </div>
            </div>

            <div className="hsa-tile">
              <div className="hsa-tile-ic" data-icon="book-open" data-size="18"></div>
              <div className="hsa-tile-body">
                <div className="hsa-tile-num"><span id="tile-done">0</span><span className="hsa-tile-of">/76</span></div>
                <div className="hsa-tile-lbl">bài đã hoàn thành</div>
                <div className="hsa-tile-bar"><i id="tile-done-bar" style={{ width: '0%' }}></i></div>
              </div>
            </div>

            <div className="hsa-tile">
              <div className="hsa-tile-ic" data-icon="clock" data-size="18"></div>
              <div className="hsa-tile-body">
                <div className="hsa-tile-num" id="tile-days">—</div>
                <div className="hsa-tile-lbl">ngày nữa tới kỳ thi</div>
                <a className="hsa-tile-cta" id="tile-days-cta" href="/questionaire">Làm khảo sát để đặt mốc thi</a>
              </div>
            </div>

            <div className="hsa-tile">
              <div className="hsa-tile-ic" data-icon="target" data-size="18"></div>
              <div className="hsa-tile-body">
                <div className="hsa-tile-num" id="tile-score">—</div>
                <div className="hsa-tile-lbl" id="tile-score-lbl">điểm thi thử gần nhất</div>
                <a className="hsa-tile-cta" id="tile-score-cta" href="/mock">Làm đề thi thử</a>
              </div>
            </div>
          </div>

          {/* Cột trái: học tiếp + tiến độ 3 hợp phần · Cột phải: lộ trình */}
          <div className="dash-row dash-row--cal">
            <div className="dash-col-left">
              <div className="section-card hsa-continue fx-fade-up" id="hsa-continue" style={{ animationDelay: '.08s' }}>
                <div className="hsa-cont-empty">
                  <div className="hsa-cont-ic" data-icon="compass" data-size="26"></div>
                  <div>
                    <b>Bắt đầu hành trình HSA</b>
                    <p>Chọn một hợp phần để vào bài học đầu tiên.</p>
                  </div>
                  <button className="hsa-cont-btn" onClick={() => W().navigate('courses')}>Khám phá khoá học</button>
                </div>
              </div>

              {/* Nhiệm vụ hôm nay — cho chuỗi ngày học có việc để làm, thay vì
                  chỉ đếm số ngày (audit 2026-08-14). */}
              <div className="section-card fx-fade-up" style={{ animationDelay: '.1s' }}>
                <div className="section-title" style={{ marginBottom: 14 }}>
                  <span className="title-icon-blue" data-icon="check" data-size="16"></span>
                  <span>Nhiệm vụ hôm nay</span>
                </div>
                <div className="hsa-missions" id="hsa-missions"></div>
              </div>

              {/* Tuần này + nhật ký học. Đặt ở đây chứ không phải Trang của tôi
                  vì đây là việc làm HẰNG NGÀY; Trang của tôi là nơi nhìn lại.
                  Một việc hằng ngày nằm dưới đáy một trang dài thì không ai dùng. */}
              <div className="section-card fx-fade-up" style={{ animationDelay: '.105s' }}>
                <div className="section-title" style={{ marginBottom: 14 }}>
                  <span className="title-icon-blue" data-icon="calendar" data-size="16"></span>
                  <span>Tuần này</span>
                </div>
                {/* Việc của tuần này do hệ thống xếp (stats/plan.py). Đứng
                    TRÊN mục tiêu tuần vì đây là "làm gì", còn mục tiêu là
                    "bao nhiêu" — người ta cần biết làm gì trước. */}
                <div className="pl-thisweek" id="pl-thisweek"></div>

                <div className="jr-week" id="jr-week">
                  <div className="hsa-mis-empty">Đang tải…</div>
                </div>

                <div className="jr-sep"></div>
                <div className="jr-hd">Nhật ký hôm nay</div>
                <div className="jr-today" id="jr-today"></div>
                <datalist id="jr-topics"></datalist>

                <button type="button" className="jr-toggle" id="jr-toggle" aria-expanded="false" hidden></button>
                <div className="jr-history" id="jr-history" hidden></div>
              </div>

              {/* Ba chủ đề yếu nhất, mỗi chủ đề đúng MỘT nút. Biết mình yếu ở
                  đâu mà không có đường đi tiếp thì thông tin đó chưa dùng được.
                  dashboard.js đổ vào từ /api/hsa/competency. */}
              <div className="section-card fx-fade-up" style={{ animationDelay: '.11s' }}>
                <div className="section-title" style={{ marginBottom: 14 }}>
                  <span className="title-icon-blue" data-icon="target" data-size="16"></span>
                  <span>Nên ôn tiếp</span>
                </div>
                <div className="hsa-weak" id="hsa-weak">
                  <div className="hsa-mis-empty">Đang tính…</div>
                </div>
              </div>

              <div className="section-card fx-fade-up" style={{ animationDelay: '.12s' }}>
                <div className="section-title" style={{ marginBottom: 14 }}>
                  <span className="title-icon-blue" data-icon="bar-chart" data-size="16"></span>
                  <span>Tiến độ theo hợp phần</span>
                </div>
                <div className="hsa-sections" id="hsa-sections"></div>
              </div>
            </div>

            <div className="section-card mini-rm-card mini-rm-card--full fx-fade-up" style={{ animationDelay: '.09s' }}>
              <div className="mini-rm-header">
                <div className="section-title" style={{ marginBottom: 0 }}>
                  <span className="title-icon-blue" data-icon="map" data-size="16"></span><span>Lộ trình của bạn</span>
                </div>
                <a className="mini-rm-more" href="#" onClick={(e) => { e.preventDefault(); W().navigate('roadmap'); }}>Xem tất cả ›</a>
              </div>
              <div className="mini-rm-canvas" id="mini-rm-canvas" tabIndex={0}>
                <div className="mini-rm-loading">Đang tải lộ trình…</div>
              </div>
              <div className="mini-rm-legend">
                <span className="lb-legend-item"><span className="lb-legend-dot lb-done">✓</span> Hoàn thành</span>
                <span className="lb-legend-item"><span className="lb-legend-dot lb-progress">◐</span> Đang học</span>
                <span className="lb-legend-item"><span className="lb-legend-dot lb-locked">○</span> Mở khoá</span>
              </div>
            </div>
          </div>
          <div className="cal-tooltip" id="cal-tooltip"></div>

          {/* Row 2: Leaderboard + Learning progress */}
          <div className="dash-row dash-row--lb">
            <div className="section-card lb-card fx-fade-up" style={{ animationDelay: '.12s' }}>
              <div className="lb-header">
                <div className="section-title" style={{ marginBottom: 0 }}>
                  <span className="title-icon-blue">🏆</span><span>Bảng xếp hạng</span>
                </div>
                <div className="lb-tabs" role="tablist" aria-label="Bảng xếp hạng">
                  <button type="button" className="lb-tab active" data-type="weekly" role="tab" aria-selected="true">⏱ Tuần</button>
                  <button type="button" className="lb-tab" data-type="streak" role="tab" aria-selected="false">🔥 Streak</button>
                  <button type="button" className="lb-tab" data-type="friends" role="tab" aria-selected="false">👥 Bạn bè</button>
                </div>
              </div>
              <div className="lb-meta" id="lb-meta">Đang tải…</div>
              <ol className="lb-list" id="lb-list" aria-live="polite">
                <li className="lb-skel">Đang tải bảng xếp hạng…</li>
              </ol>
              <div className="lb-me" id="lb-me" hidden></div>
            </div>

            <div className="section-card dash-progress-card fx-fade-up" style={{ animationDelay: '.15s' }}>
              <div className="section-title" style={{ marginBottom: 0 }}>
                <span className="title-icon-blue">📋</span><span>Tiến độ học tập</span>
              </div>
              <div className="dash-progress-empty" id="dash-progress-empty">
                <span className="dash-progress-icon" data-icon="book-open" data-size="20" data-color="#60A5FA"></span>
                <p>Chưa đăng ký khóa học nào</p>
                <span className="dash-progress-sub">Bắt đầu học ngay hôm nay!</span>
                <button className="dash-progress-btn" onClick={() => W().navigate('courses')}>Xem khóa học →</button>
              </div>
              {/* Danh sách tiến độ thật (bảng enrollments) — main.js renderDashProgress() đổ vào */}
              <div className="dash-progress-list" id="dash-progress-list" hidden></div>
            </div>
          </div>
        </div>

        {/* ── Kế hoạch học ── */}
        <div className="page" id="page-plan">
          <div className="courses-header fx-fade-up">
            <div>
              <h2>🗓️ Kế hoạch học</h2>
              <p className="courses-subtitle">
                Lịch tới ngày thi, hệ thống xếp từ ngày thi, sức học bạn khai và chủ đề bạn đang yếu.
              </p>
            </div>
          </div>
          <div className="section-card fx-fade-up" style={{ animationDelay: '.05s' }}>
            <div className="pl-all" id="pl-all">
              <div className="hsa-mis-empty">Đang tải…</div>
            </div>
          </div>
        </div>

        {/* ── Courses ── */}
        <div className="page" id="page-courses">
          <div className="courses-header fx-fade-up">
            <div>
              <h2>📚 Khóa học</h2>
              <p className="courses-subtitle" id="courses-count-sub">Đang tải…</p>
            </div>
            <div className="courses-controls">
              <div className="filter-group" role="group" aria-label="Enrollment filter">
                <button className="filter-btn active" onClick={(e) => W().setEnrollmentFilter(e.currentTarget, 'all')} role="radio" aria-checked="true">Tất cả</button>
                <button className="filter-btn" onClick={(e) => W().setEnrollmentFilter(e.currentTarget, 'enrolled')} role="radio" aria-checked="false">Đang học</button>
                <button className="filter-btn" onClick={(e) => W().setEnrollmentFilter(e.currentTarget, 'not-enrolled')} role="radio" aria-checked="false">Chưa đăng ký</button>
              </div>
              <div className="sort-dropdown-wrap">
                <label htmlFor="course-sort-select" className="sort-label">Sắp xếp:</label>
                <select id="course-sort-select" className="sort-select" onChange={(e) => W().setSortOrder(e.currentTarget.value)} aria-label="Sort courses by">
                  <option value="newest">Mới nhất</option>
                  <option value="popular">Phổ biến nhất</option>
                  <option value="duration">Ngắn nhất</option>
                </select>
              </div>
            </div>
          </div>

          {/* Search bar + tag filter row */}
          <div className="courses-filter-row fx-fade-up" style={{ animationDelay: '.07s' }}>
            <div className="courses-search-bar-wrap" id="courses-search-bar-wrap">
              <span className="csb-icon" data-icon="search" data-size="14"></span>
              <input
                type="text"
                id="course-search-input"
                className="courses-search-bar-input"
                placeholder="Tìm khóa học, hợp phần, chủ đề..."
                autoComplete="off"
                onClick={() => W().cshOpen()}
                onInput={(e) => W().cshInput(e.currentTarget.value)}
              />
              <button className="csb-clear" id="course-search-clear" type="button" style={{ display: 'none' }} onClick={() => W().cshClear()}>✕</button>
              <div className="course-search-hints" id="course-search-hints" style={{ display: 'none' }}>
                <div id="csh-static">
                  <div className="csh-label">Gợi ý tìm kiếm</div>
                  <div className="csh-pills">
                    <button type="button" className="csh-pill" onClick={() => W().cshPick('Định lượng')}><span className="csh-ic" data-icon="bar-chart" data-size="14"></span> Định lượng</button>
                    <button type="button" className="csh-pill" onClick={() => W().cshPick('Định tính')}><span className="csh-ic" data-icon="pencil" data-size="14"></span> Định tính</button>
                    <button type="button" className="csh-pill" onClick={() => W().cshPick('Khoa học')}><span className="csh-ic" data-icon="microscope" data-size="14"></span> Khoa học</button>

                    <button type="button" className="csh-pill" onClick={() => W().cshPick('Phần trăm')}>％ Phần trăm</button>
                    <button type="button" className="csh-pill" onClick={() => W().cshPick('Hàm số')}><span className="csh-ic" data-icon="bar-chart" data-size="14"></span> Hàm số</button>
                    <button type="button" className="csh-pill" onClick={() => W().cshPick('Đọc hiểu')}><span className="csh-ic" data-icon="book-open" data-size="14"></span> Đọc hiểu</button>
                    <button type="button" className="csh-pill" onClick={() => W().cshPick('Đề thi thử')}><span className="csh-ic" data-icon="clock" data-size="14"></span> Đề thi thử</button>
                  </div>
                </div>
                <ul id="csh-dynamic" style={{ display: 'none', listStyle: 'none', padding: 0, margin: '8px 0 0' }}></ul>
              </div>
            </div>

            {/* Bộ lọc theo hợp phần HSA (đã bỏ 'Cấp độ' + 'Ngôn ngữ' lập trình pe_test) */}
            <div className="course-filter-panel">
              <div className="filter-pill-row" id="section-filter-row">
                <span className="pill-label">Hợp phần</span>
                <button className="pill-btn" onClick={(e) => W().toggleLanguageFilter(e.currentTarget, 'Định lượng')}>Định lượng</button>
                <button className="pill-btn" onClick={(e) => W().toggleLanguageFilter(e.currentTarget, 'Định tính')}>Định tính</button>
                <button className="pill-btn" onClick={(e) => W().toggleLanguageFilter(e.currentTarget, 'Khoa học')}>Khoa học</button>
              </div>
              <div className="active-filters hidden" id="active-filters"></div>
            </div>
          </div>

          <div className="courses-grid" id="courses-grid">
            {/* Skeleton */}
            {[0, 1, 2, 3].map((i) => (
              <div className="skel-course-card" key={i}><div className="skel-card-img skel"></div><div className="skel-card-body"><div className="skel-card-tag skel"></div><div className="skel-card-title skel"></div><div className="skel-card-desc skel"></div><div className="skel-card-footer"><div className="skel-card-meta skel"></div><div className="skel-card-btn skel"></div></div></div></div>
            ))}
          </div>
          <div className="empty hidden" id="empty-state">
            <div className="empty-icon">🔍</div>
            <p>Không tìm thấy khóa học phù hợp.</p>
          </div>
        </div>

        {/* ── Roadmap (partial roadmap.html) ── */}
        <RoadmapSection />

        {/* ── Skills ── */}
        <div className="page" id="page-skills">
          <div className="courses-header fx-fade-up">
            <h2>🐙 Kỹ năng</h2>
          </div>
          <div className="courses-search-bar-wrap fx-fade-up" id="skills-search-wrap" style={{ animationDelay: '.07s' }}>
            <span className="csb-icon" data-icon="search" data-size="14"></span>
            <input
              type="text"
              id="skills-search-input"
              className="courses-search-bar-input"
              placeholder="Tìm chủ đề (ví dụ: Phần trăm, Hàm số, Đọc hiểu...)"
              autoComplete="off"
              onInput={(e) => W().skillsSearch(e.currentTarget.value)}
            />
            <button className="csb-clear" id="skills-search-clear" type="button" style={{ display: 'none' }} onClick={() => W().skillsClearSearch()}>✕</button>
          </div>

          <div id="skills-search-empty" style={{ display: 'none', textAlign: 'center', padding: '32px 0', color: 'var(--t3)', fontSize: 14 }}>🔍 Không tìm thấy kỹ năng phù hợp.</div>
          <div className="sk-summary fx-fade-up" id="sk-summary" style={{ animationDelay: '.12s' }}></div>
          <div className="sk-grid" id="sk-grid">
            <div style={{ color: '#9CA3AF', fontSize: 14, padding: 24 }}>Đang tải...</div>
          </div>
        </div>

        {/* ── Forum ── */}
        <div className="page" id="page-forum">
          <div className="courses-header fx-fade-up">
            <div>
              <h2>💬 Diễn đàn</h2>
              <p className="page-subtitle">Chia sẻ kiến thức, đặt câu hỏi và thảo luận cùng mọi người</p>
            </div>
          </div>

          <div className="courses-search-bar-wrap fx-fade-up" id="forum-search-wrap" style={{ animationDelay: '.07s' }}>
            <span className="csb-icon" data-icon="search" data-size="14"></span>
            <input
              type="text"
              id="forum-search-input"
              className="courses-search-bar-input"
              placeholder="Tìm bài viết..."
              autoComplete="off"
              onInput={(e) => W().forumSearch(e.currentTarget.value)}
            />
            <button className="csb-clear" id="forum-search-clear" type="button" style={{ display: 'none' }} onClick={() => W().forumClearSearch()}>✕</button>
          </div>

          <div className="courses-header fx-fade-up" style={{ marginBottom: 16, animationDelay: '.11s' }}>
            <div className="filter-group" id="forum-tabs">
              <button className="filter-btn active" data-cat="all" onClick={(e) => W().forumSetCat(e.currentTarget, 'all')}>🗂️ Tất cả</button>
              <button className="filter-btn" data-cat="question" onClick={(e) => W().forumSetCat(e.currentTarget, 'question')}>❓ Câu hỏi</button>
              <button className="filter-btn" data-cat="share" onClick={(e) => W().forumSetCat(e.currentTarget, 'share')}>💡 Chia sẻ</button>
              <button className="filter-btn" data-cat="discuss" onClick={(e) => W().forumSetCat(e.currentTarget, 'discuss')}>💬 Thảo luận</button>
            </div>
            <div className="sort-dropdown-wrap">
              <label className="sort-label">Sắp xếp:</label>
              <select className="sort-select" onChange={(e) => W().forumSetSort(e.currentTarget.value)}>
                <option value="newest">Mới nhất</option>
                <option value="oldest">Cũ nhất</option>
                <option value="likes">Nhiều like nhất</option>
              </select>
            </div>
          </div>

          {/* Create box */}
          <div className="forum-create-box fx-fade-up" style={{ animationDelay: '.15s' }}>
            <div className="forum-create-row">
              <div className="fcb-avatar" id="fcb-avatar">?</div>
              <textarea
                id="forum-inline-body"
                className="fcb-textarea"
                maxLength={2000}
                placeholder="Bạn đang nghĩ gì? Chia sẻ với mọi người..."
                onInput={(e) => W().forumInlineInput(e.currentTarget.value)}
              ></textarea>
            </div>
            <div className="fcb-bottom-row">
              <div className="fcb-type-picker" id="fcb-type-picker">
                <button type="button" className="fcb-type-btn active" data-val="question" onClick={(e) => W().forumInlinePickType(e.currentTarget)}>❓ Câu hỏi</button>
                <button type="button" className="fcb-type-btn" data-val="share" onClick={(e) => W().forumInlinePickType(e.currentTarget)}>💡 Chia sẻ</button>
                <button type="button" className="fcb-type-btn" data-val="discuss" onClick={(e) => W().forumInlinePickType(e.currentTarget)}>💬 Thảo luận</button>
              </div>
              {/* disabled qua ref (DOM), không qua prop JSX — prop disabled làm React
                  chặn onClick vĩnh viễn dù main.js đã enable nút khi có nội dung */}
              <button
                className="fcb-submit-btn"
                id="fcb-submit-btn"
                ref={(el) => { if (el) el.disabled = true; }}
                onClick={() => W().forumSubmitInline?.()}
              >Đăng</button>
            </div>
          </div>

          {/* Post list */}
          <div id="forum-list"></div>

          {/* Empty state */}
          <div className="empty hidden" id="forum-empty">
            <div className="empty-icon">💬</div>
            <p>Chưa có bài viết nào. Hãy là người đầu tiên đăng bài!</p>
          </div>
        </div>

        {/* ── Settings ── */}
        <div className="page" id="page-settings">
          <div className="settings-wrap">
            <div className="settings-section">
              <div className="settings-section-title"><span className="title-icon-blue" data-icon="user" data-size="16"></span><span>Thông tin cá nhân</span></div>
              <div className="profile-top">
                <div className="profile-avatar">
                  <img src="/static/images/avatar.svg" alt="avatar" />
                  <button className="avatar-edit-btn">+</button>
                </div>
                <div>
                  <div className="profile-name" id="settings-profile-name">—</div>
                  <div className="profile-email" id="settings-profile-email">—</div>
                  <span className="profile-badge">Học viên</span>
                </div>
              </div>
              <div className="fields-grid">
                <div><label className="field-label">Họ và tên</label><input id="field-name" className="field-input" placeholder="Nhập họ và tên" /></div>
                <div><label className="field-label">Email</label><input id="field-email" className="field-input" placeholder="Nhập email" /></div>
                <div><label className="field-label">Số điện thoại</label><input id="field-phone" className="field-input" placeholder="Nhập số điện thoại" /></div>
                <div><label className="field-label">Ngày sinh</label><input id="field-birthday" className="field-input" placeholder="Chọn ngày sinh" /></div>
              </div>
            </div>

            {/* Mục tiêu HSA — trước đây chỉ đặt được MỘT LẦN lúc làm khảo sát,
                dù chúng nuôi thẻ đếm ngược ở Bảng điều khiển (audit 2026-08-15). */}
            <div className="settings-section" id="hsa-goals">
              <div className="settings-section-title">
                <span className="title-icon-blue" data-icon="target" data-size="16"></span>
                <span>Mục tiêu HSA</span>
              </div>
              <p className="goal-hint">
                Đổi ở đây khi mục tiêu hoặc lịch thi thay đổi — thẻ đếm ngược và
                lộ trình ở Bảng điều khiển cập nhật theo.
              </p>

              <div className="goal-field">
                <span className="field-label" id="lbl-goal-score">Điểm mục tiêu</span>
                <div className="goal-chips" role="radiogroup" aria-labelledby="lbl-goal-score">
                  {['Dưới 75', '75–90', '90–105', 'Trên 105'].map((v) => (
                    <label className="goal-chip" key={v}>
                      <input type="radio" name="goal-target-score" value={v} /><span>{v}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="goal-field">
                <span className="field-label" id="lbl-goal-timing">Bạn dự định thi khi nào?</span>
                <div className="goal-chips" role="radiogroup" aria-labelledby="lbl-goal-timing">
                  {['Trong 1 tháng', '1–3 tháng', '3–6 tháng', 'Trên 6 tháng'].map((v) => (
                    <label className="goal-chip" key={v}>
                      <input type="radio" name="goal-exam-timing" value={v} /><span>{v}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="goal-field">
                <label className="field-label" htmlFor="goal-exam-date">
                  Ngày thi chính xác <span className="goal-optional">(nếu đã biết)</span>
                </label>
                <input type="date" id="goal-exam-date" className="field-input goal-date" />
                <p className="goal-help">Nhập ngày cụ thể để đếm ngược chính xác thay vì ước lượng từ mốc ở trên.</p>
              </div>

              <div className="goal-field">
                <span className="field-label" id="lbl-goal-sec3">Hợp phần thứ 3</span>
                <div className="goal-chips" role="radiogroup" aria-labelledby="lbl-goal-sec3">
                  {['Khoa học', 'Tiếng Anh', 'Chưa quyết định'].map((v) => (
                    <label className="goal-chip" key={v}>
                      <input type="radio" name="goal-section3" value={v} /><span>{v}</span>
                    </label>
                  ))}
                </div>
              </div>

              <p className="goal-status" id="goal-status" role="status" aria-live="polite"></p>
            </div>

            <div className="settings-section">
              <div className="settings-section-title"><span className="title-icon-red" data-icon="bell" data-size="16"></span><span>Thông báo</span></div>
              <div className="notif-row">
                <div>
                  <div className="notif-lbl">Thông báo qua Email</div>
                  <div className="notif-desc">Nhận cập nhật khóa học qua email</div>
                </div><button id="toggle-email" className="toggle on" onClick={(e) => W().toggleSwitch(e.currentTarget)} aria-label="Toggle email notifications"><span className="toggle-knob"></span></button>
              </div>
              <div className="notif-row">
                <div>
                  <div className="notif-lbl">Thông báo đẩy</div>
                  <div className="notif-desc">Nhận thông báo trực tiếp trên trình duyệt</div>
                </div><button id="toggle-push" className="toggle" onClick={(e) => W().toggleSwitch(e.currentTarget)} aria-label="Toggle push notifications"><span className="toggle-knob"></span></button>
              </div>
              <div className="notif-row">
                <div>
                  <div className="notif-lbl">Nhắc nhở học tập</div>
                  <div className="notif-desc">Nhắc nhở lịch học hàng ngày</div>
                </div><button id="toggle-remind" className="toggle on" onClick={(e) => W().toggleSwitch(e.currentTarget)} aria-label="Toggle study reminders"><span className="toggle-knob"></span></button>
              </div>
              <div className="notif-row">
                <div>
                  <div className="notif-lbl">Cập nhật nội dung</div>
                  <div className="notif-desc">Thông báo khi có bài học mới</div>
                </div><button id="toggle-content" className="toggle" onClick={(e) => W().toggleSwitch(e.currentTarget)} aria-label="Toggle content updates"><span className="toggle-knob"></span></button>
              </div>
            </div>

            <div className="sec-lang-grid">
              <div className="sec-lang-card">
                <div className="sec-lang-title"><span className="title-icon-blue" data-icon="shield" data-size="16"></span><span>Bảo mật</span></div>
                <button className="change-pw-btn" onClick={() => W().openChangePasswordModal()}>Đổi mật khẩu</button>
              </div>
              <div className="sec-lang-card">
                <div className="sec-lang-title"><span className="title-icon-red" data-icon="globe" data-size="16"></span><span>Ngôn ngữ</span></div>
                <select className="lang-select" aria-label="Select language">
                  <option>Tiếng Việt</option>
                  <option>English</option>
                </select>
              </div>
            </div>

            <button className="save-btn" onClick={() => W().saveSettings()}>
              <span data-icon="check" data-size="16"></span> Lưu thay đổi
            </button>
          </div>
        </div>

        {/* ══════════ TRANG CỦA TÔI ══════════ */}
        <div className="page" id="page-profile">
          <div className="prof-wrap">
            {/* Hero card */}
            <div className="prof-hero fx-fade-up">
              <div className="prof-hero-bg"></div>
              <div className="prof-hero-body">
                <div className="prof-avatar-wrap">
                  <div className="prof-avatar" id="prof-avatar-letter">?</div>
                  <span className="prof-avatar-badge">🎓</span>
                </div>
                <div className="prof-hero-info">
                  <div className="prof-name" id="prof-name">—</div>
                  <div className="prof-email" id="prof-email">—</div>
                  {/* Mục tiêu HSA ngay trên hồ sơ: hồ sơ học viên HSA là mục
                      tiêu + mốc thi, không phải chỉ tên và email. */}
                  <div className="prof-goals" id="prof-goals"></div>
                </div>
                <button className="prof-edit-btn" onClick={() => W().navigate('settings')}>
                  <span data-icon="pencil" data-size="13"></span> Chỉnh sửa hồ sơ
                </button>
              </div>
            </div>

            {/* Stats row (5 cards) */}
            <div className="prof-stats-row">
              <div className="prof-stat-card fx-fade-up" style={{ animationDelay: '.05s' }}>
                <div className="prof-stat-icon" data-icon="flame" data-size="22" data-color="#F97316"></div>
                <div className="prof-stat-val" id="prof-streak">—</div>
                <div className="prof-stat-lbl">Chuỗi ngày học</div>
              </div>
              <div className="prof-stat-card fx-fade-up" style={{ animationDelay: '.1s' }}>
                <div className="prof-stat-icon" data-icon="book-open" data-size="22" data-color="#3B82F6"></div>
                <div className="prof-stat-val" id="prof-enrolled">—</div>
                <div className="prof-stat-lbl">Khóa học đang học</div>
              </div>
              <div className="prof-stat-card fx-fade-up" style={{ animationDelay: '.15s' }}>
                <div className="prof-stat-icon" data-icon="check-circle-2" data-size="22" data-color="#10B981"></div>
                <div className="prof-stat-val" id="prof-done">—</div>
                <div className="prof-stat-lbl">Bài học hoàn thành</div>
              </div>
              <div className="prof-stat-card fx-fade-up" style={{ animationDelay: '.2s' }}>
                <div className="prof-stat-icon" data-icon="medal" data-size="22" data-color="#F59E0B"></div>
                <div className="prof-stat-val" id="prof-achievements">—</div>
                <div className="prof-stat-lbl">Thành tích đạt được</div>
              </div>
              <div className="prof-stat-card prof-stat-card--link fx-fade-up" style={{ animationDelay: '.25s' }} onClick={() => W().navigateToSkills()} title="Xem kỹ năng">
                <div className="prof-stat-icon" data-icon="sparkles" data-size="22" data-color="#A78BFA"></div>
                <div className="prof-stat-val" id="prof-skills">—</div>
                <div className="prof-stat-lbl">Kỹ năng</div>
              </div>
            </div>

            {/* Nội dung: TRÁI = hồ sơ năng lực · PHẢI = cộng đồng.
                Trước đây cột trái có 2 khối nói cùng một chuyện ("Khóa học đang
                học" và "XP theo hợp phần" đều là tiến độ khoá), còn năng lực
                theo hợp phần — thứ quan trọng nhất với thí sinh HSA — thì không
                có ở đâu (audit 2026-08-15). */}
            <div className="prof-grid">
              <div className="prof-col-left">
                {/* Bản đồ năng lực 20 ô (3 hợp phần × chương mục). Chương mục
                    đã gắn sẵn cho đủ 76 bài từ lâu nhưng chưa lần nào dùng để
                    chấm mạnh–yếu — đây là chỗ dùng nó.
                    Khối "Năng lực theo hợp phần" trước đây nằm ngay trên đây và
                    nói cùng một chuyện bằng ba thanh thô hơn; nay nhập thẳng vào
                    đầu mỗi nhóm của bản đồ. */}
                <div className="prof-section fx-fade-up" style={{ animationDelay: '.25s' }}>
                  <div className="prof-section-hd">
                    <span className="prof-section-icon" data-icon="map" data-size="16"></span>
                    <span className="prof-section-title">Bản đồ năng lực theo chủ đề</span>
                  </div>
                  <div className="cmp-map" id="cmp-map">
                    <div className="prof-empty">Đang tải…</div>
                  </div>
                  <p className="prof-caps-note" id="cmp-note"></p>
                </div>

                {/* Đường tiến bộ — câu hỏi thứ hai của thí sinh, sau "tôi yếu ở
                    đâu": "mấy tuần qua tôi có khá lên không?". Cột thời lượng và
                    đường điểm dùng HAI thang riêng, xem dashboard.js. */}
                <div className="prof-section fx-fade-up" style={{ animationDelay: '.3s' }}>
                  <div className="prof-section-hd">
                    <span className="prof-section-icon" data-icon="trending-up" data-size="16"></span>
                    <span className="prof-section-title">Đường tiến bộ</span>
                    <div className="cv-range" id="curve-range" role="group" aria-label="Khoảng thời gian">
                      <button type="button" data-weeks="8" aria-pressed="false">8 tuần</button>
                      <button type="button" data-weeks="12" className="active" aria-pressed="true">12 tuần</button>
                      <button type="button" data-weeks="24" aria-pressed="false">24 tuần</button>
                    </div>
                  </div>
                  <div className="cv-empty" id="curve-empty" hidden></div>
                  <div className="cv-chart" id="curve-chart"></div>
                  <div className="cv-meta" id="curve-meta"></div>
                  <p className="prof-caps-note" id="curve-note"></p>
                </div>

                {/* Sổ điểm THAY cho "Lịch sử thi thử": thi thử chỉ là một trong
                    bốn loại hoạt động được chấm, hiện riêng nó thì bài học,
                    phòng luyện và quiz ôn tập không có chỗ nào nhìn lại. */}
                <div className="prof-section fx-fade-up" style={{ animationDelay: '.34s' }}>
                  <div className="prof-section-hd">
                    <span className="prof-section-icon" data-icon="file-text" data-size="16"></span>
                    <span className="prof-section-title">Sổ điểm</span>
                  </div>
                  <div className="bk-sums" id="book-sum"></div>
                  <div className="bk-rows" id="book-rows">
                    <div className="prof-empty">Đang tải…</div>
                  </div>
                </div>
              </div>

              <div className="prof-col-right">
                <div className="prof-section fx-fade-up" style={{ animationDelay: '.25s' }}>
                  <div className="prof-section-hd">
                    <span className="prof-section-icon" data-icon="trophy" data-size="16"></span>
                    <span className="prof-section-title">Vị trí trong cộng đồng</span>
                  </div>
                  <div className="prof-ranks" id="prof-ranks">
                    <div className="prof-empty">Đang tải…</div>
                  </div>
                </div>

                <div className="prof-section prof-section--posts fx-fade-up" style={{ animationDelay: '.3s' }}>
                  <div className="prof-section-hd">
                    <span className="prof-section-icon" data-icon="message-circle" data-size="16"></span>
                    <span className="prof-section-title">Bài đăng của tôi</span>
                  </div>
                  <div className="prof-post-list" id="prof-post-list">
                    <div className="prof-empty">Chưa có bài đăng nào.</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ★ MODAL HỦY ĐĂNG KÝ KHÓA HỌC */}
      <div className="un-overlay" id="unenrollModal" onClick={(e) => W().handleUnenrollOverlayClick(e)}>
        <div className="un-card">
          <div className="un-icon-wrap">🗑️</div>
          <h3 className="un-title">Hủy đăng ký?</h3>
          <p className="un-sub">Bạn sắp hủy đăng ký khóa học</p>
          <p className="un-course-name" id="unenroll-course-name"></p>
          <div className="un-warning">
            <span>⚠️</span>
            <p>Toàn bộ tiến độ học tập của bạn trong khóa này sẽ bị <strong>xóa vĩnh viễn</strong> và không thể khôi phục lại.</p>
          </div>
          <div className="un-actions">
            <button className="un-btn-cancel" onClick={() => W().closeUnenrollModal()}>Không, giữ lại</button>
            <button className="un-btn-confirm" onClick={() => W().confirmUnenroll()}>Đồng ý hủy</button>
          </div>
        </div>
      </div>

      {/* ★ MODAL ĐỔI MẬT KHẨU */}
      <div className="cp-overlay" id="changePasswordModal" role="dialog" aria-modal="true" aria-labelledby="cpTitle">
        <div className="cp-modal">
          <button className="cp-close" onClick={() => W().closeChangePasswordModal()} aria-label="Đóng">✕</button>

          <div className="cp-header">
            <div className="cp-icon-wrap">
              <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="4" y="11" width="16" height="10" rx="2"></rect>
                <path d="M8 11V7a4 4 0 0 1 8 0v4"></path>
                <circle cx="12" cy="16" r="1.2" fill="currentColor" stroke="none"></circle>
              </svg>
            </div>
            <h3 className="cp-title" id="cpTitle">Đổi mật khẩu</h3>
            <p className="cp-subtitle">Bảo vệ tài khoản của bạn an toàn hơn</p>
          </div>

          <form id="cpForm" autoComplete="off">
            {/* Mật khẩu hiện tại */}
            <div className="cp-group">
              <label className="cp-label" htmlFor="cpCurrent">Mật khẩu hiện tại</label>
              <div className="cp-input-wrap">
                <svg className="cp-leading-icon" viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="4" y="11" width="16" height="10" rx="2"></rect>
                  <path d="M8 11V7a4 4 0 0 1 8 0v4"></path>
                </svg>
                <input type="password" className="cp-input" id="cpCurrent" placeholder="Nhập mật khẩu hiện tại" required />
                <button type="button" className="cp-toggle-eye" onClick={(e) => W().togglePassword('cpCurrent', e.currentTarget)} aria-label="Hiện/ẩn mật khẩu">
                  <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                </button>
              </div>
              <div className="cp-msg" id="cpCurrentMsg"></div>
            </div>

            {/* Mật khẩu mới */}
            <div className="cp-group">
              <label className="cp-label" htmlFor="cpNew">Mật khẩu mới</label>
              <div className="cp-input-wrap">
                <svg className="cp-leading-icon" viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="8" cy="15" r="4"></circle>
                  <path d="M10.8 12.2 21 2"></path>
                  <path d="m19 5 2 2"></path>
                  <path d="m16 8 2 2"></path>
                </svg>
                <input type="password" className="cp-input" id="cpNew" placeholder="Tối thiểu 8 ký tự" required onInput={(e) => W().checkStrength(e.currentTarget.value)} />
                <button type="button" className="cp-toggle-eye" onClick={(e) => W().togglePassword('cpNew', e.currentTarget)} aria-label="Hiện/ẩn mật khẩu">
                  <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                </button>
              </div>
              <div className="cp-strength" id="cpStrength">
                <div className="cp-strength-bars">
                  <span></span><span></span><span></span><span></span>
                </div>
                <div className="cp-strength-label" id="cpStrengthLabel"></div>
              </div>
            </div>

            {/* Xác nhận mật khẩu mới */}
            <div className="cp-group">
              <label className="cp-label" htmlFor="cpConfirm">Xác nhận mật khẩu mới</label>
              <div className="cp-input-wrap">
                <svg className="cp-leading-icon" viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2 4 6v6c0 5 3.5 9 8 10 4.5-1 8-5 8-10V6l-8-4z"></path>
                  <path d="m9 12 2 2 4-4"></path>
                </svg>
                <input type="password" className="cp-input" id="cpConfirm" placeholder="Nhập lại mật khẩu mới" required onInput={() => W().checkMatch()} />
                <button type="button" className="cp-toggle-eye" onClick={(e) => W().togglePassword('cpConfirm', e.currentTarget)} aria-label="Hiện/ẩn mật khẩu">
                  <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                </button>
              </div>
              <div className="cp-msg" id="cpConfirmMsg"></div>
            </div>

            <div className="cp-actions">
              <button type="button" className="cp-btn cp-btn-cancel" onClick={() => W().closeChangePasswordModal()}>Hủy</button>
              <button type="submit" className="cp-btn cp-btn-submit" id="cpSubmitBtn">
                <span className="cp-btn-text">Cập nhật mật khẩu</span>
                <span className="cp-spinner"></span>
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Nhắc giữ chuỗi: KHÔNG còn markup ở đây. Bản cũ là lớp phủ kín màn
          hình bật sau mỗi lần đăng nhập; nay dashboard.js dựng một thẻ nhỏ ở
          góc, tự tắt, không chặn thao tác (audit 2026-08-19). */}

      <Chatbot />

      <LegacyScripts srcs={SCRIPTS} />
    </>
  );
}
