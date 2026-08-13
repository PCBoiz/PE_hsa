"""Port routes/stats.py + db/repositories/missions.py (phần verify)."""
import json
import re
from datetime import date, datetime, timedelta

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

        # Đếm theo từng khoá luôn: dải tiến độ 3 hợp phần trước đây đọc
        # enrollments.progress — bộ nhớ đệm chỉ được cập nhật khi học viên ĐÃ
        # ghi danh, nên người học thẳng từ lộ trình thấy 0% dù đã xong bài.
        per_course = {r['course_id']: r['n'] for r in q(
            "SELECT course_id, COUNT(*) AS n FROM lesson_progress "
            "WHERE user_id=%s AND status='completed' GROUP BY course_id", (uid,))}
        done = sum(per_course.values())

        streak_row = q1("SELECT streak FROM users WHERE id=%s", (uid,)) or {}

        # Mục tiêu điểm + mốc thi lấy từ bài khảo sát gần nhất.
        target_score, exam_timing, exam_date, timing_set_at = None, None, None, None
        row = q1("SELECT data_json, created_at FROM surveys WHERE user_id=%s "
                 "ORDER BY id DESC LIMIT 1", (uid,))
        if row and row.get('data_json'):
            try:
                data = row['data_json']
                if isinstance(data, str):
                    data = json.loads(data)
                target_score = data.get('target_score')
                exam_timing = data.get('exam_timing')
                exam_date = data.get('exam_date')
                timing_set_at = data.get('exam_timing_set_at')
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
            'byCourse': per_course,
            'targetScore': target_score,
            'examTiming': exam_timing,
            'examDate': exam_date,
            'daysToExam': _days_to_exam(exam_timing, exam_date,
                                        timing_set_at or (row or {}).get('created_at')),
            'lastMockScore': last_score,
            'lastMockTotal': last_total,
        })


#: Câu "Bạn dự định thi HSA khi nào?" trong khảo sát trả về KHOẢNG thời gian
#: tương đối chứ không phải năm ("Trong 1 tháng", "1–3 tháng"...). Quy mỗi
#: khoảng về số ngày tới CUỐI khoảng đó.
_TIMING_DAYS = (
    (re.compile(r'trong\s*1\s*th[áa]ng', re.I), 30),
    (re.compile(r'1\s*[-–—]\s*3\s*th[áa]ng', re.I), 90),
    (re.compile(r'3\s*[-–—]\s*6\s*th[áa]ng', re.I), 180),
    (re.compile(r'tr[êe]n\s*6\s*th[áa]ng', re.I), 240),
)


def _as_date(value):
    """date/datetime/chuỗi 'YYYY-MM-DD' (hoặc ISO) → date. Không parse được → None."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)[:19].replace(' ', 'T')).date()
    except ValueError:
        return None


def _days_to_exam(exam_timing, exam_date=None, answered_at=None):
    """Số ngày còn lại tới kỳ thi, theo thứ tự ưu tiên nguồn dữ liệu.

    1. ``exam_date`` — ngày thi học viên tự nhập ở Cài đặt → chính xác tuyệt đối.
    2. ``exam_timing`` có ghi năm ("đợt 1/2027") → quy ước kỳ thi đợt đầu cuối
       tháng 3 của năm đó (năm sau nếu đã qua).
    3. ``exam_timing`` là khoảng tương đối → neo vào NGÀY LÀM KHẢO SÁT rồi cộng
       độ dài khoảng. Neo vào hôm nay thì con số đứng yên mãi mãi, không bao giờ
       đếm ngược — người trả lời "Trong 1 tháng" từ nửa năm trước vẫn thấy 30.

    Không suy ra được → None để thẻ hiện dấu gạch kèm nút sửa mốc thi, thay vì
    một con số bịa.
    """
    today = date.today()

    d = _as_date(exam_date)
    if d:
        delta = (d - today).days
        return delta if delta >= 0 else None

    if not exam_timing:
        return None
    s = str(exam_timing)

    m = re.search(r'20\d{2}', s)
    if m:
        for y in (int(m.group()), int(m.group()) + 1):
            try:
                delta = (date(y, 3, 31) - today).days
            except ValueError:
                return None
            if delta >= 0:
                return delta
        return None

    anchor = _as_date(answered_at) or today
    for rx, days in _TIMING_DAYS:
        if rx.search(s):
            delta = (anchor + timedelta(days=days) - today).days
            return delta if delta >= 0 else None
    return None


class HsaGoalsView(APIView):
    """GET/PATCH /api/hsa/goals — mục tiêu HSA của học viên.

    Điểm mục tiêu, mốc dự thi và 3 môn Khoa học tự chọn trước đây chỉ đặt được
    MỘT LẦN lúc làm khảo sát, dù chúng nuôi thẻ đếm ngược ở dashboard và lộ
    trình cá nhân hoá (audit 2026-08-14). Lưu chung vào bản khảo sát gần nhất
    để không phải đổi schema; chưa có khảo sát thì tạo một bản mới.
    """

    #: ``exam_date`` không có trong khảo sát — thêm ở Cài đặt cho học viên đã
    #: biết ngày thi chính xác, để thẻ đếm ngược khỏi phải đoán từ khoảng tương đối.
    FIELDS = ('target_score', 'exam_timing', 'section3_choice', 'exam_date')

    def _latest(self, uid):
        return q1("SELECT id, data_json FROM surveys WHERE user_id=%s "
                  "ORDER BY id DESC LIMIT 1", (uid,))

    @staticmethod
    def _as_dict(row):
        data = (row or {}).get('data_json') or {}
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}
        return data if isinstance(data, dict) else {}

    def get(self, request):
        data = self._as_dict(self._latest(request.user.id))
        return Response({k: data.get(k) for k in self.FIELDS})

    def patch(self, request):
        body = request.data if isinstance(request.data, dict) else {}
        # Chỉ nhận đúng các trường mục tiêu; phần còn lại của khảo sát giữ nguyên.
        updates = {k: str(body[k])[:120] for k in self.FIELDS if body.get(k) not in (None, '')}
        # Xoá ngày thi: gửi exam_date rỗng → quay về suy ra từ mốc tương đối.
        if 'exam_date' in body and not body.get('exam_date'):
            updates['exam_date'] = None
        elif 'exam_date' in updates and not _as_date(updates['exam_date']):
            return Response({'error': 'Ngày thi không hợp lệ (định dạng YYYY-MM-DD).'}, status=400)
        if not updates:
            return Response({'error': 'Không có trường hợp lệ để cập nhật.'}, status=400)

        uid = request.user.id
        row = self._latest(uid)
        data = self._as_dict(row)
        data.update(updates)
        # Mốc tương đối ("Trong 1 tháng") được tính từ lúc học viên NÓI ra nó.
        # Không ghi lại thời điểm này thì mốc mãi neo vào ngày làm khảo sát —
        # sửa lại sau nửa năm sẽ ra số ngày âm.
        if 'exam_timing' in updates:
            data['exam_timing_set_at'] = date.today().isoformat()
        payload = json.dumps(data, ensure_ascii=False)
        if row:
            x("UPDATE surveys SET data_json=%s WHERE id=%s", (payload, row['id']))
        else:
            x("INSERT INTO surveys (user_id, data_json, created_at) VALUES (%s, %s, %s)",
              (uid, payload, datetime.utcnow().isoformat()))
        return Response({k: data.get(k) for k in self.FIELDS})
