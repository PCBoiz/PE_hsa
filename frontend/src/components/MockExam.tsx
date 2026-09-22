'use client';

// Trụ cột ④ — Thi thử CBT (ProgrammingEdu × TopHSA). React thuần + apiFetch.
// list → làm bài (bấm giờ, palette câu, MCQ/điền) → kết quả + phân tích hợp phần.
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ghiNhomVai } from '@/lib/nhomVai';
import { taiTrang } from '@/lib/dieuHuong';
import { useCallback, useEffect, useRef, useState } from 'react';
import AppShell from '@/components/AppShell';

import Chatbot from '@/components/Chatbot';
import PageStyles from '@/components/PageStyles';
import { apiFetch, errorText, ghiJson, loiBatDuoc } from '@/lib/api';
// `zod/mini` chứ KHÔNG `zod` (14/09/2026 tối): đây là mã chạy ở TRÌNH DUYỆT.
// Bản đầy đủ không rung cây được — đo A/B trên Thi thử: 956 kB (zod) → 608 kB
// (zod/mini), byte giải nén, ba lượt mỗi bên. Bản mini cùng luật
// `looseObject`/`safeParse`, viết dạng hàm (`z.optional(z.string())` thay vì
// `.optional()`). Mã máy chủ vẫn dùng `zod` đầy đủ — gói máy chủ không ai tải.
import * as z from 'zod/mini';

const fmt = (s: number) =>
  `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(Math.max(0, s % 60)).padStart(2, '0')}`;

const SECTION_COLOR: Record<string, string> = {
  'Định lượng': '#8B7CF6', 'Định tính': '#F472B6', 'Khoa học': '#2DD4BF',
};

/* Hình dạng TỜ KẾT QUẢ đề thi thử — `mockexam/views.py`. `looseObject` nên máy
   chủ thêm khoá thì không sao; thiếu khoá màn hình đang vẽ mới là lỗi. */
const HD_KET_QUA = z.looseObject({
  score: z.number(),
  total: z.number(),
  section_scores: z.record(z.string(), z.looseObject({ correct: z.number(), total: z.number() })),
  weakest: z.nullable(z.string()),
  results: z.array(z.looseObject({})),
  durationSeconds: z.number(),
  counted: z.boolean(),
  notCountedReason: z.nullable(z.string()),
  xpGained: z.number(),
});

