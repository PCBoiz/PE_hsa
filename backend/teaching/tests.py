"""Phép kiểm cho khu `teaching/` — bắt đầu bằng giao bài & chấm tay (ERP §5).

VÌ SAO TỆP NÀY RA ĐỜI MUỘN. Cả khối ERP — lớp, buổi học, điểm danh, đợt, báo
cáo phụ huynh, bảng điều khiển trung tâm, và giờ là chấm bài — được viết mà
`teaching/` KHÔNG có lấy một phép kiểm nào trong bộ chạy được. Từng đường đều đã
kiểm bằng kịch bản rời chạy qua view thật, nhưng kịch bản rời nằm ngoài repo:
lần chạy sau không ai chạy lại, và CI không biết nó tồn tại. Tệp này biến những
phép kiểm ấy thành thứ chạy lại được.

Bộ này chạy trên CSDL THẬT rồi cuộn lại (xem conftest.py), nên mọi thứ tạo ra ở
đây phải tạo bằng SQL trong test — không có bản ghi cố định nào để dựa vào.
"""
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.clock import local_now
from common.db import q, q1
from common.permissions import ROLE_STUDENT, ROLE_TEACHER
from teaching.assignments import (AssignmentDetailView, AssignmentGradingView,
                                  ClassAssignmentsView, MyAssignmentsView)

f = APIRequestFactory()


def _goi(view, method, body=None, ai=None, url='/x', **kw):
    req = (getattr(f, method)(url, body, format='json') if body is not None
           else getattr(f, method)(url))
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(ten, vai):
    row = q1('INSERT INTO users (name, email, password, role, streak) '
             'VALUES (%s, %s, %s, %s, 0) RETURNING id',
             (ten, '%s_tmp@example.com' % ten.replace(' ', '_'), 'x', vai))
    return User.objects.get(id=row['id'])


@pytest.fixture
def lop(db):
    """Một lớp có giảng viên phụ trách và hai học viên đang học."""
    gv = _nguoi('GV Kiem Tra', ROLE_TEACHER)
    hv = [_nguoi('HV Mot', ROLE_STUDENT), _nguoi('HV Hai', ROLE_STUDENT)]
    c = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
           "VALUES ('Lop kiem tra','hsa_quantitative',%s,'active') RETURNING id", (gv.id,))
    for u in hv:
        q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s) '
           'RETURNING id', (c['id'], u.id, local_now()))
    return {'id': c['id'], 'gv': gv, 'hv': hv}


def _tao_bai(lop, **kw):
    body = {'title': 'Bai luan 1', 'topic': 'Số học', 'max_score': 10, 'status': 'open'}
    body.update(kw)
    kq = _goi(ClassAssignmentsView, 'post', body, ai=lop['gv'], class_id=lop['id'])
    assert kq.status_code == 201, kq.data
    return kq.data['id']


# ── Đầu vào hỏng ────────────────────────────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.parametrize('body', [
    {'description': 'khong co tieu de'},
    {'title': 'a', 'max_score': -1},
    {'title': 'a', 'max_score': 'abc'},
    {'title': 'a', 'status': 'khong_co_trang_thai_nay'},
    {'title': 'a', 'due_at': 'hom qua'},
    {'title': 'a', 'course_id': 'khoa_khong_ton_tai'},
])
def test_tao_bai_dau_vao_hong_tra_400(lop, body):
    assert _goi(ClassAssignmentsView, 'post', body, ai=lop['gv'],
                class_id=lop['id']).status_code == 400


@pytest.mark.django_db
def test_truong_none_thanh_null_chu_khong_thanh_chuoi_None(lop):
    """`str(None)` ra chuỗi "None" — truthy, và đi thẳng vào CSDL.

    Đã trả giá cho đúng lỗi này ở `terms.py` và `views.py` ngày 31/08/2026. Phép
    kiểm ở đây tồn tại để nó không quay lại lần thứ ba.
    """
    aid = _tao_bai(lop, topic=None, description=None)
    row = q1('SELECT topic, description FROM assignments WHERE id=%s', (aid,))
    assert row['topic'] is None
    assert row['description'] is None


