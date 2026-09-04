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

    # LẦN ĐẦU THẮNG (A12): gửi lại bộ SAI HẾT cho đúng những câu ấy không đổi
    # được gì. Một câu chỉ được trả lời một lần trong một lượt học — nếu không
    # thì `/check` là chỗ thử đáp án miễn phí.
    kq2 = _goi(CheckAnswersView, 'post',
               {'phan': 'test', 'answers': {i: 'khong phai dap an' for i in ids}},
               ai=em, course_id=KHOA, lesson_no=1)
    assert kq2.data['correct'] == len(ids), (
        'gửi lại đáp án khác cho câu đã trả lời mà điểm đổi được: %s' % kq2.data)

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
def _mot_cau_test(course_id, lesson_no):
    """Một `(id_câu, đáp_án_đúng)` của phần `test` — để phép kiểm vượt được cửa
    "hoàn thành phải có bằng chứng" (anh Sơn chốt 04/09/2026) mà không phải ghim
    id câu hỏi vào mã kiểm.

    Cửa ấy là HÀNH VI MỚI, không phải phép kiểm bị nới: ba phép kiểm dưới đây
    trước kia gọi `/complete` mà không trả lời gì, và nay đường đó trả 400. Mỗi
    cái vẫn đo đúng thứ nó vốn đo — nguồn của XP, nguồn của tiêu đề, và việc
    kết quả phòng luyện tự khai bị bỏ qua.
    """
    from lessons.grading import dap_an
    bang = dap_an(course_id, lesson_no).get('test') or {}
    for cid, v in bang.items():
        return cid, v.get('answer')
    return None, None


def test_XP_lay_tu_NOI_DUNG_BAI_chu_khong_tu_than_request(em):
    """Bảng xếp hạng là thứ các em thi nhau thật.

    Đỏ trên mã cũ: bản cũ kẹp 0–500 rồi cộng thẳng con số client gửi, nên
    `{"xpEarned": 500}` cho 76 bài là 38.000 XP thay vì 3.800.
    """
    from lessons.views import CompleteLessonView
    cid, dap = _mot_cau_test(KHOA, 1)
    r = _goi(CompleteLessonView, 'post',
             {'courseId': KHOA, 'xpEarned': 500,
              'answers': {cid: dap} if cid else {}}, ai=em, lesson_no=1)
    assert r.status_code == 200
    assert r.data['xpGained'] == 50, 'phải là xp_reward của bài, không phải số client khai'
    ghi = q1("SELECT xp_earned FROM lesson_progress lp JOIN lessons l ON l.id = lp.lesson_id "
             "WHERE lp.user_id=%s AND l.course_id=%s AND l.sort_order=1", (em.id, KHOA))
    assert ghi['xp_earned'] == 50


@pytest.mark.django_db
def test_tieu_de_trong_nhat_ky_lay_tu_CSDL_chu_khong_tu_client(em):
    """`learning_events.meta.title` hiện lại trong nhật ký học tập của em."""
    from lessons.views import CompleteLessonView
    cid, dap = _mot_cau_test(KHOA, 1)
    _goi(CompleteLessonView, 'post',
         {'courseId': KHOA, 'lessonTitle': 'TIEU DE DO CLIENT BIA',
          'answers': {cid: dap} if cid else {}}, ai=em, lesson_no=1)
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
              # Bằng chứng qua phần TEST, không qua drill: một câu drill thật sẽ
              # tạo ra đúng dòng năng lực mà phép kiểm này khẳng định KHÔNG có.
              'answers': {'t1': '2'},
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


# ── A12 · `/check` không còn là chỗ moi đáp án miễn phí ─────────────────────

@pytest.mark.django_db
def test_moi_dap_an_qua_check_thi_BO_DOAN_BUA_AY_chinh_la_bai_lam(em):
    """Đo được (audit chéo 31/08/2026): `/check` trả `answer` cho MỌI id có mặt
    trong `answers`, bất kể đúng sai. Nên hai request là xong:

        1. /check {"phan":"drill","answers":{"d1":"x", … ,"d8":"x"}} → trọn đáp án
        2. /complete với đúng bộ đáp án vừa lấy → 8/8, 120 XP, năng lực 8/8

    Nó làm rỗng ruột chính bản vá "chấm ở máy chủ" của cùng ngày hôm ấy.

    Nay câu trả lời bị GHI NHẬN ngay ở bước 1, lần đầu thắng — nên bộ đoán bừa
    CHÍNH LÀ bài làm, và bước 2 không cứu được.
    """
    from lessons.grading import dap_an
    from lessons.views import CheckAnswersView, CompleteLessonView
    bang = dap_an(KHOA, 1).get('test') or {}
    ids = sorted(bang)
    assert ids, 'bài 1 phải có phần test để kiểm'

    # Bước 1 — đoán bừa để moi đáp án.
    moi = _goi(CheckAnswersView, 'post',
               {'phan': 'test', 'answers': {i: 'doan bua' for i in ids}},
               ai=em, course_id=KHOA, lesson_no=1)
    assert moi.data['correct'] == 0

    # Bước 2 — nộp lại bằng đúng bộ đáp án vừa moi được.
    dung_het = {i: bang[i]['answer'] for i in ids}
    r = _goi(CompleteLessonView, 'post',
             {'courseId': KHOA, 'answers': dung_het}, ai=em, lesson_no=1)
    assert r.status_code == 200
    ghi = q1("SELECT quiz_score FROM lesson_progress lp JOIN lessons l ON l.id = lp.lesson_id "
             "WHERE lp.user_id=%s AND l.course_id=%s AND l.sort_order=1", (em.id, KHOA))
    assert ghi['quiz_score'] == 0, (
        'điểm ghi vào sổ phải là điểm của bộ ĐOÁN BỪA, không phải bộ moi được: %s' % ghi)


