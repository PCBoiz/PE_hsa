'use client';

/**
 * Lưới cuối cùng: lỗi ném ra từ chính `layout.tsx` gốc — lúc ấy `error.tsx`
 * không dựng được vì nó nằm TRONG layout ấy. Next thay cả cây bằng component
 * này, nên nó phải tự mang `<html>` và `<body>`, và không dùng được component
 * hay CSS nào của sản phẩm (chúng đều nằm trong layout vừa hỏng) — kiểu viết
 * thẳng ở đây là cố ý, không phải quên.
 */
export default function LoiToanCuc({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="vi">
      <body style={{ margin: 0, fontFamily: 'system-ui, sans-serif', background: '#F7F7FB', color: '#141023' }}>
        <main style={{ maxWidth: '40rem', margin: '0 auto', padding: '4rem 1rem' }}>
          <h1 style={{ fontSize: '1.5rem', margin: 0 }}>Hệ thống đang không mở được</h1>
          <p style={{ lineHeight: 1.6 }}>
            Bấm “Thử lại”. Nếu vẫn vậy, báo cho người quản lý kèm mã bên dưới.
          </p>
          {error.digest && (
            <p style={{ fontFamily: 'monospace', color: '#4B4459' }}>Mã lỗi: {error.digest}</p>
          )}
          <button
            type="button"
            onClick={() => reset()}
            style={{
              minHeight: '2.75rem', padding: '0 1rem', border: 'none', borderRadius: '0.5rem',
              background: '#6D5AE6', color: '#fff', fontSize: '1rem', fontWeight: 600, cursor: 'pointer',
            }}
          >
            Thử lại
          </button>
        </main>
      </body>
    </html>
  );
}
