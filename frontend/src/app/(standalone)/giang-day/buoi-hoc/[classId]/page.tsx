import Link from 'next/link';

import { HD_CHI_TIET_LOP, type ChiTietLop } from '@/lib/hinhDang';
import { chanTu } from '@/lib/chanTu';
import { serverJson, type HinhDang } from '@/lib/server-api';
import { z } from 'zod';

import SessionsClient, { type SessionRow } from './SessionsClient';
import type { GoiYSinh } from './SinhBuoi';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Buổi học & điểm danh | TopHSA' };

/**
 * Hình dạng do `teaching/reports.py:class_report()` trả về.
 *
 * Khoá là `class`, KHÔNG phải `klass`. Bản đầu của tệp này đoán sai tên đó
 * (30/08/2026) và hậu quả là `if (!detail?.class)` luôn đúng — trang LUÔN hiện
 * "Không mở được lớp này" và chưa ai từng vào được màn hình điểm danh.
 * `tsc` không bắt được vì `serverJson<T>` chỉ ép kiểu, không kiểm gì lúc chạy:
 * kiểu ở đây là lời TỰ KHAI về thứ người viết TƯỞNG backend trả.
 *
 * Đừng sửa tên khoá ở đây mà không mở trang thật trong trình duyệt xem lại.
 */
type ClassDetail = ChiTietLop;

/* Hình dạng hai phản hồi còn lại của trang (T18 mức 2). `SessionRow` là kiểu
   `SessionsClient` đọc — khai đủ khoá bắt buộc; `satisfies` để tsc bắt thiếu. */
type DsBuoi = { sessions: SessionRow[]; quyen?: { xoaBuoi: boolean; baoCaoPhuHuynh: boolean } };
const HD_BUOI = z.looseObject({
  sessions: z.array(z.looseObject({
    id: z.number(),
    startsAt: z.string().nullable(),
    durationMinutes: z.number().nullable(),
    topic: z.string().nullable(),
    status: z.string(),
    note: z.string().nullable(),
    meetingUrl: z.string().nullable().optional(),
    recordingUrl: z.string().nullable().optional(),
    attendanceTakenAt: z.string().nullable().optional(),
    started: z.boolean().optional(),
    attendance: z.looseObject({
      present: z.number(), late: z.number(), absent: z.number(), excused: z.number(),
      unmarked: z.number(),
    }).optional(),
  })),
  quyen: z.looseObject({ xoaBuoi: z.boolean(), baoCaoPhuHuynh: z.boolean() }).optional(),
}) satisfies HinhDang<DsBuoi>;
const HD_GOI_Y = z.looseObject({
  lop: z.looseObject({ id: z.number(), name: z.string(), schedule: z.string().nullable() }),
  dot: z.looseObject({
    id: z.number(), name: z.string(),
    ngayNghi: z.array(z.looseObject({ id: z.number(), ngay: z.string(), ten: z.string() })),
  }).nullable(),
  goiY: z.looseObject({
    weekdays: z.array(z.number()),
    startTime: z.string().nullable(),
    durationMinutes: z.number().nullable(),
    from: z.string(),
    to: z.string().nullable(),
  }),
  coTheSinh: z.boolean(),
}) satisfies HinhDang<GoiYSinh>;

export default async function BuoiHocPage({
  params,
  searchParams,
}: {
  params: Promise<{ classId: string }>;
  searchParams: Promise<{ 'diem-danh'?: string }>;
}) {
  const { classId } = await params;
  // `?diem-danh=<id>` từ trang "Việc hôm nay": mở sẵn sổ điểm danh của đúng
  // buổi đó. Chỉ nhận số — một giá trị lạ không được thành `openId`.
  const { 'diem-danh': dd } = await searchParams;
  const moBuoi = dd && /^\d+$/.test(dd) ? Number(dd) : null;
  const [detail, list, sinh] = await Promise.all([
    serverJson<ClassDetail>(`/api/teach/classes/${classId}`, { requireAuth: true }, HD_CHI_TIET_LOP),
    serverJson<DsBuoi>(`/api/teach/classes/${classId}/sessions`, { requireAuth: true }, HD_BUOI),
    // Gợi ý sinh lịch cả kỳ lấy Ở ĐÂY, cùng lượt dựng trang: nó mang cờ
    // `coTheSinh`, và biết cờ ấy trước khi vẽ thì trợ giảng không bao giờ thấy
    // một nút bấm vào mới báo không được phép.
    serverJson<GoiYSinh>(`/api/teach/classes/${classId}/sessions/generate`, { requireAuth: true }, HD_GOI_Y),
  ]);

  // 404 = lớp không tồn tại HOẶC không phụ trách lớp đó — backend cố ý trả cùng
  // một mã để không lộ ra lớp có tồn tại hay không, nên chỗ này mới là nơi duy
  // nhất được nói câu "không phải giảng viên phụ trách". Mọi mã khác (500, mất
  // kết nối) phải nói đúng câu của nó, không mượn câu này.
  const klass = detail.ok ? detail.data.class : undefined;

  if (!klass) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16" data-chan={chanTu(detail.ok ? 404 : detail.status)}>
        <h1 className="text-title text-ink">Không mở được lớp này</h1>
        <p className="mt-2 text-body text-ink-2">
          {!detail.ok && detail.status !== 404
            ? detail.message
            : 'Lớp không tồn tại, hoặc bạn không phải giảng viên phụ trách lớp đó.'}
        </p>
        <Link href="/dashboard" className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline">
          ← Về khu Giảng dạy
        </Link>
      </main>
    );
  }

  return (
    <div className="min-h-dvh bg-ground">
      <main>
          {/* Dải tiêu đề nằm TRONG `<main>`: là `<header>` ngoài `main` thì thành
              banner thứ hai (axe `landmark-no-duplicate-banner`), là `div` ngoài
              `main` thì rơi ngoài mọi mốc (axe `region`) — đo 20/09/2026. */}
        <div className="border-b border-line bg-surface">
          <div className="mx-auto flex max-w-5xl flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-4">
            {/* `/giang-day` chứ KHÔNG `/dashboard` (21/09/2026): nhãn nói "Khu
                Giảng dạy" mà bấm vào lại về Trang của tôi — rà vai nhân sự bắt
                được ở cả ba trang lớp. */}
            <Link href="/giang-day" className="-my-3 py-3 text-small text-ink-3 hover:text-brand-ink">
              ← Việc hôm nay
            </Link>
            <h1 className="text-section text-ink">{klass.name}</h1>
            {klass.schedule && <span className="text-small text-ink-3">{klass.schedule}</span>}
            <Link
              href={`/giang-day/bai-tap/${klass.id}`}
              className="-my-3 py-3 text-small text-brand-ink underline"
            >
              Bài tập &amp; chấm bài
            </Link>
          </div>
        </div>
        <div className="mx-auto max-w-5xl px-4 py-6">
        <SessionsClient
          classId={Number(classId)}
          className={klass.name}
          initial={list.ok ? list.data.sessions : []}
          goiYSinh={sinh.ok ? sinh.data : null}
          moBuoi={moBuoi}
          /* Thiếu (API cũ) thì coi như được — máy chủ vẫn là hàng rào thật. */
          quyen={list.ok ? (list.data.quyen ?? { xoaBuoi: true, baoCaoPhuHuynh: true }) : { xoaBuoi: true, baoCaoPhuHuynh: true }}
        />
        </div>
      </main>
    </div>
  );
}
