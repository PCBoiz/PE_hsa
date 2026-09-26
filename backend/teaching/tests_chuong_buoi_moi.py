"""CHUÔNG KHI LỚP CÓ BUỔI MỚI (bảng TopHSA dòng 27, ô *"Lịch học (buổi mới)"*).

Em đã nhận chuông khi lịch ĐỔI (`lich_doi`) và khi có buổi BÙ (`hoc_bu`). Nhưng buổi mới
thêm vào lịch thì không — mà đó lại là thứ hay xảy ra nhất: trung tâm xếp thêm buổi ôn
sát kỳ thi, giảng viên chèn một buổi chữa đề. Em chỉ biết nếu tự mở trang.

── VÌ SAO GỘP KHI SINH CẢ KỲ ─────────────────────────────────────────────────

"Sinh lịch cả kỳ" tạo một lượt hàng chục buổi. Bắn mỗi buổi một chuông là 12–30 chuông
trong một giây cho mỗi em — và cái chuông thứ hai đã đủ làm em thôi đọc chuông nữa. Nên
lượt sinh hàng loạt gửi MỘT chuông nói số buổi, còn tạo lẻ từng buổi thì nói đúng buổi ấy.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. Tạo MỘT buổi → em trong lớp nhận chuông nói ngày giờ buổi ấy.
  2. Sinh cả kỳ → MỘT chuông nói số buổi, không phải mỗi buổi một chuông.
  3. Em ĐÃ RỜI lớp không nhận.
  4. Buổi tạo ở trạng thái `cancelled` không báo (không ai cần biết về một buổi đã huỷ
     ngay lúc sinh ra).
  5. Chuông có `link` mở đúng chỗ xem lịch.

Chạy trên CSDL thật, giao dịch CUỘN LẠI; chỉ đếm dữ liệu của chính mình.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q, q1, x
from common.permissions import ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db


def _nguoi(ten, vai):
    r = q1("INSERT INTO users (name, email, password, role, streak) "
           "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
           (ten, '%s_bm@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=r['id'])


def _api(u):
    c = APIClient()
    c.force_authenticate(user=u)
    return c


@pytest.fixture
def canh():
    gv = _nguoi('GV Buoi Moi', ROLE_TEACHER)
    em = _nguoi('Em Buoi Moi', ROLE_STUDENT)
    roi = _nguoi('Em Da Roi Buoi Moi', ROLE_STUDENT)
    lop = q1("INSERT INTO classes (name, course_id, teacher_id, status, schedule) "
             "VALUES ('Lop buoi moi', 'hsa_quantitative', %s, 'active', 'Thứ 3, 5 · 19:30') "
             "RETURNING id", (gv.id,))['id']
    nay = local_now()
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s)',
      (lop, em.id, nay - timedelta(days=30)))
    x('INSERT INTO class_members (class_id, user_id, joined_at, left_at) VALUES (%s,%s,%s,%s)',
      (lop, roi.id, nay - timedelta(days=30), nay - timedelta(days=1)))
    return {'gv': gv, 'em': em, 'roi': roi, 'lop': lop, 'nay': nay}


def _chuong(uid, loai='buoi_moi'):
    return q('SELECT title, body, link, coalesce(coalesce_count, 1) AS gop '
             'FROM notifications WHERE user_id = %s AND type = %s ORDER BY id', (uid, loai))


def _tao_buoi(canh, lech_gio=48, **body):
    d = {'starts_at': (canh['nay'] + timedelta(hours=lech_gio)).strftime('%Y-%m-%dT%H:%M'),
         'duration_minutes': 90}
    d.update(body)
    return _api(canh['gv']).post('/api/teach/classes/%d/sessions' % canh['lop'], d, format='json')


# ── 1. Tạo một buổi ─────────────────────────────────────────────────────────

def test_tao_mot_buoi_thi_em_trong_lop_nhan_chuong(canh):
    r = _tao_buoi(canh)
    assert r.status_code in (200, 201), r.data
    ds = _chuong(canh['em'].id)
    assert len(ds) == 1, ds
    assert 'Lop buoi moi' in ds[0]['title'], ds[0]['title']


def test_em_da_roi_lop_khong_nhan(canh):
    _tao_buoi(canh)
    assert _chuong(canh['roi'].id) == []


def test_buoi_tao_o_trang_thai_huy_thi_khong_bao(canh):
    _tao_buoi(canh, status='cancelled')
    assert _chuong(canh['em'].id) == []


def test_chuong_co_link_mo_dung_cho(canh):
    _tao_buoi(canh)
    assert (_chuong(canh['em'].id)[0]['link'] or '').startswith('/')


# ── 2. Sinh cả kỳ → MỘT chuông ─────────────────────────────────────────────

def test_sinh_ca_ky_chi_mot_chuong_noi_so_buoi(canh):
    """Mỗi buổi một chuông là 12–30 chuông trong một giây, và cái thứ hai đã đủ làm em
    thôi đọc chuông nữa."""
    r = _api(canh['gv']).post('/api/teach/classes/%d/sessions/generate' % canh['lop'],
                              {'from': (canh['nay'] + timedelta(days=1)).date().isoformat(),
                               'to': (canh['nay'] + timedelta(days=28)).date().isoformat(),
                               'weekdays': [1, 3], 'start_time': '19:30',
                               'duration_minutes': 90},
                              format='json')
    assert r.status_code in (200, 201), r.data
    so_buoi = len(r.data.get('ids') or [])
    ds = _chuong(canh['em'].id)
    assert len(ds) == 1, 'sinh %d buổi mà bắn %d chuông' % (so_buoi, len(ds))
    if so_buoi > 1:
        assert str(so_buoi) in (ds[0]['title'] + ds[0]['body']), ds[0]
