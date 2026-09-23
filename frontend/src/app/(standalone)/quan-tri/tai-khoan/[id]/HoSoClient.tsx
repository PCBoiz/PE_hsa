'use client';

import Link from 'next/link';
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';

import { Button, Card, CardHead, Chip, Field } from '@/components/ui';
import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';
import { kiemHinhDang } from '@/lib/kiemDang';

import { HD_DA_LUU, type HoSo, type HoSoPayload } from './hoSo';

/** Khoá GỬI LÊN — trùng tên với khoá trong `profile` và trong `errors` của 400. */
const O_SUA = [
  'name', 'birthday', 'username',
  'school', 'schoolGrade', 'region', 'studyGoal', 'aspiration',
  'consultantId', 'enrollSource',
  'parentName', 'parentPhone', 'parentEmail',
] as const;
type OSua = (typeof O_SUA)[number];
type Form = Record<OSua, string>;

/** Chỉ các ô này có nghĩa với tài khoản nhân sự (quản trị viên mở hồ sơ nhân sự). */
const O_NHAN_SU: readonly OSua[] = ['name', 'birthday', 'username'];

const HOC_VIEN = 'Học viên';

function tuHoSo(p: HoSo): Form {
  return {
    name: p.name ?? '',
    birthday: p.birthday ?? '',
    username: p.username ?? '',
    school: p.school ?? '',
    schoolGrade: p.schoolGrade ?? '',
    region: p.region ?? '',
    studyGoal: p.studyGoal ?? '',
    aspiration: p.aspiration ?? '',
    consultantId: p.consultantId == null ? '' : String(p.consultantId),
    enrollSource: p.enrollSource ?? '',
    parentName: p.parentName ?? '',
    parentPhone: p.parentPhone ?? '',
    parentEmail: p.parentEmail ?? '',
  };
}

/**
 * Hồ sơ học viên — một form, một nút Lưu.
 *
 * ── CHỈ GỬI Ô ĐÃ ĐỔI ─────────────────────────────────────────────────────────
 *
 * Gửi cả form mỗi lần Lưu thì một thẻ trình duyệt mở từ sáng sẽ ĐÈ lên điều
 * người khác vừa sửa ở ô mình không động tới — đúng lỗi đã vá ở Cài đặt ngày
 * 13/09. Và với liên hệ phụ huynh, "có gửi" kéo theo KHOÁ (§47): gửi lại nguyên
 * số cũ không được phép khoá ô em đang tự điền.
 *
 * ── LƯU XONG THÌ LẤY LẠI BẢN CỦA MÁY CHỦ ───────────────────────────────────
 *
 * Máy chủ chuẩn hoá ("0912 345 678" → "0912345678", email hạ chữ thường). Giữ
 * nguyên chữ người dùng gõ là để form lệch với CSDL, và lần Lưu sau lại "đổi"
 * một ô không ai đổi.
 */