@pytest.mark.django_db
def test_moi_dap_an_PHONG_LUYEN_cung_khong_an_duoc_XP(em):
    """Cùng cửa, nhưng phòng luyện là nơi phần thưởng lớn hơn: 8 câu đúng +
    combo 8 = 120 XP, gấp 2,4 lần phần thưởng của cả bài học."""
    from lessons.grading import dap_an
    from lessons.views import CheckAnswersView, CompleteLessonView
    bang = dap_an(KHOA, 1).get('drill') or {}
    ids = sorted(bang)
    assert ids, 'bài 1 phải có phòng luyện để kiểm'

    moi = _goi(CheckAnswersView, 'post',
               {'phan': 'drill', 'answers': {i: 'doan bua' for i in ids}},
               ai=em, course_id=KHOA, lesson_no=1)
    assert moi.status_code == 200
    lo = [k for k, v in moi.data['results'].items() if 'answer' in v]
    assert lo == [], 'phòng luyện không được trả `answer`, chỉ cần đúng/sai: %s' % lo

    dung_het = {i: bang[i]['answer'] for i in ids}
    r = _goi(CompleteLessonView, 'post',
             {'courseId': KHOA, 'drill': {'answers': dung_het, 'seconds': 40}},
             ai=em, lesson_no=1)
    assert r.data.get('xpDrill') == 0, (
        'XP phòng luyện phải tính trên bộ ĐOÁN BỪA: %s' % r.data.get('drill'))
    assert (r.data.get('drill') or {}).get('correct') == 0


@pytest.mark.django_db
def test_hoan_thanh_xong_thi_XOA_phan_da_ghi_nhan(em):
    """Ôn lại bài phải bắt đầu từ giấy trắng, không kẹt với câu hôm trước."""
    from lessons.grading import dap_an, doc_ghi_nhan
    from lessons.views import CheckAnswersView, CompleteLessonView
    bang = dap_an(KHOA, 1).get('test') or {}
    ids = sorted(bang)
    _goi(CheckAnswersView, 'post', {'phan': 'test', 'answers': {ids[0]: 'x'}},
         ai=em, course_id=KHOA, lesson_no=1)
    lid = q1("SELECT id FROM lessons WHERE course_id=%s AND sort_order=1", (KHOA,))['id']
    assert doc_ghi_nhan(em.id, lid, 'test') != {}
    _goi(CompleteLessonView, 'post', {'courseId': KHOA, 'answers': {}},
         ai=em, lesson_no=1)
    assert doc_ghi_nhan(em.id, lid, 'test') == {}


# ── A14/A15 · khối `drill` cũng phải được kiểm lúc nhập ────────────────────

def _bai_mau(drill):
    return {'id': 'x', 'index': 1, 'title': 't',
            'test': {'questions': [{'id': 't1', 'question': 'q', 'answer': 'a', 'type': 'fill'}]},
            'theory': {'condensed': {'cards': [{'text': 'x'}]}},
            'drill': drill}


def test_khoi_drill_hop_le_thi_qua():
    from lessons.content import validate_lesson
    assert validate_lesson(_bai_mau(
        {'time_seconds': 60,
         'questions': [{'id': 'd1', 'question': 'q', 'answer': 'a', 'type': 'fill'}]})) == []


def test_sai_ten_khoa_thoi_luong_bi_chan():
    """Mẫu nhập giáo trình CHÍNH THỨC từng ghi `seconds` trong khi engine đọc
    `time_seconds`: bài nhập đúng theo mẫu sẽ có đồng hồ phòng luyện chạy mãi
    không hết giờ (`NaN <= 0` luôn sai)."""
    from lessons.content import validate_lesson
    loi = validate_lesson(_bai_mau(
        {'seconds': 60,
         'questions': [{'id': 'd1', 'question': 'q', 'answer': 'a', 'type': 'fill'}]}))
    assert any('time_seconds' in e for e in loi), loi


