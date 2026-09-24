"""DANH SÁCH HỌC VIÊN (1.4b, kế hoạch thử nghiệm TopHSA 24/09/2026) — `GET /api/admin/users`.

Ghi chú họp TopHSA: "quản lý lớp là priority số 1, rồi quản lý học sinh". Màn Tài khoản
thêm cho mỗi học viên: lớp ĐANG HỌC (kèm loại lớp), lần cuối hoạt động, tiến độ bài; và
hai ô lọc "chưa xếp lớp", "không hoạt động ≥ N ngày".

Ba luật phép kiểm canh:
  · "hoạt động" ĐÚNG MỘT định nghĩa với thẻ "Tài khoản lâu không vào" ở Tổng quan
    (`overview.tai_khoan_ngu`) — số trên thẻ và số dòng của danh sách lọc phải bằng nhau;
  · "lớp đang học" và "môn mở" ĐÚNG luật của cổng mở môn (`courses/truy_cap.py`);
  · số câu truy vấn KHÔNG tăng theo số dòng của trang.

Chạy trên CSDL thật trong giao dịch cuộn lại (`conftest.py`). Mỗi phép kiểm đặt tên người
của mình bằng một tiền tố riêng rồi lọc `q=<tiền tố>` — không đếm tổng bảng.
"""
import uuid
from datetime import timedelta

import pytest

from common.clock import local_now, local_today
from common.db import q1, x
from common.permissions import ROLE_ACADEMIC, ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db


def _tien_to():
    return 'hv14b%s' % uuid.uuid4().hex[:8]


def _nguoi(tien_to, ten, vai=ROLE_STUDENT, status='active', tao_luc=None):
    return q1("INSERT INTO users (name, email, password, role, status, created_at) "
              "VALUES (%s, %s, 'x', %s, %s, %s) RETURNING id",
              ('%s %s' % (tien_to, ten), '%s_%s@example.com' % (tien_to, uuid.uuid4().hex[:8]),
               vai, status, tao_luc or local_now()))['id']


def _lop(ten, mon='hsa_quantitative', loai='nhom', status='active'):
    return q1("INSERT INTO classes (name, course_id, status, class_type) "
              "VALUES (%s, %s, %s, %s) RETURNING id", (ten, mon, status, loai))['id']


def _vao(lop, uid, roi_luc=None):
    x('INSERT INTO class_members (class_id, user_id, joined_at, left_at, leave_reason) '
      'VALUES (%s, %s, %s, %s, %s)',
      (lop, uid, local_now() - timedelta(days=60), roi_luc, 'dropped' if roi_luc else None))


def _thay(uid, luc):
    x('UPDATE users SET last_seen_at = %s WHERE id = %s', (luc, uid))


def _su_kien(uid, kind, luc):
    x("INSERT INTO learning_events (user_id, dedup_key, occurred_at, event_date, kind, "
      "course_id, source) VALUES (%s, %s, %s, %s, %s, 'hsa_quantitative', 'system')",
      (uid, 'hv14b:%s' % uuid.uuid4().hex[:10], luc, luc.date(), kind))


def _xong(uid, lesson_id, course_id):
    x("INSERT INTO lesson_progress (user_id, lesson_id, course_id, status, completed_at) "
      "VALUES (%s, %s, %s, 'completed', %s)", (uid, lesson_id, course_id, local_now()))


def _ds(api, tien_to, **loc):
    qs = '&'.join(['q=%s' % tien_to, 'per_page=100'] + ['%s=%s' % kv for kv in loc.items()])
    r = api.get('/api/admin/users?' + qs)
    assert r.status_code == 200, r.data
    return r.data


def _theo_id(d):
    return {u['id']: u for u in d['users']}


