"""Test cơ bản app accounts (auth/user/follow — domain chưa từng có test ở bản Flask)."""
import pytest

from accounts.hashers import check_werkzeug_password, make_werkzeug_password
from common.db import q1

pytestmark = pytest.mark.django_db


def test_werkzeug_hasher_roundtrip():
    """Hasher tương thích werkzeug: hash mới verify được, sai mật khẩu fail."""
    h = make_werkzeug_password('SecretPass123')
    assert h.startswith('scrypt:')
    assert check_werkzeug_password(h, 'SecretPass123') is True
    assert check_werkzeug_password(h, 'WrongPass') is False


def test_register_then_login_happy_path(api):
    email = 'dj_reg_test@example.com'
    res = api.post('/auth/register', {
        'name': 'Reg Tester', 'email': email, 'password': 'SecretPass123',
    }, format='json')
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert 'access' in data and 'refresh' in data  # JWT thêm vào (MIGRATION_NOTES §Auth)

    res2 = api.post('/auth/login', {'email': email, 'password': 'SecretPass123'}, format='json')
    assert res2.status_code == 200
    assert res2.json()['name'] == 'Reg Tester'

    res3 = api.post('/auth/login', {'email': email, 'password': 'WrongPass99'}, format='json')
    assert res3.status_code == 401


def test_register_validation_errors(api, db):
    res = api.post('/auth/register', {'name': '', 'email': 'bad', 'password': '1'}, format='json')
    assert res.status_code == 400
    errors = res.json()['errors']
    assert 'name' in errors and 'email' in errors and 'password' in errors


def test_login_empty_fields(api, db):
    res = api.post('/auth/login', {'email': '', 'password': ''}, format='json')
    assert res.status_code == 400
    assert 'errors' in res.json()


def test_get_user_requires_auth(api, db):
    res = api.get('/api/user')
    assert res.status_code == 401
    assert res.json() == {'error': 'Chưa đăng nhập'}  # body y hệt guard Flask


def test_get_user_no_password_leak(auth_api):
    data = auth_api.get('/api/user').json()
    assert 'password' not in data  # vá có chủ đích (MIGRATION_NOTES §Vá bảo mật)
    assert data['is_new_user'] is True


def test_follow_self_rejected(auth_api, temp_user):
    res = auth_api.post(f'/api/users/{temp_user}/follow')
    assert res.status_code == 400


def test_follow_unfollow_flow(auth_api):
    other = q1("INSERT INTO users (name, email, password) VALUES (%s,%s,%s) RETURNING id",
               ('Follow Target', 'dj_follow_target@example.com', 'x'))['id']
    res = auth_api.post(f'/api/users/{other}/follow')
    assert res.status_code == 200 and res.json()['following'] is True
    # idempotent
    assert auth_api.post(f'/api/users/{other}/follow').status_code == 200
    res2 = auth_api.delete(f'/api/users/{other}/follow')
    assert res2.json()['following'] is False


def test_survey_generates_roadmap(auth_api, temp_user):
    res = auth_api.post('/api/survey', {'career_target': 'Backend Developer'}, format='json')
    assert res.status_code == 200
    user = q1('SELECT questionnaire_completed FROM users WHERE id=%s', (temp_user,))
    assert user['questionnaire_completed'] == 1
    rm = q1('SELECT id, source FROM roadmaps WHERE id=%s', (f'u{temp_user}_generated',))
    assert rm is not None and rm['source'] == 'generated'
