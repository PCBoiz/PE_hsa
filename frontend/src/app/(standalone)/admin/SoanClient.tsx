'use client';

import Link from 'next/link';
import { useCallback, useRef, useState } from 'react';

import {
  Button,
  Card,
  CardHead,
  EmptyState,
  Field,
  Modal,
  TableWrap,
  Tbody,
  Td,
  Th,
  Thead,
  ThemeToggle,
  Tr,
} from '@/components/ui';
import { apiFetch, errorText, loiBatDuoc } from '@/lib/api';

import DeThi, { type DeRow } from './DeThi';
import NoiDungBai from './NoiDungBai';

export type KhoaRow = {
  id: string;
  title: string;
  subtitle?: string | null;
  lessons?: number | null;
};

export type BaiRow = {
  id: number;
  course_id: string;
  title: string;
  module?: string | null;
  sort_order?: number | null;
  content_json?: unknown;
};

async function doc(path: string, opts?: RequestInit) {
  const r = await apiFetch(path, opts);
  const data: unknown = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(errorText(r.status, data));
  return data;
}

/**
 * Khu soạn giáo trình.
 *
 * BỐ CỤC THEO ĐÚNG THỨ TỰ NGƯỜI TA LÀM VIỆC: chọn khoá → thấy danh sách bài →
 * mở một bài ra soạn. Bản cũ đặt ba khối cạnh nhau và để người dùng tự hiểu
 * rằng khối giữa phụ thuộc khối trên; ai mở thẳng khối "bài học" đều thấy một
 * bảng trống không nói vì sao.
 */