export default function MockExam() {
  const [view, setView] = useState<'loading' | 'list' | 'take' | 'result'>('loading');
  const [exams, setExams] = useState<any[]>([]);
  const [exam, setExam] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [cur, setCur] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [loi, setLoi] = useState<string>('');
  /* Tên cho chip người dùng ở thanh trên. Trang này trước đây không có chip
     nên cũng không cần tên; nay có thì phải lấy thật — một chip hiện "—" là
     một điều khiển nửa chết, và người dùng không biết mình đang đăng nhập bằng
     tài khoản nào. */
  const [ten, setTen] = useState<string | undefined>(undefined);
  const startRef = useRef(0);
  /* ĐANG CHẤM (21/09/2026). Bản cũ `setView('loading')` lúc nộp: cả trang chỉ
     còn vòng xoay + "Đang tải…" ~2,5 s (đo 2.590 ms ở 1024, 2.605 ở 768) — mất
     cả đề lẫn bảng câu hỏi, đúng lúc em vừa bấm một nút không hoàn tác được.
     Nay giữ nguyên khung đề, phủ một lớp mờ nói rõ "đang chấm". `useRef` để
     đồng hồ hết giờ trong lúc chấm không gọi `submit` lần hai. */
  const [dangNop, setDangNop] = useState(false);
  const dangNopRef = useRef(false);
  // Mốc hết giờ (ms từ epoch). Đặt cùng lúc với `startRef` khi mở đề.
  const hanRef = useRef(0);
  const answersRef = useRef<Record<string, string>>({});
  // Gán trong effect, KHÔNG gán thẳng lúc dựng: sửa ref giữa lúc dựng khiến
  // React không đảm bảo component vẽ lại đúng lúc, và với Strict Mode / dựng
  // lại lần hai thì giá trị ref có thể lệch với thứ đang hiện trên màn hình.
  useEffect(() => {
    answersRef.current = answers;
  }, [answers]);

  useEffect(() => {
    // `void`: khối dưới bắt hết mọi lỗi ở chính nó nên lời hứa này không thể
    // hỏng — `void` nói rõ điều đó thay vì để người đọc tự đoán.
    void (async () => {
      try {
        const r = await apiFetch('/api/mock-exams');
        if (r.status === 401) { taiTrang('/login'); return; }
        const d = await r.json();
        setExams(d.exams || []); setView('list');
      } catch { setExams([]); setView('list'); }
      /* Tên người dùng — lời gọi RIÊNG, cố tình đặt SAU. Danh sách đề là thứ
         người ta vào đây để xem; tên chỉ để hiện trên chip. Gộp vào cùng một
         `Promise.all` là để một lỗi mạng ở chỗ phụ giữ chỗ chính lại. */
      try {
        const u = await apiFetch('/api/user');
        if (u.ok) { const d = await u.json(); if (d?.name) setTen(d.name); ghiNhomVai(d?.role); }
      } catch { /* không có tên thì chip hiện dấu gạch — không chặn việc thi */ }
    })();
  }, []);

  const submit = useCallback(async () => {
    if (!exam || dangNopRef.current) return;
    const dur = Math.round((Date.now() - startRef.current) / 1000);
    dangNopRef.current = true; setDangNop(true);
    try {
      /* Hình dạng (T18 mức 2, chiều GHI — 14/09/2026): CẢ TỜ KẾT QUẢ của em
         đọc từ phản hồi này. Máy chủ đổi tên `section_scores` hay `results` thì
         màn hình hiện "0/0", bảng theo hợp phần trống và danh sách câu biến
         mất — mà em không có cách nào biết đó là lỗi mã chứ không phải điểm
         của mình. Nay lệch là một câu lỗi nói thẳng. */
      const d = await ghiJson(`/api/mock-exams/${exam.id}/submit`, {
        method: 'POST',
        body: JSON.stringify({ answers: answersRef.current, duration_seconds: dur }),
      }, HD_KET_QUA);
      setResult(d); setView('result');
    } catch (e) {
      setLoi(loiBatDuoc(e, 'Không nộp được bài — thử nộp lại sau giây lát.'));
    } finally {
      dangNopRef.current = false; setDangNop(false);
    }
  }, [exam]);

  /* Đồng hồ tính từ MỐC HẾT GIỜ, không trừ dần từng giây.
     Hai lỗi của bản trừ-dần, và cái thứ hai mới là cái hại người học:

     ① `submit()` gọi NGAY TRONG `setTimeLeft(t => …)`. Hàm cập nhật state phải
        THUẦN — React có quyền gọi nó hai lần (Strict Mode, hoặc render bị bỏ dở
        rồi chạy lại) — nên "nộp bài", một lời gọi mạng đổi dữ liệu, có thể bắn
        hai lần. Máy chủ có chặn (`submitted_at IS NULL`) nên chưa ai mất bài,
        nhưng hàng rào ấy nằm ở đầu kia chứ không phải ở đây.

     ② Trình duyệt HÃM `setInterval` xuống còn khoảng 1 lần/phút khi tab chạy
        nền. Đồng hồ trừ dần vì thế chạy CHẬM: em chuyển sang tab khác tra cứu
        rồi quay lại, màn hình vẫn báo còn nhiều thời gian hơn sự thật. Điểm thì
        không sai (máy chủ giữ `started_at`), nhưng con số trên màn hình nói dối
        đúng lúc người ta cần tin nó nhất. Tính từ mốc thì tab nền hay không
        cũng ra cùng một số. */
  useEffect(() => {
    if (view !== 'take') return;
    const dem = () => {
      const con = Math.max(0, Math.round((hanRef.current - Date.now()) / 1000));
      setTimeLeft(con);
      if (con <= 0) { clearInterval(id); void submit(); }
    };
    const id = setInterval(dem, 1000);
    // Chạy ngay một nhịp: quay lại tab sau 5 phút thì không phải chờ thêm 1 giây
    // mới thấy con số đúng.
    const khiHien = () => { if (!document.hidden) dem(); };
    document.addEventListener('visibilitychange', khiHien);
    return () => { clearInterval(id); document.removeEventListener('visibilitychange', khiHien); };
  }, [view, submit]);

  // useCallback như `submit` ở trên: `Date.now()` là hàm không thuần, và một
  // hàm khai trần trong thân component thì bộ kiểm không chứng minh được là nó
  // chỉ chạy từ trình xử lý sự kiện. Ở đây `start` chỉ được gọi từ onClick.
  const start = useCallback(async (id: number) => {
    setView('loading'); setLoi('');
    // POST /start chứ không phải GET đề: đường này mở `started_at` Ở MÁY CHỦ.
    // Số giây còn lại cũng do máy chủ trả — tải lại trang giữa chừng thì nối
    // tiếp đúng phần thời gian còn lại, không được cấp lại 20 phút.
    let r: Response;
    try {
      r = await apiFetch(`/api/mock-exams/${id}/start`, { method: 'POST' });
    } catch {
      // `apiFetch` ném khi không gửi đi được (mất mạng, DNS, CORS). Không bắt
      // thì promise reject và trang KẸT ở "Đang tải…" cho tới khi người dùng
      // tự tải lại — vì dòng trên đã setView('loading') rồi.
      setLoi('Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.');
      setView('list'); return;
    }
    let d: any = null;
    try { d = await r.json(); } catch { d = null; }
    if (!r.ok) {
      // Nói ra chứ không quay về danh sách im lặng: người dùng bấm "Bắt đầu",
      // màn hình chớp một cái rồi y như cũ, không một chữ giải thích.
      setLoi(errorText(r.status, d)); setView('list'); return;
    }
    if (!d || !Array.isArray(d.questions) || d.questions.length === 0) {
      setLoi('Đề này chưa có câu hỏi nào.'); setView('list'); return;
    }
    // Câu trả lời đã lưu của lượt đang mở: lỡ F5 ở phút thứ 15 thì đồng hồ nối
    // tiếp mà bài làm cũng phải còn.
    setExam(d);
    setAnswers(d.savedAnswers && typeof d.savedAnswers === 'object' ? d.savedAnswers : {});
    setCur(0);
    const con = typeof d.secondsLeft === 'number' ? d.secondsLeft
                                                 : (d.duration_minutes || 20) * 60;
    setTimeLeft(con);
    startRef.current = Date.now();
    hanRef.current = startRef.current + con * 1000;
    setView('take');
  }, []);

  // Lưu tạm câu trả lời lên máy chủ, gộp nhịp 1,5 giây. Không có nó thì mất
  // mạng hay đóng tab là mất trắng bài làm, và lượt bỏ dở tới lúc cạn giờ
  // không còn gì để chấm.
  useEffect(() => {
    if (view !== 'take' || !exam) return;
    const id = setTimeout(() => {
      apiFetch(`/api/mock-exams/${exam.id}/save`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: answersRef.current }),
      }).catch(() => { /* lưu tạm hỏng thì thôi — nộp bài vẫn gửi đủ */ });
    }, 1500);
    return () => clearTimeout(id);
  }, [answers, view, exam]);
  const setAns = (qid: string, val: string) => setAnswers((a) => ({ ...a, [qid]: val }));
  const answeredCount = () => Object.keys(answers).filter((k) => answers[k] != null && answers[k] !== '').length;
  const confirmSubmit = () => {
    if (window.confirm(`Nộp bài? Bạn đã trả lời ${answeredCount()}/${exam.questions.length} câu.`)) void submit();
  };

  // ─────────── views ───────────
  return (
    <>
      <PageStyles hrefs={['/static/css/theme.css', '/static/css/shell.css', '/static/css/mock.css', '/static/css/chatbot.css', '/static/css/a11y.css']} />
      <title>Thi thử CBT — ProgrammingEdu × TopHSA</title>
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />

      <div className="mk-wrap">
        {/* KHUNG CHUNG — cùng component với dashboard và màn chi tiết khoá.
            Bản cũ ở đây là BẢN DỰNG THỨ BA (`.mk-topbar`, chữ trần, không biểu
            tượng) và nó THIẾU chip người dùng: grep `user-chip|logout` trong
            tệp này ra 0. Nghĩa là vào Thi thử là học viên mất luôn đường Đăng
            xuất và nút đổi sáng/tối — không phải chuyện thẩm mỹ.

            `dieuKhien="react"`: trang này không nạp main.js lẫn dashboard.js,
            nên menu người dùng do chính AppShell giữ (kể cả bấm-ra-ngoài và
            phím Escape). Chuông thì KHÔNG dựng — không có nguồn dữ liệu ở đây,
            và một cái nút không ai nghe còn tệ hơn một cái nút vắng mặt.

            Lúc ĐANG làm bài thì tước xuống chế độ `lam-bai`: bỏ hết điều hướng
            để không ai bấm nhầm mà mất bài, và ĐỒNG HỒ chuyển lên thanh cố
            định. Trước đây đồng hồ nằm trong thân trang nên cuộn xuống là mất
            — đúng lúc thí sinh cần nhìn nó nhất. */}
        {view === 'take' && exam ? (
          <AppShell
            cheDo="lam-bai"
            nhan={exam.counts === false ? 'Lượt luyện · không tính điểm' : 'Đang làm bài'}
            phai={
              <>
                <div className={'mk-timer' + (timeLeft <= 60 ? ' low' : '')}>
                  <i className="fa-regular fa-clock"></i> {fmt(timeLeft)}
                </div>
                {/* LỐI THOÁT (21/09/2026). Chế độ làm bài tước hết điều hướng để
                    không ai bấm nhầm mà mất bài — nhưng tước cả lối ra thì em
                    mở nhầm đề chỉ còn cách đóng tab. Hỏi trước, vì thoát là bỏ
                    lượt đang làm. */}
                <button
                  type="button"
                  className="mk-btn ghost mk-thoat"
                  onClick={() => {
                    if (dangNop) return;
                    if (window.confirm('Thoát khỏi bài thi? Bài đang làm sẽ KHÔNG được nộp.')) {
                      setExam(null); setResult(null); setView('list');
                    }
                  }}
                >
                  Thoát
                </button>
              </>
            }
          />
        ) : (
          <AppShell trang="/mock" spa={false} dieuKhien="react" ten={ten} />
        )}

        {/* `<main>` bọc ba màn (danh sách / làm bài / kết quả) — mốc trang cho
            trình đọc màn hình (axe `landmark-one-main`, 20/09/2026). */}
        <main>
        {view === 'loading' && <div className="mk-loading"><div className="mk-spinner" /> Đang tải…</div>}

        {view === 'list' && (
          <div className="mk-list">
            <h1 className="mk-h1">Thi thử Đánh giá năng lực</h1>
            <p className="mk-sub">Làm đề trên máy như thi thật — bấm giờ, chấm điểm và phân tích mạnh–yếu theo từng hợp phần.</p>
            {loi && <div className="mk-loi" role="alert">{loi}</div>}
            {exams.length === 0 && <div className="mk-empty">Chưa có đề thi thử nào. Đề đầy đủ sẽ được cập nhật.</div>}
            <div className="mk-exam-grid">
              {exams.map((e) => (
                <div className="mk-exam-card" key={e.id}>
                  <div className="mk-exam-ic"><i className="fa-solid fa-file-pen"></i></div>
                  <h2>{e.title}</h2>
                  <p>{e.description}</p>
                  <div className="mk-exam-meta">
                    <span><i className="fa-solid fa-list-ol"></i> {e.total_questions} câu</span>
                    <span><i className="fa-regular fa-clock"></i> {e.duration_minutes} phút</span>
                  </div>
                  <button className="mk-btn primary" onClick={() => void start(e.id)}>Bắt đầu làm bài →</button>
                </div>
              ))}
            </div>
          </div>
        )}

        {view === 'take' && exam && (() => {
          const q = exam.questions[cur];
          return (
            <div className="mk-take">
              {dangNop && (
                <div className="mk-cham-phu" role="status" aria-live="polite">
                  <div className="mk-spinner" /> Đang chấm bài…
                </div>
              )}
              <div className="mk-take-head">
                <div className="mk-progress-txt">
                  Câu {cur + 1}/{exam.questions.length} · đã trả lời {answeredCount()}
                  {/* Nhãn "lượt luyện" nay nằm ở thanh trên — nói MỘT lần,
                      và nói ở chỗ luôn nhìn thấy kể cả khi cuộn. */}
                </div>
                {/* Đồng hồ nay ở thanh trên (cố định), xem AppShell phía trên. */}
              </div>

              <div className="mk-take-body">
                <div className="mk-qcard">
                  <div className="mk-q-sec" style={{ color: SECTION_COLOR[q.section_label] || '#8B7CF6' }}>
                    {q.section_label} · {q.type === 'fill' ? 'Điền đáp án' : 'Trắc nghiệm'}
                  </div>
                  <p className="mk-q-text">{q.question}</p>
                  {q.type === 'fill' ? (
                    <input className="mk-fill" value={answers[q.id] || ''} placeholder="Nhập đáp án…"
                      onChange={(e) => setAns(q.id, e.target.value)} autoComplete="off" />
                  ) : (
                    <div className="mk-opts">
                      {/* `aria-pressed` (22/09/2026, agent tiếp cận F15): "đã chọn"
                          trước chỉ nằm ở lớp `.sel` — trình đọc màn hình nghe các
                          phương án y hệt nhau, không biết mình đã chọn cái nào. */}
                      {(q.options || []).map((op: string) => (
                        <button key={op} type="button" className={'mk-opt' + (answers[q.id] === op ? ' sel' : '')}
                          aria-pressed={answers[q.id] === op}
                          onClick={() => setAns(q.id, op)}>{op}</button>
                      ))}
                    </div>
                  )}
                  <div className="mk-q-nav">
                    <button className="mk-btn ghost" disabled={cur === 0} onClick={() => setCur((c) => c - 1)}>← Câu trước</button>
                    {cur < exam.questions.length - 1
                      ? <button className="mk-btn" onClick={() => setCur((c) => c + 1)}>Câu sau →</button>
                      : <button className="mk-btn primary" onClick={confirmSubmit}>Nộp bài ✓</button>}
                  </div>
                </div>

                <aside className="mk-palette">
                  <div className="mk-palette-label">Bảng câu hỏi</div>
                  {/* Tên nút nói đủ điều mà màu đang nói (F15): "Câu 3, đã trả lời";
                      câu đang xem mang `aria-current`. Trước đó tên chỉ là "3" —
                      đã làm / đang xem nằm hết ở lớp `done` / `cur`. Tên vẫn CHỨA
                      con số nhìn thấy (WCAG 2.5.3 — điều khiển bằng giọng nói). */}
                  <div className="mk-palette-grid" role="group" aria-label="Bảng câu hỏi">
                    {exam.questions.map((qq: any, i: number) => (
                      <button key={qq.id} type="button"
                        className={'mk-pal' + (i === cur ? ' cur' : '') + (answers[qq.id] ? ' done' : '')}
                        aria-label={`Câu ${i + 1}, ${answers[qq.id] ? 'đã trả lời' : 'chưa trả lời'}`}
                        aria-current={i === cur ? 'step' : undefined}
                        onClick={() => setCur(i)}>{i + 1}</button>
                    ))}
                  </div>
                  {/* Nút PHỤ, không phải tím đặc (21/09/2026): ở 768 bảng câu hỏi
                      rơi xuống dưới thẻ câu hỏi, nên nút tím 704×50 này nằm ngay
                      dưới câu 1 — nút to nhất màn hình là nút nộp, mà nộp thì
                      chấm ngay, không hoàn tác. Nút chính "Nộp bài ✓" vẫn ở hàng
                      điều hướng khi tới câu cuối; đây là lối tắt, trông như lối tắt. */}
                  <button className="mk-btn full" onClick={confirmSubmit}>Nộp bài sớm ✓</button>
                  <div className="mk-palette-note">Hết giờ sẽ tự nộp.</div>
                </aside>
              </div>
            </div>
          );
        })()}

        {view === 'result' && result && (
          <div className="mk-result">
            <h1 className="mk-h1">Kết quả thi thử</h1>
            <div className="mk-score-card">
              <div className="mk-score-num">{result.score}<span>/{result.total}</span></div>
              <div className="mk-score-body">
                <div className="mk-score-pct">{Math.round((result.score / (result.total || 1)) * 100)}% chính xác</div>
                {/* "Đã làm bao nhiêu câu" (21/09/2026): điểm tính trên TỔNG số câu
                    của đề, nên nộp sớm mà bỏ trống 6/9 câu vẫn ra "0/9 · 0%" —
                    nhìn như làm sai hết. Câu bỏ trống khác câu làm sai. */}
                {(() => {
                  const daLam = (result.results || []).filter((r: { answered?: boolean }) => r.answered).length;
                  return daLam < (result.total || 0)
                    ? <div className="mk-score-answered">Đã làm {daLam}/{result.total} câu — {(result.total || 0) - daLam} câu bỏ trống tính là chưa có điểm.</div>
                    : null;
                })()}
                {result.weakest && <div className="mk-weak">Cần ôn nhất: <b>{result.weakest}</b></div>}
                {/* Một lượt vào sổ (quyết định 31/08/2026). Nói ra ngay ở đây,
                    vì im lặng rồi không cộng XP thì học viên tưởng hệ lỗi. */}
                {result.counted === false && (
                  <div className="mk-note-practice">
                    {result.notCountedReason === 'het_gio'
                      ? 'Nộp quá giờ nên lượt này không vào sổ điểm.'
                      : 'Lượt luyện tập — bạn đã có một lượt vào sổ cho đề này, nên lượt này không tính điểm và không cộng XP.'}
                  </div>
                )}
                {result.counted !== false && result.xpGained
                  ? <div className="mk-note-xp">+{result.xpGained} XP</div> : null}
              </div>
            </div>

            <div className="mk-sec-label">Phân tích theo hợp phần</div>
            <div className="mk-sections">
              {Object.entries(result.section_scores || {}).map(([label, sc]: any) => {
                const pct = sc.total ? Math.round((sc.correct / sc.total) * 100) : 0;
                return (
                  <div className="mk-sec-row" key={label}>
                    <div className="mk-sec-name">{label} {label === result.weakest && <span className="mk-sec-weak">⚠ yếu</span>}</div>
                    <div className="mk-sec-bar"><div className="mk-sec-fill" style={{ width: pct + '%', background: SECTION_COLOR[label] || '#8B7CF6' }} /></div>
                    <div className="mk-sec-val">{sc.correct}/{sc.total}</div>
                  </div>
                );
              })}
            </div>

            <div className="mk-sec-label">Xem lại từng câu</div>
            <ul className="mk-review">
              {/* Máy chủ chỉ trả đáp án cho câu ĐÃ trả lời (mockexam/views.py
                  luật 2). Câu bỏ trống về `answer: null` — nói thẳng là chưa
                  trả lời, đừng in "Đáp án: null".
                  Và bỏ trống KHÁC làm sai (21/09/2026): dấu ✕ đỏ cho câu chưa
                  làm khiến màn kết quả đọc như "sai hết" — dùng ○ trung tính. */}
              {(result.results || []).map((r: any, i: number) => (
                <li className={'mk-rev ' + (r.correct ? 'ok' : r.answered ? 'no' : 'trong')} key={r.id}>
                  <span className="mk-rev-ic">{r.correct ? '✓' : r.answered ? '✕' : '○'}</span>
                  <span className="mk-rev-q">Câu {i + 1}</span>
                  <span className="mk-rev-a">
                    {/* ĐỀ BÀI trước, rồi mới tới đáp án (21/09/2026): "Đáp án: 17 ·
                        bạn chọn: 15" mà không có câu hỏi thì muốn biết sai ở đâu
                        phải nhớ lại đề. */}
                    {r.question && <span className="mk-rev-de">{r.question}</span>}
                    {r.answered
                      ? <>Đáp án: <b>{r.answer}</b>{!r.correct && r.your ? ` · bạn chọn: ${r.your}` : ''}</>
                      : <em>Bỏ trống — làm lại đề để xem đáp án câu này.</em>}
                  </span>
                </li>
              ))}
            </ul>

            <div className="mk-result-actions">
              <button className="mk-btn ghost" onClick={() => { setResult(null); setExam(null); setView('list'); }}>← Đề khác</button>
              <button className="mk-btn primary" onClick={() => taiTrang('/dashboard')}>Về lộ trình →</button>
            </div>
          </div>
        )}
        </main>
      </div>

      {/* Trợ lý HSA cũng có mặt ở phòng thi thử (audit 2026-08-14): sau khi
          nộp bài, học viên hay muốn hỏi ngay câu vừa sai. */}
      <Chatbot />
    </>
  );
}
