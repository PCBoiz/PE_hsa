"""Test cơ bản app leaderboard (0-test ở bản Flask)."""
import pytest

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('lb_type,unit', [('weekly', 'XP'), ('streak', 'ngày'), ('friends', 'XP')])
def test_leaderboard_types(auth_api, lb_type, unit):
    res = auth_api.get(f'/api/leaderboard?type={lb_type}')
    assert res.status_code == 200
    data = res.json()
    assert data['type'] == lb_type
    assert data['unit'] == unit
    assert isinstance(data['entries'], list)
    assert data['me'] is not None


def test_leaderboard_invalid_type_400(auth_api):
    assert auth_api.get('/api/leaderboard?type=bogus').status_code == 400


def test_requires_auth(api, db):
    assert api.get('/api/leaderboard').status_code == 401
