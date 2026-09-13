"""Việc hôm nay của giảng viên — `GET /api/teach/viec-hom-nay`.

Chạy trên DB thật, giao dịch CUỘN LẠI (xem `conftest.py`). Đi qua URL thật.

── THỨ ĐANG ĐƯỢC CANH (anh Sơn chốt 14/09/2026) ─────────────────────────────

  1. Giảng viên chỉ thấy lớp mình; trợ giảng chỉ thấy lớp được gán và KHÔNG thấy
     hai khối về từng em (vắng liền, cần chú ý) — cùng ranh giới với báo cáo
     phụ huynh. Học viên 403.
  2. Bốn khối việc đúng nghĩa của chúng: buổi ĐÃ BẮT ĐẦU mà chưa mở sổ; bài ĐÃ
     NỘP mà chưa chấm (đỏ khi chờ quá 5 ngày); em vắng LIỀN từ 2 buổi đã điểm
     danh; em có cảnh báo mức cao — dùng CHUNG luật với báo cáo lớp.
  3. Buổi trong 24 giờ tới hiện trước, kèm cờ thiếu link phòng.
  4. Số câu SQL không phụ thuộc số lớp — đây là màn mở mỗi tối.
"""
from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q1, x
from common.permissions import ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db


def _nguoi(ten, vai):
    row = q1("INSERT INTO users (name, email, password, role, streak) "
             "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
             (ten, '%s_vhn@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=row['id'])


def _lop(ten, gv, link='https://meet.google.com/lop-hoc'):
    return q1("INSERT INTO classes (name, course_id, teacher_id, status, meeting_url) "
              "VALUES (%s, 'hsa_quantitative', %s, 'active', %s) RETURNING id",
              (ten, gv.id, link))['id']


def _vao(lop, u, cach_ngay=20):
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, %s)',
      (lop, u.id, local_now() - timedelta(days=cach_ngay)))


def _buoi(lop, lech_gio, phut=90, status='planned', da_tick=False, link=None):
    bd = local_now() + timedelta(hours=lech_gio)
    return q1('INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status, '
              'meeting_url, attendance_taken_at) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id',
              (lop, bd, phut, status, link, bd + timedelta(minutes=phut) if da_tick else None))['id']


def _tick(buoi, u, tt):
    x('INSERT INTO attendance (session_id, user_id, status) VALUES (%s, %s, %s)',
      (buoi, u.id, tt))


def _bai(lop, ten):
    return q1("INSERT INTO assignments (class_id, title, status) VALUES (%s, %s, 'open') "
              'RETURNING id', (lop, ten))['id']


def _nop(bai, u, cach_ngay, cham=False):
    luc = local_now() - timedelta(days=cach_ngay)
    x('INSERT INTO submissions (assignment_id, user_id, submitted_at, content, graded_at, score) '
      'VALUES (%s, %s, %s, %s, %s, %s)',
      (bai, u.id, luc, 'bài', luc if cham else None, 8 if cham else None))


def _hoat_dong(u, cach_ngay):
    luc = local_now() - timedelta(days=cach_ngay)
    x("INSERT INTO learning_events (user_id, dedup_key, kind, ref_type, ref_id, course_id, "
      "topic, event_date, occurred_at) VALUES (%s, %s, 'lesson', 'lesson', 'x', "
      "'hsa_quantitative', 'Tỉ lệ', %s, %s)", (u.id, 'vhn-%d' % u.id, luc.date(), luc))


def _goi(ai):
    a = APIClient()
    if ai is not None:
        a.force_authenticate(user=ai)
    return a.get('/api/teach/viec-hom-nay')