# ── Phân quyền ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_hoc_vien_khong_tao_duoc_bai(lop):
    assert _goi(ClassAssignmentsView, 'post', {'title': 'a'}, ai=lop['hv'][0],
                class_id=lop['id']).status_code == 403


@pytest.mark.django_db
def test_lop_khong_phu_trach_tra_404_chu_khong_403(lop):
    """404 chứ không 403: 403 là tự thú nhận "lớp đó có tồn tại"."""
    khac = q1("INSERT INTO classes (name, course_id, status) "
              "VALUES ('Lop nguoi khac','hsa_quantitative','active') RETURNING id")
    assert _goi(ClassAssignmentsView, 'get', ai=lop['gv'],
                class_id=khac['id']).status_code == 404


@pytest.mark.django_db
def test_hoc_vien_khong_thay_bai_dang_soan(lop):
    _tao_bai(lop, title='Bai dang soan', status='draft')
    _tao_bai(lop, title='Bai da mo', status='open')
    ds = _goi(MyAssignmentsView, 'get', ai=lop['hv'][0]).data['assignments']
    assert [a['title'] for a in ds] == ['Bai da mo']


# ── Chấm điểm ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.parametrize('grades', [
    [{'user_id': 0, 'score': 11}],       # vượt thang
    [{'user_id': 0, 'score': -1}],       # âm
    [{'user_id': 0, 'score': 'gioi'}],   # không phải số
    [],                                   # rỗng
])
def test_cham_diem_dau_vao_hong_tra_400(lop, grades):
    aid = _tao_bai(lop)
    for g in grades:
        g['user_id'] = lop['hv'][0].id
    assert _goi(AssignmentGradingView, 'post', {'grades': grades}, ai=lop['gv'],
                assignment_id=aid).status_code == 400


@pytest.mark.django_db
def test_toan_nguoi_ngoai_lop_tra_400_chu_khong_im_lang_200(lop):
    """Gửi toàn id lạ mà trả 200 là nói dối: không có gì được lưu cả."""
    aid = _tao_bai(lop)
    assert _goi(AssignmentGradingView, 'post', {'grades': [{'user_id': 999999, 'score': 5}]},
                ai=lop['gv'], assignment_id=aid).status_code == 400


@pytest.mark.django_db
def test_user_id_trung_trong_cung_me_giu_dong_cuoi(lop):
    """Postgres ném "ON CONFLICT DO UPDATE cannot affect row a second time".

    Không gộp trùng thì một danh sách có id lặp thành lỗi 500 thay vì được ghi.
    Cùng cái bẫy đã gặp ở đường lưu điểm danh.
    """
    aid = _tao_bai(lop)
    kq = _goi(AssignmentGradingView, 'post', {'grades': [
        {'user_id': lop['hv'][0].id, 'score': 3},
        {'user_id': lop['hv'][0].id, 'score': 8, 'feedback': 'ban sau'},
        {'user_id': 999999, 'score': 9},
    ]}, ai=lop['gv'], assignment_id=aid)
    assert kq.status_code == 200, kq.data
    assert kq.data['graded'] == 1
    assert kq.data['skipped'] == [999999]
    row = q1('SELECT score, feedback FROM submissions WHERE assignment_id=%s AND user_id=%s',
             (aid, lop['hv'][0].id))
    assert float(row['score']) == 8
    assert row['feedback'] == 'ban sau'


