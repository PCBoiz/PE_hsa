'use client';

import { useRef, useState } from 'react';
// `zod/mini`, không phải `zod`: đây là mã trình duyệt — xem e2e/unit/zod-phia-trinh-duyet.
import * as z from 'zod/mini';

import { Button, Chip, TableWrap, Tbody, Td, Th, Thead, Tr } from '@/components/ui';
import { ghiJson } from '@/lib/api';
import type { HinhDang } from '@/lib/server-api';

/** Một dòng của bảng khớp — khớp `teaching/nhap_ket_qua_view.py::danh_gia`. */
type TrangThai = 'san-sang' | 'chua-khop' | 'bo-qua' | 'trung';
type Dong = {
  thuTu: number;
  tep: string;
  trangThai: TrangThai;
  hoTen: string;
  maHocSinh: string | null;
  khopTuDong: number | null;
  userId: number | null;
  chonTay: boolean;
  tenTrongLop: string | null;
  ghiChu: string | null;
  ngayThi: string;
  dot: string | null;
  tongDiem: number;
  tongToiDa: number;
  diemPhan: { phan: number; ten: string; diem: number; toiDa: number }[];
  soDonVi: number;
  yeuNhat: { ten: string; pct: number }[];
  canhBao: string[];
  seGhiDe: boolean;
};
type BangKhop = {
  daGhi: number;
  tomTat: { tong: number; sanSang: number; chuaKhop: number; boQua: number; trung: number; seGhiDe: number };
  dong: Dong[];
  hocVienTrongLop: { id: number; name: string | null }[];
};
type KetQuaDoc = { tep: { tep: string; phieu?: string; loi?: string }[] };

const so = z.number();
const chu = z.string();
const HD_BANG_KHOP = z.looseObject({
  daGhi: so,
  tomTat: z.looseObject({ tong: so, sanSang: so, chuaKhop: so, boQua: so, trung: so, seGhiDe: so }),
  dong: z.array(z.looseObject({
    thuTu: so,
    tep: chu,
    trangThai: z.enum(['san-sang', 'chua-khop', 'bo-qua', 'trung']),
    hoTen: chu,
    maHocSinh: z.nullable(chu),
    khopTuDong: z.nullable(so),
    userId: z.nullable(so),
    chonTay: z.boolean(),
    tenTrongLop: z.nullable(chu),
    ghiChu: z.nullable(chu),
    ngayThi: chu,
    dot: z.nullable(chu),
    tongDiem: so,
    tongToiDa: so,
    diemPhan: z.array(z.looseObject({ phan: so, ten: chu, diem: so, toiDa: so })),
    soDonVi: so,
    yeuNhat: z.array(z.looseObject({ ten: chu, pct: so })),
    canhBao: z.array(chu),
    seGhiDe: z.boolean(),
  })),
  hocVienTrongLop: z.array(z.looseObject({ id: so, name: z.nullable(chu) })),
}) satisfies HinhDang<BangKhop>;
const HD_DOC = z.looseObject({
  tep: z.array(z.looseObject({ tep: chu, phieu: z.optional(chu), loi: z.optional(chu) })),
}) satisfies HinhDang<KetQuaDoc>;

/** Số tệp gửi đi đọc CÙNG LÚC. Máy chủ production có 2 worker × 2 luồng; lấy
 *  cả bốn thì mọi người khác đang dùng hệ thống phải chờ lượt nhập này xong. */
const DONG_THOI = 2;

/** Mọi `/api/*` đi qua route handler Next trên Vercel, thân request tối đa 4,5 MB
 *  (gồm cả phần bao của multipart). Tờ báo cáo thật ~0,5 MB — tệp quá trần này gần
 *  như chắc chắn là chọn nhầm, nên nói thẳng thay vì để Vercel trả 413. */
const TRAN_TEP = 4 * 1024 * 1024;

