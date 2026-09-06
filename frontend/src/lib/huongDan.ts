/**
 * HƯỚNG DẪN VẬN HÀNH — viết theo VIỆC, không theo màn hình.
 *
 * ── VÌ SAO CÓ TỆP NÀY (07/09/2026) ────────────────────────────────────────
 *
 * Anh Sơn chốt: tài liệu đặt **trong ứng dụng** và **in ra được**, không phải
 * một tệp `.md` trong repo. Người đọc là học vụ và giảng viên — họ không mở
 * GitHub, và họ đọc lúc đang cần làm một việc cụ thể.
 *
 * Nên đơn vị ở đây là VIỆC ("xếp một học viên mới vào lớp"), không phải màn
 * hình ("trang Lớp học"). Một tài liệu xếp theo màn hình bắt người mới tự dịch
 * từ việc-họ-cần sang màn-hình-nào, mà đó chính là phần họ chưa biết.
 *
 * ── VÌ SAO ĐƯỜNG DẪN SỐNG, KHÔNG PHẢI ẢNH CHỤP MÀN ───────────────────────
 *
 * Ảnh chụp màn hỏng IM LẶNG: giao diện đổi, ảnh vẫn nằm đó dạy sai, và không
 * ai biết cho tới khi có người làm theo rồi không tìm thấy cái nút trong ảnh.
 * Đường dẫn hỏng thì trả 404, và `e2e/unit/huong-dan.test.mjs` bắt được ngay
 * lúc biên dịch — nó đối chiếu mọi `o` dưới đây với tuyến thật trong `app/`.
 *
 * Đánh đổi: người đọc phải tự nhìn màn hình thật thay vì đối chiếu với một
 * bức ảnh. Bù lại, thứ họ nhìn luôn là thứ đang chạy.
 *
 * ── CHỈ ĐƯỜNG DẪN TĨNH ───────────────────────────────────────────────────
 *
 * Không dùng tuyến động (`/giang-day/buoi-hoc/<lớp>`) làm `o`: chúng cần một
 * mã lớp mà tài liệu không biết, và một đường dẫn dựng sẵn với mã lớp bất kỳ
 * sẽ dẫn người đọc vào lớp của người khác. Bước nào cần chọn lớp thì nói bằng
 * lời.
 */

import { VAI_BIEN_TAP, VAI_GIANG_VIEN, VAI_HOC_VU, VAI_QUAN_TRI, VAI_TRO_GIANG } from './vaiTro';

export type Buoc = {
  lam: string;
  /** Đường dẫn TĨNH tới màn hình của bước này. Phép kiểm đối chiếu với `app/`. */
  o?: string;
  /** Điều dễ làm sai ở đúng bước này. Bỏ trống nếu không có gì đáng nhắc. */
  luu_y?: string;
};

export type Bai = {
  ma: string;
  tieu_de: string;
  /** Vai nào cần đọc bài này. Dùng để lọc, không phải để chặn. */
  vai: readonly string[];
  /** Khi nào việc này xảy ra — giúp người đọc biết bài nào liên quan tới mình. */
  khi_nao: string;
  buoc: Buoc[];
  /** Triệu chứng hay gặp và cách xử. Đây là phần người mới cần nhất. */
  hong_thi_sao?: { trieu_chung: string; xu_ly: string }[];
};

