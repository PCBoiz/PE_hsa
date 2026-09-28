'use client';

import { useState } from 'react';

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
  nhanTrangThai,
  type DaSoan,
  type MotThongBao,
  type XemTruoc,
} from '@/lib/thongBaoSoan';

/**
 * SOẠN THÔNG BÁO CHO LỚP — giảng viên VÀ trợ giảng (bảng TopHSA dòng 20).
 *
 * ── VÌ SAO MÀN NÀY LÀ NỬA CÒN LẠI CỦA DÒNG 20 ─────────────────────────────
 *
 * Backend §61 đã đứng sẵn từ 26/09/2026 và đo được qua API: xem trước đếm đúng, gửi lớp
 * mình 201, gửi lớp người khác 404, thư đi qua hộp thư đi. Nhưng `grep` cả `frontend/src`
 * ra **0** nơi gọi `/api/teach/classes/<id>/thong-bao` — tức trợ giảng không bấm được ở
 * đâu, và dòng 20 vẫn "MỘT PHẦN" dù mã đã viết xong. Đó là một cách hỏng không kêu:
 * mọi phép kiểm backend xanh, không ai dùng được.
 *
 * ── BA ĐIỀU RÀNG BUỘC CÁCH DỰNG MÀN ───────────────────────────────────────
 *
 * ① ĐỐI TƯỢNG KHÔNG PHẢI MỘT Ô CHỌN. Cửa này cố định đối tượng là lớp trên đường dẫn
 *   (`_soan(request, {'classIds': [class_id]}, True)`), nên màn KHÔNG bày ô chọn lớp.
 *   Bày ra rồi máy chủ bỏ qua là một lời hứa màn hình không giữ được.
 *
 * ② XEM TRƯỚC LÀ MỘT LỜI GỌI RIÊNG, và nó phụ thuộc ô "Gửi kèm email". Máy chủ mặc định
 *   `sendEmail=False` cho bản xem trước (quyết định 2 của anh Sơn, 26/09) đúng vì ô ấy để
 *   trống — nên đổi ô là bản xem trước cũ HẾT HẠN. Giữ lại con số cũ dưới cái nhãn mới thì
 *   người gửi đọc "3 em nhận email" trong khi sắp gửi cho 0 em, hoặc ngược lại.
 *
 * ③ GỬI LÀ KHÔNG CUỘN LẠI ĐƯỢC, nên có một bước hỏi lại và bước ấy nêu ĐÚNG SỐ người.
 *   "Bạn có chắc không" thì ai cũng bấm Có; "báo cho 27 em, 12 em nhận email" thì người ta
 *   dừng lại một nhịp. Nếu chưa xem trước lần nào thì nút Gửi tự gọi `/preview` trước —
 *   câu hỏi phải mang một con số thật, không mang chữ "cả lớp".
 *
 * Và điều thứ tư, đo được chứ không suy ra: MỌI Ô VÀ MỌI NÚT KHOÁ TỚI KHI REACT GẮN XONG
 * (`useDaGan`). Trang dựng ở máy chủ, nên ô nhập hiện ra trước khi JavaScript gắn vào —
 * gõ trong khoảng ấy thì chữ bị lượt hydrate đầu xoá sạch, và bấm thì không lời gọi nào
 * đi. Lead mất một lượt đo ngày 26/09 vì đúng chuyện này ở trang `/thong-bao`.
 */
