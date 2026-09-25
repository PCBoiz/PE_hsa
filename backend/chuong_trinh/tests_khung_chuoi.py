"""Luật phiên bản của bộ soạn khung (`courseadmin/syllabus.py`, §64g–h) — chuỗi phiên bản,
xuất bản thay bản cũ cùng chuỗi, nhân bản trong một giao dịch, trọng số > 0, học vụ soạn được."""
import pytest

from common.db import q, q1


def _tao(api, khoa, **than):
    return api.post('/api/admin/courses/%s/syllabus' % khoa, dict({'name': 'Khung'}, **than),
                    format='json')


def _buoi(api, vid, ten='Buổi'):
    return api.post('/api/admin/syllabus/%s/sessions' % vid, {'name': ten}, format='json').json()['id']


def _xuat_ban(api, vid):
    return api.put('/api/admin/syllabus/%s' % vid, {'status': 'xuat_ban'}, format='json')


def test_hoc_vu_soan_duoc_khung(dung):
    hv = dung.api('Quản lý học vụ')
    k = dung.khoa()
    r = _tao(hv, k)
    assert r.status_code == 201, r.json()
    assert _buoi(hv, r.json()['id'])


def test_moi_chuoi_mot_ban_nhap_chuoi_moi_thi_duoc(dung):
    a = dung.api('admin')
    k = dung.khoa()
    v1 = _tao(a, k).json()['id']
    _buoi(a, v1)
    assert _xuat_ban(a, v1).status_code == 200
    assert _tao(a, k, duplicateFrom=v1).status_code == 201
    r = _tao(a, k, duplicateFrom=v1)
    assert r.status_code == 409, 'chuỗi đã có bản nháp — bản nháp thứ hai phải bị từ chối'
    assert _tao(a, k).status_code == 201, 'khung MỚI (chuỗi khác) của cùng môn vẫn tạo được'


def test_xuat_ban_thay_ban_dang_dung_cung_chuoi_lop_o_ban_cu_giu_nguyen(dung):
    a = dung.api('admin')
    k = dung.khoa()
    v1 = _tao(a, k).json()['id']
    ss1 = _buoi(a, v1)
    assert _xuat_ban(a, v1).status_code == 200
    khac = _tao(a, k).json()['id']          # chuỗi khác, cùng môn
    _buoi(a, khac)
    assert _xuat_ban(a, khac).status_code == 200
    lop = dung.lop(k, vid=v1)
    s = dung.buoi(lop, ss=ss1)
    v2 = _tao(a, k, duplicateFrom=v1).json()['id']
    r = _xuat_ban(a, v2)
    assert r.status_code == 200 and r.json()['thayBan'] == v1, r.json()
    trang_thai = {r_['id']: r_['status'] for r_ in q(
        'SELECT id, status FROM syllabus_versions WHERE id = ANY(%s)', ([v1, v2, khac],))}
    assert trang_thai == {v1: 'ngung', v2: 'xuat_ban', khac: 'xuat_ban'}, trang_thai
    assert q1('SELECT syllabus_version_id FROM classes WHERE id = %s', (lop,))['syllabus_version_id'] == v1
    assert q1('SELECT syllabus_session_id FROM class_sessions WHERE id = %s', (s,))['syllabus_session_id'] == ss1


def test_nhan_ban_chep_du_cay_va_cung_chuoi(dung):
    a = dung.api('admin')
    k = dung.khoa()
    v1 = _tao(a, k).json()['id']
    ss = _buoi(a, v1, 'Buổi 1')
    a.post('/api/admin/syllabus-sessions/%s/items' % ss, {'title': 'Nội dung', 'kind': 'chu_de',
                                                          'weight': 3}, format='json')
    a.post('/api/admin/syllabus-sessions/%s/materials' % ss, {'title': 'Tài liệu'}, format='json')
    assert _xuat_ban(a, v1).status_code == 200   # bản nháp của chuỗi phải đi trước đã
    v2 = _tao(a, k, duplicateFrom=v1).json()['id']
    cay = a.get('/api/admin/syllabus/%s' % v2).json()
    assert cay['sessions'][0]['items'][0]['weight'] == 3.0
    assert cay['sessions'][0]['materials'][0]['title'] == 'Tài liệu'
    assert q1('SELECT lineage_id FROM syllabus_versions WHERE id = %s', (v2,))['lineage_id'] == v1


def test_nhan_ban_hong_giua_chung_khong_de_lai_gi(dung, monkeypatch):
    """Câu chép học liệu (câu cuối) hỏng → cả bản mới cuộn lại: không có bản nháp nửa vời."""
    import courseadmin.syllabus as mod
    a = dung.api('admin')
    k = dung.khoa()
    v1 = _tao(a, k).json()['id']
    _buoi(a, v1)
    assert _xuat_ban(a, v1).status_code == 200
    that = mod.x

    def hong(sql, params=None):
        if 'INSERT INTO syllabus_materials' in sql:
            raise RuntimeError('giả lập hỏng')
        return that(sql, params)

    monkeypatch.setattr(mod, 'x', hong)
    try:
        r = _tao(a, k, duplicateFrom=v1)
        assert r.status_code >= 500, r.status_code
    except RuntimeError:
        pass   # tuỳ tầng xử lý lỗi: ném ra ngoài hoặc thành 500 — cả hai đều là "hỏng"
    assert q1('SELECT COUNT(*) AS n FROM syllabus_versions WHERE course_id = %s', (k,))['n'] == 1


@pytest.mark.parametrize('w', [0, -1, 'abc'])
def test_trong_so_khong_duong_bi_tu_choi(dung, w):
    a = dung.api('admin')
    k = dung.khoa()
    ss = _buoi(a, _tao(a, k).json()['id'])
    r = a.post('/api/admin/syllabus-sessions/%s/items' % ss,
               {'title': 'M', 'kind': 'chu_de', 'weight': w}, format='json')
    assert r.status_code == 400, r.json()


def test_thieu_trong_so_la_1(dung):
    a = dung.api('admin')
    k = dung.khoa()
    ss = _buoi(a, _tao(a, k).json()['id'])
    iid = a.post('/api/admin/syllabus-sessions/%s/items' % ss, {'title': 'M', 'kind': 'chu_de'},
                 format='json').json()['id']
    assert float(q1('SELECT weight FROM syllabus_items WHERE id = %s', (iid,))['weight']) == 1.0
    assert a.put('/api/admin/syllabus-items/%s' % iid, {'weight': None},
                 format='json').status_code == 200
    assert float(q1('SELECT weight FROM syllabus_items WHERE id = %s', (iid,))['weight']) == 1.0
