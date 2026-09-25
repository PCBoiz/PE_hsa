"""Mở môn QUA LỚP (mục 1.3 kế hoạch thử nghiệm, 24/09/2026 — góp ý TopHSA số 3).

Khách: "mục Học không rõ để đăng ký hay để quản lý; giáo viên, trợ giảng cũng thấy nút
Đăng ký". Chủ sản phẩm chốt: học viên KHÔNG tự đăng ký — học vụ xếp em vào lớp thì môn
của lớp mở; nhân sự (mọi vai không phải học viên) xem bài ở chế độ chỉ-đọc.

Một cổng duy nhất `courses/truy_cap.py`. Đi qua VIEW THẬT; CSDL cuộn lại sau mỗi test.
"""
import uuid

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q1, x
from common.permissions import ROLE_ACADEMIC, ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER

f = APIRequestFactory()
pytestmark = pytest.mark.django_db
KHOA = 'hsa_quantitative'
KHAC = 'hsa_verbal'


def _goi(view, method, body=None, ai=None, qs='', **kw):
    req = (getattr(f, method)('/x' + qs, body, format='json') if body is not None
           else getattr(f, method)('/x' + qs))
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(vai):
    r = q1('INSERT INTO users (name, email, password, role, streak) VALUES (%s, %s, %s, %s, 0) RETURNING id',
           ('TC %s' % vai, 'tc_%s@example.com' % uuid.uuid4().hex[:10], 'x', vai))
    return User.objects.get(id=r['id'])


def _lop(mon, status='active'):
    return q1("INSERT INTO classes (name, course_id, status) VALUES (%s, %s, %s) RETURNING id",
              ('TC lop %s' % uuid.uuid4().hex[:6], mon, status))['id']


def _vao(lop, u):
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, now())', (lop, u.id))


def _quyen(u):
    from courses.truy_cap import quen_truy_cap, quyen_khoa
    quen_truy_cap(u.id)
    return quyen_khoa(u)


def test_lop_mon_X_mo_X_khong_mo_Y():
    em = _nguoi(ROLE_STUDENT)
    _vao(_lop(KHOA), em)
    q = _quyen(em)
    assert q.get(KHOA) == 'hoc' and KHAC not in q, q


def test_lop_ca_ba_mon_mo_ca_ba():
    em = _nguoi(ROLE_STUDENT)
    _vao(_lop(None), em)
    q = _quyen(em)
    assert {q.get(m) for m in ('hsa_quantitative', 'hsa_verbal', 'hsa_science')} == {'hoc'}, q


def test_roi_lop_hay_lop_huy_thi_mat_quyen():
    em = _nguoi(ROLE_STUDENT)
    lop = _lop(KHOA)
    _vao(lop, em)
    x('UPDATE class_members SET left_at = now(), leave_reason = %s WHERE class_id = %s AND user_id = %s',
      ('dropped', lop, em.id))
    assert KHOA not in _quyen(em)
    em2 = _nguoi(ROLE_STUDENT)
    _vao(_lop(KHOA, status='cancelled'), em2)
    assert KHOA not in _quyen(em2)
    # Lớp ĐÃ KẾT THÚC mà em chưa bị cho rời: vẫn mở (mặc định đã nói với anh Sơn).
    em3 = _nguoi(ROLE_STUDENT)
    _vao(_lop(KHOA, status='finished'), em3)
    assert _quyen(em3).get(KHOA) == 'hoc'


def test_lop_tam_dung_van_giu_quyen_mon():
    """V-c (25/09/2026): học vụ chuyển lớp sang TẠM DỪNG → em VẪN mở được bài (ôn tiếp
    trong lúc lớp nghỉ). Chỉ lớp HUỶ mới đóng môn. Đi qua view thật cả hai phía."""
    from lessons.views import CourseContentView
    from teaching.views import AdminClassDetailView
    em = _nguoi(ROLE_STUDENT)
    lop = _lop(KHOA)
    _vao(lop, em)
    r = _goi(AdminClassDetailView, 'put', {'status': 'paused'}, ai=_nguoi(ROLE_ACADEMIC), class_id=lop)
    assert r.status_code == 200, r.data
    _quyen(em)
    r = _goi(CourseContentView, 'get', ai=em, qs='?lesson=1', course_id=KHOA)
    assert r.status_code == 200 and r.data.get('cheDo') == 'hoc', (r.status_code, r.data.get('cheDo'))


def test_nhan_su_moi_vai_xem_duoc_moi_mon():
    for vai in (ROLE_TEACHER, ROLE_ASSISTANT, ROLE_ACADEMIC, 'admin', 'Biên tập nội dung'):
        q = _quyen(_nguoi(vai))
        assert {q.get(m) for m in ('hsa_quantitative', 'hsa_verbal', 'hsa_science')} == {'xem'}, (vai, q)


def test_noi_dung_bai_hoc_theo_quyen():
    from lessons.views import CourseContentView
    em = _nguoi(ROLE_STUDENT)
    r = _goi(CourseContentView, 'get', ai=em, qs='?lesson=1', course_id=KHOA)
    assert r.status_code == 403 and 'chưa mở cho lớp của em' in r.data['error'], r.data
    _vao(_lop(KHOA), em)
    _quyen(em)
    r = _goi(CourseContentView, 'get', ai=em, qs='?lesson=1', course_id=KHOA)
    assert r.status_code == 200 and r.data.get('cheDo') == 'hoc', r.data.get('cheDo')
    gv = _nguoi(ROLE_TEACHER)
    r = _goi(CourseContentView, 'get', ai=gv, qs='?lesson=1', course_id=KHOA)
    assert r.status_code == 200 and r.data.get('cheDo') == 'xem', r.data.get('cheDo')


