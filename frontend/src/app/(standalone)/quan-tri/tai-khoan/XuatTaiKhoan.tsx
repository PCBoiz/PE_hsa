'use client';

import { useState } from 'react';

import ChonDinhDang, { dinhDangQs, type DinhDang } from '@/components/ChonDinhDang';
import { Button, Field, Modal } from '@/components/ui';
import { layJson, loiBatDuoc } from '@/lib/api';
import * as z from 'zod/mini';

/**
 * "Tải danh sách" tài khoản — Excel hoặc CSV, lọc THÊM theo đợt học, môn, ngày cấp tài
 * khoản (V-k, bảng TopHSA dòng 6: "bộ lọc thời gian / lớp / môn / khoá").
 *
 * Tệp = đúng tập đang nhìn (ô Tìm, Vai trò, Trạng thái, Lớp… — `loc`) CỘNG các điều kiện
 * trong hộp này. Máy chủ lọc bằng CÙNG hàm với màn hình (`build_user_filters`), nên tệp
 * không bao giờ lệch bảng. Hai danh sách chọn (đợt, môn) chỉ tải khi mở hộp — trang Tài
 * khoản mở hằng ngày, hộp này thì không.
 */
type Dot = { id: number; name: string; code?: string | null };
type Mon = { id: string; title: string };

const HD_DOT = z.looseObject({
  terms: z.array(z.looseObject({ id: z.number(), name: z.string(), code: z.optional(z.nullable(z.string())) })),
});
const HD_MON = z.looseObject({
  courses: z.array(z.looseObject({ id: z.string(), title: z.string() })),
});

const O_CHON =
  'min-h-11 w-full max-w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink';

export default function XuatTaiKhoan({ loc }: { loc: string }) {
  const [mo, setMo] = useState(false);
  const [dinhDang, setDinhDang] = useState<DinhDang>('xlsx');
  const [dot, setDot] = useState('');
  const [mon, setMon] = useState('');
  const [tu, setTu] = useState('');
  const [den, setDen] = useState('');
  const [ds, setDs] = useState<{ dot: Dot[]; mon: Mon[] } | null>(null);
  const [loi, setLoi] = useState<string | null>(null);

  async function moHop() {
    setMo(true);
    if (ds) return;
    try {
      const [d, m] = await Promise.all([
        layJson('/api/teach/terms', HD_DOT),
        layJson('/api/public/courses', HD_MON),
      ]);
      setDs({ dot: d.terms, mon: m.courses });
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Không tải được danh sách đợt học và môn'));
    }
  }

  const nguoc = !!tu && !!den && tu > den;
  const qs = [loc, dinhDangQs(dinhDang), dot && `term_id=${dot}`,
    mon && `course_id=${encodeURIComponent(mon)}`, tu && `tu=${tu}`, den && `den=${den}`]
    .filter(Boolean)
    .join('&');

  return (
    <>
      <Button variant="ghost" onClick={() => void moHop()}>
        Tải danh sách
      </Button>
      <Modal open={mo} onClose={() => setMo(false)} title="Tải danh sách tài khoản">
        <div className="flex flex-col gap-4">
          <p className="text-small text-ink-3">
            Tệp gồm các tài khoản khớp bộ lọc đang xem, thêm các điều kiện dưới đây (để trống = không lọc).
          </p>
          <ChonDinhDang value={dinhDang} onChange={setDinhDang} ten="dinh-dang-tai-khoan" />
          {loi && (
            <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">
              {loi}
            </p>
          )}
          <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,11rem),1fr))]">
            <label className="flex min-w-0 flex-col gap-2">
              <span className="text-label text-ink-3">Đợt học</span>
              <select value={dot} onChange={(e) => setDot(e.target.value)} className={O_CHON}>
                <option value="">Tất cả</option>
                {(ds?.dot ?? []).map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.code ? `${d.name} (${d.code})` : d.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex min-w-0 flex-col gap-2">
              <span className="text-label text-ink-3">Môn học</span>
              <select value={mon} onChange={(e) => setMon(e.target.value)} className={O_CHON}>
                <option value="">Tất cả</option>
                {(ds?.mon ?? []).map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.title}
                  </option>
                ))}
              </select>
            </label>
            <Field id="xuat-tk-tu" label="Cấp tài khoản từ ngày" type="date" value={tu} max={den || undefined}
              onChange={(e) => setTu(e.target.value)} />
            <Field id="xuat-tk-den" label="Cấp tài khoản đến ngày" type="date" value={den} min={tu || undefined}
              onChange={(e) => setDen(e.target.value)}
              error={nguoc ? '"Đến ngày" phải sau hoặc bằng "từ ngày".' : null} />
          </div>
          <p className="text-small text-ink-3">
            Đợt học và môn học tính theo lớp em ĐANG học.
          </p>
          <div>
            <a
              href={nguoc ? undefined : `/api/admin/export/users.csv?${qs}`}
              aria-disabled={nguoc || undefined}
              className="inline-flex min-h-11 items-center justify-center rounded-md bg-brand-fill px-4 text-small font-semibold text-white hover:brightness-110 aria-disabled:opacity-50"
            >
              Tải về
            </a>
          </div>
        </div>
      </Modal>
    </>
  );
}
