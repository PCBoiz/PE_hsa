'use client';

import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';

import { Button, Card, CardHead, Chip, TableWrap, Tbody, Td, Th, Thead, Tr } from '@/components/ui';
import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';

/**
 * Dán liên hệ phụ huynh cho CẢ LỚP — xem trước, rồi mới lưu.
 *
 * ── VÌ SAO CÓ (13/09/2026) ────────────────────────────────────────────────
 *
 * Kênh gửi báo cáo chính là email, nhưng tới hôm nay không có chỗ nào nhập
 * email phụ huynh: production 0 em có. Số và email của bố mẹ nằm trong tệp
 * đăng ký học vụ đang giữ — nên đường nhanh nhất là dán thẳng tệp ấy vào đây,
 * không phải chờ từng em vào Cài đặt.
 *
 * ── HAI BƯỚC, KHÔNG PHẢI MỘT ──────────────────────────────────────────────
 *
 * Dán nhầm cột là ghi email của nhà này vào hồ sơ nhà kia, và báo cáo tiến độ
 * của một em đi tới một gia đình khác. Nên nút Lưu chỉ mở SAU khi đã xem bảng
 * "sẽ đổi gì": ô nào ghi đè giá trị cũ thì hiện giá trị cũ gạch ngang. Sửa chữ
 * trong ô dán là bảng xem trước tự bỏ — lưu một bản khác với bản vừa duyệt là
 * đúng thứ bước xem trước sinh ra để chặn.
 *
 * Backend: `backend/teaching/lien_he_phu_huynh.py`.
 */
type Doi = { cu: string; moi: string };
type KhoaO = 'parentName' | 'parentPhone' | 'parentEmail';

type Dong = {
  line: number;
  hocVien: { id: number; name: string | null } | null;
  trangThai: 'doi' | 'giu' | 'bo_qua';
  lyDo: string | null;
  doi: Partial<Record<KhoaO, Doi>>;
};

type KetQua = {
  dryRun: boolean;
  theoTieuDe: boolean;
  cot: { tieuDe: string; la: string | null }[];
  soDong: number;
  dem: { doi: number; giu: number; bo_qua: number };
  canhBao: string[];
  conThieu: string[];
  rows: Dong[];
};

const TEN_O: [KhoaO, string][] = [
  ['parentName', 'Tên'],
  ['parentPhone', 'Zalo'],
  ['parentEmail', 'Email'],
];

