'use client';

// Trụ cột ④ — Thi thử CBT (ProgrammingEdu × TopHSA). React thuần + apiFetch.
// list → làm bài (bấm giờ, palette câu, MCQ/điền) → kết quả + phân tích hợp phần.
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useCallback, useEffect, useRef, useState } from 'react';

import Chatbot from '@/components/Chatbot';
import LegacyScripts from '@/components/LegacyScripts';
import PageStyles from '@/components/PageStyles';
import { apiFetch } from '@/lib/api';

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
  const startRef = useRef(0);
  const answersRef = useRef<Record<string, string>>({});
  answersRef.current = answers;

  useEffect(() => {
    (async () => {
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

  useEffect(() => {
    if (view !== 'take') return;
    const id = setInterval(() => {
      setTimeLeft((t) => { if (t <= 1) { clearInterval(id); submit(); return 0; } return t - 1; });
    }, 1000);
    return () => clearInterval(id);
  }, [view, submit]);

  async function start(id: number) {
    setView('loading');
    const r = await apiFetch(`/api/mock-exams/${id}`);
    const d = await r.json();
    setExam(d); setAnswers({}); setCur(0);
    setTimeLeft((d.duration_minutes || 20) * 60);
    startRef.current = Date.now(); setView('take');
  }
  const setAns = (qid: string, val: string) => setAnswers((a) => ({ ...a, [qid]: val }));
  const answeredCount = () => Object.keys(answers).filter((k) => answers[k] != null && answers[k] !== '').length;
  const confirmSubmit = () => {
    if (window.confirm(`Nộp bài? Bạn đã trả lời ${answeredCount()}/${exam.questions.length} câu.`)) submit();
  };

  // ─────────── views ───────────
  return (
    <>
      <PageStyles hrefs={['/static/css/theme.css', '/static/css/mock.css', '/static/css/chatbot.css']} />
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
          <nav className="mk-nav" aria-label="Điều hướng chính">
            <a className="mk-nav-link" href="/dashboard#dashboard">Dashboard</a>
            <a className="mk-nav-link" href="/dashboard#courses">Khóa học</a>
            <a className="mk-nav-link" href="/dashboard#roadmap">Lộ trình</a>
            <a className="mk-nav-link" href="/dashboard#forum">Diễn đàn</a>
            <span className="mk-nav-link is-active" aria-current="page">Thi thử</span>
          </nav>
          <div className="mk-top-tag">Thi thử CBT</div>
        </div>

        {view === 'loading' && <div className="mk-loading"><div className="mk-spinner" /> Đang tải…</div>}

        {view === 'list' && (
          <div className="mk-list">
            <h1 className="mk-h1">Thi thử Đánh giá năng lực</h1>
            <p className="mk-sub">Làm đề trên máy như thi thật — bấm giờ, chấm điểm và phân tích mạnh–yếu theo từng hợp phần.</p>
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
                  <button className="mk-btn primary" onClick={() => start(e.id)}>Bắt đầu làm bài →</button>
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
                <div className="mk-progress-txt">Câu {cur + 1}/{exam.questions.length} · đã trả lời {answeredCount()}</div>
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
              {(result.results || []).map((r: any, i: number) => (
                <li className={'mk-rev ' + (r.correct ? 'ok' : 'no')} key={r.id}>
                  <span className="mk-rev-ic">{r.correct ? '✓' : '✕'}</span>
                  <span className="mk-rev-q">Câu {i + 1}</span>
                  <span className="mk-rev-a">Đáp án: <b>{r.answer}</b>{!r.correct && r.your ? ` · bạn chọn: ${r.your}` : ''}</span>
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
