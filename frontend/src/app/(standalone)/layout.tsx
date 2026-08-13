// Nhóm (standalone): các template gốc KHÔNG extends base.html — không có CSS
// chung nào ở đây; từng page tự import đúng tổ hợp CSS của nó (MIGRATION_PLAN §4).
export default function StandaloneLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
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
