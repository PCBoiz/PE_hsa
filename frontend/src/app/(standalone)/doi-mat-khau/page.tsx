import type { Metadata } from 'next';

import ChangePasswordForm from './ChangePasswordForm';

export const metadata: Metadata = {
  title: 'Đổi mật khẩu — ProgrammingEdu × TopHSA',
};

/**
 * Màn đổi mật khẩu.
 *
 * Tồn tại vì chính sách "tài khoản do trung tâm cấp": trợ giảng tạo tài khoản
 * và đọc mật khẩu tạm cho học viên, nghĩa là có ít nhất một người khác biết
 * mật khẩu đó. Bắt đổi ngay lần đăng nhập đầu tiên là cách trả lại quyền riêng
 * tư cho học viên — và phải nói thẳng lý do, không thì đây chỉ là một rào cản
 * vô cớ trước khi được vào học.
 */
export default async function ChangePasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ [k: string]: string | string[] | undefined }>;
}) {
  const sp = await searchParams;
  const lanDau = sp['lan-dau'] === '1';

  return (
    <main className="grid min-h-dvh place-items-center bg-ground px-4 py-10">
      <div className="w-full max-w-[440px]">
        <div className="rounded-lg border border-line bg-surface p-6 shadow-e2">
          <h1 className="text-title text-ink">
            {lanDau ? 'Đặt mật khẩu của riêng bạn' : 'Đổi mật khẩu'}
          </h1>

          {lanDau ? (
            <div className="mt-3 mb-6 rounded-md border-l-[3px] border-brand bg-brand-soft px-4 py-3">
              <p className="text-body text-ink-2">
                Tài khoản này do TopHSA cấp, nên <b className="text-ink">mật khẩu tạm hiện
                tại có người khác biết</b>. Đặt một mật khẩu mới chỉ mình bạn biết rồi vào
                học — mất chưa tới một phút.
              </p>
            </div>
          ) : (
            <p className="mt-1 mb-6 text-body text-ink-3">
              Đặt mật khẩu mới cho tài khoản của bạn.
            </p>
          )}

          <ChangePasswordForm lanDau={lanDau} />
        </div>

        {!lanDau && (
          <p className="mt-4 text-center text-small text-ink-3">
            <a href="/dashboard" className="text-brand hover:underline">
              Quay lại Trang của tôi
            </a>
          </p>
        )}
      </div>
    </main>
  );
}
