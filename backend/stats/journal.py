"""Nhật ký học hằng ngày + mục tiêu tuần — phần học viên TỰ ghi nhận.

Hệ thống đo được điểm số và thời lượng làm bài trong ứng dụng. Nó KHÔNG đo được
thứ quyết định nhất: học viên thấy phần nào khó, vướng chỗ nào, hôm nay có ngồi
học ngoài ứng dụng hay không. Đó là dữ liệu chỉ người học mới có, và cũng là thứ
làm trợ lý AI tư vấn được sát hơn nhiều so với chỉ nhìn điểm.

RANH GIỚI KHÔNG ĐƯỢC XOÁ NHOÀ: mọi thứ ở đây là **số tự khai**. Nó đi vào
``learning_events`` với ``source='self'`` và mọi nơi hiển thị phải tách nó khỏi
số hệ thống đo được. Trộn hai loại vào một con số là cách nhanh nhất làm mất tin
cậy của toàn bộ phần số liệu — và một khi đã mất thì không lấy lại được.
"""
import json
from datetime import timedelta

from django.db import DatabaseError

from common.clock import local_now, local_today
from common.db import q, q1, x
from common.events import (KIND_LESSON, KIND_MOCK, KIND_SELF_LOG, SOURCE_SELF,
                           forget_events,
                           record_event)
from common.params import so_nguyen
from stats.goals import as_date, read_goals

#: Mức khó học viên tự chấm. Ba bậc là đủ; nhiều hơn chỉ khiến người ta chọn bừa.
DIFFICULTIES = ('easy', 'ok', 'hard')
DIFFICULTY_LABELS = {'easy': 'Dễ thở', 'ok': 'Vừa sức', 'hard': 'Khó'}

#: Trần cho số tự khai. Không phải để nghi ngờ học viên, mà để một lần gõ nhầm
#: không kéo lệch cả biểu đồ thời lượng của họ.
MAX_MINUTES = 16 * 60
MAX_TEXT = 500
#: Số ngày nhật ký trả về mặc định.
DEFAULT_DAYS = 30
MAX_DAYS = 180

TARGET_LIMITS = {'lessons': (0, 100), 'mocks': (0, 20), 'minutes': (0, 5000)}

#: Hai tuần cuối trước kỳ thi dành cho luyện đề, không nạp bài mới.
FINAL_DRILL_WEEKS = 2
#: Chưa biết ngày thi thì lấy mốc này để còn gợi ý được điều gì đó.
FALLBACK_WEEKS = 12
#: Thời lượng trung bình một bài khi giáo trình chưa khai (phút).
FALLBACK_LESSON_MINUTES = 20
#: Một lượt thi thử HSA đầy đủ ~150 phút; đề rút gọn hiện tại ngắn hơn nhiều,
#: nên lấy mốc vừa phải để không thổi phồng thời gian đã dành cho luyện đề.
MOCK_MINUTES = 90


def _monday(d):
    return d - timedelta(days=d.weekday())


# ── Nhật ký ─────────────────────────────────────────────────────────────────

def _clean_text(value):
    if value is None:
        return None
    value = str(value).strip()
    return value[:MAX_TEXT] or None


def _row_out(r):
    return {
        'date': r['log_date'].isoformat(),
        'minutes': r['minutes'],
        'topic': r['topic'],
        'what': r['what'],
        'difficulty': r['difficulty'],
        'difficultyLabel': DIFFICULTY_LABELS.get(r['difficulty']),
        'note': r['note'],
    }


def recent_logs(uid, days=DEFAULT_DAYS):
    days = so_nguyen(days, DEFAULT_DAYS, 1, MAX_DAYS)
    since = local_today() - timedelta(days=days - 1)
    try:
        rows = q('''SELECT log_date, minutes, topic, what, difficulty, note
                    FROM study_logs
                    WHERE user_id = %s AND log_date >= %s
                    ORDER BY log_date DESC''', (uid, since))
    except DatabaseError:
        return []
    return [_row_out(r) for r in rows]


