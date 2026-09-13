/**
 * KHUNG CHỜ của khối "Lớp của bạn" — giữ đúng CHỖ, không giữ chỗ ước lượng.
 *
 * ── VÌ SAO PHẢI CÓ (đo 14/09/2026) ────────────────────────────────────────
 *
 * Khối thật cao 333px ở khổ máy tính và 465px ở khổ điện thoại, và nó nằm TRÊN
 * thẻ "Học tiếp". Tới muộn là đẩy cả cột xuống: khi khối tự gọi API ở trình
 * duyệt, CLS đo được **0,177** — quá ngưỡng 0,1.
 *
 * Chờ nó ở máy chủ thì hết nhảy, nhưng trang không gửi được byte nào cho tới
 * khi `/api/lop-cua-toi` trả lời (1,45 s trên máy này): LCP vọt lên **4,59 s**.
 * Nên: vẫn chảy theo `Suspense`, và chỗ trống được giữ bằng một khung có CÙNG
 * cấu trúc thẻ — cùng class, cùng số dòng — để chiều cao tự khớp ở MỌI khổ
 * máy thay vì đóng cứng một con số (RULES: không hardcode px).
 *
 * `aria-hidden` + `.skel`: trình đọc màn hình bỏ qua, mắt thấy một thẻ đang
 * tải. Không viết chữ giả — chữ giả bị đọc lên là nói dối người khiếm thị.
 */
function Dong({ rong }: { rong: string }) {
  return <span className="skel" style={{ display: 'block', width: rong, height: '0.9em', borderRadius: '0.25rem' }} />;
}

export default function LopCuaToiKhung() {
  return (
    <section className="section-card lct" aria-hidden="true">
      <div className="section-title" style={{ marginBottom: 6 }}>
        <Dong rong="min(14rem, 60%)" />
      </div>
      <p className="lct-meta"><Dong rong="min(20rem, 85%)" /></p>

      <div className="lct-next">
        <div className="lct-next-text">
          <span className="lct-next-lbl"><Dong rong="4.5rem" /></span>
          <b className="lct-next-time"><Dong rong="8rem" /></b>
          <span className="lct-next-sub"><Dong rong="min(16rem, 70%)" /></span>
        </div>
        <span className="hsa-cont-btn lct-go skel" style={{ color: 'transparent' }}>Vào phòng học →</span>
      </div>

      <p className="lct-more"><Dong rong="min(22rem, 90%)" /></p>
      <p className="lct-cc"><Dong rong="min(18rem, 75%)" /></p>
    </section>
  );
}
