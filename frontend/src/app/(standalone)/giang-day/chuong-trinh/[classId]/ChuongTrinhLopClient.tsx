'use client';

import Link from 'next/link';
import { useRef, useState } from 'react';

import {
  Button,
  Card,
  CardHead,
  Chip,
  EmptyState,
  TableWrap,
  Tbody,
  Td,
  Th,
  Thead,
  Tile,
  TileRow,
  Tr,
} from '@/components/ui';
import { ghiJson, layJson, loiBatDuoc } from '@/lib/api';
import {
  HD_CT_LOP,
  HD_NHAN_KHUNG,
  HD_OK,
  phanTram,
  type CtLop,
  type NhanKhung,
} from '@/lib/chuongTrinh';
import { lucVN } from '@/lib/gioVN';

const O_CHON =
  'min-h-11 w-full rounded-md border border-line-input bg-sunken px-3 text-input text-ink focus:outline-2 focus:outline-brand';

/**
 * Màn "Chương trình lớp". Nhận khung = xem trước (`dryRun`) rồi mới lưu — luật gắn ở
 * `chuong_trinh/dich_vu.py::nhan_khung`: buổi đã gắn không bị đè, buổi huỷ và buổi bù
 * bỏ qua, tên buổi chỉ điền ô đang trống. Gắn tay từng buổi: ô chọn ở bảng buổi học.
 */
