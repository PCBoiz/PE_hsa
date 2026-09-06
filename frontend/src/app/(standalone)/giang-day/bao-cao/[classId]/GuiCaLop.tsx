'use client';

import { useState } from 'react';

import { Button } from '@/components/ui';
import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';

/**
 * Nút GỬI CẢ LỚP — và cửa xác nhận trước nó.
 *
 * ── VÌ SAO CÓ MỘT BƯỚC XÁC NHẬN ───────────────────────────────────────────
 *
 * Một tin đã tới Zalo phụ huynh thì không thu về được, và mỗi tin ZNS đều mất
 * phí. Nút này gửi cho CẢ LỚP một lúc, nên một cú bấm nhầm là 25 tin nhắn
 * không rút lại được và một hoá đơn thật. Ngưỡng "hỏi lại" ở đây không phải sự
 * cẩn thận thừa — nó tỉ lệ với thứ không hoàn tác được.
 *
 * Câu hỏi nêu ĐÚNG SỐ người sẽ nhận, không hỏi chung chung "bạn có chắc
 * không". "Chắc không" thì ai cũng bấm Có; "gửi cho 25 phụ huynh" thì người ta
 * dừng lại một nhịp và đối chiếu.
 *
 * ── KHI CHƯA CÓ ZALO OA ───────────────────────────────────────────────────
 *
 * Nút vẫn dùng được, nhưng nó nói thẳng là sẽ CẤP LINK chứ không gửi tin —
 * chứ không im lặng làm một việc khác với chữ trên nút. Nhãn nút đổi theo.
 */
type KetQua = {
  tong: number;
  znsSanSang: boolean;
  dem: Record<string, number>;
  ketQua: {
    id: number;
    name: string | null;
    trangThai: 'da_gui' | 'gui_tay' | 'thieu_so' | 'loi';
    duongDan: string;
    loi: string | null;
  }[];
};

const NHAN: Record<string, { chu: string; mau: string }> = {
  da_gui: { chu: 'Đã gửi', mau: 'text-success-ink' },
  gui_tay: { chu: 'Cần gửi tay', mau: 'text-ink-2' },
  thieu_so: { chu: 'Thiếu số phụ huynh', mau: 'text-warning-ink' },
  loi: { chu: 'Lỗi', mau: 'text-danger-ink' },
};

export default function GuiCaLop({
  classId,
  soEm,
  znsSanSang,
  znsThieu,
}: {
  classId: string;
  soEm: number;
  znsSanSang: boolean;
  znsThieu: string[];
}) {
  const [hoiLai, setHoiLai] = useState(false);
  const [dangChay, setDangChay] = useState(false);
  const [kq, setKq] = useState<KetQua | null>(null);
  const [loi, setLoi] = useState<string | null>(null);

  async function gui() {
    setDangChay(true);
    setLoi(null);
    try {
      const r = await apiFetch(`/api/teach/classes/${classId}/parent-report/send-all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
      });
      const body: unknown = await r.json().catch(() => null);
      if (!r.ok) {
        setLoi(errorText(r.status, body));
        return;
      }
      setKq(body as KetQua);
      setHoiLai(false);
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Chưa gửi được. Thử lại sau ít phút.'));
    } finally {
      setDangChay(false);
    }
  }

  if (kq) {
    return (
      <div className="flex flex-col gap-3">
        <p className="text-body text-ink">
          Xong {kq.tong} em:{' '}
          {Object.entries(kq.dem)
            .map(([k, n]) => `${n} ${NHAN[k]?.chu.toLowerCase() ?? k}`)
            .join(' · ')}
        </p>
        <ul className="flex flex-col gap-1">
          {kq.ketQua.map((r) => (
            <li key={r.id} className="flex flex-wrap items-baseline gap-x-2 text-small">
              <span className="font-semibold text-ink">{r.name || `#${r.id}`}</span>
              <span className={NHAN[r.trangThai]?.mau ?? 'text-ink-2'}>
                {NHAN[r.trangThai]?.chu ?? r.trangThai}
              </span>
              {r.loi && <span className="text-danger-ink">— {r.loi}</span>}
              {/* Đường dẫn hiện ra CẢ khi đã gửi thành công: phụ huynh báo chưa
                  nhận được là chuyện thường, và khi ấy người trực cần chép được
                  link ngay chứ không phải mở lại từng em. */}
              <a
                href={r.duongDan}
                target="_blank"
                rel="noopener noreferrer"
                className="font-mono text-ink-3 underline"
              >
                mở tờ
              </a>
            </li>
          ))}
        </ul>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {!znsSanSang && (
        <p className="rounded-md border border-line bg-sunken px-3 py-2 text-small text-ink-2">
          Chưa nối Zalo OA nên hệ thống chưa tự nhắn được. Bấm nút bên dưới thì nó
          <strong> cấp đường dẫn cho từng em</strong> để bạn gửi tay.
          {znsThieu.length > 0 && (
            <> Còn thiếu cấu hình: <code className="font-mono">{znsThieu.join(', ')}</code>.</>
          )}
        </p>
      )}

      {!hoiLai ? (
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={() => setHoiLai(true)} disabled={soEm === 0}>
            {znsSanSang ? `Gửi cho ${soEm} phụ huynh` : `Cấp đường dẫn cho ${soEm} em`}
          </Button>
          {soEm === 0 && (
            <span className="text-small text-ink-3">
              Chưa em nào có số Zalo của phụ huynh.
            </span>
          )}
        </div>
      ) : (
        <div className="rounded-md border border-line bg-sunken px-4 py-3">
          {/* Nêu ĐÚNG SỐ người sẽ nhận. "Bạn có chắc không" thì ai cũng bấm Có. */}
          <p className="text-body text-ink">
            {znsSanSang
              ? `Gửi tin Zalo tới ${soEm} phụ huynh ngay bây giờ? Tin đã gửi không thu về được, và mỗi tin đều tính phí.`
              : `Cấp đường dẫn báo cáo cho ${soEm} em? Chưa có tin nào được gửi đi.`}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button onClick={() => void gui()} disabled={dangChay}>
              {dangChay ? 'Đang chạy…' : znsSanSang ? 'Gửi ngay' : 'Cấp đường dẫn'}
            </Button>
            <Button variant="ghost" onClick={() => setHoiLai(false)} disabled={dangChay}>
              Huỷ
            </Button>
          </div>
        </div>
      )}

      {loi && (
        <p role="alert" className="text-small text-danger-ink">
          {loi}
        </p>
      )}
    </div>
  );
}
