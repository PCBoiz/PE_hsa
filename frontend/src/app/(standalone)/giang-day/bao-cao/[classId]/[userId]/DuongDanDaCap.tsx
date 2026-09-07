'use client';

import { useCallback, useEffect, useState } from 'react';

import { Button } from '@/components/ui';
import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';

/**
 * ĐƯỜNG DẪN ĐÃ CẤP: xem chúng, biết phụ huynh đã mở chưa, và THU HỒI được.
 *
 * ── VÌ SAO CÓ TỆP NÀY (07/09/2026) ────────────────────────────────────────
 *
 * Audit luồng hôm nay dò ngược 104 endpoint của backend xem cái nào không có
 * nơi gọi ở frontend. Hai cái nằm ngay cạnh nhau, và cả hai đều thuộc đường đi
 * NHẠY CẢM NHẤT của sản phẩm — đường mà người không có tài khoản cũng đi được:
 *
 *   GET  /api/teach/classes/<c>/students/<u>/parent-report/link
 *        → danh sách chìa còn hiệu lực, kèm `openedCount`, `lastOpenedAt`
 *   POST /api/teach/parent-report/links/<id>/revoke
 *        → thu hồi một chìa
 *
 * Cả hai đã dựng, đã có phép kiểm, đã ghi trong tài liệu, và bảng "Ai làm được
 * gì" LIỆT KÊ "Thu hồi một đường dẫn đã gửi" như một việc giảng viên làm được.
 * Nhưng không màn nào gọi tới. Tức sản phẩm hứa ba nơi một việc mà không bấm
 * được ở đâu cả.
 *
 * Điều đó nguy hơn là thiếu tính năng. Ngay trong `TaoDuongDan` có câu dặn
 * "đừng dán vào nhóm lớp" — dặn đúng, nhưng người lỡ dán rồi thì không có
 * đường lùi. Lời cảnh báo mà không kèm lối thoát là lời cảnh báo rỗng.
 *
 * ── VÌ SAO HIỆN SỐ LẦN MỞ ────────────────────────────────────────────────
 *
 * `openedCount` trả lời câu giảng viên thật sự hỏi sau khi gửi: "phụ huynh đã
 * xem chưa?". Không có nó thì họ nhắn Zalo hỏi lại, hoặc gửi thêm lần nữa.
 *
 * Nó KHÔNG nói được ai mở — chỉ nói chìa này đã được dùng mấy lần. Ghi rõ vậy
 * để không ai đọc con số ấy thành "phụ huynh đã đọc báo cáo".
 *
 * ── THU HỒI LÀ VIỆC MỘT CHIỀU, NÊN HỎI LẠI MỘT NHỊP ──────────────────────
 *
 * Backend đặt `revoked_at` chứ không xoá dòng (giữ bằng chứng đã gửi cho ai,
 * lúc nào). Nhưng với phụ huynh thì chìa chết hẳn, và cấp lại là một đường dẫn
 * KHÁC — cái cũ họ đã lưu sẽ báo lỗi. Nên nút hỏi lại một nhịp ngay tại chỗ,
 * không phải hộp thoại `confirm()` của trình duyệt (nó chặn cả trang, không
 * theo giao diện, và trên vài trình duyệt còn bị chặn hẳn).
 */

export type ChiaKhoa = {
  id: number;
  token: string;
  from: string;
  to: string;
  createdAt: string;
  expiresAt: string;
  openedCount: number;
  lastOpenedAt: string | null;
};

const ngay = (s: string) => new Date(s).toLocaleDateString('vi-VN');

