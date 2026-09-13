"""Sinh buổi học hàng loạt theo lịch tuần + ngày nghỉ theo đợt học.

Chạy trên DB thật, trong giao dịch được CUỘN LẠI (xem `conftest.py`). Mọi lời
gọi đi qua URL thật. Ngày dùng năm 2031 để phép kiểm không đổi nghĩa theo ngày
chạy (buổi "tương lai" vẫn là tương lai) — trừ phép kiểm cờ `started`, vốn phải
tính quanh "bây giờ".

── THỨ ĐANG ĐƯỢC CANH (anh Sơn chốt 13/09/2026) ─────────────────────────────

  1. Giảng viên + học vụ + quản trị sinh được; trợ giảng KHÔNG (vẫn tạo từng
     buổi được như cũ). Giảng viên lớp khác nhận 404.
  2. Xem trước không ghi gì — kể cả nhật ký.
  3. Ngày nghỉ lưu THEO ĐỢT; học vụ khai, hệ thống gợi ý lễ dương lịch cố định.
     Tết và Giỗ Tổ theo âm lịch, ngày nghỉ bù do Nhà nước công bố từng năm —
     KHÔNG tự tính: đoán sai một ngày là cả lớp vào phòng học trống.
  4. Chạy lại không đẻ buổi trùng — người ta SẼ bấm hai lần.
  5. Buổi chưa tới không được làm sai số liệu: không tính là "đã mở" trong cơ
     sở học phí (xem `tests_co_so_hoc_phi.py`), và danh sách buổi nói rõ buổi
     nào chưa diễn ra.
"""
import json
from datetime import date, datetime, time, timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q, q1, x
from common.permissions import ROLE_ACADEMIC, ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db

NAM = 2031
_MUNG_1 = date(NAM, 9, 1)
#: Thứ Hai đầu tiên kể từ 01/09/2031 — mốc để tính Thứ 3 / Thứ 5 không ghim tay.
THU_HAI = _MUNG_1 + timedelta(days=(7 - _MUNG_1.weekday()) % 7)
LINK = 'https://meet.google.com/abc-defg-hij'


def _nguoi(ten, vai):
    row = q1("INSERT INTO users (name, email, password, role, streak) "
             "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
             (ten, '%s_sb@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=row['id'])


def _api(ai):
    a = APIClient()
    if ai is not None:
        a.force_authenticate(user=ai)
    return a


@pytest.fixture
def lop(db):
    gv = _nguoi('GV Sinh', ROLE_TEACHER)
    gv_khac = _nguoi('GV Khac Sinh', ROLE_TEACHER)
    hv = _nguoi('HV Sinh', ROLE_STUDENT)
    tg = _nguoi('TG Sinh', ROLE_ASSISTANT)
    hoc_vu = _nguoi('Hoc Vu Sinh', ROLE_ACADEMIC)
    dot = q1("INSERT INTO terms (name, starts_on, ends_on, status) "
             "VALUES (%s, %s, %s, 'active') RETURNING id",
             ('Dot thu sinh buoi', date(NAM, 8, 1), date(NAM, 12, 31)))['id']
    c = q1("INSERT INTO classes (name, course_id, teacher_id, status, schedule, meeting_url, term_id) "
           "VALUES ('Lop sinh buoi', 'hsa_quantitative', %s, 'active', %s, %s, %s) RETURNING id",
           (gv.id, 'Thứ 3, 5 · 19:30–21:00', LINK, dot))['id']
    nay = local_now()
    for u in (hv, tg):
        x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, %s)',
          (c, u.id, nay - timedelta(days=3)))
    return {'id': c, 'dot': dot, 'gv': gv, 'gv_khac': gv_khac, 'hv': hv, 'tg': tg,
            'hoc_vu': hoc_vu}


def _sinh(ai, class_id, **sua):
    body = {'weekdays': [2, 4], 'start_time': '19:30', 'duration_minutes': 90,
            'from': THU_HAI.isoformat(), 'to': (THU_HAI + timedelta(days=13)).isoformat(),
            'dry_run': False}
    body.update(sua)
    return _api(ai).post(f'/api/teach/classes/{class_id}/sessions/generate', body, format='json')


def _goi_y(ai, class_id):
    return _api(ai).get(f'/api/teach/classes/{class_id}/sessions/generate')


def _so_buoi(class_id):
    return q1('SELECT COUNT(*) AS n FROM class_sessions WHERE class_id=%s', (class_id,))['n']


def _so_nhat_ky():
    return q1('SELECT COUNT(*) AS n FROM admin_audit')['n']


def _ngay(*cach_thu_hai):
    return [(THU_HAI + timedelta(days=n)).isoformat() for n in cach_thu_hai]


