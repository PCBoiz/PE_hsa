"""Phép kiểm cho khu `lessons/` — chấm ở MÁY CHỦ (31/08/2026).

Khu này trước nay không có tệp test nào, và đó chính là chỗ lỗ hổng nặng nhất
của cả sản phẩm nằm: đáp án đi xuống trình duyệt trước khi học viên trả lời, và
điểm là con số học viên tự khai.
"""
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q1
from lessons.views import CourseContentView

# `lessons.grading` nhập MUỘN, trong từng phép kiểm cần tới nó. Lý do: hai phép
# kiểm quan trọng nhất (đáp án có lộ không · chưa ghi danh có đọc được không)
# phải CHẠY ĐƯỢC trên mã CŨ để chứng minh chúng đỏ ở đó. Nhập ở đầu tệp thì cả
# tệp chết bằng `ModuleNotFoundError` — một màu đỏ không nói lên điều gì.

f = APIRequestFactory()
KHOA = 'hsa_quantitative'


def _goi(view, method, body=None, ai=None, **kw):
    req = (getattr(f, method)('/x', body, format='json') if body is not None
           else getattr(f, method)('/x'))
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


@pytest.fixture
def em(db):
    """Học viên ĐÃ ghi danh khoá — rollback tự dọn."""
    r = q1("INSERT INTO users (name, email, password, streak) "
           "VALUES ('HV Cham','hv_cham_tmp@example.com','x',0) RETURNING id")
    q1("INSERT INTO enrollments (user_id, course_id, progress, completed_lessons, "
       "time_spent, last_lesson, next_lesson) VALUES (%s,%s,0,0,'0h','','') "
       'RETURNING user_id', (r['id'], KHOA))
    return User.objects.get(id=r['id'])


@pytest.mark.django_db
def test_noi_dung_gui_xuong_KHONG_con_dap_an(em):
    """Đo 31/08/2026 trong trình duyệt thật: một request lấy 297 đáp án cả khoá.

    Mở DevTools tab Network là thấy đáp án — kể cả bài chưa mở khoá. Toàn bộ hệ
    đo lường năng lực của trung tâm mất giá trị chứng cứ.
    """
    for url in ('/x', '/x?lesson=1'):
        req = f.get(url)
        force_authenticate(req, user=em)
        kq = CourseContentView.as_view()(req, course_id=KHOA)
        assert kq.status_code == 200, kq.data
        than = str(kq.data)
        assert "'answer'" not in than and '"answer"' not in than, url
        assert "'explain'" not in than and '"explain"' not in than, url


@pytest.mark.django_db
def test_chua_ghi_danh_thi_khong_doc_duoc_noi_dung(db):
    """Đo được: một giảng viên chưa ghi danh tải được nguyên nội dung khoá."""
    r = q1("INSERT INTO users (name, email, password, streak) "
           "VALUES ('Nguoi La','nguoi_la_tmp@example.com','x',0) RETURNING id")
    req = f.get('/x')
    force_authenticate(req, user=User.objects.get(id=r['id']))
    assert CourseContentView.as_view()(req, course_id=KHOA).status_code == 403


