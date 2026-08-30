"""Báo cáo lớp cho giảng viên.

Đây là chỗ năm trụ cột đã dựng trả công: mọi con số per-học-viên (bài đã xong,
điểm năng lực theo chủ đề, độ chậm kế hoạch, hoạt động gần nhất) đều đã nằm gọn
trong ``learning_events`` và các bảng đi kèm. Báo cáo lớp chỉ là thêm một tầng
gom nhóm — không phải một kho dữ liệu mới.

BA NGUYÊN TẮC:

1. **Một lượt truy vấn cho cả lớp, không phải một lượt cho mỗi học viên.**
   Mỗi lượt tới Neon tốn ~245ms thuần đường truyền; gọi ``competency.compute``
   cho từng người trong lớp 30 học viên là 60 lượt = 15 giây. Ở đây mọi thứ gom
   theo lớp trong vài câu SQL.

2. **Cảnh báo sớm phải nói ĐƯỢC LÀM GÌ TIẾP.** "Nam đang yếu" thì giảng viên
   không làm gì được; "Nam 9 ngày không mở bài, chưa làm đề nào" thì gọi điện
   được. Mỗi cảnh báo là một câu có động từ.

3. **Không xếp hạng học viên trong lớp.** Bảng có thể sắp theo tiến độ, nhưng
   KHÔNG có cột "hạng" — bảng xếp hạng nội bộ lớp làm hỏng động lực của đúng
   những em cần được giữ lại nhất, mà giảng viên vẫn đọc được thứ tự từ số liệu.
"""
from datetime import timedelta

from django.db import DatabaseError

from common.clock import local_today
from common.db import q, q1
from common.events import KIND_LESSON, KIND_MOCK
from stats.competency import (COURSE_ORDER, HALF_LIFE_DAYS, KIND_TO_SOURCE,
                              MIN_ACTIVITIES, SOURCE_WEIGHTS, TOPIC_SOURCES)

#: Không hoạt động quá ngần này ngày thì cảnh báo.
IDLE_DAYS = 7
#: Chậm quá ngần này việc trong kế hoạch thì cảnh báo.
LAG_ITEMS = 5
#: Dưới mức này coi là chủ đề yếu khi tổng hợp cho cả lớp.
WEAK_BELOW = 60


def _class_row(class_id):
    return q1('''SELECT c.id, c.code, c.name, c.course_id, c.teacher_id, c.schedule,
                        c.meeting_url, c.starts_on, c.ends_on, c.exam_date,
                        c.capacity, c.status, c.note,
                        u.name AS teacher_name, co.title AS course_title
                 FROM classes c
                 LEFT JOIN users u ON u.id = c.teacher_id
                 LEFT JOIN courses co ON co.id = c.course_id
                 WHERE c.id = %s''', (class_id,))


def _members(class_id):
    return q('''SELECT m.user_id, m.joined_at, m.left_at, m.note,
                       u.name, u.email, u.streak, u.last_study_date, u.xp
                FROM class_members m
                JOIN users u ON u.id = m.user_id
                WHERE m.class_id = %s
                ORDER BY u.name''', (class_id,))


def _decayed(items, today):
    """Trung bình có suy giảm theo thời gian — CÙNG công thức với bản đồ năng
    lực cá nhân. Hai nơi tính khác nhau thì giảng viên và học viên nhìn hai con
    số khác nhau cho cùng một chủ đề, và không ai tin cái nào nữa."""
    num = den = 0.0
    for value, when in items:
        age = (today - when).days if when else 0
        w = 0.5 ** (max(0, age) / HALF_LIFE_DAYS)
        num += w * value
        den += w
    return (num / den) if den else None


def _events_by_user(uids):
    """Sự kiện có chấm điểm của CẢ LỚP trong một lượt hỏi."""
    out = {}
    if not uids:
        return out
    try:
        rows = q('''SELECT user_id, kind, course_id, topic, score, max_score,
                           event_date, ref_id
                    FROM learning_events
                    WHERE user_id = ANY(%s) AND kind = ANY(%s)
                      AND max_score IS NOT NULL AND max_score > 0''',
                 (list(uids), list(KIND_TO_SOURCE)))
    except DatabaseError:
        return out
    for r in rows:
        out.setdefault(r['user_id'], []).append(r)
    return out


