import { Card, CardHead } from '@/components/ui';

/**
 * Bảng cơ sở tính, một khối cho mỗi lớp.
 *
 * ── HAI CỘT ĐẾM, KHÔNG CHỌN HỘ MỘT CỘT ────────────────────────────────────
 *
 * "Em ấy học mấy buổi" có hai câu trả lời khác nhau và chúng lệch nhau thật:
 *
 *   · Buổi trong kỳ — số buổi lớp đã mở TRONG QUÃNG em còn là thành viên.
 *                     Con số của cách thu theo THỜI GIAN.
 *   · Có mặt        — số buổi em thật sự tới. Con số của cách thu theo BUỔI.
 *
 * Hiện cả hai. Gộp lại thành một cột "số buổi" là ngầm quyết định chính sách
 * thu tiền của một trung tâm mình không điều hành.
 *
 * ── CỘT "LỆCH GHI DANH" LÀ CỘT ĐÁNG NHÌN NHẤT ────────────────────────────
 *
 * Đếm lượt điểm danh vào buổi diễn ra NGOÀI quãng em là thành viên. Mỗi lượt
 * như thế là một trong hai chuyện, và hai chuyện ấy ra tiền ngược nhau:
 * buổi học thử trước khi ghi danh (thường không thu), hay ngày ghi danh nhập
 * sai (phải thu, và ngày vào lớp đang sai). Máy không phân biệt được; người
 * nhìn thì phân biệt ngay. Nên nó là một CỘT, không bị nuốt vào tổng.
 *
 * ── IN RA GIẤY LÀ MỘT YÊU CẦU ────────────────────────────────────────────
 *
 * Người tính học phí hôm nay làm bằng Excel và bằng giấy. Bảng phải in được:
 * không nền tối, không cắt cột.
 */

export type HocVien = {
  userId: number;
  ten: string;
  email: string;
  vaoLop: string | null;
  roiLop: string | null;
  lyDoRoi: string | null;
  buoiTrongKy: number;
  coMat: number;
  muon: number;
  vang: number;
  lechGhiDanh: number;
};

export type Lop = {
  id: number;
  ma: string | null;
  ten: string;
  trangThai: string | null;
  dot: string | null;
  giangVien: string | null;
  buoiDaMo: number;
  buoiDaHuy: number;
  hocVien: HocVien[];
};

const ngay = (s: string | null) => (s ? new Date(s).toLocaleDateString('vi-VN') : '—');

