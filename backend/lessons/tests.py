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


# ── L5 · bảng `lessons` là bảng DÙNG CHUNG, học viên không được viết vào ─────

@pytest.mark.django_db
def test_khong_de_ra_duoc_bai_hoc_GIA_trong_bang_dung_chung(em):
    """Đo được: một dòng `"<b>BAI GIA MAO</b>"` với `sort_order 9999` do chính
    endpoint của học viên INSERT, và `SkillsView` đọc `lessons` không lọc theo
    người dùng nên dòng giả ấy hiện trong trang Kỹ năng của MỌI học viên.

    Đỏ trên mã cũ: bản cũ trả 200 và đẻ ra dòng đó.
    """
    from lessons.views import CompleteLessonView
    truoc = q1("SELECT COUNT(*) AS n FROM lessons WHERE course_id=%s", (KHOA,))['n']
    r = _goi(CompleteLessonView, 'post',
             {'courseId': KHOA, 'lessonTitle': '<b>BAI GIA MAO</b>',
              'module': 'Chủ đề giả', 'xpEarned': 50},
             ai=em, lesson_no=9999)
    # Kiểm BẤT BIẾN trước, kiểm mã trả về sau: thứ thật sự nguy hiểm là dòng
    # ghi vào bảng dùng chung, còn 404 chỉ là cách nói ra điều đó.
    gia = q1("SELECT id, sort_order FROM lessons WHERE title LIKE %s", ('%BAI GIA MAO%',))
    assert gia is None, 'học viên đẻ được dòng %r vào bảng lessons' % (gia,)
    sau = q1("SELECT COUNT(*) AS n FROM lessons WHERE course_id=%s", (KHOA,))['n']
    assert sau == truoc, 'endpoint của học viên đã ghi thêm %d dòng vào bảng dùng chung' % (sau - truoc)
    assert r.status_code == 404, 'bài không có trong khoá thì phải nói là không có'


@pytest.mark.django_db
def test_XP_lay_tu_NOI_DUNG_BAI_chu_khong_tu_than_request(em):
    """Bảng xếp hạng là thứ các em thi nhau thật.

    Đỏ trên mã cũ: bản cũ kẹp 0–500 rồi cộng thẳng con số client gửi, nên
    `{"xpEarned": 500}` cho 76 bài là 38.000 XP thay vì 3.800.
    """
    from lessons.views import CompleteLessonView
    r = _goi(CompleteLessonView, 'post',
             {'courseId': KHOA, 'xpEarned': 500}, ai=em, lesson_no=1)
    assert r.status_code == 200
    assert r.data['xpGained'] == 50, 'phải là xp_reward của bài, không phải số client khai'
    ghi = q1("SELECT xp_earned FROM lesson_progress lp JOIN lessons l ON l.id = lp.lesson_id "
             "WHERE lp.user_id=%s AND l.course_id=%s AND l.sort_order=1", (em.id, KHOA))
    assert ghi['xp_earned'] == 50


@pytest.mark.django_db
def test_tieu_de_trong_nhat_ky_lay_tu_CSDL_chu_khong_tu_client(em):
    """`learning_events.meta.title` hiện lại trong nhật ký học tập của em."""
    from lessons.views import CompleteLessonView
    _goi(CompleteLessonView, 'post',
         {'courseId': KHOA, 'lessonTitle': 'TIEU DE DO CLIENT BIA'}, ai=em, lesson_no=1)
    ev = q1("SELECT meta FROM learning_events WHERE user_id=%s AND kind='lesson' "
            "ORDER BY id DESC LIMIT 1", (em.id,))
    import json as _json
    meta = ev['meta'] if isinstance(ev['meta'], dict) else _json.loads(ev['meta'])
    assert meta.get('title') == 'Tỉ lệ & phần trăm', meta


# ── L5b · phòng luyện tốc độ cũng phải chấm ở MÁY CHỦ ───────────────────────

#: Bài tạm có phòng luyện 4 câu, đáp án biết trước. Không mượn bài thật: nội
#: dung bài thật đổi thì phép kiểm phải vẫn đúng.
NOI_DUNG_LUYEN = {
    'id': 'tmp_luyen', 'index': 900, 'title': 'Bài tạm luyện', 'xp_reward': 40,
    'test': {'questions': [{'id': 't1', 'question': '1+1?', 'answer': '2'}]},
    'theory': {'condensed': {'cards': [{'text': 'x'}]}},
    'drill': {'time_seconds': 60, 'questions': [
        {'id': 'd1', 'question': 'a', 'answer': 'A'},
        {'id': 'd2', 'question': 'b', 'answer': 'B'},
        {'id': 'd3', 'question': 'c', 'answer': 'C'},
        {'id': 'd4', 'question': 'd', 'answer': 'D'},
    ]},
}


