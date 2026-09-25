'use client';

import { useRef, useState } from 'react';

import { Button, Chip, TableWrap, Tbody, Td, Th, Thead, Tr } from '@/components/ui';
import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';
import { kiemHinhDang } from '@/lib/kiemDang';
import * as z from 'zod/mini';

/**
 * "Nhập từ tệp mẫu" — xếp cả danh sách học viên vào MỘT lớp từ tệp .xlsx / .csv (V-j, bảng
 * TopHSA dòng 4: "import danh sách theo biểu mẫu").
 *
 * Tải mẫu → điền → chọn tệp → "Kiểm tra tệp" (máy chủ XEM TRƯỚC từng dòng, chưa ghi gì) →
 * "Nhập vào lớp". Em có sẵn tài khoản (khớp mã HSA / email / số điện thoại) được thêm vào
 * lớp; em chưa có được cấp tài khoản mới — mật khẩu tạm hiện MỘT lần ở bảng kết quả.
 * Máy chủ: `teaching/nhap_hoc_vien.py`.
 */
type Dong = {
  line: number;
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  status: 'tao_moi' | 'them_vao_lop' | 'da_trong_lop' | 'loi';
  reason?: string | null;
  studentCode?: string | null;
  tempPassword?: string | null;
};
type KetQua = {
  rows: Dong[];
  dem: Record<Dong['status'], number>;
  warnings?: string[];
  dryRun: boolean;
};

const HD = z.looseObject({
  rows: z.array(z.looseObject({
    line: z.number(),
    name: z.optional(z.nullable(z.string())),
    email: z.optional(z.nullable(z.string())),
    phone: z.optional(z.nullable(z.string())),
    status: z.enum(['tao_moi', 'them_vao_lop', 'da_trong_lop', 'loi']),
    reason: z.optional(z.nullable(z.string())),
    studentCode: z.optional(z.nullable(z.string())),
    tempPassword: z.optional(z.nullable(z.string())),
  })),
  dem: z.looseObject({ tao_moi: z.number(), them_vao_lop: z.number(), da_trong_lop: z.number(), loi: z.number() }),
  warnings: z.optional(z.array(z.string())),
  dryRun: z.boolean(),
});

const NHAN: Record<Dong['status'], { chu: string; tone: 'good' | 'brand' | 'neutral' | 'bad' }> = {
  tao_moi: { chu: 'Cấp tài khoản mới', tone: 'good' },
  them_vao_lop: { chu: 'Thêm vào lớp', tone: 'brand' },
  da_trong_lop: { chu: 'Đã trong lớp', tone: 'neutral' },
  loi: { chu: 'Lỗi', tone: 'bad' },
};

