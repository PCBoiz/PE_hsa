'use client';

import { useMemo, useState } from 'react';

import { Button, Chip, EmptyState } from '@/components/ui';
import { ghiJson, loiBatDuoc } from '@/lib/api';
import { useDaGan } from '@/lib/daGan';
import { ngayGio } from '@/lib/thongBao';
import {
  HD_DA_SOAN,
  HD_XEM_TRUOC,
  TRAN_NOI_DUNG,
  TRAN_TIEU_DE,
  cauXemTruoc,
  moTaDoiTuong,
  nhanTrangThai,
  type DaSoan,
  type MotThongBao,
  type TrangTrungTam,
  type XemTruoc,
} from '@/lib/thongBaoSoan';

/**
 * THÔNG BÁO TRUNG TÂM — màn của học vụ (§61, bảng TopHSA dòng 27).
 *
 * Bốn cửa backend đã đứng sẵn từ 26/09/2026 và không nơi nào trong `frontend/src` gọi tới:
 * `GET/POST /api/admin/thong-bao`, `…/preview`, `…/<id>/gui`, `…/<id>/huy`. Màn này là
 * người gọi của cả bốn.
 *
 * ── BỐN ĐIỀU RÀNG BUỘC CÁCH DỰNG ──────────────────────────────────────────
 *
 * ① DANH MỤC ĐỐI TƯỢNG TỪ MÁY CHỦ (`chon`). Không một tên lớp, không một tên môn nào gõ
 *   trong tệp này (RULES §7). Bảng ba môn HSA sống ở `courses.truy_cap.BA_MON`; chép sang
 *   đây là dựng nguồn sự thật thứ hai cho cùng một câu hỏi.
 *
 * ② LƯU NHÁP VÀ GỬI NGAY LÀ HAI NÚT KHÁC NHAU, vì backend phân biệt (`gui: true/false`) và
 *   vì chúng khác nhau ở thứ không hoàn tác được. Nháp sửa được bằng cách huỷ rồi soạn lại;
 *   thông báo đã gửi thì không.
 *
 * ③ XEM TRƯỚC HẾT HẠN khi đổi đối tượng HOẶC đổi ô "Gửi kèm email" — hai thứ duy nhất nó
 *   phụ thuộc. Giữ con số cũ dưới cái nhãn mới là để học vụ đọc một con số của phạm vi
 *   TRƯỚC rồi bấm Gửi cho phạm vi SAU.
 *
 * ④ HUỶ NHÁP KHÔNG HỎI LẠI, GỬI THÌ HỎI. Huỷ một bản nháp là việc cuộn lại được (soạn lại
 *   mất một phút); gửi cho vài trăm em thì không. Ngưỡng "hỏi lại" tỉ lệ với thứ không hoàn
 *   tác được, không tỉ lệ với việc nút nào trông nguy hiểm hơn.
 *
 * Và: MỌI Ô, MỌI NÚT KHOÁ TỚI KHI REACT GẮN XONG (`useDaGan`). Trang dựng ở máy chủ nên
 * biểu mẫu hiện ra trước khi JavaScript gắn vào; gõ trong khoảng ấy thì chữ bị lượt hydrate
 * đầu xoá sạch, bấm thì không lời gọi nào đi, và không dấu hiệu nào cho người bấm biết.
 */
