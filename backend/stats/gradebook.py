"""Sổ điểm & đường cong tiến bộ — đọc lại ``learning_events``, không thêm bảng.

Trả lời câu hỏi thứ hai của thí sinh, sau "tôi yếu ở đâu": **"mấy tuần qua tôi
có khá lên không, và còn cách đích bao xa?"**

Ba quyết định đáng ghi lại:

1. **Đường điểm và cột thời lượng KHÔNG chung một trục.** "Học 300 phút" và
   "đúng 62%" là hai đơn vị khác nhau; ép chung một thang là vẽ ra một tương
   quan không có thật. Cột thời lượng nằm nền, thang riêng, chỉ để mắt tự nối
   "tuần học nhiều ↔ điểm lên".
2. **Xu hướng chỉ vẽ khi có từ 3 lượt thi trở lên.** Nối hai điểm rồi gọi là xu
   hướng là trò lừa thị giác kinh điển: hai điểm luôn thẳng hàng.
3. **Số tự khai tách riêng khỏi số đo được** (`source`), kể cả khi hiện tại chưa
   có nguồn tự khai nào — trụ cột 4 sẽ đổ vào đúng chỗ này.
"""
import json
from datetime import timedelta

from django.db import DatabaseError

from common.clock import local_today
from common.db import q
from common.events import (
    KIND_DRILL,
    KIND_LESSON,
    KIND_MISSION,
    KIND_MOCK,
    KIND_REVIEW_QUIZ,
    SOURCE_SELF,
)
from common.params import so_nguyen
from stats.goals import HSA_MAX_SCORE, read_goals, target_band

#: Số tuần mặc định trên đường cong. 12 tuần ≈ một mùa ôn thi.
DEFAULT_WEEKS = 12
#: Sàn 4 tuần: dưới ngần ấy thì đường cong chỉ còn vài điểm, nhìn ra xu hướng là
#: nhìn ra ảo giác. Trước đây con số này chôn trong `max(4, ...)` giữa thân hàm.
MIN_WEEKS = 4
MAX_WEEKS = 52
#: Dưới ngần này lượt thi thử thì KHÔNG vẽ đường xu hướng (xem chú thích ở đầu).
MIN_POINTS_FOR_TREND = 3
#: Trần số dòng sổ điểm trả về một lượt.
DEFAULT_ROWS = 40
MAX_ROWS = 200

KIND_LABELS = {
    KIND_LESSON: 'Kiểm tra đầu vào',
    KIND_DRILL: 'Phòng luyện tốc độ',
    KIND_REVIEW_QUIZ: 'Quiz ôn tập',
    KIND_MOCK: 'Thi thử',
    KIND_MISSION: 'Nhiệm vụ ngày',
}
#: Thứ tự các loại trong bảng tổng hợp — quan trọng nhất trước.
KIND_ORDER = (KIND_MOCK, KIND_LESSON, KIND_DRILL, KIND_REVIEW_QUIZ)


