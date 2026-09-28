"""HỌC VỤ PHỤ TRÁCH LỚP (bảng TopHSA dòng 4, ô *"Phân công GV, giáo vụ, TG"*).

Bảng đang ghi MỘT PHẦN với lý do: *"GV + TG CÓ; học vụ thấy mọi lớp, không gán riêng"*.

── GÁN KHÔNG PHẢI LÀ CẮT QUYỀN ───────────────────────────────────────────────

Quản lý học vụ **vẫn thấy mọi lớp** — đó là việc của họ, và siết lại sẽ làm hỏng hàng loạt
màn đang chạy. Cái còn thiếu là câu trả lời cho "lớp này ai phụ trách": trung tâm có nhiều
học vụ, và khi một lớp có chuyện thì phải biết gọi ai. Nên đây là một dòng PHÂN CÔNG, không
phải một hàng rào quyền.

Vì thế dùng lại `class_members` — đúng cách hệ thống đã biết "trợ giảng X phụ trách lớp Y"
(`permissions._la_tro_giang_cua_lop`). Không bảng mới, không cột mới: một khái niệm đã có
tên thì đừng đặt cho nó cái tên thứ hai.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. Gán được một học vụ vào lớp; danh sách lớp trả về tên họ.
  2. Gỡ ra thì hết (`left_at`), và người đã gỡ không còn trên danh sách.
  3. Gán học vụ KHÔNG làm họ thành học viên: sĩ số lớp không đổi.
  4. Quyền KHÔNG đổi: học vụ chưa được gán vẫn mở được lớp ấy như trước.
  5. Chỉ quản trị / học vụ gán được — giảng viên của lớp thì không.

Chạy trên CSDL thật, giao dịch CUỘN LẠI. Xác nhận qua CỬA API, không đọc thẳng bảng.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q1, x
from common.permissions import ROLE_ACADEMIC, ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db


def _nguoi(ten, vai):
    r = q1("INSERT INTO users (name, email, password, role, streak) "
           "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
           (ten, '%s_hv@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=r['id'])


def _api(u):
    c = APIClient()
    c.force_authenticate(user=u)
    return c


@pytest.fixture
def canh():
    qt = _nguoi('QT Phu Trach', ROLE_ADMIN)
    gv = _nguoi('GV Phu Trach', ROLE_TEACHER)
    hv1 = _nguoi('Hoc Vu Mot', ROLE_ACADEMIC)
    hv2 = _nguoi('Hoc Vu Hai', ROLE_ACADEMIC)
    em = _nguoi('Em Phu Trach', ROLE_STUDENT)
    lop = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
             "VALUES ('Lop phu trach', 'hsa_quantitative', %s, 'active') RETURNING id",
             (gv.id,))['id']
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s)',
      (lop, em.id, local_now() - timedelta(days=10)))
    return {'qt': qt, 'gv': gv, 'hv1': hv1, 'hv2': hv2, 'em': em, 'lop': lop}


def _gan(canh, ai, uid):
    return _api(ai).post('/api/admin/classes/%d/members' % canh['lop'],
                         {'user_id': uid}, format='json')


def _chi_tiet(canh, ai=None):
    """Báo cáo đầy đủ một lớp. `/api/admin/classes/<id>` chỉ có PUT/DELETE — cửa ĐỌC là
    đường của khu giảng dạy, và nó cũng chính là chỗ màn Lớp học của học vụ lấy dữ liệu."""
    r = _api(ai or canh['qt']).get('/api/teach/classes/%d' % canh['lop'])
    assert r.status_code == 200, r.data
    return r.data


def _ten_hoc_vu(canh, ai=None):
    return sorted(x['name'] for x in (_chi_tiet(canh, ai).get('hocVuPhuTrach') or []))


# ── 1. Gán và gỡ ─────────────────────────────────────────────────────────────

def test_gan_duoc_hoc_vu_vao_lop(canh):
    assert _gan(canh, canh['qt'], canh['hv1'].id).status_code in (200, 201)
    assert _ten_hoc_vu(canh) == ['Hoc Vu Mot']


def test_hai_hoc_vu_thi_ca_hai_len_danh_sach(canh):
    for k in ('hv1', 'hv2'):
        _gan(canh, canh['qt'], canh[k].id)
    assert _ten_hoc_vu(canh) == ['Hoc Vu Hai', 'Hoc Vu Mot']


def test_go_ra_thi_khong_con_tren_danh_sach(canh):
    _gan(canh, canh['qt'], canh['hv1'].id)
    # Cửa gỡ nằm trên chính `/members`, nhận `user_id` ở query — không phải
    # `/members/<id>` (đường ấy chỉ có nhánh `/transfer`).
    r = _api(canh['qt']).delete('/api/admin/classes/%d/members?user_id=%d'
                                % (canh['lop'], canh['hv1'].id))
    assert r.status_code in (200, 204), getattr(r, 'data', r.status_code)
    assert _ten_hoc_vu(canh) == []


# ── 2. Gán học vụ KHÔNG phải là thêm một học viên ───────────────────────────

def test_gan_hoc_vu_khong_lam_tang_si_so(canh):
    """Sĩ số là số EM. Một học vụ lọt vào đó sẽ chảy vào mẫu số chuyên cần, vào tờ
    phụ huynh, và vào mọi con số trung tâm nhìn để quyết định mở lớp."""
    si_truoc = (_chi_tiet(canh).get('summary') or {}).get('students')
    _gan(canh, canh['qt'], canh['hv1'].id)
    si_sau = (_chi_tiet(canh).get('summary') or {}).get('students')
    assert si_sau == si_truoc, 'gán học vụ làm sĩ số lớp nhảy'


# ── 3. Gán KHÔNG phải là cắt quyền ──────────────────────────────────────────

def test_hoc_vu_chua_duoc_gan_van_mo_duoc_lop(canh):
    """Học vụ vẫn thấy mọi lớp — đây là dòng phân công, không phải hàng rào."""
    _gan(canh, canh['qt'], canh['hv1'].id)
    assert _api(canh['hv2']).get('/api/teach/classes/%d' % canh['lop']).status_code == 200


# ── 4. Ai gán được ──────────────────────────────────────────────────────────

def test_giang_vien_cua_lop_khong_gan_duoc_hoc_vu(canh):
    """Phân công nhân sự là việc của quản trị / học vụ, không phải của giảng viên."""
    assert _gan(canh, canh['gv'], canh['hv1'].id).status_code in (403, 404)
    assert _ten_hoc_vu(canh) == []
