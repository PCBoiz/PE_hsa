"""Khung chương trình theo buổi (E1, §64, 25/09/2026) — quản lý khóa học 5.2."""
import pytest

from common.db import q1

pytestmark = pytest.mark.django_db


def _tai_khoan(api, ten, email, vai):
    from accounts.models import User
    row = q1('INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,%s) '
             'RETURNING id', (ten, email, 'x', vai))
    api.force_authenticate(user=User.objects.get(id=row['id']))
    return api


@pytest.fixture
def admin_api(api, db):
    from common.permissions import ROLE_ADMIN
    return _tai_khoan(api, 'Admin CTr', 'dj_admin_ctr_tmp@example.com', ROLE_ADMIN)


@pytest.fixture
def hocvu_api(api, db):
    from common.permissions import ROLE_ACADEMIC
    return _tai_khoan(api, 'HocVu CTr', 'dj_hocvu_ctr_tmp@example.com', ROLE_ACADEMIC)


@pytest.fixture
def giang_vien_api(api, db):
    from common.permissions import ROLE_TEACHER
    return _tai_khoan(api, 'GV CTr', 'dj_gv_ctr_tmp@example.com', ROLE_TEACHER)


@pytest.fixture
def hoc_vien_api(api, db):
    from common.permissions import ROLE_STUDENT
    return _tai_khoan(api, 'HS CTr', 'dj_hs_ctr_tmp@example.com', ROLE_STUDENT)


@pytest.fixture
def khoa(db):
    """Một khóa học test riêng — rollback tự dọn."""
    cid = 'zz_syllabus_test'
    q1("INSERT INTO courses (id, title, is_published) VALUES (%s, %s, true) RETURNING id",
       (cid, 'Khóa test khung chương trình'))
    return cid


# ── Phiên bản: tạo / sửa / xoá / xuất bản ────────────────────────────────────

def test_tao_phien_ban_nhap(admin_api, khoa):
    r = admin_api.post('/api/admin/courses/%s/syllabus' % khoa, {'name': 'Bản nháp 1'}, format='json')
    assert r.status_code == 201, r.json()
    vid = r.json()['id']
    d = admin_api.get('/api/admin/syllabus/%s' % vid)
    assert d.status_code == 200
    body = d.json()
    assert body['status'] == 'nhap' and body['sessions'] == []


def test_them_buoi_va_noi_dung(admin_api, khoa):
    vid = admin_api.post('/api/admin/courses/%s/syllabus' % khoa,
                         {'name': 'B1'}, format='json').json()['id']
    s = admin_api.post('/api/admin/syllabus/%s/sessions' % vid,
                       {'name': 'Buổi 1: Tỉ lệ phần trăm', 'durationMinutes': 90}, format='json')
    assert s.status_code == 201, s.json()
    sid = s.json()['id']
    assert s.json()['sortOrder'] == 1

    it = admin_api.post('/api/admin/syllabus-sessions/%s/items' % sid,
                        {'title': 'Đại số', 'kind': 'chu_de'}, format='json')
    assert it.status_code == 201, it.json()

    m = admin_api.post('/api/admin/syllabus-sessions/%s/materials' % sid,
                       {'title': 'Slide buổi 1'}, format='json')
    assert m.status_code == 201, m.json()
    assert q1('SELECT file_url FROM syllabus_materials WHERE id=%s',
              (m.json()['id'],))['file_url'] is None, 'chưa có file thật thì fileUrl phải rỗng'

    cay = admin_api.get('/api/admin/syllabus/%s' % vid).json()
    assert len(cay['sessions']) == 1
    assert cay['sessions'][0]['items'][0]['title'] == 'Đại số'
    assert cay['sessions'][0]['materials'][0]['title'] == 'Slide buổi 1'


def test_them_buoi_thu_hai_tiep_theo_buoi_dau(admin_api, khoa):
    vid = admin_api.post('/api/admin/courses/%s/syllabus' % khoa, {'name': 'B'}, format='json').json()['id']
    admin_api.post('/api/admin/syllabus/%s/sessions' % vid, {'name': 'Buổi 1'}, format='json')
    r2 = admin_api.post('/api/admin/syllabus/%s/sessions' % vid, {'name': 'Buổi 2'}, format='json')
    assert r2.json()['sortOrder'] == 2


