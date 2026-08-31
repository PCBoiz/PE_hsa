'use client';

// Port course_detail.html (khóa python/java/htmlcss/cpp) — markup 1:1.
// Khác cơ chế (bắt buộc): Flask render Jinja server-side với CURRICULA +
// enrollment; bản Next fetch /api/courses + /api/enrolled + /api/stats +
// /api/user rồi tính trạng thái done/current/locked ĐÚNG logic main.py
// (curricula.json xuất nguyên văn từ CURRICULA).
// LƯU Ý: 3 khóa db_design* có route tĩnh riêng (courses/db_design*/page.tsx)
// vì tổ hợp CSS khác (course_db_design.css đè 63 class trùng tên).

import PageStyles from '@/components/PageStyles';
import { use, useEffect, useState } from 'react';

import Chatbot from '@/components/Chatbot';
import LegacyScripts from '@/components/LegacyScripts';
import { apiFetch } from '@/lib/api';
import CURRICULA_JSON from '@/lib/curricula.json';

/* eslint-disable @typescript-eslint/no-explicit-any, @next/next/no-img-element */
const W = () => window as any;

type Curriculum = {
  requirements?: string[];
  skills?: string[];
  instructor?: string;
  modules?: { title: string; lessons: string[] }[];
};
const CURRICULA = CURRICULA_JSON.CURRICULA as Record<string, Curriculum>;
const LESSON_URLS = CURRICULA_JSON.LESSON_URLS as Record<string, string>;

type LessonRow = { title: string; status: 'done' | 'current' | 'locked'; index: number };
type ModuleRow = { title: string; lessons: LessonRow[]; done_count: number; total: number; has_current: boolean };

