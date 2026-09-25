"""KHOÁ NHÁP — trạng thái "Đang mở / Nháp" của một khoá học (V-i, bảng TopHSA dòng 5).

Trước 25/09/2026 `courses.is_published` có trong lược đồ nhưng KHÔNG đường nào sửa được
(`courseadmin/views.py` không nhận nó), và cổng mở môn (`courses/truy_cap.py`) không đọc
nó — khoá "nháp" và khoá "đang mở" giống hệt nhau với học viên.

Luật: học viên KHÔNG thấy và KHÔNG mở được khoá nháp (kể cả lớp em đang học mang khoá ấy);
nhân sự vẫn thấy ở chế độ chỉ-xem. Đổi trạng thái thì cổng quên đệm của mọi em trong lớp
của khoá ấy NGAY — không chờ 60 giây.

Đi qua VIEW THẬT. CSDL cuộn lại sau mỗi test (`conftest.py`).
"""
import json
import uuid

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q1, x
from common.permissions import ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER

f = APIRequestFactory()
pytestmark = pytest.mark.django_db


def _goi(view, method, body=None, ai=None, qs='', **kw):
    req = (getattr(f, method)('/x' + qs, body, format='json') if body is not None
           else getattr(f, method)('/x' + qs))
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(vai):
    r = q1('INSERT INTO users (name, email, password, role, streak) VALUES (%s, %s, %s, %s, 0) RETURNING id',
           ('KN %s' % vai, 'kn_%s@example.com' % uuid.uuid4().hex[:10], 'x', vai))
    return User.objects.get(id=r['id'])


def _khoa():
    ma = 'kn_%s' % uuid.uuid4().hex[:8]
    x("INSERT INTO courses (id, title, is_published) VALUES (%s, %s, TRUE)", (ma, 'KN khoá %s' % ma))
    return ma


def _lop_co_em(mon):
    em = _nguoi(ROLE_STUDENT)
    lop = q1("INSERT INTO classes (name, course_id, status) VALUES (%s, %s, 'active') RETURNING id",
             ('KN lớp %s' % uuid.uuid4().hex[:6], mon))['id']
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, now())', (lop, em.id))
    return em


def _dat(ma, mo, ai):
    from courseadmin.views import AdminCourseDetailView
    return _goi(AdminCourseDetailView, 'put', {'is_published': mo}, ai=ai, course_id=ma)


def test_sua_duoc_is_published_va_ghi_nhat_ky():
    from courseadmin.views import AdminCourseDetailView
    ad = _nguoi(ROLE_ADMIN)
    ma = _khoa()
    r = _dat(ma, False, ad)
    assert r.status_code == 200, r.data
    assert q1('SELECT is_published FROM courses WHERE id=%s', (ma,))['is_published'] is False
    nk = q1("SELECT action, summary, detail FROM admin_audit WHERE target_type='course' AND target_id=%s "
            "ORDER BY id DESC LIMIT 1", (ma,))
    assert nk and nk['action'] == 'course.publish', nk
    ct = nk['detail'] if isinstance(nk['detail'], dict) else json.loads(nk['detail'])
    assert ct == {'cu': True, 'moi': False}, ct
    assert 'nháp' in nk['summary']
    # Gửi lại đúng giá trị đang có: không phải một lần đổi, không ghi thêm dòng nhật ký.
    dem = q1("SELECT count(*) AS n FROM admin_audit WHERE target_type='course' AND target_id=%s", (ma,))['n']
    assert _dat(ma, False, ad).status_code == 200
    assert q1("SELECT count(*) AS n FROM admin_audit WHERE target_type='course' AND target_id=%s",
              (ma,))['n'] == dem
    # Nhận đúng/sai và chuỗi true/false/1/0 (biểu mẫu cũ gửi chuỗi) — ép về BOOL THẬT;
    # chuỗi "false" không được lặng lẽ thành TRUE, chuỗi lạ và NULL bị từ chối.
    r = _goi(AdminCourseDetailView, 'put', {'is_published': '1'}, ai=ad, course_id=ma)
    assert r.status_code == 200, r.data
    assert q1('SELECT is_published FROM courses WHERE id=%s', (ma,))['is_published'] is True
    r = _goi(AdminCourseDetailView, 'put', {'is_published': 'false'}, ai=ad, course_id=ma)
    assert r.status_code == 200, r.data
    assert q1('SELECT is_published FROM courses WHERE id=%s', (ma,))['is_published'] is False
    for la in ('nháp', None, 'no'):
        r = _goi(AdminCourseDetailView, 'put', {'is_published': la}, ai=ad, course_id=ma)
        assert r.status_code == 400, (la, r.data)
    assert q1('SELECT is_published FROM courses WHERE id=%s', (ma,))['is_published'] is False
    # Tạo khoá kèm trạng thái: ghi đúng một lần (cột không lặp trong câu INSERT).
    from courseadmin.views import AdminCoursesView
    moi = 'kn_%s' % uuid.uuid4().hex[:8]
    r = _goi(AdminCoursesView, 'post', {'id': moi, 'title': 'KN mới', 'is_published': 'false'}, ai=ad)
    assert r.status_code == 200, r.data
    assert q1('SELECT is_published FROM courses WHERE id=%s', (moi,))['is_published'] is False


