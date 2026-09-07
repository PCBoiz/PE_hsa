import { ToBaoCao, type BaoCao } from '@/components/ToBaoCao';

/**
 * "Phụ huynh nhận được gì" — render CHÍNH tờ báo cáo thật, không phải ảnh chụp.
 *
 * ── VÌ SAO KHỐI NÀY LÀ KHỐI QUAN TRỌNG NHẤT TRANG (07/09/2026) ────────────
 *
 * Anh Sơn: "landing trông chán ngắt, trừ nút đăng nhập ra thì cả đoạn kia vô
 * nghĩa". Đúng — trang cũ toàn câu mô tả: "lộ trình cá nhân hoá", "bám sát đề
 * thi", "phân tích điểm mạnh yếu". Mọi trung tâm luyện thi đều viết y hệt, nên
 * chúng không phân biệt được gì và người đọc lướt qua.
 *
 * Anh chốt: chưa có ảnh lớp học, chưa có kết quả khoá trước, chưa chốt học phí
 * — **dùng chính SẢN PHẨM làm bằng chứng**.
 *
 * Thứ TopHSA có mà phần lớn trung tâm không có là tờ báo cáo này: mỗi kỳ, phụ
 * huynh nhận qua Zalo một trang nói con đi học mấy buổi, làm xong mấy bài, thi
 * thử được bao nhiêu, và đang yếu chủ đề nào. Đó là câu trả lời cho câu hỏi mà
 * phụ huynh thật sự hỏi — "con tôi học có ổn không" — và nó cụ thể tới mức
 * không copy bằng lời quảng cáo được.
 *
 * ── VÌ SAO RENDER COMPONENT THẬT, KHÔNG DÙNG ẢNH ─────────────────────────
 *
 * `ToBaoCao` là component thuần trình bày, và đây ĐÚNG là component mà phụ
 * huynh sẽ mở từ tin Zalo (`/bc/<chìa>`) và giảng viên sẽ in ra. Nên khối này
 * không phải bản vẽ lại — nó là chính thứ ấy, cùng một dòng mã.
 *
 * Ảnh chụp thì: nặng, mờ trên màn hình nét cao, không đổi theo bộ sáng/tối,
 * không đọc được bằng trình đọc màn hình, và CŨ ĐI mà không ai biết. Component
 * thật thì đổi cùng sản phẩm — nếu ai sửa tờ báo cáo, trang giới thiệu tự đúng
 * theo.
 *
 * ── SỐ LIỆU LÀ MẪU, VÀ PHẢI NÓI RA ──────────────────────────────────────
 *
 * Không học viên thật nào lên trang công khai. Số dưới đây là của một em không
 * có thật, và khối này nói thẳng điều đó ngay cạnh tờ giấy. Đưa số của một em
 * thật lên đây là chuyện khác hẳn — kể cả khi che tên.
 *
 * Số cũng KHÔNG được chọn cho đẹp: em mẫu vắng một buổi, có một buổi giảng viên
 * quên tick, và đang yếu hai chủ đề. Một tờ báo cáo toàn màu xanh là tờ báo cáo
 * không ai tin, và nó cũng không giống thứ phụ huynh sẽ nhận.
 */

