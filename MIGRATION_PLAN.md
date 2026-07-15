# MIGRATION_PLAN.md — Programming_EDU → Next.js + Django + Neon

> Giai đoạn 1 (audit, chưa viết code). Nguồn: đọc read-only `Programming_EDU/`
> (routes/, db/schema.py, templates/, static/, app.py, config.py) ngày 2026-07-14.
> Thư mục đích: `Programming_EDU_next/` (backend/ = Django, frontend/ = Next.js).

---

## 1. Danh sách endpoint hiện có → Django app dự kiến

Ghi chú chung:
- Mọi route `/api/*` giữ nguyên **path + method** (ràng buộc #2). Vì path không theo
  chuẩn router lồng của DRF (vd `/api/course/rating` số ít, `/api/courses-enrolled`),
  sẽ dùng **explicit `path()` urlconf + APIView/ViewSet action** thay vì để
  DefaultRouter tự sinh URL — router tự sinh sẽ đổi path, vi phạm ràng buộc.
- Các route render template (main.py, admin.py GET /admin) **không port sang Django**
  — chúng trở thành page Next.js (mục 3).
- Auth guard: `@api_login_required` (JSON 401) → DRF `IsAuthenticated` + JWT;
  `@admin_required`/`@api_admin_required` → permission class custom kiểm tra role
  (hiện tại check `role == 'Quản trị viên'`? — sẽ đối chiếu `utils.py` khi implement).

### App `accounts` (từ blueprint auth + oauth + user)

| Method | Path | Nguồn | Ghi chú |
|---|---|---|---|
| POST | `/auth/login` | auth.py | rate-limit 5/phút. Trả JWT thay vì set session |
| POST | `/auth/register` | auth.py | rate-limit 3/phút |
| GET | `/auth/logout` | auth.py | với JWT: blacklist refresh token (SimpleJWT blacklist app) |
| GET | `/auth/google` → `/auth/google/callback` | oauth.py (flask-dance) | django-allauth; callback cấp JWT rồi redirect về frontend (xem MIGRATION_NOTES khi làm) |
| GET | `/auth/facebook` → `/auth/facebook/callback` | oauth.py | như trên |
| GET | `/api/user` | user.py | profile hiện tại |
| PUT | `/api/user` | user.py | cập nhật name/phone/birthday/avatar |
| PUT | `/api/user/password` | user.py | đổi mật khẩu (check hash cũ) |
| POST | `/api/users/<id>/follow` | user.py | |
| DELETE | `/api/users/<id>/follow` | user.py | |
| GET | `/api/users/<id>/following` | user.py | |
| POST | `/api/survey` | user.py | lưu survey JSONB + đánh dấu questionnaire_completed |

Luồng nghiệp vụ OAuth phải giữ: (1) tìm theo (provider, provider_id); (2) nếu email
trùng tài khoản thường → auto-link; (3) tạo user mới. Google redirect `/dashboard`,
Facebook redirect `/` (khác nhau — giữ nguyên).

### App `courses` (courses.py)

| Method | Path | Ghi chú |
|---|---|---|
| GET | `/api/courses` | list + search/filter |
| GET | `/api/enrolled` | |
| GET | `/api/courses-enrolled` | join courses × enrollments |
| POST | `/api/courses/<course_id>/enroll` | |
| DELETE | `/api/courses/<course_id>/enroll` | |
| POST | `/api/course/rating` | path SỐ ÍT — giữ nguyên |
| GET | `/api/course/<course_id>/rating` | |
| GET | `/api/skills` | trang Kỹ năng (đọc lessons + lesson_progress) |

### App `lessons` (lessons.py + phần lesson của main.py)

| Method | Path | Ghi chú |
|---|---|---|
| POST | `/api/lessons/<lesson_no>/complete` | logic XP/streak/achievement — vùng rủi ro cao, port cẩn thận |

### App `quizzes` (quizzes.py)

| Method | Path | Ghi chú |
|---|---|---|
| POST | `/api/courses/<course_id>/quiz/generate` | sinh quiz từ `lessons.content_json` (step_2); questions_json là snapshot có đáp án — CHỈ backend đọc |
| POST | `/api/quizzes/<quiz_id>/submit` | chấm điểm server-side |
| GET | `/api/quizzes/<quiz_id>` | trả câu hỏi ĐÃ LỌC đáp án |
| GET | `/api/courses/<course_id>/quiz/history` | |

### App `stats` (stats.py)

| Method | Path | Ghi chú |
|---|---|---|
| GET | `/api/stats` | |
| GET | `/api/stats/xp-by-course` | |
| POST | `/api/mission/complete` | mission + XP + daily log |
| GET | `/api/streak/review-quiz-status` | logic streak — có test hiện hữu (test_streak.py) |

### App `notifications` (notifications.py)

| Method | Path | Ghi chú |
|---|---|---|
| GET | `/api/notifications` | CÀI ĐẶT thông báo (bảng notification_settings) |
| PUT | `/api/notifications` | |
| GET | `/api/notifications/feed` | FEED chuông (bảng notifications) |
| POST | `/api/notifications/feed/<id>/read` | |
| POST | `/api/notifications/feed/read-all` | |

### App `roadmap` (roadmap.py)

| Method | Path | Ghi chú |
|---|---|---|
| GET | `/api/roadmaps` | template + của user |
| GET | `/api/roadmap` | |
| GET | `/api/me/roadmap` | |
| POST | `/api/me/roadmap` | |
| POST | `/api/me/roadmap/ai` | sinh roadmap bằng AI |
| PUT | `/api/roadmap/<item_id>` | toggle done (roadmap_progress) |

### App `leaderboard` (leaderboard.py)

| Method | Path | Ghi chú |
|---|---|---|
| GET | `/api/leaderboard` | weekly dùng user_daily_xp_logs; friends dùng user_follows |

### App `achievements` (achievements.py + db/repositories/achievements.py)

| Method | Path | Ghi chú |
|---|---|---|
| GET | `/api/achievements` | logic award nằm ở repositories — port thành service dùng chung |

### App `forum` (forum.py)

| Method | Path | Ghi chú |
|---|---|---|
| GET, POST | `/api/posts` | |
| GET, PUT, DELETE | `/api/posts/<post_id>` | |
| POST | `/api/posts/<post_id>/react` | 6 loại reaction, 1/user/post |
| GET, POST | `/api/posts/<post_id>/comments` | reply lồng 1 cấp (parent_comment_id) |
| POST | `/api/comments/<comment_id>/react` | |
| PUT, DELETE | `/api/comments/<comment_id>` | |

### App `courseadmin` (admin.py — tên "admin" đụng django.contrib.admin nên đặt `courseadmin`)

| Method | Path | Ghi chú |
|---|---|---|
| GET, POST | `/api/admin/courses` | |
| PUT, DELETE | `/api/admin/courses/<course_id>` | |
| GET | `/api/admin/courses/<course_id>/lessons` | |
| POST | `/api/admin/lessons` | |
| PUT, DELETE | `/api/admin/lessons/<lesson_id>` | |

### Hạ tầng app.py phải port (không phải endpoint)

- **Error handler JSON thống nhất** 400/401/403/404/429/500 + catch-all, format
  `{"error": {"status", "message", "detail"}, "request_id"}` — message tiếng Việt giữ nguyên
  (frontend có thể hiển thị). → DRF custom exception handler + handler404/500.
- **Security headers** (X-Content-Type-Options, X-Frame-Options SAMEORIGIN,
  Referrer-Policy, CSP với đúng whitelist CDN hiện tại, HSTS khi production).
- **Rate limit** mặc định `200/day, 50/hour` theo IP (extensions.py) + per-route
  login 5/min, register 3/min; **static files được EXEMPT** (AUDIT-FIX 2026-07-07 —
  với Next.js static do frontend serve nên tự nhiên thoát rate-limit, nhưng phải ghi
  MIGRATION_NOTES để không ai thêm throttle toàn cục lên media sau này).
- **CORS** `/api/*` theo `ALLOWED_ORIGINS` env — giờ bắt buộc vì cross-origin thật.
- **Neon**: pool 2–10 connection, TCP keepalive, retry backoff khi init;
  `start_keepalive()` chống cold-start → thay bằng phương án ở Giai đoạn 2 (CONN_MAX_AGE +
  Neon pooler, hoặc /health + cron ping — chọn và ghi lý do vào MIGRATION_NOTES).
- **Logging**: `utils/logging.py` (request-id, log 5xx) → Django LOGGING config +
  middleware request-id. Lưu ý: trong app.py 2 dòng `setup_logging`/`init_request_id`
  đang **bị comment tắt** — sẽ hỏi anh/chị ở checkpoint có muốn bật lại ở bản mới không.

---

## 2. Bảng trong db/schema.py → Django models

Chung: bảng đã tồn tại trên Neon → mọi model đặt `class Meta: db_table = '<tên cũ>'`,
`managed = False` giai đoạn đầu (hoặc `managed=True` + `migrate --fake-initial`) —
**không để Django tạo lại bảng**. Sẽ chạy `inspectdb` đối chiếu trước khi viết tay
(Giai đoạn 2) vì schema.py có nhiều ALTER migration guard — cột thật trên Neon là
nguồn chân lý, không phải CREATE TABLE gốc.

| Bảng | App | Model | Điểm cần lưu ý |
|---|---|---|---|
| `users` | accounts | `User` (custom AUTH_USER_MODEL) | password là hash werkzeug (`scrypt:`/`pbkdf2:`) — Django phải verify được: thêm custom password hasher tương thích werkzeug, KHÔNG reset mật khẩu user. Cột: name, email UNIQUE, phone, birthday(TEXT), role, streak, certificates, gems, xp, questionnaire_completed(INT), last_study_date, oauth_provider(+partial unique index), avatar, is_verified, created_at |
| `courses` | courses | `Course` | PK = TEXT (`id`), instructor_id FK→users SET_NULL, xp_reward, is_published, content_meta JSONB |
| `lessons` | lessons | `Lesson` | FK course CASCADE; unique (course_id, lesson_code); content_json JSONB (GIN index); lesson_type, xp_reward, is_free_preview, subtitle, estimated_minutes |
| `quizzes` | quizzes | `Quiz` | FK user, course CASCADE; questions_json JSONB NOT NULL |
| `review_quiz_results` | quizzes | `ReviewQuizResult` | FK quiz, user CASCADE |
| `enrollments` | courses | `Enrollment` | **PK composite (user_id, course_id)** — Django không hỗ trợ composite PK: dùng `unique_together` + surrogate; vì bảng thật không có cột id → để `managed=False` và khai báo 1 cột làm `primary_key=True` (pattern chuẩn cho legacy composite-PK), mọi write dùng queryset filter theo cặp khóa. Ghi rõ vào MIGRATION_NOTES |
| `lesson_progress` | lessons | `LessonProgress` | composite PK (user_id, lesson_id) — như trên |
| `course_ratings` | courses | `CourseRating` | composite PK; CHECK rating 1–5; created_at là TEXT (giữ nguyên, không "sửa tiện tay") |
| `missions` | stats | `Mission` | FK course |
| `notification_settings` | notifications | `NotificationSetting` | PK = user_id |
| `notifications` | notifications | `Notification` | feed chuông |
| `surveys` | accounts | `Survey` | data_json JSONB |
| `user_daily_xp_logs` | stats | `UserDailyXpLog` | UNIQUE (user_id, log_date) |
| `roadmaps` | roadmap | `Roadmap` | PK TEXT; user_id NULL = template; nodes_json/edges_json JSONB, mermaid_def TEXT |
| `roadmap_progress` | roadmap | `RoadmapProgress` | composite PK 3 cột |
| `posts` | forum | `Post` | like_count = tổng mọi reaction, recompute bằng COUNT |
| `comments` | forum | `Comment` | parent_comment_id self-FK (1 cấp) |
| `post_likes` | forum | `PostReaction` | composite PK; CHECK reaction_type IN 6 loại |
| `comment_likes` | forum | `CommentReaction` | như trên |
| `achievements` | achievements | `Achievement` | seed 6 achievement theo `code` |
| `user_achievements` | achievements | `UserAchievement` | composite PK |
| `user_follows` | accounts | `UserFollow` | composite PK + CHECK follower != followee |

**Seed/migration logic trong init_db() KHÔNG port nguyên xi** — nó là lịch sử migration
tích lũy (rename notifications, tách 3 khóa DB Design, normalize level...). DB thật đã
ở trạng thái cuối. Chỉ port phần seed **idempotent còn giá trị chạy lại**:
seed courses/roadmaps/missions/achievements khi bảng rỗng + upsert lessons từ
`db/lessons_seed.py` + sync content_json (Giai đoạn 4) → gom vào Django management
command `python manage.py seed_data` (không chạy tự động mỗi startup như Flask).

---

## 3. Template → Page Next.js (App Router)

Kiến trúc route: 3 nhóm layout để giữ ĐÚNG tổ hợp CSS từng trang (xem mục 4):

```
frontend/src/app/
├── (base)/               ← layout = port base.html (topbar, bell, user-chip, theme script)
│   ├── page.tsx                        ← landing.html   (/)
│   └── dashboard/page.tsx              ← dashboard.html (/dashboard)
├── (standalone)/         ← layout rỗng (các trang gốc KHÔNG extends base)
│   ├── login/page.tsx                  ← login.html
│   ├── register/page.tsx               ← register.html
│   ├── questionaire/page.tsx           ← questionaire.html
│   ├── interface/page.tsx              ← interface.html
│   ├── lesson/[courseId]/page.tsx      ← lesson_python/java/htmlcss/db_design.html (chọn variant theo courseId, như _LESSON_TEMPLATES)
│   ├── courses/[courseId]/page.tsx     ← course_detail.html / course_db_design.html (rẽ nhánh theo courseId như main.py)
│   ├── card/[cardId]/page.tsx          ← concept_card.html
│   └── admin/page.tsx                  ← admin.html
└── auth/callback/page.tsx              ← trang nhận JWT sau OAuth (MỚI — bắt buộc vì cross-domain)
```

| Template | Route | Ghi chú port |
|---|---|---|
| base.html | `(base)/layout.tsx` | topbar/nav/bell/user-chip; script chống FOUC theme (`localStorage.theme`) phải inline trong layout trước hydration; `csrf_token()` meta bỏ → JWT (ghi MIGRATION_NOTES) |
| landing.html | `/` | extends base; block body_decor/nav/footer riêng |
| login.html | `/login` | standalone |
| register.html | `/register` | standalone; inline script particle/ripple giữ nguyên |
| dashboard.html | `/dashboard` | **Trang SPA-hub**: nav `navigate('courses'/'roadmap'/'forum'/'profile'/'settings')` chuyển section CLIENT-SIDE trong cùng trang (main.js), không phải route riêng. Giữ nguyên cơ chế — KHÔNG tách thành nhiều route Next. Include partial roadmap.html + chatbot.html |
| questionaire.html | `/questionaire` | server truyền `_user_stats()` → chuyển thành fetch `/api/user` + `/api/stats` (client) hoặc props |
| interface.html | `/interface` | mission cpp; confetti CDN → copy lib vào public/vendor (CSP hiện cho jsdelivr — giữ CDN cũng được, quyết ở Giai đoạn 3) |
| lesson_python.html | `/lesson/python` | 3 file gần giống nhau — port thành 1 component + khác biệt nhỏ theo course; **đối chiếu diff 3 file trước**, nếu khác nhau đáng kể thì giữ 3 bản riêng cho an toàn 1:1 |
| lesson_java.html | `/lesson/java` | như trên |
| lesson_htmlcss.html | `/lesson/htmlcss` | như trên |
| lesson_db_design.html | `/lesson/db_design`, `/lesson/db_design_tc`, `/lesson/db_design_nc` | template nặng nhất (636 dòng + 7 file JS + CodeMirror 5 CDN). Query `?lesson=N` (1-based) và `?lesson_idx=N` (0-based legacy) giữ nguyên semantics |
| course_detail.html | `/courses/[id]` (python/java/htmlcss/cpp) | server-side render CURRICULA + trạng thái done/current/locked → CURRICULA (data tĩnh trong main.py) chuyển thành module data TS hoặc API — đề xuất: API `/api/courses/<id>/curriculum` mới ở Django (ghi chú lý do: dữ liệu + trạng thái cần DB) HOẶC giữ tính toán trong Next server component gọi API enrollment. Chốt ở Giai đoạn 3 |
| course_db_design.html | `/courses/db_design`, `/courses/db_design_tc`, `/courses/db_design_nc` | JS đọc `data-course` để render roadmap đúng khóa |
| concept_card.html | `/card/[cardId]` | hydrate client-side từ lesson_content_tc/nc.js theo card_id — giữ nguyên |
| chatbot.html | component `<Chatbot />` | partial include ở 6 trang; chatbot.js gọi Gemini (`generativelanguage.googleapis.com` có trong CSP connect-src) |
| roadmap.html | component `<RoadmapSection />` | chỉ dùng trong dashboard |
| admin.html | `/admin` | standalone, style + script inline — port nguyên |

Trang nào hiện được Flask bơm `**_user_stats()` (questionaire, interface, lesson_*,
concept_card, course_detail): bản Next lấy cùng dữ liệu qua API — cần xem `_user_stats()`
trả gì để đảm bảo field nào template dùng thì API có (làm ở Giai đoạn 3, đối chiếu từng field).

---

## 4. Tổ hợp CSS/JS theo từng template (ràng buộc #1 — KHÔNG import global tất cả)

Trích trực tiếp từ `<link>`/`<script>` trong từng template (đã gồm phần kế thừa từ base):

| Trang | CSS local (theo thứ tự load) | CSS/JS CDN | JS local (theo thứ tự) |
|---|---|---|---|
| base (nền cho landing, dashboard) | theme.css?v=3, auth.css, chatbot.css | Google Fonts Inter, Font Awesome 6.4.0 | icons.js?v=2 |
| landing | (chỉ của base) | (của base) | inline script |
| dashboard | (base) + style.css, dashboard.css, pages.css, dark-mode.css, roadmap.css, skeleton.css, ChangePassword.css | (base) + mermaid@11, svg-pan-zoom@3.6.1 | main.js, dashboard.js, roadmap.js, roadmapData.js, chatbot.js |
| login | chatbot.css, login.css | Font Awesome | main.js + inline |
| register | register.css | Google Fonts Sora | inline script |
| questionaire | questionaire.css | — | main.js, questionaire.js |
| interface | lesson.css | Font Awesome, canvas-confetti@1.5.1 | main.js + inline |
| lesson_python / java / htmlcss | lesson.css, chatbot.css | Font Awesome, canvas-confetti@1.5.1 | main.js, chatbot.js |
| lesson_db_design | lesson_db_design.css | Font Awesome, CodeMirror 5.65.7 (lib css + material-darker theme + lib js + mode/sql + placeholder addon), canvas-confetti@1.9.2 | lesson_content.js, lesson_content_tc.js, lesson_content_nc.js, lesson_db_design.js, drag_game.js, decomp_game.js, table_explorer.js |
| course_detail | style.css, dashboard.css, pages.css, dark-mode.css, course_detail.css, chatbot.css | Font Awesome | chatbot.js, course_detail.js, review_quiz.js |
| course_db_design | style.css, dashboard.css, pages.css, dark-mode.css, course_db_design.css, chatbot.css | Font Awesome | chatbot.js, course_db_design.js |
| concept_card | (inline `<style>` trong template) | Google Fonts Inter+JetBrains Mono, Font Awesome | lesson_content_tc.js, lesson_content_nc.js + inline hydrate |
| admin | (inline `<style>`) | — | inline script |

Chiến lược trong Next.js:
- App Router cho phép import CSS global ở **từng page/layout** — mỗi page import đúng
  danh sách trên, đúng thứ tự.
- Rủi ro đã biết: khi client-side navigate giữa 2 route, CSS route cũ **không được gỡ**
  → có thể đè class trùng tên (login.css vs register.css vs dashboard.css đều define
  nhiều class chung). App cũ điều hướng bằng `window.location` (main.js `navigate()`)
  tức full page load — bản Next sẽ **giữ điều hướng full-load bằng thẻ `<a>` thường**
  giữa các nhóm trang khác tổ hợp CSS, không dùng `<Link>` prefetch/client-nav ở các
  điểm đó. Hành vi giống hệt bản cũ, tránh CSS bleed.
- Không Tailwind, không CSS-in-JS, không CSS Modules. Copy byte-nguyên-xi.
- Query version `?v=3`, `?v=2`... không cần mang theo (Next tự hash asset), ghi chú lại.

## 5. File JS port NGUYÊN VẸN (bọc wrapper, không rewrite) + độ phức tạp

| File | Dòng | Vai trò | Độ phức tạp port | Chiến lược |
|---|---|---|---|---|
| lesson_db_design.js | 9 171 | Engine renderer bài học DB (steps, sim WAL/ARIES/2PL/MVCC, chấm SQL PE_runSQL, boss...) | **RẤT CAO** — nhiều `window.*` global, đọc DOM theo id, phụ thuộc CodeMirror global, LESSON_CONTENT global | Load nguyên file qua wrapper `useLegacyScript` (useRef+useEffect, gọi init/cleanup). Thứ tự load: content trước, engine sau (như template cũ) |
| lesson_content_nc.js | 6 503 | DATA khóa Nâng cao (`window.LESSON_CONTENT.db_design_nc`) | Thấp (file data thuần, chỉ to) | Copy nguyên, load `<Script strategy="beforeInteractive">` hoặc script tag trong page |
| lesson_content.js | 5 348 | DATA khóa Cơ bản | Thấp | như trên |
| lesson_content_tc.js | 3 990 | DATA khóa Trung cấp | Thấp | như trên |
| dashboard.js | 2 337 | Logic dashboard (stats, courses grid, forum, profile, settings...) | Cao — gọi nhiều API, thao tác DOM, phối hợp main.js | Bọc wrapper; fetch đi qua shim apiClient (đính JWT) — KHÔNG sửa logic |
| main.js | 1 905 | SPA navigate(), theme, search, bell, user-chip, filterCourses | Cao — chạy trên nhiều trang, đọc meta csrf-token | Bọc wrapper. Điểm ĐỘNG duy nhất phải chạm: chỗ đọc CSRF meta + credentials fetch → chuyển qua shim JWT. Sẽ diff tối thiểu, ghi rõ từng dòng đổi vào MIGRATION_NOTES |
| drag_game.js | 1 709 | Mini-game kéo-thả WHERE (PE_parseWhereRows) | Trung–cao (global API được file khác gọi) | Bọc nguyên |
| course_db_design.js | 836 | Roadmap 3 khóa DB Design (skill tree, prereq) | Trung | Bọc nguyên |
| decomp_game.js | 491 | Mini-game chuẩn hóa/decomposition | Trung | Bọc nguyên |
| roadmap.js | 473 | Render mermaid roadmap + pan-zoom + tooltip | Trung (phụ thuộc mermaid + svg-pan-zoom CDN global) | Bọc nguyên; load CDN như cũ |
| roadmapData.js | 411 | Data roadmap tĩnh | Thấp | Copy nguyên |
| chatbot.js | 383 | Chatbot Gemini | Thấp–trung | Bọc nguyên |
| table_explorer.js | 314 | Widget khám phá bảng | Thấp–trung | Bọc nguyên |
| questionaire.js | 304 | Form khảo sát | Thấp | Bọc nguyên |
| course_detail.js | 224 | Trang chi tiết khóa thường | Thấp | Bọc nguyên |
| review_quiz.js | 101 | Quiz ôn tập FE-06 | Thấp | Bọc nguyên |
| icons.js | ~nhỏ | Icon sprite `data-icon` | Thấp | Bọc nguyên (chạy trong base layout) |

Nguyên tắc wrapper (áp dụng thống nhất, viết 1 lần):
```tsx
// LegacyScripts: nạp tuần tự các file .js legacy (giữ nguyên nội dung, đặt tại
// public/legacy/), gọi hàm init sau khi DOM section render, cleanup khi unmount.
```
File nào lúc port phát hiện quá phức tạp để bọc an toàn 1 lần (ứng viên số 1:
`lesson_db_design.js`) → **dừng, báo cáo trước khi tiếp** (ràng buộc #1).

---

## 6. File rời rạc ở root — phân loại (a) port / (b) bỏ / (c) hỏi

| File | Loại | Lý do |
|---|---|---|
| `migrate_password_hash.py` | **(b) bỏ** | Migration một-lần rehash plaintext→werkzeug; auth.py hiện đã dùng check/generate_password_hash, DB đã hash. Bản Django cần **hasher tương thích werkzeug** (đã ghi ở mục 2), không cần script này nữa. (CLAUDE.md gốc ghi "plaintext — known issue" đã LỖI THỜI) |
| `check_user.py` | **(a) port** | Tool vận hành thật (xem user / reset password) → Django management command `python manage.py check_user` (khỏi viết SQL tay). |
| `probe_e2_fix.py` | **(b) bỏ** | Probe Playwright một-lần cho fix E2 cụ thể (bài 15/10/2), hardcode localhost:9000 + tài khoản audit; giá trị đã tiêu hết sau khi fix merge. |
| `test_e2.py` | **(c) HỎI** | Không phải debug một-lần: là bộ test 20 bài PE_runSQL + backward-compat E1/E2/E3 — đang là **regression test duy nhất của engine chấm SQL** (phần logic quan trọng nhất). Đề xuất: port thành Playwright e2e trong `frontend/e2e/` trỏ vào bản Next (Giai đoạn 5). Cần anh/chị xác nhận. |
| `regression_b6.py` | **(c) HỎI** | Tương tự — regression 2 path (PE_runSQL + PE_parseWhereRows) cho bug B6/B10 đã fix. Đề xuất gộp chung vào bộ e2e trên. |
| `dev_server.py` | **(b) bỏ** | Server dev không-cần-DB để xem template — `next dev` thay thế hoàn toàn vai trò này. |
| `erd_v2_2_lesson_jsonb.html`, `schema_v2_2_quiz.sql`, `src.zip` | **(b) không mang theo** | Tài liệu thiết kế/artifact lịch sử — ở lại repo gốc, vẫn tham khảo được. |
| `scripts/export_js_to_json.py`, `scripts/inspect_lesson_data.py` | **(c) HỎI** | Tool thao tác lesson content — có thể được thay bởi script Node mới ở Giai đoạn 4. Đề xuất: không port, viết bản Node tương đương khi cần. |
| `scripts/probe_2g_bfix.cjs` | **(b) bỏ** | Probe một-lần. |
| `scripts/test_forum_api.py` | **(c) HỎI** | Smoke test API forum — forum hiện 0 unit test; đề xuất dùng nó làm checklist case khi viết Django test cho app forum (Giai đoạn 5) rồi không port file. |

## 7. Content pipeline & test hiện có (input cho Giai đoạn 4–5)

- `db/seed_lesson_content.py`: eval `lesson_content*.js` bằng py_mini_racer → ghi
  `lessons.content_json` theo SHA-256 hash (idempotent). → viết lại thành script Node
  trong `content-tools/` (Node require/eval trực tiếp, giữ hash-based change detection).
- `content/courses/{db_design,db_design_tc,db_design_nc}/` (course.json + lessons/):
  đối chiếu vai trò với lesson_content*.js khi làm Giai đoạn 4 (nghi là bản export JSON).
- Test port: `tests/test_streak.py` → app stats; `tests/test_review_quiz.py` → quizzes;
  `tests/test_parse_time_spent.py` → courses (helper parse time_spent);
  `tests/test_course_ratings.py` → courses. Mỗi app còn lại viết tối thiểu happy-path
  + 1 error-path (ràng buộc Giai đoạn 5).

## 8. Quyết định đã chốt với chủ dự án (2026-07-14)

1. **test_e2.py / regression_b6.py**: ✅ port thành bộ Playwright e2e trong
   `frontend/e2e/`, trỏ vào bản Next.js, chạy ở Giai đoạn 5.
2. **scripts/**: ✅ KHÔNG port; Giai đoạn 4 viết content-tools Node mới;
   `test_forum_api.py` dùng làm checklist case cho Django test app forum.
3. **Logging**: ✅ BẬT request-id + log 5xx ở bản Django (Django LOGGING config +
   middleware request-id) dù bản Flask gốc đang comment tắt.
4. **Package manager frontend**: ✅ `corepack pnpm`.
