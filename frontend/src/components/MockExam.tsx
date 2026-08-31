'use client';

// Trụ cột ④ — Thi thử CBT (ProgrammingEdu × TopHSA). React thuần + apiFetch.
// list → làm bài (bấm giờ, palette câu, MCQ/điền) → kết quả + phân tích hợp phần.
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useCallback, useEffect, useRef, useState } from 'react';
import { MUC_NAV } from '@/components/navMuc';

import Chatbot from '@/components/Chatbot';
import LegacyScripts from '@/components/LegacyScripts';
import PageStyles from '@/components/PageStyles';
import { apiFetch, errorText } from '@/lib/api';

const fmt = (s: number) =>
  `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(Math.max(0, s % 60)).padStart(2, '0')}`;

const SECTION_COLOR: Record<string, string> = {
  'Định lượng': '#8B7CF6', 'Định tính': '#F472B6', 'Khoa học': '#2DD4BF',
};

export default function MockExam() {
  const [view, setView] = useState<'loading' | 'list' | 'take' | 'result'>('loading');
  const [exams, setExams] = useState<any[]>([]);
  const [exam, setExam] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [cur, setCur] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [loi, setLoi] = useState<string>('');
  const startRef = useRef(0);
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
        if (r.status === 401) { window.location.href = '/login'; return; }
        const d = await r.json();
        setExams(d.exams || []); setView('list');
      } catch { setExams([]); setView('list'); }
    })();
  }, []);

  const submit = useCallback(async () => {
    if (!exam) return;
    const dur = Math.round((Date.now() - startRef.current) / 1000);
    setView('loading');
    try {
      const r = await apiFetch(`/api/mock-exams/${exam.id}/submit`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: answersRef.current, duration_seconds: dur }),
      });
      const d = await r.json();
      setResult(d); setView('result');
    } catch { setView('take'); }
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
      <PageStyles hrefs={['/static/css/theme.css', '/static/css/mock.css', '/static/css/chatbot.css', '/static/css/a11y.css']} />
      <title>Thi thử CBT — ProgrammingEdu × TopHSA</title>
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />

      <div className="mk-wrap">
        <div className="mk-topbar">
          <div className="mk-brand" onClick={() => (window.location.href = '/dashboard')}>
            <span className="mk-c1">ProgrammingEdu</span> <span className="mk-x">×</span> <span className="mk-c2">TopHSA</span>
          </div>
          {/* Trang này trước đây KHÔNG có điều hướng — vào Thi thử là mất đường
              về (audit 2026-08-14). Dashboard là SPA nên dùng deep-link #hash
              (main.js đọc hash lúc khởi động) thay vì gọi navigate() vốn không
              tồn tại ở trang này. */}
          {/* BẢN SAO THỨ BA của thanh điều hướng, và nó thiếu nhiều nhất: chỉ
              5 trong 8 mục (không có Kế hoạch, Kỹ năng, Bài tập). Nay đọc từ
              `navMuc.ts` như hai bản kia. Vẫn dựng riêng vì màn này có chrome
              của nó (`.mk-nav-link`, không icon) và không nạp main.js. */}
          <nav className="mk-nav" aria-label="Điều hướng chính">
            {MUC_NAV.map((m) => (m.nhan === 'Thi thử' ? (
              <span className="mk-nav-link is-active" aria-current="page" key={m.nhan}>{m.nhan}</span>
            ) : (
              <a className="mk-nav-link" href={m.url} key={m.nhan}>{m.nhan}</a>
            )))}
          </nav>
          <div className="mk-top-tag">Thi thử CBT</div>
        </div>

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
                  <h3>{e.title}</h3>
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
              <div className="mk-take-head">
                <div className="mk-progress-txt">
                  Câu {cur + 1}/{exam.questions.length} · đã trả lời {answeredCount()}
                  {/* Nói TRƯỚC khi làm, không đợi tới lúc nộp: biết mình đang
                      luyện hay đang lấy điểm là thứ ảnh hưởng tới cách làm bài. */}
                  {exam.counts === false && <span className="mk-tag-practice">Lượt luyện · không tính điểm</span>}
                </div>
                <div className={'mk-timer' + (timeLeft <= 60 ? ' low' : '')}>
                  <i className="fa-regular fa-clock"></i> {fmt(timeLeft)}
                </div>
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
                      {(q.options || []).map((op: string) => (
                        <button key={op} className={'mk-opt' + (answers[q.id] === op ? ' sel' : '')}
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
                  <div className="mk-palette-grid">
                    {exam.questions.map((qq: any, i: number) => (
                      <button key={qq.id}
                        className={'mk-pal' + (i === cur ? ' cur' : '') + (answers[qq.id] ? ' done' : '')}
                        onClick={() => setCur(i)}>{i + 1}</button>
                    ))}
                  </div>
                  <button className="mk-btn primary full" onClick={confirmSubmit}>Nộp bài ✓</button>
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
                  trả lời, đừng in "Đáp án: null". */}
              {(result.results || []).map((r: any, i: number) => (
                <li className={'mk-rev ' + (r.correct ? 'ok' : 'no')} key={r.id}>
                  <span className="mk-rev-ic">{r.correct ? '✓' : '✕'}</span>
                  <span className="mk-rev-q">Câu {i + 1}</span>
                  <span className="mk-rev-a">
                    {r.answered
                      ? <>Đáp án: <b>{r.answer}</b>{!r.correct && r.your ? ` · bạn chọn: ${r.your}` : ''}</>
                      : <em>Bỏ trống — làm lại đề để xem đáp án câu này.</em>}
                  </span>
                </li>
              ))}
            </ul>

            <div className="mk-result-actions">
              <button className="mk-btn ghost" onClick={() => { setResult(null); setExam(null); setView('list'); }}>← Đề khác</button>
              <button className="mk-btn primary" onClick={() => (window.location.href = '/dashboard')}>Về lộ trình →</button>
            </div>
          </div>
        )}
      </div>

      {/* Trợ lý HSA cũng có mặt ở phòng thi thử (audit 2026-08-14): sau khi
          nộp bài, học viên hay muốn hỏi ngay câu vừa sai. */}
      <Chatbot />
      <LegacyScripts srcs={['/static/js/chatbot.js']} />
    </>
  );
}