def test_xuat_ban_can_it_nhat_mot_buoi(admin_api, khoa):
    vid = admin_api.post('/api/admin/courses/%s/syllabus' % khoa, {'name': 'Rỗng'}, format='json').json()['id']
    r = admin_api.put('/api/admin/syllabus/%s' % vid, {'status': 'xuat_ban'}, format='json')
    assert r.status_code == 400, r.json()

    admin_api.post('/api/admin/syllabus/%s/sessions' % vid, {'name': 'Buổi 1'}, format='json')
    r2 = admin_api.put('/api/admin/syllabus/%s' % vid, {'status': 'xuat_ban'}, format='json')
    assert r2.status_code == 200, r2.json()
    assert q1('SELECT status FROM syllabus_versions WHERE id=%s', (vid,))['status'] == 'xuat_ban'


def test_khong_sua_duoc_ban_da_xuat_ban(admin_api, khoa):
    vid = admin_api.post('/api/admin/courses/%s/syllabus' % khoa, {'name': 'X'}, format='json').json()['id']
    sid = admin_api.post('/api/admin/syllabus/%s/sessions' % vid, {'name': 'B1'}, format='json').json()['id']
    admin_api.put('/api/admin/syllabus/%s' % vid, {'status': 'xuat_ban'}, format='json')

    assert admin_api.put('/api/admin/syllabus/%s' % vid, {'name': 'Đổi tên'}, format='json').status_code == 409
    assert admin_api.put('/api/admin/syllabus-sessions/%s' % sid, {'name': 'Đổi'}, format='json').status_code == 409
    assert admin_api.post('/api/admin/syllabus/%s/sessions' % vid, {'name': 'B2'}, format='json').status_code == 409
    assert admin_api.delete('/api/admin/syllabus-sessions/%s' % sid).status_code == 409
    # tên KHÔNG đổi — 409 không được ghi nửa vời
    assert q1('SELECT name FROM syllabus_sessions WHERE id=%s', (sid,))['name'] == 'B1'


def test_khong_lui_trang_thai_ve_nhap(admin_api, khoa):
    vid = admin_api.post('/api/admin/courses/%s/syllabus' % khoa, {'name': 'X'}, format='json').json()['id']
    admin_api.post('/api/admin/syllabus/%s/sessions' % vid, {'name': 'B1'}, format='json')
    admin_api.put('/api/admin/syllabus/%s' % vid, {'status': 'xuat_ban'}, format='json')
    r = admin_api.put('/api/admin/syllabus/%s' % vid, {'status': 'nhap'}, format='json')
    assert r.status_code == 409, r.json()


def test_nhan_ban_chep_toan_bo_cay(admin_api, khoa):
    vid = admin_api.post('/api/admin/courses/%s/syllabus' % khoa, {'name': 'Gốc'}, format='json').json()['id']
    sid = admin_api.post('/api/admin/syllabus/%s/sessions' % vid,
                         {'name': 'Buổi 1', 'durationMinutes': 60}, format='json').json()['id']
    admin_api.post('/api/admin/syllabus-sessions/%s/items' % sid, {'title': 'Nội dung A', 'kind': 'bai_hoc'},
                   format='json')
    admin_api.post('/api/admin/syllabus-sessions/%s/materials' % sid, {'title': 'Tài liệu A'}, format='json')
    admin_api.put('/api/admin/syllabus/%s' % vid, {'status': 'xuat_ban'}, format='json')

    r = admin_api.post('/api/admin/courses/%s/syllabus' % khoa,
                       {'name': 'Bản 2', 'duplicateFrom': vid}, format='json')
    assert r.status_code == 201, r.json()
    vid2 = r.json()['id']
    cay = admin_api.get('/api/admin/syllabus/%s' % vid2).json()
    assert cay['status'] == 'nhap', 'bản nhân bản luôn bắt đầu ở nháp dù bản gốc đã xuất bản'
    assert len(cay['sessions']) == 1
    assert cay['sessions'][0]['name'] == 'Buổi 1' and cay['sessions'][0]['durationMinutes'] == 60
    assert cay['sessions'][0]['items'][0]['title'] == 'Nội dung A'
    assert cay['sessions'][0]['materials'][0]['title'] == 'Tài liệu A'
    # sửa được bản MỚI dù bản GỐC đã khoá
    assert admin_api.put('/api/admin/syllabus/%s' % vid2, {'name': 'Bản 2 sửa'},
                         format='json').status_code == 200


