'use client';

// Bài học HSA — luồng ĐẢO NGƯỢC (cô Hương): Kiểm tra → Đánh giá → Lý thuyết
// (thích ứng) → Ghi chú. TÁI DÙNG chrome/CSS của lesson_db_design (header,
// progress-track, step-pane, nav-footer, success-modal); logic ở lesson_hsa.js
// (engine riêng, KHÔNG đụng 9219 dòng DB). Data: lesson_content_hsa.js.
import { useEffect } from 'react';

import Chatbot from '@/components/Chatbot';
import LegacyScripts from '@/components/LegacyScripts';
import PageStyles from '@/components/PageStyles';
import { apiFetch } from '@/lib/api';

/* eslint-disable @typescript-eslint/no-explicit-any */
const W = () => window as any;

const STEPS = [
  { n: 1, label: 'Kiểm tra' },
  { n: 2, label: 'Đánh giá' },
  { n: 3, label: 'Lý thuyết' },
  { n: 4, label: 'Ghi chú' },
  { n: 5, label: 'Luyện tốc độ' },
];

export default function LessonHsa({ courseId }: { courseId: string }) {
  useEffect(() => {
    document.body.classList.add('lesson-focus-mode');
    document.body.setAttribute('data-course', courseId);
    return () => {
      document.body.classList.remove('lesson-focus-mode');
      document.body.removeAttribute('data-course');
    };
  }, [courseId]);

  useEffect(() => {
    apiFetch('/api/user').then((r) => (r.ok ? r.json() : null)).then((u) => {
      if (!u) return;
      const el = document.querySelector('.xp-text');
      if (el) el.textContent = `${u.xp || 0}/2000`;
    }).catch(() => {});
  }, []);

  const scripts = [
    'https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.2/dist/confetti.browser.min.js',
    '/static/js/lesson_content_hsa.js',
    '/static/js/lesson_hsa.js',
    '/static/js/chatbot.js',
  ];

  const eyebrow = (n: number, label: string) => (
    <div className="eyebrow-row">
      <span className="step-pill">Bước {n} / 5</span>
      <span className="topic-tag">{label}</span>
    </div>
  );

  return (
    <>
      {/* theme.css PHẢI nạp đầu tiên: nó chứa bộ token màu chung (--card,
          --t1…) cho cả 2 theme. Thiếu nó thì var(--card) rơi về fallback tối
          và thẻ câu hỏi vẫn đen dù đang ở theme sáng (audit 2026-08-13). */}
      <PageStyles hrefs={['/static/css/theme.css', '/static/css/lesson_db_design.css', '/static/css/lesson_hsa.css', '/static/css/chatbot.css']} />
      <title>Bài học HSA — ProgrammingEdu × TopHSA</title>
      <link rel="preconnect" href="https://cdnjs.cloudflare.com" />
      <link
        rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
      />

      <div className="scroll-progress" id="scroll-progress"></div>

      <header className="lesson-header">
        <button className="exit-btn" onClick={() => W().HSALesson?.exit()} title="Thoát bài học">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="header-center">
          <div className="progress-track" id="progress-track">
            {STEPS.map((s, i) => (
              <span key={s.n} style={{ display: 'contents' }}>
                <div className={'progress-step' + (s.n === 1 ? ' active' : '')} data-step={s.n}>
                  <span className="step-num">{s.n}</span>
                  <span className="step-label-tiny">{s.label}</span>
                  <span className="step-check"><i className="fa-solid fa-check"></i></span>
                </div>
                {i < STEPS.length - 1 && <div className="progress-connector"></div>}
              </span>
            ))}
          </div>
        </div>

        <div className="header-right">
          <div className="player-pill" title="Điểm kinh nghiệm">
            <div className="player-avatar"><i className="fa-solid fa-graduation-cap"></i></div>
            <div className="player-info">
              <div className="player-name">Sĩ tử HSA</div>
              <div className="player-meta"><span className="xp-text">0/2000</span></div>
            </div>
          </div>
        </div>
      </header>

      <main className="lesson-stage">
        {/* Bước 1: KIỂM TRA */}
        <section className="step-pane active" data-step="1">
          <article className="step-1-content">
            {eyebrow(1, 'Kiểm tra đầu vào — định vị năng lực')}
            <h1 className="lesson-title" id="lesson-title">Bài học</h1>
            <p className="hsa-intro" id="hsa-test-intro"></p>
            <div id="hsa-test-questions"></div>
          </article>
        </section>

        {/* Bước 2: ĐÁNH GIÁ */}
        <section className="step-pane" data-step="2">
          <article className="step-1-content">
            {eyebrow(2, 'Đánh giá năng lực — bạn đang ở đâu')}
            <div id="hsa-assess"></div>
          </article>
        </section>

        {/* Bước 3: LÝ THUYẾT */}
        <section className="step-pane" data-step="3">
          <article className="step-1-content">
            {eyebrow(3, 'Lý thuyết — thích ứng theo kết quả của bạn')}
            <div id="hsa-theory"></div>
          </article>
        </section>

        {/* Bước 4: GHI CHÚ */}
        <section className="step-pane" data-step="4">
          <article className="step-1-content">
            {eyebrow(4, 'Ghi chú — chốt lại để nhớ lâu')}
            <div id="hsa-notes"></div>
          </article>
        </section>

        {/* Bước 5: LUYỆN TỐC ĐỘ (gamified) */}
        <section className="step-pane" data-step="5">
          <article className="step-1-content">
            {eyebrow(5, 'Phòng luyện bấm giờ — nhanh & chính xác')}
            <div id="hsa-drill"></div>
          </article>
        </section>
      </main>

      <nav className="lesson-nav-footer" id="lesson-nav-footer">
        <button className="nav-btn nav-back" id="nav-back" onClick={() => W().HSALesson?.back()}
          ref={(el) => { if (el) el.disabled = true; }} aria-label="Quay lại">
          <i className="fa-solid fa-arrow-left"></i>
          <span className="nav-btn-label">Quay lại</span>
        </button>
        <button className="nav-btn nav-next" id="nav-next" onClick={() => W().HSALesson?.next()} aria-label="Tiếp theo">
          <span className="nav-btn-label">Nộp &amp; xem đánh giá</span>
          <i className="fa-solid fa-arrow-right"></i>
        </button>
      </nav>

      <div id="success-modal" className="modal-overlay hidden">
        <div className="success-card">
          <div className="success-icon"><i className="fa-solid fa-trophy"></i></div>
          <h2 className="success-title">Hoàn thành bài học!</h2>
          <div className="success-lesson-tag">
            <span className="success-lesson-title" id="success-lesson-title">—</span>
          </div>
          <p className="success-message" id="success-message"></p>
          <div className="success-rewards">
            <div className="reward">
              <div className="reward-icon"><i className="fa-solid fa-bolt"></i></div>
              <div className="reward-info">
                <div className="reward-value" id="reward-xp">+50</div>
                <div className="reward-label">XP</div>
              </div>
            </div>
          </div>
          <div className="success-actions">
            <button className="next-btn primary" onClick={() => W().HSALesson?.exit()}>
              Về trang chủ <i className="fa-solid fa-arrow-right"></i>
            </button>
          </div>
        </div>
      </div>

      {/* Trợ lý HSA phải theo học viên VÀO BÀI HỌC, không chỉ ở dashboard
          (audit 2026-08-14) — đây mới là lúc người học cần hỏi nhất. */}
      <Chatbot />

      <LegacyScripts srcs={scripts} />
    </>
  );
}