def _mastery_by_topic(events, today):
    """Điểm thành thạo từng (khoá, chủ đề) của MỘT học viên, từ sự kiện đã có.

    Lặp lại luật của stats/competency.py có chủ đích: ở đó tính cho một người
    bằng nhiều câu SQL, ở đây tính cho cả lớp từ một mảng sự kiện đã nạp sẵn.
    Trọng số và công thức lấy trực tiếp từ module kia (import), nên không thể
    lệch nhau.
    """
    by_cell, by_course = {}, {}
    for r in events:
        source = KIND_TO_SOURCE.get(r['kind'])
        if not source:
            continue
        try:
            pct = max(0.0, min(100.0,
                               float(r['score'] or 0) * 100.0 / float(r['max_score'])))
        except (TypeError, ValueError, ZeroDivisionError):
            continue
        item = (pct, r['event_date'], r['ref_id'])
        if source == 'mock':
            by_course.setdefault(r['course_id'], []).append(item)
        elif r['topic']:
            by_cell.setdefault((r['course_id'], r['topic']), {}) \
                   .setdefault(source, []).append(item)

    out = {}
    for cell, sources in by_cell.items():
        srcs = dict(sources)
        mock_items = by_course.get(cell[0])
        if mock_items:
            srcs['mock'] = mock_items
        activities = {ref for name in TOPIC_SOURCES
                      for _, _, ref in srcs.get(name, []) if ref}
        if len(activities) < MIN_ACTIVITIES:
            continue                      # chưa đủ dữ liệu — không bịa ra số
        parts = weight_sum = 0.0
        for name, items in srcs.items():
            mean = _decayed([(v, d) for v, d, _ in items], today)
            if mean is None:
                continue
            w = SOURCE_WEIGHTS.get(name, 0)
            parts += w * mean
            weight_sum += w
        if weight_sum:
            out[cell] = round(parts / weight_sum)
    return out


def _progress_by_user(uids):
    rows = q('''SELECT user_id, course_id, COUNT(*) AS n
                FROM lesson_progress
                WHERE user_id = ANY(%s) AND status = 'completed'
                GROUP BY user_id, course_id''', (list(uids),)) if uids else []
    out = {}
    for r in rows:
        out.setdefault(r['user_id'], {})[r['course_id']] = r['n']
    return out


def _last_activity(uids):
    rows = q('''SELECT user_id, MAX(event_date) AS last_day, COUNT(*) AS events
                FROM learning_events WHERE user_id = ANY(%s)
                GROUP BY user_id''', (list(uids),)) if uids else []
    return {r['user_id']: r for r in rows}


def _mocks_by_user(uids):
    rows = q('''SELECT user_id, score, max_score, event_date
                FROM learning_events
                WHERE user_id = ANY(%s) AND kind = %s
                  AND max_score IS NOT NULL AND max_score > 0
                ORDER BY occurred_at''', (list(uids), KIND_MOCK)) if uids else []
    out = {}
    for r in rows:
        pct = round(float(r['score'] or 0) * 100.0 / float(r['max_score']))
        out.setdefault(r['user_id'], []).append({'pct': pct, 'date': r['event_date']})
    return out


def _lag_by_user(uids):
    """Số việc quá hạn chưa xong trong kế hoạch của từng học viên.

    Chỉ đếm mục BÀI HỌC: mục thi thử và ôn tập cần đối chiếu sự kiện phức tạp
    hơn, và với giảng viên thì "chậm mấy bài" đã đủ để gọi điện.
    """
    if not uids:
        return {}
    monday = local_today() - timedelta(days=local_today().weekday())
    try:
        rows = q('''SELECT p.user_id, COUNT(*) AS n
                    FROM study_plan_items i
                    JOIN study_plans p ON p.id = i.plan_id AND p.is_active
                    LEFT JOIN lessons l
                           ON l.course_id = i.course_id AND l.sort_order = i.lesson_no
                    LEFT JOIN lesson_progress lp
                           ON lp.lesson_id = l.id AND lp.user_id = p.user_id
                          AND lp.status = 'completed'
                    WHERE p.user_id = ANY(%s) AND i.kind = 'lesson'
                      AND i.status <> 'skipped' AND i.week_start < %s
                      AND lp.user_id IS NULL
                    GROUP BY p.user_id''', (list(uids), monday))
    except DatabaseError:
        return {}
    return {r['user_id']: r['n'] for r in rows}


