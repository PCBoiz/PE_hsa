import BangHuongDan from '@/components/BangHuongDan';

import { layVai } from '../quan-tri/layVai';

/**
 * Hướng dẫn CỦA ĐÚNG VAI người đang đăng nhập.
 *
 * Mặc định LỌC theo vai: người mới mở ra thấy đúng phần việc của mình, không
 * phải tự dò qua chín bài để đoán bài nào liên quan. `?tat-ca=1` bỏ lọc —
 * đường ra ấy phải có, vì "vai tôi chưa có bài nào" mà không lối đi tiếp là
 * một ngõ cụt.
 *
 * Nội dung dựng ở `components/BangHuongDan.tsx`, dùng chung với trang trong
 * khu Vận hành — hai bản chép tay thì bản ít người đọc hơn sẽ lệch trước.
 */
export const dynamic = 'force-dynamic';
export const metadata = { title: 'Hướng dẫn | TopHSA' };

export default async function Trang({
  searchParams,
}: {
  searchParams: Promise<{ 'tat-ca'?: string }>;
}) {
  const [kq, tham] = await Promise.all([layVai(), searchParams]);
  const vai = kq.ok ? kq.vai : undefined;
  return <BangHuongDan vai={vai} loc={tham['tat-ca'] !== '1'} />;
}