def test_cau_drill_thieu_id_hoac_trung_id_bi_chan():
    """Thiếu `id` thì `dap_an` lọc câu đó ra, và học viên thấy mọi câu hiện
    "Chưa chấm được câu này" — một câu an ủi nói dối."""
    from lessons.content import validate_lesson
    assert validate_lesson(_bai_mau(
        {'time_seconds': 60,
         'questions': [{'question': 'q', 'answer': 'a', 'type': 'fill'}]})) != []
    assert validate_lesson(_bai_mau(
        {'time_seconds': 60,
         'questions': [{'id': 'd1', 'question': 'q', 'answer': 'a', 'type': 'fill'},
                       {'id': 'd1', 'question': 'q2', 'answer': 'b', 'type': 'fill'}]})) != []


@pytest.mark.django_db
def test_bo_kiem_moi_KHONG_chan_bai_nao_dang_co(db):
    """Siết bộ kiểm mà chặn luôn nội dung đang chạy thì giảng viên sửa một chữ
    cũng bị từ chối. Đo trên chính 76 bài thật."""
    import json as _json

    from common.db import q as _q
    from lessons.content import validate_lesson
    hong = []
    for r in _q('SELECT course_id, sort_order, content_json FROM lessons '
                'WHERE content_json IS NOT NULL'):
        d = r['content_json']
        if isinstance(d, str):
            d = _json.loads(d)
        e = validate_lesson(d, path='%s#%s' % (r['course_id'], r['sort_order']))
        if e:
            hong.append(e[0])
    assert hong == [], hong[:5]


# ── Audit chéo 01/09/2026 · ba lỗ nặng của chính bản A12 ───────────────────

@pytest.mark.django_db
def test_check_KHONG_de_ra_dong_lesson_progress_thieu_course_id(em):
    """Trước A12, đường DUY NHẤT tạo dòng `lesson_progress` là `/complete`, và
    nó luôn điền `course_id`. Từ khi `/check` ghi nhận câu trả lời, đường này
    chèn TRƯỚC — để trống thì cột ấy ở NULL VĨNH VIỄN (nhánh `DO UPDATE` của
    `/complete` không đụng tới nó).

    Bảy chỗ đọc lọc theo `lp.course_id`, nặng nhất là câu tính lại
    `enrollments` ngay sau khi hoàn thành bài → tiến độ đứng ở 0%.
    """
    from lessons.grading import dap_an
    from lessons.views import CheckAnswersView
    ids = sorted(dap_an(KHOA, 1).get('test') or {})
    _goi(CheckAnswersView, 'post', {'phan': 'test', 'answers': {ids[0]: 'x'}},
         ai=em, course_id=KHOA, lesson_no=1)
    dong = q1("SELECT lp.course_id FROM lesson_progress lp JOIN lessons l ON l.id = lp.lesson_id "
              "WHERE lp.user_id=%s AND l.course_id=%s AND l.sort_order=1", (em.id, KHOA))
    assert dong and dong['course_id'] == KHOA, dong


@pytest.mark.django_db
def test_hoan_thanh_LAN_HAI_khong_ghi_de_diem_lan_dau(em):
    """Đường vòng hai agent cùng chỉ ra: `/check` trả đáp án cho câu đã trả lời,
    `/complete` XOÁ khoá "lần đầu thắng" để lần ôn sau bắt đầu từ giấy trắng.
    Hai thứ cộng lại: gửi bừa để moi đáp án → hoàn thành (0 điểm vào sổ) →
    hoàn thành lại bằng bộ vừa moi → 100 GHI ĐÈ số 0.

    Giữ điểm CAO NHẤT cũng không chặn được, vì 0 → 100 là đi LÊN.
    """
    from lessons.grading import dap_an
    from lessons.views import CheckAnswersView, CompleteLessonView
    bang = dap_an(KHOA, 1).get('test') or {}
    ids = sorted(bang)
    dung_het = {i: bang[i]['answer'] for i in ids}

    # Vòng 1 — đoán bừa để moi, rồi hoàn thành.
    _goi(CheckAnswersView, 'post', {'phan': 'test', 'answers': {i: 'bua' for i in ids}},
         ai=em, course_id=KHOA, lesson_no=1)
    _goi(CompleteLessonView, 'post', {'courseId': KHOA, 'answers': dung_het},
         ai=em, lesson_no=1)
    # Vòng 2 — nộp lại bằng bộ đáp án đã moi được.
    _goi(CompleteLessonView, 'post', {'courseId': KHOA, 'answers': dung_het},
         ai=em, lesson_no=1)

    lid = q1("SELECT id FROM lessons WHERE course_id=%s AND sort_order=1", (KHOA,))['id']
    ghi = q1("SELECT quiz_score FROM lesson_progress WHERE user_id=%s AND lesson_id=%s",
             (em.id, lid))
    assert ghi['quiz_score'] == 0, (
        'điểm vào sổ bị nâng lên %s bằng bộ đáp án đã moi' % ghi['quiz_score'])
    ev = q1("SELECT score FROM learning_events WHERE user_id=%s AND dedup_key=%s",
            (em.id, 'lesson:%s' % lid))
    assert ev and int(ev['score']) == 0, (
        'dòng năng lực bị nâng lên %s trong khi sổ điểm giữ 0' % (ev or {}).get('score'))