@pytest.fixture
def hoc_vu_api(db):
    # APIClient RIÊNG — không nhận fixture `api`: `admin_api` cũng dùng chính đối tượng
    # ấy, và `force_authenticate` lần sau đè lần trước (lượt đầu viết vậy: "quản trị
    # viên" của phép kiểm lặng lẽ thành học vụ, chỉ thấy học viên).
    from rest_framework.test import APIClient

    from accounts.models import User
    uid = _nguoi(_tien_to(), 'hoc vu', vai=ROLE_ACADEMIC)
    c = APIClient()
    c.force_authenticate(user=User.objects.get(id=uid))
    return c


# ── (a) Lớp đang học ───────────────────────────────────────────────────────

def test_lop_dang_hoc_co_loai_lop_bo_lop_huy_va_lop_da_roi(admin_api):
    t = _tien_to()
    em = _nguoi(t, 'An')
    a = _lop('%s A nhom' % t)
    b = _lop('%s B gia su xong' % t, loai='gia_su', status='finished')
    c = _lop('%s C da huy' % t, status='cancelled')
    d = _lop('%s D da roi' % t)
    _vao(a, em)
    _vao(b, em)                                  # lớp đã kết thúc: em vẫn mở môn → vẫn "đang học"
    _vao(c, em)                                  # lớp đã huỷ: không mở môn → không hiện
    _vao(d, em, roi_luc=local_now() - timedelta(days=3))

    u = _theo_id(_ds(admin_api, t))[em]
    assert u['lopDangHoc'] == [
        {'id': a, 'name': '%s A nhom' % t, 'classType': 'nhom'},
        {'id': b, 'name': '%s B gia su xong' % t, 'classType': 'gia_su'},
    ], u['lopDangHoc']
    # Khoá cũ (tên lớp) — màn hình bản trước còn đọc — phải kể CÙNG tập lớp.
    assert u['classes'] == [l['name'] for l in u['lopDangHoc']]


# ── (b) Hoạt động cuối ─────────────────────────────────────────────────────

def test_hoat_dong_cuoi_cung_dinh_nghia_voi_tong_quan(admin_api):
    from teaching.overview import tai_khoan_ngu
    t = _tien_to()
    nay = local_now()

    def truoc(n):
        return nay - timedelta(days=n)

    ngu_20 = _nguoi(t, 'ngu20'); _thay(ngu_20, truoc(20))
    vua_hoc = _nguoi(t, 'vuahoc'); _thay(vua_hoc, truoc(40)); _su_kien(vua_hoc, 'lesson', truoc(3))
    # Điểm danh là việc GIẢNG VIÊN làm cho em — không phải em vào hệ thống.
    chi_dd = _nguoi(t, 'chidd'); _thay(chi_dd, truoc(20)); _su_kien(chi_dd, 'attendance', truoc(1))
    # Sự kiện ở tương lai (tick nhầm buổi tuần sau) không phải hoạt động.
    tuong_lai = _nguoi(t, 'tuonglai', tao_luc=truoc(40)); _su_kien(tuong_lai, 'lesson', nay + timedelta(days=3))
    chua_vao = _nguoi(t, 'chuavao', tao_luc=truoc(60))
    hom_nay = _nguoi(t, 'homnay'); _thay(hom_nay, nay - timedelta(minutes=5))

    u = _theo_id(_ds(admin_api, t))
    lay = {k: (u[k]['hoatDongCuoi'], u[k]['ngayKhongHoatDong'])
           for k in (ngu_20, vua_hoc, chi_dd, tuong_lai, chua_vao, hom_nay)}
    assert lay == {
        ngu_20: (truoc(20).date().isoformat(), 20),
        vua_hoc: (truoc(3).date().isoformat(), 3),
        chi_dd: (truoc(20).date().isoformat(), 20),
        tuong_lai: (None, None),
        chua_vao: (None, None),
        hom_nay: ((nay - timedelta(minutes=5)).date().isoformat(), (local_today() - (nay - timedelta(minutes=5)).date()).days),
    }, lay
    # Cùng MỘT định nghĩa với thẻ Tổng quan: ngày thấy cuối của từng em khớp từng dòng.
    ngu = {d['id']: d['lanCuoi'] for d in tai_khoan_ngu(chi_id=list(lay))['ds']}
    for k, lan_cuoi in ngu.items():
        assert u[k]['hoatDongCuoi'] == lan_cuoi, (k, u[k]['hoatDongCuoi'], lan_cuoi)


