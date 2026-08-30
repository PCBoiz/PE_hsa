"""Test cơ bản app lessons — luồng complete lesson (XP/streak/achievement)."""
import pytest

from common.db import q1, x

pytestmark = pytest.mark.django_db

COURSE_ID = 'hsa_quantitative'   # CSDL HSA khong con khoa 'db_design' cua ProgrammingEdu


@pytest.fixture
def enrolled_user(temp_user):
    x('''INSERT INTO enrollments (user_id, course_id, progress, completed_lessons,
                                  time_spent, last_lesson, next_lesson)
         VALUES (%s, %s, 0, 0, '0h', '', '')
         ON CONFLICT (user_id, course_id) DO NOTHING''', (temp_user, COURSE_ID))
    return temp_user


def test_complete_lesson_happy_path(auth_api, enrolled_user):
    res = auth_api.post('/api/lessons/1/complete',
                        {'courseId': COURSE_ID, 'quizScore': 90, 'xpEarned': 50},
                        format='json')
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert data['completedLessons'] == 1
    assert data['xpGained'] == 50
    # achievement 'first_lesson' phải được trao lần đầu
    assert any(a['code'] == 'first_lesson' for a in data['newAchievements'])
    user = q1('SELECT xp, gems, streak FROM users WHERE id=%s', (enrolled_user,))
    assert user['xp'] == 50 and user['gems'] == 50 and user['streak'] == 1


def test_complete_lesson_no_double_xp(auth_api, enrolled_user):
    auth_api.post('/api/lessons/1/complete', {'courseId': COURSE_ID, 'xpEarned': 50}, format='json')
    res = auth_api.post('/api/lessons/1/complete', {'courseId': COURSE_ID, 'xpEarned': 50}, format='json')
    assert res.json()['xpGained'] == 0  # chống spam F5 modal
    user = q1('SELECT xp FROM users WHERE id=%s', (enrolled_user,))
    assert user['xp'] == 50


def test_complete_lesson_xp_clamped(auth_api, enrolled_user):
    """Client gửi XP tùy ý > 500 → mặc định an toàn 50."""
    res = auth_api.post('/api/lessons/2/complete',
                        {'courseId': COURSE_ID, 'xpEarned': 99999}, format='json')
    assert res.json()['xpGained'] == 50


def test_complete_lesson_missing_course_400(auth_api):
    res = auth_api.post('/api/lessons/1/complete', {}, format='json')
    assert res.status_code == 400


def test_complete_lesson_unknown_course_404(auth_api):
    res = auth_api.post('/api/lessons/1/complete', {'courseId': 'nope'}, format='json')
    assert res.status_code == 404