@pytest.mark.django_db
def test_cham_xong_de_su_kien_hoc_tap(lop):
    """Điểm tự luận vào bản đồ năng lực qua `learning_events`, không qua luật riêng."""
    aid = _tao_bai(lop, topic='Số học')
    _goi(AssignmentGradingView, 'post',
         {'grades': [{'user_id': lop['hv'][0].id, 'score': 8}]},
         ai=lop['gv'], assignment_id=aid)
    sk = q1('SELECT kind, topic, score, max_score, minutes FROM learning_events '
            'WHERE ref_type=%s AND ref_id=%s', ('assignment', str(aid)))
    assert sk['kind'] == 'assignment'
    assert sk['topic'] == 'Số học'
    assert float(sk['score']) == 8
    # `minutes` CỐ Ý để NULL: không ai đo được thời gian em ngồi viết bài tự
    # luận, và bịa một con số sẽ trộn thẳng vào chỉ tiêu học tuần.
    assert sk['minutes'] is None


@pytest.mark.django_db
def test_doi_thang_diem_sau_khi_cham_phai_canh_bao(lop):
    aid = _tao_bai(lop, max_score=10)
    _goi(AssignmentGradingView, 'post', {'grades': [{'user_id': lop['hv'][0].id, 'score': 8}]},
         ai=lop['gv'], assignment_id=aid)
    kq = _goi(AssignmentDetailView, 'patch', {'max_score': 100}, ai=lop['gv'],
              assignment_id=aid)
    assert kq.status_code == 200
    assert kq.data.get('warning'), 'đổi thang sau khi chấm mà im lặng là đổi ý nghĩa mọi điểm cũ'


# ── Phía học viên ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_nop_lai_xoa_diem_cua_chinh_minh_va_chi_cua_minh(lop):
    """Lỗi thật, tự viết ra rồi tự bắt được ngày 31/08/2026.

    Bản đầu gọi ``forget_events('assignment', aid)`` — dạng khoá xoá MỌI sự kiện
    trỏ về bài tập này, tức một em nộp lại thổi bay điểm đã chấm của cả lớp.
    """
    aid = _tao_bai(lop, status='open')
    a, b = lop['hv']
    _goi(MyAssignmentsView, 'post', {'assignment_id': aid, 'content': 'ban dau'}, ai=a)
    _goi(AssignmentGradingView, 'post', {'grades': [
        {'user_id': a.id, 'score': 5}, {'user_id': b.id, 'score': 9},
    ]}, ai=lop['gv'], assignment_id=aid)

    kq = _goi(MyAssignmentsView, 'post', {'assignment_id': aid, 'content': 'ban sua'}, ai=a)
    assert kq.status_code == 200

    cua_a = q1('SELECT score, graded_at FROM submissions WHERE assignment_id=%s AND user_id=%s',
               (aid, a.id))
    cua_b = q1('SELECT score FROM submissions WHERE assignment_id=%s AND user_id=%s',
               (aid, b.id))
    assert cua_a['score'] is None and cua_a['graded_at'] is None
    assert float(cua_b['score']) == 9, 'điểm của bạn cùng lớp KHÔNG được đụng tới'

    con = q('SELECT user_id FROM learning_events WHERE ref_type=%s AND ref_id=%s',
            ('assignment', str(aid)))
    assert [r['user_id'] for r in con] == [b.id]


@pytest.mark.django_db
def test_khong_nop_duoc_vao_bai_dang_soan_hoac_da_dong(lop):
    for tt in ('draft', 'closed'):
        aid = _tao_bai(lop, title='Bai %s' % tt, status=tt)
        kq = _goi(MyAssignmentsView, 'post', {'assignment_id': aid, 'content': 'x'},
                  ai=lop['hv'][0])
        # draft → 404 (em không thấy bài đó), closed → 409 (thấy nhưng đã đóng)
        assert kq.status_code in (404, 409), (tt, kq.status_code)


@pytest.mark.django_db
def test_nop_rong_tra_400(lop):
    aid = _tao_bai(lop, status='open')
    assert _goi(MyAssignmentsView, 'post', {'assignment_id': aid, 'content': '   '},
                ai=lop['hv'][0]).status_code == 400


