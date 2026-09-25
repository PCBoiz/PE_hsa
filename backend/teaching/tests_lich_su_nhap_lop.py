"""4.1 — Xem lịch sử lớp + nhập DS học viên từ bảng tính vào lớp (V-n, V-j, 25/09/2026)."""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q1
from common.permissions import ROLE_ACADEMIC, ROLE_STUDENT, ROLE_TEACHER
from teaching.admin_users import AdminClassImportStudentsView
from teaching.views import AdminClassDetailView, AdminClassHistoryView

f = APIRequestFactory()


def _goi(view, method, body=None, ai=None, url='/x', fmt='json', **kw):
    req = (getattr(f, method)(url, body, format=fmt) if body is not None
           else getattr(f, method)(url))
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(ten, vai, hau_to='lsnl'):
    r = q1('INSERT INTO users (name, email, password, role, streak) '
           'VALUES (%s, %s, %s, %s, 0) RETURNING id',
           (ten, '%s_%s@example.com' % (ten.replace(' ', '_').lower(), hau_to), 'x', vai))
    return User.objects.get(id=r['id'])


@pytest.fixture
def canh(db):
    hocvu = _nguoi('HocVu LS', ROLE_ACADEMIC)
    gv = _nguoi('GV LS', ROLE_TEACHER)
    lop = q1("INSERT INTO classes (name, teacher_id, status, created_at) "
             "VALUES ('Lớp lịch sử/nhập', %s, 'active', now()) RETURNING id", (gv.id,))['id']
    return {'hocvu': hocvu, 'gv': gv, 'lop': lop}


def _csv(rows):
    return SimpleUploadedFile('ds.csv', ('\n'.join(rows)).encode('utf-8-sig'), content_type='text/csv')


# ── Lịch sử lớp (V-n) ────────────────────────────────────────────────────────

def test_lich_su_lop_gom_tao_va_sua(canh):
    r = _goi(AdminClassDetailView, 'put', {'note': 'Ghi chú mới'},
             ai=canh['hocvu'], class_id=canh['lop'])
    assert r.status_code == 200, r.data

    h = _goi(AdminClassHistoryView, 'get', ai=canh['hocvu'], class_id=canh['lop'])
    assert h.status_code == 200, h.data
    hanh_dong = [e['action'] for e in h.data['history']]
    assert 'class.update' in hanh_dong, h.data
    # Mới nhất ở TRÊN.
    assert h.data['history'][0]['action'] == 'class.update'


def test_lich_su_lop_khong_lan_lop_khac(canh):
    lop2 = q1("INSERT INTO classes (name, status, created_at) "
             "VALUES ('Lớp khác LS', 'active', now()) RETURNING id")['id']
    _goi(AdminClassDetailView, 'put', {'note': 'Đổi lớp 1'}, ai=canh['hocvu'], class_id=canh['lop'])
    _goi(AdminClassDetailView, 'put', {'note': 'Đổi lớp 2'}, ai=canh['hocvu'], class_id=lop2)

    h1 = _goi(AdminClassHistoryView, 'get', ai=canh['hocvu'], class_id=canh['lop'])
    assert all(e['summary'] and 'lớp 2' not in e['summary'].lower() for e in h1.data['history'])
    h2 = _goi(AdminClassHistoryView, 'get', ai=canh['hocvu'], class_id=lop2)
    assert all('lớp 1' not in (e['summary'] or '').lower() for e in h2.data['history'])


def test_lich_su_lop_khong_ton_tai_404(canh):
    r = _goi(AdminClassHistoryView, 'get', ai=canh['hocvu'], class_id=999999)
    assert r.status_code == 404


def test_giang_vien_khong_xem_duoc_lich_su_lop(canh):
    r = _goi(AdminClassHistoryView, 'get', ai=canh['gv'], class_id=canh['lop'])
    assert r.status_code == 403


def test_hoc_vien_khong_xem_duoc_lich_su_lop(canh):
    em = _nguoi('Em LS', ROLE_STUDENT)
    r = _goi(AdminClassHistoryView, 'get', ai=em, class_id=canh['lop'])
    assert r.status_code == 403


# ── Nhập DS học viên từ bảng tính vào lớp (V-j) ─────────────────────────────

def test_nhap_tu_csv_du_lieu_hop_le(canh):
    # CHỈ email — số điện thoại "đẹp" kiểu 09xxxxxxxx dễ trùng tài khoản THẬT có
    # sẵn trên `dev` (đã gặp: "0912345678" là số của một tài khoản đang dùng).
    tep = _csv(['Họ tên,Email', 'Nguyễn Văn Nhập,nvnhap_lsnl@example.com'])
    r = _goi(AdminClassImportStudentsView, 'post', {'file': tep},
             ai=canh['hocvu'], url='/x', fmt='multipart', class_id=canh['lop'])
    assert r.status_code == 201, r.data
    assert r.data['created'] == 1 and r.data['addedToClass'] is True
    d = q1("SELECT id, role, student_code FROM users WHERE lower(email)='nvnhap_lsnl@example.com'")
    assert d['role'] == ROLE_STUDENT and (d['student_code'] or '').startswith('HSA-')
    assert q1('SELECT 1 FROM class_members WHERE class_id=%s AND user_id=%s AND left_at IS NULL',
              (canh['lop'], d['id']))