@pytest.fixture
def bai_luyen(db):
    import json as _json
    from lessons.grading import quen_dap_an
    q1("INSERT INTO lessons (course_id, title, module, sort_order, content_json) "
       "VALUES (%s,'Bài tạm luyện','Chủ đề tạm',900,%s::jsonb) RETURNING id",
       (KHOA, _json.dumps(NOI_DUNG_LUYEN, ensure_ascii=False)))
    quen_dap_an(KHOA, 900)   # đệm 60 giây của phép kiểm trước không được lẫn sang
    yield 900
    quen_dap_an(KHOA, 900)


@pytest.mark.django_db
def test_phong_luyen_KHONG_nhan_ket_qua_tu_khai(em, bai_luyen):
    """Đỏ trên mã cũ: bản cũ nhận `correct`/`maxCombo` từ thân request rồi chỉ
    kẹp biên — mà `{"correct": 4, "maxCombo": 4}` là hợp lệ về biên, đáng 60 XP,
    và nó nuôi bản đồ năng lực (`KIND_DRILL` là một nguồn của competency)."""
    from lessons.views import CompleteLessonView
    r = _goi(CompleteLessonView, 'post',
             {'courseId': KHOA,
              'drill': {'correct': 4, 'total': 4, 'maxCombo': 4, 'answered': 4, 'seconds': 30}},
             ai=em, lesson_no=bai_luyen)
    assert r.status_code == 200
    # Kiểm BẤT BIẾN trước: thứ nguy hiểm là dòng năng lực dựng từ số tự khai.
    ev = q1("SELECT score, max_score FROM learning_events "
            "WHERE user_id=%s AND kind='drill'", (em.id,))
    assert ev is None, 'đã ghi một dòng năng lực %r dựng từ con số tự khai' % (ev,)
    assert r.data.get('xpDrill') == 0
    assert r.data['xpGained'] == 40, 'chỉ được cộng xp_reward của bài'


@pytest.mark.django_db
def test_phong_luyen_cham_tu_CAU_TRA_LOI_va_combo_theo_thu_tu_de(em, bai_luyen):
    """d1 đúng · d2 đúng · d3 SAI · d4 đúng → 3 đúng, combo dài nhất 2.

    Combo phải tính theo THỨ TỰ CÂU TRONG ĐỀ, không theo thứ tự dict gửi lên.
    """
    from lessons.views import CompleteLessonView
    r = _goi(CompleteLessonView, 'post',
             {'courseId': KHOA,
              'drill': {'seconds': 30,
                        'answers': {'d4': 'D', 'd1': 'A', 'd3': 'sai', 'd2': 'B'}}},
             ai=em, lesson_no=bai_luyen)
    assert r.data.get('drill') == {'correct': 3, 'total': 4, 'maxCombo': 2, 'answered': 4}, r.data.get('drill')
    assert r.data.get('xpDrill') == 3 * 10 + 2 * 5
    assert r.data['xpGained'] == 40 + 40
    ev = q1("SELECT score, max_score FROM learning_events "
            "WHERE user_id=%s AND kind='drill' ORDER BY id DESC LIMIT 1", (em.id,))
    assert (ev['score'], ev['max_score']) == (3, 4)


@pytest.mark.django_db
def test_cau_bo_trong_dut_chuoi_combo_va_tinh_la_sai(em, bai_luyen):
    """Hết giờ chưa kịp làm cũng là một kết quả trong bài luyện tính giờ."""
    from lessons.views import CompleteLessonView
    r = _goi(CompleteLessonView, 'post',
             {'courseId': KHOA, 'drill': {'seconds': 60, 'answers': {'d1': 'A', 'd4': 'D'}}},
             ai=em, lesson_no=bai_luyen)
    assert r.data.get('drill') == {'correct': 2, 'total': 4, 'maxCombo': 1, 'answered': 2}, r.data.get('drill')


@pytest.mark.django_db
def test_dap_an_PHONG_LUYEN_cung_khong_di_xuong_trinh_duyet(em, bai_luyen):
    """Phòng luyện là một nguồn của bản đồ năng lực, nên đáp án của nó cũng
    phải bí mật y như bài kiểm tra đầu vào."""
    from lessons.content import one_lesson
    data, _ = one_lesson(KHOA, bai_luyen)
    cau = data['drill']['questions']
    assert all('answer' not in c for c in cau), cau
    assert cau[0]['question'] == 'a', 'chỉ cắt đáp án, giữ đề bài'