export default function ThongBaoTrungTam({
  dauTien, loiTai,
}: { dauTien: TrangTrungTam | null; loiTai: string | null }) {
  const chon = dauTien?.chon ?? { lop: [], mon: [] };
  const [ds, setDs] = useState<MotThongBao[]>(dauTien?.items ?? []);
  const [tieuDe, setTieuDe] = useState('');
  const [noiDung, setNoiDung] = useState('');
  const [lopChon, setLopChon] = useState<number[]>([]);
  const [monChon, setMonChon] = useState<string[]>([]);
  const [kemEmail, setKemEmail] = useState(false);
  const [xemTruoc, setXemTruoc] = useState<XemTruoc | null>(null);
  const [hoiLai, setHoiLai] = useState(false);
  const [dangChay, setDangChay] = useState(false);
  const [dangDoi, setDangDoi] = useState<number | null>(null);
  const [loi, setLoi] = useState<string | null>(loiTai);
  const [xong, setXong] = useState<string | null>(null);
  const daGan = useDaGan();

  // Bảng tra id → tên cho dòng danh sách. Không có nó thì mô tả đối tượng phải in `#7586`,
  // một con số kỹ thuật trên màn học vụ (RULES §10).
  const tenLop = useMemo(() => new Map(chon.lop.map((l) => [l.id, l.name])), [chon.lop]);
  const tenMon = useMemo(() => new Map(chon.mon.map((m) => [m.id, m.nhan])), [chon.mon]);

  const doiTuong = { classIds: lopChon, courseIds: monChon };
  const chuaChonAi = lopChon.length === 0 && monChon.length === 0;

  /** Đổi phạm vi hoặc kênh → bản xem trước cũ hết hạn (③). */
  function hetHanXemTruoc() {
    setXemTruoc(null);
    setHoiLai(false);
  }

  function batLop(id: number) {
    setLopChon((cu) => (cu.includes(id) ? cu.filter((x) => x !== id) : [...cu, id]));
    hetHanXemTruoc();
  }

  function batMon(id: string) {
    setMonChon((cu) => (cu.includes(id) ? cu.filter((x) => x !== id) : [...cu, id]));
    hetHanXemTruoc();
  }

  async function goiXemTruoc(): Promise<XemTruoc | null> {
    setLoi(null);
    try {
      const d = await ghiJson<XemTruoc>(
        '/api/admin/thong-bao/preview',
        { method: 'POST', body: JSON.stringify({ audience: doiTuong, sendEmail: kemEmail }) },
        HD_XEM_TRUOC,
      );
      setXemTruoc(d);
      return d;
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Chưa xem trước được. Thử lại sau ít phút.'));
      return null;
    }
  }

  async function bamXemTruoc() {
    setDangChay(true);
    await goiXemTruoc();
    setDangChay(false);
  }

  /** Nút "Gửi ngay" mở bước hỏi lại — và câu hỏi phải mang một con số thật (④). */
  async function bamGui() {
    setXong(null);
    setDangChay(true);
    const d = xemTruoc ?? (await goiXemTruoc());
    setDangChay(false);
    if (d) setHoiLai(true);
  }

  /** `gui = false` → lưu nháp; `true` → gửi ngay. Cùng một cửa, khác một cờ (②). */
  async function soan(gui: boolean) {
    setDangChay(true);
    setLoi(null);
    try {
      const kq = await ghiJson<DaSoan>(
        '/api/admin/thong-bao',
        {
          method: 'POST',
          body: JSON.stringify({
            title: tieuDe, body: noiDung, audience: doiTuong, sendEmail: kemEmail, gui,
          }),
        },
        HD_DA_SOAN,
      );
      setDs((cu) => [{
        id: kq.id, title: tieuDe, body: noiDung, audience: doiTuong,
        sendEmail: kemEmail, sendZalo: false, status: kq.status,
        recipientCount: kq.recipientCount ?? 0, createdAt: new Date().toISOString(),
        sentAt: gui ? new Date().toISOString() : null, createdByName: '', daGuiThu: 0, daDoc: 0,
      }, ...cu]);
      setXong(gui
        ? `Đã gửi tới ${kq.recipientCount ?? 0} em.`
        : 'Đã lưu bản nháp — bấm Gửi ở dòng dưới khi muốn phát đi.');
      setTieuDe('');
      setNoiDung('');
      setLopChon([]);
      setMonChon([]);
      setXemTruoc(null);
      setHoiLai(false);
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Chưa lưu được. Thử lại sau ít phút.'));
    } finally {
      setDangChay(false);
    }
  }

  /** Gửi hoặc huỷ một bản nháp đã có. Chờ máy chủ trả lời rồi mới đổi màn. */
  async function doiNhap(a: MotThongBao, viec: 'gui' | 'huy') {
    if (dangDoi) return;
    setDangDoi(a.id);
    setLoi(null);
    setXong(null);
    try {
      const kq = await ghiJson<DaSoan>(`/api/admin/thong-bao/${a.id}/${viec}`, { method: 'POST' }, HD_DA_SOAN);
      setDs((cu) => cu.map((r) => (r.id === a.id
        ? { ...r, status: kq.status, recipientCount: kq.recipientCount ?? r.recipientCount,
            sentAt: viec === 'gui' ? new Date().toISOString() : r.sentAt }
        : r)));
      setXong(viec === 'gui'
        ? `Đã gửi "${a.title ?? ''}" tới ${kq.recipientCount ?? 0} em.`
        : `Đã huỷ bản nháp "${a.title ?? ''}".`);
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Chưa thực hiện được. Thử lại sau ít phút.'));
    } finally {
      setDangDoi(null);
    }
  }

  const duSoan = tieuDe.trim().length > 0;

  return (
    <div data-khu="thong-bao-trung-tam" className="flex flex-col gap-6">
      <section className="rounded-xl border border-line bg-surface p-4">
        <h2 className="text-section text-ink">Soạn thông báo</h2>
        <p className="mt-1 text-small text-ink-3">
          Thông báo hiện trên chuông của từng em. Chọn lớp, hoặc chọn môn để báo cho mọi lớp
          của môn ấy.
        </p>

        <div className="mt-4 flex flex-col gap-2">
          <label htmlFor="tt-tieu-de" className="text-label text-ink-3">Tiêu đề</label>
          <input
            id="tt-tieu-de"
            data-o="tieu-de"
            value={tieuDe}
            maxLength={TRAN_TIEU_DE}
            disabled={!daGan || dangChay}
            onChange={(e) => setTieuDe(e.target.value)}
            placeholder="Nghỉ lễ 2/9 — các lớp học bù vào cuối tuần"
            className="min-h-11 w-full rounded-md border border-line-input bg-sunken px-3 text-input text-ink placeholder:text-ink-3/70 focus:outline-2 focus:outline-brand disabled:opacity-60"
          />
        </div>

        <div className="mt-4 flex flex-col gap-2">
          <label htmlFor="tt-noi-dung" className="text-label text-ink-3">Nội dung</label>
          <textarea
            id="tt-noi-dung"
            data-o="noi-dung"
            value={noiDung}
            rows={4}
            maxLength={TRAN_NOI_DUNG}
            disabled={!daGan || dangChay}
            onChange={(e) => setNoiDung(e.target.value)}
            className="w-full rounded-md border border-line-input bg-sunken px-3 py-2 text-input text-ink focus:outline-2 focus:outline-brand disabled:opacity-60"
          />
        </div>

        {/* ① Danh mục do máy chủ trả. `fieldset`/`legend` chứ không một dòng chữ đậm: nhóm
            ô tick cần một nhãn nhóm để trình đọc màn hình đọc được "Lớp — 3 trong 6". */}
        <fieldset className="mt-4" data-nhom="lop">
          <legend className="text-label text-ink-3">Lớp nhận thông báo</legend>
          {chon.lop.length === 0 ? (
            <p className="mt-2 text-small text-ink-3">
              Chưa có lớp nào đang chạy — mở lớp ở mục Lớp học trước.
            </p>
          ) : (
            <div className="mt-2 flex flex-wrap gap-2">
              {chon.lop.map((l) => (
                <label
                  key={l.id}
                  data-lop={l.id}
                  className={`-mx-0 flex min-h-11 cursor-pointer items-center gap-2 rounded-full border px-4 text-small ${
                    lopChon.includes(l.id)
                      ? 'border-brand bg-brand-soft text-brand-ink'
                      : 'border-line bg-surface text-ink-2'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={lopChon.includes(l.id)}
                    disabled={!daGan || dangChay}
                    onChange={() => batLop(l.id)}
                    className="size-4 accent-[var(--brand)]"
                  />
                  {l.name} ({l.soEm} em)
                </label>
              ))}
            </div>
          )}
        </fieldset>

        <fieldset className="mt-4" data-nhom="mon">
          <legend className="text-label text-ink-3">Hoặc theo môn (mọi lớp của môn ấy)</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {chon.mon.map((m) => (
              <label
                key={m.id}
                data-mon={m.id}
                className={`flex min-h-11 cursor-pointer items-center gap-2 rounded-full border px-4 text-small ${
                  monChon.includes(m.id)
                    ? 'border-brand bg-brand-soft text-brand-ink'
                    : 'border-line bg-surface text-ink-2'
                }`}
              >
                <input
                  type="checkbox"
                  checked={monChon.includes(m.id)}
                  disabled={!daGan || dangChay}
                  onChange={() => batMon(m.id)}
                  className="size-4 accent-[var(--brand)]"
                />
                {m.nhan}
              </label>
            ))}
          </div>
        </fieldset>

        <label className="mt-4 -mx-2 flex min-h-11 items-center gap-2 px-2 text-body text-ink-2">
          <input
            type="checkbox"
            data-o="kem-email"
            checked={kemEmail}
            disabled={!daGan || dangChay}
            onChange={(e) => { setKemEmail(e.target.checked); hetHanXemTruoc(); }}
            className="size-5 accent-[var(--brand)]"
          />
          Gửi kèm email
        </label>
        {dauTien && !dauTien.zalo.sanSang && dauTien.zalo.lyDo && (
          <p className="mt-2 text-small text-ink-3">{dauTien.zalo.lyDo}</p>
        )}

        <div className="mt-4 flex flex-wrap gap-2">
          <Button
            variant="ghost"
            data-nut="xem-truoc"
            onClick={() => void bamXemTruoc()}
            disabled={!daGan || dangChay || chuaChonAi}
          >
            Xem trước người nhận
          </Button>
          <Button
            variant="ghost"
            data-nut="luu-nhap"
            onClick={() => void soan(false)}
            disabled={!daGan || dangChay || !duSoan}
          >
            Lưu nháp
          </Button>
          <Button
            data-nut="gui"
            onClick={() => void bamGui()}
            disabled={!daGan || dangChay || !duSoan || chuaChonAi}
          >
            Gửi ngay
          </Button>
          {(!duSoan || chuaChonAi) && (
            <span className="self-center text-small text-ink-3">
              {!duSoan ? 'Nhập tiêu đề rồi mới lưu hoặc gửi được.' : 'Chọn ít nhất một lớp hoặc một môn.'}
            </span>
          )}
        </div>

        {xemTruoc && (
          <p
            data-xem-truoc
            data-tong={xemTruoc.tong}
            data-email={xemTruoc.email}
            className="mt-3 rounded-xl bg-brand-soft px-4 py-3 text-small text-brand-ink"
          >
            {cauXemTruoc(xemTruoc, kemEmail)}
          </p>
        )}

        {hoiLai && (
          <div className="mt-3 rounded-xl border border-line bg-sunken px-4 py-3">
            <p className="text-body text-ink">
              Gửi ngay cho {xemTruoc?.tong ?? 0} em?
              {kemEmail && (xemTruoc?.email ?? 0) > 0
                ? ` ${xemTruoc?.email} em nhận thêm email — thư đã đi thì không thu về được.`
                : ' Thông báo đã tới chuông thì không thu về được.'}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button data-nut="xac-nhan" onClick={() => void soan(true)} disabled={dangChay}>
                {dangChay ? 'Đang gửi…' : 'Gửi ngay'}
              </Button>
              <Button variant="ghost" onClick={() => setHoiLai(false)} disabled={dangChay}>
                Quay lại
              </Button>
            </div>
          </div>
        )}

        {xong && (
          <p data-xong className="mt-3 rounded-xl bg-success/10 px-4 py-3 text-small text-success-ink" role="status">
            {xong}
          </p>
        )}
        {loi && (
          <p className="mt-3 rounded-xl bg-danger/10 px-4 py-3 text-small text-danger-ink" role="alert">
            {loi}
          </p>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-section text-ink">Đã soạn</h2>
        {ds.length === 0 ? (
          <EmptyState
            title="Chưa có thông báo nào"
            hint="Thông báo bạn soạn ở trên sẽ hiện tại đây, kèm số em đã nhận và số em đã đọc."
          />
        ) : (
          <ul data-ds="da-soan" className="flex flex-col gap-2">
            {ds.map((a) => {
              const tt = nhanTrangThai(a.status);
              return (
                <li
                  key={a.id}
                  data-id={a.id}
                  data-trang-thai={a.status}
                  className="rounded-xl border border-line bg-surface p-4"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Chip tone={tt.tone}>{tt.nhan}</Chip>
                    <span className="text-small text-ink-3">{ngayGio(a.sentAt ?? a.createdAt)}</span>
                    {a.status === 'sent' && (
                      <span className="text-small text-ink-2">{a.recipientCount ?? 0} em nhận</span>
                    )}
                    {a.sendEmail && a.status === 'sent' && (
                      <span className="text-small text-ink-3">· {a.daGuiThu} thư đã gửi</span>
                    )}
                    {a.status === 'sent' && (
                      <span className="text-small text-ink-3">· {a.daDoc} em đã đọc</span>
                    )}
                    {a.createdByName && (
                      <span className="text-small text-ink-3">· {a.createdByName} soạn</span>
                    )}
                    {a.status === 'draft' && (
                      <span className="ml-auto flex gap-2">
                        <Button
                          size="sm"
                          data-nut="gui-nhap"
                          onClick={() => void doiNhap(a, 'gui')}
                          disabled={!daGan || dangDoi === a.id}
                        >
                          Gửi
                        </Button>
                        {/* ④ Huỷ nháp không hỏi lại: việc này cuộn lại được bằng cách soạn
                            lại, khác hẳn nút Gửi ngay bên cạnh. */}
                        <Button
                          size="sm"
                          variant="ghost-danger"
                          data-nut="huy-nhap"
                          onClick={() => void doiNhap(a, 'huy')}
                          disabled={!daGan || dangDoi === a.id}
                        >
                          Huỷ nháp
                        </Button>
                      </span>
                    )}
                  </div>
                  <p className="mt-2 text-body font-medium text-ink">{a.title}</p>
                  <p className="mt-1 text-small text-ink-3">
                    Gửi cho: {moTaDoiTuong(a.audience, tenLop, tenMon)}
                  </p>
                  {a.body && <p className="mt-1 whitespace-pre-line text-small text-ink-2">{a.body}</p>}
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