def save_log(uid, payload):
    """Ghi (hoặc sửa) nhật ký của một ngày. Trả về (bản ghi, lỗi)."""
    day = as_date(payload.get('date')) or local_today()
    if day > local_today():
        return None, 'Không ghi nhật ký cho ngày trong tương lai được.'

    minutes = payload.get('minutes')
    if minutes in (None, ''):
        minutes = None
    else:
        try:
            minutes = int(minutes)
        except (TypeError, ValueError):
            return None, 'Số phút phải là một số nguyên.'
        if minutes < 0 or minutes > MAX_MINUTES:
            return None, 'Số phút phải nằm trong khoảng 0–%d.' % MAX_MINUTES

    difficulty = (payload.get('difficulty') or '').strip().lower() or None
    if difficulty and difficulty not in DIFFICULTIES:
        return None, 'Mức độ phải là một trong: %s.' % ', '.join(DIFFICULTIES)

    topic = _clean_text(payload.get('topic'))
    what = _clean_text(payload.get('what'))
    note = _clean_text(payload.get('note'))

    # Bản ghi rỗng hoàn toàn thì không lưu — nó chỉ làm nhiễu danh sách.
    if minutes is None and not any((topic, what, note, difficulty)):
        return None, 'Hãy điền ít nhất một thông tin (số phút, nội dung hoặc ghi chú).'

    now = local_now()
    row = q1('''INSERT INTO study_logs
                    (user_id, log_date, minutes, topic, what, difficulty, note,
                     created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, log_date) DO UPDATE SET
                    minutes    = EXCLUDED.minutes,
                    topic      = EXCLUDED.topic,
                    what       = EXCLUDED.what,
                    difficulty = EXCLUDED.difficulty,
                    note       = EXCLUDED.note,
                    updated_at = EXCLUDED.updated_at
                RETURNING log_date, minutes, topic, what, difficulty, note''',
             (uid, day, minutes, topic, what, difficulty, note, now, now))

    # Sự kiện đi kèm: source='self' để mọi biểu đồ tách được số tự khai.
    # KHÔNG có score/max_score — nhật ký không phải một phép đo năng lực.
    record_event(uid, KIND_SELF_LOG, _selflog_key(day),
                 occurred_at=now, event_date=day, topic=topic,
                 ref_type='study_log', ref_id=day.isoformat(),
                 minutes=minutes, source=SOURCE_SELF,
                 meta={'difficulty': difficulty, 'what': what})
    return _row_out(row), None


def _selflog_key(day):
    """Khoá dedup của một ngày nhật ký tự ghi — MỘT chỗ đặt, dùng cho cả ghi lẫn xoá.

    Trước 30/08/2026 chuỗi này được dựng lại ở hai nơi. Đổi tiền tố ở chỗ ghi mà
    quên chỗ xoá thì lệnh xoá nhật ký ngày sẽ im lặng không xoá gì, và dòng sự
    kiện tự khai tồn tại vĩnh viễn cho một bản ghi đã bị xoá.
    """
    return 'selflog:%s' % day.isoformat()


def delete_log(uid, day):
    day = as_date(day)
    if not day:
        return False
    x('DELETE FROM study_logs WHERE user_id=%s AND log_date=%s', (uid, day))
    # Đi qua common/events.py chứ không tự viết DELETE: đó là cửa DUY NHẤT được
    # đụng vào learning_events, cả ghi lẫn xoá. Câu DELETE cũ ở đây còn tự dựng
    # lại chuỗi dedup_key, nên luật đặt tên khoá nằm ở hai nơi.
    forget_events(user_id=uid, dedup_key=_selflog_key(day))
    return True


# ── Mục tiêu tuần ───────────────────────────────────────────────────────────

def _clamp_target(payload):
    out = {}
    for key, (lo, hi) in TARGET_LIMITS.items():
        val = payload.get(key)
        if val in (None, ''):
            continue
        try:
            val = int(val)
        except (TypeError, ValueError):
            return None, '"%s" phải là một số nguyên.' % key
        out[key] = max(lo, min(hi, val))
    if not out:
        return None, 'Cần ít nhất một trong: lessons, mocks, minutes.'
    return out, None


def read_target(uid):
    """Mục tiêu tuần đang hoạt động. Chưa đặt → None (không bịa mục tiêu hộ)."""
    try:
        row = q1('SELECT weekly_target FROM study_plans '
                 'WHERE user_id=%s AND is_active LIMIT 1', (uid,))
    except DatabaseError:
        return None
    if not row or not row.get('weekly_target'):
        return None
    target = row['weekly_target']
    if isinstance(target, str):
        try:
            target = json.loads(target)
        except ValueError:
            return None
    return target if isinstance(target, dict) else None


def save_target(uid, payload):
    target, err = _clamp_target(payload)
    if err:
        return None, err
    now = local_now()
    x('''INSERT INTO study_plans (user_id, created_at, updated_at, weekly_target, is_active)
         VALUES (%s, %s, %s, %s::jsonb, TRUE)
         ON CONFLICT (user_id) WHERE is_active
         DO UPDATE SET weekly_target = EXCLUDED.weekly_target,
                       updated_at    = EXCLUDED.updated_at''',
      (uid, now, now, json.dumps(target, ensure_ascii=False)))
    return target, None



