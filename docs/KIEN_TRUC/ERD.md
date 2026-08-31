<!-- TỆP NÀY ĐƯỢC SINH RA. Đừng sửa tay.
     Chạy lại sau mỗi lần đổi lược đồ:
         cd backend && python manage.py ve_erd
     Nguồn: information_schema của chính CSDL đang chạy. -->
# ERD — sinh từ CSDL
**53 bảng** trong lược đồ `public`: **38 bảng nghiệp vụ** + 15 bảng khung (Django/allauth/SimpleJWT). **57 khoá ngoại** trong khối nghiệp vụ.

## 1. Bản đồ MIỀN — đọc cái này trước
Sơ đồ đầy đủ có 38 hộp; không ai đọc nổi một bức như thế. Đây là bản đồ miền, và mỗi mũi tên là "có ít nhất một khoá ngoại".

```mermaid
flowchart LR
  M1["Tài khoản & hồ sơ<br/><small>5 bảng</small>"]
  M2["Nội dung & khoá học<br/><small>4 bảng</small>"]
  M3["Học & đo lường<br/><small>9 bảng</small>"]
  M4["Kiểm tra & thi<br/><small>4 bảng</small>"]
  M5["Trò chơi hoá<br/><small>5 bảng</small>"]
  M6["Lớp học (ERP)<br/><small>7 bảng</small>"]
  M7["Diễn đàn<br/><small>4 bảng</small>"]
  M7 --> M1
  M3 --> M2
  M3 --> M1
  M4 --> M2
  M4 --> M1
  M6 --> M2
  M6 --> M1
  M2 --> M1
  M5 --> M2
  M5 --> M1
```

## 2. ERD chi tiết, theo miền
Cột hiển thị: khoá chính (PK), khoá ngoại (FK), và cột NOT NULL. Cột tuỳ chọn được lược để sơ đồ còn đọc được — mở `sql/*.sql` khi cần đủ.

### Tài khoản & hồ sơ

```mermaid
erDiagram
  users {
    integer id PK
    integer streak_freezes 
    boolean must_change_password 
    text status 
  }
  user_follows {
    integer follower_id PK
    integer followee_id PK
  }
  notification_settings {
    integer user_id PK
  }
  notifications {
    integer id PK
    integer user_id FK
    integer coalesce_count 
  }
  admin_audit {
    bigint id PK
    integer actor_id FK
    text action 
    timestamp_without_time_zone occurred_at 
  }
  users ||--o{ admin_audit : "actor_id (SET NULL)"
  users ||--o{ notification_settings : "user_id (CASCADE)"
  users ||--o{ notifications : "user_id (CASCADE)"
  users ||--o{ user_follows : "followee_id (CASCADE)"
  users ||--o{ user_follows : "follower_id (CASCADE)"
```

| bảng | dòng | khoá ngoại ra ngoài miền |
|---|---:|---|
| `users` | 5 | — |
| `user_follows` | 0 | — |
| `notification_settings` | 2 | — |
| `notifications` | 0 | — |
| `admin_audit` | 32 | — |

### Nội dung & khoá học

```mermaid
erDiagram
  courses {
    text id PK
    integer instructor_id FK
  }
  lessons {
    integer id PK
    text course_id FK
    text title 
  }
  enrollments {
    integer user_id PK
    text course_id PK
  }
  course_ratings {
    integer user_id PK
    text course_id PK
    integer rating 
  }
  courses ||--o{ course_ratings : "course_id (CASCADE)"
  courses ||--o{ enrollments : "course_id (CASCADE)"
  courses ||--o{ lessons : "course_id (CASCADE)"
```

| bảng | dòng | khoá ngoại ra ngoài miền |
|---|---:|---|
| `courses` | 3 | `instructor_id` → `users` |
| `lessons` | 76 | — |
| `enrollments` | 6 | `user_id` → `users` |
| `course_ratings` | 0 | `user_id` → `users` |

### Học & đo lường

