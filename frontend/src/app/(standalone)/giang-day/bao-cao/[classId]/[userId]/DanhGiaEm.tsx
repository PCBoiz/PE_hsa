'use client';

import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';
import * as z from 'zod/mini';

import { Button } from '@/components/ui';
import { ghiJson, loiBatDuoc } from '@/lib/api';
import { lucVN } from '@/lib/gioVN';
import type { HinhDang } from '@/lib/kiemDang';

/** `GET/PUT …/students/<u>/danh-gia` (`teaching/danh_gia.py`). Trợ giảng không có
 *  ba ô của giảng viên — trang này chỉ mở cho giảng viên trở lên nên chúng luôn có,
 *  nhưng vẫn để tuỳ chọn: thiếu thì khối ẩn phần ấy thay vì hiện ô trống ghi đè được. */
export type DanhGia = {
  canHoTro: boolean;
  lyDo: string | null;
  canHoTroAt: string | null;
  canHoTroBy: string | null;
  quyen: { nhanXet: boolean };
  teacherComment?: string | null;
  teacherCommentAt?: string | null;
  teacherCommentBy?: string | null;
  deXuatHuongHoc?: string | null;
  deXuatHuongHocAt?: string | null;
  deXuatHuongHocBy?: string | null;
};

const chu = z.nullable(z.string());
export const HD_DANH_GIA_TRINH_DUYET = z.looseObject({
  canHoTro: z.boolean(), lyDo: chu, canHoTroAt: chu, canHoTroBy: chu,
  quyen: z.looseObject({ nhanXet: z.boolean() }),
  teacherComment: z.optional(chu), teacherCommentAt: z.optional(chu), teacherCommentBy: z.optional(chu),
  deXuatHuongHoc: z.optional(chu), deXuatHuongHocAt: z.optional(chu), deXuatHuongHocBy: z.optional(chu),
}) satisfies HinhDang<DanhGia>;

const O = 'w-full rounded-md border border-line-input bg-sunken p-3 text-input text-ink focus:outline-2 focus:outline-offset-0 focus:outline-brand';

/** "bởi Cô Lan · 25/09/2026 20:15" — ai ghi, lúc nào. */
function dau(boi: string | null | undefined, luc: string | null | undefined) {
  if (!boi && !luc) return null;
  return [boi ? `bởi ${boi}` : null, luc ? lucVN(luc) : null].filter(Boolean).join(' · ');
}

/**
 * Đánh giá của giảng viên về em (kế hoạch v2 V-a + V-f — bảng TopHSA dòng 18).
 *
 * Ba ô, HAI mức riêng tư, nói rõ ngay dưới từng ô:
 *  · Nhận xét gửi phụ huynh — IN LÊN tờ báo cáo bên dưới (và đường dẫn phụ huynh mở).
 *  · Cần hỗ trợ + lý do — nội bộ: hiện ở "Việc hôm nay" của giảng viên và trợ giảng lớp.
 *  · Đề xuất hướng học — nội bộ, không in.
 * Chỉ gửi ô ĐÃ ĐỔI (máy chủ ghi người + lúc ghi theo từng nhóm ô). Lưu xong làm mới
 * trang để tờ báo cáo bên dưới in đúng nhận xét vừa ghi.
 */
