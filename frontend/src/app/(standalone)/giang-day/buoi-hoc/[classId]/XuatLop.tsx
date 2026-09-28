'use client';

import { useState } from 'react';

import ChonDinhDang, { dinhDangQs, type DinhDang } from '@/components/ChonDinhDang';
import { Button, Field, Modal } from '@/components/ui';

/**
 * "Tải bảng tính" của một lớp — chuyên cần + tiến độ, Excel hoặc CSV (V-k, bảng TopHSA
 * dòng 6). Chuyên cần lọc được theo khoảng ngày của buổi học; tiến độ là ảnh chụp hôm nay
 * nên không có ô ngày.
 *
 * Hai liên kết tải là THẺ NEO thường, không fetch: cookie đăng nhập đi kèm sẵn và trình
 * duyệt lo phần lưu tệp (cùng lối với các nút xuất cũ). Trợ giảng tải được cả hai tệp —
 * máy chủ tự bỏ cột email / số điện thoại cho họ.
 */
const NUT_TAI =
  'inline-flex min-h-11 items-center justify-center rounded-md px-4 text-small font-semibold';

export default function XuatLop({ classId }: { classId: number | string }) {
  const [mo, setMo] = useState(false);
  const [dinhDang, setDinhDang] = useState<DinhDang>('xlsx');
  const [tu, setTu] = useState('');
  const [den, setDen] = useState('');

  const nguoc = !!tu && !!den && tu > den;
  const qsChuyenCan = [dinhDangQs(dinhDang), tu && `tu=${tu}`, den && `den=${den}`]
    .filter(Boolean)
    .join('&');
  const goc = `/api/teach/classes/${classId}/export`;

  return (
    <>
      <Button variant="ghost" onClick={() => setMo(true)}>
        Tải bảng tính
      </Button>
      <Modal open={mo} onClose={() => setMo(false)} title="Tải bảng tính của lớp">
        <div className="flex flex-col gap-4">
          <ChonDinhDang value={dinhDang} onChange={setDinhDang} ten={`dinh-dang-lop-${classId}`} />
          <fieldset className="flex flex-col gap-2">
            <legend className="mb-1 text-label text-ink-3">Chuyên cần: chỉ các buổi trong khoảng (để trống = mọi buổi)</legend>
            <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,11rem),1fr))]">
              <Field id={`xuat-tu-${classId}`} label="Từ ngày" type="date" value={tu} max={den || undefined}
                onChange={(e) => setTu(e.target.value)} />
              <Field id={`xuat-den-${classId}`} label="Đến ngày" type="date" value={den} min={tu || undefined}
                onChange={(e) => setDen(e.target.value)}
                error={nguoc ? '"Đến ngày" phải sau hoặc bằng "Từ ngày".' : null} />
            </div>
          </fieldset>
          <div className="flex flex-wrap gap-2">
            <a
              href={nguoc ? undefined : `${goc}/attendance.csv?${qsChuyenCan}`}
              aria-disabled={nguoc || undefined}
              className={`${NUT_TAI} bg-brand-fill text-white hover:brightness-110 aria-disabled:opacity-50`}
            >
              Tải chuyên cần
            </a>
            <a
              href={`${goc}/progress.csv?${dinhDangQs(dinhDang)}`}
              className={`${NUT_TAI} border border-line text-ink-2 hover:border-brand hover:text-brand-ink`}
            >
              Tải tiến độ
            </a>
          </div>
        </div>
      </Modal>
    </>
  );
}
