"""Loại lớp + danh sách lớp mở rộng được (§54, 24/09/2026) — mục 1.2a kế hoạch thử nghiệm.

TopHSA có ~400 lớp gia sư cá nhân hoá bên cạnh lớp nhóm. `GET /api/admin/classes`
trước hôm nay trả MỌI lớp một lượt; nay lọc + phân trang ở máy chủ, đếm theo
loại/trạng thái cho hàng chip. `/api/admin/classes/options` là danh sách GỌN (không
sĩ số, không phân trang) cho các ô chọn lớp ở màn khác — phải ra TRƯỚC phân trang,
nếu không ô lọc lớp ở màn Tài khoản lặng lẽ chỉ còn 25 lớp đầu.

Đi qua VIEW THẬT; chạy trên CSDL trong giao dịch cuộn lại (`conftest.py`). Mỗi phép
kiểm lọc về lớp của CHÍNH nó bằng tiền tố tên riêng (CSDL dùng chung).
"""
import uuid

import pytest
from django.db import IntegrityError, transaction
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q1, x
from common.permissions import ROLE_ACADEMIC, ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER

f = APIRequestFactory()
pytestmark = pytest.mark.django_db


def _goi(view, method, body=None, ai=None, qs='', **kw):
    duong = '/x' + qs
    req = getattr(f, method)(duong, body, format='json') if body is not None else getattr(f, method)(duong)
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(ten, vai):
    r = q1('INSERT INTO users (name, email, password, role, streak) VALUES (%s, %s, %s, %s, 0) RETURNING id',
           (ten, 'dsl_%s@example.com' % uuid.uuid4().hex[:10], 'x', vai))
    return User.objects.get(id=r['id'])


def _lop(ten, gv=None, loai='nhom', status='active'):
    return q1("INSERT INTO classes (name, course_id, teacher_id, status, class_type) "
              "VALUES (%s, 'hsa_quantitative', %s, %s, %s) RETURNING id",
              (ten, gv.id if gv else None, status, loai))['id']


def _vao(lop, u):
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, now())', (lop, u.id))


@pytest.fixture
def canh():
    tien_to = 'DSL%s' % uuid.uuid4().hex[:6]
    hv = _nguoi('HocVu DSL', ROLE_ACADEMIC)
    gv1, gv2 = _nguoi('GV1 DSL', ROLE_TEACHER), _nguoi('GV2 DSL', ROLE_TEACHER)
    tg = _nguoi('TG DSL', ROLE_ASSISTANT)
    nhom = _lop('%s Nhom A' % tien_to, gv1)
    gia_su = _lop('%s Gia su B' % tien_to, gv2, loai='gia_su')
    xong = _lop('%s Nhom C' % tien_to, gv1, status='finished')
    _vao(nhom, tg)
    return {'tt': tien_to, 'hv': hv, 'gv1': gv1, 'gv2': gv2, 'tg': tg,
            'nhom': nhom, 'gia_su': gia_su, 'xong': xong}


def _ds(canh, qs=''):
    from teaching.views import AdminClassesView
    r = _goi(AdminClassesView, 'get', ai=canh['hv'], qs='?q=%s%s' % (canh['tt'], qs))
    assert r.status_code == 200, r.data
    return r.data


def test_lop_moi_mac_dinh_nhom_va_check_chan_gia_tri_la(canh):
    from teaching.views import AdminClassesView
    r = _goi(AdminClassesView, 'post', {'name': '%s Moi' % canh['tt']}, ai=canh['hv'])
    assert r.status_code in (200, 201), r.data
    assert q1('SELECT class_type FROM classes WHERE id=%s', (r.data['id'],))['class_type'] == 'nhom'
    with pytest.raises(IntegrityError), transaction.atomic():
        _lop('%s La' % canh['tt'], loai='ca_nhan')


def test_loc_theo_loai_giang_vien_tro_giang_trang_thai(canh):
    ids = lambda d: {c['id'] for c in d['classes']}  # noqa: E731
    assert ids(_ds(canh)) == {canh['nhom'], canh['gia_su'], canh['xong']}
    assert ids(_ds(canh, '&type=gia_su')) == {canh['gia_su']}
    assert ids(_ds(canh, '&status=finished')) == {canh['xong']}
    assert ids(_ds(canh, '&teacher_id=%s' % canh['gv1'].id)) == {canh['nhom'], canh['xong']}
    # Lọc "giảng viên" tìm cả lớp mà người ấy là TRỢ GIẢNG đang gán.
    assert ids(_ds(canh, '&teacher_id=%s' % canh['tg'].id)) == {canh['nhom']}
    d = _ds(canh)
    gs = next(c for c in d['classes'] if c['id'] == canh['gia_su'])
    assert gs['classType'] == 'gia_su'