export default function DanhGiaEm({ classId, userId, initial }: {
  classId: string;
  userId: string;
  initial: DanhGia;
}) {
  const router = useRouter();
  const [goc, setGoc] = useState(initial);
  const [nhanXet, setNhanXet] = useState(initial.teacherComment ?? '');
  const [canHoTro, setCanHoTro] = useState(initial.canHoTro);
  const [lyDo, setLyDo] = useState(initial.lyDo ?? '');
  const [huong, setHuong] = useState(initial.deXuatHuongHoc ?? '');
  const [dangLuu, setDangLuu] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);
  const [daLuu, setDaLuu] = useState(false);
  const dangGui = useRef(false);

  const coNhanXet = goc.quyen.nhanXet && goc.teacherComment !== undefined;
  const body: Record<string, unknown> = {};
  if (coNhanXet && nhanXet !== (goc.teacherComment ?? '')) body.teacherComment = nhanXet;
  if (coNhanXet && huong !== (goc.deXuatHuongHoc ?? '')) body.deXuatHuongHoc = huong;
  if (canHoTro !== goc.canHoTro || (canHoTro && lyDo !== (goc.lyDo ?? ''))) {
    body.canHoTro = canHoTro;
    if (canHoTro) body.lyDo = lyDo;
  }
  const conDoi = Object.keys(body).length > 0;

  async function luu() {
    if (!conDoi || dangGui.current) return;
    dangGui.current = true;
    setDangLuu(true);
    setLoi(null);
    try {
      const d = await ghiJson(`/api/teach/classes/${classId}/students/${userId}/danh-gia`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }, HD_DANH_GIA_TRINH_DUYET);
      setGoc(d);
      setNhanXet(d.teacherComment ?? '');
      setCanHoTro(d.canHoTro);
      setLyDo(d.lyDo ?? '');
      setHuong(d.deXuatHuongHoc ?? '');
      setDaLuu(true);
      if ('teacherComment' in body) router.refresh();
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Không lưu được đánh giá của em'));
    } finally {
      dangGui.current = false;
      setDangLuu(false);
    }
  }

  const doi = <T,>(dat: (v: T) => void) => (v: T) => { dat(v); setDaLuu(false); };

  return (
    <section aria-labelledby="danh-gia-em" className="rounded-lg border border-line bg-surface p-4 print:hidden">
      <h2 id="danh-gia-em" className="text-section text-ink">Đánh giá của giảng viên</h2>
      <form
        className="mt-3 grid gap-4"
        onSubmit={(e) => {
          e.preventDefault();
          void luu();
        }}
      >
        {coNhanXet && (
          <label className="flex flex-col gap-2">
            <span className="text-label text-ink-3">Nhận xét gửi phụ huynh</span>
            <textarea
              value={nhanXet}
              onChange={(e) => doi(setNhanXet)(e.target.value)}
              rows={3}
              maxLength={2000}
              placeholder="Ví dụ: Con đi học đều, tiến bộ rõ ở phần tỉ lệ; cần luyện thêm tốc độ làm bài."
              className={O}
            />
            <span className="text-small text-ink-3">
              In lên tờ báo cáo bên dưới và trang phụ huynh mở bằng đường dẫn.
              {dau(goc.teacherCommentBy, goc.teacherCommentAt) && <> Lần ghi cuối: {dau(goc.teacherCommentBy, goc.teacherCommentAt)}.</>}
            </span>
          </label>
        )}

        <fieldset className="flex flex-col gap-2">
          <legend className="text-label text-ink-3">Cần hỗ trợ</legend>
          <label className="flex min-h-11 items-center gap-3 text-body text-ink">
            <input
              type="checkbox"
              checked={canHoTro}
              onChange={(e) => doi(setCanHoTro)(e.target.checked)}
              className="size-5 accent-brand"
            />
            Đánh dấu em cần hỗ trợ
          </label>
          {canHoTro && (
            <label className="flex flex-col gap-2">
              <span className="text-label text-ink-3">Lý do</span>
              <input
                value={lyDo}
                onChange={(e) => doi(setLyDo)(e.target.value)}
                maxLength={500}
                placeholder="Ví dụ: vắng hai buổi liền, điểm kiểm tra giảm"
                className={`min-h-11 ${O}`}
              />
            </label>
          )}
          <span className="text-small text-ink-3">
            Nội bộ — hiện ở “Việc hôm nay” của giảng viên và trợ giảng lớp, không in lên tờ phụ huynh.
            {goc.canHoTro && dau(goc.canHoTroBy, goc.canHoTroAt) && <> Đánh dấu {dau(goc.canHoTroBy, goc.canHoTroAt)}.</>}
          </span>
        </fieldset>

        {coNhanXet && (
          <label className="flex flex-col gap-2">
            <span className="text-label text-ink-3">Đề xuất hướng học</span>
            <textarea
              value={huong}
              onChange={(e) => doi(setHuong)(e.target.value)}
              rows={2}
              maxLength={1000}
              placeholder="Ví dụ: ôn lại phần hình học trước, rồi mới luyện đề tốc độ."
              className={O}
            />
            <span className="text-small text-ink-3">Nội bộ trung tâm — không in, không gửi phụ huynh.</span>
          </label>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" size="sm" loading={dangLuu} disabled={!conDoi}>
            {dangLuu ? 'Đang lưu…' : 'Lưu đánh giá'}
          </Button>
          <span className="text-small text-ink-3" aria-live="polite">
            {loi ? <span role="alert" className="text-danger">{loi}</span> : daLuu && !conDoi ? 'Đã lưu' : ''}
          </span>
        </div>
      </form>
    </section>
  );
}
