'use client';

import { useRouter } from 'next/navigation';
import { useRef, useState, type ReactNode } from 'react';

import {
  Button,
  Card,
  CardHead,
  Chip,
  EmptyState,
  Modal,
  TableWrap,
  Tbody,
  Td,
  Th,
  Thead,
  ToastProvider,
  Tr,
  useToast,
} from '@/components/ui';
import { apiFetch, errorText, ghiJson, loiBatDuoc } from '@/lib/api';
import { NHAN_HINH_THUC, noiHoc } from '@/lib/noiHoc';
import * as z from 'zod/mini';

import { LOAI_LOP, TRANG_THAI, type Form, type LopRow, formRong, formTuLop, tachEmail, thanForm } from './lop';

export type { LopRow };
export type ChonNguoi = { id: number; name: string | null; email: string };
export type ChonKhoa = { id: string; title: string };
type ChonDot = { id: number; name: string; code: string | null };

type HocVien = {
  userId: number;
  name: string;
  email: string;
  lessonsDone?: number;
  lessonsTotal?: number;
  /** Ngày vào lớp — chuyên cần tính theo nó, nên phải NHÌN THẤY (21/09/2026). */
  joinedAt?: string | null;
  left?: boolean;
};
/** Trợ giảng đang được gán vào lớp — `class_report.assistants`. */
type TroGiang = { userId: number; name: string | null; email: string };
/** Trả lời của `POST members {emails}` — từng email một, không gộp. */
type KetQuaThem = {
  added: { email: string; role: string | null }[];
  already: { email: string }[];
  missing: string[];
  /** Lớp GIA SƯ đã đủ 3 em (§54) — em ấy không vào, các em khác vẫn vào. */
  full?: { email: string }[];
};

/**
 * Lý do rời lớp — `teaching/vocab.py::LEAVE_REASONS`.
 *
 * Bản cũ KHÔNG hỏi lý do, luôn gửi `DELETE ?user_id=` trần, nên mọi lượt rời
 * lớp vào CSDL với `leave_reason = NULL`. Backend nói rõ trong chú thích của nó
 * vì sao chuyện đó tệ: "học xong" và "bỏ giữa chừng" là HAI con số khác nhau khi
 * trung tâm báo tỉ lệ bỏ học của một đợt, và gộp lại thì mọi lớp kết thúc đều
 * trông như bỏ học 100%. Backend đã sẵn sàng nhận lý do từ 31/08; chỉ thiếu chỗ
 * để người dùng nói ra.
 */
const LY_DO: { ma: string; nhan: string }[] = [
  { ma: 'completed', nhan: 'Học xong' },
  { ma: 'dropped', nhan: 'Bỏ giữa chừng' },
  { ma: 'transferred', nhan: 'Chuyển lớp' },
];

/**
 * Nhãn cho `willDelete` của backend (`teaching/views.py`, năm khoá đúng tên các
 * cột `AS members / sessions / attendance / assignments / submissions`).
 *
 * Có nhãn thì hộp thoại nói "Điểm danh: 12" thay vì "attendance: 12" — người
 * đọc nó là nhân viên học vụ, không phải người viết truy vấn. Khoá lạ vẫn hiện
 * nguyên (`?? k`): thêm một cột ở backend thì thà thấy tên kỹ thuật còn hơn
 * biến mất khỏi danh sách những thứ sắp mất.
 */
const NHAN_MAT: Record<string, string> = {
  members: 'Học viên trong lớp',
  sessions: 'Buổi học',
  attendance: 'Lượt điểm danh',
  assignments: 'Bài đã giao',
  submissions: 'Bài học viên đã nộp',
};