# ── Mục tiêu tuần do HỆ THỐNG đề xuất ───────────────────────────────────────
# Hướng sản phẩm là System-Guided + Adaptive: hệ thống thiết kế mục tiêu từng
# giai đoạn, rồi tự chỉnh theo tình trạng thật của người học. Một hằng số
# "5 bài/tuần" cho mọi người là phản lại cả hai vế đó — người còn 3 tuần và
# người còn 8 tháng không thể chung một mục tiêu.
#
# Ba ràng buộc dùng để suy ra con số:
#   1. Số bài CÒN LẠI phải hết trước kỳ thi, chừa 2 tuần cuối luyện đề.
#   2. SỨC CHỨA thật = số phút mỗi ngày học viên tự khai x 7 / thời lượng một bài.
#   3. Không đủ sức chứa thì NÓI THẲNG, không lặng lẽ hạ mục tiêu xuống cho vừa.

def _lesson_stats(uid):
    """Tổng số bài, số đã xong, thời lượng trung bình — gộp trong MỘT lượt hỏi."""
    row = q1("""SELECT
            (SELECT COUNT(*) FROM lessons
              WHERE course_id IS NOT NULL AND module IS NOT NULL AND module <> '') AS total,
            (SELECT COUNT(*) FROM lesson_progress
              WHERE user_id = %s AND status = 'completed')                         AS done,
            (SELECT COALESCE(AVG(estimated_minutes), 0) FROM lessons
              WHERE estimated_minutes IS NOT NULL)                                 AS avg_minutes""",
             (uid,)) or {}
    total = int(row.get('total') or 0)
    done = min(int(row.get('done') or 0), total)
    avg = int(row.get('avg_minutes') or 0) or FALLBACK_LESSON_MINUTES
    return total, done, avg


