'use client';

import { BieuTuong } from './bieuTuong';

// Port chatbot.html (Jinja partial include ở 6 trang) — markup 1:1.
// Logic nằm nguyên trong chatbot.js (legacy); handler gọi global.
/* eslint-disable @typescript-eslint/no-explicit-any */
const W = () => window as any;

export default function Chatbot() {
  return (
    <>
      {/* Font Awesome — component này TỰ nạp, không trông chờ trang cha.
        *
        * ── VÌ SAO (hồi quy do chính tôi gây ra, 07/09/2026) ──────────────────
        *
        * Sáng nay tôi gỡ Font Awesome khỏi `(base)/layout.tsx` để tiết kiệm
        * 100kB, sau khi grep và kết luận "0 lần dùng class `fa-`". Kết luận ấy
        * SAI: chính tệp này dùng 10 biểu tượng `fa-`, và `chatbot.js` dùng thêm
        * 4. Đo sau đó trên `/dashboard`: 12 thẻ `<i class="fa-*">` hiện ở
        * **0×0px**, `::before` rỗng — trợ lý AI mất sạch biểu tượng, và bản ấy
        * đã lên production.
        *
        * Vì sao tự nạp chứ không trả Font Awesome về layout: chatbot được gắn ở
        * BỐN nơi (`/dashboard`, `courses/[courseId]`, `LessonHsa`, `MockExam`).
        * Ba nơi kia đã tự nạp sẵn, nên chỉ `/dashboard` hỏng. Nếu vá bằng cách
        * sửa layout thì nơi gắn thứ NĂM sẽ lại hỏng y hệt, và lại không ai
        * biết. Đặt lời nạp cạnh chỗ dùng thì hai thứ không thể rời nhau.
        *
        * Cái giá: `/dashboard` nhận lại 100kB CSS, tức mất phần lớn phần tối ưu
        * sáng nay. Nói thẳng ra đây thay vì giấu. Cách đúng để lấy lại là
        * chuyển 11 biểu tượng này sang bộ SVG riêng của dự án (`icons.js` có 45
        * biểu tượng; 4 trong 11 đã có sẵn: sparkles, pencil, map, user) — việc
        * riêng, không làm chen vào lúc đang vá hồi quy.
        *
        * `e2e/unit/font-awesome-tu-nap.test.mjs` canh: tệp .tsx nào dùng `fa-`
        * thì phải tự nạp Font Awesome. Đó là phép kiểm mà sáng nay tôi không
        * có, nên không có gì chặn tôi lại. */}
      <link rel="preconnect" href="https://cdnjs.cloudflare.com" />
      <link
        rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
      />

      {/* Floating Chat Button */}
      <button id="chatbot-toggle" className="chatbot-floating-btn" aria-label="Mở trợ lý AI">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" className="chatbot-btn-icon">
          <path d="M12 1L13.8 9.2L22 11L13.8 12.8L12 21L10.2 12.8L2 11L10.2 9.2L12 1Z" />
          <path d="M19.5 2L20.5 6L24 7L20.5 8L19.5 12L18.5 8L15 7L18.5 6L19.5 2Z" opacity="0.75" />
          <path d="M5 15L5.8 17.7L8.5 18.5L5.8 19.3L5 22L4.2 19.3L1.5 18.5L4.2 17.7L5 15Z" opacity="0.65" />
        </svg>
        <div className="chatbot-badge">
          <span className="chatbot-pulse"></span>
        </div>
      </button>

      {/* Chat Window */}
      <div id="chatbot-window" className="chatbot-window chatbot-hidden">
        <div className="chatbot-header">
          <div className="chatbot-header-left">
            <div className="chatbot-avatar">
              <i className="fas fa-robot"></i>
            </div>
            <div className="chatbot-header-text">
              <h3>Trợ lý HSA</h3>
              <span className="chatbot-status"><span className="chatbot-status-dot"></span> Trực tuyến</span>
            </div>
          </div>
          <button id="chatbot-close" className="chatbot-close-btn" aria-label="Đóng chat">
            <i className="fas fa-times"></i>
          </button>
        </div>

        <div id="chatbot-messages" className="chatbot-messages">
          <div className="chatbot-message chatbot-message-ai">
            <div className="chatbot-message-avatar">
              {/* `fa-sparkles` là biểu tượng bản PRO của Font Awesome. Trên bộ
                  Free đang nạp, nó CHƯA TỪNG hiện — đo 07/09/2026: 0×0px,
                  `::before` rỗng, trong khi `fa-robot`/`fa-user` cạnh đó đều
                  vẽ bình thường. Không lỗi nào, chỉ là một ô trống.
                  Dùng bộ SVG của dự án (`icons.js` có `sparkles`). */}
              <BieuTuong ten="sparkles" co={16} />
            </div>
            <div className="chatbot-message-content">
              <div className="chatbot-message-bubble">
                Chào bạn! 👋 Tôi là Ichatbot, trợ lý AI của bạn. Hãy hỏi tôi bất kỳ điều gì về lập trình hoặc học tập! 🚀
              </div>
            </div>
          </div>
        </div>

        <div id="chatbot-image-preview" className="chatbot-image-preview chatbot-hidden">
          <div className="chatbot-preview-item">
            {/* Không đặt src="" — React cảnh báo (browser có thể tải lại cả trang);
                chatbot.js sẽ gán .src khi user đính kèm ảnh */}
            {/* eslint-disable-next-line @next/next/no-img-element -- `next/image`
                cần biết `src` lúc dựng. Ở đây `src` do `chatbot.js` (mã ngoài
                React) gán lúc chạy, từ một blob cục bộ người dùng vừa đính kèm:
                không có URL nào để tối ưu, và cũng không đi qua mạng. */}
            <img id="chatbot-preview-img" alt="Preview" />
            <button className="chatbot-preview-remove" onClick={() => W().removeChatbotImage()} aria-label="Xóa hình ảnh">
              <i className="fas fa-trash"></i>
            </button>
          </div>
        </div>

        <div className="chatbot-input-area">
          {/* Nút gợi ý nhanh — trước đây là "Giải thích code này" / "Tối ưu
              code", tàn dư của pe_test (audit 2026-08-14). TopHSA luyện thi
              ĐGNL, không dạy lập trình. chatbot.js sẽ chèn thêm bài đang học
              vào câu hỏi khi người dùng đứng ở trang bài học. */}
          <div className="chatbot-quick-actions">
            <button className="chatbot-quick-btn" onClick={() => W().quickChatbotAsk('Giải thích giúp mình phần lý thuyết của bài này, cho ví dụ dễ hiểu.')}>
              <i className="fas fa-lightbulb"></i>
              <span>Giảng lại</span>
            </button>
            <button className="chatbot-quick-btn" onClick={() => W().quickChatbotAsk('Bài này hay có bẫy gì trong đề HSA? Mẹo làm nhanh là gì?')}>
              <i className="fas fa-triangle-exclamation"></i>
              <span>Bẫy &amp; mẹo</span>
            </button>
            <button className="chatbot-quick-btn" onClick={() => W().quickChatbotAsk('Cho mình 3 câu luyện thêm dạng này, kèm đáp án và lời giải.')}>
              <i className="fas fa-pen-to-square"></i>
              <span>Luyện thêm</span>
            </button>
            <button className="chatbot-quick-btn" onClick={() => W().generateChatbotRoadmap()}>
              <i className="fas fa-map"></i>
              <span>Lộ trình</span>
            </button>
          </div>

          <div className="chatbot-input-box">
            <label htmlFor="chatbot-image-upload" className="chatbot-attach-btn" title="Đính kèm hình ảnh">
              <i className="fas fa-paperclip"></i>
              <input type="file" id="chatbot-image-upload" className="chatbot-hidden" accept="image/*" title="Chọn hình ảnh" />
            </label>
            <input
              id="chatbot-input"
              type="text"
              placeholder="Nhập câu hỏi..."
              className="chatbot-input"
              autoComplete="off"
            />
            <button id="chatbot-send-btn" className="chatbot-send-btn" aria-label="Gửi">
              <i className="fas fa-arrow-up"></i>
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
