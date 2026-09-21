'use client';

import Link from 'next/link';
import { useEffect } from 'react';

/**
 * Trang cho LỖI DỰNG TRANG (khác `not-found.tsx` — đó là "không có trang này").
 *
 * Vì sao có (rà vai nhân sự 21/09/2026): repo chưa có `error.tsx` nào, nên mọi
 * lỗi ném ra lúc dựng trang đều rơi vào màn mặc định của Next —
 * "This page couldn't load" bằng tiếng Anh, không nói làm gì tiếp, giữa một
 * sản phẩm toàn tiếng Việt. Agent gặp đúng một lần ở `/dashboard` sau khi đăng
 * nhập ở khổ điện thoại và không tái hiện được; thứ tái hiện được thì mình sửa,
 * thứ không tái hiện được thì ít nhất phải nói cho người dùng hiểu.
 *
 * `reset()` là của Next: dựng lại đúng nhánh vừa hỏng mà KHÔNG tải lại cả
 * trang — với lỗi thoáng qua (mạng chớp, một lượt gọi lỗi) thì một cú bấm là
 * xong. Vẫn để thêm đường về Trang của tôi cho trường hợp hỏng thật.
 *
 * Câu lỗi kỹ thuật KHÔNG hiện cho người dùng: nó không giúp họ làm gì, và
 * thông điệp lỗi đôi khi mang tên bảng, tên cột. `digest` thì hiện — đó là mã
 * Next sinh ra để đối chiếu với log máy chủ, và là thứ người dùng đọc lại cho
 * mình khi báo lỗi.
 */
export default function LoiTrang({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Ghi ra console để còn dấu vết khi mở DevTools; máy chủ đã có log riêng.
    console.error('[trang hỏng]', error);
  }, [error]);

  return (
    <main className="mx-auto max-w-3xl px-4 py-16">
      <h1 className="text-title text-ink">Trang này đang không mở được</h1>
      <p className="mt-2 text-body text-ink-2">
        Lỗi xảy ra khi hệ thống dựng trang. Bấm “Thử lại” — phần lớn trường hợp là
        trục trặc thoáng qua. Nếu vẫn vậy, báo cho người quản lý kèm mã bên dưới.
      </p>
      {error.digest && (
        <p className="mt-3 font-mono text-small text-ink-3">Mã lỗi: {error.digest}</p>
      )}
      <div className="mt-6 flex flex-wrap items-center gap-4">
        <button
          type="button"
          onClick={() => reset()}
          className="inline-flex min-h-11 items-center rounded-md bg-brand-fill px-4 text-body font-semibold text-white"
        >
          Thử lại
        </button>
        <Link href="/dashboard" className="-mx-2 inline-flex min-h-11 items-center px-2 text-body text-brand-ink underline">
          ← Về trang của tôi
        </Link>
      </div>
    </main>
  );
}
