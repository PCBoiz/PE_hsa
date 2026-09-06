'use client';

import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';

import { doiChuDe, useDangToi } from '@/lib/chuDe';
import { goiLegacy } from '@/lib/goiLegacy';

import { BieuTuong } from './bieuTuong';
import { MUC_NAV, NHOM_NAV } from './navMuc';

/* ══════════════════════════════════════════════════════════════════════════
 * KHUNG CHUNG — một thanh trên cho MỌI màn.
 *
 * ── CÁI NÓ THAY THẾ (06/09/2026) ──────────────────────────────────────────
 *
 * Trước đó có BA bản dựng, chỉ dùng chung mỗi danh sách mục (`navMuc.ts`):
 *
 *   Topbar.tsx           .topbar    · biểu tượng SVG (nhờ icons.js điền)
 *   courses/[courseId]   .topbar    · biểu tượng EMOJI 🔍🌙🔔▾
 *   MockExam.tsx         .mk-topbar · chữ trần, KHÔNG chip người dùng
 *
 * Hệ quả không phải chuyện thẩm mỹ: vào màn Thi thử là học viên **mất đường
 * Đăng xuất và nút đổi sáng/tối** (grep `user-chip|logout` trong MockExam.tsx
 * ra 0). Và biểu tượng ở hai màn kia không thể giống nhau, vì `icons.js` chỉ
 * quét `[data-icon]` một lần lúc `DOMContentLoaded` — React dựng sau mốc đó.
 * Nay biểu tượng vẽ thẳng trong React (`bieuTuong.tsx`, sinh từ `icons.js` và
 * khoá bằng `e2e/unit/bieu-tuong-khop.test.mjs`).
 *
 * ── HAI TRỤC, KHÔNG PHẢI MỘT ──────────────────────────────────────────────
 *
 * Dễ nhầm là chỉ có "trang cũ / trang mới". Thật ra có hai câu hỏi độc lập:
 *
 *   `spa`        Trang này có `main.js` không? Có thì điều hướng bằng
 *                `navigate()` (đổi khung trong cùng một trang); không thì
 *                `location.href`.
 *   `dieuKhien`  Trang này có bộ xử lý menu/chuông của JS cũ không?
 *
 * Chúng KHÁC nhau: `courses/[courseId]` không nạp main.js (`spa: false`) nhưng
 * `course_detail.js` CÓ định nghĩa `toggleUserMenu`/`toggleBellPanel`
 * (`dieuKhien: 'legacy'`). Gộp hai trục làm một là hoặc dựng lại menu bằng
 * React đè lên bản đang chạy, hoặc để /mock có một cái nút không ai nghe.
 *
 * `dashboard.js` sở hữu TRỌN menu người dùng — mở, đóng, bấm-ra-ngoài, phím
 * Escape. Ở đó tuyệt đối không dựng lại bằng React; chỉ dựng ở nơi nó vắng.
 * ══════════════════════════════════════════════════════════════════════════ */

type CheDo = 'day-du' | 'lam-bai';

export type AppShellProps = {
  /** Mục đang mở: `data-page` ('dashboard') hoặc đường dẫn ('/mock'). */
  trang?: string;
  /** Trang có `main.js` → dùng `navigate()` thay cho `location.href`. */
  spa?: boolean;
  /** Ai điều khiển menu/chuông: JS cũ, hay chính component này. */
  dieuKhien?: 'legacy' | 'react';
  /** Tên hiển thị, nếu trang tự biết. Bỏ trống thì để JS cũ điền vào #chip-name. */
  ten?: string;
  /** Vai hiển thị trong menu. */
  vai?: string;
  cheDo?: CheDo;
  /** Nhãn ngắn ở chế độ làm bài, ví dụ "Đang làm bài". */
  nhan?: string;
  /** Nội dung bên phải ở chế độ làm bài: đồng hồ, nút nộp. */
  phai?: ReactNode;
};