export default function SoanClient({
  initial,
  deThi,
  laQuanTri,
  loi,
}: {
  initial: KhoaRow[];
  deThi: DeRow[];
  laQuanTri: boolean;
  loi: string | null;
}) {
  const [khoa, setKhoa] = useState<KhoaRow[]>(initial);
  const [err, setErr] = useState<string | null>(loi);
  const [dangChon, setDangChon] = useState<KhoaRow | null>(null);
  const [bai, setBai] = useState<BaiRow[]>([]);
  const [dangNap, setDangNap] = useState(false);
  const [soanBaiId, setSoanBaiId] = useState<number | null>(null);

  // `setBusy` của React không có tác dụng NGAY, nên hai cú bấm liền nhau đều
  // lọt qua phép kiểm `if (busy) return`. Một `ref` thì đổi tức thì. (Cùng bẫy
  // đã ghi ở `TermsClient`, nơi nó tạo ra hai đợt học trùng tên.)
  const dangGui = useRef(false);

  const napKhoa = useCallback(async () => {
    try {
      const d = (await doc('/api/admin/courses')) as { courses: KhoaRow[] };
      setKhoa(d.courses);
      setErr(null);
    } catch (e) {
      setErr(loiBatDuoc(e, 'Không tải được danh sách khoá.'));
    }
  }, []);

  const chonKhoa = useCallback(async (k: KhoaRow) => {
    setDangChon(k);
    setSoanBaiId(null);
    setDangNap(true);
    try {
      const d = (await doc(`/api/admin/courses/${encodeURIComponent(k.id)}/lessons`)) as {
        lessons: BaiRow[];
      };
      setBai(d.lessons);
      setErr(null);
    } catch (e) {
      setBai([]);
      setErr(loiBatDuoc(e, 'Không tải được danh sách bài.'));
    } finally {
      setDangNap(false);
    }
  }, []);

  /* Trả `void`, KHÔNG trả Promise. Mọi bên gọi đều là `onClick`, chỗ React
     mong một hàm trả `void`; trả Promise ở đó thì rejection không ai bắt — và
     `no-misused-promises` bắt đúng chuyện ấy. Vì hàm này đã tự bắt lỗi và đổ
     vào ô báo lỗi, `void` là mô tả ĐÚNG chứ không phải một cách làm im lint. */
  function chay(viec: () => Promise<void>, macDinh: string): void {
    if (dangGui.current) return;
    dangGui.current = true;
    void (async () => {
      try {
        await viec();
        setErr(null);
      } catch (e) {
        setErr(loiBatDuoc(e, macDinh));
      } finally {
        dangGui.current = false;
      }
    })();
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-title text-ink">Soạn giáo trình</h1>
          <p className="mt-1 text-body text-ink-2">
            Khoá học, bài học, và nội dung 5 bước của từng bài.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Đường VỀ phải có cho MỌI vai, không chỉ quản trị viên: người biên
              tập vào thẳng đây từ thanh điều hướng và nếu không có lối ra thì
              họ phải gõ tay địa chỉ. */}
          {/* `-my-3 py-3` nới VÙNG CHẠM lên 48px mà không đẩy bố cục — đo
              04/09/2026: hai liên kết này cao 24px trên khổ điện thoại, dưới
              ngưỡng 44px. Cùng cách khu Vận hành đã dùng
              (`quan-tri/layout.tsx`); thêm `py` mà không kèm `-my` thì hàng
              tiêu đề cao thêm 24px trên MỌI khổ, kể cả máy tính. */}
          <Link href="/dashboard" className="-my-3 py-3 text-body text-brand-ink underline">
            ← Trang của tôi
          </Link>
          {laQuanTri && (
            <Link
              href="/quan-tri/tong-quan"
              className="-my-3 py-3 text-body text-brand-ink underline"
            >
              Khu vận hành →
            </Link>
          )}
          <ThemeToggle />
        </div>
      </div>

      {err && (
        <div
          role="alert"
          className="mt-4 rounded-md border border-danger bg-danger-soft px-4 py-3 text-body text-danger-ink"
        >
          {err}
        </div>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <KhoiKhoa
          khoa={khoa}
          dangChon={dangChon}
          laQuanTri={laQuanTri}
          onChon={(k) => {
            void chonKhoa(k);
          }}
          onDoi={() => {
            void napKhoa();
          }}
          chay={chay}
        />
        <KhoiBai
          khoa={dangChon}
          bai={bai}
          dangNap={dangNap}
          onDoi={() => {
            if (dangChon) void chonKhoa(dangChon);
          }}
          onSoan={setSoanBaiId}
          chay={chay}
          laQuanTri={laQuanTri}
        />
      </div>

      {soanBaiId !== null && (
        <div className="mt-6">
          {/* `key` BẮT BUỘC: không có nó, bấm "Soạn nội dung" ở một bài khác
              chỉ đổi prop `baiId` — React giữ nguyên cây, `NoiDungBai` không
              unmount, và mọi ô có state riêng (rõ nhất là ô JSON minh hoạ) vẫn
              giữ nội dung của BÀI TRƯỚC. Sửa một chữ trong ô ấy là ghi đồ thị
              của bài trước sang bài này. */}
          <NoiDungBai
            key={soanBaiId}
            baiId={soanBaiId}
            onDong={() => setSoanBaiId(null)}
            onLuuXong={() => {
              if (dangChon) void chonKhoa(dangChon);
            }}
          />
        </div>
      )}

      {/* Đề thi thử nằm CÙNG khu với giáo trình vì cùng một ranh giới quyền:
          `IsContentEditor`. Đề thi là NỘI DUNG, không phải dữ liệu học viên —
          xếp nó sang khu Vận hành sẽ buộc người soạn đề phải có quyền nhìn thấy
          tài khoản và mật khẩu của học viên. */}
      <div className="mt-6">
        <DeThi initial={deThi} loi={null} />
      </div>
    </main>
  );
}

/* ── Khối KHOÁ HỌC ───────────────────────────────────────────────────────── */

function KhoiKhoa({
  khoa,
  dangChon,
  laQuanTri,
  onChon,
  onDoi,
  chay,
}: {
  khoa: KhoaRow[];
  dangChon: KhoaRow | null;
  laQuanTri: boolean;
  onChon: (k: KhoaRow) => void;
  onDoi: () => void;
  chay: (viec: () => Promise<void>, macDinh: string) => void;
}) {
  const [moTao, setMoTao] = useState(false);
  const [ma, setMa] = useState('');
  const [ten, setTen] = useState('');

  return (
    <Card as="section">
      <CardHead
        title="Khoá học"
        action={
          laQuanTri ? (
            <Button size="sm" variant="ghost" onClick={() => setMoTao(true)}>
              + Khoá mới
            </Button>
          ) : undefined
        }
      />

      {khoa.length === 0 ? (
        <EmptyState
          title="Chưa có khoá học nào"
          hint="Quản trị viên tạo khoá đầu tiên bằng nút “+ Khoá mới”."
        />
      ) : (
        <TableWrap caption="Danh sách khoá học">
          <Thead>
            <Tr>
              {/* Mã khoá nằm DƯỚI tên chứ không thành cột riêng: ở khổ này bốn
                  cột làm tên khoá vỡ thành ba dòng và nút "Mở bài" gãy đôi.
                  Mã là thông tin phụ — người soạn tìm khoá bằng TÊN. */}
              <Th>Khoá học</Th>
              <Th>Số bài</Th>
              <Th>Thao tác</Th>
            </Tr>
          </Thead>
          <Tbody>
            {khoa.map((k) => (
              <Tr key={k.id}>
                <Td label="Khoá học">
                  <span className="block text-ink">{k.title}</span>
                  <code className="text-caption text-ink-3">{k.id}</code>
                </Td>
                <Td label="Số bài" num>
                  {k.lessons ?? 0}
                </Td>
                <Td label="Thao tác">
                  <div className="flex flex-wrap gap-2 [&_button]:whitespace-nowrap">
                    <Button size="sm" variant="ghost" onClick={() => onChon(k)}>
                      {dangChon?.id === k.id ? 'Đang mở' : 'Mở bài'}
                    </Button>
                    {laQuanTri && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() =>
                          chay(async () => {
                            if (
                              !window.confirm(
                                `Xoá khoá "${k.title}"?\n\n` +
                                  'Bài học của khoá bị xoá theo. Nếu còn học viên đã ghi danh ' +
                                  'thì hệ thống sẽ từ chối.',
                              )
                            ) {
                              return;
                            }
                            await doc(`/api/admin/courses/${encodeURIComponent(k.id)}`, {
                              method: 'DELETE',
                            });
                            onDoi();
                          }, 'Không xoá được khoá.')
                        }
                      >
                        Xoá
                      </Button>
                    )}
                  </div>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </TableWrap>
      )}

      <Modal
        open={moTao}
        onClose={() => setMoTao(false)}
        title="Khoá học mới"
        footer={
          <>
            <Button variant="ghost" onClick={() => setMoTao(false)}>
              Huỷ
            </Button>
            <Button
              onClick={() =>
                chay(async () => {
                  await doc('/api/admin/courses', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: ma.trim(), title: ten.trim() }),
                  });
                  setMa('');
                  setTen('');
                  setMoTao(false);
                  onDoi();
                }, 'Không tạo được khoá.')
              }
            >
              Tạo khoá
            </Button>
          </>
        }
      >
        <div className="flex flex-col gap-4">
          <Field
            id="ma-khoa"
            label="Mã khoá"
            hint="Chữ thường, không dấu, không khoảng trắng — nó nằm trên đường dẫn của mọi bài."
            value={ma}
            onChange={(e) => setMa(e.target.value)}
            placeholder="hsa_quantitative"
          />
          <Field
            id="ten-khoa"
            label="Tên khoá"
            value={ten}
            onChange={(e) => setTen(e.target.value)}
            placeholder="Tư duy Định lượng"
          />
        </div>
      </Modal>
    </Card>
  );
}

