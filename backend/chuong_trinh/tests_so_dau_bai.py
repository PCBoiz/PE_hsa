"""Sổ đầu bài (`chuong_trinh/so_dau_bai.py`) — cửa, quyền, luật ghi."""
import pytest

from chuong_trinh.dich_vu import tien_do_lop
from common.db import q, q1


@pytest.fixture
def lop_co_khung(dung):
    k = dung.khoa()
    b = dung.ban(k, [[1, 2], [1]])
    gv = dung.api('Giảng viên')
    lop = dung.lop(k, gv=gv.uid, vid=b['id'])
    da_day = dung.buoi(lop, ngay=-1, ss=b['buoi'][0])
    sap_toi = dung.buoi(lop, ngay=3, ss=b['buoi'][1])
    return {'k': k, 'ban': b, 'gv': gv, 'lop': lop, 'da_day': da_day, 'sap_toi': sap_toi}


def _url(sid):
    return '/api/teach/sessions/%d/so-dau-bai' % sid


def test_giang_vien_ghi_so_muc_ke_hoach_va_tien_do_doi_theo(dung, lop_co_khung):
    L = lop_co_khung
    em = dung.nguoi()
    dung.vao(L['lop'], em)
    r = L['gv'].get(_url(L['da_day']))
    assert r.status_code == 200
    assert [m['itemId'] for m in r.data['mucKeHoach']] == L['ban']['muc'][0]
    assert r.data['ghiDuoc'] is True and r.data['soDauBai'] is None
    assert tien_do_lop([L['lop']])[L['lop']]['chuaGhiSo'] == 1

    m1, m2 = L['ban']['muc'][0]
    r = L['gv'].put(_url(L['da_day']), {
        'items': [{'item_id': m1, 'status': 'done', 'label': 'chữ trình duyệt'},
                  {'item_id': m2, 'status': 'partial', 'note': 'còn phần b'}],
        'comprehension': 4, 'de_xuat': 'Cần một buổi luyện thêm',
        'support': [{'user_id': em, 'note': 'hổng phần hàm số'}]}, format='json')
    assert r.status_code == 200, r.data
    assert r.data['soDauBai']['comprehension'] == 4
    assert r.data['hocVien'][0]['canHoTro'] is True
    # Tên mục chép từ khung, không lấy chữ trình duyệt gửi.
    assert q1('SELECT label FROM session_log_items WHERE item_id = %s', (m1,))['label'] == 'Mục 1.1'
    td = tien_do_lop([L['lop']])[L['lop']]
    assert td['chuaGhiSo'] == 0
    assert td['phaiXong'] == 3.0 and td['daXong'] == 2.0, 'đã dạy 1 + một phần 0,5 × 2'
    assert q1("SELECT COUNT(*) AS n FROM admin_audit WHERE action = 'session.log' "
              'AND target_id = %s', (str(L['da_day']),))['n'] == 1


def test_luu_lai_thay_toan_bo_so_cu(dung, lop_co_khung):
    L = lop_co_khung
    m1, m2 = L['ban']['muc'][0]
    L['gv'].put(_url(L['da_day']), {'items': [{'item_id': m1, 'status': 'done'},
                                              {'item_id': m2, 'status': 'done'}]}, format='json')
    L['gv'].put(_url(L['da_day']), {'items': [{'item_id': m1, 'status': 'not_done'}]},
                format='json')
    assert [(r['item_id'], r['status']) for r in q(
        'SELECT item_id, status FROM session_log_items WHERE session_id = %s',
        (L['da_day'],))] == [(m1, 'not_done')]


def test_buoi_chua_dien_ra_va_buoi_huy_khong_ghi_duoc(dung, lop_co_khung):
    L = lop_co_khung
    assert L['gv'].put(_url(L['sap_toi']), {'items': []}, format='json').status_code == 409
    huy = dung.buoi(L['lop'], ngay=-2, status='cancelled')
    assert L['gv'].put(_url(huy), {'items': []}, format='json').status_code == 409
    assert not q1('SELECT 1 FROM session_logs WHERE session_id IN (%s, %s)',
                  (L['sap_toi'], huy))


@pytest.mark.parametrize('than', [
    {'comprehension': 6}, {'comprehension': 0}, {'items': [{'item_id': 1, 'status': 'xong'}]},
    {'items': [{'status': 'done'}]}])
