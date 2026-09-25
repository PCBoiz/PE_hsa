'use client';

import { useCallback, useRef, useState } from 'react';

import {
  Button,
  Card,
  CardHead,
  Chip,
  EmptyState,
  Field,
  TableWrap,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
} from '@/components/ui';
import { ghiJson, layJson, loiBatDuoc } from '@/lib/api';
import {
  HD_CAY,
  HD_MUC_LUC,
  HD_OK,
  HD_TAO,
  type Cay,
  type MucLuc,
  type PhienBan,
} from '@/lib/chuongTrinh';

/**
 * Bộ soạn khung chương trình: chọn môn → các phiên bản → mở một bản ra sửa.
 *
 * Luật phiên bản ở máy chủ (`courseadmin/syllabus.py`): chỉ bản NHÁP sửa được; "Tạo bản
 * mới" chép bản đang chọn thành bản nháp CÙNG CHUỖI; xuất bản thay bản đang dùng của chuỗi
 * (lớp đã nhận bản cũ giữ bản cũ); bản đang có lớp dùng không xoá được. Màn này không
 * kiểm lại các luật ấy — chỉ ẩn nút vô nghĩa và in câu lỗi của máy chủ.
 */
const O_CHON =
  'min-h-11 w-full rounded-md border border-line-input bg-sunken px-3 text-input text-ink focus:outline-2 focus:outline-brand';

function tone(status: string): 'brand' | 'good' | 'neutral' {
  if (status === 'nhap') return 'brand';
  if (status === 'xuat_ban') return 'good';
  return 'neutral';
}

