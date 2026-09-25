/**
 * Tên tiếng Việt của từng mã hành động trong nhật ký (`admin_audit.action`).
 *
 * DỜI từ `quan-tri/nhat-ky/page.tsx` (V-n, 25/09/2026): nay HAI màn đọc bảng này — Nhật ký
 * (quản trị viên) và "Lịch sử thay đổi" của một lớp (học vụ). Chép sang màn thứ hai là bản
 * thứ hai sẽ trôi; `e2e/unit/nhan-nhat-ky.test.mjs` đọc tệp NÀY và đối chiếu với
 * `backend/common/audit.py`.
 */
/**
 * Tên việc, bằng tiếng Việt.
 *
 * Cột `admin_audit.action` lưu mã máy (`attendance.mark`, `user.password_reset`)
 * — đúng cho CSDL, nhưng nhật ký này là thứ trợ giảng và quản lý trung tâm đọc
 * khi có chuyện xảy ra. Hiện mã trần lên màn hình là bắt người đọc tự dịch đúng
 * lúc họ đang cần đọc nhanh nhất (RULES §10).
 *
 * Khoá ở đây phải khớp hằng số trong `backend/common/audit.py`. Mã lạ thì hiện
 * nguyên mã chứ KHÔNG giấu đi: một dòng nhật ký không đọc được vẫn hơn một dòng
 * nhật ký biến mất.
 */
export const VIEC: Record<string, string> = {
  'user.create': 'Cấp tài khoản',
  'user.role': 'Đổi vai trò',
  'user.status': 'Khoá / mở tài khoản',
  'user.password_reset': 'Đặt lại mật khẩu',
  // 23/09/2026 (§51): học vụ sửa hồ sơ, giảng viên sửa mục tiêu/nguyện vọng.
  // Cột "Nội dung" nêu các ô đã đổi; giá trị cũ nằm trong `detail.cu`.
  'user.profile': 'Sửa hồ sơ học viên',
  // §52: chủ tài khoản tự đặt lại qua đường dẫn trong email (người làm = người bị đổi).
  'user.password_self_reset': 'Tự đặt lại mật khẩu qua email',
  'class.create': 'Tạo lớp',
  'class.update': 'Sửa lớp',
  'class.delete': 'Xoá lớp',
  'class.member.add': 'Thêm vào lớp',
  'class.member.remove': 'Cho rời lớp',
  'class.member.transfer': 'Chuyển lớp',
  'class.member.import': 'Nhập học viên từ tệp',
  // 25/09/2026 (V-a, V-f): nhận xét gửi phụ huynh, cờ cần hỗ trợ, đề xuất hướng học.
  'class.member.assess': 'Đánh giá học viên',
  'class.parent_contacts': 'Nhập liên hệ phụ huynh',
  'session.create': 'Tạo buổi học',
  'session.update': 'Sửa buổi học',
  'session.delete': 'Xoá buổi học',
  'session.generate': 'Sinh buổi học hàng loạt',
  'attendance.mark': 'Điểm danh',
  // Báo cáo phụ huynh (14/09/2026): đường công khai tới tờ báo cáo một em là
  // dữ liệu của một đứa trẻ đi ra ngoài cửa — phải thấy ở đây, không phải ở SQL.
  'parent_link.create': 'Phát hành link báo cáo phụ huynh',
  'parent_link.revoke': 'Thu hồi link báo cáo phụ huynh',
  'parent_report.send_all': 'Gửi báo cáo cả lớp',
  // 16/09/2026: điểm kỳ thi thử đọc từ PDF đi thẳng vào tờ gửi về nhà.
  'exam.external_import': 'Nhập kết quả thi thử từ PDF',
  // Nhóm `term.*` thêm 31/08/2026 cùng tính năng đợt học. Đây đúng là cách
  // bảng nhãn này trôi khỏi backend: thêm hành động mới ở `common/audit.py` mà
  // quên chỗ này, và mã máy lại lọt ra màn hình — đúng thứ chú thích trên vừa
  // nói là không được để xảy ra.
  'term.create': 'Tạo đợt học',
  'term.update': 'Sửa đợt học',
  'term.delete': 'Xoá đợt học',
  'term.holiday.add': 'Khai ngày nghỉ của đợt',
  'term.holiday.delete': 'Xoá ngày nghỉ của đợt',
  // Bốn nhóm dưới đây thêm ở backend từ 31/08 tới 04/09 và lọt ra màn hình
  // dưới dạng mã máy suốt hai tuần — dù chú thích ngay trên đã dặn. Lời dặn
  // nằm ở tệp mà người thêm hằng số không mở; nay `e2e/unit/nhan-nhat-ky`
  // đọc cả hai tệp và đỏ ở CI của chính người ấy.
  'assignment.create': 'Giao bài',
  'assignment.update': 'Sửa bài đã giao',
  'assignment.delete': 'Xoá bài đã giao',
  'assignment.grade': 'Chấm bài',
  'course.create': 'Tạo khoá học',
  'course.update': 'Sửa khoá học',
  // Khung chương trình theo buổi (§64, 25/09/2026).
  'syllabus.create': 'Tạo khung chương trình',
  'syllabus.update': 'Sửa khung chương trình',
  'syllabus.delete': 'Xoá khung chương trình',
  'syllabus.publish': 'Xuất bản khung chương trình',
  'class.syllabus.assign': 'Gán khung chương trình cho lớp',
  'course.delete': 'Xoá khoá học',
  'course.import': 'Nhập giáo trình',
  'course.publish': 'Mở / chuyển nháp khoá học',
  'lesson.create': 'Thêm bài học',
  'lesson.update': 'Sửa thông tin bài',
  'lesson.delete': 'Xoá bài học',
  'lesson.content': 'Sửa nội dung bài',
  'mock_exam.create': 'Tạo đề thi thử',
  'mock_exam.update': 'Sửa đề thi thử',
  // Một mã cho cả hai chiều (xem `mockexam/quan_tri.py`) — cột "Nội dung" nói
  // rõ là xuất bản hay ẩn.
  'mock_exam.publish': 'Xuất bản / ẩn đề thi thử',
};

/** Nhãn một mã hành động — mã lạ hiện nguyên (một dòng không đọc được vẫn hơn một dòng biến mất). */
export function nhanViec(action: string): string {
  return VIEC[action] || action;
}
