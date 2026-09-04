import { serverJson } from '@/lib/server-api';

import { KhongDocDuoc, KhongDuQuyen } from '../ChanVai';
import { layVai } from '../layVai';
import { VAI_HOC_VU, VAI_QUAN_TRI, duocVao } from '../vai';

import LopHocClient, { type ChonKhoa, type ChonNguoi, type LopRow } from './LopHocClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Lớp học | TopHSA' };

type DsLop = { classes: LopRow[]; teachers: ChonNguoi[]; statuses: string[] };
type DsDot = { terms: { id: number; name: string; code: string | null }[] };
type DsKhoa = { courses: ChonKhoa[] };

/**
 * Quản lý LỚP HỌC — tạo, sửa, xếp học viên vào lớp.
 *
 * ── VÌ SAO TRANG NÀY CÓ MẶT TRỞ LẠI (04/09/2026) ────────────────────────────
 *
 * Nó từng nằm trong `public/static/js/pages/admin.inline.js`, và tôi XOÁ NHẦM
 * cả tệp ấy khi chuyển khu Soạn giáo trình sang React (0af1c26). Tôi có grep
 * cả repo trước khi xoá — nhưng chỉ grep xem có ai THAM CHIẾU tới tệp không,
 * chứ không hỏi tệp ấy CUNG CẤP chức năng gì. Không ai tham chiếu tới nó là
 * đúng: nó là một trang tự chạy. Tám chỗ gọi biến mất theo, và chỗ này là
 * đường DUY NHẤT để xếp một học viên vào lớp — không có nó thì cả khu Giảng
 * dạy không có gì để hiện.
 *
 * ── DỰNG LẠI, KHÔNG CHÉP LẠI ────────────────────────────────────────────────
 *
 * Bản cũ có một lỗi thật, và chép nguyên là chép cả lỗi: biểu mẫu SỬA chỉ đổ
 * 7 trong 11 trường (thiếu `meeting_url`, `starts_on`, `ends_on`, `note`, và
 * giảng viên), rồi `PUT` gửi cả 11 — nên sửa tên lớp là XOÁ TRẮNG link họp và
 * ghi chú của lớp đó. Đúng lớp lỗi vừa vá ở bộ soạn bài học sáng nay: biểu mẫu
 * DỰNG LẠI từ đầu thay vì ĐÈ LÊN bản đã có.
 *
 * Vì thế `class_list` đã được bổ sung năm cột ấy (`teaching/reports.py`), và
 * biểu mẫu ở đây đổ ĐỦ. Có phép kiểm khẳng định điều đó:
 * `e2e/unit/lop-hoc.test.mjs`.
 *
 * ── BA NGUỒN, BA MỨC QUYỀN KHÁC NHAU ────────────────────────────────────────
 *
 * Danh sách khoá lấy từ `/api/public/courses` chứ KHÔNG từ `/api/admin/courses`:
 * đường admin đòi `IsContentEditor`, mà trang này mở cho `Quản lý học vụ` — họ
 * sẽ nhận 403 và ô chọn khoá hiện rỗng, không báo gì. Chọn nguồn theo QUYỀN của
 * người dùng trang, không theo tên nghe cho oai.
 */
export default async function LopHocPage() {
  const kq = await layVai();
  if (!kq.ok) return <KhongDocDuoc loi={kq.loi} />;
  if (!duocVao(kq.vai, [VAI_QUAN_TRI, VAI_HOC_VU])) {
    return <KhongDuQuyen can="quản trị viên và quản lý học vụ" />;
  }

  const [lop, dot, khoa] = await Promise.all([
    serverJson<DsLop>('/api/admin/classes', { requireAuth: true }),
    serverJson<DsDot>('/api/admin/terms', { requireAuth: true }),
    serverJson<DsKhoa>('/api/public/courses'),
  ]);

  return (
    <LopHocClient
      initial={lop.ok ? lop.data.classes : []}
      giangVien={lop.ok ? lop.data.teachers : []}
      trangThai={lop.ok ? lop.data.statuses : ['draft', 'active', 'finished']}
      // Đợt và khoá chỉ là ô CHỌN. Không đọc được thì trang vẫn phải dùng được
      // để tạo lớp — nên không cho hỏng cả trang vì một danh sách phụ.
      dotHoc={dot.ok ? dot.data.terms : []}
      khoaHoc={khoa.ok ? khoa.data.courses : []}
      loi={lop.ok ? null : lop.message}
    />
  );
}