def _chi_tiet(nk):
    return json.loads(nk['detail']) if isinstance(nk['detail'], str) else nk['detail']


# ── 1. Ai được sinh ─────────────────────────────────────────────────────────

def test_ai_duoc_sinh_hang_loat(lop):
    assert _sinh(None, lop['id'], dry_run=True).status_code == 401
    assert _sinh(lop['hv'], lop['id'], dry_run=True).status_code == 403, 'học viên'
    r = _sinh(lop['tg'], lop['id'], dry_run=True)
    assert r.status_code == 403, 'trợ giảng sinh hàng loạt được'
    assert 'Trợ giảng' in str(r.json()), r.json()
    assert _sinh(lop['gv_khac'], lop['id'], dry_run=True).status_code == 404
    assert _sinh(lop['gv'], lop['id'], dry_run=True).status_code == 200
    assert _sinh(lop['hoc_vu'], lop['id'], dry_run=True).status_code == 200


def test_tro_giang_mo_duoc_goi_y_va_duoc_bao_truoc_la_khong_sinh_duoc(lop):
    """Gợi ý chỉ có lịch lớp và ngày nghỉ — không có gì riêng tư. Trả cờ để màn
    hình KHÔNG dựng một nút mà bấm vào mới biết là không được phép."""
    g = _goi_y(lop['tg'], lop['id'])
    assert g.status_code == 200, g.json()
    assert g.json()['coTheSinh'] is False
    assert _goi_y(lop['gv'], lop['id']).json()['coTheSinh'] is True
    assert _goi_y(lop['gv_khac'], lop['id']).status_code == 404


# ── 2. Xem trước không ghi gì ───────────────────────────────────────────────

def test_xem_truoc_khong_ghi_gi(lop):
    truoc, truoc_nk = _so_buoi(lop['id']), _so_nhat_ky()
    r = _sinh(lop['gv'], lop['id'], dry_run=True)
    assert r.status_code == 200, r.json()
    d = r.json()
    assert d['dryRun'] is True
    assert d['dem']['tao'] == 4, d['dem']
    assert [b['ngay'] for b in d['buoi'] if b['trangThai'] == 'tao'] == _ngay(1, 3, 8, 10)
    assert _so_buoi(lop['id']) == truoc
    assert _so_nhat_ky() == truoc_nk


# ── Sinh thật ───────────────────────────────────────────────────────────────

def test_sinh_that_dung_gio_ke_thua_link_va_ghi_nhat_ky(lop):
    r = _sinh(lop['gv'], lop['id'])
    assert r.status_code == 201, r.json()
    rows = q('SELECT id, starts_at, duration_minutes, status, meeting_url, created_by '
             'FROM class_sessions WHERE class_id=%s ORDER BY starts_at', (lop['id'],))
    assert [b['starts_at'] for b in rows] == [
        datetime.combine(THU_HAI + timedelta(days=n), time(19, 30)) for n in (1, 3, 8, 10)]
    assert {b['status'] for b in rows} == {'planned'}
    # Kế thừa link phòng của lớp — cùng luật với tạo từng buổi.
    assert {b['meeting_url'] for b in rows} == {LINK}
    assert {b['duration_minutes'] for b in rows} == {90}
    assert {b['created_by'] for b in rows} == {lop['gv'].id}

    nk = q1("SELECT target_type, target_id, detail FROM admin_audit "
            "WHERE action='session.generate' ORDER BY id DESC LIMIT 1")
    assert nk is not None, 'sinh 4 buổi mà nhật ký không có dòng nào'
    assert (nk['target_type'], nk['target_id']) == ('class', str(lop['id']))
    assert sorted(_chi_tiet(nk)['ids']) == sorted(b['id'] for b in rows)


# ── 3. Ngày nghỉ theo đợt ───────────────────────────────────────────────────

def test_bo_ngay_nghi_cua_dot(lop):
    x('INSERT INTO term_holidays (term_id, on_date, name) VALUES (%s, %s, %s)',
      (lop['dot'], THU_HAI + timedelta(days=3), 'Nghỉ bù thử'))
    r = _sinh(lop['gv'], lop['id'])
    assert r.status_code == 201, r.json()
    nghi = [b for b in r.json()['buoi'] if b['trangThai'] == 'nghi_le']
    assert [b['ngay'] for b in nghi] == _ngay(3)
    assert 'Nghỉ bù thử' in nghi[0]['lyDo']
    assert _so_buoi(lop['id']) == 3