def test_xoa_phien_ban_dang_dung_bi_chan(admin_api, khoa):
    vid = admin_api.post('/api/admin/courses/%s/syllabus' % khoa, {'name': 'X'}, format='json').json()['id']
    admin_api.post('/api/admin/syllabus/%s/sessions' % vid, {'name': 'B1'}, format='json')
    admin_api.put('/api/admin/syllabus/%s' % vid, {'status': 'xuat_ban'}, format='json')
    lop = q1("INSERT INTO classes (name, course_id, status, syllabus_version_id) "
             "VALUES ('Lop CTr Test', %s, 'active', %s) RETURNING id", (khoa, vid))['id']
    r = admin_api.delete('/api/admin/syllabus/%s' % vid)
    assert r.status_code == 409, r.json()
    q1('DELETE FROM classes WHERE id=%s RETURNING id', (lop,))  # dọn tay, rollback vẫn dọn nhưng tường minh hơn


# ── Quyền ─────────────────────────────────────────────────────────────────

def test_giang_vien_khong_soan_duoc_khung(giang_vien_api, khoa):
    r = giang_vien_api.post('/api/admin/courses/%s/syllabus' % khoa, {'name': 'X'}, format='json')
    assert r.status_code == 403


def test_hoc_vien_khong_soan_duoc_khung(hoc_vien_api, khoa):
    r = hoc_vien_api.post('/api/admin/courses/%s/syllabus' % khoa, {'name': 'X'}, format='json')
    assert r.status_code == 403


# ── Gán khung cho lớp ─────────────────────────────────────────────────────

@pytest.fixture
def lop_va_khung(admin_api, khoa):
    """1 lớp có 3 buổi thật (2 buổi thường + 1 buổi bù) + 1 khung xuất bản có 2 buổi."""
    gv = q1("INSERT INTO users (name, email, password, role) VALUES "
           "('GV Lop CTr', 'dj_gv_lopctr_tmp@example.com', 'x', 'Giảng viên') RETURNING id")['id']
    lop = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
             "VALUES ('Lop Gan Khung', %s, %s, 'active') RETURNING id", (khoa, gv))['id']
    b1 = q1("INSERT INTO class_sessions (class_id, starts_at, status) "
           "VALUES (%s, now(), 'planned') RETURNING id", (lop,))['id']
    b2 = q1("INSERT INTO class_sessions (class_id, starts_at, status, topic) "
           "VALUES (%s, now() + interval '7 day', 'planned', 'GV đã tự ghi chủ đề') RETURNING id",
           (lop,))['id']
    # buổi bù đi kèm b1 — KHÔNG được tính vào danh sách khớp khung
    q1("INSERT INTO class_sessions (class_id, starts_at, status, makeup_for) "
       "VALUES (%s, now() + interval '1 day', 'planned', %s) RETURNING id", (lop, b1))

    vid = admin_api.post('/api/admin/courses/%s/syllabus' % khoa, {'name': 'Khung Gán'}, format='json').json()['id']
    admin_api.post('/api/admin/syllabus/%s/sessions' % vid, {'name': 'Buổi 1: Mở đầu'}, format='json')
    admin_api.post('/api/admin/syllabus/%s/sessions' % vid, {'name': 'Buổi 2: Tiếp'}, format='json')
    admin_api.put('/api/admin/syllabus/%s' % vid, {'status': 'xuat_ban'}, format='json')
    return {'lop': lop, 'b1': b1, 'b2': b2, 'vid': vid}


