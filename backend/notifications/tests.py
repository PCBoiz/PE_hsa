"""Test cơ bản app notifications (0-test ở bản Flask)."""
import pytest

pytestmark = pytest.mark.django_db


def test_settings_default(auth_api):
    res = auth_api.get('/api/notifications')
    assert res.status_code == 200
    assert res.json() == {'emailNotif': True, 'pushNotif': False,
                          'studyRemind': True, 'contentUpdate': False}


def test_settings_roundtrip(auth_api):
    res = auth_api.put('/api/notifications',
                       {'emailNotif': False, 'pushNotif': True,
                        'studyRemind': False, 'contentUpdate': True}, format='json')
    assert res.status_code == 200
    data = auth_api.get('/api/notifications').json()
    assert data == {'emailNotif': False, 'pushNotif': True,
                    'studyRemind': False, 'contentUpdate': True}


def test_feed_empty_and_read_all(auth_api):
    feed = auth_api.get('/api/notifications/feed').json()
    assert feed['items'] == [] and feed['unread'] == 0
    assert auth_api.post('/api/notifications/feed/read-all').status_code == 200


def test_badge_empty(auth_api):
    res = auth_api.get('/api/notifications/badge')
    assert res.status_code == 200
    assert res.json() == {'unread': 0, 'latest': 0}


def test_badge_counts_unread(auth_api, temp_user):
    from notifications.service import notify
    notify(temp_user, 'system', 'Chào mừng', 'nội dung', 'post', 1)
    data = auth_api.get('/api/notifications/badge').json()
    assert data['unread'] == 1 and data['latest'] > 0


def test_requires_auth(api, db):
    assert api.get('/api/notifications').status_code == 401
    assert api.get('/api/notifications/badge').status_code == 401