export default function ChuongTrinhLopClient({ initial }: { initial: CtLop }) {
  const [d, setD] = useState<CtLop>(initial);
  const [err, setErr] = useState<string | null>(null);
  const [bao, setBao] = useState<string | null>(null);
  const [chon, setChon] = useState<number | ''>(initial.luaChon?.[0]?.versionId ?? '');
  const [xemTruoc, setXemTruoc] = useState<NhanKhung | null>(null);
  const dangGui = useRef(false);
  const lopId = d.class.id;

  function chay(viec: () => Promise<void>, macDinh: string): void {
    if (dangGui.current) return;
    dangGui.current = true;
    void (async () => {
      try {
        await viec();
        setErr(null);
      } catch (e) {
        setErr(loiBatDuoc(e, macDinh));
        setBao(null);
      } finally {
        dangGui.current = false;
      }
    })();
  }
  const napLai = async () => setD(await layJson(`/api/teach/classes/${lopId}/chuong-trinh`, HD_CT_LOP));

  const nhan = (dryRun: boolean) => ghiJson(`/api/admin/classes/${lopId}/chuong-trinh`,
    { method: 'PUT', body: JSON.stringify({ versionId: chon, dryRun }) }, HD_NHAN_KHUNG);

  const td = d.tienDo;

  return (
    <div className="space-y-6">
      {err && (
        <div role="alert" className="rounded-md border border-danger bg-danger-soft px-4 py-3 text-body text-danger-ink">{err}</div>
      )}
      {bao && !err && (
        <p role="status" className="rounded-md bg-success/10 px-4 py-3 text-body text-success-ink">{bao}</p>
      )}

      {!d.khung ? (
        <EmptyState
          title="Lớp chưa nhận khung chương trình"
          hint={d.quyen.nhanKhung
            ? 'Chọn một khung bên dưới để gắn các buổi học của lớp vào khung.'
            : 'Nhờ học vụ cho lớp nhận khung — khi ấy tiến độ và sổ đầu bài mới tính được.'}
        />
      ) : (
        <Card>
          <CardHead
            title={d.khung.name}
            hint={td
              ? `Chậm khi trễ từ ${td.nguong.treBuoi} buổi, hoặc xong dưới ${td.nguong.tiLe}% phần phải xong.`
              : undefined}
            action={td && (
              <Chip tone={td.cham ? 'bad' : 'good'}>{td.cham ? 'Chậm tiến độ' : 'Đúng tiến độ'}</Chip>
            )}
          />
          {td && (
            <TileRow>
              <Tile label="Đã dạy (cả khung)" value={phanTram(td.pct)} />
              <Tile label="Kế hoạch tới hôm nay" value={phanTram(td.keHoachPct)} />
              <Tile label="Trễ so với kế hoạch" tone={td.cham ? 'warn' : 'neutral'}
                value={td.treBuoi == null ? '—' : td.treBuoi <= 0 ? 'Không trễ' : `${td.treBuoi} buổi`} />
              <Tile label="Buổi đã dạy chưa ghi sổ" tone={td.chuaGhiSo ? 'warn' : 'good'} value={td.chuaGhiSo} />
            </TileRow>
          )}
        </Card>
      )}

      {d.quyen.nhanKhung && d.luaChon && (
        <Card>
          <CardHead title={d.khung ? 'Đổi khung' : 'Nhận khung'} hint="Xem trước để biết buổi nào gắn vào đâu, rồi mới lưu." />
          {d.luaChon.length === 0 ? (
            <p className="text-body text-ink-3">
              Chưa có khung nào đang dùng cho môn của lớp.{' '}
              <Link href="/giao-trinh/khung-chuong-trinh" className="text-brand-ink underline">Soạn khung</Link>
            </p>
          ) : (
            <div className="flex flex-wrap items-end gap-3">
              <div className="min-w-0 flex-1 basis-64">
                <label htmlFor="chon-khung" className="text-label text-ink-3">Khung đang dùng</label>
                <select id="chon-khung" className={`mt-2 ${O_CHON}`} value={chon}
                  onChange={(e) => { setChon(Number(e.target.value)); setXemTruoc(null); }}>
                  {d.luaChon.map((v) => (
                    <option key={v.versionId} value={v.versionId}>
                      {v.name}{v.courseTitle ? ` — ${v.courseTitle}` : ''} ({v.soBuoi} buổi)
                    </option>
                  ))}
                </select>
              </div>
              <Button variant="ghost" disabled={!chon}
                onClick={() => chay(async () => { setXemTruoc(await nhan(true)); setBao(null); }, 'Không xem trước được.')}>
                Xem trước
              </Button>
            </div>
          )}
          {xemTruoc && (
            <div className="mt-4 space-y-2 text-body text-ink-2">
              <p>
                Sẽ gắn <b>{xemTruoc.ganMoi.length}</b> buổi học vào khung “{xemTruoc.khung.name}”.
                {xemTruoc.giuNguyen > 0 && ` Giữ nguyên ${xemTruoc.giuNguyen} buổi đã gắn.`}
                {xemTruoc.doiBan && ` Chuyển ${xemTruoc.dichSang} buổi đã gắn sang buổi cùng số của khung mới.`}
                {xemTruoc.dienTen > 0 && ` Điền tên cho ${xemTruoc.dienTen} buổi đang để trống.`}
              </p>
              {(xemTruoc.boQuaBuoiHuy > 0 || xemTruoc.boQuaBuoiBu > 0) && (
                <p className="text-small text-ink-3">
                  Bỏ qua {xemTruoc.boQuaBuoiHuy} buổi đã huỷ và {xemTruoc.boQuaBuoiBu} buổi học bù.
                </p>
              )}
              {xemTruoc.buoiThua.length > 0 && (
                <p className="text-small text-warning-ink">
                  {xemTruoc.buoiThua.length} buổi học không có buổi khung tương ứng (từ {lucVN(xemTruoc.buoiThua[0].startsAt)}).
                </p>
              )}
              {xemTruoc.khungThieu.length > 0 && (
                <p className="text-small text-warning-ink">
                  {xemTruoc.khungThieu.length} buổi khung chưa có buổi học để gắn (từ buổi {xemTruoc.khungThieu[0].soBuoi}) —
                  tạo thêm buổi học rồi nhận khung lại.
                </p>
              )}
              <Button onClick={() => chay(async () => {
                const r = await nhan(false);
                setXemTruoc(null);
                setBao(`Đã nhận khung “${r.khung.name}”: gắn ${r.ganMoi.length} buổi.`);
                await napLai();
              }, 'Không nhận khung được.')}>
                Nhận khung
              </Button>
            </div>
          )}
        </Card>
      )}

      {d.khung && (
        <Card>
          <CardHead title="Buổi học và sổ đầu bài" hint="Buổi khung gắn sai thì chọn lại ở cột Buổi khung." />
          <TableWrap caption="Buổi học của lớp và buổi khung tương ứng">
            <Thead>
              <Tr>
                <Th>Ngày</Th>
                <Th>Buổi khung</Th>
                <Th>Sổ đầu bài</Th>
              </Tr>
            </Thead>
            <Tbody>
              {d.buoi.map((b) => (
                <Tr key={b.id}>
                  <Td label="Ngày">
                    <span className="text-ink">{lucVN(b.startsAt)}</span>
                    {b.status === 'cancelled' && <span className="ml-2"><Chip tone="bad">Đã huỷ</Chip></span>}
                    {b.makeupFor != null && <span className="ml-2 text-small text-ink-3">(học bù)</span>}
                  </Td>
                  <Td label="Buổi khung">
                    <label htmlFor={`gan-${b.id}`} className="sr-only">Buổi khung của buổi {lucVN(b.startsAt)}</label>
                    <select id={`gan-${b.id}`} className={O_CHON}
                      value={b.lechBan ? '' : (b.syllabusSessionId ?? '')}
                      onChange={(e) => {
                        const v = e.target.value ? Number(e.target.value) : null;
                        chay(async () => {
                          await ghiJson(`/api/teach/sessions/${b.id}/chuong-trinh`,
                            { method: 'PATCH', body: JSON.stringify({ syllabusSessionId: v }) }, HD_OK);
                          await napLai();
                        }, 'Không gắn được buổi.');
                      }}>
                      <option value="">— Không gắn —</option>
                      {d.buoiKhung.map((k) => (
                        <option key={k.id} value={k.id}>Buổi {k.soBuoi}: {k.name}</option>
                      ))}
                    </select>
                  </Td>
                  <Td label="Sổ đầu bài">
                    {b.soDauBai ? (
                      <Link href={`/giang-day/so-dau-bai/${b.id}`} className="text-brand-ink underline">
                        {b.soDauBai.xong} đã dạy{b.soDauBai.motPhan ? `, ${b.soDauBai.motPhan} một phần` : ''}
                        {b.soDauBai.chua ? `, ${b.soDauBai.chua} chưa dạy` : ''}
                      </Link>
                    ) : b.started && b.status !== 'cancelled' ? (
                      <Link href={`/giang-day/so-dau-bai/${b.id}`} className="font-medium text-warning-ink underline">
                        Chưa ghi — ghi ngay
                      </Link>
                    ) : (
                      <span className="text-ink-3">—</span>
                    )}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </TableWrap>
        </Card>
      )}

      {d.khung && d.buoiKhung.length > 0 && (
        <Card>
          <CardHead title="Nội dung từng buổi khung" hint="Phần trăm là phần nội dung đã dạy, theo sổ đầu bài." />
          <ol className="space-y-2">
            {d.buoiKhung.map((k) => {
              const gan = d.buoi.filter((b) => b.syllabusSessionId === k.id && !b.lechBan);
              return (
                <li key={k.id} className="rounded-md border border-line p-3">
                  <div className="flex flex-wrap items-baseline gap-x-3">
                    <h3 className="text-body font-semibold text-ink">Buổi {k.soBuoi}: {k.name}</h3>
                    <span className="text-small text-ink-3">
                      {gan.length ? gan.map((b) => lucVN(b.startsAt).slice(0, 5)).join(', ') : 'chưa có buổi học'}
                    </span>
                    <span className="ml-auto">
                      <Chip tone={k.pctDaDay == null ? 'neutral' : k.pctDaDay >= 100 ? 'good' : k.pctDaDay > 0 ? 'warn' : 'neutral'}>
                        {k.pctDaDay == null ? 'Chưa có nội dung' : `Đã dạy ${k.pctDaDay}%`}
                      </Chip>
                    </span>
                  </div>
                  {k.items.length > 0 && (
                    <p className="mt-1 text-small text-ink-2">{k.items.map((i) => i.title).join(' · ')}</p>
                  )}
                </li>
              );
            })}
          </ol>
        </Card>
      )}

      {d.khung && d.tungEm.length > 0 && (
        <Card>
          <CardHead title="Từng em" hint="Phần chương trình em đã học, chỉ tính buổi em có mặt hoặc đi muộn." />
          <ul className="grid gap-2 sm:grid-cols-2">
            {d.tungEm.map((e) => (
              <li key={e.userId} className="flex items-center justify-between gap-3 rounded-md bg-sunken px-3 py-2">
                <span className="min-w-0 truncate text-body text-ink">{e.name}</span>
                <span className="font-mono text-body tabular-nums text-ink-2">{phanTram(e.pct)}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