def test_loc_khong_hoat_dong_bang_dung_so_cua_the_tong_quan(admin_api, hoc_vu_api):
    """Số trên thẻ "Tài khoản lâu không vào" (≥7/14/30 ngày) = số dòng danh sách lọc.
    Lệch nhau là học vụ bấm từ "12 em" sang danh sách 15 em — không ai biết bên nào đúng."""
    from teaching.overview import NGUONG_NGU, tai_khoan_ngu
    t = _tien_to()
    nay = local_now()

    def truoc(n):
        return nay - timedelta(days=n)

    ids = []
    for ten, ngay in (('a', 3), ('b', 8), ('c', 15), ('d', 31), ('e', 100)):
        u = _nguoi(t, ten); _thay(u, truoc(ngay)); ids.append(u)
    ids.append(_nguoi(t, 'chuavao60', tao_luc=truoc(60)))
    ids.append(_nguoi(t, 'moicap', tao_luc=truoc(2)))            # cấp hôm kia: chưa "ngủ"
    vua_hoc = _nguoi(t, 'vuahoc'); _thay(vua_hoc, truoc(40)); _su_kien(vua_hoc, 'lesson', truoc(1))
    ids.append(vua_hoc)
    khoa = _nguoi(t, 'khoa', status='suspended'); _thay(khoa, truoc(90)); ids.append(khoa)
    gv = _nguoi(t, 'gv', vai=ROLE_TEACHER); _thay(gv, truoc(20)); ids.append(gv)

    the = tai_khoan_ngu(chi_id=ids)
    for n in NGUONG_NGU:
        dong = {u['id'] for u in _ds(admin_api, t, khong_hoat_dong=n)['users']}
        assert len(dong) == the['hocVien']['d%d' % n] + the['nhanSu']['d%d' % n], (n, dong, the)
        assert khoa not in dong, 'tài khoản đã khoá không tính "không hoạt động"'
        # Học vụ chỉ thấy học viên — con số của họ là con số dòng Học viên của thẻ.
        hv = {u['id'] for u in _ds(hoc_vu_api, t, khong_hoat_dong=n)['users']}
        assert len(hv) == the['hocVien']['d%d' % n] and gv not in hv, (n, hv)
    assert {u['id'] for u in _ds(admin_api, t, khong_hoat_dong=14)['users']} == {
        ids[2], ids[3], ids[4], ids[5], gv}


@pytest.mark.parametrize('rac', ['abc', '0', '-7', '1e9'])
def test_loc_khong_hoat_dong_tham_so_rac_khong_ai_khop_va_khong_500(admin_api, rac):
    t = _tien_to()
    _nguoi(t, 'x', tao_luc=local_now() - timedelta(days=90))
    assert _ds(admin_api, t, khong_hoat_dong=rac)['total'] == 0


# ── (c) Tiến độ ────────────────────────────────────────────────────────────

def _mon_tam(so_bai_co_chuong, so_bai_khong_chuong=1):
    mon = 'hv14b_%s' % uuid.uuid4().hex[:8]
    x("INSERT INTO courses (id, title) VALUES (%s, 'Môn thử 1.4b')", (mon,))
    bai = [q1("INSERT INTO lessons (course_id, module, title, sort_order) VALUES (%s, 'Chương 1', %s, %s) "
              "RETURNING id", (mon, 'Bài %d' % i, i))['id'] for i in range(so_bai_co_chuong)]
    for i in range(so_bai_khong_chuong):   # bài chưa gắn chương: không vào mẫu số (cùng luật báo cáo lớp)
        q1("INSERT INTO lessons (course_id, module, title, sort_order) VALUES (%s, '', 'Nháp', %s) "
           "RETURNING id", (mon, 100 + i))
    return mon, bai


