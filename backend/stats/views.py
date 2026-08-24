"""Port routes/stats.py + db/repositories/missions.py (phần verify)."""
import json
import re
from datetime import date, datetime, timedelta

from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from achievements.services import check_and_award_achievements
from common.clock import local_now, local_today
from common.db import q, q1, x
from common.events import KIND_MISSION, record_event
from stats import competency


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
        streak_active = (last_date == local_today()) if last_date else False
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


# ── Nhiệm vụ hằng ngày ──────────────────────────────────────────────────────
# Bản cũ (`_verify_mission_by_course`) chấm nhiệm vụ bằng cặp (correct_condition,
# correct_action) — đó là NHIỆM VỤ SQL của pe_test, vô nghĩa với luyện thi HSA.
# Nay nhiệm vụ chấm bằng số liệu THẬT của học viên trong ngày hôm nay.


def _today_metrics(uid, today):
    """Khoá ở đây phải khớp missions.condition_type do seed_data ghi vào."""
    lessons = (q1("SELECT COUNT(*) AS n FROM lesson_progress "
                  "WHERE user_id=%s AND status='completed' "
                  "AND completed_at::date = %s", (uid, today)) or {}).get('n', 0)
    mocks = (q1("SELECT COUNT(*) AS n FROM mock_attempts "
                "WHERE user_id=%s AND submitted_at::date = %s", (uid, today)) or {}).get('n', 0)
    xp = (q1("SELECT xp_earned AS n FROM user_daily_xp_logs "
             "WHERE user_id=%s AND log_date=%s", (uid, today)) or {}).get('n', 0)
    return {
        'lessons_today': lessons or 0,
        'mocks_today': mocks or 0,
        'xp_today': xp or 0,
    }


def _missions_for(uid, today):
    rows = q('SELECT id, code, title, description, xp_reward, condition_type, '
             'condition_value FROM missions WHERE is_active ORDER BY sort_order, id')
    claimed = {r['mission_id'] for r in q(
        'SELECT mission_id FROM user_missions WHERE user_id=%s AND mission_date=%s',
        (uid, today))}
    metrics = _today_metrics(uid, today)
    out = []
    for m in rows:
        target = m['condition_value'] or 1
        progress = metrics.get(m['condition_type'], 0)
        out.append({
            'id': m['id'],
            'code': m['code'],
            'title': m['title'],
            'description': m['description'] or '',
            'xpReward': m['xp_reward'] or 0,
            'progress': min(progress, target),
            'target': target,
            'done': progress >= target,
            'claimed': m['id'] in claimed,
        })
    return out


class TodayMissionsView(APIView):
    """GET /api/missions/today — 3 nhiệm vụ trong ngày + tiến độ thật."""

    def get(self, request):
        today = local_today()
        missions = _missions_for(request.user.id, today)
        return Response({
            'date': today.isoformat(),
            'missions': missions,
            'allDone': bool(missions) and all(m['claimed'] for m in missions),
        })


