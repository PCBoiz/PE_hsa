import Link from 'next/link';

import AppShell from '@/components/AppShell';
import PageStyles from '@/components/PageStyles';

import { serverJson, type Ket } from '@/lib/server-api';
import {
  BAN_GHI,
  HD_TRANG_BAN_GHI,
  HD_TRANG_HOC_LIEU,
  HOC_LIEU,
  type Loai,
  type TrangBanGhi,
  type TrangHocLieu,
  duongTrang,
} from '@/lib/xemDu';

import { layVai } from '../../../quan-tri/layVai';
import XemLaiClient from './XemLaiClient';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Xem lại bài | TopHSA' };

const KHONG_THAY: Ket<never> = { ok: false, status: 404, message: 'Không tìm thấy lớp này.' };

/**
 * `/lop/<id>/xem-lai` — em xem lại ĐỦ bản ghi và tài liệu của cả khoá (dòng 29, 30).
 *
 * Vì sao là một trang riêng chứ không mở rộng thẻ lớp: thẻ lớp trả lời "tối nay học gì, còn
 * bài nào phải nộp" và phải đọc được trong mươi giây. Một lớp ba tháng có ~26 buổi và hàng
 * chục tài liệu; đổ hết vào thẻ là làm chìm đúng cái dòng em cần. Thẻ giữ bốn dòng gần nhất
 * cộng hai đường "Xem tất cả" dẫn tới đây — `?xem=tai-lieu` mở sẵn tab Tài liệu, để đường ấy
 * không bắt em bấm thêm một lần nữa.
 *
 * Trang ĐẦU tải sẵn ở máy chủ: bốn bước "HTML rỗng → JS → gọi API → vẽ" đủ lâu để em tưởng
 * trang trắng. Máy chủ trả 404 cho lớp em không học (không 403 — không lộ lớp nào tồn tại),
 * nên trang không tự kiểm quyền: nó chỉ nói lại bằng lời người dùng.
 */
export default async function XemLaiPage({
  params, searchParams,
}: {
  params: Promise<{ classId: string }>;
  searchParams: Promise<{ xem?: string }>;
}) {
  const [{ classId }, { xem }] = await Promise.all([params, searchParams]);
  const id = Number(classId);
  const hopLe = Number.isInteger(id) && id > 0;
  const tabDau: Loai = xem === 'tai-lieu' ? HOC_LIEU : BAN_GHI;

  // Chỉ tải TRƯỚC danh sách của tab đang mở — tab kia tải khi em bấm sang. Hai nhánh là hai
  // biến riêng chứ không một biến rồi ép kiểu: ép kiểu ở đây là tự hứa với `tsc` một điều nó
  // không kiểm được, và chỗ đúng để hứa hão thì không có chỗ nào.
  const [bg, tl, vai] = await Promise.all([
    hopLe && tabDau === BAN_GHI
      ? serverJson<TrangBanGhi>(duongTrang(id, BAN_GHI),
                                { requireAuth: true }, HD_TRANG_BAN_GHI)
      : Promise.resolve(null),
    hopLe && tabDau === HOC_LIEU
      ? serverJson<TrangHocLieu>(duongTrang(id, HOC_LIEU),
                                 { requireAuth: true }, HD_TRANG_HOC_LIEU)
      : Promise.resolve(null),
    layVai(),
  ]);
  const kq: Ket<{ lop: { name: string } }> = bg ?? tl ?? KHONG_THAY;
  const khongThay = !kq.ok && kq.status === 404;

  return (
    <div className="min-h-dvh bg-ground">
      <PageStyles hrefs={['/static/css/theme.css', '/static/css/shell.css']} />
      <AppShell
        spa={false}
        dieuKhien="react"
        vai={vai.ok ? vai.vai : undefined}
        ten={vai.ok ? vai.ten : undefined}
      />
      <main className="mx-auto max-w-3xl px-4 pb-6 pt-[calc(var(--topbar-h)+1.5rem)]">
        {khongThay ? (
          <section className="rounded-xl border border-line bg-surface p-5" aria-labelledby="xl-khong">
            <h1 id="xl-khong" className="m-0 text-section text-ink">Không tìm thấy lớp này</h1>
            <p className="mt-2 mb-0 text-ink-2">
              Trang này chỉ mở cho lớp bạn đang học. Nếu bạn vừa chuyển lớp hoặc đã kết thúc
              khoá, hãy nhắn học vụ để được mở lại.
            </p>
            <p className="mt-3 mb-0">
              <Link href="/" className="font-semibold text-brand-ink underline-offset-2 hover:underline">
                Về trang của tôi →
              </Link>
            </p>
          </section>
        ) : (
          <>
            <h1 className="mb-1 text-section text-ink">Xem lại bài</h1>
            <p className="mb-4 text-small text-ink-3">
              {kq.ok ? kq.data.lop.name : 'Lớp của bạn'} · bản ghi buổi học và tài liệu của cả khoá.
            </p>
            <XemLaiClient
              lopId={id}
              tabDau={tabDau}
              dauBanGhi={bg?.ok ? bg.data : null}
              dauTaiLieu={tl?.ok ? tl.data : null}
              // Danh sách rỗng vì chưa có bản ghi nào và rỗng vì không đọc được trông y hệt
              // nhau — và ở trường hợp thứ hai em sẽ tưởng lớp mình chưa có gì để xem lại.
              loiTai={kq.ok ? null : kq.message}
            />
          </>
        )}
      </main>
    </div>
  );
}
