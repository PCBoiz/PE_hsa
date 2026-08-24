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
      <PageStyles hrefs={['/static/css/pages/admin.inline.css','/static/css/a11y.css']} />
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

        {/* LỚP HỌC — bước đầu thành ERP: có lớp thì khu Giảng dạy mới có gì
            để hiện, và giảng viên mới có phạm vi để phân quyền theo. */}
        <section>
          <h2>Lớp học</h2>
          <table>
            <thead><tr><th>Mã</th><th>Tên lớp</th><th>Giảng viên</th><th>Lịch</th><th>Sĩ số</th><th>Trạng thái</th><th></th></tr></thead>
            <tbody id="classRows"></tbody>
          </table>

          <div className="form-box">
            <h3 id="classFormTitle">Thêm lớp</h3>
            <div className="row">
              <input id="klCode" placeholder="Mã lớp (vd: HSA-QL-01)" />
              <input id="klName" placeholder="Tên lớp" />
            </div>
            <div className="row">
              <input id="klCourse" placeholder="Khoá (hsa_quantitative / hsa_verbal / hsa_science — để trống = cả ba)" />
              <select id="klTeacher" aria-label="Giảng viên phụ trách"></select>
            </div>
            <div className="row">
              <input id="klSchedule" placeholder="Lịch học (vd: Thứ 3, 5 · 19:30–21:00)" />
              <input id="klUrl" placeholder="Link phòng học online" />
            </div>
            <div className="row">
              <input id="klStart" placeholder="Khai giảng (YYYY-MM-DD)" />
              <input id="klExam" placeholder="Kỳ thi nhắm tới (YYYY-MM-DD)" />
            </div>
            <div className="row">
              <input id="klCap" placeholder="Sĩ số tối đa" />
              <select id="klStatus" aria-label="Trạng thái lớp"></select>
            </div>
            <textarea id="klNote" placeholder="Ghi chú"></textarea>
            <button className="btn-primary" onClick={() => W().saveClass()}>Lưu lớp</button>
            <button className="btn-ghost" onClick={() => W().resetClassForm()}>Hủy</button>
          </div>
        </section>

        {/* HỌC VIÊN TRONG LỚP */}
        <section id="memberSection" style={{ display: 'none' }}>
          <h2 id="memberTitle">Học viên trong lớp</h2>
          <p className="hint">
            Cho rời lớp KHÔNG xoá dữ liệu học tập — học viên nghỉ giữa chừng vẫn còn trong báo cáo của kỳ đó.
          </p>
          <table>
            <thead><tr><th>Tên</th><th>Email</th><th>Bài đã xong</th><th>Trạng thái</th><th></th></tr></thead>
            <tbody id="memberRows"></tbody>
          </table>
          <div className="form-box">
            <h3>Thêm học viên vào lớp</h3>
            <input id="mbEmail" placeholder="Email tài khoản học viên" />
            <button className="btn-primary" onClick={() => W().addMember()}>Thêm vào lớp</button>
          </div>
        </section>

        {/* TÀI KHOẢN & VAI TRÒ */}
        <section>
          <h2>Tài khoản &amp; vai trò</h2>
          <p className="hint">
            Gán vai trò <b>Giảng viên</b> cho tài khoản trước, rồi mới chọn được người đó làm giảng viên phụ trách lớp.
          </p>
          <div className="row">
            <input id="usQ" placeholder="Tìm theo tên hoặc email" />
            <button className="btn-ghost" onClick={() => W().searchUsers()}>Tìm</button>
          </div>
          <table>
            <thead><tr><th>Id</th><th>Tên</th><th>Email</th><th>Vai trò</th></tr></thead>
            <tbody id="userRows"></tbody>
          </table>
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

      {/* ══════════════════════════════════════════════════════════════════
          SOẠN NỘI DUNG BÀI HỌC (2026-08-14)
          Trước đây trang này chỉ ghi được cột `content` (TEXT) mà engine
          không đọc, nên bài tạo ở đây học viên KHÔNG BAO GIỜ thấy. Khối này
          soạn thẳng vào lessons.content_json — đúng thứ engine phục vụ.
          ══════════════════════════════════════════════════════════════════ */}
      <div className="wrap wrap--full">
        <section id="contentSection">
          <div className="sec-head">
            <h2 id="contentTitle">Nội dung bài học</h2>
            <div id="contentActions" style={{ display: 'none' }}>
              <a className="btn-ghost btn-link" id="btnPreview" target="_blank" rel="noreferrer">Xem thử ↗</a>
              <button className="btn-danger" onClick={() => W().clearLessonContent()}>Xoá nội dung</button>
              <button className="btn-primary" onClick={() => W().saveLessonContent()}>Lưu nội dung</button>
            </div>
          </div>
          <p className="hint" id="contentHint">
            Chọn một khoá học rồi bấm <b>Soạn</b> ở dòng bài giảng để bắt đầu.
            Bài chưa soạn ở đây vẫn dùng nội dung mặc định trong mã nguồn.
          </p>

          <div id="contentErrors" className="err-box" style={{ display: 'none' }}></div>

          <div id="contentForm" style={{ display: 'none' }}>
            {/* ── Thông tin bài ── */}
            <fieldset>
              <legend>Thông tin bài</legend>
              <div className="row">
                <label>Mã bài<input id="fId" placeholder="ql_01" /></label>
                <label>Số thứ tự<input id="fIndex" type="number" min={1} placeholder="1" /></label>
              </div>
              <label>Tiêu đề<input id="fTitle" placeholder="Tỉ lệ &amp; phần trăm" /></label>
              <label>Phụ đề<input id="fSubtitle" placeholder="Tăng – giảm phần trăm và bài toán thực tế" /></label>
              <div className="row">
                <label>Thẻ chủ đề<input id="fTopic" placeholder="Định lượng · Số học" /></label>
                <label>XP thưởng<input id="fXp" type="number" min={0} max={500} placeholder="50" /></label>
              </div>
            </fieldset>

            {/* ── Bước 1 ── */}
            <fieldset>
              <legend>Bước 1 — Kiểm tra đầu vào</legend>
              <label>Lời dẫn<textarea id="fTestIntro" placeholder="Làm nhanh 3 câu để hệ thống định vị năng lực của bạn."></textarea></label>
              <div id="testQs" className="repeat"></div>
              <button className="btn-ghost" onClick={() => W().addQuestion('testQs')}>+ Thêm câu hỏi</button>
              <div className="row" style={{ marginTop: 10 }}>
                <label>Đúng ≥ mấy câu thì &quot;vững&quot;?<input id="fStrongMin" type="number" min={0} placeholder="3" /></label>
                <label>Đúng ≥ mấy câu thì &quot;ổn&quot;?<input id="fOkMin" type="number" min={0} placeholder="2" /></label>
              </div>
              <p className="hint">
                Đạt mốc &quot;vững&quot; → học viên nhận <b>bản tóm tắt</b>. Dưới mốc → nhận <b>bản đầy đủ</b>.
              </p>
            </fieldset>

            {/* ── Bước 3 ── */}
            <fieldset>
              <legend>Bước 3 — Lý thuyết</legend>
              <div className="tabs">
                <button className="tab is-on" data-variant="full" onClick={(e) => W().switchVariant(e.currentTarget, 'full')}>Bản đầy đủ</button>
                <button className="tab" data-variant="condensed" onClick={(e) => W().switchVariant(e.currentTarget, 'condensed')}>Bản tóm tắt</button>
              </div>
              <p className="hint">
                Minh hoạ đặt ở hai bản là <b>hai bản riêng</b> — chỉ đặt ở bản đầy đủ thì học viên giỏi
                sẽ không bao giờ nhìn thấy đồ thị.
              </p>
              <div className="variant-pane" data-pane="full">
                <label>Tiêu đề phần lý thuyết<input id="fFullTitle" placeholder="Lý thuyết đầy đủ — cùng ôn kỹ…" /></label>
                <div id="fullCards" className="repeat"></div>
                <button className="btn-ghost" onClick={() => W().addCard('fullCards')}>+ Thêm thẻ lý thuyết</button>
              </div>
              <div className="variant-pane" data-pane="condensed" style={{ display: 'none' }}>
                <label>Tiêu đề phần lý thuyết<input id="fCondTitle" placeholder="Tóm tắt nhanh — bạn đã khá vững" /></label>
                <div id="condCards" className="repeat"></div>
                <button className="btn-ghost" onClick={() => W().addCard('condCards')}>+ Thêm thẻ lý thuyết</button>
              </div>
            </fieldset>

            {/* ── Bước 4 ── */}
            <fieldset>
              <legend>Bước 4 — Ghi chú</legend>
              <label>Tiêu đề<input id="fNoteTitle" placeholder="Ghi nhớ" /></label>
              <label>Các ý — <span className="hint-inline">mỗi dòng một ý</span>
                <textarea id="fNotePoints" placeholder="Giảm 25% nghĩa là còn 75%&#10;Nhân thẳng hệ số, đừng tính hai bước"></textarea>
              </label>
            </fieldset>

            {/* ── Bước 5 ── */}
            <fieldset>
              <legend>Bước 5 — Luyện tốc độ</legend>
              <div className="row">
                <label>Lời dẫn<input id="fDrillIntro" placeholder="Trả lời càng nhanh càng nhiều điểm." /></label>
                <label>Thời gian (giây)<input id="fDrillSeconds" type="number" min={10} placeholder="60" /></label>
              </div>
              <div id="drillQs" className="repeat"></div>
              <button className="btn-ghost" onClick={() => W().addQuestion('drillQs')}>+ Thêm câu luyện</button>
            </fieldset>
          </div>
        </section>

        {/* ── Nhập cả khoá ── */}
        <section id="importSection">
          <h2>Nhập cả khoá từ file JSON</h2>
          <p className="hint">
            Đây là đường nhận giáo trình đối tác bàn giao. Hệ thống <b>kiểm toàn bộ trước khi ghi</b> —
            sai một bài thì không bài nào được ghi. Cấu trúc file: xem <code>docs/NHAP_GIAO_TRINH.md</code>.
          </p>
          <p className="hint" id="importCourse">Chọn một khoá học ở trên trước.</p>
          <input type="file" id="importFile" accept=".json,application/json" />
          <textarea id="importText" placeholder='{"lessons": [ … ], "total_lessons": 27}'></textarea>
          <div className="row">
            <label>Tổng số bài của khoá — <span className="hint-inline">bỏ trống nếu chưa bàn giao trọn</span>
              <input id="importTotal" type="number" min={1} placeholder="27" />
            </label>
            <div style={{ alignSelf: 'end' }}>
              <button className="btn-primary" onClick={() => W().importCourse()}>Nhập vào khoá</button>
            </div>
          </div>
          <div id="importResult" className="err-box" style={{ display: 'none' }}></div>
        </section>
      </div>

      <div id="toast"></div>

      <LegacyScripts srcs={['/static/js/pages/admin.inline.js']} />
    </>
  );
}
