"""API CHUÔNG mở rộng (E2): phân trang theo khoá, lọc, đánh dấu chưa đọc. Tuyến cũ giữ nguyên."""
import pytest

from common.db import q1, x

pytestmark = pytest.mark.django_db


def _tao(uid, n, loai='system'):
    from notifications.service import notify
    return [notify(uid, loai, 'T%d' % i, 'N', 'post', 1000 + i, coalesce_minutes=0) for i in range(n)]


def test_phan_trang_theo_khoa_khong_trung_khong_sot(auth_api, temp_user):
    ids = _tao(temp_user, 7)
    thay, truoc, trang = [], None, 0
    while True:
        url = '/api/notifications/feed?limit=3' + ('&truoc=%d' % truoc if truoc else '')
        d = auth_api.get(url).json()
        thay += [r['id'] for r in d['items']]
        trang += 1
        truoc = d['tiep']
        if not truoc:
            break
    assert trang == 3
    assert thay == sorted(ids, reverse=True), 'trùng, sót hoặc sai thứ tự'


def test_phan_trang_khong_lech_khi_co_thong_bao_moi_chen_vao(auth_api, temp_user):
    ids = _tao(temp_user, 4)
    d1 = auth_api.get('/api/notifications/feed?limit=2').json()
    _tao(temp_user, 2)                                     # tới giữa hai lần bấm "tải thêm"
    d2 = auth_api.get('/api/notifications/feed?limit=2&truoc=%d' % d1['tiep']).json()
    assert [r['id'] for r in d1['items'] + d2['items']] == sorted(ids, reverse=True)


def test_loc_loai_va_chua_doc(auth_api, temp_user):
    a = _tao(temp_user, 2, 'lich_doi')
    b = _tao(temp_user, 2, 'thong_bao')
    x('UPDATE notifications SET is_read = TRUE WHERE id = %s', (b[0],))
    assert [r['id'] for r in auth_api.get('/api/notifications/feed?loai=lich_doi').json()['items']] == a[::-1]
    assert [r['id'] for r in auth_api.get('/api/notifications/feed?chuaDoc=1&loai=thong_bao').json()['items']] \
        == [b[1]]
    d = auth_api.get('/api/notifications/feed?limit=30').json()
    assert {r['loai'] for r in d['cacLoai']} == {'lich_doi', 'thong_bao'}


def test_danh_dau_chua_doc_doi_so_chuong(auth_api, temp_user):
    nid = _tao(temp_user, 1)[0]
    auth_api.post('/api/notifications/feed/%d/read' % nid)
    assert auth_api.get('/api/notifications/badge').json()['unread'] == 0
    assert q1('SELECT read_at FROM notifications WHERE id = %s', (nid,))['read_at'] is not None
    r = auth_api.post('/api/notifications/feed/%d/unread' % nid)
    assert r.status_code == 200 and r.json()['unread'] == 1
    assert auth_api.get('/api/notifications/badge').json()['unread'] == 1
    assert q1('SELECT is_read, read_at FROM notifications WHERE id = %s', (nid,)) == {'is_read': False,
                                                                                       'read_at': None}


def test_khong_danh_dau_duoc_thong_bao_cua_nguoi_khac(auth_api, temp_admin):
    nid = _tao(temp_admin, 1)[0]
    x('UPDATE notifications SET is_read = TRUE WHERE id = %s', (nid,))
    assert auth_api.post('/api/notifications/feed/%d/unread' % nid).status_code == 404
    assert q1('SELECT is_read FROM notifications WHERE id = %s', (nid,))['is_read'] is True


def test_tuyen_cu_giu_nguyen_hinh_dang(auth_api, temp_user):
    _tao(temp_user, 2)
    d = auth_api.get('/api/notifications/feed').json()
    assert set(d) == {'items', 'unread'} and len(d['items']) == 2
    assert {'id', 'type', 'title', 'body', 'ref_type', 'ref_id', 'is_read', 'created_at',
            'coalesce_count'} <= set(d['items'][0])


def test_limit_bi_kep(auth_api, temp_user):
    _tao(temp_user, 3)
    assert len(auth_api.get('/api/notifications/feed?limit=0').json()['items']) == 1
    assert auth_api.get('/api/notifications/feed?limit=abc&truoc=xyz').status_code == 200