export default function HoSoClient({ initial }: { initial: HoSoPayload }) {
  const [goc, setGoc] = useState<HoSo>(initial.profile);
  const [form, setForm] = useState<Form>(() => tuHoSo(initial.profile));
  const [loi, setLoi] = useState<Partial<Record<OSua, string>>>({});
  const [loiChung, setLoiChung] = useState<string | null>(null);
  const [dangLuu, setDangLuu] = useState(false);
  const [daLuuLuc, setDaLuuLuc] = useState<string | null>(null);
  /** Chốt ĐỒNG BỘ chống bấm Lưu hai lần — `setState` chưa kịp có hiệu lực. */
  const dangGui = useRef(false);

  const laHocVien = goc.role === HOC_VIEN;
  const gocForm = useMemo(() => tuHoSo(goc), [goc]);
  const oHienCo: readonly OSua[] = laHocVien ? O_SUA : O_NHAN_SU;
  const doi = oHienCo.filter((k) => form[k] !== gocForm[k]);
  const conDoi = doi.length > 0;

  // Rời trang khi còn thay đổi chưa lưu → trình duyệt hỏi lại. Chỉ gắn khi có
  // thay đổi: gắn thường trực thì trang không vào được bộ nhớ đệm quay lại.
  useEffect(() => {
    if (!conDoi) return;
    const chan = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener('beforeunload', chan);
    return () => window.removeEventListener('beforeunload', chan);
  }, [conDoi]);

  function dat(k: OSua, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
    setLoi((l) => (l[k] ? { ...l, [k]: undefined } : l));
    setDaLuuLuc(null);
  }

  async function luu() {
    if (!conDoi || dangGui.current) return;
    dangGui.current = true;
    setDangLuu(true);
    setLoiChung(null);
    const body: Record<string, string | number | null> = {};
    for (const k of doi) body[k] = k === 'consultantId' ? (form[k] ? Number(form[k]) : null) : form[k];
    const duong = `/api/admin/users/${goc.id}/profile`;
    try {
      const r = await apiFetch(duong, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const d: unknown = await r.json().catch(() => ({}));
      const errors = (d as { errors?: Partial<Record<OSua, string>> }).errors;
      if (r.status === 400 && errors && typeof errors === 'object') {
        // Lỗi NGAY DƯỚI ô sai, và đưa con trỏ tới ô sai đầu tiên theo thứ tự
        // trên màn hình — không bắt người dùng cuộn đi tìm.
        setLoi(errors);
        const dau = oHienCo.find((k) => errors[k]);
        if (dau) document.getElementById(`hs-${dau}`)?.focus();
        return;
      }
      if (!r.ok) throw new Error(errorText(r.status, d));
      const kq = kiemHinhDang(duong, d, r.status, HD_DA_LUU);
      if (!kq.ok) throw new Error(kq.message);
      setGoc(kq.data.profile);
      setForm(tuHoSo(kq.data.profile));
      setLoi({});
      setDaLuuLuc(new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }));
    } catch (e) {
      setLoiChung(loiBatDuoc(e, 'Không lưu được hồ sơ'));
    } finally {
      dangGui.current = false;
      setDangLuu(false);
    }
  }

  const ten = goc.name || goc.email || goc.phone || `#${goc.id}`;

  return (
    <form
      className="mx-auto flex max-w-3xl flex-col gap-5"
      onSubmit={(e) => {
        e.preventDefault();
        void luu();
      }}
      noValidate
    >
      <div className="flex flex-col gap-2">
        <Link
          href="/quan-tri/tai-khoan"
          className="-mx-2 inline-flex min-h-11 w-fit items-center px-2 text-small text-ink-3 hover:text-brand-ink"
        >
          ← Danh sách tài khoản
        </Link>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <h2 className="min-w-0 text-title text-ink [overflow-wrap:anywhere]">{ten}</h2>
          {goc.studentCode && (
            <Chip tone="neutral">
              <span className="font-mono">{goc.studentCode}</span>
            </Chip>
          )}
          {!laHocVien && <Chip tone="neutral">{goc.role === 'admin' ? 'Quản trị viên' : goc.role}</Chip>}
          {goc.status === 'suspended' && <Chip tone="bad">Đã khoá</Chip>}
          {/* Lịch tuần này của RIÊNG em — gộp mọi lớp em đang học (`/giang-day/lich`
              lọc theo tư cách thành viên tại giờ từng buổi). Học vụ hay được hỏi
              "tối nay em học lớp nào, phòng nào" khi phụ huynh gọi tới. */}
          {laHocVien && (
            <Link
              href={`/giang-day/lich?hoc_vien=${goc.id}`}
              className="ml-auto inline-flex min-h-11 items-center text-small text-brand-ink underline"
            >
              Lịch học của em
            </Link>
          )}
        </div>
        {goc.studentCode && (
          <p className="text-small text-ink-3">
            Mã học viên do hệ thống cấp và không đổi được — dùng để tìm nhanh và đối chiếu với phụ huynh.
          </p>
        )}
      </div>

      <Card>
        <CardHead title="Thông tin cá nhân" />
        <div className="grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(min(100%,16rem),1fr))]">
          <Field
            id="hs-name"
            label="Họ và tên"
            value={form.name}
            onChange={(e) => dat('name', e.target.value)}
            error={loi.name}
            autoComplete="off"
            required
          />
          <Field
            id="hs-birthday"
            label="Ngày sinh"
            type="date"
            value={form.birthday}
            onChange={(e) => dat('birthday', e.target.value)}
            error={loi.birthday}
          />
        </div>
        {/* Email và SĐT là hai cách ĐĂNG NHẬP — sửa ở đây là đổi cửa vào của em
            mà em không biết. Em tự đổi ở Cài đặt (có kiểm trùng). */}
        <dl className="mt-4 grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,16rem),1fr))]">
          <ChiDoc nhan="Email" giaTri={goc.email} />
          <ChiDoc nhan="Số điện thoại" giaTri={goc.phone} />
        </dl>
        <p className="mt-2 text-small text-ink-3">
          Email và số điện thoại là thông tin đăng nhập, {laHocVien ? 'em' : 'người dùng'} tự đổi trong Cài đặt.
        </p>
      </Card>

      <Card>
        <CardHead
          title="Tên đăng nhập"
          hint="Không bắt buộc. Có tên này thì em đăng nhập bằng nó thay cho email hay số điện thoại."
        />
        <Field
          id="hs-username"
          label="Tên đăng nhập"
          value={form.username}
          onChange={(e) => dat('username', e.target.value.toLowerCase())}
          error={loi.username}
          hint="3–30 ký tự: chữ thường không dấu, số, dấu chấm; có ít nhất một chữ. Ví dụ: an.nguyen08"
          autoComplete="off"
          autoCapitalize="none"
          spellCheck={false}
          inputMode="email"
        />
      </Card>

      {laHocVien && (
        <>
          <Card>
            <CardHead title="Học tập" />
            <div className="grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(min(100%,12rem),1fr))]">
              <Field id="hs-school" label="Trường" value={form.school} error={loi.school}
                onChange={(e) => dat('school', e.target.value)} maxLength={200} />
              <Field id="hs-schoolGrade" label="Lớp" value={form.schoolGrade} error={loi.schoolGrade}
                onChange={(e) => dat('schoolGrade', e.target.value)} maxLength={20} hint="Ví dụ: 12A1" />
              <Field id="hs-region" label="Khu vực" value={form.region} error={loi.region}
                onChange={(e) => dat('region', e.target.value)} maxLength={100} hint="Tỉnh / thành phố" />
            </div>
            <div className="mt-4 grid gap-4">
              <OChu id="hs-studyGoal" nhan="Mục tiêu học tập" giaTri={form.studyGoal} loi={loi.studyGoal}
                doi={(v) => dat('studyGoal', v)} goiY="Ví dụ: đạt 100 điểm HSA đợt tháng 3." />
              <OChu id="hs-aspiration" nhan="Nguyện vọng trường / ngành" giaTri={form.aspiration}
                loi={loi.aspiration} doi={(v) => dat('aspiration', v)}
                goiY="Giảng viên của lớp em cũng cập nhật được hai ô này." />
            </div>
          </Card>

          <Card>
            <CardHead title="Tuyển sinh" />
            <div className="grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(min(100%,16rem),1fr))]">
              <OChon id="hs-consultantId" nhan="Người tư vấn" giaTri={form.consultantId}
                loi={loi.consultantId} doi={(v) => dat('consultantId', v)}>
                <option value="">Chưa chọn</option>
                {initial.consultants.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name || `#${c.id}`} · {c.role === 'admin' ? 'Quản trị viên' : c.role}
                  </option>
                ))}
                {/* Người tư vấn cũ đã bị khoá thì không còn trong danh sách
                    chọn — vẫn phải hiện đúng tên, không được rơi về "Chưa chọn"
                    rồi bị xoá ở lần Lưu sau. */}
                {goc.consultantId != null && !initial.consultants.some((c) => c.id === goc.consultantId) && (
                  <option value={goc.consultantId}>{goc.consultantName || `#${goc.consultantId}`} (đã nghỉ)</option>
                )}
              </OChon>
              <OChon id="hs-enrollSource" nhan="Nguồn tuyển sinh" giaTri={form.enrollSource}
                loi={loi.enrollSource} doi={(v) => dat('enrollSource', v)}>
                <option value="">Chưa chọn</option>
                {initial.sources.map((s) => (
                  <option key={s.ma} value={s.ma}>
                    {s.nhan}
                  </option>
                ))}
              </OChon>
            </div>
          </Card>

          <Card>
            <CardHead
              title="Phụ huynh"
              hint="Nơi nhận báo cáo tiến độ. Ô trung tâm đã nhập thì em không tự sửa được, chỉ điền ô trống."
            />
            <div className="grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(min(100%,12rem),1fr))]">
              <Field id="hs-parentName" label="Họ tên phụ huynh" value={form.parentName} error={loi.parentName}
                onChange={(e) => dat('parentName', e.target.value)} maxLength={100} autoComplete="off" />
              <Field id="hs-parentPhone" label="Số Zalo" type="tel" inputMode="tel" value={form.parentPhone}
                error={loi.parentPhone} onChange={(e) => dat('parentPhone', e.target.value)} autoComplete="off" />
              <Field id="hs-parentEmail" label="Email" type="email" inputMode="email" value={form.parentEmail}
                error={loi.parentEmail} onChange={(e) => dat('parentEmail', e.target.value)}
                autoComplete="off" spellCheck={false} />
            </div>
          </Card>
        </>
      )}

      {!laHocVien && (
        <p className="text-small text-ink-3">
          Tài khoản nhân sự không có các mục học tập, tuyển sinh và phụ huynh.
        </p>
      )}

      {/* Thanh Lưu DÍNH đáy: form dài, trên điện thoại nút Lưu ở cuối trang là
          năm lần cuộn sau ô vừa sửa. Nói rõ còn bao nhiêu ô chưa lưu — nút tắt
          mà không giải thích là thứ người dùng bấm hoài không hiểu vì sao. */}
      <div className="sticky bottom-0 z-10 -mx-4 flex flex-wrap items-center gap-3 border-t border-line bg-surface px-4 py-3">
        <p className="min-w-0 flex-1 text-small text-ink-3" aria-live="polite">
          {loiChung ? (
            <span role="alert" className="text-danger">{loiChung}</span>
          ) : conDoi ? (
            `${doi.length} ô chưa lưu`
          ) : daLuuLuc ? (
            `Đã lưu lúc ${daLuuLuc}`
          ) : (
            'Chưa có thay đổi'
          )}
        </p>
        <Button
          type="button"
          variant="ghost"
          disabled={!conDoi || dangLuu}
          onClick={() => {
            setForm(gocForm);
            setLoi({});
            setLoiChung(null);
          }}
        >
          Bỏ thay đổi
        </Button>
        <Button type="submit" loading={dangLuu} disabled={!conDoi}>
          {dangLuu ? 'Đang lưu…' : 'Lưu hồ sơ'}
        </Button>
      </div>
    </form>
  );
}

