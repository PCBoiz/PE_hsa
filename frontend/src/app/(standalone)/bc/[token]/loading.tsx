/**
 * KHUNG CHỜ của trang phụ huynh — thứ duy nhất phụ huynh thấy trong lúc máy chủ
 * thức dậy.
 *
 * ── VÌ SAO PHẢI CÓ (17/09/2026) ──────────────────────────────────────────────
 *
 * `page.tsx` là Server Component: nó gọi Django rồi mới dựng HTML, nên tới khi
 * Django trả lời thì điện thoại phụ huynh KHÔNG nhận được byte nào — tab trắng.
 * Máy chủ chạy gói miễn phí, ngủ sau ~15 phút vắng người; lượt gọi đánh thức đo
 * 17/09 mất **76,3 giây**. Đo 14/09 trên production: Vercel giữ hàm sống qua
 * 71 giây ấy và trang VẪN ra — nhưng phụ huynh nhìn màn hình trắng hơn một
 * phút, từ một tin nhắn Zalo, không có tài khoản, không biết chờ gì. Phần lớn
 * sẽ đóng tab và nhắn lại giảng viên "link hỏng".
 *
 * Màn đăng nhập đã được vá bằng cách tự đánh thức máy chủ và nói ra đang chờ gì
 * (`LoginForm.tsx`). Trang này KHÔNG làm thế được: nó không có JavaScript nào
 * chạy trước khi HTML về. Cách duy nhất là để Next gửi TRƯỚC một khung — tệp
 * `loading.tsx` chính là cơ chế ấy: Next bọc `page.tsx` trong `Suspense`, gửi
 * khung này ngay (hàng chục mili-giây), rồi CHẢY nội dung thật tới khi có.
 *
 * ── GIỮ ĐÚNG CẤU TRÚC, KHÔNG GIỮ CHỖ ƯỚC LƯỢNG ──────────────────────────────
 *
 * Cùng thanh trên, cùng khung `article`, cùng thứ tự khối và cùng lớp chữ với
 * tờ thật (`ToBaoCao.tsx`) — để lúc nội dung thật thay vào, trang không nhảy
 * (CLS) ở mọi khổ máy, thay vì đóng cứng một chiều cao bằng px. Không viết chữ
 * giả trong ô mờ: trình đọc màn hình bỏ qua khung (`aria-hidden`), và câu duy
 * nhất có nghĩa — "đang tải" — nằm trong `role="status"` để được đọc lên.
 *
 * Câu nói ra lý do chờ chỉ hiện sau vài giây (CSS `animation-delay`, không cần
 * JavaScript): mạng bình thường thì tờ về trước khi câu ấy kịp hiện, không
 * nhấp nháy; máy chủ ngủ thì câu ấy hiện đúng lúc người ta bắt đầu sốt ruột.
 */
function O({ rong, cao = '0.9em' }: { rong: string; cao?: string }) {
  return (
    <span
      className="block animate-pulse rounded bg-sunken"
      style={{ width: rong, height: cao }}
    />
  );
}

/** Một ô số như `Ô` trong ToBaoCao: nhãn nhỏ, số to, dòng phụ. */
function OSo() {
  return (
    <div className="rounded-md border border-line bg-surface px-4 py-3">
      <O rong="60%" cao="0.8em" />
      <p className="mt-1 text-title"><O rong="2.5em" cao="1em" /></p>
      <p className="mt-0.5 text-small"><O rong="80%" cao="0.8em" /></p>
    </div>
  );
}

export default function DangTaiBaoCao() {
  return (
    <div className="min-h-dvh bg-ground">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-3xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-4">
          <span className="flex-1 text-section text-ink">Báo cáo học tập</span>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-6">
        <p role="status" className="sr-only">Đang tải tờ báo cáo…</p>
        {/* ĐẶT TRÊN khung, không đặt dưới: soi ảnh 390px thấy câu này rơi xuống dưới
            mép màn hình — phụ huynh nhìn 60 giây ô xám mà không cuộn thì không bao
            giờ thấy nó. Hiện sau 6 giây, cùng ngưỡng với màn đăng nhập (`GIAY_NOI_DANG_THUC`).
            `motion-reduce:animate-none` + `motion-reduce:opacity-100`: ai tắt hiệu
            ứng thì thấy câu này ngay, còn hơn không bao giờ thấy. */}
        <p
          role="status"
          className="mb-4 animate-[hien_0.3s_ease-out_6s_both] rounded-md border border-line bg-sunken px-4 py-3 text-small text-ink-2 motion-reduce:animate-none"
        >
          Máy chủ đang thức dậy (gói miễn phí tạm dừng khi không ai dùng). Lần mở đầu
          trong ngày có thể mất khoảng một phút — cứ để trang này mở, tờ báo cáo sẽ
          tự hiện.
        </p>
        <article className="rounded-lg border border-line bg-surface p-6" aria-hidden="true">
          <h2 className="text-title"><O rong="min(14rem, 70%)" cao="1em" /></h2>
          <p className="mt-1 text-body"><O rong="min(20rem, 90%)" /></p>
          <p className="mt-2 text-body"><O rong="min(12rem, 55%)" /></p>
          <p className="mt-0.5 text-small"><O rong="min(16rem, 75%)" cao="0.8em" /></p>

          <h3 className="mt-6 text-subhead"><O rong="9rem" cao="1em" /></h3>
          <p className="mt-2 text-body"><O rong="min(22rem, 95%)" /></p>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <OSo /><OSo /><OSo /><OSo />
          </div>

          <h3 className="mt-6 text-subhead"><O rong="11rem" cao="1em" /></h3>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
            <OSo /><OSo /><OSo />
          </div>

          <h3 className="mt-6 text-subhead"><O rong="10rem" cao="1em" /></h3>
          <p className="mt-2 text-body"><O rong="min(24rem, 100%)" /></p>
          <p className="mt-1 text-body"><O rong="min(18rem, 80%)" /></p>
        </article>

      </main>

      {/* Khai keyframes tại chỗ, như `ui/Modal.tsx`: chỉ một nơi dùng, đừng đưa vào
          tệp CSS chung để rồi không ai biết nó phục vụ ai. `both` ở trên giữ
          `opacity: 0` suốt 6 giây chờ, nên không cần trạng thái ẩn riêng. */}
      <style>{`
        @keyframes hien {
          from { opacity: 0; transform: translateY(4px); }
          to   { opacity: 1; transform: none; }
        }
      `}</style>
    </div>
  );
}
