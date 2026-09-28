'use client';

import { useRouter } from 'next/navigation';
import { useId, useRef, useState } from 'react';
import * as z from 'zod/mini';

import { Button } from '@/components/ui';
import { ghiJson, loiBatDuoc } from '@/lib/api';

/* Chỉ đọc lại cờ — phần còn lại của phản hồi `danh-gia` là việc của trang từng em. */
const HD_CO = z.looseObject({ canHoTro: z.boolean() });

/**
 * Đánh dấu / bỏ đánh dấu "cần hỗ trợ" NGAY trên "Việc hôm nay" (kế hoạch v2 V-f).
 *
 * Vì sao ở đây: trợ giảng KHÔNG mở được tờ báo cáo từng em (tờ ấy in liên lạc — cổng
 * `IsSeniorTeachingStaff`), mà bảng TopHSA dòng 21 đòi trợ giảng báo được "em cần hỗ
 * trợ". Dòng em vắng liền / cần chú ý là đúng chỗ họ nhìn thấy dấu hiệu, nên nút nằm
 * ngay trên dòng ấy. Lý do là tuỳ chọn nhưng nên có: giảng viên đọc nó để biết gọi ai.
 * Máy chủ (`teaching/danh_gia.py`) mới là hàng rào; nút này chỉ gửi `canHoTro` + `lyDo`.
 */
export default function NutCanHoTro({ classId, userId, ten, dangDanhDau }: {
  classId: number;
  userId: number;
  ten: string;
  /** Đang được đánh dấu → nút "Bỏ đánh dấu" (một bấm), không mở ô lý do. */
  dangDanhDau: boolean;
}) {
  const router = useRouter();
  const idLyDo = useId();
  const [mo, setMo] = useState(false);
  const [lyDo, setLyDo] = useState('');
  const [dangGui, setDangGui] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);
  const khoa = useRef(false);

  async function gui(co: boolean) {
    if (khoa.current) return;
    khoa.current = true;
    setDangGui(true);
    setLoi(null);
    try {
      await ghiJson(`/api/teach/classes/${classId}/students/${userId}/danh-gia`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(co ? { canHoTro: true, lyDo } : { canHoTro: false }),
      }, HD_CO);
      setMo(false);
      setLyDo('');
      router.refresh();
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Không lưu được'));
    } finally {
      khoa.current = false;
      setDangGui(false);
    }
  }

  if (dangDanhDau) {
    return (
      <span className="inline-flex flex-wrap items-center gap-2">
        <Button size="sm" variant="ghost" loading={dangGui} onClick={() => void gui(false)}
          aria-label={`Bỏ đánh dấu cần hỗ trợ — ${ten}`}>
          Bỏ đánh dấu
        </Button>
        {loi && <span role="alert" className="text-small text-danger-ink">{loi}</span>}
      </span>
    );
  }

  if (!mo) {
    return (
      <Button size="sm" variant="ghost" onClick={() => setMo(true)} aria-label={`Báo cần hỗ trợ — ${ten}`}>
        Báo cần hỗ trợ
      </Button>
    );
  }

  return (
    <form
      className="flex w-full flex-wrap items-end gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        void gui(true);
      }}
    >
      <label htmlFor={idLyDo} className="flex min-w-0 flex-[1_1_14rem] flex-col gap-1">
        <span className="text-label text-ink-3">Lý do (giảng viên sẽ đọc)</span>
        <input
          id={idLyDo}
          value={lyDo}
          onChange={(e) => setLyDo(e.target.value)}
          maxLength={500}
          placeholder="Ví dụ: không vào phòng hai buổi, nhắn không trả lời"
          className="min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink placeholder:text-ink-3/70"
        />
      </label>
      <Button type="submit" size="sm" loading={dangGui}>Đánh dấu</Button>
      <Button type="button" size="sm" variant="ghost" onClick={() => setMo(false)}>Huỷ</Button>
      {loi && <span role="alert" className="basis-full text-small text-danger-ink">{loi}</span>}
    </form>
  );
}
