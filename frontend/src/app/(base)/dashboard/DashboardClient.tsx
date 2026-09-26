'use client';

// Port dashboard.html (extends base.html) — SPA-hub: các "trang" Dashboard/
// Khóa học/Lộ trình/Kỹ năng/Diễn đàn/Cài đặt/Trang của tôi chuyển client-side
// bằng main.js navigate() trong CÙNG route này (không tách route Next — giữ UX cũ).
// CSS đúng tổ hợp gốc (dashboard.html block extra_head, thứ tự giữ nguyên).

import { useEffect, useRef, useState } from 'react';
import { flushSync } from 'react-dom';

import PageStyles from '@/components/PageStyles';
import BaHopPhan from '@/components/BaHopPhan';
import Chatbot from '@/components/Chatbot';
import KhoaLienHePhuHuynh from '@/components/KhoaLienHePhuHuynh';
import LegacyScripts, { CAU_NOI } from '@/components/LegacyScripts';
import NapTruocDuLieu from '@/components/NapTruocDuLieu';
import NapTruocScript from '@/components/NapTruocScript';
import RoadmapSection from '@/components/RoadmapSection';
import AppShell from '@/components/AppShell';
import { BieuTuong } from '@/components/bieuTuong';
import KhuNhanSu from '@/components/KhuNhanSu';
import { useVaiHienTai } from '@/lib/useVaiHienTai';
import { NHAN_VAI } from '@/lib/vaiTro';

/* eslint-disable @typescript-eslint/no-explicit-any, @next/next/no-img-element */
const W = () => window as any;

// Thứ tự script y hệt cuối dashboard.html; icons.js vốn nằm ở <head> base.html.
// GỠ 30/08/2026: mermaid (3,41 MB) và svg-pan-zoom (29 kB) từng nằm giữa
// icons.js và roadmapData.js. Cả hai không được dùng — xem ghi chú dài trong
// public/static/js/main.js. Đây là 3,44 MB cắt khỏi mọi lượt mở dashboard.
const SCRIPTS = [
  '/static/js/icons.js',
  '/static/js/roadmapData.js',
  '/static/js/roadmap.js',
  '/static/js/main.js',
  '/static/js/dashboard.js',
];

/**
 * Thân TRANG CỦA TÔI — phần chạy ở trình duyệt.
 *
 * Vỏ máy chủ nằm ở `page.tsx` (14/09/2026): nó dựng những khối CẦN DỮ LIỆU
 * NGAY TRONG HTML ĐẦU TIÊN — thẻ "Học tiếp" (phần tử LCP) và "Lớp của bạn" —
 * rồi truyền xuống đây như hai nút React. Phần còn lại vẫn client y như cũ, vì
 * SPA cũ (`main.js::navigate`) đổi tab bằng class chứ không đổi route.
 */
