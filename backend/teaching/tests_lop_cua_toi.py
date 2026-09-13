"""Lớp của tôi — `GET /api/lop-cua-toi`: học viên nhìn thấy lớp mình, buổi tới,
link phòng, chuyên cần của CHÍNH mình.

Chạy trên DB thật, giao dịch CUỘN LẠI. Đi qua URL thật.

── THỨ ĐANG ĐƯỢC CANH (anh Sơn chốt 14/09/2026) ─────────────────────────────

  1. Chỉ lớp em ĐANG học; em không ở lớp nào thì danh sách rỗng; em đã rời thì
     lớp ấy không hiện. Không có gì về em khác.
  2. Buổi tới = buổi chưa huỷ gần nhất từ bây giờ; link phòng của buổi, thiếu
     thì của lớp — cùng luật với "Việc hôm nay" của giảng viên.
  3. Chuyên cần đếm CÙNG hàm với tờ báo cáo phụ huynh (`_chuyen_can`) — em và bố
     mẹ nhìn cùng một con số.
  4. Ngày thi của lớp khác mục tiêu cá nhân thì nói ra (`ngayThiLech`), không
     tự đổi mục tiêu.
"""
from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q1, x
from common.permissions import ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db

LINK_LOP = 'https://meet.google.com/lop-cua-toi'


def _nguoi(ten, vai):
    row = q1("INSERT INTO users (name, email, password, role, streak) "
             "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
             (ten, '%s_lct@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=row['id'])


def _goi(ai):
    a = APIClient()
    if ai is not None:
        a.force_authenticate(user=ai)
    return a.get('/api/lop-cua-toi')


@pytest.fixture
def canh(db):
    gv = _nguoi('GV LCT', ROLE_TEACHER)
    em = _nguoi('Em LCT', ROLE_STUDENT)
    khac = _nguoi('Em Khac LCT', ROLE_STUDENT)
    ngoai = _nguoi('Em Ngoai LCT', ROLE_STUDENT)
    lop = q1("INSERT INTO classes (name, course_id, teacher_id, status, schedule, meeting_url, "
             "exam_date) VALUES ('Lop LCT', 'hsa_quantitative', %s, 'active', "
             "'Thứ 3, 5 · 19:30', %s, %s) RETURNING id",
             (gv.id, LINK_LOP, date(2026, 12, 6)))['id']
    nay = local_now()
    for u in (em, khac):
        x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, %s)',
          (lop, u.id, nay - timedelta(days=10)))
    return {'gv': gv, 'em': em, 'khac': khac, 'ngoai': ngoai, 'lop': lop, 'nay': nay}


def _buoi(lop, lech_gio, status='planned', da_tick=False, link=None):
    bd = local_now() + timedelta(hours=lech_gio)
    return q1('INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status, '
              'meeting_url, attendance_taken_at) VALUES (%s, %s, 90, %s, %s, %s) RETURNING id',
              (lop, bd, status, link, bd if da_tick else None))['id']


# ── 1. Ai thấy gì ───────────────────────────────────────────────────────────

def test_chi_lop_dang_hoc_cua_chinh_minh(canh):
    assert _goi(None).status_code == 401
    assert _goi(canh['ngoai']).json()['lop'] == []
    d = _goi(canh['em']).json()
    assert [l['id'] for l in d['lop']] == [canh['lop']]
    l = d['lop'][0]
    assert l['teacherName'] == 'GV LCT' and l['schedule'] == 'Thứ 3, 5 · 19:30'
    assert l['examDate'] == '2026-12-06'
    # Không rò gì về em khác.
    assert 'Em Khac' not in str(d)
    # Rời lớp thì hết.
    x('UPDATE class_members SET left_at=%s WHERE user_id=%s', (canh['nay'], canh['em'].id))
    assert _goi(canh['em']).json()['lop'] == []


# ── 2. Buổi tới + link phòng ────────────────────────────────────────────────

