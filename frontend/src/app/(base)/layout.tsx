// Layout nhóm (base) ← port <head> + theme script của base.html.
// CSS: theme.css?v=3, auth.css, chatbot.css — ĐÚNG 3 file, đúng thứ tự (base.html:8-11).
// Nav/topbar KHÔNG nằm ở đây vì landing override block nav — trang nào dùng
// topbar thì render <Topbar /> (dashboard), trang nào override thì tự render.
import PageStyles from '@/components/PageStyles';

export default function BaseLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <PageStyles hrefs={["/static/css/theme.css","/static/css/auth.css","/static/css/chatbot.css"]} />
      {/* Fonts + Font Awesome như base.html */}
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
      <link
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
        rel="stylesheet"
      />
      <link
        rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
      />
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