function ngay(iso: string | null) {
  if (!iso) return '—';
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

const O_CHUNG =
  'min-h-11 w-full min-w-0 rounded-md border border-line bg-surface px-3 text-input text-ink placeholder:text-ink-3/70';

type Props = {
  /** MỘT TRANG lớp theo bộ lọc trên URL (§54) — máy chủ lọc + phân trang. */
  initial: LopRow[];
  /** Bộ lọc + chip đếm + phân trang — dựng ở MÁY CHỦ (`BoLocLop.tsx`), form GET thuần. */
  boLoc?: ReactNode;
  phanTrang?: ReactNode;
  /** Có đang lọc không — để câu "chưa có lớp nào" không nói sai khi chỉ là lọc ra rỗng. */
  dangLoc?: boolean;
  giangVien: ChonNguoi[];
  /** Mọi tài khoản Trợ giảng — để ô "Gán trợ giảng" có gì mà chọn. */
  troGiang: ChonNguoi[];
  trangThai: string[];
  dotHoc: ChonDot[];
  khoaHoc: ChonKhoa[];
  loi: string | null;
};

export default function LopHocClient(props: Props) {
  return (
    <ToastProvider>
      <BangLop {...props} />
    </ToastProvider>
  );
}

function BangLop({ initial, boLoc, phanTrang, dangLoc = false, giangVien, troGiang, trangThai, dotHoc, khoaHoc, loi }: Props) {
  const toast = useToast();
  const router = useRouter();
  // Danh sách là MỘT TRANG do máy chủ lọc (§54): không giữ bản sao trong state —
  // sau mỗi lần ghi thì `router.refresh()` dựng lại trang với ĐÚNG bộ lọc đang xem.
  const lop = initial;
  const [err, setErr] = useState<string | null>(loi);
  const [busy, setBusy] = useState(false);

  /** `null` = biểu mẫu đóng; `0` = thêm mới; `>0` = đang sửa lớp id ấy. */
  const [dangSua, setDangSua] = useState<number | null>(null);
  const [form, setForm] = useState<Form>(formRong);

  const [lopMoRong, setLopMoRong] = useState<LopRow | null>(null);
  const [hocVien, setHocVien] = useState<HocVien[] | null>(null);
  const [troGiangLop, setTroGiangLop] = useState<TroGiang[]>([]);
  const [emailMoi, setEmailMoi] = useState('');
  /** Đang gửi "Thêm vào lớp". Là STATE chứ không phải ref vì nút phải ĐỔI MẶT:
      rà luồng 20/09/2026 đo được lượt bấm thứ hai bị nuốt lặng lẽ trong lúc
      báo cáo lớp tải lại (nút vẫn sáng, không báo gì) — 1/3 em vào lớp. */
  const [dangThem, setDangThem] = useState(false);
  const [tgChon, setTgChon] = useState('');
  /** Ngày vào lớp thật cho em ghi danh muộn — rỗng = hôm nay (máy chủ ghi lúc bấm). */
  const [ngayVao, setNgayVao] = useState('');
  /** Mật khẩu tạm vừa cấp — hiện đúng một lần trong hộp, không lưu ở đâu khác. */
  const [mkTam, setMkTam] = useState<{ ten: string; matKhau: string } | null>(null);
  /** userId đang chạy lượt đặt lại mật khẩu — khoá nút để không bấm hai lần. */
  const [dangDatLai, setDangDatLai] = useState<number | null>(null);

  // `setBusy` của React không có tác dụng NGAY, nên hai cú bấm liền nhau đều
  // lọt qua `if (busy) return`. Với nút "Lưu" của một biểu mẫu tạo lớp thì đó
  // là hai lớp trùng tên trong CSDL. `useRef` đổi giá trị đồng bộ nên chặn thật.
  const dangGui = useRef(false);

  const dat = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  async function nap() {
    router.refresh();
  }

  async function luu() {
    if (dangGui.current) return;
    // Ô SỐ gõ sai thì dừng NGAY Ở ĐÂY, đừng gửi. `JSON.stringify(NaN)` là
    // `null`, và backend đọc `null` đúng như đọc một ô người dùng CỐ Ý xoá —
    // nên gõ "25 em" vào ô Sĩ số sẽ xoá trắng sĩ số và báo thành công.
    // Xem chú thích dài ở `lop.ts::thanForm`.
    const { body, loi: loiSo } = thanForm(form);
    if (loiSo) {
      setErr(loiSo);
      return;
    }
    dangGui.current = true;
    setBusy(true);
    setErr(null);
    try {
      const moi = dangSua === 0;
      const r = await apiFetch(moi ? '/api/admin/classes' : `/api/admin/classes/${dangSua}`, {
        method: moi ? 'POST' : 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      setDangSua(null);
      setForm(formRong());
      // Bảng tải lại mất vài giây (Neon); không có câu này thì người dùng
      // không biết lớp đã vào CSDL hay chưa và bấm "Tạo lớp" lần nữa.
      toast(moi ? `Đã tạo lớp "${form.name}".` : `Đã lưu lớp "${form.name}".`, 'ok');
      await nap();
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không lưu được lớp'));
    } finally {
      dangGui.current = false;
      setBusy(false);
    }
  }

  /**
   * Xoá lớp — HAI BƯỚC khi lớp còn dữ liệu.
   *
   * Backend trả 409 kèm `needsConfirm` và `willDelete` (đếm từng loại: thành
   * viên, buổi học, điểm danh, bài giao, bài nộp), rồi mới nhận `?confirm=1`.
   *
   * Bản đầu của màn hình này KHÔNG gửi bước hai — nó ném thẳng câu 409 ra dải
   * đỏ và dừng. Tức nút Xoá là NGÕ CỤT với mọi lớp còn dữ liệu, mà lớp duy nhất
   * đang tồn tại trên CSDL thật có 4 thành viên. Trang anh em `dot-hoc` xử lý
   * đúng luật này; ở đây tôi chép được nửa đầu và bỏ nửa sau.
   *
   * Hộp thoại thứ hai liệt kê ĐÚNG con số backend đếm, không đoán lại: người
   * đang đọc nó cần biết chính xác cái gì mất trước khi gật.
   */
  async function xoa(c: LopRow) {
    // Hỏi TRƯỚC khi gửi. Dữ liệu học tập của từng em KHÔNG mất — nó nằm ở
    // `learning_events`/`lesson_progress`, gắn với tài khoản chứ không gắn với
    // lớp. Cái mất là danh sách lớp, điểm danh và bài giao của lớp.
    if (
      !confirm(
        `Xoá lớp "${c.name}"?\n\n` +
          'Tiến độ học của từng em KHÔNG mất — nó gắn với tài khoản, không gắn với lớp.\n' +
          'Muốn đóng lớp mà giữ lịch sử thì đổi trạng thái sang “Đã kết thúc” thay vì xoá.',
      )
    )
      return;
    setErr(null);
    try {
      const r = await apiFetch(`/api/admin/classes/${c.id}`, { method: 'DELETE' });
      const d = (await r.json().catch(() => ({}))) as {
        needsConfirm?: boolean;
        willDelete?: Record<string, number>;
        hint?: string;
      };
      if (r.status === 409 && d.needsConfirm) {
        const ke = Object.entries(d.willDelete ?? {})
          .filter(([, n]) => n > 0)
          .map(([k, n]) => `  · ${NHAN_MAT[k] ?? k}: ${n}`)
          .join('\n');
        if (!confirm(`Lớp "${c.name}" còn dữ liệu. Xoá là mất hẳn:\n\n${ke}\n\nVẫn xoá?`)) return;
        const r2 = await apiFetch(`/api/admin/classes/${c.id}?confirm=1`, { method: 'DELETE' });
        const d2 = await r2.json().catch(() => ({}));
        if (!r2.ok) throw new Error(errorText(r2.status, d2));
      } else if (!r.ok) {
        throw new Error(errorText(r.status, d));
      }
      if (lopMoRong?.id === c.id) {
        setLopMoRong(null);
        setHocVien(null);
      }
      await nap();
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không xoá được lớp'));
    }
  }

  async function moHocVien(c: LopRow) {
    setLopMoRong(c);
    // `null` = đang tải. Báo cáo lớp tính tiến độ từng em nên mất vài giây;
    // không có dòng chờ thì người dùng tưởng nút hỏng và bấm lại.
    setHocVien(null);
    setErr(null);
    try {
      const r = await apiFetch(`/api/teach/classes/${c.id}`);
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      setHocVien((d.students as HocVien[]) ?? []);
      setTroGiangLop((d.assistants as TroGiang[]) ?? []);
    } catch (e) {
      setHocVien([]);
      setErr(loiBatDuoc(e, 'Không tải được danh sách học viên'));
    }
  }

  async function themHocVien() {
    if (!lopMoRong || dangGui.current) return;
    const emails = tachEmail(emailMoi);
    if (!emails.length) return;
    dangGui.current = true;
    setDangThem(true);
    setErr(null);
    try {
      const r = await apiFetch(`/api/admin/classes/${lopMoRong.id}/members`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ emails, ...(ngayVao ? { joined_at: ngayVao } : {}) }),
      });
      const d = (await r.json().catch(() => ({}))) as Partial<KetQuaThem> & { error?: string };
      if (!r.ok) throw new Error(errorText(r.status, d));
      const kq = { added: d.added ?? [], already: d.already ?? [], missing: d.missing ?? [] };
      // Email KHÔNG có tài khoản ở lại trong ô để người dùng sửa chính tả hoặc
      // mang sang trang Tài khoản — không bắt gõ lại.
      setEmailMoi(kq.missing.join('\n'));
      const tg = kq.added.filter((a) => a.role === 'Trợ giảng').length;
      const em = kq.added.length - tg;
      const cau = [
        em ? `Đã thêm ${em} học viên.` : '',
        tg ? `Đã gán ${tg} trợ giảng.` : '',
        kq.already.length ? `${kq.already.length} đã ở trong lớp.` : '',
        kq.missing.length
          ? `${kq.missing.length} email chưa có tài khoản (tạo ở trang Tài khoản rồi thêm lại).`
          : '',
        (d.full ?? []).length ? `${(d.full ?? []).length} em chưa vào được: lớp gia sư đã đủ 3 em.` : '',
      ].filter(Boolean);
      toast(cau.join(' '), kq.added.length ? 'ok' : kq.missing.length ? 'error' : 'info');
      await Promise.all([moHocVien(lopMoRong), nap()]);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không thêm được học viên'));
    } finally {
      dangGui.current = false;
      setDangThem(false);
    }
  }

  async function ganTroGiang() {
    if (!lopMoRong || !tgChon || dangGui.current) return;
    dangGui.current = true;
    setDangThem(true);
    setErr(null);
    try {
      const r = await apiFetch(`/api/admin/classes/${lopMoRong.id}/members`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: Number(tgChon) }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      const nguoi = troGiang.find((t) => String(t.id) === tgChon);
      toast(`Đã gán ${nguoi?.name ?? 'trợ giảng'} vào lớp.`, 'ok');
      setTgChon('');
      // Hiện thẻ NGAY: báo cáo lớp tải lại mất vài giây, và trong lúc đó khu
      // này không có dòng "đang tải" nào — thẻ cũ đứng im trông như chưa gán.
      if (nguoi) {
        setTroGiangLop((ds) => [...ds, { userId: nguoi.id, name: nguoi.name, email: nguoi.email }]);
      }
      await moHocVien(lopMoRong);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không gán được trợ giảng'));
    } finally {
      dangGui.current = false;
      setDangThem(false);
    }
  }

  /**
   * Đặt lại mật khẩu cho một em ngay trong danh sách lớp (20/09/2026, anh Sơn
   * chốt mở cho học vụ). Cùng endpoint và cùng hộp hiện mật khẩu tạm với trang
   * Tài khoản; đặt ở đây vì học vụ không có tab Tài khoản, và "em quên mật
   * khẩu" là chuyện xảy ra khi đang nhìn danh sách lớp.
   */
  async function datLaiMatKhau(s: HocVien) {
    if (!confirm(`Đặt lại mật khẩu cho "${s.name}"?\n\nMật khẩu cũ của em ngừng hoạt động ngay lập tức.`)) return;
    setErr(null);
    /* KHOÁ NÚT trong lúc chạy (21/09/2026). Rà vai học vụ đo: lượt đặt lại mất
       20–29 s mà nút không đổi mặt → bấm lần hai là hai mật khẩu tạm, và cái
       vừa đọc cho em chết ngay. Máy chủ nay nhanh hơn nhiều (`_thu_hoi_refresh`
       gộp một lượt), nhưng mạng vẫn có độ trễ nên nút vẫn phải nói nó đang bận. */
    setDangDatLai(s.userId);
    try {
      const d = await ghiJson(`/api/admin/users/${s.userId}/reset-password`, { method: 'POST' },
        z.looseObject({ tempPassword: z.string() }));
      setMkTam({ ten: s.name, matKhau: d.tempPassword });
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không đặt lại được mật khẩu'));
    } finally {
      setDangDatLai(null);
    }
  }

  async function goTroGiang(t: TroGiang) {
    if (!lopMoRong) return;
    if (!confirm(`Gỡ trợ giảng "${t.name ?? t.email}" khỏi lớp này?`)) return;
    setErr(null);
    try {
      const r = await apiFetch(`/api/admin/classes/${lopMoRong.id}/members?user_id=${t.userId}`, {
        method: 'DELETE',
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      toast(`Đã gỡ ${t.name ?? t.email} khỏi lớp.`, 'ok');
      setTroGiangLop((ds) => ds.filter((g) => g.userId !== t.userId));
      await moHocVien(lopMoRong);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không gỡ được trợ giảng'));
    }
  }

  async function choRoiLop(s: HocVien, lyDo: string) {
    if (!lopMoRong) return;
    setErr(null);
    try {
      const r = await apiFetch(
        `/api/admin/classes/${lopMoRong.id}/members?user_id=${s.userId}&leave_reason=${lyDo}`,
        { method: 'DELETE' },
      );
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errorText(r.status, d));
      await Promise.all([moHocVien(lopMoRong), nap()]);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không cập nhật được'));
    }
  }

  /** Ô SỐ. `inputMode` mở bàn phím số trên điện thoại; `type=number` chặn được
      phần lớn ca gõ nhầm ngay trên trình duyệt. Hàng rào thật vẫn ở
      `thanForm` — `type=number` không chặn được dán chuỗi trong mọi trình duyệt. */
  const oSo = (k: string, nhan: string, goi?: string) => (
    <label className="flex flex-col gap-1">
      <span className="text-label text-ink-3">{nhan}</span>
      <input
        value={form[k] ?? ''}
        onChange={(e) => dat(k, e.target.value)}
        type="number"
        inputMode="numeric"
        min={0}
        placeholder={goi}
        className={O_CHUNG}
      />
    </label>
  );

  const oChu = (k: string, nhan: string, goi?: string) => (
    <label className="flex flex-col gap-1">
      <span className="text-label text-ink-3">{nhan}</span>
      <input
        value={form[k] ?? ''}
        onChange={(e) => dat(k, e.target.value)}
        placeholder={goi}
        className={O_CHUNG}
      />
    </label>
  );

  const oNgay = (k: string, nhan: string) => (
    <label className="flex flex-col gap-1">
      <span className="text-label text-ink-3">{nhan}</span>
      <input
        type="date"
        value={form[k] ?? ''}
        onChange={(e) => dat(k, e.target.value)}
        className={O_CHUNG}
      />
    </label>
  );

  const oChon = (k: string, nhan: string, muc: { gt: string; nhan: string }[]) => (
    <label className="flex flex-col gap-1">
      <span className="text-label text-ink-3">{nhan}</span>
      <select
        value={form[k] ?? ''}
        onChange={(e) => dat(k, e.target.value)}
        className={O_CHUNG}
      >
        {muc.map((m) => (
          <option key={m.gt} value={m.gt}>
            {m.nhan}
          </option>
        ))}
      </select>
    </label>
  );

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHead
          title="Lớp học"
          hint="Học viên phải được xếp lớp thì mới được điểm danh, giao bài."
          action={
            dangSua === null && (
              <Button
                onClick={() => {
                  setForm(formRong());
                  setDangSua(0);
                }}
              >
                Thêm lớp
              </Button>
            )
          }
        />

        {err && (
          <p
            role="alert"
            className="mb-3 rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink"
          >
            {err}
          </p>
        )}

        {dangSua !== null && (
          <div role="group" aria-labelledby="lop-form-tieu-de" className="mb-4 rounded-md border border-line bg-sunken p-4">
            <h3 id="lop-form-tieu-de" className="mb-3 text-label text-ink">
              {dangSua === 0 ? 'Thêm lớp' : `Sửa lớp: ${form.name || '(chưa đặt tên)'}`}
            </h3>
            <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr))]">
              {oChu('name', 'Tên lớp', 'Luyện HSA đợt 1/2027 — Ca tối')}
              {oChon('classType', 'Loại lớp', [
                { gt: 'nhom', nhan: LOAI_LOP.nhom },
                { gt: 'gia_su', nhan: `${LOAI_LOP.gia_su} (1–3 em)` },
              ])}
              {oChu('code', 'Mã lớp (không bắt buộc)', 'HSA-01')}
              {oChon('course', 'Môn học', [
                { gt: '', nhan: '(cả ba môn)' },
                ...khoaHoc.map((k) => ({ gt: k.id, nhan: k.title })),
              ])}
              {oChon('teacherId', 'Giảng viên', [
                { gt: '', nhan: '(chưa gán)' },
                ...giangVien.map((g) => ({ gt: String(g.id), nhan: g.name || g.email })),
              ])}
              {oChon('termId', 'Đợt học', [
                { gt: '', nhan: '(chưa thuộc đợt nào)' },
                ...dotHoc.map((d) => ({
                  gt: String(d.id),
                  nhan: d.code ? `${d.name} (${d.code})` : d.name,
                })),
              ])}
              {oChon(
                'status',
                'Trạng thái',
                trangThai.map((s) => ({ gt: s, nhan: TRANG_THAI[s]?.nhan ?? s })),
              )}
              {oChu('schedule', 'Lịch học', 'T3–T5 19:30')}
              {oSo('capacity', 'Sĩ số tối đa', '30')}
              {oNgay('startsOn', 'Khai giảng')}
              {oNgay('endsOn', 'Kết thúc')}
              {oNgay('examDate', 'Ngày thi')}
              {oChon('mode', 'Hình thức', [
                { gt: '', nhan: '(chưa đặt)' },
                { gt: 'online', nhan: NHAN_HINH_THUC.online },
                { gt: 'offline', nhan: NHAN_HINH_THUC.offline },
              ])}
              {oChu('room', 'Phòng (lớp tại trung tâm)', 'P201')}
              {oChu('meetingUrl', 'Link họp', 'https://meet.google.com/...')}
              {oChu('note', 'Ghi chú')}
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button loading={busy} disabled={!(form.name ?? '').trim()} onClick={() => void luu()}>
                {dangSua === 0 ? 'Tạo lớp' : 'Lưu thay đổi'}
              </Button>
              <Button variant="ghost" onClick={() => setDangSua(null)}>
                Huỷ
              </Button>
            </div>
          </div>
        )}

        {boLoc}

        {lop.length === 0 ? (
          dangLoc ? (
            <EmptyState title="Không có lớp khớp bộ lọc" hint="Bỏ bớt điều kiện lọc, hoặc tìm bằng tên khác." />
          ) : (
            <EmptyState
              title="Chưa có lớp nào"
              hint="Tạo lớp đầu tiên, rồi bấm “Học viên” để xếp các em vào."
            />
          )
        ) : (
          <TableWrap caption="Các lớp của trung tâm, kèm giảng viên phụ trách và sĩ số hiện tại">
            <Thead>
              <tr>
                <Th>Lớp</Th>
                <Th>Môn học</Th>
                <Th>Giảng viên</Th>
                <Th>Lịch</Th>
                <Th align="right">Sĩ số</Th>
                <Th>Trạng thái</Th>
                <Th align="right">Thao tác</Th>
              </tr>
            </Thead>
            <Tbody>
              {lop.map((c) => (
                <Tr key={c.id} dim={c.status === 'finished'}>
                  <Td label="Lớp">
                    <span className="font-semibold text-ink">{c.name}</span>
                    {c.classType === 'gia_su' && <> <Chip tone="brand">{LOAI_LOP.gia_su}</Chip></>}
                    <span className="block text-ink-3">
                      {[c.code, c.termName].filter(Boolean).join(' · ') || '—'}
                    </span>
                    {/* Lớp gia sư: tên EM là thứ người ta tìm ("lớp của em An"). */}
                    {(c.studentNames ?? []).length > 0 && (
                      <span className="block text-ink-2">Em: {(c.studentNames ?? []).join(', ')}</span>
                    )}
                  </Td>
                  <Td label="Môn học" muted>
                    {c.courseTitle ?? 'Cả ba môn'}
                  </Td>
                  <Td label="Giảng viên" muted>
                    {c.teacherName ?? '(chưa gán)'}
                    {(c.assistantNames ?? []).length > 0 && (
                      <span className="block">TG: {(c.assistantNames ?? []).join(', ')}</span>
                    )}
                  </Td>
                  <Td label="Lịch" muted>
                    {c.schedule || '—'}
                    {noiHoc(c.mode, c.room) && <span className="block text-ink-3">{noiHoc(c.mode, c.room)}</span>}
                    {c.startsOn && <span className="block text-ink-3">từ {ngay(c.startsOn)}</span>}
                  </Td>
                  <Td label="Sĩ số" num>
                    {c.members}
                    {c.capacity ? `/${c.capacity}` : ''}
                  </Td>
                  <Td label="Trạng thái">
                    <Chip tone={TRANG_THAI[c.status]?.tone ?? 'neutral'}>
                      {TRANG_THAI[c.status]?.nhan ?? c.status}
                    </Chip>
                  </Td>
                  <Td label="Thao tác">
                    <span className="flex flex-wrap justify-end gap-2">
                      <Button size="sm" variant="ghost" onClick={() => void moHocVien(c)}>
                        Học viên
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          // Đổ ĐỦ mọi trường. Bản cũ đổ 7/11 rồi gửi cả 11, nên
                          // sửa tên lớp là xoá trắng link họp và ghi chú.
                          setForm(formTuLop(c));
                          setDangSua(c.id);
                        }}
                      >
                        Sửa
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => void xoa(c)}>
                        Xoá
                      </Button>
                    </span>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </TableWrap>
        )}
        {phanTrang}
      </Card>

      <Modal
        open={mkTam !== null}
        onClose={() => setMkTam(null)}
        title={mkTam ? `Mật khẩu tạm của ${mkTam.ten}` : ''}
        footer={
          <>
            <Button variant="ghost" onClick={() => { if (mkTam) void navigator.clipboard?.writeText(mkTam.matKhau); }}>
              Chép
            </Button>
            <Button onClick={() => setMkTam(null)}>Đã đọc xong</Button>
          </>
        }
      >
        <p className="mb-3 text-body text-ink-2">
          Đọc chuỗi này cho em. Lần đăng nhập đầu, hệ thống bắt em đặt mật khẩu mới rồi mới vào học.
        </p>
        <p className="rounded-md bg-sunken px-4 py-3 text-center font-mono text-title tracking-wide text-ink select-all">
          {mkTam?.matKhau}
        </p>
        <p className="mt-3 text-small text-ink-3">
          Chuỗi này chỉ hiện đúng một lần — hệ thống không lưu lại dạng đọc được. Cần xem lại thì
          phải đặt lại lần nữa.
        </p>
      </Modal>

      {lopMoRong && (
        /* Cuộn tới khu vừa mở (20/09/2026): ở 390px bảng lớp xếp thành thẻ nên
           khu Học viên nằm ở y ≈ 1.590px — bấm "Học viên" xong màn không đổi gì.
           `key` theo lớp để mở lớp khác thì cuộn lại. */
        <div
          key={`hv-${lopMoRong.id}`}
          className="scroll-mt-[calc(var(--topbar-h)+1rem)]"
          ref={(el) => {
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }}
        >
        <Card>
          <CardHead
            title={`Học viên lớp: ${lopMoRong.name}`}
            hint="Rời lớp KHÔNG xoá dữ liệu học tập — em vẫn còn trong báo cáo của đợt đó, kèm lý do rời."
            action={
              <Button
                variant="ghost"
                onClick={() => {
                  setLopMoRong(null);
                  setHocVien(null);
                }}
              >
                Đóng
              </Button>
            }
          />

          <div className="mb-4 flex flex-wrap items-end gap-2">
            <label className="flex min-w-60 flex-1 flex-col gap-1">
              <span className="text-label text-ink-3">Email học viên</span>
              {/* textarea chứ không phải input: dán một cột email từ bảng tính
                  vào <input> là mất hết dấu xuống dòng — 30 email dính thành
                  một chuỗi. Ctrl+Enter gửi; Enter xuống dòng như mọi ô dán. */}
              <textarea
                value={emailMoi}
                rows={emailMoi.includes('\n') ? 4 : 1}
                autoComplete="off"
                onChange={(e) => setEmailMoi(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey || !emailMoi.includes('\n'))) {
                    e.preventDefault();
                    void themHocVien();
                  }
                }}
                placeholder="hocvien@example.com — dán nhiều email, mỗi dòng một em"
                className={`${O_CHUNG} py-2.5 leading-snug`}
              />
            </label>
            <Button disabled={!emailMoi.trim() || dangThem} onClick={() => void themHocVien()}>
              {dangThem ? 'Đang thêm…' : 'Thêm vào lớp'}
            </Button>
          </div>
          {/* Lớp đã khai giảng: em nhập hôm nay có thể đã học từ trước. Ngày vào
              lớp là mẫu số chuyên cần của em — để mặc định "hôm nay" thì mọi
              buổi trước đó biến mất khỏi tờ phụ huynh của em (rà 20/09/2026). */}
          {lopMoRong.startsOn && lopMoRong.startsOn < new Date().toISOString().slice(0, 10) && (
            <label className="mb-4 flex flex-wrap items-center gap-2 text-small text-ink-2">
              <span>
                Lớp đã khai giảng {ngay(lopMoRong.startsOn)}. Em vào lớp từ ngày
              </span>
              <input
                type="date"
                value={ngayVao}
                min={lopMoRong.startsOn}
                max={new Date().toISOString().slice(0, 10)}
                onChange={(e) => setNgayVao(e.target.value)}
                aria-label="Ngày vào lớp"
                className={`${O_CHUNG} w-auto min-w-40`}
              />
              <span className="text-ink-3">(để trống = hôm nay; chọn ngày khai giảng nếu em học từ đầu)</span>
            </label>
          )}

          {/* Trợ giảng của lớp. Trước 20/09/2026 màn này không có chữ "trợ
              giảng" nào: gán được (qua ô email ở trên) nhưng gán xong thì họ
              biến mất — không nằm trong sĩ số, không có chỗ gỡ. */}
          <div className="mb-4 rounded-md border border-line bg-sunken p-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-label text-ink-3">Trợ giảng của lớp:</span>
              {troGiangLop.length === 0 && (
                <span className="text-small text-ink-3">chưa gán</span>
              )}
              {troGiangLop.map((t) => (
                <span
                  key={t.userId}
                  className="inline-flex items-center gap-1 rounded-full border border-line bg-surface pl-3 text-small text-ink"
                >
                  {t.name ?? t.email}
                  {/* Vùng chạm ≥ 44px: dấu × trần đo được 16×22 ở 390px (rà 20/09). */}
                  <button
                    type="button"
                    aria-label={`Gỡ trợ giảng ${t.name ?? t.email} khỏi lớp`}
                    className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-full text-ink-3 hover:text-danger"
                    onClick={() => void goTroGiang(t)}
                  >
                    ×
                  </button>
                </span>
              ))}
              <label className="ml-auto flex items-center gap-2">
                <span className="sr-only">Chọn trợ giảng để gán</span>
                <select
                  value={tgChon}
                  onChange={(e) => setTgChon(e.target.value)}
                  className={`${O_CHUNG} min-w-52`}
                >
                  <option value="">— gán thêm trợ giảng —</option>
                  {troGiang
                    .filter((t) => !troGiangLop.some((g) => g.userId === t.id))
                    .map((t) => (
                      <option key={t.id} value={String(t.id)}>
                        {t.name ?? t.email}
                      </option>
                    ))}
                </select>
                <Button size="sm" disabled={!tgChon || dangThem} onClick={() => void ganTroGiang()}>
                  Gán
                </Button>
              </label>
            </div>
            {troGiang.length === 0 && (
              <p className="mt-2 text-small text-ink-3">
                Chưa có tài khoản Trợ giảng nào — quản trị viên cấp ở trang Tài khoản.
              </p>
            )}
          </div>

          {hocVien === null ? (
            <p className="text-small text-ink-3">Đang tải danh sách học viên…</p>
          ) : hocVien.length === 0 ? (
            <EmptyState
              title="Lớp chưa có học viên"
              hint="Dán danh sách email (mỗi dòng một em) rồi bấm “Thêm vào lớp”. Tài khoản phải có sẵn — trang Tài khoản là nơi tạo."
            />
          ) : (
            <TableWrap caption={`Học viên của lớp ${lopMoRong.name}`}>
              <Thead>
                <tr>
                  <Th>Học viên</Th>
                  <Th>Email</Th>
                  {/* Trước 21/09/2026 không màn nào hiện ngày này, trong khi ô
                      "Ngày vào lớp" ở khối thêm học viên lại ghi nó và mẫu số
                      chuyên cần đếm từ nó — người dùng không có cách nào biết
                      mình vừa đặt đúng hay chưa. */}
                  <Th>Vào lớp</Th>
                  <Th align="right">Bài đã học</Th>
                  <Th>Tình trạng</Th>
                  <Th align="right">Mật khẩu</Th>
                  <Th align="right">Cho rời lớp</Th>
                </tr>
              </Thead>
              <Tbody>
                {hocVien.map((s) => (
                  <Tr key={s.userId} dim={s.left}>
                    <Td label="Học viên">{s.name}</Td>
                    <Td label="Email" muted>
                      {s.email}
                    </Td>
                    <Td label="Vào lớp" muted>
                      {/* `joinedAt` là ISO đầy đủ; `ngay()` nhận YYYY-MM-DD. */}
                      {s.joinedAt ? ngay(s.joinedAt.slice(0, 10)) : '—'}
                    </Td>
                    <Td label="Bài đã học" num>
                      {s.lessonsDone ?? 0}/{s.lessonsTotal ?? 0}
                    </Td>
                    <Td label="Tình trạng">
                      <Chip tone={s.left ? 'neutral' : 'good'}>
                        {s.left ? 'đã rời lớp' : 'đang học'}
                      </Chip>
                    </Td>
                    <Td label="Mật khẩu">
                      <Button
                        size="sm"
                        variant="ghost"
                        loading={dangDatLai === s.userId}
                        disabled={s.left || dangDatLai !== null}
                        onClick={() => void datLaiMatKhau(s)}
                      >
                        {dangDatLai === s.userId ? 'Đang đặt lại…' : 'Đặt lại'}
                      </Button>
                    </Td>
                    <Td label="Cho rời lớp">
                      {/* Bắt CHỌN LÝ DO chứ không có nút "rời lớp" trần: xem
                          chú thích ở `LY_DO`. Ô về lại "—" sau mỗi lần chọn nên
                          nó không bao giờ trông như một trạng thái đang lưu. */}
                      <select
                        value=""
                        disabled={s.left}
                        aria-label={`Cho ${s.name} rời lớp, kèm lý do`}
                        onChange={(e) => {
                          const ly = e.target.value;
                          e.currentTarget.value = '';
                          if (!ly) return;
                          const nhan = LY_DO.find((l) => l.ma === ly)?.nhan ?? ly;
                          if (
                            !confirm(
                              `Cho "${s.name}" rời lớp với lý do "${nhan}"?\n\n` +
                                'Dữ liệu học tập của em vẫn giữ nguyên.',
                            )
                          )
                            return;
                          void choRoiLop(s, ly);
                        }}
                        className="min-h-11 max-w-full min-w-0 rounded-md border border-line-input bg-sunken px-2 text-small text-ink"
                      >
                        <option value="">— chọn lý do —</option>
                        {LY_DO.map((l) => (
                          <option key={l.ma} value={l.ma}>
                            {l.nhan}
                          </option>
                        ))}
                      </select>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </TableWrap>
          )}
        </Card>
        </div>
      )}
    </div>
  );
}