/* ── Khối BÀI HỌC + nhập cả khoá ─────────────────────────────────────────── */

function KhoiBai({
  khoa,
  bai,
  dangNap,
  onDoi,
  onSoan,
  chay,
  laQuanTri,
}: {
  khoa: KhoaRow | null;
  bai: BaiRow[];
  dangNap: boolean;
  onDoi: () => void;
  onSoan: (id: number) => void;
  chay: (viec: () => Promise<void>, macDinh: string) => void;
  laQuanTri: boolean;
}) {
  const [tenMoi, setTenMoi] = useState('');
  const [moNhap, setMoNhap] = useState(false);

  if (!khoa) {
    return (
      <Card as="section">
        <CardHead title="Bài học" />
        <EmptyState
          title="Chọn một khoá học ở bên trái"
          hint="Danh sách bài, đường soạn nội dung và đường nhập giáo trình đều nằm trong một khoá."
        />
      </Card>
    );
  }

  return (
    <Card as="section">
      <CardHead
        title={`Bài học — ${khoa.title}`}
        action={
          <Button size="sm" variant="ghost" onClick={() => setMoNhap(true)}>
            Nhập từ file JSON
          </Button>
        }
      />

      <div className="flex flex-wrap items-end gap-2">
        <div className="min-w-60 flex-1">
          <Field
            id="bai-moi"
            label="Thêm bài mới"
            value={tenMoi}
            onChange={(e) => setTenMoi(e.target.value)}
            placeholder="Tên bài — ví dụ: Tỉ lệ & phần trăm"
          />
        </div>
        <Button
          onClick={() =>
            chay(async () => {
              const t = tenMoi.trim();
              if (!t) throw new Error('Nhập tên bài trước đã.');
              // `sort_order` = số bài lớn nhất + 1. Không để máy chủ tự đoán:
              // thiếu nó thì bài mới rơi vào vị trí 0 và `index` của nội dung
              // sẽ không bao giờ khớp `sort_order` — máy chủ từ chối lưu nội
              // dung với một câu lỗi nói về "vị trí", thứ người soạn không hiểu
              // vì sao lại sai.
              const ke = bai.reduce((m, b) => Math.max(m, b.sort_order || 0), 0) + 1;
              await doc('/api/admin/lessons', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ course_id: khoa.id, title: t, sort_order: ke }),
              });
              setTenMoi('');
              onDoi();
            }, 'Không thêm được bài.')
          }
        >
          Thêm bài
        </Button>
      </div>

      <div className="mt-4">
        {dangNap ? (
          <p className="text-body text-ink-3">Đang tải…</p>
        ) : bai.length === 0 ? (
          <EmptyState
            title="Khoá này chưa có bài nào"
            hint="Thêm từng bài ở trên, hoặc nhập cả khoá từ một file JSON."
          />
        ) : (
          <TableWrap caption={`Bài học của khoá ${khoa.title}`}>
            <Thead>
              <Tr>
                <Th>#</Th>
                <Th>Tên bài</Th>
                <Th>Chương</Th>
                <Th>Nội dung</Th>
                <Th>Thao tác</Th>
              </Tr>
            </Thead>
            <Tbody>
              {bai.map((b) => (
                <Tr key={b.id}>
                  <Td label="#" num>
                    {b.sort_order ?? '—'}
                  </Td>
                  <Td label="Tên bài">{b.title}</Td>
                  <Td label="Chương" muted>
                    {b.module || '—'}
                  </Td>
                  <Td label="Nội dung">
                    {b.content_json ? (
                      <span className="text-caption text-ok-ink">đã soạn</span>
                    ) : (
                      <span className="text-caption text-ink-3">chưa có</span>
                    )}
                  </Td>
                  <Td label="Thao tác">
                    <div className="flex flex-wrap gap-2 [&_button]:whitespace-nowrap">
                      <Button size="sm" variant="ghost" onClick={() => onSoan(b.id)}>
                        Soạn nội dung
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() =>
                          chay(async () => {
                            if (!window.confirm(`Xoá bài "${b.title}"?`)) return;
                            await doc(`/api/admin/lessons/${b.id}`, { method: 'DELETE' });
                            onDoi();
                          }, 'Không xoá được bài.')
                        }
                      >
                        Xoá
                      </Button>
                    </div>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </TableWrap>
        )}
      </div>

      <NhapKhoa
        open={moNhap}
        onClose={() => setMoNhap(false)}
        khoa={khoa}
        laQuanTri={laQuanTri}
        onXong={onDoi}
        chay={chay}
      />
    </Card>
  );
}

