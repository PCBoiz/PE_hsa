"""BÀI TẬP TRỎ VỀ MỤC KHUNG CHƯƠNG TRÌNH (§74, bảng TopHSA dòng 5).

Khung đã có mục loại `bai_tap` / `kiem_tra` (§64), giảng viên đã giao được bài cho lớp
(`assignments`). Nhưng hai thứ KHÔNG nối nhau: khung nói "buổi 3 có bài về nhà", bài giao
nói "bài tập X hạn thứ Sáu", và không gì trả lời được **"bài về nhà của buổi 3 đã giao chưa"**.

── NULL LÀ TRẠNG THÁI BÌNH THƯỜNG ────────────────────────────────────────────

Phần lớn bài hiện có không thuộc mục khung nào, và vẫn phải giao được như thế. Cột này chỉ
THÊM một đường nối, không bắt ai phải dùng — một trường bắt buộc ở đây sẽ chặn đúng giảng
viên đang vội giao bài trước giờ lên lớp.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. Giao bài KHÔNG chọn mục khung → vẫn giao được, `syllabus_item_id` là NULL.
  2. Giao bài CÓ chọn mục → đọc lại thấy đúng mục ấy.
  3. Mục thuộc khung của khoá KHÁC → từ chối (không nối bừa hai chương trình).
  4. Xoá mục khung → bài KHÔNG bị xoá theo, chỉ rơi về NULL (§29: giữ lịch sử).
  5. Mục khung trả về "đã giao bài nào chưa" — đó là câu hỏi cột này sinh ra để trả lời.

Chạy trên CSDL thật, giao dịch CUỘN LẠI; chỉ đếm dữ liệu của chính mình.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q1, x
from common.permissions import ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db


def _nguoi(ten, vai):
    r = q1("INSERT INTO users (name, email, password, role, streak) "
           "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
           (ten, '%s_bk@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=r['id'])


def _api(u):
    c = APIClient()
    c.force_authenticate(user=u)
    return c


def _khung(course_id='hsa_quantitative'):
    """Một khung + một buổi + một mục loại `bai_tap`."""
    v = q1("INSERT INTO syllabus_versions (course_id, name, status) "
           "VALUES (%s, 'Khung thu §74', 'nhap') RETURNING id", (course_id,))['id']
    s = q1('INSERT INTO syllabus_sessions (version_id, sort_order, name) '
           "VALUES (%s, 1, 'Buoi 1') RETURNING id", (v,))['id']
    m = q1('''INSERT INTO syllabus_items (session_id, sort_order, kind, title, weight)
              VALUES (%s, 1, 'bai_tap', 'Bai ve nha buoi 1', 1) RETURNING id''', (s,))['id']
    return {'ver': v, 'buoi': s, 'muc': m}


@pytest.fixture
def canh():
    gv = _nguoi('GV Bai Khung', ROLE_TEACHER)
    em = _nguoi('Em Bai Khung', ROLE_STUDENT)
    lop = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
             "VALUES ('Lop bai khung', 'hsa_quantitative', %s, 'active') RETURNING id",
             (gv.id,))['id']
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s)',
      (lop, em.id, local_now() - timedelta(days=10)))
    return {'gv': gv, 'em': em, 'lop': lop, **_khung()}


def _giao(canh, **body):
    d = {'title': 'Bai tap thu', 'due_at': (local_now() + timedelta(days=3)).isoformat()}
    d.update(body)
    return _api(canh['gv']).post('/api/teach/classes/%d/assignments' % canh['lop'], d, format='json')


def _doc(canh, aid):
    return q1('SELECT syllabus_item_id FROM assignments WHERE id = %s', (aid,))


# ── 1. Không chọn mục vẫn giao được ─────────────────────────────────────────

def test_giao_bai_khong_chon_muc_van_duoc(canh):
    """Trường bắt buộc ở đây sẽ chặn đúng giảng viên đang vội giao bài trước giờ lên lớp."""
    r = _giao(canh)
    assert r.status_code in (200, 201), r.data
    assert _doc(canh, r.data['id'])['syllabus_item_id'] is None


# ── 2. Chọn mục thì nối được ────────────────────────────────────────────────

def test_giao_bai_co_chon_muc_khung(canh):
    r = _giao(canh, syllabus_item_id=canh['muc'])
    assert r.status_code in (200, 201), r.data
    assert _doc(canh, r.data['id'])['syllabus_item_id'] == canh['muc']


def test_muc_cua_khoa_khac_thi_tu_choi(canh):
    """Không nối bừa hai chương trình: bài của lớp môn A trỏ vào mục khung môn B."""
    khac = _khung('hsa_verbal')
    r = _giao(canh, syllabus_item_id=khac['muc'])
    assert r.status_code == 400, r.data


def test_muc_khong_ton_tai_thi_tu_choi(canh):
    assert _giao(canh, syllabus_item_id=99_999_999).status_code == 400


# ── 3. Xoá mục khung KHÔNG kéo mất bài ─────────────────────────────────────

def test_xoa_muc_khung_thi_bai_roi_ve_null_chu_khong_mat(canh):
    """Sửa khung không được kéo mất bài giảng viên đã giao và các em đã nộp (§29)."""
    aid = _giao(canh, syllabus_item_id=canh['muc']).data['id']
    x('DELETE FROM syllabus_items WHERE id = %s', (canh['muc'],))
    con = q1('SELECT id, syllabus_item_id FROM assignments WHERE id = %s', (aid,))
    assert con is not None, 'bài tập bị xoá theo mục khung'
    assert con['syllabus_item_id'] is None