function ngay(iso?: string) {
  if (!iso) return '—';
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

/** Trạng thái một tờ → chữ và tông màu ngữ nghĩa của `Chip`. */
const NHAN: Record<TrangThai, { chu: string; tone: 'good' | 'warn' | 'bad' | 'neutral' }> = {
  'san-sang': { chu: 'Sẽ ghi', tone: 'good' },
  'chua-khop': { chu: 'Chưa khớp', tone: 'warn' },
  trung: { chu: 'Trùng em', tone: 'bad' },
  'bo-qua': { chu: 'Bỏ qua', tone: 'neutral' },
};

/**
 * Nhập kết quả thi thử từ tờ PDF của hệ thống khảo thí.
 *
 * BA BƯỚC, KHÔNG PHẢI MỘT:
 *   1. Đọc — gửi TỪNG tệp (một lớp 35 tờ trong một request vượt trần thời gian
 *      của máy chủ và trần 4,5 MB của Vercel; xem docstring view).
 *   2. Khớp — máy chủ trả bảng; đổi lựa chọn tay thì hỏi lại máy chủ, để luật
 *      khớp và soát trùng chỉ có MỘT bản.
 *   3. Ghi — một cú bấm riêng. Điểm gán nhầm sẽ đi thẳng vào tờ báo cáo gửi về
 *      nhà, nơi không ai kiểm lại được nữa.
 */
export default function NhapKetQuaClient({ classId }: { classId: number }) {
  const [tep, setTep] = useState<File[]>([]);
  const [tienDo, setTienDo] = useState<{ xong: number; tong: number } | null>(null);
  const [phieu, setPhieu] = useState<string[]>([]);
  const [hong, setHong] = useState<{ tep: string; loi: string }[]>([]);
  const [bang, setBang] = useState<BangKhop | null>(null);
  const [chon, setChon] = useState<Record<number, number>>({});
  const [dangGoi, setDangGoi] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);
  const [daGhi, setDaGhi] = useState<number | null>(null);
  // Mỗi lượt đọc/khớp mang một số. Phản hồi của lượt CŨ về muộn (chọn lại tệp
  // giữa chừng) thì bỏ, không được đè lên bảng của lượt mới.
  const luot = useRef(0);

  const goc = `/api/teach/classes/${classId}/ket-qua-thi`;

  function datLai() {
    luot.current += 1;
    setPhieu([]);
    setHong([]);
    setBang(null);
    setChon({});
    setDaGhi(null);
    setLoi(null);
    setTienDo(null);
    setDangGoi(false);
  }

  async function khop(ds: string[], chonMoi: Record<number, number>, ghi: boolean) {
    const lan = ++luot.current;
    setDangGoi(true);
    setLoi(null);
    try {
      const kq = await ghiJson(
        `${goc}/ghi`,
        { method: 'POST', body: JSON.stringify({ phieu: ds, chon: chonMoi, ghi }) },
        HD_BANG_KHOP,
      );
      if (lan !== luot.current) return;
      setBang(kq);
      if (ghi) setDaGhi(kq.daGhi);
    } catch (e) {
      if (lan === luot.current) setLoi(e instanceof Error ? e.message : 'Không gọi được máy chủ.');
    } finally {
      if (lan === luot.current) setDangGoi(false);
    }
  }

  async function docHet() {
    const ds = tep;
    if (!ds.length) return;
    datLai();
    const lan = luot.current;
    setTienDo({ xong: 0, tong: ds.length });

    const kq: KetQuaDoc['tep'] = new Array(ds.length);
    let tiep = 0;
    let xong = 0;
    async function tho() {
      while (tiep < ds.length && lan === luot.current) {
        const k = tiep++;
        const f = ds[k];
        if (f.size > TRAN_TEP) {
          kq[k] = { tep: f.name, loi: 'Tệp nặng hơn 4 MB — tờ báo cáo thật chỉ khoảng nửa MB. Kiểm lại có chọn đúng tệp không.' };
        } else {
          const fd = new FormData();
          fd.append('files', f);
          try {
            const r = await ghiJson(`${goc}/doc`, { method: 'POST', body: fd }, HD_DOC);
            kq[k] = r.tep[0] ?? { tep: f.name, loi: 'Máy chủ không trả kết quả cho tệp này.' };
          } catch (e) {
            kq[k] = { tep: f.name, loi: e instanceof Error ? e.message : 'Không gọi được máy chủ.' };
          }
        }
        xong += 1;
        if (lan === luot.current) setTienDo({ xong, tong: ds.length });
      }
    }
    await Promise.all(Array.from({ length: Math.min(DONG_THOI, ds.length) }, tho));
    if (lan !== luot.current) return;

    setTienDo(null);
    const doc = kq.filter((t) => t.phieu).map((t) => t.phieu as string);
    setPhieu(doc);
    setHong(kq.filter((t) => !t.phieu).map((t) => ({ tep: t.tep, loi: t.loi || 'Không đọc được tệp này.' })));
    if (doc.length) await khop(doc, {}, false);
  }

  function doiChon(thuTu: number, gia: string) {
    const moi = { ...chon };
    if (gia === '') delete moi[thuTu];
    else moi[thuTu] = Number(gia);
    setChon(moi);
    void khop(phieu, moi, false);
  }

  const t = bang?.tomTat;
  const dangDoc = tienDo !== null;
  const hocVien = bang?.hocVienTrongLop ?? [];

  return (
    <section className="mt-6">
      <div className="rounded-lg border border-line bg-surface p-4">
        <h2 className="text-subhead text-ink">1. Chọn tệp PDF kết quả</h2>
        <p className="mt-1 text-body text-ink-2">
          Tệp do hệ thống khảo thí xuất cho từng em. Chọn được cả xấp một lúc. Hệ thống chỉ đọc và
          hiện bảng trước — chưa ghi gì vào hồ sơ học viên.
        </p>
        <input
          type="file"
          accept="application/pdf,.pdf"
          multiple
          aria-label="Chọn các tệp PDF kết quả thi thử"
          className="mt-3 block w-full text-body text-ink-2 file:mr-3 file:min-h-11 file:rounded-md file:border file:border-line file:bg-ground file:px-4 file:text-body file:text-ink"
          onChange={(e) => {
            setTep(e.target.files ? Array.from(e.target.files) : []);
            datLai();
          }}
        />
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <Button onClick={() => void docHet()} disabled={!tep.length || dangDoc || dangGoi}>
            {dangDoc ? 'Đang đọc…' : `Đọc ${tep.length || ''} tệp`}
          </Button>
          {dangDoc && tienDo && (
            <span className="text-caption text-ink-2" role="status" aria-live="polite">
              Đã đọc {tienDo.xong}/{tienDo.tong} tệp
            </span>
          )}
          {!dangDoc && tep.length > 0 && !bang && (
            <span className="text-caption text-ink-3">{tep.length} tệp đã chọn</span>
          )}
        </div>
        {dangDoc && tienDo && (
          <progress
            className="mt-3 block h-2 w-full accent-brand"
            max={tienDo.tong}
            value={tienDo.xong}
            aria-label="Tiến độ đọc tệp"
          />
        )}
        {loi && <p className="mt-3 text-body text-danger-ink" role="alert">{loi}</p>}
      </div>

      {hong.length > 0 && (
        <div className="mt-6 rounded-lg border border-line bg-surface p-4">
          <h2 className="text-subhead text-ink">Không đọc được {hong.length} tệp</h2>
          <ul className="mt-2 flex flex-col gap-2">
            {hong.map((h, i) => (
              <li key={`${h.tep}-${i}`} className="text-body">
                <span className="text-ink">{h.tep}</span>
                <span className="block text-caption text-danger-ink">{h.loi}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {bang && (
        <div className="mt-6 rounded-lg border border-line bg-surface p-4">
          <h2 className="text-subhead text-ink">2. Kiểm lại rồi mới ghi</h2>
          <p className="mt-1 text-body text-ink-2" aria-live="polite">
            {t?.sanSang ?? 0} tờ sẽ ghi
            {t?.seGhiDe ? ` (trong đó ${t.seGhiDe} tờ ghi đè lượt thi đã có)` : ''}
            {t?.chuaKhop ? ` · ${t.chuaKhop} tờ chưa khớp` : ''}
            {t?.trung ? ` · ${t.trung} tờ trùng em` : ''}
            {t?.boQua ? ` · ${t.boQua} tờ bỏ qua` : ''}.
            {' '}Tờ nào khớp sai hoặc chưa khớp thì chọn lại em ở cột “Ghi cho”.
          </p>

          <TableWrap caption="Các tờ kết quả vừa đọc và học viên sẽ nhận điểm">
            <Thead>
              <Tr>
                <Th>Tệp</Th>
                <Th>Tên trên tờ</Th>
                <Th>Ghi cho</Th>
                <Th>Kỳ thi</Th>
                <Th align="right">Tổng điểm</Th>
                <Th>Thấp nhất</Th>
              </Tr>
            </Thead>
            <Tbody>
              {bang.dong.map((d) => (
                <Tr key={d.thuTu}>
                  <Td label="Tệp">
                    <span className="block break-words text-body text-ink">{d.tep}</span>
                    <span className="mt-1 inline-block">
                      <Chip tone={NHAN[d.trangThai].tone}>{NHAN[d.trangThai].chu}</Chip>
                    </span>
                  </Td>
                  <Td label="Tên trên tờ">{d.hoTen}</Td>
                  <Td label="Ghi cho">
                    <select
                      aria-label={`Học viên nhận điểm của tệp ${d.tep}`}
                      /* `min-w-[18ch]`: bảng tự chia cột theo nội dung, và cột này
                         từng co tới mức tên em bị cắt còn "Tự khớp: Te…" — đúng
                         thứ người nhập cần đọc để biết điểm vào hồ sơ ai. */
                      className="min-h-11 w-full min-w-[18ch] rounded-md border border-line-input bg-sunken px-3 text-input text-ink disabled:opacity-50"
                      value={chon[d.thuTu] !== undefined ? String(chon[d.thuTu]) : ''}
                      disabled={dangGoi || daGhi !== null}
                      onChange={(e) => doiChon(d.thuTu, e.target.value)}
                    >
                      <option value="">
                        {/* TÊN đứng trước: ô hẹp thì bị cắt phần đuôi "(tự khớp)",
                            không phải cắt mất tên em. */}
                        {d.khopTuDong
                          ? `${hocVien.find((e) => e.id === d.khopTuDong)?.name || `#${d.khopTuDong}`} (tự khớp)`
                          : '— Chưa chọn em nào —'}
                      </option>
                      <option value="0">Bỏ qua tờ này</option>
                      {hocVien.map((e) => (
                        <option key={e.id} value={e.id}>{e.name || `#${e.id}`}</option>
                      ))}
                    </select>
                    {d.ghiChu && (
                      <span
                        className={`mt-1 block text-caption ${d.trangThai === 'trung' ? 'text-danger-ink' : 'text-warning-ink'}`}
                      >
                        {d.ghiChu}
                      </span>
                    )}
                  </Td>
                  <Td label="Kỳ thi">
                    {d.dot || '—'}
                    <span className="block text-caption text-ink-3">{ngay(d.ngayThi)}</span>
                    {d.seGhiDe && d.trangThai === 'san-sang' && (
                      <span className="block text-caption text-warning-ink">ghi đè lượt đã có</span>
                    )}
                  </Td>
                  <Td label="Tổng điểm" num>
                    {`${d.tongDiem}/${d.tongToiDa}`}
                    {d.diemPhan.length ? (
                      <span className="block text-caption text-ink-3">
                        {d.diemPhan.map((p) => `${p.diem}/${p.toiDa}`).join(' · ')}
                      </span>
                    ) : null}
                    {d.canhBao.map((c) => (
                      <span key={c} className="mt-1 block text-caption text-warning-ink">{c}</span>
                    ))}
                  </Td>
                  <Td label="Thấp nhất">
                    {d.yeuNhat.length ? d.yeuNhat.map((v) => `${v.ten} (${v.pct}%)`).join(' · ') : '—'}
                    {d.soDonVi ? (
                      <span className="block text-caption text-ink-3">{d.soDonVi} đơn vị kiến thức</span>
                    ) : null}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </TableWrap>

          {daGhi !== null ? (
            <p className="mt-4 text-body text-success-ink" role="status">
              Đã ghi {daGhi} kết quả vào hồ sơ học viên. Mở báo cáo phụ huynh của lớp là thấy điểm
              kỳ thi này trong tờ của từng em.
            </p>
          ) : (
            <div className="mt-4 flex flex-wrap items-center gap-3">
              {(t?.sanSang ?? 0) > 0 ? (
                <Button onClick={() => void khop(phieu, chon, true)} disabled={dangGoi}>
                  {dangGoi ? 'Đang xử lý…' : `Ghi ${t?.sanSang} kết quả vào hồ sơ`}
                </Button>
              ) : (
                <span className="text-body text-ink-2">
                  Chưa có tờ nào sẵn sàng để ghi — chọn em ở cột “Ghi cho”.
                </span>
              )}
              {(t?.sanSang ?? 0) > 0 && (t?.tong ?? 0) > (t?.sanSang ?? 0) && (
                <span className="text-caption text-ink-3">
                  Tờ chưa khớp, trùng em hoặc bỏ qua sẽ không được ghi.
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
