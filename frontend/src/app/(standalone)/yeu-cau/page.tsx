import Link from 'next/link';

import { chanTu } from '@/lib/chanTu';
import { serverJson } from '@/lib/server-api';
import { VAI_GIANG_VIEN, VAI_HOC_VIEN, VAI_HOC_VU, VAI_QUAN_TRI, VAI_TRO_GIANG } from '@/lib/vaiTro';
import { HD_DS, HD_LUA_CHON_HV, HD_LUA_CHON_NS, type DanhSach, type LuaChonHV, type LuaChonNS } from '@/lib/yeuCau';

import { layVai } from '../quan-tri/layVai';
import HopHocVien from './HopHocVien';
import HopNhanSu from './HopNhanSu';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Yêu cầu | TopHSA' };

/** Cùng bốn vai với `IsTeachingStaff` (lib/quyenVai.ts) — ai vào được hộp nhân sự. */
const NHAN_SU = [VAI_QUAN_TRI, VAI_HOC_VU, VAI_GIANG_VIEN, VAI_TRO_GIANG];

/**
 * `/yeu-cau` — HỘP YÊU CẦU (E3). Học viên: gửi + theo dõi yêu cầu của mình. Nhân sự dạy học:
 * hộp chung đã lọc theo phạm vi ở máy chủ. Vai khác (biên tập nội dung): màn chặn — hai đường
 * API đều trả 403 cho họ, dựng hộp rỗng là nói dối "không có yêu cầu nào".
 */
export default async function YeuCauPage() {
  const vai = await layVai();
  if (!vai.ok) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16" data-chan="loi">
        <h1 className="text-title text-ink">Không mở được trang này</h1>
        <p className="mt-2 text-body text-ink-2">{vai.loi}</p>
      </main>
    );
  }

  if (vai.vai === VAI_HOC_VIEN) {
    const [ds, lc] = await Promise.all([
      serverJson<DanhSach>('/api/yeu-cau', { requireAuth: true }, HD_DS),
      serverJson<LuaChonHV>('/api/yeu-cau/lua-chon', { requireAuth: true }, HD_LUA_CHON_HV),
    ]);
    return (
      <main className="mx-auto max-w-3xl px-4 py-6">
        <h1 className="mb-1 text-section text-ink">Hỏi &amp; yêu cầu</h1>
        <p className="mb-4 text-small text-ink-3">Hỏi giảng viên, trợ giảng hoặc nhờ trung tâm hỗ trợ. Trả lời hiện ở đây.</p>
        <HopHocVien
          initial={ds.ok ? ds.data.yeuCau : []}
          luaChon={lc.ok ? lc.data : null}
          // Danh sách rỗng vì chưa gửi gì và rỗng vì không đọc được trông y hệt nhau.
          loiTai={ds.ok ? null : ds.message}
        />
      </main>
    );
  }

  if (vai.vai && NHAN_SU.includes(vai.vai)) {
    const [ds, lc] = await Promise.all([
      serverJson<DanhSach>('/api/teach/yeu-cau?mo=1', { requireAuth: true }, HD_DS),
      serverJson<LuaChonNS>('/api/teach/yeu-cau/lua-chon', { requireAuth: true }, HD_LUA_CHON_NS),
    ]);
    if (!ds.ok && ds.status !== null) {
      return (
        <main className="mx-auto max-w-3xl px-4 py-16" data-chan={chanTu(ds.status)}>
          <h1 className="text-title text-ink">Không mở được hộp yêu cầu</h1>
          <p className="mt-2 text-body text-ink-2">{ds.message}</p>
        </main>
      );
    }
    return (
      <main className="mx-auto max-w-5xl px-4 py-6">
        <h1 className="mb-4 text-section text-ink">Yêu cầu</h1>
        <HopNhanSu
          initial={ds.ok ? ds.data.yeuCau : []}
          coTheDuyet={ds.ok ? !!ds.data.coTheDuyet : false}
          luaChon={lc.ok ? lc.data : null}
          loiTai={ds.ok ? null : ds.message}
        />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-16" data-chan="vai">
      <h1 className="text-title text-ink">Trang này dành cho học viên và nhân sự dạy học</h1>
      <p className="mt-2 text-body text-ink-2">Tài khoản của bạn không gửi hay xử lý yêu cầu.</p>
      <Link href="/dashboard" className="mt-6 -mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline">
        ← Về trang của tôi
      </Link>
    </main>
  );
}
