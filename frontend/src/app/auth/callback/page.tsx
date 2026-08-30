'use client';

// Điểm hạ cánh sau khi đăng nhập bằng Google/Facebook.
//
// Backend trả token qua fragment của URL (`#access=...`). Fragment không bao
// giờ được gửi lên máy chủ — đó là thiết kế của trình duyệt — nên bắt buộc
// phải có một đoạn JavaScript đọc nó. Điểm khác so với bản trước: token KHÔNG
// còn được cất vào localStorage; nó được nộp ngay cho /auth/session để cất vào
// cookie httpOnly rồi bị xoá khỏi thanh địa chỉ. Cửa sổ mà token còn nằm trong
// tầm với của JavaScript chỉ dài đúng một lời gọi mạng.
import { useEffect } from 'react';

export default function OAuthCallbackPage() {
  useEffect(() => {
    const params = new URLSearchParams(window.location.hash.replace(/^#/, ''));
    const access = params.get('access');
    const refresh = params.get('refresh');

    if (!access) {
      window.location.replace('/login?error=oauth_failed');
      return;
    }

    // Xoá fragment khỏi thanh địa chỉ NGAY, trước cả khi gọi mạng — để người
    // dùng không vô tình chép cả token khi chia sẻ đường dẫn.
    history.replaceState(null, '', window.location.pathname);

    fetch('/auth/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ access, refresh }),
    })
      .then((r) => {
        window.location.replace(r.ok ? '/dashboard' : '/login?error=oauth_failed');
      })
      .catch(() => window.location.replace('/login?error=oauth_failed'));
  }, []);

  return (
    <p
      style={{
        fontFamily: 'var(--font-body), system-ui, sans-serif',
        fontSize: 15,
        color: 'var(--t2, #4B4459)',
        padding: 24,
      }}
    >
      Đang đưa bạn vào Trang của tôi…
    </p>
  );
}