export default function KhungClient({ initial, loi }: { initial: MucLuc | null; loi: string | null }) {
  const [muc, setMuc] = useState<MucLuc | null>(initial);
  const [err, setErr] = useState<string | null>(loi);
  const [bao, setBao] = useState<string | null>(null);
  const [monId, setMonId] = useState<string>(
    () => initial?.mon.find((m) => m.versions.length)?.id ?? initial?.mon[0]?.id ?? '',
  );
  const [cay, setCay] = useState<Cay | null>(null);
  const [tenMoi, setTenMoi] = useState('');
  const dangGui = useRef(false);

  const mon = muc?.mon.find((m) => m.id === monId) ?? null;

  const napMucLuc = useCallback(async () => {
    setMuc(await layJson('/api/admin/chuong-trinh/khung', HD_MUC_LUC));
  }, []);
  const moBan = useCallback(async (id: number) => {
    setCay(await layJson(`/api/admin/syllabus/${id}`, HD_CAY));
  }, []);

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

  const ghi = (path: string, method: string, body?: unknown) =>
    ghiJson(path, { method, body: body === undefined ? undefined : JSON.stringify(body) }, HD_OK);

  /** Sau mỗi lượt sửa: nạp lại mục lục (số buổi) và cây đang mở. */
  async function napLai(id?: number) {
    await napMucLuc();
    if (id ?? cay?.id) await moBan((id ?? cay?.id) as number);
  }

  function taoKhung() {
    const ten = tenMoi.trim();
    if (!ten || !mon) return;
    chay(async () => {
      const r = await ghiJson(`/api/admin/courses/${encodeURIComponent(mon.id)}/syllabus`,
        { method: 'POST', body: JSON.stringify({ name: ten }) }, HD_TAO);
      setTenMoi('');
      setBao(`Đã tạo bản nháp "${ten}". Thêm buổi rồi xuất bản.`);
      await napLai(r.id);
    }, 'Không tạo được khung.');
  }

  function taoBanMoi(v: PhienBan) {
    chay(async () => {
      const r = await ghiJson(`/api/admin/courses/${encodeURIComponent(monId)}/syllabus`,
        { method: 'POST', body: JSON.stringify({ name: v.name, duplicateFrom: v.id }) }, HD_TAO);
      setBao(`Đã chép "${v.name}" thành một bản nháp mới — sửa xong thì xuất bản.`);
      await napLai(r.id);
    }, 'Không tạo được bản mới.');
  }

  function xuatBan(v: PhienBan) {
    const dangDung = mon?.versions.find((x) => x.chuoi === v.chuoi && x.status === 'xuat_ban');
    const cau = dangDung
      ? `Xuất bản "${v.name}"? Bản đang dùng sẽ chuyển sang "Đã thay"; lớp đã nhận bản cũ vẫn giữ bản cũ.`
      : `Xuất bản "${v.name}"? Sau khi xuất bản không sửa được nữa, lớp mới nhận được khung này.`;
    if (!window.confirm(cau)) return;
    chay(async () => {
      await ghi(`/api/admin/syllabus/${v.id}`, 'PUT', { status: 'xuat_ban' });
      setBao(`Đã xuất bản "${v.name}".`);
      await napLai(v.id);
    }, 'Không xuất bản được.');
  }

  function xoaBan(v: PhienBan) {
    if (!window.confirm(`Xoá hẳn "${v.name}" cùng mọi buổi của nó?`)) return;
    chay(async () => {
      await ghi(`/api/admin/syllabus/${v.id}`, 'DELETE');
      if (cay?.id === v.id) setCay(null);
      setBao(`Đã xoá "${v.name}".`);
      await napMucLuc();
    }, 'Không xoá được.');
  }

  const coNhapCungChuoi = (v: PhienBan) =>
    !!mon?.versions.some((x) => x.chuoi === v.chuoi && x.status === 'nhap');

  return (
    <main className="mx-auto max-w-6xl px-4 pb-8 pt-[calc(var(--topbar-h)+1.5rem)]">
      <h1 className="text-title text-ink">Khung chương trình theo buổi</h1>
      <p className="mt-1 text-body text-ink-2">
        Buổi nào học gì, trọng số từng nội dung. Chỉ sửa được bản nháp; xuất bản rồi lớp mới nhận được.
      </p>

      {err && (
        <div role="alert" className="mt-4 rounded-md border border-danger bg-danger-soft px-4 py-3 text-body text-danger-ink">
          {err}
        </div>
      )}
      {bao && !err && (
        <p role="status" className="mt-4 rounded-md bg-success/10 px-4 py-3 text-body text-success-ink">{bao}</p>
      )}

      {!muc ? null : (
        <Card className="mt-6">
          <CardHead title="Các khung của môn" hint="Mỗi môn có thể có nhiều khung, ví dụ lớp nhóm và lớp gia sư." />
          <div className="max-w-md">
            <label htmlFor="chon-mon" className="text-label text-ink-3">Môn</label>
            <select
              id="chon-mon"
              className={`mt-2 ${O_CHON}`}
              value={monId}
              onChange={(e) => { setMonId(e.target.value); setCay(null); setBao(null); }}
            >
              {muc.mon.map((m) => (
                <option key={m.id} value={m.id}>{m.title}</option>
              ))}
            </select>
          </div>

          {mon && mon.versions.length === 0 && (
            <p className="mt-4 text-body text-ink-3">Môn này chưa có khung nào. Tạo khung đầu tiên ở ô bên dưới.</p>
          )}
          {mon && mon.versions.length > 0 && (
            <div className="mt-4">
            <TableWrap caption="Các phiên bản khung của môn">
                <Thead>
                  <Tr>
                    <Th>Khung</Th>
                    <Th>Trạng thái</Th>
                    <Th>Số buổi</Th>
                    <Th>Lớp đang theo</Th>
                    <Th><span className="sr-only">Thao tác</span></Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {mon.versions.map((v) => (
                    <Tr key={v.id}>
                      <Td label="Khung">
                        <span className="font-medium text-ink">{v.name}</span>
                        {v.isDemo && <span className="ml-2 text-small text-ink-3">(mẫu)</span>}
                      </Td>
                      <Td label="Trạng thái"><Chip tone={tone(v.status)}>{v.statusLabel}</Chip></Td>
                      <Td label="Số buổi" num>{v.soBuoi}</Td>
                      <Td label="Lớp đang theo" num>{v.soLop}</Td>
                      <Td label="Thao tác">
                        <span className="flex flex-wrap gap-2">
                          <Button size="sm" variant={cay?.id === v.id ? 'primary' : 'ghost'}
                            onClick={() => chay(() => moBan(v.id), 'Không mở được bản này.')}>
                            {v.status === 'nhap' ? 'Sửa' : 'Xem'}
                          </Button>
                          {v.status === 'nhap' && (
                            <Button size="sm" onClick={() => xuatBan(v)}>Xuất bản</Button>
                          )}
                          {v.status !== 'nhap' && !coNhapCungChuoi(v) && (
                            <Button size="sm" variant="ghost" onClick={() => taoBanMoi(v)}>Tạo bản mới</Button>
                          )}
                          {v.soLop === 0 && (
                            <Button size="sm" variant="ghost-danger" onClick={() => xoaBan(v)}>Xoá</Button>
                          )}
                        </span>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
            </TableWrap>
            </div>
          )}

          {mon && (
            <form
              className="mt-6 flex flex-wrap items-end gap-3"
              onSubmit={(e) => { e.preventDefault(); taoKhung(); }}
            >
              <div className="min-w-0 flex-1 basis-64">
                <Field id="ten-khung-moi" label="Tên khung mới" value={tenMoi}
                  placeholder="Ví dụ: Luyện Toán HSA 24 buổi"
                  onChange={(e) => setTenMoi(e.target.value)} />
              </div>
              <Button type="submit" disabled={!tenMoi.trim()}>Tạo khung</Button>
            </form>
          )}
        </Card>
      )}

      {cay && muc && (
        <BanSoan
          key={cay.id}
          cay={cay}
          loaiMuc={muc.loaiMuc}
          chay={chay}
          ghi={ghi}
          napLai={() => napLai()}
        />
      )}
    </main>
  );
}

type Ghi = (path: string, method: string, body?: unknown) => Promise<unknown>;
type Chay = (viec: () => Promise<void>, macDinh: string) => void;

function BanSoan({
  cay, loaiMuc, chay, ghi, napLai,
}: {
  cay: Cay;
  loaiMuc: { ma: string; nhan: string }[];
  chay: Chay;
  ghi: Ghi;
  napLai: () => Promise<void>;
}) {
  const nhap = cay.status === 'nhap';
  const [ten, setTen] = useState(cay.name);
  const [buoiMoi, setBuoiMoi] = useState({ name: '', durationMinutes: '', homework: '' });
  const nhanLoai = Object.fromEntries(loaiMuc.map((l) => [l.ma, l.nhan]));
  const tongW = cay.sessions.reduce((a, s) => a + s.items.reduce((b, i) => b + i.weight, 0), 0);

  function themBuoi() {
    if (!buoiMoi.name.trim()) return;
    chay(async () => {
      await ghi(`/api/admin/syllabus/${cay.id}/sessions`, 'POST', {
        name: buoiMoi.name.trim(),
        durationMinutes: buoiMoi.durationMinutes ? Number(buoiMoi.durationMinutes) : null,
        homework: buoiMoi.homework.trim() || null,
      });
      setBuoiMoi({ name: '', durationMinutes: '', homework: '' });
      await napLai();
    }, 'Không thêm được buổi.');
  }

  return (
    <Card className="mt-6">
      <CardHead
        title={cay.name}
        hint={nhap
          ? `Bản nháp · ${cay.sessions.length} buổi · tổng trọng số ${tongW}`
          : `Đã xuất bản · ${cay.sessions.length} buổi — muốn sửa thì bấm "Tạo bản mới" ở bảng trên.`}
      />
      {nhap && (
        <form className="mb-4 flex flex-wrap items-end gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            chay(async () => { await ghi(`/api/admin/syllabus/${cay.id}`, 'PUT', { name: ten.trim() }); await napLai(); },
              'Không đổi được tên.');
          }}>
          <div className="min-w-0 flex-1 basis-64">
            <Field id={`ten-ban-${cay.id}`} label="Tên khung" value={ten} onChange={(e) => setTen(e.target.value)} />
          </div>
          <Button type="submit" variant="ghost" disabled={!ten.trim() || ten.trim() === cay.name}>Đổi tên</Button>
        </form>
      )}

      {cay.sessions.length === 0 ? (
        <EmptyState title="Chưa có buổi nào" hint="Thêm buổi đầu tiên ở ô bên dưới." />
      ) : (
        <ol className="space-y-3">
          {cay.sessions.map((s, i) => (
            <BuoiKhung key={s.id} so={i + 1} buoi={s} nhap={nhap} nhanLoai={nhanLoai}
              loaiMuc={loaiMuc} chay={chay} ghi={ghi} napLai={napLai} />
          ))}
        </ol>
      )}

      {nhap && (
        <form className="mt-6 grid gap-3 border-t border-line pt-4 sm:grid-cols-[2fr_1fr]"
          onSubmit={(e) => { e.preventDefault(); themBuoi(); }}>
          <Field id="buoi-moi-ten" label={`Buổi ${cay.sessions.length + 1} — tên buổi`} value={buoiMoi.name}
            onChange={(e) => setBuoiMoi({ ...buoiMoi, name: e.target.value })} />
          <Field id="buoi-moi-phut" label="Thời lượng (phút)" type="number" min={1} value={buoiMoi.durationMinutes}
            onChange={(e) => setBuoiMoi({ ...buoiMoi, durationMinutes: e.target.value })} />
          <div className="sm:col-span-2">
            <Field id="buoi-moi-btvn" label="Bài về nhà (không bắt buộc)" value={buoiMoi.homework}
              onChange={(e) => setBuoiMoi({ ...buoiMoi, homework: e.target.value })} />
          </div>
          <div><Button type="submit" disabled={!buoiMoi.name.trim()}>Thêm buổi</Button></div>
        </form>
      )}
    </Card>
  );
}

