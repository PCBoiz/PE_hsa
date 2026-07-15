"""Test cơ bản app forum (domain 0-test ở bản Flask — yêu cầu Giai đoạn 5).
Case lấy từ scripts/test_forum_api.py cũ làm checklist."""
import pytest

pytestmark = pytest.mark.django_db


def _create_post(client, content='Bài test migration', category='question', title='T'):
    return client.post('/api/posts', {'content': content, 'category': category, 'title': title},
                       format='json')


def test_create_and_list_post(auth_api):
    res = _create_post(auth_api)
    assert res.status_code == 200
    post_id = res.json()['id']

    lst = auth_api.get('/api/posts').json()
    assert any(p['id'] == post_id for p in lst['posts'])
    mine = auth_api.get('/api/posts?mine=1').json()
    assert all('reactions' in p and 'my_reaction' in p for p in mine['posts'])


def test_create_post_empty_content_400(auth_api):
    res = _create_post(auth_api, content='   ')
    assert res.status_code == 400


def test_react_toggle(auth_api):
    post_id = _create_post(auth_api).json()['id']
    r1 = auth_api.post(f'/api/posts/{post_id}/react', {'reaction': 'love'}, format='json')
    assert r1.status_code == 200
    assert r1.json()['my_reaction'] == 'love'
    assert r1.json()['reactions']['love'] == 1
    # cùng loại → gỡ
    r2 = auth_api.post(f'/api/posts/{post_id}/react', {'reaction': 'love'}, format='json')
    assert r2.json()['my_reaction'] is None
    assert r2.json()['reactions']['love'] == 0


def test_react_invalid_type_400(auth_api):
    post_id = _create_post(auth_api).json()['id']
    res = auth_api.post(f'/api/posts/{post_id}/react', {'reaction': 'meh'}, format='json')
    assert res.status_code == 400


def test_comment_nesting_one_level_only(auth_api):
    post_id = _create_post(auth_api).json()['id']
    c1 = auth_api.post(f'/api/posts/{post_id}/comments', {'content': 'gốc'}, format='json').json()
    c2 = auth_api.post(f'/api/posts/{post_id}/comments',
                       {'content': 'reply', 'parent_comment_id': c1['id']}, format='json').json()
    # reply của reply → 400
    r3 = auth_api.post(f'/api/posts/{post_id}/comments',
                       {'content': 'reply-of-reply', 'parent_comment_id': c2['id']}, format='json')
    assert r3.status_code == 400


def test_modify_other_users_post_403(auth_api, api, db):
    from accounts.models import User
    from common.db import q1
    post_id = _create_post(auth_api).json()['id']
    other = q1("INSERT INTO users (name, email, password) VALUES (%s,%s,%s) RETURNING id",
               ('Forum Other', 'dj_forum_other@example.com', 'x'))['id']
    api.force_authenticate(user=User.objects.get(id=other))
    res = api.put(f'/api/posts/{post_id}', {'content': 'hack'}, format='json')
    assert res.status_code == 403
