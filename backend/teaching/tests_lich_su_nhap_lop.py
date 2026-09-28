"""4.1 — Xem lịch sử lớp (V-n, 25/09/2026).

Phần "nhập DS học viên từ bảng tính vào lớp" (V-j) từng ở đây đã bỏ: gộp nhánh `erp`
(27/09/2026) mang sang một bản làm SẴN, đầy đủ hơn (`teaching/nhap_hoc_vien.py` +
`teaching/tests_nhap_hoc_vien.py`, cùng ticket V-j) — giữ cả hai là hai tuyến trùng cùng
một URL. Bỏ bản ở đây (`AdminClassImportStudentsView`, `_nhap_hang_loat`), dùng bản kia.
"""
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q1
from common.permissions import ROLE_ACADEMIC, ROLE_STUDENT, ROLE_TEACHER
from teaching.views import AdminClassDetailView, AdminClassHistoryView

f = APIRequestFactory()


def _goi(view, method, body=None, ai=None, url='/x', fmt='json', **kw):
    req = (getattr(f, method)(url, body, format=fmt) if body is not None
           else getattr(f, method)(url))
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(ten, vai, hau_to='lsnl'):
    r = q1('INSERT INTO users (name, email, password, role, streak) '
           'VALUES (%s, %s, %s, %s, 0) RETURNING id',
           (ten, '%s_%s@example.com' % (ten.replace(' ', '_').lower(), hau_to), 'x', vai))
    return User.objects.get(id=r['id'])


@pytest.fixture
def canh(db):
    hocvu = _nguoi('HocVu LS', ROLE_ACADEMIC)
    gv = _nguoi('GV LS', ROLE_TEACHER)
    lop = q1("INSERT INTO classes (name, teacher_id, status, created_at) "
             "VALUES ('Lớp lịch sử/nhập', %s, 'active', now()) RETURNING id", (gv.id,))['id']
    return {'hocvu': hocvu, 'gv': gv, 'lop': lop}


# ── Lịch sử lớp (V-n) ────────────────────────────────────────────────────────

def test_lich_su_lop_gom_tao_va_sua(canh):
    r = _goi(AdminClassDetailView, 'put', {'note': 'Ghi chú mới'},
             ai=canh['hocvu'], class_id=canh['lop'])
    assert r.status_code == 200, r.data

    h = _goi(AdminClassHistoryView, 'get', ai=canh['hocvu'], class_id=canh['lop'])
    assert h.status_code == 200, h.data
    hanh_dong = [e['action'] for e in h.data['history']]
    assert 'class.update' in hanh_dong, h.data
    # Mới nhất ở TRÊN.
    assert h.data['history'][0]['action'] == 'class.update'


def test_lich_su_lop_khong_lan_lop_khac(canh):
    lop2 = q1("INSERT INTO classes (name, status, created_at) "
             "VALUES ('Lớp khác LS', 'active', now()) RETURNING id")['id']
    _goi(AdminClassDetailView, 'put', {'note': 'Đổi lớp 1'}, ai=canh['hocvu'], class_id=canh['lop'])
    _goi(AdminClassDetailView, 'put', {'note': 'Đổi lớp 2'}, ai=canh['hocvu'], class_id=lop2)

    h1 = _goi(AdminClassHistoryView, 'get', ai=canh['hocvu'], class_id=canh['lop'])
    assert all(e['summary'] and 'lớp 2' not in e['summary'].lower() for e in h1.data['history'])
    h2 = _goi(AdminClassHistoryView, 'get', ai=canh['hocvu'], class_id=lop2)
    assert all('lớp 1' not in (e['summary'] or '').lower() for e in h2.data['history'])


def test_lich_su_lop_khong_ton_tai_404(canh):
    r = _goi(AdminClassHistoryView, 'get', ai=canh['hocvu'], class_id=999999)
    assert r.status_code == 404


def test_giang_vien_khong_xem_duoc_lich_su_lop(canh):
    r = _goi(AdminClassHistoryView, 'get', ai=canh['gv'], class_id=canh['lop'])
    assert r.status_code == 403


def test_hoc_vien_khong_xem_duoc_lich_su_lop(canh):
    em = _nguoi('Em LS', ROLE_STUDENT)
    r = _goi(AdminClassHistoryView, 'get', ai=em, class_id=canh['lop'])
    assert r.status_code == 403