@pytest.mark.django_db
def test_may_chu_cham_dung_va_chi_lo_dap_an_cua_cau_DA_TRA_LOI(em):
    from lessons.grading import dap_an
    from lessons.views import CheckAnswersView
    bang = dap_an(KHOA, 1).get('test') or {}
    assert bang, 'bài 1 phải có phần test để kiểm'
    ids = sorted(bang)
    dung_het = {i: bang[i]['answer'] for i in ids}

    kq = _goi(CheckAnswersView, 'post', {'phan': 'test', 'answers': dung_het},
              ai=em, course_id=KHOA, lesson_no=1)
    assert kq.status_code == 200, kq.data
    assert kq.data['correct'] == len(ids) and kq.data['scorePct'] == 100

    # sai hết
    kq2 = _goi(CheckAnswersView, 'post',
               {'phan': 'test', 'answers': {i: 'khong phai dap an' for i in ids}},
               ai=em, course_id=KHOA, lesson_no=1)
    assert kq2.data['correct'] == 0 and kq2.data['scorePct'] == 0

    # CỬA SAU: gửi rỗng để moi đáp án
    kq3 = _goi(CheckAnswersView, 'post', {'phan': 'test', 'answers': {}},
               ai=em, course_id=KHOA, lesson_no=1)
    assert kq3.data['results'] == {}, (
        'gửi answers rỗng mà moi được đáp án thì endpoint chấm chính là cửa sau '
        'thay cho lỗ vừa bịt: %s' % kq3.data['results'])
    assert kq3.data['total'] == len(ids), 'nhưng vẫn phải nói ra đề có mấy câu'

    # trả lời MỘT câu → chỉ lộ đáp án câu đó
    kq4 = _goi(CheckAnswersView, 'post',
               {'phan': 'test', 'answers': {ids[0]: 'x'}},
               ai=em, course_id=KHOA, lesson_no=1)
    assert set(kq4.data['results']) == {ids[0]}, kq4.data['results']


@pytest.mark.django_db
def test_bo_qua_han_va_dau_vao_hong(em):
    from lessons.views import CheckAnswersView
    for body, ma in (
        ({'phan': 'khong_co', 'answers': {}}, 400),
        ({'phan': 'test'}, 400),
        ({'phan': 'test', 'answers': 'khong phai dict'}, 400),
    ):
        assert _goi(CheckAnswersView, 'post', body, ai=em,
                    course_id=KHOA, lesson_no=1).status_code == ma, body
    # bài không tồn tại
    assert _goi(CheckAnswersView, 'post', {'phan': 'test', 'answers': {'a': 'b'}},
                ai=em, course_id=KHOA, lesson_no=99999).status_code == 404


def test_chuan_hoa_cau_tra_loi():
    """Chuẩn hoá PHẢI khoan dung với cách gõ, KHÔNG khoan dung với nội dung."""
    from lessons.grading import _chuan
    assert _chuan('  300.000Đ ') == _chuan('300.000đ')
    assert _chuan('a  b') == _chuan('a b')
    # dấu tiếng Việt và dấu phân cách nghìn LÀ một phần của đáp án
    assert _chuan('300.000đ') != _chuan('300000d')
    assert _chuan(None) == ''


def test_phan_tram_de_rong_tra_None():
    """Đề rỗng → None, KHÔNG phải 0 — cùng luật với `common.events.pct`."""
    from lessons.grading import phan_tram
    assert phan_tram(0, 0) is None
    assert phan_tram(2, 3) == 67
    assert phan_tram(0, 3) == 0


def test_bo_dap_an_cat_ca_hai_phan():
    from lessons.grading import bo_dap_an
    goc = {'test': {'questions': [{'id': 't1', 'answer': 'x', 'explain': 'y', 'question': 'q'}]},
           'drill': [{'id': 'd1', 'answer': 'z', 'question': 'q2'}],
           'theory': 'giữ nguyên'}
    ra = bo_dap_an(goc)
    assert 'answer' not in ra['test']['questions'][0]
    assert 'explain' not in ra['test']['questions'][0]
    assert 'answer' not in ra['drill'][0]
    assert ra['test']['questions'][0]['question'] == 'q', 'chỉ cắt đáp án, giữ đề bài'
    assert ra['theory'] == 'giữ nguyên'


@pytest.mark.django_db
def test_cham_bai_khong_ton_tai_tra_None_chu_khong_0_diem(db):
    from lessons.grading import cham
    ket_qua, dung, tong = cham(KHOA, 99999, 'test', {'a': 'b'})
    assert ket_qua is None and dung == 0 and tong == 0, (
        '"không tìm thấy đề" và "làm sai hết" là hai chuyện khác nhau')