def test_hoc_vien_mat_khoa_nhap_ngay_nhan_su_van_xem():
    """Đệm đã NÓNG trước khi đổi: cổng phải tự quên, không chờ 60 giây."""
    from courses.truy_cap import quen_truy_cap, quyen_khoa
    from courses.views import CourseDetailView, CoursesEnrolledView, CoursesView
    from lessons.views import CourseContentView
    ad = _nguoi(ROLE_ADMIN)
    gv = _nguoi(ROLE_TEACHER)
    ma = _khoa()
    em = _lop_co_em(ma)
    quen_truy_cap(em.id)
    assert quyen_khoa(em).get(ma) == 'hoc'          # đệm nóng

    assert _dat(ma, False, ad).status_code == 200
    assert ma not in quyen_khoa(em), 'khoá nháp vẫn mở cho học viên — cổng không quên đệm'
    assert _goi(CourseContentView, 'get', ai=em, course_id=ma).status_code == 403
    ds = _goi(CoursesView, 'get', ai=em)
    assert ma not in {c['id'] for c in ds.data}, 'học viên vẫn thấy khoá nháp trong danh sách'
    assert _goi(CourseDetailView, 'get', ai=em, course_id=ma).status_code == 404
    gop = _goi(CoursesEnrolledView, 'get', ai=em).data
    assert ma not in {c['id'] for c in gop['courses']} | {c['id'] for c in gop['enrolled']}
    # Nhân sự: vẫn thấy, chỉ-xem.
    assert quyen_khoa(gv).get(ma) == 'xem'
    assert ma in {c['id'] for c in _goi(CoursesView, 'get', ai=gv).data}
    assert _goi(CourseDetailView, 'get', ai=gv, course_id=ma).status_code == 200

    assert _dat(ma, True, ad).status_code == 200
    assert quyen_khoa(em).get(ma) == 'hoc', 'mở lại khoá mà em vẫn chưa vào được'
    assert ma in {c['id'] for c in _goi(CoursesView, 'get', ai=em).data}


def test_lop_ca_ba_mon_chi_mat_dung_mon_nhap():
    """Lớp để trống môn = học cả ba môn HSA. Chuyển MỘT môn về nháp thì em mất đúng môn
    ấy (đệm của em cũng phải được quên — em không nằm trong lớp `course_id = môn`)."""
    from courses.truy_cap import BA_MON, quen_truy_cap, quyen_khoa
    ad = _nguoi(ROLE_ADMIN)
    em = _lop_co_em(None)
    quen_truy_cap(em.id)
    assert set(quyen_khoa(em)) >= set(BA_MON)
    assert _dat('hsa_science', False, ad).status_code == 200
    q = quyen_khoa(em)
    assert 'hsa_science' not in q and q.get('hsa_quantitative') == 'hoc' and q.get('hsa_verbal') == 'hoc', q
