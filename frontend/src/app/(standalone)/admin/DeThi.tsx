'use client';

import { useRef, useState } from 'react';

import {
  Button,
  Card,
  CardHead,
  Chip,
  EmptyState,
  TableWrap,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
} from '@/components/ui';
import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';

export type DeRow = {
  id: number;
  title: string;
  durationMinutes: number | null;
  totalQuestions: number | null;
  isPublished: boolean;
  attempts: number;
};

/**
 * ĐỀ THI THỬ — tải mẫu, điền, tải lên.
 *
 * ── VÌ SAO MÀN HÌNH NÀY CÓ MẶT ────────────────────────────────────────────
 *
 * Đường nhập ở máy chủ (`mockexam/quan_tri.py`) dựng xong 04/09/2026 nhưng
 * KHÔNG có cửa nào để dùng — tức tính năng ấy chưa tồn tại với người dùng. Bốn
 * endpoint không có nút bấm thì bằng không.
 *
 * Trước đó, đường DUY NHẤT để có thêm một đề thi là sửa mã nguồn: đo trên CSDL
 * thật chỉ có ĐÚNG MỘT đề, đến từ `seed_data`. Mà đề CBT /150 là trụ cột 4 của
 * `TOPHSA_STRATEGY_PLAN` — thứ biến sản phẩm thành *luyện thi* thay vì một
 * trang bài giảng. Với một đề, học viên tự đo được đúng một lần.
 *
 * ── BA CHI TIẾT LẤY TỪ KAHOOT, VÀ CHI TIẾT THỨ HAI LÀ QUAN TRỌNG NHẤT ─────
 *
 * · tải mẫu → điền → tải lên: người soạn đề làm việc trong Excel, không trong
 *   dấu ngoặc nhọn;
 * · **báo TỪNG DÒNG sai trong MỘT lượt**, kèm số dòng như trong Excel. Sửa một
 *   lỗi rồi tải lên lại để gặp lỗi thứ hai là một vòng lặp làm người ta bỏ cuộc.
 *   `errorText()` dùng chung của repo chỉ trả về MỘT chuỗi và bỏ mảng `details`
 *   — nên ở đây `details` có state riêng, không đi qua nó;
 * · trần độ dài hiện ra dưới dạng LỖI chứ không cắt ngầm.
 *
 * ── VÌ SAO ĐỀ NHẬP VÀO MẶC ĐỊNH BỊ ẨN ─────────────────────────────────────
 *
 * Nhập xong là học viên thấy ngay thì một lần nhầm cột đáp án sẽ chấm sai cho
 * cả lớp trước khi ai kịp nhận ra. Người soạn phải tự bấm "Hiện cho học viên".
 */