# ── Xoá ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_xoa_bai_da_co_nguoi_nop_phai_xac_nhan_hai_buoc(lop):
    aid = _tao_bai(lop, status='open')
    _goi(MyAssignmentsView, 'post', {'assignment_id': aid, 'content': 'bai lam'},
         ai=lop['hv'][0])
    _goi(AssignmentGradingView, 'post', {'grades': [{'user_id': lop['hv'][0].id, 'score': 7}]},
         ai=lop['gv'], assignment_id=aid)

    kq = _goi(AssignmentDetailView, 'delete', ai=lop['gv'], assignment_id=aid)
    assert kq.status_code == 409 and kq.data['needsConfirm']

    req = f.delete('/x?confirm=1')
    force_authenticate(req, user=lop['gv'])
    assert AssignmentDetailView.as_view()(req, assignment_id=aid).status_code == 200

    assert q1('SELECT count(*) c FROM assignments WHERE id=%s', (aid,))['c'] == 0
    assert q1('SELECT count(*) c FROM submissions WHERE assignment_id=%s', (aid,))['c'] == 0
    # Sự kiện học tập phải đi theo: để lại thì điểm của một bài KHÔNG CÒN TỒN
    # TẠI vẫn nằm trong bản đồ năng lực và sổ điểm của em.
    assert q1('SELECT count(*) c FROM learning_events WHERE ref_type=%s AND ref_id=%s',
              ('assignment', str(aid)))['c'] == 0


# ── Hiệu năng ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_danh_sach_khong_N_cong_1(lop):
    """Số câu SQL phải cố định, không tăng theo số bài trong lớp."""
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    def dem():
        with CaptureQueriesContext(connection) as ctx:
            _goi(ClassAssignmentsView, 'get', ai=lop['gv'], class_id=lop['id'])
        return len(ctx.captured_queries)

    _tao_bai(lop, title='B1')
    mot = dem()
    for i in range(7):
        _tao_bai(lop, title='B%d' % (i + 2))
    assert dem() == mot


# ── Bảng điều khiển trung tâm — hồi quy cho 4 lỗi vá ngày 31/08/2026 ────────
#
# Bốn lỗi dưới đây do một agent audit tìm ra và tôi đọc mã xác nhận lại từng
# cái. Điểm chung: KHÔNG cái nào làm sập gì cả — chúng chỉ in ra một con số
# sai, và con số sai thì trông y hệt con số đúng. Đó là lý do phải có test.

def _lop_trong(ten='Lop overview', course='hsa_quantitative', gv=None):
    c = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
           "VALUES (%s,%s,%s,'active') RETURNING id", (ten, course, gv))
    return c['id']


def _vao_lop(cid, uid, roi=False, ly_do=None):
    r = q1('INSERT INTO class_members (class_id, user_id, joined_at) '
           'VALUES (%s,%s,%s) RETURNING id', (cid, uid, local_now()))
    if roi:
        q1('UPDATE class_members SET left_at=%s, leave_reason=%s WHERE id=%s RETURNING id',
           (local_now(), ly_do, r['id']))
    return r['id']


def _mot_lop(cid):
    from teaching.overview import tong_quan
    return [x for x in tong_quan()['classes'] if x['id'] == cid][0]


@pytest.mark.django_db
def test_buoi_chua_toi_khong_bi_tinh_la_chua_diem_danh(db):
    """Buổi CHƯA TỚI thì chưa thể thiếu điểm danh.

    Trước bản vá, màn hình quản lý in "11 buổi đã dạy nhưng chưa ai điểm danh"
    cho một lớp mới xếp lịch 10 buổi tuần sau. Lớp nào chuẩn bị kỹ nhất thì bị
    quy trách nhiệm nặng nhất.
    """
    from datetime import timedelta
    gv = _nguoi('GV Overview 1', ROLE_TEACHER)
    cid = _lop_trong('Lop buoi tuong lai', gv=gv.id)
    nay = local_now()
    # đã dạy + đã tick
    q1("INSERT INTO class_sessions (class_id, starts_at, status, attendance_taken_at, "
       "created_by) VALUES (%s,%s,'planned',%s,%s) RETURNING id",
       (cid, nay - timedelta(days=2), nay, gv.id))
    # đã dạy, quên tick
    q1("INSERT INTO class_sessions (class_id, starts_at, status, created_by) "
       "VALUES (%s,%s,'planned',%s) RETURNING id", (cid, nay - timedelta(days=1), gv.id))
    # 10 buổi tuần sau
    for i in range(10):
        q1("INSERT INTO class_sessions (class_id, starts_at, status, created_by) "
           "VALUES (%s,%s,'planned',%s) RETURNING id",
           (cid, nay + timedelta(days=i + 1), gv.id))

    r = _mot_lop(cid)
    assert r['sessionsHeld'] == 2, r['sessionsHeld']
    assert r['sessionsUnmarked'] == 1, r['sessionsUnmarked']


