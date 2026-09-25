'use client';

import { useState } from 'react';

import { Button, Chip } from '@/components/ui';
import { layJson, loiBatDuoc } from '@/lib/api';
import { lucVN } from '@/lib/gioVN';
import { nhanViec } from '@/lib/viecNhatKy';
import * as z from 'zod/mini';

/**
 * "Lịch sử thay đổi" của MỘT lớp — cho học vụ (V-n, bảng TopHSA dòng 4 + 10).
 *
 * Ai sửa lớp, thêm / cho rời / chuyển em, gán trợ giảng, tạo / sửa / huỷ buổi — mới nhất
 * trước. Đọc `GET /api/admin/classes/<id>/lich-su` (chỉ phần của lớp này; Nhật ký đầy đủ
 * vẫn chỉ quản trị viên xem). Tải khi MỞ khối, không tải lúc mở danh sách học viên: lịch
 * sử là thứ tra khi có chuyện, không phải thứ đọc mỗi lần. Giờ ghi là giờ VN ngây thơ →
 * `lucVN` (tách chuỗi, không qua `Date`).
 */
type Dong = {
  id: number;
  actorName: string | null;
  actorRole: string | null;
  action: string;
  summary: string | null;
  occurredAt: string | null;
};

const HD = z.looseObject({
  entries: z.array(z.looseObject({
    id: z.number(),
    actorName: z.nullable(z.string()),
    actorRole: z.nullable(z.string()),
    action: z.string(),
    summary: z.nullable(z.string()),
    occurredAt: z.nullable(z.string()),
  })),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
});

const VAI: Record<string, string> = { admin: 'Quản trị viên' };

export default function LichSuLop({ classId }: { classId: number }) {
  const [dong, setDong] = useState<Dong[] | null>(null);
  const [tong, setTong] = useState(0);
  const [trang, setTrang] = useState(0);
  const [dangTai, setDangTai] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);

  async function tai(p: number) {
    setDangTai(true);
    setLoi(null);
    try {
      const d = await layJson(`/api/admin/classes/${classId}/lich-su?page=${p}&per_page=20`, HD);
      setDong((cu) => (p === 1 ? d.entries : [...(cu ?? []), ...d.entries]));
      setTong(d.total);
      setTrang(p);
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Không tải được lịch sử của lớp'));
    } finally {
      setDangTai(false);
    }
  }

  return (
    <details
      className="mb-4 rounded-md border border-line bg-sunken"
      onToggle={(e) => {
        if ((e.currentTarget as HTMLDetailsElement).open && dong === null && !dangTai) void tai(1);
      }}
    >
      <summary className="flex min-h-11 cursor-pointer items-center px-3 text-label text-ink">
        Lịch sử thay đổi của lớp
      </summary>
      <div className="px-3 pb-3">
        {loi && (
          <p role="alert" className="mb-2 rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">
            {loi}
          </p>
        )}
        {dong === null ? (
          <p className="text-small text-ink-3">{dangTai ? 'Đang tải lịch sử…' : ''}</p>
        ) : dong.length === 0 ? (
          <p className="text-small text-ink-3">Lớp chưa có thay đổi nào được ghi.</p>
        ) : (
          <>
            <p className="mb-2 text-small text-ink-3">
              {tong} thay đổi — mới nhất ở trên. Điểm danh từng buổi xem ở sổ buổi học.
            </p>
            <ol aria-label="Các thay đổi của lớp, mới nhất trước" className="flex flex-col gap-2">
              {dong.map((d) => (
                <li key={d.id} className="rounded-md border border-line bg-surface px-3 py-2">
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <Chip>{nhanViec(d.action)}</Chip>
                    <span className="text-small text-ink-3">
                      {lucVN(d.occurredAt)} · {d.actorName || '(tài khoản đã xoá)'}
                      {d.actorRole ? ` (${VAI[d.actorRole] ?? d.actorRole})` : ''}
                    </span>
                  </div>
                  {d.summary && <p className="mt-1 text-small text-ink-2">{d.summary}</p>}
                </li>
              ))}
            </ol>
            {dong.length < tong && (
              <Button size="sm" variant="ghost" className="mt-2" loading={dangTai} onClick={() => void tai(trang + 1)}>
                Xem thêm
              </Button>
            )}
          </>
        )}
      </div>
    </details>
  );
}