def test_le_co_dinh_chua_khai_thi_van_tao_nhung_canh_bao(lop):
    """Gợi ý, không tự quyết: lớp luyện thi có khi vẫn học ngày lễ. Nhưng phải
    NÓI ra trên đúng dòng ấy, trước khi bấm."""
    qk = date(NAM, 9, 2)
    r = _sinh(lop['gv'], lop['id'], weekdays=[qk.isoweekday()], dry_run=True,
              **{'from': (qk - timedelta(days=3)).isoformat(),
                 'to': (qk + timedelta(days=3)).isoformat()})
    assert r.status_code == 200, r.json()
    b = next(b for b in r.json()['buoi'] if b['ngay'] == qk.isoformat())
    assert b['trangThai'] == 'tao', b
    assert 'Quốc khánh' in (b['canhBao'] or ''), b


# ── 4. Chạy lại không đẻ buổi trùng ─────────────────────────────────────────

def test_chay_lai_khong_de_buoi_trung(lop):
    assert _sinh(lop['gv'], lop['id']).status_code == 201
    d = _sinh(lop['gv'], lop['id'], dry_run=True).json()
    assert d['dem']['tao'] == 0 and d['dem']['trung'] == 4, d['dem']
    assert all('#' in b['lyDo'] for b in d['buoi'] if b['trangThai'] == 'trung'), d['buoi']
    r2 = _sinh(lop['gv'], lop['id'])
    # Không tạo gì thì không phải 201, và không ghi nhật ký một việc không xảy ra.
    assert r2.status_code == 200, r2.json()
    assert _so_buoi(lop['id']) == 4


def test_buoi_da_huy_khong_chan_sinh_lai(lop):
    x("INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status) "
      "VALUES (%s, %s, 90, 'cancelled')",
      (lop['id'], datetime.combine(THU_HAI + timedelta(days=1), time(19, 30))))
    d = _sinh(lop['gv'], lop['id'], dry_run=True).json()
    assert d['dem']['tao'] == 4, d['dem']


# ── Dữ liệu vào sai ─────────────────────────────────────────────────────────

@pytest.mark.parametrize(('sua', 'chu'), [
    ({'weekdays': []}, 'thứ'),
    ({'weekdays': [8]}, 'thứ'),
    ({'weekdays': 'thu 3'}, 'thứ'),
    ({'start_time': '25:00'}, 'giờ'),
    ({'duration_minutes': 0}, 'phút'),
    ({'from': f'{NAM}-10-10', 'to': f'{NAM}-10-01'}, 'ngày'),
    ({'from': 'hôm nay'}, 'ngày'),
    ({'weekdays': [1, 2, 3, 4, 5, 6, 7], 'from': f'{NAM}-01-01', 'to': f'{NAM}-12-31'}, 'buổi'),
])
def test_du_lieu_vao_sai_thi_400_va_khong_ghi(lop, sua, chu):
    r = _sinh(lop['gv'], lop['id'], **sua)
    assert r.status_code == 400, r.json()
    assert chu in r.json()['error'].lower(), r.json()
    assert _so_buoi(lop['id']) == 0


# ── Gợi ý ───────────────────────────────────────────────────────────────────

def test_goi_y_doc_tu_mo_ta_lich_va_tu_dot(lop):
    x('INSERT INTO term_holidays (term_id, on_date, name) VALUES (%s, %s, %s)',
      (lop['dot'], date(NAM, 9, 2), 'Quốc khánh'))
    d = _goi_y(lop['gv'], lop['id']).json()
    assert d['goiY']['weekdays'] == [2, 4], d['goiY']
    assert d['goiY']['startTime'] == '19:30'
    assert d['goiY']['durationMinutes'] == 90
    # Đợt bắt đầu SAU hôm nay → từ ngày đầu đợt; lớp không có ngày kết thúc →
    # tới hết đợt.
    assert d['goiY']['from'] == f'{NAM}-08-01'
    assert d['goiY']['to'] == f'{NAM}-12-31'
    assert d['dot']['id'] == lop['dot']
    assert [n['ngay'] for n in d['dot']['ngayNghi']] == [f'{NAM}-09-02']


@pytest.mark.parametrize(('mo_ta', 'thu', 'gio', 'phut'), [
    ('Thứ 3, 5 · 19:30–21:00', [2, 4], '19:30', 90),
    ('T2, T4, T6 · 18h–19h30', [1, 3, 5], '18:00', 90),
    ('Thứ 7 và Chủ nhật 8:00 - 10:00', [6, 7], '08:00', 120),
    ('CN 14:00', [7], '14:00', None),
    ('Lịch linh hoạt, báo sau', [], None, None),
    ('', [], None, None),
])
def test_doan_lich_tu_mo_ta(mo_ta, thu, gio, phut):
    from teaching.sinh_buoi import doan_lich
    assert doan_lich(mo_ta) == (thu, gio, phut)


# ── API ngày nghỉ của đợt ───────────────────────────────────────────────────

