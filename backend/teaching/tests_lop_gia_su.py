"""Tạo nhanh lớp gia sư (mục 1.2b, 24/09/2026) — `POST /api/admin/classes/gia-su`.

Một em + một giảng viên + lịch tuần → lớp `gia_su` + em vào lớp + buổi, trong MỘT
giao dịch. Đi qua VIEW THẬT, CSDL trong giao dịch cuộn lại (`conftest.py`); mỗi phép
kiểm lọc về dữ liệu của chính nó bằng tên riêng.
"""
import uuid
from datetime import timedelta

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.clock import local_today
from common.db import q, q1, x
from common.permissions import ROLE_ACADEMIC, ROLE_STUDENT, ROLE_TEACHER

f = APIRequestFactory()
pytestmark = pytest.mark.django_db


def _goi(body, ai):
    from teaching.lop_gia_su import TaoLopGiaSuView
    req = f.post('/x', body, format='json')
    force_authenticate(req, user=ai)
    return TaoLopGiaSuView.as_view()(req)


def _nguoi(ten, vai):
    r = q1('INSERT INTO users (name, email, password, role, streak) VALUES (%s, %s, %s, %s, 0) RETURNING id',
           (ten, 'lgs_%s@example.com' % uuid.uuid4().hex[:10], 'x', vai))
    return User.objects.get(id=r['id'])


@pytest.fixture
def canh():
    tt = 'LGS%s' % uuid.uuid4().hex[:6]
    # Từ Thứ 2 của tuần SAU NỮA, 4 tuần: không buổi nào rơi vào quá khứ. (Lễ cố định
    # nằm trong khoảng chỉ thêm cảnh báo, không bớt buổi — số buổi vẫn là 8.)
    hom_nay = local_today()
    tu = hom_nay + timedelta(days=14 - hom_nay.weekday())
    return {'tt': tt, 'hv': _nguoi('HocVu LGS', ROLE_ACADEMIC), 'gv': _nguoi('%s GV' % tt, ROLE_TEACHER),
            'em': _nguoi('%s Em' % tt, ROLE_STUDENT), 'tu': tu, 'den': tu + timedelta(days=27)}


def _than(canh, **them):
    return dict({'student_id': canh['em'].id, 'teacher_id': canh['gv'].id, 'generate': True,
                 'weekdays': [2, 4], 'start_time': '19:30', 'duration_minutes': 90,
                 'from': canh['tu'].isoformat(), 'to': canh['den'].isoformat()}, **them)


def _lop_cua(canh):
    return q("SELECT id, name, class_type, capacity, status, schedule, teacher_id FROM classes "
             "WHERE teacher_id = %s", (canh['gv'].id,))


def test_tao_that_mot_giao_dich_du_lop_em_buoi(canh):
    r = _goi(_than(canh), canh['hv'])
    assert r.status_code == 201, r.data
    lop = _lop_cua(canh)
    assert len(lop) == 1
    lop = lop[0]
    assert (lop['class_type'], lop['capacity'], lop['status']) == ('gia_su', 3, 'active')
    assert lop['name'] == 'Gia sư · %s Em · %s GV' % (canh['tt'], canh['tt']), lop['name']
    assert lop['schedule'] == 'T3, T5 · 19:30–21:00', lop['schedule']
    em = q('SELECT user_id FROM class_members WHERE class_id = %s AND left_at IS NULL', (lop['id'],))
    assert [e['user_id'] for e in em] == [canh['em'].id]
    so_buoi = q1('SELECT count(*) AS n FROM class_sessions WHERE class_id = %s', (lop['id'],))['n']
    assert so_buoi == 8 and r.data['sessions']['dem']['tao'] == 8, (so_buoi, r.data['sessions'])
    assert r.data['classId'] == lop['id'] and r.data['memberUserId'] == canh['em'].id


def test_xem_truoc_khong_ghi_gi(canh):
    nk_truoc = q1('SELECT count(*) AS n FROM admin_audit')['n']
    r = _goi(_than(canh, dry_run=True), canh['hv'])
    assert r.status_code == 200 and r.data['dryRun'] is True, r.data
    assert r.data['sessions']['dem']['tao'] == 8
    assert r.data['name'].startswith('Gia sư · ')
    assert _lop_cua(canh) == [], 'xem trước để lại lớp'
    assert q1('SELECT count(*) AS n FROM class_members WHERE user_id = %s', (canh['em'].id,))['n'] == 0
    assert q1('SELECT count(*) AS n FROM admin_audit')['n'] == nk_truoc, 'xem trước ghi nhật ký'