def test_tien_do_la_bai_xong_tren_tong_bai_cua_mon_mo_qua_lop(admin_api):
    from courses.truy_cap import BA_MON
    t = _tien_to()
    mon, bai = _mon_tam(3)
    mon_khac, bai_khac = _mon_tam(2)

    em_mot_mon = _nguoi(t, 'motmon')
    _vao(_lop('%s lop mon tam' % t, mon=mon), em_mot_mon)
    _xong(em_mot_mon, bai[0], mon)
    _xong(em_mot_mon, bai_khac[0], mon_khac)     # môn KHÔNG mở qua lớp → không cộng

    em_ca_ba = _nguoi(t, 'caba')
    _vao(_lop('%s lop ca ba mon' % t, mon=None), em_ca_ba)     # course_id NULL = cả ba môn
    bai_dl = q1("SELECT id FROM lessons WHERE course_id = 'hsa_verbal' "
                "AND module IS NOT NULL AND module <> '' ORDER BY id LIMIT 1")['id']
    _xong(em_ca_ba, bai_dl, 'hsa_verbal')

    chua_lop = _nguoi(t, 'chualop'); _xong(chua_lop, bai[1], mon)
    roi_lop = _nguoi(t, 'roilop')
    _vao(_lop('%s lop da roi' % t, mon=mon), roi_lop, roi_luc=local_now() - timedelta(days=1))
    # Nhân sự CÓ trong lớp (đo 31/08: quản trị viên id 7 là thành viên lớp 1 để xem giao
    # diện) — vẫn không có tiến độ: bỏ vế "chỉ học viên" thì dòng này mọc "0/3 bài".
    gv = _nguoi(t, 'gv', vai=ROLE_TEACHER)
    _vao(_lop('%s lop co gv' % t, mon=mon), gv)

    u = _theo_id(_ds(admin_api, t))
    assert u[em_mot_mon]['tienDo'] == {'xong': 1, 'tong': 3}, u[em_mot_mon]
    tong_ba = q1("SELECT COUNT(*) AS n FROM lessons WHERE course_id = ANY(%s) "
                 "AND module IS NOT NULL AND module <> ''", (list(BA_MON),))['n']
    assert u[em_ca_ba]['tienDo'] == {'xong': 1, 'tong': tong_ba}, u[em_ca_ba]
    # Chưa mở môn nào thì KHÔNG có tiến độ — "0/0" hay "1/0" đều nói sai.
    assert u[chua_lop]['tienDo'] is None and u[roi_lop]['tienDo'] is None
    assert u[gv]['tienDo'] is None, 'nhân sự không học — không có tiến độ'


# ── Lọc "chưa xếp lớp" ─────────────────────────────────────────────────────

def test_loc_chua_xep_lop_theo_dung_luat_lop_dang_hoc(admin_api):
    t = _tien_to()
    khong_lop = _nguoi(t, 'khonglop')
    chi_lop_huy = _nguoi(t, 'lophuy'); _vao(_lop('%s huy' % t, status='cancelled'), chi_lop_huy)
    da_roi = _nguoi(t, 'daroi'); _vao(_lop('%s roi' % t), da_roi, roi_luc=local_now() - timedelta(days=2))
    dang_hoc = _nguoi(t, 'danghoc'); _vao(_lop('%s dang' % t), dang_hoc)
    lop_xong = _nguoi(t, 'lopxong'); _vao(_lop('%s xong' % t, status='finished'), lop_xong)
    gv = _nguoi(t, 'gv', vai=ROLE_TEACHER)           # nhân sự không "chờ xếp lớp"

    d = _ds(admin_api, t, chua_xep_lop=1)
    assert {u['id'] for u in d['users']} == {khong_lop, chi_lop_huy, da_roi}, d['users']
    assert gv not in {u['id'] for u in d['users']}
    assert all(u['lopDangHoc'] == [] for u in d['users']), 'lọc và cột Lớp phải cùng một luật'
    # Ô không tích thì không lọc.
    assert _ds(admin_api, t, chua_xep_lop=0)['total'] == 6


