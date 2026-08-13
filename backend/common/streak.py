"""Chuỗi ngày học + cộng XP — một nguồn duy nhất cho mọi hoạt động tính điểm.

Trước 2026-08-14 logic này nằm rải trong lessons/views.py và stats/views.py, còn
thi thử thì KHÔNG cộng XP và KHÔNG tính vào chuỗi — học viên làm hết một đề 150
câu vẫn mất chuỗi nếu hôm đó không mở bài học nào.

Gọi trong transaction của caller (không tự mở transaction).
"""
from datetime import timedelta

from common.clock import local_today
from common.db import q1, x


def touch_streak(uid, today=None):
    """Ghi nhận "hôm nay có học" và trả về (chuỗi mới, đã tiêu vé bảo hiểm?).

    Quy tắc:
      - Học lần đầu, hoặc nghỉ từ 2 ngày trở lên và hết vé → chuỗi về 1.
      - Nghỉ ĐÚNG 1 ngày và còn vé bảo hiểm → tiêu 1 vé, chuỗi tiếp tục tăng.
        Thí sinh ôn 6 tháng mà mất sạch chuỗi vì một ngày bận là điểm bỏ cuộc
        kinh điển; vé bảo hiểm giữ chân họ mà không nói dối về số liệu.
      - Đã học trong hôm nay → giữ nguyên.
    """
    today = today or local_today()
    user = q1('SELECT streak, last_study_date, streak_freezes FROM users WHERE id=%s', (uid,))
    if not user:
        return 0, False

    last = user['last_study_date']
    streak = user['streak'] or 0
    freezes = user['streak_freezes'] if user['streak_freezes'] is not None else 0
    used_freeze = False

    if last == today:
        return streak, False           # hôm nay đã ghi nhận rồi
    if last is None:
        streak = 1
    elif last == today - timedelta(days=1):
        streak = streak + 1
    elif last == today - timedelta(days=2) and freezes > 0:
        # Nghỉ đúng một ngày: tiêu vé, coi như chuỗi không đứt.
        streak = streak + 1
        freezes -= 1
        used_freeze = True
    else:
        streak = 1

    x('UPDATE users SET streak=%s, last_study_date=%s, streak_freezes=%s WHERE id=%s',
      (streak, today, freezes, uid))
    return streak, used_freeze


def award_xp(uid, xp, today=None):
    """Cộng XP vào tổng của user và vào nhật ký XP theo ngày (nguồn của BXH tuần)."""
    if not xp or xp <= 0:
        return 0
    today = today or local_today()
    x('UPDATE users SET xp = xp + %s, gems = gems + %s WHERE id=%s', (xp, xp, uid))
    x('''INSERT INTO user_daily_xp_logs (user_id, log_date, xp_earned)
         VALUES (%s, %s, %s)
         ON CONFLICT (user_id, log_date)
         DO UPDATE SET xp_earned = user_daily_xp_logs.xp_earned + EXCLUDED.xp_earned''',
      (uid, today, xp))
    return xp