@pytest.mark.django_db
def test_bo_cau_tra_loi_khong_lo_bi_kep_bien(em):
    """`ghi_nhan` GỘP THÊM chứ không thay thế, nên không trần thì mỗi request
    nạp thêm tới 2,5 MB khoá rác vào ĐÚNG MỘT dòng. Vài chục lượt là mỗi lần
    chấm kéo cả trăm MB từ Neon về — một tài khoản đủ giết một worker."""
    from lessons.grading import MAX_CAU_TRA_LOI, MAX_DAI_TRA_LOI, kep_tra_loi
    to = {('k%d' % i): ('x' * 2000) for i in range(5000)}
    ra, cat = kep_tra_loi(to)
    assert cat is True
    assert len(ra) <= MAX_CAU_TRA_LOI, len(ra)
    assert all(len(v) <= MAX_DAI_TRA_LOI for v in ra.values())


# ── B13/B15 · phòng luyện: lượt ĐẦU vào sổ, và thân request chỉ là bản sao lưu ─

@pytest.mark.django_db
def test_phong_luyen_chi_LUOT_DAU_cong_XP_va_ghi_nang_luc(em, bai_luyen):
    """Anh Sơn chốt 01/09/2026, cùng luật với thi thử. Không có nó thì `reset`
    + `/check` là một máy dò đáp án: trả lời → xem đúng/sai → bấm Bắt đầu →
    thử khác, cho tới khi biết hết — rồi làm một lượt sạch lấy 120 XP và ô năng
    lực 8/8."""
    from lessons.views import CompleteLessonView
    dung = {'d1': 'A', 'd2': 'B', 'd3': 'C', 'd4': 'D'}
    mot = _goi(CompleteLessonView, 'post',
               {'courseId': KHOA, 'drill': {'answers': dung, 'seconds': 30}},
               ai=em, lesson_no=bai_luyen)
    assert mot.data.get('xpDrill') == 4 * 10 + 4 * 5, mot.data

    hai = _goi(CompleteLessonView, 'post',
               {'courseId': KHOA, 'drill': {'answers': dung, 'seconds': 30}},
               ai=em, lesson_no=bai_luyen)
    assert hai.data.get('xpDrill') == 0, 'lượt sau vẫn cộng XP: %s' % hai.data
    assert (hai.data.get('drill') or {}).get('correct') == 4, 'vẫn phải được chấm để luyện'
    n = q1("SELECT COUNT(*) AS n FROM learning_events "
           "WHERE user_id=%s AND kind='drill'", (em.id,))['n']
    assert n == 1, n


@pytest.mark.django_db
def test_bam_BAT_DAU_lai_CHOT_luot_dang_do_vao_so(em, bai_luyen):
    """Chốt ngay lúc bỏ dở thì lượt DÒ chính là lượt đầu. Không có chỗ này thì
    em cứ dò mà KHÔNG BAO GIỜ gọi `/complete`, rồi lượt sạch trở thành lượt đầu.
    """
    from lessons.views import CheckAnswersView
    # Lượt một: trả lời sai hết rồi bấm Bắt đầu lại.
    _goi(CheckAnswersView, 'post',
         {'phan': 'drill', 'answers': {'d1': 'sai', 'd2': 'sai'}},
         ai=em, course_id=KHOA, lesson_no=bai_luyen)
    _goi(CheckAnswersView, 'post', {'phan': 'drill', 'reset': True, 'answers': {}},
         ai=em, course_id=KHOA, lesson_no=bai_luyen)

    ev = q1("SELECT score, max_score FROM learning_events "
            "WHERE user_id=%s AND kind='drill'", (em.id,))
    assert ev is not None, 'lượt bỏ dở không được chốt — máy dò đáp án vẫn mở'
    assert int(ev['score']) == 0, ev


@pytest.mark.django_db
def test_tai_lai_trang_van_cham_duoc_phan_phong_luyen_da_ghi_nhan(em, bai_luyen):
    """Em làm đủ 4 câu qua `/check` rồi TẢI LẠI TRANG trước khi bấm Hoàn thành:
    thân gửi `"drill": null`. Máy chủ có sẵn bài làm — phải dùng nó."""
    from lessons.views import CheckAnswersView, CompleteLessonView
    for cid, val in (('d1', 'A'), ('d2', 'B'), ('d3', 'C'), ('d4', 'D')):
        _goi(CheckAnswersView, 'post', {'phan': 'drill', 'answers': {cid: val}},
             ai=em, course_id=KHOA, lesson_no=bai_luyen)
    r = _goi(CompleteLessonView, 'post', {'courseId': KHOA, 'drill': None},
             ai=em, lesson_no=bai_luyen)
    assert (r.data.get('drill') or {}).get('correct') == 4, (
        'bỏ qua phần đã ghi nhận: %s' % r.data.get('drill'))
    assert r.data.get('xpDrill') == 4 * 10 + 4 * 5


