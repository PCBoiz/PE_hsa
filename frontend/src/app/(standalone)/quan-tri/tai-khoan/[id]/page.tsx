import Link from 'next/link';

import { chanTu } from '@/lib/chanTu';
import { serverJson } from '@/lib/server-api';

import DongThoiGian from './DongThoiGian';
import HoSoClient from './HoSoClient';
import {
  HD_DONG_THOI_GIAN,
  HD_TRANG_HO_SO,
  type DongThoiGian as DuLieuDongThoiGian,
  type HoSoPayload,
} from './hoSo';

export const metadata = { title: 'Hồ sơ học viên | TopHSA' };

/**
 * Hồ sơ một học viên — mở từ nút "Hồ sơ" ở danh sách tài khoản.
 *
 * Dựng sẵn trên máy chủ như trang danh sách: một lượt gọi mang cả hồ sơ lẫn hai
 * danh sách chọn (nguồn tuyển sinh, người tư vấn), nên form hiện đủ ngay khi
 * trang tới — không có nhịp "ô chọn trống rồi mới đầy". Dòng thời gian gọi SONG
 * SONG (hai lượt Neon nối đuôi là cộng dồn ~245 ms mỗi lượt).
 */
export default async function HoSoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const hopLe = /^\d+$/.test(id);
  const [kq, tg] = hopLe
    ? await Promise.all([
        serverJson<HoSoPayload>(`/api/admin/users/${id}/profile`, { requireAuth: true }, HD_TRANG_HO_SO),
        serverJson<DuLieuDongThoiGian>(`/api/admin/users/${id}/timeline`, { requireAuth: true }, HD_DONG_THOI_GIAN),
      ])
    : [{ ok: false, status: 404, message: 'Đường dẫn hồ sơ không đúng.' } as const, null];

  if (!kq.ok) {
    return (
      // `data-chan`: móc cho e2e phân biệt "không đủ quyền" / "không có" / "máy
      // chủ lỗi" mà không phải dò câu chữ (`lib/chanTu.ts`).
      <div className="py-10" data-chan={chanTu(kq.status)}>
        <h2 className="text-title text-ink">Không mở được hồ sơ này</h2>
        <p className="mt-2 text-body text-ink-2">{kq.message}</p>
        <Link
          href="/quan-tri/tai-khoan"
          className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline"
        >
          ← Về danh sách tài khoản
        </Link>
      </div>
    );
  }

  return (
    <>
      <HoSoClient initial={kq.data} />
      {/* Dòng thời gian hỏng KHÔNG được kéo cả form sập theo: hồ sơ vẫn sửa được,
          chỉ khối này báo không đọc được. */}
      {tg?.ok ? (
        <DongThoiGian duLieu={tg.data} />
      ) : (
        <p className="mx-auto mt-5 max-w-3xl text-small text-ink-3" role="status">
          Chưa đọc được dòng thời gian của em{tg && !tg.ok ? ` — ${tg.message}` : ''}.
        </p>
      )}
    </>
  );
}
