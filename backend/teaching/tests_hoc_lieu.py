"""HỌC LIỆU CỦA LỚP (§60) — giảng viên gắn tài liệu, học viên mở được.

Bảng TopHSA dòng 30 (*"học sinh · học liệu"*) và phần tài liệu của dòng 15. Anh Sơn chốt
26/09: làm **liên kết ngoài** trước (Drive, YouTube, link đề) vì nó không chờ khoá
Cloudflare R2; gắn được vào **cả kho chung của lớp lẫn từng buổi**.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. Giảng viên của lớp gắn được tài liệu cho lớp mình; lớp KHÁC → 404 (không lộ lớp
     có tồn tại hay không).
  2. Học viên thấy tài liệu của lớp mình, KHÔNG thấy tài liệu lớp khác.
  3. `an = TRUE` là "đã gắn, chưa mở cho em xem": giảng viên vẫn thấy, học viên KHÔNG.
  4. Tài liệu gắn vào MỘT BUỔI chỉ tới em THUỘC buổi ấy — buổi bù (`session_participants`,
     §62e) có hai em thì hai em ấy thấy, cả lớp thì không. Đây đúng là lỗ mà agent soát
     tìm ra trong §72 ngày 26/09: bốn cửa của một tính năng, ba cửa quên mất buổi bù, nên
     thống kê đếm cả lớp còn màn của em lại ẩn đúng buổi ấy. Viết phép kiểm này TRƯỚC khi
     viết mã, để lần này không lặp lại.
  5. Em ĐÃ RỜI LỚP (`left_at` có giá trị) không còn thấy tài liệu.
  6. `javascript:` và các lược đồ khác http/https bị TỪ CHỐI. Đây là ô nhập tự do rồi
     đem dựng thành thẻ `<a href>` cho người khác bấm — đúng hình dạng của hai lỗ
     stored-XSS đã từng nằm trong tầng JS cũ của repo này.

Chạy trên CSDL thật, giao dịch CUỘN LẠI (`conftest.py`); chỉ đếm dữ liệu của chính mình,
mọi lời gọi đi qua URL thật.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q1, x
from common.permissions import ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db

LINK = 'https://drive.google.com/file/d/hl-thu-nghiem-26-09/view'


def _nguoi(ten, vai):
    row = q1("INSERT INTO users (name, email, password, role, streak) "
             "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
             (ten, '%s_hl@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=row['id'])


def _lop(ten, gv):
    return q1("INSERT INTO classes (name, course_id, teacher_id, status) "
              "VALUES (%s, 'hsa_quantitative', %s, 'active') RETURNING id", (ten, gv.id))['id']


def _vao(lop, u, roi=False):
    q1('INSERT INTO class_members (class_id, user_id, joined_at, left_at) '
       'VALUES (%s, %s, %s, %s) RETURNING id',
       (lop, u.id, local_now() - timedelta(days=20),
        local_now() - timedelta(days=1) if roi else None))


def _buoi(lop, cach_ngay=3):
    return q1('INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status) '
              "VALUES (%s, %s, 90, 'done') RETURNING id",
              (lop, local_now() - timedelta(days=cach_ngay)))['id']


def _rieng(buoi, uids):
    """Buổi BÙ: chỉ những em này thuộc buổi (§62e `session_participants`)."""
    # Khoá chính là (session_id, user_id) — bảng KHÔNG có cột `id`, nên `x` chứ không `q1`.
    for u in uids:
        x('INSERT INTO session_participants (session_id, user_id) VALUES (%s, %s)', (buoi, u.id))


def _api(u):
    c = APIClient()
    c.force_authenticate(user=u)
    return c


@pytest.fixture
def lop():
    gv = _nguoi('GV Hoc Lieu', ROLE_TEACHER)
    tg = _nguoi('TG Hoc Lieu', ROLE_ASSISTANT)
    a = _nguoi('HV Hoc Lieu A', ROLE_STUDENT)
    b = _nguoi('HV Hoc Lieu B', ROLE_STUDENT)
    roi = _nguoi('HV Da Roi Lop', ROLE_STUDENT)
    ngoai = _nguoi('HV Ngoai Lop', ROLE_STUDENT)
    l = _lop('Lop hoc lieu', gv)
    khac = _lop('Lop khac hoc lieu', gv)
    for u in (a, b):
        _vao(l, u)
    _vao(l, roi, roi=True)
    return {'gv': gv, 'tg': tg, 'a': a, 'b': b, 'roi': roi, 'ngoai': ngoai,
            'id': l, 'khac': khac}


def _gan(lop_id, ai, **body):
    d = {'ten': 'Slide buổi 1', 'url': LINK}
    d.update(body)
    return _api(ai).post('/api/teach/classes/%d/hoc-lieu' % lop_id, d, format='json')


# ── 1. Ai gắn được ───────────────────────────────────────────────────────────

def test_giang_vien_gan_duoc_cho_lop_minh(lop):
    r = _gan(lop['id'], lop['gv'])
    assert r.status_code == 201, r.data
    assert r.data['id'] and r.data['nguon'] == 'link'


def test_lop_khong_phai_cua_minh_thi_404_chu_khong_403(lop):
    gv2 = _nguoi('GV Khong Lien Quan', ROLE_TEACHER)
    r = _gan(lop['id'], gv2)
    assert r.status_code == 404, r.data
    assert 'lớp' in str(r.data).lower()


def test_hoc_vien_khong_gan_duoc(lop):
    assert _gan(lop['id'], lop['a']).status_code in (403, 404)


# ── 2. Ai xem được ───────────────────────────────────────────────────────────

def _xem(lop_id, ai):
    return _api(ai).get('/api/teach/classes/%d/hoc-lieu' % lop_id)


def test_hoc_vien_trong_lop_thay_tai_lieu(lop):
    _gan(lop['id'], lop['gv'])
    r = _xem(lop['id'], lop['a'])
    assert r.status_code == 200, r.data
    assert [t['ten'] for t in r.data['items']] == ['Slide buổi 1']


def test_nguoi_ngoai_lop_khong_thay_gi(lop):
    _gan(lop['id'], lop['gv'])
    assert _xem(lop['id'], lop['ngoai']).status_code in (403, 404)


def test_em_da_roi_lop_khong_con_thay(lop):
    """Rời lớp là hết quyền xem tài liệu — cùng luật với bản ghi buổi học (§72)."""
    _gan(lop['id'], lop['gv'])
    assert _xem(lop['id'], lop['roi']).status_code in (403, 404)


# ── 3. Ẩn / hiện ─────────────────────────────────────────────────────────────

def test_tai_lieu_an_thi_hoc_vien_khong_thay_nhung_giang_vien_van_thay(lop):
    """Giảng viên soạn trước cả khoá rồi mở dần theo tiến độ."""
    _gan(lop['id'], lop['gv'], ten='Đề thi thử', an=True)
    assert [t['ten'] for t in _xem(lop['id'], lop['a']).data['items']] == []
    ds = _xem(lop['id'], lop['gv']).data['items']
    assert [t['ten'] for t in ds] == ['Đề thi thử']
    assert ds[0]['an'] is True


# ── 4. Buổi bù — cái lỗ đã lặp lại một lần trong §72 ────────────────────────

def test_tai_lieu_cua_buoi_bu_chi_toi_em_thuoc_buoi_ay(lop):
    bu = _buoi(lop['id'])
    _rieng(bu, [lop['a']])                       # buổi bù: chỉ em A
    _gan(lop['id'], lop['gv'], ten='Bài chữa buổi bù', sessionId=bu)
    assert [t['ten'] for t in _xem(lop['id'], lop['a']).data['items']] == ['Bài chữa buổi bù']
    assert [t['ten'] for t in _xem(lop['id'], lop['b']).data['items']] == [], \
        'em KHÔNG thuộc buổi bù vẫn thấy tài liệu của buổi ấy'


def test_tai_lieu_cua_buoi_thuong_toi_ca_lop(lop):
    """Buổi không có `session_participants` thì cả lớp thuộc buổi — đừng ẩn nhầm."""
    b = _buoi(lop['id'])
    _gan(lop['id'], lop['gv'], ten='Slide buổi thường', sessionId=b)
    for em in ('a', 'b'):
        assert [t['ten'] for t in _xem(lop['id'], lop[em]).data['items']] == ['Slide buổi thường']


def test_kho_chung_cua_lop_toi_moi_em(lop):
    """`sessionId` trống = kho chung, không dính buổi nào."""
    bu = _buoi(lop['id'])
    _rieng(bu, [lop['a']])
    _gan(lop['id'], lop['gv'], ten='Sổ tay cả khoá')
    for em in ('a', 'b'):
        assert [t['ten'] for t in _xem(lop['id'], lop[em]).data['items']] == ['Sổ tay cả khoá']


# ── 5. Địa chỉ nhập vào — ô tự do dựng thành <a href> cho người khác bấm ────

@pytest.mark.parametrize('xau', [
    'javascript:alert(1)',
    'JavaScript:alert(1)',
    ' javascript:alert(1)',
    'data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==',
    'file:///C:/Windows/System32',
    'vbscript:msgbox(1)',
    'khong-phai-dia-chi',
    # Lược đồ ĐÚNG mà không có tên miền: `https:` qua được phép kiểm lược đồ rồi trỏ
    # đi đâu không ai biết. Đột biến "bỏ đòi tên miền" LỌT qua bộ kiểm ngày 26/09 vì
    # không ca nào ở đây đòi tới `netloc` — một hàng rào không ai canh là một hàng rào
    # sẽ bị gỡ mất trong một lần dọn mã nào đó mà không ai nhận ra.
    'https:///khong-co-ten-mien',
    'http://',
    'https://',
])
def test_dia_chi_khong_phai_http_thi_tu_choi(lop, xau):
    r = _gan(lop['id'], lop['gv'], url=xau)
    assert r.status_code == 400, (xau, r.status_code, r.data)
    assert _xem(lop['id'], lop['gv']).data['items'] == [], 'đã ghi một dòng đáng lẽ phải bị từ chối'


@pytest.mark.parametrize('tot', [
    'https://drive.google.com/file/d/abc/view',
    'http://tophsa.vn/de-thi.pdf',
    'https://www.youtube.com/watch?v=abc',
])
def test_dia_chi_http_va_https_thi_nhan(lop, tot):
    assert _gan(lop['id'], lop['gv'], url=tot).status_code == 201


def test_khong_gan_duoc_vao_buoi_cua_lop_khac(lop):
    """Số buổi có thật nhưng thuộc lớp khác → 400, và không dòng nào được ghi.

    Không có phép kiểm này thì lời gọi `q1('SELECT 1 FROM class_sessions WHERE id = %s
    AND class_id = %s')` trong `hoc_lieu.py` có thể bị gỡ mà mọi thứ vẫn xanh — đột biến
    "gắn không kiểm buổi có thuộc lớp không" LỌT ngày 26/09. Hậu quả nếu gỡ thật: một
    tài liệu của lớp A dính số buổi của lớp B, và `thuoc_buoi` đem so em của lớp A với
    một buổi họ không bao giờ thuộc — tài liệu biến mất khỏi màn của chính lớp mình.
    """
    buoi_lop_khac = _buoi(lop['khac'])
    r = _gan(lop['id'], lop['gv'], sessionId=buoi_lop_khac)
    assert r.status_code == 400, r.data
    assert 'sessionId' in r.data.get('errors', {}), r.data
    ds = _xem(lop['id'], lop['gv']).data['items']
    assert ds == [], ('đã ghi một dòng đáng lẽ phải bị từ chối: %r | lop=%s buoi_lop_khac=%s'
                      % (ds, lop['id'], buoi_lop_khac))


def test_ten_rong_thi_tu_choi(lop):
    r = _gan(lop['id'], lop['gv'], ten='   ')
    assert r.status_code == 400 and 'ten' in r.data.get('errors', {})


# ── 6. Xoá ───────────────────────────────────────────────────────────────────

def test_giang_vien_xoa_duoc_tai_lieu_cua_lop_minh(lop):
    tid = _gan(lop['id'], lop['gv']).data['id']
    r = _api(lop['gv']).delete('/api/teach/classes/%d/hoc-lieu/%d' % (lop['id'], tid))
    assert r.status_code == 200, r.data
    assert [t['ten'] for t in _xem(lop['id'], lop['a']).data['items']] == []


def test_khong_xoa_duoc_tai_lieu_cua_lop_khac(lop):
    """Số id đúng nhưng lớp trên đường dẫn sai → 404, và tài liệu vẫn còn.

    Phần "vẫn còn" đo QUA CỬA API chứ không đọc thẳng bảng: một câu `SELECT` của phép kiểm
    đi bằng kết nối khác với lời gọi API, nên nó thấy hay không thấy dòng vừa ghi là tuỳ
    lượt chạy — chạy riêng thì xanh, chạy cả bộ thì đỏ, và cái đỏ ấy không nói gì về sản
    phẩm. Đo bằng chính đường người dùng đi thì câu trả lời không phụ thuộc vào chuyện ấy.
    """
    tid = _gan(lop['id'], lop['gv']).data['id']
    r = _api(lop['gv']).delete('/api/teach/classes/%d/hoc-lieu/%d' % (lop['khac'], tid))
    assert r.status_code == 404, r.data
    con = [t['id'] for t in _xem(lop['id'], lop['gv']).data['items']]
    assert tid in con, 'tài liệu bị xoá dù đường dẫn mang lớp khác'
