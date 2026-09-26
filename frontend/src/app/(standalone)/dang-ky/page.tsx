import type { Metadata } from 'next';
import Link from 'next/link';

import { HD_LUA_CHON_DANG_KY } from '@/lib/dangKy';
import { serverJson } from '@/lib/server-api';

import PhieuDangKy from './PhieuDangKy';

export const metadata: Metadata = {
  title: 'Đăng ký học — TopHSA',
};

/**
 * Học viên mới TỰ mở tài khoản (§73, E5 — bảng TopHSA dòng 26). Trang KHÔNG cần
 * đăng nhập.
 *
 * Danh mục "bạn biết TopHSA từ đâu" gọi ngay trên máy chủ, lúc đang dựng trang:
 * trang tới nơi là ô chọn đã có đủ mục, không có một nhịp trống nào. Và nó tới từ
 * `teaching/ho_so.NGUON_TUYEN_SINH` chứ không gõ lại ở đây (RULES §7).
 *
 * Gọi hỏng (backend đang ngủ) thì KHÔNG dựng một phiếu thiếu ô — em điền xong mới
 * bị từ chối vì một ô em không thấy là một cách làm người ta bỏ đi. Hiện thẳng câu
 * lỗi kèm đường về, đúng như `serverJson` đã soạn.
 */
export default async function DangKyPage() {
  const ket = await serverJson('/auth/dang-ky', {}, HD_LUA_CHON_DANG_KY);

  return (
    <main className="grid min-h-dvh place-items-center bg-ground px-4 py-10">
      <div className="w-full max-w-[520px]">
        <div className="rounded-lg border border-line bg-surface p-6 shadow-e2" data-khu="dang-ky">
          <h1 className="text-title text-ink">Đăng ký học tại TopHSA</h1>
          <p className="mt-1 mb-6 text-body text-ink-3">
            Điền thông tin dưới đây. Hệ thống gửi một thư xác nhận tới email của bạn; bấm vào
            đường dẫn trong thư là tài khoản hoạt động. Học vụ sẽ liên hệ để xếp lớp phù hợp.
          </p>

          {ket.ok ? (
            <PhieuDangKy nguon={ket.data.nguon} />
          ) : (
            <p
              role="alert"
              className="rounded-md border-l-[3px] border-danger bg-danger/10 px-4 py-3 text-body text-ink-2"
              data-chan="khong-tai-duoc"
            >
              {ket.message} Nếu vẫn không được, bạn gọi trực tiếp cho TopHSA để đăng ký.
            </p>
          )}

          <div className="mt-6 border-t border-line pt-5">
            <p className="text-small text-ink-3">
              <b className="text-ink-2">Đã có tài khoản?</b>{' '}
              <Link href="/login" className="-my-3 inline-block py-3 text-brand-ink underline">
                Đăng nhập
              </Link>
            </p>
            <p className="mt-3 text-small text-ink-3">
              Đã đăng ký nhưng chưa nhận được thư xác nhận? Vào{' '}
              <Link href="/login" className="-my-3 inline-block py-3 text-brand-ink underline">
                trang đăng nhập
              </Link>{' '}
              và chọn “Gửi lại thư xác nhận”.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
