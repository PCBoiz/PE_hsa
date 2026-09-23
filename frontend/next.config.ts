import type { NextConfig } from "next";

/**
 * Header bảo mật cho MỌI phản hồi của Vercel (trang, `/api/*` qua proxy, tệp tĩnh).
 *
 * Vì sao (14/09/2026, rà hạ tầng): backend Render đã gửi đủ CSP, nosniff,
 * X-Frame-Options, Referrer-Policy — nhưng người dùng KHÔNG BAO GIỜ mở trang
 * Render; họ mở `pe-hsa.vercel.app`, và ở đó chỉ có HSTS, kèm `X-Powered-By:
 * Next.js`. Lớp bảo vệ dựng xong mà đặt nhầm cửa.
 *
 * Danh sách nguồn đo từ mã, không chép từ backend (grep 14/09/2026):
 * - script ngoài: chỉ `cdn.jsdelivr.net` (canvas-confetti ở `LessonHsa.tsx`).
 * - style/phông ngoài: chỉ Font Awesome ở `cdnjs.cloudflare.com`; phông chính do
 *   `next/font` tự lưu trên cùng miền.
 * - ảnh/iframe/fetch ra ngoài: 0 — kể cả nội dung trong CSDL (quét mọi cột chữ:
 *   máy chủ ngoài duy nhất là link Meet, là điều hướng, CSP không chặn).
 * - trình duyệt gọi API qua `/api/*` cùng miền → `connect-src 'self'`.
 *
 * Còn NỚI, có chủ đích — đừng tưởng đây là CSP chặt:
 * - `'unsafe-inline'` ở script: bốn `<script>` nội tuyến (chống nháy theme, gốc
 *   API) + `onclick="…"` khắp tầng cũ + script khởi động của Next. Bỏ được khi
 *   chuyển sang nonce, mà nonce buộc mọi trang dựng động.
 * - `'unsafe-eval'`: CHỈ khi chạy dev. Production gỡ từ 15/09/2026 — đồ thị bài
 *   học thôi dùng `new Function`, điểm do máy chủ tính (`backend/lessons/do_thi.py`).
 *   Dev vẫn cần: React dùng `eval` để dựng lại ngăn xếp lỗi phía máy chủ trên trình
 *   duyệt (tài liệu đi kèm gói: `next/dist/docs/01-app/02-guides/content-security-policy.md`).
 * Dù vậy CSP này vẫn chặn thật: nhúng trang vào iframe lạ (clickjacking), gửi
 * dữ liệu đi máy chủ lạ bằng fetch/ảnh, `<base>` giả, `<object>`, form trỏ ra ngoài.
 */
const CSP = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${process.env.NODE_ENV === 'production' ? '' : " 'unsafe-eval'"} https://cdn.jsdelivr.net`,
  "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com",
  "font-src 'self' data: https://cdnjs.cloudflare.com",
  "img-src 'self' data: blob:",
  "media-src 'self' data: blob:",
  "connect-src 'self'",
  // canvas-confetti dựng worker từ blob: — bị chặn thì nó tự lùi về luồng chính,
  // nhưng để lại lỗi đỏ trong console mỗi lần hoàn thành bài.
  "worker-src 'self' blob:",
  "frame-src 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join('; ');

const DAU_BAO_MAT = [
  { key: 'Content-Security-Policy', value: CSP },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  // Trình duyệt cũ không hiểu `frame-ancestors` — giữ cả hai.
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  // Sản phẩm không dùng camera/mic/vị trí/thanh toán — tắt hẳn, để một script
  // lọt vào cũng không xin được quyền. Clipboard KHÔNG tắt: nút "Sao chép"
  // đường dẫn báo cáo phụ huynh và mật khẩu tạm dùng nó.
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), browsing-topics=()' },
  // Không trang nào mở cửa sổ bật lên (đăng nhập Google/Facebook là điều hướng
  // cả trang sang backend), nên cô lập ngữ cảnh duyệt không làm gãy gì.
  { key: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
];

const nextConfig: NextConfig = {
  // Không quảng cáo phiên bản khung — bớt một manh mối cho người dò lỗ hổng.
  poweredByHeader: false,
  async headers() {
    return [{ source: '/:path*', headers: DAU_BAO_MAT }];
  },
  /* Sáu view của Trang của tôi là view trong CÙNG trang /dashboard, không phải
     tuyến riêng — nên gõ thẳng /courses (theo trí nhớ, hay dán lại từ tin nhắn)
     ra "Không có trang này" (agent rà điện thoại, 20/09/2026). Chuyển về đúng
     view; `DashboardClient` đọc `location.hash` lúc hydrate. Tạm thời (307),
     để sau này view nào thành tuyến thật thì gỡ dòng của nó là xong. */
  async redirects() {
    return [
      ...['courses', 'roadmap', 'skills', 'forum', 'settings', 'profile', 'plan'].map((v) => ({
        source: `/${v}`,
        destination: `/dashboard#${v}`,
        permanent: false,
      })),
      /* Khu soạn bài đổi tên `/admin` → `/giao-trinh` (24/09/2026, góp ý TopHSA #4:
         "sao soạn giáo trình lại nằm trong khu vận hành"). Link cũ trong thư, dấu
         trang, cẩm nang in ra vẫn mở được. */
      { source: '/admin', destination: '/giao-trinh', permanent: false },
      /* Bỏ thi, pha A (24/09/2026 — anh Sơn chốt "bỏ mọi thứ về thi, giữ ngày thi
         HSA"): màn thi thử và màn nhập kết quả thi đã gỡ, tuyến API của chúng tháo.
         Link cũ (dấu trang, thư, cẩm nang in) đưa về chỗ gần nhất thay vì "Không
         có trang này". TẠM (307) như trên: pha A đảo ngược được, còn 308 thì trình
         duyệt nhớ luôn. Guard: `e2e/unit/bo-thi.test.mjs`. */
      { source: '/mock', destination: '/dashboard', permanent: false },
      {
        source: '/giang-day/ket-qua-thi/:classId',
        destination: '/giang-day/buoi-hoc/:classId',
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
