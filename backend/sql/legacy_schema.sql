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
-- (BỎ 01/09/2026 — thừa: PRIMARY KEY (user_id, ...) đã phục vụ `WHERE user_id`.
--  Xem §35 để biết danh sách đầy đủ và câu DROP chờ duyệt.)
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
-- (BỎ 01/09/2026 — thừa: PRIMARY KEY (user_id, ...) đã phục vụ `WHERE user_id`.
--  Xem §35 để biết danh sách đầy đủ và câu DROP chờ duyệt.)

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
-- (BỎ 01/09/2026 — thừa: PRIMARY KEY (user_id, lesson_id) đã phục vụ
--  `WHERE user_id`. Xem §35 để biết danh sách đầy đủ và câu DROP chờ duyệt.)

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

-- ============================================================================
-- 27. Học viên tự ghi nhận: nhật ký ngày + mục tiêu tuần (2026-08-24)
-- ============================================================================
-- Hệ thống đo được điểm số và thời lượng làm bài, nhưng KHÔNG đo được thứ quyết
-- định nhất: học viên thấy phần nào khó, vướng ở đâu, hôm nay có học ngoài ứng
-- dụng không. Đó là dữ liệu chỉ người học mới có.
--
-- Mỗi bản ghi đẻ kèm một dòng learning_events với kind='self_log' và
-- source='self'. Cột `source` tồn tại đúng cho việc này: số TỰ KHAI không bao
-- giờ được trộn lẫn với số hệ thống ĐO ĐƯỢC trong cùng một con số.
CREATE TABLE IF NOT EXISTS study_logs (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date   DATE NOT NULL,
    minutes    INTEGER,
    topic      TEXT,
    what       TEXT,
    difficulty TEXT,
    note       TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP,
    UNIQUE (user_id, log_date)
);
CREATE INDEX IF NOT EXISTS idx_study_logs_user ON study_logs(user_id, log_date DESC);