def test_gan_khung_khop_theo_thu_tu_khong_de_topic_da_co(admin_api, lop_va_khung):
    lvk = lop_va_khung
    r = admin_api.put('/api/admin/classes/%s/chuong-trinh' % lvk['lop'],
                      {'versionId': lvk['vid']}, format='json')
    assert r.status_code == 200, r.json()
    body = r.json()
    assert body['daKhop'] == 2 and body['thuaTrongKhung'] == 0 and body['thieuTrongLop'] == 0

    b1 = q1('SELECT syllabus_session_id, topic FROM class_sessions WHERE id=%s', (lvk['b1'],))
    assert b1['topic'] == 'Buổi 1: Mở đầu', 'topic rỗng thì được điền từ tên buổi khung'
    b2 = q1('SELECT syllabus_session_id, topic FROM class_sessions WHERE id=%s', (lvk['b2'],))
    assert b2['syllabus_session_id'] is not None
    assert b2['topic'] == 'GV đã tự ghi chủ đề', 'topic GV đã gõ tay thì KHÔNG bị đè'
    assert q1('SELECT syllabus_version_id FROM classes WHERE id=%s',
              (lvk['lop'],))['syllabus_version_id'] == lvk['vid']


def test_gan_khung_dry_run_khong_ghi_gi(admin_api, lop_va_khung):
    lvk = lop_va_khung
    r = admin_api.put('/api/admin/classes/%s/chuong-trinh' % lvk['lop'],
                      {'versionId': lvk['vid'], 'dryRun': True}, format='json')
    assert r.status_code == 200 and r.json()['ghiThat'] is False
    assert q1('SELECT syllabus_session_id FROM class_sessions WHERE id=%s',
              (lvk['b1'],))['syllabus_session_id'] is None
    assert q1('SELECT syllabus_version_id FROM classes WHERE id=%s',
              (lvk['lop'],))['syllabus_version_id'] is None


def test_gan_khung_khong_de_buoi_da_khop_tay(admin_api, lop_va_khung):
    lvk = lop_va_khung
    # Buổi khung CÓ THẬT nhưng ở một version khác (chỉ cần khác NULL và qua
    # được khoá ngoại — id giả 999999 sẽ ăn ForeignKeyViolation).
    v_khac = q1("INSERT INTO syllabus_versions (course_id, name, status) "
               "SELECT course_id, 'Khác', 'xuat_ban' FROM syllabus_versions WHERE id=%s "
               "RETURNING id", (lvk['vid'],))['id']
    buoi_khac = q1("INSERT INTO syllabus_sessions (version_id, sort_order, name) "
                  "VALUES (%s, 1, 'Buổi lạ') RETURNING id", (v_khac,))['id']
    q1('UPDATE class_sessions SET syllabus_session_id=%s WHERE id=%s RETURNING id',
       (buoi_khac, lvk['b1']))
    r = admin_api.put('/api/admin/classes/%s/chuong-trinh' % lvk['lop'],
                      {'versionId': lvk['vid']}, format='json')
    assert r.status_code == 200, r.json()
    assert q1('SELECT syllabus_session_id FROM class_sessions WHERE id=%s',
              (lvk['b1'],))['syllabus_session_id'] == buoi_khac, 'đã khớp tay thì không bị đè'


def test_gan_khung_bao_thua_thieu(admin_api, khoa):
    lop = q1("INSERT INTO classes (name, course_id, status) VALUES ('Lop Le', %s, 'active') "
             "RETURNING id", (khoa,))['id']
    q1("INSERT INTO class_sessions (class_id, starts_at, status) VALUES (%s, now(), 'planned') "
       "RETURNING id", (lop,))
    vid = admin_api.post('/api/admin/courses/%s/syllabus' % khoa, {'name': 'Khung dài'}, format='json').json()['id']
    admin_api.post('/api/admin/syllabus/%s/sessions' % vid, {'name': 'B1'}, format='json')
    admin_api.post('/api/admin/syllabus/%s/sessions' % vid, {'name': 'B2'}, format='json')
    admin_api.put('/api/admin/syllabus/%s' % vid, {'status': 'xuat_ban'}, format='json')

    r = admin_api.put('/api/admin/classes/%s/chuong-trinh' % lop, {'versionId': vid}, format='json')
    assert r.json() == {'ok': True, 'daKhop': 1, 'thuaTrongKhung': 1, 'thieuTrongLop': 0, 'ghiThat': True}


