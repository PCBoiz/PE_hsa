"""
Port db/repositories/achievements.py — logic trao thành tích dùng chung
(gọi từ lessons.complete và stats.mission_complete, trong transaction của caller).
"""
from common.db import q, q1


def _get_metrics(user_id):
    """Gom số liệu thật của user để so với điều kiện achievement."""
    user = q1('SELECT streak, xp FROM users WHERE id=%s', (user_id,))
    lesson_row = q1("SELECT COUNT(*) AS n FROM lesson_progress "
                    "WHERE user_id=%s AND status='completed'", (user_id,))
    course_row = q1('SELECT COUNT(*) AS n FROM enrollments '
                    'WHERE user_id=%s AND progress >= 100', (user_id,))
    return {
        'lesson_count': lesson_row['n'] if lesson_row else 0,
        'streak_days': (user['streak'] if user else 0) or 0,
        'xp_total': (user['xp'] if user else 0) or 0,
        'course_complete': course_row['n'] if course_row else 0,
    }


def check_and_award_achievements(user_id):
    """So điều kiện từng achievement với số liệu thật; insert nếu đạt và chưa có.
    Trả danh sách achievement VỪA được trao (có thể rỗng)."""
    metrics = _get_metrics(user_id)
    rows = q('SELECT id, code, name, icon, condition_type, condition_value FROM achievements')

    newly_awarded = []
    for a in rows:
        value = metrics.get(a['condition_type'])
        if value is None or value < a['condition_value']:
            continue
        inserted = q1('''INSERT INTO user_achievements (user_id, achievement_id)
                         VALUES (%s, %s)
                         ON CONFLICT (user_id, achievement_id) DO NOTHING
                         RETURNING achievement_id''', (user_id, a['id']))
        if inserted:
            newly_awarded.append({'code': a['code'], 'name': a['name'], 'icon': a['icon']})
    return newly_awarded
