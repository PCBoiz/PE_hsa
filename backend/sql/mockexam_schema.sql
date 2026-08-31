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

-- ─────────────────────────────────────────────────────────────────────────
-- Lượt thi thử nào VÀO SỔ (L4, 31/08/2026)
-- ─────────────────────────────────────────────────────────────────────────
--
-- Phòng thi thử trước đây không giới hạn lượt và mỗi lượt cộng tới 100 XP, nên
-- một lượt thi vừa là bài kiểm tra vừa là cái cần gạt để cày XP. Tệ hơn: phản
-- hồi lúc nộp trả đủ đáp án cả đề, nên nộp RỖNG rồi nộp lại là 9/9 + 100 XP.
--
-- Anh Sơn chốt 31/08/2026: "một lượt tính điểm, làm lại không cộng XP". Cột này
-- ghi lại quyết định ấy CHO TỪNG DÒNG, thay vì để mọi bên đọc tự suy ra bằng
-- "dòng nào có submitted_at nhỏ nhất" — cách suy ấy sẽ sai ngay khi có lượt hết
-- giờ hoặc lượt bỏ dở xen vào.
--
-- Cột này nằm ở ĐÂY chứ không ở legacy_schema.sql: `bootstrap_schema` đọc thư
-- mục sql/ theo `sorted()`, mà "legacy" < "mockexam", nên một `ALTER TABLE
-- mock_attempts` đặt bên kia sẽ chạy TRƯỚC lệnh CREATE TABLE ở trên và làm đổ
-- cả lần triển khai trên một CSDL rỗng.
--
-- MẶC ĐỊNH TRUE, KHÔNG hồi tố. Năm dòng đang có trên Neon (hai học viên đã làm
-- lại) giữ nguyên counted = TRUE: luật mới áp từ lượt tiếp theo trở đi. Đặt lại
-- lịch sử của người thật theo một luật ban hành sau đó là sửa dữ liệu của họ,
-- không phải sửa lỗi.
--
-- Bên đọc phải lọc counted khi đang đọc SỔ ĐIỂM (bản đồ năng lực, đường cong
-- tiến bộ, nạp lại learning_events). Bên đọc THÓI QUEN (nhiệm vụ ngày "làm 1 đề
-- thi thử") thì KHÔNG lọc — xem docstring mockexam/views.py.
ALTER TABLE mock_attempts ADD COLUMN IF NOT EXISTS counted BOOLEAN NOT NULL DEFAULT TRUE;

-- MỘT lượt đang mở cho mỗi (học viên, đề). Không có ràng buộc này thì hai lời
-- gọi /start song song đều thấy "chưa có lượt nào" rồi cùng INSERT, và lần vào
-- phòng thi sau sẽ nhặt phải cái đồng hồ đã chạy của lượt kia.
CREATE UNIQUE INDEX IF NOT EXISTS uq_mock_attempt_dang_mo
    ON mock_attempts(user_id, exam_id) WHERE submitted_at IS NULL;

-- MỘT lượt tính điểm cho mỗi (học viên, đề). "Một lượt vào sổ" trước đây chỉ
-- dựa vào một câu SELECT không khoá; ở mức cách ly `read committed` thì năm lời
-- gọi /submit song song đều đọc xong trước khi ai kịp COMMIT, và cả năm cùng
-- cộng XP. Ràng buộc này để Postgres từ chối, thay vì để mã tự canh.
--
-- `started_at IS NOT NULL` không phải để cho vui: năm dòng lịch sử trên Neon
-- đều có started_at NULL (không dòng mã nào từng ghi nó) và hai học viên đang
-- có 2 dòng counted. Điều kiện này để lịch sử nằm NGOÀI chỉ mục — đúng với
-- quyết định "không hồi tố" ở trên — trong khi mọi dòng mới (luôn có started_at
-- do /start ghi) đều bị ràng buộc.
CREATE UNIQUE INDEX IF NOT EXISTS uq_mock_attempt_tinh_diem
    ON mock_attempts(user_id, exam_id) WHERE counted AND started_at IS NOT NULL;