function BuoiKhung({
  so, buoi, nhap, nhanLoai, loaiMuc, chay, ghi, napLai,
}: {
  so: number;
  buoi: Cay['sessions'][number];
  nhap: boolean;
  nhanLoai: Record<string, string>;
  loaiMuc: { ma: string; nhan: string }[];
  chay: Chay;
  ghi: Ghi;
  napLai: () => Promise<void>;
}) {
  const [sua, setSua] = useState(false);
  const [f, setF] = useState({
    name: buoi.name, durationMinutes: buoi.durationMinutes ? String(buoi.durationMinutes) : '',
    homework: buoi.homework ?? '',
  });
  const [muc, setMuc] = useState({ kind: loaiMuc[0]?.ma ?? 'chu_de', title: '', weight: '1' });
  const [lieu, setLieu] = useState({ title: '', fileUrl: '' });
  const idp = `bk-${buoi.id}`;

  return (
    <li className="rounded-md border border-line p-3">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h3 className="text-body font-semibold text-ink">Buổi {so}: {buoi.name}</h3>
        {buoi.durationMinutes && <span className="text-small text-ink-3">{buoi.durationMinutes} phút</span>}
        {nhap && (
          <span className="ml-auto flex gap-2">
            <Button size="sm" variant="ghost" onClick={() => setSua(!sua)}>{sua ? 'Đóng' : 'Sửa buổi'}</Button>
            <Button size="sm" variant="ghost-danger" onClick={() => {
              if (!window.confirm(`Xoá buổi ${so} "${buoi.name}"?`)) return;
              chay(async () => { await ghi(`/api/admin/syllabus-sessions/${buoi.id}`, 'DELETE'); await napLai(); },
                'Không xoá được buổi.');
            }}>Xoá buổi</Button>
          </span>
        )}
      </div>
      {buoi.homework && <p className="mt-1 text-small text-ink-2">Bài về nhà: {buoi.homework}</p>}

      {sua && (
        <form className="mt-3 grid gap-3 sm:grid-cols-[2fr_1fr]" onSubmit={(e) => {
          e.preventDefault();
          chay(async () => {
            await ghi(`/api/admin/syllabus-sessions/${buoi.id}`, 'PUT', {
              name: f.name.trim(),
              durationMinutes: f.durationMinutes ? Number(f.durationMinutes) : null,
              homework: f.homework.trim() || null,
            });
            setSua(false);
            await napLai();
          }, 'Không lưu được buổi.');
        }}>
          <Field id={`${idp}-ten`} label="Tên buổi" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />
          <Field id={`${idp}-phut`} label="Thời lượng (phút)" type="number" min={1} value={f.durationMinutes}
            onChange={(e) => setF({ ...f, durationMinutes: e.target.value })} />
          <div className="sm:col-span-2">
            <Field id={`${idp}-btvn`} label="Bài về nhà" value={f.homework} onChange={(e) => setF({ ...f, homework: e.target.value })} />
          </div>
          <div><Button type="submit" disabled={!f.name.trim()}>Lưu buổi</Button></div>
        </form>
      )}

      {buoi.items.length > 0 && (
        <ul className="mt-2 space-y-1">
          {buoi.items.map((it) => (
            <li key={it.id} className="flex flex-wrap items-center gap-2 text-body text-ink">
              <Chip>{nhanLoai[it.kind] ?? it.kind}</Chip>
              <span className="min-w-0 flex-1">{it.title}</span>
              <span className="text-small text-ink-3">trọng số {it.weight}</span>
              {nhap && (
                <Button size="sm" variant="ghost-danger" aria-label={`Xoá nội dung ${it.title}`} onClick={() =>
                  chay(async () => { await ghi(`/api/admin/syllabus-items/${it.id}`, 'DELETE'); await napLai(); },
                    'Không xoá được nội dung.')}>
                  Xoá
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
      {buoi.items.length === 0 && (
        <p className="mt-2 text-small text-warning-ink">Buổi chưa có nội dung — tiến độ không tính được cho buổi này.</p>
      )}

      {buoi.materials.length > 0 && (
        <ul className="mt-2 space-y-1">
          {buoi.materials.map((m) => (
            <li key={m.id} className="flex flex-wrap items-center gap-2 text-small text-ink-2">
              <span>Học liệu:</span>
              {m.fileUrl ? (
                <a href={m.fileUrl} target="_blank" rel="noreferrer" className="text-brand-ink underline">{m.title}</a>
              ) : (
                <span>{m.title}</span>
              )}
              {nhap && (
                <Button size="sm" variant="ghost-danger" aria-label={`Xoá học liệu ${m.title}`} onClick={() =>
                  chay(async () => { await ghi(`/api/admin/syllabus-materials/${m.id}`, 'DELETE'); await napLai(); },
                    'Không xoá được học liệu.')}>
                  Xoá
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}

      {nhap && (
        <details className="mt-3">
          <summary className="inline-flex min-h-11 cursor-pointer items-center text-small font-medium text-brand-ink">
            Thêm nội dung hoặc học liệu
          </summary>
          <form className="mt-2 grid gap-3 sm:grid-cols-[1fr_2fr_1fr_auto] sm:items-end" onSubmit={(e) => {
            e.preventDefault();
            chay(async () => {
              await ghi(`/api/admin/syllabus-sessions/${buoi.id}/items`, 'POST', {
                kind: muc.kind, title: muc.title.trim(), weight: muc.weight ? Number(muc.weight) : 1,
              });
              setMuc({ ...muc, title: '' });
              await napLai();
            }, 'Không thêm được nội dung.');
          }}>
            <div className="flex flex-col gap-2">
              <label htmlFor={`${idp}-loai`} className="text-label text-ink-3">Loại</label>
              <select id={`${idp}-loai`} className={O_CHON} value={muc.kind}
                onChange={(e) => setMuc({ ...muc, kind: e.target.value })}>
                {loaiMuc.map((l) => <option key={l.ma} value={l.ma}>{l.nhan}</option>)}
              </select>
            </div>
            <Field id={`${idp}-muc`} label="Nội dung" value={muc.title} onChange={(e) => setMuc({ ...muc, title: e.target.value })} />
            <Field id={`${idp}-w`} label="Trọng số" type="number" min={0.5} step={0.5} value={muc.weight}
              onChange={(e) => setMuc({ ...muc, weight: e.target.value })} />
            <Button type="submit" disabled={!muc.title.trim()}>Thêm</Button>
          </form>
          <form className="mt-3 grid gap-3 sm:grid-cols-[2fr_2fr_auto] sm:items-end" onSubmit={(e) => {
            e.preventDefault();
            chay(async () => {
              await ghi(`/api/admin/syllabus-sessions/${buoi.id}/materials`, 'POST', {
                title: lieu.title.trim(), fileUrl: lieu.fileUrl.trim() || null,
              });
              setLieu({ title: '', fileUrl: '' });
              await napLai();
            }, 'Không thêm được học liệu.');
          }}>
            <Field id={`${idp}-lieu`} label="Tên học liệu" value={lieu.title} onChange={(e) => setLieu({ ...lieu, title: e.target.value })} />
            <Field id={`${idp}-link`} label="Đường dẫn (không bắt buộc)" type="url" value={lieu.fileUrl}
              onChange={(e) => setLieu({ ...lieu, fileUrl: e.target.value })} />
            <Button type="submit" variant="ghost" disabled={!lieu.title.trim()}>Thêm học liệu</Button>
          </form>
        </details>
      )}
    </li>
  );
}
