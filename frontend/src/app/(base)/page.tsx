// Port landing.html (extends base.html) — markup 1:1, giữ nguyên class/id.
// Nội dung đã rebrand sang ProgrammingEdu × TopHSA (luyện thi ĐGNL HSA).
// Inline script gốc (landing.html block extra_scripts) → /static/js/pages/landing.inline.js
import type { Metadata } from 'next';

import LegacyScripts from '@/components/LegacyScripts';

export const metadata: Metadata = {
  title: 'ProgrammingEdu × TopHSA — Luyện thi Đánh giá năng lực HSA',
};

export default function LandingPage() {
  return (
    <div className="landing-body-wrap">
      <BodyClass name="landing-body" />
      {/* block body_decor */}
      <div className="bg-canvas">
        <div className="bg-blob b1"></div>
        <div className="bg-blob b2"></div>
        <div className="bg-blob b3"></div>
        <div className="bg-blob b4"></div>
      </div>
      <div className="grid-overlay"></div>
      <div className="particles" id="landingParticles">
        <span className="particle particle-1"></span>
        <span className="particle particle-2"></span>
        <span className="particle particle-3"></span>
        <span className="particle particle-4"></span>
        <span className="particle particle-5"></span>
        <span className="particle particle-6"></span>
      </div>

      {/* block nav (landing override) */}
      <nav className="landing-nav">
        <div className="landing-logo">
          ProgrammingEdu <span className="red">× TopHSA</span>
        </div>
        <div className="nav-actions">
          <a href="/login" className="btn-outline">Đăng nhập</a>
          <a href="/register" className="btn-primary">Đăng ký miễn phí →</a>
        </div>
      </nav>

      {/* block content */}
      <section className="hero-section reveal-on-scroll">
        <div className="hero-content">
          <div className="hero-badge neon-badge">🎯 Luyện thi Đánh giá năng lực HSA · ĐHQG Hà Nội</div>

          <h1 className="hero-title neon-text">
            Chinh Phục <span className="neon-cyan">Đánh Giá Năng Lực</span>
            <br />
            Theo Cách <span className="neon-pink">Thông Minh</span>
          </h1>

          <p className="hero-sub fade-in-up delay-1">
            Từ Tư duy Định lượng đến Định tính và Khoa học — luyện đúng dạng câu hỏi HSA, bấm giờ như thi thật, theo lộ trình cá nhân hoá đúng năng lực của bạn.
          </p>

          <div className="hero-actions fade-in-up delay-2">
            <a href="/register" className="btn-main neon-btn">Bắt đầu miễn phí →</a>
            <a href="/login" className="btn-hero-outline glass-btn">Đăng nhập</a>
          </div>

          <div className="hero-stats fade-in-up delay-3">
            <div className="hero-stat">
              <div className="hero-stat-val neon-glow-text" id="stat-courses">—</div>
              <div className="hero-stat-lbl">Hợp phần</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-val neon-glow-text" id="stat-hours">—</div>
              <div className="hero-stat-lbl">Giờ luyện đề</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-val neon-glow-text">150</div>
              <div className="hero-stat-lbl">Câu mỗi đề</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-val neon-glow-text">CBT</div>
              <div className="hero-stat-lbl">Thi thử trên máy</div>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-section reveal-on-scroll">
        <div className="section-container">
          <h2 className="section-heading neon-text-sm">Luyện thi theo lộ trình cá nhân hoá</h2>
          <p className="section-sub">Chúng tôi định vị điểm mạnh — điểm yếu của bạn ở từng hợp phần, rồi thiết kế lộ trình luyện tập bám đúng cấu trúc đề Đánh giá năng lực ĐHQG Hà Nội. Học đúng chỗ cần, luyện đúng dạng, tiến bộ nhìn thấy được.</p>

          <div className="section-grid 3d-grid">
            <div className="section-card neon-card">
              <div className="card-icon neon-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
              </div>
              <strong>Chẩn đoán năng lực đầu vào</strong>
              <p>Bài test + bộ câu hỏi định vị điểm mạnh, điểm yếu của bạn ở từng hợp phần trước khi bắt đầu.</p>
            </div>
            <div className="section-card neon-card">
              <div className="card-icon neon-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>
              </div>
              <strong>Luyện đúng dạng câu hỏi HSA</strong>
              <p>Ngân hàng câu hỏi bám đúng cấu trúc đề ĐGNL, chia theo chủ đề và độ khó để bạn luyện có trọng tâm.</p>
            </div>
            <div className="section-card neon-card">
              <div className="card-icon neon-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="9" /><path strokeLinecap="round" strokeLinejoin="round" d="M12 7v5l3 2" /></svg>
              </div>
              <strong>Bấm giờ như phòng thi thật</strong>
              <p>Chế độ luyện tính giờ từng phần, rèn tốc độ xử lý và tâm lý làm bài dưới áp lực thời gian.</p>
            </div>
            <div className="section-card neon-card">
              <div className="card-icon neon-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              </div>
              <strong>Thi thử CBT &amp; phân tích</strong>
              <p>Đề đầy đủ 150 câu trên máy tính, chấm điểm ngay và chỉ rõ hợp phần bạn cần cải thiện.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-section reveal-on-scroll">
        <div className="section-container">
          <h2 className="section-heading neon-text-sm">Ba hợp phần đề HSA</h2>
          <p className="section-sub">Bắt đầu với đúng ba hợp phần của kỳ thi Đánh giá năng lực. Mỗi hợp phần có bài luyện theo dạng và chế độ bấm giờ như thi thật.</p>

          <div className="section-grid 3d-grid" id="course-preview-grid">
            <div className="section-card neon-card" id="course-preview-loading">
              <div className="card-icon neon-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></svg></div>
              <strong>Đang tải hợp phần…</strong>
              <p>Vui lòng chờ trong giây lát.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-section reveal-on-scroll">
        <div className="section-container">
          <h2 className="section-heading neon-text-sm">Bạn sẽ chinh phục những gì?</h2>
          <p className="section-sub">Toàn bộ phạm vi kỳ thi ĐGNL cùng những kỹ năng phòng thi quyết định điểm số — luyện đến đâu, thấy tiến bộ đến đó.</p>

          <div className="project-grid">
            <article className="project-card neon-card">
              <div className="project-thumb" style={{ background: 'linear-gradient(135deg, #8B5CF6 0%, #4C1D95 100%)' }}>
                <div className="project-thumb-icon">🔢</div>
              </div>
              <strong>Tư duy Định lượng</strong>
              <p>Đại số, hàm số, hình học, xác suất – thống kê và đọc số liệu theo đúng dạng đề HSA.</p>
              <span className="project-tag">Hợp phần 1 · Toán học</span>
            </article>
            <article className="project-card neon-card">
              <div className="project-thumb" style={{ background: 'linear-gradient(135deg, #F472B6 0%, #9D174D 100%)' }}>
                <div className="project-thumb-icon">✍️</div>
              </div>
              <strong>Tư duy Định tính</strong>
              <p>Đọc hiểu, từ vựng – ngữ pháp tiếng Việt và suy luận ngôn ngữ theo cấu trúc đề.</p>
              <span className="project-tag">Hợp phần 2 · Ngữ văn – Ngôn ngữ</span>
            </article>
            <article className="project-card neon-card">
              <div className="project-thumb" style={{ background: 'linear-gradient(135deg, #34D399 0%, #065F46 100%)' }}>
                <div className="project-thumb-icon">🔬</div>
              </div>
              <strong>Khoa học &amp; Tiếng Anh</strong>
              <p>Lý – Hoá – Sinh – Sử – Địa hoặc lựa chọn Tiếng Anh theo đúng định dạng HSA.</p>
              <span className="project-tag">Hợp phần 3 · Khoa học / English</span>
            </article>
            <article className="project-card neon-card">
              <div className="project-thumb" style={{ background: 'linear-gradient(135deg, #FBBF24 0%, #B45309 100%)' }}>
                <div className="project-thumb-icon">⏱️</div>
              </div>
              <strong>Tốc độ &amp; chiến thuật làm bài</strong>
              <p>Phân bổ thời gian, thứ tự làm bài và kỹ thuật loại trừ để tối ưu điểm số phòng thi.</p>
              <span className="project-tag">Kỹ năng · Chiến thuật</span>
            </article>
            <article className="project-card neon-card">
              <div className="project-thumb" style={{ background: 'linear-gradient(135deg, #2DD4BF 0%, #0F766E 100%)' }}>
                <div className="project-thumb-icon">🎯</div>
              </div>
              <strong>Lộ trình cá nhân hoá</strong>
              <p>Học đúng chỗ yếu, ưu tiên phần dễ lên điểm nhất dựa trên kết quả chẩn đoán của bạn.</p>
              <span className="project-tag">Lộ trình · Theo năng lực</span>
            </article>
            <article className="project-card neon-card">
              <div className="project-thumb" style={{ background: 'linear-gradient(135deg, #818CF8 0%, #3730A3 100%)' }}>
                <div className="project-thumb-icon">🖥️</div>
              </div>
              <strong>Thi thử CBT đầy đủ</strong>
              <p>Trải nghiệm phòng thi máy tính với 150 câu, chấm điểm và phân tích mạnh – yếu tức thì.</p>
              <span className="project-tag">Mock exam · 150 câu</span>
            </article>
          </div>
        </div>
      </section>

      <section className="landing-section reveal-on-scroll">
        <div className="section-container">
          <h2 className="section-heading neon-text-sm">Bạn sẽ đạt được gì sau khi luyện?</h2>
          <p className="section-sub">Tập trung vào kết quả rõ ràng cho kỳ thi Đánh giá năng lực: giải nhanh, đọc hiểu sắc bén và tự tin kiểm soát phòng thi.</p>

          <div className="section-grid 3d-grid">
            <div className="section-card neon-card">
              <span className="value-pill neon-pill">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" /><path strokeLinecap="round" strokeLinejoin="round" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" /></svg>
                Vững tư duy định lượng
              </span>
              <p>Giải nhanh các dạng toán ĐGNL, đọc biểu đồ – số liệu chính xác và không mất điểm oan.</p>
            </div>
            <div className="section-card neon-card">
              <span className="value-pill neon-pill">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
                Sắc bén ngôn ngữ &amp; đọc hiểu
              </span>
              <p>Nắm ý chính nhanh, suy luận chặt chẽ và dùng từ – ngữ pháp chuẩn trong hợp phần định tính.</p>
            </div>
            <div className="section-card neon-card">
              <span className="value-pill neon-pill">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                Tự tin trong phòng thi
              </span>
              <p>Quen giao diện thi CBT, kiểm soát thời gian và giữ tâm lý ổn định để phát huy hết năng lực.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-section reveal-on-scroll">
        <div className="section-container">
          <h2 className="section-heading neon-text-sm">Vì sao chọn ProgrammingEdu × TopHSA</h2>
          <p className="section-sub">Nền tảng luyện tập của ProgrammingEdu kết hợp kinh nghiệm luyện thi và ngân hàng đề của TopHSA — trung tâm chuyên Đánh giá năng lực ĐHQG Hà Nội.</p>

          <div className="testimonial-grid">
            <div className="testimonial-card glass-card trust-card">
              <div className="trust-stat">
                <div className="trust-stat-val neon-glow-text">100%</div>
                <div className="trust-stat-lbl">Miễn phí luyện tập cơ bản</div>
              </div>
              <div className="trust-stat">
                <div className="trust-stat-val neon-glow-text">3</div>
                <div className="trust-stat-lbl">Hợp phần theo đúng cấu trúc HSA</div>
              </div>
              <div className="trust-stat">
                <div className="trust-stat-val neon-glow-text">CBT</div>
                <div className="trust-stat-lbl">Thi thử trên máy, chấm điểm tức thì</div>
              </div>
            </div>
            <div className="testimonial-card glass-card trust-card">
              <p className="trust-quote">&quot;Luyện theo dạng và bấm giờ như thi thật giúp mình quen áp lực thời gian — vào phòng thi không còn bị cuống.&quot;</p>
              <div className="trust-note">Trải nghiệm từ nhóm học viên thử nghiệm — phần đánh giá đầy đủ đang được tích hợp.</div>
            </div>
            <div className="testimonial-card glass-card trust-card">
              <p className="trust-quote">&quot;Bài chẩn đoán đầu vào chỉ ra đúng chỗ mình yếu nhất, nên lộ trình luyện tập không bị dàn trải, lên điểm nhanh.&quot;</p>
              <div className="trust-note">Phản hồi từ nhóm pilot — chúng tôi đang thu thập đánh giá từ những học viên đầu tiên.</div>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-section cta-panel neon-cta reveal-on-scroll">
        <div className="section-container">
          <h2 className="neon-text-sm">Sẵn sàng cho kỳ thi Đánh giá năng lực?</h2>
          <p>Đăng ký miễn phí, làm bài chẩn đoán và nhận ngay lộ trình luyện thi HSA phù hợp với mục tiêu điểm số của bạn.</p>
          <div className="hero-actions">
            <a href="/register" className="btn-hero-primary neon-btn">Tham gia miễn phí</a>
            <a href="/login" className="btn-hero-outline glass-btn">Đã có tài khoản?</a>
          </div>
        </div>
      </section>

      {/* block footer */}
      <footer className="landing-footer">© 2026 ProgrammingEdu × TopHSA · Luyện thi Đánh giá năng lực HSA.</footer>

      {/* icons.js của base + inline script landing (block extra_scripts) */}
      <LegacyScripts srcs={['/static/js/icons.js', '/static/js/pages/landing.inline.js']} />
    </div>
  );
}

// base.html đặt class lên <body> qua block body_class — component nhỏ gắn/gỡ đúng class đó
function BodyClass({ name }: { name: string }) {
  return (
    <script
      dangerouslySetInnerHTML={{ __html: `document.body.classList.add(${JSON.stringify(name)});` }}
    />
  );
}
