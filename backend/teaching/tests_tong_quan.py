"""Tổng quan v2 (1.4a, 24/09/2026) — `teaching/overview.py`.

Ghi chú họp TopHSA: admin/học vụ cần xem "hiện nay bao nhiêu lớp, bao nhiêu rời
lớp, giáo viên điểm danh, bao nhiêu tài khoản lâu không hoạt động".

Chạy trên CSDL thật rồi cuộn lại (conftest.py). Số liệu tổng quan là số TOÀN
TRUNG TÂM, nên mỗi phép kiểm tự dựng MỘT ĐỢT HỌC RIÊNG và lọc `term_id` về đợt
ấy (lớp, rời lớp, điểm danh), hoặc truyền `chi_id` (tài khoản ngủ) — không đếm
tổng bảng, để người khác thao tác song song trên cùng CSDL không làm đỏ oan.
"""
import uuid
from datetime import datetime, time, timedelta

import pytest

from common.clock import local_now, local_today
from common.db import q1, x
from common.permissions import ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db


def _nguoi(vai=ROLE_STUDENT, status='active', tao_luc=None):
    r = q1("INSERT INTO users (name, email, password, role, status, created_at) "
           "VALUES (%s, %s, 'x', %s, %s, %s) RETURNING id",
           ('TQ %s' % uuid.uuid4().hex[:6], 'dj_tq_%s@example.com' % uuid.uuid4().hex[:12],
            vai, status, tao_luc or local_now()))
    return r['id']


def _dot():
    return q1("INSERT INTO terms (name, code) VALUES (%s, %s) RETURNING id",
              ('Dot TQ', 'tq-%s' % uuid.uuid4().hex[:8]))['id']


def _lop(dot, loai='nhom', gv=None, ten='Lop TQ', status='active'):
    return q1("INSERT INTO classes (name, course_id, teacher_id, status, term_id, class_type) "
              "VALUES (%s, 'hsa_quantitative', %s, %s, %s, %s) RETURNING id",
              (ten, gv, status, dot, loai))['id']


def _vao(lop, uid):
    q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s) RETURNING id',
       (lop, uid, local_now() - timedelta(days=60)))


def _roi(lop, uid, luc, ly_do):
    q1('INSERT INTO class_members (class_id, user_id, joined_at, left_at, leave_reason) '
       'VALUES (%s,%s,%s,%s,%s) RETURNING id',
       (lop, uid, luc - timedelta(days=30), luc, ly_do))


def _buoi(lop, bat_dau, phut, tick, status='planned'):
    q1('INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status, '
       'attendance_taken_at) VALUES (%s,%s,%s,%s,%s) RETURNING id',
       (lop, bat_dau, phut, status, tick))


def _su_kien(uid, kind, luc):
    q1("INSERT INTO learning_events (user_id, dedup_key, occurred_at, event_date, kind, "
       "course_id, source) VALUES (%s,%s,%s,%s,%s,'hsa_quantitative','system') RETURNING id",
       (uid, 'tq:%s' % uuid.uuid4().hex[:10], luc, luc.date(), kind))


def _thay(uid, luc):
    x('UPDATE users SET last_seen_at = %s WHERE id = %s', (luc, uid))


def _luc(ngay, gio, phut=0):
    return datetime.combine(ngay, time(gio, phut))


# ── Rời lớp ────────────────────────────────────────────────────────────────

