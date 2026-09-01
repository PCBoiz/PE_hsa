/**
 * Hook phân giải module cho các unit test chạy bằng Node THUẦN.
 *
 * Bộ kiểm ở đây cố ý không dùng runner (vitest/jest): thêm một runner là thêm
 * một tầng biến đổi mã giữa thứ ta viết và thứ ta chạy, mà cả hai lỗi đắt nhất
 * đợt này (`middleware.ts` giết phiên khi 5xx, XSS ở forum) đều là lỗi HÀNH VI
 * chứ không phải lỗi cú pháp — cái cần là gọi được mã thật.
 *
 * Có hai thứ bundler của Next phân giải được mà Node thì không:
 *
 *   · `@/lib/auth` — alias khai trong `tsconfig.json`, Node không đọc tsconfig.
 *     Alias không mang đuôi tệp, mà nguồn ở đây là TypeScript; Node 24 tự bóc
 *     kiểu khi thấy `.ts`, nên chỉ cần nối đuôi vào.
 *   · `next/server`, `next/headers` — gói `next` KHÔNG khai trường `exports`,
 *     nên bộ phân giải ESM của Node đòi đủ đuôi `.js` (chính nó gợi ý thế trong
 *     thông báo lỗi).
 *
 * Hook này chỉ dịch TÊN module. Nó không đụng tới nội dung tệp: thứ chạy trong
 * bộ kiểm vẫn là `src/middleware.ts` nguyên bản, không phải một bản chép.
 */
import { pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SRC = pathToFileURL(
  join(dirname(fileURLToPath(import.meta.url)), '..', '..', 'src') + '/',
).href;

export async function resolve(spec, ctx, next) {
  if (spec.startsWith('@/')) return next(new URL(spec.slice(2) + '.ts', SRC).href, ctx);
  if (spec.startsWith('next/') && !spec.endsWith('.js')) return next(spec + '.js', ctx);
  return next(spec, ctx);
}