# ── HTML trong nội dung bài: cho phép in đậm, chặn mã (vá 04/09/2026) ───────
#
# Engine đổ HAI trường vào `innerHTML` mà KHÔNG escape, cố ý, vì người soạn cần
# in đậm và gõ công thức: `test.intro` (lesson_hsa.js:33) và
# `theory.*.cards[].body` (:401).
#
# Vô hại khi người soạn CHÍNH LÀ quản trị viên. Nhưng từ 04/09 có vai `Biên tập
# nội dung` — vai sinh ra để KHÔNG phải cấp quyền quản trị cho người gõ bài.
# Không lọc thì vai ấy leo thẳng lên quyền quản trị: nhét một thẻ có `onerror`
# vào bài, đợi quản trị viên mở xem thử. Mã chạy trên miền Vercel nơi cookie
# phiên sống, nên không cần đọc token — chỉ cần dùng nó.

def _bai(**doi):
    """Một bài hợp lệ tối thiểu; `doi` ghi đè để thử từng chỗ."""
    b = {
        'id': 'x1', 'index': 1, 'title': 'Bài thử',
        'test': {'intro': 'Làm nhanh 3 câu.',
                 'questions': [{'id': 't1', 'type': 'fill',
                                'question': '2+2?', 'answer': '4'}]},
        'theory': {'full': {'title': 'Lý thuyết',
                            'cards': [{'title': 'A', 'body': 'nội dung'}]}},
    }
    for k, v in doi.items():
        if k == 'intro':
            b['test']['intro'] = v
        elif k == 'body':
            b['theory']['full']['cards'][0]['body'] = v
        else:
            b[k] = v
    return b


def _loi_html(kq):
    return [e for e in kq if 'thẻ' in e]


def test_the_treo_ma_bi_chan_o_moi_truong():
    from lessons.content import validate_lesson
    for cho, bai in (('test.intro', _bai(intro='<img src=x onerror=alert(1)>')),
                     ('cards[].body', _bai(body='<img src=x onerror=alert(1)>'))):
        assert _loi_html(validate_lesson(bai)), 'lọt <img> ở ' + cho
    assert _loi_html(validate_lesson(_bai(intro='<script>fetch("/api/admin")</script>')))
    assert _loi_html(validate_lesson(_bai(body='<iframe src="x"></iframe>')))
    # `<a>` không nằm trong danh sách → chặn luôn cả `javascript:`, không cần
    # một luật riêng cho lược đồ liên kết.
    assert _loi_html(validate_lesson(_bai(body='<a href="javascript:alert(1)">x</a>')))


def test_the_duoc_phep_nhung_MANG_THUOC_TINH_van_bi_chan():
    """Cấm HẾT thuộc tính, không lọc từng cái. Danh sách đen luôn thiếu một dòng —
    `onerror`, `onload`, `onpointerover`, `style` với `expression()`…"""
    from lessons.content import validate_lesson
    assert _loi_html(validate_lesson(_bai(intro='<b onmouseover="alert(1)">x</b>')))
    assert _loi_html(validate_lesson(_bai(body='<code style="x">y</code>')))
    assert not _loi_html(validate_lesson(_bai(intro='<b>x</b>'))), 'thẻ sạch phải qua'


def test_dau_be_hon_trong_toan_hoc_KHONG_bi_chan():
    """`0 < a < 1` có THẬT trong `hsa_quantitative#8`.

    Theo chuẩn HTML, `<` chỉ mở thẻ khi LIỀN SAU là chữ cái hoặc `/`; có dấu
    cách thì nó là ký tự thường. Bộ lọc phải dùng đúng luật ấy.

    Đây không phải trường hợp lý thuyết: phép ĐO đầu tiên của tôi dùng regex
    `<\s*/?\s*([a-zA-Z]…)` và báo "76 bài có 1 thẻ <a>" — thật ra là chuỗi
    `0 < a < 1`. Chặn theo phép đo ấy là chặn oan nội dung toán học của cả khoá
    Định lượng.
    """
    from lessons.content import validate_lesson
    for chuoi in ('y = aˣ (a > 0, a ≠ 1). Nếu a > 1: đồng biến; 0 < a < 1: nghịch biến.',
                  'x < y < z', '3 < 5 và 5 > 3', 'nhiệt độ < 0 độ C'):
        assert not _loi_html(validate_lesson(_bai(body=chuoi))), 'chặn oan: ' + chuoi