```mermaid
erDiagram
  lesson_progress {
    integer user_id PK
    integer lesson_id PK
  }
  learning_events {
    bigint id PK
    integer user_id FK
    text dedup_key 
    timestamp_without_time_zone occurred_at 
    date event_date 
    text kind 
    text source 
  }
  topic_self_marks {
    integer user_id PK
    text course_id PK
    text topic PK
    boolean known 
    timestamp_without_time_zone marked_at 
  }
  study_logs {
    integer id PK
    integer user_id FK
    date log_date 
    timestamp_without_time_zone created_at 
  }
  study_plans {
    integer id PK
    integer user_id FK
    timestamp_without_time_zone created_at 
    boolean is_active 
  }
  study_plan_items {
    integer id PK
    integer plan_id FK
    date week_start 
    integer sort_order 
    text kind 
    text status 
  }
  surveys {
    integer id PK
    integer user_id FK
  }
  roadmaps {
    text id PK
    integer user_id FK
    integer generated_from_survey_id FK
  }
  roadmap_progress {
    integer user_id PK
    text roadmap_id PK
    text item_id PK
  }
  surveys ||--o{ roadmaps : "generated_from_survey_id (NO ACTION)"
  study_plans ||--o{ study_plan_items : "plan_id (CASCADE)"
```

| bảng | dòng | khoá ngoại ra ngoài miền |
|---|---:|---|
| `lesson_progress` | 10 | `lesson_id` → `lessons`, `user_id` → `users` |
| `learning_events` | 37 | `user_id` → `users` |
| `topic_self_marks` | 1 | `user_id` → `users` |
| `study_logs` | 1 | `user_id` → `users` |
| `study_plans` | 3 | `user_id` → `users` |
| `study_plan_items` | 269 | — |
| `surveys` | 5 | `user_id` → `users` |
| `roadmaps` | 4 | `user_id` → `users` |
| `roadmap_progress` | 0 | `user_id` → `users` |

### Kiểm tra & thi

```mermaid
erDiagram
  quizzes {
    integer id PK
    integer user_id FK
    text course_id FK
    jsonb questions_json 
  }
  review_quiz_results {
    integer id PK
    integer quiz_id FK
    integer user_id 
    integer score 
    integer total 
    jsonb answers_json 
  }
  mock_exams {
    integer id PK
    text title 
    jsonb questions_json 
  }
  mock_attempts {
    integer id PK
    integer user_id FK
    integer exam_id FK
    boolean counted 
  }
  mock_exams ||--o{ mock_attempts : "exam_id (CASCADE)"
  quizzes ||--o{ review_quiz_results : "quiz_id (CASCADE)"
```

| bảng | dòng | khoá ngoại ra ngoài miền |
|---|---:|---|
| `quizzes` | 1 | `course_id` → `courses`, `user_id` → `users` |
| `review_quiz_results` | 1 | — |
| `mock_exams` | 1 | — |
| `mock_attempts` | 5 | `user_id` → `users` |

### Trò chơi hoá

```mermaid
erDiagram
  achievements {
    integer id PK
    text code 
    text name 
    text condition_type 
    integer condition_value 
  }
  user_achievements {
    integer user_id PK
    integer achievement_id PK
  }
  missions {
    integer id PK
    text title 
    text course_id FK
  }
  user_missions {
    integer user_id PK
    integer mission_id PK
    date mission_date PK
  }
  user_daily_xp_logs {
    integer id PK
    integer user_id FK
    date log_date 
  }
  achievements ||--o{ user_achievements : "achievement_id (CASCADE)"
  missions ||--o{ user_missions : "mission_id (CASCADE)"
```

| bảng | dòng | khoá ngoại ra ngoài miền |
|---|---:|---|
| `achievements` | 10 | — |
| `user_achievements` | 4 | — |
| `missions` | 3 | `course_id` → `courses` |
| `user_missions` | 2 | `user_id` → `users` |
| `user_daily_xp_logs` | 6 | `user_id` → `users` |

### Lớp học (ERP)

