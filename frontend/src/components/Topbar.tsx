'use client';

// Port block nav của base.html (topbar + search + bell + user-chip) — markup 1:1.
// Mọi handler gọi hàm global của main.js (giữ nguyên logic legacy).
/* eslint-disable @typescript-eslint/no-explicit-any */
const W = () => window as any;

export default function Topbar() {
  return (
    <>
      <span id="sidebar-name" style={{ display: 'none' }}>—</span>
      <span id="sidebar-role" style={{ display: 'none' }}>Học viên</span>

      <div className="topbar">
        <div className="topbar-left">
          <div
            className="brand brand-always"
            onClick={() => {
              W().navigate('dashboard');
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
            style={{ cursor: 'pointer' }}
            title="Về trang chủ"
          >
            <span className="brand-title brand-full"><span className="brand-c1">ProgrammingEdu</span> <span className="brand-x">×</span> <span className="brand-c2">TopHSA</span></span>
            <span className="brand-title brand-short">PE×T</span>
          </div>
        </div>

        <nav className="topbar-nav" role="navigation" aria-label="Main navigation" id="topbar-nav">
          <button className="nav-btn active" data-page="dashboard" onClick={() => W().navigate('dashboard')} aria-label="Dashboard">
            <span className="nav-icon" data-icon="home" data-size="17"></span><span>Dashboard</span>
          </button>
          <button className="nav-btn" data-page="courses" onClick={() => W().navigate('courses')} aria-label="Khóa học">
            <span className="nav-icon" data-icon="library" data-size="17"></span><span>Khóa học</span>
          </button>
          {/* Kế hoạch học có lịch — vế System-Guided. Khác "Lộ trình" (danh mục
              tĩnh 26 lộ trình từ bản cũ): đây là lịch của riêng học viên, sinh
              từ ngày thi + sức học + chủ đề đang yếu. */}
          <button className="nav-btn" data-page="plan" onClick={() => W().navigate('plan')} aria-label="Kế hoạch">
            <span className="nav-icon" data-icon="calendar" data-size="17"></span><span>Kế hoạch</span>
          </button>
          <button className="nav-btn" data-page="roadmap" onClick={() => W().navigate('roadmap')} aria-label="Lộ trình">
            <span className="nav-icon" data-icon="map" data-size="17"></span><span>Lộ trình</span>
          </button>
          <button className="nav-btn" data-page="forum" onClick={() => W().navigate('forum')} aria-label="Diễn đàn">
            <span className="nav-icon" data-icon="chat" data-size="17"></span><span>Diễn đàn</span>
          </button>
          <button className="nav-btn" onClick={() => { window.location.href = '/mock'; }} aria-label="Thi thử">
            <span className="nav-icon" data-icon="target" data-size="17"></span><span>Thi thử</span>
          </button>

          {/* Bài tập giảng viên giao (ERP §5, 31/08/2026). Cùng kiểu điều hướng
              với "Thi thử": rời khỏi trang legacy sang một tuyến Next thật, vì
              màn hình này dựng bằng bộ component mới chứ không phải main.js.
              KHÔNG ẩn theo vai trò — giảng viên cũng có thể đang học một khoá,
              và trang tự trả về danh sách rỗng nếu không có bài nào. */}
          <button className="nav-btn" onClick={() => { window.location.href = '/bai-tap'; }} aria-label="Bài tập">
            <span className="nav-icon" data-icon="pencil" data-size="17"></span><span>Bài tập</span>
          </button>

          {/* Khu giảng dạy — chỉ hiện với vai trò Giảng viên hoặc admin.
              dashboard.js bật/tắt theo window.__currentUser.role. */}
          <button className="nav-btn" id="nav-teach" data-page="teach" style={{ display: 'none' }} onClick={() => W().navigate('teach')} aria-label="Giảng dạy">
            <span className="nav-icon" data-icon="users" data-size="17"></span><span>Giảng dạy</span>
          </button>

          <button className="nav-btn" id="nav-admin" style={{ display: 'none' }} onClick={() => { window.location.href = '/admin'; }} aria-label="Quản trị">
            <span className="nav-icon" data-icon="wrench" data-size="17"></span><span>Quản trị</span>
          </button>
          <span className="nav-underline" id="nav-underline"></span>
        </nav>

        <div className="topbar-right">
          <div className="search-wrap" id="search-wrap">
            <span className="search-icon"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg></span>
            <input
              type="text"
              id="search-input"
              placeholder="Tìm kiếm..."
              onInput={() => { W().filterCourses(); W().showSearchSuggestions(); }}
              onFocus={() => W().showSearchSuggestions()}
              onClick={() => W().showSearchSuggestions()}
              onBlur={() => W().closeSearchSuggestions()}
              autoComplete="off"
            />
            <div className="search-suggestions hidden" id="search-suggestions">
              <div className="suggestions-header">Gợi ý tìm kiếm</div>
              <div className="suggestions-row" id="suggestions-row"></div>
              <div className="suggestions-header">Cấp độ học</div>
              <div className="suggestion-levels" id="suggestion-levels"></div>
            </div>
          </div>
          <button className="theme-toggle-btn" id="theme-toggle" onClick={() => W().toggleTheme()} title="Đổi giao diện" aria-label="Đổi giao diện">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" /></svg>
          </button>
          <div className="bell-wrap" id="bell-wrap">
            <button className="bell-btn" id="bell-btn" onClick={() => W().toggleBellPanel()} aria-haspopup="true" aria-expanded="false" aria-label="Thông báo">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" /></svg>
              <span className="bell-dot" id="bell-dot"></span>
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
            {/* <button>, KHÔNG phải <div>. Đo 31/08/2026: bấm Tab 80 lần từ đầu
                trang không lần nào dừng ở đây — một <div> không nằm trong thứ tự
                tiêu điểm — mà menu thì `visibility: hidden` khi đóng nên ba nút
                bên trong cũng không tới được. Nghĩa là người dùng bàn phím KHÔNG
                CÓ CÁCH NÀO đăng xuất, trên mọi trang của sản phẩm.
                Đổi thẻ là đủ: <button> tự có tiêu điểm, tự nhận Enter và Space,
                và `aria-haspopup`/`aria-expanded` ở đây mới đúng nghĩa. `.user-chip`
                đã tự đặt nền, viền, bo góc và con trỏ nên hình dạng không đổi;
                `type="button"` để nó không vô tình gửi form nào bọc ngoài. */}
            <button type="button" className="user-chip" id="user-chip-btn" onClick={() => W().toggleUserMenu()} aria-haspopup="true" aria-expanded="false">
              <span className="chip-avatar" id="chip-avatar">?</span>
              <span className="chip-name" id="chip-name">—</span>
              <span className="dropdown-icon" id="chip-arrow"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6" /></svg></span>
            </button>
            <div className="user-dropdown" id="user-dropdown" role="menu">
              <div className="user-dropdown-header">
                <span className="chip-avatar udh-avatar" id="udh-avatar">?</span>
                <div>
                  <div className="udh-name" id="udh-name">—</div>
                  <div className="udh-role">Học viên</div>
                </div>
              </div>
              <div className="user-dropdown-divider"></div>
              <button className="user-dropdown-item" onClick={() => { W().navigate('profile'); W().closeUserMenu(); }} role="menuitem">
                <span className="udi-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg></span> Trang của tôi
              </button>
              <button className="user-dropdown-item" onClick={() => { W().navigate('settings'); W().closeUserMenu(); }} role="menuitem">
                <span className="udi-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg></span> Cài đặt
              </button>
              <div className="user-dropdown-divider"></div>
              <button className="user-dropdown-item danger" onClick={() => { window.location.href = '/auth/logout'; }} role="menuitem">
                <span className="udi-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="m16 17 5-5-5-5" /><path d="M21 12H9" /></svg></span> Đăng xuất
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
