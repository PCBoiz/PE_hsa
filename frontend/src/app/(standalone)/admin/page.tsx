'use client';

// Port admin.html — trang quản trị (style + script inline gốc trích verbatim).
// Backend guard: mọi /api/admin/* yêu cầu role admin (403 nếu không) — giống
// @api_admin_required cũ; trang chỉ là shell gọi API.
import LegacyScripts from '@/components/LegacyScripts';
import PageStyles from '@/components/PageStyles';

/* eslint-disable @typescript-eslint/no-explicit-any */
const W = () => window as any;

export default function AdminPage() {
  return (
    <>
      <PageStyles hrefs={['/static/css/pages/admin.inline.css']} />
      <title>Quản trị | Programming EDU</title>

      <header>
        <h1>🛠️ Trang quản trị</h1>
        <a href="/dashboard">← Về dashboard</a>
      </header>

      <div className="wrap">
        {/* KHÓA HỌC */}
        <section>
          <h2>Khóa học</h2>
          <table>
            <thead><tr><th>Id</th><th>Tiêu đề</th><th>Bài</th><th></th></tr></thead>
            <tbody id="courseRows"></tbody>
          </table>

          <div className="form-box">
            <h3 id="courseFormTitle">Thêm khóa học</h3>
            <input id="cId" placeholder="id (vd: python)" />
            <input id="cTitle" placeholder="Tiêu đề" />
            <input id="cSubtitle" placeholder="Phụ đề" />
            <textarea id="cDescription" placeholder="Mô tả"></textarea>
            <div className="row">
              <input id="cLevel" placeholder="Cấp độ" />
              <input id="cDuration" placeholder="Thời lượng" />
            </div>
            <div className="row">
              <input id="cTag" placeholder="Tag" />
              <input id="cImage" placeholder="Đường dẫn ảnh" />
            </div>
            <div className="row">
              <input id="cColor" placeholder="color" />
              <input id="cAccentColor" placeholder="accent_color" />
            </div>
            <button className="btn-primary" onClick={() => W().saveCourse()}>Lưu</button>
            <button className="btn-ghost" onClick={() => W().resetCourseForm()}>Hủy</button>
          </div>
        </section>

        {/* BÀI GIẢNG */}
        <section>
          <h2 id="lessonTitle">Bài giảng</h2>
          <p className="hint" id="lessonHint">Chọn một khóa học để xem bài giảng.</p>
          <table>
            <thead><tr><th>#</th><th>Module</th><th>Tiêu đề</th><th></th></tr></thead>
            <tbody id="lessonRows"></tbody>
          </table>

          <div className="form-box" id="lessonFormBox" style={{ display: 'none' }}>
            <h3 id="lessonFormTitle">Thêm bài giảng</h3>
            <input id="lModule" placeholder="Module" />
            <input id="lLessonTitle" placeholder="Tiêu đề bài giảng" />
            <textarea id="lContent" placeholder="Nội dung"></textarea>
            <input id="lSort" type="number" placeholder="Thứ tự" defaultValue={0} />
            <button className="btn-primary" onClick={() => W().saveLesson()}>Lưu</button>
            <button className="btn-ghost" onClick={() => W().resetLessonForm()}>Hủy</button>
          </div>
        </section>
      </div>

      <div id="toast"></div>

      <LegacyScripts srcs={['/static/js/pages/admin.inline.js']} />
    </>
  );
}
