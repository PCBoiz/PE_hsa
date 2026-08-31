import type { Metadata } from 'next';

import LoginForm from './LoginForm';

/**
 * Trang đăng nhập — dựng lại 27/08/2026.
 *
 * Vì sao bỏ nửa bên phải: bản cũ là một trang bán hàng (khối "Chinh phục Đánh
 * giá năng lực", 3 hợp phần, 150 câu mỗi đề, 5 chip có emoji). Từ khi bỏ tự
 * đăng ký, **mọi người tới đây đều đã là học viên của trung tâm** — họ đã đóng
 * tiền học rồi, không còn ai cần thuyết phục. Giữ khối đó chỉ làm chậm việc
 * duy nhất họ muốn làm: vào học.
 *
 * Ba thứ khác đã bỏ, mỗi thứ vì một lý do cụ thể:
 *  · Chuyển sắc hồng–tím ở nút chính: màu đó KHÔNG nằm trong bảng đã khoá.
 *  · Emoji làm icon: sản phẩm có sẵn bộ SVG, và emoji hiện khác nhau trên mỗi
 *    hệ điều hành nên không kiểm soát được diện mạo.
 *  · Nền tối cố định: trang này từng là màn hình duy nhất phớt lờ lựa chọn
 *    sáng/tối của người dùng.
 *
 * Đây là Server Component; chỉ riêng biểu mẫu là client.
 */
export const metadata: Metadata = {
  title: 'Đăng nhập — ProgrammingEdu × TopHSA',
};

function Mark() {
  return (
    <span className="grid size-11 shrink-0 place-items-center rounded-md bg-brand-fill text-white">
      <svg viewBox="0 0 24 24" className="size-6" fill="currentColor" aria-hidden="true">
        <circle cx="12" cy="12" r="4" />
        <path
          d="M8 6l4-4 4 4M8 18l4 4 4-4M4 12H2m20 0h-2M6.3 6.3l-1.4-1.4M19.1 19.1l-1.4-1.4M6.3 17.7l-1.4 1.4M19.1 4.9l-1.4 1.4"
          stroke="currentColor"
          strokeWidth="1.8"
          fill="none"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  // Đọc mã lỗi OAuth ngay trên máy chủ để câu giải thích nằm sẵn trong HTML.
  const sp = await searchParams;
  const raw = Array.isArray(sp.error) ? sp.error[0] : sp.error;
  // Vừa đổi mật khẩu xong: phiên cũ đã bị cắt có chủ ý (§39). Nói ra, nếu không
  // người dùng vừa làm đúng lại thấy mình bị đá về trang đăng nhập và tưởng
  // hỏng — rồi thử mật khẩu CŨ.
  const vuaDoi = (Array.isArray(sp['vua-doi-mat-khau']) ? sp['vua-doi-mat-khau'][0]
                                                       : sp['vua-doi-mat-khau']) === '1';

  return (
    <main className="grid min-h-dvh place-items-center bg-ground px-4 py-10">
      <div className="w-full max-w-[420px]">
        <div className="mb-6 flex items-center gap-3">
          <Mark />
          <span className="text-section text-ink">
            ProgrammingEdu <span className="text-ink-3">×</span> TopHSA
          </span>
        </div>

        <div className="rounded-lg border border-line bg-surface p-6 shadow-e2">
          <h1 className="text-title text-ink">Đăng nhập</h1>
          <p className="mt-1 mb-6 text-body text-ink-3">
            Tiếp tục hành trình luyện thi Đánh giá năng lực của bạn.
          </p>

          {vuaDoi && (
            <p
              role="status"
              className="mb-5 rounded-md border border-success/30 bg-success/10 px-3 py-2 text-small text-success-ink"
            >
              Đã đổi mật khẩu. Mọi thiết bị đang đăng nhập tài khoản này đều bị đăng xuất —
              kể cả máy bạn vừa dùng. Đăng nhập lại bằng <b>mật khẩu mới</b>.
            </p>
          )}

          <LoginForm oauthError={raw ?? null} />

          <div className="mt-6 border-t border-line pt-5">
            <p className="text-small text-ink-3">
              <b className="text-ink-2">Quên mật khẩu?</b> Nhắn cho giảng viên phụ trách lớp
              hoặc trung tâm — tài khoản sẽ được đặt lại ngay trong buổi.
            </p>
            <p className="mt-3 text-small text-ink-3">
              <b className="text-ink-2">Chưa có tài khoản?</b> Tài khoản do TopHSA cấp khi bạn
              đăng ký học. Liên hệ trung tâm để được cấp.
            </p>
          </div>
        </div>

        <p className="mt-5 text-center text-small text-ink-3">
          Luyện thi Đánh giá năng lực ĐHQG Hà Nội · 3 hợp phần · 76 bài
        </p>
      </div>
    </main>
  );
}
