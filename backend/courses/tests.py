"""Port tests/test_course_ratings.py (Flask) + happy-path /api/courses."""
import pytest

from common.db import q, q1, x

pytestmark = pytest.mark.django_db

TEST_COURSE_ID = 'hsa_quantitative'   # CSDL HSA khong con khoa 'python' cua ProgrammingEdu


@pytest.fixture
def test_enrollment(temp_user):
    x('''INSERT INTO enrollments (user_id, course_id, progress, completed_lessons,
                                  time_spent, last_lesson, next_lesson)
         VALUES (%s, %s, 0, 0, '0h', '', '')
         ON CONFLICT (user_id, course_id) DO NOTHING''', (temp_user, TEST_COURSE_ID))
    return temp_user


def _rate(client, payload):
    return client.post('/api/course/rating', payload, format='json')


def test_rate_course_success(auth_api, test_enrollment):
    res = _rate(auth_api, {'course_id': TEST_COURSE_ID, 'rating': 4})
    assert res.status_code == 200
    assert res.json()['ok'] is True
    row = q1('SELECT rating FROM course_ratings WHERE user_id=%s AND course_id=%s',
             (test_enrollment, TEST_COURSE_ID))
    assert row['rating'] == 4


def test_rate_course_updates_not_duplicates(auth_api, test_enrollment):
    _rate(auth_api, {'course_id': TEST_COURSE_ID, 'rating': 3})
    res = _rate(auth_api, {'course_id': TEST_COURSE_ID, 'rating': 5})
    assert res.status_code == 200
    rows = q('SELECT rating FROM course_ratings WHERE user_id=%s AND course_id=%s',
             (test_enrollment, TEST_COURSE_ID))
    assert len(rows) == 1
    assert rows[0]['rating'] == 5


def test_rate_course_requires_enrollment(auth_api):
    res = _rate(auth_api, {'course_id': TEST_COURSE_ID, 'rating': 4})
    assert res.status_code == 403


def test_rate_course_unknown_course(auth_api):
    res = _rate(auth_api, {'course_id': 'does-not-exist', 'rating': 4})
    assert res.status_code == 404


@pytest.mark.parametrize('bad_rating', [0, 6, 'abc', True, None])
def test_rate_course_invalid_rating(auth_api, test_enrollment, bad_rating):
    payload = {'course_id': TEST_COURSE_ID}
    if bad_rating is not None:
        payload['rating'] = bad_rating
    assert _rate(auth_api, payload).status_code == 400


def test_rate_course_requires_login(api, db):
    res = _rate(api, {'course_id': TEST_COURSE_ID, 'rating': 4})
    assert res.status_code == 401


def test_get_rating_endpoint(auth_api, test_enrollment):
    _rate(auth_api, {'course_id': TEST_COURSE_ID, 'rating': 4})
    res = auth_api.get(f'/api/course/{TEST_COURSE_ID}/rating')
    assert res.status_code == 200
    data = res.json()
    assert data['count'] >= 1
    assert data['average'] is not None


def test_get_rating_unknown_course(auth_api):
    assert auth_api.get('/api/course/does-not-exist/rating').status_code == 404


# ── Coverage cơ bản mới (khóa /api/courses chưa từng có test) ────────────────

def test_courses_list_happy_path(auth_api):
    res = auth_api.get('/api/courses')
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list) and len(data) >= 1
    sample = data[0]
    assert 'accentColor' in sample and 'enrolled' in sample


def test_courses_enrolled_combined(auth_api, test_enrollment):
    res = auth_api.get('/api/courses-enrolled')
    assert res.status_code == 200
    data = res.json()
    assert any(e['id'] == TEST_COURSE_ID for e in data['enrolled'])