/* ── Nhập cả khoá từ một file JSON ───────────────────────────────────────── */

function NhapKhoa({
  open,
  onClose,
  khoa,
  laQuanTri,
  onXong,
  chay,
}: {
  open: boolean;
  onClose: () => void;
  khoa: KhoaRow;
  laQuanTri: boolean;
  onXong: () => void;
  chay: (viec: () => Promise<void>, macDinh: string) => void;
}) {
  const [tho, setTho] = useState('');
  const [tong, setTong] = useState('');
  const [chiTiet, setChiTiet] = useState<string[]>([]);
  const [ketQua, setKetQua] = useState<string | null>(null);

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`Nhập giáo trình vào "${khoa.title}"`}
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Đóng
          </Button>
          <Button
            onClick={() =>
              chay(async () => {
                setChiTiet([]);
                setKetQua(null);
                let than: unknown;
                try {
                  than = JSON.parse(tho);
                } catch (e) {
                  throw new Error(
                    'File không phải JSON hợp lệ: ' + (e instanceof Error ? e.message : ''),
                  );
                }
                const goi = (
                  Array.isArray(than) ? { lessons: than } : (than as Record<string, unknown>)
                ) as Record<string, unknown>;
                // Chỉ gửi `total_lessons` khi người dùng THẬT SỰ gõ vào. Gửi
                // kèm một chuỗi rỗng cũng đủ để máy chủ trả 403 cho người biên
                // tập — và câu lỗi ấy sẽ nói về một ô họ không hề đụng tới.
                if (tong.trim()) goi.total_lessons = Number(tong);
                else delete goi.total_lessons;

                const r = await apiFetch(
                  `/api/admin/courses/${encodeURIComponent(khoa.id)}/import`,
                  {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(goi),
                  },
                );
                const d = (await r.json().catch(() => ({}))) as {
                  details?: string[];
                  created?: number;
                  updated?: number;
                };
                if (!r.ok) {
                  setChiTiet(Array.isArray(d.details) ? d.details : []);
                  throw new Error(errorText(r.status, d));
                }
                setKetQua(`Đã thêm ${d.created ?? 0} bài, cập nhật ${d.updated ?? 0} bài.`);
                onXong();
              }, 'Không nhập được giáo trình.')
            }
          >
            Nhập vào khoá
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <p className="text-body text-ink-2">
          Hệ thống <b>kiểm toàn bộ trước khi ghi</b>: sai một bài thì không bài nào được ghi,
          nên không có trạng thái nửa vời. Nhập lại cùng một file là cập nhật, không nhân đôi.
        </p>

        <label className="flex flex-col gap-2">
          <span className="text-label text-ink-3">Chọn file .json</span>
          <input
            type="file"
            accept=".json,application/json"
            className="text-body text-ink-2"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (!f) return;
              void f.text().then(setTho);
            }}
          />
        </label>

        <label className="flex flex-col gap-2">
          <span className="text-label text-ink-3">…hoặc dán thẳng nội dung</span>
          <textarea
            value={tho}
            onChange={(e) => setTho(e.target.value)}
            rows={8}
            spellCheck={false}
            className="rounded-md border border-line bg-surface p-3 font-mono text-caption text-ink"
            placeholder={'{"lessons": [ … ]}'}
          />
        </label>

        {laQuanTri ? (
          <Field
            id="tong-so-bai"
            label="Tổng số bài của khoá"
            hint="Bỏ trống nếu chưa bàn giao trọn giáo trình. Đây là đường DUY NHẤT hạ được con số này, và nó là mẫu số của mọi phần trăm tiến độ."
            type="number"
            min={1}
            value={tong}
            onChange={(e) => setTong(e.target.value)}
            placeholder="27"
          />
        ) : (
          <p className="text-caption text-ink-3">
            Tổng số bài của khoá do quản trị viên đặt. Nhập bao nhiêu bài cũng được — hệ thống
            tự nâng tổng lên theo bài có số thứ tự lớn nhất.
          </p>
        )}

        {ketQua && <p className="text-body text-ok-ink">{ketQua}</p>}

        {chiTiet.length > 0 && (
          <div className="rounded-md border border-danger bg-danger-soft p-3">
            <p className="text-label text-danger-ink">{chiTiet.length} lỗi trong file:</p>
            <ul className="mt-2 flex flex-col gap-1">
              {chiTiet.map((c, i) => (
                <li key={i} className="font-mono text-caption text-danger-ink">
                  {c}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Modal>
  );
}
