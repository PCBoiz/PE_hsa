/**
 * DANH SÁCH MỤC ĐIỀU HƯỚNG — nguồn sự thật duy nhất.
 *
 * Vì sao tệp này tồn tại. Thanh điều hướng có HAI bản dựng: `Topbar.tsx` (trang
 * legacy, dùng `icons.js` + `navigate()` của main.js) và bản riêng trong
 * `courses/[courseId]/page.tsx` (dùng emoji + `location.href`, vì trang đó
 * không nạp main.js). Hai bản sao của một danh sách là hai bản sẽ trôi khỏi
 * nhau — và đã trôi, theo CẢ HAI chiều:
 *
 *   · bản sao thiếu "Kế hoạch", "Thi thử", "Bài tập" (vá 31/08/2026);
 *   · bản CHÍNH thiếu **"Kỹ năng"** — mà `page-skills` là một trang đầy đủ,
 *     có tìm kiếm và dữ liệu thật (đo 01/09/2026: 20 kỹ năng, 1 đạt, 1 cần ôn,
 *     18 chưa bắt đầu). Nghĩa là suốt thời gian đó, cách duy nhất vào được
 *     trang ấy là đi vòng qua màn chi tiết khoá học, hoặc tự gõ `#skills`.
 *
 * Gộp hẳn hai bản dựng thì phải kéo main.js + dashboard.js vào màn chi tiết
 * khoá — màn học viên mở hằng ngày — nên chưa làm. Nhưng phần SINH RA sự trôi
 * là danh sách, không phải cách dựng; tách riêng nó thì thêm một mục là sửa
 * đúng một chỗ.
 */

export type MucNav = {
  /** `data-page` cho `navigate()` của main.js. `null` = tuyến Next riêng. */
  trang: string | null;
  nhan: string;
  /** Tên biểu tượng cho `icons.js` (bản Topbar). */
  icon: string;
  /** Bản dự phòng cho trang KHÔNG nạp `icons.js` (màn chi tiết khoá). */
  emoji: string;
  /** Đường đi khi không có `navigate()` — luôn phải dùng được một mình. */
  url: string;
  /**
   * Chỉ sáng khi đường dẫn BẰNG ĐÚNG `url`, không sáng cho trang con.
   * "Việc hôm nay" (`/giang-day`) là tiền tố của mọi trang lớp; trang con
   * không có tab riêng (`/giang-day/ket-qua-thi/7586`) mà để nó sáng thì thanh
   * nói người dùng đang ở Việc hôm nay trong khi họ đang nhập điểm thi (rà
   * 20/09/2026). Không mục nào sáng còn hơn sáng nhầm.
   */
  chinhXac?: boolean;
  /** Câu giải thích, chỉ để đọc mã. */
  ghi_chu?: string;
  /**
   * Mục này nằm TRONG nhóm nào trên thanh (bỏ trống = đứng ở cấp một).
   *
   * Vì sao có nhóm (06/09/2026, anh Sơn chốt). Thanh từng có TÁM mục cấp một,
   * mà năm trong số đó chỉ là `#hash` của cùng một trang dashboard — tức thanh
   * đang trình bày các PHẦN của một màn như thể chúng là những nơi khác nhau.
   * Đo được hệ quả: tám mục có nhãn cần 818px, không vừa laptop 1440, nên nhãn
   * chữ phải biến mất và người mới nhìn vào tám biểu tượng trần.
   */
  nhom?: string;
  /**
   * Việc của RIÊNG học viên — nhân sự không thấy mục này (20/09/2026, xem
   * `lib/nhomVai.ts`). Chỉ là giấu: trang đích vẫn tự lo quyền của nó.
   */
  chiHocVien?: boolean;
};

/** Các nhóm trên thanh. `icon` dùng chung bộ với `MUC_NAV`. */
export const NHOM_NAV: Record<string, { nhan: string; icon: string }> = {
  hoc: { nhan: 'Học', icon: 'library' },
};

export const MUC_NAV: MucNav[] = [
  // "Trang của tôi" chứ không "Dashboard" (21/09/2026): đó là tên trang tự gọi
  // mình ở tiêu đề h1, và là chữ tiếng Anh DUY NHẤT còn lại trên thanh.
  { trang: 'dashboard', nhan: 'Trang của tôi', icon: 'home', emoji: '🏠', url: '/dashboard' },
  { trang: 'courses', nhan: 'Khóa học', icon: 'library', emoji: '📖', url: '/dashboard#courses', nhom: 'hoc' },
  {
    trang: 'plan', nhan: 'Kế hoạch', icon: 'calendar', emoji: '🗓️', url: '/dashboard#plan', chiHocVien: true,
    ghi_chu: 'Vế System-Guided. Khác "Lộ trình" (danh mục tĩnh 26 lộ trình của '
      + 'bản cũ): đây là lịch của riêng học viên, sinh từ ngày thi + sức học + '
      + 'chủ đề đang yếu.',
    nhom: 'hoc',
  },
  { trang: 'roadmap', nhan: 'Lộ trình', icon: 'map', emoji: '🗺️', url: '/dashboard#roadmap', nhom: 'hoc', chiHocVien: true },
  {
    trang: 'skills', nhan: 'Kỹ năng', icon: 'medal', emoji: '🏅', url: '/dashboard#skills', chiHocVien: true,
    ghi_chu: 'Mục BỊ MẤT khỏi thanh chính cho tới 01/09/2026 — xem đầu tệp.',
    nhom: 'hoc',
  },
  { trang: 'forum', nhan: 'Diễn đàn', icon: 'chat', emoji: '💬', url: '/dashboard#forum' },
  {
    trang: null, nhan: 'Thi thử', icon: 'target', emoji: '🎯', url: '/mock', chiHocVien: true,
    ghi_chu: 'Tuyến Next thật, không phải trang trong SPA legacy.',
  },
  {
    trang: null, nhan: 'Bài tập', icon: 'pencil', emoji: '✏️', url: '/bai-tap', chiHocVien: true,
    ghi_chu: 'Bài giảng viên giao (ERP §5), phía NGƯỜI LÀM bài. Trước 20/09/2026 '
      + 'mục này cố ý không ẩn theo vai ("giảng viên cũng có thể đang học") — '
      + 'đi thử bằng sáu vai cho thấy cái giá: trợ giảng gắn với lớp qua cùng '
      + 'bảng `class_members` với học viên, nên trang này mời trợ giảng "Làm bài" '
      + 'bài tập của chính lớp mình phụ trách. Nhân sự giao/chấm bài ở /giang-day.',
  },
];
