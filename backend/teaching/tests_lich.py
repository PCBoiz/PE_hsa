"""LỊCH HỌC NÂNG CẤP (§53, 23/09/2026): trùng lịch giữa các lớp, hình thức + phòng,
báo đổi lịch cho học viên, lịch gộp theo phạm vi người xem.

Đi qua VIEW THẬT (`ClassSessionsView`, `ClassSessionDetailView`, `LichView`) —
chuông và thư phải do chính đường sửa buổi sinh ra. Thư ở CHẾ ĐỘ THỬ (`.eml` vào
thư mục tạm). Chạy trên DB production trong giao dịch cuộn lại (`conftest.py`).
"""
import datetime

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.clock import local_now
from common.db import q, q1
from common.permissions import ROLE_ACADEMIC, ROLE_STUDENT, ROLE_TEACHER

f = APIRequestFactory()


def _goi(view, method, body=None, ai=None, qs='', **kw):
    duong = '/x' + qs
    req = getattr(f, method)(duong, body, format='json') if body is not None else getattr(f, method)(duong)
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(ten, vai, email=True):
    r = q1('INSERT INTO users (name, email, password, role, streak) VALUES (%s, %s, %s, %s, 0) RETURNING id',
           (ten, ('%s_lt@example.com' % ten.replace(' ', '_').lower()) if email else None, 'x', vai))
    return User.objects.get(id=r['id'])


def _lop(ten, gv, mode=None, room=None):
    return q1("INSERT INTO classes (name, course_id, teacher_id, status, mode, room) "
              "VALUES (%s, 'hsa_quantitative', %s, 'active', %s, %s) RETURNING id",
              (ten, gv.id, mode, room))['id']


def _vao(lop, em, luc=None, roi=None):
    q1('INSERT INTO class_members (class_id, user_id, joined_at, left_at) VALUES (%s, %s, %s, %s) RETURNING id',
       (lop, em.id, luc or local_now() - datetime.timedelta(days=30), roi))


def _buoi(lop, luc, phut=90, **kw):
    return q1('INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status, mode, room) '
              'VALUES (%s, %s, %s, %s, %s, %s) RETURNING id',
              (lop, luc, phut, kw.get('status', 'planned'), kw.get('mode'), kw.get('room')))['id']


def _iso(dt):
    return dt.strftime('%Y-%m-%dT%H:%M')


@pytest.fixture
def canh(db, tmp_path, monkeypatch):
    from teaching import bao_doi_lich
    monkeypatch.setenv('EMAIL_CHE_DO_THU', '1')
    monkeypatch.setenv('EMAIL_THU_MUC_THU', str(tmp_path))
    monkeypatch.setattr(bao_doi_lich, 'GUI_NGAY', True)
    gv1, gv2 = _nguoi('GV1 LT', ROLE_TEACHER), _nguoi('GV2 LT', ROLE_TEACHER)
    hocvu = _nguoi('HocVu LT', ROLE_ACADEMIC)
    em1, em2, em3 = _nguoi('Em1 LT', ROLE_STUDENT), _nguoi('Em2 LT', ROLE_STUDENT), _nguoi('Em3 LT', ROLE_STUDENT)
    a = _lop('Lop A LT', gv1, mode='offline', room='P201')
    b = _lop('Lop B LT', gv1, mode='online')
    c = _lop('Lop C LT', gv2, mode='offline', room=' p201 ')
    _vao(a, em1)
    _vao(a, em2)
    _vao(a, em3, roi=local_now() - datetime.timedelta(days=1))    # đã rời lớp A
    _vao(c, em1)
    luc = (local_now() + datetime.timedelta(days=2)).replace(hour=19, minute=0, second=0, microsecond=0)
    a1 = _buoi(a, luc)
    return {'gv1': gv1, 'gv2': gv2, 'hocvu': hocvu, 'em1': em1, 'em2': em2, 'em3': em3,
            'a': a, 'b': b, 'c': c, 'a1': a1, 'luc': luc, 'thu': tmp_path}


def _tao(canh, lop, luc, ai, **them):
    from teaching.sessions import ClassSessionsView
    return _goi(ClassSessionsView, 'post', dict({'starts_at': _iso(luc), 'duration_minutes': 90}, **them),
                ai=ai, class_id=lop)