def test_dau_be_hon_DINH_chu_cai_thi_PHAI_bi_chan():
    """Ngược lại của phép kiểm trên, và nó sửa một niềm tin SAI của chính nó.

    Phép kiểm này trước 04/09/2026 khẳng định `a<b là sai cú pháp nhưng 3 < 5
    thì không` phải ĐƯỢC ĐI QUA. Sai. Đo bằng bộ phân tích HTML thật, chuỗi ấy
    trong `<p>…</p>` dựng ra một phần tử `<b>` với 11 "thuộc tính", và **chỉ mỗi
    chữ `a` còn hiện ra trên màn hình** — phần còn lại bị nuốt vào trong thẻ.

    Tức bản cũ không "cho qua nội dung toán học", nó cho qua một nội dung SẼ BỊ
    HỎNG KHI HIỂN THỊ mà không ai được báo. Chặn là đúng, và thông báo lỗi phải
    chỉ đường: viết `&lt;` hoặc thêm dấu cách.

    Ranh giới đúng vẫn là luật HTML: `<` mở thẻ CHỈ KHI liền sau là chữ cái —
    nên `0 < a < 1` (có dấu cách) vẫn đi qua, xem phép kiểm ngay trên.
    """
    from lessons.content import validate_lesson
    for chuoi in ('a<b là sai cú pháp nhưng 3 < 5 thì không',
                  'nếu x<y thì...'):
        loi = _loi_html(validate_lesson(_bai(body=chuoi)))
        assert loi, 'lọt chuỗi sẽ bị nuốt khi hiển thị: ' + chuoi
        assert '&lt;' in loi[0], 'thông báo lỗi phải chỉ đường sửa: ' + loi[0]


def test_the_in_dam_va_ma_lenh_van_dung_duoc():
    """Đo trên 76 bài đang chạy: <strong> 160 lần, <code> 134, <b> 62.
    Bộ lọc mà chặn chúng là làm hỏng cả giáo trình."""
    from lessons.content import validate_lesson
    assert not _loi_html(validate_lesson(_bai(
        intro='Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong>.')))
    assert not _loi_html(validate_lesson(_bai(
        body='Giảm p%: <code>× (1 - p/100)</code> · <b>giá trị gốc</b>')))


# ── PHÚT PHÒNG LUYỆN: con số CLIENT KHAI nằm trong xô của MÁY (vá 04/09/2026) ──
#
# `_cham_drill` nhận `drill.seconds` từ thân request, đổi ra phút, rồi ghi vào
# `learning_events.minutes` với `source='system'`. Mà `stats/gradebook.py` tách
# hai xô `minutes` / `selfMinutes` ĐÚNG THEO cột `source` ấy — toàn bộ ý nghĩa
# của phép tách là "cái này máy đo, cái kia học viên tự khai".
#
# Trần cũ `min(120, …)` là 120 PHÚT cho một bài luyện 75 GIÂY.

def test_phut_phong_luyen_kep_ve_tran_dong_ho_cua_bai(temp_user, db):
    """Khai 6 tiếng cho một bài luyện 75 giây thì chỉ được ghi 1 phút."""
    from lessons.grading import gioi_han_giay_drill, id_bai
    from lessons.views import _cham_drill

    course_id, lesson_no = 'hsa_quantitative', 1
    tran = gioi_han_giay_drill(course_id, lesson_no)
    assert tran, 'bài mẫu phải có time_seconds — nếu không, phép kiểm không kiểm gì'

    lesson_id = id_bai(course_id, lesson_no)
    ket = _cham_drill({'answers': {'q1': 'x'}, 'seconds': 21600},
                      course_id, lesson_no, temp_user, lesson_id)
    assert ket is not None
    toi_da = max(0, min(120, round(tran / 60))) or None
    assert ket['phut'] == toi_da, (
        'khai 21600 giây (6 tiếng) cho bài luyện %d giây mà ghi %r phút'
        % (tran, ket['phut']))


def test_phut_phong_luyen_van_giu_con_so_that(temp_user, db):
    """Hàng rào không được làm mất con số ĐÚNG — chặn oan cũng là hỏng."""
    from lessons.grading import id_bai
    from lessons.views import _cham_drill

    course_id, lesson_no = 'hsa_quantitative', 1
    lesson_id = id_bai(course_id, lesson_no)
    ket = _cham_drill({'answers': {'q1': 'x'}, 'seconds': 40},
                      course_id, lesson_no, temp_user, lesson_id)
    assert ket is not None
    assert ket['phut'] == 1, ket['phut']    # round(40/60) = 1


