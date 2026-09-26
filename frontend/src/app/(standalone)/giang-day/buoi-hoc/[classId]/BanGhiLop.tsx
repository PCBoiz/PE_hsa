'use client';

import { useEffect, useState } from 'react';

import { Button, Card, CardHead } from '@/components/ui';
import { apiFetch, loiBatDuoc } from '@/lib/api';

/**
 * AI ĐÃ XEM LẠI BẢN GHI — và một nút để nhắc em chưa xem (§72, 26/09/2026).
 *
 * Bảng phân rã dòng 22 (trợ giảng · quản lý record Zoom): *"Học sinh đã xem/chưa
 * xem · Nhắc học sinh chưa xem"*; dòng 21: *"Theo dõi việc xem record"*.
 *
 * Đặt ở màn Buổi học vì đây đã là chỗ dán link bản ghi — người vừa dán xong là
 * người muốn biết ngay có ai mở không, không phải đi tìm một trang khác.
 *
 * "Đã mở" chứ không phải "đã xem xong": bản ghi nằm trên Zoom hoặc Drive, hệ
 * thống chỉ biết em đã bấm vào link. Chữ trên màn nói đúng bấy nhiêu — một con
 * số hứa nhiều hơn nó đo được thì lần sau không ai tin nó nữa.
 *
 * Khối này IM LẶNG khi lớp chưa buổi nào có bản ghi: chưa có gì để theo dõi thì
 * đừng chiếm chỗ trên màn (luật gọt chữ, `docs/HUONG_GIAO_DIEN_2026-09-26.md`).
 */
type Buoi = {
  sessionId: number;
  startsAt: string;
  topic: string | null;
  recordingUrl: string;
  daMo: number;
  chuaMo: number;
  dsChuaMo: { id: number; name: string }[];
};

/**
 * "24/09". Tự ghép chứ không nhờ `toLocaleDateString('vi-VN')`: đo trên màn thật
 * 26/09 thấy nó nhả ra "24-09" — dữ liệu vùng miền của trình duyệt quyết định
 * dấu phân cách, và nó khác máy này với máy khác. Ngày trong sản phẩm này viết
 * bằng dấu `/` ở mọi màn.
 */
function ngay(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  const p = (n: number) => String(n).padStart(2, '0');
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}`;
}

type Thieu = { sessionId: number; startsAt: string; topic: string | null };

export default function BanGhiLop({ classId }: { classId: number }) {
  const [ds, setDs] = useState<Buoi[] | null>(null);
  const [thieu, setThieu] = useState<Thieu[]>([]);
  const [loi, setLoi] = useState<string | null>(null);
  const [dangNhac, setDangNhac] = useState<number | null>(null);
  const [daNhac, setDaNhac] = useState<Record<number, number>>({});

  // Tải trong effect theo đúng khuôn của màn này: `alive` chặn setState sau khi
  // component đã tháo, và mọi setState nằm SAU một `await` nên không phải lượt
  // vẽ đồng bộ mà `react-hooks/set-state-in-effect` cấm.
  useEffect(() => {
    let alive = true;
    void (async () => {
      try {
        const r = await apiFetch(`/api/teach/classes/${classId}/ban-ghi`);
        if (!r.ok) return;
        const d = (await r.json()) as { buoi: Buoi[]; thieuBanGhi?: Thieu[] };
        if (alive) {
          setDs(d.buoi ?? []);
          setThieu(d.thieuBanGhi ?? []);
        }
      } catch {
        /* Khối phụ: hỏng thì im, đừng chắn màn Buổi học. */
      }
    })();
    return () => {
      alive = false;
    };
  }, [classId]);

  async function nhac(b: Buoi) {
    setDangNhac(b.sessionId);
    setLoi(null);
    try {
      const r = await apiFetch(`/api/teach/classes/${classId}/ban-ghi/${b.sessionId}/nhac`, { method: 'POST' });
      if (!r.ok) throw new Error('Chưa nhắc được.');
      const d = (await r.json()) as { daNhac: number };
      setDaNhac((t) => ({ ...t, [b.sessionId]: d.daNhac }));
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Chưa nhắc được. Thử lại sau ít phút.'));
    } finally {
      setDangNhac(null);
    }
  }

  if (!ds || (ds.length === 0 && thieu.length === 0)) return null;

  return (
    <Card>
      {/* Không câu phụ dưới tiêu đề: cột "3/12 em đã mở" tự nói nó là cái gì
          (luật gọt chữ §3.2 — bỏ câu giải thích không ngăn được lỗi nào). */}
      <CardHead title="Bản ghi buổi học" />
      {loi && <p role="alert" className="text-small text-danger-ink">{loi}</p>}
      <ul className="flex flex-col gap-3">
        {ds.map((b) => (
          <li key={b.sessionId} className="flex flex-wrap items-center gap-x-4 gap-y-2">
            <span className="min-w-[4.5rem] font-semibold text-ink">{ngay(b.startsAt)}</span>
            <span className="text-small text-ink-3">
              {b.daMo}/{b.daMo + b.chuaMo} em đã mở
            </span>
            {b.chuaMo > 0 && (
              <>
                <details className="text-small text-ink-3">
                  <summary className="cursor-pointer">Chưa mở: {b.chuaMo}</summary>
                  <p className="mt-1">{b.dsChuaMo.map((e) => e.name).join(' · ')}</p>
                </details>
                {daNhac[b.sessionId] === undefined ? (
                  <Button
                    variant="ghost"
                    onClick={() => void nhac(b)}
                    disabled={dangNhac === b.sessionId}
                  >
                    {dangNhac === b.sessionId ? 'Đang nhắc…' : 'Nhắc em chưa mở'}
                  </Button>
                ) : (
                  <span className="text-small text-ink-3">Đã nhắc {daNhac[b.sessionId]} em</span>
                )}
              </>
            )}
          </li>
        ))}
      </ul>
      {/* Buổi đã học mà chưa ai dán link. Không nêu ra thì một buổi bị quên cứ
          nằm im — không ai thấy cái KHÔNG có mặt trên màn. */}
      {thieu.length > 0 && (
        <p className="text-small text-ink-3">
          Chưa có bản ghi: {thieu.map((t) => ngay(t.startsAt)).join(' · ')}
        </p>
      )}
    </Card>
  );
}
