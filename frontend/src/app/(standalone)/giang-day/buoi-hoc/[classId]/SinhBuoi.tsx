'use client';

import { useRef, useState } from 'react';

import { Button, Card, CardHead, Chip, TableWrap, Tbody, Td, Th, Thead, Tr } from '@/components/ui';
import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';

/**
 * Sinh lịch cả kỳ theo thứ trong tuần — xem trước, rồi mới tạo.
 *
 * ── VÌ SAO CÓ (13/09/2026) ────────────────────────────────────────────────
 *
 * Lớp của TopHSA học cố định hai tối mỗi tuần trong ba tháng: ~26 buổi. Tạo
 * từng buổi là 26 lần chọn ngày-giờ, và chính tôi đã tạo nhầm 4 buổi mẫu vào
 * Thứ 6 thay vì Thứ 5 khi làm bằng tay. Công cụ đọc sẵn lịch lớp, bỏ ngày nghỉ
 * của đợt, và không đẻ buổi trùng khi bấm lại.
 *
 * ── AI THẤY KHỐI NÀY ──────────────────────────────────────────────────────
 *
 * Giảng viên, học vụ, quản trị (anh Sơn chốt). Trợ giảng KHÔNG thấy — máy chủ
 * báo `coTheSinh: false` và khối không dựng gì, thay vì dựng một nút bấm vào
 * mới biết là không được phép. Ô "Tạo buổi học" ngay trên vẫn dùng được.
 *
 * Backend: `backend/teaching/sinh_buoi.py`.
 */
export type GoiYSinh = {
  lop: { id: number; name: string; schedule: string | null };
  dot: {
    id: number;
    name: string;
    ngayNghi: { id: number; ngay: string; ten: string }[];
  } | null;
  goiY: {
    weekdays: number[];
    startTime: string | null;
    durationMinutes: number | null;
    from: string;
    to: string | null;
  };
  coTheSinh: boolean;
  /** Lớp đang TẠM DỪNG (V-c, 25/09/2026) — không sinh lịch; tuỳ chọn vì máy chủ cũ không trả. */
  tamDung?: boolean;
};

type DongSinh = {
  ngay: string;
  startsAt: string;
  trangThai: 'tao' | 'nghi_le' | 'trung';
  lyDo: string | null;
  canhBao: string | null;
};

type KetQuaSinh = {
  dryRun: boolean;
  dem: { tao: number; nghi_le: number; trung: number };
  buoi: DongSinh[];
  canhBao: string[];
};

/** ISO: 1 = Thứ 2 … 7 = Chủ nhật — khớp `isoweekday()` bên máy chủ. */
const THU: { so: number; nhan: string; day: string }[] = [
  { so: 1, nhan: 'T2', day: 'Thứ 2' },
  { so: 2, nhan: 'T3', day: 'Thứ 3' },
  { so: 3, nhan: 'T4', day: 'Thứ 4' },
  { so: 4, nhan: 'T5', day: 'Thứ 5' },
  { so: 5, nhan: 'T6', day: 'Thứ 6' },
  { so: 6, nhan: 'T7', day: 'Thứ 7' },
  { so: 7, nhan: 'CN', day: 'Chủ nhật' },
];

/** `YYYY-MM-DD` → "T3 · 15/09/2026". Dựng Date từ số, không từ chuỗi: chuỗi ISO
 *  ngày trần bị hiểu là UTC, lệch sang hôm trước ở múi giờ âm. */
function ngayCoThu(iso: string) {
  const [y, m, d] = iso.split('-').map(Number);
  const w = new Date(y, m - 1, d).getDay();
  const thu = w === 0 ? 'CN' : `T${w + 1}`;
  return `${thu} · ${String(d).padStart(2, '0')}/${String(m).padStart(2, '0')}/${y}`;
}

