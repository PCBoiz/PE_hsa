import { Chip } from '@/components/ui';
import { lucVN } from '@/lib/gioVN';
import { cauSuKien, nhanVaiNguoi, type SuKien } from '@/lib/yeuCau';

/**
 * LỊCH SỬ một yêu cầu — trả lời và mọi lần đổi trạng thái / giao / duyệt, cũ trước mới sau
 * (bảng TopHSA dòng 11 "lưu lịch sử", dòng 20 "lịch sử trao đổi").
 *
 * Dùng chung cho học viên, nhân sự và phụ huynh: máy chủ đã lọc sẵn ghi chú nội bộ theo vai
 * (`su_kien_cua`), nên dòng nào tới đây là người xem được đọc. Ghi chú nội bộ (chỉ nhân sự
 * nhận) tô khác màu kèm chip "Nội bộ" — gõ nhầm vào ô nội bộ thì phải nhìn ra ngay.
 */
export default function YeuCauDongThoiGian({ suKien }: { suKien: SuKien[] }) {
  if (suKien.length === 0) {
    return <p className="text-body text-ink-3">Chưa có gì.</p>;
  }
  return (
    <ol className="flex flex-col gap-3" aria-label="Lịch sử yêu cầu">
      {suKien.map((s) => {
        const vai = nhanVaiNguoi(s.ai.vai);
        const loi = s.kieu === 'tra_loi' || s.kieu === 'ghi_chu' || s.kieu === 'tao';
        return (
          <li
            key={s.id}
            className={[
              'rounded-md border px-3 py-2',
              s.noiBo ? 'border-warning/40 bg-warning/10' : loi ? 'border-line bg-surface' : 'border-transparent bg-sunken',
            ].join(' ')}
          >
            <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-small">
              <span className="font-semibold text-ink">{s.ai.ten || 'Hệ thống'}</span>
              {vai && vai !== s.ai.ten && <span className="text-ink-3">{vai}</span>}
              <span className="text-ink-2">· {cauSuKien(s)}</span>
              {s.noiBo && <Chip tone="warn">Nội bộ</Chip>}
              <time className="ml-auto font-mono tabular-nums text-ink-3" dateTime={s.luc ?? undefined}>
                {lucVN(s.luc)}
              </time>
            </div>
            {s.noiDung && (
              // Xuống dòng của người viết phải giữ nguyên — gộp lại là đọc một lời khác.
              <p className="mt-1 whitespace-pre-wrap break-words text-body text-ink">{s.noiDung}</p>
            )}
          </li>
        );
      })}
    </ol>
  );
}
