# Báo cáo trạng thái — số đo thật

*Sinh tự động ngày 13/09/2026 bằng `python scripts/kiem_ke_san_pham.py --md`. Mọi con số dưới đây được đếm lại từ mã
nguồn hoặc đo trực tiếp trên CSDL tại thời điểm chạy lệnh.*

*Bản này CHỈ ĐO, không nhận định. Muốn biết vì sao một con số ra như vậy thì đọc
`PROGRESS.md`. Đừng chép số từ đây sang tài liệu khác — chép ra là bắt đầu cũ đi.*

---

## Mã nguồn

| Hạng mục | Số đo | Nguồn |
|---|---|---|
| Vai trò người dùng | 6 | `permissions.py` → `ASSIGNABLE_ROLES` |
| Lớp cổng phân quyền | 6 | `permissions.py` → `Is*` |
| Đường API | 107 | `get_resolver()` — đường bắt đầu bằng `api/` |
| · không cần đăng nhập | 2 | AllowAny hoặc `authentication_classes = []` |
| · chỉ cần đăng nhập | 60 | `permission_classes == [IsAuthenticated]` |
| · · trong đó KHÔNG tự khai cổng | 60 | dựa vào mặc định của khung |
| · có cổng vai trò | 45 | lớp `Is*` khác |
| Trang giao diện | 26 | `frontend/src/app/**/page.tsx` |
| Bảng CSDL | 55 | `information_schema.tables` |
| · có dữ liệu | 36 | count(*) > 0 |
| Tệp kiểm thử backend | 32 | `backend/**/tests*.py` |
| Tệp kiểm thử frontend | 32 | `frontend/e2e/**` |

## Dữ liệu nghiệp vụ trên CSDL

| Hạng mục | Số đo |
|---|---|
| Hợp phần (khoá học) | 3 |
| Bài học | 76 |
| Tài khoản | 5 |
| · học viên | 3 |
| Lớp | 1 |
| Đợt học | 1 |
| Buổi học | 4 |
| Lượt điểm danh | 6 |
| Đề thi thử | 1 |
| Học viên có email phụ huynh | 0 |
| Học viên có số phụ huynh | 0 |

## Đường API chỉ cần đăng nhập mà KHÔNG tự khai cổng

*Mặc định của khung là "phải đăng nhập" — đúng, nhưng một đường mới quên khai sẽ
mở cho mọi người đã đăng nhập, im lặng. Liệt kê để đối chiếu từng dòng.*

| api/achievements | AchievementsView |
| api/assignments | MyAssignmentsView |
| api/chat | ChatView |
| api/comments/<int:comment_id> | CommentDetailView |
| api/comments/<int:comment_id>/react | ReactCommentView |
| api/course/<str:course_id>/rating | CourseRatingView |
| api/course/rating | RateCourseView |
| api/courses | CoursesView |
| api/courses-enrolled | CoursesEnrolledView |
| api/courses/<str:course_id> | CourseDetailView |
| api/courses/<str:course_id>/content | CourseContentView |
| api/courses/<str:course_id>/enroll | EnrollView |
| api/courses/<str:course_id>/lessons/<int:lesson_no>/check | CheckAnswersView |
| api/courses/<str:course_id>/quiz/generate | GenerateQuizView |
| api/courses/<str:course_id>/quiz/history | QuizHistoryView |
| api/enrolled | EnrolledView |
| api/hsa/competency | CompetencyView |
| api/hsa/competency/self | TopicSelfMarkView |
| api/hsa/goals | HsaGoalsView |
| api/hsa/gradebook | GradebookView |
| api/hsa/journal | JournalView |
| api/hsa/progress-curve | ProgressCurveView |
| api/hsa/study-plan | StudyPlanView |
| api/hsa/study-plan/items/<int:item_id> | StudyPlanItemView |
| api/hsa/summary | HsaSummaryView |
| api/hsa/weekly-target | WeeklyTargetView |
| api/leaderboard | LeaderboardView |
| api/lessons/<int:lesson_no>/complete | CompleteLessonView |
| api/me/roadmap | MyRoadmapView |
| api/me/roadmap/ai | AiRoadmapView |
| api/missions/claim | ClaimMissionView |
| api/missions/today | TodayMissionsView |
| api/mock-attempts | MockAttemptsView |
| api/mock-exams | MockExamsView |
| api/mock-exams/<int:exam_id>/save | MockSaveView |
| api/mock-exams/<int:exam_id>/start | MockStartView |
| api/mock-exams/<int:exam_id>/submit | MockSubmitView |
| api/notifications | NotificationSettingsView |
| api/notifications/badge | BadgeView |
| api/notifications/feed | FeedView |
| api/notifications/feed/<int:notif_id>/read | FeedReadView |
| api/notifications/feed/read-all | FeedReadAllView |
| api/posts | PostsView |
| api/posts/<int:post_id> | PostDetailView |
| api/posts/<int:post_id>/comments | CommentsView |
| api/posts/<int:post_id>/react | ReactPostView |
| api/quizzes/<int:quiz_id> | QuizView |
| api/quizzes/<int:quiz_id>/submit | SubmitQuizView |
| api/roadmap | RoadmapProgressView |
| api/roadmap/<str:item_id> | UpdateRoadmapItemView |
| api/roadmaps | RoadmapsView |
| api/skills | SkillsView |
| api/stats | StatsView |
| api/stats/xp-by-course | XpByCourseView |
| api/streak/review-quiz-status | ReviewQuizStatusView |
| api/survey | SurveyView |
| api/user | UserView |
| api/user/password | PasswordView |
| api/users/<int:user_id>/follow | FollowView |
| api/users/<int:user_id>/following | FollowingView |

---

*Sinh bởi `scripts/kiem_ke_san_pham.py --md`. Chạy lại bất cứ lúc nào để có số mới.*
