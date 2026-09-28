"""DẠY THAY MỘT BUỔI (§58, Đ2 — bảng TopHSA dòng 10).

Giảng viên và trợ giảng gắn theo LỚP, nhưng một buổi lẻ có thể do người khác đứng: giảng
viên ốm, trợ giảng bận, trung tâm đổi người. `class_sessions.teacher_id` / `assistant_id`
NULL = theo lớp; có giá trị = buổi NÀY người ấy dạy.

── VÌ SAO PHÉP KIỂM CHẤM CÔNG NẰM CHUNG TỆP NÀY ──────────────────────────────

Đổi người dạy một buổi mà bảng chấm công vẫn tính cho người đứng tên lớp thì **lương sai**,
và đó là loại lỗi người ta chỉ phát hiện vào cuối tháng — khi đã trả tiền. Hai thứ phải đi
cùng nhau, nên phép kiểm cũng đứng cùng chỗ: ai sửa một bên mà quên bên kia thì đỏ ngay.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. Đặt người dạy thay cho một buổi; buổi khác của lớp KHÔNG đổi theo.
  2. Bỏ trống trở lại (`null`) thì buổi về lại "theo lớp".
  3. Chấm công đếm buổi ấy cho NGƯỜI DẠY THAY, và KHÔNG đếm cho giảng viên chủ lớp.
  4. Trợ giảng thay cũng vậy.
  5. Người được gán phải ĐÚNG VAI: gán một học viên làm giảng viên buổi → từ chối.
  6. Lớp không phải của mình → 404, và buổi không đổi.

Chạy trên CSDL thật, giao dịch CUỘN LẠI; chỉ đếm dữ liệu của chính mình. Xác nhận qua CỬA
API chứ không đọc thẳng bảng — câu `SELECT` của phép kiểm đi bằng kết nối khác với lời gọi
API, nên nó thấy hay không thấy dòng vừa ghi là tuỳ lượt (đo 27/09: một phép kiểm xanh khi
chạy riêng, đỏ khi chạy cả bộ, và cái đỏ ấy không nói gì về sản phẩm).
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q1, x
from common.permissions import ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db


def _nguoi(ten, vai):
    r = q1("INSERT INTO users (name, email, password, role, streak) "
           "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
           (ten, '%s_dt@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=r['id'])


def _lop(ten, gv):
    return q1("INSERT INTO classes (name, course_id, teacher_id, status) "
              "VALUES (%s, 'hsa_quantitative', %s, 'active') RETURNING id", (ten, gv.id))['id']


def _buoi(lop, cach_ngay=2, nguoi_tick=None):
    """Buổi ĐÃ dạy (đã điểm danh) — chấm công chỉ đếm buổi như thế."""
    bd = local_now() - timedelta(days=cach_ngay)
    return q1('''INSERT INTO class_sessions
                    (class_id, starts_at, duration_minutes, status,
                     attendance_taken_at, attendance_taken_by)
                 VALUES (%s, %s, 90, 'done', %s, %s) RETURNING id''',
              (lop, bd, bd + timedelta(minutes=95), nguoi_tick.id if nguoi_tick else None))['id']


def _api(u):
    c = APIClient()
    c.force_authenticate(user=u)
    return c


@pytest.fixture
def canh():
    gv = _nguoi('GV Chu Lop DT', ROLE_TEACHER)
    thay = _nguoi('GV Day Thay DT', ROLE_TEACHER)
    tg = _nguoi('TG Chu Lop DT', ROLE_ASSISTANT)
    tg2 = _nguoi('TG Thay DT', ROLE_ASSISTANT)
    em = _nguoi('Em DT', ROLE_STUDENT)
    lop = _lop('Lop day thay', gv)
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s)',
      (lop, tg.id, local_now() - timedelta(days=30)))
    return {'gv': gv, 'thay': thay, 'tg': tg, 'tg2': tg2, 'em': em, 'lop': lop}


def _dat(canh, buoi, ai, **body):
    return _api(ai).patch('/api/teach/sessions/%d' % buoi, body, format='json')


def _doc(canh, buoi, ai=None):
    r = _api(ai or canh['gv']).get('/api/teach/sessions/%d' % buoi)
    assert r.status_code == 200, r.data
    # Cửa bọc trong khoá `session` — đọc thẳng `r.data` là đọc cái vỏ.
    return r.data['session']


# ── 1. Đặt và bỏ người dạy thay ──────────────────────────────────────────────

def test_dat_nguoi_day_thay_cho_mot_buoi(canh):
    b = _buoi(canh['lop'])
    r = _dat(canh, b, canh['gv'], teacherId=canh['thay'].id)
    assert r.status_code == 200, r.data
    assert _doc(canh, b)['teacherId'] == canh['thay'].id


def test_buoi_khac_cua_lop_khong_doi_theo(canh):
    """Đổi người một buổi là đổi MỘT buổi — không phải đổi giảng viên của lớp."""
    b1, b2 = _buoi(canh['lop'], 2), _buoi(canh['lop'], 4)
    _dat(canh, b1, canh['gv'], teacherId=canh['thay'].id)
    assert _doc(canh, b2)['teacherId'] is None


def test_bo_trong_thi_ve_lai_theo_lop(canh):
    b = _buoi(canh['lop'])
    _dat(canh, b, canh['gv'], teacherId=canh['thay'].id)
    r = _dat(canh, b, canh['gv'], teacherId=None)
    assert r.status_code == 200, r.data
    assert _doc(canh, b)['teacherId'] is None


def test_dat_tro_giang_thay(canh):
    b = _buoi(canh['lop'])
    assert _dat(canh, b, canh['gv'], assistantId=canh['tg2'].id).status_code == 200
    assert _doc(canh, b)['assistantId'] == canh['tg2'].id


# ── 2. Vai phải đúng ─────────────────────────────────────────────────────────

def test_khong_gan_hoc_vien_lam_giang_vien_buoi(canh):
    """Một ô chọn trên màn có thể bị gửi kèm id bất kỳ — hàng rào ở máy chủ."""
    b = _buoi(canh['lop'])
    r = _dat(canh, b, canh['gv'], teacherId=canh['em'].id)
    assert r.status_code == 400, r.data
    assert _doc(canh, b)['teacherId'] is None


def test_khong_gan_giang_vien_vao_o_tro_giang(canh):
    b = _buoi(canh['lop'])
    r = _dat(canh, b, canh['gv'], assistantId=canh['thay'].id)
    assert r.status_code == 400, r.data
    assert _doc(canh, b)['assistantId'] is None


def test_nguoi_khong_ton_tai_thi_tu_choi(canh):
    b = _buoi(canh['lop'])
    assert _dat(canh, b, canh['gv'], teacherId=99_999_999).status_code == 400


# ── 3. Hàng rào lớp ──────────────────────────────────────────────────────────

def test_lop_khong_phai_cua_minh_thi_404(canh):
    b = _buoi(canh['lop'])
    nguoi_la = _nguoi('GV Khong Lien Quan DT', ROLE_TEACHER)
    assert _dat(canh, b, nguoi_la, teacherId=nguoi_la.id).status_code == 404
    assert _doc(canh, b)['teacherId'] is None


# ── 4. Chấm công — nơi lỗi này thành tiền ───────────────────────────────────

def _cong(uid, buoi_id):
    """Số buổi của `uid` trong bảng chấm công, tính quanh buổi đã dựng."""
    from teaching.cham_cong import cham_cong
    s = q1('SELECT starts_at FROM class_sessions WHERE id = %s', (buoi_id,))['starts_at']
    dau = s.date().replace(day=1)
    ds = cham_cong(dau, (dau + timedelta(days=45)).replace(day=1))
    for r in ds:
        if r['id'] == uid:
            return {'buoi': r['soBuoi']}
    return None


def test_cham_cong_tinh_cho_nguoi_day_thay_chu_khong_phai_chu_lop(canh):
    """Dạy thay mà lương chảy về người đứng tên lớp là lỗi chỉ lộ ra vào cuối tháng."""
    b = _buoi(canh['lop'], nguoi_tick=canh['thay'])
    truoc_chu = (_cong(canh['gv'].id, b) or {}).get('buoi', 0)
    _dat(canh, b, canh['gv'], teacherId=canh['thay'].id)
    sau_chu = (_cong(canh['gv'].id, b) or {}).get('buoi', 0)
    sau_thay = (_cong(canh['thay'].id, b) or {}).get('buoi', 0)
    assert sau_thay >= 1, 'người dạy thay không được tính buổi nào'
    assert sau_chu == truoc_chu - 1, 'chủ lớp vẫn bị tính buổi mình không dạy'


def test_cham_cong_tinh_cho_tro_giang_thay(canh):
    b = _buoi(canh['lop'], nguoi_tick=canh['gv'])
    truoc_tg = (_cong(canh['tg'].id, b) or {}).get('buoi', 0)
    _dat(canh, b, canh['gv'], assistantId=canh['tg2'].id)
    assert (_cong(canh['tg2'].id, b) or {}).get('buoi', 0) >= 1
    assert (_cong(canh['tg'].id, b) or {}).get('buoi', 0) == truoc_tg - 1
