"""Test cơ bản app achievements (0-test ở bản Flask)."""
import pytest

pytestmark = pytest.mark.django_db


def test_list_achievements(auth_api):
    res = auth_api.get('/api/achievements')
    assert res.status_code == 200
    data = res.json()
    assert data['totalCount'] >= 6  # 6 achievement seed
    assert data['unlockedCount'] == 0  # user tạm chưa đạt gì
    codes = {a['code'] for a in data['achievements']}
    assert {'first_lesson', 'streak_7', 'xp_1000'} <= codes


def test_requires_auth(api, db):
    assert api.get('/api/achievements').status_code == 401
