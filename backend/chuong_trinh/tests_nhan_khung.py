"""Lớp nhận khung — `PUT /api/admin/classes/<id>/chuong-trinh` (`dich_vu.nhan_khung`).

Ba ca then chốt đỏ trên bản ghép theo VỊ TRÍ của 3f47421 (`ClassSyllabusView`):
buổi khung đã có gắn tay bị phát lần hai; lớp đổi bản giữ gắn vào bản cũ; lớp không môn
không nhận được khung.
"""
from common.db import q, q1, x


def _gan(r):
    return {row['id']: row['syllabus_session_id'] for row in q(
        'SELECT id, syllabus_session_id FROM class_sessions WHERE class_id = %s', (r,))}


def _nhan(api, lop, vid, **them):
    return api.put('/api/admin/classes/%s/chuong-trinh' % lop, dict({'versionId': vid}, **them),
                   format='json')


def test_gan_theo_thu_tu_ngay_bo_buoi_huy_va_buoi_bu_dien_ten_khi_trong(dung):
    hv = dung.api('Quản lý học vụ')
    k = dung.khoa()
    b = dung.ban(k, [[1], [1], [1]])
    lop = dung.lop(k)
    b1 = dung.buoi(lop, ngay=-5)
    huy = dung.buoi(lop, ngay=-4, status='cancelled')
    bu = dung.buoi(lop, ngay=-3, makeup_for=b1)
    b2 = dung.buoi(lop, ngay=-2, topic='Giảng viên tự đặt tên')
    b3 = dung.buoi(lop, ngay=2)
    r = _nhan(hv, lop, b['id'])
    assert r.status_code == 200, r.json()
    g = _gan(lop)
    assert [g[b1], g[b2], g[b3]] == b['buoi'], g
    assert g[huy] is None and g[bu] is None, 'buổi huỷ và buổi bù không vào lượt gắn tự động'
    ten = {row['id']: row['topic'] for row in q(
        'SELECT id, topic FROM class_sessions WHERE class_id = %s', (lop,))}
    assert ten[b1] == 'Buổi khung 1' and ten[b2] == 'Giảng viên tự đặt tên', ten
    assert r.json()['boQuaBuoiHuy'] == 1 and r.json()['boQuaBuoiBu'] == 1
    # Con số báo cho học vụ ở bước xem trước phải khớp việc thật: 2 buổi trống tên
    # (b1, b3) — không tính b2 đã có tên.
    assert r.json()['dienTen'] == 2


def test_khong_de_gan_tay_va_khong_phat_lai_buoi_khung_da_co_nguoi_giu(dung):
    """Buổi học SAU được gắn tay vào buổi khung 1 → buổi học ĐẦU phải nhận buổi khung 2,
    không nhận lại buổi khung 1 (bản 3f47421 ghép theo vị trí: cả hai cùng buổi khung 1)."""
    hv = dung.api('admin')
    k = dung.khoa()
    b = dung.ban(k, [[1], [1], [1]])
    lop = dung.lop(k)
    dau = dung.buoi(lop, ngay=-5)
    sau = dung.buoi(lop, ngay=-2)
    x('UPDATE classes SET syllabus_version_id = %s WHERE id = %s', (b['id'], lop))
    x('UPDATE class_sessions SET syllabus_session_id = %s WHERE id = %s', (b['buoi'][0], sau))
    r = _nhan(hv, lop, b['id'])
    assert r.status_code == 200, r.json()
    g = _gan(lop)
    assert g[sau] == b['buoi'][0], 'gắn tay giữ nguyên'
    assert g[dau] == b['buoi'][1], 'buổi khung đã có người giữ thì không phát lần hai'
    assert [k_['soBuoi'] for k_ in r.json()['khungThieu']] == [3]


def test_dry_run_khong_ghi_gi(dung):
    hv = dung.api('admin')
    k = dung.khoa()
    b = dung.ban(k, [[1]])
    lop = dung.lop(k)
    s = dung.buoi(lop)
    r = _nhan(hv, lop, b['id'], dryRun=True)
    assert r.status_code == 200 and r.json()['ghiThat'] is False
    assert r.json()['ganMoi'][0]['sessionId'] == s
    assert _gan(lop)[s] is None
    assert q1('SELECT syllabus_version_id FROM classes WHERE id = %s', (lop,))['syllabus_version_id'] is None


def test_lop_khong_mon_nhan_duoc_khung_lop_khac_mon_bi_tu_choi(dung):
    hv = dung.api('admin')
    k = dung.khoa()
    b = dung.ban(k, [[1]])
    ca_ba = dung.lop(None)
    dung.buoi(ca_ba)
    assert _nhan(hv, ca_ba, b['id']).status_code == 200, 'lớp ôn cả ba môn nhận khung môn nào cũng được'
    khac = dung.lop(dung.khoa())
    assert _nhan(hv, khac, b['id']).status_code == 400