export default function SoanThongBaoLop({
  classId, tenLop, dauTien, loiTai,
}: { classId: number; tenLop: string; dauTien: MotThongBao[]; loiTai: string | null }) {
  const [tieuDe, setTieuDe] = useState('');
  const [noiDung, setNoiDung] = useState('');
  const [kemEmail, setKemEmail] = useState(false);
  const [xemTruoc, setXemTruoc] = useState<XemTruoc | null>(null);
  const [hoiLai, setHoiLai] = useState(false);
  const [dangChay, setDangChay] = useState(false);
  const [ds, setDs] = useState<MotThongBao[]>(dauTien);
  const [loi, setLoi] = useState<string | null>(loiTai);
  const [xong, setXong] = useState<string | null>(null);
  const daGan = useDaGan();

  /** Đổi ô "Gửi kèm email" → bản xem trước cũ hết hạn (② ở đầu tệp). */
  function doiKemEmail(bat: boolean) {
    setKemEmail(bat);
    setXemTruoc(null);
    setHoiLai(false);
  }

  async function goiXemTruoc(): Promise<XemTruoc | null> {
    setLoi(null);
    try {
      const d = await ghiJson<XemTruoc>(
        `/api/teach/classes/${classId}/thong-bao/preview`,
        { method: 'POST', body: JSON.stringify({ sendEmail: kemEmail }) },
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

  /** Nút Gửi mở bước hỏi lại — và bảo đảm câu hỏi mang một con số thật (③). */
  async function bamGui() {
    setXong(null);
    setDangChay(true);
    const d = xemTruoc ?? (await goiXemTruoc());
    setDangChay(false);
    if (d) setHoiLai(true);
  }

  async function guiThat() {
    setDangChay(true);
    setLoi(null);
    try {
      const kq = await ghiJson<DaSoan>(
        `/api/teach/classes/${classId}/thong-bao`,
        {
          method: 'POST',
          body: JSON.stringify({ title: tieuDe, body: noiDung, sendEmail: kemEmail }),
        },
        HD_DA_SOAN,
      );
      // Dựng dòng mới từ thứ MÌNH vừa gửi + số người máy chủ đếm. Không gọi lại danh sách:
      // một lượt gọi nữa trên máy chủ gói miễn phí là thêm vài giây người gửi ngồi nhìn
      // màn hình chưa đổi, và mọi trường của dòng này đều đã biết.
      setDs((cu) => [{
        id: kq.id, title: tieuDe, body: noiDung, audience: { classIds: [classId] },
        sendEmail: kemEmail, sendZalo: false, status: kq.status,
        recipientCount: kq.recipientCount ?? 0, createdAt: new Date().toISOString(),
        sentAt: new Date().toISOString(), createdByName: '', daGuiThu: 0, daDoc: 0,
      }, ...cu]);
      setXong(`Đã báo cho ${kq.recipientCount ?? 0} em của lớp ${tenLop}.`);
      setTieuDe('');
      setNoiDung('');
      setXemTruoc(null);
      setHoiLai(false);
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Chưa gửi được. Thử lại sau ít phút.'));
    } finally {
      setDangChay(false);
    }
  }

  const duGui = tieuDe.trim().length > 0;

  return (
    <div data-khu="soan-thong-bao-lop" className="flex flex-col gap-6">
      <section className="rounded-xl border border-line bg-surface p-4">
        <h2 className="text-section text-ink">Nhắc cả lớp</h2>
        <p className="mt-1 text-small text-ink-3">
          Thông báo hiện trên chuông của từng em trong lớp. Tick &ldquo;Gửi kèm email&rdquo;
          thì em nào bật nhận thư sẽ nhận thêm một thư.
        </p>

        <div className="mt-4 flex flex-col gap-2">
          <label htmlFor="tb-tieu-de" className="text-label text-ink-3">Tiêu đề</label>
          <input
            id="tb-tieu-de"
            data-o="tieu-de"
            value={tieuDe}
            maxLength={TRAN_TIEU_DE}
            disabled={!daGan || dangChay}
            onChange={(e) => setTieuDe(e.target.value)}
            placeholder="Nhớ làm bài trước buổi tối mai"
            className="min-h-11 w-full rounded-md border border-line-input bg-sunken px-3 text-input text-ink placeholder:text-ink-3/70 focus:outline-2 focus:outline-brand disabled:opacity-60"
          />
        </div>

        <div className="mt-4 flex flex-col gap-2">
          <label htmlFor="tb-noi-dung" className="text-label text-ink-3">Nội dung</label>
          <textarea
            id="tb-noi-dung"
            data-o="noi-dung"
            value={noiDung}
            rows={5}
            maxLength={TRAN_NOI_DUNG}
            disabled={!daGan || dangChay}
            onChange={(e) => setNoiDung(e.target.value)}
            placeholder="Các em làm hết phần Định lượng trước 20h mai nhé."
            className="w-full rounded-md border border-line-input bg-sunken px-3 py-2 text-input text-ink placeholder:text-ink-3/70 focus:outline-2 focus:outline-brand disabled:opacity-60"
          />
          <p className="text-small text-ink-3">
            Còn {TRAN_NOI_DUNG - noiDung.length} ký tự.
          </p>
        </div>

        <label className="mt-4 -mx-2 flex min-h-11 items-center gap-2 px-2 text-body text-ink-2">
          <input
            type="checkbox"
            data-o="kem-email"
            checked={kemEmail}
            disabled={!daGan || dangChay}
            onChange={(e) => doiKemEmail(e.target.checked)}
            className="size-5 accent-[var(--brand)]"
          />
          Gửi kèm email
        </label>

        <div className="mt-4 flex flex-wrap gap-2">
          <Button
            variant="ghost"
            data-nut="xem-truoc"
            onClick={() => void bamXemTruoc()}
            disabled={!daGan || dangChay}
          >
            Xem trước người nhận
          </Button>
          <Button
            data-nut="gui"
            onClick={() => void bamGui()}
            disabled={!daGan || dangChay || !duGui}
          >
            Gửi thông báo
          </Button>
          {!duGui && (
            <span className="self-center text-small text-ink-3">Nhập tiêu đề rồi mới gửi được.</span>
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
              {/* Nêu ĐÚNG SỐ người, không hỏi chung chung (③). */}
              Gửi ngay cho {xemTruoc?.tong ?? 0} em của lớp {tenLop}?
              {kemEmail && (xemTruoc?.email ?? 0) > 0
                ? ` ${xemTruoc?.email} em nhận thêm email — thư đã đi thì không thu về được.`
                : ' Thông báo đã tới chuông thì không thu về được.'}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button data-nut="xac-nhan" onClick={() => void guiThat()} disabled={dangChay}>
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
        <h2 className="mb-3 text-section text-ink">Đã gửi cho lớp này</h2>
        {ds.length === 0 ? (
          <EmptyState
            title="Chưa gửi thông báo nào cho lớp này"
            hint="Thông báo bạn gửi ở trên sẽ hiện lại tại đây, kèm số em đã nhận."
          />
        ) : (
          <ul data-ds="da-gui" className="flex flex-col gap-2">
            {ds.map((a) => {
              const tt = nhanTrangThai(a.status);
              return (
                <li key={a.id} data-id={a.id} className="rounded-xl border border-line bg-surface p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <Chip tone={tt.tone}>{tt.nhan}</Chip>
                    <span className="text-small text-ink-3">
                      {ngayGio(a.sentAt ?? a.createdAt)}
                    </span>
                    <span data-so-nhan className="text-small text-ink-2">
                      {a.recipientCount ?? 0} em nhận
                    </span>
                    {a.sendEmail && (
                      <span className="text-small text-ink-3">· {a.daGuiThu} thư đã gửi</span>
                    )}
                    <span className="ml-auto text-small text-ink-3">{a.daDoc} em đã đọc</span>
                  </div>
                  <p className="mt-2 text-body font-medium text-ink">{a.title}</p>
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
