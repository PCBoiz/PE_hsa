'use client';

import { useEffect, useRef, useState } from 'react';

import { Button, Card, CardHead } from '@/components/ui';
import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';

/**
 * Ngày nghỉ của MỘT đợt học — thứ mà "Sinh lịch cả kỳ" bỏ qua ở mọi lớp.
 *
 * ── VÌ SAO LƯU THEO ĐỢT VÀ KHÔNG TỰ TÍNH (anh Sơn chốt 13/09/2026) ────────
 *
 * Bốn lễ dương lịch cố định (01/01, 30/04, 01/05, 02/09) thì hệ thống gợi ý.
 * Tết Nguyên đán, Giỗ Tổ Hùng Vương (âm lịch) và ngày nghỉ liền kề / nghỉ bù thì
 * Nhà nước công bố TỪNG NĂM — đoán sai một ngày là cả lớp vào phòng học trống,
 * nên ngày ấy do học vụ nhập theo thông báo chính thức.
 *
 * Backend: `backend/teaching/terms.py` (TermHolidaysView), schema §46.
 */
type NgayNghi = { id: number; ngay: string; ten: string };
type DuLieu = {
  dot: { id: number; name: string; startsOn: string | null; endsOn: string | null };
  ngayNghi: NgayNghi[];
  goiY: { ngay: string; ten: string }[];
};

