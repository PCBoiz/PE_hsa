'use client';

import { BieuTuong } from './bieuTuong';

// Port chatbot.html (Jinja partial include ở 6 trang) — markup 1:1.
// Logic nằm nguyên trong chatbot.js (legacy); handler gọi global.
/* eslint-disable @typescript-eslint/no-explicit-any */
const W = () => window as any;

export default function Chatbot() {
  return (
    <>
      {/* KHÔNG còn Font Awesome ở đây (14/09/2026).
        *
        * ── LỊCH SỬ NGẮN ─────────────────────────────────────────────────────
        *
        * 07/09 tôi gỡ Font Awesome khỏi `(base)/layout.tsx` (100 kB CSS, "0 lần
        * dùng `fa-`") — kết luận sai, 12 biểu tượng của trợ lý AI hiện 0×0px
        * trên production. Vá cùng ngày bằng cách cho component này TỰ nạp, và
        * ghi rõ cái giá: `/dashboard` nhận lại 100 kB, cách đúng là chuyển 11
        * biểu tượng sang bộ SVG riêng.
        *
        * 14/09 mổ xẻ LCP Trang của tôi: ở lượt lạnh, tệp CSS ấy tải từ cdnjs
        * mất 2,9 s và LCP là 4,7 s; long task = 0 ms — tức không phải mã chạy
        * chậm, mà là một tài nguyên ngoài miền chen vào đường vẽ. Đây là lúc
        * làm "việc riêng" hôm ấy.
        *
        * ── NAY ──────────────────────────────────────────────────────────────
        *
        * Mọi biểu tượng là `BieuTuong` (SVG inline, sinh từ `icons.js`, nhận
        * `currentColor` nên đổi màu theo nút khi rê chuột — Font Awesome cũng
        * thế, nhưng phải tải 100 kB rồi thêm một phông woff2 mới vẽ được).
        * `chatbot.js` (tầng cũ) vẽ tin nhắn lúc chạy và cũng cần hai hình
        * bot/user: nó KHÔNG nạp `icons.js` ở mọi trang có gắn chatbot, nên thay
        * vì trông vào global `Icon`, nó nhân bản SVG từ ô `#chatbot-bieu-tuong`
        * ẩn dưới đây — một nguồn hình, hai tầng cùng đọc.
        *
        * `e2e/unit/font-awesome-tu-nap.test.mjs` vẫn canh: tệp .tsx nào dùng
        * `fa-` thì phải tự nạp; tệp này nay không dùng nên không nạp. */}
      <div id="chatbot-bieu-tuong" hidden aria-hidden="true">
        <span data-ten="bot"><BieuTuong ten="bot" co={16} /></span>
        <span data-ten="user"><BieuTuong ten="user" co={16} /></span>
      </div>

      {/* Floating Chat Button */}
      {/* Trợ lý là công cụ ÔN THI: prompt coi người dùng là học sinh và bơm hồ sơ
          học tập vào. Nhân sự không thấy nút (20/09/2026, `lib/nhomVai.ts`). */}
      <button id="chatbot-toggle" className="chatbot-floating-btn" aria-label="Mở trợ lý AI" data-chi-hoc-vien="">
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
      <div id="chatbot-window" className="chatbot-window chatbot-hidden" data-chi-hoc-vien="">
        <div className="chatbot-header">
          <div className="chatbot-header-left">
            <div className="chatbot-avatar">
              <BieuTuong ten="bot" co={22} />
            </div>
            <div className="chatbot-header-text">
              <h3>Trợ lý HSA</h3>
              <span className="chatbot-status"><span className="chatbot-status-dot"></span> Trực tuyến</span>
            </div>
          </div>
          <button id="chatbot-close" className="chatbot-close-btn" aria-label="Đóng chat">
            <BieuTuong ten="x" co={18} />
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
                Chào bạn! 👋 Mình là Trợ lý HSA. Hỏi mình về bài đang học, cách làm một dạng bài,
                hay chụp đề gửi lên để mình hướng dẫn nhé.
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
              <BieuTuong ten="trash-2" co={14} />
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
              <BieuTuong ten="lightbulb" co={13} />
              <span>Giảng lại</span>
            </button>
            <button className="chatbot-quick-btn" onClick={() => W().quickChatbotAsk('Bài này hay có bẫy gì trong đề HSA? Mẹo làm nhanh là gì?')}>
              <BieuTuong ten="triangle-alert" co={13} />
              <span>Bẫy &amp; mẹo</span>
            </button>
            <button className="chatbot-quick-btn" onClick={() => W().quickChatbotAsk('Cho mình 3 câu luyện thêm dạng này, kèm đáp án và lời giải.')}>
              <BieuTuong ten="square-pen" co={13} />
              <span>Luyện thêm</span>
            </button>
            <button className="chatbot-quick-btn" onClick={() => W().generateChatbotRoadmap()}>
              <BieuTuong ten="map" co={13} />
              <span>Lộ trình</span>
            </button>
          </div>

          <div className="chatbot-input-box">
            <label htmlFor="chatbot-image-upload" className="chatbot-attach-btn" title="Đính kèm hình ảnh">
              <BieuTuong ten="paperclip" co={16} />
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
              <BieuTuong ten="arrow-up" co={16} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
