'use client';

import Link from 'next/link';
import { useState } from 'react';

import { Button, Chip, EmptyState } from '@/components/ui';
import { ghiJson, layJson, loiBatDuoc } from '@/lib/api';
import { useDaGan } from '@/lib/daGan';
import {
  HD_DANH_DAU,
  HD_TRANG,
  duongTrang,
  khiNao,
  ngayGio,
  type Dong,
  type DanhDau,
  type MotLoai,
  type Trang,
} from '@/lib/thongBao';

/**
 * TRANG "THÔNG BÁO" của người dùng (§61, bảng TopHSA dòng 27).
 *
 * Panel chuông chỉ giữ 30 dòng mới nhất và biến mất khi bấm ra ngoài — đủ cho "có gì mới",
 * không đủ cho "tuần trước cô nhắn gì". Trang này là chỗ xem lại: lọc theo loại, lọc chưa
 * đọc, và tải thêm cho tới hết.
 *
 * BA ĐIỀU ĐÁNG NÓI RÕ, vì mỗi điều đều là một cách hỏng đã thấy ở nơi khác trong repo:
 *
 * ① TẢI THÊM THEO KHOÁ, không theo số trang. Máy chủ trả `tiep` = id nhỏ nhất của trang
 *   vừa rồi, và trang kế xin `truoc=<id>`. Có thông báo mới chen vào giữa hai lần bấm thì
 *   phân trang theo số trang sẽ đẩy một dòng cũ xuống và người đọc thấy nó HAI lần —
 *   `tests_feed.py` có phép kiểm riêng cho đúng chuyện đó.
 *
 * ② ĐỔI BỘ LỌC LÀ TẢI LẠI TỪ ĐẦU, và dọn sạch danh sách trước. Giữ lại dòng cũ trong lúc
 *   chờ thì trong một nhịp màn hình đang hiện kết quả của bộ lọc TRƯỚC dưới cái nhãn của
 *   bộ lọc SAU — người dùng đọc số liệu sai mà không biết.
 *
 * ③ ĐÁNH DẤU ĐỌC / CHƯA ĐỌC chờ máy chủ trả lời rồi mới đổi màn. Bản đầu của nút "Báo hỏng
 *   bản ghi" (§72) đặt trạng thái TRƯỚC rồi `.catch(() => {})` — màn nói "đã xong" trong khi
 *   không có gì xảy ra, và phải mất một lượt soát mới thấy.
 *
 * Và một điều thứ tư, đo được chứ không suy ra: MỌI Ô LỌC KHOÁ TỚI KHI REACT GẮN XONG
 * (`useDaGan`). Trang này dựng sẵn ở máy chủ, nên ô lọc HIỆN RA trước khi JavaScript gắn
 * vào — bấm trong khoảng ấy thì không có gì xảy ra: không lời gọi mạng, `aria-pressed` không
 * đổi, không một dấu hiệu nào cho người bấm biết là họ vừa bấm vào hư không. Bộ đo
 * `do_thong_bao.mjs` gặp đúng chuyện đó ở bước lọc theo loại (bước đầu tiên nó bấm), rồi
 * những bước sau lại chạy tốt vì lúc ấy React đã gắn. Nút mờ đi một khoảnh khắc là câu trả
 * lời trung thực; một nút trông bấm được mà không làm gì thì không.
 */
