-- ============================================================================
-- mockexam_schema.sql — bảng cho trụ cột ④: Thi thử CBT (ProgrammingEdu × TopHSA)
-- Chạy sau legacy_schema.sql (FK tới users). Idempotent.
-- ============================================================================

-- Đề thi thử: questions_json = mảng {id, section, type('mcq'|'fill'), question, options?, answer}
CREATE TABLE IF NOT EXISTS mock_exams (
    id               SERIAL PRIMARY KEY,
    title            TEXT NOT NULL,
    description      TEXT DEFAULT '',
    duration_minutes INTEGER DEFAULT 60,
    total_questions  INTEGER DEFAULT 0,
    questions_json   JSONB NOT NULL,
    is_published     BOOLEAN DEFAULT TRUE,
    created_at       TIMESTAMP DEFAULT now()
);

-- Lượt làm bài của user (chấm + phân tích theo hợp phần)
CREATE TABLE IF NOT EXISTS mock_attempts (
    id                  SERIAL PRIMARY KEY,
    user_id             INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exam_id             INTEGER REFERENCES mock_exams(id) ON DELETE CASCADE,
    score               INTEGER DEFAULT 0,
    total               INTEGER DEFAULT 0,
    section_scores_json JSONB,
    answers_json        JSONB,
    duration_seconds    INTEGER DEFAULT 0,
    started_at          TIMESTAMP,
    submitted_at        TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_mock_attempts_user ON mock_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_mock_attempts_exam ON mock_attempts(exam_id);
