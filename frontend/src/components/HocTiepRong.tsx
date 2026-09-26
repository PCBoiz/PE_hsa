'use client';

/**
 * Khối rỗng của thẻ "Học tiếp" — phần DUY NHẤT cần chạy ở trình duyệt.
 *
 * Tách riêng vì nút "Khám phá khoá học" chuyển tab bằng `navigate('courses')`
 * của `main.js` (SPA cũ: chín "trang" nằm trong CÙNG một route, đổi tab là đổi
 * class `.active` chứ không đổi URL). Một `<Link href>` sẽ tải lại cả trang và
 * rơi về đúng tab dashboard — tức nút trông giống mà làm việc khác.
 *
 * Phần CÓ dữ liệu (`HocTiep`) dựng ở máy chủ; chỉ mảnh này là client.
 */
import { BieuTuong } from './bieuTuong';

/* eslint-disable @typescript-eslint/no-explicit-any */
const W = () => window as any;

export default function HocTiepRong() {
  return (
    <div className="hsa-cont-empty">
      {/* `BieuTuong` chứ KHÔNG `data-icon`: khối này dựng ở máy chủ và chảy tới
          sau, nên `icons.js::mountIcons` kịp nhét SVG vào ô trống trước khi
          React hydrate — React thấy DOM khác và dựng lại cả nhánh (lỗi
          "hydration failed", đo 14/09/2026). Vẽ sẵn thì không còn ô trống. */}
      <div className="hsa-cont-ic"><BieuTuong ten="compass" co={26} /></div>
      <div>
        <b>Bắt đầu hành trình HSA</b>
        <p>Chọn một môn học để vào bài học đầu tiên.</p>
      </div>
      <button className="hsa-cont-btn" onClick={() => W().navigate('courses')}>
        Khám phá khoá học
      </button>
    </div>
  );
}