export default function DanhSachThongBao({
  dauTien, loiTai,
}: { dauTien: Trang | null; loiTai: string | null }) {
  const [ds, setDs] = useState<Dong[]>(dauTien?.items ?? []);
  const [tiep, setTiep] = useState<number | null>(dauTien?.tiep ?? null);
  const [cacLoai, setCacLoai] = useState<MotLoai[]>(dauTien?.cacLoai ?? []);
  const [chuaDocTong, setChuaDocTong] = useState(dauTien?.unread ?? 0);
  const [loai, setLoai] = useState<string | null>(null);
  const [chiChuaDoc, setChiChuaDoc] = useState(false);
  const [dangTai, setDangTai] = useState(false);
  const [err, setErr] = useState<string | null>(loiTai);
  // Dòng đang chờ máy chủ trả lời — nút của riêng nó khoá lại, các dòng khác vẫn bấm được.
  const [dangDoi, setDangDoi] = useState<number | null>(null);
  const daGan = useDaGan();

  async function tai(truoc: number | null, l: string | null, cd: boolean) {
    setDangTai(true);
    setErr(null);
    try {
      const d = await layJson<Trang>(duongTrang(truoc, l, cd), HD_TRANG);
      setDs((cu) => (truoc ? [...cu, ...d.items] : d.items));
      setTiep(d.tiep ?? null);
      setChuaDocTong(d.unread);
      // `cacLoai` chỉ có ở trang đầu — máy chủ không đếm lại ở mỗi lần "tải thêm".
      if (d.cacLoai) setCacLoai(d.cacLoai);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không tải được thông báo. Thử lại sau ít phút.'));
    } finally {
      setDangTai(false);
    }
  }

  function doiLoc(l: string | null, cd: boolean) {
    setLoai(l);
    setChiChuaDoc(cd);
    setDs([]);            // ② dọn trước, đừng để nhãn mới đứng trên số liệu cũ
    setTiep(null);
    void tai(null, l, cd);
  }

  async function doiDaDoc(d: Dong) {
    if (dangDoi) return;
    setDangDoi(d.id);
    try {
      const duong = d.is_read
        ? `/api/notifications/feed/${d.id}/unread`
        : `/api/notifications/feed/${d.id}/read`;
      const kq = await ghiJson<DanhDau>(duong, { method: 'POST' }, HD_DANH_DAU); // ③ chờ máy chủ trước
      setDs((cu) => cu.map((r) => (r.id === d.id ? { ...r, is_read: !d.is_read } : r)));
      setChuaDocTong((n) => kq.unread ?? Math.max(0, n + (d.is_read ? 1 : -1)));
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không đổi được trạng thái. Thử lại sau ít phút.'));
    } finally {
      setDangDoi(null);
    }
  }

  async function docHet() {
    if (dangTai) return;
    setDangTai(true);
    try {
      await ghiJson('/api/notifications/feed/read-all', { method: 'POST' }, HD_DANH_DAU);
      setDs((cu) => cu.map((r) => ({ ...r, is_read: true })));
      setChuaDocTong(0);
      if (chiChuaDoc) doiLoc(loai, true);   // đang lọc "chưa đọc" thì danh sách phải rỗng đi
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không đánh dấu được. Thử lại sau ít phút.'));
    } finally {
      setDangTai(false);
    }
  }

  const rong = ds.length === 0 && !dangTai;

  return (
    <div data-khu="thong-bao">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => doiLoc(null, false)}
          aria-pressed={loai === null && !chiChuaDoc}
          disabled={!daGan}
          className={o(loai === null && !chiChuaDoc)}
        >
          Tất cả
        </button>
        <button
          type="button"
          onClick={() => doiLoc(loai, !chiChuaDoc)}
          aria-pressed={chiChuaDoc}
          disabled={!daGan}
          className={o(chiChuaDoc)}
        >
          Chưa đọc{chuaDocTong > 0 ? ` (${chuaDocTong})` : ''}
        </button>
        {cacLoai.map((l) => (
          <button
            key={l.loai}
            type="button"
            onClick={() => doiLoc(loai === l.loai ? null : l.loai, chiChuaDoc)}
            aria-pressed={loai === l.loai}
            disabled={!daGan}
            className={o(loai === l.loai)}
          >
            {/* Nhãn do máy chủ trả (RULES §7) — màn hình không giữ bảng mã nào. */}
            {l.nhan} ({l.so})
          </button>
        ))}
        {chuaDocTong > 0 && (
          <Button variant="ghost" size="sm" className="ml-auto" onClick={() => void docHet()} disabled={dangTai || !daGan}>
            Đánh dấu tất cả đã đọc
          </Button>
        )}
      </div>

      {err && (
        <p className="mb-3 rounded-xl bg-danger/10 px-4 py-3 text-small text-danger-ink" role="alert">
          {err}
        </p>
      )}

      {rong ? (
        <EmptyState
          title={chiChuaDoc ? 'Không có thông báo chưa đọc' : 'Chưa có thông báo nào'}
          hint={
            chiChuaDoc
              ? 'Mọi thông báo đều đã đọc.'
              : 'Bài tập mới, đổi lịch học và thông báo của trung tâm sẽ hiện ở đây.'
          }
        />
      ) : (
        <ul className="flex flex-col gap-2">
          {ds.map((d) => (
            <li
              key={d.id}
              data-id={d.id}
              data-doc={d.is_read ? 'roi' : 'chua'}
              className={`rounded-xl border p-4 ${d.is_read ? 'border-line bg-surface' : 'border-brand/30 bg-brand-soft/30'}`}
            >
              <div className="flex flex-wrap items-start gap-2">
                <Chip tone={d.is_read ? 'neutral' : 'brand'}>{d.loaiNhan}</Chip>
                <time className="text-small text-ink-3" dateTime={d.created_at ?? undefined} title={ngayGio(d.created_at)}>
                  {khiNao(d.created_at)}
                </time>
                {!d.is_read && <span className="text-small text-brand-ink">• chưa đọc</span>}
                <button
                  type="button"
                  onClick={() => void doiDaDoc(d)}
                  disabled={dangDoi === d.id || !daGan}
                  className="ml-auto text-small text-ink-3 underline underline-offset-2 hover:text-ink disabled:opacity-50"
                >
                  {d.is_read ? 'Đánh dấu chưa đọc' : 'Đánh dấu đã đọc'}
                </button>
              </div>
              <p className="mt-2 text-body font-medium text-ink">{d.title}</p>
              {d.body && <p className="mt-1 whitespace-pre-line text-small text-ink-2">{d.body}</p>}
              {d.link && (
                <Link href={d.link} className="mt-2 inline-block text-small text-brand-ink underline underline-offset-2">
                  Mở mục liên quan
                </Link>
              )}
            </li>
          ))}
        </ul>
      )}

      {tiep && (
        <div className="mt-4 flex justify-center">
          <Button variant="ghost" onClick={() => void tai(tiep, loai, chiChuaDoc)} disabled={dangTai}>
            {dangTai ? 'Đang tải…' : 'Xem thêm'}
          </Button>
        </div>
      )}
    </div>
  );
}

/** Ô lọc: cùng chiều cao chạm với nút thường (44px), khác nhau ở nền khi đang bật. */
function o(dangBat: boolean): string {
  return `min-h-11 rounded-full border px-4 text-small disabled:opacity-60 ${
    dangBat
      ? 'border-brand bg-brand-soft text-brand-ink'
      : 'border-line bg-surface text-ink-2 hover:border-brand hover:text-brand-ink'
  }`;
}