def test_roi_lop_chi_dem_trong_khoang_ca_hai_bien_va_tach_ly_do_loai():
    from teaching.overview import tong_quan
    dot = _dot()
    nhom, gia_su = _lop(dot, 'nhom'), _lop(dot, 'gia_su')
    hom_nay = local_today()
    tu, den = hom_nay - timedelta(days=10), hom_nay - timedelta(days=3)

    _roi(nhom, _nguoi(), _luc(tu, 0, 5), 'dropped')               # biên trái: tính
    _roi(nhom, _nguoi(), _luc(hom_nay - timedelta(days=5), 9), 'completed')
    _roi(nhom, _nguoi(), _luc(hom_nay - timedelta(days=4), 9), 'dropped')
    _roi(gia_su, _nguoi(), _luc(hom_nay - timedelta(days=6), 9), 'transferred')
    _roi(gia_su, _nguoi(), _luc(den, 23), None)                   # biên phải: CẢ NGÀY `den`
    _roi(nhom, _nguoi(), _luc(tu - timedelta(days=1), 23, 59), 'dropped')   # trước khoảng
    _roi(nhom, _nguoi(), _luc(hom_nay - timedelta(days=1), 9), 'completed')  # sau khoảng
    _vao(nhom, _nguoi())                                          # đang học
    _roi(nhom, _nguoi(ROLE_TEACHER), _luc(hom_nay - timedelta(days=5), 9), 'dropped')  # nhân sự

    r = tong_quan(term_id=dot, tu=tu, den=den)['roiLop']
    assert (r['tu'], r['den']) == (tu.isoformat(), den.isoformat())
    assert r['tong'] == 5, r
    assert r['theoLyDo'] == {'completed': 1, 'dropped': 2, 'transferred': 1, 'chuaGhi': 1}, r
    assert r['theoLoai'] == {'nhom': 3, 'gia_su': 2}, r
    assert [d['leftOn'] for d in r['ds']][0] == den.isoformat(), 'mới nhất lên đầu'
    assert len(r['ds']) == 5 and {d['reason'] for d in r['ds']} == {
        'completed', 'dropped', 'transferred', None}
    # 6 tháng, tháng cuối là tháng của `den`; gồm cả em rời TRƯỚC `tu` (vẫn trong 6
    # tháng), không gồm em rời SAU `den`.
    thang = r['theoThang']
    assert len(thang) == 6 and thang[-1]['thang'] == den.strftime('%Y-%m'), thang
    assert sum(t['tong'] for t in thang) == 6, thang


def test_roi_lop_chuyen_lop_ghi_lop_moi():
    """Dòng "Chuyển lớp" trong danh sách rời lớp nói em SANG lớp nào (§55 `transferred_to`)."""
    from teaching.overview import tong_quan
    dot = _dot()
    a, b = _lop(dot, ten='Lop TQ A'), _lop(dot, ten='Lop TQ B')
    em, em2 = _nguoi(), _nguoi()
    hom_nay = local_today()
    luc = _luc(hom_nay - timedelta(days=2), 9)
    moi = q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s) RETURNING id',
             (b, em, luc))['id']
    q1("INSERT INTO class_members (class_id, user_id, joined_at, left_at, leave_reason, transferred_to) "
       "VALUES (%s,%s,%s,%s,'transferred',%s) RETURNING id", (a, em, luc - timedelta(days=30), luc, moi))
    _roi(a, em2, luc, 'dropped')

    ds = tong_quan(term_id=dot, tu=hom_nay - timedelta(days=7), den=hom_nay)['roiLop']['ds']
    theo_em = {d['userId']: d for d in ds}
    assert theo_em[em]['sangLop'] == 'Lop TQ B', theo_em[em]
    assert theo_em[em2]['sangLop'] is None, theo_em[em2]


# ── Điểm danh của giảng viên ───────────────────────────────────────────────