def test_phan_trang_giu_tong_va_dem_theo_loai(canh):
    d = _ds(canh, '&per_page=1&page=1')
    assert d['total'] == 3 and len(d['classes']) == 1 and d['per_page'] == 1
    rong = _ds(canh, '&per_page=1&page=99')
    assert rong['total'] == 3 and rong['classes'] == [], 'trang rỗng không được làm mất tổng'
    assert d['counts']['byType']['gia_su'] >= 1 and d['counts']['byType']['nhom'] >= 2


def test_lop_gia_su_toi_da_ba_em(canh):
    from teaching.views import AdminClassMembersView
    ems = [_nguoi('Em%d DSL' % i, ROLE_STUDENT) for i in range(4)]
    for em in ems[:3]:
        r = _goi(AdminClassMembersView, 'post', {'user_id': em.id}, ai=canh['hv'], class_id=canh['gia_su'])
        assert r.status_code == 200, r.data
    r = _goi(AdminClassMembersView, 'post', {'user_id': ems[3].id}, ai=canh['hv'], class_id=canh['gia_su'])
    assert r.status_code == 409, r.data
    # Dán hàng loạt: em không vào được nằm riêng ở `full`, không chặn cả lượt.
    email = q1('SELECT email FROM users WHERE id=%s', (ems[3].id,))['email']
    r = _goi(AdminClassMembersView, 'post', {'emails': [email]}, ai=canh['hv'], class_id=canh['gia_su'])
    assert r.status_code == 200 and [e['email'] for e in r.data['full']] == [email], r.data
    # Trợ giảng không tính vào ba chỗ của học viên.
    r = _goi(AdminClassMembersView, 'post', {'user_id': canh['tg'].id}, ai=canh['hv'], class_id=canh['gia_su'])
    assert r.status_code == 200, r.data


def test_doi_loai_lop_ghi_that_va_chan_khi_hon_ba_em(canh):
    from teaching.views import AdminClassDetailView
    loai = lambda lop: q1('SELECT class_type FROM classes WHERE id=%s', (lop,))['class_type']  # noqa: E731
    # Chiều thuận: lớp ≤ 3 em đổi được sang gia sư, và THẬT SỰ ghi.
    r = _goi(AdminClassDetailView, 'put', {'class_type': 'gia_su'}, ai=canh['hv'], class_id=canh['xong'])
    assert r.status_code == 200, r.data
    assert loai(canh['xong']) == 'gia_su'
    # Giá trị lạ → 400 nói đúng tên trường.
    r = _goi(AdminClassDetailView, 'put', {'class_type': 'ca_nhan'}, ai=canh['hv'], class_id=canh['xong'])
    assert r.status_code == 400 and 'Loại lớp' in r.data['error'], r.data
    # Lớp đang > 3 em không đổi sang gia sư được — câu lỗi nói RÕ lý do.
    for i in range(4):
        _vao(canh['nhom'], _nguoi('Ban%d DSL' % i, ROLE_STUDENT))
    r = _goi(AdminClassDetailView, 'put', {'class_type': 'gia_su'}, ai=canh['hv'], class_id=canh['nhom'])
    assert r.status_code == 400 and 'gia sư' in r.data['error'] and '4' in r.data['error'], r.data
    assert loai(canh['nhom']) == 'nhom'
    # `null` = không gửi: sửa tên kèm class_type null không được ghi NULL (cột NOT NULL → 500).
    r = _goi(AdminClassDetailView, 'put', {'class_type': None, 'name': '%s Nhom A2' % canh['tt']},
             ai=canh['hv'], class_id=canh['nhom'])
    assert r.status_code == 200, r.data
    assert loai(canh['nhom']) == 'nhom'


def test_options_gon_khong_phan_trang(canh):
    from teaching.views import AdminClassOptionsView
    r = _goi(AdminClassOptionsView, 'get', ai=canh['hv'], qs='?q=%s' % canh['tt'])
    assert r.status_code == 200, r.data
    ds = {c['id']: c for c in r.data['classes']}
    assert set(ds) == {canh['nhom'], canh['gia_su'], canh['xong']}
    assert ds[canh['gia_su']]['classType'] == 'gia_su'
    assert 'members' not in ds[canh['nhom']], 'danh sách gọn không đếm sĩ số'
    gv = _goi(AdminClassOptionsView, 'get', ai=canh['gv1'])
    assert gv.status_code == 403