# ── Trùng lịch giữa các lớp ─────────────────────────────────────────────────

def test_trung_giang_vien_o_lop_khac(canh):
    r = _tao(canh, canh['b'], canh['luc'] + datetime.timedelta(minutes=30), canh['gv1'])
    assert r.status_code == 201, r.data
    loai = {t['loai'] for t in r.data['conflicts']}
    assert 'giang-vien' in loai, r.data['conflicts']
    assert 'giảng viên đang dạy lớp Lop A LT' in r.data['warning']


def test_trung_hoc_vien_va_phong(canh):
    r = _tao(canh, canh['c'], canh['luc'], canh['gv2'])
    assert r.status_code == 201, r.data
    ds = {t['loai']: t for t in r.data['conflicts']}
    assert ds['hoc-vien']['soEm'] == 1 and ds['hoc-vien']['tenEm'] == ['Em1 LT']
    # Phòng so KHÔNG phân biệt hoa thường / khoảng trắng: "P201" với " p201 ".
    assert 'phong' in ds, r.data['conflicts']
    assert 'giang-vien' not in ds, 'GV2 không dạy lớp A — không được báo trùng giảng viên'


def test_buoi_da_huy_khong_chiem_gio(canh):
    q1("UPDATE class_sessions SET status='cancelled' WHERE id=%s RETURNING id", (canh['a1'],))
    r = _tao(canh, canh['b'], canh['luc'], canh['gv1'])
    assert r.data['conflicts'] == [] and 'Trùng lịch' not in (r.data.get('warning') or '')


def test_khong_chong_gio_thi_khong_bao(canh):
    r = _tao(canh, canh['b'], canh['luc'] + datetime.timedelta(hours=2), canh['gv1'])
    assert r.data['conflicts'] == []


def test_doi_sang_phong_dang_co_lop_cung_bao_trung(canh):
    from teaching.sessions import ClassSessionDetailView
    c1 = _buoi(canh['c'], canh['luc'] + datetime.timedelta(days=7), mode='online')   # buổi C online
    a2 = _buoi(canh['a'], canh['luc'] + datetime.timedelta(days=7), mode='online')   # buổi A online cùng giờ
    # Đổi c1 về offline (phòng lớp C = p201) trong khi a2 vẫn online → chưa trùng phòng.
    r = _goi(ClassSessionDetailView, 'patch', {'mode': 'offline'}, ai=canh['gv2'], session_id=c1)
    assert 'phong' not in {t['loai'] for t in r.data['conflicts']}
    q1("UPDATE class_sessions SET mode='offline' WHERE id=%s RETURNING id", (a2,))
    r = _goi(ClassSessionDetailView, 'patch', {'room': 'P201'}, ai=canh['gv2'], session_id=c1)
    assert 'phong' in {t['loai'] for t in r.data['conflicts']}, r.data


# ── Hình thức + phòng: buổi để trống = theo lớp ─────────────────────────────

def test_buoi_ke_thua_hinh_thuc_va_phong_cua_lop(canh):
    r = _tao(canh, canh['a'], canh['luc'] + datetime.timedelta(days=10), canh['gv1'])
    s = r.data['session']
    assert (s['mode'], s['room']) == (None, None)
    assert (s['modeHieuLuc'], s['roomHieuLuc']) == ('offline', 'P201')
    r = _tao(canh, canh['a'], canh['luc'] + datetime.timedelta(days=11), canh['gv1'], room='P305')
    assert r.data['session']['roomHieuLuc'] == 'P305'
    r = _tao(canh, canh['a'], canh['luc'] + datetime.timedelta(days=12), canh['gv1'], mode='bay')
    assert r.status_code == 400


# ── Báo đổi lịch ────────────────────────────────────────────────────────────

def _chuong(uid):
    return q("SELECT title, body FROM notifications WHERE user_id=%s AND type='lich_doi' ORDER BY id", (uid,))


