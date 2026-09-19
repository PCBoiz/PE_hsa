/**
 * KHU LÀM VIỆC THEO VAI — nội dung "Trang của tôi" của NHÂN SỰ (20/09/2026).
 *
 * Nhân sự vào `/dashboard` từng thấy nguyên màn luyện thi của học viên. Nay họ
 * thấy đúng các khu của vai mình, mỗi khu một câu nói nó dùng để làm gì — một
 * giảng viên mới vào không phải đoán "Giảng dạy" với "Vận hành" khác nhau ra sao.
 *
 * MỖI `vai` Ở ĐÂY ĐÃ ĐI THỬ bằng tài khoản thật của vai đó (lượt đi sáu vai
 * 20/09): khu nào trả "Không đủ quyền" cho một vai thì vai ấy không có tên ở
 * dòng của khu đó. Thêm khu mới thì đi thử lại — dựng một thẻ dẫn tới bức
 * tường là đúng cái lỗi tệp này sinh ra để tránh.
 */
import {
  VAI_BIEN_TAP,
  VAI_GIANG_VIEN,
  VAI_HOC_VU,
  VAI_QUAN_TRI,
  VAI_TRO_GIANG,
} from './vaiTro';

export type KhuViec = {
  nhan: string;
  moTa: string;
  icon: string;
  /** Tuyến Next riêng (thẻ `<a>`), hoặc tab của SPA Trang của tôi (`navigate`). */
  url?: string;
  tab?: string;
  vai: readonly string[];
};

const DAY = [VAI_GIANG_VIEN, VAI_TRO_GIANG, VAI_HOC_VU, VAI_QUAN_TRI];
const MOI_NHAN_SU = [...DAY, VAI_BIEN_TAP];

export const KHU_VIEC: readonly KhuViec[] = [
  {
    nhan: 'Việc hôm nay', icon: 'check-circle-2', url: '/giang-day', vai: DAY,
    moTa: 'Buổi chưa điểm danh, bài chưa chấm, em vắng liền — gom từ mọi lớp của bạn.',
  },
  {
    nhan: 'Lớp của tôi', icon: 'users', tab: 'teach', vai: DAY,
    moTa: 'Danh sách lớp, ai đang cần chú ý, hồ sơ học tập của từng em.',
  },
  {
    nhan: 'Vận hành trung tâm', icon: 'shield', url: '/quan-tri/tong-quan', vai: [VAI_HOC_VU, VAI_QUAN_TRI],
    moTa: 'Tài khoản, lớp, đợt học, liên hệ phụ huynh, nhật ký thao tác.',
  },
  {
    nhan: 'Soạn giáo trình', icon: 'wrench', url: '/admin', vai: [VAI_BIEN_TAP, VAI_QUAN_TRI],
    moTa: 'Khoá, bài, câu hỏi; nhập đề từ bảng tính.',
  },
  {
    nhan: 'Xem khoá học', icon: 'library', tab: 'courses', vai: MOI_NHAN_SU,
    moTa: 'Nội dung đúng như học viên thấy — để soát bài hoặc chuẩn bị buổi dạy.',
  },
  {
    nhan: 'Diễn đàn', icon: 'chat', tab: 'forum', vai: MOI_NHAN_SU,
    moTa: 'Câu hỏi học viên đăng, và trả lời của nhau.',
  },
  {
    nhan: 'Hướng dẫn từng bước', icon: 'book-open', url: '/quan-tri/huong-dan', vai: [VAI_HOC_VU, VAI_QUAN_TRI],
    moTa: 'Cách làm những việc hay gặp: mở lớp, thêm học viên, gửi báo cáo phụ huynh.',
  },
];

export const khuCua = (vai?: string) => (vai ? KHU_VIEC.filter((k) => k.vai.includes(vai)) : []);