export const HUONG_DAN: readonly Bai[] = [
  {
    ma: 'hom-nay',
    tieu_de: 'Mở đầu ngày làm việc',
    vai: [VAI_QUAN_TRI, VAI_HOC_VU],
    khi_nao: 'Mỗi sáng, trước khi làm gì khác.',
    buoc: [
      {
        lam: 'Mở "Toàn trung tâm". Khối đầu tiên là "Hôm nay cần làm gì" — đó là danh sách việc còn tồn, không phải số liệu.',
        o: '/quan-tri/tong-quan',
      },
      {
        lam: 'Bấm thẳng vào từng dòng: mỗi việc dẫn tới đúng chỗ để làm nó.',
        luu_y: 'Danh sách trống nghĩa là hết việc tồn, không phải hệ thống chưa tải xong.',
      },
      {
        lam: 'Số liệu nằm ở khối bên dưới, để đối chiếu — không phải để bắt đầu.',
      },
    ],
    hong_thi_sao: [
      {
        trieu_chung: 'Cả trang toàn dấu "—".',
        xu_ly: 'Bình thường khi trung tâm chưa có dữ liệu. Dấu "—" nghĩa là CHƯA TÍNH ĐƯỢC, khác hẳn số 0. Ví dụ chuyên cần "—" là chưa buổi nào được điểm danh.',
      },
      {
        trieu_chung: 'Có dòng đỏ "Chưa đọc được: …".',
        xu_ly: 'Máy chủ không đọc nổi một mảng dữ liệu. Tải lại trang; còn nguyên thì báo kỹ thuật — các cột liên quan đang KHÔNG đáng tin.',
      },
    ],
  },

  {
    ma: 'tai-khoan-moi',
    tieu_de: 'Cấp tài khoản cho người mới',
    vai: [VAI_QUAN_TRI],
    khi_nao: 'Có học viên mới nhập học, hoặc trung tâm tuyển thêm giảng viên.',
    buoc: [
      {
        lam: 'Mở "Tài khoản".',
        o: '/quan-tri/tai-khoan',
        luu_y: 'Từ 27/08/2026 người dùng KHÔNG tự đăng ký được. Mọi tài khoản do trung tâm cấp.',
      },
      {
        lam: 'Một người thì điền form; cả lớp thì dán danh sách vào ô nhập hàng loạt — hệ thống báo trước dòng nào trùng email hoặc trùng số điện thoại.',
        luu_y: 'Xem trước (dry run) trước khi tạo thật. Danh sách trùng mà tạo luôn là hai tài khoản cho một người.',
      },
      {
        lam: 'Chọn vai. Không chắc chọn vai nào thì mở bảng "Ai làm được gì".',
        o: '/quan-tri/vai-tro',
        luu_y: 'Cấp vai rộng hơn mức cần là mở dữ liệu của học viên cho thêm một người. Vai mặc định là Học viên — cứ để vậy nếu chưa chắc.',
      },
      {
        lam: 'Báo cho người đó mật khẩu tạm. Lần đăng nhập đầu hệ thống bắt đổi mật khẩu trước khi vào được bất cứ đâu.',
      },
    ],
    hong_thi_sao: [
      {
        trieu_chung: 'Báo "Email đã được sử dụng" nhưng tìm không thấy ai.',
        xu_ly: 'Tài khoản có thể đang bị KHOÁ nên không hiện ở danh sách mặc định. Bỏ bộ lọc trạng thái rồi tìm lại.',
      },
    ],
  },

  {
    ma: 'xep-lop',
    tieu_de: 'Mở lớp và xếp học viên',
    vai: [VAI_QUAN_TRI, VAI_HOC_VU],
    khi_nao: 'Đầu mỗi đợt tuyển sinh, và mỗi khi có em chuyển lớp.',
    buoc: [
      {
        lam: 'Mở đợt học trước nếu chưa có. Đợt là khung thời gian để so sánh giữ chân giữa các khoá tuyển sinh.',
        o: '/quan-tri/dot-hoc',
      },
      {
        lam: 'Tạo lớp, chọn khoá và phân công giảng viên.',
        o: '/quan-tri/lop-hoc',
        luu_y: 'Lớp chưa phân công giảng viên thì KHÔNG ai điểm danh và KHÔNG ai giao bài được cho lớp đó. "Hôm nay cần làm gì" sẽ nhắc.',
      },
      {
        lam: 'Xếp học viên vào lớp.',
        luu_y: 'Sĩ số vượt sức chứa vẫn xếp được, nhưng hệ thống sẽ nhắc — lớp quá tải là lý do bỏ giữa chừng hay gặp nhất.',
      },
      {
        lam: 'Em nào rời lớp thì GHI LÝ DO ngay lúc cho rời.',
        luu_y: 'Không ghi lý do thì em đó không nằm trong tỉ lệ giữ chân, và con số ấy sẽ nói dối theo hướng đẹp hơn sự thật.',
      },
    ],
  },

  {
    ma: 'diem-danh',
    tieu_de: 'Điểm danh một buổi',
    vai: [VAI_GIANG_VIEN, VAI_TRO_GIANG, VAI_HOC_VU, VAI_QUAN_TRI],
    khi_nao: 'Ngay sau mỗi buổi dạy. Để sang hôm sau là quên ai vắng.',
    buoc: [
      {
        lam: 'Từ Trang của tôi, mở mục "Giảng dạy" rồi chọn lớp.',
        o: '/dashboard',
        luu_y: 'Giảng viên chỉ thấy lớp mình phụ trách; trợ giảng chỉ thấy lớp được gán.',
      },
      { lam: 'Chọn buổi trong danh sách, tick từng em, bấm lưu.' },
      {
        lam: 'Buổi chưa có trong danh sách thì tạo buổi trước.',
        luu_y: 'Buổi đã dạy mà không ai điểm danh thì KHÔNG được tính vào mẫu số chuyên cần — nó bị báo riêng là "chưa điểm danh". Đó là cố ý: chia vào mẫu số sẽ biến thành "con vắng" trong mắt phụ huynh.',
      },
    ],
    hong_thi_sao: [
      {
        trieu_chung: 'Chuyên cần của lớp thấp bất thường.',
        xu_ly: 'Xem "Hôm nay cần làm gì" — thường là còn buổi đã dạy mà chưa ai điểm danh.',
      },
      {
        trieu_chung: 'Bốn ô (có mặt / muộn / vắng / có phép) cộng lại không bằng số buổi.',
        xu_ly: 'Có buổi cả lớp đã tick nhưng riêng em đó bị sót dòng. Tờ báo cáo nói rõ số buổi ấy — vào buổi đó bổ sung.',
      },
    ],
  },

  {
    ma: 'bao-cao-phu-huynh',
    tieu_de: 'Gửi báo cáo cho phụ huynh',
    vai: [VAI_GIANG_VIEN, VAI_HOC_VU, VAI_QUAN_TRI],
    khi_nao: 'Cuối mỗi tháng, hoặc khi phụ huynh hỏi.',
    buoc: [
      {
        lam: 'Vào lớp, bấm "Báo cáo phụ huynh". Trang hiện bản SOẠN SẴN: ai nhận được, ai chưa có số.',
        luu_y: 'Mở trang này KHÔNG gửi gì cả. Chưa có gì rời khỏi hệ thống cho tới khi bấm nút.',
      },
      {
        lam: 'Xem qua danh sách. Em nào thiếu số Zalo của phụ huynh thì nhắc em tự điền ở Cài đặt → Liên hệ phụ huynh.',
        o: '/dashboard',
      },
      {
        lam: 'Bấm nút và xác nhận. Cửa xác nhận nêu ĐÚNG SỐ người sẽ nhận — đọc con số đó trước khi gật.',
        luu_y: 'Tin đã tới Zalo phụ huynh thì KHÔNG thu về được, và mỗi tin đều tính phí.',
      },
      {
        lam: 'Chưa nối Zalo OA thì nút cấp đường dẫn cho từng em; chép đi gửi tay.',
        luu_y: 'Ai có đường dẫn đều xem được báo cáo. Gửi RIÊNG cho phụ huynh, đừng dán vào nhóm lớp. Lỡ dán thì vào lại và thu hồi đường dẫn ấy.',
      },
    ],
    hong_thi_sao: [
      {
        trieu_chung: 'Phụ huynh báo mở link không được.',
        xu_ly: 'Đường dẫn sống 45 ngày và thu hồi được. Hết hạn hoặc đã thu hồi thì cấp lại đường dẫn mới — một câu báo lỗi duy nhất cho cả ba trường hợp, nên không đoán được là vì sao.',
      },
      {
        trieu_chung: 'Trên tờ báo cáo, "Điểm trung bình 0%".',
        xu_ly: 'Nếu em mới làm MỘT đề, tờ báo cáo tự thêm câu giải thích rằng một lượt chưa đủ để kết luận. Nếu chưa làm đề nào thì ô ấy hiện "—", không hiện 0.',
      },
    ],
  },

  {
    ma: 'giao-bai',
    tieu_de: 'Giao bài và chấm tay',
    vai: [VAI_GIANG_VIEN, VAI_TRO_GIANG],
    khi_nao: 'Khi cần bài tự luận hoặc bài nộp ảnh — bài trắc nghiệm thì hệ thống tự chấm.',
    buoc: [
      { lam: 'Vào lớp, mở "Bài tập", tạo bài và đặt hạn nộp.' },
      { lam: 'Học viên nộp; danh sách bài nộp hiện ngay trong bài đó.' },
      {
        lam: 'Chấm điểm và ghi nhận xét.',
        luu_y: 'Nhận xét ở đây là để HỌC VIÊN đọc. Ghi chú riêng về em (dành cho giảng viên và cho tờ báo cáo phụ huynh) nằm ở hồ sơ học viên, chỗ khác.',
      },
    ],
  },

  {
    ma: 'noi-dung',
    tieu_de: 'Soạn khoá học và đề thi thử',
    vai: [VAI_BIEN_TAP, VAI_QUAN_TRI],
    khi_nao: 'Khi thêm bài mới hoặc mở một đề thi thử.',
    buoc: [
      { lam: 'Mở khu Soạn giáo trình.', o: '/admin' },
      {
        lam: 'Đề thi thử nhập từ bảng tính .xlsx theo mẫu có sẵn.',
        luu_y: 'Dùng .xlsx chứ không .csv: Excel bản tiếng Việt lưu CSV theo bảng mã hệ thống, nên "Định lượng" quay về thành ký tự hỏng.',
      },
      {
        lam: 'Xem trước rồi mới xuất bản. Chưa xuất bản thì học viên không thấy.',
      },
    ],
  },

  {
    ma: 'kiem-toan',
    tieu_de: 'Khi cần biết ai đã làm gì',
    vai: [VAI_QUAN_TRI],
    khi_nao: 'Có tranh cãi về một thay đổi, hoặc nghi ngờ thao tác nhầm.',
    buoc: [
      {
        lam: 'Mở "Nhật ký".',
        o: '/quan-tri/nhat-ky',
        luu_y: 'Nhật ký ghi các việc NẶNG: đổi vai trò, đặt lại mật khẩu, khoá tài khoản. Không ghi mọi thao tác.',
      },
      { lam: 'Lọc theo ngày hoặc theo người để thu hẹp.' },
    ],
  },
] as const;

/** Bài nào liên quan tới vai này. Lọc để đọc, KHÔNG phải để chặn. */
export function baiCho(vai: string | undefined): readonly Bai[] {
  if (!vai) return HUONG_DAN;
  const co = HUONG_DAN.filter((b) => b.vai.includes(vai));
  // Vai chưa có bài nào (ví dụ Học viên) thì hiện tất cả còn hơn hiện một
  // trang trống — trang trống trông như hỏng.
  return co.length ? co : HUONG_DAN;
}
