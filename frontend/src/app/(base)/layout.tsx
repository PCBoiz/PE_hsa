// Layout nhóm (base) ← port <head> + theme script của base.html.
// CSS: theme.css?v=3, auth.css, chatbot.css — ĐÚNG 3 file, đúng thứ tự (base.html:8-11).
// Nav/topbar KHÔNG nằm ở đây vì landing override block nav — trang nào dùng
// topbar thì render <Topbar /> (dashboard), trang nào override thì tự render.
import PageStyles from '@/components/PageStyles';

export default function BaseLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {/* auth.css ĐÃ RỜI KHỎI ĐÂY (27/08/2026). Nó là CSS của TRANG CHỦ tối, nhưng
          lớp `.section-card` của nó trùng tên với thẻ nội dung của dashboard.css và
          có độ đặc hiệu cao hơn — luật `.section-card p { color: rgba(226,232,255,.74) }`
          đè chữ trắng-xanh lên thẻ TRẮNG, đo được tương phản 1.16:1. Câu bị nuốt
          nặng nhất là "Bạn chưa đặt mục tiêu tuần." — đúng thông điệp cần đọc nhất.
          Trên /dashboard file này còn dùng có 2%, tức 29 kB gần như phí sạch.
          Nay chỉ trang chủ nạp nó. theme.css nạp ở tầng gốc (app/layout.tsx). */}
      <PageStyles hrefs={["/static/css/chatbot.css","/static/css/a11y.css"]} />
      {/* Font Awesome ĐÃ GỠ khỏi tầng này (07/09/2026).
          Đo: 100 kB CSS tải từ CDN cho nhóm `(base)` — tức TRANG CHỦ và TRANG
          CỦA TÔI, hai màn có nhiều người mở nhất. Grep cả hai màn: **0 lần**
          dùng class `fa-`. Một trăm kilobyte cho không icon nào.

          Font Awesome vẫn còn ở ba chỗ THẬT SỰ dùng nó (`LessonHsa.tsx`,
          `lesson_hsa.js`, `MockExam.tsx`) và chúng tự nạp lấy.

          Ghi rõ để không ai "khôi phục cho chắc": nếu thêm một icon `fa-` vào
          nhóm này thì nó sẽ KHÔNG hiện, và cách đúng là dùng `BieuTuong`
          (bộ SVG riêng, sinh từ `icons.js`) chứ không phải nạp lại 100 kB. */}
      {/* Chống FOUC theme — chạy trước khi vẽ nội dung.
          Quy tắc (audit 2026-08-13): người dùng đã chọn tay thì theo lựa chọn đó;
          CHƯA chọn thì theo hệ điều hành (trước đây mặc định cứng là tối, và
          course_detail.js lại mặc định sáng → hai trang lệch theme nhau). */}
      <script
        dangerouslySetInnerHTML={{
          __html: `(function(){var t=null;try{t=localStorage.getItem('theme')}catch(e){}
var d=t?t==='dark':(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches);
document.body.classList.toggle('dark',!!d);document.body.classList.toggle('light',!d)})();`,
        }}
      />
      {children}
    </>
  );
}