def test_doi_gio_buoi_sap_toi_bao_chuong_va_thu_cho_em_dang_hoc(canh):
    from teaching.sessions import ClassSessionDetailView
    moi = canh['luc'] + datetime.timedelta(days=1)
    r = _goi(ClassSessionDetailView, 'patch', {'starts_at': _iso(moi)}, ai=canh['gv1'], session_id=canh['a1'])
    assert r.status_code == 200 and r.data['daBao'] == 2, r.data
    for em in (canh['em1'], canh['em2']):
        c = _chuong(em.id)
        assert len(c) == 1 and 'dời buổi' in c[0]['title'] and 'Lop A LT' in c[0]['title']
    assert _chuong(canh['em3'].id) == [], 'em đã rời lớp không được báo'
    assert _chuong(canh['gv1'].id) == [], 'không báo giảng viên'
    thu = list(canh['thu'].glob('*.eml'))
    assert len(thu) == 2, [t.name for t in thu]


def test_em_tat_email_chi_co_chuong(canh):
    from teaching.sessions import ClassSessionDetailView
    q1('INSERT INTO notification_settings (user_id, email_notif) VALUES (%s, 0) '
       'ON CONFLICT (user_id) DO UPDATE SET email_notif = 0 RETURNING user_id', (canh['em2'].id,))
    _goi(ClassSessionDetailView, 'patch', {'starts_at': _iso(canh['luc'] + datetime.timedelta(hours=3))},
         ai=canh['gv1'], session_id=canh['a1'])
    assert len(_chuong(canh['em2'].id)) == 1
    assert [t.name for t in canh['thu'].glob('*.eml')] == [t.name for t in canh['thu'].glob('em1*.eml')]


def test_sua_chu_de_hay_buoi_da_qua_thi_khong_bao(canh):
    from teaching.sessions import ClassSessionDetailView
    r = _goi(ClassSessionDetailView, 'patch', {'topic': 'Ôn tập'}, ai=canh['gv1'], session_id=canh['a1'])
    assert r.data['daBao'] == 0 and _chuong(canh['em1'].id) == []
    cu = _buoi(canh['a'], local_now() - datetime.timedelta(days=3))
    r = _goi(ClassSessionDetailView, 'patch', {'starts_at': _iso(local_now() - datetime.timedelta(days=2))},
             ai=canh['gv1'], session_id=cu)
    assert r.data['daBao'] == 0 and _chuong(canh['em1'].id) == []


def test_huy_va_xoa_buoi_sap_toi_deu_bao_huy(canh):
    from teaching.sessions import ClassSessionDetailView
    r = _goi(ClassSessionDetailView, 'patch', {'status': 'cancelled'}, ai=canh['gv1'], session_id=canh['a1'])
    assert r.data['daBao'] == 2 and 'đã huỷ' in _chuong(canh['em1'].id)[-1]['title']
    b2 = _buoi(canh['a'], canh['luc'] + datetime.timedelta(days=5))
    hv = canh['hocvu']
    r = _goi(ClassSessionDetailView, 'delete', ai=hv, session_id=b2)
    assert r.status_code == 200 and r.data['daBao'] == 2


def test_doi_phong_bao_noi_hoc_moi(canh):
    from teaching.sessions import ClassSessionDetailView
    r = _goi(ClassSessionDetailView, 'patch', {'room': 'P305'}, ai=canh['gv1'], session_id=canh['a1'])
    assert r.data['daBao'] == 2
    assert 'phòng P305' in _chuong(canh['em1'].id)[-1]['title']


# ── Lịch gộp ────────────────────────────────────────────────────────────────

def _lich(canh, ai, qs=''):
    from teaching.lich import LichView
    tu = canh['luc'].date() - datetime.timedelta(days=1)
    den = canh['luc'].date() + datetime.timedelta(days=1)
    return _goi(LichView, 'get', ai=ai, qs='?tu=%s&den=%s%s' % (tu, den, qs))


