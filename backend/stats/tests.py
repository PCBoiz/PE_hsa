"""Port tests/test_parse_time_spent.py + tests/test_streak.py (Flask) — cùng case."""
from datetime import date, timedelta

import pytest

from common.db import q1, x
from stats.views import parse_time_spent

pytestmark = pytest.mark.django_db


# ── test_parse_time_spent.py (port nguyên văn) ──────────────────────────────

def test_happy_path():
    assert parse_time_spent('2h') == 2.0
    assert parse_time_spent('0.5h') == 0.5
    assert parse_time_spent('24h') == 24.0
    assert parse_time_spent('0') == 0.0


def test_none_and_empty():
    assert parse_time_spent(None) == 0.0
    assert parse_time_spent('') == 0.0
    assert parse_time_spent('   ') == 0.0


def test_negative():
    assert parse_time_spent('-2h') == 0.0
    assert parse_time_spent('-0.1h') == 0.0


def test_overflow():
    assert parse_time_spent('25h') == 25.0
    assert parse_time_spent('9999h') == 500.0


def test_invalid_format():
    assert parse_time_spent('abc') == 0.0
    assert parse_time_spent('2.5.1h') == 0.0


def test_boundary():
    assert parse_time_spent('24.0h') == 24.0


# ── test_streak.py (port — mission mock qua monkeypatch như bản Flask) ──────

def _set_streak(uid, streak, last_study_date):
    x('UPDATE users SET streak=%s, last_study_date=%s WHERE id=%s',
      (streak, last_study_date, uid))


@pytest.fixture
def da_ghi_danh(temp_user):
    """Ghi danh học viên tạm vào khoá HSA — điều kiện để hoàn thành một bài."""
    x("INSERT INTO enrollments (user_id, course_id, progress, completed_lessons, "
      "time_spent, last_lesson, next_lesson) VALUES (%s, %s, 0, 0, '0h', '', '') "
      "ON CONFLICT (user_id, course_id) DO NOTHING", (temp_user, 'hsa_quantitative'))
    return temp_user


def _hoc_xong_mot_bai(client):
    """Đường THẬT làm chuỗi ngày nhúc nhích: hoàn thành một bài học.

    Viết lại 31/08/2026. Sáu phép kiểm chuỗi ngày dưới đây trước kia đi qua
    `/api/mission/complete` và vá vào `stats.views._verify_mission_by_course`.
    Cả endpoint lẫn hàm đó đã bị xoá khi nhiệm vụ chuyển từ "nhiệm vụ SQL của
    pe_test" sang chấm bằng số liệu HSA thật, nên `monkeypatch.setattr` ném
    AttributeError NGAY Ở KHÂU DỰNG — tức chúng chưa từng chạy kể từ lần đổi ấy.
    Và chúng báo "error" chứ không "fail", thứ dễ lướt qua hơn nhiều.

    Nay đi qua `common/streak.py:touch_streak`, chỗ DUY NHẤT viết cột `streak`.
    Nó chỉ được gọi từ hai nơi: hoàn thành bài học và nộp đề thi thử. Nhận
    thưởng nhiệm vụ KHÔNG chạm vào chuỗi ngày — hợp lý, vì nhiệm vụ chỉ đủ điều
    kiện sau khi đã học thật, nên chuỗi đã cộng từ trước đó rồi.
    """
    return client.post('/api/lessons/1/complete',
                       {'courseId': 'hsa_quantitative', 'xpEarned': 10}, format='json')


def test_locked_when_streak_below_5(auth_api, temp_user):
    _set_streak(temp_user, 3, date.today())
    res = auth_api.get('/api/streak/review-quiz-status')
    assert res.status_code == 200
    data = res.json()
    assert data['streak'] == 3
    assert data['is_unlocked'] is False
    assert data['days_remaining'] == 2


def test_unlocked_when_streak_reaches_5(auth_api, temp_user):
    _set_streak(temp_user, 5, date.today())
    data = auth_api.get('/api/streak/review-quiz-status').json()
    assert data['streak'] == 5
    assert data['is_unlocked'] is True
    assert data['days_remaining'] == 0


def test_unlocked_when_streak_above_5(auth_api, temp_user):
    _set_streak(temp_user, 9, date.today())
    data = auth_api.get('/api/streak/review-quiz-status').json()
    assert data['is_unlocked'] is True
    assert data['days_remaining'] == 0


def test_requires_login(api, db):
    res = api.get('/api/streak/review-quiz-status')
    assert res.status_code == 401


def test_streak_increments_on_consecutive_day_khi_hoc_xong_bai(auth_api, da_ghi_danh):
    _set_streak(da_ghi_danh, 4, date.today() - timedelta(days=1))
    data = _hoc_xong_mot_bai(auth_api).json()
    assert data['ok'] is True
    assert data['streak'] == 5
    assert auth_api.get('/api/streak/review-quiz-status').json()['is_unlocked'] is True