export default function NhapTuTep({
  classId,
  ngayVao,
  onXong,
}: {
  classId: number;
  /** Ngày vào lớp chọn ở ô bên trên (lớp đã khai giảng) — rỗng = hôm nay. */
  ngayVao: string;
  onXong: (cau: string) => void;
}) {
  const [tep, setTep] = useState<File | null>(null);
  const [kq, setKq] = useState<KetQua | null>(null);
  const [dangGui, setDangGui] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);
  const khoa = useRef(false);

  async function gui(xemTruoc: boolean) {
    if (!tep || khoa.current) return;
    khoa.current = true;
    setDangGui(true);
    setLoi(null);
    try {
      const fd = new FormData();
      fd.append('tep', tep);
      fd.append('dry_run', xemTruoc ? '1' : '0');
      if (ngayVao) fd.append('joined_at', ngayVao);
      const duong = `/api/admin/classes/${classId}/nhap-hoc-vien`;
      const r = await apiFetch(duong, { method: 'POST', body: fd });
      const than = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, than));
      const d = kiemHinhDang(duong, than, r.status, HD);
      if (!d.ok) throw new Error(d.message);
      setKq(d.data);
      if (!xemTruoc) {
        const n = d.data.dem.tao_moi + d.data.dem.them_vao_lop;
        onXong(`Đã nhập ${n} học viên vào lớp (${d.data.dem.tao_moi} tài khoản mới).`);
      }
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Không đọc được tệp'));
    } finally {
      khoa.current = false;
      setDangGui(false);
    }
  }

  const soNhap = kq && kq.dryRun ? kq.dem.tao_moi + kq.dem.them_vao_lop : 0;
  const coMatKhau = kq && !kq.dryRun && kq.rows.some((d) => d.tempPassword);

  return (
    <section aria-labelledby={`nhap-tep-${classId}`} className="mb-4 rounded-md border border-line bg-sunken p-3">
      <h3 id={`nhap-tep-${classId}`} className="text-label text-ink">
        Nhập học viên từ tệp mẫu
      </h3>
      <p className="mt-1 text-small text-ink-3">
        Mỗi dòng một em: họ và tên, email, số điện thoại — hoặc chỉ mã học viên với em đã có tài khoản.
        Tối đa 50 em mỗi tệp.
      </p>
      <div className="mt-3 flex flex-wrap items-end gap-2">
        <a
          href={`/api/admin/classes/${classId}/nhap-hoc-vien/mau`}
          className="inline-flex min-h-11 items-center rounded-md border border-line px-4 text-small font-semibold text-ink-2 hover:border-brand hover:text-brand-ink"
        >
          Tải tệp mẫu (.xlsx)
        </a>
        <label className="flex min-w-0 flex-col gap-1">
          <span className="text-label text-ink-3">Tệp danh sách (.xlsx hoặc .csv)</span>
          <input
            type="file"
            accept=".xlsx,.csv"
            onChange={(e) => {
              setTep(e.target.files?.[0] ?? null);
              setKq(null);
              setLoi(null);
            }}
            className="min-h-11 max-w-full text-small text-ink file:mr-3 file:min-h-11 file:rounded-md file:border file:border-line file:bg-surface file:px-3 file:text-ink"
          />
        </label>
        <Button variant="ghost" disabled={!tep} loading={dangGui} onClick={() => void gui(true)}>
          Kiểm tra tệp
        </Button>
        {kq?.dryRun && (
          <Button disabled={soNhap === 0} loading={dangGui} onClick={() => void gui(false)}>
            {soNhap ? `Nhập ${soNhap} em vào lớp` : 'Không có dòng nào nhập được'}
          </Button>
        )}
      </div>

      {loi && (
        <p role="alert" className="mt-3 rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">
          {loi}
        </p>
      )}
      {kq?.warnings?.map((w) => (
        <p key={w} className="mt-3 rounded-md bg-warning/10 px-3 py-2 text-small text-warning-ink">
          {w}
        </p>
      ))}

      {kq && (
        <div className="mt-3">
          <p className="mb-2 text-body text-ink">
            {kq.dryRun ? 'Kết quả kiểm tra (chưa ghi gì): ' : 'Đã nhập: '}
            {kq.dem.tao_moi} tài khoản mới, {kq.dem.them_vao_lop} em có sẵn thêm vào lớp,{' '}
            {kq.dem.da_trong_lop} em đã trong lớp, {kq.dem.loi} dòng lỗi.
          </p>
          {coMatKhau && (
            <p className="mb-2 rounded-md bg-warning/10 px-3 py-2 text-small text-warning-ink">
              Chép mật khẩu tạm dưới đây ngay — hệ thống không lưu lại dạng đọc được, rời trang là mất.
            </p>
          )}
          <TableWrap caption="Từng dòng của tệp danh sách">
            <Thead>
              <tr>
                <Th align="right">Dòng</Th>
                <Th>Học viên</Th>
                <Th>Liên hệ</Th>
                <Th>Kết quả</Th>
                {coMatKhau && <Th>Mật khẩu tạm</Th>}
              </tr>
            </Thead>
            <Tbody>
              {kq.rows.map((d) => (
                <Tr key={d.line} dim={d.status === 'loi' || d.status === 'da_trong_lop'}>
                  <Td label="Dòng" num>
                    {d.line}
                  </Td>
                  <Td label="Học viên">
                    <span className="block">{d.name || '—'}</span>
                    {d.studentCode && <span className="block text-small text-ink-3">{d.studentCode}</span>}
                  </Td>
                  <Td label="Liên hệ" muted>
                    <span className="block break-all">{d.email || ''}</span>
                    <span className="block">{d.phone || ''}</span>
                  </Td>
                  <Td label="Kết quả">
                    <span className="flex flex-col items-start gap-1 max-sm:items-end">
                      <Chip tone={NHAN[d.status].tone}>{NHAN[d.status].chu}</Chip>
                      {d.status === 'loi' && d.reason && <span className="text-small text-ink-3">{d.reason}</span>}
                    </span>
                  </Td>
                  {coMatKhau && (
                    <Td label="Mật khẩu tạm">
                      {d.tempPassword ? (
                        <code className="font-mono text-small text-ink select-all">{d.tempPassword}</code>
                      ) : (
                        '—'
                      )}
                    </Td>
                  )}
                </Tr>
              ))}
            </Tbody>
          </TableWrap>
        </div>
      )}
    </section>
  );
}