def _nghi(ai, term_id, method='get', body=None, hid=None):
    url = f'/api/admin/terms/{term_id}/holidays' + (f'/{hid}' if hid else '')
    a = _api(ai)
    return getattr(a, method)(url, body, format='json') if body is not None else getattr(a, method)(url)


def test_ngay_nghi_chi_hoc_vu_va_quan_tri_khai(lop):
    than = {'ngay': f'{NAM}-09-02', 'ten': 'Quốc khánh'}
    assert _nghi(lop['gv'], lop['dot'], 'post', than).status_code == 403, 'giảng viên'
    assert _nghi(lop['tg'], lop['dot'], 'post', than).status_code == 403, 'trợ giảng'
    r = _nghi(lop['hoc_vu'], lop['dot'], 'post', than)
    assert r.status_code == 201, r.json()
    assert _nghi(lop['hoc_vu'], lop['dot'], 'post', than).status_code == 409
    nk = q1("SELECT target_id FROM admin_audit WHERE action='term.holiday.add' "
            "ORDER BY id DESC LIMIT 1")
    assert nk and nk['target_id'] == str(lop['dot'])


def test_ngay_nghi_ngoai_dot_bi_chan(lop):
    r = _nghi(lop['hoc_vu'], lop['dot'], 'post', {'ngay': f'{NAM + 1}-01-01', 'ten': 'Tết Dương lịch'})
    assert r.status_code == 400, r.json()
    assert 'ngoài' in r.json()['error']


def test_goi_y_le_co_dinh_trong_dot_bo_cai_da_khai_va_xoa_duoc(lop):
    d = _nghi(lop['hoc_vu'], lop['dot']).json()
    # Đợt 01/08–31/12: trong bốn lễ dương lịch cố định chỉ 02/09 rơi vào.
    assert [g['ngay'] for g in d['goiY']] == [f'{NAM}-09-02'], d['goiY']
    assert _nghi(lop['hoc_vu'], lop['dot'], 'post', d['goiY'][0]).status_code == 201
    d2 = _nghi(lop['hoc_vu'], lop['dot']).json()
    assert d2['goiY'] == []
    hid = d2['ngayNghi'][0]['id']
    assert _nghi(lop['hoc_vu'], lop['dot'], 'delete', hid=hid).status_code == 200
    assert _nghi(lop['hoc_vu'], lop['dot']).json()['ngayNghi'] == []


def test_khong_goi_y_ngay_le_da_qua(lop):
    """Đo 13/09/2026 trên đợt thật: màn hình gợi ý "02/09/2026 Quốc khánh" mười
    một ngày sau khi nó đã qua. Ngày đã qua không bỏ được buổi nào nữa."""
    hom_nay = local_now().date()
    dot = q1("INSERT INTO terms (name, starts_on, ends_on, status) "
             "VALUES ('Dot bac qua hom nay', %s, %s, 'active') RETURNING id",
             (hom_nay - timedelta(days=400), hom_nay + timedelta(days=400)))['id']
    goi_y = [date.fromisoformat(g['ngay']) for g in _nghi(lop['hoc_vu'], dot).json()['goiY']]
    assert goi_y, 'khoảng 800 ngày mà không gợi ý lễ nào — phép kiểm không kiểm được gì'
    assert all(d >= hom_nay for d in goi_y), goi_y


def test_them_nhieu_ngay_mot_lan_hong_mot_thi_khong_ghi_gi(lop):
    tot = {'ngay': f'{NAM}-09-02', 'ten': 'Quốc khánh'}
    hong = {'ngay': f'{NAM}-13-40', 'ten': 'Sai'}
    r = _nghi(lop['hoc_vu'], lop['dot'], 'post', {'items': [tot, hong]})
    assert r.status_code == 400, r.json()
    assert _nghi(lop['hoc_vu'], lop['dot']).json()['ngayNghi'] == []
    r = _nghi(lop['hoc_vu'], lop['dot'], 'post',
              {'items': [tot, {'ngay': f'{NAM}-09-03', 'ten': 'Nghỉ liền kề Quốc khánh'}]})
    assert r.status_code == 201, r.json()
    assert len(_nghi(lop['hoc_vu'], lop['dot']).json()['ngayNghi']) == 2


# ── 5. Danh sách buổi nói rõ buổi nào chưa diễn ra ──────────────────────────

def test_danh_sach_buoi_co_co_da_dien_ra(lop):
    nay = local_now()
    x("INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status) "
      "VALUES (%s, %s, 90, 'planned'), (%s, %s, 90, 'planned')",
      (lop['id'], nay - timedelta(days=2), lop['id'], nay + timedelta(days=2)))
    d = _api(lop['gv']).get(f'/api/teach/classes/{lop["id"]}/sessions').json()
    co = sorted((s['startsAt'], s['started']) for s in d['sessions'])
    assert [c[1] for c in co] == [True, False], co