def test_nhap_tu_csv_dry_run_khong_ghi_gi(canh):
    tep = _csv(['Họ tên,Email', 'Em Xem Truoc,emxemtruoc_lsnl@example.com'])
    r = _goi(AdminClassImportStudentsView, 'post', {'file': tep, 'dry_run': 'true'},
             ai=canh['hocvu'], url='/x', fmt='multipart', class_id=canh['lop'])
    assert r.status_code == 200, r.data
    assert r.data['dryRun'] is True and r.data['created'] == 1
    assert not q1("SELECT 1 FROM users WHERE lower(email)='emxemtruoc_lsnl@example.com'")


def test_nhap_tu_csv_thieu_cot_ho_ten(canh):
    tep = _csv(['Email', 'thieucot_lsnl@example.com'])
    r = _goi(AdminClassImportStudentsView, 'post', {'file': tep},
             ai=canh['hocvu'], url='/x', fmt='multipart', class_id=canh['lop'])
    assert r.status_code == 400 and 'Họ tên' in r.data['error']


def test_nhap_tu_csv_dong_thieu_lien_lac_bi_bo_qua(canh):
    tep = _csv(['Họ tên,Email', 'Khong Co Lien Lac,'])
    r = _goi(AdminClassImportStudentsView, 'post', {'file': tep},
             ai=canh['hocvu'], url='/x', fmt='multipart', class_id=canh['lop'])
    assert r.status_code == 201, r.data
    assert r.data['created'] == 0 and r.data['skipped'] == 1
    assert r.data['rows'][0]['reason'] == 'Cần ít nhất email hoặc số điện thoại.'


def test_nhap_tu_csv_email_da_ton_tai_bi_bo_qua(canh):
    da_co = _nguoi('Da Co San', ROLE_STUDENT)
    tep = _csv(['Họ tên,Email', 'Trung Email,%s' % da_co.email])
    r = _goi(AdminClassImportStudentsView, 'post', {'file': tep},
             ai=canh['hocvu'], url='/x', fmt='multipart', class_id=canh['lop'])
    assert r.status_code == 201, r.data
    assert r.data['created'] == 0 and r.data['skipped'] == 1
    assert 'đã là tài khoản' in r.data['rows'][0]['reason']


def test_nhap_sai_dinh_dang_tep(canh):
    tep = SimpleUploadedFile('ds.pdf', b'%PDF-thu', content_type='application/pdf')
    r = _goi(AdminClassImportStudentsView, 'post', {'file': tep},
             ai=canh['hocvu'], url='/x', fmt='multipart', class_id=canh['lop'])
    assert r.status_code == 400 and 'xlsx' in r.data['error'].lower()


def test_nhap_khong_co_tep(canh):
    r = _goi(AdminClassImportStudentsView, 'post', {}, ai=canh['hocvu'],
             url='/x', fmt='multipart', class_id=canh['lop'])
    assert r.status_code == 400 and 'tệp' in r.data['error'].lower()


def test_nhap_lop_khong_ton_tai_404(canh):
    tep = _csv(['Họ tên,Email', 'X,x_lsnl@example.com'])
    r = _goi(AdminClassImportStudentsView, 'post', {'file': tep},
             ai=canh['hocvu'], url='/x', fmt='multipart', class_id=999999)
    assert r.status_code == 404


def test_giang_vien_khong_nhap_duoc_qua_tep(canh):
    tep = _csv(['Họ tên,Email', 'X,x2_lsnl@example.com'])
    r = _goi(AdminClassImportStudentsView, 'post', {'file': tep},
             ai=canh['gv'], url='/x', fmt='multipart', class_id=canh['lop'])
    assert r.status_code == 403


def test_nhap_lop_gia_su_vuot_tran_tu_choi_thang(canh):
    """Trần 3 em/lớp gia sư (§54). KHÔNG tạo-rồi-cắt-bớt: kiểm TRƯỚC khi ghi
    bất cứ gì, danh sách vượt trần thì từ chối thẳng cả mẻ (400) — giữ đúng
    luật "kiểm hết rồi mới ghi" của cả khối nhập hàng loạt, không tạo 4 tài
    khoản rồi phải nêu tên 1 em "có tài khoản nhưng chưa vào lớp"."""
    gv2 = _nguoi('GV Gia Su LS', ROLE_TEACHER)
    lop_gs = q1("INSERT INTO classes (name, teacher_id, status, class_type, created_at) "
               "VALUES ('Lớp GS nhập', %s, 'active', 'gia_su', now()) RETURNING id", (gv2.id,))['id']
    tep = _csv(['Họ tên,Email',
               'GS Mot,gs1_lsnl@example.com', 'GS Hai,gs2_lsnl@example.com',
               'GS Ba,gs3_lsnl@example.com', 'GS Bon,gs4_lsnl@example.com'])
    r = _goi(AdminClassImportStudentsView, 'post', {'file': tep},
             ai=canh['hocvu'], url='/x', fmt='multipart', class_id=lop_gs)
    assert r.status_code == 400, r.data
    assert 'chỉ còn 3 chỗ' in r.data['error'], r.data
    # Từ chối THẲNG — không dòng nào được tạo, kể cả 3 dòng lẽ ra vừa đủ chỗ.
    assert not q1("SELECT 1 FROM users WHERE email IN "
                 "('gs1_lsnl@example.com','gs2_lsnl@example.com',"
                 "'gs3_lsnl@example.com','gs4_lsnl@example.com')")
