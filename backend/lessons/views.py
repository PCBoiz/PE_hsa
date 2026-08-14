"""Port routes/lessons.py — API tiến độ bài học (nguồn thật: lesson_progress)."""
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from achievements.services import check_and_award_achievements
from common.clock import local_now, local_today
from common.db import q1, x
from lessons.content import course_content
from common.streak import award_xp, touch_streak


def _resolve_lesson_id(course_id, lesson_no, title, module=None):
    """Tìm lesson theo (course_id, sort_order); chưa có thì tạo stub giữ FK hợp lệ.

    Nội dung bài HSA nằm trong JS phía client, bảng ``lessons`` chỉ giữ stub cho
    khoá ngoại. Vẫn phải ghi ``module``: trang Kỹ năng lọc
    ``WHERE module <> '' AND module IS NOT NULL``, nên stub thiếu module khiến
    trang đó rỗng vĩnh viễn dù học viên học bao nhiêu bài (audit 2026-08-15).
    """
    module = (module or '').strip()[:120] or None
    row = q1('SELECT id, module FROM lessons WHERE course_id=%s AND sort_order=%s LIMIT 1',
             (course_id, lesson_no))
    if row:
        # Stub tạo trước khi client biết gửi module → bổ sung ngược lại.
        if module and not row.get('module'):
            x('UPDATE lessons SET module=%s WHERE id=%s', (module, row['id']))
        return row['id']
    row = q1('INSERT INTO lessons (course_id, title, sort_order, module) '
             'VALUES (%s, %s, %s, %s) RETURNING id',
             (course_id, title or f'Bài {lesson_no}', lesson_no, module))
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

            lesson_id = _resolve_lesson_id(course_id, lesson_no,
                                           data.get('lessonTitle'), data.get('module'))

            # Đã completed rồi thì không cộng XP lần nữa (chống spam F5 modal)
            existed = q1("SELECT 1 FROM lesson_progress "
                         "WHERE user_id=%s AND lesson_id=%s AND status='completed'",
                         (uid, lesson_id))

            x('''INSERT INTO lesson_progress
                     (user_id, lesson_id, course_id, status, quiz_score, xp_earned, completed_at)
                 VALUES (%s, %s, %s, 'completed', %s, %s, %s)
                 ON CONFLICT (user_id, lesson_id) DO UPDATE SET
                     status       = 'completed',
                     quiz_score   = COALESCE(EXCLUDED.quiz_score, lesson_progress.quiz_score),
                     xp_earned    = GREATEST(EXCLUDED.xp_earned, lesson_progress.xp_earned),
                     completed_at = COALESCE(lesson_progress.completed_at, EXCLUDED.completed_at)''',
              (uid, lesson_id, course_id, quiz_score, xp_earned, local_now()))

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
                     completed_at      = CASE WHEN %s >= 100 THEN COALESCE(completed_at, %s)
                                              ELSE completed_at END
                 WHERE user_id=%s AND course_id=%s''',
              (completed_count, progress, time_spent, progress, local_now(), uid, course_id))

            gained = 0
            new_streak, used_freeze = None, False
            if not existed:
                gained = xp_earned
                today = local_today()
                # Chuỗi + XP dùng chung common/streak.py để thi thử tính y hệt
                # (và để luật bảo hiểm chuỗi chỉ có một bản duy nhất).
                award_xp(uid, gained, today)
                new_streak, used_freeze = touch_streak(uid, today)

            newly_awarded = check_and_award_achievements(uid)

        return Response({
            'ok': True,
            'completedLessons': completed_count,
            'progress': progress,
            'xpGained': gained,
            'streak': new_streak,
            'usedStreakFreeze': used_freeze,
            'newAchievements': newly_awarded,
        })


class CourseContentView(APIView):
    """GET /api/courses/<course_id>/content — nội dung bài đã soạn trong DB.

    Engine bài học gọi endpoint này trước, rồi mới rơi về file JS cho những bài
    DB chưa có (xem lessons/content.py để biết vì sao).
    """

    def get(self, request, course_id):
        if not q1('SELECT 1 FROM courses WHERE id=%s', (course_id,)):
            return Response({'error': 'Không tìm thấy khoá học'}, status=404)
        lessons = course_content(course_id)
        return Response({'courseId': course_id, 'count': len(lessons), 'lessons': lessons})
