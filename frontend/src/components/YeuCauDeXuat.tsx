'use client';

import Link from 'next/link';
import { useRef, useState } from 'react';

import { Button } from '@/components/ui';
import { ghiJson, loiBatDuoc } from '@/lib/api';
import { lucVN } from '@/lib/gioVN';
import { HD_YEU_CAU } from '@/lib/yeuCau';

/**
 * Ô "Đề xuất" của sổ đầu bài → MỘT yêu cầu "Báo lên" gửi học vụ (bảng TopHSA dòng 16 "đề xuất
 * học bù / điều chỉnh tiến độ"; kế hoạch v2 E1 phần sót). Đề xuất trong sổ vẫn là chữ tự do của
 * buổi; nút này đưa nó vào hộp Yêu cầu để học vụ nhận, giao, trả lời và có lịch sử.
 *
 * Gắn buổi (`session_id`) — máy chủ tự suy lớp và kiểm người gửi dạy lớp ấy (`dich_vu.tao`).
 */
export default function YeuCauDeXuat({
  sessionId, startsAt, deXuat,
}: { sessionId: number; startsAt: string | null; deXuat: string }) {
  const [daGui, setDaGui] = useState<number | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const dangGui = useRef(false);
  const chu = deXuat.trim();

  async function gui() {
    if (dangGui.current || !chu) return;
    dangGui.current = true;
    setBusy(true);
    setErr(null);
    try {
      const y = await ghiJson('/api/teach/yeu-cau', {
        method: 'POST',
        body: JSON.stringify({
          loai: 'bao_cao_len',
          session_id: sessionId,
          tieu_de: `Đề xuất sau buổi ${lucVN(startsAt)}: ${chu.slice(0, 120)}`.slice(0, 200),
          noi_dung: chu,
        }),
      }, HD_YEU_CAU);
      setDaGui(y.id);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không gửi được đề xuất.'));
    } finally {
      dangGui.current = false;
      setBusy(false);
    }
  }

  if (daGui) {
    return (
      <p role="status" className="mt-2 text-small text-success-ink">
        Đã gửi đề xuất cho học vụ. <Link href={`/yeu-cau/${daGui}`} className="font-semibold underline">Xem yêu cầu →</Link>
      </p>
    );
  }
  return (
    <div className="mt-2 flex flex-wrap items-center gap-3">
      <Button type="button" size="sm" variant="ghost" loading={busy} disabled={!chu} onClick={() => void gui()}>
        {busy ? 'Đang gửi…' : 'Gửi đề xuất cho học vụ'}
      </Button>
      {err && <span role="alert" className="text-small text-danger-ink">{err}</span>}
    </div>
  );
}