@pytest.mark.django_db
def test_tien_do_khong_tinh_nguoi_da_bo_hoc(db):
    """Tử số và mẫu số phải đếm CÙNG một tập người.

    Mẫu số nhân với số em đang học; trước bản vá tử số gộp cả người đã rời lớp,
    nên lớp càng nhiều em bỏ học trông càng tiến độ tốt.
    """
    gv = _nguoi('GV Overview 2', ROLE_TEACHER)
    o_lai = _nguoi('HV O Lai', ROLE_STUDENT)
    da_bo = _nguoi('HV Da Bo', ROLE_STUDENT)
    cid = _lop_trong('Lop bo hoc', gv=gv.id)
    _vao_lop(cid, o_lai.id)
    _vao_lop(cid, da_bo.id, roi=True, ly_do='dropped')

    for i in range(3):
        _bai_xong(o_lai.id, 'hsa_quantitative', 'ol%d' % i)
    for i in range(20):
        _bai_xong(da_bo.id, 'hsa_quantitative', 'db%d' % i)

    r = _mot_lop(cid)
    assert r['lessonsDone'] == 3, 'người đã bỏ học không được cộng vào: %s' % r['lessonsDone']


@pytest.mark.django_db
def test_tien_do_chi_tinh_bai_cua_KHOA_MA_LOP_DANG_DAY(db):
    """Mẫu số là tổng bài của khoá lớp, nên tử số cũng phải bó theo khoá đó."""
    khoa = [r['id'] for r in q('SELECT id FROM courses ORDER BY id LIMIT 2')]
    if len(khoa) < 2:
        pytest.skip('cần ít nhất hai khoá trong CSDL để kiểm')
    gv = _nguoi('GV Overview 3', ROLE_TEACHER)
    hv = _nguoi('HV Hoc Cheo', ROLE_STUDENT)
    cid = _lop_trong('Lop bo khoa', course=khoa[0], gv=gv.id)
    _vao_lop(cid, hv.id)

    _bai_xong(hv.id, khoa[0], 'dung-khoa-1')
    _bai_xong(hv.id, khoa[0], 'dung-khoa-2')
    for i in range(9):
        _bai_xong(hv.id, khoa[1], 'khoa-khac-%d' % i)

    r = _mot_lop(cid)
    assert r['lessonsDone'] == 2, 'bài khoá khác không được cộng vào: %s' % r['lessonsDone']


@pytest.mark.django_db
def test_diem_thi_thu_khong_tinh_nguoi_da_bo_hoc(db):
    gv = _nguoi('GV Overview 4', ROLE_TEACHER)
    o_lai = _nguoi('HV Thi O Lai', ROLE_STUDENT)
    da_bo = _nguoi('HV Thi Da Bo', ROLE_STUDENT)
    cid = _lop_trong('Lop diem thi', gv=gv.id)
    _vao_lop(cid, o_lai.id)
    _vao_lop(cid, da_bo.id, roi=True, ly_do='dropped')
    _de_thi(o_lai.id, 80)
    _de_thi(da_bo.id, 10)

    r = _mot_lop(cid)
    assert r['mockCount'] == 1, r['mockCount']
    assert r['mockAvg'] == 80, 'điểm người đã bỏ học kéo trung bình xuống: %s' % r['mockAvg']


