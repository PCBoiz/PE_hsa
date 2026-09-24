"""Thứ tự bài KHÔNG được trùng trong một khoá (24/09/2026).

Đo trên nhánh dev (bản sao production 24/09): khoá `hsa_quantitative` có HAI bài
`sort_order 1` — bài gốc "Tỉ lệ & phần trăm" và bài "Chương 1: Xác suất thống kê" do
Biên tập nội dung của TopHSA thêm lúc 08:30 ngày 23/09 (nhật ký `lesson.create`). Bộ
soạn tính vị trí = lớn nhất + 1 TỪ DANH SÁCH ĐANG NẠP — danh sách rỗng (chưa nạp xong,
hay nạp hỏng) thì gửi 1, và máy chủ nhận mù.

Hậu quả: "bài số 1" trỏ HAI dòng. Đường đọc nội dung lọc bài có nội dung nên em vẫn
thấy đúng bài, nhưng `_tim_bai`/`id_bai` lấy `LIMIT 1` không thứ tự — hoàn thành bài 1
có thể ghi tiến độ, XP, năng lực sang bài RỖNG. Đi qua VIEW THẬT; CSDL cuộn lại.
"""
import uuid

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q1

f = APIRequestFactory()
pytestmark = pytest.mark.django_db
KHOA = 'hsa_quantitative'


def _bien_tap():
    r = q1("INSERT INTO users (name, email, password, role, streak) VALUES "
           "('BT thu tu', %s, 'x', 'Biên tập nội dung', 0) RETURNING id",
           ('tt_%s@example.com' % uuid.uuid4().hex[:10],))
    return User.objects.get(id=r['id'])


def _goi(view, method, body, ai, **kw):
    req = getattr(f, method)('/x', body, format='json')
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _lon_nhat():
    return q1('SELECT COALESCE(MAX(sort_order), 0) AS m FROM lessons WHERE course_id=%s', (KHOA,))['m']


def test_them_bai_khong_gui_vi_tri_thi_xep_cuoi():
    from courseadmin.views import AdminLessonsView
    truoc = _lon_nhat()
    ten = 'Bài cuối %s' % uuid.uuid4().hex[:6]
    r = _goi(AdminLessonsView, 'post', {'course_id': KHOA, 'title': ten}, _bien_tap())
    assert r.status_code in (200, 201), r.data
    so = q1('SELECT sort_order FROM lessons WHERE course_id=%s AND title=%s', (KHOA, ten))['sort_order']
    assert so == truoc + 1, 'bài mới phải xếp CUỐI (%s), không phải %s' % (truoc + 1, so)


def test_them_bai_vao_vi_tri_da_co_bai_bi_tu_choi():
    from courseadmin.views import AdminLessonsView
    ten = 'Bài trùng %s' % uuid.uuid4().hex[:6]
    r = _goi(AdminLessonsView, 'post', {'course_id': KHOA, 'title': ten, 'sort_order': 1}, _bien_tap())
    assert r.status_code == 409, r.data
    assert 'Vị trí 1 đã có bài' in r.data['error'], r.data
    assert not q1('SELECT 1 AS c FROM lessons WHERE course_id=%s AND title=%s', (KHOA, ten))


def test_doi_vi_tri_bai_sang_vi_tri_da_co_bai_bi_tu_choi():
    from courseadmin.views import AdminLessonDetailView
    bai = q1("INSERT INTO lessons (course_id, title, module, sort_order) VALUES (%s, 'Bài tạm', 'Tạm', %s) "
             'RETURNING id', (KHOA, _lon_nhat() + 1))['id']
    r = _goi(AdminLessonDetailView, 'put', {'sort_order': 1}, _bien_tap(), lesson_id=bai)
    assert r.status_code == 409, r.data
    # Giữ nguyên vị trí của CHÍNH nó thì không phải trùng.
    so = q1('SELECT sort_order FROM lessons WHERE id=%s', (bai,))['sort_order']
    r = _goi(AdminLessonDetailView, 'put', {'sort_order': so, 'title': 'Bài tạm 2'}, _bien_tap(), lesson_id=bai)
    assert r.status_code == 200, r.data


def test_bai_trung_vi_tri_thi_tra_bai_CO_NOI_DUNG():
    """Dữ liệu đã trùng (như production 23/09): mọi đường tra "bài số N" phải chọn
    CÙNG một bài — bài có nội dung, là bài em đang thấy — không chọn ngẫu nhiên."""
    from lessons.grading import id_bai, quen_dap_an
    from lessons.views import _tim_bai
    goc = q1('SELECT id FROM lessons WHERE course_id=%s AND sort_order=1 AND content_json IS NOT NULL '
             'ORDER BY id LIMIT 1', (KHOA,))['id']
    # Dòng rỗng cùng vị trí, id NHỎ hơn mọi dòng thật để "LIMIT 1 không thứ tự" dễ trúng nó.
    q1("INSERT INTO lessons (id, course_id, title, module, sort_order) "
       "VALUES (-424242, %s, 'Rỗng trùng vị trí', '', 1) RETURNING id", (KHOA,))
    quen_dap_an(KHOA, 1)
    assert _tim_bai(KHOA, 1)[0] == goc
    assert id_bai(KHOA, 1) == goc
