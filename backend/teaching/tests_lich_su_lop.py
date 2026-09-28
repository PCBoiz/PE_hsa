"""LỊCH SỬ THAY ĐỔI CỦA MỘT LỚP cho học vụ — V-n, bảng TopHSA dòng 4 + 10.

Mọi dòng nhật ký ở đây sinh bằng VIEW THẬT (sửa lớp, thêm em, tạo buổi, điểm danh, chuyển
lớp) — để phép kiểm bắt được lúc một view đổi cách ghi lớp vào `detail` (`class_id` của
buổi học, `fromClassId` của chuyển lớp). Dựng dòng tay bằng SQL thì chỉ kiểm được chính
nó. CSDL cuộn lại sau mỗi test (`conftest.py`).
"""
import uuid

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q1
from common.permissions import ROLE_ACADEMIC, ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER

f = APIRequestFactory()
pytestmark = pytest.mark.django_db


def _goi(view, method, body=None, ai=None, qs='', **kw):
    req = (getattr(f, method)('/x' + qs, body, format='json') if body is not None
           else getattr(f, method)('/x' + qs))
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(vai):
    r = q1('INSERT INTO users (name, email, password, role, streak) VALUES (%s, %s, %s, %s, 0) RETURNING id',
           ('LS %s' % vai, 'ls_%s@example.com' % uuid.uuid4().hex[:10], 'x', vai))
    return User.objects.get(id=r['id'])


@pytest.fixture
def canh(db):
    from teaching.views import AdminClassesView
    hv = _nguoi(ROLE_ACADEMIC)
    gv = _nguoi(ROLE_TEACHER)
    lop = {}
    for k in ('a', 'b'):
        r = _goi(AdminClassesView, 'post', {'name': 'LS lớp %s %s' % (k, uuid.uuid4().hex[:6]),
                                            'teacher_id': gv.id, 'status': 'active'}, ai=hv)
        assert r.status_code == 201, r.data
        lop[k] = r.data['id']
    return {'hv': hv, 'gv': gv, 'a': lop['a'], 'b': lop['b']}


def test_lich_su_lop_gom_dung_viec_cua_lop_moi_nhat_truoc(canh):
    from teaching.chuyen_lop import ChuyenLopView
    from teaching.lich_su_lop import LichSuLopView
    from teaching.sessions import (
        ClassSessionDetailView,
        ClassSessionsView,
        SessionAttendanceView,
    )
    from teaching.views import (
        AdminClassDetailView,
        AdminClassMembersView,
        AdminResetPasswordView,
    )
    hv, a, b = canh['hv'], canh['a'], canh['b']
    em, em2 = _nguoi(ROLE_STUDENT), _nguoi(ROLE_STUDENT)
    assert _goi(AdminClassDetailView, 'put', {'room': 'P201'}, ai=hv, class_id=a).status_code == 200
    for e in (em, em2):
        assert _goi(AdminClassMembersView, 'post', {'user_id': e.id}, ai=hv, class_id=a).status_code == 200
    r = _goi(ClassSessionsView, 'post', {'starts_at': '2031-05-04T19:00', 'topic': 'Buổi LS'}, ai=hv, class_id=a)
    assert r.status_code == 201, r.data
    buoi = r.data['id']
    r = _goi(SessionAttendanceView, 'post', {'marks': [{'user_id': em.id, 'status': 'present'}]},
             ai=hv, session_id=buoi)
    assert r.status_code == 200, r.data
    # Sửa buổi rồi HUỶ buổi: nhật ký `session.update` không mang lớp trong `detail` — vẫn phải
    # hiện ở lịch sử lớp (nhận qua id buổi).
    r = _goi(ClassSessionDetailView, 'patch', {'room': 'P305'}, ai=hv, session_id=buoi)
    assert r.status_code == 200, r.data
    r = _goi(ClassSessionDetailView, 'patch', {'status': 'cancelled'}, ai=hv, session_id=buoi)
    assert r.status_code == 200, r.data
    # Buổi đã XOÁ: không còn trong `class_sessions` — nhận qua `detail.class_id`.
    r = _goi(ClassSessionsView, 'post', {'starts_at': '2031-05-11T19:00', 'topic': 'Buổi xoá'}, ai=hv, class_id=a)
    assert r.status_code == 201, r.data
    assert _goi(ClassSessionDetailView, 'delete', ai=hv, session_id=r.data['id']).status_code in (200, 204)
    r = _goi(ChuyenLopView, 'post', {'to_class_id': b}, ai=hv, class_id=a, user_id=em2.id)
    assert r.status_code == 200, r.data
    assert _goi(AdminClassDetailView, 'put', {'room': 'P999'}, ai=hv, class_id=b).status_code == 200
    assert _goi(AdminResetPasswordView, 'post', {}, ai=hv, user_id=em.id).status_code == 200

    r = _goi(LichSuLopView, 'get', ai=hv, class_id=a)
    assert r.status_code == 200, r.data
    viec = [e['action'] for e in r.data['entries']]
    assert viec == ['class.member.transfer', 'session.delete', 'session.create', 'session.update',
                    'session.update', 'session.create', 'class.member.add', 'class.member.add',
                    'class.update', 'class.create'], viec
    assert r.data['total'] == 10
    assert all(set(e) == {'id', 'actorName', 'actorRole', 'action', 'summary', 'occurredAt'}
               for e in r.data['entries']), 'không lộ ip / detail'
    assert r.data['entries'][0]['summary'].startswith('Chuyển'), r.data['entries'][0]
    # Lớp B: chuyển lớp VÀO + sửa lớp + tạo lớp — không có việc của lớp A.
    vb = [e['action'] for e in _goi(LichSuLopView, 'get', ai=hv, class_id=b).data['entries']]
    assert vb == ['class.update', 'class.member.transfer', 'class.create'], vb
    # Phân trang: tổng giữ nguyên, trang 2 tiếp đúng chỗ trang 1 dừng.
    t1 = _goi(LichSuLopView, 'get', ai=hv, qs='?per_page=6', class_id=a).data
    t2 = _goi(LichSuLopView, 'get', ai=hv, qs='?per_page=6&page=2', class_id=a).data
    assert t1['total'] == t2['total'] == 10
    assert [e['action'] for e in t1['entries'] + t2['entries']] == viec


def test_quyen_va_lop_khong_co(canh):
    from teaching.lich_su_lop import LichSuLopView
    assert _goi(LichSuLopView, 'get', ai=_nguoi(ROLE_ADMIN), class_id=canh['a']).status_code == 200
    assert _goi(LichSuLopView, 'get', ai=canh['gv'], class_id=canh['a']).status_code == 403
    assert _goi(LichSuLopView, 'get', ai=_nguoi(ROLE_STUDENT), class_id=canh['a']).status_code == 403
    assert _goi(LichSuLopView, 'get', ai=canh['hv'], class_id=0).status_code == 404
