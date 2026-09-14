/**
 * BẮT ĐẦU GỌI DỮ LIỆU NGAY TỪ HTML MÁY CHỦ TRẢ VỀ.
 *
 * ── VÌ SAO (đo 14/09/2026, bản production, CPU chậm 4×) ────────────────────
 *
 * Trang của tôi dựng nội dung bằng TẦNG JS CŨ, mà tầng ấy chỉ được chèn vào
 * trang trong `useEffect` của `LegacyScripts` — tức sau khi React hydrate
 * xong. Thác thời gian một lượt mở:
 *
 *     0,2 s  chunk React tải xong
 *     0,5 s  vẽ lần đầu (FCP)
 *     0,5–1,5 s  dàn trang + dựng chữ cho 1.900 nút (690 ms) rồi thêm 230 ms
 *     1,6 s  React hydrate
 *     2,2 s  `LegacyScripts` chèn 7 tệp JS cũ → LỜI GỌI API ĐẦU TIÊN
 *     2,7 s  thẻ "Học tiếp" hiện — và đó là phần tử LCP ở các lượt chậm
 *
 * Hai giây đầu mạng NGỒI KHÔNG trong khi luồng chính bận. Tệp này lấp đúng
 * khoảng ấy: một script nội tuyến, chạy lúc trình duyệt vừa đọc tới nó, bắn
 * sẵn những lượt GET mà trang chắc chắn cần, rồi cất *lời hứa* vào
 * `window.__napTruoc`. Khi tầng cũ chạy tới nơi, dữ liệu đã về hoặc đang trên
 * đường — không phải bắt đầu từ đầu.
 *
 * ── VÌ SAO KHÔNG ĐƠN GIẢN LÀ CHO TẦNG CŨ CHẠY SỚM HƠN ─────────────────────
 *
 * Vì tầng cũ SỬA DOM ngay khi chạy (`mountIcons` đổ SVG vào mọi `[data-icon]`,
 * `main.js` điền tên người dùng), mà những nút ấy do React dựng. Chạy trước
 * lúc hydrate là đưa cho React một cái cây khác với cái nó mong đợi. Nạp
 * trước DỮ LIỆU thì không đụng một nút nào — không có gì để lệch.
 *
 * ── QUY TẮC ĐẶT URL VÀO ĐÂY ───────────────────────────────────────────────
 *
 * CHỈ những lượt GET mà trang LUÔN gọi, không phụ thuộc người dùng bấm gì.
 * Thêm một URL "để phòng" là bắt máy chủ làm việc thừa cho mọi lượt mở, và
 * làm chậm đúng những lượt gọi thật đang xếp hàng sau nó.
 *
 * Bên đọc: `window.__apiGet` (main.js) tự tìm trong `__napTruoc` trước khi
 * fetch, nên mọi nơi gọi qua nó đều hưởng mà không phải sửa gì. `LopCuaToi`
 * (React) đọc thẳng vì nó không đi qua tầng cũ.
 */
export const NAP_TRUOC = [
  // `/api/user` KHÔNG có ở đây: chỉ `loadUser` đọc nó, mà đường ấy phải giữ
  // `handleFetch` để 401 đá về `/login` — nạp trước là mất chỗ duy nhất biết
  // phiên đã hết hạn.
  // (14/09/2026, cuối ngày) DANH SÁCH NÀY RỖNG — và tệp vẫn ở lại có chủ ý.
  // Ba lượt từng nằm đây đều đã chuyển sang MÁY CHỦ: `HocTiep` gọi
  // `hsa/summary` + `courses-enrolled` rồi ĐƯA XUỐNG cùng ổ khoá
  // `window.__napTruoc` bằng một script chảy cùng khối (xem `DuaXuong` ở đó);
  // `LopCuaToiNguon` gọi `lop-cua-toi` và không tầng cũ nào cần nó. Nạp trước
  // ở trình duyệt nữa là gọi thừa. Giữ khung ở đây để lượt GET tiếp theo mà
  // trang luôn cần (nếu có) có chỗ đặt — kèm luật ở trên.
] as const;

export default function NapTruocDuLieu({ urls = NAP_TRUOC }: { urls?: readonly string[] }) {
  return (
    <script
      // Chạy ngay tại chỗ, KHÔNG chờ hydrate — đó là toàn bộ mục đích.
      dangerouslySetInnerHTML={{
        __html:
          `(function(){var u=${JSON.stringify(urls)};window.__napTruoc={};` +
          // `catch` trả null chứ không để lời hứa vỡ: một lời hứa bị từ chối mà
          // chưa ai `await` sẽ nổ "unhandled rejection" ra console — và bên đọc
          // thì mãi sau mới tới.
          `for(var i=0;i<u.length;i++){(function(x){window.__napTruoc[x]=` +
          `fetch(x,{credentials:'same-origin'}).then(function(r){return r.ok?r.json():null})` +
          `.catch(function(){return null})})(u[i])}})();`,
      }}
    />
  );
}