def test_diem_danh_muon_tinh_tu_KET_THUC_buoi_cong_24_gio():
    from teaching.overview import tong_quan
    dot = _dot()
    gv, gv_ranh = _nguoi(ROLE_TEACHER), _nguoi(ROLE_TEACHER)
    lop = _lop(dot, gv=gv)
    _lop(dot, gv=gv_ranh)                     # lớp đang chạy, chưa buổi nào trong kỳ
    khong_gv = _lop(dot, gv=None)
    nay = local_now()

    def truoc(ngay, gio=0, phut=0):
        return nay - timedelta(days=ngay) + timedelta(hours=gio, minutes=phut)

    _buoi(lop, truoc(5), 90, truoc(5, 1, 90 + 60))            # tick 1 giờ sau kết thúc
    # Không ghi độ dài = 90 phút. Tick 25 giờ sau GIỜ BẮT ĐẦU = 23g30 sau KẾT THÚC →
    # đúng hạn. Đo từ giờ bắt đầu (quên độ dài buổi) thì thành "muộn".
    _buoi(lop, truoc(4), None, truoc(4, 25))
    _buoi(lop, truoc(3), 30, truoc(3, 24, 30 + 5))            # 24g05 sau kết thúc → MUỘN
    _buoi(lop, truoc(2), 90, None)                            # chưa điểm danh
    _buoi(lop, truoc(1), 90, None, status='cancelled')        # huỷ → không tính
    _buoi(lop, nay + timedelta(days=2), 90, None)             # chưa tới → không tính
    _buoi(lop, truoc(15), 90, None)                           # trước kỳ → không tính
    _buoi(khong_gv, truoc(2), 90, None)

    gv_rows = tong_quan(term_id=dot, tu=local_today() - timedelta(days=10),
                        den=local_today())['giangVien']
    theo = {g['teacherId']: g for g in gv_rows}
    assert {k: theo[gv][k] for k in ('soLop', 'buoiDaDay', 'daDiemDanh', 'chuaDiemDanh',
                                     'diemDanhMuon', 'tiLe')} == {
        'soLop': 1, 'buoiDaDay': 4, 'daDiemDanh': 3, 'chuaDiemDanh': 1,
        'diemDanhMuon': 1, 'tiLe': 75}, theo[gv]
    # Có lớp đang chạy mà chưa có buổi nào trong kỳ — vẫn hiện, tỉ lệ None chứ không 0%.
    assert theo[gv_ranh]['buoiDaDay'] == 0 and theo[gv_ranh]['tiLe'] is None
    # Buổi của lớp chưa phân công không được biến mất khỏi bảng.
    assert theo[None]['chuaDiemDanh'] == 1
    assert gv_rows[0]['chuaDiemDanh'] >= gv_rows[-1]['chuaDiemDanh'], 'việc tồn nhiều lên đầu'


# ── Tài khoản không hoạt động ──────────────────────────────────────────────

def test_tai_khoan_ngu_theo_nguong_tach_hoc_vien_nhan_su():
    from teaching.overview import tai_khoan_ngu
    nay = local_now()

    def truoc(ngay):
        return nay - timedelta(days=ngay)

    ngu_20 = _nguoi(); _thay(ngu_20, truoc(20))
    # Đăng nhập lâu rồi nhưng HỌC 3 ngày trước → đang hoạt động.
    vua_hoc = _nguoi(); _thay(vua_hoc, truoc(40)); _su_kien(vua_hoc, 'lesson', truoc(3))
    chua_vao_60 = _nguoi(tao_luc=truoc(60))
    da_khoa = _nguoi(status='suspended'); _thay(da_khoa, truoc(100))
    # Giảng viên điểm danh em hôm qua (kể cả "vắng") — đó là việc của giảng viên,
    # không phải em vào hệ thống.
    chi_diem_danh = _nguoi(); _thay(chi_diem_danh, truoc(20)); _su_kien(chi_diem_danh, 'attendance', truoc(1))
    moi_cap = _nguoi(tao_luc=truoc(2))
    # Sự kiện ở TƯƠNG LAI (tick nhầm buổi tuần sau) không phải hoạt động.
    tuong_lai = _nguoi(tao_luc=truoc(40)); _su_kien(tuong_lai, 'lesson', nay + timedelta(days=3))
    gv = _nguoi(ROLE_TEACHER); _thay(gv, truoc(15))

    r = tai_khoan_ngu(chi_id=[ngu_20, vua_hoc, chua_vao_60, da_khoa, chi_diem_danh, moi_cap,
                              tuong_lai, gv])
    assert r['nguong'] == [7, 14, 30]
    assert r['hocVien'] == {'tong': 6, 'd7': 4, 'd14': 4, 'd30': 2, 'chuaTungVao': 3}, r['hocVien']
    assert r['nhanSu'] == {'tong': 1, 'd7': 1, 'd14': 1, 'd30': 0, 'chuaTungVao': 0}, r['nhanSu']
    ds = r['ds']
    assert [d['id'] for d in ds][:2] == [chua_vao_60, tuong_lai], 'lâu nhất lên đầu'
    assert {d['id'] for d in ds} == {chua_vao_60, tuong_lai, ngu_20, chi_diem_danh}, \
        'chỉ học viên đang mở, ngủ ≥ 7 ngày'
    dong = {d['id']: d for d in ds}
    assert dong[chua_vao_60]['ngay'] == 60 and dong[chua_vao_60]['lanCuoi'] is None
    assert dong[ngu_20]['ngay'] == 20 and dong[ngu_20]['lanCuoi'] == truoc(20).date().isoformat()


