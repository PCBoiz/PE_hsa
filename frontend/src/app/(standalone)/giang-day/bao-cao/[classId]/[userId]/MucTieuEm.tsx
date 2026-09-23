'use client';

import { useRef, useState } from 'react';

import { Button } from '@/components/ui';
import { ghiJson, loiBatDuoc } from '@/lib/api';
import type { HinhDang } from '@/lib/kiemDang';
import * as z from 'zod/mini';

export type MucTieu = { studentCode: string | null; studyGoal: string | null; aspiration: string | null };

/* Hình dạng phản hồi PATCH (`teaching/ho_so.py::MucTieuHocVienView`). Máy chủ
   trả lại hai ô SAU khi ghi — cắt 500 ký tự, rỗng thành null — và form lấy lại
   đúng bản đó, không giữ chữ đã gõ. */
const HD_DA_LUU = z.looseObject({
  studyGoal: z.nullable(z.string()),
  aspiration: z.nullable(z.string()),
}) satisfies HinhDang<Omit<MucTieu, 'studentCode'>>;

/**
 * Mục tiêu + nguyện vọng của em — giảng viên cập nhật ngay trên tờ báo cáo.
 *
 * Đặt Ở ĐÂY vì đây là trang giảng viên mở cho TỪNG em (dòng 14 của bảng yêu cầu
 * TopHSA: "cập nhật hồ sơ học sinh trong lớp — mục tiêu, nguyện vọng"). Cùng
 * cổng với tờ báo cáo: trợ giảng không vào được trang này, và API cũng chặn họ.
 *
 * KHÔNG in, không nằm trong tờ gửi phụ huynh (`print:hidden`): đây là ghi chú
 * nội bộ. Đưa nó vào tờ gửi về nhà là một quyết định riêng, chưa ai chốt.
 */
export default function MucTieuEm({ classId, userId, initial }: {
  classId: string;
  userId: string;
  initial: MucTieu;
}) {
  const [goc, setGoc] = useState({ studyGoal: initial.studyGoal ?? '', aspiration: initial.aspiration ?? '' });
  const [muc, setMuc] = useState(goc.studyGoal);
  const [nv, setNv] = useState(goc.aspiration);
  const [dangLuu, setDangLuu] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);
  const [daLuu, setDaLuu] = useState(false);
  const dangGui = useRef(false);

  const conDoi = muc !== goc.studyGoal || nv !== goc.aspiration;

  async function luu() {
    if (!conDoi || dangGui.current) return;
    dangGui.current = true;
    setDangLuu(true);
    setLoi(null);
    try {
      // Chỉ gửi ô đã đổi — cùng lý do với form hồ sơ của học vụ: gửi cả hai là
      // đè lên điều học vụ vừa sửa ở ô mình không động tới.
      const body: Record<string, string> = {};
      if (muc !== goc.studyGoal) body.studyGoal = muc;
      if (nv !== goc.aspiration) body.aspiration = nv;
      const d = await ghiJson(`/api/teach/classes/${classId}/students/${userId}/profile`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }, HD_DA_LUU);
      const moi = { studyGoal: d.studyGoal ?? '', aspiration: d.aspiration ?? '' };
      setGoc(moi);
      setMuc(moi.studyGoal);
      setNv(moi.aspiration);
      setDaLuu(true);
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Không lưu được mục tiêu của em'));
    } finally {
      dangGui.current = false;
      setDangLuu(false);
    }
  }

  const o = 'w-full rounded-md border border-line-input bg-sunken p-3 text-input text-ink focus:outline-2 focus:outline-offset-0 focus:outline-brand';

  return (
    <section
      aria-labelledby="muc-tieu-em"
      className="rounded-lg border border-line bg-surface p-4 print:hidden"
    >
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h2 id="muc-tieu-em" className="text-section text-ink">Mục tiêu và nguyện vọng</h2>
        {initial.studentCode && <span className="font-mono text-small text-ink-3">{initial.studentCode}</span>}
      </div>
      <p className="mt-1 text-small text-ink-3">Ghi chú nội bộ trung tâm — không in, không gửi phụ huynh.</p>
      <form
        className="mt-3 grid gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          void luu();
        }}
      >
        <label className="flex flex-col gap-2">
          <span className="text-label text-ink-3">Mục tiêu học tập</span>
          <textarea
            value={muc}
            onChange={(e) => { setMuc(e.target.value); setDaLuu(false); }}
            rows={2}
            maxLength={500}
            placeholder="Ví dụ: đạt 100 điểm HSA đợt tháng 3"
            className={o}
          />
        </label>
        <label className="flex flex-col gap-2">
          <span className="text-label text-ink-3">Nguyện vọng trường / ngành</span>
          <textarea
            value={nv}
            onChange={(e) => { setNv(e.target.value); setDaLuu(false); }}
            rows={2}
            maxLength={500}
            placeholder="Ví dụ: ĐH Bách khoa Hà Nội — CNTT"
            className={o}
          />
        </label>
        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" size="sm" loading={dangLuu} disabled={!conDoi}>
            {dangLuu ? 'Đang lưu…' : 'Lưu'}
          </Button>
          <span className="text-small text-ink-3" aria-live="polite">
            {loi ? <span role="alert" className="text-danger">{loi}</span> : daLuu && !conDoi ? 'Đã lưu' : ''}
          </span>
        </div>
      </form>
    </section>
  );
}
