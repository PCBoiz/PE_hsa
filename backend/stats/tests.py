"""Port tests/test_parse_time_spent.py + tests/test_streak.py (Flask) — cùng case."""
from datetime import date, timedelta

import pytest

from common.db import x
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
def mock_mission(monkeypatch):
    monkeypatch.setattr('stats.views._verify_mission_by_course',
                        lambda course_id, condition, action: {'xp_reward': 10})


def _complete_mission(client):
    return client.post('/api/mission/complete',
                       {'mission_id': 'any-course', 'condition': '', 'action': ''},
                       format='json')


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


def test_streak_increments_on_consecutive_day_via_mission_complete(auth_api, temp_user, mock_mission):
    _set_streak(temp_user, 4, date.today() - timedelta(days=1))
    data = _complete_mission(auth_api).json()
    assert data['success'] is True
    assert data['streak'] == 5
    assert auth_api.get('/api/streak/review-quiz-status').json()['is_unlocked'] is True


def test_streak_resets_after_missing_a_day(auth_api, temp_user, mock_mission):
    _set_streak(temp_user, 5, date.today() - timedelta(days=3))
    data = _complete_mission(auth_api).json()
    assert data['streak'] == 1
    assert auth_api.get('/api/streak/review-quiz-status').json()['is_unlocked'] is False


def test_streak_unchanged_when_studying_again_same_day(auth_api, temp_user, mock_mission):
    _set_streak(temp_user, 5, date.today())
    data = _complete_mission(auth_api).json()
    assert data['success'] is True
    assert data['streak'] == 5


def test_streak_resets_at_exactly_two_days_gap(auth_api, temp_user, mock_mission):
    _set_streak(temp_user, 5, date.today() - timedelta(days=2))
    assert _complete_mission(auth_api).json()['streak'] == 1


def test_streak_starts_at_one_for_first_time_user(auth_api, mock_mission):
    # temp_user fixture tạo với last_study_date=NULL
    assert _complete_mission(auth_api).json()['streak'] == 1


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


def test_mission_complete_streak_active_field_present(auth_api, temp_user, mock_mission):
    """Hành vi hiện tại (giữ nguyên từ Flask): streak_active hardcode True."""
    _set_streak(temp_user, 5, date.today() - timedelta(days=5))
    data = _complete_mission(auth_api).json()
    assert data['streak_active'] is True
