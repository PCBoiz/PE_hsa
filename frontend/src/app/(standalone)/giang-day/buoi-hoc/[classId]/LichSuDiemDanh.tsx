'use client';

import { useRef, useState } from 'react';
import * as z from 'zod/mini';

import { layJson, loiBatDuoc } from '@/lib/api';
import { lucVN } from '@/lib/gioVN';

/* `GET /api/teach/sessions/<id>/attendance/history` (`teaching/sessions.py`, V-d). */
const chu = z.nullable(z.string());
const HD_LICH_SU = z.looseObject({
  lichSu: z.array(z.looseObject({
    userId: z.number(), name: chu, tu: chu, den: z.string(), luc: chu, boi: chu, nguon: z.string(),
  })),
  labels: z.record(z.string(), z.string()),
  catBot: z.boolean(),
});
type LichSu = z.infer<typeof HD_LICH_SU>;

/**
 * "Lịch sử sửa" của MỘT buổi — ai đổi điểm danh của em nào, từ gì sang gì, lúc nào
 * (bảng TopHSA dòng 9, 14). Gấp sẵn và chỉ tải khi MỞ — không tốn một lượt gọi cho
 * mỗi lần mở sổ điểm danh. Nơi dùng đặt `key` theo số lần Lưu, nên sau mỗi lần lưu
 * khối dựng lại từ đầu (gấp, dữ liệu cũ bỏ đi) thay vì giữ một lịch sử đã cũ.
 */
export default function LichSuDiemDanh({ sessionId }: { sessionId: number }) {
  const [data, setData] = useState<LichSu | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [mo, setMo] = useState(false);
  const daGoi = useRef(false);

  async function tai() {
    if (daGoi.current) return;
    daGoi.current = true;
    setLoi(null);
    try {
      setData(await layJson(`/api/teach/sessions/${sessionId}/attendance/history`, HD_LICH_SU));
    } catch (e) {
      daGoi.current = false;          // mở lại thì thử lại
      setLoi(loiBatDuoc(e, 'Không tải được lịch sử sửa'));
    }
  }

  const nhan = (s: string | null) => (s ? (data?.labels[s] ?? s) : '');

  return (
    <details
      className="group mt-4 rounded-md border border-line bg-surface px-3 py-2"
      onToggle={(e) => {
        const dangMo = e.currentTarget.open;
        setMo(dangMo);
        if (dangMo) void tai();
      }}
    >
      <summary className="inline-flex min-h-11 cursor-pointer items-center gap-1 text-small font-semibold text-brand-ink">
        <span aria-hidden="true" className="inline-block transition-transform group-open:rotate-90 motion-reduce:transition-none">›</span>
        Lịch sử sửa điểm danh
      </summary>
      {loi && <p role="alert" className="mt-2 text-small text-danger-ink">{loi}</p>}
      {mo && !data && !loi && <p className="mt-2 text-small text-ink-3">Đang tải…</p>}
      {data && data.lichSu.length === 0 && (
        <p className="mt-2 text-small text-ink-3">Buổi này chưa có lần lưu điểm danh nào.</p>
      )}
      {data && data.lichSu.length > 0 && (
        <ol className="mt-2 flex flex-col">
          {data.lichSu.map((h, i) => (
            <li key={`${h.userId}-${h.luc}-${i}`} className="border-t border-line/50 py-2 text-small text-ink-2 first:border-t-0">
              <span className="font-semibold text-ink">{h.name || `#${h.userId}`}</span>
              {': '}
              {h.tu ? <>{nhan(h.tu)} → <b className="text-ink">{nhan(h.den)}</b></> : <>tick <b className="text-ink">{nhan(h.den)}</b></>}
              <span className="block text-ink-3">
                {[lucVN(h.luc), h.boi ? `bởi ${h.boi}` : null].filter(Boolean).join(' · ')}
              </span>
            </li>
          ))}
        </ol>
      )}
      {data?.catBot && <p className="mt-2 text-small text-ink-3">Đang hiện các lần sửa gần nhất.</p>}
    </details>
  );
}
