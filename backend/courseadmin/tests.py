"""Test cơ bản app courseadmin (admin API — 0-test ở bản Flask)."""
import pytest

from common.db import q1

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_api(api, db):
    from accounts.models import User
    row = q1("INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,%s) RETURNING id",
             ('Admin Tester', 'dj_admin_test@example.com', 'x', 'admin'))
    api.force_authenticate(user=User.objects.get(id=row['id']))
    return api


def test_non_admin_forbidden(auth_api):
    res = auth_api.get('/api/admin/courses')
    assert res.status_code == 403
    assert res.json() == {'error': 'Không có quyền truy cập'}


def test_admin_list_courses(admin_api):
    res = admin_api.get('/api/admin/courses')
    assert res.status_code == 200
    assert any(c['id'] == 'python' for c in res.json()['courses'])


def test_admin_course_crud(admin_api):
    # create
    r = admin_api.post('/api/admin/courses',
                       {'id': 'zz_test_course', 'title': 'Khóa test'}, format='json')
    assert r.status_code == 200
    # duplicate id → 400
    assert admin_api.post('/api/admin/courses',
                          {'id': 'zz_test_course', 'title': 'X'}, format='json').status_code == 400
    # update
    assert admin_api.put('/api/admin/courses/zz_test_course',
                         {'subtitle': 'Sub'}, format='json').status_code == 200
    # lesson create + sync count
    assert admin_api.post('/api/admin/lessons',
                          {'course_id': 'zz_test_course', 'title': 'Bài 1'},
                          format='json').status_code == 200
    assert q1("SELECT lessons FROM courses WHERE id='zz_test_course'")['lessons'] == 1
    # delete course không được khi... (không có enrollment → xóa được sau khi xóa lesson)
    lesson = q1("SELECT id FROM lessons WHERE course_id='zz_test_course' LIMIT 1")
    assert admin_api.delete(f"/api/admin/lessons/{lesson['id']}").status_code == 200
    assert admin_api.delete('/api/admin/courses/zz_test_course').status_code == 200


def test_admin_delete_unknown_404(admin_api):
    assert admin_api.delete('/api/admin/courses/does-not-exist').status_code == 404