```mermaid
erDiagram
  terms {
    integer id PK
    text name 
    text status 
    timestamp_without_time_zone created_at 
  }
  classes {
    integer id PK
    text name 
    text course_id FK
    integer teacher_id FK
    text status 
    timestamp_without_time_zone created_at 
    integer term_id FK
  }
  class_members {
    integer class_id FK
    integer user_id FK
    timestamp_without_time_zone joined_at 
    integer id PK
  }
  class_sessions {
    integer id PK
    integer class_id FK
    timestamp_without_time_zone starts_at 
    text status 
    integer created_by FK
    timestamp_without_time_zone created_at 
    integer attendance_taken_by FK
  }
  attendance {
    integer session_id PK
    integer user_id PK
    text status 
    integer marked_by FK
    timestamp_without_time_zone marked_at 
  }
  assignments {
    integer id PK
    integer class_id FK
    text title 
    text course_id FK
    numeric max_score 
    text status 
    integer created_by FK
    timestamp_without_time_zone created_at 
  }
  submissions {
    integer assignment_id PK
    integer user_id PK
    integer graded_by FK
  }
  classes ||--o{ assignments : "class_id (CASCADE)"
  class_sessions ||--o{ attendance : "session_id (CASCADE)"
  classes ||--o{ class_members : "class_id (CASCADE)"
  classes ||--o{ class_sessions : "class_id (CASCADE)"
  terms ||--o{ classes : "term_id (SET NULL)"
  assignments ||--o{ submissions : "assignment_id (CASCADE)"
```

| bảng | dòng | khoá ngoại ra ngoài miền |
|---|---:|---|
| `terms` | 0 | — |
| `classes` | 1 | `course_id` → `courses`, `teacher_id` → `users` |
| `class_members` | 4 | `user_id` → `users` |
| `class_sessions` | 0 | `attendance_taken_by` → `users`, `created_by` → `users` |
| `attendance` | 0 | `marked_by` → `users`, `user_id` → `users` |
| `assignments` | 0 | `course_id` → `courses`, `created_by` → `users` |
| `submissions` | 0 | `graded_by` → `users`, `user_id` → `users` |

### Diễn đàn

```mermaid
erDiagram
  posts {
    integer id PK
    integer user_id FK
    text content 
    boolean is_sample 
  }
  comments {
    integer id PK
    integer post_id FK
    integer user_id FK
    text content 
    integer parent_comment_id FK
  }
  post_likes {
    integer post_id PK
    integer user_id PK
    text reaction_type 
  }
  comment_likes {
    integer comment_id PK
    integer user_id PK
    text reaction_type 
  }
  comments ||--o{ comment_likes : "comment_id (CASCADE)"
  comments ||--o{ comments : "parent_comment_id (CASCADE)"
  posts ||--o{ comments : "post_id (CASCADE)"
  posts ||--o{ post_likes : "post_id (CASCADE)"
```

| bảng | dòng | khoá ngoại ra ngoài miền |
|---|---:|---|
| `posts` | 9 | `user_id` → `users` |
| `comments` | 0 | `user_id` → `users` |
| `post_likes` | 0 | `user_id` → `users` |
| `comment_likes` | 0 | `user_id` → `users` |

## 3. Đọc từ số liệu, không từ trí nhớ

**12 bảng đang RỖNG** — tính năng đã dựng nhưng chưa ai dùng, hoặc dựng thừa. Đáng rà lại trước khi thêm tính năng mới:

`assignments`, `attendance`, `class_sessions`, `comment_likes`, `comments`, `course_ratings`, `notifications`, `post_likes`, `roadmap_progress`, `submissions`, `terms`, `user_follows`

**Bảng không dính khoá ngoại nào**: (không có — tốt)

**Luật xoá của khoá ngoại** — trộn nhiều luật trong một hệ là cách dữ liệu mồ côi sinh ra:

- `CASCADE`: 43 khoá
- `SET NULL`: 10 khoá
- `NO ACTION`: 4 khoá — `courses.instructor_id`, `missions.course_id`, `roadmaps.generated_from_survey_id`, `roadmaps.user_id`