def test_buoi_toi_va_link_phong(canh):
    _buoi(canh['lop'], -48)                       # đã qua
    _buoi(canh['lop'], 2, status='cancelled')     # huỷ → bỏ
    toi = _buoi(canh['lop'], 5)                   # buổi tới, không link riêng → link lớp
    ke = _buoi(canh['lop'], 50, link='https://meet.google.com/rieng')
    _buoi(canh['lop'], 100)
    _buoi(canh['lop'], 150)                       # buổi thứ tư — ngoài 3
    l = _goi(canh['em']).json()['lop'][0]
    assert l['buoiToi']['sessionId'] == toi
    assert l['buoiToi']['meetingUrl'] == LINK_LOP
    assert l['buoiToi']['dangDienRa'] is False
    assert [b['sessionId'] for b in l['sapToi']][:2] == [toi, ke]
    assert len(l['sapToi']) == 3
    assert l['sapToi'][1]['meetingUrl'] == 'https://meet.google.com/rieng'


def test_buoi_dang_dien_ra_van_la_buoi_toi(canh):
    dang = _buoi(canh['lop'], -0.5)
    l = _goi(canh['em']).json()['lop'][0]
    assert l['buoiToi']['sessionId'] == dang and l['buoiToi']['dangDienRa'] is True


def test_khong_co_buoi_nao_thi_buoi_toi_null(canh):
    l = _goi(canh['em']).json()['lop'][0]
    assert l['buoiToi'] is None and l['sapToi'] == []


# ── 3. Chuyên cần của chính em, cùng hàm với tờ báo cáo phụ huynh ──────────

def test_chuyen_can_dem_nhu_bao_cao_phu_huynh(canh):
    from teaching.parent_report import _chuyen_can
    b1 = _buoi(canh['lop'], -72, da_tick=True)
    b2 = _buoi(canh['lop'], -48, da_tick=True)
    _buoi(canh['lop'], -24)                        # đã qua, chưa tick → không đếm
    x("INSERT INTO attendance (session_id, user_id, status) VALUES (%s, %s, 'present'), "
      "(%s, %s, 'absent')", (b1, canh['em'].id, b2, canh['em'].id))
    # Em khác có mặt cả hai — không được lẫn vào số của em.
    x("INSERT INTO attendance (session_id, user_id, status) VALUES (%s, %s, 'present'), "
      "(%s, %s, 'present')", (b1, canh['khac'].id, b2, canh['khac'].id))
    cc = _goi(canh['em']).json()['lop'][0]['chuyenCan']
    assert (cc['present'], cc['absent'], cc['sessionsCounted']) == (1, 1, 2), cc
    assert cc['attendedPct'] == 50
    goc = _chuyen_can(canh['lop'], canh['em'].id,
                      (canh['nay'] - timedelta(days=10)).date(), canh['nay'].date(),
                      cac_dot=[(canh['nay'] - timedelta(days=10), None)])
    assert cc == goc


# ── 4. Ngày thi lệch mục tiêu cá nhân ──────────────────────────────────────

def test_ngay_thi_lech_muc_tieu(canh):
    d = _goi(canh['em']).json()
    assert d['mucTieu']['examDate'] is None
    assert d['lop'][0]['ngayThiLech'] is False, 'chưa có mục tiêu thì không có gì để lệch'
    x("INSERT INTO surveys (user_id, data_json, created_at) VALUES (%s, %s, %s)",
      (canh['em'].id, '{"exam_date": "2027-03-15"}', canh['nay'].isoformat()))
    d = _goi(canh['em']).json()
    assert d['mucTieu']['examDate'] == '2027-03-15'
    assert d['lop'][0]['ngayThiLech'] is True
    x("UPDATE surveys SET data_json=%s WHERE user_id=%s", ('{"exam_date": "2026-12-06"}', canh['em'].id))
    assert _goi(canh['em']).json()['lop'][0]['ngayThiLech'] is False