@pytest.fixture
def canh(db):
    gv = _nguoi('GV VHN', ROLE_TEACHER)
    gv_khac = _nguoi('GV Khac VHN', ROLE_TEACHER)
    tg = _nguoi('TG VHN', ROLE_ASSISTANT)
    an = _nguoi('An VHN', ROLE_STUDENT)
    binh = _nguoi('Binh VHN', ROLE_STUDENT)
    chau = _nguoi('Chau VHN', ROLE_STUDENT)
    lop = _lop('Lop VHN', gv)
    lop_khac = _lop('Lop khac VHN', gv_khac)
    for u in (an, binh, chau, tg):
        _vao(lop, u)
    _vao(lop_khac, an)
    for u in (an, binh):
        _hoat_dong(u, 1)
    return {'gv': gv, 'gv_khac': gv_khac, 'tg': tg, 'an': an, 'binh': binh, 'chau': chau,
            'lop': lop, 'lop_khac': lop_khac}


# ── 1. Ai thấy gì ───────────────────────────────────────────────────────────

def test_ai_thay_gi(canh):
    assert _goi(None).status_code == 401
    assert _goi(canh['an']).status_code == 403
    b1 = _buoi(canh['lop'], -30)
    b2 = _buoi(canh['lop_khac'], -30)

    gv = _goi(canh['gv'])
    assert gv.status_code == 200, gv.json()
    assert [b['sessionId'] for b in gv.json()['chuaDiemDanh']['ds']] == [b1]
    assert [l['id'] for l in gv.json()['lop']] == [canh['lop']]
    assert gv.json()['troGiang'] is False
    assert 'vangLien' in gv.json() and 'canChuY' in gv.json()

    tg = _goi(canh['tg'])
    assert tg.status_code == 200, tg.json()
    assert [b['sessionId'] for b in tg.json()['chuaDiemDanh']['ds']] == [b1]
    assert tg.json()['troGiang'] is True
    # Không phải danh sách rỗng — KHÔNG CÓ khoá. Rỗng trông như "không em nào
    # vắng", tức một câu trả lời sai cho người không được phép hỏi.
    assert 'vangLien' not in tg.json() and 'canChuY' not in tg.json()

    khac = _goi(canh['gv_khac']).json()
    assert [b['sessionId'] for b in khac['chuaDiemDanh']['ds']] == [b2]


# ── 2. Bốn khối việc ────────────────────────────────────────────────────────

def test_buoi_da_bat_dau_ma_chua_mo_so(canh):
    qua = _buoi(canh['lop'], -48)
    dang = _buoi(canh['lop'], -0.5)
    _buoi(canh['lop'], -24, da_tick=True)
    _buoi(canh['lop'], -12, status='cancelled')
    _buoi(canh['lop'], 3)
    d = _goi(canh['gv']).json()['chuaDiemDanh']
    assert d['tong'] == 2
    theo_id = {b['sessionId']: b for b in d['ds']}
    assert set(theo_id) == {qua, dang}
    assert theo_id[dang]['dangDienRa'] is True and theo_id[qua]['dangDienRa'] is False
    # Buổi GẦN NHẤT trước: "tối qua tôi tick xong chưa" là câu hỏi đầu tiên.
    assert [b['sessionId'] for b in d['ds']] == [dang, qua]


def test_bai_da_nop_chua_cham_va_cho_qua_5_ngay(canh):
    moi = _bai(canh['lop'], 'Bài mới')
    cu = _bai(canh['lop'], 'Bài cũ')
    xong = _bai(canh['lop'], 'Bài đã chấm')
    _nop(moi, canh['an'], 1)
    _nop(moi, canh['binh'], 2)
    _nop(cu, canh['chau'], 6)
    _nop(xong, canh['an'], 3, cham=True)
    # Bài giao mà chưa ai nộp: không có gì để chấm.
    _bai(canh['lop'], 'Chưa ai nộp')
    d = _goi(canh['gv']).json()['chuaCham']
    theo_id = {b['assignmentId']: b for b in d}
    assert set(theo_id) == {moi, cu}, d
    assert theo_id[moi]['soBai'] == 2 and theo_id[moi]['quaHan'] is False
    assert theo_id[cu]['soBai'] == 1 and theo_id[cu]['quaHan'] is True
    assert theo_id[cu]['choNgay'] == 6
    # Chờ lâu nhất lên đầu.
    assert [b['assignmentId'] for b in d] == [cu, moi]