@pytest.mark.django_db
def test_lop_chi_co_tai_khoan_khong_phai_hoc_vien_van_hien_tren_bang(db):
    """Quản trị viên vào xem lớp mới trước khi xếp học viên → lớp không được biến mất."""
    from teaching.overview import tong_quan
    admin = _nguoi('Admin Xem Lop', 'admin')
    gv = _nguoi('GV Overview 5', ROLE_TEACHER)
    rong = _lop_trong('Lop hoan toan rong', gv=gv.id)
    chi_admin = _lop_trong('Lop chi co admin', gv=gv.id)
    _vao_lop(chi_admin, admin.id)

    ids = {c['id'] for c in tong_quan()['classes']}
    assert rong in ids, 'lớp rỗng phải hiện'
    assert chi_admin in ids, 'lớp chỉ có tài khoản quản trị viên KHÔNG được biến mất'
    r = _mot_lop(chi_admin)
    assert r['active'] == 0, 'nhưng tài khoản đó KHÔNG được đếm là học viên: %s' % r['active']


@pytest.mark.django_db
def test_khong_doc_duoc_thi_tra_None_chu_khong_tra_0(db, monkeypatch):
    """Số 0 GIẢ là lỗi nguy hiểm nhất ở đây: nó trông y hệt số 0 thật.

    Màn hình vẽ dấu gạch cho None và "0%" cho 0. Trước bản vá, một câu SQL hỏng
    làm CẢ TRUNG TÂM hiện "Tiến độ 0%" — trông như chưa ai học bài nào.
    """
    from django.db import DatabaseError

    from teaching import overview
    gv = _nguoi('GV Overview 6', ROLE_TEACHER)
    hv = _nguoi('HV Cho Hong', ROLE_STUDENT)
    cid = _lop_trong('Lop cau hong', gv=gv.id)
    _vao_lop(cid, hv.id)
    _bai_xong(hv.id, 'hsa_quantitative', 'co-that')

    that = overview.q

    def gia(sql, params=None):
        if 'learning_events' in sql:
            raise DatabaseError('gia lap cau tra hoc tap hong')
        return that(sql, params)

    monkeypatch.setattr(overview, 'q', gia)
    d = overview.tong_quan()
    r = [x for x in d['classes'] if x['id'] == cid][0]
    assert 'study' in d['summary']['incomplete']
    assert r['progressPct'] is None, 'phải là None, KHÔNG phải 0: %r' % r['progressPct']
    assert r['lessonsDone'] is None, r['lessonsDone']
    assert r['mockCount'] is None, r['mockCount']


def _bai_xong(uid, course_id, khoa_chong):
    q1("INSERT INTO learning_events (user_id, dedup_key, occurred_at, event_date, kind, "
       "course_id, score, max_score, source) "
       "VALUES (%s,%s,%s,%s,'lesson',%s,1,1,'system') RETURNING id",
       (uid, 'test:%s:%s' % (uid, khoa_chong), local_now(), local_now().date(), course_id))


def _de_thi(uid, diem):
    q1("INSERT INTO learning_events (user_id, dedup_key, occurred_at, event_date, kind, "
       "score, max_score, source) VALUES (%s,%s,%s,%s,'mock',%s,100,'system') RETURNING id",
       (uid, 'test:mock:%s' % uid, local_now(), local_now().date(), diem))


# ── Học viên quay lại lớp cũ — hồi quy cho `reports._members` (31/08/2026) ──