export default function DashboardClient(
  { hocTiep, lopCuaBan, nhiemVu, theSo, tienDo }: {
    hocTiep: React.ReactNode; lopCuaBan: React.ReactNode; nhiemVu: React.ReactNode;
    theSo: React.ReactNode; tienDo: React.ReactNode;
  },
) {
  /* Vai thật cho nhãn ở Cài đặt (24/09/2026): nhãn từng gõ cứng "Học viên" nên
     quản trị viên, giảng viên mở Cài đặt cũng thấy mình là "Học viên" (khách thử
     tài khoản giáo viên thấy). Đọc từ `window.__currentUser` mà `main.js` đã nạp. */
  const vai = useVaiHienTai(undefined, true);
  /* ── DỰNG LƯỜI BẢY TRANG CÒN LẠI + khối lộ trình (16/09/2026) ──────────
     Trang này là hub SPA cũ: chín "trang" nằm cùng một route, tám trong số đó
     `display:none`. Dựng sẵn cả chín nghĩa là React hydrate cả chín — chi phí
     người dùng trả ngay lần mở đầu, cho bảy trang phần lớn họ không mở.

     `main.js::navigate()` gọi `window.__moTrang(trang)` TRƯỚC khi đổi class.
     `flushSync` là bắt buộc: các module trong `dashboard.js` bọc `navigate` theo
     khuôn `orig(page); if (page === 'forum') renderPosts();` — chúng chạy NGAY
     SAU `orig`, nên DOM của trang vừa mở phải có mặt trong cùng một nhịp, không
     đợi được React vẽ ở nhịp sau.

     HAI TRANG KHÔNG TỰ NẠP LẠI KHI MỞ. Bảy trang kia có module trong `dashboard.js`
     bọc `navigate` để nạp khi mở. Lưới khoá học thì do `loadAll()` dựng MỘT lần lúc
     vào trang, các ô ở Cài đặt do `loadUser()` điền MỘT lần — hai lần ghi ấy rơi vào
     chỗ chưa có DOM. Nên sau khi dựng, gọi lại hai hàm của tầng cũ (`renderCourses`,
     `setText` là hàm ở cột 0 của script cổ điển → thuộc tính `window`); cả hai tự
     bỏ qua khi thiếu phần tử. Logic này nằm ở ĐÂY chứ không ở `main.js`: tầng cũ
     chỉ được nhỏ đi (`e2e/unit/chot-ham-tang-cu`).

     ĐƯỜNG VÀO SÂU (`/dashboard#forum`): `main.js` đọc hash và gọi `navigate` — có
     thể TRƯỚC khi React hydrate xong (nó được nạp sớm có chủ ý), lúc chưa có
     `__moTrang` để dựng. Hiệu ứng dưới đây đọc lại hash lúc hydrate xong, dựng,
     rồi gọi `navigate` lại; thứ tự ngược (main.js nạp sau) cũng đúng, vì khi ấy
     `navigate` của nó đã thấy `__moTrang`. CHỈ làm với trang chưa dựng: gọi lại
     `navigate('dashboard')` là chạy lại MỌI module bọc `navigate` lần hai — đo được
     +10 lượt gọi mạng và CLS 0,004 → 0,044 (16/09/2026). */
  const [daMo, setDaMo] = useState<Set<string>>(() => new Set(['dashboard']));
  const daMoRef = useRef(daMo);

  useEffect(() => {
    const w = W();
    const sauKhiDung = (trang: string) => {
      /* VẼ BIỂU TƯỢNG của trang vừa dựng (22/09/2026, agent tiếp cận F12).
         `icons.js` quét `[data-icon]` MỘT lần lúc DOMContentLoaded. Vào thẳng
         `/dashboard#courses` thì trang được dựng TRƯỚC lượt quét ấy nên đủ biểu
         tượng; đi bằng MENU thì trang dựng lười ở đây, SAU lượt quét — và không
         ai quét lại: đo được Khoá học thiếu 7, Cài đặt 7, Lộ trình 3 (nút Đóng
         của ngăn chi tiết thành ô vuông trống). Gọi lại bộ vẽ cho đúng trang
         vừa dựng, ở cả hai đường (menu và hash) — vẽ lại ô đã có SVG là vô hại. */
      const khoi = document.getElementById('page-' + trang);
      if (khoi && typeof w.mountIcons === 'function') w.mountIcons(khoi);
      if (trang === 'courses' && typeof w.renderCourses === 'function') w.renderCourses();
      if (trang === 'settings' && w.__currentUser && typeof w.setText === 'function') {
        const u = w.__currentUser;
        w.setText('settings-profile-name', u.name);
        w.setText('settings-profile-email', u.email);
        document.querySelectorAll<HTMLInputElement>('[data-ho-so]').forEach((o) => {
          o.value = u[o.getAttribute('data-ho-so') || ''] || '';
        });
      }
    };
    w.__moTrang = (trang: string) => {
      if (!trang || daMoRef.current.has(trang)) return;
      const moi = new Set(daMoRef.current).add(trang);
      daMoRef.current = moi;
      flushSync(() => setDaMo(moi));
      sauKhiDung(trang);
    };
    const hash = window.location.hash.replace('#', '');
    if (hash && !daMoRef.current.has(hash) && /^[\w-]+$/.test(hash)) {
      const moi = new Set(daMoRef.current).add(hash);
      daMoRef.current = moi;
      setDaMo(moi);
      // Đổi class sau khi React đã vẽ xong trang vừa mở. `navigate` không tồn tại
      // nếu main.js chưa nạp — khi ấy chính main.js sẽ gọi nó lúc nạp xong.
      requestAnimationFrame(() => {
        if (typeof w.navigate !== 'function') return;
        w.navigate(hash);
        sauKhiDung(hash);   // `__moTrang` sẽ thấy trang đã dựng và bỏ qua — gọi ở đây
      });
    }
    /* CỜ "chưa ghi danh khoá nào" trong PHIÊN (21/09/2026). Máy chủ đặt cờ lần
       đầu (`HocTiep::CoChuaGhiDanh`); nhưng em có thể ghi danh ngay ở view Khoá
       học rồi quay lại đây mà không tải lại trang. Tín hiệu có sẵn:
       `main.js::renderDashProgress` bật/tắt thuộc tính `hidden` của
       `#dash-progress-empty` theo đúng `enrolledCourses`. Theo dõi thuộc tính ấy
       thay vì thêm lượt gọi API hay thêm dòng vào tầng cũ (tầng cũ chỉ được
       nhỏ đi — `e2e/unit/chot-ham-tang-cu`). */
    const trang = document.getElementById('page-dashboard');
    const oRong = document.getElementById('dash-progress-empty');
    let theoDoi: MutationObserver | undefined;
    if (trang && oRong) {
      theoDoi = new MutationObserver(() => {
        trang.classList.toggle('chua-ghi-danh', !(oRong as HTMLElement).hidden);
      });
      theoDoi.observe(oRong, { attributes: true, attributeFilter: ['hidden'] });
    }
    return () => { theoDoi?.disconnect(); delete w.__moTrang; };
  }, []);

  return (
    <>
      <PageStyles hrefs={["/static/css/shell.css","/static/css/style.css","/static/css/dashboard.css","/static/css/pages.css","/static/css/ChangePassword.css","/static/css/skeleton.css","/static/css/dark-mode.css","/static/css/roadmap.css","/static/css/a11y.css"]} />
      {/* TẢI TRƯỚC bảy tệp JS cũ, ngay từ HTML máy chủ trả về.
          `LegacyScripts` chèn chúng trong `useEffect` nên chúng chỉ bắt đầu
          tải SAU khi React hydrate — đo được 1,4 giây trang trắng (load xong
          759ms, FCP 2184ms). Xem `NapTruocScript.tsx`.
          CÙNG một mảng `SCRIPTS` cho cả hai; hai mảng chép tay sẽ trôi. */}
      <NapTruocScript srcs={[CAU_NOI, ...SCRIPTS]} />
      {/* Bắn sẵn ba lượt GET dựng nội dung trên màn hình đầu. Tầng cũ chỉ chạy
          sau khi React hydrate (2,2 s trên máy CPU chậm 4×) — không có dòng
          này thì hai giây ấy mạng ngồi không. Xem `NapTruocDuLieu`. */}
      <NapTruocDuLieu />
      <title>TopHSA</title>
      {/* Khung chung — CÙNG component với màn khoá học và màn thi thử.
          `spa`: trang này có main.js nên điều hướng bằng `navigate()`.
          `dieuKhien="legacy"`: dashboard.js sở hữu menu người dùng và
          chuông (kể cả bấm-ra-ngoài và phím Escape) — đừng dựng lại. */}
      <AppShell trang="dashboard" spa dieuKhien="legacy" />

      {/* `<main>` chứ không `<div>`: mốc trang cho trình đọc màn hình (axe
          `landmark-one-main`, 20/09/2026). CSS/JS bám `#main` nên không đổi gì.
          h1 `sr-only`: trang không có tiêu đề nhìn thấy nào ngoài lời chào. */}
      <main id="main">
        <h1 className="sr-only">Trang của tôi</h1>
        {/* ── Dashboard ── */}
        <div className="page active" id="page-dashboard">
          {/* Nhân sự thấy khu làm việc của vai mình; mọi khối luyện thi bên dưới
              mang `data-chi-hoc-vien` và ẩn với họ (20/09/2026, `lib/nhomVai.ts`). */}
          <KhuNhanSu />

          {/* Hero banner */}
          <div className="dash-hero fx-fade-up" data-chi-hoc-vien="">
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

          {/* Khối GỘP cho học viên chưa ghi danh khoá nào (21/09/2026, anh Sơn
              chốt). Trước đó trang dài 4,3 màn ở 390px với bốn khối rỗng
              ("Lộ trình", "Nên ôn tiếp", "Tiến độ theo hợp phần", "Tiến độ học
              tập") và bốn lời mời "Khám phá khoá học" ở bốn chỗ khác nhau.
              `main.js::renderDashProgress` gắn `chua-ghi-danh` lên #page-dashboard
              khi `enrolledCourses` rỗng; CSS ẩn bốn khối kia và hiện khối này,
              đồng thời thu bảng xếp hạng còn Top 3. Ghi danh xong: y như cũ. */}
          <div className="section-card dash-bat-dau fx-fade-up" id="dash-bat-dau" data-chi-hoc-vien="">
            <div className="section-title" style={{ marginBottom: 10 }}>
              <span className="title-icon-blue"><BieuTuong ten="compass" co={16} /></span>
              <span>Bắt đầu hành trình HSA</span>
            </div>
            <p className="dash-bat-dau-sub">
              Chọn một môn học để mở bài học, lộ trình và tiến độ của riêng bạn. Cả ba môn đều miễn phí.
            </p>
            <ol className="dash-bat-dau-buoc">
              <li>Chọn môn học bạn muốn chắc trước — Định lượng, Định tính hoặc Khoa học &amp; Tiếng Anh.</li>
              <li>Làm bài kiểm tra đầu vào ba câu; hệ thống chấm rồi chọn bản lý thuyết vừa sức bạn.</li>
              <li>Lộ trình, tiến độ và phần &ldquo;nên ôn tiếp&rdquo; sẽ hiện ngay tại trang này.</li>
            </ol>
            <button type="button" className="dash-bat-dau-btn" onClick={() => W().navigate('courses')}>
              Khám phá khóa học <span data-icon="arrow-right" data-size="13"></span>
            </button>
          </div>

          {/* ── Hàng thẻ số liệu (audit 2026-08-14) ──
              Trước đây màn hình đầu bị "Lịch học tuần này" chiếm trọn một hàng
              ngang còn lộ trình thì teo lại. Nay 4 chỉ số quan trọng nhất lên
              trên cùng, lịch học thu thành dải 7 chấm ngay trong thẻ streak.
              dashboard.js đổ số vào qua /api/hsa/summary. */}
          {/* Bốn thẻ số dựng ở máy chủ (`components/TheSoHsa.tsx`, 14/09/2026 tối);
              phần client đăng ký lại `window.__refreshHsaTiles` cho nút "Nhận"
              nhiệm vụ và nút lưu mục tiêu ở Cài đặt. */}
          <div className="hsa-tiles fx-fade-up" style={{ animationDelay: '.04s' }} data-chi-hoc-vien="">
            {theSo}
          </div>

          {/* Cột trái: học tiếp + tiến độ 3 hợp phần · Cột phải: lộ trình */}
          <div className="dash-row dash-row--cal" data-chi-hoc-vien="">
            <div className="dash-col-left">
              {/* Lớp của bạn — đứng TRÊN "học tiếp": buổi tối nay là việc có
                  giờ, bài học thì lúc nào cũng làm được. Không ở lớp nào thì
                  khối không dựng gì (14/09/2026). */}
              {lopCuaBan}
              {/* Thẻ "Học tiếp" dựng Ở MÁY CHỦ (`components/HocTiep.tsx`, 14/09/2026)
                  và truyền vào đây như một nút React — trước đó
                  `dashboard.js::renderContinue` vẽ nó SAU khi hydrate (2,2–2,5 s),
                  mà đây chính là phần tử LCP của trang. `id` giữ nguyên: CSS và
                  bộ đo giao diện đều bám vào nó. */}
              <div className="section-card hsa-continue fx-fade-up" id="hsa-continue" style={{ animationDelay: '.08s' }}>
                {hocTiep}
              </div>

              {/* Nhiệm vụ hôm nay — cho chuỗi ngày học có việc để làm, thay vì
                  chỉ đếm số ngày (audit 2026-08-14). */}
              <div className="section-card fx-fade-up" style={{ animationDelay: '.1s' }}>
                <div className="section-title" style={{ marginBottom: 14 }}>
                  {/* `BieuTuong` chứ không `data-icon`: khối bên dưới chảy tới sau,
                      ô trống sẽ bị `mountIcons` điền trước khi React hydrate. */}
                  <span className="title-icon-blue"><BieuTuong ten="check" co={16} /></span>
                  <span>Nhiệm vụ hôm nay</span>
                </div>
                {/* Dựng ở máy chủ (`components/NhiemVu.tsx`, 14/09/2026); `id`
                    giữ để CSS cũ và bộ đo giao diện còn bám. */}
                <div className="hsa-missions" id="hsa-missions">{nhiemVu}</div>
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

            </div>

            {/* CỘT PHẢI (20/09/2026). Trước đó cột phải chỉ có thẻ lộ trình
                327px rồi TRỐNG ~1.400px suốt chiều cao cột trái (đo 1366).
                "Nên ôn tiếp" và "Tiến độ theo hợp phần" là hai thẻ NHÌN LẠI —
                hợp với lộ trình hơn là với việc hằng ngày ở cột trái. Ở khổ một
                cột chúng đứng ngay sau lộ trình. */}
            <div className="dash-col-right">
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
              {/* Ba chủ đề yếu nhất, mỗi chủ đề đúng MỘT nút. Biết mình yếu ở
                  đâu mà không có đường đi tiếp thì thông tin đó chưa dùng được.
                  dashboard.js đổ vào từ /api/hsa/competency. */}
              <div className="section-card fx-fade-up" id="the-nen-on-tiep" style={{ animationDelay: '.11s' }}>
                <div className="section-title" style={{ marginBottom: 14 }}>
                  <span className="title-icon-blue" data-icon="target" data-size="16"></span>
                  <span>Nên ôn tiếp</span>
                </div>
                <div className="hsa-weak" id="hsa-weak">
                  <div className="hsa-mis-empty">Đang tính…</div>
                </div>
              </div>

              <div className="section-card fx-fade-up" id="the-tien-do-hop-phan" style={{ animationDelay: '.12s' }}>
                <div className="section-title" style={{ marginBottom: 14 }}>
                  <span className="title-icon-blue"><BieuTuong ten="bar-chart" co={16} /></span>
                  <span>Tiến độ theo môn học</span>
                </div>
                {/* Dựng ở máy chủ (`components/TienDoHopPhan.tsx`, 14/09/2026 tối). */}
                <div className="hsa-sections" id="hsa-sections">{tienDo}</div>
              </div>
            </div>
          </div>
          <div className="cal-tooltip" id="cal-tooltip"></div>

          {/* Row 2: Tiến độ học tập — MỘT cột. Thẻ Bảng xếp hạng từng đứng bên trái
              đã ẩn (24/09/2026, anh Sơn chốt theo góp ý TopHSA: màn đầu nhiều thông
              tin, và xếp hạng XP giữa các em không phải việc chính của trung tâm).
              Hạng của RIÊNG em vẫn ở Hồ sơ. */}
          <div className="dash-row dash-row--lb dash-row--mot" data-chi-hoc-vien="">

            <div className="section-card dash-progress-card fx-fade-up" style={{ animationDelay: '.15s' }}>
              <div className="section-title" style={{ marginBottom: 0 }}>
                <span className="title-icon-blue">📋</span><span>Tiến độ học tập</span>
              </div>
              <div className="dash-progress-empty" id="dash-progress-empty">
                <span className="dash-progress-icon" data-icon="book-open" data-size="20" data-color="#60A5FA"></span>
                <p>Chưa có môn nào mở cho lớp của em</p>
                <span className="dash-progress-sub">Trung tâm mở môn khi xếp em vào lớp.</span>
                <button className="dash-progress-btn" onClick={() => W().navigate('courses')}>Xem các môn →</button>
              </div>
              {/* Danh sách tiến độ thật (bảng enrollments) — main.js renderDashProgress() đổ vào */}
              <div className="dash-progress-list" id="dash-progress-list" hidden></div>
            </div>
          </div>
        </div>

        {/* ── Khu giảng dạy (Giảng viên / Quản trị viên) ── */}
        {daMo.has('teach') && (
        <div className="page" id="page-teach">
          <div className="courses-header fx-fade-up">
            <div>
              <h2>👩‍🏫 Giảng dạy</h2>
              <p className="courses-subtitle">
                Lớp bạn phụ trách, ai đang cần chú ý, và hồ sơ học tập của từng học viên.
              </p>
            </div>
            {/* Lối vào trang "Việc hôm nay" (14/09/2026) — gom mọi lớp: buổi
                chưa điểm danh, bài chưa chấm, em vắng liền. Đặt ở đầu khu vì
                đó là câu hỏi đầu tiên mỗi tối; thẻ neo thường, không qua SPA. */}
            <a className="tc-link" href="/giang-day">Việc hôm nay →</a>
          </div>
          <div className="tc-wrap">
            <div className="section-card tc-side fx-fade-up">
              <div className="section-title" style={{ marginBottom: 12 }}>
                <span className="title-icon-blue" data-icon="users" data-size="16"></span>
                <span>Lớp của tôi</span>
              </div>
              <div className="tc-classes" id="tc-classes">
                <div className="tc-empty">Đang tải…</div>
              </div>
            </div>
            <div className="tc-main">
              <div className="section-card fx-fade-up" style={{ animationDelay: '.05s' }}>
                <div className="tc-report" id="tc-report">
                  <div className="tc-empty">Chọn một lớp để xem báo cáo.</div>
                </div>
              </div>
              <div className="section-card tc-student fx-fade-up" id="tc-student" hidden></div>
            </div>
          </div>
        </div>
        )}

        {/* ── Kế hoạch học ── */}
        {daMo.has('plan') && (
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
        )}

        {/* ── Courses ── */}
        {daMo.has('courses') && (
        <div className="page" id="page-courses">
          <div className="courses-header fx-fade-up">
            <div>
              <h2>📚 Khóa học</h2>
              <p className="courses-subtitle" id="courses-count-sub">Đang tải…</p>
            </div>
            <div className="courses-controls">
              <div className="filter-group" role="group" aria-label="Lọc theo trạng thái ghi danh">
                <button className="filter-btn active" onClick={(e) => W().setEnrollmentFilter(e.currentTarget, 'all')} role="radio" aria-checked="true">Tất cả</button>
                <button className="filter-btn" onClick={(e) => W().setEnrollmentFilter(e.currentTarget, 'enrolled')} role="radio" aria-checked="false">Đang học</button>
                <button className="filter-btn" onClick={(e) => W().setEnrollmentFilter(e.currentTarget, 'not-enrolled')} role="radio" aria-checked="false">Chưa mở</button>
              </div>
              <div className="sort-dropdown-wrap">
                <label htmlFor="course-sort-select" className="sort-label">Sắp xếp:</label>
                {/* Tên tiếng Việt, chứa nguyên nhãn nhìn thấy "Sắp xếp" (WCAG 2.5.3) —
                    bản cũ "Sort courses by" là tiếng Anh (22/09/2026, F4). */}
                <select id="course-sort-select" className="sort-select" onChange={(e) => W().setSortOrder(e.currentTarget.value)} aria-label="Sắp xếp khoá học">
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
                placeholder="Tìm khóa học, môn học, chủ đề..."
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
                    {/* Chip "Đề thi thử" gỡ 24/09/2026 — bỏ thi, pha A. */}
                  </div>
                </div>
                <ul id="csh-dynamic" style={{ display: 'none', listStyle: 'none', padding: 0, margin: '8px 0 0' }}></ul>
              </div>
            </div>

            {/* Bộ lọc theo hợp phần HSA (đã bỏ 'Cấp độ' + 'Ngôn ngữ' lập trình pe_test) */}
            <div className="course-filter-panel">
              <div className="filter-pill-row" id="section-filter-row">
                <span className="pill-label">Môn học</span>
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
        )}

        {/* ── Roadmap (partial roadmap.html) ── */}
        {daMo.has('roadmap') && <RoadmapSection />}

        {/* ── Skills ── */}
        {daMo.has('skills') && (
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
          {/* Ba hợp phần HSA. Component TỰ tải dữ liệu khi tab hiện ra
              (IntersectionObserver), nên không đụng vào LCP của trang này —
              màn chậm nhất của sản phẩm. Xem `BaHopPhan.tsx`. */}
          <BaHopPhan />
          <div className="sk-grid" id="sk-grid">
            <div style={{ color: '#9CA3AF', fontSize: 14, padding: 24 }}>Đang tải...</div>
          </div>
        </div>
        )}

        {/* ── Forum ── */}
        {daMo.has('forum') && (
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
              {/* Nhãn nối với ô chọn (22/09/2026, agent tiếp cận F4): bản cũ `<label>`
                  không `htmlFor`, ô không tên → axe `select-name` ở cả bốn lượt đo. */}
              <label htmlFor="forum-sort-select" className="sort-label">Sắp xếp:</label>
              <select id="forum-sort-select" className="sort-select" aria-label="Sắp xếp bài viết" onChange={(e) => W().forumSetSort(e.currentTarget.value)}>
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
        )}

        {/* ── Settings ── */}
        {daMo.has('settings') && (
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
                  {vai && <span className="profile-badge">{NHAN_VAI[vai] ?? vai}</span>}
                </div>
              </div>
              {/* `data-ho-so` là hợp đồng với `main.js::saveSettings` và
                  `loadUser`: cả hai đọc THEO NHÃN này chứ không gọi tên từng ô,
                  nên thêm một trường hồ sơ chỉ cần thêm một <input> ở đây.
                  Giá trị của nhãn phải khớp tên khoá `PUT /api/user` nhận. */}
              <div className="fields-grid">
                <div><label className="field-label" htmlFor="field-name">Họ và tên</label><input id="field-name" data-ho-so="name" className="field-input" placeholder="Nhập họ và tên" /></div>
                <div><label className="field-label" htmlFor="field-email">Email</label><input id="field-email" data-ho-so="email" className="field-input" placeholder="Nhập email" /></div>
                <div><label className="field-label" htmlFor="field-phone">Số điện thoại</label><input id="field-phone" data-ho-so="phone" className="field-input" placeholder="Nhập số điện thoại" /></div>
                <div><label className="field-label" htmlFor="field-birthday">Ngày sinh</label><input id="field-birthday" data-ho-so="birthday" className="field-input" placeholder="Chọn ngày sinh" /></div>
              </div>
            </div>

            {/* ── LIÊN HỆ PHỤ HUYNH ────────────────────────────────────────
                Trung tâm gửi báo cáo tiến độ tới email (kênh chính từ 07/09)
                hoặc Zalo của phụ huynh. Số ở mục trên là số của CHÍNH EM — với
                học sinh lớp 12 thì Zalo ở số ấy là của các em, nên gửi vào đó
                là "báo cáo cho phụ huynh" mà phụ huynh không bao giờ đọc.

                Ô email thêm 13/09/2026. Trước đó kênh gửi CHÍNH không có chỗ
                nào để nhập địa chỉ — đo production: 0 em có email phụ huynh.

                Để học viên tự điền chứ không bắt học vụ nhập hộ từng em: chính
                các em biết số của bố mẹ, và một ô phải chờ người khác điền hộ
                là một ô sẽ trống mãi. */}
            <div className="settings-section" id="lien-he-phu-huynh" data-chi-hoc-vien="">
              <div className="settings-section-title">
                <span className="title-icon-blue" data-icon="users" data-size="16"></span>
                <span>Liên hệ phụ huynh</span>
              </div>
              <p className="goal-hint">
                Trung tâm gửi báo cáo tiến độ học của bạn tới email hoặc số Zalo
                của phụ huynh. Bỏ trống thì không gửi cho ai cả — không có gì tự
                động xảy ra.
              </p>
              <div className="fields-grid">
                <div>
                  <label className="field-label" htmlFor="field-parent-name">Tên phụ huynh</label>
                  <input id="field-parent-name" data-ho-so="parent_name" className="field-input" placeholder="VD: Nguyễn Văn A" />
                </div>
                <div>
                  <label className="field-label" htmlFor="field-parent-phone">Số Zalo của phụ huynh</label>
                  <input id="field-parent-phone" data-ho-so="parent_phone" className="field-input" inputMode="tel" placeholder="VD: 0912345678" />
                </div>
                <div>
                  <label className="field-label" htmlFor="field-parent-email">Email của phụ huynh</label>
                  {/* `type="email"` cho bàn phím có sẵn @ trên điện thoại. KHÔNG
                      trông vào kiểm tra của trình duyệt: ô này không nằm trong
                      <form>, nên đúng/sai dạng là việc của `PUT /api/user`. */}
                  <input id="field-parent-email" data-ho-so="parent_email" className="field-input" type="email" autoComplete="off" placeholder="VD: me.an@gmail.com" />
                </div>
              </div>
              {/* §47: trung tâm đã nhập thì ô đã có thông tin thành chỉ-đọc,
                  kèm câu giải thích. Máy chủ vẫn là hàng rào thật. */}
              <KhoaLienHePhuHuynh />
            </div>

            {/* Mục tiêu HSA — trước đây chỉ đặt được MỘT LẦN lúc làm khảo sát,
                dù chúng nuôi thẻ đếm ngược ở Bảng điều khiển (audit 2026-08-15). */}
            <div className="settings-section" id="hsa-goals" data-chi-hoc-vien="">
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
                <span className="field-label" id="lbl-goal-sec3">Môn học thứ 3</span>
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
                </div><button id="toggle-email" className="toggle on" onClick={(e) => W().toggleSwitch(e.currentTarget)} aria-pressed="true" aria-label="Thông báo qua Email"><span className="toggle-knob"></span></button>
              </div>
              <div className="notif-row">
                <div>
                  <div className="notif-lbl">Thông báo đẩy</div>
                  <div className="notif-desc">Nhận thông báo trực tiếp trên trình duyệt</div>
                </div><button id="toggle-push" className="toggle" onClick={(e) => W().toggleSwitch(e.currentTarget)} aria-pressed="false" aria-label="Thông báo đẩy"><span className="toggle-knob"></span></button>
              </div>
              <div className="notif-row">
                <div>
                  <div className="notif-lbl">Nhắc nhở học tập</div>
                  <div className="notif-desc">Nhắc nhở lịch học hàng ngày</div>
                </div><button id="toggle-remind" className="toggle on" onClick={(e) => W().toggleSwitch(e.currentTarget)} aria-pressed="true" aria-label="Nhắc nhở học tập"><span className="toggle-knob"></span></button>
              </div>
              <div className="notif-row">
                <div>
                  <div className="notif-lbl">Cập nhật nội dung</div>
                  <div className="notif-desc">Thông báo khi có bài học mới</div>
                </div><button id="toggle-content" className="toggle" onClick={(e) => W().toggleSwitch(e.currentTarget)} aria-pressed="false" aria-label="Cập nhật nội dung"><span className="toggle-knob"></span></button>
              </div>
            </div>

            <div className="sec-lang-grid">
              <div className="sec-lang-card">
                <div className="sec-lang-title"><span className="title-icon-blue" data-icon="shield" data-size="16"></span><span>Bảo mật</span></div>
                <button className="change-pw-btn" onClick={() => W().openChangePasswordModal()}>Đổi mật khẩu</button>
              </div>
              <div className="sec-lang-card">
                <div className="sec-lang-title"><span className="title-icon-red" data-icon="globe" data-size="16"></span><span>Ngôn ngữ</span></div>
                <select className="lang-select" aria-label="Ngôn ngữ hiển thị">
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
        )}

        {/* ══════════ TRANG CỦA TÔI ══════════ */}
        {daMo.has('profile') && (
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
        )}
      </main>

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