def test_em_vang_lien_tu_hai_buoi(canh):
    b1 = _buoi(canh['lop'], -72, da_tick=True)
    b2 = _buoi(canh['lop'], -48, da_tick=True)
    b3 = _buoi(canh['lop'], -24, da_tick=True)
    # An: vắng ba buổi liền. Bình: vắng hai buổi rồi có mặt buổi cuối → không.
    # Châu: buổi cuối vắng, buổi trước KHÔNG có dòng (chưa tick) → chuỗi đứt.
    for b in (b1, b2, b3):
        _tick(b, canh['an'], 'absent')
    _tick(b1, canh['binh'], 'absent')
    _tick(b2, canh['binh'], 'absent')
    _tick(b3, canh['binh'], 'present')
    _tick(b3, canh['chau'], 'absent')
    d = _goi(canh['gv']).json()['vangLien']
    assert [(e['userId'], e['soBuoi']) for e in d] == [(canh['an'].id, 3)], d
    assert d[0]['classId'] == canh['lop']


def test_vang_co_phep_khong_tinh_la_vang_lien(canh):
    b1 = _buoi(canh['lop'], -48, da_tick=True)
    b2 = _buoi(canh['lop'], -24, da_tick=True)
    _tick(b1, canh['an'], 'absent')
    _tick(b2, canh['an'], 'excused')
    assert _goi(canh['gv']).json()['vangLien'] == []


def test_can_chu_y_dung_chung_luat_voi_bao_cao_lop(canh):
    """Châu chưa có hoạt động nào → mức cao. An, Bình hoạt động hôm qua → không.
    Và câu chữ phải là câu của `reports._alerts`, không phải một bản chép."""
    from teaching.reports import _alerts, canh_bao_muc_cao
    d = _goi(canh['gv']).json()['canChuY']
    assert [e['userId'] for e in d] == [canh['chau'].id], d
    assert d[0]['lyDo'] == canh_bao_muc_cao(None)
    st = {'idleDays': None, 'mockCount': 1, 'mockTrend': None, 'lag': 0}
    assert [a['text'] for a in _alerts(st) if a['level'] == 'high'] == [canh_bao_muc_cao(None)]
    assert canh_bao_muc_cao(3) is None


# ── 3. Sắp tới trong 24 giờ ─────────────────────────────────────────────────

def test_sap_toi_24_gio_va_co_thieu_link(canh):
    khong_link = _lop('Lop khong link VHN', canh['gv'], link=None)
    toi_nay = _buoi(canh['lop'], 2)
    mai = _buoi(khong_link, 20)
    _buoi(khong_link, 20, link='https://meet.google.com/rieng')
    _buoi(canh['lop'], 30)          # ngoài 24 giờ
    _buoi(canh['lop'], 5, status='cancelled')
    d = _goi(canh['gv']).json()['sapToi']
    assert d[0]['sessionId'] == toi_nay and d[0]['thieuLink'] is False
    theo_id = {b['sessionId']: b for b in d}
    assert theo_id[mai]['thieuLink'] is True
    assert sum(1 for b in d if b['classId'] == khong_link) == 2
    assert len(d) == 3


# ── 4. Số câu SQL không theo số lớp ─────────────────────────────────────────

def test_so_cau_sql_khong_theo_so_lop(canh):
    def dem():
        with CaptureQueriesContext(connection) as c:
            assert _goi(canh['gv']).status_code == 200
        return len(c.captured_queries)
    mot = dem()
    for i in range(4):
        l = _lop('Lop them %d VHN' % i, canh['gv'])
        _vao(l, canh['chau'])
        _buoi(l, -20)
        _buoi(l, 2)
    assert dem() == mot, 'thêm lớp là thêm câu SQL — N+1'
