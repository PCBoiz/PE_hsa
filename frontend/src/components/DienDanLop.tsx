'use client';

import { useEffect, useState } from 'react';

import { Button, Card, CardHead, EmptyState } from '@/components/ui';
import { ghiJson, layJson, loiBatDuoc } from '@/lib/api';
import { useDaGan } from '@/lib/daGan';
import {
  HD_DS_BAI,
  HD_DS_BINH_LUAN,
  HD_OK,
  HD_TAO_BAI,
  TRAN_NOI_DUNG,
  TRAN_TIEU_DE,
  khiNao,
  type Bai,
  type BinhLuan,
  type DsBai,
  type DsBinhLuan,
} from '@/lib/dienDan';

/**
 * DIỄN ĐÀN RIÊNG CỦA LỚP (§75 · bảng TopHSA dòng 20).
 *
 * Anh Sơn chốt 27/09/2026: *"Những phần như này thì mình biến thành nhắn tin qua Zalo hoặc
 * qua diễn đàn riêng của lớp, không làm thành 1 messenger trong ứng dụng mình đâu"*.
 *
 * Nên đây KHÔNG phải hộp chat, và điều đó đổi cả hình dạng màn:
 *   · mỗi lượt là một BÀI có chỗ đọc lại, không phải một dòng trôi đi;
 *   · trả lời nằm dưới bài, gập lại được — người vào sau đọc được cả mạch;
 *   · không có "đang gõ…", không dấu đã xem, không thông báo đẩy từng tin.
 * Ba thứ vừa kể là thứ khiến một hộp chat thành nơi phải trực; trung tâm không trực được.
 *
 * MỘT MÀN, HAI VAI. Giảng viên / trợ giảng và học viên nhìn cùng một thứ: hàng rào nằm ở
 * máy chủ (`forum/views.py::vao_duoc_dien_dan_lop`), không ở đây. Màn không tự quyết ai
 * được đăng — nó chỉ hiện câu máy chủ trả về khi bị từ chối.
 *
 * ── Ba điều đã học ở màn khác, áp thẳng vào đây ───────────────────────────
 * ① Ô nhập và nút KHOÁ tới khi React gắn xong (`useDaGan`) — trang dựng ở máy chủ nên form
 *   hiện trước khi JavaScript gắn vào, bấm giữa hai mốc ấy là bấm vào hư không.
 * ② Chờ máy chủ trả lời RỒI mới đổi màn — không đặt trạng thái trước rồi nuốt lỗi.
 * ③ Danh sách tải thêm theo TRANG của máy chủ, không tự đoán còn bao nhiêu.
 */