export default function DuongDanDaCap({
  classId,
  userId,
  lamMoiKhi,
}: {
  classId: string;
  userId: string;
  /** Đổi giá trị này để bắt danh sách nạp lại — nơi gọi tăng nó sau khi cấp chìa mới. */
  lamMoiKhi: number;
}) {
  const [ds, setDs] = useState<ChiaKhoa[] | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [hoiThuHoi, setHoiThuHoi] = useState<number | null>(null);
  const [dangThuHoi, setDangThuHoi] = useState<number | null>(null);

  const nap = useCallback(async () => {
    try {
      const r = await apiFetch(
        `/api/teach/classes/${classId}/students/${userId}/parent-report/link`,
      );
      const body: unknown = await r.json().catch(() => null);
      if (!r.ok) { setLoi(errorText(r.status, body)); return; }
      setLoi(null);
      setDs(((body as { links?: ChiaKhoa[] })?.links) ?? []);
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Chưa đọc được danh sách đường dẫn.'));
    }
  }, [classId, userId]);

  /* Nạp lần đầu và mỗi khi `lamMoiKhi` đổi.
   *
   * ── VÌ SAO KHÔNG PHẢI `useEffect(() => { void nap(); }, [nap, lamMoiKhi])`
   *
   * Luật `react-hooks/set-state-in-effect` (theo cùng đợt nâng thư viện
   * 06/09/2026) báo đỏ dòng ấy, và nó báo đúng một chuyện có thật: hàm gọi
   * trong thân effect dẫn thẳng tới `setState`.
   *
   * Nhưng thứ đáng sửa không phải cái nhãn đỏ. Bản cũ KHÔNG HUỶ được lượt gọi
   * đang bay: đổi học viên hay bấm làm mới hai lần thì lượt cũ về sau vẫn
   * `setDs`, và danh sách chìa của em TRƯỚC hiện dưới tên em SAU. Trên màn
   * quản lý chìa xem báo cáo của một đứa trẻ thì đó là nhầm dữ liệu giữa hai
   * gia đình, không phải một lỗi hiển thị.
   *
   * Nên nạp ngay trong effect kèm cờ huỷ. `nap` vẫn giữ nguyên cho đường bấm
   * tay sau khi thu hồi chìa — ở đó không có chuyện gắn/gỡ thành phần. */
  useEffect(() => {
    let huy = false;
    void (async () => {
      try {
        const r = await apiFetch(
          `/api/teach/classes/${classId}/students/${userId}/parent-report/link`,
        );
        const body: unknown = await r.json().catch(() => null);
        if (huy) return;
        if (!r.ok) { setLoi(errorText(r.status, body)); return; }
        setLoi(null);
        setDs(((body as { links?: ChiaKhoa[] })?.links) ?? []);
      } catch (e) {
        if (!huy) setLoi(loiBatDuoc(e, 'Chưa đọc được danh sách đường dẫn.'));
      }
    })();
    return () => { huy = true; };
  }, [classId, userId, lamMoiKhi]);

  async function thuHoi(id: number) {
    setDangThuHoi(id);
    setLoi(null);
    try {
      const r = await apiFetch(`/api/teach/parent-report/links/${id}/revoke`, { method: 'POST' });
      if (!r.ok) {
        setLoi(errorText(r.status, await r.json().catch(() => null)));
        return;
      }
      /* Nạp LẠI từ máy chủ thay vì tự xoá khỏi mảng trong máy: máy chủ chỉ trả
         chìa `revoked_at IS NULL AND expires_at > now()`, nên lượt nạp lại còn
         dọn luôn những chìa vừa hết hạn trong lúc trang đang mở. Tự sửa mảng
         thì danh sách trên màn dần lệch khỏi sự thật mà không ai biết. */
      await nap();
      setHoiThuHoi(null);
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Chưa thu hồi được. Thử lại sau ít phút.'));
    } finally {
      setDangThuHoi(null);
    }
  }

  // Chưa nạp xong, hoặc không có chìa nào: không chiếm chỗ. Trang này việc
  // chính là xem tờ báo cáo, danh sách chìa chỉ hiện khi thật sự có chìa.
  if (!ds || ds.length === 0) {
    return loi ? (
      <p role="alert" className="text-small text-danger-ink print:hidden">{loi}</p>
    ) : null;
  }

  return (
    <div className="rounded-md border border-line bg-surface px-4 py-3 print:hidden">
      <p className="text-subhead text-ink">
        Đường dẫn đang hiệu lực ({ds.length})
      </p>
      <p className="mt-0.5 text-small text-ink-2">
        Mỗi đường dẫn ai cầm cũng mở được cho tới ngày hết hạn. Thu hồi là cách
        duy nhất cắt hiệu lực trước hạn.
      </p>

      {loi && (
        <p role="alert" className="mt-2 text-small text-danger-ink">{loi}</p>
      )}

      <ul className="mt-3 flex flex-col gap-2">
        {ds.map((c) => (
          <li
            key={c.id}
            className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2 rounded-md border border-line bg-sunken px-3 py-2"
          >
            <div className="min-w-0">
              <p className="text-small text-ink">
                Kỳ {ngay(c.from)} – {ngay(c.to)} · hết hạn {ngay(c.expiresAt)}
              </p>
              <p className="mt-0.5 text-small text-ink-2">
                {c.openedCount === 0
                  ? 'Chưa ai mở lần nào'
                  : `Đã mở ${c.openedCount} lần${c.lastOpenedAt ? `, gần nhất ${ngay(c.lastOpenedAt)}` : ''}`}
                {/* Nói rõ giới hạn của con số.
                    "Đã mở 3 lần" rất dễ bị đọc thành "phụ huynh đã đọc". Nó
                    KHÔNG nói được thế, vì hai lý do:
                      · không ghi ai mở (cố ý — xem `parent_link.py`);
                      · trang `/bc/<chìa>` dựng ở MÁY CHỦ, nên MỌI lượt GET đều
                        tính, kể cả lượt bot xem trước liên kết của Zalo hay
                        Messenger lấy về khi vừa dán link vào khung chat.
                    Tức con số này thường đã ≥ 1 trước khi phụ huynh nhìn. Audit
                    07/09/2026; cách đếm cho đúng là một quyết định đang chờ anh
                    Sơn (xem VIEC_CUA_ANH 14.2). */}
                {c.openedCount > 0
                  && ' — đếm cả lượt bot chat xem trước liên kết, nên chưa chắc phụ huynh đã mở.'}
              </p>
            </div>

            {hoiThuHoi === c.id ? (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-small text-warning-ink">
                  Thu hồi? Phụ huynh sẽ không mở được nữa.
                </span>
                <Button
                  variant="danger"
                  onClick={() => void thuHoi(c.id)}
                  disabled={dangThuHoi === c.id}
                >
                  {dangThuHoi === c.id ? 'Đang thu hồi…' : 'Thu hồi'}
                </Button>
                <Button variant="ghost" onClick={() => setHoiThuHoi(null)}>
                  Thôi
                </Button>
              </div>
            ) : (
              <Button variant="ghost" onClick={() => setHoiThuHoi(c.id)}>
                Thu hồi
              </Button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