def suggest_target(uid, goals=None):
    """Mục tiêu tuần hệ thống đề xuất, kèm LÝ DO và cảnh báo nếu không kịp.

    Lý do đi kèm không phải để cho đẹp: một mục tiêu do hệ thống áp xuống mà
    không nói vì sao thì người học không có cơ sở nào để tin, và bỏ ngay tuần đầu.
    """
    goals = goals or read_goals(uid)
    total, done, avg_minutes = _lesson_stats(uid)
    left = max(0, total - done)

    days = goals.get('daysToExam')
    # `is not None` chứ KHÔNG phải `if days`: ngày thi HÔM NAY cho `days = 0`,
    # mà `0` là falsy. Hệ quả đo được: còn 1 ngày → chế độ báo động (3 đề/tuần,
    # cảnh báo "bỏ N bài"); còn 0 ngày → chế độ thư thả (1 đề/tuần, cảnh báo
    # biến mất, lịch trải 12 tuần). Đúng cái ngày cần siết nhất thì hệ nới ra.
    weeks_left = max(1, -(-days // 7)) if days is not None else None
    # Tuần dành cho bài mới = tổng trừ giai đoạn luyện đề cuối.
    build_weeks = max(1, (weeks_left or FALLBACK_WEEKS) - FINAL_DRILL_WEEKS)

    needed = -(-left // build_weeks) if left else 0        # làm tròn LÊN
    daily = goals.get('dailyMinutes')

    # Càng gần ngày thi càng nặng luyện đề; còn xa thì một đề mỗi tuần là đủ.
    if weeks_left and weeks_left <= FINAL_DRILL_WEEKS:
        mocks = 3
    elif weeks_left and weeks_left <= 6:
        mocks = 2
    else:
        mocks = 1

    # Sức chứa cho BÀI HỌC = quỹ thời gian tuần TRỪ thời gian làm đề. Không trừ
    # thì hệ thống hứa cả bài lẫn đề trên cùng một quỹ thời gian, và mục tiêu
    # trượt ngay tuần đầu — mục tiêu do hệ thống áp xuống mà không đạt nổi thì
    # tệ hơn là không có mục tiêu.
    capacity = None
    if daily:
        for_lessons = max(0, daily * 7 - mocks * MOCK_MINUTES)
        capacity = max(1, int(for_lessons / avg_minutes))

    lessons = needed or 1
    if capacity:
        lessons = max(1, min(lessons, capacity))
    lessons = min(lessons, TARGET_LIMITS['lessons'][1])

    minutes = daily * 7 if daily else lessons * avg_minutes + mocks * MOCK_MINUTES

    why = []
    if weeks_left and left:
        why.append('còn %d tuần tới kỳ thi và %d bài chưa học' % (weeks_left, left))
    elif left:
        why.append('còn %d bài chưa học (chưa đặt mốc thi nên tạm tính %d tuần)'
                   % (left, FALLBACK_WEEKS))
    if daily:
        why.append('bạn khai ôn được %d phút/ngày' % daily)

    warning = None
    if capacity and needed > capacity:
        thieu = left - capacity * build_weeks
        warning = ('Với %d phút/ngày bạn làm được khoảng %d bài/tuần, mà cần %d bài/tuần '
                   'mới hết %d bài trước kỳ thi. Hoặc tăng giờ ôn, hoặc chấp nhận bỏ '
                   'khoảng %d bài ít trọng số nhất.'
                   % (daily, capacity, needed, left, max(0, thieu)))

    return {
        'lessons': lessons, 'mocks': mocks, 'minutes': int(minutes),
        'why': ' · '.join(why) or None,
        'warning': warning,
        'basis': {
            'weeksLeft': weeks_left, 'buildWeeks': build_weeks,
            'lessonsLeft': left, 'lessonsTotal': total,
            'neededPerWeek': needed, 'capacityPerWeek': capacity,
            'dailyMinutes': daily, 'avgLessonMinutes': avg_minutes,
        },
    }


def target_gap(target, suggestion):
    """Mục tiêu học viên tự đặt có kịp không? Trả câu nhắc, hoặc None nếu ổn.

    Đây là vế adaptive: hệ thống không im lặng chấp nhận một mục tiêu sẽ trượt.
    """
    if not target or not suggestion:
        return None
    needed = (suggestion.get('basis') or {}).get('neededPerWeek') or 0
    mine = target.get('lessons')
    if mine is None or not needed or mine >= needed:
        return None
    basis = suggestion['basis']
    return ('Mục tiêu %d bài/tuần chưa đủ: còn %d bài và %d tuần học, '
            'cần %d bài/tuần mới kịp.'
            % (mine, basis['lessonsLeft'], basis['buildWeeks'], needed))


def week_progress(uid, target=None):
    """Đối chiếu tuần này với mục tiêu. Phút TỰ KHAI đếm riêng phút hệ thống đo.

    Trả về cả hai con số phút chứ không cộng gộp: học viên phải nhìn ra được bao
    nhiêu là do mình khai, bao nhiêu là hệ thống bấm giờ.
    """
    start = _monday(local_today())
    try:
        row = q1('''SELECT
                COUNT(*) FILTER (WHERE kind = %s)                       AS lessons,
                COUNT(*) FILTER (WHERE kind = %s)                       AS mocks,
                COALESCE(SUM(minutes) FILTER (WHERE source <> %s), 0)   AS sys_minutes,
                COALESCE(SUM(minutes) FILTER (WHERE source =  %s), 0)   AS self_minutes,
                COUNT(*)                                               AS events
            FROM learning_events
            WHERE user_id = %s AND event_date >= %s''',
                 (KIND_LESSON, KIND_MOCK, SOURCE_SELF, SOURCE_SELF, uid, start)) or {}
    except DatabaseError:
        row = {}

    sys_min = int(row.get('sys_minutes') or 0)
    self_min = int(row.get('self_minutes') or 0)
    done = {
        'lessons': int(row.get('lessons') or 0),
        'mocks': int(row.get('mocks') or 0),
        'minutes': sys_min + self_min,
    }
    out = {
        'weekStart': start.isoformat(),
        'done': done,
        'systemMinutes': sys_min,
        'selfMinutes': self_min,
        'events': int(row.get('events') or 0),
        'target': target,
        'met': None,
    }
    if target:
        out['met'] = all(done.get(k, 0) >= v for k, v in target.items() if v)
    return out


def overview(uid, days=DEFAULT_DAYS):
    """Cả khối nhật ký trong MỘT lượt gọi.

    Mỗi lượt truy vấn tới Neon tốn ~245ms thuần đường truyền, nên gộp bốn thứ mà
    màn hình luôn hiện cùng nhau vào một endpoint là cách rẻ nhất để nó mở nhanh.
    """
    target = read_target(uid)
    logs = recent_logs(uid, days)
    suggestion = suggest_target(uid)
    today = local_today().isoformat()
    return {
        'today': next((l for l in logs if l['date'] == today), None),
        'todayDate': today,
        'recent': logs,
        'target': target,
        # Đề xuất của hệ thống, tính lại theo tình trạng thật — KHÔNG tự lưu.
        # Chưa đặt thì màn hình nói là chưa đặt, và bày đề xuất kèm lý do.
        'suggestion': suggestion,
        'targetGap': target_gap(target, suggestion),
        'week': week_progress(uid, target),
        'difficulties': [{'value': d, 'label': DIFFICULTY_LABELS[d]} for d in DIFFICULTIES],
    }
