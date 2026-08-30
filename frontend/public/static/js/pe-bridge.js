/**
 * pe-bridge.js — cầu nối giữa JavaScript cũ trong thư mục này và vỏ Next.js.
 *
 * BẢN RÚT GỌN 27/08/2026. Trước đây file này phải làm rất nhiều: viết lại URL
 * `/api/*` sang miền backend, đọc token từ localStorage gắn vào từng request,
 * tự đổi refresh token khi gặp 401, dedupe các lời gọi refresh chạy song song…
 *
 * Toàn bộ những việc đó nay do máy chủ Next làm (src/lib/proxy.ts). Trình
 * duyệt gọi `/api/...` trên chính miền đang đứng, máy chủ đọc cookie httpOnly
 * rồi gắn `Authorization` giúp. Nghĩa là:
 *
 *   · JavaScript cũ giữ nguyên đường dẫn tương đối — không phải sửa gì.
 *   · Không đoạn script nào trên trang đọc được token nữa, kể cả script chèn
 *     lậu qua một lỗ XSS. Đó là lý do chính của lần đổi này.
 *   · Token hết hạn được làm mới ở máy chủ, không còn cảnh hai lời gọi refresh
 *     song song đá người dùng ra ngoài oan.
 *
 * File vẫn PHẢI được nạp trước mọi script cũ khác: `main.js` bọc `window.fetch`
 * ngay lúc nạp, nên thứ tự quyết định chuỗi bọc có đúng không.
 */
(function () {
  'use strict';

  /* Giữ lại cho tương thích: vài chỗ trong mã cũ vẫn đọc biến này để dựng URL.
     Rỗng = cùng miền, nên phép nối chuỗi vẫn ra đường dẫn đúng. */
  window.__PE_API_ORIGIN = window.__PE_API_ORIGIN || '';

  /* Thân lỗi từ backend có hai dạng: {error: 'chuỗi'} và
     {error: {status, message, detail}}. Mã cũ gọi alert(res.error) thẳng nên
     dạng thứ hai sẽ hiện "[object Object]" — helper này rút lấy câu tiếng Việt
     dùng được cho cả hai. Đang được gọi ở 7 chỗ trong course_detail,
     dashboard, main và review_quiz. */
  window.__PE_errMsg = function (e) {
    if (e && typeof e === 'object') return e.message || JSON.stringify(e);
    return e;
  };

  /* ── Phiên hết hạn thì đưa về trang đăng nhập ───────────────────────────
     Máy chủ đã thử làm mới token trước khi trả 401, nên 401 tới được đây
     nghĩa là hết hạn thật. Không chuyển hướng khi đang ở trang công khai: ở đó
     401 là chuyện bình thường (trang chủ vẫn hỏi /api/user để biết có ai đăng
     nhập hay chưa), chuyển hướng sẽ thành vòng lặp. */
  var PUBLIC_PAGES = ['/', '/login'];
  var _origFetch = window.fetch.bind(window);

  window.fetch = function (url, opts) {
    return _origFetch(url, opts).then(function (resp) {
      if (
        resp.status === 401 &&
        typeof url === 'string' &&
        url.indexOf('/api/') === 0 &&
        PUBLIC_PAGES.indexOf(window.location.pathname) === -1
      ) {
        window.location.replace('/login?error=het_han');
      }
      return resp;
    });
  };

  /* ── Vá DOMContentLoaded ────────────────────────────────────────────────
     Script cũ được nạp SAU khi React đã dựng xong DOM, nên listener
     DOMContentLoaded đăng ký muộn sẽ không bao giờ chạy. Gọi thẳng handler khi
     tài liệu đã qua giai đoạn 'loading'. */
  var _addEventListener = document.addEventListener.bind(document);
  document.addEventListener = function (type, handler, options) {
    if (type === 'DOMContentLoaded' && document.readyState !== 'loading') {
      setTimeout(function () {
        handler.call(document, new Event('DOMContentLoaded'));
      }, 0);
      return;
    }
    return _addEventListener(type, handler, options);
  };
})();
