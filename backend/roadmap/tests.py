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


def test_tien_do_tra_ve_CAP_lo_trinh_va_muc(auth_api):
    """`doneItems` là id mục TRẦN — không đủ để client khớp đúng.

    `roadmap.js::normalize` sinh id mục theo VỊ TRÍ (`0-m`, `1-l0`, `2-r1`), nên
    cùng một id tồn tại trong CẢ 26 lộ trình tĩnh. Client cũ khớp theo đuôi khoá
    và làm tiến độ của một lộ trình hiện lên 25 lộ trình còn lại.

    Bảng `roadmap_progress` LUÔN lưu `roadmap_id`; thứ thiếu chỉ là trả CẶP về.
    """
    for lt, muc in (('hsa_quantitative', '0-m'), ('hsa_verbal', '0-m'),
                    ('hsa_quantitative', '1-l0')):
        assert auth_api.put('/api/roadmap/%s' % muc,
                            {'done': True, 'roadmap_id': lt},
                            format='json').status_code == 200

    d = auth_api.get('/api/roadmap').json()
    cap = {(x['roadmapId'], x['itemId']) for x in d['done']}
    assert ('hsa_quantitative', '0-m') in cap
    assert ('hsa_verbal', '0-m') in cap
    assert ('hsa_quantitative', '1-l0') in cap

    # CÙNG id mục, KHÁC lộ trình → phải là HAI cặp riêng. Đây là thông tin mà
    # `doneItems` làm mất: nó chỉ có `['0-m', '0-m', '1-l0']`.
    assert len([1 for r, i in cap if i == '0-m']) == 2, cap

    # `doneItems` vẫn còn cho bản client đang mở dở — không phá nó.
    assert '0-m' in d['doneItems']

    # Lọc theo lộ trình cũng phải trả cặp.
    d2 = auth_api.get('/api/roadmap?roadmap_id=hsa_verbal').json()
    assert {(x['roadmapId'], x['itemId']) for x in d2['done']} == {('hsa_verbal', '0-m')}