/** Chữ cái đầu cho ảnh đại diện chữ. */
const chuDau = (s?: string) => (s?.trim()?.[0] ?? '?').toUpperCase();

export default function AppShell({
  trang,
  spa = false,
  dieuKhien = 'legacy',
  ten,
  vai = 'Học viên',
  cheDo = 'day-du',
  nhan = 'Đang làm bài',
  phai,
}: AppShellProps) {
  const toi = useDangToi();
  const [moMenu, setMoMenu] = useState(false);
  const oMenu = useRef<HTMLDivElement>(null);
  /* Nhóm nào đang mở trên thanh (`null` = không nhóm nào).
     KHÁC menu người dùng ở chỗ: nhóm là UI của CHÍNH component này, không có
     bản legacy nào tranh — nên nó tự giữ trạng thái ở mọi chế độ. */
  const [moNhom, setMoNhom] = useState<string | null>(null);
  const oNav = useRef<HTMLElement>(null);

  /* Bấm ra ngoài và phím Escape — CHỈ ở chế độ React. Trên trang legacy,
     `dashboard.js` đã gắn đúng hai hành vi này lên `document`; gắn thêm một bộ
     nữa là hai bộ cùng đóng một menu, và cú bấm đầu tiên sẽ nhấp nháy. */
  useEffect(() => {
    if (dieuKhien !== 'react' || !moMenu) return;
    const ngoai = (e: MouseEvent) => {
      if (oMenu.current && !oMenu.current.contains(e.target as Node)) setMoMenu(false);
    };
    const esc = (e: KeyboardEvent) => { if (e.key === 'Escape') setMoMenu(false); };
    document.addEventListener('click', ngoai);
    document.addEventListener('keydown', esc);
    return () => {
      document.removeEventListener('click', ngoai);
      document.removeEventListener('keydown', esc);
    };
  }, [dieuKhien, moMenu]);

  /* Bấm ra ngoài và Escape thì đóng nhóm. Áp dụng cho MỌI chế độ: đây là menu
     do component này dựng, không phải của `dashboard.js`, nên không có ai khác
     đóng hộ. Một menu chỉ đóng được bằng cách bấm đúng vào nút vừa mở nó là
     một cái bẫy — người ta bấm ra chỗ khác và nó vẫn treo đó. */
  useEffect(() => {
    if (!moNhom) return;
    const ngoai = (e: MouseEvent) => {
      if (oNav.current && !oNav.current.contains(e.target as Node)) setMoNhom(null);
    };
    const esc = (e: KeyboardEvent) => { if (e.key === 'Escape') setMoNhom(null); };
    document.addEventListener('click', ngoai);
    document.addEventListener('keydown', esc);
    return () => {
      document.removeEventListener('click', ngoai);
      document.removeEventListener('keydown', esc);
    };
  }, [moNhom]);

  const doiTheme = useCallback(() => {
    // Trang legacy: gọi hàm của main.js để nó cũng cập nhật những gì nó giữ.
    // Trang React: bản dùng chung ở `lib/chuDe` — cùng một phép logic.
    if (dieuKhien === 'legacy') goiLegacy('toggleTheme');
    else doiChuDe();
  }, [dieuKhien]);

  const bamMenu = useCallback(() => {
    if (dieuKhien === 'legacy') goiLegacy('toggleUserMenu');
    else setMoMenu((v) => !v);
  }, [dieuKhien]);

  /** Đi tới một mục điều hướng. */
  const di = useCallback((muc: (typeof MUC_NAV)[number]) => {
    if (spa && muc.trang) goiLegacy('navigate', muc.trang);
    else window.location.href = muc.url;
  }, [spa]);

  /* Ô tìm kiếm ở trang KHÔNG có main.js: Enter thì sang dashboard kèm `?q=`. */
  const timNgoaiSpa = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    const v = e.currentTarget.value.trim();
    if (e.key === 'Enter' && v) window.location.href = '/dashboard?q=' + encodeURIComponent(v);
  }, []);

  /* ĐẦU BÊN KIA của `?q=`. Trước 06/09/2026 màn chi tiết khoá học đã gửi tham
     số này rồi, nhưng grep toàn bộ FE cho `get('q')` ra **0 kết quả**: không
     một dòng nào đọc nó. Người học gõ "Định lượng", bấm Enter, sang một
     dashboard trống trơn — chữ mình vừa gõ biến mất. Nay khung điều hướng dùng
     chung nên ô ấy có mặt ở mọi màn; một ô nhập nuốt chữ rồi vứt đi thì càng
     nhân ra nhiều chỗ.
     Đặt ở ĐÂY chứ không ở `main.js`: `chot-ham-tang-cu.test.mjs` chốt số dòng
     logic của tầng JS cũ, và nó bắt đúng — luật mới thì viết ở `src/`. Chỗ này
     còn hợp lý hơn về mặt gắn kết: cùng một component vừa GỬI `?q=` vừa NHẬN.
     `goiLegacy` lo phần `main.js` có thể chưa nạp xong. */
  useEffect(() => {
    if (!spa) return;
    const q = new URLSearchParams(window.location.search).get('q');
    if (!q) return;
    const o = document.getElementById('search-input') as HTMLInputElement | null;
    if (!o) return;
    o.value = q;
    // `filterCourses` đọc thẳng `#search-input`, rồi tự chuyển sang trang Khoá
    // học và lọc — nên chỉ cần đặt giá trị trước khi gọi.
    goiLegacy('filterCourses');
  }, [spa]);

  const thuongHieu = (
    <div
      className="brand brand-always"
      onClick={() => {
        if (cheDo === 'lam-bai') return;   // đang thi thì không rời trang
        if (spa) { goiLegacy('navigate', 'dashboard'); window.scrollTo({ top: 0, behavior: 'smooth' }); }
        else window.location.href = '/dashboard';
      }}
      style={{ cursor: cheDo === 'lam-bai' ? 'default' : 'pointer' }}
      title={cheDo === 'lam-bai' ? 'Đang làm bài' : 'Về trang chủ'}
    >
      <span className="brand-title brand-full">
        <span className="brand-c1">ProgrammingEdu</span>{' '}
        <span className="brand-x">×</span>{' '}
        <span className="brand-c2">TopHSA</span>
      </span>
      <span className="brand-title brand-short">PE×T</span>
    </div>
  );

  /* ── CHẾ ĐỘ LÀM BÀI ────────────────────────────────────────────────────
     Tước xuống còn tên sản phẩm, một nhãn, và phần bên phải của trang (đồng hồ
     + nộp bài). Đây là CHỦ Ý: một cú bấm nhầm vào điều hướng giữa lúc thi là
     mất bài đang làm. Màn chọn đề và màn kết quả vẫn dùng thanh đầy đủ. */
  if (cheDo === 'lam-bai') {
    return (
      <div className="topbar shell-lam-bai">
        <div className="topbar-left">{thuongHieu}</div>
        <span className="shell-lam-bai-nhan">{nhan}</span>
        <div className="shell-lam-bai-phai">{phai}</div>
      </div>
    );
  }

  const dangMo = (m: (typeof MUC_NAV)[number]) =>
    (m.trang != null && m.trang === trang) || m.url === trang;

  /* Một mục điều hướng — dùng CHUNG cho mục ở cấp một và mục nằm trong nhóm.
     Phải là cùng một hàm dựng: hai bản chép tay của cùng một nút là đúng thứ
     phiên làm việc này đi dọn (ba thanh điều hướng, ba bản `.nav-btn`). */
  const nutMuc = (m: (typeof MUC_NAV)[number]) => (
    <button
      key={m.nhan}
      type="button"
      className={'nav-btn' + (dangMo(m) ? ' active' : '')}
      /* `data-page` là hợp đồng với `main.js::navigate()`: nó tìm
         `.nav-btn[data-page='…']` để tô mục đang mở và kéo gạch chân. ĐÂY là
         lý do bốn mục trong nhóm vẫn là NÚT THẬT nằm trong DOM chứ không phải
         một danh sách dựng lại — gỡ chúng ra là main.js không còn gì để tô. */
      {...(m.trang ? { 'data-page': m.trang } : {})}
      {...(dangMo(m) ? { 'aria-current': 'page' as const } : {})}
      /* `aria-label` và `title` BẮT BUỘC: dưới 96rem `shell.css` đặt
         `display: none` cho nhãn chữ, mà phần tử `display:none` thì trình đọc
         màn hình cũng bỏ qua — nút sẽ KHÔNG CÒN TÊN nào. `title` lo cho người
         dùng chuột: rê lên một biểu tượng lạ thì hiện chữ. */
      aria-label={m.nhan}
      title={m.nhan}
      onClick={() => { setMoNhom(null); di(m); }}
    >
      <span className="nav-icon"><BieuTuong ten={m.icon} co={17} /></span>
      <span>{m.nhan}</span>
    </button>
  );

  /* Dựng danh sách hiển thị: mục có `nhom` được thu vào panel của nhóm, và
     nhóm xuất hiện ĐÚNG chỗ mục đầu tiên của nó — thứ tự trong `navMuc.ts`
     vẫn là thứ tự người dùng thấy. */
  const daVe = new Set<string>();
  const dayNav = MUC_NAV.flatMap((m) => {
    if (!m.nhom) return [nutMuc(m)];
    if (daVe.has(m.nhom)) return [];
    daVe.add(m.nhom);
    const khoa = m.nhom;
    const nhomTin = NHOM_NAV[khoa];
    const con = MUC_NAV.filter((x) => x.nhom === khoa);
    const dangXem = con.some(dangMo);
    return [(
      <div className={'nav-nhom' + (moNhom === khoa ? ' mo' : '')} key={'nhom-' + khoa}>
        <button
          type="button"
          className={'nav-btn nav-nhom-nut' + (dangXem ? ' active' : '')}
          aria-haspopup="true"
          aria-expanded={moNhom === khoa}
          aria-label={nhomTin.nhan}
          title={nhomTin.nhan}
          onClick={() => setMoNhom((v) => (v === khoa ? null : khoa))}
        >
          <span className="nav-icon"><BieuTuong ten={nhomTin.icon} co={17} /></span>
          <span>{nhomTin.nhan}</span>
          <span className="nav-nhom-mui"><BieuTuong ten="chevron-down" co={11} /></span>
        </button>
        <div className="nav-nhom-panel" role="menu" aria-label={nhomTin.nhan}>
          {con.map(nutMuc)}
        </div>
      </div>
    )];
  });

  return (
    <div className="topbar">
      <div className="topbar-left">{thuongHieu}</div>

      <nav className="topbar-nav" role="navigation" aria-label="Điều hướng chính" id="topbar-nav" ref={oNav}>
        {dayNav}

        {/* Ba mục dưới do `dashboard.js` bật/tắt theo VAI qua `id` — nên chúng
            không nằm trong `navMuc.ts`, và chỉ có nghĩa ở trang có main.js.
            Trang khác dựng chúng ra là dựng ba nút ẩn vĩnh viễn.

            `aria-label`/`title` cũng BẮT BUỘC ở đây, y như tám mục trên. Tôi đã
            quên đúng ba nút này khi viết lại component, và `khung-chung.spec.ts`
            bắt được ngay ở lượt chạy đầu ("Expected: 0, Received: 3") — vì với
            tài khoản quản trị thì `dashboard.js` mở chúng ra, và dưới 96rem
            nhãn chữ bị `display:none`, tức ba nút thành KHÔNG CÓ TÊN. */}
        {spa && (
          <>
            <button type="button" className="nav-btn" id="nav-teach" data-page="teach"
              aria-label="Giảng dạy" title="Giảng dạy"
              style={{ display: 'none' }} onClick={() => goiLegacy('navigate', 'teach')}>
              <span className="nav-icon"><BieuTuong ten="users" co={17} /></span><span>Giảng dạy</span>
            </button>
            <button type="button" className="nav-btn" id="nav-vanhanh" style={{ display: 'none' }}
              aria-label="Vận hành" title="Vận hành"
              onClick={() => { window.location.href = '/quan-tri/tong-quan'; }}>
              <span className="nav-icon"><BieuTuong ten="shield" co={17} /></span><span>Vận hành</span>
            </button>
            <button type="button" className="nav-btn" id="nav-admin" style={{ display: 'none' }}
              aria-label="Quản trị" title="Quản trị"
              onClick={() => { window.location.href = '/admin'; }}>
              <span className="nav-icon"><BieuTuong ten="wrench" co={17} /></span><span>Quản trị</span>
            </button>
          </>
        )}
        {/* `main.js::_updateNavUnderline` đo vị trí `.nav-btn.active` rồi đặt
            `left`/`width` cho phần tử này. Không có main.js thì nó nằm im ở
            width 0 — vô hại, và mục đang mở vẫn nhận ra được nhờ viên thuốc màu. */}
        <span className="nav-underline" id="nav-underline"></span>
      </nav>

      <div className="topbar-right">
        <div className="search-wrap" id="search-wrap">
          <span className="search-icon"><BieuTuong ten="search" co={14} /></span>
          <input
            type="search"
            id="search-input"
            placeholder="Tìm kiếm..."
            aria-label="Tìm kiếm khoá học"
            autoComplete="off"
            {...(spa
              ? {
                /* GỌI QUA `goiLegacy`, không `window.X()` thẳng: React gắn
                   handler ngay, `main.js` thì nạp sau — chạm vào ô trong khoảng
                   giữa sẽ ném `filterCourses is not a function`. */
                onInput: () => { goiLegacy('filterCourses'); goiLegacy('showSearchSuggestions'); },
                onFocus: () => goiLegacy('showSearchSuggestions'),
                onClick: () => goiLegacy('showSearchSuggestions'),
                onBlur: () => goiLegacy('closeSearchSuggestions'),
              }
              : { onKeyDown: timNgoaiSpa })}
          />
          {/* Bảng gợi ý do `renderSearchSuggestions` của main.js đổ dữ liệu
              vào. Trang không có main.js thì không dựng — một bảng rỗng bật ra
              khi bấm vào ô là tệ hơn không có bảng nào. */}
          {spa && (
            <div className="search-suggestions hidden" id="search-suggestions">
              <div className="suggestions-header">Gợi ý tìm kiếm</div>
              <div className="suggestions-row" id="suggestions-row"></div>
              <div className="suggestions-header">Cấp độ học</div>
              <div className="suggestion-levels" id="suggestion-levels"></div>
            </div>
          )}
        </div>

        <span className="shell-chia" aria-hidden="true" />

        <button
          type="button"
          className="theme-toggle-btn"
          id="theme-toggle"
          onClick={doiTheme}
          title={toi ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối'}
          aria-label={toi ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối'}
          aria-pressed={toi}
        >
          {/* CẢ HAI biểu tượng luôn có mặt; `shell.css` chọn hiện cái nào theo
              `body.dark`. Không dựng theo state React: script chống nháy màu ở
              layout đặt `body.dark` TRƯỚC khi React chạy, nên nếu để React
              quyết thì lượt vẽ đầu ở máy chủ luôn là "sáng" và nút nháy một cái
              khi hydrate. Để CSS quyết thì không có khoảnh khắc nào sai. */}
          <span className="shell-ic-troi"><BieuTuong ten="sun" co={16} /></span>
          <span className="shell-ic-trang"><BieuTuong ten="moon" co={16} /></span>
        </button>

        {/* Chuông chỉ có nghĩa ở nơi JS cũ cung cấp dữ liệu và bộ xử lý. Ở
            /mock thì không có — dựng ra là một cái nút bấm không ai nghe, và
            một nút chết còn tệ hơn một nút vắng mặt. */}
        {dieuKhien === 'legacy' && (
          <div className="bell-wrap" id="bell-wrap">
            <button type="button" className="bell-btn" id="bell-btn"
              onClick={() => goiLegacy('toggleBellPanel')}
              aria-haspopup="true" aria-expanded="false" aria-label="Thông báo">
              <BieuTuong ten="bell" co={16} />
              <span className="bell-dot" id="bell-dot"></span>
            </button>
            <div className="bell-panel" id="bell-panel" role="dialog" aria-label="Thông báo">
              <div className="bell-panel-header">
                <span className="bell-panel-title">Thông báo</span>
                <button type="button" className="bell-mark-all"
                  onClick={() => goiLegacy('markAllBellRead')}>Đánh dấu đã đọc</button>
              </div>
              <div className="bell-panel-body" id="bell-panel-body"></div>
            </div>
          </div>
        )}

        <div className="user-chip-wrap" id="user-chip-wrap" ref={oMenu}>
          {/* <button>, KHÔNG phải <div>. Đo 31/08/2026: bấm Tab 80 lần từ đầu
              trang không lần nào dừng ở đây — <div> không nằm trong thứ tự tiêu
              điểm — mà menu thì `visibility: hidden` khi đóng nên ba mục bên
              trong cũng không tới được. Nghĩa là người dùng bàn phím KHÔNG CÓ
              CÁCH NÀO đăng xuất, trên mọi trang của sản phẩm. */}
          <button
            type="button"
            className={'user-chip' + (dieuKhien === 'react' && moMenu ? ' open' : '')}
            id="user-chip-btn"
            onClick={bamMenu}
            aria-haspopup="true"
            aria-expanded={dieuKhien === 'react' ? moMenu : false}
          >
            <span className="chip-avatar" id="chip-avatar">{chuDau(ten)}</span>
            <span className="chip-name" id="chip-name">{ten ?? '—'}</span>
            <span className="dropdown-icon" id="chip-arrow"><BieuTuong ten="chevron-down" co={12} /></span>
          </button>

          <div
            className={'user-dropdown' + (dieuKhien === 'react' && moMenu ? ' open' : '')}
            id="user-dropdown"
            role="menu"
          >
            <div className="user-dropdown-header">
              <span className="chip-avatar udh-avatar" id="udh-avatar">{chuDau(ten)}</span>
              <div>
                <div className="udh-name" id="udh-name">{ten ?? '—'}</div>
                <div className="udh-role">{vai}</div>
              </div>
            </div>
            <div className="user-dropdown-divider"></div>
            <button type="button" className="user-dropdown-item" role="menuitem"
              onClick={() => {
                if (spa) { goiLegacy('navigate', 'profile'); goiLegacy('closeUserMenu'); }
                else window.location.href = '/dashboard#profile';
              }}>
              <span className="udi-icon"><BieuTuong ten="user" co={14} /></span> Trang của tôi
            </button>
            <button type="button" className="user-dropdown-item" role="menuitem"
              onClick={() => {
                if (spa) { goiLegacy('navigate', 'settings'); goiLegacy('closeUserMenu'); }
                else window.location.href = '/dashboard#settings';
              }}>
              <span className="udi-icon"><BieuTuong ten="settings" co={14} /></span> Cài đặt
            </button>
            <div className="user-dropdown-divider"></div>
            <button type="button" className="user-dropdown-item danger" role="menuitem"
              onClick={() => { window.location.href = '/auth/logout'; }}>
              <span className="udi-icon"><BieuTuong ten="log-out" co={14} /></span> Đăng xuất
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
