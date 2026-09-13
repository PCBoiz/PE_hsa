import { Suspense } from 'react';

import DashboardClient from './DashboardClient';
import HocTiep from '@/components/HocTiep';
import LopCuaToiKhung from '@/components/LopCuaToiKhung';
import LopCuaToiNguon from '@/components/LopCuaToiNguon';

/**
 * TRANG CỦA TÔI — vỏ MÁY CHỦ mỏng bọc quanh phần client.
 *
 * ── VÌ SAO TÁCH (14/09/2026) ──────────────────────────────────────────────
 *
 * Toàn bộ màn này là `'use client'` vì SPA cũ (`main.js::navigate`) đổi tab
 * bằng class chứ không đổi route — không đổi được chuyện đó trong một vòng.
 * Nhưng một component `'use client'` KHÔNG nhúng được component máy chủ, mà
 * thẻ "Học tiếp" thì cần dữ liệu ngay trong HTML đầu tiên (nó là phần tử LCP).
 *
 * Cách đi: trang trở thành component MÁY CHỦ, dựng `<HocTiep />` rồi truyền
 * xuống như một nút React. Phần còn lại vẫn client y như cũ. Đây cũng là lối
 * mở cho các khối sau: mỗi khối chuyển sang máy chủ chỉ cần thêm một prop.
 *
 * ── `Suspense` KHÔNG PHẢI TRANG TRÍ (đo 14/09/2026) ───────────────────────
 *
 * Bản đầu không có nó: trang chờ `HocTiep` gọi xong hai lượt API rồi mới gửi
 * BẤT KỲ byte HTML nào. Backend ngủ dậy mất 1,7–2,8 s cho một lượt, nên LCP
 * **xấu đi**, từ 2,46 s lên **4,28 s** — tối ưu thành phản tác dụng, và chỉ
 * nhìn thấy bằng cách đo lại. Với `Suspense`, khung trang đi ngay, thẻ "Học
 * tiếp" chảy tới sau; chỗ của nó được giữ sẵn bằng một khối cùng chiều cao nên
 * không có cú nhảy bố cục (CLS).
 */
function KhungHocTiep() {
  // 74px = chiều cao thật của `.hsa-cont-link` (18px đệm trên/dưới + 46px huy
  // hiệu + đường viền). Giữ đúng chỗ để nội dung thật không đẩy trang.
  return <div className="skel" style={{ height: '4.625rem', margin: '0.25rem' }} aria-hidden="true" />;
}

export default function DashboardPage() {
  return (
    <DashboardClient
      hocTiep={(
        <Suspense fallback={<KhungHocTiep />}>
          <HocTiep />
        </Suspense>
      )}
      /* "Lớp của bạn" cũng chảy, nhưng chỗ của nó được GIỮ bằng một khung
         cùng cấu trúc (`LopCuaToiKhung`) — nó cao 333px (390px: 465) và nằm
         TRÊN thẻ "Học tiếp", tới muộn mà không giữ chỗ là đẩy cả cột xuống
         (đo: CLS 0,177). Chờ hẳn ở máy chủ thì hết nhảy nhưng LCP vọt lên
         4,59s vì không byte nào đi trước `/api/lop-cua-toi` (1,45s). */
      lopCuaBan={(
        <Suspense fallback={<LopCuaToiKhung />}>
          <LopCuaToiNguon />
        </Suspense>
      )}
    />
  );
}
