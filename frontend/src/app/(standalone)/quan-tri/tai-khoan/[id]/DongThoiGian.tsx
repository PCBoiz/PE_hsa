import { Card, CardHead, Chip, EmptyState } from '@/components/ui';

import type { DongThoiGian as DuLieu, MocThoiGian } from './hoSo';

/** Loại mốc → nhãn + tông. Nhãn bằng CHỮ, không chỉ bằng màu (WCAG 1.4.1). */
const LOAI: Record<string, { nhan: string; tong: 'neutral' | 'brand' | 'good' | 'warn' | 'bad' }> = {
  'tai-khoan': { nhan: 'Tài khoản', tong: 'neutral' },
  'khao-sat': { nhan: 'Khảo sát', tong: 'neutral' },
  'khoa-hoc': { nhan: 'Khoá học', tong: 'brand' },
  'lop-hoc': { nhan: 'Lớp học', tong: 'brand' },
  thi: { nhan: 'Thi', tong: 'good' },
  'bao-cao': { nhan: 'Phụ huynh', tong: 'warn' },
  'ho-so': { nhan: 'Hồ sơ', tong: 'neutral' },
  // Giảng viên / trợ giảng đánh dấu cần hỗ trợ, đề xuất hướng học, ghi nhận xét (V-f).
  'theo-doi': { nhan: 'Theo dõi', tong: 'warn' },
  // Điểm bài kiểm tra làm trên lớp, giảng viên nhập (V-h).
  'kiem-tra': { nhan: 'Bài kiểm tra', tong: 'good' },
  // Mốc "Làm bài" trong chuỗi khách yêu cầu (bảng phân rã dòng 4, 26/09/2026):
  // lần em nộp bài tập đầu tiên, kèm tổng số bài đã nộp.
  'bai-tap': { nhan: 'Bài tập', tong: 'brand' },
};

/**
 * Ngày giờ ĐỌC THẲNG từ chuỗi, không qua `Date`: máy chủ trả giờ Việt Nam dạng
 * naive ('2026-08-02T08:00:00'); dựng `Date` trên Vercel (UTC) rồi định dạng lại
 * là để múi giờ của máy dựng trang chen vào con số.
 */
function hienLuc(m: MocThoiGian): string {
  const [ngay, gio = ''] = m.luc.split('T');
  const [y, mo, d] = ngay.split('-');
  const ngayVN = `${d}/${mo}/${y}`;
  return m.caNgay || !gio ? ngayVN : `${ngayVN} ${gio.slice(0, 5)}`;
}

/**
 * Dòng thời gian của một em — CHỈ ĐỌC, dựng sẵn ở máy chủ cùng lượt với hồ sơ.
 * Mốc mới nhất ở trên: người mở trang này thường cần biết "gần đây có chuyện
 * gì", không phải đọc lại từ ngày em nhập học.
 */
export default function DongThoiGian({ duLieu }: { duLieu: DuLieu }) {
  return (
    <div className="mx-auto mt-5 max-w-3xl">
      <Card>
        <CardHead
          title="Dòng thời gian"
          hint="Mọi mốc của em, mới nhất ở trên: vào lớp, chuyển lớp, thi, báo cáo phụ huynh, cần hỗ trợ."
        />
        {duLieu.events.length === 0 ? (
          <EmptyState title="Chưa có mốc nào" hint="Em vừa được cấp tài khoản và chưa vào lớp nào." />
        ) : (
          <ol className="flex flex-col">
            {duLieu.events.map((m, i) => {
              const loai = LOAI[m.loai] ?? { nhan: 'Khác', tong: 'neutral' as const };
              return (
                /* flex-wrap, không lưới hai cột cố định: ở 390px cột ngày 8,5rem
                   chiếm nửa hàng và ép tên sự kiện thành một cột chữ hẹp (soi ảnh
                   23/09/2026). Nay phần chữ cần tối thiểu ~16rem — không đủ chỗ
                   thì ngày tự nằm một dòng riêng phía trên, không cần mốc px nào. */
                <li
                  key={`${m.luc}-${i}`}
                  className="flex flex-wrap items-baseline gap-x-4 gap-y-1 border-t border-line py-3 first:border-t-0"
                >
                  <time dateTime={m.luc} className="shrink-0 basis-[8.5rem] text-small text-ink-3 tabular-nums">
                    {hienLuc(m)}
                  </time>
                  <div className="min-w-0 flex-1 basis-[min(100%,16rem)]">
                    <p className="flex flex-wrap items-center gap-x-2 gap-y-1">
                      <Chip tone={loai.tong}>{loai.nhan}</Chip>
                      <span className="text-body text-ink [overflow-wrap:anywhere]">{m.tieuDe}</span>
                    </p>
                    {m.chiTiet && <p className="mt-1 text-small text-ink-2 [overflow-wrap:anywhere]">{m.chiTiet}</p>}
                    {m.boi && <p className="mt-0.5 text-small text-ink-3">bởi {m.boi}</p>}
                  </div>
                </li>
              );
            })}
          </ol>
        )}
        {duLieu.catBot && (
          <p className="mt-3 text-small text-ink-3">
            Đang hiện {duLieu.events.length} mốc gần nhất trong tổng số {duLieu.tong}.
          </p>
        )}
      </Card>
    </div>
  );
}
