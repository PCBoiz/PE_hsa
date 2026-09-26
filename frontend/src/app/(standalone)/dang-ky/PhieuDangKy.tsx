'use client';

import { useState } from 'react';

import { Button, Field } from '@/components/ui';
import { CAU_MAT_MANG, CAU_QUA_NHIEU, MK_TOI_THIEU, type OPhieu } from '@/lib/dangKy';
import { useDaGan } from '@/lib/daGan';
import { oChu } from '@/lib/form';

/**
 * Phiếu đăng ký của học viên mới (§73).
 *
 * ── BA ĐIỀU CỐ Ý ───────────────────────────────────────────────────────────
 *
 * · NÚT BỊ KHOÁ TỚI KHI REACT GẮN XONG (`useDaGan`). Biểu mẫu này có ô mật khẩu:
 *   theo đặc tả HTML, biểu mẫu có nút mặc định `disabled` thì Enter không gửi ngầm
 *   — không có hàng rào ấy, Enter trước lượt hydrate là trình duyệt tự gửi GET và
 *   `?password=…` lên thẳng thanh địa chỉ (đo được trên production 20/09/2026).
 * · MÁY CHỦ TRẢ MỘT CÂU CHO MỌI TRƯỜNG HỢP (có tài khoản hay không, trùng số điện
 *   thoại hay không). Màn hiện NGUYÊN câu ấy, KHÔNG tự thêm "đã gửi tới bạn" hay
 *   "email này đã dùng" — đó chính là thứ máy chủ cố ý không nói ra, vì một câu
 *   "email đã được sử dụng" là công cụ dò xem ai đang học ở TopHSA.
 * · MẬT KHẨU KIỂM ĐỘ DÀI NGAY TẠI ĐÂY nhưng máy chủ vẫn kiểm lại; phép kiểm phía
 *   trình duyệt chỉ để em không phải chờ một vòng gọi mạng cho một lỗi gõ.
 */