def test_tran_dong_ho_doc_dung_tu_giao_trinh(db):
    """`gioi_han_giay_drill` phải đọc ĐÚNG `time_seconds`, và nhớ cả ca KHÔNG có.

    Ca "không có trần" phải được đệm riêng: nếu nó rơi vào nhánh đệm-trượt thì
    mỗi lần chấm một bài không có phòng luyện lại tra CSDL thêm một lượt, ngay
    trong đường `/complete`.
    """
    from common.db import q1
    from lessons.grading import gioi_han_giay_drill

    that = q1("SELECT (content_json->'drill'->>'time_seconds')::int AS ts "
              "FROM lessons WHERE course_id='hsa_quantitative' AND sort_order=1")
    assert gioi_han_giay_drill('hsa_quantitative', 1) == that['ts']
    # Bài không tồn tại → None, và gọi lại vẫn None (đi qua đệm `-1`).
    assert gioi_han_giay_drill('khong_co_khoa_nay', 999) is None
    assert gioi_han_giay_drill('khong_co_khoa_nay', 999) is None


# ── THẺ KHÔNG ĐÓNG `>`: bộ lọc phải đọc như TRÌNH DUYỆT SẼ ĐỌC SAU KHI NỐI ──
#
# Bộ lọc dựng sáng 04/09 bắt buộc thẻ phải có `>` đóng, nên một thẻ mở ở CUỐI
# chuỗi thì `findall` trả rỗng và nó báo "không có lỗi". Mà chỗ hiển thị CUNG
# CẤP LUÔN dấu `>` còn thiếu — `lesson_hsa.js:417` là `'…<p>' + c.body + '</p>'`,
# và cái `>` của `</p>` đóng nốt thẻ của kẻ tấn công.
#
# Vai `Biên tập nội dung` nhét payload vào `theory.cards[].body` → bất kỳ ai mở
# bước Lý thuyết, KỂ CẢ QUẢN TRỊ VIÊN, chạy mã ấy trên phiên của chính họ.

_KHONG_DONG = [
    '<img src=x onerror=alert(1)//',
    'Câu dẫn bình thường <img src=x onerror=alert(1)//',
    '<svg/onload=alert(1)',
    '</p><script',
    '<iframe src=//x',
]


def test_the_KHONG_DONG_ngoac_van_bi_chan():
    """Dấu `>` không được là điều kiện để bộ lọc nhìn thấy một thẻ."""
    from lessons.content import loi_html, validate_lesson
    for xau in _KHONG_DONG:
        assert loi_html(xau, 'body'), 'lọt %r' % xau
        assert _loi_html(validate_lesson(_bai(body=xau))), 'lọt qua validate_lesson: %r' % xau
        assert _loi_html(validate_lesson(_bai(intro=xau))), 'lọt ở intro: %r' % xau


def test_payload_khong_dong_THUC_SU_dung_ra_the_img_chay_duoc():
    """Chứng minh vì sao phép kiểm trên đáng có — bằng một bộ PHÂN TÍCH HTML thật.

    Không có bước này thì "thẻ không đóng" nghe như chuyện hình thức. Nó không
    hình thức: dấu `>` còn thiếu do CHÍNH TRANG cung cấp. Dựng lại đúng chuỗi mà
    `lesson_hsa.js:417` phát ra rồi cho `html.parser` (thư viện chuẩn, cùng luật
    với trình duyệt ở điểm này) đọc — nó dựng ra một phần tử `<img>` MANG
    `onerror`, tức một chỗ treo mã thật.
    """
    from html.parser import HTMLParser

    class Doc(HTMLParser):
        def __init__(self):
            super().__init__()
            self.the = []

        def handle_starttag(self, tag, attrs):
            self.the.append((tag, dict(attrs)))

    body = '<img src=x onerror=alert(1)//'
    # ĐÚNG chuỗi lesson_hsa.js phát ra: `c.body` đổ thô, ngay sau là `</p>`.
    html = '<div class="hsa-card-body"><h4>T</h4><p>' + body + '</p></div>'
    d = Doc()
    d.feed(html)

    img = [a for t, a in d.the if t == 'img']
    assert img, 'không dựng ra <img> — nếu vậy thì lỗ này không có thật, xoá phép kiểm đi'
    assert 'onerror' in img[0], img[0]
    # `//` biến phần thừa `</p` thành chú thích, nên phần THỰC THI là `alert(1)`.
    assert img[0]['onerror'].split('//')[0].strip() == 'alert(1)', img[0]['onerror']

    # Và bộ lọc phải chặn nó. Ba khẳng định trên là lý do; dòng này là hàng rào.
    from lessons.content import loi_html
    assert loi_html(body, 'body'), 'bộ lọc để lọt payload vừa chứng minh là chạy được'