function ChiDoc({ nhan, giaTri }: { nhan: string; giaTri: string | null }) {
  return (
    <div className="flex flex-col gap-1">
      <dt className="text-label text-ink-3">{nhan}</dt>
      <dd className="text-body text-ink [overflow-wrap:anywhere]">{giaTri || '—'}</dd>
    </div>
  );
}

/** Ô chữ nhiều dòng — cùng luật với `Field`: nhãn luôn hiện, lỗi ngay dưới ô. */
function OChu({ id, nhan, giaTri, loi, doi, goiY }: {
  id: string;
  nhan: string;
  giaTri: string;
  loi?: string;
  doi: (v: string) => void;
  goiY?: string;
}) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className="text-label text-ink-3">{nhan}</label>
      <textarea
        id={id}
        value={giaTri}
        onChange={(e) => doi(e.target.value)}
        rows={3}
        maxLength={500}
        aria-invalid={loi ? true : undefined}
        aria-describedby={loi ? `${id}-error` : goiY ? `${id}-hint` : undefined}
        className={[
          'w-full rounded-md border bg-sunken p-3 text-input text-ink',
          'focus:outline-2 focus:outline-offset-0 focus:outline-brand',
          loi ? 'border-danger' : 'border-line-input',
        ].join(' ')}
      />
      <GhiChuO id={id} loi={loi} goiY={goiY} />
    </div>
  );
}

