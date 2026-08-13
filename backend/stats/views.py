"""Port routes/stats.py + db/repositories/missions.py (phần verify)."""
import json
import re
from datetime import date, timedelta

from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from achievements.services import check_and_award_achievements
from common.db import q, q1, x


def _json_rows(value):
    """json_agg từ psycopg3 thường đã là list; phòng trường hợp trả str (như
    ghi chú roadmap/views._jsonb) thì parse lại."""
    if value is None:
        return []
    if isinstance(value, str):
        import json
        try:
            return json.loads(value)
        except ValueError:
            return []
    return value


def parse_time_spent(value) -> float:
    if value is None or value == '':
        return 0.0
    s = str(value).replace('h', '').strip()
    if not s:
        return 0.0
    try:
        result = float(s)
    except ValueError:
        return 0.0
    if result < 0:
        return 0.0
    # Sanity clamp: khóa dài nhất ~60h, 500h là chặn dữ liệu rác
    if result > 500:
        return 500.0
    return result


class StatsView(APIView):
    def get(self, request):
        # PERF 2026-07-19: gộp 2 query thành 1 round trip (RTT tới Neon ~240ms/câu)
        uid = request.user.id
        summary = q1('''
            SELECT u.streak, u.certificates, u.last_study_date,
                   (SELECT COALESCE(json_agg(json_build_object(
                               'progress', e.progress, 'time_spent', e.time_spent)), '[]'::json)
                    FROM enrollments e WHERE e.user_id = u.id) AS enroll_rows
            FROM users u
            WHERE u.id = %s
        ''', (uid,))
        rows = _json_rows(summary['enroll_rows'])
        # progress nullable trong DB → coalesce về 0, tránh TypeError (sum None)
        avg_progress = round(sum((r['progress'] or 0) for r in rows) / len(rows)) if rows else 0
        total_hours = sum(parse_time_spent(r.get('time_spent')) for r in rows)
        last_date = summary['last_study_date']
        streak_active = (last_date == date.today()) if last_date else False
        return Response({
            'enrolledCount': len(rows),
            'avgProgress': avg_progress,
            'totalHours': str(round(total_hours, 1)) + 'h',
            'streakDays': summary['streak'],
            'streakActive': streak_active,
            'certificates': summary['certificates'],
        })


class XpByCourseView(APIView):
    def get(self, request):
        """XP tích lũy theo từng khóa — nguồn thật lesson_progress."""
        rows = q('''
            SELECT lp.course_id, c.title, SUM(lp.xp_earned) AS xp
            FROM lesson_progress lp
            LEFT JOIN courses c ON c.id = lp.course_id
            WHERE lp.user_id = %s AND lp.status = 'completed'
            GROUP BY lp.course_id, c.title
            ORDER BY xp DESC
        ''', (request.user.id,))
        return Response({'subjects': [
            {
                'courseId': r['course_id'],
                'title': r['title'] or r['course_id'] or 'Khóa học',
                'xp': int(r['xp'] or 0),
            }
            for r in rows
        ]})


def _verify_mission_by_course(course_id, condition, action):
    """MissionRepository.verify_answer_by_course — frontend gửi mission_id = course_id."""
    return q1('''SELECT * FROM missions
                 WHERE course_id = %s
                   AND correct_condition = %s
                   AND correct_action    = %s
                   AND is_active = TRUE
                 LIMIT 1''', (course_id, condition, action))


