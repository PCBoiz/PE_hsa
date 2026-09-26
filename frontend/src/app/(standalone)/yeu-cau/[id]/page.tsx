import Link from 'next/link';

import { chanTu } from '@/lib/chanTu';
import { serverJson } from '@/lib/server-api';
import { VAI_HOC_VIEN } from '@/lib/vaiTro';
import { HD_YEU_CAU, type YeuCau } from '@/lib/yeuCau';

import { layVai } from '../../quan-tri/layVai';
import ChiTietYeuCau from './ChiTietYeuCau';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Yêu cầu | TopHSA' };

/**
 * `/yeu-cau/<id>` — MỘT yêu cầu, cho mọi vai (chuông thông báo trỏ về đây). Học viên đọc qua
 * đường học viên (không có ghi chú nội bộ), nhân sự qua đường nhân sự. Ngoài phạm vi → máy chủ
 * trả 404 (không lộ yêu cầu có tồn tại) → màn `khong-thay`.
 */
export default async function ChiTietYeuCauPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const vai = await layVai();
  const laHocVien = vai.ok && vai.vai === VAI_HOC_VIEN;
  const so = /^\d+$/.test(id) ? id : '0';
  const kq = await serverJson<YeuCau>(
    laHocVien ? `/api/yeu-cau/${so}` : `/api/teach/yeu-cau/${so}`, { requireAuth: true }, HD_YEU_CAU);
  if (!kq.ok) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16" data-chan={chanTu(kq.status)}>
        <h1 className="text-title text-ink">Không mở được yêu cầu này</h1>
        <p className="mt-2 text-body text-ink-2">
          {kq.status === 404 ? 'Yêu cầu không tồn tại, hoặc không thuộc phạm vi của bạn.' : kq.message}
        </p>
        <Link href="/yeu-cau" className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline">
          ← Danh sách yêu cầu
        </Link>
      </main>
    );
  }
  return (
    <main className="mx-auto max-w-4xl px-4 py-6">
      <ChiTietYeuCau initial={kq.data} laHocVien={laHocVien} />
    </main>
  );
}
