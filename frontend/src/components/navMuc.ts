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
  /** Câu giải thích, chỉ để đọc mã. */
  ghi_chu?: string;
};

export const MUC_NAV: MucNav[] = [
  { trang: 'dashboard', nhan: 'Dashboard', icon: 'home', emoji: '🏠', url: '/dashboard' },
  { trang: 'courses', nhan: 'Khóa học', icon: 'library', emoji: '📖', url: '/dashboard#courses' },
  {
    trang: 'plan', nhan: 'Kế hoạch', icon: 'calendar', emoji: '🗓️', url: '/dashboard#plan',
    ghi_chu: 'Vế System-Guided. Khác "Lộ trình" (danh mục tĩnh 26 lộ trình của '
      + 'bản cũ): đây là lịch của riêng học viên, sinh từ ngày thi + sức học + '
      + 'chủ đề đang yếu.',
  },
  { trang: 'roadmap', nhan: 'Lộ trình', icon: 'map', emoji: '🗺️', url: '/dashboard#roadmap' },
  {
    trang: 'skills', nhan: 'Kỹ năng', icon: 'medal', emoji: '🏅', url: '/dashboard#skills',
    ghi_chu: 'Mục BỊ MẤT khỏi thanh chính cho tới 01/09/2026 — xem đầu tệp.',
  },
  { trang: 'forum', nhan: 'Diễn đàn', icon: 'chat', emoji: '💬', url: '/dashboard#forum' },
  {
    trang: null, nhan: 'Thi thử', icon: 'target', emoji: '🎯', url: '/mock',
    ghi_chu: 'Tuyến Next thật, không phải trang trong SPA legacy.',
  },
  {
    trang: null, nhan: 'Bài tập', icon: 'pencil', emoji: '✏️', url: '/bai-tap',
    ghi_chu: 'Bài giảng viên giao (ERP §5). KHÔNG ẩn theo vai trò — giảng viên '
      + 'cũng có thể đang học một khoá, và trang tự trả danh sách rỗng.',
  },
];