@pytest.mark.django_db
def test_hoc_vien_quay_lai_lop_cu_chi_hien_MOT_dong(db):
    """Từ §36, một cặp (lớp, người) có thể có nhiều dòng `class_members`.

    Chỉ mục duy nhất là chỉ mục MỘT PHẦN (`WHERE left_at IS NULL`) nên em rời
    lớp rồi quay lại sinh dòng mới — đúng thiết kế, để giữ lịch sử từng lượt.
    Nhưng `_members` chưa gộp theo người, nên em đó bị đếm HAI LẦN ở khắp nơi:
    sổ điểm danh CSV in hai dòng cùng tên, `summary.left` báo có người rời lớp
    trong khi không ai rời, và mẫu số bản đồ năng lực lớp bị thổi lên.
    """
    from teaching.reports import _members, class_report
    gv = _nguoi('GV Quay Lai', ROLE_TEACHER)
    a = _nguoi('HV O Yen', ROLE_STUDENT)
    b = _nguoi('HV Quay Lai', ROLE_STUDENT)
    c = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
           "VALUES ('Lop quay lai','hsa_quantitative',%s,'active') RETURNING id", (gv.id,))
    for u in (a, b):
        q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s) '
           'RETURNING id', (c['id'], u.id, local_now()))
    # em B rời lớp rồi quay lại → hai dòng cho cùng một người
    cu = q1("UPDATE class_members SET left_at=%s, leave_reason='completed' "
            'WHERE class_id=%s AND user_id=%s RETURNING id', (local_now(), c['id'], b.id))
    q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s) '
       'RETURNING id', (c['id'], b.id, local_now()))
    assert q1('SELECT count(*) n FROM class_members WHERE class_id=%s AND user_id=%s',
              (c['id'], b.id))['n'] == 2, 'kịch bản phải thật sự sinh được hai dòng'
    assert cu

    ds = _members(c['id'])
    assert [r['user_id'] for r in ds] == sorted([a.id, b.id], key=lambda i: (
        'HV O Yen' if i == a.id else 'HV Quay Lai')), [r['name'] for r in ds]
    assert len(ds) == 2, 'hai con người thì hai dòng, không phải ba'

    # Lượt được giữ phải là lượt ĐANG HỌC, không phải lượt đã kết thúc.
    dong_b = [r for r in ds if r['user_id'] == b.id][0]
    assert dong_b['left_at'] is None, 'phải giữ lượt đang học, không giữ lượt đã rời'
    assert dong_b['luot'] == 2, 'nhưng vẫn phải đếm được là em ấy học hai lượt'

    bc = class_report(c['id'])
    s = bc['summary']
    assert s['students'] == 2 and s['active'] == 2, s
    assert s['left'] == 0, 'không ai đang ở ngoài lớp, `left` phải là 0: %s' % s['left']
    assert s['enrolledEver'] == 3, 'số LƯỢT ghi danh vẫn là 3: %s' % s['enrolledEver']


@pytest.mark.django_db
def test_chu_de_phai_thuoc_danh_muc_cua_khoa(lop):
    """Bẫy gõ phím tôi tự tạo ra rồi tự bịt lại, cùng ngày 31/08/2026.

    Bản đầu nhận `topic` là văn bản tự do. Bản đồ năng lực của HỌC VIÊN dựng ô
    từ `lessons.module`, còn bản đồ của GIẢNG VIÊN dựng ô từ `topic` của sự
    kiện — nên "Doc hieu" (thiếu dấu) và "Đọc hiểu" thành HAI ô trên màn hình
    giảng viên và KHÔNG ô nào trên màn hình em. Một dấu tiếng Việt là đủ, và
    không màn hình nào báo gì.
    """
    kq = _goi(ClassAssignmentsView, 'post',
              {'title': 'Bai lech chu de', 'topic': 'So hoc'},  # thiếu dấu
              ai=lop['gv'], class_id=lop['id'])
    assert kq.status_code == 400, 'chủ đề ngoài danh mục phải bị từ chối'
    assert 'Số học' in kq.data['error'], 'và phải nói ra danh mục hợp lệ: %s' % kq.data
    # để trống vẫn được — điểm vào sổ, chỉ là không vào được ô nào
    assert _goi(ClassAssignmentsView, 'post', {'title': 'Bai khong chu de', 'topic': None},
                ai=lop['gv'], class_id=lop['id']).status_code == 201
    # danh mục gửi kèm để màn hình vẽ ô CHỌN thay vì ô gõ
    ds = _goi(ClassAssignmentsView, 'get', ai=lop['gv'], class_id=lop['id']).data
    assert 'Số học' in ds['topics'], ds.get('topics')