def _as_json(value):
    """Cột JSONB đọc qua cursor thô có khi trả về CHUỖI, có khi trả về dict —
    tuỳ đường ghi. Không parse lại thì mọi nhãn lấy từ meta im lặng biến thành
    giá trị mặc định (đã dính: sổ điểm hiện "Bài học" thay vì tên bài thật)."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return {}
    return value if isinstance(value, dict) else {}


def _pct(score, max_score):
    try:
        score, max_score = float(score), float(max_score)
    except (TypeError, ValueError):
        return None
    if max_score <= 0:
        return None
    return max(0.0, min(100.0, score * 100.0 / max_score))


def _monday(d):
    return d - timedelta(days=d.weekday())


def _row_label(kind, meta):
    """Tên hoạt động hiện trong sổ điểm. Không có tiêu đề thì dùng số bài."""
    meta = _as_json(meta)
    title = (meta.get('title') or '').strip()
    no = meta.get('lessonNo')
    if kind in (KIND_LESSON, KIND_DRILL):
        base = title or (('Bài %s' % no) if no else 'Bài học')
        return base if kind == KIND_LESSON else ('Luyện tốc độ · ' + base)
    if kind == KIND_MOCK:
        return 'Đề thi thử'
    if kind == KIND_REVIEW_QUIZ:
        return 'Quiz ôn tập'
    return KIND_LABELS.get(kind, kind)


def gradebook(uid, limit=DEFAULT_ROWS):
    """Mọi hoạt động CÓ CHẤM ĐIỂM, mới nhất trước, kèm tổng hợp theo loại.

    ``mock_section`` cố ý không xuất hiện: nó là bản chi tiết của cùng lượt thi
    đã có ở dòng ``mock``, hiện cả hai là đếm một lượt thi bốn lần.
    """
    limit = so_nguyen(limit, DEFAULT_ROWS, 1, MAX_ROWS)
    kinds = [KIND_MOCK, KIND_LESSON, KIND_DRILL, KIND_REVIEW_QUIZ]
    try:
        rows = q('''SELECT kind, course_id, topic, score, max_score, minutes,
                           occurred_at, event_date, source, meta
                    FROM learning_events
                    WHERE user_id = %s AND kind = ANY(%s)
                      AND max_score IS NOT NULL AND max_score > 0
                    ORDER BY occurred_at DESC
                    LIMIT %s''', (uid, kinds, limit))
        totals = q('''SELECT kind, COUNT(*) AS n,
                             SUM(score) AS s, SUM(max_score) AS m
                      FROM learning_events
                      WHERE user_id = %s AND kind = ANY(%s)
                        AND max_score IS NOT NULL AND max_score > 0
                      GROUP BY kind''', (uid, kinds))
    except DatabaseError:
        return {'rows': [], 'byKind': [], 'hint': 'Chưa có dữ liệu học tập nào.'}

    titles = _course_titles()
    out_rows = []
    for r in rows:
        out_rows.append({
            'kind': r['kind'],
            'kindLabel': KIND_LABELS.get(r['kind'], r['kind']),
            'label': _row_label(r['kind'], r['meta']),
            'course': r['course_id'],
            'courseTitle': titles.get(r['course_id']),
            'topic': r['topic'],
            'score': float(r['score']) if r['score'] is not None else None,
            'max': float(r['max_score']),
            'pct': round(_pct(r['score'], r['max_score']) or 0),
            'minutes': r['minutes'],
            'at': r['occurred_at'].isoformat() if r['occurred_at'] else None,
            'selfReported': r['source'] == SOURCE_SELF,
        })

    by_kind = []
    by_id = {t['kind']: t for t in totals}
    for kind in KIND_ORDER:
        t = by_id.get(kind)
        if not t or not t['n']:
            continue
        by_kind.append({
            'kind': kind,
            'label': KIND_LABELS.get(kind, kind),
            'n': t['n'],
            # Trung bình theo TỔNG số câu, không phải trung bình của các phần
            # trăm: một quiz 8 câu và một đề 150 câu không được cân bằng nhau.
            'avgPct': round(_pct(t['s'], t['m']) or 0),
        })

    return {
        'rows': out_rows,
        'byKind': by_kind,
        'hint': None if out_rows else 'Chưa có hoạt động nào được chấm điểm.',
    }


def _course_titles():
    try:
        return {r['id']: r['title'] for r in q('SELECT id, title FROM courses')}
    except DatabaseError:
        return {}


def _trend(points):
    """Hồi quy tuyến tính đơn giản trên các lượt thi thử → (điểm đầu, điểm cuối).

    Trả None khi chưa đủ điểm: xem chú thích 2 ở đầu module.
    """
    n = len(points)
    if n < MIN_POINTS_FOR_TREND:
        return None
    xs = [p['x'] for p in points]
    ys = [p['pct'] for p in points]
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:                      # mọi lượt thi cùng một ngày
        return None
    slope = sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / den
    x0, x1 = min(xs), max(xs)
    return {
        'fromPct': round(my + slope * (x0 - mx), 1),
        'toPct': round(my + slope * (x1 - mx), 1),
        'perWeek': round(slope * 7, 2),
        'x0': x0,
        'x1': x1,
    }


def progress_curve(uid, weeks=DEFAULT_WEEKS):
    """Đường cong tiến bộ: điểm thi thử theo thời gian + thời lượng học mỗi tuần."""
    weeks = so_nguyen(weeks, DEFAULT_WEEKS, MIN_WEEKS, MAX_WEEKS)
    today = local_today()
    first_monday = _monday(today) - timedelta(weeks=weeks - 1)

    try:
        rows = q('''SELECT kind, score, max_score, minutes, occurred_at, event_date,
                           source, meta
                    FROM learning_events
                    WHERE user_id = %s AND event_date >= %s''', (uid, first_monday))
    except DatabaseError:
        rows = []

    # Khung tuần dựng sẵn: tuần không học phải là một cột TRỐNG nhìn thấy được,
    # không phải một khoảng trắng bị bỏ qua — nghỉ một tuần là thông tin.
    buckets = {}
    order = []
    for i in range(weeks):
        start = first_monday + timedelta(weeks=i)
        buckets[start] = {
            'weekStart': start.isoformat(),
            'label': '%d/%d' % (start.day, start.month),
            'minutes': 0, 'selfMinutes': 0, 'events': 0,
            '_mock': [0.0, 0.0], '_lesson': [0.0, 0.0],
        }
        order.append(start)

    mocks = []
    for r in rows:
        start = _monday(r['event_date'])
        b = buckets.get(start)
        if b is None:
            continue
        b['events'] += 1
        mins = r['minutes'] or 0
        if r['source'] == SOURCE_SELF:
            b['selfMinutes'] += mins
        else:
            b['minutes'] += mins
        if r['max_score'] and float(r['max_score']) > 0:
            if r['kind'] == KIND_MOCK:
                b['_mock'][0] += float(r['score'] or 0)
                b['_mock'][1] += float(r['max_score'])
                meta = _as_json(r['meta'])
                mocks.append({
                    'at': r['occurred_at'].isoformat() if r['occurred_at'] else None,
                    'date': r['event_date'].isoformat(),
                    'x': (r['event_date'] - first_monday).days,
                    'score': float(r['score'] or 0),
                    'max': float(r['max_score']),
                    'pct': round(_pct(r['score'], r['max_score']) or 0, 1),
                    'examId': meta.get('examId'),
                })
            elif r['kind'] == KIND_LESSON:
                b['_lesson'][0] += float(r['score'] or 0)
                b['_lesson'][1] += float(r['max_score'])

    points = []
    for start in order:
        b = buckets[start]
        mock_s, mock_m = b.pop('_mock')
        les_s, les_m = b.pop('_lesson')
        b['mockPct'] = round(_pct(mock_s, mock_m)) if mock_m else None
        b['lessonPct'] = round(_pct(les_s, les_m)) if les_m else None
        points.append(b)

    mocks.sort(key=lambda m: m['x'])
    goals = read_goals(uid)
    band = target_band(goals.get('targetScore'))

    return {
        'weeks': points,
        'mocks': mocks,
        'spanDays': weeks * 7,
        'trend': _trend(mocks),
        'minPointsForTrend': MIN_POINTS_FOR_TREND,
        'target': band,
        'daysToExam': goals.get('daysToExam'),
        'examDate': goals.get('examDate'),
        'scoreScale': HSA_MAX_SCORE,
        # Câu chữ trung thực về chuyện quy đổi — giao diện in nguyên văn.
        'scaleNote': ('Đề HSA thật có %d câu, mỗi câu 1 điểm, nên phần trăm đúng '
                      'chính là điểm trên thang %d. Đề trong sản phẩm hiện là bản '
                      'rút gọn nên con số chỉ để tham khảo, chờ đề đầy đủ của TopHSA.'
                      % (HSA_MAX_SCORE, HSA_MAX_SCORE)),
    }