def test_than_sai_bi_400(lop_co_khung, than):
    r = lop_co_khung['gv'].put(_url(lop_co_khung['da_day']), than, format='json')
    assert r.status_code == 400 and r.data['error']


def test_muc_cua_khung_khac_bi_400(dung, lop_co_khung):
    L = lop_co_khung
    khac = dung.ban(dung.khoa(), [[1]])
    r = L['gv'].put(_url(L['da_day']), {'items': [{'item_id': khac['muc'][0][0],
                                                   'status': 'done'}]}, format='json')
    assert r.status_code == 400


def test_em_ngoai_lop_khong_danh_dau_ho_tro_duoc(dung, lop_co_khung):
    L = lop_co_khung
    la = dung.nguoi()
    r = L['gv'].put(_url(L['da_day']), {'support': [{'user_id': la}]}, format='json')
    assert r.status_code == 400


def test_hai_nguoi_cung_mo_so_nguoi_sau_nhan_409(dung, lop_co_khung):
    L = lop_co_khung
    m1 = L['ban']['muc'][0][0]
    mo = L['gv'].get(_url(L['da_day'])).data['soDauBai']
    assert mo is None
    assert L['gv'].put(_url(L['da_day']), {'phien_ban': None, 'items': [
        {'item_id': m1, 'status': 'done'}]}, format='json').status_code == 200
    r = L['gv'].put(_url(L['da_day']), {'phien_ban': None, 'items': []}, format='json')
    assert r.status_code == 409 and r.data['xungDot'] is True


def test_tro_giang_cua_lop_ghi_duoc_tro_giang_lop_khac_nhan_404(dung, lop_co_khung):
    L = lop_co_khung
    tg = dung.api('Trợ giảng')
    dung.vao(L['lop'], tg.uid)
    assert tg.get(_url(L['da_day'])).status_code == 200
    assert tg.put(_url(L['da_day']), {'items': []}, format='json').status_code == 200

    tg_khac = dung.api('Trợ giảng')
    dung.vao(dung.lop(L['k']), tg_khac.uid)
    assert tg_khac.get(_url(L['da_day'])).status_code == 404
    assert tg_khac.put(_url(L['da_day']), {'items': []}, format='json').status_code == 404


def test_giang_vien_lop_khac_nhan_404(dung, lop_co_khung):
    gv = dung.api('Giảng viên')
    assert gv.get(_url(lop_co_khung['da_day'])).status_code == 404


def test_hoc_vien_bi_403_o_moi_cua_chuong_trinh(dung, lop_co_khung):
    L = lop_co_khung
    hv = dung.api('Học viên')
    dung.vao(L['lop'], hv.uid)
    assert hv.get(_url(L['da_day'])).status_code == 403
    assert hv.put(_url(L['da_day']), {}, format='json').status_code == 403
    assert hv.get('/api/teach/classes/%d/chuong-trinh' % L['lop']).status_code == 403
    assert hv.patch('/api/teach/sessions/%d/chuong-trinh' % L['da_day'],
                    {'syllabusSessionId': None}, format='json').status_code == 403
    assert hv.put('/api/admin/classes/%d/chuong-trinh' % L['lop'],
                  {'versionId': L['ban']['id']}, format='json').status_code == 403
    assert hv.get('/api/admin/courses/%s/syllabus' % L['k']).status_code == 403


def test_man_chuong_trinh_lop_tra_tien_do_va_tung_em(dung, lop_co_khung):
    L = lop_co_khung
    em = dung.nguoi()
    dung.vao(L['lop'], em)
    dung.diem_danh(L['da_day'], em, 'present')
    dung.ghi_so(L['da_day'], [(L['ban']['muc'][0][0], 'done')])
    r = L['gv'].get('/api/teach/classes/%d/chuong-trinh' % L['lop'])
    assert r.status_code == 200
    assert r.data['quyen']['nhanKhung'] is False and 'luaChon' not in r.data
    assert r.data['tienDo']['daXong'] == 1.0
    assert [(e['userId'], e['pct']) for e in r.data['tungEm']] == [(em, 25.0)]
    assert r.data['buoiKhung'][0]['pctDaDay'] == 33