def test_streak_resets_after_missing_a_day(auth_api, da_ghi_danh):
    _set_streak(da_ghi_danh, 5, date.today() - timedelta(days=3))
    data = _hoc_xong_mot_bai(auth_api).json()
    assert data['streak'] == 1
    assert auth_api.get('/api/streak/review-quiz-status').json()['is_unlocked'] is False


def test_streak_unchanged_when_studying_again_same_day(auth_api, da_ghi_danh):
    _set_streak(da_ghi_danh, 5, date.today())
    data = _hoc_xong_mot_bai(auth_api).json()
    assert data['ok'] is True
    assert data['streak'] == 5


def test_nghi_dung_mot_ngay_con_ve_thi_chuoi_khong_dut(auth_api, da_ghi_danh):
    """Nghỉ đúng một ngày mà còn vé bảo hiểm → tiêu vé, chuỗi vẫn tăng.

    Phép kiểm cũ tên `test_streak_resets_at_exactly_two_days_gap` khẳng định
    chuỗi về 1 ở đây — đó là luật CŨ, trước khi có vé bảo hiểm. Vé sinh ra vì
    "ôn 6 tháng rồi mất sạch chuỗi vì một ngày bận" là điểm bỏ cuộc kinh điển
    (xem `common/streak.py`). Tách làm hai phép kiểm để cả hai nhánh đều có
    người canh: một nhánh còn vé, một nhánh hết vé.
    """
    _set_streak(da_ghi_danh, 5, date.today() - timedelta(days=2))
    x('UPDATE users SET streak_freezes=1 WHERE id=%s', (da_ghi_danh,))
    data = _hoc_xong_mot_bai(auth_api).json()
    assert data['streak'] == 6
    assert data['usedStreakFreeze'] is True
    assert q1('SELECT streak_freezes AS n FROM users WHERE id=%s',
              (da_ghi_danh,))['n'] == 0   # đã tiêu đúng một vé


def test_nghi_mot_ngay_ma_HET_ve_thi_chuoi_ve_1(auth_api, da_ghi_danh):
    _set_streak(da_ghi_danh, 5, date.today() - timedelta(days=2))
    x('UPDATE users SET streak_freezes=0 WHERE id=%s', (da_ghi_danh,))
    data = _hoc_xong_mot_bai(auth_api).json()
    assert data['streak'] == 1
    assert data['usedStreakFreeze'] is False


def test_streak_starts_at_one_for_first_time_user(auth_api, da_ghi_danh):
    # fixture tạo tài khoản với last_study_date=NULL
    assert _hoc_xong_mot_bai(auth_api).json()['streak'] == 1


def test_stats_streak_active_true_when_studied_today(auth_api, temp_user):
    _set_streak(temp_user, 3, date.today())
    res = auth_api.get('/api/stats')
    assert res.status_code == 200
    assert res.json()['streakActive'] is True


def test_stats_streak_active_false_when_not_studied_today(auth_api, temp_user):
    _set_streak(temp_user, 3, date.today() - timedelta(days=1))
    assert auth_api.get('/api/stats').json()['streakActive'] is False


def test_stats_streak_active_false_when_never_studied(auth_api):
    assert auth_api.get('/api/stats').json()['streakActive'] is False


def test_hoc_xong_bai_thi_streak_active_bat_len(auth_api, da_ghi_danh):
    """Nghỉ 5 ngày rồi học lại: chuỗi về 1, và /api/stats phải nói "đang hoạt động".

    Bản cũ khẳng định phản hồi có trường `streak_active` hardcode True — di sản
    Flask, và trường đó đã không còn. Viết lại để đo thứ NGƯỜI DÙNG thấy: sau
    khi học xong một bài thì màn hình chuỗi ngày phải sáng lên trong hôm nay,
    chứ không phải một khoá JSON có tồn tại hay không.
    """
    _set_streak(da_ghi_danh, 5, date.today() - timedelta(days=5))
    assert auth_api.get('/api/stats').json()['streakActive'] is False
    data = _hoc_xong_mot_bai(auth_api).json()
    assert data['streak'] == 1
    assert auth_api.get('/api/stats').json()['streakActive'] is True


# ── memory-plan T4.3: /api/stats không được 500 khi enrollment.progress = NULL ──
def test_stats_avg_progress_handles_null_progress(auth_api, temp_user):
    """Cột enrollments.progress nullable → dữ liệu thật có thể NULL. StatsView tính
    sum(progress)/len phải bỏ qua NULL, không được ném TypeError (500)."""
    x("INSERT INTO courses (id, title) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
      ('mp_t43_course', 'T43 Course'))
    x("INSERT INTO enrollments (user_id, course_id, progress) VALUES (%s, %s, NULL) "
      "ON CONFLICT (user_id, course_id) DO UPDATE SET progress = NULL",
      (temp_user, 'mp_t43_course'))
    res = auth_api.get('/api/stats')
    assert res.status_code == 200
    assert res.json()['avgProgress'] == 0  # NULL coi như 0