def test_hoan_thanh_bai_nhan_su_403_hoc_vien_khong_quyen_403():
    from lessons.views import CompleteLessonView
    gv = _nguoi(ROLE_TEACHER)
    r = _goi(CompleteLessonView, 'post', {'courseId': KHOA, 'answers': {}}, ai=gv, lesson_no=1)
    assert r.status_code == 403 and 'nhân sự' in r.data['error'], r.data
    em = _nguoi(ROLE_STUDENT)
    r = _goi(CompleteLessonView, 'post', {'courseId': KHOA, 'answers': {}}, ai=em, lesson_no=1)
    assert r.status_code == 403, r.data
    assert not q1('SELECT 1 AS c FROM enrollments WHERE user_id = %s', (em.id,)), \
        'học viên không quyền mà vẫn được ghi danh ngầm'


def test_nhan_su_cham_bai_KHONG_ghi_nhan():
    from lessons.grading import dap_an
    from lessons.views import CheckAnswersView
    bang = dap_an(KHOA, 1).get('test') or {}
    assert bang
    gv = _nguoi(ROLE_TEACHER)
    r = _goi(CheckAnswersView, 'post', {'phan': 'test', 'answers': {i: 'x' for i in bang}},
             ai=gv, course_id=KHOA, lesson_no=1)
    assert r.status_code == 200, r.data
    assert not q1('SELECT 1 AS c FROM lesson_progress WHERE user_id = %s', (gv.id,)), \
        'lượt chấm của nhân sự bị ghi thành bài làm'


def test_dang_ky_tu_do_da_dong():
    from courses.views import EnrollView
    em = _nguoi(ROLE_STUDENT)
    assert _goi(EnrollView, 'post', {}, ai=em, course_id=KHOA).status_code == 410
    assert _goi(EnrollView, 'delete', ai=em, course_id=KHOA).status_code == 410
    assert not q1('SELECT 1 AS c FROM enrollments WHERE user_id = %s', (em.id,))


def test_danh_sach_khoa_tra_access():
    from courses.views import CoursesView
    em = _nguoi(ROLE_STUDENT)
    _vao(_lop(KHOA), em)
    _quyen(em)
    ds = {c['id']: c for c in _goi(CoursesView, 'get', ai=em).data}
    assert ds[KHOA]['access'] == 'hoc' and ds[KHOA]['enrolled'] is True
    assert ds[KHAC]['access'] is None and ds[KHAC]['enrolled'] is False


def test_chuyen_lop_doi_quyen_mon_ngay():
    """Chuyển lớp phải QUÊN đệm quyền — không thì em chờ tới 60 giây mới vào được môn mới."""
    from courses.truy_cap import quyen_khoa
    from teaching.chuyen_lop import ChuyenLopView
    em = _nguoi(ROLE_STUDENT)
    a, b = _lop(KHOA), _lop(KHAC)
    _vao(a, em)
    assert _quyen(em).get(KHOA) == 'hoc'           # đệm lúc này: chỉ KHOA
    r = _goi(ChuyenLopView, 'post', {'to_class_id': b}, ai=_nguoi(ROLE_ACADEMIC), class_id=a, user_id=em.id)
    assert r.status_code == 200, r.data
    q = quyen_khoa(em)                               # KHÔNG quên tay — cổng phải tự quên
    assert q.get(KHAC) == 'hoc' and KHOA not in q, q


def _quyen_dem(u):
    """Đọc quyền QUA ĐỆM (không quên tay) — cửa ghi phải tự quên."""
    from courses.truy_cap import quyen_khoa
    return quyen_khoa(u)


def test_them_roi_lop_doi_mon_xoa_lop_deu_quen_dem():
    from teaching.views import AdminClassDetailView, AdminClassMembersView
    hv = _nguoi(ROLE_ACADEMIC)
    em = _nguoi(ROLE_STUDENT)
    lop = _lop(KHOA)
    assert _quyen(em) == {}                                   # đệm: chưa mở gì
    r = _goi(AdminClassMembersView, 'post', {'user_id': em.id}, ai=hv, class_id=lop)
    assert r.status_code == 200, r.data
    assert _quyen_dem(em).get(KHOA) == 'hoc', 'thêm vào lớp mà môn chưa mở (đệm cũ)'

    r = _goi(AdminClassDetailView, 'put', {'course_id': KHAC}, ai=hv, class_id=lop)
    assert r.status_code == 200, r.data
    q = _quyen_dem(em)
    assert q.get(KHAC) == 'hoc' and KHOA not in q, 'đổi môn của lớp mà quyền chưa đổi: %r' % q

    req = f.delete('/x?user_id=%s&leave_reason=dropped' % em.id)
    force_authenticate(req, user=hv)
    assert AdminClassMembersView.as_view()(req, class_id=lop).status_code == 200
    assert _quyen_dem(em) == {}, 'rời lớp mà môn vẫn mở'

    lop2 = _lop(KHOA)
    _vao(lop2, em)
    assert _quyen(em).get(KHOA) == 'hoc'
    req = f.delete('/x?confirm=1')
    force_authenticate(req, user=hv)
    assert AdminClassDetailView.as_view()(req, class_id=lop2).status_code in (200, 204)
    assert _quyen_dem(em) == {}, 'xoá lớp mà môn vẫn mở'
