"""Địa chỉ lịch riêng: chìa, quyền và tuyến công khai — §71, 26/09/2026.

Chạy trên CSDL thật trong giao dịch cuộn lại; mọi phép đếm lọc về dữ liệu do chính
phép kiểm dựng ra (xem `RULES.md §5`), không đếm tổng bảng.
"""
import pytest
from django.test import Client

from common.db import q1, x
from lich import chia as chia_mod

pytestmark = pytest.mark.django_db(transaction=False)


def _nguoi(vai='Học viên', ten='Lịch Thử'):
    r = q1("INSERT INTO users (name, email, password, role, status) "
           "VALUES (%s, %s, 'x', %s, 'active') RETURNING id",
           (ten, 'lich.%s@example.com' % q1('SELECT gen_random_uuid() AS u')['u'], vai))
    return r['id']


def _the(uid):
    from rest_framework_simplejwt.tokens import AccessToken
    return str(AccessToken.for_user(type('U', (), {'id': uid, 'pk': uid})()))


def _lop_co_buoi(uid):
    """Một lớp có đúng một buổi, em `uid` đang học."""
    c = q1("INSERT INTO classes (name, status, created_at) "
           "VALUES ('Lớp lịch thử', 'active', now()) RETURNING id")
    x("INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, now())",
      (c['id'], uid))
    s = q1("INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status, created_at) "
           "VALUES (%s, now() + interval '2 days', 90, 'planned', now()) RETURNING id", (c['id'],))
    return c['id'], s['id']


# ── chìa ────────────────────────────────────────────────────────────────────

def test_chia_khong_luu_tho_trong_csdl():
    """Cột `token_hash` không được chứa chính chìa — nếu có, ai đọc được CSDL là
    mở được lịch của mọi người."""
    uid = _nguoi()
    chia = chia_mod.cap(uid)
    r = q1('SELECT token_hash FROM calendar_links WHERE user_id = %s', (uid,))
    assert chia not in r['token_hash']
    assert len(r['token_hash']) == 64          # SHA-256 dạng hex


def test_cap_lai_thu_hoi_chia_cu():
    uid = _nguoi()
    cu = chia_mod.cap(uid)
    moi = chia_mod.cap(uid)
    assert cu != moi
    assert chia_mod.tra(cu) is None            # chìa cũ chết ngay
    assert chia_mod.tra(moi)['user_id'] == uid
    song = q1('SELECT count(*) AS n FROM calendar_links '
              'WHERE user_id = %s AND revoked_at IS NULL', (uid,))
    assert song['n'] == 1


def test_chia_lam_va_chia_thu_hoi_khong_phan_biet_duoc():
    uid = _nguoi()
    chia = chia_mod.cap(uid)
    chia_mod.thu_hoi(uid)
    assert chia_mod.tra(chia) is None
    assert chia_mod.tra('chia-bia-dat') is None


# ── tuyến công khai ─────────────────────────────────────────────────────────

def test_tep_ics_tra_dung_kieu_va_co_buoi_cua_em():
    uid = _nguoi()
    _lop_co_buoi(uid)
    chia = chia_mod.cap(uid)
    r = Client().get('/lich/%s.ics' % chia)
    assert r.status_code == 200
    assert r['Content-Type'].startswith('text/calendar')
    vb = r.content.decode('utf-8')
    assert vb.startswith('BEGIN:VCALENDAR')
    assert 'Lớp lịch thử' in vb


def test_chia_lạ_tra_404_khong_lo_gi():
    r = Client().get('/lich/khong-he-co-chia-nay.ics')
    assert r.status_code == 404
    assert 'BEGIN:VCALENDAR' not in r.content.decode('utf-8')


def test_khong_xem_duoc_lop_minh_khong_hoc():
    """Chìa của em A không được mang buổi của lớp em A KHÔNG học."""
    a, b = _nguoi(), _nguoi()
    _lop_co_buoi(b)                              # lớp của em B
    vb = Client().get('/lich/%s.ics' % chia_mod.cap(a)).content.decode('utf-8')
    assert 'BEGIN:VEVENT' not in vb


def test_tai_khoan_bi_khoa_thi_lich_tat_theo():
    uid = _nguoi()
    _lop_co_buoi(uid)
    chia = chia_mod.cap(uid)
    assert Client().get('/lich/%s.ics' % chia).status_code == 200
    x("UPDATE users SET status = 'suspended' WHERE id = %s", (uid,))
    assert Client().get('/lich/%s.ics' % chia).status_code == 404


def test_lich_toan_trung_tam_chi_cho_hoc_vu_va_quan_tri():
    hv = _nguoi()
    c = Client()
    r = c.post('/api/lich/dia-chi', data={'scope': 'trung_tam'},
               content_type='application/json', HTTP_AUTHORIZATION='Bearer ' + _the(hv))
    assert r.status_code == 403

    hoc_vu = _nguoi('Quản lý học vụ')
    r = c.post('/api/lich/dia-chi', data={'scope': 'trung_tam'},
               content_type='application/json', HTTP_AUTHORIZATION='Bearer ' + _the(hoc_vu))
    assert r.status_code == 201
    assert r.json()['duongDan'].startswith('/lich/')


def test_hoc_vien_xin_pham_vi_la_thi_thanh_ca_nhan():
    """Gửi `scope` lạ không được âm thầm thành 'trung_tam'."""
    uid = _nguoi()
    r = Client().post('/api/lich/dia-chi', data={'scope': 'tất cả mọi thứ'},
                      content_type='application/json',
                      HTTP_AUTHORIZATION='Bearer ' + _the(uid))
    assert r.status_code == 201 and r.json()['scope'] == 'toi'


def test_chua_dang_nhap_thi_khong_cap_duoc_dia_chi():
    assert Client().post('/api/lich/dia-chi').status_code in (401, 403)