def _alerts(student):
    """Cảnh báo sớm — mỗi cái là một câu NÓI ĐƯỢC LÀM GÌ TIẾP."""
    out = []
    if student['idleDays'] is None:
        out.append({'level': 'high', 'text': 'Chưa hoạt động lần nào kể từ khi vào lớp.'})
    elif student['idleDays'] >= IDLE_DAYS:
        out.append({'level': 'high',
                    'text': '%d ngày không mở bài nào.' % student['idleDays']})
    if not student['mockCount']:
        out.append({'level': 'mid', 'text': 'Chưa làm đề thi thử nào.'})
    elif student['mockTrend'] is not None and student['mockTrend'] <= -8:
        out.append({'level': 'mid',
                    'text': 'Điểm thi thử giảm %d điểm %% so với lượt trước.'
                            % abs(student['mockTrend'])})
    if student['lag'] >= LAG_ITEMS:
        out.append({'level': 'mid',
                    'text': 'Chậm %d bài so với kế hoạch.' % student['lag']})
    return out


def class_report(class_id):
    """Toàn bộ số liệu một lớp trong 6 lượt truy vấn, không phải 2×N lượt."""
    info = _class_row(class_id)
    if not info:
        return None
    members = _members(class_id)
    uids = [m['user_id'] for m in members]
    today = local_today()

    events = _events_by_user(uids)
    progress = _progress_by_user(uids)
    activity = _last_activity(uids)
    mocks = _mocks_by_user(uids)
    lags = _lag_by_user(uids)

    totals = {r['course_id']: r['n'] for r in q(
        "SELECT course_id, COUNT(*) AS n FROM lessons "
        "WHERE module IS NOT NULL AND module <> '' GROUP BY course_id")}

    # Mẫu số là số bài của KHOÁ LỚP NÀY HỌC, không phải tổng cả ba khoá.
    #
    # Lỗi đã có thật, sửa 30/08/2026: trước đây `lessons_total` luôn là tổng của
    # cả ba hợp phần (27 Định lượng + 26 Khoa học + 23 Định tính = 76), kể cả
    # với lớp chỉ ôn một hợp phần. Đo trên lớp "Luyện HSA đợt 1/2027 — Ca tối"
    # (course_id = hsa_quantitative): một em học xong TRỌN VẸN cả 27 bài của
    # khoá mình sẽ hiện 36%, không phải 100%.
    #
    # Con số này không nằm im trong hệ thống: nó đi vào bảng điều khiển lớp, vào
    # file xuất ra Excel, và từ đó vào buổi họp phụ huynh. Nói với phụ huynh rằng
    # con họ mới đi được 36% chặng đường trong khi em đã học hết giáo trình là
    # sai theo hướng tệ nhất.
    #
    # `classes.course_id` để NULL nghĩa là lớp ôn cả ba hợp phần — khi đó tổng
    # cả ba mới đúng, nên vẫn giữ nhánh cũ.
    scope = info.get('course_id')
    lessons_total = (totals.get(scope, 0) if scope else sum(totals.values())) or 1

    students, cell_scores = [], {}
    for m in members:
        uid = m['user_id']
        done_by_course = progress.get(uid, {})
        # Tử số bó theo cùng phạm vi với mẫu số. Không bó thì một em tự học thêm
        # Định tính ngoài giờ sẽ được cộng vào tiến độ của lớp Định lượng —
        # và với lớp một hợp phần, tiến độ có thể vượt quá 100%.
        done = done_by_course.get(scope, 0) if scope else sum(done_by_course.values())
        act = activity.get(uid) or {}
        last_day = act.get('last_day')
        idle = (today - last_day).days if last_day else None

        my_mocks = mocks.get(uid) or []
        trend = None
        if len(my_mocks) >= 2:
            trend = my_mocks[-1]['pct'] - my_mocks[-2]['pct']

        mastery = _mastery_by_topic(events.get(uid, []), today)
        for cell, val in mastery.items():
            cell_scores.setdefault(cell, []).append(val)
        weakest = sorted(mastery.items(), key=lambda kv: kv[1])[:3]

        st = {
            'userId': uid,
            'name': m['name'] or m['email'],
            'email': m['email'],
            'joinedAt': m['joined_at'].isoformat() if m['joined_at'] else None,
            'left': bool(m['left_at']),
            'lessonsDone': done,
            'lessonsTotal': lessons_total,
            'progressPct': round(done * 100 / lessons_total),
            'byCourse': done_by_course,
            'streak': m['streak'] or 0,
            'lastActive': last_day.isoformat() if last_day else None,
            'idleDays': idle,
            'mockCount': len(my_mocks),
            'lastMockPct': my_mocks[-1]['pct'] if my_mocks else None,
            'mockTrend': trend,
            'lag': lags.get(uid, 0),
            'measuredTopics': len(mastery),
            'weakest': [{'course': c, 'topic': t, 'mastery': v}
                        for (c, t), v in weakest],
        }
        st['alerts'] = _alerts(st)
        students.append(st)

    # Bản đồ năng lực của CẢ LỚP: trung bình các học viên ĐÃ ĐO ĐƯỢC ô đó.
    # Không lấy trung bình trên toàn lớp: người chưa đủ dữ liệu mà tính là 0 thì
    # mọi chủ đề đều trông như cả lớp đang dốt.
    topics = []
    for (course_id, topic), vals in cell_scores.items():
        topics.append({
            'course': course_id, 'topic': topic,
            'avg': round(sum(vals) / len(vals)),
            'measuredStudents': len(vals),
            'ofStudents': len(students),
        })
    order = {c: i for i, c in enumerate(COURSE_ORDER)}
    topics.sort(key=lambda t: (order.get(t['course'], 9), t['topic']))

    at_risk = [s for s in students if any(a['level'] == 'high' for a in s['alerts'])]
    weak_class = sorted([t for t in topics if t['avg'] < WEAK_BELOW],
                        key=lambda t: t['avg'])[:3]

    active = [s for s in students if not s['left']]
    return {
        'class': {
            'id': info['id'], 'code': info['code'], 'name': info['name'],
            'course': info['course_id'], 'courseTitle': info['course_title'],
            'teacherId': info['teacher_id'], 'teacherName': info['teacher_name'],
            'schedule': info['schedule'], 'meetingUrl': info['meeting_url'],
            'startsOn': info['starts_on'].isoformat() if info['starts_on'] else None,
            'endsOn': info['ends_on'].isoformat() if info['ends_on'] else None,
            'examDate': info['exam_date'].isoformat() if info['exam_date'] else None,
            'capacity': info['capacity'], 'status': info['status'], 'note': info['note'],
        },
        'students': students,
        'topics': topics,
        'summary': {
            'students': len(students),
            'active': len(active),
            'avgProgress': round(sum(s['progressPct'] for s in active) / len(active))
                           if active else 0,
            'noMock': sum(1 for s in active if not s['mockCount']),
            'idle': sum(1 for s in active
                        if s['idleDays'] is None or s['idleDays'] >= IDLE_DAYS),
            'behind': sum(1 for s in active if s['lag'] >= LAG_ITEMS),
            'atRisk': len(at_risk),
            'weakestTopics': weak_class,
            'idleDays': IDLE_DAYS,
            'lagItems': LAG_ITEMS,
        },
    }


def class_list(class_ids):
    """Danh sách lớp kèm vài con số đủ để chọn lớp, KHÔNG tính toàn bộ báo cáo."""
    if not class_ids:
        return []
    rows = q('''SELECT c.id, c.code, c.name, c.course_id, c.schedule, c.status,
                       c.exam_date, c.capacity,
                       u.name AS teacher_name, co.title AS course_title,
                       (SELECT COUNT(*) FROM class_members m
                         WHERE m.class_id = c.id AND m.left_at IS NULL) AS members
                FROM classes c
                LEFT JOIN users u ON u.id = c.teacher_id
                LEFT JOIN courses co ON co.id = c.course_id
                WHERE c.id = ANY(%s)
                ORDER BY c.status, c.name''', (list(class_ids),))
    return [{
        'id': r['id'], 'code': r['code'], 'name': r['name'],
        'course': r['course_id'], 'courseTitle': r['course_title'],
        'teacherName': r['teacher_name'], 'schedule': r['schedule'],
        'status': r['status'], 'capacity': r['capacity'], 'members': r['members'],
        'examDate': r['exam_date'].isoformat() if r['exam_date'] else None,
    } for r in rows]
