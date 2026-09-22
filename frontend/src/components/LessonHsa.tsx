'use client';

// Bài học HSA — luồng ĐẢO NGƯỢC (cô Hương): Kiểm tra → Đánh giá → Lý thuyết
// (thích ứng) → Ghi chú. TÁI DÙNG chrome/CSS của lesson_db_design (header,
// progress-track, step-pane, nav-footer, success-modal); logic ở lesson_hsa.js
// (engine riêng, KHÔNG đụng 9219 dòng DB). Data: CSDL qua API nội dung.
import { useEffect } from 'react';

import Chatbot from '@/components/Chatbot';
import LegacyScripts, { CAU_NOI } from '@/components/LegacyScripts';
import NapTruocScript from '@/components/NapTruocScript';
import PageStyles from '@/components/PageStyles';
import { ghiNhomVai } from '@/lib/nhomVai';
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
      ghiNhomVai(u.role);   // trang này không có AppShell — tự đặt nhóm vai (lib/nhomVai.ts)
      const el = document.querySelector('.xp-text');
      if (el) el.textContent = `${u.xp || 0}/2000`;
    }).catch(() => {});
  }, []);

  /* Hộp "Hoàn thành bài học" mở (engine bỏ lớp `hidden`) → phần còn lại của
     trang `inert` và tiêu điểm vào nút đầu tiên của hộp ("Bài tiếp theo" khi
     còn bài, không thì "Về trang chủ"). Theo dõi lớp thay vì sửa engine: tầng
     cũ chỉ được co lại (chot-ham-tang-cu). */
  useEffect(() => {
    const hop = document.getElementById('success-modal');
    if (!hop) return;
    const sau = () => ['.lesson-header', '.lesson-stage', '.lesson-nav-footer']
      .map((c) => document.querySelector<HTMLElement>(c)).filter((e): e is HTMLElement => !!e);
    const theo = new MutationObserver(() => {
      const mo = !hop.classList.contains('hidden');
      sau().forEach((e) => { e.inert = mo; });
      if (mo) hop.querySelector<HTMLElement>('.success-actions .next-btn:not(.hidden)')?.focus();
    });
    theo.observe(hop, { attributes: true, attributeFilter: ['class'] });
    return () => theo.disconnect();
  }, []);

  /* ENGINE TRƯỚC, confetti SAU (20/09/2026). `LegacyScripts` nạp theo thứ tự,
     sau hydrate. Bản trước để confetti (jsdelivr, miền khác) đứng đầu, nên
     engine — thứ VẼ nội dung bài, phần tử LCP — phải chờ một lượt tải + chạy
     146 ms của thứ chỉ dùng khi HOÀN THÀNH bài (Lighthouse production: long
     task confetti ở 5,3 s, engine sau đó). `window.confetti` được engine hỏi
     `if (window.confetti)` lúc dùng, nên tới muộn không sao.
     lesson_content_hsa.js ĐÃ BỎ (2026-08-19): 76 bài nay nằm trong CSDL.
     chatbot.js ĐÃ BỎ (20/09/2026): trợ lý nay là React. */
  const scripts = [
    '/static/js/lesson_hsa.js',
    'https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.2/dist/confetti.browser.min.js',
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
      <PageStyles hrefs={['/static/css/theme.css', '/static/css/lesson_chrome.css', '/static/css/lesson_hsa.css', '/static/css/chatbot.css', '/static/css/a11y.css']} />
      <title>Bài học HSA — ProgrammingEdu × TopHSA</title>
      {/* Tải trước cầu nối + engine ngay từ HTML: `LegacyScripts` chỉ chèn thẻ
          script sau hydrate — lúc ấy tệp đã nằm sẵn trong bộ đệm (cùng lối với
          Trang của tôi). */}
      <NapTruocScript srcs={[CAU_NOI, ...scripts]} />
      {/* NẠP TRƯỚC NỘI DUNG BÀI ngay lúc HTML được phân tích (20/09/2026).
          Lighthouse (mobile, production): phần tử LCP của trang là câu dẫn bước 1
          do `lesson_hsa.js` vẽ, và 88% thời gian LCP (4,5 s) là "render delay" —
          chuỗi nối tiếp: tải JS → chạy → mới gọi `/api/courses/…/content` → về →
          vẽ. Script này bắn lượt gọi ấy từ dòng đầu của HTML, cùng ổ khoá
          `window.__napTruoc` mà Trang của tôi dùng (`NapTruocDuLieu`); engine tìm
          ở đó trước khi tự fetch. Số bài đọc từ `location.search` vì trang là
          client component, không có `searchParams` ở máy chủ. Chỉ nạp trước khi
          THÀNH CÔNG (`r.ok`); lỗi 403/404 để engine tự gọi lại và đọc đúng lý do. */}
      <script
        dangerouslySetInnerHTML={{
          __html:
            `(function(){var n=parseInt(new URLSearchParams(location.search).get('lesson'),10);if(isNaN(n)||n<1)n=1;`
            + `var x='/api/courses/'+encodeURIComponent(${JSON.stringify(courseId)})+'/content?lesson='+n;`
            + `window.__napTruoc=window.__napTruoc||{};window.__napTruoc[x]=fetch(x,{credentials:'same-origin'})`
            + `.then(function(r){return r.ok?r.json():null}).catch(function(){return null})})();`,
        }}
      />
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
        {/* `tabIndex={0}` trên MỌI bước: bước đang mở là vùng cuộn, và vùng cuộn
            không nhận tiêu điểm thì bàn phím không cuộn được (axe-core
            `scrollable-region-focusable`, WCAG 2.1.1 — mức SERIOUS, 20/09/2026).

            Bước ĐANG ẨN thì `inert` (21/09/2026). Bước ẩn chỉ là `opacity:0;
            pointer-events:none` — chặn CHUỘT, không chặn BÀN PHÍM: từ nút "Tiếp
            tục" phải Tab 14 lần mới tới bước 2, 10 lần trong đó tiêu điểm nằm ở
            phần tử vô hình; đang ở bước 3 mà Space trên phương án bước 1 (ẩn)
            thì đáp án đã chấm đổi luôn (agent tc3 F5). `lesson_hsa.js::goToStep`
            bật/tắt `inert` cùng lúc với lớp `active`. */}
        <section className="step-pane active" data-step="1" tabIndex={0}>
          <article className="step-1-content">
            {eyebrow(1, 'Kiểm tra đầu vào — định vị năng lực')}
            <h1 className="lesson-title" id="lesson-title">Bài học</h1>
            <p className="hsa-intro" id="hsa-test-intro"></p>
            <div id="hsa-test-questions"></div>
          </article>
        </section>

        {/* Bước 2: ĐÁNH GIÁ */}
        <section className="step-pane" data-step="2" tabIndex={0} inert>
          <article className="step-1-content">
            {eyebrow(2, 'Đánh giá năng lực — bạn đang ở đâu')}
            <div id="hsa-assess"></div>
          </article>
        </section>

        {/* Bước 3: LÝ THUYẾT */}
        <section className="step-pane" data-step="3" tabIndex={0} inert>
          <article className="step-1-content">
            {eyebrow(3, 'Lý thuyết — thích ứng theo kết quả của bạn')}
            <div id="hsa-theory"></div>
          </article>
        </section>

        {/* Bước 4: GHI CHÚ */}
        <section className="step-pane" data-step="4" tabIndex={0} inert>
          <article className="step-1-content">
            {eyebrow(4, 'Ghi chú — chốt lại để nhớ lâu')}
            <div id="hsa-notes"></div>
          </article>
        </section>

        {/* Bước 5: LUYỆN TỐC ĐỘ (gamified) */}
        <section className="step-pane" data-step="5" tabIndex={0} inert>
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
        {/* Không `aria-label`: tên nút lấy từ nhãn đang hiện, vốn đổi theo bước
            ("Nộp & xem đánh giá" / "Tiếp tục" / "Hoàn thành bài học"). Nhãn cố
            định "Tiếp theo" từng đọc cùng một chữ cho cả ba việc khác nhau. */}
        <button className="nav-btn nav-next" id="nav-next" onClick={() => W().HSALesson?.next()}>
          <span className="nav-btn-label">Nộp &amp; xem đánh giá</span>
          <i className="fa-solid fa-arrow-right"></i>
        </button>
      </nav>

      {/* HỘP THOẠI THẬT (21/09/2026): bản cũ không `role`, tiêu điểm ở lại nút
          "Hoàn thành" phía sau, Tab đi ra sau lớp phủ và trình đọc màn hình
          không được báo gì (agent tc3 F10). Mở/đóng do `lesson_hsa.js` bật lớp
          `hidden`; phần giữ tiêu điểm ở `useEffect` phía trên. */}
      <div id="success-modal" className="modal-overlay hidden">
        <div className="success-card" role="dialog" aria-modal="true" aria-labelledby="success-title">
          <div className="success-icon"><i className="fa-solid fa-trophy"></i></div>
          <h2 className="success-title" id="success-title">Hoàn thành bài học!</h2>
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
            {/* Lối sang BÀI KẾ (21/09/2026): hộp này từng chỉ có "Về trang chủ",
                nên mỗi bài học viên phải vòng qua Trang của tôi rồi tìm khối
                Học tiếp — thêm hai chạm và một lần tải trang. `lesson_hsa.js`
                (`complete`) điền địa chỉ và bỏ `hidden` khi khoá còn bài sau;
                bài cuối khoá thì nút này ở ẩn. Khi nó hiện, "Về trang chủ" lùi
                thành nút phụ (lesson_chrome.css, `.success-actions`). */}
            <a id="success-next" className="next-btn primary hidden" href="#">
              Bài tiếp theo <i className="fa-solid fa-arrow-right"></i>
            </a>
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
