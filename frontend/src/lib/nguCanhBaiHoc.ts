/**
 * Ngữ cảnh trang hiện tại để trợ lý biết học viên ĐANG học bài nào.
 *
 * Máy chủ không tự biết em đang mở bài nào, nên client gói gọn phần cần thiết
 * (bài, bước đang xem, ý chính, công thức) rồi gửi kèm. Nhờ vậy trợ lý trả lời
 * BÁM bài đang học thay vì nói chung chung (audit 2026-08-14).
 *
 * ── TÍNH NĂNG NÀY ĐÃ CHẾT LẶNG BA TUẦN (vá 05/09/2026) ──────────────────────
 *
 * Bản cũ đọc `window.LESSON_CONTENT_HSA` — biến do `lesson_content_hsa.js` đặt.
 * Tệp ấy THÔI ĐƯỢC NẠP từ 19/08/2026 khi 76 bài chuyển vào CSDL, nên hàm rơi
 * vào nhánh `typeof … undefined` và trả `null` cho MỌI lần gọi, suốt ba tuần.
 * Không log, không màn hình đỏ: trợ lý vẫn trả lời, chỉ chung chung hơn.
 *
 * Nay đọc `window.__PE_BAI_DANG_MO` — do `lesson_hsa.js` công bố NGAY SAU khi
 * tải bài từ API. `e2e/unit/ngu-canh-tro-ly.test.mjs` giữ mối nối: tên biến
 * hàm này ĐỌC phải là tên biến engine GHI.
 *
 * `course_title` KHÔNG gửi từ đây: máy chủ tra từ `course_id`
 * (`chatbot/views.py::_ten_khoa`) — nơi có sự thật.
 *
 * Chuyển từ `chatbot.js::collectLessonContext` (20/09/2026). Thân hàm viết
 * không chú thích kiểu bên trong để phép kiểm unit rút ra và chạy được bằng
 * Node mà không cần bộ dịch TS.
 */
/**
 * CHỈ BA THAM SỐ (20/09/2026, OWASP LLM01). Bản trước gửi cả tên bài, chủ đề,
 * ý chính, công thức — và máy chủ nối thẳng chúng vào system prompt, tức ai
 * đăng nhập cũng viết được vài dòng vào lời hệ thống của mô hình. Nay máy chủ
 * tra bốn thứ ấy từ `lessons.content_json` bằng `course_id` + `lesson_index`;
 * `step` là một trong năm giá trị cố định của engine.
 */
export type NguCanhBaiHoc = {
  course_id: string;
  lesson_index: number | null;
  step: string;
};

type BaiDangMo = {
  courseId?: string;
  index?: number;
  lesson?: { id?: string; title?: string };
};

export function nguCanhBaiHoc(
  w: { __PE_BAI_DANG_MO?: BaiDangMo } = window as unknown as { __PE_BAI_DANG_MO?: BaiDangMo },
  d: Document = document,
): NguCanhBaiHoc | null {
  try {
    const mo = w.__PE_BAI_DANG_MO;
    if (!mo || !mo.lesson) return null;
    const stepEl = d.querySelector('.progress-step.active');
    const stepNames = ['Kiểm tra', 'Đánh giá', 'Lý thuyết', 'Ghi chú', 'Luyện tốc độ'];
    const stepNum = stepEl ? parseInt(stepEl.getAttribute('data-step') || '1', 10) : 1;
    return {
      course_id: mo.courseId || d.body.getAttribute('data-course') || '',
      lesson_index: mo.index || null,
      step: stepNames[(stepNum || 1) - 1] || '',
    };
  } catch {
    return null; // ngữ cảnh chỉ là phần bổ trợ — hỏng thì vẫn chat bình thường
  }
}
