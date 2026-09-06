'use client';

import { useState } from 'react';

import { Button } from '@/components/ui';
import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';

/**
 * Cấp ĐƯỜNG DẪN để gửi phụ huynh, và hiện nó ra để giảng viên chép đi gửi.
 *
 * ── VÌ SAO KHÔNG TỰ BẮN TIN LUÔN ──────────────────────────────────────────
 *
 * Anh Sơn chốt 07/09/2026: hệ thống soạn sẵn, NGƯỜI bấm gửi. Tin đã đến Zalo
 * phụ huynh thì không thu về được, và mỗi tin ZNS đều mất phí — nên giữ đúng
 * một cái gật của con người trước khi nó rời khỏi hệ thống.
 *
 * Ở bước này (07/09) phần gửi hàng loạt chưa dựng, nên nút chỉ cấp đường dẫn
 * và giảng viên tự dán vào Zalo. Đó là bản dùng được ngay, không phải bản tạm:
 * trung tâm chưa có Zalo OA đã xác thực, mà ZNS thì bắt buộc phải có.
 *
 * ── KHÔNG CÓ SỐ PHỤ HUYNH THÌ NÓI TRƯỚC, ĐỪNG ĐỂ BẤM XONG MỚI BIẾT ────────
 *
 * Đường dẫn vẫn cấp được (giảng viên có thể gửi qua kênh khác), nhưng phải nói
 * rõ ngay cạnh nút — nếu không thì người ta bấm, chép link, mở Zalo, rồi mới
 * phát hiện không biết gửi cho ai.
 */
type Cap = {
  token: string;
  from: string;
  to: string;
  expiresDays: number;
  parentName: string;
  parentPhone: string;
};

export default function TaoDuongDan({
  classId,
  userId,
  coSoPhuHuynh,
}: {
  classId: string;
  userId: string;
  coSoPhuHuynh: boolean;
}) {
  const [dangChay, setDangChay] = useState(false);
  const [kq, setKq] = useState<Cap | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [daChep, setDaChep] = useState(false);

  // Dựng ở TRÌNH DUYỆT chứ không nhận từ máy chủ: máy chủ không biết chắc tên
  // miền người dùng đang mở (dev 3100, production tophsa.vn, và có thể là một
  // bản xem trước của Vercel). Lấy `origin` đang chạy là luôn đúng.
  const diaChi = kq ? `${window.location.origin}/bc/${kq.token}` : '';

  async function cap() {
    setDangChay(true);
    setLoi(null);
    try {
      const r = await apiFetch(
        `/api/teach/classes/${classId}/students/${userId}/parent-report/link`,
        { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' },
      );
      const body: unknown = await r.json().catch(() => null);
      if (!r.ok) {
        setLoi(errorText(r.status, body));
        return;
      }
      setKq(body as Cap);
      setDaChep(false);
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Chưa cấp được đường dẫn. Thử lại sau ít phút.'));
    } finally {
      setDangChay(false);
    }
  }

  async function chep() {
    try {
      await navigator.clipboard.writeText(diaChi);
      setDaChep(true);
    } catch {
      // Trình duyệt từ chối quyền clipboard (hay gặp khi trang không chạy
      // https). Ô chữ bên dưới vẫn chọn được bằng tay — nên đây không phải
      // ngõ cụt, chỉ là chậm hơn một nhịp.
      setDaChep(false);
    }
  }

  return (
    <div className="print:hidden">
      {!kq && (
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={() => void cap()} disabled={dangChay}>
            {dangChay ? 'Đang cấp…' : 'Tạo đường dẫn gửi phụ huynh'}
          </Button>
          {!coSoPhuHuynh && (
            <span className="text-small text-warning-ink">
              Em này chưa khai số Zalo của phụ huynh — vẫn tạo được đường dẫn, nhưng
              bạn sẽ phải tự chọn cách gửi.
            </span>
          )}
        </div>
      )}

      {loi && (
        <p role="alert" className="mt-2 text-small text-danger-ink">
          {loi}
        </p>
      )}

      {kq && (
        <div className="rounded-md border border-line bg-sunken px-4 py-3">
          <p className="text-label text-ink-3">Đường dẫn gửi phụ huynh</p>
          {/* `readOnly` + `onFocus select` thay cho một khối chữ: người dùng
              bấm vào là bôi đen sẵn cả dòng, chép được cả khi nút Chép không
              chạy (trình duyệt chặn clipboard trên http). */}
          <input
            readOnly
            value={diaChi}
            onFocus={(e) => e.currentTarget.select()}
            aria-label="Đường dẫn báo cáo gửi phụ huynh"
            className="mt-1 min-h-11 w-full rounded-md border border-line-input bg-surface px-3 font-mono text-small text-ink"
          />
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <Button variant="ghost" onClick={() => void chep()}>
              {daChep ? 'Đã chép ✓' : 'Chép đường dẫn'}
            </Button>
            {kq.parentPhone && (
              <span className="text-small text-ink-2">
                Gửi tới {kq.parentName || 'phụ huynh'} · {kq.parentPhone}
              </span>
            )}
          </div>
          {/* Nói HẠN ra, và nói cả điều quan trọng hơn: ai có link cũng xem
              được. Giảng viên là người quyết định gửi vào đâu, nên họ phải
              biết điều đó trước khi dán vào một nhóm chat. */}
          <p className="mt-2 text-small text-ink-3">
            Còn dùng được {kq.expiresDays} ngày. Ai có đường dẫn này đều xem được báo
            cáo, nên chỉ gửi riêng cho phụ huynh, đừng dán vào nhóm lớp.
          </p>
        </div>
      )}
    </div>
  );
}