export default function CourseDetailPage({ params }: { params: Promise<{ courseId: string }> }) {
  const { courseId } = use(params);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    // db_design* không vào route này (đã có route tĩnh) — guard giống main.py
    (async () => {
      try {
        // apiFetch (không phải fetch tương đối): pe-bridge chưa nạp ở thời điểm này
        // Lấy ĐÚNG một khoá thay vì tải cả danh sách rồi lọc ở client
        // (audit 2026-08-13) — gọn payload, bớt việc cho client.
        const [course, enrolled, stats, user]: any[] = await Promise.all([
          apiFetch(`/api/courses/${encodeURIComponent(courseId)}`).then((r) => (r.ok ? r.json() : null)),
          apiFetch('/api/enrolled').then((r) => (r.ok ? r.json() : [])),
          apiFetch('/api/stats').then((r) => (r.ok ? r.json() : {})),
          apiFetch('/api/user').then((r) => (r.ok ? r.json() : {})),
        ]);
        if (!course || !course.id) {
          window.location.replace('/dashboard');
          return;
        }
        const enrollment = Array.isArray(enrolled) ? enrolled.find((e: any) => e.id === courseId) : null;
        setData({ course, enrollment, streak: stats.streakDays || 0, userName: user.name || '—' });
      } catch {
        window.location.replace('/login');
      }
    })();
  }, [courseId]);

  if (!data) return null;

  const { course, enrollment, streak, userName } = data;
  const curriculum = CURRICULA[courseId] || {};
  const completed = enrollment ? enrollment.completedLessons || 0 : 0;
  const lessonUrl = LESSON_URLS[courseId] || `/lesson/${courseId}`;
  const progress = enrollment ? enrollment.progress || 0 : 0;

  // Port vòng tính status của main.py course_detail()
  let flatIdx = 0;
  const modules: ModuleRow[] = (curriculum.modules || []).map((module) => {
    const lessons: LessonRow[] = module.lessons.map((title) => {
      const status: LessonRow['status'] =
        flatIdx < completed ? 'done' : flatIdx === completed ? 'current' : 'locked';
      return { title, status, index: flatIdx++ };
    });
    const done_count = lessons.filter((l) => l.status === 'done').length;
    return {
      title: module.title,
      lessons,
      done_count,
      total: lessons.length,
      has_current: lessons.some((l) => l.status === 'current'),
    };
  });

  const totalLessons = course.lessons || 0;
  const ratingFill = Math.round(((course.rating || 0) / 5) * 1000) / 10;
  const image = `/${(course.image || '').replace(/^static\//, 'static/')}`;

  return (
    <>
      {/* theme.css ĐỨNG ĐẦU — chứa bộ token màu cho cả 2 theme. Thiếu nó thì
          var(--bg)/var(--card) vô định: ở theme tối body thành TRONG SUỐT
          (audit 2026-08-13). */}
      <PageStyles hrefs={["/static/css/theme.css","/static/css/style.css","/static/css/dashboard.css","/static/css/pages.css","/static/css/dark-mode.css","/static/css/chatbot.css","/static/css/course_detail.css","/static/css/a11y.css"]} />
      <title>{`${course.title} – ProgrammingEdu × TopHSA`}</title>
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />

      <div id="main">
        {/* Topbar (bản riêng của course_detail.html — khác base.html) */}
        <div className="topbar">
          <div className="topbar-left">
            <div className="brand brand-always" onClick={() => { window.location.href = '/dashboard'; }} style={{ cursor: 'pointer' }} title="Về trang chủ">
              <div className="brand-title"><span className="brand-c1">ProgrammingEdu</span> <span className="brand-x">×</span> <span className="brand-c2">TopHSA</span></div>
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
              {/* <button> chứ không <div> — xem chú thích ở components/Topbar.tsx.
                  Bản sao thứ hai của cùng khối này: sửa một chỗ mà bỏ chỗ kia thì
                  người dùng bàn phím vẫn kẹt, chỉ là kẹt ở một trang khác. */}
              <button type="button" className="user-chip" id="user-chip-btn" onClick={() => W().toggleUserMenu()} aria-haspopup="true" aria-expanded="false">
                <img src="/static/images/avatar.svg" alt="avatar" />
                <span className="chip-name">{userName}</span>
                <span className="dropdown-icon" id="chip-arrow">▾</span>
              </button>
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
              <span className="cd-tag">{course.tag}</span>
              <h1 className="cd-hero-title">{course.title}</h1>
              <p className="cd-hero-subtitle">{course.subtitle}</p>
              <div className="cd-meta">
                <div className="cd-meta-item">🕐 <span className="val">{course.duration}</span></div>
                <div className="cd-meta-item">📖 <span className="val">{course.lessons}</span> bài học</div>
                <div className="cd-meta-item">🎯 <span className="val">{course.level}</span></div>
              </div>
            </div>
            <div className="cd-hero-visual">
              <img src={image} alt={course.title} onError={(e) => { e.currentTarget.style.display = 'none'; }} />
            </div>
          </div>

          {/* Body */}
          <div className="cd-body">
            {/* Left column */}
            <div className="cd-main-col">
              {/* Block 1: Tổng quan */}
              <div className="cd-block">
                <div className="cd-block-hd">
                  <div className="cd-block-icon">📋</div>
                  <h3>Tổng quan khóa học</h3>
                </div>
                <div className="cd-block-body">
                  <p className="cd-desc">{course.description}</p>
                </div>
              </div>

              {/* Block 2: Giáo trình */}
              <div className="cd-block">
                <div className="cd-block-hd">
                  <div className="cd-block-icon">📚</div>
                  <h3>Giáo trình</h3>
                  <span style={{ marginLeft: 'auto', fontSize: 12, color: '#9CA3AF' }}>
                    {modules.length} module · {course.lessons} bài học
                  </span>
                </div>
                <div style={{ padding: 0 }}>
                  {modules.map((module, mi) => {
                    const open = module.has_current || mi === 0;
                    return (
                      <div className="cd-module" key={mi}>
                        <div className={`cd-module-hd ${open ? 'open' : ''}`} onClick={(e) => W().toggleModule(e.currentTarget)}>
                          <div className="cd-module-arrow">▶</div>
                          <div className="cd-module-name">{module.title}</div>
                          <div className="cd-module-meta">{module.total} bài</div>
                          {enrollment && module.done_count > 0 && (
                            <div className="cd-module-prog" style={{ marginLeft: 8 }}>{module.done_count}/{module.total} ✓</div>
                          )}
                        </div>
                        <div className={`cd-module-body ${open ? 'open' : ''}`}>
                          <div className="cd-lesson-list">
                            {module.lessons.map((lesson) => (
                              <div
                                className={`cd-lesson ${lesson.status}`}
                                key={lesson.index}
                                id={lesson.status === 'current' ? 'current-lesson' : undefined}
                                style={lesson.status !== 'locked' ? { cursor: 'pointer' } : undefined}
                                onClick={
                                  lesson.status !== 'locked'
                                    ? () => { window.location.href = `${lessonUrl}?lesson=${lesson.index}`; }
                                    : undefined
                                }
                              >
                                <div className="cd-lesson-icon">
                                  {lesson.status === 'done' ? '✓' : lesson.status === 'current' ? '▶' : '○'}
                                </div>
                                <div className="cd-lesson-title">{lesson.title}</div>
                                {lesson.status === 'current' ? (
                                  <span className="cd-lesson-badge">Tiếp tục</span>
                                ) : (
                                  <div className="cd-lesson-num">{lesson.index + 1}</div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    );
                  })}
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
                    {(curriculum.requirements || []).map((req, i) => (
                      <li key={i}>{req}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Block 4: Kỹ năng đạt được */}
              <div className="cd-block">
                <div className="cd-block-hd">
                  <div className="cd-block-icon">🏅</div>
                  <h3>Kỹ năng đạt được</h3>
                </div>
                <div className="cd-block-body">
                  <div className="cd-skills">
                    {(curriculum.skills || []).map((skill, i) => (
                      <div className="cd-skill-item" key={i}>
                        <div className="check">✓</div>
                        <span>{skill}</span>
                      </div>
                    ))}
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
                        <div className="star-avg-fill" data-fill={ratingFill}>★★★★★</div>
                      </div>
                    </div>
                    <div className="score">{course.rating}</div>
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

              {/* Block 6: Quiz ôn tập (FE-06) */}
              <div className="cd-block" id="review-quiz-block">
                <div className="cd-block-hd">
                  <div className="cd-block-icon">🧠</div>
                  <h3>Quiz ôn tập</h3>
                </div>
                <div className="cd-block-body">
                  {enrollment && completed >= 5 ? (
                    <>
                      <div id="quiz-idle">
                        <p>Ôn lại kiến thức đã học bằng 5-10 câu random từ các bài bạn đã hoàn thành.</p>
                        <button type="button" className="quiz-btn primary" onClick={() => W().startReviewQuiz(course.id)}>Bắt đầu ôn tập</button>
                      </div>
                      <div id="quiz-runner" style={{ display: 'none' }}></div>
                    </>
                  ) : (
                    <p className="cd-locked-note">🔒 Hoàn thành ít nhất 5 bài học để mở khóa quiz ôn tập.</p>
                  )}
                </div>
              </div>
            </div>

            {/* Right sidebar card */}
            <div className="cd-side-col">
              <div className="cd-card">
                <div className="cd-card-image">
                  <img src={image} alt={course.title} onError={(e) => { e.currentTarget.style.display = 'none'; }} />
                </div>
                <div className="cd-card-body">
                  <div className="cd-card-price">Miễn phí</div>
                  <div className="cd-card-free">🎉 Hoàn toàn không mất phí</div>

                  {enrollment ? (
                    <>
                      <div className="cd-progress-row">
                        <div className="cd-progress-label">
                          <span>Tiến độ</span>
                          <span className="pct">{progress}%</span>
                        </div>
                        <div className="cd-prog-bar">
                          <div className="cd-prog-fill" id="prog-fill" style={{ width: `${progress}%` }}></div>
                        </div>
                      </div>

                      <div className="cd-card-stats">
                        <div className="cd-cs">
                          <div className="v">{completed}</div>
                          <div className="l">Bài đã học</div>
                        </div>
                        <div className="cd-cs">
                          <div className="v">{totalLessons - completed}</div>
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

                      <button type="button" className="cd-enroll-btn continue" onClick={() => W().goLesson()}>▶ Tiếp tục học</button>
                      <button type="button" className="cd-enroll-btn unenroll" id="unenroll-btn" onClick={() => W().unenroll()}>Hủy đăng ký</button>
                    </>
                  ) : (
                    <button type="button" className="cd-enroll-btn primary" id="enroll-btn" onClick={() => W().enroll()}>
                      Đăng ký ngay – Miễn phí
                    </button>
                  )}

                  <div className="cd-includes">
                    <div className="cd-includes-title">KHÓA HỌC BAO GỒM</div>
                    <div className="cd-inc-item"><i className="fas fa-book-open"></i> {course.lessons} bài học</div>
                    <div className="cd-inc-item"><i className="fas fa-clock"></i> {course.duration}</div>
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
      {/* Globals cho course_detail.js — thay inline script Jinja của template gốc.
          <script> trong JSX không bao giờ được React thực thi (client component),
          nên gán qua LegacyScripts trước khi nạp file legacy. */}
      <LegacyScripts
        srcs={['/static/js/course_detail.js', '/static/js/review_quiz.js', '/static/js/chatbot.js']}
        globals={{
          COURSE_ID: course.id,
          CURRENT_LESSON_IDX: completed,
          LESSON_URL: lessonUrl,
        }}
      />
    </>
  );
}
