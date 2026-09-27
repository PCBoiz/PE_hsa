"""KHE LỘ SỰ TỒN TẠI — cửa nào trả 403 ở chỗ đáng lẽ 404 (audit bảo mật 27/09/2026).

Luật của dự án, ghi ở ba chỗ độc lập (`docs/ERP_TOPHSA_2026-08-24.md` dòng 48,
`common/permissions.py::can_see_class`, `forum/views.py` §75): **lớp / bài / buổi
không thuộc mình thì trả 404, không trả 403** — 403 là tự thú nhận "thứ đó có
thật, chỉ là anh không được xem".

Tệp này không đọc mã để biết kết quả mong đợi. Nó dựng hai lớp RIÊNG BIỆT, cầm
thẻ của người lớp A gõ vào id của lớp B, rồi so mã trả về với mã trả về khi gõ
vào một id KHÔNG TỒN TẠI. Hai mã ấy phải bằng nhau — nếu khác nhau thì chính sự
khác nhau ấy là câu trả lời cho "id này có thật không".

Vì sao "chỉ là mã trạng thái" vẫn đáng vá: người dùng của TopHSA là trẻ vị thành
niên, và một vòng lặp đếm id nói được "trung tâm có bao nhiêu lớp, bao nhiêu buổi,
bao nhiêu bài viết" — tức quy mô và nhịp hoạt động của trung tâm — mà không cần
đọc nổi một dòng nội dung nào. Đó là thứ mà chính ba chú thích trên đã quyết là
không nói ra.

Chạy trên CSDL thật, giao dịch CUỘN LẠI (`conftest.py`); chỉ đếm dữ liệu của
chính mình, mọi lời gọi đi qua URL thật.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q1
from common.permissions import ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db

#: Id chắc chắn không có trong bảng nào — mốc "không tồn tại" để so.
KHONG_CO = 2 ** 31 - 7

LINK = 'https://zoom.us/rec/share/audit-27-09'


def _nguoi(hau_to, vai=ROLE_STUDENT):
    r = q1("INSERT INTO users (name, email, password, role, streak) "
           "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
           ('Audit ' + hau_to, 'audit_lt_%s@example.com' % hau_to, vai))
    return User.objects.get(id=r['id'])


def _lop(ten, gv):
    return q1("INSERT INTO classes (name, course_id, teacher_id, status) "
              "VALUES (%s, 'hsa_quantitative', %s, 'active') RETURNING id",
              (ten, gv.id))['id']


def _vao(lop, u):
    q1('INSERT INTO class_members (class_id, user_id, joined_at) '
       'VALUES (%s, %s, %s) RETURNING id', (lop, u.id, local_now() - timedelta(days=10)))


def _buoi(lop):
    return q1('INSERT INTO class_sessions (class_id, starts_at, duration_minutes, '
              "topic, recording_url, status) VALUES (%s, %s, 90, 'Buổi audit', %s, 'done') "
              'RETURNING id', (lop, local_now() - timedelta(days=2), LINK))['id']


def _bai(lop, tac_gia):
    return q1("INSERT INTO posts (user_id, category, title, content, class_id) "
              "VALUES (%s, 'discuss', 'Bài của lớp B', 'nội dung riêng', %s) RETURNING id",
              (tac_gia.id, lop))['id']


def _the(u):
    c = APIClient()
    c.force_authenticate(user=u)
    return c


@pytest.fixture
def hai_lop(db):
    """Lớp A (em `emA` học) và lớp B (em `emB` học) — không dính nhau."""
    gv = _nguoi('gv', ROLE_TEACHER)
    a, b = _lop('Audit A', gv), _lop('Audit B', gv)
    em_a, em_b = _nguoi('a'), _nguoi('b')
    _vao(a, em_a)
    _vao(b, em_b)
    return {'gv': gv, 'a': a, 'b': b, 'emA': em_a, 'emB': em_b}


def _hai_ma(client, duong_that, duong_ma):
    """(mã khi gõ id CÓ THẬT của người khác, mã khi gõ id KHÔNG TỒN TẠI)."""
    return (client.post(duong_that).status_code, client.post(duong_ma).status_code)


def test_ghi_luot_mo_ban_ghi_khong_phan_biet_buoi_co_that(hai_lop):
    """POST /api/sessions/<id>/ban-ghi/da-mo — em lớp A gõ buổi của lớp B.

    Buổi có thật của lớp khác và buổi không tồn tại phải cho CÙNG một mã.
    """
    buoi_b = _buoi(hai_lop['b'])
    c = _the(hai_lop['emA'])
    that, ma = _hai_ma(c, '/api/sessions/%d/ban-ghi/da-mo' % buoi_b,
                       '/api/sessions/%d/ban-ghi/da-mo' % KHONG_CO)
    assert that == ma == 404, (
        'buổi có thật của lớp khác trả %s, buổi không tồn tại trả %s — chênh lệch này '
        'đếm được từ ngoài và nó nói "buổi %d có thật"' % (that, ma, buoi_b))


def test_bao_loi_ban_ghi_khong_phan_biet_buoi_co_that(hai_lop):
    """Cùng khe, ở cửa báo lỗi bản ghi."""
    buoi_b = _buoi(hai_lop['b'])
    c = _the(hai_lop['emA'])
    that, ma = _hai_ma(c, '/api/sessions/%d/ban-ghi/bao-loi' % buoi_b,
                       '/api/sessions/%d/ban-ghi/bao-loi' % KHONG_CO)
    assert that == ma == 404, (
        'buổi có thật của lớp khác trả %s, buổi không tồn tại trả %s' % (that, ma))


def test_thong_ke_ban_ghi_tra_404_cho_lop_khong_phu_trach(hai_lop):
    """GET /api/teach/classes/<id>/ban-ghi — giảng viên không phụ trách lớp.

    `can_see_class` trả False cho cả "lớp không có" lẫn "lớp có mà không phải của
    anh", nên cửa phải trả 404 như mọi cửa khác của `teaching/` (quy ước ghi ở
    `teaching/sessions.py:17`, `teaching/assignments.py:464`, `teaching/danh_gia.py:108`).
    """
    gv_ngoai = _nguoi('gvngoai', ROLE_TEACHER)
    c = _the(gv_ngoai)
    that = c.get('/api/teach/classes/%d/ban-ghi' % hai_lop['a']).status_code
    ma = c.get('/api/teach/classes/%d/ban-ghi' % KHONG_CO).status_code
    assert that == ma == 404, 'lớp thật %s ≠ lớp không có %s' % (that, ma)


def test_nhac_xem_ban_ghi_tra_404_cho_lop_khong_phu_trach(hai_lop):
    """Cùng khe ở cửa "nhắc em chưa mở"."""
    gv_ngoai = _nguoi('gvngoai2', ROLE_TEACHER)
    buoi_a = _buoi(hai_lop['a'])
    c = _the(gv_ngoai)
    that = c.post('/api/teach/classes/%d/ban-ghi/%d/nhac'
                  % (hai_lop['a'], buoi_a)).status_code
    ma = c.post('/api/teach/classes/%d/ban-ghi/%d/nhac'
                % (KHONG_CO, buoi_a)).status_code
    assert that == ma == 404, 'lớp thật %s ≠ lớp không có %s' % (that, ma)


def test_sua_bai_dien_dan_lop_khac_khong_lo_bai_co_that(hai_lop):
    """PUT /api/posts/<id> — em lớp A sửa bài trong diễn đàn riêng của lớp B.

    `_chan_bai` (§75) đã gác GET, bình luận và thả cảm xúc, nhưng PUT/DELETE chỉ đi
    qua `_can_modify` — hàm ấy chỉ hỏi "có phải bài của anh không" nên trả 403, và
    403 ở đây nói ra rằng bài đó CÓ THẬT.
    """
    bai_b = _bai(hai_lop['b'], hai_lop['emB'])
    c = _the(hai_lop['emA'])
    than = {'content': 'sửa trộm'}
    that = c.put('/api/posts/%d' % bai_b, than, format='json').status_code
    ma = c.put('/api/posts/%d' % KHONG_CO, than, format='json').status_code
    assert that == ma == 404, (
        'bài có thật của lớp khác trả %s, bài không tồn tại trả %s' % (that, ma))
    # Và không được sửa được gì thật.
    con = q1('SELECT content FROM posts WHERE id=%s', (bai_b,))
    assert con['content'] == 'nội dung riêng'


def test_xoa_bai_dien_dan_lop_khac_khong_lo_bai_co_that(hai_lop):
    """DELETE /api/posts/<id> — cùng khe, và phải không xoá được gì."""
    bai_b = _bai(hai_lop['b'], hai_lop['emB'])
    c = _the(hai_lop['emA'])
    that = c.delete('/api/posts/%d' % bai_b).status_code
    ma = c.delete('/api/posts/%d' % KHONG_CO).status_code
    assert that == ma == 404, 'bài thật %s ≠ bài không có %s' % (that, ma)
    assert q1('SELECT 1 FROM posts WHERE id=%s', (bai_b,)), 'bài đã bị xoá!'


def test_sua_binh_luan_dien_dan_lop_khac_khong_lo_binh_luan_co_that(hai_lop):
    """PUT /api/comments/<id> — cùng khe ở tầng bình luận."""
    bai_b = _bai(hai_lop['b'], hai_lop['emB'])
    cid = q1("INSERT INTO comments (post_id, user_id, content) "
             "VALUES (%s, %s, 'bình luận riêng') RETURNING id",
             (bai_b, hai_lop['emB'].id))['id']
    c = _the(hai_lop['emA'])
    than = {'content': 'sửa trộm'}
    that = c.put('/api/comments/%d' % cid, than, format='json').status_code
    ma = c.put('/api/comments/%d' % KHONG_CO, than, format='json').status_code
    assert that == ma == 404, 'bình luận thật %s ≠ không có %s' % (that, ma)
    assert q1('SELECT content FROM comments WHERE id=%s', (cid,))['content'] == 'bình luận riêng'
