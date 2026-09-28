/**
 * Chọn định dạng tệp tải về: Excel (.xlsx) hay CSV — dùng chung cho mọi hộp "Tải bảng tính".
 *
 * Excel đứng TRƯỚC và là mặc định (bảng TopHSA dòng 6 đòi "Xuất Excel"): mở ra đúng dấu
 * tiếng Việt, số là số, ngày là ngày. CSV giữ lại cho ai cần đưa sang phần mềm khác.
 * Máy chủ đọc `?dinh_dang=` — `dinhDangQs` dựng đúng tham số ấy.
 */
export type DinhDang = 'xlsx' | 'csv';

export const NHAN_DINH_DANG: Record<DinhDang, string> = {
  xlsx: 'Excel (.xlsx)',
  csv: 'CSV — mở được bằng mọi phần mềm bảng tính',
};

export function dinhDangQs(dd: DinhDang): string {
  return `dinh_dang=${dd}`;
}

export default function ChonDinhDang({
  value,
  onChange,
  ten,
}: {
  value: DinhDang;
  onChange: (v: DinhDang) => void;
  /** `name` của nhóm radio — duy nhất trong trang. */
  ten: string;
}) {
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-1 text-label text-ink-3">Định dạng tệp</legend>
      {(Object.keys(NHAN_DINH_DANG) as DinhDang[]).map((dd) => (
        <label key={dd} className="flex min-h-11 items-center gap-3 text-body text-ink">
          <input
            type="radio"
            name={ten}
            value={dd}
            checked={value === dd}
            onChange={() => onChange(dd)}
            className="size-5 accent-brand-fill"
          />
          {NHAN_DINH_DANG[dd]}
        </label>
      ))}
    </fieldset>
  );
}