export default function DanLienHe({ classId, soThieu }: { classId: string; soThieu: number }) {
  const router = useRouter();
  const [mo, setMo] = useState(false);
  const [text, setText] = useState('');
  const [xemTruoc, setXemTruoc] = useState<KetQua | null>(null);
  const [daLuu, setDaLuu] = useState<KetQua | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [dangChay, setDangChay] = useState(false);
  // Chặn bấm hai lần: state đổi ở lượt vẽ SAU, ref đổi ngay — cùng lối với ô
  // cấp tài khoản hàng loạt.
  const dangGui = useRef(false);

  async function gui(dryRun: boolean) {
    if (dangGui.current) return;
    dangGui.current = true;
    setDangChay(true);
    setLoi(null);
    try {
      const r = await apiFetch(`/api/teach/classes/${classId}/parent-contacts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, dry_run: dryRun }),
      });
      const body: unknown = await r.json().catch(() => null);
      if (!r.ok) {
        setLoi(errorText(r.status, body));
        return;
      }
      if (dryRun) {
        setXemTruoc(body as KetQua);
        setDaLuu(null);
      } else {
        setDaLuu(body as KetQua);
        setXemTruoc(null);
        setText('');
        // Bảng học viên và hai lời cảnh báo phía trên là dữ liệu dựng ở máy
        // chủ — không làm mới thì chúng vẫn nói "N em chưa có liên lạc" ngay
        // cạnh dòng "đã lưu".
        router.refresh();
      }
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Chưa gửi được danh sách. Thử lại sau ít phút.'));
    } finally {
      dangGui.current = false;
      setDangChay(false);
    }
  }

  if (!mo) {
    return (
      <Card tone="flat">
        <div className="flex flex-wrap items-center gap-3">
          <div className="min-w-0 flex-1">
            <h2 className="text-section text-ink">Nhập liên hệ phụ huynh</h2>
            <p className="mt-1 text-small text-ink-3">
              {soThieu > 0 && `${soThieu} em chưa có liên lạc phụ huynh. `}
              Dán thẳng từ bảng đăng ký (Excel, Google Sheets) — bấm “Kiểm tra trước” rồi mới lưu.
            </p>
          </div>
          <Button variant="ghost" onClick={() => setMo(true)}>
            Mở ô dán
          </Button>
        </div>
      </Card>
    );
  }

  const soLuu = xemTruoc?.dem.doi ?? 0;

  return (
    <Card>
      <CardHead
        title="Nhập liên hệ phụ huynh"
        hint="Chỉ khớp với em đang học trong lớp này. Ô để trống thì giữ nguyên thông tin đang có."
        action={
          <Button variant="ghost" onClick={() => setMo(false)}>
            Thu gọn
          </Button>
        }
      />

      <ul className="mb-3 flex list-disc flex-col gap-1 pl-5 text-small text-ink-2">
        <li>
          <strong className="text-ink">Dán cả bảng kèm dòng tiêu đề</strong> — hệ thống đọc theo tên
          cột (“Họ và tên”, “SĐT phụ huynh”, “Email phụ huynh”…). Chỉ cách này tách được số của em
          khỏi số của bố mẹ.
        </li>
        <li>
          Không có tiêu đề thì mỗi dòng: <strong className="text-ink">em học viên trước</strong> (họ
          tên, email hoặc SĐT của em), rồi tên, số Zalo, email phụ huynh.
        </li>
      </ul>

      <textarea
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setXemTruoc(null);
          setDaLuu(null);
        }}
        rows={6}
        aria-label="Danh sách liên hệ phụ huynh"
        placeholder={'Nguyễn Văn An, Mẹ An, 0912345678, me.an@gmail.com\nTrần Thị Bình, Bố Bình, 0987654321'}
        className="w-full rounded-md border border-line bg-sunken p-3 font-mono text-small leading-relaxed text-ink placeholder:text-ink-3/70 focus:outline-2 focus:outline-brand"
      />

      <div className="mt-3 flex flex-wrap gap-2">
        <Button variant="ghost" loading={dangChay} disabled={!text.trim()} onClick={() => void gui(true)}>
          Kiểm tra trước
        </Button>
        <Button loading={dangChay} disabled={soLuu === 0} onClick={() => void gui(false)}>
          {!xemTruoc
            ? 'Lưu'
            : soLuu > 0
              ? `Lưu thay đổi cho ${soLuu} em`
              : 'Không có gì để lưu'}
        </Button>
      </div>

      {loi && (
        <p role="alert" className="mt-3 rounded-md bg-danger/10 px-3 py-2 text-small text-danger-ink">
          {loi}
        </p>
      )}

      {xemTruoc && <KetQuaDan kq={xemTruoc} />}
      {daLuu && <KetQuaDan kq={daLuu} />}
    </Card>
  );
}

function KetQuaDan({ kq }: { kq: KetQua }) {
  const xem = kq.dryRun;
  // Ghi đè là chỗ duy nhất một lần dán làm MẤT thông tin — đếm riêng và nói
  // trước khi bấm, không để người ta tự dò trong bảng.
  const ghiDe = kq.rows.reduce(
    (n, r) => n + TEN_O.filter(([k]) => r.doi[k]?.cu).length,
    0,
  );

  return (
    <div className="mt-4 flex flex-col gap-3" aria-live="polite">
      <p className="text-body text-ink">
        {xem ? 'Xem trước' : 'Đã lưu'} {kq.soDong} dòng: {kq.dem.doi} em {xem ? 'sẽ' : 'đã'} cập
        nhật · {kq.dem.giu} em không đổi · {kq.dem.bo_qua} dòng bỏ qua.
      </p>

      {kq.theoTieuDe && (
        <p className="text-small text-ink-3">
          Đọc theo dòng tiêu đề:{' '}
          {kq.cot.map((c) => `${c.tieuDe} → ${c.la ?? 'bỏ qua'}`).join(' · ')}
        </p>
      )}

      {xem && ghiDe > 0 && (
        <p className="rounded-md bg-warning/10 px-3 py-2 text-small text-warning-ink">
          {ghiDe} ô sẽ GHI ĐÈ thông tin đang có (giá trị cũ gạch ngang trong bảng). Kiểm tra kỹ các
          dòng ấy — nhật ký vẫn giữ giá trị cũ nếu cần khôi phục.
        </p>
      )}

      {kq.canhBao.map((w) => (
        <p key={w} className="rounded-md bg-warning/10 px-3 py-2 text-small text-warning-ink">
          {w}
        </p>
      ))}

      <TableWrap caption="Kết quả đọc danh sách liên hệ phụ huynh, từng dòng một">
        <Thead>
          <tr>
            <Th align="right">Dòng</Th>
            <Th>Học viên</Th>
            <Th>Thay đổi</Th>
            <Th>Kết quả</Th>
          </tr>
        </Thead>
        <Tbody>
          {kq.rows.map((r) => (
            <Tr key={r.line} dim={r.trangThai === 'giu'}>
              <Td label="Dòng" num>
                {r.line}
              </Td>
              <Td label="Học viên">
                {r.hocVien ? (
                  <span className="font-semibold text-ink">{r.hocVien.name || `#${r.hocVien.id}`}</span>
                ) : (
                  <span className="text-ink-3">—</span>
                )}
              </Td>
              <Td label="Thay đổi">
                {r.trangThai === 'doi' ? (
                  <span className="flex flex-col gap-0.5">
                    {TEN_O.map(([k, ten]) => {
                      const d = r.doi[k];
                      if (!d) return null;
                      return (
                        /* `break-words`, không `break-all`: `break-all` cho bẻ ở
                           BẤT KỲ ký tự nào, nên bảng tự co cột này lại và email
                           gãy giữa chữ ("me.test@example.c / om") dù bên cạnh
                           còn thừa chỗ. Đo trên ảnh chụp 13/09/2026. */
                        <span key={k} className="break-words">
                          <span className="text-ink-3">{ten}: </span>
                          {d.cu ? (
                            <del className="text-ink-3">{d.cu}</del>
                          ) : (
                            <span className="text-ink-3">(trống)</span>
                          )}
                          {' → '}
                          <span className="text-ink">{d.moi}</span>
                        </span>
                      );
                    })}
                  </span>
                ) : (
                  <span className="text-ink-3">—</span>
                )}
              </Td>
              <Td label="Kết quả">
                {r.trangThai === 'bo_qua' ? (
                  <span className="flex flex-col items-start gap-1">
                    <Chip tone="warn">Bỏ qua</Chip>
                    <span className="text-small text-warning-ink">{r.lyDo}</span>
                  </span>
                ) : r.trangThai === 'giu' ? (
                  <Chip>Không đổi</Chip>
                ) : (
                  <Chip tone={xem ? 'brand' : 'good'}>{xem ? 'Sẽ cập nhật' : 'Đã cập nhật'}</Chip>
                )}
              </Td>
            </Tr>
          ))}
        </Tbody>
      </TableWrap>

      {kq.conThieu.length > 0 && (
        <p className="text-small text-ink-2">
          {xem ? 'Sau lần này vẫn' : 'Vẫn'} còn {kq.conThieu.length} em chưa có số hay email phụ
          huynh: {kq.conThieu.join(' · ')}.
        </p>
      )}
    </div>
  );
}