def test_lich_theo_pham_vi_nguoi_xem(canh):
    b1 = _buoi(canh['b'], canh['luc'] + datetime.timedelta(minutes=30))
    c1 = _buoi(canh['c'], canh['luc'] + datetime.timedelta(hours=4))
    thay_gv1 = {x['id'] for x in _lich(canh, canh['gv1']).data['buoi']}
    assert {canh['a1'], b1} <= thay_gv1 and c1 not in thay_gv1
    thay_hv = {x['id'] for x in _lich(canh, canh['hocvu']).data['buoi']}
    assert {canh['a1'], b1, c1} <= thay_hv
    # Cờ trùng giảng viên: a1 và b1 cùng GV1, chồng giờ.
    ds = {x['id']: x for x in _lich(canh, canh['hocvu']).data['buoi']}
    assert ds[canh['a1']]['trungGiangVien'] and ds[b1]['trungGiangVien'] and not ds[c1]['trungGiangVien']
    # Lọc theo giảng viên và theo lớp.
    assert {x['id'] for x in _lich(canh, canh['hocvu'], '&giang_vien=%s' % canh['gv2'].id).data['buoi']} == {c1}
    assert {x['id'] for x in _lich(canh, canh['hocvu'], '&lop=%s' % canh['b']).data['buoi']} == {b1}


def test_lich_cua_mot_em_tinh_theo_thoi_diem_buoi_hoc(canh):
    c1 = _buoi(canh['c'], canh['luc'] + datetime.timedelta(hours=4))
    r = _lich(canh, canh['hocvu'], '&hoc_vien=%s' % canh['em1'].id)
    assert {x['id'] for x in r.data['buoi']} >= {canh['a1'], c1}
    assert r.data['hocVien']['ten'] == 'Em1 LT'
    # em3 đã rời lớp A hôm qua → buổi A ngày kia KHÔNG còn là lịch của em.
    assert canh['a1'] not in {x['id'] for x in _lich(canh, canh['hocvu'], '&hoc_vien=%s' % canh['em3'].id).data['buoi']}


def test_lich_hinh_thuc_phong_hieu_luc_va_khoang_ngay(canh):
    ds = {x['id']: x for x in _lich(canh, canh['gv1']).data['buoi']}
    assert (ds[canh['a1']]['hinhThuc'], ds[canh['a1']]['phong']) == ('offline', 'P201')
    from teaching.lich import LichView
    assert _goi(LichView, 'get', ai=canh['gv1'], qs='?tu=2026-01-01&den=2026-06-01').status_code == 400
    assert _goi(LichView, 'get', ai=canh['em1']).status_code == 403


# ── Sinh lịch cả kỳ: trùng với lớp khác cảnh báo TỪNG DÒNG, vẫn tạo ─────────

def _sinh(canh, lop, ai, **them):
    from teaching.sinh_buoi import GenerateSessionsView
    d = canh['luc'].date()
    return _goi(GenerateSessionsView, 'post',
                dict({'weekdays': [d.isoweekday()], 'start_time': '19:00', 'duration_minutes': 90,
                      'from': d.isoformat(), 'to': (d + datetime.timedelta(days=7)).isoformat()}, **them),
                ai=ai, class_id=lop)


def test_sinh_lich_bao_trung_lop_khac_tung_dong_van_tao(canh):
    d = canh['luc'].date()
    r = _sinh(canh, canh['c'], canh['gv2'])
    assert r.status_code == 201, r.data
    assert len(r.data['ids']) == 2, 'trùng lớp khác chỉ CẢNH BÁO — không được bỏ buổi'
    dong = {b['ngay']: b for b in r.data['buoi']}
    dau, sau = dong[d.isoformat()], dong[(d + datetime.timedelta(days=7)).isoformat()]
    assert {t['loai'] for t in dau['trungLop']} == {'hoc-vien', 'phong'}, dau
    assert 'phòng p201 (lớp Lop A LT)' in dau['canhBao'] and '1 em học lớp Lop A LT' in dau['canhBao']
    assert 'trungLop' not in sau and not sau['canhBao']
    assert any(w.startswith('1 buổi trùng giờ với lớp khác') for w in r.data['canhBao'])


def test_sinh_lich_trung_giang_vien_va_buoi_huy_khong_tinh(canh):
    d = canh['luc'].date().isoformat()
    r = _sinh(canh, canh['b'], canh['gv1'], dry_run=True)
    assert [t['loai'] for t in {b['ngay']: b for b in r.data['buoi']}[d]['trungLop']] == ['giang-vien']
    q1("UPDATE class_sessions SET status='cancelled' WHERE id=%s RETURNING id", (canh['a1'],))
    r = _sinh(canh, canh['b'], canh['gv1'], dry_run=True)
    assert all('trungLop' not in b for b in r.data['buoi']), r.data['buoi']