def test_cap_hang_loat_vao_lop_gia_su_day_bi_chan_truoc_khi_tao(canh):
    """Lượt cấp hàng loạt xếp cả mẻ bằng MỘT câu — phải kiểm chỗ trống TRƯỚC."""
    from teaching.admin_users import AdminBulkCreateUsersView
    _vao(canh['gia_su'], _nguoi('Co San DSL', ROLE_STUDENT))
    dong = '\n'.join('Em Moi %d, dsl_moi_%s_%d@example.com' % (i, canh['tt'].lower(), i) for i in range(3))
    than = {'text': dong, 'role': ROLE_STUDENT, 'class_id': canh['gia_su']}
    xem = _goi(AdminBulkCreateUsersView, 'post', dict(than, dry_run=True), ai=canh['hv'])
    assert xem.status_code == 200 and any('chỉ còn 2 chỗ' in w for w in xem.data['warnings']), xem.data
    that = _goi(AdminBulkCreateUsersView, 'post', than, ai=canh['hv'])
    assert that.status_code == 400 and 'gia sư' in that.data['error'], that.data
    assert not q1("SELECT 1 AS c FROM users WHERE email LIKE %s", ('dsl_moi_%s_%%' % canh['tt'].lower(),)), \
        'từ chối phải xảy ra TRƯỚC khi cấp tài khoản nào'


def test_them_em_vao_lop_gia_su_ghi_trong_cung_giao_dich_voi_khoa(canh, monkeypatch):
    """Khoá `FOR UPDATE` dòng lớp chỉ chặn được hai lượt thêm cùng lúc nếu câu
    INSERT chạy TRƯỚC khi khoá nhả — tức trong CÙNG giao dịch (savepoint) với khoá.

    Bản đầu (24/09/2026) đếm dưới khoá rồi thoát `atomic()` mới INSERT: hai lượt
    cùng lúc vào lớp 2 em đều đếm được 2, đều nhả khoá, đều ghi → lớp gia sư 4 em.
    Không dựng được hai luồng thật trong giao dịch cuộn lại của pytest, nên phép kiểm
    canh đúng bất biến ấy: savepoint giữ khoá vẫn còn mở lúc câu INSERT chạy.
    """
    from django.db import connection

    from teaching import views
    goc = views.q1
    vet = {}

    def gian_diep(sql, *a, **kw):
        if 'FOR UPDATE' in sql:
            vet['khoa'] = list(connection.savepoint_ids)
        elif sql.lstrip().startswith('INSERT INTO class_members'):
            vet['ghi'] = list(connection.savepoint_ids)
        return goc(sql, *a, **kw)

    monkeypatch.setattr(views, 'q1', gian_diep)
    em = _nguoi('Em Khoa DSL', ROLE_STUDENT)
    r = _goi(views.AdminClassMembersView, 'post', {'user_id': em.id}, ai=canh['hv'], class_id=canh['gia_su'])
    assert r.status_code == 200, r.data
    assert 'khoa' in vet and 'ghi' in vet, vet
    assert vet['khoa'] and vet['ghi'][:len(vet['khoa'])] == vet['khoa'], \
        'INSERT chạy sau khi savepoint giữ khoá đã đóng: %r' % vet


def test_cap_hang_loat_dem_lai_duoi_khoa_khi_co_em_chen_vao(canh, monkeypatch):
    """Kiểm chỗ ở đầu lượt cấp hàng loạt chạy TRƯỚC khi cấp tài khoản; một em được
    thêm vào lớp trong lúc đang cấp (tab khác, người khác) thì lúc xếp lớp chỉ còn
    ít chỗ hơn lúc kiểm. Câu xếp lớp cuối phải đếm lại dưới khoá — không thì lớp gia
    sư vượt 3 em. Tài khoản đã cấp vẫn giữ (thiết kế cũ), em thừa được NÊU TÊN."""
    from teaching import admin_users, ho_so
    goc = ho_so.cap_ma_hoc_vien  # `admin_users` nhập nó TRONG hàm → vá ở nguồn
    chen = {'xong': False}

    def cap_va_chen(uid):
        if not chen['xong']:
            chen['xong'] = True
            _vao(canh['gia_su'], _nguoi('Chen Ngang DSL', ROLE_STUDENT))
        return goc(uid)

    monkeypatch.setattr(ho_so, 'cap_ma_hoc_vien', cap_va_chen)
    _vao(canh['gia_su'], _nguoi('Co San DSL', ROLE_STUDENT))
    dong = '\n'.join('Em Dua %d, dsl_dua_%s_%d@example.com' % (i, canh['tt'].lower(), i) for i in range(2))
    r = _goi(admin_users.AdminBulkCreateUsersView, 'post',
             {'text': dong, 'role': ROLE_STUDENT, 'class_id': canh['gia_su']}, ai=canh['hv'])
    assert r.status_code == 201 and r.data['created'] == 2, r.data
    n = q1('SELECT count(*) AS n FROM class_members m JOIN users u ON u.id = m.user_id '
           'WHERE m.class_id = %s AND m.left_at IS NULL AND u.role = %s', (canh['gia_su'], ROLE_STUDENT))['n']
    assert n == 3, 'lớp gia sư có %d em' % n
    thua = 'dsl_dua_%s_1@example.com' % canh['tt'].lower()
    assert any('chưa vào lớp' in w and thua in w for w in r.data['warnings']), r.data['warnings']
