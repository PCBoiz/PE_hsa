-- ============================================================================
-- legacy_schema.sql — DDL đầy đủ 22 bảng nền của ProgrammingEdu (bản HSA)
-- Nguồn chuẩn: model pe_hsa (inspectdb_snapshot.py + app models.py) — phản chiếu
-- 100% schema production. DEFAULT lấy từ db/schema.py (PE_test) cho đúng hành vi
-- raw-SQL đã port. KHÔNG kèm bất kỳ seed nội dung nào (seed HSA nằm ở seed_data).
-- Thứ tự bảng theo phụ thuộc FK (bảng được tham chiếu tạo trước).
-- Idempotent: CREATE ... IF NOT EXISTS. Bỏ 'playing_with_neon' (bảng demo Neon).
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1. users (AUTH_USER_MODEL = accounts.User) --------------------------------
CREATE TABLE IF NOT EXISTS users (
    id                      SERIAL PRIMARY KEY,
    name                    TEXT,
    email                   TEXT UNIQUE,
    phone                   TEXT DEFAULT '',
    birthday                TEXT DEFAULT '',
    role                    TEXT DEFAULT 'Học viên',
    password                VARCHAR(512),
    streak                  INTEGER DEFAULT 0,
    certificates            INTEGER DEFAULT 0,
    gems                    INTEGER DEFAULT 0,
    xp                      INTEGER DEFAULT 0,
    questionnaire_completed INTEGER DEFAULT 0,
    last_study_date         DATE,
    oauth_provider          TEXT,
    oauth_provider_id       TEXT,
    avatar                  TEXT DEFAULT '',
    is_verified             BOOLEAN DEFAULT FALSE,
    created_at              TIMESTAMP DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_oauth
    ON users(oauth_provider, oauth_provider_id) WHERE oauth_provider IS NOT NULL;

-- 2. courses ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS courses (
    id            TEXT PRIMARY KEY,
    title         TEXT,
    subtitle      TEXT,
    description   TEXT,
    image         TEXT,
    level         TEXT,
    duration      TEXT,
    students      TEXT,
    rating        DOUBLE PRECISION,
    lessons       INTEGER,
    color         TEXT,
    accent_color  TEXT,
    tag           TEXT,
    instructor_id INTEGER REFERENCES users(id),
    xp_reward     INTEGER,
    is_published  BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT now(),
    content_meta  JSONB
);
CREATE INDEX IF NOT EXISTS idx_courses_level ON courses(level);
CREATE INDEX IF NOT EXISTS idx_courses_title_trgm ON courses USING gin(title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_courses_tag_trgm ON courses USING gin(tag gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_courses_subtitle_trgm ON courses USING gin(subtitle gin_trgm_ops);

-- 3. achievements -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS achievements (
    id              SERIAL PRIMARY KEY,
    code            TEXT UNIQUE NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    icon            TEXT,
    condition_type  TEXT NOT NULL,
    condition_value INTEGER NOT NULL
);

-- 4. surveys ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS surveys (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER,
    data_json  JSONB,
    created_at TEXT
);

-- 5. roadmaps (template khi user_id NULL; roadmap cá nhân khi có user_id) ----
CREATE TABLE IF NOT EXISTS roadmaps (
    id                       TEXT PRIMARY KEY,
    user_id                  INTEGER REFERENCES users(id),
    source                   TEXT,
    generated_from_survey_id INTEGER REFERENCES surveys(id),
    title                    TEXT,
    icon                     TEXT,
    color                    TEXT,
    nodes_json               JSONB,
    edges_json               JSONB,
    mermaid_def              TEXT,
    created_at               TIMESTAMP DEFAULT now(),
    updated_at               TIMESTAMP DEFAULT now()
);

-- 6. lessons ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lessons (
    id                SERIAL PRIMARY KEY,
    course_id         TEXT REFERENCES courses(id) ON DELETE CASCADE,
    module            TEXT DEFAULT '',
    title             TEXT NOT NULL,
    content           TEXT DEFAULT '',
    sort_order        INTEGER DEFAULT 0,
    created_at        TIMESTAMP DEFAULT now(),
    lesson_type       TEXT,
    xp_reward         INTEGER,
    is_free_preview   BOOLEAN DEFAULT FALSE,
    lesson_code       TEXT,
    content_json      JSONB,
    subtitle          TEXT,
    estimated_minutes INTEGER,
    updated_at        TIMESTAMP DEFAULT now(),
    UNIQUE (course_id, lesson_code)
);
CREATE INDEX IF NOT EXISTS idx_lessons_course_id ON lessons(course_id);

-- 7. missions ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS missions (
    id                SERIAL PRIMARY KEY,
    title             TEXT NOT NULL,
    description       TEXT DEFAULT '',
    xp_reward         INTEGER DEFAULT 50,
    course_id         TEXT REFERENCES courses(id),
    sort_order        INTEGER DEFAULT 0,
    is_active         BOOLEAN DEFAULT TRUE,
    correct_condition TEXT DEFAULT '',
    correct_action    TEXT DEFAULT ''
);

-- 8. enrollments (không FK — giữ đúng schema production) --------------------
CREATE TABLE IF NOT EXISTS enrollments (
    user_id           INTEGER,
    course_id         TEXT,
    progress          INTEGER DEFAULT 0,
    completed_lessons INTEGER DEFAULT 0,
    time_spent        TEXT DEFAULT '0h',
    last_lesson       TEXT DEFAULT '',
    next_lesson       TEXT DEFAULT '',
    status            TEXT DEFAULT 'active',
    enrolled_at       TIMESTAMP DEFAULT now(),
    completed_at      TIMESTAMP,
    PRIMARY KEY (user_id, course_id)
);
CREATE INDEX IF NOT EXISTS idx_enrollments_user_id ON enrollments(user_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course_id ON enrollments(course_id);

-- 9. course_ratings ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS course_ratings (
    user_id    INTEGER,
    course_id  TEXT,
    rating     INTEGER NOT NULL,
    created_at TEXT,
    PRIMARY KEY (user_id, course_id)
);
CREATE INDEX IF NOT EXISTS idx_course_ratings_course_id ON course_ratings(course_id);
CREATE INDEX IF NOT EXISTS idx_course_ratings_user_id ON course_ratings(user_id);

-- 10. lesson_progress -------------------------------------------------------
CREATE TABLE IF NOT EXISTS lesson_progress (
    user_id      INTEGER,
    lesson_id    INTEGER,
    course_id    TEXT,
    status       TEXT DEFAULT 'not_started',
    quiz_score   INTEGER,
    xp_earned    INTEGER DEFAULT 0,
    completed_at TIMESTAMP,
    PRIMARY KEY (user_id, lesson_id)
);
CREATE INDEX IF NOT EXISTS idx_lesson_progress_user ON lesson_progress(user_id);

-- 11. quizzes ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quizzes (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id      TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    status         TEXT,
    questions_json JSONB NOT NULL,
    created_at     TIMESTAMP DEFAULT now()
);

-- 12. review_quiz_results ---------------------------------------------------
CREATE TABLE IF NOT EXISTS review_quiz_results (
    id           SERIAL PRIMARY KEY,
    quiz_id      INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    user_id      INTEGER NOT NULL,
    score        INTEGER NOT NULL,
    total        INTEGER NOT NULL,
    answers_json JSONB NOT NULL,
    submitted_at TIMESTAMP DEFAULT now()
);

-- 13. posts -----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS posts (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
    category   TEXT DEFAULT 'discuss',
    title      TEXT DEFAULT '',
    content    TEXT NOT NULL,
    like_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);

-- 14. comments (self-FK parent_comment_id để lồng bình luận) -----------------
CREATE TABLE IF NOT EXISTS comments (
    id                SERIAL PRIMARY KEY,
    post_id           INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    user_id           INTEGER REFERENCES users(id) ON DELETE CASCADE,
    content           TEXT NOT NULL,
    created_at        TIMESTAMP DEFAULT now(),
    updated_at        TIMESTAMP DEFAULT now(),
    parent_comment_id INTEGER REFERENCES comments(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id);

-- 15. post_likes ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS post_likes (
    post_id       INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    user_id       INTEGER REFERENCES users(id) ON DELETE CASCADE,
    reaction_type TEXT NOT NULL,
    created_at    TIMESTAMP DEFAULT now(),
    PRIMARY KEY (post_id, user_id)
);

-- 16. comment_likes ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS comment_likes (
    comment_id    INTEGER REFERENCES comments(id) ON DELETE CASCADE,
    user_id       INTEGER REFERENCES users(id) ON DELETE CASCADE,
    reaction_type TEXT NOT NULL,
    created_at    TIMESTAMP DEFAULT now(),
    PRIMARY KEY (comment_id, user_id)
);

-- 17. notifications (feed) --------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type       TEXT,
    title      TEXT,
    body       TEXT,
    ref_type   TEXT,
    ref_id     INTEGER,
    is_read    BOOLEAN DEFAULT FALSE,
    coalesce_count INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT now()
);
-- coalesce_count (gộp thông báo trùng, notifications/service.py) là additive —
-- bảng cũ chưa có cột này → thêm nếu thiếu để /api/notifications/feed không 500.
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS coalesce_count INTEGER NOT NULL DEFAULT 1;
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);

-- 18. notification_settings -------------------------------------------------
CREATE TABLE IF NOT EXISTS notification_settings (
    user_id        INTEGER PRIMARY KEY,
    email_notif    INTEGER DEFAULT 1,
    push_notif     INTEGER DEFAULT 0,
    study_remind   INTEGER DEFAULT 1,
    content_update INTEGER DEFAULT 0
);

-- 19. roadmap_progress (PK 3 cột: user + roadmap + item) --------------------
CREATE TABLE IF NOT EXISTS roadmap_progress (
    user_id      INTEGER,
    roadmap_id   TEXT REFERENCES roadmaps(id) ON DELETE CASCADE,
    item_id      TEXT,
    done         BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    PRIMARY KEY (user_id, roadmap_id, item_id)
);

-- 20. user_achievements -----------------------------------------------------
CREATE TABLE IF NOT EXISTS user_achievements (
    user_id        INTEGER,
    achievement_id INTEGER REFERENCES achievements(id) ON DELETE CASCADE,
    awarded_at     TIMESTAMP DEFAULT now(),
    PRIMARY KEY (user_id, achievement_id)
);

-- 21. user_daily_xp_logs ----------------------------------------------------
CREATE TABLE IF NOT EXISTS user_daily_xp_logs (
    id        SERIAL PRIMARY KEY,
    user_id   INTEGER REFERENCES users(id) ON DELETE CASCADE,
    log_date  DATE NOT NULL,
    xp_earned INTEGER DEFAULT 0,
    UNIQUE (user_id, log_date)
);

-- 22. user_follows ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_follows (
    follower_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    followee_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMP DEFAULT now(),
    PRIMARY KEY (follower_id, followee_id)
);

-- ============================================================================
-- 23. Nhiệm vụ hằng ngày & bảo hiểm chuỗi (gamification HSA, 2026-08-14)
-- ============================================================================
-- `missions` vốn là NHIỆM VỤ SQL của pe_test: chấm đúng/sai bằng cặp
-- (correct_condition, correct_action) — vô nghĩa với luyện thi HSA. Đổi thành
-- nhiệm vụ hằng ngày chấm bằng SỐ LIỆU THẬT trong ngày (số bài xong, XP kiếm
-- được, số đề đã làm). Bảng rỗng ở mọi môi trường nên đổi cột là an toàn.
ALTER TABLE missions DROP COLUMN IF EXISTS correct_condition;
ALTER TABLE missions DROP COLUMN IF EXISTS correct_action;
ALTER TABLE missions ADD COLUMN IF NOT EXISTS code TEXT;
ALTER TABLE missions ADD COLUMN IF NOT EXISTS condition_type TEXT;
ALTER TABLE missions ADD COLUMN IF NOT EXISTS condition_value INTEGER DEFAULT 1;
ALTER TABLE missions ALTER COLUMN course_id DROP NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_missions_code ON missions(code);

-- Nhận thưởng nhiệm vụ: khoá chính gồm cả NGÀY để mỗi ngày nhận lại được một
-- lần, và không bao giờ nhận trùng trong cùng ngày.
CREATE TABLE IF NOT EXISTS user_missions (
    user_id      INTEGER REFERENCES users(id) ON DELETE CASCADE,
    mission_id   INTEGER REFERENCES missions(id) ON DELETE CASCADE,
    mission_date DATE NOT NULL,
    xp_earned    INTEGER DEFAULT 0,
    claimed_at   TIMESTAMP DEFAULT now(),
    PRIMARY KEY (user_id, mission_id, mission_date)
);

-- Bảo hiểm chuỗi: nghỉ đúng 1 ngày thì tiêu 1 vé thay vì mất sạch chuỗi. Thí
-- sinh ôn 6 tháng mà mất chuỗi vì một ngày bận là điểm bỏ cuộc kinh điển.
ALTER TABLE users ADD COLUMN IF NOT EXISTS streak_freezes INTEGER NOT NULL DEFAULT 3;

-- ============================================================================
-- 24. Gắn bài viết diễn đàn vào BÀI HỌC (2026-08-14)
-- ============================================================================
-- Học viên đang ở bài 12 Định lượng cần thấy ngay câu hỏi về bài 12. Lưu
-- (course_id, lesson_no) chứ KHÔNG phải FK tới lessons: bảng lessons chỉ chứa
-- stub tạo lười khi có người hoàn thành bài, nên bài chưa ai học sẽ không có
-- dòng để tham chiếu.
ALTER TABLE posts ADD COLUMN IF NOT EXISTS course_id TEXT;
ALTER TABLE posts ADD COLUMN IF NOT EXISTS lesson_no INTEGER;
-- Bài mồi để diễn đàn không trống trơn lúc demo. Có cờ riêng để giao diện DÁN
-- NHÃN rõ ràng — người xem không được phép nhầm đây là bài của học viên thật.
ALTER TABLE posts ADD COLUMN IF NOT EXISTS is_sample BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS idx_posts_lesson ON posts(course_id, lesson_no);

-- ============================================================================
-- 25. Tiến độ lộ trình: bỏ khoá ngoại tới `roadmaps` (2026-08-19)
-- ============================================================================
-- Danh mục 26 lộ trình nằm trong roadmapData.js phía client (giống hệt trường
-- hợp nội dung bài học trước đây), bảng `roadmaps` chỉ có mẫu do seed tạo. Khoá
-- ngoại này khiến MỌI lần lưu tiến độ đều 500 vì roadmap_id là TÊN lộ trình
-- tĩnh, không có dòng tương ứng. Hệ quả: tiến độ lộ trình chỉ nằm trong
-- localStorage, đổi máy là mất sạch.
ALTER TABLE roadmap_progress DROP CONSTRAINT IF EXISTS roadmap_progress_roadmap_id_fkey;

-- ============================================================================
-- 26. learning_events — MỘT dòng sự kiện học tập cho mọi hoạt động (2026-08-24)
-- ============================================================================
-- Trước đây dữ liệu học tập nằm ở NĂM bảng rời (lesson_progress, mock_attempts,
-- review_quiz_results, user_missions, user_daily_xp_logs), mỗi nơi một hình
-- dạng. Hệ quả: không màn hình nào trả lời được câu hỏi quan trọng nhất của thí
-- sinh — "tôi mạnh yếu ở đâu, tiến bộ tới đâu?" — và mỗi lần thêm một loại hoạt
-- động lại phải sửa mọi chỗ hiển thị.
--
-- Bảng này mượn ý Completion API của Moodle: hoạt động chỉ việc BÁO CÁO một sự
-- kiện; sổ điểm, bản đồ năng lực, đường cong tiến bộ và kế hoạch học đều là các
-- cách ĐỌC KHÁC NHAU trên cùng một bảng.
--
-- Hai điểm cố ý:
--   · `source` tách rạch ròi số hệ thống ĐO ĐƯỢC với số học viên TỰ KHAI. Trộn
--     hai loại vào một biểu đồ là cách nhanh nhất làm mất tin cậy của số liệu.
--   · `topic` CHÉP LẠI lúc ghi, không tham chiếu tới lessons.module. Giáo trình
--     sẽ được soạn lại theo TopHSA; chép giá trị giữ cho số liệu lịch sử không
--     đổi nghĩa khi chương mục thay đổi.
--
-- Từ vựng `kind` (mỗi dòng chỉ mang đúng một nghĩa):
--   lesson       kiểm tra đầu vào của bài học   (score = phần trăm đúng, max 100)
--   drill        phòng luyện tốc độ             (score/max = số câu)
--   review_quiz  quiz ôn tập, MỘT DÒNG MỖI CHỦ ĐỀ trong cùng một lượt
--   mock         TỔNG một lượt thi thử (course_id NULL) = nguồn của đường cong
--   mock_section điểm theo hợp phần của chính lượt đó = nguồn của năng lực
--   mission      nhận thưởng nhiệm vụ ngày (không chấm điểm)
--   self_log     học viên tự ghi nhận (source='self')
-- `mock` và `mock_section` cùng một lượt thi: bên đọc CHỌN một trong hai, nên
-- không bao giờ cộng trùng một lượt vào cùng một phép tính.
--
-- `dedup_key` BẮT BUỘC và duy nhất theo từng học viên. Nhờ nó lệnh nạp dữ liệu
-- cũ chạy lại bao nhiêu lần cũng không nhân đôi số liệu, và học lại một bài thì
-- sự kiện được CẬP NHẬT chứ không đẻ thêm dòng — khớp đúng với lesson_progress
-- (bảng đó cũng chỉ giữ một dòng cho mỗi cặp học viên–bài).
CREATE TABLE IF NOT EXISTS learning_events (
    id          BIGSERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dedup_key   TEXT NOT NULL,
    occurred_at TIMESTAMP NOT NULL,
    event_date  DATE NOT NULL,
    kind        TEXT NOT NULL,
    course_id   TEXT,
    topic       TEXT,
    ref_type    TEXT,
    ref_id      TEXT,
    score       NUMERIC(6,2),
    max_score   NUMERIC(6,2),
    minutes     INTEGER,
    xp          INTEGER DEFAULT 0,
    source      TEXT NOT NULL DEFAULT 'system',
    meta        JSONB,
    created_at  TIMESTAMP DEFAULT now(),
    UNIQUE (user_id, dedup_key)
);
CREATE INDEX IF NOT EXISTS idx_levents_user_date ON learning_events(user_id, event_date DESC);
CREATE INDEX IF NOT EXISTS idx_levents_user_topic ON learning_events(user_id, course_id, topic);
CREATE INDEX IF NOT EXISTS idx_levents_user_kind ON learning_events(user_id, kind, occurred_at DESC);

-- Tự đánh dấu "đã nắm" một chủ đề.
-- Khoá gồm course_id vì "Chiến thuật" là chủ đề của CẢ BA hợp phần — bỏ course
-- ra khỏi khoá thì đánh dấu Chiến thuật ở Định lượng sẽ tắt luôn Chiến thuật
-- của Khoa học.
-- QUY TẮC: tự đánh dấu là ĐẦU VÀO ĐỂ XẾP LỊCH, KHÔNG phải bằng chứng năng lực.
-- Điểm thành thạo vẫn tính theo bài làm thật.
CREATE TABLE IF NOT EXISTS topic_self_marks (
    user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id TEXT NOT NULL,
    topic     TEXT NOT NULL,
    known     BOOLEAN NOT NULL,
    marked_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, course_id, topic)
);
