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
    ma: 'viec-hom-nay',
    tieu_de: 'Mở đầu ngày dạy',
    vai: [VAI_GIANG_VIEN, VAI_TRO_GIANG, VAI_HOC_VU, VAI_QUAN_TRI],
    khi_nao: 'Mỗi ngày có buổi dạy, trước khi lên lớp.',
    buoc: [
      {
        lam: 'Mở "Việc hôm nay". Năm ô đếm ở trên trả lời năm câu: sắp có buổi nào, buổi nào chưa điểm danh, bài nào chưa chấm, em nào vắng liền từ 2 buổi, em nào cần chú ý ngay.',
        o: '/giang-day',
        luu_y: 'Ô nào khác 0 là có việc. Đây là danh sách việc còn tồn, không phải bảng thống kê.',
      },
      {
        lam: 'Bấm thẳng vào dòng việc bên dưới — nó dẫn tới đúng lớp và đúng buổi, không phải tự đi tìm.',
      },
      {
        lam: 'Làm hết phần "Chưa điểm danh xong" trước khi về.',
        luu_y: 'Buổi chưa tick thì KHÔNG tính vào chuyên cần của em, và tờ gửi phụ huynh sẽ báo thiếu. Đây là lỗi hay gặp nhất và khó thấy nhất.',
      },
    ],
    hong_thi_sao: [
      {
        trieu_chung: 'Không thấy lớp nào của mình.',
        xu_ly: 'Giảng viên: lớp phải được PHÂN CÔNG cho bạn. Trợ giảng: bạn phải được XẾP VÀO lớp. Cả hai đều là việc của quản lý học vụ — nhắn họ kiểm tra.',
      },
      {
        trieu_chung: 'Danh sách việc trống trơn.',
        xu_ly: 'Hết việc tồn, không phải trang chưa tải xong. Ngày không có buổi dạy thì trang này trống là đúng.',
      },
    ],
  },

  {
    ma: 'tai-khoan-moi',
    tieu_de: 'Cấp tài khoản cho người mới',
    // Học vụ từ 23/09/2026 — nhưng chỉ cấp được tài khoản HỌC VIÊN.
    vai: [VAI_QUAN_TRI, VAI_HOC_VU],
    khi_nao: 'Có học viên mới nhập học, hoặc trung tâm tuyển thêm giảng viên.',
    buoc: [
      {
        lam: 'Mở "Tài khoản".',
        o: '/quan-tri/tai-khoan',
        luu_y: 'Từ 27/08/2026 người dùng KHÔNG tự đăng ký được. Mọi tài khoản do trung tâm cấp. Học vụ chỉ thấy và cấp được tài khoản học viên; giảng viên, trợ giảng do quản trị viên cấp.',
      },
      {
        // KHÔNG có form cấp lẻ (đo 23/09/2026: không màn hình nào gọi đường
        // cấp lẻ) — bản trước viết "một người thì điền form".
        lam: 'Bấm "Mở ô nhập" ở khối "Cấp tài khoản hàng loạt", dán danh sách: mỗi dòng một người — họ tên, email, số điện thoại. Một người thì dán một dòng.',
        luu_y: 'Bấm "Kiểm tra trước" rồi mới bấm tạo. Danh sách trùng mà tạo luôn là hai tài khoản cho một người.',
      },
      {
        lam: 'Quản trị viên: chọn vai cho cả danh sách. Không chắc chọn vai nào thì mở bảng "Ai làm được gì". Học vụ: ô này chỉ có Học viên.',
        o: '/quan-tri/vai-tro',
        luu_y: 'Cấp vai rộng hơn mức cần là mở dữ liệu của học viên cho thêm một người. Vai mặc định là Học viên — cứ để vậy nếu chưa chắc.',
      },
      {
        lam: 'Chép bảng mật khẩu tạm ngay, rồi báo cho từng người. Lần đăng nhập đầu hệ thống bắt đổi mật khẩu trước khi vào được bất cứ đâu.',
        luu_y: 'Mỗi học viên có mã HSA-xxxxx ngay khi tạo — hiện dưới tên em trong danh sách. Mã này không đổi được.',
      },
    ],
    hong_thi_sao: [
      {
        trieu_chung: 'Báo "Email đã được sử dụng" nhưng tìm không thấy ai.',
        xu_ly: 'Tài khoản có thể đang bị KHOÁ nên không hiện ở danh sách mặc định. Bỏ bộ lọc trạng thái rồi tìm lại.',
      },
      {
        trieu_chung: 'Em quên mật khẩu.',
        xu_ly: 'Tài khoản → tìm em → "Đặt lại mật khẩu" (học vụ: được với học viên; ở Lớp học → Học viên cũng có nút "Đặt lại", được cả với trợ giảng). Giảng viên, học vụ khác thì cần quản trị viên. Đọc chuỗi tạm cho em — hiện đúng một lần.',
      },
      {
        trieu_chung: 'Em không nhớ đã đăng ký bằng email nào.',
        xu_ly: 'Mở Hồ sơ của em, đặt "Tên đăng nhập" (ví dụ an.nguyen08) rồi đặt lại mật khẩu. Em đăng nhập bằng tên ấy, gõ hoa hay thường đều được.',
      },
    ],
  },

  {
    ma: 'ho-so-hoc-vien',
    tieu_de: 'Cập nhật hồ sơ học viên',
    vai: [VAI_QUAN_TRI, VAI_HOC_VU],
    khi_nao: 'Khi tư vấn xong một em, khi em đổi trường hay đổi mục tiêu, hoặc khi phụ huynh báo số liên lạc mới.',
    buoc: [
      {
        lam: 'Mở "Tài khoản" và tìm em — gõ tên, email, số điện thoại, mã học viên (HSA-…) hoặc tên đăng nhập đều được.',
        o: '/quan-tri/tai-khoan',
      },
      {
        lam: 'Bấm "Hồ sơ" trên dòng của em. Trang hồ sơ có năm mục: thông tin cá nhân, tên đăng nhập, học tập, tuyển sinh, phụ huynh.',
      },
      {
        lam: 'Sửa ô cần sửa rồi bấm "Lưu hồ sơ" ở thanh dưới cùng. Thanh ấy đếm số ô chưa lưu; ô nào sai thì báo ngay dưới ô đó.',
        luu_y: 'Người tư vấn và nguồn tuyển sinh chọn từ danh sách, không gõ tay — để còn thống kê được.',
      },
      {
        lam: 'Liên hệ phụ huynh lưu ở đây là "trung tâm đã nhập": từ đó em chỉ còn điền được ô trống trong Cài đặt, muốn sửa phải qua học vụ.',
        luu_y: 'Mã học viên không ai sửa được. Email và số điện thoại là thông tin đăng nhập — em tự đổi trong Cài đặt.',
      },
    ],
    hong_thi_sao: [
      {
        trieu_chung: 'Báo "Tên đăng nhập này đã có người dùng."',
        xu_ly: 'Chọn tên khác — thêm năm sinh hoặc một con số, ví dụ an.nguyen08.',
      },
      {
        trieu_chung: 'Không thấy người tư vấn trong danh sách chọn.',
        xu_ly: 'Danh sách chỉ có tài khoản nhân sự đang hoạt động. Người đã bị khoá vẫn hiện trên hồ sơ cũ, kèm chữ "(đã nghỉ)".',
      },
      {
        trieu_chung: 'Học vụ bấm Hồ sơ của một giảng viên thì bị chặn.',
        xu_ly: 'Đúng thiết kế: học vụ chỉ xem và sửa hồ sơ HỌC VIÊN. Hồ sơ nhân sự do quản trị viên sửa.',
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
        lam: 'Mở "Việc hôm nay" trong khu Giảng dạy. Buổi vừa dạy mà chưa mở sổ nằm ngay đó, kèm nút "Điểm danh" dẫn thẳng vào buổi ấy.',
        o: '/giang-day',
        luu_y: 'Giảng viên chỉ thấy lớp mình phụ trách; trợ giảng chỉ thấy lớp được gán. Trang này gom MỌI lớp — không phải mở từng lớp.',
      },
      { lam: 'Tick từng em (hoặc "Đánh dấu cả lớp có mặt" rồi sửa em vắng), bấm lưu.' },
      {
        lam: 'Buổi chưa có trong danh sách thì tạo buổi trước — hoặc "Sinh lịch cả kỳ" một lần cho cả đợt (xem bài "Sinh lịch cả kỳ").',
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
    ma: 'sinh-lich',
    tieu_de: 'Sinh lịch cả kỳ và khai ngày nghỉ',
    vai: [VAI_HOC_VU, VAI_GIANG_VIEN, VAI_QUAN_TRI],
    khi_nao: 'Đầu mỗi đợt, sau khi lớp đã có lịch học (thứ trong tuần và giờ).',
    buoc: [
      {
        lam: 'Học vụ khai ngày nghỉ của ĐỢT trước: mở Đợt học, bấm "Ngày nghỉ". Hệ thống gợi ý lễ dương lịch cố định; Tết, Giỗ Tổ và ngày nghỉ bù thì nhập theo thông báo chính thức của năm đó.',
        o: '/quan-tri/dot-hoc',
        luu_y: 'Hệ thống KHÔNG tự tính Tết — đoán sai một ngày là cả lớp vào phòng học trống. Ngày nghỉ lưu theo đợt, nên khai một lần là mọi lớp của đợt cùng bỏ.',
      },
      {
        lam: 'Vào lớp → trang Buổi học → "Sinh lịch cả kỳ". Thứ, giờ, khoảng ngày đã điền sẵn theo lịch lớp — kiểm tra rồi bấm "Xem trước".',
        luu_y: 'Bảng xem trước nói rõ ngày nào tạo, ngày nào nghỉ, ngày nào đã có buổi. Chỉ bấm "Tạo" sau khi đọc bảng ấy.',
      },
      {
        lam: 'Bấm lại lần nữa không tạo buổi trùng — ngày đã có buổi được giữ nguyên. Sửa ngày kết thúc rồi sinh thêm là cách nối dài lịch.',
      },
    ],
    hong_thi_sao: [
      {
        trieu_chung: 'Trong bảng xem trước có dòng cảnh báo "là Quốc khánh nhưng đợt chưa khai nghỉ".',
        xu_ly: 'Lớp vẫn học ngày lễ thì cứ tạo. Nghỉ thì học vụ khai ngày ấy ở Đợt học rồi bấm "Xem trước" lại.',
      },
      {
        trieu_chung: 'Trợ giảng không thấy nút "Sinh lịch cả kỳ".',
        xu_ly: 'Đúng thiết kế: trợ giảng tạo từng buổi được, sinh cả kỳ thì không. Nhờ giảng viên phụ trách hoặc học vụ.',
      },
    ],
  },

  {
    ma: 'muc-tieu-hoc-vien',
    tieu_de: 'Ghi mục tiêu và nguyện vọng của em',
    // Dòng 14 của bảng yêu cầu TopHSA. Học vụ, quản trị viên sửa ở trang Hồ sơ
    // (bài "Cập nhật hồ sơ học viên"); trợ giảng không sửa.
    vai: [VAI_GIANG_VIEN],
    khi_nao: 'Sau buổi tư vấn hay buổi nói chuyện riêng với em, hoặc khi em đổi mục tiêu điểm hay đổi trường muốn vào.',
    buoc: [
      {
        lam: 'Vào lớp của em, bấm "Báo cáo phụ huynh", rồi "Xem tờ" trên dòng của em.',
        o: '/giang-day',
      },
      {
        lam: 'Khối "Mục tiêu và nguyện vọng" nằm ngay trên tờ báo cáo. Sửa hai ô rồi bấm "Lưu".',
        luu_y: 'Đây là ghi chú NỘI BỘ: không in ra, không gửi phụ huynh. Học vụ thấy ngay trên hồ sơ của em.',
      },
    ],
    hong_thi_sao: [
      {
        trieu_chung: 'Không thấy khối "Mục tiêu và nguyện vọng".',
        xu_ly: 'Khối chỉ hiện với em ĐANG học lớp ấy. Em đã rời lớp thì nhờ học vụ sửa trên hồ sơ.',
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
        lam: 'Em nào thiếu email hoặc số Zalo của phụ huynh: dán cả bảng đăng ký (kèm dòng tiêu đề) vào "Nhập liên hệ phụ huynh" ngay trên trang này → "Kiểm tra trước" → "Lưu". Hoặc để em tự điền ở Cài đặt → Liên hệ phụ huynh.',
        luu_y: 'Trung tâm đã nhập thì học viên KHÔNG sửa được ô ấy nữa (chỉ điền được ô còn trống) — để không em nào đổi được địa chỉ nhận báo cáo về chính mình. Cần sửa thì học vụ dán lại.',
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