export default function BangCoSo({ lop }: { lop: Lop[] }) {
  const tongLech = lop.reduce(
    (s, l) => s + l.hocVien.reduce((t, e) => t + e.lechGhiDanh, 0), 0,
  );

  return (
    <>
      {tongLech > 0 && (
        <Card>
          <CardHead title="Cần người xem lại trước khi tính tiền" />
          <p className="text-body text-ink-2">
            Có <strong>{tongLech}</strong> lượt điểm danh nằm ngoài quãng ghi danh
            (trước ngày vào lớp, hoặc sau ngày rời lớp). Mỗi lượt là một trong hai
            chuyện, và hai chuyện ra tiền ngược nhau:
          </p>
          <ul className="mt-2 flex list-disc flex-col gap-1 pl-5 text-body text-ink-2">
            <li>Buổi <strong>học thử</strong> trước khi ghi danh — thường không thu.</li>
            <li>
              Ngày ghi danh <strong>nhập sai</strong> — phải thu, và ngày vào lớp
              trong hệ thống đang sai nên cột &ldquo;buổi trong kỳ&rdquo; cũng sai theo.
            </li>
          </ul>
        </Card>
      )}

      {lop.map((l) => (
        <Card key={l.id}>
          <CardHead
            title={l.ten}
            hint={[
              l.dot ? `Đợt ${l.dot}` : 'Chưa thuộc đợt nào',
              l.giangVien ? `GV ${l.giangVien}` : null,
              `${l.buoiDaMo} buổi đã mở`,
              l.buoiDaHuy > 0 ? `${l.buoiDaHuy} buổi đã huỷ (không tính)` : null,
              `${l.hocVien.length} học viên`,
            ].filter(Boolean).join(' · ')}
          />

          {/* Khổ hẹp: mỗi em một THẺ. Bảng bảy cột trên màn 390px không đọc
              được kể cả khi không tràn — cùng lối đã dùng ở bảng quyền. */}
          <ul className="flex flex-col gap-2 sm:hidden">
            {l.hocVien.map((e) => (
              <li key={e.userId} className="rounded-md border border-line bg-surface px-3 py-2">
                <p className="text-body font-semibold text-ink">{e.ten}</p>
                <p className="mt-0.5 text-small text-ink-2">
                  Vào {ngay(e.vaoLop)}{e.roiLop ? ` · rời ${ngay(e.roiLop)}` : ''}
                  {e.lyDoRoi ? ` (${e.lyDoRoi})` : ''}
                </p>
                <p className="mt-1 text-small text-ink">
                  {e.buoiTrongKy} buổi trong kỳ · có mặt {e.coMat} · vắng {e.vang}
                </p>
                {e.lechGhiDanh > 0 && (
                  <p className="mt-1 text-small text-warning-ink">
                    {e.lechGhiDanh} lượt điểm danh ngoài quãng ghi danh
                  </p>
                )}
              </li>
            ))}
          </ul>

          <div className="hidden overflow-x-auto overflow-y-hidden rounded-md border border-line bg-surface sm:block">
            <table className="w-full border-collapse text-small">
              <caption className="sr-only">
                {`Cơ sở tính học phí của lớp ${l.ten}`}
              </caption>
              <thead>
                <tr className="bg-sunken text-label text-ink-3">
                  <th scope="col" className="border-b border-line px-3 py-2 text-left">Học viên</th>
                  <th scope="col" className="border-b border-line px-3 py-2 text-left">Vào lớp</th>
                  <th scope="col" className="border-b border-line px-3 py-2 text-left">Rời lớp</th>
                  {/* `tabular-nums` cho mọi cột số: không có nó thì các chữ số
                      rộng khác nhau và mắt không dóng được cột khi đối chiếu. */}
                  <th scope="col" className="border-b border-line px-3 py-2 text-right">Buổi trong kỳ</th>
                  <th scope="col" className="border-b border-line px-3 py-2 text-right">Có mặt</th>
                  <th scope="col" className="border-b border-line px-3 py-2 text-right">Muộn</th>
                  <th scope="col" className="border-b border-line px-3 py-2 text-right">Vắng</th>
                  <th scope="col" className="border-b border-line px-3 py-2 text-right">Lệch ghi danh</th>
                </tr>
              </thead>
              <tbody>
                {l.hocVien.map((e) => (
                  <tr key={e.userId}>
                    <td className="border-b border-line/50 px-3 py-2 text-ink">{e.ten}</td>
                    <td className="border-b border-line/50 px-3 py-2 text-ink-2">{ngay(e.vaoLop)}</td>
                    <td className="border-b border-line/50 px-3 py-2 text-ink-2">
                      {ngay(e.roiLop)}
                      {e.lyDoRoi && <span className="block text-ink-3">{e.lyDoRoi}</span>}
                    </td>
                    <td className="border-b border-line/50 px-3 py-2 text-right tabular-nums text-ink">{e.buoiTrongKy}</td>
                    <td className="border-b border-line/50 px-3 py-2 text-right tabular-nums text-ink">{e.coMat}</td>
                    <td className="border-b border-line/50 px-3 py-2 text-right tabular-nums text-ink-2">{e.muon}</td>
                    <td className="border-b border-line/50 px-3 py-2 text-right tabular-nums text-ink-2">{e.vang}</td>
                    <td
                      className={
                        'border-b border-line/50 px-3 py-2 text-right tabular-nums '
                        + (e.lechGhiDanh > 0 ? 'text-warning-ink' : 'text-ink-3')
                      }
                    >
                      {e.lechGhiDanh}
                      {/* Số 0 im lặng là đúng; số khác 0 cần một câu cho trình
                          đọc màn hình, vì màu cam không tới được họ. */}
                      {e.lechGhiDanh > 0 && (
                        <span className="sr-only"> lượt cần xem lại</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ))}
    </>
  );
}
