'use client';

import { useEffect, useState } from 'react';

import { Button, Card, CardHead } from '@/components/ui';
import { ghiJson, layJson, loiBatDuoc } from '@/lib/api';
import { useDaGan } from '@/lib/daGan';
import { HD_KHO, buoiNgan, nhom, tenMien, type Kho, type TaiLieu } from '@/lib/hocLieu';

/**
 * HỌC LIỆU CỦA LỚP — màn của giảng viên / trợ giảng (§60, bảng TopHSA dòng 30 và phần tài
 * liệu của dòng 15).
 *
 * Anh Sơn chốt 26/09: **liên kết ngoài trước** (Drive, YouTube, link đề) vì nó không chờ
 * khoá Cloudflare R2, và gắn được vào **cả kho chung của lớp lẫn từng buổi**.
 *
 * Đặt ở màn Buổi học vì đây đã là chỗ người ta quản lý từng buổi: người vừa dựng xong buổi
 * là người có slide của buổi ấy trong tay. Bắt họ đi tìm một trang khác là cách chắc chắn
 * để tài liệu không bao giờ được gắn.
 *
 * ── BA ĐIỀU ĐÃ HỌC Ở NƠI KHÁC, ÁP THẲNG VÀO ĐÂY ──────────────────────────
 *
 * ① Nút và ô nhập KHOÁ tới khi React gắn xong (`useDaGan`). Trang dựng ở máy chủ nên form
 *   hiện ra trước khi JavaScript gắn vào; bấm giữa hai mốc ấy thì không có gì xảy ra và
 *   không dấu hiệu nào cho người bấm biết. Mất một lượt đo vì chuyện này ở trang Thông báo.
 * ② Chờ máy chủ trả lời RỒI mới đổi màn. Nút "Báo hỏng bản ghi" (§72) đặt trạng thái trước
 *   rồi nuốt lỗi, nên màn nói "đã xong" trong khi không có gì xảy ra.
 * ③ Câu lỗi của máy chủ hiện NGUYÊN VĂN theo ô (`errors`), không gộp thành một câu chung:
 *   "Dán địa chỉ bắt đầu bằng http:// hoặc https://" chỉ có nghĩa khi nó nằm cạnh ô địa chỉ.
 */
type Buoi = { id: number; luc: string | null; chuDe: string | null };