-- Kế hoạch học. Đợt này MỚI DÙNG `weekly_target` (mục tiêu tuần học viên tự
-- đặt); phần lịch chi tiết là study_plan_items nằm ở việc 5 của đặc tả và chưa
-- làm. Tạo bảng ở đây thay vì nhét mục tiêu tuần vào chỗ khác rồi phải chuyển
-- sang sau — mục tiêu tuần vốn là một thuộc tính của kế hoạch.
CREATE TABLE IF NOT EXISTS study_plans (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at    TIMESTAMP NOT NULL DEFAULT now(),
    updated_at    TIMESTAMP,
    exam_date     DATE,
    weekly_target JSONB,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_study_plans_active
    ON study_plans(user_id) WHERE is_active;

-- ============================================================================
-- 28. study_plan_items — lịch học chi tiết do hệ thống sinh (2026-08-24)
-- ============================================================================
-- Vế "System-Guided" của sản phẩm: học viên vẫn là người tư duy và làm bài, còn
-- lộ trình, mục tiêu từng giai đoạn và việc theo dõi là do hệ thống lo.
--
-- BA ĐIỀU CỐ Ý, đọc kỹ trước khi sửa:
--
-- 1. `week_start` là TUẦN DỰ KIẾN LÚC SINH, và KHÔNG bao giờ bị ghi đè. Lúc
--    đọc, những mục chưa xong được dồn lại vào tuần này trở đi theo sức chứa.
--    Nhờ tách hai thứ đó mà đo được ĐỘ CHẬM ("đang chậm 3 bài") — ghi đè
--    week_start là mất luôn thước đo, lịch lúc nào cũng trông đúng hạn.
--
-- 2. KHÔNG có trạng thái 'done' được ghi vào đây. Xong hay chưa suy ra từ
--    `learning_events` lúc đọc, nên không bao giờ lệch với thực tế và không cần
--    tác vụ đồng bộ. Chỉ 'skipped' mới là quyết định của người dùng nên mới lưu.
--
-- 3. `reason` giữ lý do mục này nằm ở đây ("chủ đề Hình học đang 45%"). Một
--    lịch do hệ thống áp xuống mà không nói vì sao thì học viên không có cơ sở
--    để tin, và bỏ ngay tuần đầu.
CREATE TABLE IF NOT EXISTS study_plan_items (
    id         SERIAL PRIMARY KEY,
    plan_id    INTEGER NOT NULL REFERENCES study_plans(id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    kind       TEXT NOT NULL,
    course_id  TEXT,
    lesson_no  INTEGER,
    topic      TEXT,
    title      TEXT,
    reason     TEXT,
    status     TEXT NOT NULL DEFAULT 'todo',
    skipped_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_plan_items_plan ON study_plan_items(plan_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_plan_items_week ON study_plan_items(plan_id, week_start);
-- Một bài chỉ được xếp đúng một lần trong cùng kế hoạch.
CREATE UNIQUE INDEX IF NOT EXISTS idx_plan_items_lesson
    ON study_plan_items(plan_id, course_id, lesson_no)
    WHERE lesson_no IS NOT NULL;

-- Kế hoạch cần nhớ lúc nào sinh và sinh trên cơ sở nào, để màn hình nói được
-- "lịch này lập ngày ..., dựa trên ... bài/tuần".
ALTER TABLE study_plans ADD COLUMN IF NOT EXISTS generated_at TIMESTAMP;
ALTER TABLE study_plans ADD COLUMN IF NOT EXISTS basis JSONB;

-- ============================================================================
-- 29. Lớp học & vai trò Giảng viên (bước đầu thành ERP, 2026-08-24)
-- ============================================================================
-- Trước đây hệ thống chỉ có HAI vai trò: 'admin' và 'Học viên', và phân quyền là
-- NHỊ PHÂN (common/permissions.py: is_admin). Với một trung tâm luyện thi, mô
-- hình đó sai ngay từ gốc: giảng viên phải thấy được học viên của MÌNH và
-- KHÔNG thấy của người khác.
--
-- Vai trò mới ghi thẳng vào users.role = 'Giảng viên' (cột đã là TEXT tự do,
-- không cần đổi kiểu). Quyền thì KHÔNG theo vai trò mà theo NGỮ CẢNH: giảng
-- viên xem được đúng những lớp mình phụ trách.
--
-- `courses.instructor_id` đã tồn tại từ lâu nhưng luôn NULL và không chỗ nào
-- đọc — cố ý KHÔNG dùng lại nó: một giảng viên phụ trách LỚP, không phụ trách
-- cả khoá (cả ba khoá HSA dùng chung cho mọi lớp).
CREATE TABLE IF NOT EXISTS classes (
    id          SERIAL PRIMARY KEY,
    code        TEXT,
    name        TEXT NOT NULL,
    -- Lớp có thể chỉ ôn một hợp phần, hoặc cả ba (NULL).
    course_id   TEXT REFERENCES courses(id) ON DELETE SET NULL,
    teacher_id  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    -- TopHSA dạy lớp online có lịch cố định. Đợt này mới lưu MÔ TẢ lịch và link
    -- phòng học; từng buổi học và điểm danh là mô-đun riêng (xem đặc tả ERP).
    schedule    TEXT,
    meeting_url TEXT,
    starts_on   DATE,
    ends_on     DATE,
    exam_date   DATE,
    capacity    INTEGER,
    status      TEXT NOT NULL DEFAULT 'active',
    note        TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT now(),
    updated_at  TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_classes_code ON classes(code) WHERE code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_classes_teacher ON classes(teacher_id);

-- Học viên trong lớp. Giữ `left_at` thay vì xoá dòng: học viên nghỉ giữa chừng
-- vẫn phải còn trong báo cáo của kỳ đó, xoá đi là mất luôn lịch sử.
CREATE TABLE IF NOT EXISTS class_members (
    class_id  INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP NOT NULL DEFAULT now(),
    left_at   TIMESTAMP,
    note      TEXT,
    PRIMARY KEY (class_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_class_members_user ON class_members(user_id);

-- ============================================================================
-- 30. Vòng đời tài khoản do trung tâm cấp (2026-08-27)
-- ============================================================================
-- Đổi chính sách sản phẩm: BỎ TỰ ĐĂNG KÝ. Học viên đăng ký học ở TopHSA, trung
-- tâm lấy email/số điện thoại đó tạo tài khoản và đưa mật khẩu tạm tận tay.
-- Nhờ vậy trung tâm biết chính xác ai đang có mặt trong hệ thống — điều không
-- thể có khi bất kỳ ai cũng tự mở được tài khoản.
--
-- Cái giá phải trả: mật khẩu tạm do người khác biết. Nên phải bắt đổi ngay lần
-- đăng nhập đầu tiên, và đó là việc của cột dưới đây.
--
-- Vì sao là cột trên `users` chứ không phải bảng riêng: đây là một trạng thái
-- nhị phân của chính tài khoản, không có lịch sử cần giữ. Một bảng riêng chỉ để
-- chứa một cờ true/false là thêm một phép nối cho mọi lần đăng nhập.
ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN NOT NULL DEFAULT FALSE;

-- Lần đổi mật khẩu gần nhất. Dùng để trả lời câu hỏi vận hành của trung tâm:
-- "tài khoản nào vẫn còn dùng mật khẩu do trợ giảng đặt?" — chưa từng đổi thì
-- cột này NULL.
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP;

-- ============================================================================
-- 31. Định danh đăng nhập & vòng đời tài khoản (2026-08-30)
-- ============================================================================
-- LỖI ĐANG CÓ THẬT, vá bằng khối này: `AdminCreateUserView` lưu email đã hạ chữ
-- thường, còn `LoginView` so khớp NGUYÊN VĂN (`WHERE email=%s`). Trợ giảng nhập
-- 'Nguyen.An@Gmail.com' thì bản lưu là 'nguyen.an@gmail.com'; học viên gõ lại
-- đúng cách mình vẫn viết (bàn phím điện thoại còn tự viết hoa chữ đầu) là
-- Postgres không khớp và trả về "sai mật khẩu" — trong khi tài khoản nằm ngay
-- đó. Từ khi bỏ tự đăng ký thì em đó KHÔNG còn đường nào tự thoát.
--
-- Chỉ mục HÀM chứ không phải chỉ mục cột: có nó thì `WHERE lower(email)=%s`
-- vẫn tra theo chỉ mục. Không có thì mỗi lần đăng nhập quét toàn bảng users.
-- UNIQUE để chính CSDL giữ bất biến, thay vì tin vào một câu kiểm tra trong mã
-- mà chỗ khác quên gọi là lọt.
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower
    ON users(lower(email)) WHERE email IS NOT NULL;

-- Số điện thoại cũng là định danh đăng nhập nên cũng phải duy nhất.
-- HỆ QUẢ VẬN HÀNH, trung tâm cần biết: hai anh em ruột KHÔNG dùng chung được số
-- điện thoại của bố mẹ — em thứ hai phải cấp bằng email. Thà chặn ở đây còn hơn
-- để hai dòng cùng số lọt vào rồi một trong hai em vĩnh viễn không đăng nhập
-- được (câu tra lấy đúng một dòng, em còn lại luôn nhận "sai mật khẩu").
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone
    ON users(phone) WHERE phone IS NOT NULL AND phone <> '';

-- Vòng đời tài khoản. Anh chốt 30/08/2026: học viên nghỉ hoặc học xong thì KHOÁ
-- ĐĂNG NHẬP nhưng GIỮ NGUYÊN dữ liệu học — báo cáo của kỳ đó vẫn phải đọc được.
--
-- Vì sao TEXT chứ không phải BOOLEAN is_active: trung tâm sẽ còn phân biệt "học
-- xong" với "nghỉ giữa chừng" (hai con số hoàn toàn khác nhau khi báo cáo tỉ lệ
-- bỏ học), và có thể thêm "bảo lưu". Một cột TEXT đổi nghĩa được mà không phải
-- chạy lại migration; một cột BOOLEAN thì hết đường.
--
-- KHÁC với class_members.left_at: cột kia nói "rời khỏi LỚP này" (có thể chuyển
-- sang lớp khác, tài khoản vẫn sống). Cột này nói "rời khỏi TRUNG TÂM".
ALTER TABLE users ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';
ALTER TABLE users ADD COLUMN IF NOT EXISTS status_changed_at TIMESTAMP;
-- Vì sao khoá. Trung tâm mở lại tài khoản sau vài tháng mà không có dòng này
-- thì không ai nhớ nổi lý do.
ALTER TABLE users ADD COLUMN IF NOT EXISTS status_note TEXT;

CREATE INDEX IF NOT EXISTS idx_users_status ON users(status) WHERE status <> 'active';

-- ============================================================================
-- 32. Nhật ký kiểm toán (2026-08-30)
-- ============================================================================
-- Đặc tả ERP §9 xếp việc này thứ 5 nhưng ghi rõ "nên chen lên sớm dù nhỏ: rẻ
-- khi làm trước, đắt khi làm sau". Đắt vì nếu để muộn thì mọi hành động đã xảy
-- ra trong khoảng thời gian đó là mất trắng, không dựng lại được từ đâu.
--
-- Phạm vi anh chốt 30/08/2026: chỉ ghi hành động SỬA (tạo/khoá tài khoản, đổi
-- vai trò, đặt lại mật khẩu, thêm/bớt học viên khỏi lớp, điểm danh, sửa điểm).
-- KHÔNG ghi hành động xem — để sau, khi TopHSA chốt chính sách quyền riêng tư
-- (đặc tả §8.3).
CREATE TABLE IF NOT EXISTS admin_audit (
    id           BIGSERIAL PRIMARY KEY,
    -- Ai làm. FK để truy ngược, nhưng CHÉP luôn tên và vai trò tại thời điểm đó
    -- vào hai cột dưới: cùng lý do với learning_events.topic. Xoá tài khoản trợ
    -- giảng cũ đi mà dòng nhật ký trở thành "NULL đã đặt lại mật khẩu của NULL"
    -- thì nhật ký kiểm toán mất sạch giá trị — mà đó lại chính là lúc người ta
    -- cần đọc nó nhất.
    actor_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    actor_name   TEXT,
    actor_role   TEXT,
    -- Động từ dạng máy đọc. DANH SÁCH ĐẦY ĐỦ nằm ở `common/audit.py` (20 hằng)
    -- — KHÔNG chép lại ở đây. Bản chép tay trước đó ghi `user.password` trong
    -- khi hằng thật là `user.password_reset`: một danh sách chép tay là một
    -- danh sách sẽ trôi, và người đọc tin nó rồi thôi không đi kiểm (§20).
    action       TEXT NOT NULL,
    target_type  TEXT,
    -- TEXT chứ không INTEGER: khoá học có id dạng chữ ('dinh-luong'), học viên
    -- thì id số. Một cột phải chứa được cả hai.
    target_id    TEXT,
    target_label TEXT,
    -- Câu tiếng Việt đọc được, dựng sẵn lúc GHI chứ không dựng lúc đọc: dựng
    -- lúc đọc là phải nối lại các bảng mà dữ liệu khi đó đã đổi, và câu chuyện
    -- kể ra sẽ không còn đúng với thời điểm nó xảy ra.
    summary      TEXT,
    detail       JSONB,
    ip           TEXT,
    occurred_at  TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_time ON admin_audit(occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON admin_audit(actor_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_target ON admin_audit(target_type, target_id, occurred_at DESC);

-- ============================================================================
-- 33. Buổi học & điểm danh (2026-08-30) — đặc tả ERP §4
-- ============================================================================
-- Trước khối này, `classes.schedule` mới chỉ là một dòng MÔ TẢ lịch ("Tối 2-4-6")
-- nên không trả lời được câu hỏi vận hành nào: buổi tới học gì, hôm qua ai vắng,
-- em này nghỉ mấy buổi rồi.
--
-- Bản này là GIẢNG VIÊN TICK TAY. Đặc tả §4 đặt câu hỏi cho TopHSA "dạy trên nền
-- tảng nào, có API lấy danh sách người tham dự không" và ghi rằng hai thiết kế
-- khác hẳn nhau — nhưng đó là khác nhau ở chỗ ĐIỀN dữ liệu, không phải ở chỗ
-- CHỨA. Hai bảng này giữ nguyên khi có API; lúc đó chỉ thêm một bộ nhập tự động
-- ghi vào cùng chỗ, và `marked_by` NULL là dấu hiệu "máy điền".
CREATE TABLE IF NOT EXISTS class_sessions (
    id               SERIAL PRIMARY KEY,
    class_id         INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    starts_at        TIMESTAMP NOT NULL,
    duration_minutes INTEGER,
    topic            TEXT,
    -- Các bài trong giáo trình buổi này dạy. JSONB mảng id bài.
    lesson_refs      JSONB,
    meeting_url      TEXT,
    recording_url    TEXT,
    -- planned | done | cancelled
    status           TEXT NOT NULL DEFAULT 'planned',
    -- Sổ đầu bài: giảng viên ghi buổi hôm nay dạy tới đâu, lớp vướng chỗ nào.
    note             TEXT,
    created_by       INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at       TIMESTAMP NOT NULL DEFAULT now(),
    updated_at       TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sessions_class ON class_sessions(class_id, starts_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_time ON class_sessions(starts_at DESC);

CREATE TABLE IF NOT EXISTS attendance (
    session_id INTEGER NOT NULL REFERENCES class_sessions(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    -- present | late | absent | excused
    status     TEXT NOT NULL,
    -- Số phút có mặt, nếu nền tảng họp trả về được. Tick tay thì để NULL.
    minutes    INTEGER,
    note       TEXT,
    -- NULL = máy điền (xem ghi chú ở class_sessions).
    marked_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    marked_at  TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_attendance_user ON attendance(user_id);

-- Từ vựng trạng thái ràng ở CHÍNH CSDL chứ không chỉ trong mã Python. Tầng ứng
-- dụng đã kiểm, nhưng bộ nhập điểm danh tự động sau này (khi TopHSA cho biết
-- nền tảng họp và có API lấy danh sách người tham dự) sẽ ghi thẳng vào bảng —
-- lúc đó câu kiểm trong view không còn nằm trên đường đi. Một dòng status rác
-- không làm hỏng gì ngay: nó chỉ nằm im, không lọt vào ô nào trên màn hình, và
-- lặng lẽ làm sai tỉ lệ chuyên cần mà trung tâm dùng để gọi điện cho phụ huynh.
-- `ADD CONSTRAINT` không có `IF NOT EXISTS`, mà tệp này phải chạy lại được
-- nhiều lần. Dạng DROP-rồi-ADD chứ không phải khối DO: bộ tách câu của bootstrap_schema
-- cắt theo dấu chấm phẩy, mà một khối DO $$ ... $$ có chấm phẩy BÊN TRONG nên
-- bị xé thành từng mảnh vô nghĩa. Hai câu dưới đây đều chạy lại được nhiều lần
-- và không chứa chấm phẩy nào ở giữa.
ALTER TABLE class_sessions DROP CONSTRAINT IF EXISTS chk_session_status;
ALTER TABLE class_sessions ADD CONSTRAINT chk_session_status
    CHECK (status IN ('planned', 'done', 'cancelled'));

ALTER TABLE attendance DROP CONSTRAINT IF EXISTS chk_attendance_status;
ALTER TABLE attendance ADD CONSTRAINT chk_attendance_status
    CHECK (status IN ('present', 'late', 'absent', 'excused'));

-- ============================================================================
-- 34. Chỉ mục cho các câu tra đang quét toàn bảng (audit T12, 30/08/2026)
-- ============================================================================
-- Mỗi chỉ mục dưới đây tương ứng một câu đã EXPLAIN ra Seq Scan hoặc Filter
-- trên đường nóng hằng ngày. Tạo lúc bảng còn nhỏ nên tức thì; để muộn thì
-- chính lệnh tạo sẽ khoá bảng đúng lúc bảng đã lớn.

-- `surveys` không có chỉ mục nào ngoài khoá chính, nên câu "lấy khảo sát mới
-- nhất của em này" đi NGƯỢC chỉ mục khoá chính rồi LỌC — tức duyệt qua mọi
-- khảo sát mới hơn của mọi người khác. Đọc ở stats/plan.py, HsaSummaryView,
-- HsaGoalsView, tức gần như mỗi lần học viên mở trang.
CREATE INDEX IF NOT EXISTS idx_surveys_user ON surveys(user_id);

-- Màn hình nhật ký chạy `SELECT DISTINCT action` MỖI LẦN MỞ chỉ để dựng ô lọc
-- mươi giá trị, và bộ lọc `WHERE action=%s` hiện là Filter chứ không phải
-- Index Cond — duyệt dọc chỉ mục thời gian tới khi gom đủ một trang. Chỉ mục
-- ghép này giải quyết cả hai.
CREATE INDEX IF NOT EXISTS idx_audit_action ON admin_audit(action, occurred_at DESC);

-- Ô tìm kiếm tài khoản dùng `LIKE '%...%'` trên tên/email/số điện thoại. Không
-- chỉ mục B-tree nào phục vụ được dạng đó (đã kiểm: ép enable_seqscan=off vẫn
-- ra Seq Scan). pg_trgm đã cài sẵn cho `courses`; dùng cùng cách ở đây.
-- pg_stat cho thấy `users` đã có 3.181 lần quét tuần tự.
-- Chỉ mục phải khớp ĐÚNG biểu thức trong câu tra. `build_user_filters` viết
-- `lower(u.name) LIKE %s`, nên chỉ mục trigram đặt trên `name` trần KHÔNG dùng
-- được — đã đo: ép enable_seqscan=off vẫn ra Seq Scan. Đặt trên `lower(...)`.
-- Cột `phone` thì câu tra dùng trần nên chỉ mục cũng để trần.
CREATE INDEX IF NOT EXISTS idx_users_name_trgm
    ON users USING gin (lower(name) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_users_email_trgm
    ON users USING gin (lower(email) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_users_phone_trgm
    ON users USING gin (phone gin_trgm_ops);

-- Khoá ngoại ON DELETE CASCADE mà KHÔNG có chỉ mục: mỗi lần xoá một dòng
-- `quizzes` là một lần quét toàn bộ bảng con.
CREATE INDEX IF NOT EXISTS idx_rqr_quiz ON review_quiz_results(quiz_id);
CREATE INDEX IF NOT EXISTS idx_quizzes_user_course ON quizzes(user_id, course_id);

CREATE INDEX IF NOT EXISTS idx_notifications_user_time
    ON notifications(user_id, created_at DESC);

-- ============================================================================
-- 35. Bất biến ở tầng CSDL (audit T42, 2026-08-31)
-- ============================================================================
-- Lược đồ này đang bất nhất với CHÍNH NÓ: `class_sessions.status` và
-- `attendance.status` có CHECK, nhưng ba cột khoá quyền — `users.role`,
-- `users.status`, `classes.status` — thì TEXT tự do. Hậu quả không đối xứng:
--   · `users.role` gõ sai một dấu ('Giang viên') thì mọi phép kiểm vai đều trả
--     false, giảng viên mất sạch quyền vào khu Giảng dạy mà không câu lỗi nào.
--   · `users.status` gõ sai thì `User.is_active` trả false (nó so BẰNG với
--     'active'), tức KHOÁ TÀI KHOẢN — hỏng theo hướng nguy hơn hẳn.
-- Ràng buộc ở tầng ứng dụng không cứu được: `manage.py shell`, lệnh nạp dữ
-- liệu, và mọi câu UPDATE viết tay đều đi vòng qua nó.
--
-- Đã đo trên dữ liệu thật 31/08/2026 trước khi thêm: role có đúng ba giá trị
-- ('admin', 'Giảng viên', 'Học viên' — khớp ASSIGNABLE_ROLES), status và
-- classes.status đều chỉ có 'active'. Không dòng nào vi phạm.
--
-- CHÚ Ý HÌNH DẠNG: bootstrap_schema NÉM LỖI ở câu đầu tiên hỏng và chạy trong
-- buildCommand của Render, nên mọi câu dưới đây phải chạy lại được. ALTER TABLE
-- ADD CONSTRAINT không có IF NOT EXISTS, nên dùng cặp DROP IF EXISTS + ADD.
-- (Không dùng khối DO $$...$$ được: bộ tách câu cắt theo dấu chấm phẩy.)

-- Thêm 'Quản lý học vụ' và 'Trợ giảng' ngày 01/09/2026. Danh sách này PHẢI
-- khớp `ASSIGNABLE_ROLES` trong `common/permissions.py` — hai nơi lệch nhau thì
-- một vai trò mới đi qua tầng Python rồi đổ ở CSDL, và câu báo lỗi là
-- `users_role_check` chứ không phải một câu người dùng hiểu được.
-- (Đúng lỗi đã mắc hôm nay: thêm hằng ở Python, quên `CHECK` ở đây.)
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users ADD CONSTRAINT users_role_check
    CHECK (role IN ('admin', 'Quản lý học vụ', 'Giảng viên', 'Trợ giảng', 'Học viên'));

ALTER TABLE users DROP CONSTRAINT IF EXISTS users_status_check;
ALTER TABLE users ADD CONSTRAINT users_status_check
    CHECK (status IN ('active', 'suspended'));

-- 'finished' và 'cancelled' chưa có dòng nào dùng, nhưng để sẵn vì lớp kết thúc
-- và lớp huỷ là hai con số khác nhau khi trung tâm báo tỉ lệ — cùng lý do đã
-- ghi cho `class_members.leave_reason` ở §36.
ALTER TABLE classes DROP CONSTRAINT IF EXISTS classes_status_check;
ALTER TABLE classes ADD CONSTRAINT classes_status_check
    CHECK (status IN ('active', 'finished', 'cancelled'));

-- ── Khoá ngoại còn thiếu ────────────────────────────────────────────────────
-- Năm bảng dưới đây trỏ tới `users`/`courses`/`lessons` mà KHÔNG có khoá ngoại,
-- nên xoá một tài khoản là bỏ lại tiến độ, khảo sát và đánh giá không chủ.
-- Đã đo 31/08/2026: bốn bảng đầu SẠCH (0 dòng mồ côi), nên thêm được ngay.
ALTER TABLE enrollments DROP CONSTRAINT IF EXISTS enrollments_user_fk;
ALTER TABLE enrollments ADD CONSTRAINT enrollments_user_fk
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE enrollments DROP CONSTRAINT IF EXISTS enrollments_course_fk;
ALTER TABLE enrollments ADD CONSTRAINT enrollments_course_fk
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE;

ALTER TABLE lesson_progress DROP CONSTRAINT IF EXISTS lesson_progress_user_fk;
ALTER TABLE lesson_progress ADD CONSTRAINT lesson_progress_user_fk
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE lesson_progress DROP CONSTRAINT IF EXISTS lesson_progress_lesson_fk;
ALTER TABLE lesson_progress ADD CONSTRAINT lesson_progress_lesson_fk
    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE;

ALTER TABLE course_ratings DROP CONSTRAINT IF EXISTS course_ratings_user_fk;
ALTER TABLE course_ratings ADD CONSTRAINT course_ratings_user_fk
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE course_ratings DROP CONSTRAINT IF EXISTS course_ratings_course_fk;
ALTER TABLE course_ratings ADD CONSTRAINT course_ratings_course_fk
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE;

ALTER TABLE roadmap_progress DROP CONSTRAINT IF EXISTS roadmap_progress_user_fk;
ALTER TABLE roadmap_progress ADD CONSTRAINT roadmap_progress_user_fk
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- `surveys` là bảng DUY NHẤT còn dòng mồ côi: id=4 trỏ user_id=10, tài khoản đó
-- không tồn tại. Thêm khoá ngoại thường ở đây sẽ LÀM GÃY DEPLOY, vì Postgres
-- kiểm toàn bảng lúc tạo ràng buộc.
--
-- NOT VALID là lối thoát đúng: ràng buộc có hiệu lực NGAY với mọi dòng ghi mới
-- (tức từ giây phút này không đẻ thêm được dòng mồ côi nào nữa), chỉ bỏ qua
-- việc soi lại dữ liệu cũ. Dòng cũ vẫn nằm đó chờ người quyết định — xoá hẳn
-- hay giữ lại là quyết định về DỮ LIỆU THẬT, không phải việc lược đồ tự làm.
-- Dọn xong thì chạy tay MỘT lần:
--     ALTER TABLE surveys VALIDATE CONSTRAINT surveys_user_fk
ALTER TABLE surveys DROP CONSTRAINT IF EXISTS surveys_user_fk;
ALTER TABLE surveys ADD CONSTRAINT surveys_user_fk
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE NOT VALID;

-- Khoá ngoại ON DELETE CASCADE mà không có chỉ mục bên con thì mỗi lần xoá một
-- tài khoản là một lần quét toàn bảng (cùng lỗi đã vá ở §34 cho review_quiz).
--
-- SỬA 01/09/2026 — LUẬT ĐÚNG, ÁP SAI CHỖ. Bản đầu của khối này tạo năm chỉ mục;
-- BỐN trong số đó đã có sẵn, vì khoá chính của các bảng ấy là khoá GHÉP dẫn đầu
-- bằng `user_id`, và chỉ mục của khoá chính phục vụ luôn `WHERE user_id = ?`:
--
--     enrollments      PRIMARY KEY (user_id, course_id)
--     course_ratings   PRIMARY KEY (user_id, course_id)
--     lesson_progress  PRIMARY KEY (user_id, lesson_id)
--     roadmap_progress PRIMARY KEY (user_id, roadmap_id, item_id)
--     surveys          PRIMARY KEY (id)            ← chỉ bảng NÀY thiếu thật
--
-- Không kiểm khoá chính trước khi thêm là cách một luật đúng đẻ ra việc thừa:
-- mỗi chỉ mục thừa là một cây B-tree phải ghi thêm ở MỌI lần INSERT/UPDATE của
-- bảng, đổi lấy đúng không gì.
--
-- Còn `surveys` thì cần thật — nhưng nó ĐÃ được tạo ở §33 phía trên, kèm đủ lý
-- lẽ (khoá chính là `id`, nên "khảo sát mới nhất của em này" phải duyệt qua
-- khảo sát của mọi người khác). Khai lại ở đây là bản thứ hai của cùng một
-- dòng: `IF NOT EXISTS` khiến nó vô hại khi CHẠY, nhưng người đọc gặp hai lần
-- sẽ không biết bản nào là bản có lý do.

-- DỌN 6 CHỈ MỤC THỪA — CẦN DUYỆT TRƯỚC KHI CHẠY.
--
-- Bốn cái §35 tạo nhầm ở trên, cộng hai cái đã trùng sẵn từ §8/§9 (cùng bảng,
-- cùng cột, khác tên, nên `IF NOT EXISTS` không đỡ được):
--
--     enrollments     (user_id) → PK + idx_enrollments_user + idx_enrollments_user_id
--     course_ratings  (user_id) → PK + idx_course_ratings_user + idx_course_ratings_user_id
--
-- KHÔNG đặt câu DROP vào tệp này để `bootstrap_schema` tự chạy: tệp này chạy ở
-- buildCommand của Render trên CSDL THẬT, và luật của repo là chỉ DDL THÊM mới
-- được tự động (RULES). Bỏ một chỉ mục là việc bỏ đi được nhưng phải có người
-- gật đầu. Duyệt xong thì chạy tay MỘT lần:
--
--     DROP INDEX IF EXISTS idx_enrollments_user;
--     DROP INDEX IF EXISTS idx_enrollments_user_id;
--     DROP INDEX IF EXISTS idx_course_ratings_user;
--     DROP INDEX IF EXISTS idx_course_ratings_user_id;
--     DROP INDEX IF EXISTS idx_lesson_progress_user;
--     DROP INDEX IF EXISTS idx_roadmap_progress_user;
--
-- GIỮ LẠI: idx_enrollments_course_id và idx_course_ratings_course_id. `course_id`
-- là cột THỨ HAI của khoá ghép nên khoá chính KHÔNG phục vụ được nó.

-- ============================================================================
-- 36. Đợt học, và một học viên học lại lớp cũ (audit T43, 2026-08-31)
-- ============================================================================
-- Làm HÔM NAY vì đây là hai thay đổi kiến trúc duy nhất mà chi phí chỉ tăng
-- theo thời gian. Đo lúc làm: classes = 1 dòng, class_members = 4,
-- learning_events = 37. Có 100 học viên rồi thì đây thành việc di trú thật.
--
-- ── Vì sao PHẢI bỏ khoá chính (class_id, user_id) ───────────────────────────
-- Khoá đó cho đúng MỘT dòng cho mỗi cặp lớp–người. Nên khi một em học lại lớp
-- cũ ở đợt sau, đường thêm vào lớp chạy `ON CONFLICT (class_id, user_id) DO
-- UPDATE SET left_at = NULL` — tức là XOÁ TRẮNG mốc rời lớp lần trước. Lượt học
-- cũ biến mất vĩnh viễn, không có bản sao nào.
--
-- Điều đó đi thẳng ngược lại §29, chỗ đã chốt rằng học viên rời lớp thì GIỮ
-- NGUYÊN dữ liệu học vì trung tâm cần đọc lại chính những báo cáo ấy. Giữ dữ
-- liệu của người đã rời mà lại xoá lịch sử của người quay lại là bất nhất.
--
-- Cách vá: khoá chính thành cột `id` thay thế, còn "mỗi lớp một người chỉ được
-- ĐANG HỌC một lần" chuyển thành CHỈ MỤC DUY NHẤT MỘT PHẦN. Vế `WHERE left_at
-- IS NULL` chính là chỗ mở ra cho nhiều lượt học nối tiếp: dòng đã rời lớp
-- không nằm trong chỉ mục nên không chặn dòng mới.
--
-- Thứ tự bốn câu dưới đây là cố ý — dựng chỉ mục duy nhất TRƯỚC khi bỏ khoá
-- chính, để không có khoảnh khắc nào bảng mất hàng rào chống trùng.

ALTER TABLE class_members ADD COLUMN IF NOT EXISTS id SERIAL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_class_members_dang_hoc
    ON class_members(class_id, user_id) WHERE left_at IS NULL;
ALTER TABLE class_members DROP CONSTRAINT IF EXISTS class_members_pkey;
ALTER TABLE class_members ADD CONSTRAINT class_members_pkey PRIMARY KEY (id);

-- "Học xong" và "bỏ giữa chừng" hiện là CÙNG một trạng thái: `left_at` có giá
-- trị. Nhưng đó là hai con số hoàn toàn khác nhau khi trung tâm báo tỉ lệ bỏ
-- học cho một đợt — gộp lại thì mọi lớp kết thúc đều trông như bỏ học 100%.
-- §31 đã nhận ra đúng điều này cho `users.status` rồi tách ra; lý lẽ đó chưa
-- được áp cho chỗ này.
-- NULL = chưa rời lớp. 'transferred' = chuyển sang lớp khác, không phải bỏ.
ALTER TABLE class_members ADD COLUMN IF NOT EXISTS leave_reason TEXT;
ALTER TABLE class_members DROP CONSTRAINT IF EXISTS class_members_leave_reason_check;
ALTER TABLE class_members ADD CONSTRAINT class_members_leave_reason_check
    CHECK (leave_reason IS NULL OR leave_reason IN ('completed', 'dropped', 'transferred'));

-- ── Đợt học ─────────────────────────────────────────────────────────────────
-- Chưa có khái niệm ĐỢT, nên "đợt 1/2027 so với đợt 2/2027" phải suy từ
-- `starts_on` và ĐỌC TÊN LỚP. Đó đúng là cái bẫy Moodle mắc rồi phải vá bằng
-- lồng thư mục: khi thông tin nghiệp vụ chỉ nằm trong một chuỗi tự do, mọi báo
-- cáo về sau đều phải đoán lại nó, và đoán sai thì không ai biết.
--
-- MỘT TẦNG, cố ý. openSIS lồng bốn tầng (năm học → học kỳ → kỳ nhỏ → đợt) cho
-- trường phổ thông; một trung tâm luyện thi mở lớp theo mùa thi thì tầng thứ
-- hai đã là chỗ để trống. Thêm tầng sau này rẻ hơn nhiều so với gỡ tầng thừa.
CREATE TABLE IF NOT EXISTS terms (
    id         SERIAL PRIMARY KEY,
    code       TEXT,
    name       TEXT NOT NULL,
    starts_on  DATE,
    ends_on    DATE,
    -- Ngày thi của đợt. Lớp vẫn có `exam_date` riêng vì một đợt có thể ôn cho
    -- hai đợt thi khác nhau; cột ở đây là mặc định, không phải luật.
    exam_date  DATE,
    status     TEXT NOT NULL DEFAULT 'active',
    note       TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
ALTER TABLE terms DROP CONSTRAINT IF EXISTS terms_status_check;
ALTER TABLE terms ADD CONSTRAINT terms_status_check
    CHECK (status IN ('active', 'finished', 'cancelled'));
CREATE UNIQUE INDEX IF NOT EXISTS idx_terms_code ON terms(code) WHERE code IS NOT NULL;

-- Cho phép NULL: lớp đã có từ trước đợt này chưa thuộc đợt nào, và ép chúng vào
-- một đợt bịa ra thì con số của đợt đó sai ngay từ đầu.
ALTER TABLE classes ADD COLUMN IF NOT EXISTS term_id INTEGER;
ALTER TABLE classes DROP CONSTRAINT IF EXISTS classes_term_fk;
ALTER TABLE classes ADD CONSTRAINT classes_term_fk
    FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_classes_term ON classes(term_id);

-- ============================================================================
-- 37. Ai đã điểm danh buổi này, và lúc nào (audit T44, 2026-08-31)
-- ============================================================================
-- Hôm nay "buổi X không có dòng `attendance` nào" MƠ HỒ giữa hai chuyện khác
-- hẳn nhau: cả lớp có mặt (giảng viên tick xong, không ai vắng nên không dòng
-- nào khác 'present'... thực ra vẫn có dòng) và giảng viên QUÊN tick. Không
-- phân biệt được thì không dựng nổi báo cáo "hôm nay ai chưa điểm danh" — thứ
-- một trung tâm cần mỗi tối.
--
-- openSIS chống lưng chỗ này bằng hẳn một bảng `attendance_completed`. Ở đây
-- hai cột là đủ, vì quan hệ là một-một với buổi học.
ALTER TABLE class_sessions ADD COLUMN IF NOT EXISTS attendance_taken_at TIMESTAMP;
ALTER TABLE class_sessions ADD COLUMN IF NOT EXISTS attendance_taken_by INTEGER;
ALTER TABLE class_sessions DROP CONSTRAINT IF EXISTS class_sessions_taken_by_fk;
ALTER TABLE class_sessions ADD CONSTRAINT class_sessions_taken_by_fk
    FOREIGN KEY (attendance_taken_by) REFERENCES users(id) ON DELETE SET NULL;

-- ============================================================================
-- 38. Giao bài & chấm tay (đặc tả ERP §5, 2026-08-31)
-- ============================================================================
-- Tới hôm nay hệ thống chỉ chấm được TRẮC NGHIỆM. Một trung tâm luyện thi HSA
-- cần giao bài tự luận, đặc biệt phần Định tính — và đó là phần duy nhất không
-- có cách nào chấm tự động.
--
-- VÌ SAO LÀM ĐƯỢC DÙ CHƯA CÓ CÂU TRẢ LỜI CỦA TopHSA. Đặc tả §5 để ngỏ ba câu:
-- có chấm tự luận không, thang điểm nào, ai chấm (giảng viên hay trợ giảng).
-- Không câu nào trong ba câu đó đổi HÌNH DẠNG dữ liệu:
--   · "có chấm tự luận không" → đổi việc bảng này CÓ ĐƯỢC DÙNG hay không;
--   · "thang điểm nào"        → `max_score` là số, mỗi bài tự khai thang của nó;
--   · "ai chấm"               → đổi PHÂN QUYỀN ở tầng view, không đổi cột nào.
-- Nên dựng bây giờ là an toàn, và chờ thì chỉ mất thời gian.
--
-- ĐIỂM TỰ LUẬN VÀO THẲNG BẢN ĐỒ NĂNG LỰC. Chấm xong đẻ một `learning_events`
-- với `kind='assignment'` và `topic` của bài — không cần luật tính riêng, vì
-- bản đồ năng lực vốn đọc từ dòng sự kiện chứ không đọc từ bảng nguồn. Đây
-- chính là lợi tức của kỷ luật một-cửa ở `common/events.py`.

CREATE TABLE IF NOT EXISTS assignments (
    id          SERIAL PRIMARY KEY,
    class_id    INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    description TEXT,
    -- Chương mục bài này thuộc về. Đây là thứ khiến điểm chấm tay vào được bản
    -- đồ năng lực đúng ô; để trống thì bài vẫn giao được nhưng điểm chỉ vào sổ
    -- điểm, không vào năng lực.
    topic       TEXT,
    -- Khoá học của chủ đề. Cần vì một chủ đề như "Chiến thuật" xuất hiện ở CẢ
    -- BA hợp phần (xem §26) — thiếu cột này thì không biết ô nào trên bản đồ.
    course_id   TEXT REFERENCES courses(id) ON DELETE SET NULL,
    due_at      TIMESTAMP,
    -- Thang điểm của RIÊNG bài này. Trung tâm chấm thang 10 hay thang 100 là
    -- việc của họ; hệ thống quy về phần trăm khi ghi sự kiện.
    max_score   NUMERIC(6,2) NOT NULL DEFAULT 10,
    attachment_url TEXT,
    -- draft: đang soạn, học viên chưa thấy · open: đã giao · closed: hết hạn nộp
    status      TEXT NOT NULL DEFAULT 'open',
    created_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT now(),
    updated_at  TIMESTAMP
);
ALTER TABLE assignments DROP CONSTRAINT IF EXISTS assignments_status_check;
ALTER TABLE assignments ADD CONSTRAINT assignments_status_check
    CHECK (status IN ('draft', 'open', 'closed'));
ALTER TABLE assignments DROP CONSTRAINT IF EXISTS assignments_max_score_check;
ALTER TABLE assignments ADD CONSTRAINT assignments_max_score_check
    CHECK (max_score > 0);
CREATE INDEX IF NOT EXISTS idx_assignments_class ON assignments(class_id, due_at DESC);

CREATE TABLE IF NOT EXISTS submissions (
    assignment_id INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    submitted_at  TIMESTAMP,
    content       TEXT,
    file_url      TEXT,
    score         NUMERIC(6,2),
    feedback      TEXT,
    graded_by     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    graded_at     TIMESTAMP,
    PRIMARY KEY (assignment_id, user_id)
);
-- Khoá chính (assignment_id, user_id) là ĐÚNG ở đây, khác hẳn `class_members`
-- (§36 phải bỏ khoá kép để cho phép nhiều lượt học). Lý do: một bài tập chỉ nộp
-- một lần; nộp lại là SỬA bài nộp đó, không phải một lượt nộp mới. Lịch sử sửa
-- không cần giữ vì `graded_at`/`graded_by` đã trả lời "ai chấm, lúc nào", còn
-- nội dung cũ thì không ai đọc lại.
CREATE INDEX IF NOT EXISTS idx_submissions_user ON submissions(user_id);
-- Câu "bài nào còn chưa chấm" là câu giảng viên hỏi mỗi tối.
CREATE INDEX IF NOT EXISTS idx_submissions_chua_cham
    ON submissions(assignment_id) WHERE graded_at IS NULL;


-- ─────────────────────────────────────────────────────────────────────────
-- §39 · Thu hồi phiên khi mật khẩu đổi (T67, 31/08/2026)
-- ─────────────────────────────────────────────────────────────────────────
--
-- Trợ giảng bấm "Đặt lại mật khẩu" vì nghi tài khoản học viên bị người khác
-- dùng. Trước cột này, token cũ VẪN SỐNG: người đang chiếm tài khoản thao tác
-- bình thường cho tới khi access token hết hạn (30 phút). Nút ấy không làm được
-- đúng việc mà người bấm nghĩ nó làm.
--
-- VÌ SAO KHÔNG DÙNG LẠI `password_changed_at`. Cột đó đã mang một nghĩa KHÁC và
-- đang được đọc: `password_changed_at IS NULL` = "tài khoản vẫn dùng mật khẩu
-- tạm do trợ giảng đặt" (xem `teaching/exports.py`). Chính đường đặt lại mật
-- khẩu SET nó về NULL — tức đúng lúc ta cần ghi một mốc thì nó phải bị xoá.
-- Nhồi hai nghĩa vào một cột là cách chắc chắn để một trong hai nghĩa sai.
--
-- VÌ SAO KHÔNG CHỈ DỰA VÀO DANH SÁCH ĐEN CỦA SimpleJWT. Danh sách đen chỉ chặn
-- được REFRESH token; ACCESS token được kiểm bằng chữ ký chứ không tra CSDL,
-- nên nó vẫn sống đủ 30 phút. Cột này cho phép từ chối cả access token bằng
-- cách so `iat` của token với mốc ở đây.
--
-- NULL = chưa từng thu hồi, mọi token còn hạn đều hợp lệ. Đó là trạng thái của
-- toàn bộ tài khoản hiện có, nên thêm cột này không đá ai ra ngoài.
ALTER TABLE users ADD COLUMN IF NOT EXISTS tokens_valid_from TIMESTAMP;


-- ─────────────────────────────────────────────────────────────────────────
-- §40 · Câu trả lời ĐÃ GHI NHẬN của một lượt học (A12, 31/08/2026)
-- ─────────────────────────────────────────────────────────────────────────
--
-- Bản vá sáng 31/08 chuyển việc chấm về máy chủ, nhưng vẫn để `/complete` chấm
-- trên CÂU TRẢ LỜI TRONG THÂN REQUEST. Kết hợp với `/check` — nơi trả đáp án
-- đúng cho mọi câu có mặt trong `answers` — thì cả bản vá đi vòng được bằng hai
-- request:
--
--   1. POST .../check {"phan":"drill","answers":{"d1":"x", … ,"d8":"x"}}
--      → nhận trọn 8 đáp án (sai hết thì cũng vẫn nhận, đó là chỗ hở)
--   2. POST /api/lessons/N/complete với đúng 8 đáp án vừa lấy
--      → 8/8, 120 XP phòng luyện, và một dòng bản đồ năng lực 8/8
--
-- Cột này khiến câu trả lời trở thành thứ ĐÃ CHỐT chứ không phải thứ gửi kèm:
-- `/check` GHI NHẬN câu trả lời lần đầu cho từng câu (lần sau cho cùng câu đó
-- không ghi đè), và `/complete` chấm trên phần đã ghi nhận. Ai xem đáp án bằng
-- cách gửi bừa thì con số bừa ấy chính là bài làm của họ.
--
-- Dạng: {"test": {"t1": "…"}, "drill": {"d1": "…"}}. Xoá về NULL khi
-- `/complete` chạy xong, để lần học lại bài đó bắt đầu từ giấy trắng.
--
-- NULL = chưa ghi nhận câu nào. Đó là trạng thái của toàn bộ dòng hiện có, nên
-- thêm cột này không đổi hành vi của một ai.
ALTER TABLE lesson_progress ADD COLUMN IF NOT EXISTS answers_json JSONB;

-- ─────────────────────────────────────────────────────────────────────────
-- §41 · `notification_settings` là bảng nghiệp vụ DUY NHẤT không có khoá ngoại
-- ─────────────────────────────────────────────────────────────────────────
--
-- Phát hiện khi trích ERD THẬT từ `information_schema` (01/09/2026) để vẽ sơ đồ
-- kiến trúc: 38 bảng nghiệp vụ, 56 khoá ngoại, và đúng một bảng đứng ngoài lưới.
--
-- Nó CÓ khoá chính trên `user_id` nên không đẻ dòng trùng, nhưng không có khoá
-- ngoại nên xoá một tài khoản là bỏ lại một dòng mồ côi vĩnh viễn — và mọi bảng
-- anh em của nó (`notifications`, `study_logs`, `topic_self_marks`…) đều đã
-- `ON DELETE CASCADE`. Một bảng lệch khỏi lưới là một bảng không ai nghĩ tới
-- lúc dọn dữ liệu.
--
-- Đo trước khi thêm: 0 dòng mồ côi (2 dòng, cả hai trỏ tới tài khoản có thật).
-- `NOT VALID` giữ đúng lối của §33: có hiệu lực NGAY với dòng ghi mới, không
-- soi lại dữ liệu cũ.
ALTER TABLE notification_settings DROP CONSTRAINT IF EXISTS notification_settings_user_fk;
ALTER TABLE notification_settings ADD CONSTRAINT notification_settings_user_fk
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE NOT VALID;


-- §42 · `roadmaps` còn `NO ACTION` — nó CHẶN xoá tài khoản
-- ─────────────────────────────────────────────────────────────────────────────
--
-- Phát hiện khi trích ERD (01/09/2026).
--
-- ĐÍNH CHÍNH (kiểm định 01/09/2026, cuối ngày). Mục này ban đầu viết "9 khoá
-- ngoại NO ACTION, 7 thuộc Django, của mình đúng HAI" — và tiêu đề gọi
-- `roadmaps` là bảng DUY NHẤT của mình còn NO ACTION. Đếm lại bằng
-- `pg_catalog`, phân loại theo tiền tố bảng của Django:
--
--     69 khoá ngoại   ·  57 của mình  ·  12 của Django
--     16 NO ACTION    ·   4 của mình  ·  12 của Django
--
-- Tức con số cũ sai ở CẢ HAI vế, và hai khoá bị bỏ sót — `courses.instructor_id`
-- và `missions.course_id` — được xử ở §43. Mỉa mai là chính đoạn viết sai ấy
-- kết bằng câu "một con số sai trong tài liệu thì tệ hơn không có con số".
-- Bài học không phải "đếm cẩn thận hơn" mà là: đừng đếm bằng mắt trên một danh
-- sách đã lọc sẵn, hãy để CSDL tự phân loại.
--
-- Hai khoá của `roadmaps`:
--
--   · `user_id` → CASCADE. Lộ trình cá nhân không còn nghĩa gì khi chủ nó biến
--     mất, và 43 khoá anh em đều đã CASCADE. Bảng này dùng `user_id IS NULL` để
--     đánh dấu MẪU (xem mục 5 ở đầu tệp), nên mẫu không bị đụng tới: 3 dòng cá
--     nhân, 1 dòng mẫu.
--   · `generated_from_survey_id` → SET NULL. Đây là XUẤT XỨ, không phải danh
--     tính: xoá bản khảo sát thì lộ trình vẫn còn giá trị, chỉ mất đường truy
--     ngược. Cột đã cho phép NULL nên không phải đổi kiểu.
--
-- Vì sao đáng sửa khi CHƯA có đường xoá tài khoản nào trong mã: ngày dựng đường
-- ấy, `NO ACTION` không báo lỗi lúc viết mã mà báo lúc CHẠY, trên tài khoản thật,
-- giữa chừng một thao tác đã xoá xong nửa số bảng khác.
--
-- Đo trước khi đổi: 0 dòng mồ côi ở cả hai cột (4 dòng `roadmaps`, 5 dòng
-- `surveys`). `NOT VALID` giữ đúng lối của §33/§41: có hiệu lực NGAY với dòng
-- ghi mới, không soi lại dữ liệu cũ.
ALTER TABLE roadmaps DROP CONSTRAINT IF EXISTS roadmaps_user_id_fkey;
ALTER TABLE roadmaps ADD CONSTRAINT roadmaps_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE NOT VALID;

ALTER TABLE roadmaps DROP CONSTRAINT IF EXISTS roadmaps_generated_from_survey_id_fkey;
ALTER TABLE roadmaps ADD CONSTRAINT roadmaps_generated_from_survey_id_fkey
    FOREIGN KEY (generated_from_survey_id) REFERENCES surveys(id) ON DELETE SET NULL NOT VALID;


-- §43 · Chỉ mục cho MỌI khoá ngoại, và hai chính sách xoá còn sót
-- ─────────────────────────────────────────────────────────────────────────────
--
-- Kiểm định 01/09/2026. Đo bằng `pg_catalog`, không đọc tệp này: với mỗi khoá
-- ngoại, hỏi xem có chỉ mục nào lấy đúng cột ấy làm cột DẪN ĐẦU không.
--
--     19 / 69 khoá ngoại không có.
--
-- VÌ SAO ĐÁNG SỬA. Postgres không tự tạo chỉ mục cho phía CON của khoá ngoại
-- (phía CHA thì có, vì nó phải là khoá chính hoặc unique). Nên mỗi lần xoá một
-- dòng CHA, nó phải quét TOÀN BỘ bảng con để tìm dòng cần dọn — kể cả với
-- `NO ACTION`, vì vẫn phải kiểm là không còn ai tham chiếu.
--
-- Xoá MỘT tài khoản hiện chạm mười bảng như thế: comment_likes, post_likes,
-- user_follows, attendance.marked_by, class_sessions ×2, submissions.graded_by,
-- assignments.created_by, courses.instructor_id, roadmaps.user_id.
--
-- LÀM HÔM NAY, KHÔNG ĐỂ SAU. Bảng còn nhỏ nên `CREATE INDEX` xong tức thì. Để
-- tới lúc có 100 học viên thì chính lệnh tạo sẽ khoá bảng đúng lúc bảng đã lớn
-- — cùng lý lẽ đã ghi ở §33.
--
-- ĐÃ HỌC TỪ §35: mục ấy thêm năm chỉ mục theo đúng luật này mà không xem khoá
-- chính, và bốn trong năm đã có sẵn (khoá chính GHÉP dẫn đầu bằng `user_id`).
-- Phép đo ở đây hỏi thẳng `indkey[0]`, nên chỉ mục khoá chính được tính — 19
-- cột dưới đây là 19 cột thật sự không có.

CREATE INDEX IF NOT EXISTS idx_assignments_course     ON assignments(course_id);
CREATE INDEX IF NOT EXISTS idx_assignments_created_by ON assignments(created_by);
CREATE INDEX IF NOT EXISTS idx_attendance_marked_by   ON attendance(marked_by);
CREATE INDEX IF NOT EXISTS idx_sessions_taken_by      ON class_sessions(attendance_taken_by);
CREATE INDEX IF NOT EXISTS idx_sessions_created_by    ON class_sessions(created_by);
CREATE INDEX IF NOT EXISTS idx_classes_course         ON classes(course_id);
CREATE INDEX IF NOT EXISTS idx_comment_likes_user     ON comment_likes(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent        ON comments(parent_comment_id);
CREATE INDEX IF NOT EXISTS idx_courses_instructor     ON courses(instructor_id);
CREATE INDEX IF NOT EXISTS idx_lesson_progress_lesson ON lesson_progress(lesson_id);
CREATE INDEX IF NOT EXISTS idx_missions_course        ON missions(course_id);
CREATE INDEX IF NOT EXISTS idx_post_likes_user        ON post_likes(user_id);
CREATE INDEX IF NOT EXISTS idx_quizzes_course         ON quizzes(course_id);
CREATE INDEX IF NOT EXISTS idx_roadmaps_survey        ON roadmaps(generated_from_survey_id);
CREATE INDEX IF NOT EXISTS idx_roadmaps_user          ON roadmaps(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_graded_by  ON submissions(graded_by);
CREATE INDEX IF NOT EXISTS idx_user_achievements_ach  ON user_achievements(achievement_id);
CREATE INDEX IF NOT EXISTS idx_user_follows_followee  ON user_follows(followee_id);
CREATE INDEX IF NOT EXISTS idx_user_missions_mission  ON user_missions(mission_id);

-- ── Hai chính sách xoá mà §42 bỏ sót ────────────────────────────────────────
--
-- `courses.instructor_id` → SET NULL, KHÔNG phải CASCADE.
--   CASCADE ở đây nghĩa là xoá tài khoản một giảng viên thì XOÁ LUÔN khoá học
--   họ đứng tên, kéo theo mọi lớp, buổi và điểm danh treo dưới nó. Khoá học là
--   tài sản của trung tâm, không phải của người dạy. Cột đã cho phép NULL.
--   Để nguyên `NO ACTION` cũng không được: nó khiến việc xoá BÁO LỖI ngay giữa
--   chừng một thao tác đã dọn xong nửa số bảng khác — nghĩa là hôm nay không
--   xoá nổi tài khoản một giảng viên đang đứng tên bất kỳ khoá nào.
--
-- `missions.course_id` → CASCADE.
--   Nhiệm vụ gắn với một khoá ("học 3 bài trong Định lượng") mất hết nghĩa khi
--   khoá biến mất. SET NULL thì tệ hơn hẳn: cột NULL ở bảng này mang nghĩa
--   "nhiệm vụ TOÀN CỤC", nên xoá một khoá sẽ lặng lẽ biến nhiệm vụ riêng của nó
--   thành nhiệm vụ giao cho mọi học viên.
--
-- Đo trước khi đổi: `courses` 3 dòng, `instructor_id` NULL cả 3, 0 mồ côi;
-- `missions` 3 dòng, `course_id` NULL cả 3, 0 mồ côi. `NOT VALID` giữ đúng lối
-- của §33/§41/§42.
ALTER TABLE courses DROP CONSTRAINT IF EXISTS courses_instructor_id_fkey;
ALTER TABLE courses ADD CONSTRAINT courses_instructor_id_fkey
    FOREIGN KEY (instructor_id) REFERENCES users(id) ON DELETE SET NULL NOT VALID;

ALTER TABLE missions DROP CONSTRAINT IF EXISTS missions_course_id_fkey;
ALTER TABLE missions ADD CONSTRAINT missions_course_id_fkey
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE NOT VALID;

-- ── TỆP NÀY ĐANG ĐI TRƯỚC CSDL THẬT ─────────────────────────────────────────
--
-- Đo 01/09/2026: `notification_settings_user_fk` của §41 CÓ trên Neon, nhưng cả
-- hai khoá của §42 thì KHÔNG — chúng vẫn là `NO ACTION`.
--
-- Không có gì hỏng ở đây, nhưng cũng không có gì NÓI ra chuyện đó: tệp này chỉ
-- chạy qua `bootstrap_schema` ở `buildCommand` của Render, tức chỉ khi `master`
-- được gộp. Mọi mục viết trên nhánh `erp` nằm chờ tới lúc ấy, và cách duy nhất
-- để biết mục nào đã tới nơi là đi hỏi `pg_catalog` từng cái một.
--
-- Cho tới khi có một bảng ghi phiên bản lược đồ: mở mục mới thì ghi rõ mục ấy
-- ĐÃ áp dụng hay CHỜ deploy, như hai dòng trên.
--   · §41 — đã áp dụng
--   · §42 — chờ deploy
--   · §43 — chỉ mục: áp dụng tay 01/09 (DDL THÊM). Hai ALTER: chờ deploy.
