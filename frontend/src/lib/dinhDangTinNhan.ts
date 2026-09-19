/**
 * Chữ của trợ lý → HTML: THOÁT HTML TRƯỚC, rồi mới áp markdown nhẹ.
 *
 * Chuyển từ `chatbot.js::formatChatbotMessage` (20/09/2026) khi trợ lý sang
 * React. Thứ tự là thứ giữ an toàn: mọi `<` của mô hình (hay của người dùng
 * dội lại) thành `&lt;` trước khi bất kỳ thẻ nào được sinh ra, nên HTML ra
 * khỏi đây chỉ có `pre/code/strong/em/br` do chính hàm này viết.
 *
 * Prompt máy chủ đã cấm bảng, tiêu đề `#`, khối mã, LaTeX — nên ở đây cố ý
 * KHÔNG dựng chúng: không có bộ dựng thì lời cấm bị quên cũng chỉ ra chữ thô,
 * không ra một bảng vỡ.
 */
export function thoatHtml(chu: string): string {
  return chu.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export function dinhDangTinNhan(chu: string): string {
  let s = thoatHtml(chu);
  s = s.replace(/```([\s\S]*?)```/g, (_m, ma: string) => `<pre><code>${ma.trim()}</code></pre>`);
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/__([^_]+)__/g, '<strong>$1</strong>');
  s = s.replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
  /* `_x_` chỉ thành nghiêng khi ĐỨNG RIÊNG (có khoảng trắng/đầu dòng hai bên):
     công thức kiểu `x_1` hay `a_n` từng bị bản cũ biến thành nghiêng nửa chừng. */
  s = s.replace(/(^|\s)_([^_\n]+)_(?=\s|$|[.,;:!?)])/g, '$1<em>$2</em>');
  return s.replace(/\n/g, '<br>');
}