def test_luot_phong_luyen_bo_do_van_co_CHU_DE(temp_user, db):
    """Lượt bỏ dở phải vào sổ KÈM chủ đề, nếu không nó vô hình với bản đồ năng lực.

    `stats/competency.py` khoá theo `(course_id, topic)`. Đường `/check` gọi
    `_chot_luot_drill` mà không truyền `topic` — nên trước bản vá, đúng cái lượt
    dò đáp án mà cơ chế này sinh ra để bắt lại được ghi với `topic = NULL` và
    không đếm vào đâu cả.
    """
    from common.db import q1
    from lessons.grading import ghi_nhan, id_bai
    from lessons.views import _chot_luot_drill, _tim_bai

    course_id, lesson_no = 'hsa_quantitative', 1
    lesson_id = id_bai(course_id, lesson_no)
    chu_de_that = _tim_bai(course_id, lesson_no)[1]
    assert chu_de_that, 'bài mẫu phải có module — nếu không, phép kiểm không kiểm gì'

    # Học viên trả lời một câu rồi bấm "Bắt đầu" lại.
    ghi_nhan(temp_user, lesson_id, 'drill', {'q1': 'x'})
    _chot_luot_drill(temp_user, lesson_id, course_id, lesson_no)

    dong = q1('SELECT topic, kind FROM learning_events '
              'WHERE user_id=%s AND dedup_key=%s', (temp_user, 'drill:%s' % lesson_id))
    assert dong, 'lượt bỏ dở phải vào sổ'
    assert dong['topic'] == chu_de_that, dong


# ── HOÀN THÀNH PHẢI CÓ BẰNG CHỨNG (anh Sơn chốt 04/09/2026) ──────────────────
#
# Trước bản vá, `POST …/complete` KHÔNG đòi gì: gọi thẳng 76 lần là được 76 bài
# "đã hoàn thành", 3.800 XP và chuỗi ngày học, không trả lời một câu nào. Mọi
# hàng rào chống gian lận phía trên canh chuyện TRẢ LỜI THẾ NÀO; không cái nào
# canh chuyện CÓ TRẢ LỜI KHÔNG.

#: `course_id` đi trong THÂN request, không trong đường dẫn — xem `lessons/urls.py`.
_COMPLETE = '/api/lessons/%d/complete'


def test_hoan_thanh_bai_CO_cau_hoi_ma_chua_lam_gi_bi_chan(auth_api, temp_user, db):
    from common.db import q1

    r = auth_api.post(_COMPLETE % 1, {'courseId': 'hsa_quantitative'}, format='json')
    assert r.status_code == 400, r.status_code
    assert 'ít nhất một câu' in r.json()['error'], r.json()

    # VÀ KHÔNG GHI GÌ: chặn rồi thì không được để lại dấu vết nào.
    assert not q1("SELECT 1 FROM lesson_progress p JOIN lessons l ON l.id=p.lesson_id "
                  "WHERE p.user_id=%s AND l.course_id='hsa_quantitative' "
                  "AND l.sort_order=1 AND p.status='completed'", (temp_user,))


def test_lam_mot_cau_roi_thi_hoan_thanh_duoc_va_ghi_la_MAY_DO(auth_api, temp_user, db):
    """Hàng rào không được chặn việc thật — làm một câu là đủ."""
    from common.db import q1
    from lessons.grading import ghi_nhan, id_bai

    lesson_id = id_bai('hsa_quantitative', 1)
    ghi_nhan(temp_user, lesson_id, 'drill', {'q1': 'x'})

    r = auth_api.post(_COMPLETE % 1, {'courseId': 'hsa_quantitative'}, format='json')
    assert r.status_code == 200, r.json()

    sk = q1('SELECT source FROM learning_events WHERE user_id=%s AND dedup_key=%s',
            (temp_user, 'lesson:%s' % lesson_id))
    assert sk and sk['source'] == 'system', sk


def test_bai_da_xong_TU_TRUOC_duoc_mien_cua_chan(auth_api, temp_user, db):
    """Bài đã hoàn thành từ trước — kể cả trước bản vá này — gọi lại KHÔNG bị chặn.

    Đường này vốn nhận cú bấm lặp (F5 trên hộp chúc mừng), và chặn ở đó là phạt
    người dùng vì một lỗ hổng cũ của hệ thống. Cửa miễn là `existed`.
    """
    from common.db import q1, x
    from lessons.grading import id_bai

    lesson_id = id_bai('hsa_quantitative', 2)
    x("""INSERT INTO lesson_progress (user_id, lesson_id, course_id, status, completed_at)
         VALUES (%s, %s, 'hsa_quantitative', 'completed', NOW())
         ON CONFLICT (user_id, lesson_id) DO UPDATE SET status='completed'""",
      (temp_user, lesson_id))

    # Không trả lời câu nào, nhưng đã completed từ trước → cho qua.
    r = auth_api.post(_COMPLETE % 2, {'courseId': 'hsa_quantitative'}, format='json')
    assert r.status_code == 200, r.json()

    # Và ghi là TỰ KHAI, vì lần gọi này không mang bằng chứng nào.
    sk = q1('SELECT source FROM learning_events WHERE user_id=%s AND dedup_key=%s',
            (temp_user, 'lesson:%s' % lesson_id))
    assert sk and sk['source'] == 'self', sk
