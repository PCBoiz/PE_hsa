"""Test cơ bản app roadmap (0-test ở bản Flask)."""
import pytest

pytestmark = pytest.mark.django_db


def test_list_templates_when_no_survey(auth_api):
    res = auth_api.get('/api/roadmaps')
    assert res.status_code == 200
    data = res.json()
    ids = [r['id'] for r in data]
    # Kiểm HÌNH DẠNG, không kiểm danh sách id cụ thể. Bản cũ đòi đúng
    # ['frontend', 'backend', 'python', 'cpp'] — bốn lộ trình của ProgrammingEdu,
    # không còn tồn tại trong CSDL HSA. Ghim tên dữ liệu mẫu vào phép kiểm khiến
    # nó hỏng mỗi lần giáo trình đổi, mà giáo trình thì SẼ đổi (schema §26).
    assert ids, 'phải có ít nhất một lộ trình'
    assert 'nodes' in data[0] and 'edges' in data[0]


def test_update_item_requires_roadmap_id(auth_api):
    res = auth_api.put('/api/roadmap/rm_1', {'done': True}, format='json')
    assert res.status_code == 400


def test_progress_toggle_flow(auth_api):
    r1 = auth_api.put('/api/roadmap/rm_1', {'done': True, 'roadmap_id': 'frontend'}, format='json')
    assert r1.status_code == 200
    done = auth_api.get('/api/roadmap?roadmap_id=frontend').json()['doneItems']
    assert 'rm_1' in done
    auth_api.put('/api/roadmap/rm_1', {'done': False, 'roadmap_id': 'frontend'}, format='json')
    done2 = auth_api.get('/api/roadmap?roadmap_id=frontend').json()['doneItems']
    assert 'rm_1' not in done2


def test_my_roadmap_save_and_get(auth_api):
    r = auth_api.post('/api/me/roadmap', {'mermaid_def': 'flowchart TD\n  a --> b'}, format='json')
    assert r.status_code == 200
    data = auth_api.get('/api/me/roadmap').json()
    assert 'a --> b' in data['mermaid_def']


def test_ai_roadmap_is_premium_402(auth_api):
    assert auth_api.post('/api/me/roadmap/ai').status_code == 402