class CompleteMissionView(APIView):
    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        mission_id = data.get('mission_id', '')
        condition = data.get('condition', '')
        action = data.get('action', '')

        if not mission_id:
            return Response({'success': False, 'message': 'Thiếu mission_id'}, status=400)

        mission = _verify_mission_by_course(mission_id, condition, action)
        if not mission:
            return Response({'success': False, 'message': 'Câu trả lời chưa đúng, thử lại nhé!'})

        xp_reward = mission['xp_reward']
        uid = request.user.id
        with transaction.atomic():
            user = q1('SELECT gems, xp, streak, last_study_date FROM users WHERE id=%s', (uid,))

            today = date.today()
            last_date = user['last_study_date']
            if last_date is None or last_date < today - timedelta(days=1):
                new_streak = 1          # bỏ học hơn 1 ngày → reset chuỗi về 1
            elif last_date == today:
                new_streak = user['streak']   # đã học hôm nay → giữ nguyên
            else:
                new_streak = user['streak'] + 1   # học hôm qua → tăng chuỗi

            x('UPDATE users SET gems = gems + %s, xp = xp + %s, streak = %s, '
              'last_study_date = %s WHERE id=%s',
              (xp_reward, xp_reward, new_streak, today, uid))
            x('''INSERT INTO user_daily_xp_logs (user_id, log_date, xp_earned)
                 VALUES (%s, %s, %s)
                 ON CONFLICT (user_id, log_date)
                 DO UPDATE SET xp_earned = user_daily_xp_logs.xp_earned + EXCLUDED.xp_earned''',
              (uid, today, xp_reward))
            user = q1('SELECT gems, xp, streak FROM users WHERE id=%s', (uid,))
            check_and_award_achievements(uid)

        return Response({
            'success': True,
            'message': 'Hoàn thành nhiệm vụ!',
            'gems': user['gems'],
            'xp': user['xp'],
            'streak': user['streak'],
            'streak_active': True,
        })


class ReviewQuizStatusView(APIView):
    def get(self, request):
        user = q1('SELECT streak FROM users WHERE id=%s', (request.user.id,))
        streak = user['streak'] if user else 0
        return Response({
            'streak': streak,
            'is_unlocked': streak >= 5,
            'days_remaining': max(0, 5 - streak),
        })


class HsaSummaryView(APIView):
    """GET /api/hsa/summary — 4 chỉ số cho hàng thẻ đầu Dashboard.

    Gộp trong MỘT lượt gọi thay vì bắt client ghép từ 4 endpoint rời
    (audit 2026-08-14). Mọi trường đều có giá trị mặc định an toàn để thẻ
    không bao giờ hiện "undefined" khi học viên chưa có dữ liệu.
    """

    #: Tổng số bài của chương trình HSA (3 khoá × 6 chương = 76 bài).
    TOTAL_LESSONS = 76

    def get(self, request):
        uid = request.user.id

        done = (q1("SELECT COUNT(*) AS n FROM lesson_progress "
                   "WHERE user_id=%s AND status='completed'", (uid,)) or {}).get('n', 0)

        streak_row = q1("SELECT streak FROM users WHERE id=%s", (uid,)) or {}

        # Mục tiêu điểm + mốc thi lấy từ bài khảo sát gần nhất.
        target_score, exam_timing = None, None
        row = q1("SELECT data_json FROM surveys WHERE user_id=%s "
                 "ORDER BY id DESC LIMIT 1", (uid,))
        if row and row.get('data_json'):
            try:
                data = row['data_json']
                if isinstance(data, str):
                    data = json.loads(data)
                target_score = data.get('target_score')
                exam_timing = data.get('exam_timing')
            except Exception:
                pass

        # Điểm đề thi thử gần nhất (thang 150 câu của HSA).
        last_score, last_total = None, None
        att = q1("SELECT score, total FROM mock_attempts "
                 "WHERE user_id=%s ORDER BY submitted_at DESC LIMIT 1", (uid,))
        if att:
            last_score, last_total = att.get('score'), att.get('total')

        return Response({
            'streakDays': streak_row.get('streak') or 0,
            'lessonsDone': done or 0,
            'lessonsTotal': self.TOTAL_LESSONS,
            'targetScore': target_score,
            'examTiming': exam_timing,
            'daysToExam': _days_to_exam(exam_timing),
            'lastMockScore': last_score,
            'lastMockTotal': last_total,
        })


def _days_to_exam(exam_timing):
    """Số ngày còn lại tới kỳ thi.

    Bài khảo sát chỉ hỏi MỐC dự thi dạng "2025"/"đợt 1" chứ không hỏi ngày cụ
    thể, nên quy ước: kỳ thi HSA đợt đầu thường vào cuối tháng 3. Lấy 31/03 của
    năm nêu trong exam_timing (hoặc năm tới nếu đã qua). Không rõ → None để
    thẻ hiện dấu gạch thay vì số bịa.
    """
    if not exam_timing:
        return None
    m = re.search(r'20\d{2}', str(exam_timing))
    today = date.today()
    year = int(m.group()) if m else (today.year if today.month <= 3 else today.year + 1)
    try:
        delta = (date(year, 3, 31) - today).days
    except ValueError:
        return None
    return delta if delta >= 0 else None
