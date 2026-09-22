// Nhóm (standalone): các template gốc KHÔNG extends base.html — từng page tự
// import đúng tổ hợp CSS của nó (MIGRATION_PLAN §4). NGOẠI LỆ DUY NHẤT là
// `a11y.css`: nó không phải bộ mặt của một trang mà là SÀN kích thước, và đầu
// tệp ấy tự nhận là "nạp trên MỌI trang".
//
// Câu ấy sai cho tới 22/09/2026. Đo 31 trang × 2 khổ: logo `a.brand` chỉ cao
// 20px (ngưỡng 44) trên ĐÚNG 16 trang, và cả 16 đều thuộc nhóm này — Quản trị,
// Giảng dạy, Soạn giáo trình, Bài tập của tôi. Mười trang tầng SPA cũ, vốn có
// nạp tệp sàn, đo ra 44px. Vết nứt nằm đúng ranh giới hai tầng frontend.
// Nạp ở layout nên nó đứng TRƯỚC CSS của từng trang — đúng thứ tự mà các luật
// `!important` trong tệp ấy trông đợi.
import PageStyles from '@/components/PageStyles';

export default function StandaloneLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <PageStyles hrefs={['/static/css/a11y.css']} />
      {/* Khởi tạo theme giống nhóm (base) — trước đây nhóm này KHÔNG set theme
          nên bài học/thi thử luôn rơi về mặc định của CSS, lệch với dashboard.
          Chọn tay thắng; chưa chọn thì theo hệ điều hành. Chạy trước nội dung
          để không nháy màu (FOUC). */}
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