# ── Một định nghĩa chuyên cần cho mọi mặt (31/08/2026) ──────────────────────

@pytest.mark.django_db
def test_ba_mat_cung_noi_MOT_con_so_chuyen_can(db):
    """Sổ CSV, báo cáo phụ huynh và phép đếm vắng phải khớp nhau.

    Trước bản vá có HAI mẫu số chạy song song và bảng chéo CSV còn cộng cả buổi
    ĐÃ HUỶ. Đo được trên cùng một em: CSV nói 100%, tờ gửi phụ huynh nói 67% —
    và tờ giấy là thứ đi ra khỏi hệ thống, về tận nhà.
    """
    from datetime import timedelta

    from teaching.attendance import dem_theo_hoc_vien, ti_le
    from teaching.parent_report import _chuyen_can
    gv = _nguoi('GV Chuyen Can', ROLE_TEACHER)
    em = _nguoi('HV Chuyen Can', ROLE_STUDENT)
    ban = _nguoi('HV Ban Cung Lop', ROLE_STUDENT)
    c = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
           "VALUES ('Lop chuyen can','hsa_quantitative',%s,'active') RETURNING id", (gv.id,))
    for u in (em, ban):
        q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s) '
           'RETURNING id', (c['id'], u.id, local_now()))

    nay = local_now()
    buoi = []
    for i, tt in enumerate(('planned', 'planned', 'planned', 'cancelled')):
        r = q1('INSERT INTO class_sessions (class_id, starts_at, status, '
               'attendance_taken_at, created_by) VALUES (%s,%s,%s,%s,%s) RETURNING id',
               (c['id'], nay - timedelta(days=5 - i), tt, nay, gv.id))
        buoi.append(r['id'])

    # Em có mặt 2 buổi, vắng 1 buổi ĐÃ HUỶ, và buổi thứ 3 giảng viên SÓT không tick em.
    for sid, tt in ((buoi[0], 'present'), (buoi[1], 'present'), (buoi[3], 'absent')):
        q1('INSERT INTO attendance (session_id, user_id, status, marked_at, marked_by) '
           'VALUES (%s,%s,%s,%s,%s) RETURNING session_id', (sid, em.id, tt, nay, gv.id))
    # Bạn cùng lớp được tick đủ cả ba buổi thật → buổi 3 vẫn nằm trong "đã tick".
    for sid in (buoi[0], buoi[1], buoi[2]):
        q1('INSERT INTO attendance (session_id, user_id, status, marked_at, marked_by) '
           'VALUES (%s,%s,%s,%s,%s) RETURNING session_id', (sid, ban.id, 'present', nay, gv.id))

    # SỰ THẬT: em có dòng ở 2 buổi KHÔNG huỷ, có mặt cả 2 → 100%, và thiếu 1 buổi.
    dem, ok = dem_theo_hoc_vien(c['id'], [em.id])
    assert ok and dem[em.id]['marked'] == 2, dem

    cc = _chuyen_can(c['id'], em.id, (nay - timedelta(days=30)).date(), nay.date())
    assert cc['present'] == 2 and cc['absent'] == 0, cc
    assert cc['noRecord'] == 1, 'buổi giảng viên sót phải được BÁO RIÊNG: %s' % cc
    assert cc['attendedPct'] == 100, (
        'em đi đủ mọi buổi có dòng thì phải là 100%%, không phải %s' % cc['attendedPct'])
    # Bất biến bốn ô: cộng lại phải bằng mẫu số của tờ giấy.
    assert (cc['present'] + cc['late'] + cc['absent'] + cc['excused'] + cc['noRecord']
            == cc['sessionsCounted']), cc

    # Cùng công thức, cùng con số, ở cả hai nơi.
    assert ti_le(cc['present'] + cc['late'], cc['sessionsCounted'] - cc['noRecord']) == 100
    assert ti_le(0, 0) is None, 'chưa có dòng nào thì None, KHÔNG phải 0'
