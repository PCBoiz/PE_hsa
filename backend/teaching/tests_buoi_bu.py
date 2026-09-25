"""Buổi bù — kế hoạch v2 V-g (bảng TopHSA dòng 10 "tạo lịch học bù").

`class_sessions.makeup_for` trỏ buổi gốc + `session_participants` (§62e). Danh sách của
một buổi = người tham gia nếu có, không thì cả lớp. Chạy trên DB thật, giao dịch CUỘN
LẠI (`conftest.py`); thư không gửi thật. Đi qua URL thật.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. Tạo buổi bù từ một buổi: chỉ những em được chọn (đang học lớp) vào buổi ấy, và
     chỉ các em ấy nhận chuông + thư "học bù" — SAU KHI lưu xong.
  2. Sổ điểm danh buổi bù chỉ có các em ấy; tick em khác bị bỏ qua.
  3. Buổi bù không vào chuyên cần / "chưa điểm danh" / "buổi tới" của em KHÔNG tham gia.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q, q1, x
from common.permissions import ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db


def _nguoi(ten, vai):
    row = q1("INSERT INTO users (name, email, password, role, streak) "
             "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
             (ten, '%s_bb@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=row['id'])


def _api(ai):
    a = APIClient()
    if ai is not None:
        a.force_authenticate(user=ai)
    return a


def _luc(gio):
    return (local_now() + timedelta(hours=gio)).replace(microsecond=0).isoformat()


@pytest.fixture
def thu(monkeypatch):
    from notifications import gui as mo_dun
    da_gui = []
    monkeypatch.setattr(mo_dun, 'GUI_NGAY', True)
    monkeypatch.setattr(mo_dun.mail, 'gui',
                        lambda den, tieu_de, chu: (da_gui.append((den, tieu_de, chu)) or (True, 'x', None)))
    return da_gui


@pytest.fixture
def canh(db):
    gv = _nguoi('GV BB', ROLE_TEACHER)
    gv_khac = _nguoi('GV Khac BB', ROLE_TEACHER)
    tg = _nguoi('TG BB', ROLE_ASSISTANT)
    an, binh, chau = (_nguoi(t, ROLE_STUDENT) for t in ('An BB', 'Binh BB', 'Chau BB'))
    ngoai = _nguoi('Ngoai BB', ROLE_STUDENT)
    lop = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
             "VALUES ('Lop BB', 'hsa_quantitative', %s, 'active') RETURNING id", (gv.id,))['id']
    for u in (an, binh, chau, tg):
        x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, %s)',
          (lop, u.id, local_now() - timedelta(days=20)))
    goc = q1("INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status, topic) "
             "VALUES (%s, %s, 90, 'planned', 'Tỉ lệ') RETURNING id",
             (lop, local_now() - timedelta(days=2)))['id']
    return {'gv': gv, 'gv_khac': gv_khac, 'tg': tg, 'an': an, 'binh': binh, 'chau': chau,
            'ngoai': ngoai, 'lop': lop, 'goc': goc}


def _tao_bu(ai, canh, uids, gio=48, **them):
    body = {'starts_at': _luc(gio), 'duration_minutes': 60, 'user_ids': [u.id for u in uids]}
    body.update(them)
    return _api(ai).post('/api/teach/sessions/%d/buoi-bu' % canh['goc'], body, format='json')


def _chuong_hoc_bu(u):
    return q("SELECT ref_type, ref_id FROM notifications WHERE user_id = %s AND type = 'hoc_bu'", (u.id,))


# ── 1. Tạo buổi bù ──────────────────────────────────────────────────────────

def test_tao_buoi_bu_chi_em_duoc_chon_va_bao_sau_khi_luu(canh, thu, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        r = _tao_bu(canh['gv'], canh, [canh['an'], canh['chau']])
    assert r.status_code == 201, r.json()
    bu = r.json()['id']
    s = q1('SELECT class_id, makeup_for, status, topic FROM class_sessions WHERE id = %s', (bu,))
    assert (s['class_id'], s['makeup_for'], s['status']) == (canh['lop'], canh['goc'], 'planned')
    assert 'Tỉ lệ' in (s['topic'] or ''), s
    assert {r['user_id'] for r in q('SELECT user_id FROM session_participants WHERE session_id = %s',
                                    (bu,))} == {canh['an'].id, canh['chau'].id}
    assert r.json()['session']['makeupFor'] == canh['goc']
    for u in (canh['an'], canh['chau']):
        assert _chuong_hoc_bu(u) == [{'ref_type': 'class_session', 'ref_id': bu}]
    assert _chuong_hoc_bu(canh['binh']) == []
    nhan = {den for den, _, _ in thu}
    assert nhan == {canh['an'].email, canh['chau'].email}, nhan
    # Trợ giảng tạo được (như tạo một buổi thường).
    assert _tao_bu(canh['tg'], canh, [canh['binh']], gio=72).status_code == 201


def test_cua_chan_va_dau_vao(canh):
    assert _tao_bu(canh['an'], canh, [canh['an']]).status_code == 403
    assert _tao_bu(canh['gv_khac'], canh, [canh['an']]).status_code == 404
    truoc = q1('SELECT COUNT(*) AS n FROM class_sessions WHERE class_id = %s', (canh['lop'],))['n']
    for uids, them in (([], {}), ([canh['ngoai']], {}), ([canh['tg']], {}),
                       ([canh['an']], {'starts_at': ''})):
        r = _tao_bu(canh['gv'], canh, uids, **them)
        assert r.status_code == 400, (uids, them, r.json())
    assert q1('SELECT COUNT(*) AS n FROM class_sessions WHERE class_id = %s', (canh['lop'],))['n'] == truoc


# ── 2. Sổ điểm danh buổi bù ─────────────────────────────────────────────────

def test_so_diem_danh_buoi_bu_chi_nguoi_tham_gia(canh):
    bu = _tao_bu(canh['gv'], canh, [canh['an'], canh['chau']], gio=-1).json()['id']
    g = _api(canh['tg']).get('/api/teach/sessions/%d/attendance' % bu).json()
    assert {s['userId'] for s in g['students']} == {canh['an'].id, canh['chau'].id}
    r = _api(canh['tg']).post('/api/teach/sessions/%d/attendance' % bu, {'marks': [
        {'user_id': canh['an'].id, 'status': 'present'},
        {'user_id': canh['binh'].id, 'status': 'present'}]}, format='json')
    assert r.status_code == 200 and r.json()['skipped'] == [canh['binh'].id], r.json()
    ds = {s['id']: s for s in _api(canh['gv']).get(
        '/api/teach/classes/%d/sessions' % canh['lop']).json()['sessions']}
    assert ds[bu]['attendance']['unmarked'] == 1, ds[bu]['attendance']
    assert ds[bu]['makeupFor'] == canh['goc'] and ds[bu]['soNguoiThamGia'] == 2
    assert ds[canh['goc']]['makeupFor'] is None and ds[canh['goc']]['soNguoiThamGia'] is None


# ── 3. Không làm sai số của em KHÔNG tham gia ───────────────────────────────

def test_buoi_bu_khong_vao_so_cua_em_khong_tham_gia(canh):
    bu = _tao_bu(canh['gv'], canh, [canh['an'], canh['chau']], gio=-3).json()['id']
    _api(canh['gv']).post('/api/teach/sessions/%d/attendance' % bu,
                          {'marks': [{'user_id': canh['an'].id, 'status': 'present'}]}, format='json')
    to = lambda u: _api(canh['gv']).get(  # noqa: E731
        '/api/teach/classes/%d/students/%d/parent-report' % (canh['lop'], u.id)).json()['attendance']
    assert to(canh['binh'])['sessionsTotal'] == 1, to(canh['binh'])     # chỉ buổi gốc
    assert to(canh['an'])['sessionsCounted'] == 1 and to(canh['an'])['present'] == 1
    assert to(canh['an'])['sessionsTotal'] == 2
    # Việc hôm nay: buổi bù còn thiếu đúng MỘT em (Châu), không phải hai.
    cdd = {b['sessionId']: b for b in _api(canh['gv']).get('/api/teach/viec-hom-nay').json()['chuaDiemDanh']['ds']}
    assert cdd[bu]['conThieu'] == 1, cdd[bu]


def test_buoi_toi_cua_hoc_vien_chi_khi_tham_gia(canh):
    bu = _tao_bu(canh['gv'], canh, [canh['an']], gio=5).json()['id']
    toi = lambda u: [b['sessionId'] for b in  # noqa: E731
                     _api(u).get('/api/lop-cua-toi').json()['lop'][0]['sapToi']]
    assert bu in toi(canh['an'])
    assert bu not in toi(canh['binh'])

    # Buổi bù bị HUỶ: chỉ em học bù thấy dòng "buổi đã huỷ" — em khác chưa từng có buổi ấy.
    x("UPDATE class_sessions SET status = 'cancelled' WHERE id = %s", (bu,))
    huy = lambda u: [b['sessionId'] for b in  # noqa: E731
                     _api(u).get('/api/lop-cua-toi').json()['lop'][0]['daHuy']]
    assert bu in huy(canh['an'])
    assert bu not in huy(canh['binh'])


def test_hoc_phi_va_so_diem_danh_csv_chi_tinh_em_tham_gia(canh):
    """Buổi bù của An không thành một buổi "đã mở" trong cơ sở học phí của Bình, và ô
    của Bình ở cột buổi bù trong sổ CSV là "—" (không phải ô trống "chưa tick")."""
    import csv
    import io
    from datetime import date
    hom_nay = date.today()
    dot = q1("INSERT INTO terms (name, starts_on, ends_on, status) VALUES ('Dot BB', %s, %s, 'active') "
             'RETURNING id', (hom_nay - timedelta(days=30), hom_nay + timedelta(days=30)))['id']
    x('UPDATE classes SET term_id = %s WHERE id = %s', (dot, canh['lop']))
    _tao_bu(canh['gv'], canh, [canh['an']], gio=-3)
    ad = _nguoi('AD BB', 'admin')
    lop = next(l for l in _api(ad).get('/api/admin/co-so-hoc-phi?term_id=%d' % dot).json()['lop']
               if l['id'] == canh['lop'])
    buoi = {e['userId']: e['buoiTrongKy'] for e in lop['hocVien']}
    assert (buoi[canh['an'].id], buoi[canh['binh'].id]) == (2, 1), buoi

    r = _api(canh['gv']).get('/api/teach/classes/%d/export/attendance.csv' % canh['lop'])
    assert r.status_code == 200
    dong = list(csv.reader(io.StringIO(r.content.decode('utf-8-sig'))))
    cot_bu = next(i for i, h in enumerate(dong[0]) if '(học bù)' in h)
    theo_ten = {d[0]: d for d in dong[1:]}
    assert theo_ten['Binh BB'][cot_bu] == '—' and theo_ten['An BB'][cot_bu] == ''
    chua = dong[0].index('Chưa điểm danh')
    assert (theo_ten['An BB'][chua], theo_ten['Binh BB'][chua]) == ('2', '1'), (theo_ten['An BB'], theo_ten['Binh BB'])


def test_doi_lich_buoi_bu_chi_bao_em_tham_gia_va_lich_cua_em(canh, thu):
    """Dời một buổi bù sắp tới: chỉ An (em của buổi) nhận chuông "đổi lịch". Lịch học
    lọc theo Bình không có buổi bù của An."""
    from teaching import bao_doi_lich as bdl
    bdl.GUI_NGAY = True
    try:
        bu = _tao_bu(canh['gv'], canh, [canh['an']], gio=30).json()['id']
        r = _api(canh['gv']).patch('/api/teach/sessions/%d' % bu, {'starts_at': _luc(54)}, format='json')
        assert r.status_code == 200 and r.json()['daBao'] == 1, r.json()
    finally:
        bdl.GUI_NGAY = False
    doi = lambda u: q("SELECT 1 FROM notifications WHERE user_id = %s AND type = 'lich_doi' "  # noqa: E731
                      "AND ref_id = %s", (u.id, bu))
    assert doi(canh['an']) and not doi(canh['binh'])
    lich = lambda u: {b['id'] for b in _api(canh['gv']).get(  # noqa: E731
        '/api/teach/lich?hoc_vien=%d&tu=%s&den=%s' % (u.id, (local_now() - timedelta(days=3)).date(),
                                                     (local_now() + timedelta(days=4)).date())).json()['buoi']}
    assert bu in lich(canh['an']) and bu not in lich(canh['binh'])
    assert canh['goc'] in lich(canh['binh'])