function OChon({ id, nhan, giaTri, loi, doi, children }: {
  id: string;
  nhan: string;
  giaTri: string;
  loi?: string;
  doi: (v: string) => void;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className="text-label text-ink-3">{nhan}</label>
      <select
        id={id}
        value={giaTri}
        onChange={(e) => doi(e.target.value)}
        aria-invalid={loi ? true : undefined}
        aria-describedby={loi ? `${id}-error` : undefined}
        /* `min-w-0`: ô chọn tự giãn theo lựa chọn dài nhất và đẩy cả lưới
           trượt ngang trên điện thoại (lỗi đã vá ở /admin 27/08/2026). */
        className={[
          'min-h-11 w-full min-w-0 max-w-full rounded-md border bg-sunken px-3 text-input text-ink',
          'focus:outline-2 focus:outline-offset-0 focus:outline-brand',
          loi ? 'border-danger' : 'border-line-input',
        ].join(' ')}
      >
        {children}
      </select>
      <GhiChuO id={id} loi={loi} />
    </div>
  );
}

function GhiChuO({ id, loi, goiY }: { id: string; loi?: string; goiY?: string }) {
  if (loi) {
    return <p id={`${id}-error`} role="alert" className="text-small text-danger">{loi}</p>;
  }
  return goiY ? <p id={`${id}-hint`} className="text-small text-ink-3">{goiY}</p> : null;
}