function ngayDu(iso: string) {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

const O_NHAP =
  'min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink';

export default function SinhBuoi({
  classId,
  data,
  onDone,
}: {
  classId: number;
  data: GoiYSinh;
  onDone: () => void;
}) {
  const [mo, setMo] = useState(false);
  const [thu, setThu] = useState<number[]>(data.goiY.weekdays);
  const [gio, setGio] = useState(data.goiY.startTime ?? '19:30');
  const [phut, setPhut] = useState(String(data.goiY.durationMinutes ?? 90));
  const [tu, setTu] = useState(data.goiY.from);
  const [den, setDen] = useState(data.goiY.to ?? '');
  const [xem, setXem] = useState<KetQuaSinh | null>(null);
  const [xong, setXong] = useState<KetQuaSinh | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [dangChay, setDangChay] = useState(false);
  const dangGui = useRef(false);

  if (!data.coTheSinh) {
    // Tạm dừng: nói ra vì sao không có khối sinh lịch — giấu im thì người sắp lịch
    // tưởng trang lỗi. Trợ giảng (không tạm dừng) vẫn không thấy gì như trước.
    return data.tamDung ? (
      <Card tone="flat">
        <p className="text-body text-ink-2">
          Lớp đang <b>tạm dừng</b> nên chưa sinh lịch cả kỳ được. Học vụ đổi trạng thái lớp sang
          “Đang học” ở trang Lớp học rồi sinh lịch.
        </p>
      </Card>
    ) : null;
  }

  /** Đổi bất kỳ ô nào là bỏ bản xem trước: tạo theo một bản khác với bản vừa
   *  duyệt là đúng thứ bước xem trước sinh ra để chặn. */
  function doi<T>(dat: (v: T) => void) {
    return (v: T) => {
      dat(v);
      setXem(null);
      setXong(null);
    };
  }

  async function gui(dryRun: boolean) {
    if (dangGui.current) return;
    dangGui.current = true;
    setDangChay(true);
    setLoi(null);
    try {
      const r = await apiFetch(`/api/teach/classes/${classId}/sessions/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          weekdays: thu,
          start_time: gio,
          duration_minutes: phut.trim() ? Number(phut) : null,
          from: tu,
          to: den,
          dry_run: dryRun,
        }),
      });
      const body: unknown = await r.json().catch(() => null);
      if (!r.ok) {
        setLoi(errorText(r.status, body));
        return;
      }
      if (dryRun) {
        setXem(body as KetQuaSinh);
      } else {
        setXong(body as KetQuaSinh);
        setXem(null);
        onDone();
      }
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Chưa sinh được lịch. Thử lại sau ít phút.'));
    } finally {
      dangGui.current = false;
      setDangChay(false);
    }
  }

  if (!mo) {
    return (
      <Card tone="flat">
        <div className="flex flex-wrap items-center gap-3">
          <p className="min-w-0 flex-1 text-body text-ink-2">
            Sinh sẵn lịch cả kỳ theo thứ trong tuần — bỏ ngày nghỉ của đợt, không tạo buổi trùng.
          </p>
          <Button variant="ghost" onClick={() => setMo(true)}>
            Sinh lịch cả kỳ
          </Button>
        </div>
      </Card>
    );
  }

  const nghi = data.dot?.ngayNghi ?? [];
  const soTao = xem?.dem.tao ?? 0;

  return (
    <Card>
      <CardHead
        title="Sinh lịch cả kỳ"
        hint={
          data.lop.schedule
            ? `Đã điền sẵn theo lịch lớp “${data.lop.schedule}” — kiểm tra lại rồi bấm Xem trước.`
            : 'Lớp chưa ghi lịch học — chọn thứ và giờ bên dưới.'
        }
        action={
          <Button variant="ghost" onClick={() => setMo(false)}>
            Thu gọn
          </Button>
        }
      />

      {/* `fieldset` giữ viền, lề và padding mặc định của trình duyệt (dự án
          không nạp preflight) — phải tự xoá, nếu không khối thứ trong tuần có
          một khung xám bao quanh không giống ô nào khác trên trang. */}
      <fieldset className="m-0 mb-3 min-w-0 border-0 p-0">
        <legend className="mb-1 p-0 text-label text-ink-3">Học vào các thứ</legend>
        <div className="flex flex-wrap gap-2">
          {THU.map((t) => {
            const bat = thu.includes(t.so);
            return (
              <button
                key={t.so}
                type="button"
                aria-pressed={bat}
                aria-label={t.day}
                onClick={() =>
                  doi(setThu)(bat ? thu.filter((s) => s !== t.so) : [...thu, t.so].sort((a, b) => a - b))
                }
                className={`min-h-11 min-w-11 rounded-md border px-3 text-small font-semibold focus-visible:outline-2 focus-visible:outline-brand ${
                  bat ? 'border-brand bg-brand/10 text-brand-ink' : 'border-line-input bg-sunken text-ink-2'
                }`}
              >
                {t.nhan}
              </button>
            );
          })}
        </div>
      </fieldset>

      <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,160px),1fr))]">
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Giờ bắt đầu</span>
          <input type="time" value={gio} onChange={(e) => doi(setGio)(e.target.value)} className={O_NHAP} />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Thời lượng (phút)</span>
          <input
            type="number"
            inputMode="numeric"
            min={15}
            value={phut}
            onChange={(e) => doi(setPhut)(e.target.value)}
            className={O_NHAP}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Từ ngày</span>
          <input type="date" value={tu} onChange={(e) => doi(setTu)(e.target.value)} className={O_NHAP} />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-label text-ink-3">Đến ngày</span>
          <input type="date" value={den} onChange={(e) => doi(setDen)(e.target.value)} className={O_NHAP} />
        </label>
      </div>

      {/* Nói TRƯỚC những ngày sẽ bị bỏ, và nói cả khi KHÔNG có ngày nào: lớp
          chưa gắn đợt thì mọi ngày lễ đều sẽ có buổi, và người bấm cần biết
          điều đó trước chứ không phải đếm lại trong bảng. */}
      <p className="mt-3 text-small text-ink-3">
        {data.dot
          ? nghi.length > 0
            ? `Bỏ ${nghi.length} ngày nghỉ của ${data.dot.name}: ${nghi.map((n) => `${ngayDu(n.ngay)} ${n.ten}`).join(' · ')}.`
            : `${data.dot.name} chưa khai ngày nghỉ nào — học vụ khai ở Vận hành → Đợt học.`
          : 'Lớp chưa thuộc đợt học nào nên không có ngày nghỉ nào được bỏ.'}
      </p>

      <div className="mt-3 flex flex-wrap gap-2">
        <Button
          variant="ghost"
          loading={dangChay}
          disabled={thu.length === 0 || !tu || !den}
          onClick={() => void gui(true)}
        >
          Xem trước
        </Button>
        <Button loading={dangChay} disabled={soTao === 0} onClick={() => void gui(false)}>
          {!xem ? 'Tạo buổi' : soTao > 0 ? `Tạo ${soTao} buổi` : 'Không có buổi mới'}
        </Button>
      </div>

      {loi && (
        <p role="alert" className="mt-3 rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">
          {loi}
        </p>
      )}

      {xong && (
        <p role="status" className="mt-3 rounded-md border border-line bg-sunken px-3 py-2 text-small text-success-ink">
          Đã tạo {xong.dem.tao} buổi
          {xong.dem.nghi_le > 0 && `, bỏ ${xong.dem.nghi_le} ngày nghỉ`}
          {xong.dem.trung > 0 && `, ${xong.dem.trung} buổi đã có sẵn nên giữ nguyên`}.
        </p>
      )}

      {xem && (
        <div className="mt-4 flex flex-col gap-3" aria-live="polite">
          <p className="text-body text-ink">
            Sẽ tạo {xem.dem.tao} buổi · bỏ {xem.dem.nghi_le} ngày nghỉ · {xem.dem.trung} buổi đã có sẵn.
          </p>
          {xem.canhBao.map((w) => (
            <p key={w} className="rounded-md bg-warning/10 px-3 py-2 text-small text-warning-ink">
              {w}
            </p>
          ))}
          <TableWrap caption="Các buổi sẽ sinh, từng ngày một">
            <Thead>
              <tr>
                <Th>Ngày</Th>
                <Th>Giờ</Th>
                <Th>Kết quả</Th>
              </tr>
            </Thead>
            <Tbody>
              {xem.buoi.map((b) => (
                <Tr key={b.ngay} dim={b.trangThai !== 'tao'}>
                  <Td label="Ngày">
                    <span className="font-semibold tabular-nums text-ink">{ngayCoThu(b.ngay)}</span>
                  </Td>
                  <Td label="Giờ" num>
                    {b.startsAt.slice(11, 16)}
                  </Td>
                  <Td label="Kết quả">
                    <span className="flex flex-col items-start gap-1">
                      {b.trangThai === 'tao' ? (
                        <Chip tone="brand">Sẽ tạo</Chip>
                      ) : b.trangThai === 'nghi_le' ? (
                        <Chip tone="warn">Nghỉ</Chip>
                      ) : (
                        <Chip>Đã có buổi</Chip>
                      )}
                      {b.lyDo && <span className="text-small text-ink-3">{b.lyDo}</span>}
                      {b.canhBao && <span className="text-small text-warning-ink">{b.canhBao}</span>}
                    </span>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </TableWrap>
        </div>
      )}
    </Card>
  );
}