export default function HocLieuLop({ classId, buoi }: { classId: number; buoi: Buoi[] }) {
  const [kho, setKho] = useState<Kho | null>(null);
  const [ten, setTen] = useState('');
  const [url, setUrl] = useState('');
  const [moTa, setMoTa] = useState('');
  const [sessionId, setSessionId] = useState<number | ''>('');
  const [an, setAn] = useState(false);
  const [loiO, setLoiO] = useState<Record<string, string>>({});
  const [err, setErr] = useState<string | null>(null);
  const [bao, setBao] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const daGan = useDaGan();

  useEffect(() => {
    let huy = false;
    layJson<Kho>(`/api/teach/classes/${classId}/hoc-lieu`, HD_KHO)
      .then((d) => { if (!huy) setKho(d); })
      .catch((e) => { if (!huy) setErr(loiBatDuoc(e, 'Không tải được danh sách tài liệu.')); });
    return () => { huy = true; };
  }, [classId]);

  async function gan() {
    if (busy) return;
    setBusy(true);
    setLoiO({});
    setErr(null);
    setBao(null);
    try {
      const moi = await ghiJson<TaiLieu>(
        `/api/teach/classes/${classId}/hoc-lieu`,
        { method: 'POST', body: JSON.stringify({ ten, url, moTa, sessionId: sessionId || null, an }) },
        // Máy chủ trả THẲNG tài liệu vừa tạo, nên không phải tải lại cả danh sách.
        (await import('@/lib/hocLieu')).HD_TAI_LIEU,
      );
      setKho((cu) => (cu ? { ...cu, items: [moi, ...cu.items] } : cu));
      setTen(''); setUrl(''); setMoTa(''); setSessionId(''); setAn(false);
      setBao(`Đã gắn "${moi.ten}".`);
    } catch (e) {
      const t = loiBatDuoc(e, 'Không gắn được tài liệu.');
      // `ghiJson` ném câu của máy chủ; lỗi theo ô nằm trong `errors` nên bắt riêng.
      try {
        const j = JSON.parse(t) as { errors?: Record<string, string> };
        if (j.errors) setLoiO(j.errors); else setErr(t);
      } catch { setErr(t); }
    } finally {
      setBusy(false);
    }
  }

  async function go(t: TaiLieu) {
    if (busy) return;
    setBusy(true);
    try {
      await ghiJson(`/api/teach/classes/${classId}/hoc-lieu/${t.id}`, { method: 'DELETE' },
        (await import('@/lib/hocLieu')).HD_GO);
      setKho((cu) => (cu ? { ...cu, items: cu.items.filter((x) => x.id !== t.id) } : cu));
      setBao(`Đã gỡ "${t.ten}".`);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không gỡ được tài liệu.'));
    } finally {
      setBusy(false);
    }
  }

  const nhomTaiLieu = nhom(kho?.items ?? []);

  return (
    /* `Card` chỉ nhận đúng năm prop và KHÔNG spread phần còn lại, nên `data-khu` đặt lên
       nó không bao giờ tới DOM — bộ đo tìm mãi không thấy khối (mất một lượt đo 27/09).
       Mốc cho bộ đo đặt ở một thẻ bọc thật. */
    <section data-khu="hoc-lieu" className="mt-6">
    <Card>
      <CardHead title="Tài liệu của lớp" />
      <p className="mb-3 text-small text-ink-3">
        Dán địa chỉ Google Drive, YouTube hoặc link đề. Để trống ô buổi học thì tài liệu nằm ở
        kho chung của lớp; chọn một buổi thì chỉ những em thuộc buổi ấy nhìn thấy.
      </p>

      <div className="flex flex-col gap-2">
        <label className="text-small text-ink-2">
          Tên tài liệu
          <input
            value={ten}
            onChange={(e) => setTen(e.target.value)}
            disabled={!daGan || busy}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-body text-ink"
            placeholder="Slide buổi 1 — Tư duy định lượng"
          />
        </label>
        {loiO.ten && <p className="text-small text-danger-ink">{loiO.ten}</p>}

        <label className="text-small text-ink-2">
          Địa chỉ
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={!daGan || busy}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-body text-ink"
            placeholder="https://drive.google.com/…"
          />
        </label>
        {loiO.url && <p className="text-small text-danger-ink">{loiO.url}</p>}

        <label className="text-small text-ink-2">
          Ghi chú cho học viên (không bắt buộc)
          <input
            value={moTa}
            onChange={(e) => setMoTa(e.target.value)}
            disabled={!daGan || busy}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-body text-ink"
          />
        </label>

        <label className="text-small text-ink-2">
          Gắn vào buổi học
          <select
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value ? Number(e.target.value) : '')}
            disabled={!daGan || busy}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-body text-ink"
          >
            <option value="">Kho chung của lớp</option>
            {buoi.map((b) => (
              <option key={b.id} value={b.id}>
                {buoiNgan(b.luc)}{b.chuDe ? ` · ${b.chuDe}` : ''}
              </option>
            ))}
          </select>
        </label>
        {loiO.sessionId && <p className="text-small text-danger-ink">{loiO.sessionId}</p>}

        <label className="flex items-center gap-2 text-small text-ink-2">
          <input type="checkbox" checked={an} onChange={(e) => setAn(e.target.checked)} disabled={!daGan || busy} />
          Gắn nhưng CHƯA cho học viên xem (mở sau theo tiến độ)
        </label>

        <div>
          <Button onClick={() => void gan()} disabled={!daGan || busy || !ten.trim() || !url.trim()}>
            {busy ? 'Đang gắn…' : 'Gắn tài liệu'}
          </Button>
        </div>
      </div>

      {err && <p className="mt-3 rounded-xl bg-danger/10 px-4 py-3 text-small text-danger-ink" role="alert">{err}</p>}
      {bao && <p className="mt-3 text-small text-success-ink" role="status">{bao}</p>}

      <div className="mt-5 flex flex-col gap-4">
        {nhomTaiLieu.length === 0 && (
          <p className="text-small text-ink-3">Lớp chưa có tài liệu nào.</p>
        )}
        {nhomTaiLieu.map((n) => (
          <div key={n.sessionId ?? 'chung'}>
            <h3 className="mb-1 text-small font-semibold text-ink-2">
              {n.sessionId === null ? 'Kho chung của lớp' : `Buổi ${buoiNgan(n.buoiLuc)}`}
            </h3>
            <ul className="flex flex-col gap-1">
              {n.items.map((t) => (
                <li key={t.id} data-id={t.id} className="flex flex-wrap items-center gap-2 text-small">
                  <a
                    href={t.url ?? undefined}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-brand-ink underline underline-offset-2"
                  >
                    {t.ten}
                  </a>
                  {tenMien(t.url) && <span className="text-ink-3">({tenMien(t.url)})</span>}
                  {t.an && <span className="rounded-full bg-sunken px-2 py-0.5 text-ink-3">chưa mở cho học viên</span>}
                  <button
                    type="button"
                    onClick={() => void go(t)}
                    disabled={!daGan || busy}
                    className="ml-auto text-ink-3 underline underline-offset-2 hover:text-danger-ink disabled:opacity-50"
                  >
                    Gỡ
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Card>
    </section>
  );
}