/** Kỳ mẫu: bốn tuần gần nhất, đúng mặc định của `ParentReportView`. */
const MAU: BaoCao = {
  student: { id: 0, name: 'Nguyễn Minh An' },
  parent: { name: 'Nguyễn Thị Hà' },
  class: {
    id: 0,
    name: 'Luyện HSA đợt 1/2027 — Ca tối',
    code: 'HSA-01',
    teacher: 'Thầy Hà Thái Sơn',
  },
  membership: {
    joinedAt: '2026-08-10',
    leftAt: null,
    // Nhãn TIẾNG VIỆT, đúng thứ backend gửi: `teaching/vocab.py::trang_thai()`
    // trả 'Đang học' / 'Đã rời lớp — …'. Bản đầu tôi để mã thô 'active' và tờ
    // giấy in ra "· active" — một mã enum tiếng Anh giữa lá thư gửi phụ huynh.
    // Kiểm rồi mới biết sản phẩm KHÔNG sai, chỉ dữ liệu mẫu của tôi sai.
    status: 'Đang học',
    teacherNote: 'Định lượng tiến bộ rõ. Định tính cần đọc thêm mỗi ngày 20 phút.',
  },
  period: { from: '2026-08-10', to: '2026-09-07', weeks: 4 },
  attendance: {
    // Cộng phải ĐÚNG: 6 có mặt + 1 muộn + 1 vắng = 8 buổi đã điểm danh, cộng
    // 1 buổi giảng viên chưa tick = 9 buổi đã mở. Bản đầu để `sessionsCounted:
    // 7` và tờ giấy hiện "Có mặt 7/7" ngay cạnh "Vắng 1" — tự mâu thuẫn, và
    // trên một trang dựng để tạo lòng tin thì đó là lỗi đắt nhất có thể mắc.
    sessionsTotal: 9,
    sessionsCounted: 8,
    // Có thật trong sản phẩm: buổi cả lớp đã tick mà em không có dòng nào.
    // Giữ nó ở đây vì tờ báo cáo thật sẽ hiện, và phụ huynh nên thấy trước.
    sessionsUnmarked: 1,
    present: 6,
    late: 1,
    absent: 1,
    excused: 0,
    noRecord: 0,
    attendedPct: 88,
  },
  study: {
    lessonsDone: 19,
    mockCount: 3,
    mockAvg: 82,
    mockBest: 91,
    mockTrend: 'up',
  },
  topics: {
    weak: [
      { course: 'hsa_verbal', courseTitle: 'Tư duy Định tính', topic: 'Đọc hiểu', mastery: 34 },
      { course: 'hsa_science', courseTitle: 'Khoa học & Tiếng Anh', topic: 'Ngữ pháp', mastery: 41 },
    ],
    strong: [
      { course: 'hsa_quantitative', courseTitle: 'Tư duy Định lượng', topic: 'Hàm số', mastery: 88 },
      { course: 'hsa_quantitative', courseTitle: 'Tư duy Định lượng', topic: 'Xử lý số liệu', mastery: 81 },
    ],
    measured: 9,
    total: 19,
    courses: [
      { id: 'hsa_quantitative', title: 'Tư duy Định lượng', lessonsDone: 11, lessonsTotal: 27, pct: 41 },
      { id: 'hsa_verbal', title: 'Tư duy Định tính', lessonsDone: 5, lessonsTotal: 23, pct: 22 },
      { id: 'hsa_science', title: 'Khoa học & Tiếng Anh', lessonsDone: 3, lessonsTotal: 26, pct: 12 },
    ],
  },
  warnings: [],
};

export default function PhuHuynhNhanGi() {
  return (
    <section className="landing-section reveal-on-scroll" id="phu-huynh">
      <div className="section-container">
        <h2 className="section-heading neon-text-sm">Mỗi kỳ, phụ huynh nhận đúng tờ này</h2>
        <p className="section-sub">
          Không phải một tin nhắn &ldquo;cháu học tốt&rdquo;. Đây là bản đầy đủ, gửi
          qua Zalo, mở được trên điện thoại mà không cần cài gì hay đăng nhập.
        </p>

        {/* Ba câu TRẢ LỜI CHO CÂU HỎI THẬT của phụ huynh, đặt ngay trên tờ giấy
            để người lướt nhanh vẫn hiểu mình đang nhìn cái gì. */}
        <ul className="ph-y-nghia">
          <li><strong>Con đi học đều không?</strong> Từng buổi, có mặt hay vắng, muộn mấy buổi.</li>
          <li><strong>Con học tới đâu?</strong> Bao nhiêu bài đã xong trên tổng số, theo từng hợp phần.</li>
          <li><strong>Con yếu chỗ nào?</strong> Chủ đề cụ thể, không phải nhận xét chung chung.</li>
        </ul>

        {/* Nói TRƯỚC khi người ta kịp hiểu nhầm. Đặt nhãn sau tờ giấy thì đã
            muộn — mắt đọc số trước khi đọc chú thích. */}
        <p className="ph-nhan-mau" role="note">
          Số liệu dưới đây là <strong>của một học viên không có thật</strong>. Chúng
          tôi không đưa dữ liệu của học viên thật lên trang công khai, kể cả khi đã
          che tên.
        </p>

        <div className="ph-khung-giay">
          {/* Chính component tờ báo cáo thật — cùng dòng mã với thứ phụ huynh
              mở từ Zalo và giảng viên in ra giấy. Không phải ảnh chụp. */}
          <ToBaoCao bc={MAU} />
        </div>

        <p className="stat-note">
          Tờ này do giảng viên phụ trách lớp bấm gửi, không phải máy tự bắn đi. Đường
          dẫn có hạn dùng và thu hồi được nếu gửi nhầm.
        </p>
      </div>
    </section>
  );
}
