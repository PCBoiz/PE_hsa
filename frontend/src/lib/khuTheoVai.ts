/**
 * KHU LÀM VIỆC THEO VAI — nội dung "Trang của tôi" của NHÂN SỰ (20/09/2026).
 *
 * Nhân sự vào `/dashboard` từng thấy nguyên màn luyện thi của học viên. Nay họ
 * thấy đúng các khu của vai mình, mỗi khu một câu nói nó dùng để làm gì — một
 * giảng viên mới vào không phải đoán "Giảng dạy" với "Vận hành" khác nhau ra sao.
 *
 * `vai` của mỗi thẻ là BẢN CHÉP của cổng thật (`cong`) — chép để tệp này không
 * phải nhập từ `app/` (phụ thuộc ngược). Bản chép thì trôi được, nên
 * `e2e/unit/khu-theo-vai.test.mjs` đọc cổng thật ở nguồn của nó và đòi hai bên
 * KHỚP TỪNG VAI:
 *   · `IsTeachingStaff`  → `lib/quyenVai.ts::VAI_CUA_LOP_QUYEN` (đã ràng với
 *                          `common/permissions.py` bởi `quyen-vai.test.mjs`)
 *   · `van-hanh`         → `app/(standalone)/quan-tri/vai.ts` (`VAI_VAO_KHU`, hoặc
 *                          `TABS[href].vai` khi thẻ trỏ vào một trang cụ thể)
 *   · `soan-giao-trinh`  → `app/(standalone)/admin/page.tsx::DUOC_VAO`
 *   · `moi-nhan-su`      → cả năm vai nhân sự, không cổng
 * Thêm thẻ mới mà không có `cong` là phép kiểm đỏ. Thêm khu mới thì vẫn phải ĐI
 * THỬ bằng tài khoản của vai đó (lượt đi sáu vai 20/09) — phép kiểm giữ cho
 * bảng không lệch cổng, không thay được việc bấm vào xem trang có mở không.
 */
import {
  VAI_BIEN_TAP,
  VAI_GIANG_VIEN,
  VAI_HOC_VU,
  VAI_QUAN_TRI,
  VAI_TRO_GIANG,
} from './vaiTro';

export type CongKhu = 'IsTeachingStaff' | 'van-hanh' | 'soan-giao-trinh' | 'moi-nhan-su';

export type KhuViec = {
  nhan: string;
  moTa: string;
  icon: string;
  /** Tuyến Next riêng (thẻ `<a>`), hoặc tab của SPA Trang của tôi (`navigate`). */
  url?: string;
  tab?: string;
  /** Cổng thật quyết định ai vào được — xem đầu tệp. */
  cong: CongKhu;
  vai: readonly string[];
};

const DAY = [VAI_GIANG_VIEN, VAI_TRO_GIANG, VAI_HOC_VU, VAI_QUAN_TRI];
const MOI_NHAN_SU = [...DAY, VAI_BIEN_TAP];

export const KHU_VIEC: readonly KhuViec[] = [
  {
    nhan: 'Việc hôm nay', icon: 'check-circle-2', url: '/giang-day', cong: 'IsTeachingStaff', vai: DAY,
    moTa: 'Buổi chưa điểm danh, bài chưa chấm, em vắng liền — gom từ mọi lớp của bạn.',
  },
  {
    nhan: 'Lớp của tôi', icon: 'users', tab: 'teach', cong: 'IsTeachingStaff', vai: DAY,
    moTa: 'Danh sách lớp, ai đang cần chú ý, hồ sơ học tập của từng em.',
  },
  {
    nhan: 'Vận hành trung tâm', icon: 'shield', url: '/quan-tri/tong-quan', cong: 'van-hanh',
    vai: [VAI_HOC_VU, VAI_QUAN_TRI],
    moTa: 'Tài khoản, lớp, đợt học, liên hệ phụ huynh, nhật ký thao tác.',
  },
  {
    nhan: 'Soạn giáo trình', icon: 'wrench', url: '/admin', cong: 'soan-giao-trinh',
    vai: [VAI_BIEN_TAP, VAI_QUAN_TRI],
    moTa: 'Khoá, bài, câu hỏi; nhập đề từ bảng tính.',
  },
  {
    nhan: 'Xem khoá học', icon: 'library', tab: 'courses', cong: 'moi-nhan-su', vai: MOI_NHAN_SU,
    moTa: 'Nội dung đúng như học viên thấy — để soát bài hoặc chuẩn bị buổi dạy.',
  },
  {
    nhan: 'Diễn đàn', icon: 'chat', tab: 'forum', cong: 'moi-nhan-su', vai: MOI_NHAN_SU,
    moTa: 'Câu hỏi học viên đăng, và trả lời của nhau.',
  },
  {
    nhan: 'Hướng dẫn từng bước', icon: 'book-open', url: '/quan-tri/huong-dan', cong: 'van-hanh',
    vai: [VAI_HOC_VU, VAI_QUAN_TRI],
    moTa: 'Cách làm những việc hay gặp: mở lớp, thêm học viên, gửi báo cáo phụ huynh.',
  },
];

export const khuCua = (vai?: string) => (vai ? KHU_VIEC.filter((k) => k.vai.includes(vai)) : []);