function ngayDu(iso: string) {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

const O_NHAP =
  'min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink placeholder:text-ink-3/70';

export default function NgayNghiDot({ termId, onClose }: { termId: number; onClose: () => void }) {
  const [d, setD] = useState<DuLieu | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [ngay, setNgay] = useState('');
  const [ten, setTen] = useState('');
  const [dangChay, setDangChay] = useState(false);
  // Tăng sau mỗi lần thêm/xoá để effect đọc lại — một nguồn sự thật duy nhất là
  // máy chủ, không tự vá danh sách ở máy rồi mong nó khớp.
  const [lan, setLan] = useState(0);
  const dangGui = useRef(false);
  const khung = useRef<HTMLDivElement>(null);

  // Khối mở ra DƯỚI bảng đợt: bấm "Ngày nghỉ" ở một dòng cuối bảng mà khối hiện
  // ngoài tầm nhìn thì trông như nút không làm gì. `nearest` không giật trang
  // khi khối vốn đã nằm trong khung nhìn.
  useEffect(() => {
    khung.current?.scrollIntoView({ block: 'nearest' });
  }, []);

  useEffect(() => {
    let huy = false;
    apiFetch(`/api/admin/terms/${termId}/holidays`)
      .then(async (r) => {
        const body: unknown = await r.json().catch(() => null);
        if (huy) return;
        if (r.ok) setD(body as DuLieu);
        else setLoi(errorText(r.status, body));
      })
      .catch((e: unknown) => {
        if (!huy) setLoi(loiBatDuoc(e, 'Không đọc được ngày nghỉ của đợt.'));
      });
    return () => {
      huy = true;
    };
  }, [termId, lan]);

  async function gui(init: RequestInit, duong = ''): Promise<boolean> {
    if (dangGui.current) return false;
    dangGui.current = true;
    setDangChay(true);
    setLoi(null);
    try {
      const r = await apiFetch(`/api/admin/terms/${termId}/holidays${duong}`, init);
      const body: unknown = await r.json().catch(() => null);
      if (!r.ok) {
        setLoi(errorText(r.status, body));
        return false;
      }
      setLan((n) => n + 1);
      return true;
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Chưa lưu được. Thử lại sau ít phút.'));
      return false;
    } finally {
      dangGui.current = false;
      setDangChay(false);
    }
  }

  const post = (than: unknown): RequestInit => ({
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(than),
  });

  /** Chỉ xoá ô nhập khi máy chủ ĐÃ nhận: lỗi (trùng ngày, ngoài đợt) mà ô trống
   *  trơn thì người ta phải gõ lại đúng thứ cần sửa. */
  async function themTay() {
    if (await gui(post({ ngay, ten: ten.trim() }))) {
      setNgay('');
      setTen('');
    }
  }

  return (
    <div ref={khung} className="scroll-mt-4">
    <Card>
      <CardHead
        title={d ? `Ngày nghỉ · ${d.dot.name}` : 'Ngày nghỉ của đợt'}
        hint="Sinh lịch cả kỳ sẽ BỎ các ngày này ở mọi lớp của đợt."
        chiTiet="Tết Nguyên đán, Giỗ Tổ Hùng Vương và ngày nghỉ bù do Nhà nước công bố từng năm — nhập theo thông báo chính thức, hệ thống không tự tính."
        action={
          <Button variant="ghost" onClick={onClose}>
            Đóng
          </Button>
        }
      />

      {loi && (
        <p role="alert" className="mb-3 rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">
          {loi}
        </p>
      )}

      {!d ? (
        !loi && <p className="text-small text-ink-3">Đang tải…</p>
      ) : (
        <div className="flex flex-col gap-5">
          <section className="flex flex-col gap-2">
            <h3 className="text-label text-ink-3">Đã khai ({d.ngayNghi.length})</h3>
            {d.ngayNghi.length === 0 ? (
              <p className="text-small text-ink-3">Chưa khai ngày nghỉ nào — lớp sinh lịch lúc này sẽ có buổi cả vào ngày lễ.</p>
            ) : (
              <ul className="flex flex-col rounded-md border border-line">
                {d.ngayNghi.map((n) => (
                  <li
                    key={n.id}
                    className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-line/50 px-3 py-2 last:border-b-0"
                  >
                    <span className="font-mono tabular-nums text-ink">{ngayDu(n.ngay)}</span>
                    <span className="min-w-0 flex-1 text-body text-ink-2">{n.ten}</span>
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={dangChay}
                      onClick={() => {
                        // Hỏi lại vì hậu quả nằm ở chỗ khác: lớp nào sinh lịch
                        // SAU lần xoá này sẽ có buổi vào đúng ngày ấy.
                        if (confirm(`Xoá ngày nghỉ ${ngayDu(n.ngay)} (${n.ten})? Lớp sinh lịch sau đó sẽ có buổi vào ngày này.`)) {
                          void gui({ method: 'DELETE' }, `/${n.id}`);
                        }
                      }}
                    >
                      Xoá
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {d.goiY.length === 0 && (
            // Hướng dẫn hứa "hệ thống gợi ý lễ"; đợt không chứa lễ nào thì phải
            // NÓI ra, không thì học vụ đi tìm cái nút không có (rà 20/09/2026).
            <p className="text-small text-ink-3">
              Không có lễ dương lịch cố định (01/01, 30/04, 01/05, 02/09) rơi vào đợt này — chỉ cần khai
              Tết, Giỗ Tổ và ngày nghỉ bù nếu có.
            </p>
          )}
          {d.goiY.length > 0 && (
            <section className="flex flex-col gap-2">
              <h3 className="text-label text-ink-3">Gợi ý — lễ dương lịch cố định rơi vào đợt này</h3>
              <div className="flex flex-wrap items-center gap-2">
                {d.goiY.map((g) => (
                  <Button key={g.ngay} size="sm" variant="ghost" disabled={dangChay} onClick={() => void gui(post(g))}>
                    + {ngayDu(g.ngay)} {g.ten}
                  </Button>
                ))}
                {d.goiY.length > 1 && (
                  <Button size="sm" disabled={dangChay} onClick={() => void gui(post({ items: d.goiY }))}>
                    Thêm cả {d.goiY.length} ngày
                  </Button>
                )}
              </div>
            </section>
          )}

          <section className="flex flex-col gap-2">
            <h3 className="text-label text-ink-3">Khai thêm (Tết, Giỗ Tổ, nghỉ bù…)</h3>
            <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,180px),1fr))]">
              <label className="flex flex-col gap-1">
                <span className="text-label text-ink-3">Ngày</span>
                <input
                  type="date"
                  value={ngay}
                  min={d.dot.startsOn ?? undefined}
                  max={d.dot.endsOn ?? undefined}
                  onChange={(e) => setNgay(e.target.value)}
                  className={O_NHAP}
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-label text-ink-3">Tên ngày nghỉ</span>
                <input
                  value={ten}
                  onChange={(e) => setTen(e.target.value)}
                  placeholder="Tết Nguyên đán"
                  className={O_NHAP}
                />
              </label>
            </div>
            <div>
              <Button
                loading={dangChay}
                disabled={!ngay || !ten.trim()}
                onClick={() => void themTay()}
              >
                Thêm ngày nghỉ
              </Button>
            </div>
          </section>
        </div>
      )}
    </Card>
    </div>
  );
}