export default function DeThi({ initial, loi }: { initial: DeRow[]; loi: string | null }) {
  const [de, setDe] = useState<DeRow[]>(initial);
  const [err, setErr] = useState<string | null>(loi);
  /** Lỗi TỪNG DÒNG của tệp vừa tải lên. Tách khỏi `err` vì nó là một danh sách. */
  const [dongLoi, setDongLoi] = useState<string[]>([]);
  const [xong, setXong] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [mo, setMo] = useState(false);

  const [ten, setTen] = useState('');
  const [phut, setPhut] = useState('195');
  const [ghiDe, setGhiDe] = useState('');
  const oTep = useRef<HTMLInputElement>(null);
  const dangGui = useRef(false);

  async function nap() {
    try {
      const r = await apiFetch('/api/admin/mock-exams');
      if (r.ok) setDe(((await r.json()).exams as DeRow[]) ?? []);
    } catch {
      /* giữ nguyên danh sách đang hiện */
    }
  }

  async function nhap() {
    if (dangGui.current) return;
    const tep = oTep.current?.files?.[0];
    if (!tep) {
      setErr('Chưa chọn tệp bảng tính.');
      return;
    }
    dangGui.current = true;
    setBusy(true);
    setErr(null);
    setDongLoi([]);
    setXong(null);
    try {
      const fd = new FormData();
      fd.append('file', tep);
      fd.append('title', ten.trim());
      fd.append('duration_minutes', phut.trim());
      if (ghiDe) fd.append('exam_id', ghiDe);
      // KHÔNG đặt `Content-Type`: trình duyệt phải tự đặt để kèm được `boundary`
      // của multipart. Đặt tay là gửi một thân không đọc nổi, và lỗi hiện ra ở
      // tận DRF dưới dạng "Chưa chọn tệp bảng tính" — chỉ sai chỗ, không sai chữ.
      const r = await apiFetch('/api/admin/mock-exams/import', { method: 'POST', body: fd });
      const d = (await r.json().catch(() => ({}))) as {
        error?: string;
        details?: string[];
        questions?: number;
      };
      if (!r.ok) {
        setDongLoi(Array.isArray(d.details) ? d.details : []);
        throw new Error(errorText(r.status, d));
      }
      setXong(
        `Đã nhập ${d.questions} câu hỏi. Đề đang ẩn — bấm “Hiện cho học viên” khi đã xem lại.`,
      );
      setTen('');
      setGhiDe('');
      if (oTep.current) oTep.current.value = '';
      setMo(false);
      await nap();
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không nhập được đề thi'));
    } finally {
      dangGui.current = false;
      setBusy(false);
    }
  }

  async function doiHien(d: DeRow) {
    setErr(null);
    if (
      !d.isPublished &&
      !confirm(
        `Hiện đề "${d.title}" cho học viên?\n\n` +
          `Đề có ${d.totalQuestions ?? 0} câu. Xem lại vài câu — nhất là cột đáp án — ` +
          'trước khi hiện: nhập nhầm cột đáp án sẽ chấm sai cho cả lớp.',
      )
    )
      return;
    try {
      const r = await apiFetch(`/api/admin/mock-exams/${d.id}/publish`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ published: !d.isPublished }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, j));
      await nap();
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không đổi được trạng thái đề'));
    }
  }

  const oChung =
    'min-h-11 w-full min-w-0 rounded-md border border-line bg-surface px-3 text-input text-ink placeholder:text-ink-3/70';

  return (
    <Card as="section">
      <CardHead
        title="Đề thi thử"
        hint="Tải mẫu .xlsx về, điền, rồi tải lên. Sai ở đâu hệ thống báo đúng số dòng như trong Excel — và một dòng sai thì không dòng nào được ghi."
        action={
          <span className="flex flex-wrap gap-2">
            {/* Liên kết thường chứ không `fetch`: đây là một lượt TẢI VỀ, và
                cookie phiên đi kèm điều hướng cùng nguồn. Cùng cách với nút xuất
                CSV của khu Giảng dạy. */}
            <a
              href="/api/admin/mock-exams/template.xlsx"
              className="inline-flex min-h-9 items-center rounded-md border border-line px-3 text-small font-semibold text-brand-ink hover:bg-sunken"
            >
              ↓ Tải mẫu .xlsx
            </a>
            {!mo && (
              <Button size="sm" onClick={() => setMo(true)}>
                Nhập đề từ bảng tính
              </Button>
            )}
          </span>
        }
      />

      {/* Chỉ hiện câu tóm tắt khi KHÔNG có danh sách dòng lỗi. Đo trên ảnh chụp
          04/09: hai hộp đỏ chồng nhau nói cùng một con số ("3 lỗi trong tệp" và
          "3 dòng cần sửa"), và hộp trên không thêm được gì mà hộp dưới chưa nói.
          Lặp lại một cảnh báo làm nó nhẹ đi, không nặng thêm. */}
      {err && dongLoi.length === 0 && (
        <p role="alert" className="mb-3 rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">
          {err}
        </p>
      )}

      {/* Lỗi TỪNG DÒNG. Đây là chi tiết khiến mẫu dùng được mà không cần hướng
          dẫn: người soạn nhấn Ctrl+G trong Excel tới đúng dòng được nêu. */}
      {dongLoi.length > 0 && (
        <div className="mb-3 rounded-md border border-danger/40 bg-danger/5 px-3 py-2">
          <p className="text-small font-semibold text-danger-ink">
            {dongLoi.length} dòng cần sửa — chưa ghi gì cả:
          </p>
          <ul className="mt-1 max-h-64 list-disc overflow-y-auto pl-5 text-small text-ink-2">
            {dongLoi.map((l, i) => (
              <li key={i}>{l}</li>
            ))}
          </ul>
        </div>
      )}

      {xong && (
        <p role="status" className="mb-3 rounded-md bg-good/10 px-3 py-2 text-small text-ink">
          {xong}
        </p>
      )}

      {mo && (
        <div className="mb-4 rounded-md border border-line bg-sunken p-4">
          <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr))]">
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Tên đề</span>
              <input
                value={ten}
                onChange={(e) => setTen(e.target.value)}
                placeholder="HSA thử sức đợt 1/2027"
                className={oChung}
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Thời gian làm bài (phút)</span>
              <input
                value={phut}
                inputMode="numeric"
                onChange={(e) => setPhut(e.target.value)}
                className={oChung}
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Tệp .xlsx hoặc .csv</span>
              {/* KHUNG ở thẻ bọc, ô nhập để trần bên trong.
                  Đặt viền + `min-h` thẳng lên `<input type=file>` thì Chromium
                  dựng hộp cao hơn hàng và tràn xuống ô bên dưới — thấy trên ảnh
                  chụp 04/09. Ô chọn tệp có bố cục nội tại riêng, không nhận
                  `items-center`; nên để thẻ bọc lo cái khung. */}
              <span className="flex min-h-11 w-full min-w-0 items-center overflow-hidden rounded-md border border-line bg-surface px-3">
                <input
                  ref={oTep}
                  type="file"
                  accept=".xlsx,.csv"
                  className="w-full min-w-0 text-small text-ink file:mr-3 file:rounded file:border-0 file:bg-sunken file:px-3 file:py-1 file:text-small file:text-brand-ink"
                />
              </span>
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-label text-ink-3">Ghi đè đề đã có</span>
              <select value={ghiDe} onChange={(e) => setGhiDe(e.target.value)} className={oChung}>
                <option value="">(tạo đề mới)</option>
                {/* Đề đã có người làm KHÔNG hiện ở đây: backend chặn bằng 409 vì
                    điểm cũ chấm trên bộ câu hỏi khác, nên mời người dùng chọn nó
                    là mời họ đi vào một bức tường. */}
                {de
                  .filter((d) => d.attempts === 0)
                  .map((d) => (
                    <option key={d.id} value={String(d.id)}>
                      {d.title}
                    </option>
                  ))}
              </select>
            </label>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button loading={busy} disabled={!ten.trim()} onClick={() => void nhap()}>
              Tải lên và kiểm
            </Button>
            <Button variant="ghost" onClick={() => setMo(false)}>
              Huỷ
            </Button>
          </div>
        </div>
      )}

      {de.length === 0 ? (
        <EmptyState
          title="Chưa có đề thi thử nào"
          hint="Tải mẫu .xlsx về, điền một dòng một câu hỏi, rồi tải lên. Trang “Hướng dẫn” trong tệp mẫu nói rõ từng cột."
        />
      ) : (
        <TableWrap caption="Các đề thi thử, kèm số câu và số lượt đã làm">
          <Thead>
            <tr>
              <Th>Đề</Th>
              <Th align="right">Câu</Th>
              <Th align="right">Phút</Th>
              <Th align="right">Lượt làm</Th>
              <Th>Học viên thấy</Th>
              <Th align="right">Thao tác</Th>
            </tr>
          </Thead>
          <Tbody>
            {de.map((d) => (
              <Tr key={d.id} dim={!d.isPublished}>
                <Td label="Đề">
                  <span className="font-semibold text-ink">{d.title}</span>
                </Td>
                <Td label="Câu" num>
                  {d.totalQuestions ?? 0}
                </Td>
                <Td label="Phút" num>
                  {d.durationMinutes ?? 0}
                </Td>
                <Td label="Lượt làm" num>
                  {d.attempts}
                </Td>
                <Td label="Học viên thấy">
                  <Chip tone={d.isPublished ? 'good' : 'neutral'}>
                    {d.isPublished ? 'đang hiện' : 'đang ẩn'}
                  </Chip>
                </Td>
                <Td label="Thao tác">
                  <span className="flex justify-end">
                    <Button size="sm" variant="ghost" onClick={() => void doiHien(d)}>
                      {d.isPublished ? 'Ẩn đi' : 'Hiện cho học viên'}
                    </Button>
                  </span>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </TableWrap>
      )}
    </Card>
  );
}