def test_gan_khung_tu_choi_ban_nhap(admin_api, khoa):
    lop = q1("INSERT INTO classes (name, course_id, status) VALUES ('Lop Nhap', %s, 'active') "
             "RETURNING id", (khoa,))['id']
    vid = admin_api.post('/api/admin/courses/%s/syllabus' % khoa, {'name': 'Chưa xuất bản'},
                         format='json').json()['id']
    r = admin_api.put('/api/admin/classes/%s/chuong-trinh' % lop, {'versionId': vid}, format='json')
    assert r.status_code == 409, r.json()


def test_giang_vien_khong_gan_duoc_khung_cho_lop(lop_va_khung, api, db):
    # KHÔNG dùng fixture `giang_vien_api`: nó và `admin_api` (dựng bên trong
    # `lop_va_khung`) dùng CHUNG một `APIClient`, và thứ tự pytest dựng fixture
    # không đảm bảo `force_authenticate` của giảng viên chạy SAU CÙNG — từng
    # đo thật: có lúc request đi lọt bằng thẻ admin còn sót lại. Xác thực lại
    # tường minh, NGAY TRƯỚC lúc gọi, để không phụ thuộc thứ tự dựng fixture.
    from accounts.models import User
    from common.permissions import ROLE_TEACHER
    lvk = lop_va_khung
    gv = q1("INSERT INTO users (name, email, password, role) VALUES "
           "('GV Bi Chan', 'dj_gv_bichan_tmp@example.com', 'x', %s) RETURNING id",
           (ROLE_TEACHER,))['id']
    api.force_authenticate(user=User.objects.get(id=gv))
    r = api.put('/api/admin/classes/%s/chuong-trinh' % lvk['lop'],
               {'versionId': lvk['vid']}, format='json')
    assert r.status_code == 403, 'gán khung là việc vận hành lớp — IsAdminOrAcademic, không phải giảng viên'


# ── Trạng thái khóa học (is_published, V-i) ──────────────────────────────

def test_sua_trang_thai_khoa_hoc(admin_api, khoa):
    assert q1('SELECT is_published FROM courses WHERE id=%s', (khoa,))['is_published'] is True
    r = admin_api.put('/api/admin/courses/%s' % khoa, {'is_published': False}, format='json')
    assert r.status_code == 200, r.json()
    assert q1('SELECT is_published FROM courses WHERE id=%s', (khoa,))['is_published'] is False


def test_is_published_gia_tri_la_khong_hop_le(admin_api, khoa):
    r = admin_api.put('/api/admin/courses/%s' % khoa, {'is_published': 'khong-phai-bool'}, format='json')
    assert r.status_code == 400, r.json()


def test_hoc_vien_khong_mo_duoc_khoa_nhap(khoa):
    from accounts.models import User
    from courses.truy_cap import quyen_khoa
    q1('UPDATE courses SET is_published=false WHERE id=%s RETURNING id', (khoa,))
    em = q1("INSERT INTO users (name, email, password, role) VALUES "
           "('Em Khoa Nhap', 'dj_em_khoanhap_tmp@example.com', 'x', 'Học viên') RETURNING id")['id']
    lop = q1("INSERT INTO classes (name, course_id, status) VALUES ('Lop Khoa Nhap', %s, 'active') "
             "RETURNING id", (khoa,))['id']
    q1('INSERT INTO class_members (class_id, user_id) VALUES (%s, %s) RETURNING id', (lop, em))
    user = User.objects.get(id=em)
    assert khoa not in quyen_khoa(user), 'khóa nháp không được lọt vào danh sách môn đã mở của học viên'
