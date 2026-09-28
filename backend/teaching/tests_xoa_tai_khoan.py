"""Xoá CỨNG tài khoản (§76, 27/09/2026) — `teaching/admin_users.py::AdminUserDeleteView`."""
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q, q1, x
from common.permissions import ROLE_ACADEMIC, ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER
from teaching.admin_users import AdminUserDeleteView

f = APIRequestFactory()


def _goi(ai, user_id, confirm=False):
    url = '/x?confirm=1' if confirm else '/x'
    req = f.delete(url)
    force_authenticate(req, user=ai)
    return AdminUserDeleteView.as_view()(req, user_id=user_id)


def _nguoi(ten, vai, hau_to='xtk'):
    r = q1('INSERT INTO users (name, email, password, role, status, streak) '
           "VALUES (%s, %s, %s, %s, 'active', 0) RETURNING id",
           (ten, '%s_%s@example.com' % (ten.replace(' ', '_').lower(), hau_to), 'x', vai))
    return User.objects.get(id=r['id'])


@pytest.fixture
def admin(db):
    return _nguoi('Admin XTK', ROLE_ADMIN)


def test_xoa_tai_khoan_khong_ton_tai_404(admin):
    r = _goi(admin, 999999)
    assert r.status_code == 404


def test_khong_tu_xoa_chinh_minh(admin):
    r = _goi(admin, admin.id)
    assert r.status_code == 400
    assert q1('SELECT id FROM users WHERE id=%s', (admin.id,))


def test_xoa_tai_khoan_khong_du_lieu_xoa_thang(admin):
    em = _nguoi('Em Trang', ROLE_STUDENT)
    r = _goi(admin, em.id)
    assert r.status_code == 200, r.data
    assert not q1('SELECT id FROM users WHERE id=%s', (em.id,))


def test_xoa_tai_khoan_con_du_lieu_can_confirm(admin):
    em = _nguoi('Em CoDuLieu', ROLE_STUDENT)
    lop = q1("INSERT INTO classes (name, status, created_at) "
             "VALUES ('Lớp XTK', 'active', now()) RETURNING id")['id']
    x("INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, now())",
      (lop, em.id))

    tu_choi = _goi(admin, em.id)
    assert tu_choi.status_code == 409, tu_choi.data
    assert tu_choi.data['needsConfirm'] is True
    assert tu_choi.data['willDelete']['classMemberships'] == 1, tu_choi.data
    # Chưa xác nhận thì KHÔNG được đụng gì.
    assert q1('SELECT id FROM users WHERE id=%s', (em.id,))

    xong = _goi(admin, em.id, confirm=True)
    assert xong.status_code == 200, xong.data
    assert not q1('SELECT id FROM users WHERE id=%s', (em.id,))
    assert not q1('SELECT 1 FROM class_members WHERE user_id=%s', (em.id,))


def test_xoa_giang_vien_canh_bao_va_bo_trong_lop(admin):
    gv = _nguoi('GV MatLop', ROLE_TEACHER)
    lop = q1("INSERT INTO classes (name, teacher_id, status, created_at) "
             "VALUES ('Lớp GV XTK', %s, 'active', now()) RETURNING id", (gv.id,))['id']

    tu_choi = _goi(admin, gv.id)
    assert tu_choi.status_code == 409, tu_choi.data
    assert [c['id'] for c in tu_choi.data['orphanedClasses']] == [lop]

    xong = _goi(admin, gv.id, confirm=True)
    assert xong.status_code == 200, xong.data
    assert q1('SELECT teacher_id FROM classes WHERE id=%s', (lop,))['teacher_id'] is None


def test_xoa_nguoi_tu_van_canh_bao_va_bo_trong_hoc_vien(admin):
    tuvan = _nguoi('HocVu TuVan', ROLE_ACADEMIC)
    em = _nguoi('Em CoTuVan', ROLE_STUDENT)
    x('UPDATE users SET consultant_id=%s WHERE id=%s', (tuvan.id, em.id))

    tu_choi = _goi(admin, tuvan.id)
    assert tu_choi.status_code == 409, tu_choi.data
    assert [s['id'] for s in tu_choi.data['orphanedStudents']] == [em.id]

    xong = _goi(admin, tuvan.id, confirm=True)
    assert xong.status_code == 200, xong.data
    assert q1('SELECT consultant_id FROM users WHERE id=%s', (em.id,))['consultant_id'] is None


def test_xoa_tai_khoan_da_tung_dang_nhap_khong_bi_chan_boi_bang_django(admin):
    """Hồi quy cho đúng phát hiện của §76: tài khoản từng đăng nhập có dòng
    trong `token_blacklist_outstandingtoken` (SimpleJWT) và `account_emailaddress`
    (allauth) — hai khoá NO ACTION đó phải được dọn tay TRƯỚC câu DELETE FROM
    users, không thì cả câu xoá ném IntegrityError."""
    em = _nguoi('Em DaDangNhap', ROLE_STUDENT)
    x("INSERT INTO account_emailaddress (email, verified, \"primary\", user_id) "
      "VALUES (%s, true, true, %s)", (em.email, em.id))
    x("INSERT INTO token_blacklist_outstandingtoken (token, expires_at, user_id, jti) "
      "VALUES ('x', now() + interval '1 day', %s, 'jti-xtk')", (em.id,))

    r = _goi(admin, em.id, confirm=True)
    assert r.status_code == 200, r.data
    assert not q1('SELECT id FROM users WHERE id=%s', (em.id,))
    assert not q('SELECT 1 FROM account_emailaddress WHERE user_id=%s', (em.id,))
    assert not q("SELECT 1 FROM token_blacklist_outstandingtoken WHERE user_id=%s", (em.id,))


def test_giang_vien_khong_xoa_duoc_tai_khoan(admin):
    gv = _nguoi('GV KhongQuyen', ROLE_TEACHER)
    em = _nguoi('Em BiTuChoi', ROLE_STUDENT)
    r = _goi(gv, em.id)
    assert r.status_code == 403
    assert q1('SELECT id FROM users WHERE id=%s', (em.id,))
