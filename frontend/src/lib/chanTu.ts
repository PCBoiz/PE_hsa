/**
 * Mã HTTP của một lần bị từ chối → giá trị móc `data-chan` trên màn chặn.
 *
 * Ba chuyện KHÁC NHAU, và người dùng phải đi hỏi ba chỗ khác nhau:
 *
 *   `vai`         · 403 — vai của bạn không làm được việc này
 *   `khong-thay`  · 404 — không có, hoặc không phải của bạn (lớp của giảng viên
 *                   khác trả 404 chứ không 403, để không lộ rằng lớp ấy tồn tại)
 *   `loi`         · mọi thứ khác — máy chủ ngủ, mạng hỏng; chưa biết quyền ra sao
 *
 * Móc này có để e2e đọc TRẠNG THÁI thay vì dò câu chữ. Đo 23/09/2026: bộ dò chữ
 * bỏ sót ba màn chặn thật, vì mỗi màn nói một câu riêng — và câu chữ là thứ
 * người ta sửa thường xuyên nhất cho dễ hiểu.
 */
export type Chan = 'vai' | 'khong-thay' | 'loi';

/** `null` là thật chứ không phải phòng xa: `serverJson` trả `status: null` khi
 *  không nhận được phản hồi nào — mạng hỏng, máy chủ ngủ. Rơi vào `loi`. */
export function chanTu(status: number | null | undefined): Chan {
  if (status === 403) return 'vai';
  if (status === 404) return 'khong-thay';
  return 'loi';
}