export default function DienDanLop({ classId, tenLop }: { classId: number; tenLop?: string }) {
  const [ds, setDs] = useState<DsBai | null>(null);
  const [trang, setTrang] = useState(1);
  const [tieuDe, setTieuDe] = useState('');
  const [noiDung, setNoiDung] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const [bao, setBao] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [mo, setMo] = useState<number | null>(null);
  const daGan = useDaGan();

  useEffect(() => {
    let huy = false;
    layJson<DsBai>(`/api/posts?lop=${classId}&page=${trang}&per_page=20`, HD_DS_BAI)
      .then((d) => {
        if (huy) return;
        // Trang 1 thay cả danh sách; trang sau NỐI thêm — người đang đọc dở không bị
        // kéo về đầu chỉ vì bấm "Xem thêm".
        setDs((cu) => (trang === 1 || !cu ? d : { ...d, posts: [...cu.posts, ...d.posts] }));
      })
      .catch((e) => { if (!huy) setErr(loiBatDuoc(e, 'Không tải được phần trao đổi của lớp.')); });
    return () => { huy = true; };
  }, [classId, trang]);

  async function gui() {
    if (busy || !noiDung.trim()) return;
    setBusy(true);
    setErr(null);
    setBao(null);
    try {
      const r = await ghiJson<{ ok: boolean; id: number }>(
        '/api/posts',
        {
          method: 'POST',
          body: JSON.stringify({
            title: tieuDe.trim() || 'Trao đổi',
            content: noiDung.trim(),
            category: 'discuss',
            class_id: classId,
          }),
        },
        HD_TAO_BAI,
      );
      // Đọc lại trang đầu thay vì tự ghép một bài giả vào danh sách: bài thật mang tên
      // người gửi và mốc giờ do máy chủ đặt, và hai thứ ấy phải khớp với lần tải sau.
      const moi = await layJson<DsBai>(`/api/posts?lop=${classId}&page=1&per_page=20`, HD_DS_BAI);
      setDs(moi);
      setTrang(1);
      setTieuDe('');
      setNoiDung('');
      setBao('Đã gửi cho lớp.');
      setMo(r.id);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không gửi được. Thử lại sau ít phút.'));
    } finally {
      setBusy(false);
    }
  }

  const bai = ds?.posts ?? [];
  const conNua = ds ? ds.page < ds.total_pages : false;

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHead
          title="Gửi cho lớp"
          hint="Cả lớp đọc được và trả lời được. Việc riêng của một em thì gửi qua hộp Yêu cầu."
        />
        <div className="flex flex-col gap-2">
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Tiêu đề (không bắt buộc)</span>
            <input
              value={tieuDe}
              onChange={(e) => setTieuDe(e.target.value)}
              maxLength={TRAN_TIEU_DE}
              disabled={!daGan || busy}
              placeholder="Nhắc bài tập buổi 3"
              className="min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink placeholder:text-ink-3/70"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Nội dung</span>
            <textarea
              value={noiDung}
              onChange={(e) => setNoiDung(e.target.value)}
              maxLength={TRAN_NOI_DUNG}
              rows={3}
              disabled={!daGan || busy}
              placeholder="Các em nhớ làm bài 3 trước buổi sau nhé."
              className="w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 py-2 text-input text-ink placeholder:text-ink-3/70"
            />
          </label>
          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={() => void gui()} loading={busy} disabled={!daGan || !noiDung.trim()}>
              Gửi cho lớp
            </Button>
            {bao && <span className="text-small text-ink-2">{bao}</span>}
            {err && <span className="text-small text-danger-ink">{err}</span>}
          </div>
        </div>
      </Card>

      <Card>
        <CardHead
          title={tenLop ? `Trao đổi của lớp ${tenLop}` : 'Trao đổi của lớp'}
          hint={ds ? `${ds.total} bài` : undefined}
        />
        {ds && bai.length === 0 ? (
          <EmptyState
            title="Chưa có trao đổi nào"
            hint="Gửi bài đầu tiên ở ô bên trên — cả lớp sẽ đọc được và trả lời ngay dưới bài."
          />
        ) : (
          <ul className="flex flex-col gap-3">
            {bai.map((b) => (
              <MotBai
                key={b.id}
                bai={b}
                mo={mo === b.id}
                onMo={() => setMo(mo === b.id ? null : b.id)}
                daGan={daGan}
              />
            ))}
          </ul>
        )}
        {conNua && (
          <div className="mt-3">
            <Button onClick={() => setTrang((t) => t + 1)} disabled={!daGan}>
              Xem thêm
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}

/** Một bài + phần trả lời. Bình luận chỉ tải KHI mở — lớp học cả năm thì danh sách rất dài. */
function MotBai({
  bai, mo, onMo, daGan,
}: { bai: Bai; mo: boolean; onMo: () => void; daGan: boolean }) {
  const [ds, setDs] = useState<DsBinhLuan | null>(null);
  const [chu, setChu] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!mo) return;
    let huy = false;
    layJson<DsBinhLuan>(`/api/posts/${bai.id}/comments?per_page=50`, HD_DS_BINH_LUAN)
      .then((d) => { if (!huy) setDs(d); })
      .catch((e) => { if (!huy) setErr(loiBatDuoc(e, 'Không tải được phần trả lời.')); });
    return () => { huy = true; };
  }, [mo, bai.id]);

  async function traLoi() {
    if (busy || !chu.trim()) return;
    setBusy(true);
    setErr(null);
    try {
      await ghiJson('/api/posts/' + bai.id + '/comments',
        { method: 'POST', body: JSON.stringify({ content: chu.trim() }) }, HD_OK);
      const moi = await layJson<DsBinhLuan>(
        `/api/posts/${bai.id}/comments?per_page=50`, HD_DS_BINH_LUAN);
      setDs(moi);
      setChu('');
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không gửi được trả lời.'));
    } finally {
      setBusy(false);
    }
  }

  const soTraLoi = ds ? ds.total : (bai.comment_count ?? 0);

  return (
    <li data-bai={bai.id} className="rounded-md border border-line p-3">
      <div className="flex flex-wrap items-baseline gap-x-3">
        <span className="text-body font-semibold text-ink">{bai.author_name || 'Ẩn danh'}</span>
        <span className="text-small text-ink-3">{khiNao(bai.created_at)}</span>
      </div>
      {bai.title && bai.title !== 'Trao đổi' && (
        <p className="mt-1 text-body font-semibold text-ink">{bai.title}</p>
      )}
      <p className="mt-1 whitespace-pre-wrap text-body text-ink-2">{bai.content}</p>
      <button
        type="button"
        onClick={onMo}
        disabled={!daGan}
        className="-mx-2 mt-2 inline-flex min-h-11 items-center px-2 text-small text-brand-ink underline"
      >
        {mo ? 'Thu lại' : soTraLoi > 0 ? `${soTraLoi} trả lời` : 'Trả lời'}
      </button>

      {mo && (
        <div className="mt-2 flex flex-col gap-2 border-t border-line pt-2">
          {(ds?.comments ?? []).map((c: BinhLuan) => (
            <div key={c.id} data-tra-loi={c.id} className="rounded-md bg-sunken px-3 py-2">
              <div className="flex flex-wrap items-baseline gap-x-3">
                <span className="text-small font-semibold text-ink">{c.author_name || 'Ẩn danh'}</span>
                <span className="text-small text-ink-3">{khiNao(c.created_at)}</span>
              </div>
              <p className="whitespace-pre-wrap text-body text-ink-2">{c.content}</p>
            </div>
          ))}
          <textarea
            value={chu}
            onChange={(e) => setChu(e.target.value)}
            rows={2}
            disabled={!daGan || busy}
            placeholder="Viết trả lời…"
            className="w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 py-2 text-input text-ink placeholder:text-ink-3/70"
          />
          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={() => void traLoi()} loading={busy} disabled={!daGan || !chu.trim()}>
              Gửi trả lời
            </Button>
            {err && <span className="text-small text-danger-ink">{err}</span>}
          </div>
        </div>
      )}
    </li>
  );
}
