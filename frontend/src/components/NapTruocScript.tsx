/**
 * Báo trình duyệt TẢI TRƯỚC các script cũ, ngay từ HTML máy chủ trả về.
 *
 * ── VÌ SAO (07/09/2026) ───────────────────────────────────────────────────
 *
 * `LegacyScripts` chèn thẻ `<script>` trong một `useEffect`, tức chúng chỉ bắt
 * đầu TẢI sau khi React hydrate xong. Đo trên Trang của tôi (bản production,
 * CPU chậm 4×):
 *
 *     TTFB                11ms      ← máy chủ nhanh
 *     HTML tải xong      637ms
 *     trang load xong    759ms
 *     bảy tệp JS cũ    ~2550ms      ← mới xong ở đây
 *     FCP               2184ms      ← trang TRẮNG suốt 1,4 giây
 *     LCP               2796ms
 *
 * Khoảng trống giữa 759ms và 2184ms là thời gian trình duyệt KHÔNG LÀM GÌ với
 * mạng: nó đã tải xong mọi thứ được khai trong HTML, và đang chờ React nói cho
 * biết còn bảy tệp nữa.
 *
 * `<link rel="preload" as="script">` nằm trong HTML máy chủ trả về, nên trình
 * duyệt bắt đầu tải chúng NGAY — song song với việc hydrate. Khi `useEffect`
 * chạy và tạo thẻ `<script>`, tệp đã nằm sẵn trong bộ đệm.
 *
 * ── VÌ SAO KHÔNG CHUYỂN THẲNG SANG `<script defer>` ──────────────────────
 *
 * Đơn giản hơn, nhưng đổi NGỮ NGHĨA. `LegacyScripts` gán `globals` vào
 * `window` TRƯỚC khi nạp, và dedupe theo `data-pe-legacy` khi điều hướng
 * client-side quay lại trang — tệp cũ khai hàm/biến toàn cục nên nạp hai lần
 * là lỗi khai trùng. `preload` giữ nguyên toàn bộ cơ chế ấy và chỉ dời phần
 * TẢI lên sớm.
 *
 * ── DANH SÁCH PHẢI LÀ MỘT ────────────────────────────────────────────────
 *
 * Nơi gọi truyền CÙNG một mảng cho cả `NapTruocScript` và `LegacyScripts`.
 * Hai mảng chép tay sẽ trôi khỏi nhau, và kiểu trôi ở đây im lặng đúng theo
 * hướng xấu: tải trước một tệp không ai dùng thì lãng phí, còn quên tải trước
 * một tệp thì mất đúng phần lợi này mà không có dấu hiệu nào.
 */
export default function NapTruocScript({ srcs }: { srcs: string[] }) {
  return (
    <>
      {srcs.map((s) => (
        <link key={s} rel="preload" as="script" href={s} />
      ))}
    </>
  );
}
