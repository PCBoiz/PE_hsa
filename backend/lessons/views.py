"""Port routes/lessons.py — API tiến độ bài học (nguồn thật: lesson_progress)."""
from datetime import date, timedelta

from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from achievements.services import check_and_award_achievements
from common.db import q1, x


def _resolve_lesson_id(course_id, lesson_no, title):
    """Tìm lesson theo (course_id, sort_order); chưa có thì tạo stub giữ FK hợp lệ."""
    row = q1('SELECT id FROM lessons WHERE course_id=%s AND sort_order=%s LIMIT 1',
             (course_id, lesson_no))
    if row:
        return row['id']
    row = q1('INSERT INTO lessons (course_id, title, sort_order) '
             'VALUES (%s, %s, %s) RETURNING id',
             (course_id, title or f'Bài {lesson_no}', lesson_no))
    return row['id']


class CompleteLessonView(APIView):
    def post(self, request, lesson_no):
        data = request.data if isinstance(request.data, dict) else {}
        course_id = data.get('courseId') or data.get('course_id')
        if not course_id:
            return Response({'error': 'Thiếu courseId'}, status=400)

        quiz_score = data.get('quizScore')
        if quiz_score is not None and not isinstance(quiz_score, int):
            quiz_score = None
        xp_earned = data.get('xpEarned')
        if not isinstance(xp_earned, int) or xp_earned < 0 or xp_earned > 500:
            xp_earned = 50  # mặc định an toàn, chống client gửi XP tùy ý

        uid = request.user.id
        with transaction.atomic():
            course = q1('SELECT id, lessons FROM courses WHERE id=%s', (course_id,))
            if not course:
                return Response({'error': 'Không tìm thấy khóa học'}, status=404)

            lesson_id = _resolve_lesson_id(course_id, lesson_no, data.get('lessonTitle'))

            # Đã completed rồi thì không cộng XP lần nữa (chống spam F5 modal)
            existed = q1("SELECT 1 FROM lesson_progress "
                         "WHERE user_id=%s AND lesson_id=%s AND status='completed'",
                         (uid, lesson_id))

            x('''INSERT INTO lesson_progress
                     (user_id, lesson_id, course_id, status, quiz_score, xp_earned, completed_at)
                 VALUES (%s, %s, %s, 'completed', %s, %s, now())
                 ON CONFLICT (user_id, lesson_id) DO UPDATE SET
                     status       = 'completed',
                     quiz_score   = COALESCE(EXCLUDED.quiz_score, lesson_progress.quiz_score),
                     xp_earned    = GREATEST(EXCLUDED.xp_earned, lesson_progress.xp_earned),
                     completed_at = COALESCE(lesson_progress.completed_at, EXCLUDED.completed_at)''',
              (uid, lesson_id, course_id, quiz_score, xp_earned))

            # Tính lại cache enrollments từ nguồn thật lesson_progress
            done_row = q1('''SELECT COUNT(*) AS n,
                                    COALESCE(SUM(COALESCE(l.estimated_minutes, 15)), 0) AS minutes
                             FROM lesson_progress lp
                             JOIN lessons l ON l.id = lp.lesson_id
                             WHERE lp.user_id=%s AND lp.course_id=%s AND lp.status='completed' ''',
                          (uid, course_id))
            completed_count = done_row['n']
            time_spent = str(round(done_row['minutes'] / 60, 1)) + 'h'
            total_lessons = course['lessons'] or 0
            progress = min(100, round(completed_count * 100 / total_lessons)) if total_lessons else 0
            x('''UPDATE enrollments
                 SET completed_lessons = %s,
                     progress          = %s,
                     time_spent        = %s,
                     completed_at      = CASE WHEN %s >= 100 THEN COALESCE(completed_at, now())
                                              ELSE completed_at END
                 WHERE user_id=%s AND course_id=%s''',
              (completed_count, progress, time_spent, progress, uid, course_id))

            gained = 0
            if not existed:
                gained = xp_earned
                today = date.today()
                user = q1('SELECT streak, last_study_date FROM users WHERE id=%s', (uid,))
                last_date = user['last_study_date'] if user else None
                if last_date is None or last_date < today - timedelta(days=1):
                    new_streak = 1
                elif last_date == today:
                    new_streak = user['streak']
                else:
                    new_streak = user['streak'] + 1
                x('UPDATE users SET xp = xp + %s, gems = gems + %s, streak = %s, '
                  'last_study_date = %s WHERE id=%s',
                  (gained, gained, new_streak, today, uid))
                # Log XP theo ngày (nguồn cho leaderboard tuần) — upsert cộng dồn
                x('''INSERT INTO user_daily_xp_logs (user_id, log_date, xp_earned)
                     VALUES (%s, %s, %s)
                     ON CONFLICT (user_id, log_date)
                     DO UPDATE SET xp_earned = user_daily_xp_logs.xp_earned + EXCLUDED.xp_earned''',
                  (uid, today, gained))

            newly_awarded = check_and_award_achievements(uid)

        return Response({
            'ok': True,
            'completedLessons': completed_count,
            'progress': progress,
            'xpGained': gained,
            'newAchievements': newly_awarded,
        })