def test_xuat_csv_loc_giong_man_hinh(admin_api):
    """Bản CSV nhận CÙNG bộ lọc (`build_user_filters`): lọc "chưa xếp lớp" trên màn mà tải
    về cả danh sách là học vụ mang nhầm danh sách đi gọi."""
    t = _tien_to()
    _nguoi(t, 'khonglop')
    _vao(_lop('%s dang' % t), _nguoi(t, 'danghoc'))
    # Em chỉ còn trong lớp ĐÃ HUỶ: vào danh sách "chưa xếp lớp", và cột lớp của tệp không
    # được kể lớp huỷ ấy — cùng luật "lớp đang học" với cột Lớp trên màn.
    _vao(_lop('%s lopdahuy' % t, status='cancelled'), _nguoi(t, 'lophuy'))
    r = admin_api.get('/api/admin/export/users.csv?q=%s&chua_xep_lop=1' % t)
    assert r.status_code == 200
    noi_dung = r.content.decode('utf-8-sig')
    assert '%s khonglop' % t in noi_dung and '%s danghoc' % t not in noi_dung
    assert '%s lophuy' % t in noi_dung and '%s lopdahuy' % t not in noi_dung, noi_dung


def test_co_loc_khong_de_dat_ten_tep_csv():
    """`any_user_filter` quyết tên tệp "(đã lọc)": ô "Chưa xếp lớp" bỏ tích (`=0`) không
    phải đang lọc — tên tệp nói "đã lọc" cho một tệp đủ là lừa người cầm tệp."""
    from teaching.admin_users import any_user_filter
    assert any_user_filter({'chua_xep_lop': '1'}) is True
    assert any_user_filter({'chua_xep_lop': '0'}) is False
    assert any_user_filter({'khong_hoat_dong': '7'}) is True
    assert any_user_filter({}) is False


# ── Số câu truy vấn là thiết kế ────────────────────────────────────────────

def test_so_cau_truy_van_khong_tang_theo_so_dong(admin_api):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    t = _tien_to()
    mon, bai = _mon_tam(2)
    lop = _lop('%s lop' % t, mon=mon)

    def them(n):
        for _ in range(n):
            em = _nguoi(t, uuid.uuid4().hex[:4])
            _vao(lop, em)
            _xong(em, bai[0], mon)
            _su_kien(em, 'lesson', local_now() - timedelta(days=1))

    them(2)
    with CaptureQueriesContext(connection) as it:
        assert len(_ds(admin_api, t)['users']) == 2
    them(10)
    with CaptureQueriesContext(connection) as nhieu:
        assert len(_ds(admin_api, t)['users']) == 12
    with CaptureQueriesContext(connection) as loc:
        _ds(admin_api, t, khong_hoat_dong=7, chua_xep_lop=1)
    assert len(it) == len(nhieu), [c['sql'][:80] for c in nhieu.captured_queries]
    # Trang + lớp/hoạt động + bài xong + tổng bài — xem docstring `AdminUsersView`.
    assert len(nhieu) <= 4, [c['sql'][:80] for c in nhieu.captured_queries]
    assert len(loc) <= len(nhieu)


def test_hoc_vien_hien_du_ba_khoa_moi_ca_khi_trang_chi_co_nhan_su(admin_api):
    """Khoá mới có mặt ở MỌI dòng (nhân sự: tiến độ None) — màn hình không phải đoán."""
    t = _tien_to()
    _nguoi(t, 'gv', vai=ROLE_TEACHER)
    u = _ds(admin_api, t)['users'][0]
    assert {'lopDangHoc', 'hoatDongCuoi', 'ngayKhongHoatDong', 'tienDo'} <= set(u), sorted(u)