class ClaimMissionView(APIView):
    """POST /api/missions/claim {code} — nhận XP thưởng, mỗi ngày một lần.

    Khoá chính (user, mission, ngày) của user_missions lo phần chống nhận trùng:
    INSERT thứ hai trong cùng ngày rơi vào DO NOTHING nên không cộng XP lần nữa.
    """

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        code = (data.get('code') or '').strip()
        if not code:
            return Response({'error': 'Thiếu mã nhiệm vụ.'}, status=400)

        today = local_today()
        uid = request.user.id
        mission = next((m for m in _missions_for(uid, today) if m['code'] == code), None)
        if not mission:
            return Response({'error': 'Không có nhiệm vụ này.'}, status=404)
        if not mission['done']:
            return Response({'error': 'Nhiệm vụ chưa hoàn thành.'}, status=400)
        if mission['claimed']:
            return Response({'error': 'Hôm nay đã nhận thưởng nhiệm vụ này rồi.'}, status=409)

        xp = mission['xpReward']
        with transaction.atomic():
            inserted = q1('''INSERT INTO user_missions
                                 (user_id, mission_id, mission_date, xp_earned)
                             VALUES (%s, %s, %s, %s)
                             ON CONFLICT (user_id, mission_id, mission_date) DO NOTHING
                             RETURNING mission_id''', (uid, mission['id'], today, xp))
            if not inserted:
                return Response({'error': 'Hôm nay đã nhận thưởng nhiệm vụ này rồi.'}, status=409)
            x('UPDATE users SET xp = xp + %s, gems = gems + %s WHERE id=%s', (xp, xp, uid))
            x('''INSERT INTO user_daily_xp_logs (user_id, log_date, xp_earned)
                 VALUES (%s, %s, %s)
                 ON CONFLICT (user_id, log_date)
                 DO UPDATE SET xp_earned = user_daily_xp_logs.xp_earned + EXCLUDED.xp_earned''',
              (uid, today, xp))
            # Nhiệm vụ không chấm điểm (score để trống) nhưng vẫn là bằng chứng
            # "hôm nay có học" — đường cong thời lượng và chuỗi ngày đọc tới.
            record_event(uid, KIND_MISSION, f'mission:{mission["id"]}:{today.isoformat()}',
                         occurred_at=local_now(), ref_type='mission',
                         ref_id=str(mission['id']), xp=xp,
                         meta={'code': mission['code'], 'title': mission['title']})
            newly = check_and_award_achievements(uid)

        return Response({
            'ok': True,
            'xpGained': xp,
            'missions': _missions_for(uid, today),
            'newAchievements': newly,
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
    today = local_today()

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
            data['exam_timing_set_at'] = local_today().isoformat()
        payload = json.dumps(data, ensure_ascii=False)
        if row:
            x("UPDATE surveys SET data_json=%s WHERE id=%s", (payload, row['id']))
        else:
            x("INSERT INTO surveys (user_id, data_json, created_at) VALUES (%s, %s, %s)",
              (uid, payload, datetime.utcnow().isoformat()))
        return Response({k: data.get(k) for k in self.FIELDS})


class CompetencyView(APIView):
    """GET /api/hsa/competency — bản đồ năng lực 20 ô (khoá × chủ đề).

    Xem stats/competency.py để biết cách chấm và vì sao ô chưa đủ dữ liệu phải
    để trống thay vì hiện 0%.
    """

    def get(self, request):
        return Response(competency.compute(request.user.id))


class TopicSelfMarkView(APIView):
    """PUT /api/hsa/competency/self — học viên tự đánh dấu đã nắm một chủ đề.

    Body ``{courseId, topic, known}``. Đặc tả ban đầu viết chủ đề vào đường dẫn
    (``/competency/<topic>/self``) nhưng tên chủ đề là tiếng Việt có dấu VÀ
    "Chiến thuật" tồn tại ở cả ba hợp phần — đường dẫn vừa phải mã hoá phần trăm
    vừa không nói được thuộc khoá nào. Đưa cả cặp xuống body là cách gọn và
    không nhập nhằng.

    Tự đánh dấu KHÔNG làm thay đổi điểm thành thạo: nó là đầu vào để xếp lịch ôn
    (hạ ưu tiên chủ đề đã nắm), không phải bằng chứng về năng lực.
    """

    def put(self, request):
        body = request.data if isinstance(request.data, dict) else {}
        course_id = (body.get('courseId') or body.get('course') or '').strip()
        topic = (body.get('topic') or '').strip()
        known = body.get('known')
        if not course_id or not topic:
            return Response({'error': 'Thiếu courseId hoặc topic.'}, status=400)
        if not isinstance(known, bool):
            return Response({'error': '"known" phải là true hoặc false.'}, status=400)
        # Chỉ nhận chủ đề có thật trong giáo trình — chặn rác vào bảng.
        if not q1('SELECT 1 FROM lessons WHERE course_id=%s AND module=%s LIMIT 1',
                  (course_id, topic)):
            return Response({'error': 'Không có chủ đề này trong khoá học.'}, status=404)

        x('''INSERT INTO topic_self_marks (user_id, course_id, topic, known, marked_at)
             VALUES (%s, %s, %s, %s, %s)
             ON CONFLICT (user_id, course_id, topic)
             DO UPDATE SET known = EXCLUDED.known, marked_at = EXCLUDED.marked_at''',
          (request.user.id, course_id, topic, known, local_now()))
        return Response({'ok': True, 'courseId': course_id, 'topic': topic, 'known': known})