def test_chi_nhan_hoc_vien_va_phai_co_giang_vien(canh):
    r = _goi(_than(canh, student_id=canh['gv'].id), canh['hv'])
    assert r.status_code == 400 and 'không phải Học viên' in r.data['error'], r.data
    r = _goi(_than(canh, teacher_id=None), canh['hv'])
    assert r.status_code == 400 and 'giảng viên' in r.data['error'], r.data
    # Giảng viên "giả" (là học viên) — luật cũ của `_clean_class_payload` vẫn chặn.
    r = _goi(_than(canh, teacher_id=canh['em'].id), canh['hv'])
    assert r.status_code == 400, r.data
    assert _lop_cua(canh) == []


def test_loi_giua_chung_khong_de_lai_lop_mo_coi(canh, monkeypatch):
    """Sinh buổi hỏng SAU KHI lớp và em đã ghi → cả ba cuộn lại, không lớp thiếu lịch."""
    from teaching import lop_gia_su

    def hong(*a, **kw):
        raise RuntimeError('sinh buổi hỏng giữa chừng')

    monkeypatch.setattr(lop_gia_su, 'tao_buoi', hong)
    # `common.errors` bắt lỗi không lường trước → 500 có câu chữ (không ném ra ngoài view).
    assert _goi(_than(canh), canh['hv']).status_code == 500
    assert _lop_cua(canh) == [], 'lỗi giữa chừng để lại lớp mồ côi'
    assert q1('SELECT count(*) AS n FROM class_members WHERE user_id = %s', (canh['em'].id,))['n'] == 0


def test_vuot_tran_buoi_bao_loi_va_khong_ghi(canh):
    r = _goi(_than(canh, weekdays=[1, 2, 3, 4, 5, 6, 7], to=(canh['tu'] + timedelta(days=300)).isoformat()),
             canh['hv'])
    assert r.status_code == 400 and 'vượt trần' in r.data['error'], r.data
    assert _lop_cua(canh) == []


def test_giang_vien_trung_gio_lop_khac_canh_bao_nhung_van_tao(canh):
    lop_khac = q1("INSERT INTO classes (name, teacher_id, status) VALUES (%s, %s, 'active') RETURNING id",
                  ('%s Lop Khac' % canh['tt'], canh['gv'].id))['id']
    thu_ba = canh['tu'] + timedelta(days=1)
    x("INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status, created_at) "
      "VALUES (%s, %s, 90, 'planned', now())", (lop_khac, '%s 19:00' % thu_ba.isoformat()))
    r = _goi(_than(canh), canh['hv'])
    assert r.status_code == 201, r.data
    assert any('trùng giờ với lớp khác' in c for c in r.data['sessions']['canhBao']), r.data['sessions']
    dong = next(b for b in r.data['sessions']['buoi'] if b['ngay'] == thu_ba.isoformat())
    assert any(t['loai'] == 'giang-vien' for t in dong['trungLop']), dong


def test_lich_chu_doc_nguoc_lai_duoc():
    from datetime import time

    from teaching.lop_gia_su import lich_chu
    from teaching.sinh_buoi import doan_lich
    for thu, gio, phut in (([2, 4], time(19, 30), 90), ([6, 7], time(8, 0), 120), ([1], time(17, 45), 60)):
        chu = lich_chu({'thu': thu, 'gio': gio, 'phut': phut})
        assert doan_lich(chu) == (thu, gio.strftime('%H:%M'), phut), chu


def test_giang_vien_khong_tao_duoc(canh):
    r = _goi(_than(canh), canh['gv'])
    assert r.status_code == 403


def test_em_trung_gio_lop_khac_hien_ngay_o_xem_truoc(canh):
    """Em được ghi vào lớp TRƯỚC khi chấm buổi (cùng giao dịch) — nhờ vậy bản xem trước
    đã thấy "em đang học lớp khác đúng giờ ấy". Đảo thứ tự là mất cảnh báo này."""
    lop_khac = q1("INSERT INTO classes (name, status) VALUES (%s, 'active') RETURNING id",
                  ('%s Lop Em' % canh['tt'],))['id']
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, now())',
      (lop_khac, canh['em'].id))
    thu_nam = canh['tu'] + timedelta(days=3)
    x("INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status, created_at) "
      "VALUES (%s, %s, 90, 'planned', now())", (lop_khac, '%s 20:00' % thu_nam.isoformat()))
    r = _goi(_than(canh, dry_run=True), canh['hv'])
    assert r.status_code == 200, r.data
    dong = next(b for b in r.data['sessions']['buoi'] if b['ngay'] == thu_nam.isoformat())
    assert any(t['loai'] == 'hoc-vien' for t in (dong.get('trungLop') or [])), dong
