"""Tiến độ chương trình hiện ở màn của miền khác — qua `dich_vu` (luật S4).

Tổng quan trung tâm, danh sách lớp, "Lớp của tôi", tờ phụ huynh: mỗi nơi một khoá
`chuongTrinh` (tuỳ chọn: lớp chưa nhận khung → None).
"""
import uuid

from common.db import q1, x


def _dot():
    return q1("INSERT INTO terms (name, code) VALUES ('Đợt CT', %s) RETURNING id",
              ('ct-%s' % uuid.uuid4().hex[:8],))['id']


def _lop_cham(dung, k, b, dot=None):
    """Lớp đã học 3 buổi khung, chưa ghi sổ buổi nào → chậm, 3 buổi chưa ghi sổ."""
    lop = dung.lop(k, vid=b['id'])
    if dot:
        x('UPDATE classes SET term_id = %s WHERE id = %s', (dot, lop))
    for i in range(3):
        dung.buoi(lop, ngay=-7 + i, ss=b['buoi'][i])
    return lop


def test_tong_quan_dem_lop_cham_va_lop_chua_ghi_so_so_cau_co_dinh(dung):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    from teaching.overview import tong_quan
    dot = _dot()
    k = dung.khoa()
    b = dung.ban(k, [[1]] * 4)

    def them(n):
        for _ in range(n):
            _lop_cham(dung, k, b, dot)

    them(2)
    with CaptureQueriesContext(connection) as hai:
        d2 = tong_quan(term_id=dot)
    them(18)
    with CaptureQueriesContext(connection) as hai_muoi:
        d = tong_quan(term_id=dot)
    assert len(hai) == len(hai_muoi), (len(hai), len(hai_muoi))
    assert d2['chuongTrinh'] == {'lopCoKhung': 2, 'lopCham': 2, 'lopChuaGhiSo': 2,
                                 'buoiChuaGhiSo': 6}
    assert d['chuongTrinh']['lopCham'] == 20
    assert all(c['chuongTrinh']['cham'] for c in d['classes'])


def test_tong_quan_lop_khong_khung_la_none_va_lop_ghi_so_du_khong_cham(dung):
    from teaching.overview import tong_quan
    dot = _dot()
    k = dung.khoa()
    b = dung.ban(k, [[1]] * 4)
    lop = _lop_cham(dung, k, b, dot)
    for s in q1("SELECT array_agg(id) AS a FROM class_sessions WHERE class_id = %s",
                (lop,))['a']:
        ss = q1('SELECT syllabus_session_id FROM class_sessions WHERE id = %s', (s,))
        muc = q1('SELECT id FROM syllabus_items WHERE session_id = %s',
                 (ss['syllabus_session_id'],))['id']
        dung.ghi_so(s, [(muc, 'done')])
    khong_khung = dung.lop(k)
    x('UPDATE classes SET term_id = %s WHERE id = %s', (dot, khong_khung))
    d = tong_quan(term_id=dot)
    theo_id = {c['id']: c for c in d['classes']}
    assert theo_id[khong_khung]['chuongTrinh'] is None
    assert theo_id[lop]['chuongTrinh']['cham'] is False
    assert d['chuongTrinh'] == {'lopCoKhung': 1, 'lopCham': 0, 'lopChuaGhiSo': 0,
                                'buoiChuaGhiSo': 0}


def test_danh_sach_lop_co_chip_tien_do(dung):
    k = dung.khoa()
    b = dung.ban(k, [[1]] * 4)
    lop = _lop_cham(dung, k, b)
    hv = dung.api('admin')
    r = hv.get('/api/admin/classes', {'course_id': k})
    assert r.status_code == 200
    (dong,) = [c for c in r.data['classes'] if c['id'] == lop]
    assert dong['chuongTrinh']['cham'] is True and dong['chuongTrinh']['chuaGhiSo'] == 3


def test_lop_cua_toi_co_pct_cua_em(dung):
    k = dung.khoa()
    b = dung.ban(k, [[1]] * 4)
    lop = dung.lop(k, vid=b['id'])
    s = dung.buoi(lop, ngay=-1, ss=b['buoi'][0])
    dung.ghi_so(s, [(b['muc'][0][0], 'done')])
    em = dung.api('Học viên')
    dung.vao(lop, em.uid)
    dung.diem_danh(s, em.uid, 'present')
    r = em.get('/api/lop-cua-toi')
    assert r.status_code == 200
    (dong,) = [c for c in r.data['lop'] if c['id'] == lop]
    assert dong['chuongTrinh']['pct'] == 25.0


def test_to_phu_huynh_co_dong_tien_do(dung):
    k = dung.khoa()
    b = dung.ban(k, [[1]] * 2)
    gv = dung.api('Giảng viên')
    lop = dung.lop(k, gv=gv.uid, vid=b['id'])
    s = dung.buoi(lop, ngay=-1, ss=b['buoi'][0])
    dung.ghi_so(s, [(b['muc'][0][0], 'partial')])
    em = dung.nguoi()
    dung.vao(lop, em)
    dung.diem_danh(s, em, 'present')
    r = gv.get('/api/teach/classes/%d/students/%d/parent-report' % (lop, em))
    assert r.status_code == 200, r.data
    assert r.data['chuongTrinh']['pct'] == 25.0
    assert r.data['chuongTrinh']['keHoachPct'] == 50.0


def test_du_lieu_mau_co_khung_so_dau_bai_va_go_sach(db):
    from accounts.models import User
    from teaching import du_lieu_mau as M
    M.go()
    gv = q1("INSERT INTO users (name, email, password, role) "
            "VALUES ('GV CT mẫu', 'gv_ct_mau@example.com', 'x', 'Giảng viên') RETURNING id")['id']
    so = M.tao(giang_vien_id=User.objects.get(id=gv).id, so_em_moi_lop=2)
    assert so['khung chương trình mẫu'] == 1 and so['sổ đầu bài'] > 0
    lop = q1("SELECT id FROM classes WHERE is_demo AND course_id = 'hsa_quantitative'")['id']
    from chuong_trinh.dich_vu import tien_do_lop
    td = tien_do_lop([lop])[lop]
    assert td['chuaGhiSo'] == 1, 'buổi gần nhất cố ý chưa ghi sổ'
    assert td['soBuoiKhung'] == 24 and 0 < td['daXong'] < td['phaiXong']
    M.go()
    assert not q1('SELECT 1 FROM syllabus_versions WHERE is_demo')