# ── Bảng từng lớp, số đếm, học 7 ngày ─────────────────────────────────────

def test_bang_lop_cat_dong_xep_theo_van_de_nhung_so_dem_tren_TOAN_BO():
    from teaching.overview import tong_quan
    dot = _dot()
    gv = _nguoi(ROLE_TEACHER)
    _lop(dot, 'nhom', gv=gv, ten='A on dinh')
    _lop(dot, 'gia_su', gv=None, ten='B chua gv')
    _lop(dot, 'nhom', gv=None, ten='C chua gv')
    _lop(dot, 'gia_su', gv=gv, ten='D xong', status='finished')
    ton = _lop(dot, 'nhom', gv=gv, ten='E ton diem danh')
    _buoi(ton, local_now() - timedelta(days=1), 90, None)

    d = tong_quan(term_id=dot, tran_lop=2)
    assert d['classesTotal'] == 5 and len(d['classes']) == 2
    assert d['classes'][0]['id'] == ton, 'lớp còn buổi chưa điểm danh lên đầu'
    s = d['summary']
    assert s['classCount'] == 5
    assert s['activeNoTeacher'] == 2, 'đếm trên MỌI lớp, không trên phần đã cắt'
    assert s['classesByType'] == {
        'nhom': {'total': 3, 'active': 3, 'paused': 0, 'finished': 0, 'cancelled': 0},
        'gia_su': {'total': 2, 'active': 1, 'paused': 0, 'finished': 1, 'cancelled': 0},
    }, s['classesByType']


def test_hoc_7_ngay_chi_tinh_em_dang_hoc_va_khong_tinh_diem_danh():
    from teaching.overview import tong_quan
    dot = _dot()
    lop = _lop(dot, gv=_nguoi(ROLE_TEACHER))
    hoc, chi_dd, cu, da_roi = _nguoi(), _nguoi(), _nguoi(), _nguoi()
    for u in (hoc, chi_dd, cu):
        _vao(lop, u)
    _roi(lop, da_roi, local_now() - timedelta(days=20), 'dropped')
    nay = local_now()
    _su_kien(hoc, 'lesson', nay - timedelta(days=2))
    _su_kien(chi_dd, 'attendance', nay - timedelta(days=1))
    _su_kien(cu, 'lesson', nay - timedelta(days=10))
    _su_kien(da_roi, 'lesson', nay - timedelta(days=1))
    r = tong_quan(term_id=dot)['classes'][0]
    assert r['activeLearners7d'] == 1, r['activeLearners7d']


# ── Số câu truy vấn là thiết kế ────────────────────────────────────────────

def test_so_cau_truy_van_co_dinh_2_lop_va_20_lop():
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    from teaching.overview import tong_quan
    dot = _dot()
    gv = _nguoi(ROLE_TEACHER)
    nay = local_now()

    def them(n):
        for _ in range(n):
            lop = _lop(dot, gv=gv)
            em = _nguoi()
            _vao(lop, em)
            _su_kien(em, 'lesson', nay - timedelta(days=1))
            _buoi(lop, nay - timedelta(days=1), 90, None)

    them(2)
    with CaptureQueriesContext(connection) as hai:
        tong_quan(term_id=dot)
    them(18)
    with CaptureQueriesContext(connection) as hai_muoi:
        d = tong_quan(term_id=dot)
    assert d['classesTotal'] == 20
    assert len(hai) == len(hai_muoi) <= 9, (len(hai), len(hai_muoi))


# ── Cửa API ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize('qs', ['tu=2026-13-01', 'den=hom-qua', 'tu=2026-09-10&den=2026-09-01',
                                'term_id=abc'])
def test_tham_so_sai_tra_400_bang_tieng_viet(admin_api, qs):
    r = admin_api.get('/api/admin/overview?' + qs)
    assert r.status_code == 400, (qs, r.status_code)
    assert r.data['error'] and '_' not in r.data['error']