def test_chi_nhan_ban_dang_dung(dung):
    hv = dung.api('admin')
    k = dung.khoa()
    nhap = dung.ban(k, [[1]], status='nhap')
    lop = dung.lop(k)
    assert _nhan(hv, lop, nhap['id']).status_code == 409


def test_doi_ban_dich_gan_va_so_dau_bai_theo_so_buoi(dung):
    """Lớp đang theo bản 1 (đã ghi sổ buổi 1) nhận bản 2 cùng chuỗi → buổi đã gắn chuyển sang
    buổi khung CÙNG SỐ của bản 2, mục trong sổ chuyển sang mục CÙNG TÊN — tiến độ giữ nguyên.
    Bản 3f47421 giữ gắn vào bản 1 → tiến độ bản 2 về 0."""
    from chuong_trinh.tien_do import tien_do_lop
    hv = dung.api('admin')
    k = dung.khoa()
    b1 = dung.ban(k, [[1], [1]])
    lop = dung.lop(k)
    s1 = dung.buoi(lop, ngay=-3)
    s2 = dung.buoi(lop, ngay=3)
    assert _nhan(hv, lop, b1['id']).status_code == 200
    dung.ghi_so(s1, [(b1['muc'][0][0], 'done')])
    x("UPDATE syllabus_versions SET status = 'ngung' WHERE id = %s", (b1['id'],))
    b2 = dung.ban(k, [[1], [1], [1]], lineage=b1['id'])
    r = _nhan(hv, lop, b2['id'])
    assert r.status_code == 200, r.json()
    assert r.json()['dichSang'] == 2 and r.json()['doiBan'] is True
    g = _gan(lop)
    assert [g[s1], g[s2]] == b2['buoi'][:2]
    assert q1('SELECT item_id FROM session_log_items WHERE session_id = %s',
              (s1,))['item_id'] == b2['muc'][0][0]
    assert tien_do_lop([lop])[lop]['daXong'] == 1.0


def test_gan_tay_vao_ban_khong_phai_ban_cua_lop_thi_giu_nguyen(dung):
    """Gắn trỏ vào một bản KHÁC bản lớp đang theo (không phải lượt đổi bản) — giữ nguyên,
    như `courseadmin/tests_syllabus.py::test_gan_khung_khong_de_buoi_da_khop_tay`."""
    hv = dung.api('admin')
    k = dung.khoa()
    b = dung.ban(k, [[1]])
    la = dung.ban(k, [[1]])
    lop = dung.lop(k)
    s = dung.buoi(lop)
    x('UPDATE class_sessions SET syllabus_session_id = %s WHERE id = %s', (la['buoi'][0], s))
    assert _nhan(hv, lop, b['id']).status_code == 200
    assert _gan(lop)[s] == la['buoi'][0]


def test_giang_vien_va_hoc_vien_khong_nhan_khung_duoc(dung):
    k = dung.khoa()
    b = dung.ban(k, [[1]])
    gv = dung.api('Giảng viên')
    lop = dung.lop(k, gv=gv.uid)
    assert _nhan(gv, lop, b['id']).status_code == 403
    assert _nhan(dung.api('Học viên'), lop, b['id']).status_code == 403


# ── Gắn tay một buổi ───────────────────────────────────────────────────────────

def test_gan_tay_chi_buoi_khung_cua_ban_lop_dang_theo(dung):
    k = dung.khoa()
    b = dung.ban(k, [[1], [1]])
    la = dung.ban(k, [[1]])
    gv = dung.api('Giảng viên')
    lop = dung.lop(k, gv=gv.uid, vid=b['id'])
    s = dung.buoi(lop)
    url = '/api/teach/sessions/%s/chuong-trinh' % s
    assert gv.patch(url, {'syllabusSessionId': la['buoi'][0]}, format='json').status_code == 400
    r = gv.patch(url, {'syllabusSessionId': b['buoi'][1]}, format='json')
    assert r.status_code == 200 and r.json()['soBuoi'] == 2
    assert gv.patch(url, {'syllabusSessionId': None}, format='json').status_code == 200
    assert _gan(lop)[s] is None


def test_gan_tay_giang_vien_lop_khac_nhan_404(dung):
    k = dung.khoa()
    b = dung.ban(k, [[1]])
    lop = dung.lop(k, vid=b['id'], gv=dung.nguoi('Giảng viên'))
    s = dung.buoi(lop)
    r = dung.api('Giảng viên').patch('/api/teach/sessions/%s/chuong-trinh' % s,
                                     {'syllabusSessionId': b['buoi'][0]}, format='json')
    assert r.status_code == 404