export default function PhieuDangKy({ nguon }: { nguon: { ma: string; nhan: string }[] }) {
  const daGan = useDaGan();
  const [dangGui, setDangGui] = useState(false);
  const [loi, setLoi] = useState<Partial<Record<OPhieu, string>>>({});
  const [loiChung, setLoiChung] = useState<string | null>(null);
  const [daGui, setDaGui] = useState<string | null>(null);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoi({});
    setLoiChung(null);
    const f = new FormData(e.currentTarget);
    const than = {
      name: oChu(f, 'name'),
      email: oChu(f, 'email'),
      phone: oChu(f, 'phone'),
      password: oChu(f, 'password'),
      nguon: oChu(f, 'nguon'),
      truong: oChu(f, 'truong'),
      lopOTruong: oChu(f, 'lopOTruong'),
      mucTieu: oChu(f, 'mucTieu'),
    };
    const cucBo: Partial<Record<OPhieu, string>> = {};
    if (!than.name.trim()) cucBo.name = 'Nhập họ tên của bạn.';
    if (!than.email.includes('@')) {
      cucBo.email = 'Nhập địa chỉ email, ví dụ an.nguyen@gmail.com — thư xác nhận gửi tới đó.';
    }
    if (!than.phone.trim()) cucBo.phone = 'Nhập số điện thoại để học vụ gọi lại xếp lớp.';
    if (than.password.length < MK_TOI_THIEU) {
      cucBo.password = `Mật khẩu cần ít nhất ${MK_TOI_THIEU} ký tự.`;
    }
    if (oChu(f, 'xacNhanMk') !== than.password) {
      cucBo.password = 'Hai lần nhập mật khẩu chưa khớp nhau.';
    }
    if (!than.nguon) cucBo.nguon = 'Chọn một mục trong danh sách.';
    const o = (['name', 'email', 'phone', 'password', 'nguon'] as OPhieu[]).find((k) => cucBo[k]);
    if (o) {
      setLoi(cucBo);
      document.getElementById(`dk-${o}`)?.focus();
      return;
    }

    setDangGui(true);
    try {
      const r = await fetch('/auth/dang-ky', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(than),
      });
      const d = (await r.json().catch(() => ({}))) as {
        message?: unknown;
        errors?: Record<string, unknown>;
      };
      if (r.status === 429) {
        setLoiChung(CAU_QUA_NHIEU);
      } else if (!r.ok) {
        const e = d?.errors;
        if (e && typeof e === 'object') {
          const map: Partial<Record<OPhieu, string>> = {};
          for (const k of ['name', 'email', 'phone', 'password', 'nguon'] as OPhieu[]) {
            if (typeof e[k] === 'string') map[k] = e[k] as string;
          }
          if (Object.keys(map).length) {
            setLoi(map);
            const dau = (['name', 'email', 'phone', 'password', 'nguon'] as OPhieu[]).find(
              (k) => map[k],
            );
            if (dau) document.getElementById(`dk-${dau}`)?.focus();
          } else {
            setLoiChung('Chưa gửi được phiếu đăng ký. Thử lại sau ít phút.');
          }
        } else {
          setLoiChung('Chưa gửi được phiếu đăng ký. Thử lại sau ít phút.');
        }
      } else {
        setDaGui(typeof d?.message === 'string' ? d.message : 'Đã nhận thông tin đăng ký.');
      }
    } catch {
      setLoiChung(CAU_MAT_MANG);
    } finally {
      setDangGui(false);
    }
  }

  if (daGui) {
    return (
      <div
        role="status"
        data-khu="da-gui"
        className="rounded-md border-l-[3px] border-brand bg-brand-soft px-4 py-3"
      >
        <p className="text-body text-ink-2">{daGui}</p>
      </div>
    );
  }

  return (
    <form onSubmit={(e) => void submit(e)} noValidate className="flex flex-col gap-5">
      {loiChung && (
        <p
          role="alert"
          className="rounded-md border-l-[3px] border-danger bg-danger/10 px-4 py-3 text-body text-ink-2"
        >
          {loiChung}
        </p>
      )}

      <Field
        id="dk-name"
        name="name"
        label="Họ và tên"
        autoComplete="name"
        error={loi.name}
        required
      />
      <Field
        id="dk-email"
        name="email"
        type="email"
        inputMode="email"
        autoComplete="email"
        label="Email"
        hint="Thư xác nhận sẽ gửi tới đây. Đây cũng là địa chỉ để bạn tự lấy lại mật khẩu."
        error={loi.email}
        spellCheck={false}
        required
      />
      <Field
        id="dk-phone"
        name="phone"
        type="tel"
        inputMode="tel"
        autoComplete="tel"
        label="Số điện thoại"
        hint="Học vụ gọi số này để tư vấn và xếp lớp."
        error={loi.phone}
        required
      />
      <Field
        id="dk-password"
        name="password"
        type="password"
        autoComplete="new-password"
        label="Mật khẩu"
        hint={`Ít nhất ${MK_TOI_THIEU} ký tự. Chọn thứ bạn nhớ được mà người khác không đoán ra.`}
        error={loi.password}
        required
      />
      <Field
        id="dk-xacNhanMk"
        name="xacNhanMk"
        type="password"
        autoComplete="new-password"
        label="Nhập lại mật khẩu"
        required
      />

      <div className="flex flex-col gap-2">
        <label htmlFor="dk-nguon" className="text-label text-ink-3">
          Bạn biết TopHSA từ đâu?
        </label>
        <select
          id="dk-nguon"
          name="nguon"
          defaultValue=""
          aria-invalid={loi.nguon ? true : undefined}
          aria-describedby={loi.nguon ? 'dk-nguon-error' : undefined}
          className={[
            'min-h-11 w-full rounded-md border bg-sunken px-3 text-input text-ink',
            'focus:outline-2 focus:outline-brand',
            loi.nguon ? 'border-danger' : 'border-line-input',
          ].join(' ')}
        >
          <option value="">— Chọn —</option>
          {nguon.map((n) => (
            <option key={n.ma} value={n.ma}>
              {n.nhan}
            </option>
          ))}
        </select>
        {loi.nguon && (
          <p id="dk-nguon-error" role="alert" className="text-small text-danger">
            {loi.nguon}
          </p>
        )}
      </div>

      <Field
        id="dk-truong"
        name="truong"
        label="Trường đang học (không bắt buộc)"
        autoComplete="organization"
        />
      <Field
        id="dk-lopOTruong"
        name="lopOTruong"
        label="Lớp ở trường (không bắt buộc)"
        placeholder="Ví dụ: 12A1"
      />
      <Field
        id="dk-mucTieu"
        name="mucTieu"
        label="Mục tiêu của bạn (không bắt buộc)"
        placeholder="Ví dụ: thi HSA đạt 100 điểm"
      />

      <Button type="submit" full loading={dangGui} disabled={!daGan}>
        {dangGui ? 'Đang gửi…' : 'Gửi phiếu đăng ký'}
      </Button>
    </form>
  );
}
